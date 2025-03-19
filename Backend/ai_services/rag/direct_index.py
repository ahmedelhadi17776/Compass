import os
import sys
import asyncio
import json
from typing import Union, Dict, Optional

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.database.models.todo import Todo
from Backend.ai_services.embedding.embedding_service import EmbeddingService
import chromadb
from Backend.data_layer.vector_db.chroma_client import chroma_client

logger = get_logger(__name__)

def prepare_todo_text(todo: Union[Todo, Dict]) -> str:
    """Convert a Todo object or dictionary to a text representation for embedding."""
    if isinstance(todo, Dict):
        title = todo.get("title", "").strip()
        description = todo.get("description", "").strip()
        tags = " ".join(todo.get("tags", [])) if todo.get("tags") else ""
        priority = str(todo.get("priority", "")).replace("TodoPriority.", "").lower()
        status = str(todo.get("status", "")).replace("TodoStatus.", "").lower()
    else:
        title = todo.title.strip()
        description = todo.description.strip() if todo.description else ""
        tags = " ".join(todo.tags) if todo.tags else ""
        priority = str(todo.priority).replace("TodoPriority.", "").lower()
        status = str(todo.status).replace("TodoStatus.", "").lower()
    
    # Combine fields with importance weighting
    # Title is most important, followed by description, then tags
    # Priority and status are included but with less weight
    # Repeat important fields to increase their weight in the embedding
    return f"{title} {title} {title} {description} {description} {tags} {tags} priority:{priority} status:{status}"

def prepare_todo_metadata(todo: Union[Todo, Dict]) -> dict:
    """Extract metadata from a Todo object."""
    if isinstance(todo, Dict):
        # Convert lists to strings for ChromaDB
        tags = todo.get("tags", [])
        tags_str = json.dumps(tags) if tags else "[]"
        
        todo_id = todo.get("id")
        created_at = todo.get("created_at")
        updated_at = todo.get("updated_at")
        due_date = todo.get("due_date")
        is_recurring = todo.get("is_recurring", False)
        ai_generated = todo.get("ai_generated", False)
        
        metadata = {
            "document_type": "todo",
            "todo_id": todo_id,
            "user_id": todo.get("user_id"),
            "title": todo.get("title", ""),
            "status": str(todo.get("status", "")),
            "priority": str(todo.get("priority", "")),
            "tags_json": tags_str,
            "is_recurring": bool(is_recurring),
            "ai_generated": bool(ai_generated),
        }
        
        # Handle date fields (Convert to string if not None)
        if due_date:
            metadata["due_date"] = due_date if isinstance(due_date, str) else due_date.isoformat()
        else:
            metadata["due_date"] = ""
            
        if created_at:
            metadata["created_at"] = created_at if isinstance(created_at, str) else created_at.isoformat()
        else:
            metadata["created_at"] = ""
            
        if updated_at:
            metadata["updated_at"] = updated_at if isinstance(updated_at, str) else updated_at.isoformat()
        else:
            metadata["updated_at"] = ""
            
        return metadata
    else:
        # Convert lists to strings for ChromaDB
        tags_str = json.dumps(todo.tags) if todo.tags else "[]"
        
        metadata = {
            "document_type": "todo",
            "todo_id": todo.id,
            "user_id": todo.user_id,
            "title": todo.title,
            "status": str(todo.status),
            "priority": str(todo.priority),
            "tags_json": tags_str,
            "is_recurring": bool(todo.is_recurring),
            "ai_generated": bool(todo.ai_generated),
        }
        
        # Handle date fields (Convert to string if not None)
        if todo.due_date:
            metadata["due_date"] = todo.due_date.isoformat()
        else:
            metadata["due_date"] = ""
            
        if todo.created_at:
            metadata["created_at"] = todo.created_at.isoformat()
        else:
            metadata["created_at"] = ""
            
        if todo.updated_at:
            metadata["updated_at"] = todo.updated_at.isoformat()
        else:
            metadata["updated_at"] = ""
            
        return metadata

async def direct_index_todo(todo: Union[Todo, Dict]) -> bool:
    """Directly index a single todo in ChromaDB."""
    try:
        # Initialize embedding service
        embedding_service = EmbeddingService()
        
        # Use the global ChromaDB client instead of creating a new one
        client = chroma_client.client
        collection = chroma_client.collection
        
        # Get todo ID (handle both Todo object and dict)
        if isinstance(todo, Dict):
            todo_id = todo.get("id")
        else:
            todo_id = todo.id
            
        if not todo_id:
            logger.error("Todo ID is required for indexing")
            return False
            
        # Prepare data
        doc_id = f"todo_{todo_id}"
        todo_text = prepare_todo_text(todo)
        metadata = prepare_todo_metadata(todo)
        
        # Generate embedding
        embedding = await embedding_service.get_embedding(todo_text)
        
        # Delete if exists (to avoid duplicates)
        try:
            collection.delete(ids=[doc_id])
            logger.info(f"Deleted existing todo: {doc_id}")
        except Exception as e:
            # It's okay if the document doesn't exist yet
            logger.debug(f"No existing todo to delete: {str(e)}")
        
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
            return True
        else:
            logger.error(f"Failed to verify todo {todo_id} was added")
            return False
            
    except Exception as e:
        logger.error(f"Error directly indexing todo: {str(e)}")
        return False

async def direct_remove_todo(todo_id: int) -> bool:
    """Directly remove a todo from ChromaDB."""
    try:
        # Use the global ChromaDB client instead of creating a new one
        client = chroma_client.client
        collection = chroma_client.collection
        
        # Create document ID
        doc_id = f"todo_{todo_id}"
        
        # Delete from ChromaDB
        try:
            collection.delete(ids=[doc_id])
            logger.info(f"Successfully removed todo {todo_id} from ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Error removing todo from ChromaDB: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error accessing ChromaDB: {str(e)}")
        return False 