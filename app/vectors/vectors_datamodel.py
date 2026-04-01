"""
Vectors Datamodels
Pydantic models for the vectorization step of the RAG pipeline.

The vectorization step converts text chunks into numerical embeddings
so they can be searched by semantic similarity.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# ==================== REQUEST SCHEMAS ====================

class EmbedRequest(BaseModel):
    """
    Request body for the embed endpoint.

    By default, embeds every chunk in the space that does not yet have
    a vector. Set re_embed=True to regenerate existing vectors (useful
    after changing the embedding model or chunk content).
    """
    artifact_ids: Optional[List[str]] = Field(
        default=None,
        description="Specific artifact IDs to embed. If None, embeds all un-embedded chunks."
    )
    re_embed: bool = Field(
        default=False,
        description="If True, re-embed chunks that already have vectors."
    )


# ==================== RESPONSE SCHEMAS ====================

class VectorInfo(BaseModel):
    """
    Metadata for a single vector entry.

    The actual embedding (list of 384 floats) is intentionally excluded
    from API responses — it is only used internally for similarity search.
    """
    chunk_id: str
    chunk: str
    artifact_id: str
    file_name: str
    has_vector: bool = True


class VectorListResponse(BaseModel):
    """Response for listing all vectors in a space"""
    vectors: List[VectorInfo]
    total: int


class EmbedResponse(BaseModel):
    """
    Summary returned after running the embed step.

    chunks_embedded: how many new embeddings were created.
    chunks_skipped:  how many chunks were already embedded (skipped).
    """
    space_uuid: str
    chunks_embedded: int
    chunks_skipped: int
    message: str
