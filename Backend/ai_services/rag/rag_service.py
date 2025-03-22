from typing import Dict, List, Optional, Union, Any, cast, AsyncGenerator
import chromadb
from chromadb.config import Settings
from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.ai_services.llm.llm_service import LLMService
from Backend.ai_services.embedding.embedding_service import EmbeddingService
from Backend.ai_services.base.ai_service_base import AIServiceBase
from Backend.data_layer.cache.ai_cache import cache_ai_result, get_cached_ai_result, invalidate_rag_cache
from Backend.data_layer.vector_db.chroma_client import ChromaClient
from Backend.data_layer.repositories.ai_model_repository import AIModelRepository
from Backend.orchestration.ai_registry import ai_registry
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from functools import lru_cache
import time
import hashlib
import json
import os
import PyPDF2

logger = get_logger(__name__)


class RAGService(AIServiceBase):
    def __init__(self, db_session: Optional[AsyncSession] = None):
        super().__init__("rag")
        self.db_session = db_session
        self.model_repository = AIModelRepository(
            db_session) if db_session else None
        self._current_model_id: Optional[int] = None

        self.chroma_client = ChromaClient()
        self.client = self.chroma_client.client
        self.collection = self.chroma_client.collection
        self.llm_service = LLMService(db_session)
        self.embedding_service = EmbeddingService(db_session=db_session)
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        self._cache = {}

    @lru_cache(maxsize=1000)
    def _generate_cache_key(self, query: str, context_str: str, filters_str: Optional[str] = None) -> str:
        """Generates a cache key based on the query and context with LRU caching."""
        cache_input = json.dumps(
            {"query": query, "context": context_str, "filters": filters_str},
            sort_keys=True
        )
        return f"rag_query:{hashlib.sha256(cache_input.encode()).hexdigest()}"

    def _get_cache_key(self, query: str, context: Dict[str, Any], filters: Optional[Dict[str, Any]] = None) -> str:
        """Helper method to convert dictionaries to strings and generate cache key."""
        def make_json_serializable(obj):
            if isinstance(obj, dict):
                return {str(k): make_json_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_json_serializable(item) for item in obj]
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            else:
                return str(obj)

        context_str = json.dumps(
            make_json_serializable(context), sort_keys=True)
        filters_str = json.dumps(make_json_serializable(
            filters), sort_keys=True) if filters is not None else None
        return self._generate_cache_key(query, context_str, filters_str)

    async def _get_or_create_model(self) -> Optional[int]:
        """Get or create AI model record in database."""
        if not self.model_repository:
            return None

        try:
            model = await self.model_repository.get_model_by_name_version(
                name="rag-service",
                version="1.0"
            )

            if not model:
                model = await self.model_repository.create_model({
                    "name": "rag-service",
                    "version": "1.0",
                    "type": "rag",
                    "provider": "hybrid",
                    "model_metadata": {
                        "embedding_model": self.embedding_service.model_name,
                        "llm_model": self.llm_service.model_name,
                        "vector_db": "chromadb"
                    },
                    "status": "active"
                })

            return model.id
        except Exception as e:
            logger.error(f"Error getting/creating AI model: {str(e)}")
            return None

    async def _update_model_stats(self, latency: float, success: bool = True) -> None:
        """Update model usage statistics."""
        if self.model_repository and self._current_model_id:
            try:
                await self.model_repository.update_model_stats(
                    self._current_model_id,
                    latency,
                    success
                )
            except Exception as e:
                logger.error(f"Error updating model stats: {str(e)}")

    async def query_knowledge_base(
        self,
        query: str,
        context: Dict[str, Any] = {},
        intent: Optional[str] = None,
        user_id: int = 1,
        limit: int = 8,
        context_window: int = 1000,
        normalize: bool = True,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Optimized knowledge base query with parallel processing and caching."""
        try:
            if not self._current_model_id:
                self._current_model_id = await self._get_or_create_model()

            start_time = time.time()
            success = True

            # Cache Check
            cache_key = self._get_cache_key(query, context, filters)
            cache_config = ai_registry.get_cache_config()
            intent_ttl = cache_config["ttl_per_intent"].get(
                intent, cache_config["default_ttl"])

            if cached_result := await get_cached_ai_result(cache_key):
                return cached_result

            # Step 2: Collection check
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return self._error_response("Knowledge base not initialized")

            # Step 3: Generate embedding asynchronously
            try:
                query_embedding = await self.embedding_service.get_embedding(query, normalize=normalize)
            except Exception as e:
                success = False
                logger.error(f"Error generating embedding: {str(e)}")
                return self._error_response(f"Error generating embedding: {str(e)}")

            # Perform semantic search
            try:
                results = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    lambda: self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=limit,
                        where=filters
                    ) if self.collection else None
                )

                if not results:
                    success = False
                    return self._error_response("No results found")

                documents = results.get("documents", [[]])[0]
                sources = results.get("metadatas", [[]])[0]

                # Process context
                context_parts = []
                total_length = 0
                for doc in documents:
                    if total_length + len(doc) <= context_window:
                        context_parts.append(doc)
                        total_length += len(doc)
                    else:
                        break
                truncated_context = "\n".join(context_parts)

                # Generate AI response
                response = await self.llm_service.generate_response(
                    prompt=self._build_prompt(
                        query, truncated_context, context),
                    context={"sources": sources}
                )

                result = await self._process_llm_response(response, sources, query_embedding)

                latency = time.time() - start_time
                await self._update_model_stats(latency, success)

                await cache_ai_result(cache_key, result, ttl=intent_ttl)
                return result

            except Exception as e:
                success = False
                logger.error(f"Error in search process: {str(e)}")
                return self._error_response(str(e))

        except Exception as e:
            success = False
            latency = time.time() - start_time
            await self._update_model_stats(latency, success)

            logger.error(f"RAG query error: {str(e)}")
            return self._error_response(str(e))

    def _build_prompt(self, query: str, context: str, additional_context: Dict[str, Any]) -> str:
        """Build an optimized prompt template."""
        return f"""
        User Query: {query}

        Knowledge Base Context:
        {context}

        Additional Context:
        {json.dumps(additional_context, indent=2)}
        """

    async def _process_llm_response(
        self,
        response: Union[Dict[str, Any], AsyncGenerator[str, None]],
        sources: List[Dict[str, Any]],
        query_embedding: List[float]
    ) -> Dict[str, Any]:
        """Process LLM response with proper handling of streaming and non-streaming responses."""
        if isinstance(response, AsyncGenerator):
            chunks = []
            async for chunk in response:
                chunks.append(chunk)
            return {
                "answer": "".join(chunks),
                "sources": sources,
                "confidence": 0.8,
                "embedding_dimension": len(query_embedding)
            }
        else:
            return {
                "answer": response.get("text", "No answer generated."),
                "sources": sources,
                "confidence": response.get("confidence", 0.0),
                "embedding_dimension": len(query_embedding)
            }

    def _error_response(self, message: str, error_type: str = "general") -> Dict[str, Any]:
        """Generate a standardized error response."""
        return {
            "answer": f"Error: {message}",
            "sources": [],
            "confidence": 0.0,
            "error": message,
            "error_type": error_type
        }

    async def add_to_knowledge_base(
        self,
        content: Union[str, List[str]],
        metadata: Union[Dict[str, Any], List[Dict[str, Any]]],
        normalize: bool = True,
        batch_size: int = 32
    ) -> bool:
        """Optimized batch addition to knowledge base."""
        try:
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return False

            # Convert to lists and validate
            contents = [content] if isinstance(content, str) else content
            metadatas = [metadata] if isinstance(metadata, dict) else metadata

            if len(contents) != len(metadatas):
                raise ValueError(
                    "Number of contents must match number of metadata items")

            # Process embeddings in batches
            embeddings = await self._get_embeddings_batch(contents, batch_size)

            # Generate IDs
            ids = [f"doc_{i}_{hashlib.sha256(str(content).encode()).hexdigest()[:16]}"
                   for i, content in enumerate(contents)]

            # Add to collection in batches
            for i in range(0, len(contents), batch_size):
                batch_end = min(i + batch_size, len(contents))
                await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    lambda: self.collection.add(
                        embeddings=embeddings[i:batch_end],
                        documents=contents[i:batch_end],
                        metadatas=metadatas[i:batch_end],
                        ids=ids[i:batch_end]
                    )
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

    async def invalidate_rag_cache(self, domain: str) -> None:
        """
        Invalidate cache for a specific domain after knowledge base updates.
        """
        await invalidate_rag_cache(domain)

    async def _get_embeddings_batch(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Process embeddings in batches asynchronously."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await self.embedding_service.get_embedding(batch, normalize=True)
            embeddings.extend(batch_embeddings)
        return embeddings

    async def add_pdf_to_knowledge_base(
        self,
        pdf_path: str,
        metadata: Dict[str, Any],
        normalize: bool = True,
        batch_size: int = 32
    ) -> bool:
        """
        Process and add PDF document to the knowledge base.

        Args:
            pdf_path: Path to the PDF file
            metadata: Metadata for the document
            normalize: Whether to normalize embeddings
            batch_size: Batch size for processing

        Returns:
            bool: Success status
        """
        try:
            # Read PDF content
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                content = []

                # Extract text from each page
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()

                    # Create page-specific metadata
                    page_metadata = metadata.copy()
                    page_metadata.update({
                        "page_number": page_num + 1,
                        "total_pages": len(pdf_reader.pages),
                        "source_file": os.path.basename(pdf_path),
                        "content_type": "pdf_page"
                    })

                    # Add each page as a separate document
                    content.append(page_text)

                    # Add domain info if not present
                    if "domain" not in page_metadata:
                        # Extract domain from filename or path
                        filename = os.path.basename(pdf_path)
                        if "habit" in filename.lower():
                            page_metadata["domain"] = "habits"
                        elif "todo" in filename.lower():
                            page_metadata["domain"] = "todos"
                        elif "task" in filename.lower():
                            page_metadata["domain"] = "tasks"
                        else:
                            page_metadata["domain"] = "default"

                    # Add to knowledge base
                    await self.add_to_knowledge_base(
                        content=page_text,
                        metadata=page_metadata,
                        normalize=normalize
                    )

            return True
        except Exception as e:
            logger.error(f"Error adding PDF to knowledge base: {str(e)}")
            return False
