from __future__ import annotations

from typing import List, Optional, Tuple

from app.dal.skill_dal import SkillDAL
from app.events import get_bus
from app.models import GlobalSkill, GlobalSkillCreate, GlobalSkillUpdate


class SkillService:
    def __init__(self) -> None:
        self.dal = SkillDAL()

    async def create(self, payload: GlobalSkillCreate, *, actor: Optional[str] = None) -> GlobalSkill:
        skill = await self.dal.create(payload)
        try:
            await get_bus().publish(
                service="skill-registry",
                event="skill.created",
                payload={"name": skill.name, "produces_kinds": skill.produces_kinds, "by": actor},
            )
        except Exception:
            pass
        return skill

    async def get(self, name: str) -> Optional[GlobalSkill]:
        return await self.dal.get(name)

    async def get_many(self, names: List[str]) -> List[GlobalSkill]:
        return await self.dal.get_many(names)

    async def update(self, name: str, patch: GlobalSkillUpdate, *, actor: Optional[str] = None) -> Optional[GlobalSkill]:
        skill = await self.dal.update(name, patch)
        if skill:
            try:
                await get_bus().publish(
                    service="skill-registry",
                    event="skill.updated",
                    payload={"name": skill.name, "produces_kinds": skill.produces_kinds, "by": actor},
                )
            except Exception:
                pass
        return skill

    async def delete(self, name: str, *, actor: Optional[str] = None) -> bool:
        ok = await self.dal.delete(name)
        if ok:
            try:
                await get_bus().publish(
                    service="skill-registry",
                    event="skill.deleted",
                    payload={"name": name, "by": actor},
                )
            except Exception:
                pass
        return ok

    async def search(
        self,
        *,
        tag: Optional[str] = None,
        produces_kind: Optional[str] = None,
        mode: Optional[str] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Tuple[List[GlobalSkill], int]:
        return await self.dal.search(
            tag=tag,
            produces_kind=produces_kind,
            mode=mode,
            status=status,
            q=q,
            limit=limit,
            offset=offset,
        )

    async def get_published_manifest(self) -> List[GlobalSkill]:
        return await self.dal.get_published_manifest()

    async def list_all_names(self) -> List[str]:
        return await self.dal.list_all_names()
