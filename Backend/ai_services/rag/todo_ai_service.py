from typing import List, Dict, Optional, Union, Any, cast, AsyncGenerator
from Backend.ai_services.rag.todo_vector_store import TodoVectorStore
from Backend.ai_services.embedding.embedding_service import EmbeddingService
from Backend.ai_services.llm.llm_service import LLMService
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.database.models.todo import Todo, TodoStatus, TodoPriority
from Backend.data_layer.cache.ai_cache import cache_ai_result, get_cached_ai_result
from datetime import datetime, timedelta
import json
from Backend.core.config import settings

logger = get_logger(__name__)

class TodoAIService:
    """AI service for Todo items.
    
    This service provides AI functionality for Todo items, including:
    - Adding and updating Todo embeddings
    - Finding similar Todos
    - Generating suggestions for Todo items
    - Analyzing Todo patterns
    """
    
    def __init__(self):
        """Initialize the TodoAIService with required components."""
        self.todo_vector_store = TodoVectorStore()
        self.embedding_service = EmbeddingService()
        self.llm_service = LLMService()
    
    async def index_todo(self, todo: Union[Todo, Dict]) -> bool:
        """Index a Todo in the vector store.
        
        This method adds or updates a Todo's embedding in the vector store.
        
        Args:
            todo: Todo object or dictionary with Todo data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            todo_id = todo.id if isinstance(todo, Todo) else todo.get("id")
            if not todo_id:
                logger.error("Todo ID is required for indexing")
                return False
            
            # Check if todo already exists in vector store
            result = await self.todo_vector_store.update_todo_embedding(todo)
            if not result:
                # If update fails, try adding instead
                result = await self.todo_vector_store.add_todo_embedding(todo)
            
            return result
        except Exception as e:
            logger.error(f"Error indexing Todo: {str(e)}")
            return False
    
    async def remove_todo_index(self, todo_id: int) -> bool:
        """Remove a Todo from the vector store.
        
        Args:
            todo_id: ID of the Todo to remove
            
        Returns:
            True if successful, False otherwise
        """
        try:
            return await self.todo_vector_store.delete_todo_embedding(todo_id)
        except Exception as e:
            logger.error(f"Error removing Todo index: {str(e)}")
            return False
    
    async def find_similar_todos(
        self,
        todo: Union[Todo, Dict, str],
        limit: int = 5,
        user_id: Optional[int] = None
    ) -> List[Dict]:
        """Find Todos similar to the provided Todo or query.
        
        Args:
            todo: Todo object, dictionary or query string
            limit: Maximum number of results to return
            user_id: Optional user ID to filter results by
            
        Returns:
            List of similar Todos with metadata and similarity scores
        """
        try:
            # Convert Todo to query string if necessary
            if isinstance(todo, (Todo, dict)):
                query_string = self._todo_to_query_string(todo)
            else:
                query_string = todo
            
            # Get similar todos
            return await self.todo_vector_store.find_similar_todos(
                query=query_string,
                limit=limit,
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Error finding similar Todos: {str(e)}")
            return []
    
    async def search_todos(
        self,
        query: str,
        user_id: Optional[int] = None,
        filters: Optional[Dict] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """Search Todos by semantic similarity.
        
        Args:
            query: Text query to search for
            user_id: Optional user ID to filter results by
            filters: Additional filters to apply
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with search results and metadata
        """
        try:
            return await self.todo_vector_store.todo_semantic_search(
                query=query,
                user_id=user_id,
                filters=filters,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Error searching Todos: {str(e)}")
            return {
                "results": [],
                "count": 0,
                "query": query,
                "error": str(e)
            }
    
    async def generate_todo_suggestions(
        self,
        user_id: int,
        count: int = 3
    ) -> List[Dict]:
        """Generate Todo suggestions for a user.
        
        Args:
            user_id: User ID to generate suggestions for
            count: Number of suggestions to generate
            
        Returns:
            List of Todo suggestions
        """
        try:
            # Check cache first
            cache_key = f"todo_suggestions:{user_id}"
            if cached_result := await get_cached_ai_result(cache_key):
                return cached_result
            
            # Get existing todos for context
            similar_todos = await self.todo_vector_store.find_similar_todos(
                query="Important productive tasks",
                limit=5,
                user_id=user_id
            )
            
            # Convert to context string
            context = "User's existing tasks:\n"
            for todo in similar_todos:
                context += f"- {todo['title']}\n"
            
            # Generate suggestions using LLM
            prompt = f"""Based on the user's existing tasks, suggest {count} new Todo items that would help improve productivity.
            For each suggestion, provide a title, description, and priority level.
            
            {context}
            
            Format the response as a JSON array with objects containing 'title', 'description', and 'priority' fields.
            """
            
            response = await self.llm_service.generate_response(prompt)
            
            # Extract suggestions from LLM response
            suggestions = []
            if response and "text" in response:
                try:
                    # Extract JSON from the response
                    json_text = response["text"]
                    # If the response contains markdown code blocks, extract the JSON
                    if "```json" in json_text:
                        json_text = json_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_text:
                        json_text = json_text.split("```")[1].split("```")[0].strip()
                    
                    suggestions = json.loads(json_text)
                    
                    # Ensure each suggestion has the required fields
                    for suggestion in suggestions:
                        if "title" not in suggestion:
                            suggestion["title"] = "Suggested Todo"
                        if "description" not in suggestion:
                            suggestion["description"] = ""
                        if "priority" not in suggestion:
                            suggestion["priority"] = "MEDIUM"
                        
                        # Add AI generated flag
                        suggestion["ai_generated"] = True
                except Exception as e:
                    logger.error(f"Error parsing LLM response: {str(e)}")
                    suggestions = []
            
            # Cache the result
            await cache_ai_result(cache_key, suggestions, ttl=3600)  # 1 hour cache
            
            return suggestions
        except Exception as e:
            logger.error(f"Error generating Todo suggestions: {str(e)}")
            return []
    
    async def analyze_todo_completion(
        self,
        user_id: int,
        time_period: str = "week"
    ) -> Dict[str, Any]:
        """Analyze Todo completion patterns for a user.
        
        Args:
            user_id: User ID to analyze
            time_period: Time period to analyze ("day", "week", "month")
            
        Returns:
            Dictionary with analysis results
        """
        try:
            # Check cache first
            cache_key = f"todo_analysis:{user_id}:{time_period}"
            if cached_result := await get_cached_ai_result(cache_key):
                return cached_result
            
            # Get completed todos
            completed_todos = await self.todo_vector_store.find_similar_todos(
                query="completed tasks",
                limit=20,
                user_id=user_id,
                status_filter=TodoStatus.COMPLETED
            )
            
            # Get pending todos
            pending_todos = await self.todo_vector_store.find_similar_todos(
                query="pending tasks",
                limit=20,
                user_id=user_id,
                status_filter=TodoStatus.PENDING
            )
            
            # Calculate basic metrics
            total_completed = len(completed_todos)
            total_pending = len(pending_todos)
            completion_rate = total_completed / (total_completed + total_pending) if (total_completed + total_pending) > 0 else 0
            
            # Get completion by priority
            completion_by_priority = {
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0
            }
            
            for todo in completed_todos:
                priority = todo.get("priority", "MEDIUM")
                completion_by_priority[priority] = completion_by_priority.get(priority, 0) + 1
            
            # Generate analysis with LLM
            context = f"""
            User has completed {total_completed} tasks and has {total_pending} pending tasks.
            Completion rate: {completion_rate:.2%}
            
            Completion by priority:
            - HIGH: {completion_by_priority.get("HIGH", 0)}
            - MEDIUM: {completion_by_priority.get("MEDIUM", 0)}
            - LOW: {completion_by_priority.get("LOW", 0)}
            
            Completed tasks:
            {", ".join([todo.get("title", "") for todo in completed_todos[:5]])}
            
            Pending tasks:
            {", ".join([todo.get("title", "") for todo in pending_todos[:5]])}
            """
            
            prompt = f"""
            Analyze the user's Todo completion patterns based on the provided data.
            Provide insights on productivity patterns, suggest improvements, and identify potential bottlenecks.
            
            {context}
            
            Format the response as a JSON object with the following fields:
            - "insights": Array of insight strings
            - "recommendations": Array of recommendation strings
            - "productivity_score": Number between 0 and 100
            """
            
            response = await self.llm_service.generate_response(prompt)
            
            # Extract analysis from LLM response
            analysis = {
                "metrics": {
                    "completion_rate": completion_rate,
                    "total_completed": total_completed,
                    "total_pending": total_pending,
                    "completion_by_priority": completion_by_priority
                },
                "insights": [],
                "recommendations": [],
                "productivity_score": 0
            }
            
            if response and "text" in response:
                try:
                    # Extract JSON from the response
                    json_text = response["text"]
                    # If the response contains markdown code blocks, extract the JSON
                    if "```json" in json_text:
                        json_text = json_text.split("```json")[1].split("```")[0].strip()
                    elif "```" in json_text:
                        json_text = json_text.split("```")[1].split("```")[0].strip()
                    
                    llm_analysis = json.loads(json_text)
                    
                    if "insights" in llm_analysis:
                        analysis["insights"] = llm_analysis["insights"]
                    if "recommendations" in llm_analysis:
                        analysis["recommendations"] = llm_analysis["recommendations"]
                    if "productivity_score" in llm_analysis:
                        analysis["productivity_score"] = llm_analysis["productivity_score"]
                except Exception as e:
                    logger.error(f"Error parsing LLM response: {str(e)}")
            
            # Cache the result
            await cache_ai_result(cache_key, analysis, ttl=3600)  # 1 hour cache
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing Todo completion: {str(e)}")
            return {
                "metrics": {
                    "completion_rate": 0,
                    "total_completed": 0,
                    "total_pending": 0,
                    "completion_by_priority": {}
                },
                "insights": [],
                "recommendations": [],
                "productivity_score": 0,
                "error": str(e)
            }
    
    def _todo_to_query_string(self, todo: Union[Todo, Dict]) -> str:
        """Convert a Todo to a query string for similarity search.
        
        Args:
            todo: Todo object or dictionary
            
        Returns:
            Query string for similarity search
        """
        if isinstance(todo, Todo):
            title = todo.title
            description = todo.description or ""
            tags = " ".join(todo.tags) if todo.tags else ""
        else:
            title = todo.get("title", "")
            description = todo.get("description", "")
            tags = " ".join(todo.get("tags", [])) if todo.get("tags") else ""
        
        return f"{title} {description} {tags}"

    async def _enhance_prompt_with_context(
        self,
        prompt: str,
        previous_query: Optional[str] = None,
        relevant_todo_ids: Optional[List[int]] = None,
        conversation_mode: Optional[str] = None
    ) -> str:
        """Enhance the prompt with conversation context and relevant todos."""
        enhanced_prompt = prompt
        
        # If this is a follow-up question, add context
        if conversation_mode == "follow_up" and previous_query:
            enhanced_prompt = f"Previous question: {previous_query}\nCurrent question: {prompt}\n\nConsider the previous question for context when answering the current question."
        
        # If we have relevant todo IDs, fetch their details
        if relevant_todo_ids:
            try:
                # Search for these specific todos
                todos = await self.todo_vector_store.get_todos_by_ids(relevant_todo_ids)
                if todos:
                    todo_context = "\n".join([
                        f"- {todo['title']}: {todo.get('description', 'No description')} "
                        f"(Priority: {todo.get('priority', 'None')}, "
                        f"Status: {todo.get('status', 'None')})"
                        for todo in todos
                    ])
                    enhanced_prompt = f"{enhanced_prompt}\n\nRelevant todos:\n{todo_context}"
            except Exception as e:
                logger.error(f"Error fetching relevant todos: {str(e)}")
        
        return enhanced_prompt

    async def stream_todo_response(
        self,
        prompt: str,
        user_id: Optional[int] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Stream a response about todos using RAG."""
        try:
            # Extract context parameters
            previous_query = context.get("previous_query") if context else None
            relevant_todo_ids = context.get("relevant_todo_ids") if context else None
            conversation_mode = context.get("conversation_mode") if context else None
            
            # Enhance the prompt with context
            enhanced_prompt = await self._enhance_prompt_with_context(
                prompt,
                previous_query,
                relevant_todo_ids,
                conversation_mode
            )
            
            # Search for relevant todos
            search_results = await self.todo_vector_store.todo_semantic_search(
                enhanced_prompt,
                user_id=user_id,
                limit=5  # Adjust based on needs
            )
            
            # Prepare todo context for the LLM
            todo_context = ""
            if search_results and search_results.get("results"):
                todo_context = "Here are the relevant todos I found:\n\n"
                for idx, todo in enumerate(search_results["results"], 1):
                    todo_context += (
                        f"{idx}. **{todo['title']}**\n\n"
                        f"  - **Status**: {todo['status']}\n\n"
                        f"  - **Priority**: {todo['priority']}\n\n"
                        f"  - **Due Date**: {todo['metadata'].get('due_date', 'Not set')}\n\n"
                        f"  - **Tags**: {', '.join(todo.get('tags', []))}\n\n"
                    )
            
            # Prepare the final prompt
            final_prompt = f"""Based on the user's question: "{enhanced_prompt}"

{todo_context}

Please provide a helpful response that:
1. Directly answers the user's question
2. References specific todos when relevant
3. Provides actionable insights or next steps
4. Maintains context from any previous conversation

Response:"""

            # Stream the response
            async for chunk in self.llm_service.stream_response(
                final_prompt,
                system_message=context.get("system_message") if context else None
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Error in todo response streaming: {str(e)}")
            yield f"Error: {str(e)}" 