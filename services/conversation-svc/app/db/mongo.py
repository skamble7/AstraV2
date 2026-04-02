from __future__ import annotations

from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config import settings

_client: Optional[AsyncIOMotorClient] = None


def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(settings.mongo_uri)
    return _client


def get_db() -> AsyncIOMotorDatabase:
    return get_client()[settings.mongo_db]


async def init_indexes() -> None:
    db = get_db()
    await db.conversations.create_index("conversation_id", unique=True)
    await db.conversations.create_index("workspace_id")
    await db.conversations.create_index("created_at")
    await db.conversations.create_index(
        [("workspace_id", 1), ("user_id", 1), ("updated_at", -1)]
    )
    await db.conversations.create_index("deleted_at", sparse=True)
