"""
Artifacts Router
API endpoints for uploading and managing artifacts (markdown files)
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, status
from fastapi.responses import Response

from app.spaces.spaces_service import space_service
from app.utils.chunker import ChunkStrategy

from .artifacts_datamodel import (
    ChunkStrategyEnum,
    ArtifactResponse,
    ArtifactListResponse,
    ArtifactDeleteResponse,
    UploadResponse,
)
from .artifacts_service import artifact_service


router = APIRouter(prefix="/spaces/{space_uuid}/artifacts", tags=["Artifacts"])


# ==================== UPLOAD ====================

@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload markdown file(s)",
    description="Upload one or more markdown files to a space. Files are automatically chunked and stored."
)
async def upload_artifacts(
    space_uuid: str,
    files: List[UploadFile] = File(..., description="Markdown files to upload"),
    chunk_strategy: ChunkStrategyEnum = Form(
        default=ChunkStrategyEnum.RECURSIVE,
        description="Chunking strategy to use"
    ),
    chunk_size: Optional[int] = Form(
        default=None,
        ge=100,
        le=5000,
        description="Custom chunk size (optional)"
    ),
    chunk_overlap: Optional[int] = Form(
        default=None,
        ge=0,
        le=500,
        description="Custom chunk overlap (optional)"
    ),
):
    """
    Upload markdown files to a space
    
    - Files are read and parsed
    - Content is split into chunks using selected strategy
    - Chunks are stored in plain table with FTS index
    
    Supported files: .md, .markdown, .txt
    """
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    # Validate files
    allowed_extensions = {".md", ".markdown", ".txt"}
    file_data_list = []
    
    for file in files:
        # Check extension
        file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type: {file.filename}. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Read content
        try:
            content = await file.read()
            content_str = content.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not read file: {file.filename}. Ensure it's UTF-8 encoded."
            )
        
        file_data_list.append({
            "file_name": file.filename,
            "content": content_str,
        })
    
    # Convert strategy enum to ChunkStrategy
    strategy = ChunkStrategy(chunk_strategy.value)
    
    # Upload and process files
    result = artifact_service.upload_multiple(
        space_uuid=space_uuid,
        files=file_data_list,
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
    """List all artifacts in a space"""
    # Validate space exists
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
    """Download artifact content reconstructed from chunks"""
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
    description="Delete an artifact and all its chunks/embeddings"
)
def delete_artifact(space_uuid: str, artifact_id: str):
    """
    Delete an artifact and all associated data
    
    ⚠️ This action is irreversible!
    """
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    # Validate artifact exists
    if not artifact_service.artifact_exists(space_uuid, artifact_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Artifact not found: {artifact_id}"
        )
    
    result = artifact_service.delete_artifact(space_uuid, artifact_id)
    return result
