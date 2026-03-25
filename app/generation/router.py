"""
Generation Router
API endpoints for LLM generation
"""

from fastapi import APIRouter, HTTPException, status

from app.spaces.service import space_service

from .schemas import (
    GenerateRequest,
    GenerateResponse,
    SummarizeRequest,
    SummarizeResponse,
    CompareRequest,
    CompareResponse,
    SourceInfo,
)
from .service import generation_service


router = APIRouter(prefix="/spaces/{space_uuid}/generate", tags=["Generation"])


# ==================== RAG GENERATION ====================

@router.post(
    "",
    response_model=GenerateResponse,
    summary="Generate answer (RAG)",
    description="Generate an answer using RAG: retrieve context, augment prompt, generate response"
)
def generate(space_uuid: str, body: GenerateRequest):
    """
    Generate answer using RAG pipeline
    
    **Flow:**
    1. Retrieve relevant chunks based on query
    2. Augment prompt with retrieved context
    3. Generate answer using Ollama LLM
    
    **Requirements:**
    - Ollama must be running (`ollama serve`)
    - Model must be pulled (`ollama pull llama3.2`)
    """
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    # Check Ollama
    if not generation_service.check_ollama():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is not running. Please start it with 'ollama serve'"
        )
    
    try:
        result = generation_service.generate(
            space_uuid=space_uuid,
            query=body.query,
            retrieval_mode=body.retrieval_mode,
            context_limit=body.context_limit,
            artifact_ids=body.artifact_ids,
            system_prompt=body.system_prompt,
            temperature=body.temperature
        )
        
        return GenerateResponse(
            query=result["query"],
            answer=result["answer"],
            sources=[SourceInfo(**s) for s in result["sources"]],
            model=result["model"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


# ==================== SUMMARIZATION ====================

@router.post(
    "/summarize",
    response_model=SummarizeResponse,
    summary="Summarize documents",
    description="Generate a summary of documents in the space"
)
def summarize(space_uuid: str, body: SummarizeRequest = SummarizeRequest()):
    """
    Summarize documents
    
    **Styles:**
    - `concise`: Brief 2-3 paragraph overview
    - `detailed`: Comprehensive summary
    - `bullet_points`: Key points as bullets
    """
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    # Check Ollama
    if not generation_service.check_ollama():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is not running. Please start it with 'ollama serve'"
        )
    
    try:
        result = generation_service.summarize(
            space_uuid=space_uuid,
            artifact_ids=body.artifact_ids,
            max_chunks=body.max_chunks,
            style=body.style
        )
        
        return SummarizeResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summarization failed: {str(e)}"
        )


# ==================== COMPARISON ====================

@router.post(
    "/compare",
    response_model=CompareResponse,
    summary="Compare documents",
    description="Compare multiple documents to find similarities and differences"
)
def compare(space_uuid: str, body: CompareRequest):
    """
    Compare multiple documents
    
    Identifies:
    - Overall comparison
    - Similarities between documents
    - Differences between documents
    
    Optionally focus on a specific aspect
    """
    # Validate space exists
    if not space_service.space_exists(space_uuid):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space not found: {space_uuid}"
        )
    
    # Check Ollama
    if not generation_service.check_ollama():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Ollama is not running. Please start it with 'ollama serve'"
        )
    
    try:
        result = generation_service.compare(
            space_uuid=space_uuid,
            artifact_ids=body.artifact_ids,
            focus=body.focus
        )
        
        return CompareResponse(**result)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Comparison failed: {str(e)}"
        )
