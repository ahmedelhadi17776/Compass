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
        return result.get("text")
