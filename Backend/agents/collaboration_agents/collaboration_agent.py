from typing import Dict, List
from Backend.agents.base.base_agent import BaseAgent
from Backend.ai_services.llm.llm_service import LLMService
from Backend.utils.logging_utils import get_logger

logger = get_logger(__name__)

class CollaborationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Collaboration Coordinator",
            role="Team Collaboration Specialist",
            goal="Optimize team collaboration and communication",
            ai_service=LLMService(),
            backstory="I specialize in improving team dynamics and collaboration efficiency."
        )

    async def analyze_collaboration(
        self,
        team_data: Dict,
        tasks: List[Dict]
    ) -> Dict:
        """Analyze team collaboration patterns and suggest improvements."""
        try:
            analysis = await self.ai_service.generate_response(
                prompt="Analyze team collaboration patterns",
                context={
                    "team_data": team_data,
                    "tasks": tasks
                }
            )
            
            return {
                "collaboration_score": float(analysis.get("collaboration_score", 0.0)),
                "communication_patterns": analysis.get("communication_patterns", []),
                "team_dynamics": analysis.get("team_dynamics", {}),
                "recommendations": analysis.get("recommendations", []),
                "improvement_areas": analysis.get("improvement_areas", [])
            }
        except Exception as e:
            logger.error(f"Collaboration analysis failed: {str(e)}")
            raise