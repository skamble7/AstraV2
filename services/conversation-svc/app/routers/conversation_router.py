from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import (
    ConversationDocument,
    ConversationCreate,
    ConversationUpdate,
    ConversationAppendRequest,
    ConversationReplace,
    RawMessagesResponse,
    ConversationListResponse,
)
from app.services import ConversationService
from app.services.conversation_service import strip_to_rendered

router = APIRouter(prefix="/conversations", tags=["conversations"])
svc = ConversationService()


@router.post("", response_model=ConversationDocument, status_code=201)
async def create_conversation(payload: ConversationCreate, actor: Optional[str] = None):
    return await svc.create(payload, actor=actor)


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    workspace_id: str = Query(..., description="Filter conversations by workspace ID"),
    user_id: str = Query(..., description="Filter conversations by user ID"),
    limit: int = Query(default=20, ge=1, le=200),
    before: Optional[str] = Query(default=None, description="Cursor for pagination (updated_at ISO timestamp)"),
):
    docs, next_cursor = await svc.list_conversations(workspace_id, user_id, limit=limit, before=before)
    conversations = []
    for doc in docs:
        doc.pop("messages", None)
        doc.pop("reasoning_trace", None)
        conversations.append(ConversationDocument.model_validate(doc))
    return ConversationListResponse(conversations=conversations, next_cursor=next_cursor)


@router.get("/{conversation_id}/messages", response_model=RawMessagesResponse)
async def get_raw_messages(conversation_id: str):
    messages = await svc.get_raw_messages(conversation_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return RawMessagesResponse(conversation_id=conversation_id, messages=messages)


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    conversation = await svc.get(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    raw_messages = [m.model_dump() for m in conversation.messages]
    rendered = strip_to_rendered(raw_messages)
    result = conversation.model_dump(exclude={"messages", "reasoning_trace"})
    result["rendered_messages"] = [r.model_dump() for r in rendered]
    return result


@router.patch("/{conversation_id}", response_model=ConversationDocument)
async def update_conversation(conversation_id: str, body: ConversationUpdate):
    """Rename a conversation."""
    conversation = await svc.update(conversation_id, body)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.patch("/{conversation_id}/messages", response_model=ConversationDocument)
async def append_messages(conversation_id: str, body: ConversationAppendRequest):
    """Append messages to the conversation's history."""
    conversation = await svc.append_messages(conversation_id, body.messages, body.reasoning_trace)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.put("/{conversation_id}/messages", response_model=ConversationDocument)
async def replace_messages(conversation_id: str, body: ConversationReplace):
    """Replace the entire message history for a conversation."""
    conversation = await svc.replace_messages(conversation_id, body.messages)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str, actor: Optional[str] = None):
    doc = await svc.delete(conversation_id, actor=actor)
    if not doc:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"deleted": True}
