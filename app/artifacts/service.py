"""
Artifacts Service
Business logic for uploading and managing artifacts (markdown files)
"""

import json
from pathlib import Path
from typing import List, Optional, Dict
from uuid import uuid4

from app.core.config import settings
from app.core.database import plain_table_manager, vector_store_manager
from app.core.logger import log_step, log_success, log_chunk, log_db
from app.utils.chunker import markdown_chunker, ChunkStrategy
from app.spaces.service import space_service


class ArtifactService:
    """
    Service for managing artifacts (uploaded files)
    
    An artifact is a markdown file uploaded to a space.
    On upload, the file is:
    1. Read and parsed
    2. Chunked using selected strategy
    3. Stored in plain table (with FTS index)
    """
    
    def __init__(self):
        self.uploads_path = settings.uploads_path
        self.uploads_path.mkdir(parents=True, exist_ok=True)
    
    # ==================== UPLOAD & CHUNK ====================
    
    def upload_artifact(
        self,
        space_uuid: str,
        file_name: str,
        content: str,
        chunk_strategy: ChunkStrategy = ChunkStrategy.RECURSIVE,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> Dict:
        """
        Upload and process a markdown file
        
        Args:
            space_uuid: Target space UUID
            file_name: Original file name
            content: File content as string
            chunk_strategy: Strategy for chunking
            chunk_size: Optional custom chunk size
            chunk_overlap: Optional custom overlap
            
        Returns:
            Artifact info with chunks
        """
        log_step("📄 Upload", f"Processing file: {file_name}")
        
        # Generate artifact ID
        artifact_id = str(uuid4())
        
        # Chunk the content
        log_chunk(f"Chunking {file_name}", strategy=chunk_strategy.value)
        chunks = markdown_chunker.chunk(
            text=content,
            strategy=chunk_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        log_chunk(f"Created chunks for {file_name}", count=len(chunks))
        
        # Prepare chunks for database with title hierarchy
        db_chunks = []
        chunk_infos = []
        
        for chunk in chunks:
            chunk_id = str(uuid4())
            chunk_text = chunk.text
            
            db_chunks.append({
                "chunk_id": chunk_id,
                "chunk": chunk_text,
                "title": chunk.title or "",
                "parent_title": chunk.parent_title or "",
                "artifact_id": artifact_id,
                "file_name": file_name,
            })
            
            chunk_infos.append({
                "chunk_id": chunk_id,
                "title": chunk.title,
                "parent_title": chunk.parent_title,
                "preview": chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text,
                "length": len(chunk_text),
            })
        
        # Insert into plain table
        plain_table_manager.insert_chunks(space_uuid, db_chunks)
        
        # Track artifact in space
        space_service.add_artifact_to_space(space_uuid, artifact_id)
        
        return {
            "artifact_id": artifact_id,
            "file_name": file_name,
            "space_uuid": space_uuid,
            "chunk_count": len(chunks),
            "chunk_strategy": chunk_strategy.value,
            "chunks": chunk_infos,
        }
    
    def upload_multiple(
        self,
        space_uuid: str,
        files: List[Dict],  # [{"file_name": str, "content": str}, ...]
        chunk_strategy: ChunkStrategy = ChunkStrategy.RECURSIVE,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
    ) -> Dict:
        """
        Upload multiple files to a space
        
        Args:
            space_uuid: Target space UUID
            files: List of file dicts with file_name and content
            chunk_strategy: Strategy for chunking
            chunk_size: Optional custom chunk size
            chunk_overlap: Optional custom overlap
            
        Returns:
            Upload summary with all artifacts
        """
        artifacts = []
        total_chunks = 0
        
        for file_data in files:
            artifact = self.upload_artifact(
                space_uuid=space_uuid,
                file_name=file_data["file_name"],
                content=file_data["content"],
                chunk_strategy=chunk_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            artifacts.append(artifact)
            total_chunks += artifact["chunk_count"]
        
        return {
            "space_uuid": space_uuid,
            "artifacts": artifacts,
            "total_chunks": total_chunks,
            "message": f"Successfully uploaded {len(artifacts)} file(s) with {total_chunks} chunks",
        }
    
    # ==================== READ ====================
    
    def list_artifacts(self, space_uuid: str) -> List[Dict]:
        """List all artifacts in a space"""
        chunks = plain_table_manager.get_all_chunks(space_uuid)
        
        # Group by artifact_id
        artifacts_map = {}
        for chunk in chunks:
            artifact_id = chunk.get("artifact_id")
            if not artifact_id:
                continue
            
            if artifact_id not in artifacts_map:
                artifacts_map[artifact_id] = {
                    "artifact_id": artifact_id,
                    "file_name": chunk.get("file_name", "unknown"),
                    "space_uuid": space_uuid,
                    "chunk_count": 0,
                    "chunk_strategy": "unknown",
                    "chunks": [],
                }
            
            artifacts_map[artifact_id]["chunk_count"] += 1
            artifacts_map[artifact_id]["chunks"].append({
                "chunk_id": chunk.get("chunk_id"),
                "preview": chunk.get("chunk", "")[:100],
                "length": len(chunk.get("chunk", "")),
            })
        
        return list(artifacts_map.values())
    
    def get_artifact(self, space_uuid: str, artifact_id: str) -> Optional[Dict]:
        """Get a specific artifact by ID"""
        chunks = plain_table_manager.get_chunks_by_artifact(space_uuid, artifact_id)
        
        if not chunks:
            return None
        
        chunk_infos = []
        for chunk in chunks:
            chunk_text = chunk.get("chunk", "")
            chunk_infos.append({
                "chunk_id": chunk.get("chunk_id"),
                "preview": chunk_text[:100] + "..." if len(chunk_text) > 100 else chunk_text,
                "length": len(chunk_text),
            })
        
        return {
            "artifact_id": artifact_id,
            "file_name": chunks[0].get("file_name", "unknown") if chunks else "unknown",
            "space_uuid": space_uuid,
            "chunk_count": len(chunks),
            "chunk_strategy": "unknown",
            "chunks": chunk_infos,
        }
    
    def artifact_exists(self, space_uuid: str, artifact_id: str) -> bool:
        """Check if an artifact exists"""
        chunks = plain_table_manager.get_chunks_by_artifact(space_uuid, artifact_id)
        return len(chunks) > 0
    
    # ==================== DELETE ====================
    
    def delete_artifact(self, space_uuid: str, artifact_id: str) -> Dict:
        """
        Delete an artifact and all its chunks
        
        Also removes vectors if they exist
        """
        # Get artifact info before deletion
        chunks = plain_table_manager.get_chunks_by_artifact(space_uuid, artifact_id)
        file_name = chunks[0].get("file_name", "unknown") if chunks else "unknown"
        chunk_count = len(chunks)
        
        # Delete from plain table
        plain_table_manager.delete_artifact_chunks(space_uuid, artifact_id)
        
        # Delete from vector store (if exists)
        vector_store_manager.delete_artifact_vectors(space_uuid, artifact_id)
        
        # Remove from space tracking
        space_service.remove_artifact_from_space(space_uuid, artifact_id)
        
        return {
            "artifact_id": artifact_id,
            "file_name": file_name,
            "deleted": True,
            "chunks_deleted": chunk_count,
            "message": f"Deleted artifact '{file_name}' with {chunk_count} chunks",
        }


# ==================== GLOBAL INSTANCE ====================

artifact_service = ArtifactService()
