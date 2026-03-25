"""
Augmentation Router
Exposes the augmentation step for inspection and debugging.

Useful to see exactly what context and prompt will be sent to the LLM
before calling the generation endpoint.
"""

from fastapi import APIRouter, HTTPException, status

from app.spaces.service import space_service

from .schemas import AugmentRequest, AugmentResponse, SourcePreview
from .service import augmentation_service


router = APIRouter(prefix="/spaces/{space_uuid}/augment", tags=["Augmentation"])


@router.post(
    "",
    response_model=AugmentResponse,
    summary="Build augmented prompt",
    description=(
        "Retrieve relevant context and assemble the augmented prompt. "
        "Use this to inspect what the LLM will receive before calling /generate."
    ),
)
def augment(space_uuid: str, body: AugmentRequest):
    """
    Augmentation pipeline: retrieve context → build prompt.

    Returns the full system prompt, user prompt, and source list so you can
    debug or preview what gets sent to the LLM.
    """
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}",
        )

    result = augmentation_service.augment(
        space_uuid=space_uuid,
        query=body.query,
        retrieval_mode=body.retrieval_mode,
        context_limit=body.context_limit,
        system_prompt=body.system_prompt,
        artifact_ids=body.artifact_ids,
    )

    return AugmentResponse(
        query=result["query"],
        context=result["context"],
        system_prompt=result["system_prompt"],
        user_prompt=result["user_prompt"],
        sources=[SourcePreview(**s) for s in result["sources"]],
        chunk_count=result["chunk_count"],
    )
