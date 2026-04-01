from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import SessionDocument, SessionCreate, SessionUpdate, SessionAppend, SessionReplace
from app.services import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])
svc = SessionService()


@router.post("", response_model=SessionDocument, status_code=201)
async def create_session(payload: SessionCreate, actor: Optional[str] = None):
    return await svc.create(payload, actor=actor)


@router.get("", response_model=List[SessionDocument])
async def list_sessions(
    workspace_id: str = Query(..., description="Filter sessions by workspace ID"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    return await svc.list_by_workspace(workspace_id, limit=limit, offset=offset)


@router.get("/{session_id}", response_model=SessionDocument)
async def get_session(session_id: str):
    session = await svc.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}", response_model=SessionDocument)
async def update_session(session_id: str, body: SessionUpdate):
    """Rename a session."""
    session = await svc.update(session_id, body)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.patch("/{session_id}/messages", response_model=SessionDocument)
async def append_messages(session_id: str, body: SessionAppend):
    """Append messages to the session's conversation history."""
    session = await svc.append_messages(session_id, body.messages)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/{session_id}/messages", response_model=SessionDocument)
async def replace_messages(session_id: str, body: SessionReplace):
    """Replace the entire message history for a session."""
    session = await svc.replace_messages(session_id, body.messages)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}")
async def delete_session(session_id: str, actor: Optional[str] = None):
    ok = await svc.delete(session_id, actor=actor)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"deleted": True}
