from typing import Dict, Any, List, Optional, Type
from data_layer.mongodb.connection import get_collection, get_async_collection
from data_layer.models.base_model import MongoBaseModel
from data_layer.models.ai_model import AIModel, ModelUsage
from data_layer.models.conversation import Conversation
from data_layer.repos.base_repo import BaseMongoRepository
from data_layer.repos.ai_model_repo import AIModelRepository, ModelUsageRepository
from data_layer.repos.conversation_repo import ConversationRepository
import logging

logger = logging.getLogger(__name__)


class MongoDBClient:
    """MongoDB client for AI services."""

    def __init__(self):
        """Initialize MongoDB client."""
        logger.info("Initializing MongoDB client for AI services")

        # Initialize repositories
        self._ai_model_repo = AIModelRepository()
        self._model_usage_repo = ModelUsageRepository()
        self._conversation_repo = ConversationRepository()

    @property
    def ai_model_repo(self) -> AIModelRepository:
        """Get AI model repository."""
        return self._ai_model_repo

    @property
    def model_usage_repo(self) -> ModelUsageRepository:
        """Get model usage repository."""
        return self._model_usage_repo

    @property
    def conversation_repo(self) -> ConversationRepository:
        """Get conversation repository."""
        return self._conversation_repo

    # Convenience methods for AI models

    def get_model_by_name_version(self, name: str, version: str) -> Optional[AIModel]:
        """Get AI model by name and version."""
        return self.ai_model_repo.find_by_name_version(name, version)

    def get_active_models(self) -> List[AIModel]:
        """Get all active AI models."""
        return self.ai_model_repo.find_active_models()

    # Convenience methods for model usage

    def log_model_usage(
        self,
        model_id: str,
        model_name: str,
        request_type: str,
        tokens_in: int = 0,
        tokens_out: int = 0,
        latency_ms: int = 0,
        success: bool = True,
        error: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Log AI model usage."""
        return self.model_usage_repo.log_usage(
            model_id=model_id,
            model_name=model_name,
            request_type=request_type,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency_ms,
            success=success,
            error=error,
            user_id=user_id,
            session_id=session_id
        )

    # Convenience methods for conversations

    def get_conversation_by_session(self, session_id: str) -> Optional[Conversation]:
        """Get conversation by session ID."""
        return self.conversation_repo.find_by_session(session_id)

    def create_conversation(
        self,
        user_id: str,
        session_id: str,
        title: Optional[str] = None,
        domain: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation."""
        return self.conversation_repo.create_conversation(
            user_id=user_id,
            session_id=session_id,
            title=title,
            domain=domain
        )

    def add_message_to_conversation(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Conversation]:
        """Add a message to a conversation."""
        return self.conversation_repo.add_message_to_conversation(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata=metadata
        )


# Create a singleton instance
_mongo_client: Optional[MongoDBClient] = None


def get_mongo_client() -> MongoDBClient:
    """Get MongoDB client singleton."""
    global _mongo_client

    if _mongo_client is None:
        _mongo_client = MongoDBClient()

    return _mongo_client
