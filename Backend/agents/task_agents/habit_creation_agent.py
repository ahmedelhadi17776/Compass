from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
from crewai import Agent, Task, Crew
from langchain.tools import Tool
from Backend.ai_services.llm.llm_service import LLMService
from Backend.utils.logging_utils import get_logger
from pydantic import Field
from Backend.services.daily_habits_service import DailyHabitService
import json
import re
from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)


class HabitCreationAgent:
    def __init__(self, db_session=None):
        self.agent = Agent(
            role="Habit Creation Specialist",
            goal="Create habits from natural language instructions",
            backstory="""I am an expert in habit formation and tracking. I help users 
                        efficiently create and manage their habits by understanding natural 
                        language and extracting structured information.""",
            tools=[
                Tool(
                    name="create_habit",
                    func=self.create_habit,
                    description="Creates a new habit from natural language"
                )
            ],
            verbose=True,
            allow_delegation=True  # Enable task delegation
        )
        
        self.ai_service = LLMService()
        self.db = db_session
        
        # Initialize services instead of repositories
        if db_session:
            # For DailyHabitService, we need to provide a DailyHabitRepository instance
            from Backend.data_layer.repositories.daily_habits_repository import DailyHabitRepository
            habit_repo = DailyHabitRepository(db_session)
            self.habit_service = DailyHabitService(habit_repo)
        else:
            self.habit_service = None
    
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