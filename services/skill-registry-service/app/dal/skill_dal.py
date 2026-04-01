from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pymongo import ReturnDocument

from app.db.mongo import get_db
from app.models import GlobalSkill, GlobalSkillCreate, GlobalSkillUpdate, SkillManifestEntry


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _strip_none(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


class SkillDAL:
    """
    CRUD for GlobalSkill.
    Collection: 'skills'
    Primary key: 'name' (sk.<group>.<action>)
    """

    def __init__(self):
        self.col = get_db().skills

    async def create(self, payload: GlobalSkillCreate) -> GlobalSkill:
        doc = GlobalSkill(
            **payload.model_dump(),
            created_at=_utcnow(),
            updated_at=_utcnow(),
        ).model_dump()
        await self.col.insert_one(doc)
        return GlobalSkill.model_validate(doc)

    async def get(self, name: str) -> Optional[GlobalSkill]:
        doc = await self.col.find_one({"name": name})
        return GlobalSkill.model_validate(doc) if doc else None

    async def get_many(self, names: List[str]) -> List[GlobalSkill]:
        """Fetch multiple skills by name in the SAME ORDER as provided (missing names skipped)."""
        if not names:
            return []
        cursor = self.col.find({"name": {"$in": names}})
        docs = [d async for d in cursor]
        by_name: Dict[str, Dict[str, Any]] = {d["name"]: d for d in docs if "name" in d}
        return [GlobalSkill.model_validate(by_name[n]) for n in names if n in by_name]

    async def delete(self, name: str) -> bool:
        res = await self.col.delete_one({"name": name})
        return res.deleted_count == 1

    async def update(self, name: str, patch: GlobalSkillUpdate) -> Optional[GlobalSkill]:
        update_dict = _strip_none(patch.model_dump())
        update_doc = {"$set": {**update_dict, "updated_at": _utcnow()}}
        doc = await self.col.find_one_and_update(
            {"name": name},
            update_doc,
            return_document=ReturnDocument.AFTER,
        )
        return GlobalSkill.model_validate(doc) if doc else None

    async def search(
        self,
        *,
        q: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[GlobalSkill], int]:
        filt: Dict[str, Any] = {}
        if q:
            filt["$or"] = [
                {"name": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
            ]

        total = await self.col.count_documents(filt)
        cursor = (
            self.col.find(filt)
            .sort("name", 1)
            .skip(max(offset, 0))
            .limit(max(min(limit, 200), 1))
        )
        items = [GlobalSkill.model_validate(d) async for d in cursor]
        return items, total

    async def get_manifest(self) -> List[SkillManifestEntry]:
        """Return lightweight manifest entries for all registered skills."""
        cursor = self.col.find({}, {"name": 1, "description": 1, "domain": 1, "is_artifact_skill": 1, "_id": 0}).sort("name", 1)
        return [
            SkillManifestEntry(
                name=d["name"],
                description=d["description"],
                domain=d["domain"],
                is_artifact_skill=d["is_artifact_skill"],
            )
            async for d in cursor
        ]

    async def list_all_names(self) -> List[str]:
        cursor = self.col.find({}, {"name": 1, "_id": 0}).sort("name", 1)
        return [d["name"] async for d in cursor]
