"""
Augmentation Schemas
Pydantic models for prompt augmentation
"""

from pydantic import BaseModel, Field
from typing import Optional, List

from app.retrieval.schemas import RetrievalMode


class AugmentRequest(BaseModel):
    """Request body for augmentation"""
    query: str = Field(..., min_length=1, description="User query")
    context_limit: int = Field(default=5, ge=1, le=20, description="Max chunks to use as context")
    retrieval_mode: RetrievalMode = Field(default=RetrievalMode.HYBRID)
    system_prompt: Optional[str] = Field(default=None, description="Custom system prompt")
    artifact_ids: Optional[List[str]] = Field(default=None, description="Filter to specific artifacts")


class SourcePreview(BaseModel):
    """A source chunk used in the augmented context"""
    file: str
    title: Optional[str] = None
    parent_title: Optional[str] = None
    preview: str


class AugmentResponse(BaseModel):
    """The augmented prompt ready for inspection or LLM input"""
    query: str
    context: str
    system_prompt: str
    user_prompt: str
    sources: List[SourcePreview]
    chunk_count: int
