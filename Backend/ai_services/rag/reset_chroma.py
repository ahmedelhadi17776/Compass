import os
import sys
import asyncio
import shutil
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from core.config import settings
from utils.logging_utils import get_logger
import chromadb
from ai_services.embedding.embedding_service import EmbeddingService

logger = get_logger(__name__)

async def reset_and_test_chroma():
    """Reset ChromaDB and test adding a document to ensure it's working properly."""
    # Get the config
    persist_dir = settings.CHROMA_PERSIST_DIRECTORY
    collection_name = settings.CHROMA_COLLECTION_NAME
    
    logger.info(f"ChromaDB persistence directory: {persist_dir}")
    logger.info(f"ChromaDB collection name: {collection_name}")
    
    # Ensure directory exists
    os.makedirs(persist_dir, exist_ok=True)
    logger.info(f"Ensured directory exists: {persist_dir}")
    
    # Delete existing ChromaDB files
    try:
        # Save the directory path
        parent_dir = os.path.dirname(persist_dir)
        
        # Remove the existing directory
        if os.path.exists(persist_dir):
            logger.info(f"Removing existing ChromaDB directory: {persist_dir}")
            shutil.rmtree(persist_dir)
            
        # Recreate the directory
        os.makedirs(persist_dir, exist_ok=True)
        logger.info(f"Created fresh ChromaDB directory: {persist_dir}")
    except Exception as e:
        logger.error(f"Error removing ChromaDB directory: {str(e)}")
        return
    
    # Create a fresh ChromaDB client
    logger.info("Creating a fresh ChromaDB client")
    
    try:
        # Initialize the client with the fresh directory
        client = chromadb.PersistentClient(
            path=persist_dir
        )
        
        # Create a new collection
        collection = client.create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Created new collection: {collection_name}")
        
        # Test adding a document
        embedding_service = EmbeddingService()
        test_text = "This is a test document for ChromaDB"
        embedding = await embedding_service.get_embedding(test_text)
        
        logger.info(f"Generated test embedding with dimension: {len(embedding)}")
        
        # Add the document
        collection.add(
            documents=[test_text],
            embeddings=[embedding],
            metadatas=[{"type": "test", "document_type": "test"}],
            ids=["test_doc_1"]
        )
        logger.info("Successfully added test document to ChromaDB")
        
        # Query to make sure it's there
        results = collection.query(
            query_texts=["test document"],
            n_results=1
        )
        
        if results and len(results["ids"]) > 0 and len(results["ids"][0]) > 0:
            logger.info(f"Successfully queried test document: {results['ids'][0]}")
        else:
            logger.error("Failed to query test document")
            
        logger.info("ChromaDB reset and test complete")
        logger.info("\n\nIMPORTANT: You need to restart your FastAPI server now to use the new ChromaDB instance!\n\n")
        
    except Exception as e:
        logger.error(f"Error resetting ChromaDB: {str(e)}")

if __name__ == "__main__":
    asyncio.run(reset_and_test_chroma()) 