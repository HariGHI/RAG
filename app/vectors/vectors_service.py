"""
Vectors Service
Business logic for the vectorization step of the RAG pipeline.

This module is responsible for taking the text chunks stored in the plain
table and converting them into numerical embeddings so they can be searched
by semantic similarity. Embeddings are produced by the all-MiniLM-L6-v2
SentenceTransformer model (384-dimensional float vectors) and stored in a
separate LanceDB vector store per space.
"""

from typing import List, Optional, Dict, Set

from app.core.database import plain_table_manager, vector_store_manager
from app.core.embeddings import embedding_model
from app.core.logger import log_step, log_success, log_embed, log_db


class VectorService:
    """
    Handles all embedding operations for a space.

    RAG pipeline step:  Artifacts → Chunks → [Vectors] → Retrieval
                                               ^^^^^^^^
                                               This service

    Responsibilities:
    - Read chunks from the plain table
    - Generate embeddings in batch using SentenceTransformers
    - Write vector records to the LanceDB vector store
    - Skip already-embedded chunks unless re_embed is requested
    """
    
    # ==================== EMBED ====================
    
    def embed_space(
        self,
        space_uuid: str,
        artifact_ids: Optional[List[str]] = None,
        re_embed: bool = False
    ) -> Dict:
        """
        Generate embeddings for all (or selected) chunks in a space.

        Flow:
          1. Load all chunks from the plain table.
          2. Optionally filter to the requested artifact_ids.
          3. Skip chunks that already have a vector (unless re_embed=True).
          4. Batch-encode the remaining chunk texts.
          5. Write vector records (chunk_id, text, vector, metadata) to
             the LanceDB vector store.

        Args:
            space_uuid:   Target space UUID.
            artifact_ids: Embed only these artifacts; None = embed all.
            re_embed:     When True, delete and re-create existing vectors.

        Returns:
            Dict with chunks_embedded, chunks_skipped, and a status message.
        """
        log_step("🧠 Embed", f"Starting embedding for space: {space_uuid[:8]}...")
        
        # Get all chunks from plain table
        all_chunks = plain_table_manager.get_all_chunks(space_uuid)
        log_embed(f"Found {len(all_chunks)} total chunks")
        
        # Filter by artifact_ids if specified
        if artifact_ids:
            all_chunks = [c for c in all_chunks if c.get("artifact_id") in artifact_ids]
            log_embed(f"Filtered to {len(all_chunks)} chunks from selected artifacts")
        
        if not all_chunks:
            log_embed("No chunks found to embed")
            return {
                "space_uuid": space_uuid,
                "chunks_embedded": 0,
                "chunks_skipped": 0,
                "message": "No chunks found to embed"
            }
        
        # Get existing vectors to check which are already embedded
        existing_vectors = vector_store_manager.get_all_vectors(space_uuid)
        existing_chunk_ids: Set[str] = {v.get("chunk_id") for v in existing_vectors}
        
        # Determine which chunks to embed
        chunks_to_embed = []
        chunks_skipped = 0
        
        for chunk in all_chunks:
            chunk_id = chunk.get("chunk_id")
            
            if chunk_id in existing_chunk_ids and not re_embed:
                chunks_skipped += 1
                continue
            
            chunks_to_embed.append(chunk)
        
        if not chunks_to_embed:
            log_embed(f"All {chunks_skipped} chunks already embedded")
            return {
                "space_uuid": space_uuid,
                "chunks_embedded": 0,
                "chunks_skipped": chunks_skipped,
                "message": f"All {chunks_skipped} chunks already embedded. Use re_embed=true to re-embed."
            }
        
        # Generate embeddings in batch
        log_embed(f"Generating embeddings for {len(chunks_to_embed)} chunks...")
        texts = [c.get("chunk", "") for c in chunks_to_embed]
        embeddings = embedding_model.embed_texts(texts)
        log_success(f"Generated {len(embeddings)} embeddings")
        
        # Prepare vector records
        vector_records = []
        for chunk, embedding in zip(chunks_to_embed, embeddings):
            chunk_id = chunk.get("chunk_id")
            
            # If re-embedding, delete existing vector first
            if chunk_id in existing_chunk_ids:
                vector_store_manager.delete_vector(space_uuid, chunk_id)
            
            vector_records.append({
                "chunk_id": chunk_id,
                "chunk": chunk.get("chunk", ""),
                "vector": embedding,
                "title": chunk.get("title", ""),
                "parent_title": chunk.get("parent_title", ""),
                "artifact_id": chunk.get("artifact_id", ""),
                "file_name": chunk.get("file_name", ""),
            })
        
        # Insert into vector store
        log_db("INSERT", f"vectors ({len(vector_records)} records)")
        vector_store_manager.insert_vectors(space_uuid, vector_records)
        log_success(f"Embedded {len(vector_records)} chunks successfully")
        
        return {
            "space_uuid": space_uuid,
            "chunks_embedded": len(vector_records),
            "chunks_skipped": chunks_skipped,
            "message": f"Successfully embedded {len(vector_records)} chunks"
        }
    
    # ==================== READ ====================

    def list_vectors(self, space_uuid: str) -> List[Dict]:
        """
        Return all vector records for a space, excluding the raw embedding data.

        The actual float arrays are stripped to keep responses readable.
        Each record includes chunk_id, chunk text, artifact_id, and file_name.
        """
        return vector_store_manager.get_all_vectors(space_uuid)

    def vector_exists(self, space_uuid: str, chunk_id: str) -> bool:
        """Return True if the given chunk already has an embedding in the vector store."""
        vectors = vector_store_manager.get_all_vectors(space_uuid)
        return any(v.get("chunk_id") == chunk_id for v in vectors)


# ==================== GLOBAL INSTANCE ====================

vector_service = VectorService()
