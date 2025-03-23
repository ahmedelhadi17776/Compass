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
        # Check if we have conversation history and determine previous domain
        previous_domain = None
        conversation_history = database_summary.get('conversation_history', [])
        
        # Try to maintain domain context from previous interactions
        if conversation_history and len(conversation_history) >= 2:
            # Look through previous assistant responses for intent/target info
            for i in range(len(conversation_history) - 1, 0, -2):
                if i >= 1 and conversation_history[i].get('role') == 'assistant':
                    content = conversation_history[i].get('content', '')
                    # Check if this is a follow-up question about the same topic
                    if user_input.lower().startswith(('what', 'which', 'who', 'how', 'when', 'where', 'why')) or \
                       any(ref in user_input.lower() for ref in ['it', 'that', 'this', 'these', 'those', 'them', 'they', 'first', 'second', 'third']):
                        logger.info("Detected likely follow-up question - maintaining previous domain context")
                        
                        # Check if we can extract the target domain from database_summary keys
                        for domain_key in database_summary.keys():
                            if domain_key in ['tasks', 'todos']:
                                if domain_key in content.lower() or \
                                   (domain_key == 'tasks' and 'task' in content.lower()) or \
                                   (domain_key == 'todos' and ('todo' in content.lower() or 'to-do' in content.lower())):
                                    previous_domain = domain_key
                                    logger.info(f"Found previous domain context: {previous_domain}")
                                    break
                    break
        
        prompt = f"""
        You are an AI assistant responsible for understanding and acting on user requests.
        Based on the following information, identify the user's intent and target data:

        User Input: "{user_input}"
        Available Domains: {list(database_summary.keys())}

        DOMAIN SELECTION RULES:
        1. For task management: If input contains "todos" or "tasks" or "habits", use respective domain
        2. For general queries (like greetings, recommendations, or questions):
           - Use "default" domain if available
           - Otherwise use the most relevant domain based on context
        3. Look at the context of what they're asking about
        4. Default to "default" domain if unclear or for general conversation
        """
        
        # Add context about previous domain if available
        if previous_domain:
            prompt += f"""
        IMPORTANT CONTEXT: The user's previous messages were about the "{previous_domain}" domain.
        If this message appears to be a follow-up question referring to the same topic, 
        maintain that domain context rather than switching to a general domain.
            """
        
        prompt += f"""
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
            "target": "tasks/todos/habits/default",
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
            
            # If this is a follow-up question and we have a previous domain, consider using it
            if previous_domain and user_input.lower().startswith(('what', 'which', 'who', 'how', 'when', 'where', 'why')) or \
               any(ref in user_input.lower() for ref in ['it', 'that', 'this', 'these', 'those', 'them', 'they', 'first', 'second', 'third']):
                # Only override if the LLM chose the default domain for generic questions
                if intent_data.get("target") == "default" and previous_domain in database_summary.keys():
                    intent_data["target"] = previous_domain
                    logger.info(f"Overriding target to maintain conversation context: {previous_domain}")
            
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
                    # If no match, use previous domain if available
                    previous_domain if previous_domain else (
                        # Otherwise try todos as default if available, else first available domain
                        next((domain for domain in available_domains if domain == "todos"), 
                             available_domains[0] if available_domains else "todos")
                    )
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
