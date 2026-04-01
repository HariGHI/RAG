"""
Retrieval Router
API endpoints for retrieving relevant chunks
"""

from fastapi import APIRouter, HTTPException, status

from app.spaces.spaces_service import space_service

from .retrieval_datamodel import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResult,
    RetrievalMode,
)
from .retrieval_service import retrieval_service


router = APIRouter(prefix="/spaces/{space_uuid}/retrieve", tags=["Retrieval"])


def _build_results(results: list) -> list[RetrievalResult]:
    """Convert raw service dicts into typed RetrievalResult Pydantic models."""
    return [
        RetrievalResult(
            chunk_id=r.get("chunk_id", ""),
            chunk=r.get("chunk", ""),
            artifact_id=r.get("artifact_id", ""),
            file_name=r.get("file_name", ""),
            score=r.get("score"),
            rank=r.get("rank", 0),
        )
        for r in results
    ]


# ==================== RETRIEVE ====================

@router.post(
    "",
    response_model=RetrievalResponse,
    summary="Retrieve relevant chunks",
    description="Search for relevant chunks using vector, FTS, or hybrid search"
)
def retrieve(space_uuid: str, body: RetrievalRequest):
    """
    Retrieve relevant chunks based on query
    
    **Modes:**
    - `vector`: Pure semantic similarity search (requires embeddings)
    - `fts`: Pure keyword-based full-text search
    - `hybrid`: Combined vector + FTS (recommended)
    
    **Usage:**
    1. Upload artifacts to create chunks
    2. Embed chunks to enable vector search
    3. Use this endpoint to retrieve relevant chunks
    """
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    # Perform retrieval
    results = retrieval_service.retrieve(
        space_uuid=space_uuid,
        query=body.query,
        mode=body.mode,
        limit=body.limit,
        artifact_ids=body.artifact_ids
    )
    
    retrieval_results = _build_results(results)
    return RetrievalResponse(
        query=body.query,
        mode=body.mode,
        results=retrieval_results,
        total=len(retrieval_results),
    )


# ==================== QUICK SEARCH ENDPOINTS ====================

@router.get(
    "/vector",
    response_model=RetrievalResponse,
    summary="Vector search",
    description="Quick vector similarity search"
)
def vector_search(
    space_uuid: str,
    q: str,
    limit: int = 5
):
    """Quick vector search endpoint"""
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    results = retrieval_service.retrieve(
        space_uuid=space_uuid,
        query=q,
        mode=RetrievalMode.VECTOR,
        limit=limit
    )
    
    retrieval_results = _build_results(results)
    return RetrievalResponse(
        query=q,
        mode=RetrievalMode.VECTOR,
        results=retrieval_results,
        total=len(retrieval_results),
    )


@router.get(
    "/fts",
    response_model=RetrievalResponse,
    summary="Full-text search",
    description="Quick FTS keyword search"
)
def fts_search(
    space_uuid: str,
    q: str,
    limit: int = 5
):
    """Quick FTS search endpoint"""
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    results = retrieval_service.retrieve(
        space_uuid=space_uuid,
        query=q,
        mode=RetrievalMode.FTS,
        limit=limit
    )
    
    retrieval_results = _build_results(results)
    return RetrievalResponse(
        query=q,
        mode=RetrievalMode.FTS,
        results=retrieval_results,
        total=len(retrieval_results),
    )


@router.get(
    "/hybrid",
    response_model=RetrievalResponse,
    summary="Hybrid search",
    description="Quick hybrid (vector + FTS) search"
)
def hybrid_search(
    space_uuid: str,
    q: str,
    limit: int = 5
):
    """Quick hybrid search endpoint"""
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    results = retrieval_service.retrieve(
        space_uuid=space_uuid,
        query=q,
        mode=RetrievalMode.HYBRID,
        limit=limit
    )
    
    retrieval_results = _build_results(results)
    return RetrievalResponse(
        query=q,
        mode=RetrievalMode.HYBRID,
        results=retrieval_results,
        total=len(retrieval_results),
    )
