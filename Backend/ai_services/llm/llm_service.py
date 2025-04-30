from typing import Dict, Any, Optional, List, Union, AsyncGenerator, cast, AsyncIterator
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai._streaming import Stream
from Backend.core.config import settings
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.repositories.ai_model_repository import AIModelRepository
from sqlalchemy.ext.asyncio import AsyncSession
import os
import time
import json
import asyncio
import hashlib
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.db_session = db_session
        self.model_repository = AIModelRepository(
            db_session) if db_session else None

        # Use the GitHub token from environment variables
        self.github_token = os.environ.get(
            "GITHUB_TOKEN", settings.LLM_API_KEY)

        # Force the correct base URL and model from settings
        self.base_url = "https://models.inference.ai.azure.com"
        self.model_name = "gpt-4o-mini"

        logger.info(f"Initializing LLM service with base URL: {self.base_url}")
        logger.info(f"Using model: {self.model_name}")

        # Configure the OpenAI client with GitHub API settings
        self.client = OpenAI(
            api_key=self.github_token,
            base_url=self.base_url
        )
        self.model = self.model_name
        self.conversation_history: List[ChatCompletionMessageParam] = []
        self.max_history_length = 10
        self._current_model_id: Optional[int] = None

    def _get_or_create_model(self) -> int:
        """Get or create model ID from database."""
        if not self.model_repository:
            return 1  # Default model ID if no database

        try:
            model = self.model_repository.get_model_by_name_version(
                name=self.model_name,
                version="1.0"
            )

            if not model:
                model = self.model_repository.create_model({
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

            # Safely convert SQLAlchemy Column to int
            model_id = getattr(model, 'id', None)
            return int(str(model_id)) if model_id is not None else 1
        except Exception as e:
            logger.error(f"Error getting/creating AI model: {str(e)}")
            return 1

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
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        """Generate a response using the LLM."""
        try:
            logger.info("Starting LLM response generation")
            start_time = time.time()

            # Prepare messages and parameters
            logger.debug("Preparing messages and parameters")
            messages = self._prepare_messages(prompt, context)
            params = self._prepare_model_parameters(model_parameters)
            logger.debug(f"Using model parameters: {params}")

            if stream:
                logger.info("Using streaming mode for response")
                return self._create_stream_generator(prompt, messages, params, start_time)

            # Make the API request
            logger.debug("Making API request")
            response = await self._make_request(
                "chat/completions",
                messages=messages,
                **params
            )

            # Process the response
            if response and "choices" in response:
                logger.debug("Processing successful response")
                result = {
                    "text": response["choices"][0]["message"]["content"],
                    "model": response.get("model", "unknown"),
                    "usage": response.get("usage", {}),
                }

                # Update stats and log training data
                latency = time.time() - start_time
                logger.info(f"Response generated in {latency:.2f} seconds")
                await self._update_model_stats(latency, True)
                await self.log_training_data(prompt, result["text"])

                return result
            else:
                logger.error("Invalid response format from LLM API")
                return {"error": "Invalid response format", "text": ""}

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            if stream:
                return self._create_error_generator(str(e))
            return {"error": str(e), "text": ""}

    async def _create_stream_generator(
        self,
        prompt: str,
        messages: List[ChatCompletionMessageParam],
        params: Dict[str, Any],
        start_time: float
    ) -> AsyncGenerator[str, None]:
        """Create a streaming response generator."""
        success = True
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                **params
            )

            full_text = []
            async for chunk in self._stream_chunks(response):
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_text.append(content)
                    yield content

            # Cache the complete response
            complete_text = "".join(full_text)
            result = {"text": complete_text}
            await self.log_training_data(prompt, complete_text)

        except Exception as e:
            success = False
            logger.error(f"Error in stream generator: {str(e)}")
            yield f"Error: {str(e)}"
        finally:
            latency = time.time() - start_time
            await self._update_model_stats(latency, success)

    async def _create_error_generator(self, error_message: str) -> AsyncGenerator[str, None]:
        """Create an error response generator."""
        yield f"Error: {error_message}"

    async def _stream_chunks(self, response: Stream[ChatCompletionChunk]) -> AsyncGenerator[ChatCompletionChunk, None]:
        """Convert OpenAI stream to async iterator."""
        for chunk in response:
            yield chunk

    async def log_training_data(self, prompt: str, response: str):
        """Log training data with proper Unicode handling."""
        try:
            with open("training_data.jsonl", "a", encoding="utf-8") as f:
                data = {
                    "prompt": prompt,
                    "completion": response
                }
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to log training data: {str(e)}")
            # Continue execution even if logging fails
            pass

    async def _make_request(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make a request to the LLM API."""
        try:
            logger.debug(f"Making request to endpoint: {endpoint}")
            if endpoint == "chat/completions":
                logger.debug("Processing chat completion request")
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=kwargs.get("messages", []),
                    **{k: v for k, v in kwargs.items() if k != "messages"}
                )
                logger.debug("Chat completion response received")
                return {
                    "choices": [{"message": {"content": choice.message.content}} for choice in response.choices],
                    "model": response.model,
                    "usage": dict(response.usage) if response.usage else {}
                }
            elif endpoint == "model_info":
                logger.debug("Processing model info request")
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
            logger.error(f"API request failed: {str(e)}", exc_info=True)
            raise

    def _prepare_messages(
        self,
        prompt: str,
        context: Optional[Dict] = None
    ) -> List[ChatCompletionMessageParam]:
        logger.debug("Preparing messages for LLM")
        messages: List[ChatCompletionMessageParam] = []

        # Add system message with domain context if available
        if context and context.get("system_message"):
            logger.debug("Adding system message from context")
            system_message = context["system_message"]
            if context.get("domain"):
                system_message = f"Current domain: {context['domain']}\n{system_message}"
            messages.append({
                "role": "system",
                "content": system_message
            })
        else:
            logger.debug("Adding default empty system message")
            messages.append({
                "role": "system",
                "content": ""
            })

        # Get conversation history with domain context
        if context and context.get("conversation_history"):
            logger.debug("Adding conversation history with domain context")
            history = context["conversation_history"]
            if isinstance(history, list):
                # Filter history to maintain domain context
                domain_history = []
                current_domain = context.get("domain")

                for msg in history[-self.max_history_length*2:]:
                    if isinstance(msg, dict):
                        # Keep messages from current domain or domain-independent messages
                        msg_domain = msg.get("metadata", {}).get("domain")
                        if not msg_domain or msg_domain == current_domain:
                            domain_history.append(msg)

                messages.extend(domain_history[-self.max_history_length:])
                logger.debug(
                    f"Added {len(domain_history[-self.max_history_length:])} domain-relevant history messages")

        # Add current prompt with metadata
        logger.debug("Adding current prompt with domain context")
        user_message = {
            "role": "user",
            "content": prompt,
            "metadata": {
                "domain": context.get("domain") if context else None,
                "timestamp": time.time()
            }
        }
        messages.append(user_message)
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
        response = await self.generate_response(
            prompt=f"Enhance this task description:\nTitle: {task.get('title')}\nDescription: {task.get('description')}"
        )
        if isinstance(response, dict):
            return {
                "enhanced_description": response.get("text", ""),
                "suggestions": [],
                "keywords": []
            }
        return {
            "enhanced_description": "",
            "suggestions": [],
            "keywords": []
        }

    async def analyze_workflow(
        self,
        workflow_id: int,
        historical_data: List[Dict]
    ) -> Dict:
        """Analyze workflow efficiency using LLM."""
        response = await self.generate_response(
            prompt=f"Analyze workflow efficiency for workflow {workflow_id} with historical data",
            context={"historical_data": historical_data}
        )
        if isinstance(response, dict):
            return {
                "efficiency_score": 0.0,
                "bottlenecks": [],
                "recommendations": []
            }
        return {
            "efficiency_score": 0.0,
            "bottlenecks": [],
            "recommendations": []
        }

    async def summarize_meeting(
        self,
        transcript: str,
        participants: List[str],
        duration: int
    ) -> Dict:
        """Generate meeting summary using LLM."""
        response = await self.generate_response(
            prompt=f"Summarize meeting transcript with {len(participants)} participants, duration: {duration} minutes",
            context={
                "transcript": transcript,
                "participants": participants
            }
        )
        if isinstance(response, dict):
            return {
                "summary": response.get("text", ""),
                "action_items": [],
                "key_points": []
            }
        return {
            "summary": "",
            "action_items": [],
            "key_points": []
        }

    async def close(self):
        """Close the LLM service."""
        # No active connections to close in OpenAI client
        pass
