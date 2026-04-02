"""
RAG Summarizer API
Minimal orchestrator — mounts the three RAG module routers plus support routers.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from contextlib import asynccontextmanager

import ollama
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logger import log_step, log_success, log_warning

# ── RAG pipeline modules ──────────────────────────────────────────────────────
from app.retrieval.retrieval_router import router as retrieval_router
from app.augmentation.augmentation_router import router as augmentation_router
from app.generation.generation_router import router as generation_router

# ── Supporting modules ────────────────────────────────────────────────────────
from app.spaces.spaces_router import router as spaces_router
from app.artifacts.artifacts_router import router as artifacts_router
from app.vectors.vectors_router import router as vectors_router


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n" + "=" * 60)
    print("  RAG SUMMARIZER  -  Starting up")
    print("=" * 60)

    settings.ensure_directories()
    log_success("Storage directories ready")
    log_step("LLM", f"Model: {settings.ollama_model}")
    log_step("Embeddings", f"Model: {settings.embedding_model}")

    try:
        ollama.list()
        log_success("Ollama connected")
    except Exception:
        log_warning("Ollama not reachable — start with: ollama serve")

    print(f"\n  Ready at http://localhost:{settings.port}")
    print(f"  Docs   at http://localhost:{settings.port}/docs")
    print("=" * 60 + "\n")

    yield  # app runs here


# ==================== APP ====================

app = FastAPI(
    title="RAG Summarizer",
    description="""
## RAG Pipeline API

Three-stage pipeline — each stage has its own module:

| Stage | Module | Endpoint prefix |
|---|---|---|
| 1 | **Retrieval** | `/spaces/{uuid}/retrieve` |
| 2 | **Augmentation** | `/spaces/{uuid}/augment` |
| 3 | **Generation** | `/spaces/{uuid}/generate` |

### Supporting endpoints
- **Spaces** — `/spaces` — create & manage workspaces
- **Artifacts** — `/spaces/{uuid}/artifacts` — upload markdown files
- **Vectors** — `/spaces/{uuid}/vectors` — manage embeddings

Built for the *"Bootstrap of RAG"* workshop.
    """,
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== ROUTERS ====================

# RAG pipeline
app.include_router(retrieval_router)
app.include_router(augmentation_router)
app.include_router(generation_router)

# Supporting
app.include_router(spaces_router)
app.include_router(artifacts_router)
app.include_router(vectors_router)


# ==================== HEALTH ====================

@app.get("/health", tags=["Health"])
def health():
    """Health check — reports Ollama connectivity"""
    try:
        ollama.list()
        ollama_status = "ok"
    except Exception:
        ollama_status = "not running"

    return {
        "status": "ok" if ollama_status == "ok" else "degraded",
        "ollama": ollama_status,
        "model": settings.ollama_model,
        "embedding_model": settings.embedding_model,
    }


# ==================== STATIC UI ====================

@app.get("/", include_in_schema=False)
def root():
    index_path = Path("static/index.html")
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "RAG Summarizer API", "docs": "/docs"}


static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


# ==================== ENTRYPOINT ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=True)
