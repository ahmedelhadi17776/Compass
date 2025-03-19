from typing import List, Dict, Optional, Union, Any, cast
from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.vector_db.chroma_client import chroma_client
from Backend.ai_services.embedding.embedding_service import EmbeddingService
from Backend.data_layer.cache.ai_cache import cache_ai_result, get_cached_ai_result
from Backend.data_layer.database.models.todo import Todo, TodoStatus
import json
from datetime import datetime

logger = get_logger(__name__)

class TodoVectorStore:
    """Specialized vector store for Todo items.
    
    This class provides methods for storing and retrieving Todo embeddings in ChromaDB.
    It handles the conversion of Todo objects to vector embeddings and provides methods
    for finding similar Todos based on semantic similarity.
    """
    
    def __init__(self):
        """Initialize the TodoVectorStore with ChromaDB client and EmbeddingService."""
        # Use the centralized ChromaClient instance
        self.client = chroma_client.client
        self.collection = chroma_client.collection
        self.embedding_service = EmbeddingService()
        self.embedding_dimension = self.embedding_service.dimension
        self.todo_collection_name = f"{settings.CHROMA_COLLECTION_NAME}_todos"
        
        # Make sure the collection exists
        self._ensure_collection()
    
    def _ensure_collection(self) -> None:
        """Ensure the Todo collection exists in ChromaDB."""
        try:
            if not self.collection:
                logger.error("ChromaDB client not initialized")
                raise RuntimeError("ChromaDB client not initialized")
            
            # Use the existing collection for now
            # In a production environment, you might want to create a separate collection for todos
            logger.info(f"Using collection: {self.collection.name}")
        except Exception as e:
            logger.error(f"Error ensuring Todo collection: {str(e)}")
            raise
    
    def _prepare_todo_text(self, todo: Union[Todo, Dict]) -> str:
        """Convert a Todo object or dictionary to a text representation for embedding.
        
        Args:
            todo: Todo object or dictionary containing Todo data
            
        Returns:
            String representation of the Todo for embedding
        """
        if isinstance(todo, Todo):
            # Extract relevant fields from Todo object
            title = todo.title
            description = todo.description or ""
            tags = " ".join(todo.tags) if todo.tags else ""
            priority = str(todo.priority)
            status = str(todo.status)
        else:
            # Extract from dictionary
            title = todo.get("title", "")
            description = todo.get("description", "")
            tags = " ".join(todo.get("tags", [])) if todo.get("tags") else ""
            priority = str(todo.get("priority", ""))
            status = str(todo.get("status", ""))
        
        # Combine fields with importance weighting (title and description have more weight)
        return f"{title} {title} {description} {description} {tags} {priority} {status}"
    
    def _prepare_todo_metadata(self, todo: Union[Todo, Dict]) -> Dict[str, Any]:
        """Extract metadata from a Todo object or dictionary.
        
        Args:
            todo: Todo object or dictionary containing Todo data
            
        Returns:
            Dictionary of metadata for storage in ChromaDB
        """
        if isinstance(todo, Todo):
            # Extract metadata from Todo object
            # Convert lists to strings for ChromaDB (it doesn't accept lists as metadata values)
            tags_str = json.dumps(todo.tags) if todo.tags else "[]"
            
            return {
                "todo_id": todo.id,
                "user_id": todo.user_id,
                "title": todo.title,
                "status": str(todo.status),
                "priority": str(todo.priority),
                "due_date": todo.due_date.isoformat() if todo.due_date else None,
                "tags_json": tags_str,  # Store as JSON string
                "is_recurring": bool(todo.is_recurring),  # Ensure it's a boolean
                "ai_generated": bool(todo.ai_generated),  # Ensure it's a boolean
                "created_at": todo.created_at.isoformat() if todo.created_at else None,
                "updated_at": todo.updated_at.isoformat() if todo.updated_at else None,
                "document_type": "todo"
            }
        else:
            # Extract from dictionary
            # Convert lists to strings for ChromaDB
            tags = todo.get("tags", [])
            tags_str = json.dumps(tags) if tags else "[]"
            
            return {
                "todo_id": todo.get("id"),
                "user_id": todo.get("user_id"),
                "title": todo.get("title", ""),
                "status": str(todo.get("status", "")),
                "priority": str(todo.get("priority", "")),
                "due_date": todo.get("due_date"),
                "tags_json": tags_str,  # Store as JSON string
                "is_recurring": bool(todo.get("is_recurring", False)),  # Ensure it's a boolean
                "ai_generated": bool(todo.get("ai_generated", False)),  # Ensure it's a boolean
                "created_at": todo.get("created_at"),
                "updated_at": todo.get("updated_at"),
                "document_type": "todo"
            }
    
    async def add_todo_embedding(self, todo: Union[Todo, Dict]) -> bool:
        """Add a Todo embedding to ChromaDB.
        
        Args:
            todo: Todo object or dictionary containing Todo data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return False
            
            # Get todo ID
            todo_id = todo.id if isinstance(todo, Todo) else todo.get("id")
            if not todo_id:
                logger.error("Todo ID is required")
                return False
            
            # Prepare text and metadata
            todo_text = self._prepare_todo_text(todo)
            metadata = self._prepare_todo_metadata(todo)
            
            logger.info(f"Adding todo {todo_id} to ChromaDB with metadata: {metadata}")
            
            # Generate embedding
            embedding = await self.embedding_service.get_embedding(todo_text)
            logger.info(f"Generated embedding for todo {todo_id} with dimension {len(embedding)}")
            
            # Convert to the format expected by ChromaDB
            doc_id = f"todo_{todo_id}"
            
            # First try to delete the document if it exists (to avoid duplicates)
            try:
                self.collection.delete(ids=[doc_id])
                logger.info(f"Deleted existing todo {todo_id} from ChromaDB")
            except Exception as e:
                # It's okay if the document doesn't exist yet
                logger.debug(f"No existing todo to delete: {str(e)}")
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=[embedding],
                documents=[todo_text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            # Verify the document was added
            verification = self.collection.get(ids=[doc_id])
            if verification and len(verification["ids"]) > 0:
                logger.info(f"Successfully added Todo {todo_id} embedding to ChromaDB with ID {doc_id}")
                logger.debug(f"Metadata stored: {verification['metadatas'][0]}")
                return True
            else:
                logger.error(f"Failed to verify Todo {todo_id} was added to ChromaDB")
                return False
                
        except Exception as e:
            logger.error(f"Error adding Todo embedding: {str(e)}")
            return False
    
    async def update_todo_embedding(self, todo: Union[Todo, Dict]) -> bool:
        """Update a Todo embedding in ChromaDB.
        
        Args:
            todo: Todo object or dictionary containing Todo data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return False
            
            # Get todo ID
            todo_id = todo.id if isinstance(todo, Todo) else todo.get("id")
            if not todo_id:
                logger.error("Todo ID is required")
                return False
            
            # Prepare text and metadata
            todo_text = self._prepare_todo_text(todo)
            metadata = self._prepare_todo_metadata(todo)
            
            # Generate embedding
            embedding = await self.embedding_service.get_embedding(todo_text)
            
            # Update in ChromaDB
            self.collection.update(
                embeddings=[embedding],
                documents=[todo_text],
                metadatas=[metadata],
                ids=[f"todo_{todo_id}"]
            )
            
            logger.info(f"Successfully updated Todo {todo_id} embedding in ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Error updating Todo embedding: {str(e)}")
            return False
    
    async def delete_todo_embedding(self, todo_id: int) -> bool:
        """Delete a Todo embedding from ChromaDB.
        
        Args:
            todo_id: ID of the Todo to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return False
            
            # Delete from ChromaDB
            self.collection.delete(ids=[f"todo_{todo_id}"])
            
            logger.info(f"Successfully deleted Todo {todo_id} embedding from ChromaDB")
            return True
        except Exception as e:
            logger.error(f"Error deleting Todo embedding: {str(e)}")
            return False
    
    async def find_similar_todos(
        self, 
        query: str, 
        limit: int = 5, 
        user_id: Optional[int] = None,
        status_filter: Optional[Union[TodoStatus, str]] = None
    ) -> List[Dict]:
        """Find similar Todos based on semantic similarity.
        
        Args:
            query: Text query to find similar Todos
            limit: Maximum number of results to return
            user_id: Optional user ID to filter results by
            status_filter: Optional status to filter results by
            
        Returns:
            List of similar Todos with metadata and similarity scores
        """
        try:
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return []
            
            # Generate embedding for query
            query_embedding = await self.embedding_service.get_embedding(query)
            
            # Prepare filter using ChromaDB's operator syntax
            where_filter = {}  # Start with empty filter
            
            # Build the filter with proper operators
            where_conditions = []
            if user_id is not None:
                where_conditions.append({"user_id": {"$eq": user_id}})
            
            where_conditions.append({"document_type": {"$eq": "todo"}})
            
            if status_filter is not None:
                where_conditions.append({"status": {"$eq": str(status_filter)}})
            
            # Apply a combined $and filter if we have multiple conditions
            if len(where_conditions) > 1:
                where_filter = {"$and": where_conditions}
            elif where_conditions:
                where_filter = where_conditions[0]  # Use the single condition directly
                
            logger.info(f"Similar todos using where filter: {where_filter}")
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter
            )
            
            # Process results
            similar_todos = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                for i, result_id in enumerate(results["ids"][0]):
                    # Extract todo_id from result ID (format: "todo_{id}")
                    if result_id.startswith("todo_"):
                        todo_id = int(result_id.split("_")[1])
                    else:
                        continue
                    
                    # Get metadata and distance
                    metadata = results["metadatas"][0][i] if results.get("metadatas") and len(results["metadatas"]) > 0 else {}
                    distance = results["distances"][0][i] if results.get("distances") and len(results["distances"]) > 0 else 0
                    
                    # Parse tags from JSON string if present
                    tags = []
                    if metadata.get("tags_json"):
                        try:
                            tags = json.loads(metadata["tags_json"])
                        except:
                            tags = []
                    
                    # Fix status string format - convert from "TodoStatus.PENDING" to "pending"
                    status = metadata.get("status", "")
                    if status.startswith("TodoStatus."):
                        status = status.replace("TodoStatus.", "").lower()
                        
                    # Fix priority string format
                    priority = metadata.get("priority", "")
                    if priority.startswith("TodoPriority."):
                        priority = priority.replace("TodoPriority.", "").lower()
                    
                    similar_todos.append({
                        "todo_id": todo_id,
                        "title": metadata.get("title", ""),
                        "status": status,
                        "priority": priority,
                        "tags": tags,  # Add parsed tags
                        "similarity_score": 1.0 - distance,  # Convert distance to similarity score
                        "metadata": {
                            k: v for k, v in metadata.items() 
                            if k not in ["tags_json"]  # Don't include raw JSON in output
                        }
                    })
            
            return similar_todos
        except Exception as e:
            logger.error(f"Error finding similar Todos: {str(e)}")
            return []
    
    async def todo_semantic_search(
        self,
        query: str,
        user_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Search Todos by semantic similarity with enhanced filtering.
        
        Args:
            query: Text query to search Todos
            user_id: Optional user ID to filter results by
            filters: Additional filters to apply
            limit: Maximum number of results to return
            
        Returns:
            Dict containing search results and metadata
        """
        try:
            # Create a more granular cache key
            filters_hash = hash(str(sorted(filters.items()))) if filters else 0
            query_complexity = len(query.split())  # Simple measure of query complexity
            cache_key = f"todo_search:{hash(query)}:u{user_id}:f{filters_hash}:l{limit}"
            
            # Determine cache TTL based on query complexity and filters
            base_ttl = 1800  # 30 minutes base
            if query_complexity > 10:  # Complex queries cached longer
                ttl = base_ttl * 2
            elif filters and len(filters) > 2:  # More filters = longer cache
                ttl = base_ttl * 1.5
            else:
                ttl = base_ttl
            
            # Check cache first
            if cached_result := await get_cached_ai_result(cache_key):
                logger.info(f"Cache hit for query: {query[:50]}...")
                return cached_result
            
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return {
                    "results": [],
                    "count": 0,
                    "query": query
                }
            
            # Generate embedding for query
            query_embedding = await self.embedding_service.get_embedding(query)
            
            # Prepare filter - FIX: Use the $eq operator for where clauses
            where_filter = {}  # Start with empty filter
            
            # Build the filter with proper operators
            where_conditions = []
            if user_id is not None:
                where_conditions.append({"user_id": {"$eq": user_id}})
            
            where_conditions.append({"document_type": {"$eq": "todo"}})
            
            # Add any additional filters
            if filters:
                for k, v in filters.items():
                    if isinstance(v, (str, int, float, bool)):
                        where_conditions.append({k: {"$eq": v}})
            
            # Apply a combined $and filter if we have multiple conditions
            if len(where_conditions) > 1:
                where_filter = {"$and": where_conditions}
            elif where_conditions:
                where_filter = where_conditions[0]  # Use the single condition directly
                
            logger.info(f"Using where filter: {where_filter}")
            
            # Query ChromaDB
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where_filter
            )
            
            # Process results
            search_results = []
            if results and results.get("ids") and len(results["ids"]) > 0:
                for i, result_id in enumerate(results["ids"][0]):
                    # Extract todo_id from result ID
                    if result_id.startswith("todo_"):
                        todo_id = int(result_id.split("_")[1])
                    else:
                        continue
                    
                    # Get metadata and distance
                    metadata = results["metadatas"][0][i] if results.get("metadatas") and len(results["metadatas"]) > 0 else {}
                    distance = results["distances"][0][i] if results.get("distances") and len(results["distances"]) > 0 else 0
                    
                    # Parse tags from JSON string if present
                    tags = []
                    if metadata.get("tags_json"):
                        try:
                            tags = json.loads(metadata["tags_json"])
                        except:
                            tags = []
                    
                    # Fix status string format - convert from "TodoStatus.PENDING" to "pending"
                    status = metadata.get("status", "")
                    if status.startswith("TodoStatus."):
                        status = status.replace("TodoStatus.", "").lower()
                        
                    # Fix priority string format
                    priority = metadata.get("priority", "")
                    if priority.startswith("TodoPriority."):
                        priority = priority.replace("TodoPriority.", "").lower()
                    
                    search_results.append({
                        "todo_id": todo_id,
                        "title": metadata.get("title", ""),
                        "status": status,  # Use the fixed status format
                        "priority": priority,  # Use the fixed priority format 
                        "tags": tags,  # Add parsed tags
                        "similarity_score": 1.0 - distance,
                        "metadata": {
                            k: v for k, v in metadata.items() 
                            if k not in ["tags_json"]  # Don't include raw JSON in output
                        }
                    })
            
            result = {
                "results": search_results,
                "count": len(search_results),
                "query": query
            }
            
            # Cache result with dynamic TTL
            await cache_ai_result(cache_key, result, ttl=int(ttl))
            
            return result
        except Exception as e:
            logger.error(f"Error in Todo semantic search: {str(e)}")
            return {
                "results": [],
                "count": 0,
                "query": query,
                "error": str(e)
            }
    
    async def get_todo_count(self, user_id: Optional[int] = None) -> int:
        """Get the number of Todos in ChromaDB.
        
        Args:
            user_id: Optional user ID to filter by
            
        Returns:
            Number of Todos
        """
        try:
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return 0
            
            # Prepare filter
            where_filter = {"document_type": "todo"}
            if user_id is not None:
                where_filter["user_id"] = user_id
            
            # Get IDs that match the filter
            results = self.collection.get(where=where_filter)
            
            return len(results["ids"]) if results and "ids" in results else 0
        except Exception as e:
            logger.error(f"Error getting Todo count: {str(e)}")
            return 0
    
    async def get_todos_by_ids(self, todo_ids: List[int]) -> List[Dict[str, Any]]:
        """Get todos by their IDs from ChromaDB.
        
        Args:
            todo_ids: List of todo IDs to fetch
            
        Returns:
            List of todos with their metadata
        """
        try:
            # Ensure collection is initialized
            if not self.collection:
                logger.error("ChromaDB collection not initialized")
                return []
            
            # Convert todo IDs to document IDs
            doc_ids = [f"todo_{todo_id}" for todo_id in todo_ids]
            
            # Get todos from ChromaDB
            results = self.collection.get(
                ids=doc_ids,
                include=["metadatas", "documents"]
            )
            
            todos = []
            if results and results.get("ids"):
                for i, doc_id in enumerate(results["ids"]):
                    metadata = results["metadatas"][i] if results.get("metadatas") else {}
                    
                    # Parse tags from JSON string
                    tags = []
                    if metadata.get("tags_json"):
                        try:
                            tags = json.loads(metadata["tags_json"])
                        except:
                            tags = []
                    
                    # Fix status string format
                    status = metadata.get("status", "")
                    if status.startswith("TodoStatus."):
                        status = status.replace("TodoStatus.", "").lower()
                    
                    # Fix priority string format
                    priority = metadata.get("priority", "")
                    if priority.startswith("TodoPriority."):
                        priority = priority.replace("TodoPriority.", "").lower()
                    
                    todos.append({
                        "todo_id": metadata.get("todo_id"),
                        "title": metadata.get("title", ""),
                        "description": results["documents"][i] if results.get("documents") else "",
                        "status": status,
                        "priority": priority,
                        "tags": tags,
                        "due_date": metadata.get("due_date"),
                        "is_recurring": metadata.get("is_recurring", False),
                        "ai_generated": metadata.get("ai_generated", False),
                        "created_at": metadata.get("created_at"),
                        "updated_at": metadata.get("updated_at")
                    })
            
            return todos
        except Exception as e:
            logger.error(f"Error getting todos by IDs: {str(e)}")
            return [] 