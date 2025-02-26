from typing import Dict, List
from crewai import Crew, Task
from langchain.tools import Tool
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
        # Initialize agents with CrewAI-specific configurations
        self.task_analyzer = TaskAnalysisAgent()
        self.task_manager = TaskManagementAgent()
        self.workflow_optimizer = WorkflowOptimizationAgent()
        self.productivity_agent = ProductivityAgent()
        self.collaboration_agent = CollaborationAgent()
        self.resource_agent = ResourceAllocationAgent()

    async def process_task(self, task_data: Dict, team_data: Dict = None) -> Dict:
        """Orchestrate task processing using CrewAI framework."""
        try:
            # Define tasks for the crew
            tasks = [
                Task(
                    description="Analyze and classify the task",
                    agent=self.task_analyzer,
                    expected_output="Detailed task analysis and classification"
                ),
                Task(
                    description="Create and plan the task",
                    agent=self.task_manager,
                    expected_output="Task creation and planning details"
                ),
                Task(
                    description="Allocate resources for the task",
                    agent=self.resource_agent,
                    expected_output="Resource allocation plan"
                )
            ]
            
            if workflow_id := task_data.get('workflow_id'):
                tasks.append(
                    Task(
                        description="Optimize workflow for the task",
                        agent=self.workflow_optimizer,
                        expected_output="Workflow optimization recommendations"
                    )
                )

            if team_data:
                tasks.append(
                    Task(
                        description="Analyze team collaboration impact",
                        agent=self.collaboration_agent,
                        expected_output="Collaboration analysis and recommendations"
                    )
                )

            # Create and execute the crew
            crew = Crew(
                agents=[task.agent for task in tasks],
                tasks=tasks,
                verbose=True
            )

            results = await crew.kickoff()
            return results
        except Exception as e:
            logger.error(f"Task processing failed: {str(e)}")
            raise

    async def update_task(self, task_id: str, updates: Dict, current_state: Dict) -> Dict:
        """Coordinate task updates using CrewAI framework."""
        try:
            tasks = [
                Task(
                    description=f"Update task {task_id} with new information",
                    agent=self.task_manager,
                    expected_output="Updated task details"
                )
            ]

            if 'team_impact' in updates:
                tasks.append(
                    Task(
                        description="Analyze team impact of task updates",
                        agent=self.collaboration_agent,
                        expected_output="Team impact analysis"
                    )
                )

            if updates.get('workflow_changes'):
                tasks.append(
                    Task(
                        description="Re-optimize workflow after task updates",
                        agent=self.workflow_optimizer,
                        expected_output="Updated workflow optimization"
                    )
                )

            crew = Crew(
                agents=[task.agent for task in tasks],
                tasks=tasks,
                verbose=True
            )

            results = await crew.kickoff()
            return results
        except Exception as e:
            logger.error(f"Task update failed: {str(e)}")
            raise

    async def delete_task(self, task_id: str, task_data: Dict) -> Dict:
        """Coordinate task deletion using CrewAI framework."""
        try:
            tasks = [
                Task(
                    description=f"Analyze impact of deleting task {task_id}",
                    agent=self.task_manager,
                    expected_output="Task deletion impact analysis"
                )
            ]

            if workflow_id := task_data.get('workflow_id'):
                tasks.append(
                    Task(
                        description="Assess workflow impact of task deletion",
                        agent=self.workflow_optimizer,
                        expected_output="Workflow impact assessment"
                    )
                )

            crew = Crew(
                agents=[task.agent for task in tasks],
                tasks=tasks,
                verbose=True
            )

            results = await crew.kickoff()
            return results
        except Exception as e:
            logger.error(f"Task deletion failed: {str(e)}")
            raise