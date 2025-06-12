from typing import Dict, Any, List, Optional
import logging

from ai_services.agents.base_agent import BaseAgent, BaseIOSchema
from pydantic import Field, BaseModel

from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator


class TodoAgentInputSchema(BaseIOSchema):
    """Input schema for TodoAgent."""
    todo_id: str = Field(..., description="ID of the todo")
    user_id: str = Field(..., description="ID of the user")


class TodoAgentOutputSchema(BaseIOSchema):
    """Output schema for TodoAgent."""
    options: List[Dict[str, Any]
                  ] = Field(..., description="List of AI options for the todo")


class TodoAgent(BaseAgent):
    """
    Agent for handling todo-related AI operations.
    Follows Atomic Agents pattern for entity-specific agents.
    """

    def __init__(self):
        super().__init__()

        # Create specialized system prompt for todo agent
        self.system_prompt_generator = SystemPromptGenerator(
            background=[
                "You are IRIS, an AI assistant for the COMPASS productivity app.",
                "You specialize in helping users manage their todos effectively."
            ],
            steps=[
                "Analyze the todo to understand its context, priority, and deadline.",
                "Identify ways you can help the user with this todo."
            ],
            output_instructions=[
                "Provide practical, actionable advice.",
                "Be specific to the todo's details when possible."
            ]
        )

    async def get_options(
        self,
        target_id: str,
        target_data: Dict[str, Any],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get AI options for a todo."""
        # Log that we're getting options
        self.logger.info(f"TodoAgent.get_options called for todo {target_id}")

        # Default options that we can always provide
        default_options = [
            {
                "id": "todo_subtasks",
                "title": "Generate Subtasks",
                "description": "Break down this todo into smaller, manageable subtasks."
            },
            {
                "id": "todo_deadline",
                "title": "Deadline-based Advice",
                "description": "Get recommendations based on the deadline and your schedule."
            },
            {
                "id": "todo_priority",
                "title": "Priority & Motivation",
                "description": "Get insights on priority and motivation strategies."
            }
        ]

        # Check if target_data is empty (could happen if MCP doesn't work)
        if not target_data or not isinstance(target_data, dict):
            self.logger.warning(
                f"Empty or invalid target_data for todo {target_id}. Using fallback options.")
            self.logger.warning(f"target_data: {target_data}")
            return default_options

        # If we have actual data, we could potentially customize options based on todo properties
        # For now, we'll use the same options but log that we have data
        self.logger.info(f"Got valid data for todo {target_id}")

        # In the future, we could check todo properties and add/remove options
        # Example: if 'due_date' in target_data and target_data['due_date']:
        #     # Add deadline-specific options

        return default_options


class SubtaskGeneratorAgent(BaseAgent):
    """
    Specialized agent for generating subtasks from a todo.
    """

    def __init__(self):
        super().__init__()

        # Create specialized system prompt for subtask generation
        self.system_prompt_generator = SystemPromptGenerator(
            background=[
                "You are IRIS, an AI assistant for the COMPASS productivity app.",
                "You specialize in breaking down todos into manageable subtasks."
            ],
            steps=[
                "Analyze the todo to understand what it involves.",
                "Break it down into 3-5 logical, sequential subtasks.",
                "Ensure each subtask is specific and actionable."
            ],
            output_instructions=[
                "Provide subtasks as a numbered list.",
                "Include a brief recommendation on how to approach these subtasks."
            ]
        )

    async def process(
        self,
        option_id: str,
        target_type: str,
        target_id: str,
        user_id: str,
        *,
        target_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate subtasks for a todo."""
        try:
            # Get todo data if not provided
            if not target_data:
                target_data = await self._get_target_data(target_type, target_id, user_id)

            # Safely access dictionary properties
            title = "this task"
            description = ""

            if isinstance(target_data, dict):
                title = target_data.get("title", "this task")
                description = target_data.get("description", "")
            else:
                self.logger.warning(
                    f"target_data is not a dictionary: {type(target_data)}")

            # Direct LLM generation with our system prompt
            prompt = f"Generate a list of 3-5 subtasks for this todo:\nTodo: {title}\nDescription: {description}\n\nPlease format your response with a numbered list of subtasks, followed by a brief recommendation on how to approach them."

            # Use our run method which directly calls the LLM service
            result = await self.run(
                {"prompt": prompt},
                user_id
            )

            if result["status"] == "success":
                return result["response"]
            else:
                # Fall back to direct LLM call
                return await self._generate_response_with_tools(
                    f"Break down this todo into smaller, manageable subtasks:\nTodo: {title}\nDescription: {description}",
                    user_id,
                    {"temperature": 0.7, "top_p": 0.9}
                )

        except Exception as e:
            self.logger.error(
                f"Error in SubtaskGeneratorAgent.process: {str(e)}", exc_info=True)
            return f"Sorry, I encountered an error while generating subtasks: {str(e)}"


class DeadlineAdvisorAgent(BaseAgent):
    """
    Specialized agent for providing deadline-based advice.
    """

    def __init__(self):
        super().__init__()

        # Create specialized system prompt for deadline advice
        self.system_prompt_generator = SystemPromptGenerator(
            background=[
                "You are IRIS, an AI assistant for the COMPASS productivity app.",
                "You specialize in providing deadline-based advice for todos."
            ],
            steps=[
                "Analyze the todo's due date and priority.",
                "Consider how it fits into the user's schedule.",
                "Develop time management strategies specific to this task."
            ],
            output_instructions=[
                "Provide specific recommendations for managing this deadline.",
                "Keep your response under 150 words.",
                "Include time management strategies and prioritization tips."
            ]
        )

    async def process(
        self,
        option_id: str,
        target_type: str,
        target_id: str,
        user_id: str,
        *,
        target_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate deadline advice for a todo."""
        try:
            # Get todo data if not provided
            if not target_data:
                target_data = await self._get_target_data(target_type, target_id, user_id)

            # Safely access dictionary properties
            title = "this task"
            due_date = "unknown"
            priority = "medium"
            status = "pending"

            if isinstance(target_data, dict):
                title = target_data.get("title", "this task")
                due_date = target_data.get("due_date", "unknown")
                priority = target_data.get("priority", "medium")
                status = target_data.get("status", "pending")
            else:
                self.logger.warning(
                    f"target_data is not a dictionary: {type(target_data)}")

            # Create prompt that encourages tool use
            prompt = f"""
You are IRIS, an AI assistant for the COMPASS productivity app.
I need deadline-based advice for this todo. You can use tools to check my calendar or other tasks.

Todo: {title}
Due date: {due_date}
Priority: {priority}
Status: {status}

Please provide specific recommendations on how to approach this task based on its deadline. Consider time management strategies, scheduling tips, and how to prioritize it among other tasks. Keep your response under 150 words.
"""

            # Generate response with model parameters for better advice
            model_params = {
                "temperature": 0.5,
                "top_p": 0.8
            }
            return await self._generate_response_with_tools(prompt, user_id, model_params)
        except Exception as e:
            self.logger.error(
                f"Error in DeadlineAdvisorAgent.process: {str(e)}", exc_info=True)
            return f"Sorry, I encountered an error while generating deadline advice: {str(e)}"


class PriorityOptimizerAgent(BaseAgent):
    """
    Specialized agent for optimizing task priority.
    """

    def __init__(self):
        super().__init__()

        # Create specialized system prompt for priority optimization
        self.system_prompt_generator = SystemPromptGenerator(
            background=[
                "You are IRIS, an AI assistant for the COMPASS productivity app.",
                "You specialize in optimizing task priorities and providing motivation."
            ],
            steps=[
                "Analyze the todo's priority, description, and due date.",
                "Evaluate if the current priority setting is appropriate.",
                "Develop motivation strategies specific to this task."
            ],
            output_instructions=[
                "Provide insights on whether the priority is appropriate.",
                "Offer specific motivation strategies for completing this task.",
                "Keep your response under 150 words and make it actionable."
            ]
        )

    async def process(
        self,
        option_id: str,
        target_type: str,
        target_id: str,
        user_id: str,
        *,
        target_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate priority and motivation advice for a todo."""
        try:
            # Get todo data if not provided
            if not target_data:
                target_data = await self._get_target_data(target_type, target_id, user_id)

            # Safely access dictionary properties
            title = "this task"
            priority = "medium"
            description = ""
            due_date = "unknown"

            if isinstance(target_data, dict):
                title = target_data.get("title", "this task")
                priority = target_data.get("priority", "medium")
                description = target_data.get("description", "")
                due_date = target_data.get("due_date", "unknown")
            else:
                self.logger.warning(
                    f"target_data is not a dictionary: {type(target_data)}")

            # Create prompt that encourages tool use
            prompt = f"""
You are IRIS, an AI assistant for the COMPASS productivity app.
I need priority and motivation advice for this todo. You can use tools to understand the context of my other work.

Todo: {title}
Description: {description}
Current priority: {priority}
Due date: {due_date}

Please provide insights on whether this priority is appropriate, and offer specific motivation strategies for completing this task. Keep your response under 150 words and make it actionable.
"""

            # Generate response with model parameters for better motivation advice
            model_params = {
                "temperature": 0.6,
                "top_p": 0.85
            }
            return await self._generate_response_with_tools(prompt, user_id, model_params)
        except Exception as e:
            self.logger.error(
                f"Error in PriorityOptimizerAgent.process: {str(e)}", exc_info=True)
            return f"Sorry, I encountered an error while generating priority advice: {str(e)}"
