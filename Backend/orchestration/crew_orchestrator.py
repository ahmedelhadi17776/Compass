from typing import Dict, List
from crewai import Crew
from Backend.agents.task_agents.task_analysis_agent import TaskAnalysisAgent
from Backend.agents.task_agents.task_management_agent import TaskManagementAgent
from Backend.agents.workflow_agents.workflow_optimization_agent import WorkflowOptimizationAgent
from Backend.agents.productivity_agents.productivity_agent import ProductivityAgent
from Backend.agents.collaboration_agents.collaboration_agent import CollaborationAgent
from Backend.agents.resource_agents.resource_allocation_agent import ResourceAllocationAgent
from Backend.utils.logging_utils import get_logger

logger = get_logger(__name__)

class CrewOrchestrator:
    def __init__(self):
        self.agents = {
            'task_analysis': TaskAnalysisAgent(),
            'task_management': TaskManagementAgent(),
            'workflow': WorkflowOptimizationAgent(),
            'productivity': ProductivityAgent(),
            'collaboration': CollaborationAgent(),
            'resource': ResourceAllocationAgent()
        }

    async def process_task(self, task_data: Dict, team_data: Dict = None) -> Dict:
        """Orchestrate comprehensive task processing with all agents."""
        try:
            results = {
                'analysis': await self.agents['task_analysis'].analyze_task(task_data),
                'management': await self.agents['task_management'].create_task(**task_data),
                'resources': await self.agents['resource'].allocate_resources(
                    task_data, 
                    team_data.get('available_resources', []) if team_data else []
                )
            }

            if workflow_id := task_data.get('workflow_id'):
                results['workflow'] = await self.agents['workflow'].optimize_workflow(workflow_id)

            if team_data:
                results['collaboration'] = await self.agents['collaboration'].analyze_collaboration(
                    team_data, 
                    [task_data]
                )

            return results
        except Exception as e:
            logger.error(f"Task processing failed: {str(e)}")
            raise

    async def update_task(self, task_id: str, updates: Dict, current_state: Dict) -> Dict:
        """Coordinate task updates across all relevant agents."""
        try:
            results = {
                'management': await self.agents['task_management'].update_task(
                    task_id, updates, current_state
                )
            }

            if 'team_impact' in updates:
                results['collaboration'] = await self.agents['collaboration'].analyze_collaboration(
                    updates.get('team_data', {}),
                    [current_state]
                )

            if updates.get('workflow_changes'):
                results['workflow'] = await self.agents['workflow'].optimize_workflow(
                    current_state.get('workflow_id')
                )

            return results
        except Exception as e:
            logger.error(f"Task update failed: {str(e)}")
            raise

    async def delete_task(self, task_id: str, task_data: Dict) -> Dict:
        """Coordinate task deletion and impact analysis."""
        try:
            deletion_impact = await self.agents['task_management'].delete_task(task_id, task_data)
            
            if not deletion_impact['can_delete']:
                return deletion_impact

            if workflow_id := task_data.get('workflow_id'):
                deletion_impact['workflow_impact'] = await self.agents['workflow'].optimize_workflow(
                    workflow_id
                )

            return deletion_impact
        except Exception as e:
            logger.error(f"Task deletion failed: {str(e)}")
            raise