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

    # skills
    await db.skills.create_index("name", unique=True)
    await db.skills.create_index("tags")
    await db.skills.create_index("produces_kinds")
    await db.skills.create_index("status")
    await db.skills.create_index("execution.mode")
    try:
        await db.skills.create_index([("name", "text"), ("description", "text")])
    except Exception:
        pass

    # skill_packs
    await db.skill_packs.create_index([("key", 1), ("version", 1)], unique=True)
    await db.skill_packs.create_index("status")
    await db.skill_packs.create_index("skill_ids")
    await db.skill_packs.create_index("agent_skill_ids")
    try:
        await db.skill_packs.create_index([("title", "text"), ("description", "text")])
    except Exception:
        pass
