import os
import sys
import asyncio
import json

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Backend.utils.logging_utils import get_logger
from Backend.ai_services.rag.todo_vector_store import TodoVectorStore

logger = get_logger(__name__)

async def test_search():
    """Test the semantic search methods directly."""
    try:
        # Initialize the TodoVectorStore
        store = TodoVectorStore()
        
        # Test todo_semantic_search
        logger.info("Testing todo_semantic_search...")
        semantic_results = await store.todo_semantic_search(
            query="color",
            user_id=1,
            limit=5
        )
        
        logger.info(f"Semantic search results: {json.dumps(semantic_results, indent=2)}")
        
        # Test find_similar_todos
        logger.info("Testing find_similar_todos...")
        similar_results = await store.find_similar_todos(
            query="color",
            user_id=1,
            limit=5
        )
        
        logger.info(f"Similar todos results: {json.dumps(similar_results, indent=2)}")
        
    except Exception as e:
        logger.error(f"Error in test search: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_search()) 