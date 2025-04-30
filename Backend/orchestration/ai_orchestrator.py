from typing import Dict, Any, Optional, Union, AsyncGenerator
from Backend.app.schemas.message_schemas import ConversationHistory, UserMessage, AssistantMessage
from Backend.ai_services.llm.llm_service import LLMService
from Backend.orchestration.ai_registry import ai_registry
from Backend.mcp_py.client import MCPClient
from Backend.core.config import settings
import logging
import json
import time

logger = logging.getLogger(__name__)

mcp_client = MCPClient()


class AIOrchestrator:
    def __init__(self):
        self.llm_service = LLMService()
        self.logger = logging.getLogger(__name__)
        self._current_model_id: Optional[int] = None
        self.ai_registry = ai_registry
        self._conversation_histories: Dict[int, ConversationHistory] = {}
        self.max_history_length = 10

    async def process_request(self, user_input: str, user_id: int, domain: Optional[str] = None) -> Dict[str, Any]:
        """Process an AI request with MCP integration."""
        try:
            # Get conversation history first
            history = self._get_conversation_history(user_id)

            # Get user context from MCP
            try:
                user_context = await mcp_client.get_user_context(str(user_id), domain or "default")
            except Exception as e:
                logger.warning(
                    f"Failed to get user context from MCP: {str(e)}")
                user_context = {}

            # Generate response using LLM
            response = await self.llm_service.generate_response(
                prompt=user_input,
                context={
                    "user_id": user_id,
                    "domain": domain,
                    "conversation_history": history.get_messages(),
                    "user_context": user_context
                }
            )

            # Update conversation history
            if isinstance(response, dict):
                self._update_conversation_history(
                    user_id, user_input, response.get("text", ""))
                result = {
                    "response": response.get("text", ""),
                    "intent": "process",
                    "target": domain or "default",
                    "description": "Process user request",
                    "rag_used": False,
                    "cached": False,
                    "confidence": response.get("confidence", 0.0)
                }
            else:
                self._update_conversation_history(
                    user_id, user_input, str(response))
                result = {
                    "response": str(response),
                    "intent": "process",
                    "target": domain or "default",
                    "description": "Process user request",
                    "rag_used": False,
                    "cached": False,
                    "confidence": 0.0
                }

            # Send result to MCP for logging
            try:
                await mcp_client.call_method("ai/log/interaction", {
                    "user_id": str(user_id),
                    "domain": domain,
                    "input": user_input,
                    "output": result["response"],
                    "metadata": {
                        "intent": result["intent"],
                        "confidence": result["confidence"],
                        "rag_used": result["rag_used"]
                    }
                })
            except Exception as e:
                logger.warning(f"Failed to log interaction to MCP: {str(e)}")

            return result

        except Exception as e:
            logger.error(f"Error in process_request: {str(e)}", exc_info=True)
            raise

    def _get_conversation_history(self, user_id: int) -> ConversationHistory:
        """Get or create conversation history for a user."""
        if user_id not in self._conversation_histories:
            self._conversation_histories[user_id] = ConversationHistory()
        return self._conversation_histories[user_id]

    def _update_conversation_history(self, user_id: int, prompt: str, response: str) -> None:
        """Update conversation history with new messages."""
        history = self._get_conversation_history(user_id)
        history.add_message(UserMessage(content=prompt))
        history.add_message(AssistantMessage(content=response))
