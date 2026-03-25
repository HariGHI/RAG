"""
Spaces Service
Business logic for managing spaces
"""

import json
from pathlib import Path
from typing import List, Optional, Dict
from uuid import uuid4
from datetime import datetime

from app.core.config import settings
from app.core.database import plain_table_manager, vector_store_manager


class SpaceService:
    """
    Service for managing spaces
    
    A space is a workspace containing:
    - Metadata (stored in spaces.json)
    - Plain table (for chunks + FTS)
    - Vector store (for embeddings)
    """
    
    def __init__(self):
        self.metadata_file = settings.plaintables_path / "spaces.json"
        self._ensure_metadata_file()
    
    def _ensure_metadata_file(self):
        """Create spaces.json if it doesn't exist"""
        settings.plaintables_path.mkdir(parents=True, exist_ok=True)
        if not self.metadata_file.exists():
            self._save_metadata({})
    
    def _load_metadata(self) -> Dict:
        """Load spaces metadata from JSON"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_metadata(self, data: Dict):
        """Save spaces metadata to JSON"""
        with open(self.metadata_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ==================== CREATE ====================
    
    def create_space(self, name: str, description: Optional[str] = None) -> Dict:
        """
        Create a new space
        
        Args:
            name: Space name
            description: Optional description
            
        Returns:
            Space metadata dict
        """
        space_uuid = str(uuid4())
        
        # Create space metadata
        space_data = {
            "uuid": space_uuid,
            "name": name,
            "description": description,
            "artifacts": [],  # List of artifact IDs
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # Save to metadata file
        metadata = self._load_metadata()
        metadata[space_uuid] = space_data
        self._save_metadata(metadata)
        
        # Create empty plain table
        plain_table_manager.create_table(space_uuid)
        
        # Create empty vector store
        vector_store_manager.create_table(space_uuid)
        
        return self._enrich_space_data(space_data)
    
    # ==================== READ ====================
    
    def get_space(self, space_uuid: str) -> Optional[Dict]:
        """Get a space by UUID"""
        metadata = self._load_metadata()
        space_data = metadata.get(space_uuid)
        
        if space_data:
            return self._enrich_space_data(space_data)
        return None
    
    def list_spaces(self) -> List[Dict]:
        """List all spaces"""
        metadata = self._load_metadata()
        spaces = []
        
        for space_data in metadata.values():
            spaces.append(self._enrich_space_data(space_data))
        
        # Sort by created_at descending
        spaces.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return spaces
    
    def space_exists(self, space_uuid: str) -> bool:
        """Check if a space exists"""
        metadata = self._load_metadata()
        return space_uuid in metadata
    
    def _enrich_space_data(self, space_data: Dict) -> Dict:
        """Add computed fields to space data"""
        space_uuid = space_data["uuid"]
        
        # Get counts
        chunks = plain_table_manager.get_all_chunks(space_uuid)
        artifact_ids = set(c.get("artifact_id") for c in chunks if c.get("artifact_id"))
        
        return {
            **space_data,
            "artifact_count": len(artifact_ids),
            "chunk_count": len(chunks),
        }
    
    # ==================== UPDATE ====================
    
    def update_space(
        self,
        space_uuid: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Dict]:
        """Update space metadata"""
        metadata = self._load_metadata()
        
        if space_uuid not in metadata:
            return None
        
        if name is not None:
            metadata[space_uuid]["name"] = name
        if description is not None:
            metadata[space_uuid]["description"] = description
        
        self._save_metadata(metadata)
        return self._enrich_space_data(metadata[space_uuid])
    
    def add_artifact_to_space(self, space_uuid: str, artifact_id: str):
        """Track an artifact in space metadata"""
        metadata = self._load_metadata()
        
        if space_uuid in metadata:
            if artifact_id not in metadata[space_uuid]["artifacts"]:
                metadata[space_uuid]["artifacts"].append(artifact_id)
                self._save_metadata(metadata)
    
    def remove_artifact_from_space(self, space_uuid: str, artifact_id: str):
        """Remove artifact tracking from space metadata"""
        metadata = self._load_metadata()
        
        if space_uuid in metadata:
            if artifact_id in metadata[space_uuid]["artifacts"]:
                metadata[space_uuid]["artifacts"].remove(artifact_id)
                self._save_metadata(metadata)
    
    # ==================== DELETE ====================
    
    def delete_space(self, space_uuid: str) -> bool:
        """
        Delete a space and all its data
        
        Removes:
        - Space metadata
        - Plain table
        - Vector store
        """
        metadata = self._load_metadata()
        
        if space_uuid not in metadata:
            return False
        
        # Delete plain table
        plain_table_manager.delete_table(space_uuid)
        
        # Delete vector store
        vector_store_manager.delete_table(space_uuid)
        
        # Delete space directories
        plain_table_path = settings.plaintables_path / space_uuid
        vector_store_path = settings.vector_stores_path / space_uuid
        
        import shutil
        if plain_table_path.exists():
            shutil.rmtree(plain_table_path)
        if vector_store_path.exists():
            shutil.rmtree(vector_store_path)
        
        # Remove from metadata
        del metadata[space_uuid]
        self._save_metadata(metadata)
        
        return True


# ==================== GLOBAL INSTANCE ====================

space_service = SpaceService()
