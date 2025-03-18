import asyncio
import sys
import os
import json

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Backend.data_layer.vector_db.chroma_client import chroma_client
from Backend.utils.logging_utils import get_logger

logger = get_logger(__name__)

async def check_collection():
    """Check what's actually in the ChromaDB collection."""
    try:
        # Get the client and collection
        client = chroma_client.client
        collection = chroma_client.collection
        
        logger.info(f"Connected to collection: {collection.name}")
        
        # Get the count of documents
        result = collection.count()
        logger.info(f"Total documents in collection: {result}")
        
        # Get all documents
        all_docs = collection.get()
        logger.info(f"Found {len(all_docs['ids'])} documents in total")
        logger.info(f"Document IDs: {all_docs['ids']}")
        
        # Print the first document's metadata
        if all_docs['ids']:
            logger.info(f"First document metadata: {json.dumps(all_docs['metadatas'][0], indent=2)}")
            logger.info(f"First document content: {all_docs['documents'][0]}")
        
        # Get all documents of type 'todo'
        todos = collection.get(where={"document_type": {"$eq": "todo"}})
        logger.info(f"Found {len(todos['ids'])} todos in ChromaDB")
        
        # Print the IDs
        logger.info(f"Todo IDs: {todos['ids']}")
        
        # Print a sample of the metadata
        if todos['ids']:
            logger.info(f"Sample metadata for first todo: {json.dumps(todos['metadatas'][0], indent=2)}")
            
            # Do a simple query
            query_result = collection.query(
                query_texts=["todo"],
                n_results=5,
                where={"document_type": {"$eq": "todo"}}
            )
            
            logger.info(f"Query results count: {len(query_result['ids'][0]) if query_result['ids'] else 0}")
            logger.info(f"Query results IDs: {query_result['ids'][0] if query_result['ids'] else []}")
            
            if query_result['ids'] and len(query_result['ids'][0]) > 0:
                logger.info(f"First result metadata: {json.dumps(query_result['metadatas'][0][0], indent=2)}")
    
    except Exception as e:
        logger.error(f"Error checking collection: {str(e)}")
        
if __name__ == "__main__":
    asyncio.run(check_collection()) 