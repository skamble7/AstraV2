from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pymongo import ReturnDocument

from app.db.mongo import get_db
from app.models import SkillPack, SkillPackCreate, SkillPackUpdate, SkillPackStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _strip_none(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _pack_id(key: str, version: str) -> str:
    return f"{key}@{version}"


class SkillPackDAL:
    """
    CRUD for SkillPack.
    Collection: 'skill_packs'
    Primary key: _id = key@version
    """

    def __init__(self):
        self.col = get_db().skill_packs

    async def create(self, payload: SkillPackCreate, *, created_by: Optional[str] = None) -> SkillPack:
        _id = _pack_id(payload.key, payload.version)
        now = _utcnow()
        doc: Dict[str, Any] = {
            "_id": _id,
            "key": payload.key,
            "version": payload.version,
            "title": payload.title,
            "description": payload.description,
            "skill_ids": payload.skill_ids or [],
            "agent_skill_ids": payload.agent_skill_ids or [],
            "pack_input_id": payload.pack_input_id,
            "playbook": payload.playbook.model_dump(),
            "status": SkillPackStatus.draft.value,
            "created_at": now,
            "updated_at": now,
            "published_at": None,
            "created_by": created_by,
            "updated_by": created_by,
        }
        await self.col.insert_one(doc)
        return SkillPack.model_validate(doc)

    async def get(self, pack_id: str) -> Optional[SkillPack]:
        doc = await self.col.find_one({"_id": pack_id})
        return SkillPack.model_validate(doc) if doc else None

    async def get_by_key_version(self, key: str, version: str) -> Optional[SkillPack]:
        return await self.get(_pack_id(key, version))

    async def delete(self, pack_id: str) -> bool:
        res = await self.col.delete_one({"_id": pack_id})
        return res.deleted_count == 1

    async def update(self, pack_id: str, patch: SkillPackUpdate, *, updated_by: Optional[str] = None) -> Optional[SkillPack]:
        raw = patch.model_dump()
        update_dict = _strip_none(raw)
        # Serialize nested playbook model if present
        if "playbook" in update_dict and update_dict["playbook"] is not None:
            from app.models import SkillPlaybook
            if isinstance(update_dict["playbook"], SkillPlaybook):
                update_dict["playbook"] = update_dict["playbook"].model_dump()
        if updated_by is not None:
            update_dict["updated_by"] = updated_by
        update_doc = {"$set": {**update_dict, "updated_at": _utcnow()}}
        doc = await self.col.find_one_and_update(
            {"_id": pack_id},
            update_doc,
            return_document=ReturnDocument.AFTER,
        )
        return SkillPack.model_validate(doc) if doc else None

    async def publish(self, pack_id: str) -> Optional[SkillPack]:
        doc = await self.col.find_one({"_id": pack_id})
        if not doc:
            return None

        if doc.get("status") == SkillPackStatus.published.value and doc.get("published_at"):
            return SkillPack.model_validate(doc)

        upd = {
            "$set": {
                "status": SkillPackStatus.published.value,
                "published_at": _utcnow(),
                "updated_at": _utcnow(),
            }
        }
        doc = await self.col.find_one_and_update(
            {"_id": pack_id},
            upd,
            return_document=ReturnDocument.AFTER,
        )
        return SkillPack.model_validate(doc) if doc else None

    async def search(
        self,
        *,
        key: Optional[str] = None,
        version: Optional[str] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[SkillPack], int]:
        filt: Dict[str, Any] = {}
        if key:
            filt["key"] = key
        if version:
            filt["version"] = version
        if status:
            filt["status"] = status
        if q:
            filt["$text"] = {"$search": q}

        total = await self.col.count_documents(filt)
        cursor = (
            self.col.find(filt)
            .sort([("key", 1), ("version", 1)])
            .skip(max(offset, 0))
            .limit(max(min(limit, 200), 1))
        )
        items = [SkillPack.model_validate(d) async for d in cursor]
        return items, total

    async def list_versions(self, key: str) -> List[str]:
        cursor = self.col.find({"key": key}, {"version": 1, "_id": 0}).sort("version", 1)
        return [d["version"] async for d in cursor]
