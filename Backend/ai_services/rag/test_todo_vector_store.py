import asyncio
import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from unittest import mock
import logging

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Backend.ai_services.rag.todo_vector_store import TodoVectorStore
from Backend.data_layer.database.models.todo import Todo, TodoStatus, TodoPriority

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock Todo objects for testing
class MockTodo:
    def __init__(self, todo_id: int, user_id: int, title: str, description: str = None):
        self.id = todo_id
        self.user_id = user_id
        self.title = title
        self.description = description or ""
        self.status = TodoStatus.PENDING
        self.priority = TodoPriority.MEDIUM
        self.due_date = None
        self.reminder_time = None
        self.is_recurring = False
        self.recurrence_pattern = None
        self.tags = ["test", "mock"]
        self.checklist = None
        self.linked_task_id = None
        self.linked_calendar_event_id = None
        self.ai_generated = False
        self.ai_suggestions = None
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


async def test_add_todo_embedding():
    """Test adding a Todo embedding to ChromaDB."""
    logger.info("Testing add_todo_embedding...")
    
    # Create a TodoVectorStore instance
    todo_vector_store = TodoVectorStore()
    
    # Create a mock Todo
    todo = MockTodo(
        todo_id=1,
        user_id=100,
        title="Test Todo",
        description="This is a test todo description for vector embedding testing"
    )
    
    # Add the Todo embedding
    result = await todo_vector_store.add_todo_embedding(todo)
    
    # Check result
    assert result, "Failed to add Todo embedding"
    logger.info("Successfully added Todo embedding")


async def test_update_todo_embedding():
    """Test updating a Todo embedding in ChromaDB."""
    logger.info("Testing update_todo_embedding...")
    
    # Create a TodoVectorStore instance
    todo_vector_store = TodoVectorStore()
    
    # Create a mock Todo
    todo = MockTodo(
        todo_id=1,
        user_id=100,
        title="Updated Test Todo",
        description="This is an updated test todo description for vector embedding testing"
    )
    
    # Update the Todo embedding
    result = await todo_vector_store.update_todo_embedding(todo)
    
    # Check result
    assert result, "Failed to update Todo embedding"
    logger.info("Successfully updated Todo embedding")


async def test_find_similar_todos():
    """Test finding similar Todos in ChromaDB."""
    logger.info("Testing find_similar_todos...")
    
    # Create a TodoVectorStore instance
    todo_vector_store = TodoVectorStore()
    
    # Find similar Todos
    similar_todos = await todo_vector_store.find_similar_todos(
        query="Test task description need to be completed",
        limit=5,
        user_id=100
    )
    
    # Check results
    logger.info(f"Found {len(similar_todos)} similar Todos")
    for i, todo in enumerate(similar_todos):
        logger.info(f"Similar Todo {i+1}: {todo['title']} (Score: {todo['similarity_score']:.4f})")


async def test_todo_semantic_search():
    """Test Todo semantic search."""
    logger.info("Testing todo_semantic_search...")
    
    # Create a TodoVectorStore instance
    todo_vector_store = TodoVectorStore()
    
    # Perform semantic search
    search_results = await todo_vector_store.todo_semantic_search(
        query="important task",
        user_id=100,
        limit=5
    )
    
    # Check results
    logger.info(f"Found {search_results['count']} search results")
    for i, result in enumerate(search_results['results']):
        logger.info(f"Search Result {i+1}: {result['title']} (Score: {result['similarity_score']:.4f})")


async def test_delete_todo_embedding():
    """Test deleting a Todo embedding from ChromaDB."""
    logger.info("Testing delete_todo_embedding...")
    
    # Create a TodoVectorStore instance
    todo_vector_store = TodoVectorStore()
    
    # Delete the Todo embedding
    result = await todo_vector_store.delete_todo_embedding(todo_id=1)
    
    # Check result
    assert result, "Failed to delete Todo embedding"
    logger.info("Successfully deleted Todo embedding")


async def main():
    """Run all tests."""
    logger.info("Starting TodoVectorStore tests...")
    
    try:
        # Run tests in sequence
        await test_add_todo_embedding()
        await test_update_todo_embedding()
        await test_find_similar_todos()
        await test_todo_semantic_search()
        await test_delete_todo_embedding()
        
        logger.info("All tests completed successfully!")
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
    

if __name__ == "__main__":
    """Run the tests when the script is executed directly."""
    asyncio.run(main()) 