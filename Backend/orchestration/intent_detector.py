from Backend.ai_services.llm.llm_service import LLMService
from typing import Dict, Optional, Any
import json


class IntentDetector:
    """
    Dynamically detects user intent from input using LLM reasoning.
    """

    def __init__(self):
        self.llm_service = LLMService()

    async def detect_intent(self, user_input: str, database_summary: Dict[str, Any]) -> Dict[str, str]:
        """
        Uses the LLM to dynamically identify user intent and relevant entities.
        
        Args:
            user_input: The user's query string
            database_summary: Context data from various domains
            
        Returns:
            Dict containing:
                - intent: One of: retrieve, analyze, summarize, plan
                - target: The domain target (tasks, todos, etc.)
                - description: Brief explanation of the user's goal
        """
        prompt = f"""
        You are an AI assistant responsible for understanding and acting on user requests.
        Based on the following information, identify the user's intent and target data:

        User Input: "{user_input}"
        Database Summary: {json.dumps(database_summary)}

        Classify the intent:
        - summarize: Provide a summary 
        - retrieve: To fetch information (e.g., "Show my tasks").
        - analyze: To generate insights (e.g., "Summarize my progress").
        - plan: To schedule, organize.
        
        Respond with a JSON object:
        {{
            "intent": "retrieve/analyze/summarize/plan",
            "target": "tasks/todos/habits",
            "description": "A short explanation of the user's goal"
        }}
        """

        # Use the LLM to reason about intent
        result = await self.llm_service.generate_response(prompt)
        
        try:
            # Parse the JSON response from the LLM
            intent_data = json.loads(result.get("text", "{}"))
            
            # Validate the required fields are present
            if not all(k in intent_data for k in ["intent", "target", "description"]):
                # Set default values if parsing failed
                return {
                    "intent": "retrieve",  # Default to retrieve as safest option
                    "target": next(iter(database_summary.keys()), "tasks"),  # Pick first available domain
                    "description": "Retrieving information based on user query"
                }
                
            # Ensure intent is one of the valid options
            valid_intents = ["retrieve", "analyze", "summarize", "plan"]
            if intent_data["intent"] not in valid_intents:
                intent_data["intent"] = "retrieve"
                
            return intent_data
            
        except (json.JSONDecodeError, AttributeError):
            # Handle parsing errors by returning a default
            return {
                "intent": "retrieve",
                "target": next(iter(database_summary.keys()), "tasks"),
                "description": "Retrieving information based on user query"
            }
