"""
Spaces Router
API endpoints for managing spaces
"""

from fastapi import APIRouter, HTTPException, status

from .spaces_datamodel import (
    SpaceCreate,
    SpaceResponse,
    SpaceListResponse,
    SpaceDeleteResponse,
)
from .spaces_service import space_service


router = APIRouter(prefix="/spaces", tags=["Spaces"])


# ==================== CREATE ====================

@router.post(
    "",
    response_model=SpaceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new space",
    description="Create a new workspace for uploading artifacts and storing chunks"
)
def create_space(body: SpaceCreate):
    """
    Create a new space (workspace)
    
    A space contains:
    - Uploaded artifacts (markdown files)
    - Chunks (text segments)
    - Embeddings (vector representations)
    """
    space = space_service.create_space(
        name=body.name,
        description=body.description
    )
    return space


# ==================== READ ====================

@router.get(
    "",
    response_model=SpaceListResponse,
    summary="List all spaces",
    description="Get a list of all spaces with their metadata"
)
def list_spaces():
    """
    Return all spaces sorted by creation date (newest first).

    Each space includes computed counts for artifacts and chunks so the
    UI can show progress without additional requests.
    """
    spaces = space_service.list_spaces()
    return SpaceListResponse(spaces=spaces, total=len(spaces))


# ==================== DELETE ====================

@router.delete(
    "/{space_uuid}",
    response_model=SpaceDeleteResponse,
    summary="Delete a space",
    description="Delete a space and all its data (artifacts, chunks, embeddings)"
)
def delete_space(space_uuid: str):
    """
    Delete a space and all associated data
    
    ⚠️ This action is irreversible!
    """
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    deleted = space_service.delete_space(space_uuid)
    
    return SpaceDeleteResponse(
        uuid=space_uuid,
        deleted=deleted,
        message="Space deleted successfully" if deleted else "Failed to delete space"
    )
