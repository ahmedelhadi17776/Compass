from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from crewai import Agent, Task, Crew
from langchain.tools import Tool
from Backend.ai_services.llm.llm_service import LLMService
from Backend.utils.logging_utils import get_logger
from pydantic import Field
from Backend.services.task_service import TaskService
from Backend.services.todo_service import TodoService
from Backend.services.daily_habits_service import DailyHabitService
from Backend.data_layer.database.models.task import TaskStatus, TaskPriority
from Backend.data_layer.database.models.calendar_event import RecurrenceType
from Backend.data_layer.database.models.todo import TodoStatus, TodoPriority
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class EntityCreationAgent:
    def __init__(self, db_session=None):
        self.agent = Agent(
            role="Entity Creation Specialist",
            goal="Create tasks, todos, and habits from natural language instructions",
            backstory="""I am an expert in task management and organization. I help users 
                        efficiently create and manage their tasks, todos, and habits by 
                        understanding natural language and extracting structured information.""",
            tools=[
                Tool(
                    name="create_task",
                    func=self.create_task,
                    description="Creates a new task from natural language"
                ),
                Tool(
                    name="create_todo",
                    func=self.create_todo,
                    description="Creates a new todo item from natural language"
                ),
                Tool(
                    name="create_habit",
                    func=self.create_habit,
                    description="Creates a new habit from natural language"
                ),
                Tool(
                    name="determine_entity_type",
                    func=self.determine_entity_type,
                    description="Determines entity type from user input"
                )
            ],
            verbose=True,
            allow_delegation=True  # Enable task delegation
        )
        
        self.ai_service = LLMService()
        self.db = db_session
        
        # Initialize services instead of repositories
        if db_session:
            # For TaskService, we need to provide a TaskRepository instance
            from Backend.data_layer.repositories.task_repository import TaskRepository
            task_repo = TaskRepository(db_session)
            self.task_service = TaskService(task_repo)
            
            # For TodoService and DailyHabitService similarly
            from Backend.data_layer.repositories.todo_repository import TodoRepository
            todo_repo = TodoRepository(db_session)
            self.todo_service = TodoService(todo_repo)
            
            from Backend.data_layer.repositories.daily_habits_repository import DailyHabitRepository
            habit_repo = DailyHabitRepository(db_session)
            self.habit_service = DailyHabitService(habit_repo)
        else:
            self.task_service = None
            self.todo_service = None
            self.habit_service = None
    
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
            # Set current_time once at the beginning
            current_time = datetime.utcnow()
            
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
                        
                        # Ensure due_date is not in the past
                        if due_date < current_time:
                            # If due date is in the past, set it to end of current day
                            logger.warning(f"Due date {due_date} is in the past, adjusting to future date")
                            adjusted_due_date = current_time.replace(hour=23, minute=59, second=59)
                            task_data["due_date"] = adjusted_due_date
                        else:
                            task_data["due_date"] = due_date
                    except ValueError:
                        # If parsing fails, remove invalid date
                        logger.warning(f"Invalid due_date format: {task_data['due_date']}")
                        task_data.pop("due_date", None)
                
                # Map task_data to parameters needed for TaskService.create_task
                task_creation_data = {
                    "title": task_data["title"],
                    "description": task_data.get("description", ""),
                    "creator_id": user_id,
                    "organization_id": 1,  # Default organization_id
                    "project_id": 1,  # Default project_id
                    "start_date": current_time,
                    "status": task_data["status"],
                    "priority": task_data["priority"],
                    "recurrence": task_data["recurrence"],
                    "due_date": task_data.get("due_date"),
                    # Safely handle None values for duration
                    "duration": float(task_data.get("estimated_hours")) if task_data.get("estimated_hours") is not None else 1.0,
                    # Safely handle None values for estimated_hours
                    "estimated_hours": float(task_data.get("estimated_hours")) if task_data.get("estimated_hours") is not None else None,
                    "dependencies": None  # Can be added if extracted from description
                }
                
                # Save to database if service is available
                if self.task_service is not None:
                    db_task = await self.task_service.create_task(**task_creation_data)
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
    
    async def create_habit(self, description: str, user_id: int = None) -> Dict[str, Any]:
        """Create a new habit from natural language description."""
        try:
            # Set current_time once at the beginning
            current_time = datetime.utcnow()
            
            # Use LLM to extract structured data
            habit_analysis = await self.ai_service.generate_response(
                prompt=f"""Extract structured habit information from this description:
Description: {description}

Extract and format as JSON with ONLY these fields:
- habit_name: A clear, concise name for the habit
- description: Full description with details
- start_day: Start date in YYYY-MM-DD format
- end_day: Optional end date in YYYY-MM-DD format""",
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
                
                # Convert date strings to date objects
                if "start_day" in habit_data and habit_data["start_day"]:
                    try:
                        start_day = datetime.strptime(habit_data["start_day"], "%Y-%m-%d").date()
                        # Ensure start_day is not in the past
                        if start_day < current_time.date():
                            logger.warning(f"Start day {start_day} is in the past, using current date")
                            habit_data["start_day"] = current_time.date()
                        else:
                            habit_data["start_day"] = start_day
                    except ValueError:
                        logger.warning(f"Invalid start_day format: {habit_data['start_day']}, using current date")
                        habit_data["start_day"] = current_time.date()
                else:
                    habit_data["start_day"] = current_time.date()
                
                if "end_day" in habit_data and habit_data["end_day"]:
                    try:
                        end_day = datetime.strptime(habit_data["end_day"], "%Y-%m-%d").date()
                        # Ensure end_day is after start_day
                        if end_day < habit_data["start_day"]:
                            # Set end_day to 30 days after start_day
                            logger.warning(f"End day {end_day} is before start day, adjusting to 30 days later")
                            habit_data["end_day"] = habit_data["start_day"] + timedelta(days=30)
                        else:
                            habit_data["end_day"] = end_day
                    except ValueError:
                        logger.warning(f"Invalid end_day format: {habit_data['end_day']}")
                        habit_data.pop("end_day", None)
                
                # Add metadata - use actual datetime objects, not strings
                habit_data["created_at"] = current_time
                habit_data["updated_at"] = current_time
                habit_data["current_streak"] = 0
                habit_data["longest_streak"] = 0
                habit_data["is_completed"] = False
                habit_data["user_id"] = user_id

                # Save to database if service is available
                if self.habit_service is not None:
                    db_habit = await self.habit_service.create_habit(**habit_data)
                    if db_habit:
                        habit_data["id"] = db_habit.id if hasattr(db_habit, 'id') else None
                
                # Ensure all values are JSON serializable
                # Convert datetime objects to strings
                for key, value in list(habit_data.items()):
                    if isinstance(value, datetime):
                        habit_data[key] = value.isoformat()
                    elif isinstance(value, date):  # Handle date objects
                        habit_data[key] = value.isoformat()
                    elif isinstance(value, (list, tuple)):
                        # Handle lists that might contain non-serializable items
                        habit_data[key] = [
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