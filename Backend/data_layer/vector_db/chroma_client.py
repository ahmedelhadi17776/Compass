import chromadb
from chromadb.config import Settings
from chromadb.api.types import (
    Document, Documents, EmbeddingFunction, Embeddings,
    QueryResult, Metadata, GetResult, OneOrMany, ID, IDs
)
from Backend.core.config import settings
import logging
import os
from typing import List, Dict, Any, Optional, Union, Sequence, cast

logger = logging.getLogger(__name__)


class ChromaClient:
    def __init__(self):
        self.client = None
        self.collection = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize ChromaDB client with proper settings."""
        try:
            # Create data directory if it doesn't exist
            os.makedirs(settings.CHROMA_PERSIST_DIRECTORY, exist_ok=True)

            # Initialize client with persistent storage
            self.client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=Settings(
                    anonymized_telemetry=settings.CHROMA_TELEMETRY_ENABLED,
                    allow_reset=settings.CHROMA_ALLOW_RESET
                )
            )

            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=settings.CHROMA_COLLECTION_NAME,
                metadata={"hnsw:space": settings.CHROMA_METADATA_SPACE}
            )
            logger.info("Successfully initialized ChromaDB client")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {str(e)}")
            raise RuntimeError(
                f"Failed to initialize ChromaDB client: {str(e)}")

    def add_documents(
        self,
        documents: Union[str, List[str]],
        metadatas: Optional[Union[Dict[str, Any],
                                  List[Dict[str, Any]]]] = None,
        ids: Optional[Union[str, List[str]]] = None
    ) -> None:
        """Add documents to the collection."""
        try:
            if self.collection is None:
                raise RuntimeError("Collection not initialized")

            # Convert single items to lists if necessary
            docs = cast(Documents, [documents] if isinstance(
                documents, str) else documents)
            metas = cast(Optional[List[Metadata]], [metadatas]
                         if isinstance(metadatas, dict) else metadatas)
            doc_ids = cast(Optional[IDs], [ids]
                           if isinstance(ids, str) else ids)

            self.collection.add(
                documents=docs,
                metadatas=metas,
                ids=doc_ids
            )
            logger.info(
                f"Successfully added {len(docs) if isinstance(docs, list) else 1} documents")
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise

    def query(
        self,
        query_text: Union[str, List[str]],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> QueryResult:
        """Query the collection."""
        try:
            if self.collection is None:
                raise RuntimeError("Collection not initialized")

            # Convert single query to list if necessary
            query_texts = cast(Documents, [query_text] if isinstance(
                query_text, str) else query_text)

            results = self.collection.query(
                query_texts=query_texts,
                n_results=n_results,
                where=where
            )
            return results
        except Exception as e:
            logger.error(f"Failed to query collection: {str(e)}")
            raise

    def delete(
        self,
        ids: Optional[Union[str, List[str]]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> None:
        """Delete documents from the collection."""
        try:
            if self.collection is None:
                raise RuntimeError("Collection not initialized")

            # Convert single ID to list if necessary
            doc_ids = cast(Optional[IDs], [ids]
                           if isinstance(ids, str) else ids)

            self.collection.delete(
                ids=doc_ids,
                where=where
            )
            logger.info("Successfully deleted documents")
        except Exception as e:
            logger.error(f"Failed to delete documents: {str(e)}")
            raise


# Initialize global client
chroma_client = ChromaClient()
