from typing import Dict, Any, Optional, List, Union, AsyncGenerator, cast, AsyncIterator
from google import genai
from google.genai import types
from core.config import settings
from utils.logging_utils import get_logger
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
        # Use the Gemini API key from environment variables
        self.api_key = os.environ.get("GEMINI_API_KEY", settings.llm_api_key)
        self.model_name = "gemini-2.5-flash-preview-04-17"

        logger.info(f"Using model: {self.model_name}")

        # Configure the Gemini client
        self.client = genai.Client(api_key=self.api_key)

        # MongoDB client for storing model data
        self.mongo_client = get_mongo_client()

        # Default model ID
        self._current_model_id: Optional[str] = None
        self._model_initialized = False

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
                    provider=ModelProvider.GOOGLE,
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
            # Ensure model is initialized
            await self.ensure_model_initialized()

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

    def _prepare_messages(
        self,
        prompt: str,
        context: Optional[Dict] = None
    ) -> List[types.Content]:
        """Prepare messages for Gemini, including system prompt and history."""
        contents: List[types.Content] = []
        
        # Start with system message if available
        system_prompt = ""
        if context and context.get("system_prompt"):
            system_prompt = context["system_prompt"]
        
        # Process conversation history
        history_text = ""
        if context and context.get("conversation_history"):
            history = context["conversation_history"]
            
            # Convert history to text format
            for msg in history:
                if isinstance(msg, dict):
                    role = msg.get("role", "")
                    content = msg.get("content", "")
                    history_text += f"{role.capitalize()}: {content}\n"
                elif hasattr(msg, "content") and hasattr(msg, "role"):
                    history_text += f"{msg.role.capitalize()}: {msg.content}\n"

        # Combine system prompt, history, and current prompt
        full_prompt = ""
        if system_prompt:
            full_prompt += f"Instructions: {system_prompt}\n\n"
        if history_text:
            full_prompt += f"Previous conversation:\n{history_text}\n"
        full_prompt += f"User: {prompt}\nAssistant: "

        # Create the content object
        contents.append(types.Content(
            role="user",
            parts=[types.Part.from_text(text=full_prompt)]
        ))

        return contents

    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        model_parameters: Optional[Dict] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncIterator[str]]:
        """Generate a response using the LLM."""
        try:
            await self.ensure_model_initialized()
            start_time = time.time()

            # Prepare messages with proper context
            contents = self._prepare_messages(prompt, context)

            # Prepare generation config
            generation_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
                temperature=model_parameters.get("temperature", 0.7) if model_parameters else 0.7,
                candidate_count=1,
                max_output_tokens=model_parameters.get("max_tokens", settings.llm_max_tokens) if model_parameters else settings.llm_max_tokens,
                top_p=model_parameters.get("top_p", 0.95) if model_parameters else 0.95,
            )

            if stream:
                return self._stream_response(contents, generation_config, start_time)

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=contents,
                config=generation_config,
            )

            result = {
                "text": response.text,
                "model": self.model_name,
                "confidence": 0.9
            }

            latency = time.time() - start_time
            await self._update_model_stats(latency, True)
            await self.log_training_data(prompt, result["text"])

            return result

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            if stream:
                async def error_gen():
                    yield f"Error: {str(e)}"
                return error_gen()
            return {"error": str(e), "text": "", "confidence": 0.0}

    async def _stream_response(
        self,
        contents: List[types.Content],
        config: types.GenerateContentConfig,
        start_time: float
    ) -> AsyncIterator[str]:
        """Stream the response from the LLM token by token."""
        success = True
        full_text = ""

        try:
            async def stream_response():
                response = await asyncio.to_thread(
                    self.client.models.generate_content_stream,
                    model=self.model_name,
                    contents=contents,
                    config=config,
                )

                for chunk in response:
                    if chunk.text:
                        yield chunk.text

            generator = stream_response()
            async for token in generator:
                full_text += token
                yield token

            await self.log_training_data(contents[0].parts[0].text, full_text)
            latency = time.time() - start_time
            await self._update_model_stats(latency, success)

        except Exception as e:
            success = False
            logger.error(f"Error in streaming response: {str(e)}")
            yield f"Error: {str(e)}"
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

    async def ensure_model_initialized(self) -> None:
        """Ensure the model ID is initialized before using it."""
        if not self._model_initialized:
            await self._initialize_model_id()
            self._model_initialized = True
