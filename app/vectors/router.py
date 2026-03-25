"""
Vectors Router
API endpoints for embedding and managing vectors
"""

from fastapi import APIRouter, HTTPException, status

from app.spaces.service import space_service

from .schemas import (
    EmbedRequest,
    EmbedResponse,
    VectorCreate,
    VectorUpdate,
    VectorInfo,
    VectorListResponse,
    VectorDeleteResponse,
)
from .service import vector_service


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


# ==================== CREATE ====================

@router.post(
    "",
    response_model=VectorInfo,
    status_code=status.HTTP_201_CREATED,
    summary="Create vector",
    description="Manually create a vector for a chunk"
)
def create_vector(space_uuid: str, body: VectorCreate):
    """
    Manually create a vector
    
    Generates embedding and stores in vector store
    """
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    # Check if vector already exists
    if vector_service.vector_exists(space_uuid, body.chunk_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Vector already exists for chunk: {body.chunk_id}"
        )
    
    result = vector_service.create_vector(
        space_uuid=space_uuid,
        chunk_id=body.chunk_id,
        chunk=body.chunk,
        artifact_id=body.artifact_id,
        file_name=body.file_name
    )
    
    return VectorInfo(**result)


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


# ==================== UPDATE ====================

@router.put(
    "/{chunk_id}",
    response_model=VectorInfo,
    summary="Update vector",
    description="Re-embed a vector with new text"
)
def update_vector(space_uuid: str, chunk_id: str, body: VectorUpdate = VectorUpdate()):
    """
    Update (re-embed) a vector
    
    If new chunk text is provided, uses that. Otherwise, fetches from plain table.
    """
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    # Check vector exists
    if not vector_service.vector_exists(space_uuid, chunk_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vector not found for chunk: {chunk_id}"
        )
    
    success = vector_service.update_vector(
        space_uuid=space_uuid,
        chunk_id=chunk_id,
        new_chunk=body.chunk
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update vector"
        )
    
    # Return updated info
    vectors = vector_service.list_vectors(space_uuid)
    for v in vectors:
        if v.get("chunk_id") == chunk_id:
            return VectorInfo(
                chunk_id=v.get("chunk_id", ""),
                chunk=v.get("chunk", ""),
                artifact_id=v.get("artifact_id", ""),
                file_name=v.get("file_name", ""),
                has_vector=True
            )
    
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Vector updated but could not retrieve info"
    )


# ==================== DELETE ====================

@router.delete(
    "/{chunk_id}",
    response_model=VectorDeleteResponse,
    summary="Delete vector",
    description="Delete a vector by chunk ID"
)
def delete_vector(space_uuid: str, chunk_id: str):
    """
    Delete a vector
    
    Note: This only deletes the vector, not the chunk in plain table
    """
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    # Check vector exists
    if not vector_service.vector_exists(space_uuid, chunk_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vector not found for chunk: {chunk_id}"
        )
    
    deleted = vector_service.delete_vector(space_uuid, chunk_id)
    
    return VectorDeleteResponse(
        chunk_id=chunk_id,
        deleted=deleted,
        message="Vector deleted successfully" if deleted else "Failed to delete vector"
    )
