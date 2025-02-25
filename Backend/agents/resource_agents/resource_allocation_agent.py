from typing import Dict, List
from Backend.agents.base.base_agent import BaseAgent
from Backend.ai_services.llm.llm_service import LLMService
from Backend.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ResourceAllocationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Resource Allocator",
            role="Resource Management Specialist",
            goal="Optimize resource allocation and workload distribution",
            ai_service=LLMService(),
            backstory="I specialize in analyzing and optimizing resource allocation for maximum efficiency."
        )

    async def allocate_resources(self, task_data: Dict, available_resources: List[Dict]) -> Dict:
        """Optimize resource allocation for tasks."""
        try:
            # Get resource allocation recommendation
            allocation = await self.ai_service.generate_response(
                prompt="Analyze and recommend resource allocation",
                context={
                    "task": task_data,
                    "available_resources": available_resources
                }
            )

            return {
                "recommended_resources": allocation.get("recommendations", []),
                "workload_distribution": allocation.get("workload_distribution", {}),
                "efficiency_score": float(allocation.get("efficiency_score", 0.0)),
                "risk_factors": allocation.get("risk_factors", [])
            }
        except Exception as e:
            logger.error(f"Resource allocation failed: {str(e)}")
            raise