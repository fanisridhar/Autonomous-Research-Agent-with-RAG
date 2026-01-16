"""Embedding service for generating text embeddings."""
from typing import List
from langchain_openai import OpenAIEmbeddings
from app.config import settings


class EmbeddingService:
    """Service for generating text embeddings."""
    
    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.embeddings = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
            )
        else:
            self.embeddings = None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        if not self.embeddings:
            raise ValueError("OpenAI API key not configured")
        
        return self.embeddings.embed_documents(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query text.
        
        Args:
            text: Query text string
            
        Returns:
            Embedding vector
        """
        if not self.embeddings:
            raise ValueError("OpenAI API key not configured")
        
        return self.embeddings.embed_query(text)


embedding_service = EmbeddingService()

