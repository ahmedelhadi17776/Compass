from Backend.ai_services.llm.llm_service import LLMService
from typing import Dict, Optional, Any
import json
import logging
import re

logger = logging.getLogger(__name__)

class IntentDetector:
    """
    Dynamically detects user intent from input using LLM reasoning.
    """

    def __init__(self):
        self.llm_service = LLMService()

    def _extract_json_from_markdown(self, text: str) -> str:
        """Extract JSON content from markdown code blocks."""
        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()
        return text.strip()

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
        Available Domains: {list(database_summary.keys())}

        DOMAIN SELECTION RULES:
        1. For task management: If input contains "todos" or "tasks", use respective domain
        2. For general queries (like greetings, recommendations, or questions):
           - Use "default" domain if available
           - Otherwise use the most relevant domain based on context
        3. Look at the context of what they're asking about
        4. Default to "default" domain if unclear or for general conversation

        Classify the intent:
        - retrieve: To fetch specific information or recommendations
        - analyze: To generate insights or analyze patterns
        - summarize: Provide a summary or overview
        - plan: To schedule, organize, or create plans
        
        For general queries or greetings:
        - Use "retrieve" for information requests or recommendations
        - Use "analyze" for analytical questions
        - Use "default" as the target domain
        
        Respond with a JSON object:
        {{
            "intent": "retrieve/analyze/summarize/plan",
            "target": "tasks/todos/default",
            "description": "A short explanation of the user's goal"
        }}
        """

        # Use the LLM to reason about intent
        logger.info(f"Sending prompt to LLM: {prompt}")
        result = await self.llm_service.generate_response(prompt)
        logger.info(f"Raw LLM response: {result}")
        
        try:
            # Extract JSON from markdown if present and parse it
            json_str = self._extract_json_from_markdown(result.get("text", "{}"))
            logger.info(f"Extracted JSON string: {json_str}")
            intent_data = json.loads(json_str)
            logger.info(f"Parsed intent data: {intent_data}")
            
            # Force target to "todos" if the word appears in input
            if "todos" in user_input.lower():
                logger.info("Found 'todos' in input, forcing target to 'todos'")
                intent_data["target"] = "todos"
            elif "tasks" in user_input.lower():
                logger.info("Found 'tasks' in input, forcing target to 'tasks'")
                intent_data["target"] = "tasks"
            elif any(greeting in user_input.lower() for greeting in ["hi", "hello", "hey"]) or \
                 any(general_query in user_input.lower() for general_query in ["recommend", "suggest", "what", "how"]):
                logger.info("Found greeting or general query, using default domain")
                intent_data["target"] = "default"
            
            # Validate the required fields are present
            if not all(k in intent_data for k in ["intent", "target", "description"]):
                logger.warning("Missing required fields in intent data")
                # Try to determine target from user input
                user_input_lower = user_input.lower()
                available_domains = list(database_summary.keys())
                logger.info(f"Available domains: {available_domains}")
                
                # First try to match domain from user input
                target_domain = next(
                    (domain for domain in available_domains if domain in user_input_lower),
                    # If no match, use todos as default if available, else first available domain
                    next((domain for domain in available_domains if domain == "todos"), available_domains[0] if available_domains else "todos")
                )
                logger.info(f"Selected target domain: {target_domain}")
                
                # Set default values if parsing failed
                intent_data = {
                    "intent": "retrieve",  # Default to retrieve as safest option
                    "target": target_domain,
                    "description": "Retrieving information based on user query"
                }
                
            # Ensure intent is one of the valid options
            valid_intents = ["retrieve", "analyze", "summarize", "plan"]
            if intent_data["intent"] not in valid_intents:
                logger.warning(f"Invalid intent {intent_data['intent']}, defaulting to retrieve")
                intent_data["intent"] = "retrieve"
                
            logger.info(f"Final intent data: {intent_data}")
            return intent_data
            
        except (json.JSONDecodeError, AttributeError) as e:
            logger.error(f"Error parsing LLM response: {str(e)}")
            # Handle parsing errors by returning a default
            default_response = {
                "intent": "retrieve",
                "target": next(iter(database_summary.keys()), "tasks"),
                "description": "Retrieving information based on user query"
            }
            logger.info(f"Returning default response: {default_response}")
            return default_response
