"""
Vectors Schemas
Pydantic models for embedding and vector operations
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# ==================== REQUEST SCHEMAS ====================

class EmbedRequest(BaseModel):
    """Request body for embedding chunks"""
    artifact_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific artifact IDs to embed. If None, embeds all chunks in space."
    )
    re_embed: bool = Field(
        default=False,
        description="If True, re-embed chunks that already have vectors"
    )


class VectorCreate(BaseModel):
    """Request body for manually creating a vector"""
    chunk_id: str = Field(..., description="Chunk ID to link to")
    chunk: str = Field(..., description="Chunk text content")
    artifact_id: str = Field(..., description="Artifact ID")
    file_name: str = Field(..., description="Source file name")


class VectorUpdate(BaseModel):
    """Request body for updating a vector (re-embed)"""
    chunk: Optional[str] = Field(
        default=None,
        description="New chunk text. If provided, vector is regenerated."
    )


# ==================== RESPONSE SCHEMAS ====================

class VectorInfo(BaseModel):
    """Info about a single vector (without the actual vector data)"""
    chunk_id: str
    chunk: str
    artifact_id: str
    file_name: str
    has_vector: bool = True


class VectorListResponse(BaseModel):
    """Response for listing vectors"""
    vectors: List[VectorInfo]
    total: int


class EmbedResponse(BaseModel):
    """Response after embedding chunks"""
    space_uuid: str
    chunks_embedded: int
    chunks_skipped: int
    message: str


class VectorDeleteResponse(BaseModel):
    """Response for deleting a vector"""
    chunk_id: str
    deleted: bool
    message: str
