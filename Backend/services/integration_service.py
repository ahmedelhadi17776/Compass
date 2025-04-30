from typing import Dict, Optional
from Backend.orchestration.crew_orchestrator import CrewOrchestrator
from Backend.utils.logging_utils import get_logger

logger = get_logger(__name__)

class IntegrationService:
    def __init__(self):
        self.crew_orchestrator = CrewOrchestrator()

    async def process_with_agents(self, data: Dict, process_type: str) -> Dict:
        """Process data through AI agent crew."""
        try:
            result = await self.crew_orchestrator.process_task(data)
            return result
        except Exception as e:
            logger.error(f"Agent processing failed: {str(e)}")
            raise

    async def analyze_workflow(self, workflow_data: Dict) -> Dict:
        """Analyze workflow using AI agents."""
        try:
            result = await self.crew_orchestrator.analyze_workflow(workflow_data)
            return result
        except Exception as e:
            logger.error(f"Workflow analysis failed: {str(e)}")
            raise