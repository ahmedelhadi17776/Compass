from typing import Dict, Any, List, Type, Optional
import logging
import asyncio
from pydantic import BaseModel, Field

from ai_services.agents.base_agent import BaseAgent, CompassAgentInputSchema, CompassAgentOutputSchema
from ai_services.agents.todo_agent import TodoAgent, SubtaskGeneratorAgent, DeadlineAdvisorAgent, PriorityOptimizerAgent

from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.base.base_io_schema import BaseIOSchema

logger = logging.getLogger(__name__)


class CoordinatorInputSchema(BaseIOSchema):
    """Input schema for the AgentOrchestrator."""
    target_type: str = Field(..., description="Type of target to process")
    target_id: str = Field(..., description="ID of the target to process")
    user_id: str = Field(..., description="ID of the user")
    option_id: Optional[str] = Field(
        None, description="ID of the option to process")
    target_data: Optional[Dict[str, Any]] = Field(
        None, description="Data for the target")


class CoordinatorOutputSchema(BaseIOSchema):
    """Output schema for the AgentOrchestrator."""
    options: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of available options")
    response: Optional[str] = Field(
        None, description="Response from processing an option")
    success: bool = Field(...,
                          description="Whether the operation was successful")
    error: Optional[str] = Field(
        None, description="Error message if the operation failed")


class AgentOrchestrator:
    """
    Orchestrates the selection and execution of specialized AI agents.
    Following the Atomic Agents pattern for agent coordination.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Map entity types to their primary agents
        self.entity_agents = {
            "todo": TodoAgent(),
            # Add more entity agents as they are implemented
            # "habit": HabitAgent(),
            # "event": EventAgent(),
            # "note": NoteAgent(),
        }

        # Map option IDs to specialized agents
        self.specialized_agents = {
            # Todo specialized agents
            "todo_subtasks": SubtaskGeneratorAgent(),
            "todo_deadline": DeadlineAdvisorAgent(),
            "todo_priority": PriorityOptimizerAgent(),

            # Add more specialized agents as they are implemented
            # Habit specialized agents
            # "habit_optimization": HabitOptimizerAgent(),
            # "habit_streak": StreakAnalyzerAgent(),
            # "habit_motivation": MotivationProviderAgent(),

            # Event specialized agents
            # "event_scheduling": SmartSchedulerAgent(),
            # "event_preparation": PreparationAdvisorAgent(),
            # "event_reminders": ReminderGeneratorAgent(),

            # Note specialized agents
            # "note_actions": ActionExtractorAgent(),
            # "note_summarize": NoteSummarizerAgent(),
            # "note_questions": QuestionGeneratorAgent(),
        }

        # Create an atomic agent coordinator
        self.coordinator = self._create_coordinator()

    def _create_coordinator(self):
        """Create an agent coordinator using Atomic Agents."""
        memory = AgentMemory()

        # System prompt generator for coordination decisions
        system_prompt = SystemPromptGenerator(
            background=[
                "You are IRIS Coordinator, the orchestration layer for the COMPASS AI system.",
                "You direct requests to specialized agents based on the target type and requested operation."
            ],
            steps=[
                "Identify the target type and requested operation.",
                "Select the appropriate specialized agent to handle the request.",
                "Route the request to the selected agent and return its response."
            ],
            output_instructions=[
                "Return the appropriate agent's response without modification.",
                "If no appropriate agent is found, return an error message."
            ]
        )

        # Initialize the coordinator
        return {
            "memory": memory,
            "system_prompt": system_prompt
        }

    async def get_options_for_target(
        self,
        target_type: str,
        target_id: str,
        target_data: Dict[str, Any],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get AI options for a specific target using the appropriate entity agent.
        """
        # Ensure target_type is a valid string
        if not target_type:
            self.logger.warning("Empty target_type provided")
            return []

        # Convert target_type to string if needed
        target_type_str = str(target_type).lower()

        # Convert target_id to string if needed
        target_id_str = str(target_id)

        # Convert user_id to string if needed
        user_id_str = str(user_id)

        agent = self.entity_agents.get(target_type_str)
        if not agent:
            self.logger.warning(
                f"No agent found for target type: {target_type_str}")
            return []

        return await agent.get_options(target_id_str, target_data, user_id_str)

    async def process_option(
        self,
        option_id: str,
        target_type: str,
        target_id: str,
        user_id: str,
        target_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a selected AI option using the appropriate specialized agent.
        """
        try:
            # Ensure parameters are valid strings
            if not option_id:
                return "Error: Missing option ID"

            if not target_type:
                return "Error: Missing target type"

            if not target_id:
                return "Error: Missing target ID"

            # Convert all parameters to strings
            option_id_str = str(option_id)
            target_type_str = str(target_type).lower()
            target_id_str = str(target_id)
            user_id_str = str(user_id)

            # Get the specialized agent for this option
            agent = self.specialized_agents.get(option_id_str)
            if not agent:
                self.logger.warning(
                    f"No specialized agent found for option: {option_id_str}")
                # Fall back to the entity agent
                agent = self.entity_agents.get(target_type_str)
                if not agent:
                    self.logger.error(
                        f"No agent found for target type: {target_type_str}")
                    return "Error: Could not find an appropriate agent to handle this request."

            # Process the option with the agent
            try:
                return await agent.process(option_id_str, target_type_str, target_id_str, user_id_str, target_data=target_data)
            except Exception as process_error:
                self.logger.error(
                    f"Error in agent.process: {str(process_error)}", exc_info=True)
                return f"Error processing your request: {str(process_error)}\n\nPlease try again or contact support if the problem persists."
        except Exception as e:
            self.logger.error(
                f"Unexpected error in process_option: {str(e)}", exc_info=True)
            return "Sorry, an unexpected error occurred while processing your request. Please try again later."
