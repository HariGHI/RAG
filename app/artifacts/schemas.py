"""
Artifacts Schemas
Pydantic models for file upload request/response
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

from app.utils.chunker import ChunkStrategy


# ==================== ENUMS ====================

class ChunkStrategyEnum(str, Enum):
    """Chunking strategies available via API"""
    FIXED_SIZE = "fixed_size"
    PARAGRAPH = "paragraph"
    SENTENCE = "sentence"
    MARKDOWN_HEADER = "markdown_header"
    SEMANTIC = "semantic"  # NEW: Smart markdown-aware chunking (recommended)
    RECURSIVE = "recursive"


# ==================== REQUEST SCHEMAS ====================

class ArtifactUploadConfig(BaseModel):
    """Configuration for artifact upload and chunking"""
    chunk_strategy: ChunkStrategyEnum = Field(
        default=ChunkStrategyEnum.SEMANTIC,  # Changed default to semantic
        description="Strategy for splitting document into chunks. 'semantic' (recommended) uses markdown-aware parsing with title hierarchy."
    )
    chunk_size: Optional[int] = Field(
        default=None,
        ge=100,
        le=5000,
        description="Maximum chunk size in characters"
    )
    chunk_overlap: Optional[int] = Field(
        default=None,
        ge=0,
        le=500,
        description="Overlap between chunks in characters"
    )


# ==================== RESPONSE SCHEMAS ====================

class ChunkInfo(BaseModel):
    """Info about a single chunk"""
    chunk_id: str
    title: Optional[str] = Field(default=None, description="Section title this chunk belongs to")
    parent_title: Optional[str] = Field(default=None, description="Parent section title")
    preview: str = Field(..., description="First 100 chars of chunk")
    length: int


class ArtifactResponse(BaseModel):
    """Response for a single artifact"""
    artifact_id: str
    file_name: str
    space_uuid: str
    chunk_count: int
    chunk_strategy: str
    chunks: List[ChunkInfo] = []


class ArtifactListResponse(BaseModel):
    """Response for listing artifacts"""
    artifacts: List[ArtifactResponse]
    total: int


class ArtifactDeleteResponse(BaseModel):
    """Response for deleting an artifact"""
    artifact_id: str
    file_name: str
    deleted: bool
    chunks_deleted: int
    message: str


class UploadResponse(BaseModel):
    """Response after uploading file(s)"""
    space_uuid: str
    artifacts: List[ArtifactResponse]
    total_chunks: int
    message: str
