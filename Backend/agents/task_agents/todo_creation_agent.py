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


class TodoCreationAgent:
    def __init__(self, db_session=None):
        self.agent = Agent(
            role="Todo Creation Specialist",
            goal="Create todos from natural language instructions",
            backstory="""I am an expert in todo management and organization. I help users 
                        efficiently create and manage their todos by understanding natural 
                        language and extracting structured information.""",
            tools=[
                Tool(
                    name="create_todo",
                    func=self.create_todo,
                    description="Creates a new todo item from natural language"
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