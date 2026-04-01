"""
Generation Datamodels
Pydantic models for the generation step of the RAG pipeline.

Generation is the final stage — it takes the augmented prompt built by
the augmentation service and calls the local Ollama LLM to produce an
answer or summary grounded in the retrieved document context.
"""

from pydantic import BaseModel, Field
from typing import Optional, List

from app.retrieval.retrieval_datamodel import RetrievalMode


# ==================== REQUEST SCHEMAS ====================

class GenerateRequest(BaseModel):
    """Request body for generation"""
    query: str = Field(..., min_length=1, description="User question or prompt")
    retrieval_mode: RetrievalMode = Field(
        default=RetrievalMode.HYBRID,
        description="How to retrieve context"
    )
    context_limit: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Max chunks to use as context"
    )
    artifact_ids: Optional[List[str]] = Field(
        default=None,
        description="Filter retrieval to specific artifacts"
    )
    system_prompt: Optional[str] = Field(
        default=None,
        description="Custom system prompt (optional)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0=deterministic, 2=creative)"
    )


class SummarizeRequest(BaseModel):
    """Request body for summarization"""
    artifact_ids: Optional[List[str]] = Field(
        default=None,
        description="Artifacts to summarize (None = all)"
    )
    max_chunks: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Max chunks to include in summary"
    )
    style: str = Field(
        default="concise",
        description="Summary style: concise, detailed, bullet_points"
    )


# ==================== RESPONSE SCHEMAS ====================

class SourceInfo(BaseModel):
    """Info about a source artifact used in generation"""
    artifact_id: str
    file_name: str
    preview: str = Field(..., description="First 100 chars")


class GenerateResponse(BaseModel):
    """Response from generation"""
    query: str
    answer: str
    sources: List[SourceInfo]
    model: str


class SummarizeResponse(BaseModel):
    """Response from summarization"""
    summary: str
    artifacts_included: List[str]
    chunks_used: int
    model: str


