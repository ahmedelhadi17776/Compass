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
        self.creation_keywords = {
            'task': ['create task', 'add task', 'new task', 'make task'],
            'todo': ['create todo', 'add todo', 'new todo', 'make todo'],
            'habit': ['create habit', 'add habit', 'new habit', 'make habit']
        }

    def _extract_json_from_markdown(self, text: str) -> str:
        """Extract JSON content from markdown code blocks."""
        # Try to find JSON in code blocks with language specifier
        json_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        # Try alternative format without newlines
        json_match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        # Try to find JSON object directly
        json_match = re.search(r'\{[^\{\}]*"intent"[^\{\}]*\}', text)
        if json_match:
            return json_match.group(0).strip()

        return text.strip()
        
    async def determine_entity_type(self, user_input: str) -> Dict[str, Any]:
        """Determine what type of entity the user wants to create."""
        try:
            # Perform basic keyword matching first for common cases
            user_input_lower = user_input.lower()
            
            # Task keywords
            if any(kw in user_input_lower for kw in ["task", "project", "deadline", "due date", "assign", "quarterly report"]):
                return {
                    "entity_type": "task",
                    "explanation": "Determined as task based on keywords related to projects, deadlines, or formal work items."
                }
            
            # Todo keywords
            if any(kw in user_input_lower for kw in ["todo", "to-do", "to do", "checklist", "shopping list", "remind me to"]):
                return {
                    "entity_type": "todo",
                    "explanation": "Determined as todo based on keywords related to simple checklist items or reminders."
                }
            
            # Habit keywords
            if any(kw in user_input_lower for kw in ["habit", "daily", "routine", "every day", "weekly", "regularly"]):
                return {
                    "entity_type": "habit",
                    "explanation": "Determined as habit based on keywords related to recurring activities or routines."
                }
            
            # Fall back to LLM for more complex cases
            entity_analysis = await self.llm_service.generate_response(
                prompt=f"""Analyze this user input and determine what type of entity they want to create:
User Input: {user_input}

Respond with one of:
- task: For project-related items with deadlines and complex details (examples: reports, assignments, project milestones)
- todo: For simple to-do list items (examples: buy groceries, call mom, send email)
- habit: For recurring daily/weekly activities to build consistency (examples: exercise, meditation, reading)

Please determine the entity type and provide a brief explanation why.""",
                context={
                    "system_message": "You are an entity classification AI. Determine if the user wants to create a task, todo, or habit."
                }
            )
            
            # Parse response
            if isinstance(entity_analysis, dict):
                response_text = entity_analysis.get("text", "")
            else:
                # For streaming response, collect all chunks
                chunks = []
                async for chunk in entity_analysis:
                    chunks.append(chunk)
                response_text = "".join(chunks)
            
            entity_type = "task"  # Default
            
            if "todo" in response_text.lower():
                entity_type = "todo"
            elif "habit" in response_text.lower():
                entity_type = "habit"
            
            return {
                "entity_type": entity_type,
                "explanation": response_text
            }
        except Exception as e:
            logger.error(f"Entity type determination failed: {str(e)}")
            return {"entity_type": "task", "explanation": f"Defaulting to task due to error: {str(e)}"}

    async def detect_intent(self, user_input: str, database_summary: Dict[str, Any]) -> Dict[str, str]:
        """
        Uses the LLM to dynamically identify user intent and relevant entities.

        Args:
            user_input: The user's query string
            database_summary: Context data from various domains

        Returns:
            Dict containing:
                - intent: One of: retrieve, analyze, summarize, plan, create
                - target: The domain target (tasks, todos, etc.)
                - description: Brief explanation of the user's goal
        """
        # Check for creation intent first with direct pattern matching
        user_input_lower = user_input.lower()
        
        # Check for creation intent
        for entity_type, keywords in self.creation_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                logger.info(f"Detected creation intent for {entity_type}")
                return {
                    "intent": "create",
                    "target": entity_type,
                    "description": f"Create a new {entity_type}"
                }
        
        # Check if we have conversation history and determine previous domain
        previous_domain = None
        conversation_history = database_summary.get('conversation_history')

        # Try to maintain domain context from previous interactions
        if conversation_history and hasattr(conversation_history, 'get_messages'):
            messages = conversation_history.get_messages()
            if len(messages) >= 2:
                # Look through previous assistant responses for intent/target info
                for i in range(len(messages) - 1, 0, -2):
                    if i >= 1 and isinstance(messages[i], dict) and messages[i].get('role') == 'assistant':
                        content = messages[i].get('content', '')
                        # Check if this is a follow-up question about the same topic
                        if user_input.lower().startswith(('what', 'which', 'who', 'how', 'when', 'where', 'why')) or \
                           any(ref in user_input.lower() for ref in ['it', 'that', 'this', 'these', 'those', 'them', 'they', 'first', 'second', 'third']):
                            logger.info(
                                "Detected likely follow-up question - maintaining previous domain context")

                            # Check if we can extract the target domain from database_summary keys
                            for domain_key in database_summary.keys():
                                if domain_key in ['tasks', 'todos']:
                                    if domain_key in content.lower() or \
                                       (domain_key == 'tasks' and 'task' in content.lower()) or \
                                       (domain_key == 'todos' and ('todo' in content.lower() or 'to-do' in content.lower())):
                                        previous_domain = domain_key
                                        logger.info(
                                            f"Found previous domain context: {previous_domain}")
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
        - create: To create a new entity (task, todo, habit)

        For general queries or greetings:
        - Use "retrieve" for information requests or recommendations
        - Use "analyze" for analytical questions
        - Use "default" as the target domain

        Respond with a JSON object:
        {{
            "intent": "retrieve/analyze/summarize/plan/create",
            "target": "tasks/todos/habits/default",
            "description": "A short explanation of the user's goal"
        }}
        """

        # Use the LLM to reason about intent
        logger.info(f"Sending prompt to LLM: {prompt}")
        result = await self.llm_service.generate_response(prompt)
        logger.info(f"Raw LLM response: {result}")

        try:
            # Handle both streaming and non-streaming responses
            if isinstance(result, dict):
                json_str = self._extract_json_from_markdown(
                    result.get("text", "{}"))
            else:
                # For streaming response, collect all chunks
                chunks = []
                async for chunk in result:
                    chunks.append(chunk)
                json_str = self._extract_json_from_markdown("".join(chunks))
                
            logger.debug(f"Raw collected response: {json_str}")

            # Ensure we have a valid JSON string, even if empty
            if not json_str or json_str.strip() == "":
                json_str = "{}"

            logger.info(f"Extracted JSON string: {json_str}")
            intent_data = json.loads(json_str)
            logger.info(f"Parsed intent data: {intent_data}")

            # Determine domain from conversation context and user input
            domain_from_input = None
            input_lower = user_input.lower()

            # First check for explicit domain mentions in input
            if "todos" in input_lower:
                domain_from_input = "todos"
                logger.info("Found 'todos' in input")
            elif "tasks" in input_lower:
                domain_from_input = "tasks"
                logger.info("Found 'tasks' in input")
            elif "habits" in input_lower:
                domain_from_input = "habits"
                logger.info("Found 'habits' in input")

            # Enhanced follow-up question detection
            follow_up_indicators = {
                'question_words': ('what', 'which', 'who', 'how', 'when', 'where', 'why'),
                'references': ('it', 'that', 'this', 'these', 'those', 'them', 'they'),
                'ordinals': ('first', 'second', 'third', 'next', 'previous', 'last'),
                'conjunctions': ('and', 'or', 'but', 'also', 'additionally'),
                'continuity': ('more', 'another', 'again', 'else', 'other')
            }

            is_followup = (
                input_lower.startswith(follow_up_indicators['question_words']) or
                any(ref in input_lower.split() for ref in follow_up_indicators['references']) or
                any(ord in input_lower.split() for ord in follow_up_indicators['ordinals']) or
                (len(input_lower.split()) <= 4 and any(conj in input_lower.split() for conj in follow_up_indicators['conjunctions'])) or
                any(cont in input_lower.split()
                    for cont in follow_up_indicators['continuity'])
            )

            # Enhanced domain selection logic
            domain_confidence = {}

            # 1. Explicit domain mention (highest priority)
            if domain_from_input:
                domain_confidence[domain_from_input] = 1.0
                logger.info(
                    f"Explicit domain mention: {domain_from_input} (confidence: 1.0)")

            # 2. Follow-up context
            if is_followup and previous_domain and previous_domain in database_summary.keys():
                confidence = 0.8 if len(input_lower.split()) <= 4 else 0.6
                domain_confidence[previous_domain] = confidence
                logger.info(
                    f"Follow-up context: {previous_domain} (confidence: {confidence})")

            # 3. Domain-specific keywords
            domain_keywords = {
                'tasks': ['task', 'doing', 'work', 'project', 'deadline'],
                'todos': ['todo', 'list', 'item', 'pending', 'incomplete'],
                'habits': ['habit', 'routine', 'daily', 'weekly', 'track'],
                'default': ['recommend', 'suggest', 'general', 'help']
            }

            for domain, keywords in domain_keywords.items():
                if domain in database_summary.keys():
                    matches = sum(
                        keyword in input_lower for keyword in keywords)
                    if matches > 0:
                        confidence = min(0.3 + (matches * 0.15), 0.9)
                        domain_confidence[domain] = max(
                            domain_confidence.get(domain, 0), confidence)
                        logger.info(
                            f"Keyword matches for {domain}: {matches} (confidence: {confidence})")

            # 4. General queries and greetings (lowest priority)
            if any(greeting in input_lower for greeting in ["hi", "hello", "hey"]):
                domain_confidence['default'] = max(
                    domain_confidence.get('default', 0), 0.3)
                logger.info("Greeting detected (confidence: 0.3)")

            # Select domain with highest confidence
            if domain_confidence:
                selected_domain = max(
                    domain_confidence.items(), key=lambda x: x[1])
                intent_data["target"] = selected_domain[0]
                logger.info(
                    f"Selected domain {selected_domain[0]} with confidence {selected_domain[1]}")
            else:
                # Keep LLM's domain choice if no confidence scores
                logger.info(
                    f"Using LLM suggested domain: {intent_data.get('target')}")

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
            valid_intents = ["retrieve", "analyze", "summarize", "plan", "create"]
            if intent_data["intent"] not in valid_intents:
                logger.warning(
                    f"Invalid intent {intent_data['intent']}, defaulting to retrieve")
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
