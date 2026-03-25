"""
Chunking Module
Smart markdown parsing with title hierarchy, code-block preservation,
abbreviation-safe sentence splitting, and frontmatter stripping.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.core.config import settings


# Common abbreviations that end with a period but are NOT sentence endings
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "rev", "gen", "sgt",
    "vs", "etc", "e.g", "i.e", "fig", "approx", "dept", "est", "govt",
    "inc", "corp", "ltd", "co", "no", "vol", "pp", "ed", "eds",
    "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "mon", "tue", "wed", "thu", "fri", "sat", "sun",
    "st", "ave", "blvd", "rd",
}


class ChunkStrategy(str, Enum):
    FIXED_SIZE = "fixed_size"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    MARKDOWN_HEADER = "markdown_header"
    SEMANTIC = "semantic"
    RECURSIVE = "recursive"


@dataclass
class Chunk:
    text: str
    index: int
    title: Optional[str] = None
    parent_title: Optional[str] = None
    level: int = 0
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "index": self.index,
            "title": self.title,
            "parent_title": self.parent_title,
            "level": self.level,
            "metadata": self.metadata or {},
        }


@dataclass
class Section:
    title: str
    level: int
    content: str
    parent_title: Optional[str] = None


# ==================== MARKDOWN CLEANING ====================

def strip_frontmatter(text: str) -> str:
    """Remove YAML/TOML frontmatter (--- ... --- or +++ ... +++) from the top."""
    for fence in ("---", "+++"):
        pattern = rf"^{re.escape(fence)}\s*\n.*?\n{re.escape(fence)}\s*\n"
        match = re.match(pattern, text, re.DOTALL)
        if match:
            return text[match.end():]
    return text


def extract_code_blocks(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Replace fenced code blocks with unique placeholders so they are never split.

    Returns (text_with_placeholders, {placeholder: original_block}).
    """
    blocks: Dict[str, str] = {}
    counter = [0]

    def replacer(m: re.Match) -> str:
        key = f"\x00CODE_BLOCK_{counter[0]}\x00"
        blocks[key] = m.group(0)
        counter[0] += 1
        return key

    # Match fenced blocks: ``` or ~~~ with optional language tag
    pattern = re.compile(r"(`{3,}|~{3,})[^\n]*\n.*?\1", re.DOTALL)
    result = pattern.sub(replacer, text)
    return result, blocks


def restore_code_blocks(text: str, blocks: Dict[str, str]) -> str:
    for key, original in blocks.items():
        text = text.replace(key, original)
    return text


# ==================== SENTENCE TOKENIZER ====================

def split_sentences(text: str) -> List[str]:
    """
    Split text into sentences, avoiding splits on known abbreviations.

    Strategy:
    1. Split on '. ', '! ', '? ' (sentence-ending punctuation + space).
    2. Re-join tokens where the preceding word is a known abbreviation or a
       single capital letter (initials like "J. Smith").
    """
    # Rough split on sentence-ending punct followed by whitespace + uppercase
    raw = re.split(r'(?<=[.!?])\s+(?=[A-Z"\'])', text)

    sentences: List[str] = []
    buffer = ""

    for fragment in raw:
        candidate = (buffer + " " + fragment).strip() if buffer else fragment

        # Find the last word before the split point in `buffer`
        last_word_match = re.search(r'\b(\w+)\.\s*$', buffer) if buffer else None
        last_word = last_word_match.group(1).lower() if last_word_match else ""

        is_abbreviation = last_word in _ABBREVIATIONS
        is_initial = bool(re.match(r'^[A-Z]$', last_word.upper()) and len(last_word) == 1)

        if buffer and (is_abbreviation or is_initial):
            # Don't split here — accumulate
            buffer = candidate
        else:
            if buffer:
                sentences.append(buffer)
            buffer = fragment

    if buffer:
        sentences.append(buffer)

    return [s.strip() for s in sentences if s.strip()]


# ==================== MARKDOWN STRUCTURE PARSER ====================

def parse_markdown_sections(text: str) -> List[Section]:
    """
    Parse markdown into a flat list of Sections with header hierarchy.

    Each Section has:
    - title: the heading text (empty string for preamble before first header)
    - level: 0-6 (0 = preamble)
    - content: text under this heading
    - parent_title: the nearest ancestor heading
    """
    # Protect code blocks from header detection
    text, code_blocks = extract_code_blocks(text)

    lines = text.split("\n")
    sections: List[Section] = []

    # Track heading hierarchy: level → title
    title_stack: Dict[int, Optional[str]] = {i: None for i in range(1, 7)}

    current_title = ""
    current_level = 0
    current_parent: Optional[str] = None
    content_lines: List[str] = []

    def flush():
        content = "\n".join(content_lines).strip()
        # Restore code blocks inside content
        content = restore_code_blocks(content, code_blocks)
        if content or current_title:
            sections.append(Section(
                title=current_title,
                level=current_level,
                content=content,
                parent_title=current_parent,
            ))
        content_lines.clear()

    for line in lines:
        header_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if header_match:
            flush()
            level = len(header_match.group(1))
            title = header_match.group(2).strip()

            # Update hierarchy
            title_stack[level] = title
            for deeper in range(level + 1, 7):
                title_stack[deeper] = None

            # Find immediate parent
            parent: Optional[str] = None
            for lvl in range(level - 1, 0, -1):
                if title_stack[lvl]:
                    parent = title_stack[lvl]
                    break

            current_title = title
            current_level = level
            current_parent = parent
        else:
            content_lines.append(line)

    flush()  # flush last section

    return sections


# ==================== CHUNKER ====================

class MarkdownChunker:
    """
    Markdown-aware text chunker.

    Improvements over baseline:
    - Strips YAML/TOML frontmatter before chunking
    - Preserves code blocks (never splits inside them)
    - Abbreviation-safe sentence tokenizer
    - Paragraph-first, then sentence-level splitting with proper overlap
    - Title hierarchy tracked on every chunk
    """

    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    # ==================== MAIN ENTRY POINT ====================

    def chunk(
        self,
        text: str,
        strategy: ChunkStrategy = ChunkStrategy.SEMANTIC,
        **kwargs,
    ) -> List[Chunk]:
        # Strip frontmatter first
        text = strip_frontmatter(text)

        dispatch = {
            ChunkStrategy.FIXED_SIZE: self._chunk_fixed_size,
            ChunkStrategy.PARAGRAPH: self._chunk_by_paragraph,
            ChunkStrategy.SENTENCE: self._chunk_by_sentence,
            ChunkStrategy.MARKDOWN_HEADER: self._chunk_by_markdown_header,
            ChunkStrategy.SEMANTIC: self._chunk_semantic,
            ChunkStrategy.RECURSIVE: self._chunk_semantic,  # recursive → semantic
        }
        fn = dispatch.get(strategy)
        if not fn:
            raise ValueError(f"Unknown strategy: {strategy}")
        return fn(text, **kwargs)

    # ==================== STRATEGY: SEMANTIC (recommended) ====================

    def _chunk_semantic(
        self,
        text: str,
        chunk_size: int = None,
        overlap: int = None,
        **kwargs,
    ) -> List[Chunk]:
        """
        Structure-aware chunking:
        - Keeps complete sections together when they fit
        - Splits large sections at paragraph → sentence boundaries
        - Preserves section title as prefix on every sub-chunk
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap

        sections = parse_markdown_sections(text)
        chunks: List[Chunk] = []
        index = 0

        for section in sections:
            new_chunks = self._chunk_section(section, chunk_size, overlap, index)
            chunks.extend(new_chunks)
            index += len(new_chunks)

        return chunks

    def _chunk_section(
        self,
        section: Section,
        chunk_size: int,
        overlap: int,
        start_index: int,
    ) -> List[Chunk]:
        if section.title:
            prefix = "#" * section.level + " " + section.title
            full_text = f"{prefix}\n\n{section.content}"
        else:
            full_text = section.content

        full_text = full_text.strip()
        if not full_text:
            return []

        # Fits in one chunk
        if len(full_text) <= chunk_size:
            return [Chunk(
                text=full_text,
                index=start_index,
                title=section.title or None,
                parent_title=section.parent_title,
                level=section.level,
                metadata={"strategy": "semantic", "complete": True},
            )]

        # Too large — split content, keep title on first sub-chunk
        parts = self._split_with_overlap(section.content, chunk_size, overlap)
        result: List[Chunk] = []

        for i, part in enumerate(parts):
            if i == 0 and section.title:
                prefix = "#" * section.level + " " + section.title
                chunk_text = f"{prefix}\n\n{part}".strip()
            else:
                chunk_text = part.strip()

            if chunk_text:
                result.append(Chunk(
                    text=chunk_text,
                    index=start_index + len(result),
                    title=section.title or None,
                    parent_title=section.parent_title,
                    level=section.level,
                    metadata={
                        "strategy": "semantic",
                        "complete": False,
                        "part": i + 1,
                        "total_parts": len(parts),
                    },
                ))

        return result

    # ==================== STRATEGY: MARKDOWN HEADER ====================

    def _chunk_by_markdown_header(
        self,
        text: str,
        max_header_level: int = 3,
        **kwargs,
    ) -> List[Chunk]:
        sections = parse_markdown_sections(text)
        chunks: List[Chunk] = []

        for i, section in enumerate(sections):
            if section.level > max_header_level:
                continue
            if section.title:
                prefix = "#" * section.level + " " + section.title
                content = f"{prefix}\n\n{section.content}".strip()
            else:
                content = section.content.strip()

            if content:
                chunks.append(Chunk(
                    text=content,
                    index=i,
                    title=section.title or None,
                    parent_title=section.parent_title,
                    level=section.level,
                    metadata={"strategy": "markdown_header"},
                ))

        return chunks

    # ==================== STRATEGY: PARAGRAPH ====================

    def _chunk_by_paragraph(self, text: str, **kwargs) -> List[Chunk]:
        sections = parse_markdown_sections(text)
        chunks: List[Chunk] = []
        index = 0

        for section in sections:
            for para in re.split(r"\n\s*\n", section.content):
                para = para.strip()
                if para:
                    chunks.append(Chunk(
                        text=para,
                        index=index,
                        title=section.title or None,
                        parent_title=section.parent_title,
                        level=section.level,
                        metadata={"strategy": "paragraph"},
                    ))
                    index += 1

        return chunks

    # ==================== STRATEGY: SENTENCE ====================

    def _chunk_by_sentence(
        self,
        text: str,
        sentences_per_chunk: int = 3,
        **kwargs,
    ) -> List[Chunk]:
        sections = parse_markdown_sections(text)
        chunks: List[Chunk] = []
        index = 0

        for section in sections:
            sentences = split_sentences(section.content)
            for i in range(0, len(sentences), sentences_per_chunk):
                group = sentences[i: i + sentences_per_chunk]
                chunk_text = " ".join(group).strip()
                if chunk_text:
                    chunks.append(Chunk(
                        text=chunk_text,
                        index=index,
                        title=section.title or None,
                        parent_title=section.parent_title,
                        level=section.level,
                        metadata={
                            "strategy": "sentence",
                            "sentence_start": i,
                            "sentence_end": i + len(group),
                        },
                    ))
                    index += 1

        return chunks

    # ==================== STRATEGY: FIXED SIZE ====================

    def _chunk_fixed_size(
        self,
        text: str,
        chunk_size: int = None,
        overlap: int = None,
        **kwargs,
    ) -> List[Chunk]:
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.chunk_overlap

        # Protect code blocks
        safe_text, code_blocks = extract_code_blocks(text)
        sections = parse_markdown_sections(text)
        title_map = self._build_title_map(sections, safe_text)

        chunks: List[Chunk] = []
        start = 0
        index = 0

        while start < len(safe_text):
            end = start + chunk_size
            raw = safe_text[start:end].strip()
            if raw:
                restored = restore_code_blocks(raw, code_blocks)
                title, parent, level = self._title_at(title_map, start)
                chunks.append(Chunk(
                    text=restored,
                    index=index,
                    title=title,
                    parent_title=parent,
                    level=level,
                    metadata={"strategy": "fixed_size", "char_start": start, "char_end": end},
                ))
                index += 1

            next_start = end - overlap
            if next_start <= start:
                next_start = start + 1
            if next_start >= len(safe_text):
                break
            start = next_start

        return chunks

    # ==================== SPLITTING HELPERS ====================

    def _split_with_overlap(
        self,
        content: str,
        chunk_size: int,
        overlap: int,
    ) -> List[str]:
        """
        Split content into chunks at paragraph → sentence boundaries.
        Adds sentence-level overlap between adjacent chunks.
        """
        if len(content) <= chunk_size:
            return [content]

        # Protect code blocks
        safe_content, code_blocks = extract_code_blocks(content)

        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", safe_content) if p.strip()]
        chunks: List[str] = []
        current = ""
        overlap_sentences: List[str] = []

        for para in paragraphs:
            # Restore before length check so sizes reflect final text
            test = (current + "\n\n" + para).strip() if current else para

            if len(test) <= chunk_size:
                current = test
            else:
                if current:
                    chunks.append(restore_code_blocks(current, code_blocks))
                    # Compute overlap from last sentences of current chunk
                    overlap_sentences = self._last_sentences(current, overlap)

                if len(para) > chunk_size:
                    # Split large paragraph by sentences
                    sub = self._split_paragraph(para, chunk_size, overlap)
                    if sub:
                        # Prepend overlap from previous chunk to first sub
                        if overlap_sentences:
                            sub[0] = " ".join(overlap_sentences) + " " + sub[0]
                        chunks.extend(
                            restore_code_blocks(s, code_blocks) for s in sub[:-1]
                        )
                        current = sub[-1]
                        overlap_sentences = self._last_sentences(current, overlap)
                    else:
                        current = ""
                else:
                    if overlap_sentences:
                        current = " ".join(overlap_sentences) + "\n\n" + para
                    else:
                        current = para

        if current:
            chunks.append(restore_code_blocks(current, code_blocks))

        return chunks

    def _split_paragraph(
        self,
        para: str,
        chunk_size: int,
        overlap: int,
    ) -> List[str]:
        """Split a single over-large paragraph at sentence boundaries."""
        sentences = split_sentences(para)
        chunks: List[str] = []
        current = ""

        for sent in sentences:
            test = (current + " " + sent).strip() if current else sent
            if len(test) <= chunk_size:
                current = test
            else:
                if current:
                    chunks.append(current)
                # Start next chunk with overlap
                tail = self._last_sentences(current, overlap)
                current = (" ".join(tail) + " " + sent).strip() if tail else sent

        if current:
            chunks.append(current)

        return chunks

    @staticmethod
    def _last_sentences(text: str, max_chars: int) -> List[str]:
        """Return the last few sentences of text that fit within max_chars."""
        if max_chars <= 0:
            return []
        sentences = split_sentences(text)
        result: List[str] = []
        total = 0
        for sent in reversed(sentences):
            if total + len(sent) + 1 <= max_chars:
                result.insert(0, sent)
                total += len(sent) + 1
            else:
                break
        return result

    # ==================== TITLE MAP HELPERS (fixed size) ====================

    @staticmethod
    def _build_title_map(
        sections: List[Section],
        text: str,
    ) -> List[Tuple[int, str, Optional[str], int]]:
        """Map character positions → (title, parent_title, level)."""
        title_map: List[Tuple[int, str, Optional[str], int]] = []
        pos = 0
        for section in sections:
            if section.title:
                header = "#" * section.level + " " + section.title
                found = text.find(header, pos)
                if found >= 0:
                    title_map.append((found, section.title, section.parent_title, section.level))
                    pos = found + len(header)
        return sorted(title_map, key=lambda x: x[0])

    @staticmethod
    def _title_at(
        title_map: List[Tuple[int, str, Optional[str], int]],
        position: int,
    ) -> Tuple[Optional[str], Optional[str], int]:
        title, parent, level = None, None, 0
        for pos, t, pt, lvl in title_map:
            if pos <= position:
                title, parent, level = t, pt, lvl
            else:
                break
        return title, parent, level


# ==================== CONVENIENCE FUNCTION ====================

def chunk_markdown(
    text: str,
    strategy: ChunkStrategy = ChunkStrategy.SEMANTIC,
    chunk_size: int = None,
    chunk_overlap: int = None,
    **kwargs,
) -> List[Dict]:
    chunker = MarkdownChunker(chunk_size, chunk_overlap)
    return [c.to_dict() for c in chunker.chunk(text, strategy, **kwargs)]


# ==================== GLOBAL INSTANCE ====================

markdown_chunker = MarkdownChunker()
