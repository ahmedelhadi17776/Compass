from typing import Dict, Any, Optional, List, Union, AsyncGenerator, cast, AsyncIterator
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai._streaming import Stream
from core.config import settings
from utils.logging_utils import get_logger
import os
import time
import json
import asyncio
import hashlib
import logging

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
        self._current_model_id: Optional[int] = None

    async def _get_or_create_model(self) -> Optional[int]:
        """Get or create model ID through MCP."""
        try:
            from core.mcp_state import get_mcp_client
            mcp_client = get_mcp_client()
            if not mcp_client:
                logger.error("MCP client not initialized")
                return None

            # Get model info from Go backend through MCP
            model_info = await mcp_client.invoke_tool("ai.model.info", {
                "name": self.model_name,
                "version": "1.0"
            })

            if model_info and "status" in model_info and model_info["status"] == "success":
                content = model_info.get("content", {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except:
                        content = {"model_id": 1}

                return int(content.get("model_id", 1))

            # Create model through MCP if it doesn't exist
            model_info = await mcp_client.invoke_tool("ai.model.create", {
                "name": self.model_name,
                "version": "1.0",
                "type": "text-generation",
                "provider": "OpenAI",
                "status": "active"
            })

            if model_info and "status" in model_info and model_info["status"] == "success":
                content = model_info.get("content", {})
                if isinstance(content, str):
                    try:
                        content = json.loads(content)
                    except:
                        content = {"model_id": 1}

                return int(content.get("model_id", 1))

            return 1  # Default model ID if we can't get it from MCP
        except Exception as e:
            logger.error(f"Error getting/creating model through MCP: {str(e)}")
            return 1  # Default model ID

    async def _update_model_stats(self, latency: float, success: bool = True) -> None:
        """Update model usage statistics through MCP."""
        if self._current_model_id:
            try:
                from core.mcp_state import get_mcp_client
                mcp_client = get_mcp_client()
                if not mcp_client:
                    logger.error("MCP client not initialized")
                    return

                await mcp_client.invoke_tool("ai.model.stats.update", {
                    "model_id": self._current_model_id,
                    "latency": latency,
                    "success": success
                })
            except Exception as e:
                logger.error(
                    f"Error updating model stats through MCP: {str(e)}")

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

        # Process conversation history
        if context and context.get("conversation_history"):
            logger.debug("Adding conversation history")
            history = context["conversation_history"]
            
            # If history is already in the format expected by OpenAI API
            if isinstance(history, list) and all(isinstance(msg, dict) for msg in history):
                for msg in history:
                    if msg.get("role") in ["user", "assistant", "system"]:
                        messages.append(msg)

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
            "response_format": { "type": "text" }  # Ensure text output for tool parsing
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
