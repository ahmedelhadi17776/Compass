from typing import Dict, Any, Optional, List, Union, AsyncGenerator
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai._streaming import Stream
from Backend.core.config import settings
from Backend.utils.cache_utils import cache_response
from Backend.utils.logging_utils import get_logger
from Backend.data_layer.cache.ai_cache import cache_ai_result

import os

logger = get_logger(__name__)


class LLMService:
    def __init__(self):
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

    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict] = None,
        model_parameters: Optional[Dict] = None,
        stream: bool = False
    ) -> Union[Dict[str, Any], AsyncGenerator[str, None]]:
        try:
            logger.info(f"Generating response for prompt: {prompt[:50]}...")
            messages = self._prepare_messages(prompt, context)
            params = self._prepare_model_parameters(model_parameters)
            cache_key = f"rag_prompt_result:{hash(prompt)}"
            logger.info(f"Making request to LLM API with stream={stream}")
            
            if stream:
                # Create a custom async generator for streaming
                async def stream_generator():
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
                            messages=messages,
                            stream=True,
                            **params
                        )
                        
                        for chunk in response:
                            if chunk.choices and chunk.choices[0].delta.content:
                                yield chunk.choices[0].delta.content
                        
                        result = {
                                "text": response.choices[0].message.content,
                                "usage": {
                                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                                    "total_tokens": response.usage.total_tokens if response.usage else 0
                                }
                            }
                        await cache_ai_result(cache_key, {prompt : result})

                        await self.log_training_data(prompt, result)

                    except Exception as e:
                        logger.error(f"Error in stream generator: {str(e)}")
                        yield f"Error: {str(e)}"
                
                # Return the generator function directly, not calling it
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
                
                await cache_ai_result(cache_key, {prompt : result})
                await self.log_training_data(prompt, result)

                self._update_conversation_history(prompt, result["text"])
                return result

            raise ValueError("Invalid response from LLM service")

        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            if stream:
                # If streaming, return an error generator
                async def error_generator():
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
