from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────
# Skill Pack — playbook structures (used by SkillPack)
# ─────────────────────────────────────────────────────────────

class SkillPlaybookStep(BaseModel):
    skill_id: str                   # sk.* reference


class SkillPlaybook(BaseModel):
    steps: List[SkillPlaybookStep] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Manifest cache entry
# Returned by GET /skills/manifest — no execution detail, no body
# ─────────────────────────────────────────────────────────────

class SkillManifestEntry(BaseModel):
    name: str
    description: str
    domain: Literal["astra", "general"]
    is_artifact_skill: bool


# ─────────────────────────────────────────────────────────────
# Global Skill — lean MongoDB document
# All execution detail lives inside skill_md_body frontmatter.
# ─────────────────────────────────────────────────────────────

class GlobalSkill(BaseModel):
    name: str = Field(..., description="Stable skill id, e.g. sk.asset.fetch_raina_input")
    description: str
    domain: Literal["astra", "general"] = "astra"
    is_artifact_skill: bool = True
    skill_md_body: str             # complete SKILL.md — frontmatter + Markdown body

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def _validate_frontmatter(v: str) -> str:
    """Shared frontmatter validator — rules 2, 3, 4."""
    # Rule 2: must start with --- and have a closing ---
    if not re.match(r"^---\s*\n", v):
        raise ValueError(
            "skill_md_body must begin with YAML frontmatter delimited by '---'"
        )
    rest = v[4:]
    close = re.search(r"\n---", rest)
    if not close:
        raise ValueError("skill_md_body frontmatter must be closed with '---'")

    fm = rest[: close.start()]

    # Rule 3: execution.tool_name must be a string, not an array
    tn_match = re.search(r"^\s*tool_name\s*:\s*(.+)$", fm, re.MULTILINE)
    if tn_match:
        value = tn_match.group(1).strip()
        if value.startswith("["):
            raise ValueError("execution.tool_name must be a string, not an array")
    # Block-sequence form: tool_name:\n  - item
    if re.search(r"^\s*tool_name\s*:\s*\n\s+-", fm, re.MULTILINE):
        raise ValueError("execution.tool_name must be a string, not an array")

    return v


class GlobalSkillCreate(BaseModel):
    name: str
    description: str
    domain: Literal["astra", "general"] = "astra"
    is_artifact_skill: bool = True
    skill_md_body: str

    @field_validator("name")
    @classmethod
    def name_must_start_with_sk(cls, v: str) -> str:
        # Rule 1
        if not v.startswith("sk."):
            raise ValueError("Skill name must start with 'sk.'")
        return v

    @field_validator("skill_md_body")
    @classmethod
    def body_must_have_valid_frontmatter(cls, v: str) -> str:
        return _validate_frontmatter(v)


class GlobalSkillUpdate(BaseModel):
    # domain and is_artifact_skill are intentionally absent — immutable after creation (Rule 5)
    description: Optional[str] = None
    skill_md_body: Optional[str] = None

    @field_validator("skill_md_body")
    @classmethod
    def body_must_have_valid_frontmatter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return _validate_frontmatter(v)
        return v


# ─────────────────────────────────────────────────────────────
# Skill Pack
# ─────────────────────────────────────────────────────────────

class SkillPackStatus(str, Enum):
    draft = "draft"
    published = "published"
    archived = "archived"


class SkillPack(BaseModel):
    id: str = Field(..., alias="_id")   # key@version composite ID
    key: str
    version: str
    title: str
    description: str
    skill_ids: List[str] = Field(default_factory=list)          # sk.* only
    agent_skill_ids: List[str] = Field(default_factory=list)    # enrichment skills (sk.*)
    pack_input_id: Optional[str] = None
    playbook: SkillPlaybook = Field(default_factory=SkillPlaybook)
    status: SkillPackStatus = SkillPackStatus.draft

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None

    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    model_config = dict(populate_by_name=True)


class SkillPackCreate(BaseModel):
    key: str
    version: str
    title: str
    description: str
    skill_ids: List[str] = Field(default_factory=list)
    agent_skill_ids: List[str] = Field(default_factory=list)
    pack_input_id: Optional[str] = None
    playbook: SkillPlaybook = Field(default_factory=SkillPlaybook)

    @property
    def id(self) -> str:
        return f"{self.key}@{self.version}"


class SkillPackUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    skill_ids: Optional[List[str]] = None
    agent_skill_ids: Optional[List[str]] = None
    pack_input_id: Optional[str] = None
    playbook: Optional[SkillPlaybook] = None
    status: Optional[SkillPackStatus] = None
