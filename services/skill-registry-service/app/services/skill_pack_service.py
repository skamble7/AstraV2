from __future__ import annotations

from typing import List, Optional, Tuple

from app.dal.skill_pack_dal import SkillPackDAL
from app.events import get_bus
from app.models import SkillPack, SkillPackCreate, SkillPackUpdate


class SkillPackService:
    def __init__(self) -> None:
        self.packs = SkillPackDAL()

    async def create(self, payload: SkillPackCreate, *, actor: Optional[str] = None) -> SkillPack:
        pack = await self.packs.create(payload, created_by=actor)
        try:
            await get_bus().publish(
                service="skill-registry",
                event="pack.created",
                payload={"pack_id": pack.id, "key": pack.key, "version": pack.version, "by": actor},
            )
        except Exception:
            pass
        return pack

    async def get(self, pack_id: str) -> Optional[SkillPack]:
        return await self.packs.get(pack_id)

    async def get_by_key_version(self, key: str, version: str) -> Optional[SkillPack]:
        return await self.packs.get_by_key_version(key, version)

    async def update(self, pack_id: str, patch: SkillPackUpdate, *, actor: Optional[str] = None) -> Optional[SkillPack]:
        pack = await self.packs.update(pack_id, patch, updated_by=actor)
        if pack:
            try:
                await get_bus().publish(
                    service="skill-registry",
                    event="pack.updated",
                    payload={"pack_id": pack.id, "key": pack.key, "version": pack.version, "by": actor},
                )
            except Exception:
                pass
        return pack

    async def delete(self, pack_id: str, *, actor: Optional[str] = None) -> bool:
        ok = await self.packs.delete(pack_id)
        if ok:
            try:
                await get_bus().publish(
                    service="skill-registry",
                    event="pack.deleted",
                    payload={"pack_id": pack_id, "by": actor},
                )
            except Exception:
                pass
        return ok

    async def publish(self, pack_id: str, *, actor: Optional[str] = None) -> Optional[SkillPack]:
        published = await self.packs.publish(pack_id)
        if published:
            try:
                await get_bus().publish(
                    service="skill-registry",
                    event="pack.published",
                    payload={"pack_id": published.id, "key": published.key, "version": published.version, "by": actor},
                )
            except Exception:
                pass
        return published

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
        return await self.packs.search(key=key, version=version, status=status, q=q, limit=limit, offset=offset)

    async def list_versions(self, key: str) -> List[str]:
        return await self.packs.list_versions(key)
