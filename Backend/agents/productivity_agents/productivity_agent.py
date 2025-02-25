from typing import Dict, List
from Backend.agents.base.base_agent import BaseAgent
from Backend.ai_services.productivity_ai.productivity_service import ProductivityService
from Backend.utils.logging_utils import get_logger

logger = get_logger(__name__)

class ProductivityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Productivity Analyzer",
            role="Productivity Optimization Specialist",
            goal="Analyze and optimize task and workflow productivity",
            ai_service=ProductivityService(),
            backstory="I specialize in analyzing productivity patterns and suggesting optimizations."
        )

    async def analyze_productivity(
        self,
        tasks: List[Dict],
        time_period: str = "daily"
    ) -> Dict:
        """Analyze productivity patterns and provide insights."""
        try:
            patterns = await self.ai_service.analyze_task_patterns(tasks, time_period)
            workflow_data = self._aggregate_workflow_data(tasks)
            efficiency = await self.ai_service.analyze_workflow_efficiency(workflow_data)
            
            return {
                "task_patterns": patterns,
                "workflow_efficiency": efficiency,
                "recommendations": self._generate_productivity_recommendations(
                    patterns,
                    efficiency
                )
            }
        except Exception as e:
            logger.error(f"Productivity analysis failed: {str(e)}")
            raise

    def _aggregate_workflow_data(self, tasks: List[Dict]) -> Dict:
        """Aggregate tasks into workflow data."""
        return {
            "steps": [self._convert_task_to_step(task) for task in tasks],
            "estimated_duration": sum(task.get("estimated_hours", 0) for task in tasks),
            "actual_duration": sum(task.get("actual_hours", 0) for task in tasks)
        }

    def _convert_task_to_step(self, task: Dict) -> Dict:
        """Convert task data to workflow step format."""
        return {
            "name": task.get("title", "Unnamed Task"),
            "description": task.get("description", ""),
            "duration": task.get("actual_hours", 0),
            "status": task.get("status", "pending")
        }

    def _generate_productivity_recommendations(
        self,
        patterns: Dict,
        efficiency: Dict
    ) -> List[str]:
        """Generate productivity recommendations."""
        recommendations = []
        
        if patterns["metrics"]["completion_rate"] < 0.7:
            recommendations.append("Task completion rate needs improvement")
        
        if efficiency["efficiency_metrics"]["efficiency_ratio"] < 0.8:
            recommendations.append("Workflow efficiency could be optimized")
            
        return recommendations