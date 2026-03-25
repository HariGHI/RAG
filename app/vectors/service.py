"""
Vectors Service
Business logic for embedding chunks and managing vector store
"""

from typing import List, Optional, Dict, Set

from app.core.database import plain_table_manager, vector_store_manager
from app.core.embeddings import embedding_model
from app.core.logger import log_step, log_success, log_embed, log_db


class VectorService:
    """
    Service for managing vectors (embeddings)
    
    Handles:
    - Generating embeddings for chunks
    - CRUD operations on vector store
    """
    
    # ==================== EMBED ====================
    
    def embed_space(
        self,
        space_uuid: str,
        artifact_ids: Optional[List[str]] = None,
        re_embed: bool = False
    ) -> Dict:
        """
        Generate embeddings for chunks in a space
        
        Args:
            space_uuid: Target space UUID
            artifact_ids: Specific artifacts to embed (None = all)
            re_embed: If True, re-embed existing vectors
            
        Returns:
            Summary of embedding operation
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
        """List all vectors in a space (without vector data)"""
        return vector_store_manager.get_all_vectors(space_uuid)
    
    def vector_exists(self, space_uuid: str, chunk_id: str) -> bool:
        """Check if a vector exists for a chunk"""
        vectors = vector_store_manager.get_all_vectors(space_uuid)
        return any(v.get("chunk_id") == chunk_id for v in vectors)
    
    # ==================== CREATE (Manual) ====================
    
    def create_vector(
        self,
        space_uuid: str,
        chunk_id: str,
        chunk: str,
        artifact_id: str,
        file_name: str
    ) -> Dict:
        """
        Manually create a vector for a chunk
        
        Generates embedding and inserts into vector store
        """
        # Generate embedding
        embedding = embedding_model.embed_text(chunk)
        
        # Insert into vector store
        vector_store_manager.insert_vectors(space_uuid, [{
            "chunk_id": chunk_id,
            "chunk": chunk,
            "vector": embedding,
            "artifact_id": artifact_id,
            "file_name": file_name,
        }])
        
        return {
            "chunk_id": chunk_id,
            "chunk": chunk,
            "artifact_id": artifact_id,
            "file_name": file_name,
            "has_vector": True,
        }
    
    # ==================== UPDATE ====================
    
    def update_vector(
        self,
        space_uuid: str,
        chunk_id: str,
        new_chunk: Optional[str] = None
    ) -> bool:
        """
        Update (re-embed) a vector
        
        If new_chunk is provided, uses that text. Otherwise, fetches from plain table.
        """
        # Get chunk text
        if new_chunk is None:
            chunk_data = plain_table_manager.get_chunk_by_id(space_uuid, chunk_id)
            if not chunk_data:
                return False
            new_chunk = chunk_data.get("chunk", "")
        
        # Generate new embedding
        new_embedding = embedding_model.embed_text(new_chunk)
        
        # Update in vector store
        return vector_store_manager.update_vector(
            space_uuid=space_uuid,
            chunk_id=chunk_id,
            new_vector=new_embedding,
            new_text=new_chunk
        )
    
    # ==================== DELETE ====================
    
    def delete_vector(self, space_uuid: str, chunk_id: str) -> bool:
        """Delete a vector by chunk_id"""
        return vector_store_manager.delete_vector(space_uuid, chunk_id)


# ==================== GLOBAL INSTANCE ====================

vector_service = VectorService()
