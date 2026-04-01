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


class SessionDocument(BaseModel):
    session_id: str
    workspace_id: str
    messages: List[AnthropicMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionCreate(BaseModel):
    workspace_id: str
    session_id: Optional[str] = Field(
        default=None,
        description="Caller-supplied session ID. Auto-generated (UUID4) if omitted.",
    )

    def effective_session_id(self) -> str:
        return self.session_id or str(uuid.uuid4())


class SessionAppend(BaseModel):
    """Append messages to the existing session history."""
    messages: List[AnthropicMessage] = Field(
        ..., min_length=1, description="Messages to append to the session."
    )


class SessionReplace(BaseModel):
    """Replace the entire message history for a session."""
    messages: List[AnthropicMessage] = Field(
        ..., description="New full message history."
    )
