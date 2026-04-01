from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.models import GlobalSkill, GlobalSkillCreate, GlobalSkillUpdate
from app.services import SkillService

router = APIRouter(prefix="/skill", tags=["skills"])
svc = SkillService()


class NamesRequest(BaseModel):
    names: List[str] = Field(default_factory=list, min_length=1)


@router.post("", response_model=GlobalSkill, status_code=201)
async def create_skill(payload: GlobalSkillCreate, actor: Optional[str] = None):
    return await svc.create(payload, actor=actor)


# IMPORTANT: /search and /by-names must be defined BEFORE /{name}
# to prevent the parametric route from shadowing them.

@router.get("/search", response_model=List[GlobalSkill])
async def search_skills(
    tag: Optional[str] = Query(default=None),
    produces_kind: Optional[str] = Query(default=None),
    mode: Optional[str] = Query(default=None, pattern="^(mcp|llm)$"),
    status: Optional[str] = Query(default=None),
    q: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    items, _ = await svc.search(
        tag=tag,
        produces_kind=produces_kind,
        mode=mode,
        status=status,
        q=q,
        limit=limit,
        offset=offset,
    )
    return items


@router.post("/by-names", response_model=List[GlobalSkill])
async def get_skills_by_names(body: NamesRequest):
    """Batch fetch skills by name. Returns skills in the SAME ORDER as provided. Missing names are skipped."""
    return await svc.get_many(body.names)


@router.get("/{name:path}", response_model=GlobalSkill)
async def get_skill(name: str):
    skill = await svc.get(name)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{name:path}", response_model=GlobalSkill)
async def update_skill(name: str, patch: GlobalSkillUpdate, actor: Optional[str] = None):
    skill = await svc.update(name, patch, actor=actor)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/{name:path}")
async def delete_skill(name: str, actor: Optional[str] = None):
    ok = await svc.delete(name, actor=actor)
    if not ok:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"deleted": True}
