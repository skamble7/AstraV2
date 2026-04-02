from __future__ import annotations

from typing import List, Optional

from app.dal.conversation_dal import ConversationDAL
from app.events import get_bus
from app.models import AnthropicMessage, ConversationDocument, ConversationCreate, ConversationUpdate, RenderedMessage


class ConversationService:
    def __init__(self) -> None:
        self.dal = ConversationDAL()

    async def create(self, payload: ConversationCreate, *, actor: Optional[str] = None) -> ConversationDocument:
        conversation = await self.dal.create(payload)
        try:
            await get_bus().publish(
                service="conversation",
                event="created",
                payload={"conversation_id": conversation.conversation_id, "workspace_id": conversation.workspace_id, "by": actor},
            )
        except Exception:
            pass
        return conversation

    async def get(self, conversation_id: str) -> Optional[ConversationDocument]:
        return await self.dal.get(conversation_id)

    async def list_conversations(
        self,
        workspace_id: str,
        user_id: str,
        limit: int = 20,
        before: str | None = None,
    ) -> tuple[list[dict], str | None]:
        return await self.dal.list_conversations(workspace_id, user_id, limit=limit, before=before)

    async def update(self, conversation_id: str, patch: ConversationUpdate) -> Optional[ConversationDocument]:
        return await self.dal.update(conversation_id, patch)

    async def append_messages(
        self,
        conversation_id: str,
        messages: list[AnthropicMessage],
        reasoning_trace: list[dict] = [],
    ) -> Optional[ConversationDocument]:
        serialized = [m.model_dump() for m in messages]
        return await self.dal.append_messages(conversation_id, serialized, reasoning_trace)

    async def replace_messages(self, conversation_id: str, messages: List[AnthropicMessage]) -> Optional[ConversationDocument]:
        return await self.dal.replace_messages(conversation_id, messages)

    async def delete(self, conversation_id: str, *, actor: Optional[str] = None) -> Optional[dict]:
        doc = await self.dal.delete_conversation(conversation_id)
        if doc:
            try:
                await get_bus().publish(
                    service="conversation",
                    event="deleted",
                    payload={"conversation_id": conversation_id, "by": actor},
                )
            except Exception:
                pass
        return doc

    async def get_raw_messages(self, conversation_id: str) -> list[dict] | None:
        return await self.dal.get_raw_messages(conversation_id)


def strip_to_rendered(messages: list[dict]) -> list[RenderedMessage]:
    rendered = []
    for msg in messages:
        role = msg.get("role")
        if role == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(
                    block.get("text", "")
                    for block in content
                    if block.get("type") == "text"
                )
            rendered.append(RenderedMessage(role="user", content=str(content)))
        elif role == "assistant":
            content = msg.get("content", [])
            if isinstance(content, list):
                text = " ".join(
                    block.get("text", "")
                    for block in content
                    if block.get("type") == "text"
                )
            else:
                text = str(content)
            rendered.append(RenderedMessage(role="assistant", content=text))
        # tool_result dropped entirely
    return rendered
