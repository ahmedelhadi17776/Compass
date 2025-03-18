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

async def test_fixed_direct_indexing():
    """Test our fixed direct indexing implementation with both Todo object and dict."""
    # Test with Todo object
    logger.info("Testing direct indexing with Todo object")
    mock_todo = Todo(
        id=999998,  # Use a large ID to avoid conflicts
        title="Test Todo Object for Fixed Direct Indexing",
        description="This is a test todo object to verify fixed direct indexing works properly.",
        status=TodoStatus.PENDING,
        priority=TodoPriority.MEDIUM,
        user_id=1,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Test with dict
    logger.info("Testing direct indexing with dict")
    mock_todo_dict = {
        "id": 999997,  # Use a large ID to avoid conflicts
        "title": "Test Todo Dict for Fixed Direct Indexing",
        "description": "This is a test todo dict to verify fixed direct indexing works properly.",
        "status": TodoStatus.PENDING,
        "priority": TodoPriority.HIGH,
        "user_id": 1,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Test Todo object indexing
    logger.info(f"Indexing Todo object with ID: {mock_todo.id}")
    result1 = await direct_index_todo(mock_todo)
    
    # Test Dict indexing
    logger.info(f"Indexing Dict with ID: {mock_todo_dict['id']}")
    result2 = await direct_index_todo(mock_todo_dict)
    
    # Verify in ChromaDB
    if result1 and result2:
        logger.info("Both indexing operations were successful")
        
        # Initialize ChromaDB client with matching settings
        try:
            from chromadb.config import Settings
            client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
        except Exception as e:
            logger.warning(f"Error initializing ChromaDB client with settings: {str(e)}")
            # Fall back to simpler initialization
            client = chromadb.PersistentClient(
                path=settings.CHROMA_PERSIST_DIRECTORY
            )
            
        # Get collection
        try:
            collection = client.get_collection(
                name=settings.CHROMA_COLLECTION_NAME
            )
            
            # Check if both todos were indexed
            doc_id1 = f"todo_{mock_todo.id}"
            doc_id2 = f"todo_{mock_todo_dict['id']}"
            
            verification1 = collection.get(ids=[doc_id1])
            verification2 = collection.get(ids=[doc_id2])
            
            if verification1 and len(verification1["ids"]) > 0:
                logger.info(f"Successfully verified Todo object with ID {doc_id1} is in ChromaDB")
            else:
                logger.error(f"Failed to verify Todo object with ID {doc_id1}")
                
            if verification2 and len(verification2["ids"]) > 0:
                logger.info(f"Successfully verified Todo dict with ID {doc_id2} is in ChromaDB")
            else:
                logger.error(f"Failed to verify Todo dict with ID {doc_id2}")
                
            # Search for the todos
            logger.info("Testing search for the indexed todos")
            search_results = collection.query(
                query_texts=["fixed direct indexing"],
                n_results=5,
            )
            
            if search_results and len(search_results["ids"]) > 0:
                logger.info(f"Found {len(search_results['ids'][0])} matching documents")
                logger.info(f"Document IDs: {search_results['ids'][0]}")
                
                # Check if our todos are in the results
                if doc_id1 in search_results["ids"][0]:
                    logger.info(f"Found Todo object with ID {doc_id1} in search results")
                else:
                    logger.warning(f"Could not find Todo object with ID {doc_id1} in search results")
                    
                if doc_id2 in search_results["ids"][0]:
                    logger.info(f"Found Todo dict with ID {doc_id2} in search results")
                else:
                    logger.warning(f"Could not find Todo dict with ID {doc_id2} in search results")
            else:
                logger.warning("No search results found")
                
            # Clean up
            logger.info("Cleaning up test todos from ChromaDB")
            removal_result1 = await direct_remove_todo(mock_todo.id)
            removal_result2 = await direct_remove_todo(mock_todo_dict["id"])
            
            if removal_result1:
                logger.info(f"Successfully removed Todo object with ID {mock_todo.id}")
            else:
                logger.warning(f"Failed to remove Todo object with ID {mock_todo.id}")
                
            if removal_result2:
                logger.info(f"Successfully removed Todo dict with ID {mock_todo_dict['id']}")
            else:
                logger.warning(f"Failed to remove Todo dict with ID {mock_todo_dict['id']}")
                
        except Exception as e:
            logger.error(f"Error verifying indexed todos: {str(e)}")
    else:
        if not result1:
            logger.error("Failed to index Todo object")
        if not result2:
            logger.error("Failed to index Todo dict")
        
if __name__ == "__main__":
    asyncio.run(test_fixed_direct_indexing()) 