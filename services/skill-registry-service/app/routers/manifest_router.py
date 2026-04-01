from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel

from app.models import SkillManifestEntry
from app.services import SkillService

router = APIRouter(prefix="/skills", tags=["manifest"])
svc = SkillService()


class SkillManifest(BaseModel):
    skills: List[SkillManifestEntry]
    generated_at: datetime
    count: int


@router.get("/manifest", response_model=SkillManifest)
async def get_skill_manifest():
    """
    Returns all registered skills as a lightweight manifest (no SKILL.md body).
    Used by the Astra Agent to build its tool registry at startup.
    """
    skills = await svc.get_manifest()
    return SkillManifest(
        skills=skills,
        generated_at=datetime.now(timezone.utc),
        count=len(skills),
    )
