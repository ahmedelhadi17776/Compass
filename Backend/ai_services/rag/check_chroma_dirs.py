import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger

logger = get_logger(__name__)

def check_chroma_dirs():
    """Check if ChromaDB persistence directory exists and is properly configured."""
    # Get the ChromaDB persistence directory from settings
    chroma_dir = settings.CHROMA_PERSIST_DIRECTORY
    
    logger.info(f"ChromaDB persistence directory: {chroma_dir}")
    
    # Check if the directory exists
    if os.path.exists(chroma_dir):
        logger.info(f"Directory exists: {chroma_dir}")
        
        # List contents of the directory
        contents = os.listdir(chroma_dir)
        logger.info(f"Directory contents: {contents}")
        
        # Check for common ChromaDB files/directories
        if "chroma.sqlite3" in contents:
            logger.info("ChromaDB SQLite database file found")
        else:
            logger.warning("ChromaDB SQLite database file not found")
            
        if "index" in contents:
            logger.info("ChromaDB index directory found")
        else:
            logger.warning("ChromaDB index directory not found")
    else:
        logger.error(f"Directory does not exist: {chroma_dir}")
        logger.info("Attempting to create the directory...")
        
        try:
            os.makedirs(chroma_dir, exist_ok=True)
            logger.info(f"Successfully created directory: {chroma_dir}")
        except Exception as e:
            logger.error(f"Failed to create directory: {str(e)}")
    
    # Check write permissions
    try:
        test_file = os.path.join(chroma_dir, "test_write.txt")
        with open(test_file, 'w') as f:
            f.write("Test write permissions")
        logger.info(f"Successfully wrote test file: {test_file}")
        
        # Clean up
        os.remove(test_file)
        logger.info(f"Successfully removed test file: {test_file}")
    except Exception as e:
        logger.error(f"Failed to write to directory: {str(e)}")
    
    # Check the collection name
    collection_name = settings.CHROMA_COLLECTION_NAME
    logger.info(f"ChromaDB collection name: {collection_name}")

if __name__ == "__main__":
    check_chroma_dirs() 