from __future__ import annotations

from typing import List, Optional

from app.dal.session_dal import SessionDAL
from app.events import get_bus
from app.models import AnthropicMessage, SessionDocument, SessionCreate, SessionUpdate


class SessionService:
    def __init__(self) -> None:
        self.dal = SessionDAL()

    async def create(self, payload: SessionCreate, *, actor: Optional[str] = None) -> SessionDocument:
        session = await self.dal.create(payload)
        try:
            await get_bus().publish(
                service="session",
                event="created",
                payload={"session_id": session.session_id, "workspace_id": session.workspace_id, "by": actor},
            )
        except Exception:
            pass
        return session

    async def get(self, session_id: str) -> Optional[SessionDocument]:
        return await self.dal.get(session_id)

    async def list_by_workspace(self, workspace_id: str, limit: int = 50, offset: int = 0) -> List[SessionDocument]:
        return await self.dal.list_by_workspace(workspace_id, limit=limit, offset=offset)

    async def update(self, session_id: str, patch: SessionUpdate) -> Optional[SessionDocument]:
        return await self.dal.update(session_id, patch)

    async def append_messages(self, session_id: str, messages: List[AnthropicMessage]) -> Optional[SessionDocument]:
        return await self.dal.append_messages(session_id, messages)

    async def replace_messages(self, session_id: str, messages: List[AnthropicMessage]) -> Optional[SessionDocument]:
        return await self.dal.replace_messages(session_id, messages)

    async def delete(self, session_id: str, *, actor: Optional[str] = None) -> bool:
        ok = await self.dal.delete(session_id)
        if ok:
            try:
                await get_bus().publish(
                    service="session",
                    event="deleted",
                    payload={"session_id": session_id, "by": actor},
                )
            except Exception:
                pass
        return ok
