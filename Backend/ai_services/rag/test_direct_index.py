import os
import sys
import asyncio
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.database.models.todo import Todo, TodoStatus, TodoPriority
from Backend.ai_services.rag.direct_index import direct_index_todo, direct_remove_todo
import chromadb
from datetime import datetime

logger = get_logger(__name__)

async def test_direct_indexing():
    """Test direct indexing with a mock todo."""
    # Create a mock todo
    mock_todo = Todo(
        id=999999,  # Use a large ID to avoid conflicts
        title="Test Todo for Direct Indexing",
        description="This is a test todo to verify direct indexing works properly.",
        status=TodoStatus.PENDING,
        priority=TodoPriority.MEDIUM,
        user_id=1,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    logger.info(f"Created mock todo: {mock_todo.id} - {mock_todo.title}")
    
    # Test direct indexing
    result = await direct_index_todo(mock_todo)
    if result:
        logger.info("Direct indexing successful")
        
        # Verify the todo can be found in ChromaDB
        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY
        )
        collection = client.get_collection(
            name=settings.CHROMA_COLLECTION_NAME
        )
        
        # Search for the todo
        search_results = collection.query(
            query_texts=["test direct indexing"],
            n_results=5,
        )
        
        if search_results and len(search_results["ids"]) > 0:
            logger.info(f"Found {len(search_results['ids'][0])} matching documents")
            logger.info(f"Document IDs: {search_results['ids'][0]}")
            
            # Check if our todo is in the results
            doc_id = f"todo_{mock_todo.id}"
            if doc_id in search_results["ids"][0]:
                logger.info(f"Successfully found our test todo with ID {doc_id}")
            else:
                logger.warning(f"Could not find our test todo with ID {doc_id}")
                logger.info(f"Found document IDs: {search_results['ids'][0]}")
        else:
            logger.warning("No search results found")
        
        # Clean up by removing the test todo
        removal_result = await direct_remove_todo(mock_todo.id)
        if removal_result:
            logger.info(f"Successfully removed test todo {mock_todo.id}")
        else:
            logger.warning(f"Failed to remove test todo {mock_todo.id}")
    else:
        logger.error("Direct indexing failed")
        
if __name__ == "__main__":
    asyncio.run(test_direct_indexing()) 