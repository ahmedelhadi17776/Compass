from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from crewai import Agent, Task, Crew
from langchain.tools import Tool
from Backend.ai_services.llm.llm_service import LLMService
from Backend.utils.logging_utils import get_logger
from pydantic import Field
from Backend.services.todo_service import TodoService
from Backend.data_layer.database.models.todo import TodoStatus, TodoPriority
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class TodoAgent:
    def __init__(self, db_session=None):
        self.agent = Agent(
            role="Todo Management Specialist",
            goal="Create and edit todos from natural language instructions",
            backstory="""I am an expert in todo management and organization. I help users 
                        efficiently create and manage their todos by understanding natural 
                        language and extracting structured information.""",
            tools=[
                Tool(
                    name="create_todo",
                    func=self.create_todo,
                    description="Creates a new todo item from natural language"
                ),
                Tool(
                    name="edit_todo",
                    func=self.edit_todo,
                    description="Processes a natural language request to edit a todo, identifying which todo to edit and how"
                )
            ],
            verbose=True,
            allow_delegation=True  # Enable task delegation
        )
        
        self.ai_service = LLMService()
        self.db = db_session
        
        # Initialize services instead of repositories
        if db_session:
            # For TodoService, we need to provide a TodoRepository instance
            from Backend.data_layer.repositories.todo_repository import TodoRepository
            todo_repo = TodoRepository(db_session)
            self.todo_service = TodoService(todo_repo)
        else:
            self.todo_service = None
    
    async def create_todo(self, description: str, user_id: int = None) -> Dict[str, Any]:
        """Create a new todo item from natural language description."""
        try:
            # Set current_time once at the beginning
            current_time = datetime.utcnow()
            
            # Use LLM to extract structured data
            todo_analysis = await self.ai_service.generate_response(
                prompt=f"""Extract structured todo information from this description:
Description: {description}

Extract and format as JSON:
- title: A clear, concise title for the todo item
- description: Any additional details (can be empty)
- priority: high, medium, or low
- due_date: Extract any mentioned deadline (YYYY-MM-DD format)
- tags: Array of relevant tags""",
                context={
                    "system_message": "You are a todo extraction AI. Extract structured todo information from natural language."
                }
            )
            
            try:
                # Parse the JSON response
                response_text = todo_analysis.get("text", "")
                
                # Extract JSON from markdown if needed
                if "```json" in response_text:
                    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                
                todo_data = json.loads(response_text)
                
                # Add metadata - use actual datetime objects, not strings
                todo_data["created_at"] = current_time
                todo_data["updated_at"] = current_time
                todo_data["is_recurring"] = False
                todo_data["user_id"] = user_id
                
                # Set status to PENDING by default
                todo_data["status"] = TodoStatus.PENDING
                
                # Convert priority string to enum value
                priority_mapping = {
                    "low": TodoPriority.LOW,
                    "medium": TodoPriority.MEDIUM,
                    "mid": TodoPriority.MEDIUM,
                    "high": TodoPriority.HIGH
                }
                
                if "priority" in todo_data:
                    priority_str = todo_data["priority"].lower()
                    todo_data["priority"] = priority_mapping.get(priority_str, TodoPriority.MEDIUM)
                else:
                    todo_data["priority"] = TodoPriority.MEDIUM
                
                # Convert due_date string to datetime object if present
                if "due_date" in todo_data and todo_data["due_date"]:
                    try:
                        # Parse YYYY-MM-DD format
                        due_date = datetime.strptime(todo_data["due_date"], "%Y-%m-%d")
                        
                        # Ensure due_date is not in the past
                        if due_date < current_time:
                            # If due date is in the past, set it to end of current day
                            logger.warning(f"Due date {due_date} is in the past, adjusting to future date")
                            adjusted_due_date = current_time.replace(hour=23, minute=59, second=59)
                            todo_data["due_date"] = adjusted_due_date
                        else:
                            todo_data["due_date"] = due_date
                    except ValueError:
                        # If parsing fails, remove invalid date
                        logger.warning(f"Invalid due_date format: {todo_data['due_date']}")
                        todo_data.pop("due_date", None)
                
                # Save to database if service is available
                if self.todo_service is not None:
                    db_todo = await self.todo_service.create_todo(**todo_data)
                    if db_todo:
                        todo_data["id"] = db_todo.id if hasattr(db_todo, 'id') else None
                
                # Ensure all values are JSON serializable
                # Convert datetime objects to strings
                for key, value in list(todo_data.items()):
                    if isinstance(value, datetime):
                        todo_data[key] = value.isoformat()
                    elif isinstance(value, (TodoStatus, TodoPriority)):  # Check if it's an enum
                        todo_data[key] = value.value
                    elif isinstance(value, (list, tuple)):
                        # Handle lists that might contain non-serializable items
                        todo_data[key] = [
                            item.value if isinstance(item, (TodoStatus, TodoPriority)) else 
                            item.isoformat() if hasattr(item, "isoformat") else 
                            item 
                            for item in value
                        ]
                
                return {
                    "status": "success",
                    "message": f"Todo '{todo_data['title']}' created successfully",
                    "todo": todo_data
                }
            except Exception as e:
                logger.error(f"Error parsing todo data: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Could not parse todo information: {str(e)}",
                    "raw_response": todo_analysis.get("text", "")
                }
        except Exception as e:
            logger.error(f"Todo creation failed: {str(e)}")
            return {"status": "error", "message": f"Todo creation failed: {str(e)}"}

    async def edit_todo(self, description: str, user_id: int = None) -> Dict[str, Any]:
        """
        Process a natural language request to edit a todo item.
        
        Args:
            description: A natural language description of the edit to perform
            user_id: The ID of the user making the request
            
        Returns:
            A dictionary with the status and result of the edit operation
        """
        try:
            # First, use LLM to understand what changes are needed and identify the todo
            edit_analysis = await self.ai_service.generate_response(
                prompt=f"""Parse this todo edit request and extract the following information as JSON:
Request: {description}

Extract and format as JSON:
- todo_identifier: The description or title that helps identify which todo the user is referring to (e.g., "Dad's birthday party")
- edit_type: What kind of edit (e.g., mark_complete, change_title, change_due_date, change_priority, etc.)
- new_value: The new value to set (if applicable)""",
                context={
                    "system_message": "You are a todo management AI. Extract edit instructions from natural language."
                }
            )
            
            # Parse the response
            response_text = edit_analysis.get("text", "")
            
            # Extract JSON from markdown if needed
            if "```json" in response_text:
                json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
            
            try:
                edit_data = json.loads(response_text)
            except Exception as e:
                logger.error(f"Error parsing edit data: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Could not understand edit request: {str(e)}",
                    "raw_response": response_text
                }
            
            # Get the todo identifier from the edit data
            todo_identifier = edit_data.get("todo_identifier")
            if not todo_identifier:
                return {"status": "error", "message": "Could not identify which todo to edit"}
            
            # Use ContextBuilder to get all todos for the user
            if self.db:
                from Backend.orchestration.context_builder import ContextBuilder
                context_builder = ContextBuilder(self.db)
                
                # Get context specifically for todos domain
                context_data = await context_builder.get_full_context(user_id, domains=["todos"])
                
                if "todos" not in context_data or not context_data["todos"]:
                    return {"status": "error", "message": "No todos found for this user"}
                
                # Find the most similar todo based on the identifier
                todos = context_data["todos"]
                if isinstance(todos, dict) and "items" in todos:
                    todos = todos["items"]
                
                # Find the best matching todo
                best_match = None
                highest_similarity = 0
                
                # Use LLM to find the best match
                match_analysis = await self.ai_service.generate_response(
                    prompt=f"""Find the best matching todo from the list based on this identifier: "{todo_identifier}"

Available todos:
{json.dumps(todos, indent=2)}

Return only the ID of the best matching todo as a plain number without any explanation:""",
                    context={
                        "system_message": "You are a precise matching AI. Find the best matching todo and return only its ID."
                    }
                )
                
                try:
                    best_match_id = int(match_analysis.get("text", "").strip())
                    
                    # Now that we have the todo ID, prepare the update data
                    update_data = {}
                    
                    # Process the edit type
                    edit_type = edit_data.get("edit_type", "").lower()
                    new_value = edit_data.get("new_value")
                    
                    if edit_type == "mark_complete" or "complete" in edit_type:
                        update_data["status"] = TodoStatus.COMPLETED
                    elif edit_type == "mark_in_progress" or "progress" in edit_type:
                        update_data["status"] = TodoStatus.IN_PROGRESS
                    elif edit_type == "mark_pending" or "pending" in edit_type:
                        update_data["status"] = TodoStatus.PENDING
                    elif edit_type == "mark_archived" or "archive" in edit_type:
                        update_data["status"] = TodoStatus.ARCHIVED
                    elif edit_type == "change_title" or "title" in edit_type:
                        update_data["title"] = new_value
                    elif edit_type == "change_description" or "description" in edit_type:
                        update_data["description"] = new_value
                    elif edit_type == "change_priority" or "priority" in edit_type:
                        priority_mapping = {
                            "low": TodoPriority.LOW,
                            "medium": TodoPriority.MEDIUM,
                            "mid": TodoPriority.MEDIUM, 
                            "high": TodoPriority.HIGH
                        }
                        if isinstance(new_value, str):
                            update_data["priority"] = priority_mapping.get(new_value.lower(), TodoPriority.MEDIUM)
                    elif edit_type == "change_due_date" or "due" in edit_type:
                        if isinstance(new_value, str):
                            try:
                                # Try to parse the date
                                due_date = datetime.strptime(new_value, "%Y-%m-%d")
                                update_data["due_date"] = due_date
                            except ValueError:
                                logger.warning(f"Invalid due_date format: {new_value}")
                    else:
                        # Generic case - just try to update the field with the new value
                        field_name = edit_type.replace("change_", "")
                        update_data[field_name] = new_value
                    
                    # Apply the update
                    if self.todo_service:
                        updated_todo = await self.todo_service.update_todo(best_match_id, user_id, **update_data)
                        
                        if updated_todo:
                            # Convert to dict if it's an ORM object
                            if hasattr(updated_todo, 'to_dict'):
                                updated_todo_dict = updated_todo.to_dict()
                            else:
                                updated_todo_dict = updated_todo
                                
                            # Ensure all values are JSON serializable
                            for key, value in list(updated_todo_dict.items()):
                                if isinstance(value, datetime):
                                    updated_todo_dict[key] = value.isoformat()
                                elif hasattr(value, 'value'):  # Handle enums
                                    updated_todo_dict[key] = value.value
                                    
                            return {
                                "status": "success",
                                "message": f"Todo updated successfully",
                                "todo": updated_todo_dict
                            }
                        else:
                            return {"status": "error", "message": f"Failed to update todo with ID {best_match_id}"}
                    else:
                        return {"status": "error", "message": "Todo service unavailable"}
                
                except ValueError as e:
                    logger.error(f"Error parsing best match ID: {str(e)}")
                    return {"status": "error", "message": f"Could not identify todo: {str(e)}"}
            
            return {"status": "error", "message": "Database session unavailable"}
            
        except Exception as e:
            logger.error(f"Todo edit failed: {str(e)}")
            return {"status": "error", "message": f"Todo edit failed: {str(e)}"}