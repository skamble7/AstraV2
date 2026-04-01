from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.models import GlobalSkill
from app.services import SkillService

router = APIRouter(prefix="/manifest", tags=["manifest"])
svc = SkillService()


class SkillManifest(BaseModel):
    skills: List[GlobalSkill]
    generated_at: datetime
    count: int


@router.get("/skills", response_model=SkillManifest)
async def get_skill_manifest():
    """
    Returns all published skills as a manifest.
    Used by the Astra Agent to build its tool registry at startup.
    Only skills with status='published' are included.
    """
    skills = await svc.get_published_manifest()
    return SkillManifest(
        skills=skills,
        generated_at=datetime.now(timezone.utc),
        count=len(skills),
    )
