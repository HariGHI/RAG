"""
Vectors Router
API endpoints for embedding and managing vectors
"""

from fastapi import APIRouter, HTTPException, status

from app.spaces.spaces_service import space_service

from .vectors_datamodel import (
    EmbedRequest,
    EmbedResponse,
    VectorInfo,
    VectorListResponse,
)
from .vectors_service import vector_service


router = APIRouter(prefix="/spaces/{space_uuid}/vectors", tags=["Vectors"])


# ==================== EMBED ====================

@router.post(
    "/embed",
    response_model=EmbedResponse,
    summary="Embed chunks",
    description="Generate embeddings for chunks in the space"
)
def embed_chunks(space_uuid: str, body: EmbedRequest = EmbedRequest()):
    """
    Generate embeddings for chunks
    
    - If artifact_ids is provided, only embeds those artifacts
    - If re_embed is True, re-embeds chunks that already have vectors
    - Uses all-MiniLM-L6-v2 model (384 dimensions)
    """
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    result = vector_service.embed_space(
        space_uuid=space_uuid,
        artifact_ids=body.artifact_ids,
        re_embed=body.re_embed
    )
    
    return EmbedResponse(**result)


# ==================== READ ====================

@router.get(
    "",
    response_model=VectorListResponse,
    summary="List vectors",
    description="List all vectors in a space (without actual vector data)"
)
def list_vectors(space_uuid: str):
    """List all vectors in a space"""
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    vectors = vector_service.list_vectors(space_uuid)
    
    vector_infos = [
        VectorInfo(
            chunk_id=v.get("chunk_id", ""),
            chunk=v.get("chunk", ""),
            artifact_id=v.get("artifact_id", ""),
            file_name=v.get("file_name", ""),
            has_vector=True
        )
        for v in vectors
    ]
    
    return VectorListResponse(vectors=vector_infos, total=len(vector_infos))


