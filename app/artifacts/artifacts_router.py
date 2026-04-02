"""
Artifacts Router
API endpoints for uploading and managing artifacts (markdown files)
"""

from typing import Annotated, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from fastapi.responses import Response

from app.spaces.spaces_service import space_service
from app.utils.chunker import ChunkStrategy

from .artifacts_datamodel import (
    ChunkStrategyEnum,
    ArtifactResponse,
    ArtifactListResponse,
    ArtifactDeleteResponse,
)
from .artifacts_service import artifact_service


router = APIRouter(prefix="/spaces/{space_uuid}/artifacts", tags=["Artifacts"])


# ==================== UPLOAD ====================

@router.post(
    "",
    response_model=ArtifactResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a markdown file",
    description="Upload a single markdown file to a space. It is automatically chunked and stored."
)
async def upload_artifact(
    space_uuid: str,
    file: Annotated[UploadFile, File(description="Markdown file to upload (.md, .markdown, .txt)")],
    chunk_strategy: Annotated[ChunkStrategyEnum, Form(description="Chunking strategy")] = ChunkStrategyEnum.RECURSIVE,
    chunk_size: Annotated[Optional[int], Form(ge=100, le=5000, description="Custom chunk size in characters (default: 500)")] = None,
    chunk_overlap: Annotated[Optional[int], Form(ge=0, le=500, description="Custom chunk overlap in characters (default: 100)")] = None,
):
    """
    Upload one markdown file to a space.

    - File is read and decoded as UTF-8
    - Content is split into chunks using the selected strategy
    - Chunks are stored in the plain LanceDB table (FTS-indexed)

    Supported: .md · .markdown · .txt
    """
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )

    # Validate extension
    allowed_extensions = {".md", ".markdown", ".txt"}
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file.filename}. Allowed: {', '.join(allowed_extensions)}"
        )

    # Read content
    try:
        content_str = (await file.read()).decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not read file: {file.filename}. Ensure it is UTF-8 encoded."
        )

    strategy = ChunkStrategy(chunk_strategy.value)

    result = artifact_service.upload_artifact(
        space_uuid=space_uuid,
        file_name=file.filename,
        content=content_str,
        chunk_strategy=strategy,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    return result


# ==================== READ ====================

@router.get(
    "",
    response_model=ArtifactListResponse,
    summary="List artifacts",
    description="List all artifacts in a space"
)
def list_artifacts(space_uuid: str):
    """List all artifacts uploaded to a space."""
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )

    artifacts = artifact_service.list_artifacts(space_uuid)
    return ArtifactListResponse(artifacts=artifacts, total=len(artifacts))


# ==================== DOWNLOAD ====================

@router.get(
    "/{artifact_id}/download",
    summary="Download artifact",
    description="Download the reconstructed content of an artifact as a file"
)
def download_artifact(space_uuid: str, artifact_id: str):
    """
    Reconstruct and download an artifact from its stored chunks.

    Since raw files are not stored on disk (only chunks in LanceDB),
    the content is rebuilt by joining all chunks for the artifact.
    """
    if not space_service.space_exists(space_uuid):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Space not found: {space_uuid}")

    data = artifact_service.get_artifact_content(space_uuid, artifact_id)
    if not data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Artifact not found: {artifact_id}")

    return Response(
        content=data["content"],
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{data["file_name"]}"'}
    )


# ==================== DELETE ====================

@router.delete(
    "/{artifact_id}",
    response_model=ArtifactDeleteResponse,
    summary="Delete an artifact",
    description="Delete an artifact and all its chunks and embeddings"
)
def delete_artifact(space_uuid: str, artifact_id: str):
    """
    Delete an artifact and all associated data (chunks + vectors).

    This action is irreversible.
    """
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )

    if not artifact_service.artifact_exists(space_uuid, artifact_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found: {artifact_id}"
        )

    return artifact_service.delete_artifact(space_uuid, artifact_id)
