from typing import Dict, List, Any, Optional, Tuple, cast
import logging
import uuid
from datetime import datetime
from langchain.memory import ChatMessageHistory
from langchain.schema import BaseChatMessageHistory, AIMessage, HumanMessage, SystemMessage, BaseMessage
from ai_services.base.mongo_client import get_mongo_client
from data_layer.models.conversation import Conversation

logger = logging.getLogger(__name__)


class MongoDBChatMessageHistory(BaseChatMessageHistory):
    """MongoDB-backed chat message history implementation for LangChain."""

    def __init__(
        self,
        user_id: str,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        domain: Optional[str] = None
    ):
        """Initialize MongoDB chat message history."""
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.conversation_id = conversation_id
        self.domain = domain
        self.mongo_client = get_mongo_client()
        self.messages: List[BaseMessage] = []

        # Initialize conversation if not yet loaded
        self._init_conversation()

        # Load initial messages
        self._load_messages()

    def _init_conversation(self) -> None:
        """Initialize or retrieve the conversation."""
        if self.conversation_id:
            # Try to load existing conversation
            conversation = self.mongo_client.conversation_repo.find_by_id(
                self.conversation_id)
            if not conversation:
                # Conversation not found, create new one
                logger.warning(
                    f"Conversation ID {self.conversation_id} not found, creating new conversation")
                self._create_new_conversation()
        else:
            # Try to find conversation by session ID
            conversation = self.mongo_client.get_conversation_by_session(
                self.session_id)
            if not conversation:
                # Conversation not found, create new one
                self._create_new_conversation()
            else:
                # Found existing conversation
                self.conversation_id = conversation.id

    def _create_new_conversation(self) -> None:
        """Create a new conversation in MongoDB."""
        conversation = self.mongo_client.create_conversation(
            user_id=self.user_id,
            session_id=self.session_id,
            domain=self.domain
        )
        self.conversation_id = conversation.id
        logger.info(f"Created new conversation with ID {self.conversation_id}")

    def _message_to_dict(self, message: BaseMessage) -> Dict[str, Any]:
        """Convert LangChain message to MongoDB dictionary."""
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, SystemMessage):
            role = "system"
        else:
            role = "unknown"

        return {
            "role": role,
            "content": message.content,
            "timestamp": datetime.utcnow(),
            "metadata": getattr(message, "additional_kwargs", {})
        }

    def _dict_to_message(self, message_dict: Dict[str, Any]) -> BaseMessage:
        """Convert MongoDB dictionary to LangChain message."""
        role = message_dict.get("role", "")
        content = message_dict.get("content", "")
        metadata = message_dict.get("metadata", {})

        if role == "user":
            return HumanMessage(content=content, additional_kwargs=metadata)
        elif role == "assistant":
            return AIMessage(content=content, additional_kwargs=metadata)
        elif role == "system":
            return SystemMessage(content=content, additional_kwargs=metadata)
        else:
            # Default to human message if unknown
            return HumanMessage(content=content, additional_kwargs=metadata)

    def _load_messages(self) -> None:
        """Load messages from MongoDB into the messages attribute."""
        if not self.conversation_id:
            self.messages = []
            return

        conversation = self.mongo_client.conversation_repo.find_by_id(
            self.conversation_id)
        if not conversation:
            logger.warning(
                f"Conversation ID {self.conversation_id} not found when retrieving messages")
            self.messages = []
            return

        self.messages = [self._dict_to_message(
            msg) for msg in conversation.messages]

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the conversation."""
        if not self.conversation_id:
            self._init_conversation()

        if not self.conversation_id:
            logger.error("Failed to initialize conversation ID")
            return

        message_dict = self._message_to_dict(message)
        updated = self.mongo_client.add_message_to_conversation(
            conversation_id=self.conversation_id,
            role=message_dict["role"],
            content=message_dict["content"],
            metadata=message_dict["metadata"]
        )

        if not updated:
            logger.error(
                f"Failed to add message to conversation {self.conversation_id}")
        else:
            # Update the local messages list
            self.messages.append(message)

    def clear(self) -> None:
        """Clear all messages from the conversation."""
        if not self.conversation_id:
            return

        conversation = self.mongo_client.conversation_repo.find_by_id(
            self.conversation_id)
        if not conversation:
            logger.warning(
                f"Conversation ID {self.conversation_id} not found when clearing messages")
            return

        # Update the conversation with empty messages list
        self.mongo_client.conversation_repo.update(
            self.conversation_id,
            {"messages": []}
        )

        # Also clear the local messages
        self.messages = []

        logger.info(
            f"Cleared all messages from conversation {self.conversation_id}")


def get_mongodb_memory(
    user_id: str,
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    domain: Optional[str] = None
) -> BaseChatMessageHistory:
    """Get MongoDB-backed chat message history for LangChain memory."""
    return MongoDBChatMessageHistory(
        user_id=user_id,
        session_id=session_id,
        conversation_id=conversation_id,
        domain=domain
    )
