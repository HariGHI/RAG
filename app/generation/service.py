"""
Generation Service
Business logic for LLM generation using Ollama
"""

from typing import List, Optional, Dict
import ollama

from app.core.config import settings
from app.core.database import plain_table_manager
from app.core.logger import log_step, log_llm, log_success
from app.retrieval.service import retrieval_service
from app.retrieval.schemas import RetrievalMode
from app.augmentation.service import augmentation_service


class GenerationService:
    """
    Service for generating responses using Ollama LLM
    
    Handles:
    - RAG-based Q&A
    - Document summarization
    - Document comparison
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
        Generate answer using RAG
        
        1. Retrieve relevant chunks
        2. Build augmented prompt
        3. Generate answer with Ollama
        """
        log_step("🤖 RAG", f"Query: {query[:50]}...")
        
        # Retrieve context
        log_step("🔍 Retrieve", f"Searching for relevant context...")
        results = retrieval_service.retrieve(
            space_uuid=space_uuid,
            query=query,
            mode=retrieval_mode,
            limit=context_limit,
            artifact_ids=artifact_ids
        )
        log_step("🔍 Retrieve", f"Found {len(results)} relevant chunks")
        
        # Augmentation: build context string and prompt messages
        augmented = augmentation_service.augment(
            space_uuid=space_uuid,
            query=query,
            retrieval_mode=retrieval_mode,
            context_limit=context_limit,
            system_prompt=system_prompt,
            artifact_ids=artifact_ids,
        )
        # Re-use already-retrieved results from augmentation
        results = retrieval_service.retrieve(
            space_uuid=space_uuid,
            query=query,
            mode=retrieval_mode,
            limit=context_limit,
            artifact_ids=artifact_ids,
        )

        # Generate with Ollama
        log_llm("Generating response", self.model)
        response = ollama.chat(
            model=self.model,
            messages=augmented["messages"],
            options={"temperature": temperature}
        )
        
        answer = response["message"]["content"]
        
        # Build sources
        sources = [
            {
                "chunk_id": r.get("chunk_id", ""),
                "file_name": r.get("file_name", ""),
                "preview": r.get("chunk", "")[:100]
            }
            for r in results
        ]
        
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
        Summarize documents in a space
        
        Styles:
        - concise: Brief overview
        - detailed: Comprehensive summary
        - bullet_points: Key points as bullets
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
        
        summary = response["message"]["content"]
        
        # Get unique artifact IDs
        artifacts_included = list(set(c.get("artifact_id", "") for c in chunks))
        
        return {
            "summary": summary,
            "artifacts_included": artifacts_included,
            "chunks_used": len(chunks),
            "model": self.model
        }
    
    # ==================== COMPARISON ====================
    
    def compare(
        self,
        space_uuid: str,
        artifact_ids: List[str],
        focus: Optional[str] = None
    ) -> Dict:
        """
        Compare multiple documents
        
        Identifies similarities and differences
        """
        # Get chunks for each artifact
        artifact_contents = {}
        for artifact_id in artifact_ids:
            chunks = plain_table_manager.get_chunks_by_artifact(space_uuid, artifact_id)
            if chunks:
                file_name = chunks[0].get("file_name", artifact_id)
                content = "\n".join(c.get("chunk", "") for c in chunks[:5])  # Limit per artifact
                artifact_contents[file_name] = content
        
        if len(artifact_contents) < 2:
            return {
                "comparison": "Need at least 2 documents with content to compare.",
                "artifacts_compared": list(artifact_contents.keys()),
                "similarities": [],
                "differences": [],
                "model": self.model
            }
        
        # Build comparison prompt
        content_parts = []
        for name, content in artifact_contents.items():
            content_parts.append(f"=== {name} ===\n{content}")
        
        all_content = "\n\n".join(content_parts)
        
        focus_instruction = f"\nFocus specifically on: {focus}" if focus else ""
        
        prompt = f"""Compare the following documents and identify their similarities and differences.{focus_instruction}

{all_content}

Provide your analysis in this format:
COMPARISON: (overall comparison)
SIMILARITIES:
- (similarity 1)
- (similarity 2)
DIFFERENCES:
- (difference 1)
- (difference 2)"""
        
        # Generate with Ollama
        response = ollama.chat(
            model=self.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            options={"temperature": 0.5}
        )
        
        result_text = response["message"]["content"]
        
        # Parse response
        comparison, similarities, differences = self._parse_comparison(result_text)
        
        return {
            "comparison": comparison,
            "artifacts_compared": list(artifact_contents.keys()),
            "similarities": similarities,
            "differences": differences,
            "model": self.model
        }
    
    # ==================== HELPERS ====================

    def _parse_comparison(self, text: str) -> tuple:
        """Parse comparison response into components"""
        comparison = ""
        similarities = []
        differences = []
        
        current_section = "comparison"
        
        for line in text.split("\n"):
            line = line.strip()
            
            if line.upper().startswith("COMPARISON:"):
                comparison = line.replace("COMPARISON:", "").strip()
                current_section = "comparison"
            elif line.upper().startswith("SIMILARITIES:"):
                current_section = "similarities"
            elif line.upper().startswith("DIFFERENCES:"):
                current_section = "differences"
            elif line.startswith("-"):
                item = line[1:].strip()
                if current_section == "similarities":
                    similarities.append(item)
                elif current_section == "differences":
                    differences.append(item)
            elif current_section == "comparison" and line:
                comparison += " " + line
        
        return comparison.strip(), similarities, differences
    
    def check_ollama(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            ollama.list()
            return True
        except Exception:
            return False


# ==================== GLOBAL INSTANCE ====================

generation_service = GenerationService()
