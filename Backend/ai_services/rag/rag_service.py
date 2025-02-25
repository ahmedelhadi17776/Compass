from typing import Dict, List, Optional
import chromadb
from chromadb.config import Settings
from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.ai_services.llm.llm_service import LLMService
from Backend.ai_services.embedding.embedding_service import EmbeddingService
from Backend.ai_services.base.ai_service_base import AIServiceBase
from Backend.data_layer.cache.ai_cache import cache_ai_result, get_cached_ai_result

logger = get_logger(__name__)

class RAGService(AIServiceBase):
    def __init__(self):
        super().__init__("rag")
        self._initialize_chromadb()
        self.llm_service = LLMService()
        self.embedding_service = EmbeddingService()

    def _initialize_chromadb(self) -> None:
        """Initialize ChromaDB with error handling."""
        try:
            self.client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=settings.CHROMA_DB_PATH
            ))
            self.collection = self.client.get_or_create_collection("tasks")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {str(e)}")
            raise

    async def query_knowledge_base(
        self,
        query: str,
        limit: int = 5,
        context_window: int = 1000,
        normalize: bool = True,
        filters: Optional[Dict] = None
    ) -> Dict:
        """Query knowledge base with enhanced filtering and caching."""
        try:
            # Check cache first
            cache_key = f"rag_query:{hash(query)}"
            if cached_result := await get_cached_ai_result(cache_key):
                return cached_result

            query_embedding = await self.embedding_service.get_embedding(
                query,
                normalize=normalize
            )
            
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=filters
            )
            
            context = "\n".join([doc for doc in results["documents"][0]])
            
            response = await self.llm_service.generate_response(
                prompt=query,
                context={"reference_docs": context[:context_window]}
            )
            
            result = {
                "answer": response.get("text", ""),
                "sources": results["metadatas"][0],
                "confidence": response.get("confidence", 0.0),
                "embedding_dimension": len(query_embedding)
            }

            # Cache the result
            await cache_ai_result(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"RAG query error: {str(e)}")
            raise

    async def add_to_knowledge_base(
        self,
        content: Union[str, List[str]],
        metadata: Union[Dict, List[Dict]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> bool:
        """Add content to knowledge base with batch support."""
        try:
            if isinstance(content, str):
                content = [content]
                metadata = [metadata]

            embeddings = await self.embedding_service.get_embedding(
                content,
                normalize=normalize,
                batch_size=batch_size
            )
            
            ids = [meta.get("id", str(i + len(self.collection))) 
                  for i, meta in enumerate(metadata)]
            
            self.collection.add(
                embeddings=embeddings,
                documents=content,
                metadatas=metadata,
                ids=ids
            )
            return True
        except Exception as e:
            logger.error(f"Error adding to knowledge base: {str(e)}")
            return False

    async def update_document(
        self,
        doc_id: str,
        content: str,
        metadata: Dict,
        normalize: bool = True
    ) -> bool:
        """Update existing document in knowledge base."""
        try:
            embedding = await self.embedding_service.get_embedding(
                content,
                normalize=normalize
            )
            
            self.collection.update(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata]
            )
            return True
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            return False

    async def delete_document(self, doc_id: str) -> bool:
        """Delete document from knowledge base."""
        try:
            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False

    async def get_collection_stats(self) -> Dict:
        """Get collection statistics."""
        try:
            return {
                "count": self.collection.count(),
                "dimension": self.embedding_service.get_dimension(),
                "name": self.collection.name
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            raise