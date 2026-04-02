from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo import ReturnDocument

from app.db.mongo import get_db
from app.models import AnthropicMessage, ConversationDocument, ConversationCreate, ConversationUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ConversationDAL:
    """
    CRUD for ConversationDocument.
    Collection: 'conversations'
    Primary key: conversation_id (string UUID)
    """

    def __init__(self):
        self.col = get_db().conversations

    async def create(self, payload: ConversationCreate) -> ConversationDocument:
        conversation_id = payload.effective_conversation_id()
        now = _utcnow()
        doc: Dict[str, Any] = {
            "conversation_id": conversation_id,
            "workspace_id": payload.workspace_id,
            "user_id": payload.user_id,
            "name": payload.name,
            "messages": [],
            "reasoning_trace": [],
            "message_count": 0,
            "deleted_at": None,
            "created_at": now,
            "updated_at": now,
        }
        await self.col.insert_one(doc)
        return ConversationDocument.model_validate(doc)

    async def update(self, conversation_id: str, patch: ConversationUpdate) -> Optional[ConversationDocument]:
        doc = await self.col.find_one_and_update(
            {"conversation_id": conversation_id},
            {"$set": {"name": patch.name, "updated_at": _utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return ConversationDocument.model_validate(doc) if doc else None

    async def get(self, conversation_id: str) -> Optional[ConversationDocument]:
        doc = await self.col.find_one({"conversation_id": conversation_id})
        return ConversationDocument.model_validate(doc) if doc else None

    async def list_conversations(
        self,
        workspace_id: str,
        user_id: str,
        limit: int = 20,
        before: str | None = None,
    ) -> tuple[list[dict], str | None]:
        query: Dict[str, Any] = {"workspace_id": workspace_id, "user_id": user_id, "deleted_at": None}
        if before:
            query["updated_at"] = {"$lt": datetime.fromisoformat(before)}
        docs = await self.col.find(query).sort("updated_at", -1).limit(limit + 1).to_list(limit + 1)
        next_cursor = docs[limit]["updated_at"].isoformat() if len(docs) > limit else None
        return docs[:limit], next_cursor

    async def append_messages(
        self,
        conversation_id: str,
        messages: list[dict],
        reasoning_trace: list[dict] = [],
    ) -> Optional[ConversationDocument]:
        doc = await self.col.find_one_and_update(
            {"conversation_id": conversation_id},
            {
                "$push": {
                    "messages": {"$each": messages},
                    "reasoning_trace": {"$each": reasoning_trace},
                },
                "$inc": {"message_count": len(messages)},
                "$set": {"updated_at": _utcnow()},
            },
            return_document=ReturnDocument.AFTER,
        )
        return ConversationDocument.model_validate(doc) if doc else None

    async def replace_messages(self, conversation_id: str, messages: List[AnthropicMessage]) -> Optional[ConversationDocument]:
        serialized = [m.model_dump() for m in messages]
        doc = await self.col.find_one_and_update(
            {"conversation_id": conversation_id},
            {"$set": {"messages": serialized, "updated_at": _utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return ConversationDocument.model_validate(doc) if doc else None

    async def delete_conversation(self, conversation_id: str) -> dict | None:
        return await self.col.find_one_and_update(
            {"conversation_id": conversation_id},
            {"$set": {"deleted_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)}},
            return_document=ReturnDocument.AFTER,
        )

    async def get_raw_messages(self, conversation_id: str) -> list[dict] | None:
        doc = await self.col.find_one(
            {"conversation_id": conversation_id, "deleted_at": None}
        )
        if not doc:
            return None
        return doc.get("messages", [])
