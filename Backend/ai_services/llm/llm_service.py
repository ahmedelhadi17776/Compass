from typing import Dict, Any, Optional, List, Union, AsyncGenerator, cast, AsyncIterator
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai._streaming import Stream
from core.config import settings
from utils.logging_utils import get_logger
from core.mcp_state import get_mcp_client
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain.schema import format_document
from ai_services.base.mongo_client import get_mongo_client
import os
import time
import json
import asyncio
import hashlib
import logging
from data_layer.models.ai_model import ModelType, ModelProvider

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        # Use the GitHub token from environment variables
        self.github_token = os.environ.get(
            "GITHUB_TOKEN", settings.llm_api_key)

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

        # MongoDB client for storing model data
        self.mongo_client = get_mongo_client()

        # Default model ID
        self._current_model_id: Optional[str] = None

        # Initialize model ID asynchronously in the background
        asyncio.create_task(self._initialize_model_id())

    async def _initialize_model_id(self) -> None:
        """Initialize the model ID by getting or creating the model in MongoDB."""
        try:
            # Check if model exists in MongoDB
            existing_model = self.mongo_client.get_model_by_name_version(
                name=self.model_name,
                version="1.0"
            )

            if existing_model:
                self._current_model_id = existing_model.id
                logger.info(
                    f"Found existing model in MongoDB with ID: {self._current_model_id}")
            else:
                # Create model in MongoDB
                model = self.mongo_client.ai_model_repo.create_model(
                    name=self.model_name,
                    version="1.0",
                    provider=ModelProvider.OPENAI,
                    type=ModelType.TEXT_GENERATION,
                    status="active",
                    capabilities={
                        "streaming": True,
                        "function_calling": True
                    }
                )
                self._current_model_id = model.id
                logger.info(
                    f"Created new model in MongoDB with ID: {self._current_model_id}")

        except Exception as e:
            logger.error(f"Failed to initialize model ID in MongoDB: {str(e)}")
            # Create a fallback ID (will be used until proper initialization)
            self._current_model_id = "temp_" + str(hash(self.model_name))[:8]
            logger.info(f"Using fallback model ID: {self._current_model_id}")

    async def _update_model_stats(self, latency: float, success: bool = True) -> None:
        """Update model usage statistics in MongoDB."""
        try:
            # Store usage data in MongoDB
            model_id = self._current_model_id or "unknown"
            self.mongo_client.log_model_usage(
                model_id=model_id,
                model_name=self.model_name,
                request_type="text_generation",
                tokens_in=0,  # We could calculate this from input length
                tokens_out=0,  # We could calculate this from output length
                latency_ms=int(latency * 1000),
                success=success,
                error=None if success else "API error"
            )
            logger.info(
                f"Logged model usage in MongoDB for model {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to log model usage in MongoDB: {str(e)}")

    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        model_parameters: Optional[Dict] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
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
                return self._stream_response(prompt, messages, params, start_time)

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
                    "confidence": 0.9
                }

                # Update stats and log training data
                latency = time.time() - start_time
                logger.info(f"Response generated in {latency:.2f} seconds")
                await self._update_model_stats(latency, True)
                await self.log_training_data(prompt, result["text"])

                return result
            else:
                logger.error("Invalid response format from LLM API")
                return {"error": "Invalid response format", "text": "", "confidence": 0.0}

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            if stream:
                async def error_gen():
                    yield f"Error: {str(e)}"
                return error_gen()
            return {"error": str(e), "text": "", "confidence": 0.0}

    async def _stream_response(
        self,
        prompt: str,
        messages: List[ChatCompletionMessageParam],
        params: Dict[str, Any],
        start_time: float
    ) -> AsyncIterator[str]:
        """Stream the response from the LLM token by token."""
        logger.info("Starting streaming response")
        success = True
        full_text = ""

        try:
            # Create a wrapper function to convert sync to async
            async def stream_openai_response():
                # Set streaming parameter
                stream_params = {**params, "stream": True}

                try:
                    response = await asyncio.to_thread(
                        self.client.chat.completions.create,
                        model=self.model,
                        messages=messages,
                        stream=True,
                        **{k: v for k, v in params.items() if k != "stream"}
                    )

                    logger.info("Stream created, yielding tokens")

                    # Process each chunk in the stream
                    for chunk in response:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            yield content
                            # Small delay to avoid overwhelming the client
                            await asyncio.sleep(0.01)

                except Exception as e:
                    logger.error(f"Error in OpenAI stream: {str(e)}")
                    yield f"Error: {str(e)}"

            # Create and return the async generator
            generator = stream_openai_response()

            # Collect the full response for training data
            async for token in generator:
                full_text += token
                yield token

            # Log the complete response for training data
            await self.log_training_data(prompt, full_text)

            # Update model stats
            latency = time.time() - start_time
            await self._update_model_stats(latency, success)

        except Exception as e:
            success = False
            logger.error(f"Error in streaming response: {str(e)}")
            yield f"Error: {str(e)}"

            # Update model stats with failure
            latency = time.time() - start_time
            await self._update_model_stats(latency, success)

    async def _create_error_generator(self, error_message: str) -> AsyncIterator[str]:
        """Create an error response generator."""
        yield f"Error: {error_message}"

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
            logger.info(f"[LLM] Making request to endpoint: {endpoint}")
            if endpoint == "chat/completions":
                logger.info("[LLM] Processing chat completion request")

                # Log important parameters
                if "messages" in kwargs:
                    messages = kwargs.get("messages", [])
                    msg_count = len(messages)

                    # Find system message if it exists
                    system_msg = None
                    for msg in messages:
                        if msg.get("role") == "system":
                            system_msg = msg
                            break

                    # Build preview safely with explicit checks
                    if system_msg and isinstance(system_msg.get("content"), str):
                        content = system_msg.get("content")
                        if len(content) > 100:
                            system_preview = content[:100] + "..."
                        else:
                            system_preview = content

                        if len(system_preview) > 50:
                            preview_to_log = system_preview[:50] + "..."
                        else:
                            preview_to_log = system_preview
                    else:
                        preview_to_log = "No system message"

                    logger.info(
                        f"[LLM] Request contains {msg_count} messages (system message: {preview_to_log})")

                # Log other parameters
                params_to_log = {k: v for k,
                                 v in kwargs.items() if k != "messages"}
                logger.info(f"[LLM] Using parameters: {params_to_log}")

                # Record start time
                start_time = time.time()
                logger.info(
                    f"[LLM] Sending request to {self.base_url} for model {self.model}")

                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model,
                    messages=kwargs.get("messages", []),
                    **{k: v for k, v in kwargs.items() if k != "messages"}
                )

                # Calculate duration
                duration = time.time() - start_time
                logger.info(
                    f"[LLM] ✅ Response received in {duration:.3f} seconds")

                # Log token usage
                if response.usage:
                    logger.info(
                        f"[LLM] Token usage: {response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion = {response.usage.total_tokens} total")

                # Log response preview
                content = response.choices[0].message.content if response.choices else "No content"
                if content:
                    content_preview = content[:100] + \
                        "..." if len(content) > 100 else content
                else:
                    content_preview = "No content"
                logger.info(f"[LLM] Response content: {content_preview}")

                return {
                    "choices": [{"message": {"content": choice.message.content}} for choice in response.choices],
                    "model": response.model,
                    "usage": dict(response.usage) if response.usage else {}
                }
            elif endpoint == "model_info":
                logger.info("[LLM] Processing model info request")

                # Get model info from MongoDB instead of MCP
                model_info = {
                    "model": self.model,
                    "capabilities": {
                        "streaming": True,
                        "function_calling": True,
                        "context_window": settings.llm_max_tokens,
                        "temperature_range": [0.0, 2.0]
                    },
                    "configuration": {
                        "temperature": settings.llm_temperature,
                        "max_tokens": settings.llm_max_tokens,
                        "top_p": settings.llm_top_p,
                        "min_p": settings.llm_min_p,
                        "top_k": settings.llm_top_k
                    }
                }

                # Try to add MongoDB model info if available
                try:
                    if self._current_model_id:
                        model = self.mongo_client.ai_model_repo.find_by_id(
                            self._current_model_id)
                        if model:
                            model_info["id"] = model.id
                            model_info["version"] = model.version
                            model_info["provider"] = model.provider.value
                            model_info["capabilities"].update(
                                model.capabilities)
                except Exception as e:
                    logger.error(
                        f"Error retrieving model info from MongoDB: {str(e)}")

                return model_info
            raise ValueError(f"Unknown endpoint: {endpoint}")
        except Exception as e:
            logger.error(
                f"[LLM] ❌ API request failed: {str(e)}", exc_info=True)
            raise

    def _prepare_messages(
        self,
        prompt: str,
        context: Optional[Dict] = None
    ) -> List[ChatCompletionMessageParam]:
        logger.debug("Preparing messages for LLM")
        messages: List[ChatCompletionMessageParam] = []

        # Add system message with tool context if available
        if context and context.get("system_prompt"):
            logger.debug("Adding system message with tool context")
            messages.append({
                "role": "system",
                "content": context["system_prompt"]
            })
        else:
            logger.debug("Adding default system message")
            messages.append({
                "role": "system",
                "content": "You are a helpful AI assistant."
            })

        # Process conversation history from LangChain memory
        if context and context.get("conversation_history"):
            logger.debug("Adding conversation history")
            history = context["conversation_history"]

            # If history is already in the format expected by OpenAI API
            if isinstance(history, list) and all(isinstance(msg, dict) for msg in history):
                for msg in history:
                    if msg.get("role") in ["user", "assistant", "system"]:
                        messages.append(msg)
            # If history is in LangChain Message format
            elif isinstance(history, list) and hasattr(history[0], "content") and hasattr(history[0], "role"):
                for msg in history:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

        # Add current prompt
        logger.debug("Adding current prompt")
        messages.append({
            "role": "user",
            "content": prompt
        })
        return messages

    def _prepare_model_parameters(self, parameters: Optional[Dict] = None) -> Dict[str, Any]:
        # Default parameters optimized for tool calling
        default_params = {
            "temperature": 0.7,  # Balanced between creativity and precision
            "max_tokens": settings.llm_max_tokens,
            "top_p": 0.95,  # High value for more focused responses
            "presence_penalty": 0.0,  # No penalty for repeated tokens
            "frequency_penalty": 0.0,  # No penalty for frequent tokens
            # Ensure text output for tool parsing
            "response_format": {"type": "text"}
        }
        if parameters:
            default_params.update(parameters)
        return default_params

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
