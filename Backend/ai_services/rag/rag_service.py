from typing import Dict, List, Optional, Union, Any, cast, AsyncGenerator, Sequence, TypedDict, Literal
import chromadb
from chromadb.config import Settings
from chromadb.types import Where
from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.ai_services.llm.llm_service import LLMService
from Backend.ai_services.embedding.embedding_service import EmbeddingService
from Backend.ai_services.base.ai_service_base import AIServiceBase
from Backend.data_layer.vector_db.chroma_client import ChromaClient
from Backend.data_layer.repositories.ai_model_repository import AIModelRepository
from Backend.orchestration.ai_registry import ai_registry
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from numpy.typing import NDArray
from functools import lru_cache
import time
import hashlib
import json
import os
import PyPDF2

logger = get_logger(__name__)


class MetadataDict(TypedDict, total=False):
    source_file: str
    page_number: int
    domain: str
    content_type: str


class WhereFilter(TypedDict):
    operator: Literal["$in", "$eq"]
    key: str
    value: Union[List[str], str]


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
        """Optimized knowledge base query with parallel processing."""
        start_time = time.time()
        success = True
        try:
            if not self._current_model_id:
                self._current_model_id = await self._get_or_create_model()

            # Step 2: Collection check
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return self._error_response("Knowledge base not initialized")

            # Enhance query with context and intent
            enhanced_query = self._enhance_query(query, context, intent)

            # Get domain-specific filters
            domain = context.get("domain", "default")
            domain_config = ai_registry.get_domain_config(domain)
            rag_settings = domain_config.get("rag_settings", {})

            # Format ChromaDB filters properly
            filter_conditions: List[Dict[str, Dict[str, Any]]] = []
            if rag_settings.get("filters"):
                for key, values in rag_settings["filters"].items():
                    if values:
                        filter_conditions.append({
                            key: {"$in": values}
                        })

            # Add any additional filters
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        filter_conditions.append({
                            key: {"$in": value}
                        })
                    else:
                        filter_conditions.append({
                            key: {"$eq": value}
                        })

            # Create the final where clause
            chroma_filters: Optional[Where] = {
                "$and": filter_conditions} if filter_conditions else None

            # Step 3: Generate embedding asynchronously
            try:
                query_embedding = await self.embedding_service.get_embedding(enhanced_query, normalize=normalize)
            except Exception as e:
                success = False
                logger.error(f"Error generating embedding: {str(e)}")
                return self._error_response(f"Error generating embedding: {str(e)}")

            # Perform semantic search with enhanced parameters
            try:
                results = await asyncio.get_event_loop().run_in_executor(
                    self.thread_pool,
                    lambda: self.collection.query(
                        query_embeddings=[query_embedding],
                        n_results=rag_settings.get("limit", limit),
                        where=chroma_filters,
                        include=["documents", "metadatas", "distances"]
                    ) if self.collection else None
                )

                if not results or not isinstance(results, dict) or "documents" not in results:
                    success = False
                    return self._error_response("No results found")

                # Safely access results with proper type checking
                documents = results.get("documents", [[]])[
                    0] if results.get("documents") else []
                sources = results.get("metadatas", [[]])[
                    0] if results.get("metadatas") else []
                distances = results.get("distances", [[]])[
                    0] if results.get("distances") else []

                # Cast to proper types
                documents = cast(List[str], documents)
                sources = cast(List[MetadataDict], sources)
                distances = cast(List[float], distances)

                # Process and filter results
                filtered_results = self._filter_relevant_results(
                    documents, sources, distances,
                    rag_settings.get("similarity_threshold", 0.6)
                )

                # Process context with enhanced window
                context_window = rag_settings.get(
                    "context_window", context_window)
                context_parts = []
                total_length = 0

                for doc, source in filtered_results:
                    if total_length + len(doc) <= context_window:
                        context_parts.append({
                            "content": doc,
                            "metadata": source
                        })
                        total_length += len(doc)
                    else:
                        break

                # Generate AI response with enhanced context
                response = await self.llm_service.generate_response(
                    prompt=self._build_prompt(query, context_parts, context),
                    context={"sources": sources}
                )

                result = await self._process_llm_response(response, sources, query_embedding)

                # Add metadata about the knowledge source
                result["knowledge_source"] = [
                    {
                        "file": source.get("source_file", "unknown"),
                        "page": source.get("page_number", 0),
                        "domain": source.get("domain", "unknown")
                    } for source in sources[:3]  # Include top 3 sources
                ]

                latency = time.time() - start_time
                await self._update_model_stats(latency, success)

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

    def _enhance_query(self, query: str, context: Dict[str, Any], intent: Optional[str]) -> str:
        """Enhance the query with context and intent information."""
        enhanced_parts = [query.lower()]

        # Get domain config for query enhancement
        domain = context.get("domain", "default")
        domain_config = ai_registry.get_domain_config(domain)
        rag_settings = domain_config.get("rag_settings", {})
        query_enhancement = rag_settings.get("query_enhancement", {})

        # Add intent-specific context
        if intent:
            intent_prefixes = {
                "retrieve": "find detailed information about",
                "analyze": "analyze and explain in detail",
                "summarize": "provide a comprehensive summary of",
                "plan": "create a detailed plan for"
            }
            if intent in intent_prefixes:
                enhanced_parts.append(intent_prefixes[intent])

        # Enhance query based on type
        query_lower = query.lower()
        if "how" in query_lower or "steps" in query_lower or "guide" in query_lower:
            # Add how-to related terms
            enhanced_parts.extend(query_enhancement.get("how_to", []))
            enhanced_parts.append("from user guide")
            enhanced_parts.append("step by step instructions")
        elif "example" in query_lower or "sample" in query_lower:
            # Add example related terms
            enhanced_parts.extend(query_enhancement.get("examples", []))
        elif "what is" in query_lower or "explain" in query_lower:
            # Add reference related terms
            enhanced_parts.extend(query_enhancement.get("reference", []))
            enhanced_parts.append("from documentation")

        # Add domain context
        if domain != "default":
            enhanced_parts.append(f"in the context of {domain}")
            if "create" in query_lower or "add" in query_lower or "new" in query_lower:
                enhanced_parts.append(f"how to create {domain}")
                enhanced_parts.append("step by step guide")

        # Join all parts and remove duplicates while maintaining order
        seen = set()
        enhanced_query = " ".join(
            [x for x in enhanced_parts if not (x in seen or seen.add(x))])

        logger.debug(f"Enhanced query: {enhanced_query}")
        return enhanced_query

    def _filter_relevant_results(
        self,
        documents: Sequence[str],
        sources: Sequence[MetadataDict],
        distances: Sequence[float],
        threshold: float
    ) -> List[tuple[str, MetadataDict]]:
        """Filter results based on relevance and metadata."""
        filtered_results = []

        for doc, source, distance in zip(documents, sources, distances):
            # Convert distance to similarity score (1 - distance)
            similarity = 1 - distance if distance <= 1 else 0

            if similarity >= threshold:
                filtered_results.append((doc, source))

        return filtered_results

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

    def _build_prompt(self, query: str, context_parts: List[MetadataDict], additional_context: Dict[str, Any]) -> str:
        """Build an optimized prompt template with enhanced context handling."""
        # Convert conversation history to serializable format
        if "conversation_history" in additional_context:
            history = additional_context["conversation_history"]
            if hasattr(history, "get_messages"):
                additional_context["conversation_history"] = history.get_messages(
                )
            elif hasattr(history, "__dict__"):
                additional_context["conversation_history"] = history.__dict__
            elif isinstance(history, list):
                additional_context["conversation_history"] = [
                    msg.__dict__ if hasattr(msg, "__dict__") else msg
                    for msg in history
                ]

        # Format context parts with metadata
        formatted_context = []
        for part in context_parts:
            content = part.get("content", "")
            metadata = part.get("metadata", {})
            source_info = f"[Source: {metadata.get('source_file', 'unknown')}"
            if metadata.get("page_number"):
                source_info += f", Page {metadata['page_number']}"
            source_info += "]"

            formatted_context.append(f"{content}\n{source_info}")

        # Filter out non-serializable objects from additional context
        serializable_context = {
            k: v for k, v in additional_context.items()
            if isinstance(v, (str, int, float, bool, list, dict, type(None)))
        }

        return f"""
        User Query: {query}

        Knowledge Base Context:
        {chr(10).join(formatted_context)}

        Additional Context:
        {json.dumps(serializable_context, indent=2)}
        """

    async def _process_llm_response(
        self,
        response: Union[Dict[str, Any], AsyncGenerator[str, None]],
        sources: Sequence[MetadataDict],
        query_embedding: Union[List[float], NDArray[np.float32]]
    ) -> Dict[str, Any]:
        """Process LLM response with proper handling of streaming and non-streaming responses."""
        if isinstance(response, AsyncGenerator):
            chunks = []
            async for chunk in response:
                chunks.append(chunk)
            return {
                "answer": "".join(chunks),
                "sources": list(sources),
                "confidence": 0.8,
                "embedding_dimension": len(query_embedding)
            }
        else:
            return {
                "answer": response.get("text", "No answer generated."),
                "sources": list(sources),
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
        This method is deprecated as caching is now handled by the orchestrator.
        """
        logger.info(
            f"Cache invalidation now handled by orchestrator for domain: {domain}")
        pass

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
