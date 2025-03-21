from typing import Dict, Any, Optional, List, Union, AsyncGenerator, cast
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai._streaming import Stream
from Backend.core.config import settings
from Backend.utils.cache_utils import cache_response
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.cache.ai_cache import cache_ai_result
from Backend.data_layer.repositories.ai_model_repository import AIModelRepository
from sqlalchemy.ext.asyncio import AsyncSession
import os
import time

logger = get_logger(__name__)


class LLMService:
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
        self.model_repository = AIModelRepository(
            db_session) if db_session else None

        # Use the GitHub token from environment variables
        github_token = os.environ.get("GITHUB_TOKEN", settings.LLM_API_KEY)

        # Force the correct base URL and model from settings
        self.base_url = "https://models.inference.ai.azure.com"
        self.model_name = "gpt-4o-mini"

        logger.info(f"Initializing LLM service with base URL: {self.base_url}")
        logger.info(f"Using model: {self.model_name}")

        # Configure the OpenAI client with GitHub API settings
        self.client = OpenAI(
            api_key=github_token,
            base_url=self.base_url
        )
        self.model = self.model_name
        self.conversation_history: List[ChatCompletionMessageParam] = []
        self.max_history_length = 10
        self._current_model_id: Optional[int] = None

    async def _get_or_create_model(self) -> Optional[int]:
        """Get or create AI model record in database."""
        if not self.model_repository:
            return None

        try:
            model = await self.model_repository.get_model_by_name_version(
                name=self.model_name,
                version="1.0"
            )

            if not model:
                model = await self.model_repository.create_model({
                    "name": self.model_name,
                    "version": "1.0",
                    "type": "text-generation",
                    "provider": "OpenAI",
                    "model_metadata": {
                        "base_url": self.base_url,
                        "max_history_length": self.max_history_length
                    },
                    "status": "active",
                    "max_tokens": settings.LLM_MAX_TOKENS,
                    "temperature": settings.LLM_TEMPERATURE
                })

            return model.id
        except Exception as e:
            logger.error(f"Error getting/creating AI model: {str(e)}")
            return None

    async def _update_model_stats(self, latency: float, success: bool = True) -> None:
        """Update model usage statistics."""
        if self.model_repository and self._current_model_id:
            try:
                await self.model_repository.update_model_stats(
                    self._current_model_id,
                    latency,
                    success
                )
            except Exception as e:
                logger.error(f"Error updating model stats: {str(e)}")

    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        model_parameters: Optional[Dict] = None,
        stream: bool = True
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        try:
            # Get or create model record
            if not self._current_model_id:
                self._current_model_id = await self._get_or_create_model()

            start_time = time.time()
            success = True

            logger.info(f"Generating response for prompt: {prompt[:50]}...")
            messages = self._prepare_messages(prompt, context)
            params = self._prepare_model_parameters(model_parameters)
            cache_key = f"rag_prompt_result:{hash(prompt)}"
            logger.info(f"Making request to LLM API with stream={stream}")

            if stream:
                async def stream_generator() -> AsyncGenerator[str, None]:
                    try:
                        response: Stream[ChatCompletionChunk] = self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            stream=True,
                            **params
                        )

                        full_text = []
                        async for chunk in response:
                            if chunk.choices and chunk.choices[0].delta.content:
                                content = chunk.choices[0].delta.content
                                full_text.append(content)
                                yield content

                        # Cache the complete response
                        complete_response = {
                            "text": "".join(full_text),
                            "usage": {
                                "prompt_tokens": 0,
                                "completion_tokens": 0,
                                "total_tokens": 0
                            }
                        }
                        await cache_ai_result(cache_key, {prompt: complete_response})
                        await self.log_training_data(prompt, complete_response["text"])

                    except Exception as e:
                        success = False
                        logger.error(f"Error in stream generator: {str(e)}")
                        yield f"Error: {str(e)}"
                    finally:
                        latency = time.time() - start_time
                        await self._update_model_stats(latency, success)

                return stream_generator()

            # Non-streaming response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=False,
                **params
            )

            if isinstance(response, ChatCompletion) and response.choices:
                result = {
                    "text": response.choices[0].message.content,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0
                    }
                }

                await cache_ai_result(cache_key, {prompt: result})
                await self.log_training_data(prompt, result["text"])
                self._update_conversation_history(prompt, result["text"])

                latency = time.time() - start_time
                await self._update_model_stats(latency, True)

                return result

            raise ValueError("Invalid response from LLM service")

        except Exception as e:
            latency = time.time() - start_time
            await self._update_model_stats(latency, False)

            logger.error(f"Error generating response: {str(e)}")
            if stream:
                async def error_generator() -> AsyncGenerator[str, None]:
                    yield f"Error: {str(e)}"
                return error_generator()
            raise

    async def log_training_data(self, prompt: str, response: str):
        with open("training_data.jsonl", "a") as f:
            f.write(f'{{"prompt": "{prompt}", "completion": "{response}"}}\n')

    async def _make_request(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the LLM API."""
        try:
            if endpoint == "model_info":
                return {
                    "model": self.model,
                    "capabilities": {
                        "streaming": True,
                        "function_calling": True,
                        "context_window": settings.LLM_MAX_TOKENS,
                        "temperature_range": [0.0, 2.0]
                    },
                    "configuration": {
                        "temperature": settings.LLM_TEMPERATURE,
                        "max_tokens": settings.LLM_MAX_TOKENS,
                        "top_p": settings.LLM_TOP_P,
                        "min_p": settings.LLM_MIN_P,
                        "top_k": settings.LLM_TOP_K
                    }
                }
            raise ValueError(f"Unknown endpoint: {endpoint}")
        except Exception as e:
            logger.error(f"API request failed: {str(e)}")
            raise

    def _prepare_messages(
        self,
        prompt: str,
        context: Optional[Dict] = None
    ) -> List[ChatCompletionMessageParam]:
        messages: List[ChatCompletionMessageParam] = []

        if context and context.get("system_message"):
            messages.append({
                "role": "system",
                "content": context["system_message"]
            })
        else:
            # Add empty system message as in the GitHub example
            messages.append({
                "role": "system",
                "content": ""
            })

        messages.extend(self.conversation_history[-self.max_history_length:])
        messages.append({"role": "user", "content": prompt})
        return messages

    def _prepare_model_parameters(self, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        # Use the same parameters as in the GitHub API example
        default_params = {
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
            "top_p": settings.LLM_TOP_P,
        }
        if parameters:
            default_params.update(parameters)
        return default_params

    def _update_conversation_history(self, prompt: str, response: str) -> None:
        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append(
            {"role": "assistant", "content": response})

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
        """Close the LLM service."""
        # No active connections to close in OpenAI client
        pass
