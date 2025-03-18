import os
import sys
import asyncio
import json

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Backend.data_layer.vector_db.chroma_client import chroma_client
from Backend.utils.logging_utils import get_logger
import chromadb

logger = get_logger(__name__)

async def check_todos():
    """Check for todos in ChromaDB using various approaches."""
    try:
        # Get the client and collection
        client = chroma_client.client
        collection = chroma_client.collection
        
        logger.info(f"Connected to collection: {collection.name}")
        
        # Get all documents 
        all_docs = collection.get()
        logger.info(f"Total documents: {len(all_docs['ids'])}")
        logger.info(f"Document IDs: {all_docs['ids']}")
        
        # Check each document
        for i, doc_id in enumerate(all_docs['ids']):
            logger.info(f"Document {i+1}: ID={doc_id}, Metadata={all_docs['metadatas'][i]}")
            
            # Check if it's a todo
            if doc_id.startswith("todo_"):
                logger.info(f"Found todo: {doc_id}")
                
        # Try different approaches to filter todos
        # Approach 1: Use the "document_type" field directly
        try:
            todos_1 = collection.get(where={"document_type": "todo"})
            logger.info(f"Approach 1: Found {len(todos_1['ids'])} todos using document_type='todo'")
            logger.info(f"Todo IDs: {todos_1['ids']}")
        except Exception as e:
            logger.error(f"Error with approach 1: {str(e)}")
            
        # Approach 2: Use equality operator
        try:
            todos_2 = collection.get(where={"document_type": {"$eq": "todo"}})
            logger.info(f"Approach 2: Found {len(todos_2['ids'])} todos using document_type=$eq:todo")
            logger.info(f"Todo IDs: {todos_2['ids']}")
        except Exception as e:
            logger.error(f"Error with approach 2: {str(e)}")
            
        # Approach 3: Look for IDs that start with "todo_"
        try:
            todo_ids = [id for id in all_docs['ids'] if id.startswith("todo_")]
            logger.info(f"Approach 3: Found {len(todo_ids)} todos by checking ID prefix 'todo_'")
            logger.info(f"Todo IDs: {todo_ids}")
            
            # If we found todos by ID, try to get them directly
            if todo_ids:
                todos_3 = collection.get(ids=todo_ids)
                logger.info(f"Retrieved {len(todos_3['ids'])} todos by ID")
        except Exception as e:
            logger.error(f"Error with approach 3: {str(e)}")
            
        # Test a direct search for one of the todos we know exists
        try:
            todo_11 = collection.get(ids=["todo_11"])
            if todo_11 and todo_11['ids']:
                logger.info(f"Found todo_11: {todo_11['metadatas'][0]}")
            else:
                logger.warning("Could not find todo_11 by direct ID lookup")
        except Exception as e:
            logger.error(f"Error looking up todo_11: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error checking todos: {str(e)}")

if __name__ == "__main__":
    asyncio.run(check_todos()) 