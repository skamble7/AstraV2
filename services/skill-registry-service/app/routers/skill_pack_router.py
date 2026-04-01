from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.models import SkillPack, SkillPackCreate, SkillPackUpdate, SkillPackStatus
from app.services import SkillPackService

logger = logging.getLogger("app.routers.skill_packs")

router = APIRouter(prefix="/skill-pack", tags=["skill-packs"])
svc = SkillPackService()


@router.post("", response_model=SkillPack, status_code=201)
async def create_skill_pack(payload: SkillPackCreate, actor: Optional[str] = None):
    return await svc.create(payload, actor=actor)


@router.get("", response_model=List[SkillPack])
async def list_skill_packs(
    key: Optional[str] = Query(default=None),
    version: Optional[str] = Query(default=None),
    status: Optional[SkillPackStatus] = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    items, _ = await svc.search(
        key=key,
        version=version,
        status=status.value if status else None,
        q=q,
        limit=limit,
        offset=offset,
    )
    return items


# Static routes before parametric to avoid shadowing
@router.get("/{pack_id}/versions", response_model=List[str])
async def list_pack_versions(pack_id: str):
    return await svc.list_versions(pack_id)


@router.get("/{pack_id}", response_model=SkillPack)
async def get_skill_pack(pack_id: str):
    pack = await svc.get(pack_id)
    if not pack:
        raise HTTPException(status_code=404, detail="Skill pack not found")
    return pack


@router.patch("/{pack_id}", response_model=SkillPack)
async def update_skill_pack(pack_id: str, patch: SkillPackUpdate, actor: Optional[str] = None):
    pack = await svc.update(pack_id, patch, actor=actor)
    if not pack:
        raise HTTPException(status_code=404, detail="Skill pack not found")
    return pack


@router.delete("/{pack_id}")
async def delete_skill_pack(pack_id: str, actor: Optional[str] = None):
    ok = await svc.delete(pack_id, actor=actor)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill pack not found")
    return {"deleted": True}


@router.post("/{pack_id}/publish", response_model=SkillPack)
async def publish_skill_pack(pack_id: str, actor: Optional[str] = None):
    pack = await svc.publish(pack_id, actor=actor)
    if not pack:
        raise HTTPException(status_code=404, detail="Skill pack not found or not publishable")
    return pack
