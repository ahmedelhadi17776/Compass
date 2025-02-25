from typing import Dict, List
from Backend.agents.base.base_agent import BaseAgent
from Backend.ai_services.workflow_ai.workflow_optimization_service import WorkflowOptimizationService
from Backend.utils.logging_utils import get_logger

logger = get_logger(__name__)

class WorkflowOptimizationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Workflow Optimizer",
            role="Workflow Optimization Specialist",
            goal="Optimize workflow efficiency and identify improvements",
            ai_service=WorkflowOptimizationService(),
            backstory="I specialize in analyzing and optimizing workflows for maximum efficiency."
        )

    async def optimize_workflow(self, workflow_id: int) -> Dict:
        """Optimize workflow and provide recommendations."""
        try:
            optimization_result = await self.ai_service.optimize_workflow(workflow_id)
            patterns = await self.ai_service.analyze_workflow_patterns(workflow_id)
            
            return {
                **optimization_result,
                "identified_patterns": patterns["patterns"],
                "risk_assessment": patterns["risk_areas"],
                "success_probability": patterns["success_probability"]
            }
        except Exception as e:
            logger.error(f"Workflow optimization failed: {str(e)}")
            raise