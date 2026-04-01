"""
Retrieval Service
Business logic for the retrieval step of the RAG pipeline.

This is the first active stage of RAG — given a user query it finds the
most relevant chunks stored in the space. Three modes are available:

  VECTOR  — embed the query and run ANN (approximate nearest-neighbour)
            search against the LanceDB vector store.
  FTS     — run a BM25 full-text search against the plain table.
  HYBRID  — run both and let LanceDB merge the ranked lists (recommended).

Results are normalised to a common score field and returned in rank order.
"""

from typing import List, Optional, Dict

from app.core.database import plain_table_manager, vector_store_manager
from app.core.embeddings import embedding_model
from app.core.logger import log_search, log_step

from .retrieval_datamodel import RetrievalMode


class RetrievalService:
    """
    Service for retrieving relevant chunks
    
    Supports:
    - Vector search (semantic similarity)
    - FTS search (keyword matching)
    - Hybrid search (combined)
    """
    
    # ==================== MAIN RETRIEVE ====================
    
    def retrieve(
        self,
        space_uuid: str,
        query: str,
        mode: RetrievalMode = RetrievalMode.HYBRID,
        limit: int = 5,
        artifact_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Retrieve relevant chunks based on query
        
        Args:
            space_uuid: Target space UUID
            query: Search query
            mode: Retrieval mode (vector, hybrid, fts)
            limit: Max results
            artifact_ids: Filter by artifacts (optional)
            
        Returns:
            List of results with scores and ranks
        """
        log_search(mode.value.upper(), query)
        
        if mode == RetrievalMode.VECTOR:
            results = self._vector_search(space_uuid, query, limit)
        elif mode == RetrievalMode.FTS:
            results = self._fts_search(space_uuid, query, limit)
        else:  # HYBRID
            results = self._hybrid_search(space_uuid, query, limit)
        
        # Filter by artifact_ids if specified
        if artifact_ids:
            results = [r for r in results if r.get("artifact_id") in artifact_ids]
        
        log_search(mode.value.upper(), query, results=len(results))
        
        # Add ranks
        for i, result in enumerate(results):
            result["rank"] = i + 1
        
        return results[:limit]
    
    # ==================== VECTOR SEARCH ====================
    
    def _vector_search(
        self,
        space_uuid: str,
        query: str,
        limit: int
    ) -> List[Dict]:
        """
        Pure vector similarity search
        
        1. Embed query
        2. Search vector store
        3. Return top-k similar chunks
        """
        # Generate query embedding
        query_vector = embedding_model.embed_query(query)
        
        # Search vector store
        results = vector_store_manager.vector_search(
            space_uuid=space_uuid,
            query_vector=query_vector,
            limit=limit
        )
        
        # Normalize scores (LanceDB returns distance, we want similarity)
        for r in results:
            if "_distance" in r:
                # Convert L2 distance to similarity score (0-1)
                r["score"] = 1 / (1 + r["_distance"])
                del r["_distance"]
            elif "score" not in r:
                r["score"] = None
        
        return results
    
    # ==================== FTS SEARCH ====================
    
    def _fts_search(
        self,
        space_uuid: str,
        query: str,
        limit: int
    ) -> List[Dict]:
        """
        Pure full-text search
        
        Uses LanceDB FTS on plain table
        """
        results = plain_table_manager.fts_search(
            space_uuid=space_uuid,
            query=query,
            limit=limit
        )
        
        # Normalize score field
        for r in results:
            if "_score" in r:
                r["score"] = r["_score"]
                del r["_score"]
            elif "score" not in r:
                r["score"] = None
        
        return results
    
    # ==================== HYBRID SEARCH ====================
    
    def _hybrid_search(
        self,
        space_uuid: str,
        query: str,
        limit: int
    ) -> List[Dict]:
        """
        Hybrid search combining vector + FTS
        
        Uses LanceDB's built-in hybrid search
        """
        # Generate query embedding
        query_vector = embedding_model.embed_query(query)
        
        # Hybrid search on vector store
        results = vector_store_manager.hybrid_search(
            space_uuid=space_uuid,
            query_vector=query_vector,
            query_text=query,
            limit=limit
        )
        
        # Normalize scores
        for r in results:
            if "_distance" in r:
                r["score"] = 1 / (1 + r["_distance"])
                del r["_distance"]
            elif "_score" in r:
                r["score"] = r["_score"]
                del r["_score"]
            elif "score" not in r:
                r["score"] = None
        
        return results
    
    # ==================== UTILITY ====================
    
    def get_context(
        self,
        space_uuid: str,
        query: str,
        mode: RetrievalMode = RetrievalMode.HYBRID,
        limit: int = 5
    ) -> str:
        """
        Convenience method used by the augmentation service.

        Retrieves relevant chunks and formats them as a single string
        where each chunk is prefixed with its source file name and
        separated by a horizontal rule. Returns an empty string when
        no results are found.
        """
        results = self.retrieve(space_uuid, query, mode, limit)
        
        if not results:
            return ""
        
        context_parts = []
        for r in results:
            source = f"[{r.get('file_name', 'unknown')}]"
            text = r.get("chunk", "")
            context_parts.append(f"{source}\n{text}")
        
        return "\n\n---\n\n".join(context_parts)


# ==================== GLOBAL INSTANCE ====================

retrieval_service = RetrievalService()
