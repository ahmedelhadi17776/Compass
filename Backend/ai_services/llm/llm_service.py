from typing import Dict, Any, Optional, List
from openai import OpenAI
from Backend.core.config import settings
from Backend.utils.cache_utils import cache_response
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction

logger = get_logger(__name__)


class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_API_BASE_URL
        )
        self.model = settings.LLM_MODEL_NAME
        self.conversation_history = []
        self.max_history_length = 10

    @cache_response(ttl=1800)
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        model_parameters: Optional[Dict] = None,
        stream: bool = False
    ) -> Dict:
        try:
            messages = self._prepare_messages(prompt, context)
            params = self._prepare_model_parameters(model_parameters)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=stream,
                **params
            )

            if stream:
                return {"stream": response}

            result = {
                "text": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens
                }
            }

            # Update conversation history
            self._update_conversation_history(prompt, result["text"])
            return result

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    def _prepare_messages(self, prompt: str, context: Optional[Dict] = None) -> List[Dict]:
        messages = []

        # Add system message if context provides it
        if context and context.get("system_message"):
            messages.append(
                {"role": "system", "content": context["system_message"]})

        # Add conversation history
        messages.extend(self.conversation_history[-self.max_history_length:])

        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        return messages

    def _prepare_model_parameters(self, parameters: Optional[Dict] = None) -> Dict:
        default_params = {
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
            "top_p": settings.LLM_TOP_P,
            "min_p": settings.LLM_MIN_P,
            "top_k": settings.LLM_TOP_K
        }
        if parameters:
            default_params.update(parameters)
        return default_params

    def _update_conversation_history(self, prompt: str, response: str) -> None:
        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append(
            {"role": "assistant", "content": response})

        # Trim history if it exceeds max length
        if len(self.conversation_history) > self.max_history_length * 2:
            self.conversation_history = self.conversation_history[-self.max_history_length * 2:]

    async def clear_conversation_history(self) -> None:
        self.conversation_history = []

    async def get_model_info(self) -> Dict:
        """Get model information and configuration."""
        return await self._make_request("model_info")

    async def enhance_task_description(self, task: Dict) -> Dict:
        """Enhance task description using LLM."""
        prompt = f"Enhance this task description:\nTitle: {task.get('title')}\nDescription: {task.get('description')}"
        response = await self.generate_response(prompt)
        return {
            "enhanced_description": response.get("text"),
            "suggestions": response.get("suggestions", []),
            "keywords": response.get("keywords", [])
        }

    async def analyze_workflow(
        self,
        workflow_id: int,
        historical_data: List[Dict]
    ) -> Dict:
        """Analyze workflow efficiency using LLM."""
        prompt = f"Analyze workflow efficiency for workflow {workflow_id} with historical data"
        response = await self.generate_response(
            prompt=prompt,
            context={"historical_data": historical_data}
        )
        return {
            "efficiency_score": float(response.get("efficiency_score", 0.0)),
            "bottlenecks": response.get("bottlenecks", []),
            "recommendations": response.get("recommendations", [])
        }

    async def summarize_meeting(
        self,
        transcript: str,
        participants: List[str],
        duration: int
    ) -> Dict:
        """Generate meeting summary using LLM."""
        prompt = f"Summarize meeting transcript with {len(participants)} participants, duration: {duration} minutes"
        response = await self.generate_response(
            prompt=prompt,
            context={
                "transcript": transcript,
                "participants": participants
            }
        )
        return {
            "summary": response.get("summary"),
            "action_items": response.get("action_items", []),
            "key_points": response.get("key_points", [])
        }

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
