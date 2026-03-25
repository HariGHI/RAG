"""
Application Configuration
Loads settings from environment variables
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
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
    
    # LLM (Ollama)
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def ensure_directories(self):
        """Create storage directories if they don't exist"""
        self.plaintables_path.mkdir(parents=True, exist_ok=True)
        self.vector_stores_path.mkdir(parents=True, exist_ok=True)
        self.uploads_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
