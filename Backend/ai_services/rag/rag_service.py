from typing import Dict, List, Optional, Union, Any, cast
import chromadb
from chromadb.config import Settings
from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.ai_services.llm.llm_service import LLMService
from Backend.ai_services.embedding.embedding_service import EmbeddingService
from Backend.ai_services.base.ai_service_base import AIServiceBase
from Backend.data_layer.cache.ai_cache import cache_ai_result, get_cached_ai_result
from Backend.data_layer.vector_db.chroma_client import ChromaClient

logger = get_logger(__name__)


class RAGService(AIServiceBase):
    def __init__(self):
        super().__init__("rag")
        # Use the centralized ChromaClient instance
        self.chroma_client = ChromaClient()
        self.client = self.chroma_client.client
        self.collection = self.chroma_client.collection
        self.llm_service = LLMService()
        self.embedding_service = EmbeddingService()

    async def query_knowledge_base(
        self,
        query: str,
        limit: int = 5,
        context_window: int = 1000,
        normalize: bool = True,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Query knowledge base with enhanced filtering and caching."""
        try:
            # Check cache first
            cache_key = f"rag_query:{hash(query)}"
            if cached_result := await get_cached_ai_result(cache_key):
                return cached_result

            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return {
                    "answer": "Unable to query knowledge base: database not initialized",
                    "sources": [],
                    "confidence": 0.0,
                    "error": "ChromaDB collection not initialized"
                }

            query_embedding = await self.embedding_service.get_embedding(
                query,
                normalize=normalize
            )

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=filters
            )

            # Handle empty results
            if not results or not results.get("documents") or len(results.get("documents", [])) == 0 or len(results.get("documents", [[]])[0]) == 0:
                return {
                    "answer": "No relevant information found in the knowledge base.",
                    "sources": [],
                    "confidence": 0.0
                }

            context = "\n".join([doc for doc in results["documents"][0]])

            response = await self.llm_service.generate_response(
                prompt=query,
                context={"reference_docs": context[:context_window]}
            )

            # Safely extract metadatas
            sources = []
            if results.get("metadatas") and len(results["metadatas"]) > 0:
                sources = results["metadatas"][0]

            result = {
                "answer": response.get("text", ""),
                "sources": sources,
                "confidence": response.get("confidence", 0.0),
                "embedding_dimension": len(query_embedding)
            }

            # Cache the result
            await cache_ai_result(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"RAG query error: {str(e)}")
            return {
                "answer": "Error querying knowledge base",
                "sources": [],
                "confidence": 0.0,
                "error": str(e)
            }

    async def add_to_knowledge_base(
        self,
        content: Union[str, List[str]],
        metadata: Union[Dict[str, Any], List[Dict[str, Any]]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> bool:
        """Add content to knowledge base with batch support."""
        try:
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return False

            # Convert single items to lists for consistent processing
            if isinstance(content, str):
                content = [content]
                metadata = [metadata] if isinstance(
                    metadata, Dict) else metadata

            embeddings = await self.embedding_service.get_embedding(
                content,
                normalize=normalize,
                batch_size=batch_size
            )

            # Generate IDs if not provided in metadata
            ids = []
            for i, meta in enumerate(metadata):
                if isinstance(meta, Dict) and meta.get("id"):
                    ids.append(str(meta["id"]))
                else:
                    ids.append(f"doc_{i}_{hash(content[i])}")

            # Ensure metadata is a list of dictionaries
            metadata_list = cast(List[Dict[str, Any]], metadata)

            self.collection.add(
                embeddings=embeddings,
                documents=content,
                metadatas=metadata_list,
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
        metadata: Dict[str, Any],
        normalize: bool = True
    ) -> bool:
        """Update existing document in knowledge base."""
        try:
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return False

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
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return False

            self.collection.delete(ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            return False

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        try:
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return {
                    "count": 0,
                    "dimension": 0,
                    "name": settings.CHROMA_COLLECTION_NAME,
                    "error": "ChromaDB collection not initialized"
                }

            # Get embedding dimension from the embedding service
            dimension = self.embedding_service.dimension if hasattr(
                self.embedding_service, "dimension") else 0

            return {
                "count": self.collection.count() if self.collection else 0,
                "dimension": dimension,
                "name": self.collection.name if self.collection else settings.CHROMA_COLLECTION_NAME
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                "count": 0,
                "dimension": 0,
                "name": settings.CHROMA_COLLECTION_NAME,
                "error": str(e)
            }
