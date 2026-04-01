"""
Retrieval Datamodels
Pydantic models for the retrieval step of the RAG pipeline.

Three search modes are supported:
  - VECTOR  — semantic similarity using the embedding vectors
  - FTS     — keyword-based full-text search on the plain table
  - HYBRID  — combination of both (recommended default)
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# ==================== ENUMS ====================

class RetrievalMode(str, Enum):
    """Retrieval modes"""
    VECTOR = "vector"      # Pure vector similarity search
    HYBRID = "hybrid"      # Combined vector + FTS
    FTS = "fts"            # Pure full-text search


# ==================== REQUEST SCHEMAS ====================

class RetrievalRequest(BaseModel):
    """Request body for retrieval"""
    query: str = Field(..., min_length=1, description="Search query")
    mode: RetrievalMode = Field(
        default=RetrievalMode.HYBRID,
        description="Retrieval mode: vector, hybrid, or fts"
    )
    limit: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of results"
    )
    artifact_ids: Optional[List[str]] = Field(
        default=None,
        description="Filter by specific artifact IDs"
    )


# ==================== RESPONSE SCHEMAS ====================

class RetrievalResult(BaseModel):
    """Single retrieval result"""
    chunk_id: str
    chunk: str
    title: Optional[str] = Field(default=None, description="Section title")
    parent_title: Optional[str] = Field(default=None, description="Parent section title")
    artifact_id: str
    file_name: str
    score: Optional[float] = Field(
        default=None,
        description="Relevance score (higher = more relevant)"
    )
    rank: int = Field(..., description="Result rank (1 = most relevant)")


class RetrievalResponse(BaseModel):
    """Response for retrieval"""
    query: str
    mode: RetrievalMode
    results: List[RetrievalResult]
    total: int
