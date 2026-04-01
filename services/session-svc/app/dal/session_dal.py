from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pymongo import ReturnDocument

from app.db.mongo import get_db
from app.models import AnthropicMessage, SessionDocument, SessionCreate, SessionUpdate


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class SessionDAL:
    """
    CRUD for SessionDocument.
    Collection: 'sessions'
    Primary key: session_id (string UUID)
    """

    def __init__(self):
        self.col = get_db().sessions

    async def create(self, payload: SessionCreate) -> SessionDocument:
        session_id = payload.effective_session_id()
        now = _utcnow()
        doc: Dict[str, Any] = {
            "session_id": session_id,
            "workspace_id": payload.workspace_id,
            "name": payload.name,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        await self.col.insert_one(doc)
        return SessionDocument.model_validate(doc)

    async def update(self, session_id: str, patch: SessionUpdate) -> Optional[SessionDocument]:
        doc = await self.col.find_one_and_update(
            {"session_id": session_id},
            {"$set": {"name": patch.name, "updated_at": _utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return SessionDocument.model_validate(doc) if doc else None

    async def get(self, session_id: str) -> Optional[SessionDocument]:
        doc = await self.col.find_one({"session_id": session_id})
        return SessionDocument.model_validate(doc) if doc else None

    async def list_by_workspace(self, workspace_id: str, limit: int = 50, offset: int = 0) -> List[SessionDocument]:
        cursor = (
            self.col.find({"workspace_id": workspace_id})
            .sort("created_at", -1)
            .skip(max(offset, 0))
            .limit(max(min(limit, 200), 1))
        )
        return [SessionDocument.model_validate(d) async for d in cursor]

    async def append_messages(self, session_id: str, messages: List[AnthropicMessage]) -> Optional[SessionDocument]:
        serialized = [m.model_dump() for m in messages]
        doc = await self.col.find_one_and_update(
            {"session_id": session_id},
            {
                "$push": {"messages": {"$each": serialized}},
                "$set": {"updated_at": _utcnow()},
            },
            return_document=ReturnDocument.AFTER,
        )
        return SessionDocument.model_validate(doc) if doc else None

    async def replace_messages(self, session_id: str, messages: List[AnthropicMessage]) -> Optional[SessionDocument]:
        serialized = [m.model_dump() for m in messages]
        doc = await self.col.find_one_and_update(
            {"session_id": session_id},
            {"$set": {"messages": serialized, "updated_at": _utcnow()}},
            return_document=ReturnDocument.AFTER,
        )
        return SessionDocument.model_validate(doc) if doc else None

    async def delete(self, session_id: str) -> bool:
        res = await self.col.delete_one({"session_id": session_id})
        return res.deleted_count == 1
