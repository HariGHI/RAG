"""
Generation Service
Business logic for the generation step of the RAG pipeline.

This module is the final stage in the RAG pipeline. It:
  1. Calls the augmentation service to retrieve context and build prompts.
  2. Sends the assembled messages to Ollama (local LLM).
  3. Returns the model's answer along with deduplicated source attribution.

Requires Ollama to be running locally (`ollama serve`) with the configured
model pulled (`ollama pull <model>`).
"""

from typing import List, Optional, Dict
import ollama

from app.core.config import settings
from app.core.database import plain_table_manager
from app.core.logger import log_step, log_llm
from app.retrieval.retrieval_service import retrieval_service
from app.retrieval.retrieval_datamodel import RetrievalMode
from app.augmentation.augmentation_service import augmentation_service


class GenerationService:
    """
    Runs the final generation step using a local Ollama LLM.

    RAG pipeline:  Retrieval → Augmentation → [Generation]
                                               ^^^^^^^^^^^^
                                               This service

    Responsibilities:
    - Coordinate the full RAG Q&A flow (retrieve → augment → generate)
    - Run document summarization over stored chunks
    - Check Ollama availability before making requests
    """
    
    def __init__(self):
        self.model = settings.ollama_model
        self.host = settings.ollama_host
    
    # ==================== RAG GENERATION ====================
    
    def generate(
        self,
        space_uuid: str,
        query: str,
        retrieval_mode: RetrievalMode = RetrievalMode.HYBRID,
        context_limit: int = 5,
        artifact_ids: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict:
        """
        Full RAG pipeline: retrieve relevant chunks → augment prompt → generate answer.

        Steps:
          1. Augmentation service retrieves context and builds system + user messages.
          2. Retrieval service is called again to get the raw results for source attribution.
          3. Ollama generates the answer from the assembled messages.
          4. Sources are deduplicated by artifact_id (one chip per file, not per chunk).

        Args:
            space_uuid:      Space to search for context.
            query:           The user's question.
            retrieval_mode:  How to search — VECTOR, FTS, or HYBRID (default).
            context_limit:   Maximum number of chunks to include as context.
            artifact_ids:    Restrict retrieval to these artifacts (None = all).
            system_prompt:   Override the default system prompt if needed.
            temperature:     LLM creativity (0 = deterministic, 2 = very creative).

        Returns:
            Dict with keys: query, answer, sources (list), model.
        """
        log_step("🤖 RAG", f"Query: {query[:50]}...")

        # Augmentation: build context string and prompt messages
        augmented = augmentation_service.augment(
            space_uuid=space_uuid,
            query=query,
            retrieval_mode=retrieval_mode,
            context_limit=context_limit,
            system_prompt=system_prompt,
            artifact_ids=artifact_ids,
        )

        # Retrieve results for source attribution
        results = retrieval_service.retrieve(
            space_uuid=space_uuid,
            query=query,
            mode=retrieval_mode,
            limit=context_limit,
            artifact_ids=artifact_ids,
        )
        log_step("🔍 Retrieve", f"Found {len(results)} relevant chunks")

        # Generate with Ollama
        log_llm("Generating response", self.model)
        response = ollama.chat(
            model=self.model,
            messages=augmented["messages"],
            options={"temperature": temperature}
        )
        
        answer = response.message.content
        
        # Build sources — one entry per unique artifact
        seen_artifacts = set()
        sources = []
        for r in results:
            aid = r.get("artifact_id", "")
            if aid not in seen_artifacts:
                seen_artifacts.add(aid)
                sources.append({
                    "artifact_id": aid,
                    "file_name": r.get("file_name", ""),
                    "preview": r.get("chunk", "")[:100]
                })
        
        return {
            "query": query,
            "answer": answer,
            "sources": sources,
            "model": self.model
        }
    
    # ==================== SUMMARIZATION ====================
    
    def summarize(
        self,
        space_uuid: str,
        artifact_ids: Optional[List[str]] = None,
        max_chunks: int = 10,
        style: str = "concise"
    ) -> Dict:
        """
        Summarize documents stored in a space.

        Loads chunks from the plain table (no vector search needed — we
        want breadth, not relevance here), builds a context block, and
        instructs the LLM to summarize in the requested style.

        Args:
            space_uuid:   Space whose documents to summarize.
            artifact_ids: Restrict to these artifacts; None = all.
            max_chunks:   Maximum number of chunks to include (caps context size).
            style:        Summary style — "concise", "detailed", or "bullet_points".

        Returns:
            Dict with keys: summary, artifacts_included, chunks_used, model.
        """
        # Get all chunks
        all_chunks = plain_table_manager.get_all_chunks(space_uuid)
        
        # Filter by artifact_ids if specified
        if artifact_ids:
            all_chunks = [c for c in all_chunks if c.get("artifact_id") in artifact_ids]
        
        # Limit chunks
        chunks = all_chunks[:max_chunks]
        
        if not chunks:
            return {
                "summary": "No content found to summarize.",
                "artifacts_included": [],
                "chunks_used": 0,
                "model": self.model
            }
        
        # Build content string
        content = augmentation_service.build_context(chunks)
        
        # Style-specific prompts
        style_prompts = {
            "concise": "Provide a brief, concise summary in 2-3 paragraphs.",
            "detailed": "Provide a comprehensive, detailed summary covering all major points.",
            "bullet_points": "Summarize the key points as a bulleted list."
        }
        
        style_instruction = style_prompts.get(style, style_prompts["concise"])
        
        prompt = f"""Please summarize the following content.

{style_instruction}

Content:
{content}

Summary:"""
        
        # Generate with Ollama
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.5}
        )
        
        summary = response.message.content
        
        # Get unique artifact IDs
        artifacts_included = list(set(c.get("artifact_id", "") for c in chunks))
        
        return {
            "summary": summary,
            "artifacts_included": artifacts_included,
            "chunks_used": len(chunks),
            "model": self.model
        }
    
    # ==================== HELPERS ====================

    def check_ollama(self) -> bool:
        """
        Return True if the Ollama server is reachable.

        This is called before every generation request so we can return a
        clean 503 error instead of an opaque 500 if Ollama is down.
        Start Ollama with: `ollama serve`
        """
        try:
            ollama.list()
            return True
        except Exception:
            return False


# ==================== GLOBAL INSTANCE ====================

generation_service = GenerationService()
