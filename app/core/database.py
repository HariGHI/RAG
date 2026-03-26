"""
LanceDB Database Operations
Handles connections and CRUD for plain tables and vector stores
"""

import lancedb
from pathlib import Path
from typing import Optional, List, Dict, Any
import pyarrow as pa
from uuid import uuid4

from .config import settings


class PlainTableManager:
    """
    Manages plain LanceDB tables (no vectors)
    Used for storing chunks with FTS indexing
    """
    
    def __init__(self):
        self.base_path = settings.plaintables_path
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_db_path(self, space_uuid: str) -> Path:
        """Get database path for a space"""
        space_path = self.base_path / space_uuid
        space_path.mkdir(parents=True, exist_ok=True)
        return space_path
    
    def _get_db(self, space_uuid: str) -> lancedb.DBConnection:
        """Get LanceDB connection for a space"""
        db_path = self._get_db_path(space_uuid)
        return lancedb.connect(str(db_path))
    
    def _get_table_name(self, space_uuid: str) -> str:
        """Table name is same as space_uuid"""
        return space_uuid
    
    # ==================== CREATE ====================
    
    def create_table(self, space_uuid: str, initial_data: Optional[List[Dict]] = None) -> bool:
        """
        Create a new plain table for a space
        
        Schema:
        - chunk_id: string (unique)
        - chunk: string (FTS indexed)
        - title: string (section title)
        - parent_title: string (parent section title)
        - artifact_id: string
        - file_name: string
        """
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        # Check if table already exists
        if table_name in db.table_names():
            return False
        
        # Define schema with title hierarchy
        schema = pa.schema([
            pa.field("chunk_id", pa.string()),
            pa.field("chunk", pa.string()),
            pa.field("title", pa.string()),
            pa.field("parent_title", pa.string()),
            pa.field("artifact_id", pa.string()),
            pa.field("file_name", pa.string()),
        ])
        
        if initial_data:
            db.create_table(table_name, initial_data)
        else:
            # Create empty table with schema
            db.create_table(table_name, schema=schema)
        
        return True
    
    def table_exists(self, space_uuid: str) -> bool:
        """Check if table exists for a space"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        return table_name in db.table_names()
    
    # ==================== INSERT ====================
    
    def insert_chunks(self, space_uuid: str, chunks: List[Dict]) -> int:
        """
        Insert chunks into the table
        
        Each chunk dict should have:
        - chunk: str (the text)
        - artifact_id: str
        - file_name: str
        
        chunk_id is auto-generated if not provided
        """
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        # Create table if it doesn't exist
        if table_name not in db.table_names():
            self.create_table(space_uuid)
        
        table = db.open_table(table_name)
        
        # Add chunk_id if not present
        for chunk in chunks:
            if "chunk_id" not in chunk:
                chunk["chunk_id"] = str(uuid4())
        
        table.add(chunks)
        return len(chunks)
    
    # ==================== READ ====================
    
    def get_all_chunks(self, space_uuid: str) -> List[Dict]:
        """Get all chunks from a space"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return []
        
        table = db.open_table(table_name)
        return table.to_pandas().to_dict(orient="records")
    
    def get_chunk_by_id(self, space_uuid: str, chunk_id: str) -> Optional[Dict]:
        """Get a specific chunk by ID"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return None
        
        table = db.open_table(table_name)
        results = table.search().where(f"chunk_id = '{chunk_id}'").limit(1).to_pandas()

        if results.empty:
            return None
        return results.to_dict(orient="records")[0]
    
    def get_chunks_by_artifact(self, space_uuid: str, artifact_id: str) -> List[Dict]:
        """Get all chunks for a specific artifact"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return []
        
        table = db.open_table(table_name)
        results = table.search().where(f"artifact_id = '{artifact_id}'").to_pandas()
        return results.to_dict(orient="records")
    
    # ==================== FTS SEARCH ====================
    
    def fts_search(self, space_uuid: str, query: str, limit: int = 10) -> List[Dict]:
        """
        Full-text search on chunks
        """
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return []
        
        table = db.open_table(table_name)
        
        # Create FTS index if not exists
        try:
            table.create_fts_index("chunk", replace=False)
        except Exception:
            pass  # Index might already exist
        
        # Perform FTS search
        results = table.search(query, query_type="fts").limit(limit).to_pandas()
        return results.to_dict(orient="records")
    
    # ==================== UPDATE ====================
    
    def update_chunk(self, space_uuid: str, chunk_id: str, new_text: str) -> bool:
        """Update chunk text by ID"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return False
        
        table = db.open_table(table_name)
        table.update(where=f"chunk_id = '{chunk_id}'", values={"chunk": new_text})
        return True
    
    # ==================== DELETE ====================
    
    def delete_chunk(self, space_uuid: str, chunk_id: str) -> bool:
        """Delete a chunk by ID"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return False
        
        table = db.open_table(table_name)
        table.delete(f"chunk_id = '{chunk_id}'")
        return True
    
    def delete_artifact_chunks(self, space_uuid: str, artifact_id: str) -> bool:
        """Delete all chunks for an artifact"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return False
        
        table = db.open_table(table_name)
        table.delete(f"artifact_id = '{artifact_id}'")
        return True
    
    def delete_table(self, space_uuid: str) -> bool:
        """Delete entire table for a space"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return False
        
        db.drop_table(table_name)
        return True


class VectorStoreManager:
    """
    Manages LanceDB vector stores
    Used for storing embeddings and similarity search
    """
    
    def __init__(self, embedding_dim: int = 384):
        self.base_path = settings.vector_stores_path
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.embedding_dim = embedding_dim  # all-MiniLM-L6-v2 = 384
    
    def _get_db_path(self, space_uuid: str) -> Path:
        """Get database path for a space"""
        space_path = self.base_path / space_uuid
        space_path.mkdir(parents=True, exist_ok=True)
        return space_path
    
    def _get_db(self, space_uuid: str) -> lancedb.DBConnection:
        """Get LanceDB connection for a space"""
        db_path = self._get_db_path(space_uuid)
        return lancedb.connect(str(db_path))
    
    def _get_table_name(self, space_uuid: str) -> str:
        """Table name encodes both space and model: {space_uuid}_{model_uuid}"""
        return f"{space_uuid}_{settings.embedding_model_id}"

    # ==================== CREATE ====================

    def create_table(self, space_uuid: str, initial_data: Optional[List[Dict]] = None) -> bool:
        """
        Create a new vector store for a space
        
        Schema:
        - chunk_id: string (links to plain table)
        - chunk: string
        - vector: fixed_size_list<float32>[embedding_dim]
        - title: string
        - parent_title: string
        - artifact_id: string
        - file_name: string
        """
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name in db.table_names():
            return False
        
        # Define schema with vector column and title hierarchy
        schema = pa.schema([
            pa.field("chunk_id", pa.string()),
            pa.field("chunk", pa.string()),
            pa.field("vector", pa.list_(pa.float32(), self.embedding_dim)),
            pa.field("title", pa.string()),
            pa.field("parent_title", pa.string()),
            pa.field("artifact_id", pa.string()),
            pa.field("file_name", pa.string()),
        ])
        
        if initial_data:
            db.create_table(table_name, initial_data)
        else:
            db.create_table(table_name, schema=schema)
        
        return True
    
    def table_exists(self, space_uuid: str) -> bool:
        """Check if vector store exists for a space"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        return table_name in db.table_names()
    
    # ==================== INSERT ====================
    
    def insert_vectors(self, space_uuid: str, records: List[Dict]) -> int:
        """
        Insert vectors into the store
        
        Each record should have:
        - chunk_id: str
        - chunk: str
        - vector: List[float]
        - artifact_id: str
        - file_name: str
        """
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            self.create_table(space_uuid)
        
        table = db.open_table(table_name)
        table.add(records)
        return len(records)
    
    # ==================== READ ====================
    
    def get_all_vectors(self, space_uuid: str) -> List[Dict]:
        """Get all records from vector store (without vectors for readability)"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return []
        
        table = db.open_table(table_name)
        df = table.to_pandas()
        if "vector" in df.columns:
            df = df.drop(columns=["vector"])
        return df.to_dict(orient="records")
    
    # ==================== VECTOR SEARCH ====================
    
    def vector_search(
        self, 
        space_uuid: str, 
        query_vector: List[float], 
        limit: int = 10
    ) -> List[Dict]:
        """
        Similarity search using query vector
        """
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return []
        
        table = db.open_table(table_name)
        results = table.search(query_vector).limit(limit).to_pandas()
        if "vector" in results.columns:
            results = results.drop(columns=["vector"])
        return results.to_dict(orient="records")
    
    # ==================== HYBRID SEARCH ====================
    
    def hybrid_search(
        self,
        space_uuid: str,
        query_vector: List[float],
        query_text: str,
        limit: int = 10,
        vector_weight: float = 0.5
    ) -> List[Dict]:
        """
        Hybrid search combining vector similarity and FTS
        
        Falls back to vector search if hybrid fails
        """
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return []
        
        table = db.open_table(table_name)
        
        # Create FTS index if not exists
        try:
            table.create_fts_index("chunk", replace=False)
        except Exception:
            pass
        
        # Try hybrid search with new API
        try:
            results = (
                table.search(query_type="hybrid")
                .vector(query_vector)
                .text(query_text)
                .limit(limit)
                .to_pandas()
            )
        except Exception:
            try:
                results = table.search(query_vector).limit(limit).to_pandas()
            except Exception:
                return []

        if "vector" in results.columns:
            results = results.drop(columns=["vector"])
        return results.to_dict(orient="records")
    
    # ==================== UPDATE ====================
    
    def update_vector(
        self, 
        space_uuid: str, 
        chunk_id: str, 
        new_vector: List[float],
        new_text: Optional[str] = None
    ) -> bool:
        """Update vector (and optionally text) by chunk_id"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return False
        
        table = db.open_table(table_name)
        updates = {"vector": new_vector}
        if new_text:
            updates["chunk"] = new_text
        
        table.update(where=f"chunk_id = '{chunk_id}'", values=updates)
        return True
    
    # ==================== DELETE ====================
    
    def delete_vector(self, space_uuid: str, chunk_id: str) -> bool:
        """Delete a vector by chunk_id"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return False
        
        table = db.open_table(table_name)
        table.delete(f"chunk_id = '{chunk_id}'")
        return True
    
    def delete_artifact_vectors(self, space_uuid: str, artifact_id: str) -> bool:
        """Delete all vectors for an artifact"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return False
        
        table = db.open_table(table_name)
        table.delete(f"artifact_id = '{artifact_id}'")
        return True
    
    def delete_table(self, space_uuid: str) -> bool:
        """Delete entire vector store for a space"""
        db = self._get_db(space_uuid)
        table_name = self._get_table_name(space_uuid)
        
        if table_name not in db.table_names():
            return False
        
        db.drop_table(table_name)
        return True


# ==================== GLOBAL INSTANCES ====================

plain_table_manager = PlainTableManager()
vector_store_manager = VectorStoreManager()
