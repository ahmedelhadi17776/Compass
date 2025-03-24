from typing import Dict, List, Optional, Any
from datetime import datetime
from crewai import Agent
from langchain.tools import Tool
from Backend.ai_services.llm.llm_service import LLMService
from Backend.utils.logging_utils import get_logger
from pydantic import Field
from Backend.data_layer.repositories.task_repository import TaskRepository
from Backend.data_layer.repositories.todo_repository import TodoRepository
from Backend.data_layer.repositories.daily_habits_repository import DailyHabitRepository
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority
from Backend.data_layer.database.models.calendar_event import RecurrenceType
from Backend.data_layer.database.models.todo import TodoStatus, TodoPriority
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class EntityCreationAgent(Agent):
    """Agent specialized in creating various entities (tasks, todos, habits) from natural language requests."""
    
    ai_service: LLMService = Field(default_factory=LLMService)
    db: Optional[AsyncSession] = Field(default=None)
    task_repository: Optional[TaskRepository] = Field(default=None)
    todo_repository: Optional[TodoRepository] = Field(default=None)
    habit_repository: Optional[DailyHabitRepository] = Field(default=None)
    
    def __init__(self, db_session=None):
        # Define agent tools
        tools = [
            Tool.from_function(
                func=self.create_task,
                name="create_task",
                description="Creates a new task from natural language description"
            ),
            Tool.from_function(
                func=self.create_todo,
                name="create_todo",
                description="Creates a new todo item from natural language description"
            ),
            Tool.from_function(
                func=self.create_habit,
                name="create_habit",
                description="Creates a new habit from natural language description"
            ),
            Tool.from_function(
                func=self.determine_entity_type,
                name="determine_entity_type",
                description="Determines what type of entity to create based on user input"
            )
        ]
        
        # Initialize agent with base properties
        super().__init__(
            role="Entity Creation Specialist",
            goal="Create tasks, todos, and habits from natural language instructions",
            backstory="I help users effortlessly create and organize their tasks, todos, and habits by understanding their natural language descriptions and capturing all relevant details.",
            tools=tools,
            verbose=True,
            allow_delegation=False,
            memory=True
        )
        
        # Initialize repositories if db_session is provided
        if db_session:
            self.db = db_session
            self.task_repository = TaskRepository(db_session)
            self.todo_repository = TodoRepository(db_session)
            self.habit_repository = DailyHabitRepository(db_session)
    
    async def determine_entity_type(self, user_input: str) -> Dict[str, Any]:
        """Determine what type of entity the user wants to create."""
        try:
            # Perform basic keyword matching first for common cases
            user_input_lower = user_input.lower()
            
            # Task keywords
            if any(kw in user_input_lower for kw in ["task", "project", "deadline", "due date", "assign", "quarterly report"]):
                return {
                    "entity_type": "task",
                    "explanation": "Determined as task based on keywords related to projects, deadlines, or formal work items."
                }
            
            # Todo keywords
            if any(kw in user_input_lower for kw in ["todo", "to-do", "to do", "checklist", "shopping list", "remind me to"]):
                return {
                    "entity_type": "todo",
                    "explanation": "Determined as todo based on keywords related to simple checklist items or reminders."
                }
            
            # Habit keywords
            if any(kw in user_input_lower for kw in ["habit", "daily", "routine", "every day", "weekly", "regularly"]):
                return {
                    "entity_type": "habit",
                    "explanation": "Determined as habit based on keywords related to recurring activities or routines."
                }
            
            # Fall back to LLM for more complex cases
            entity_analysis = await self.ai_service.generate_response(
                prompt=f"""Analyze this user input and determine what type of entity they want to create:
User Input: {user_input}

Respond with one of:
- task: For project-related items with deadlines and complex details (examples: reports, assignments, project milestones)
- todo: For simple to-do list items (examples: buy groceries, call mom, send email)
- habit: For recurring daily/weekly activities to build consistency (examples: exercise, meditation, reading)

Please determine the entity type and provide a brief explanation why.""",
                context={
                    "system_message": "You are an entity classification AI. Determine if the user wants to create a task, todo, or habit."
                }
            )
            
            # Parse response
            response_text = entity_analysis.get("text", "")
            entity_type = "task"  # Default
            
            if "todo" in response_text.lower():
                entity_type = "todo"
            elif "habit" in response_text.lower():
                entity_type = "habit"
            
            return {
                "entity_type": entity_type,
                "explanation": response_text
            }
        except Exception as e:
            logger.error(f"Entity type determination failed: {str(e)}")
            return {"entity_type": "task", "explanation": f"Defaulting to task due to error: {str(e)}"}
    
    async def create_task(self, description: str, user_id: int = None) -> Dict[str, Any]:
        """Create a new task from natural language description."""
        try:
            # Use LLM to extract structured data from description
            task_analysis = await self.ai_service.generate_response(
                prompt=f"""Extract structured task information from this description:
Description: {description}

Extract and format as JSON:
- title: A clear, concise title for the task
- description: Full description with details
- priority: high, medium, or low
- due_date: Extract any mentioned deadline (YYYY-MM-DD format)
- estimated_hours: Numerical estimate of hours needed (if mentioned)
- tags: Array of relevant tags
- status: Default is "todo", other options are "in_progress", "completed", "cancelled", "blocked", "under_review", "deferred" """,
                context={
                    "system_message": "You are a task extraction AI. Extract structured task information from natural language."
                }
            )
            
            try:
                # Parse the JSON response
                response_text = task_analysis.get("text", "")
                
                # Extract JSON from markdown if needed
                if "```json" in response_text:
                    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                
                task_data = json.loads(response_text)
                
                # Add metadata - use actual datetime objects, not strings
                current_time = datetime.utcnow()
                task_data["created_at"] = current_time
                task_data["updated_at"] = current_time
                
                # Map status string to proper TaskStatus enum value
                # Map common status terms to our enum values
                status_mapping = {
                    "pending": "TODO",
                    "todo": "TODO",
                    "to do": "TODO",
                    "to-do": "TODO",
                    "in progress": "IN_PROGRESS",
                    "in-progress": "IN_PROGRESS",
                    "inprogress": "IN_PROGRESS",
                    "done": "COMPLETED",
                    "complete": "COMPLETED",
                    "completed": "COMPLETED",
                    "cancel": "CANCELLED",
                    "canceled": "CANCELLED",
                    "cancelled": "CANCELLED",
                    "block": "BLOCKED",
                    "blocked": "BLOCKED",
                    "review": "UNDER_REVIEW",
                    "under review": "UNDER_REVIEW",
                    "under-review": "UNDER_REVIEW",
                    "defer": "DEFERRED",
                    "deferred": "DEFERRED"
                }
                
                if "status" in task_data:
                    status_str = task_data["status"].lower()
                    if status_str in status_mapping:
                        enum_value = status_mapping[status_str]
                        try:
                            task_data["status"] = TaskStatus[enum_value]
                        except KeyError:
                            logger.warning(f"Invalid status mapping: {enum_value}, using TODO")
                            task_data["status"] = TaskStatus.TODO
                    else:
                        # Try direct enum lookup
                        try:
                            task_data["status"] = TaskStatus[status_str.upper()]
                        except KeyError:
                            logger.warning(f"Invalid status: {status_str}, using TODO")
                            task_data["status"] = TaskStatus.TODO
                else:
                    task_data["status"] = TaskStatus.TODO
                
                # Convert priority string to enum value
                priority_mapping = {
                    "low": "LOW",
                    "medium": "MEDIUM",
                    "mid": "MEDIUM",
                    "high": "HIGH",
                    "urgent": "URGENT",
                    "critical": "URGENT"
                }
                
                if "priority" in task_data:
                    priority_str = task_data["priority"].lower()
                    if priority_str in priority_mapping:
                        enum_value = priority_mapping[priority_str]
                        try:
                            task_data["priority"] = TaskPriority[enum_value]
                        except KeyError:
                            logger.warning(f"Invalid priority mapping: {enum_value}, using MEDIUM")
                            task_data["priority"] = TaskPriority.MEDIUM
                    else:
                        # Try direct enum lookup
                        try:
                            task_data["priority"] = TaskPriority[priority_str.upper()]
                        except KeyError:
                            logger.warning(f"Invalid priority: {priority_str}, using MEDIUM")
                            task_data["priority"] = TaskPriority.MEDIUM
                else:
                    task_data["priority"] = TaskPriority.MEDIUM
                
                # Set recurrence type to NONE by default
                task_data["recurrence"] = RecurrenceType.NONE
                
                # Convert due_date string to datetime object if present
                if "due_date" in task_data and task_data["due_date"]:
                    try:
                        # Parse YYYY-MM-DD format
                        due_date = datetime.strptime(task_data["due_date"], "%Y-%m-%d")
                        task_data["due_date"] = due_date
                    except ValueError:
                        # If parsing fails, remove invalid date
                        logger.warning(f"Invalid due_date format: {task_data['due_date']}")
                        task_data.pop("due_date", None)
                
                # Add required fields
                task_data["creator_id"] = user_id  # Use the user_id as creator_id
                task_data["organization_id"] = 1  # Default organization_id
                task_data["project_id"] = 1  # Default project_id
                
                # Set status_updated_at to current time
                task_data["status_updated_at"] = current_time
                
                # Convert string fields to expected types for TaskRepository.create()
                # The create method expects start_date and possibly duration
                task_data["start_date"] = current_time
                if "estimated_hours" in task_data and task_data["estimated_hours"]:
                    task_data["duration"] = float(task_data["estimated_hours"])
                
                # Save to database if repository is available
                if self.task_repository is not None:
                    start_date = task_data.pop("start_date", current_time)
                    duration = task_data.pop("duration", None)
                    db_task = await self.task_repository.create(start_date=start_date, duration=duration, **task_data)
                    task_data["id"] = db_task.id
                
                # Ensure all values are JSON serializable
                # Convert datetime objects to strings
                for key, value in list(task_data.items()):
                    if isinstance(value, datetime):
                        task_data[key] = value.isoformat()
                    elif hasattr(value, "name"):  # Check if it's an enum
                        task_data[key] = value.name
                    elif isinstance(value, (list, tuple)):
                        # Handle lists that might contain non-serializable items
                        task_data[key] = [
                            item.name if hasattr(item, "name") else 
                            item.isoformat() if hasattr(item, "isoformat") else 
                            item 
                            for item in value
                        ]
                
                return {
                    "status": "success",
                    "message": f"Task '{task_data['title']}' created successfully",
                    "task": task_data
                }
            except Exception as e:
                logger.error(f"Error parsing task data: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Could not parse task information: {str(e)}",
                    "raw_response": task_analysis.get("text", "")
                }
        except Exception as e:
            logger.error(f"Task creation failed: {str(e)}")
            return {"status": "error", "message": f"Task creation failed: {str(e)}"}
    
    async def create_todo(self, description: str, user_id: int = None) -> Dict[str, Any]:
        """Create a new todo item from natural language description."""
        try:
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
                current_time = datetime.utcnow()
                todo_data["created_at"] = current_time
                todo_data["updated_at"] = current_time
                todo_data["completed"] = False
                todo_data["user_id"] = user_id
                
                # Set status to PENDING by default (assuming TodoStatus.PENDING exists)
                # Map common status terms to TodoStatus enum values
                status_mapping = {
                    "pending": "PENDING",
                    "todo": "PENDING",
                    "to do": "PENDING",
                    "to-do": "PENDING",
                    "in progress": "IN_PROGRESS",
                    "in-progress": "IN_PROGRESS",
                    "inprogress": "IN_PROGRESS",
                    "done": "COMPLETED",
                    "complete": "COMPLETED",
                    "completed": "COMPLETED"
                }
                
                # Check if TodoStatus.PENDING exists, otherwise use something like IN_PROGRESS
                try:
                    todo_data["status"] = TodoStatus.PENDING
                except AttributeError:
                    # If PENDING doesn't exist, try other common status values
                    for status_name in ["TODO", "NEW", "ACTIVE"]:
                        try:
                            todo_data["status"] = getattr(TodoStatus, status_name)
                            break
                        except AttributeError:
                            continue
                    else:
                        # If no matching status found, use the first enum value as default
                        todo_data["status"] = list(TodoStatus)[0]
                
                # Convert priority string to enum value
                priority_mapping = {
                    "low": "LOW",
                    "medium": "MEDIUM",
                    "mid": "MEDIUM",
                    "high": "HIGH",
                    "urgent": "HIGH",  # Map urgent to HIGH if URGENT doesn't exist
                    "critical": "HIGH"
                }
                
                if "priority" in todo_data:
                    priority_str = todo_data["priority"].lower()
                    if priority_str in priority_mapping:
                        enum_value = priority_mapping[priority_str]
                        try:
                            todo_data["priority"] = TodoPriority[enum_value]
                        except KeyError:
                            logger.warning(f"Invalid priority mapping: {enum_value}, using MEDIUM")
                            todo_data["priority"] = TodoPriority.MEDIUM
                    else:
                        # Try direct enum lookup
                        try:
                            todo_data["priority"] = TodoPriority[priority_str.upper()]
                        except KeyError:
                            logger.warning(f"Invalid priority: {priority_str}, using MEDIUM")
                            todo_data["priority"] = TodoPriority.MEDIUM
                else:
                    todo_data["priority"] = TodoPriority.MEDIUM
                
                # Convert due_date string to datetime object if present
                if "due_date" in todo_data and todo_data["due_date"]:
                    try:
                        # Parse YYYY-MM-DD format
                        due_date = datetime.strptime(todo_data["due_date"], "%Y-%m-%d")
                        todo_data["due_date"] = due_date
                    except ValueError:
                        # If parsing fails, remove invalid date
                        logger.warning(f"Invalid due_date format: {todo_data['due_date']}")
                        todo_data.pop("due_date", None)
                
                # Save to database if repository is available
                if self.todo_repository is not None:
                    db_todo = await self.todo_repository.create(**todo_data)
                    todo_data["id"] = db_todo.id
                
                # Ensure all values are JSON serializable
                # Convert datetime objects to strings
                for key, value in list(todo_data.items()):
                    if isinstance(value, datetime):
                        todo_data[key] = value.isoformat()
                    elif hasattr(value, "name"):  # Check if it's an enum
                        todo_data[key] = value.name
                    elif isinstance(value, (list, tuple)):
                        # Handle lists that might contain non-serializable items
                        todo_data[key] = [
                            item.name if hasattr(item, "name") else 
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
    
    async def create_habit(self, description: str, user_id: int = None) -> Dict[str, Any]:
        """Create a new habit from natural language description."""
        try:
            # Use LLM to extract structured data
            habit_analysis = await self.ai_service.generate_response(
                prompt=f"""Extract structured habit information from this description:
Description: {description}

Extract and format as JSON with ONLY these fields:
- habit_name: A clear, concise name for the habit
- description: Full description with details
- tags: Array of relevant tags

Note: DO NOT include frequency, target_completion_time, difficulty, or motivation fields as they are not supported by the system.""",
                context={
                    "system_message": "You are a habit extraction AI. Extract structured habit information from natural language, using only the supported fields."
                }
            )
            
            try:
                # Parse the JSON response
                response_text = habit_analysis.get("text", "")
                
                # Extract JSON from markdown if needed
                if "```json" in response_text:
                    json_match = re.search(r'```json\n(.*?)\n```', response_text, re.DOTALL)
                    if json_match:
                        response_text = json_match.group(1)
                
                habit_data = json.loads(response_text)
                
                # Adapt field names to match the model requirements
                if "name" in habit_data:
                    habit_data["habit_name"] = habit_data.pop("name")
                
                # Add metadata - use actual datetime objects, not strings
                current_time = datetime.utcnow()
                habit_data["created_at"] = current_time
                habit_data["current_streak"] = 0
                habit_data["longest_streak"] = 0
                habit_data["is_completed"] = False
                habit_data["start_day"] = current_time.date()
                habit_data["user_id"] = user_id
                
                # Filter out fields not accepted by the DailyHabit model
                # These are common fields from LLM extraction that might not be in the model
                fields_to_remove = [
                    "frequency", 
                    "target_completion_time", 
                    "difficulty", 
                    "motivation"
                ]
                
                # Create a clean copy with only fields that should be passed to the repository
                clean_habit_data = {k: v for k, v in habit_data.items() 
                                    if k not in fields_to_remove}
                
                # Save to database if repository is available
                if self.habit_repository is not None:
                    db_habit = await self.habit_repository.create(**clean_habit_data)
                    habit_data["id"] = db_habit.id
                
                # Ensure all values are JSON serializable
                # Convert datetime objects to strings
                for key, value in list(habit_data.items()):
                    if isinstance(value, datetime):
                        habit_data[key] = value.isoformat()
                    elif hasattr(value, "name"):  # Check if it's an enum
                        habit_data[key] = value.name
                    elif isinstance(value, (list, tuple)):
                        # Handle lists that might contain non-serializable items
                        habit_data[key] = [
                            item.name if hasattr(item, "name") else 
                            item.isoformat() if hasattr(item, "isoformat") else 
                            item 
                            for item in value
                        ]
                
                return {
                    "status": "success",
                    "message": f"Habit '{habit_data['habit_name']}' created successfully",
                    "habit": habit_data
                }
            except Exception as e:
                logger.error(f"Error parsing habit data: {str(e)}")
                return {
                    "status": "error",
                    "message": f"Could not parse habit information: {str(e)}",
                    "raw_response": habit_analysis.get("text", "")
                }
        except Exception as e:
            logger.error(f"Habit creation failed: {str(e)}")
            return {"status": "error", "message": f"Habit creation failed: {str(e)}"} 