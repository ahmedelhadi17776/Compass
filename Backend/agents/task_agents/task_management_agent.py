from typing import Dict, List, Optional
from crewai import Agent
from langchain.tools import Tool
from Backend.ai_services.llm.llm_service import LLMService
from Backend.utils.logging_utils import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)

class TaskManagementAgent(Agent):
    def __init__(self):
        # Initialize AI service
        self.ai_service = LLMService()

        # Define agent tools
        tools = [
            Tool.from_function(
                func=self.create_task,
                name="create_task",
                description="Creates a new task with AI-enhanced metadata and planning"
            ),
            Tool.from_function(
                func=self.update_task,
                name="update_task",
                description="Updates existing tasks with impact analysis and recommendations"
            ),
            Tool.from_function(
                func=self.plan_task_timeline,
                name="plan_timeline",
                description="Plans optimal task timeline considering team capacity and dependencies"
            )
        ]

        super().__init__(
            name="Task Manager",
            role="Task Management Specialist",
            goal="Optimize task lifecycle management and resource planning",
            backstory="I am an expert in task management and planning, using AI to enhance decision-making and ensure optimal workflow execution.",
            tools=tools,
            verbose=True
        )

    async def create_task(
        self,
        title: str,
        description: str,
        priority: Optional[str] = "medium",
        due_date: Optional[str] = None,
        assignee: Optional[Dict] = None
    ) -> Dict:
        """Create a new task with AI-enhanced metadata."""
        try:
            task_data = {
                "title": title,
                "description": description,
                "priority": priority,
                "due_date": due_date,
                "assignee": assignee,
                "status": "pending",
                "created_at": datetime.utcnow().isoformat()
            }

            # Get AI recommendations for task
            enhancement = await self.ai_service.generate_response(
                prompt="Enhance task creation with recommendations",
                context={"task": task_data}
            )

            return {
                **task_data,
                "estimated_hours": float(enhancement.get("estimated_hours", 0)),
                "suggested_skills": enhancement.get("required_skills", []),
                "recommended_priority": enhancement.get("recommended_priority", priority),
                "suggested_deadline": enhancement.get("suggested_deadline", due_date),
                "potential_blockers": enhancement.get("potential_blockers", [])
            }
        except Exception as e:
            logger.error(f"Task creation failed: {str(e)}")
            raise

    async def update_task(
        self,
        task_id: str,
        updates: Dict,
        current_state: Dict
    ) -> Dict:
        """Update task with AI validation and recommendations."""
        try:
            # Analyze impact of updates
            impact_analysis = await self.ai_service.generate_response(
                prompt="Analyze task update impact",
                context={
                    "current_state": current_state,
                    "proposed_updates": updates
                }
            )

            validated_updates = {
                **updates,
                "last_updated": datetime.utcnow().isoformat(),
                "update_impact": impact_analysis.get("impact_assessment", {}),
                "suggested_adjustments": impact_analysis.get("suggested_adjustments", [])
            }

            return validated_updates
        except Exception as e:
            logger.error(f"Task update failed: {str(e)}")
            raise

    async def plan_task_timeline(
        self,
        task_data: Dict,
        team_capacity: Dict,
        existing_tasks: List[Dict]
    ) -> Dict:
        """Plan optimal task timeline considering team capacity."""
        try:
            timeline = await self.ai_service.generate_response(
                prompt="Generate optimal task timeline",
                context={
                    "task": task_data,
                    "team_capacity": team_capacity,
                    "existing_tasks": existing_tasks
                }
            )

            return {
                "suggested_start_date": timeline.get("start_date"),
                "suggested_end_date": timeline.get("end_date"),
                "milestones": timeline.get("milestones", []),
                "dependencies_schedule": timeline.get("dependencies_schedule", {}),
                "resource_allocation": timeline.get("resource_allocation", {})
            }
        except Exception as e:
            logger.error(f"Task timeline planning failed: {str(e)}")
            raise

    async def delete_task(self, task_id: str, task_data: Dict) -> Dict:
        """Analyze impact of task deletion and provide recommendations."""
        try:
            deletion_impact = await self.ai_service.generate_response(
                prompt="Analyze task deletion impact",
                context={"task": task_data}
            )

            return {
                "can_delete": deletion_impact.get("can_delete", True),
                "impact_assessment": deletion_impact.get("impact_assessment", {}),
                "affected_dependencies": deletion_impact.get("affected_dependencies", []),
                "recommended_actions": deletion_impact.get("recommended_actions", [])
            }
        except Exception as e:
            logger.error(f"Task deletion analysis failed: {str(e)}")
            raise