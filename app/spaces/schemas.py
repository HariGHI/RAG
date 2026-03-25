"""
Spaces Schemas
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== REQUEST SCHEMAS ====================

class SpaceCreate(BaseModel):
    """Request body for creating a space"""
    name: str = Field(..., min_length=1, max_length=100, description="Space name")
    description: Optional[str] = Field(None, max_length=500, description="Space description")


# ==================== RESPONSE SCHEMAS ====================

class SpaceResponse(BaseModel):
    """Response for a single space"""
    uuid: str
    name: str
    description: Optional[str] = None
    artifact_count: int = 0
    chunk_count: int = 0
    created_at: str
    
    class Config:
        from_attributes = True


class SpaceListResponse(BaseModel):
    """Response for listing spaces"""
    spaces: List[SpaceResponse]
    total: int


class SpaceDeleteResponse(BaseModel):
    """Response for deleting a space"""
    uuid: str
    deleted: bool
    message: str
