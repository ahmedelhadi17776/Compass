import os
import sys
import asyncio
import json
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.database.models.todo import Todo
from Backend.ai_services.embedding.embedding_service import EmbeddingService
import chromadb

logger = get_logger(__name__)

async def get_all_todos(db: AsyncSession, user_id=None):
    """Get all todos from the database."""
    try:
        # Create query
        query = select(Todo)
        if user_id:
            query = query.where(Todo.user_id == user_id)
            
        # Execute query
        result = await db.execute(query)
        todos = result.scalars().all()
        logger.info(f"Found {len(todos)} todos in database")
        return todos
    except Exception as e:
        logger.error(f"Error getting todos: {str(e)}")
        return []

def prepare_todo_text(todo: Todo) -> str:
    """Convert a Todo object to a text representation for embedding."""
    title = todo.title
    description = todo.description or ""
    tags = " ".join(todo.tags) if todo.tags else ""
    priority = str(todo.priority)
    status = str(todo.status)
    
    # Combine fields with importance weighting
    return f"{title} {title} {description} {description} {tags} {priority} {status}"

def prepare_todo_metadata(todo: Todo) -> dict:
    """Extract metadata from a Todo object."""
    # Convert lists to strings for ChromaDB
    tags_str = json.dumps(todo.tags) if todo.tags else "[]"
    
    return {
        "document_type": "todo",
        "todo_id": todo.id,
        "user_id": todo.user_id,
        "title": todo.title,
        "status": str(todo.status),
        "priority": str(todo.priority),
        "tags_json": tags_str,
        "due_date": todo.due_date.isoformat() if todo.due_date else None,
        "is_recurring": bool(todo.is_recurring),
        "ai_generated": bool(todo.ai_generated),
        "created_at": todo.created_at.isoformat() if todo.created_at else None,
        "updated_at": todo.updated_at.isoformat() if todo.updated_at else None
    }

async def simple_reindex(user_id=None):
    """Reindex todos using direct ChromaDB access."""
    try:
        # Initialize embedding service
        embedding_service = EmbeddingService()
        
        # Connect to the database
        db_url = settings.DATABASE_URL
        engine = create_async_engine(db_url)
        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # Initialize ChromaDB client directly
        client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIRECTORY
        )
        
        # Get or create collection
        collection = client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Connected to collection: {collection.name}")
        logger.info(f"Current document count: {collection.count()}")
        
        # Get todos from database
        async with async_session() as session:
            todos = await get_all_todos(session, user_id)
            
            if not todos:
                logger.warning("No todos found to index")
                return
                
            logger.info(f"Processing {len(todos)} todos")
            
            # Process each todo
            success_count = 0
            error_count = 0
            
            for todo in todos:
                try:
                    # Prepare data
                    todo_id = todo.id
                    doc_id = f"todo_{todo_id}"
                    todo_text = prepare_todo_text(todo)
                    metadata = prepare_todo_metadata(todo)
                    
                    # Generate embedding
                    embedding = await embedding_service.get_embedding(todo_text)
                    
                    # Delete if exists (to avoid duplicates)
                    try:
                        collection.delete(ids=[doc_id])
                        logger.info(f"Deleted existing todo: {doc_id}")
                    except:
                        pass
                    
                    # Add to ChromaDB
                    collection.add(
                        documents=[todo_text],
                        embeddings=[embedding],
                        metadatas=[metadata],
                        ids=[doc_id]
                    )
                    
                    # Verify it was added
                    verification = collection.get(ids=[doc_id])
                    if verification and len(verification["ids"]) > 0:
                        logger.info(f"Successfully indexed todo {todo_id}")
                        success_count += 1
                    else:
                        logger.error(f"Failed to verify todo {todo_id} was added")
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Error indexing todo {todo.id}: {str(e)}")
                    error_count += 1
            
            logger.info(f"Reindexing complete: {success_count} successful, {error_count} failed")
            
            # Test a search query
            results = collection.query(
                query_texts=["todo"],
                n_results=5,
                where={"document_type": {"$eq": "todo"}}
            )
            
            if results and len(results["ids"]) > 0 and len(results["ids"][0]) > 0:
                logger.info(f"Test search found {len(results['ids'][0])} documents")
                logger.info(f"Search result IDs: {results['ids'][0]}")
            else:
                logger.warning("Test search found no results")
                
        # Close database connection
        await engine.dispose()
        
    except Exception as e:
        logger.error(f"Error in reindexing process: {str(e)}")

if __name__ == "__main__":
    asyncio.run(simple_reindex()) 