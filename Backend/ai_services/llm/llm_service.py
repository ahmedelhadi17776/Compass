from typing import Dict, Any, Optional
import aiohttp
from Backend.core.config import settings
from Backend.utils.cache_utils import cache_response
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.database.models.ai_interactions import AIAgentInteraction

logger = get_logger(__name__)

from typing import Dict, Optional
from Backend.ai_services.base.ai_service_base import AIServiceBase
from Backend.utils.cache_utils import cache_response
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.cache.ai_cache import cache_ai_result, get_cached_ai_result

logger = get_logger(__name__)

class LLMService(AIServiceBase):
    def __init__(self):
        super().__init__("llm")
        self.model_version = "1.0.0"
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
        """Generate LLM response with streaming support."""
        try:
            response = await self._make_request(
                "generate",
                data={
                    "prompt": prompt,
                    "context": context or {},
                    "parameters": self._prepare_model_parameters(model_parameters),
                    "stream": stream,
                    "conversation_history": self.conversation_history[-self.max_history_length:]
                }
            )
            
            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": prompt
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response.get("text", "")
            })
            
            return response
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            raise

    def _prepare_model_parameters(self, parameters: Optional[Dict] = None) -> Dict:
        """Prepare and validate model parameters."""
        default_params = {
            "temperature": 0.7,
            "max_tokens": 1000,
            "top_p": 0.9,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
        if parameters:
            default_params.update(parameters)
        return default_params

    async def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
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