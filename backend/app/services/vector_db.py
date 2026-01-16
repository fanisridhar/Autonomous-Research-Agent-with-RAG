"""Vector database service for storing and retrieving embeddings."""
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional, Tuple
from app.config import settings
import uuid


class VectorDBService:
    """Service for managing vector database operations."""
    
    def __init__(self):
        self.db_type = settings.VECTOR_DB_TYPE
        if self.db_type == "chroma":
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False),
            )
            self.collection_name = "research_documents"
            self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure collection exists."""
        try:
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        except Exception as e:
            # Create new collection if get fails
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict],
        ids: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Add documents to vector database.
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: Optional list of IDs (generated if not provided)
            
        Returns:
            List of generated IDs
        """
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]
        
        if self.db_type == "chroma":
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
        
        return ids
    
    def query(
        self,
        query_texts: List[str],
        n_results: int = 5,
        filter_dict: Optional[Dict] = None,
    ) -> Dict:
        """
        Query vector database for similar documents.
        
        Args:
            query_texts: List of query texts to search (will be embedded if embedding_fn is set)
            n_results: Number of results to return
            filter_dict: Optional filter dictionary (e.g., {"project_id": 1})
            
        Returns:
            Dictionary with 'ids', 'documents', 'metadatas', 'distances'
        """
        if self.db_type == "chroma":
            # ChromaDB will use embedding_fn to embed query_texts automatically
            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=filter_dict,
            )
            return {
                "ids": results["ids"][0] if results["ids"] else [],
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else [],
            }
        return {"ids": [], "documents": [], "metadatas": [], "distances": []}
    
    def delete(self, ids: List[str]):
        """
        Delete documents by IDs.
        
        Args:
            ids: List of IDs to delete
        """
        if self.db_type == "chroma":
            self.collection.delete(ids=ids)
    
    def delete_by_metadata(self, filter_dict: Dict):
        """
        Delete documents by metadata filter.
        
        Args:
            filter_dict: Filter dictionary
        """
        if self.db_type == "chroma":
            # Get IDs matching filter
            results = self.collection.get(where=filter_dict)
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        if self.db_type == "chroma":
            count = self.collection.count()
            return {"count": count, "type": self.db_type}
        return {"count": 0, "type": self.db_type}


vector_db_service = VectorDBService()

