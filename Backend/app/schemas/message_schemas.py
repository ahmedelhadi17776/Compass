from pydantic import BaseModel
from typing import Optional, Dict, Any, List, cast
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam, ChatCompletionAssistantMessageParam, ChatCompletionSystemMessageParam


class MessageBase(BaseModel):
    role: str
    content: str

    def to_chat_message(self) -> ChatCompletionMessageParam:
        """Convert to OpenAI chat message format."""
        if self.role == "user":
            return cast(ChatCompletionUserMessageParam, {
                "role": "user",
                "content": self.content
            })
        elif self.role == "assistant":
            return cast(ChatCompletionAssistantMessageParam, {
                "role": "assistant",
                "content": self.content
            })
        else:
            return cast(ChatCompletionSystemMessageParam, {
                "role": "system",
                "content": self.content
            })


class UserMessage(MessageBase):
    role: str = "user"


class AssistantMessage(MessageBase):
    role: str = "assistant"


class SystemMessage(MessageBase):
    role: str = "system"


class ConversationHistory:
    def __init__(self):
        self._messages: List[ChatCompletionMessageParam] = []
        self.max_length = 10

    def add_message(self, message: MessageBase) -> None:
        """Add a message to the conversation history."""
        chat_message = message.to_chat_message()
        self._messages.append(chat_message)
        if len(self._messages) > self.max_length * 2:
            self._messages = self._messages[-self.max_length * 2:]

    def get_messages(self) -> List[ChatCompletionMessageParam]:
        """Get all messages in the conversation."""
        return self._messages.copy()

    def clear(self) -> None:
        """Clear the conversation history."""
        self._messages = []

    def __len__(self) -> int:
        return len(self._messages)
