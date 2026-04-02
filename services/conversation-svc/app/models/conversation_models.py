from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field


class AnthropicMessage(BaseModel):
    """
    Anthropic SDK message format — stored as-is.
    Content can be a plain string or a list of content blocks.
    """
    role: Literal["user", "assistant"]
    content: Any  # str | List[ContentBlock]


class ConversationDocument(BaseModel):
    conversation_id: str
    workspace_id: str
    user_id: str
    name: Optional[str] = None
    messages: List[AnthropicMessage] = Field(default_factory=list)
    reasoning_trace: list[dict] = []
    message_count: int = 0
    deleted_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationCreate(BaseModel):
    workspace_id: str
    user_id: str
    conversation_id: Optional[str] = Field(
        default=None,
        description="Caller-supplied conversation ID. Auto-generated (UUID4) if omitted.",
    )
    name: Optional[str] = Field(
        default=None,
        description="Human-readable conversation name.",
    )

    def effective_conversation_id(self) -> str:
        return self.conversation_id or str(uuid.uuid4())


class ConversationUpdate(BaseModel):
    """Rename a conversation."""
    name: str


class ConversationAppend(BaseModel):
    """Append messages to the existing conversation history."""
    messages: List[AnthropicMessage] = Field(
        ..., min_length=1, description="Messages to append to the conversation."
    )


class ConversationReplace(BaseModel):
    """Replace the entire message history for a conversation."""
    messages: List[AnthropicMessage] = Field(
        ..., description="New full message history."
    )


class ConversationAppendRequest(BaseModel):
    messages: list[AnthropicMessage] = Field(
        ..., min_length=1, description="Messages to append to the conversation."
    )
    reasoning_trace: list[dict] = []


class RawMessagesResponse(BaseModel):
    conversation_id: str
    messages: list[dict]


class RenderedMessage(BaseModel):
    role: str
    content: str


class ConversationListResponse(BaseModel):
    conversations: list[ConversationDocument]
    next_cursor: str | None = None
