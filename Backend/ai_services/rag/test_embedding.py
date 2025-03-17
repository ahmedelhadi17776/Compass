import os
import sys
import asyncio
import json

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.ai_services.embedding.embedding_service import EmbeddingService
import chromadb

logger = get_logger(__name__)

async def test_direct_embedding():
    """Test adding and retrieving embeddings directly with ChromaDB."""
    try:
        # Initialize embedded service
        embedding_service = EmbeddingService()
        
        # Get the persistence directory and collection name
        persist_dir = settings.CHROMA_PERSIST_DIRECTORY
        collection_name = settings.CHROMA_COLLECTION_NAME
        
        logger.info(f"ChromaDB persistence directory: {persist_dir}")
        logger.info(f"ChromaDB collection name: {collection_name}")
        
        # Initialize the client directly
        client = chromadb.PersistentClient(
            path=persist_dir
        )
        
        # Get or create the collection
        collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Connected to collection: {collection.name}")
        
        # Get the count of documents
        count = collection.count()
        logger.info(f"Current document count: {count}")
        
        # Test adding a new document with a todo-like structure
        test_text = "This is a test todo about finding colors"
        test_id = "test_todo_color_123"
        test_metadata = {
            "document_type": "todo",
            "todo_id": 123,
            "user_id": 1,
            "title": "Test color todo",
            "status": "PENDING"
        }
        
        # Generate embedding
        embedding = await embedding_service.get_embedding(test_text)
        logger.info(f"Generated embedding with dimension: {len(embedding)}")
        
        # Try to delete if it exists
        try:
            collection.delete(ids=[test_id])
            logger.info(f"Deleted existing test document: {test_id}")
        except:
            pass
        
        # Add to ChromaDB
        collection.add(
            documents=[test_text],
            embeddings=[embedding],
            metadatas=[test_metadata],
            ids=[test_id]
        )
        logger.info(f"Added test document: {test_id}")
        
        # Verify it was added
        result = collection.get(ids=[test_id])
        if result and len(result["ids"]) > 0:
            logger.info(f"Retrieved test document: {result}")
        else:
            logger.error("Failed to retrieve test document")
        
        # Search for color-related todos
        search_results = collection.query(
            query_texts=["color"],
            n_results=5,
            where={"document_type": {"$eq": "todo"}}
        )
        
        if search_results and len(search_results["ids"]) > 0 and len(search_results["ids"][0]) > 0:
            logger.info(f"Search found {len(search_results['ids'][0])} documents")
            logger.info(f"Search result IDs: {search_results['ids'][0]}")
            logger.info(f"Search result metadata: {json.dumps(search_results['metadatas'][0], indent=2)}")
        else:
            logger.warning("Search found no results")
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_direct_embedding()) 