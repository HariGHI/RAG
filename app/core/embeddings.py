"""
Embeddings Module
Wrapper for Sentence Transformers to generate text embeddings
"""

from typing import List
from sentence_transformers import SentenceTransformer

from .config import settings


class EmbeddingModel:
    """
    Wrapper for Sentence Transformers embedding model
    Default: all-MiniLM-L6-v2 (384 dimensions, fast, good quality)
    """
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern - load model only once"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self._load_model()
    
    def _load_model(self):
        """Load the embedding model"""
        print(f"📦 Loading embedding model: {settings.embedding_model}")
        self._model = SentenceTransformer(settings.embedding_model)
        self._dimension = self._model.get_sentence_embedding_dimension()
        print(f"✅ Model loaded! Dimension: {self._dimension}")
    
    @property
    def dimension(self) -> int:
        """Get embedding dimension"""
        return self._dimension
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text string
            
        Returns:
            List of floats (embedding vector)
        """
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing)
        
        Args:
            texts: List of input text strings
            
        Returns:
            List of embedding vectors
        """
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    def embed_query(self, query: str) -> List[float]:
        """
        Generate embedding for a search query
        Same as embed_text, but named for clarity
        
        Args:
            query: Search query string
            
        Returns:
            Query embedding vector
        """
        return self.embed_text(query)
    
    def similarity(self, text1: str, text2: str) -> float:
        """
        Calculate cosine similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score (0 to 1)
        """
        from sentence_transformers import util
        
        emb1 = self._model.encode(text1, convert_to_tensor=True)
        emb2 = self._model.encode(text2, convert_to_tensor=True)
        
        similarity = util.cos_sim(emb1, emb2)
        return float(similarity[0][0])


# ==================== GLOBAL INSTANCE ====================

embedding_model = EmbeddingModel()
