from typing import Dict, Any
from crewai import Agent
from Backend.utils.logging_utils import get_logger
from Backend.ai_services.base.ai_service_base import AIServiceBase

logger = get_logger(__name__)

class BaseAgent(Agent):
    def __init__(
        self,
        name: str,
        role: str,
        goal: str,
        ai_service: AIServiceBase,
        backstory: str = None,
        verbose: bool = False
    ):
        super().__init__(
            name=name,
            role=role,
            goal=goal,
            backstory=backstory or f"I am an AI agent specialized in {role}",
            verbose=verbose
        )
        self.ai_service = ai_service

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task using the agent's AI service."""
        try:
            logger.info(f"Agent {self.name} executing task: {task.get('title', '')}")
            return await self.ai_service.process_task(task)
        except Exception as e:
            logger.error(f"Agent {self.name} failed to execute task: {str(e)}")
            raise