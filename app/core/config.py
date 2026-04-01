"""
Application Configuration
Central settings object loaded from environment variables (or .env file).

Override any default by setting the corresponding env variable, e.g.:
    OLLAMA_MODEL=llama3.2 python -m uvicorn app.main:app
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings with sensible defaults for local development.

    Groups:
      Server       — host, port, debug flag
      Storage      — local filesystem paths for LanceDB tables and uploads
      Embeddings   — SentenceTransformer model name and its stable UUID
      LLM (Ollama) — Ollama base URL and model name
      Chunking     — default chunk_size and chunk_overlap in characters
    """
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Storage Paths
    plaintables_path: Path = Path("./fs/plaintables")
    vector_stores_path: Path = Path("./fs/vector_stores")
    uploads_path: Path = Path("./uploads")
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_model_id: str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"  # UUID for all-MiniLM-L6-v2
    
    # LLM (Ollama)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 100
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def ensure_directories(self):
        """
        Create all required storage directories if they don't already exist.

        Called once at application startup (lifespan). Directories are:
          fs/plaintables/  — LanceDB plain tables (chunks + FTS index)
          fs/vector_stores/ — LanceDB vector stores (embeddings)
          uploads/         — raw uploaded files (currently unused but reserved)
        """
        self.plaintables_path.mkdir(parents=True, exist_ok=True)
        self.vector_stores_path.mkdir(parents=True, exist_ok=True)
        self.uploads_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
