"""
Augmentation Service
Bridges retrieval and generation:
  - Formats retrieved chunks into a structured context string
  - Builds system + user prompts ready for the LLM
"""

from typing import List, Dict, Optional

from app.retrieval.service import retrieval_service
from app.retrieval.schemas import RetrievalMode
from app.core.logger import log_step


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based on the provided context. "
    "Always ground your answers in the context. "
    "If the context does not contain enough information, say so clearly. "
    "Be concise and accurate."
)


class AugmentationService:
    """
    Augmentation step in the RAG pipeline.

    Retrieval  →  [Augmentation]  →  Generation
                  ^^^^^^^^^^^^
                  This service

    Responsibilities:
    - Retrieve relevant chunks for a query
    - Format them into a readable context block (with section hierarchy)
    - Compose the system and user prompts for the LLM
    """

    # ==================== CONTEXT BUILDING ====================

    def build_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into a structured context string.

        Each chunk is annotated with its source file and section path
        so the LLM has provenance information.
        """
        if not chunks:
            return "No relevant context found."

        context_parts = []
        for chunk in chunks:
            title = chunk.get("title", "")
            parent = chunk.get("parent_title", "")
            text = chunk.get("chunk", "")
            source = chunk.get("file_name", "unknown")

            # Build breadcrumb: file > parent > title
            if parent and title:
                breadcrumb = f"{source} > {parent} > {title}"
            elif title:
                breadcrumb = f"{source} > {title}"
            else:
                breadcrumb = source

            context_parts.append(f"[{breadcrumb}]\n{text}")

        return "\n\n---\n\n".join(context_parts)

    # ==================== PROMPT BUILDING ====================

    def build_messages(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
    ) -> List[Dict]:
        """
        Build the messages list for Ollama/OpenAI-style chat APIs.

        Returns:
            [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
        """
        system = system_prompt or DEFAULT_SYSTEM_PROMPT

        user_content = (
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            f"Answer based on the context above:"
        )

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ]

    # ==================== FULL PIPELINE ====================

    def augment(
        self,
        space_uuid: str,
        query: str,
        retrieval_mode: RetrievalMode = RetrievalMode.HYBRID,
        context_limit: int = 5,
        system_prompt: Optional[str] = None,
        artifact_ids: Optional[List[str]] = None,
    ) -> Dict:
        """
        Full augmentation pipeline:
          1. Retrieve relevant chunks
          2. Build context string
          3. Build LLM-ready messages

        Returns a dict with context, prompts, sources, and chunk count.
        """
        log_step("Augment", f"Retrieving context for: {query[:60]}...")

        chunks = retrieval_service.retrieve(
            space_uuid=space_uuid,
            query=query,
            mode=retrieval_mode,
            limit=context_limit,
            artifact_ids=artifact_ids,
        )

        context = self.build_context(chunks)
        messages = self.build_messages(query, context, system_prompt)

        sources = []
        for r in chunks:
            chunk_text = r.get("chunk", "")
            sources.append({
                "file": r.get("file_name", ""),
                "title": r.get("title") or None,
                "parent_title": r.get("parent_title") or None,
                "preview": chunk_text[:120] + "..." if len(chunk_text) > 120 else chunk_text,
            })

        return {
            "query": query,
            "context": context,
            "system_prompt": messages[0]["content"],
            "user_prompt": messages[1]["content"],
            "messages": messages,
            "sources": sources,
            "chunk_count": len(chunks),
        }


# ==================== GLOBAL INSTANCE ====================

augmentation_service = AugmentationService()
