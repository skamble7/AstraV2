from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Annotated, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from astra_models.capability_models import AuthAlias


# ─────────────────────────────────────────────────────────────
# Retry config
# ─────────────────────────────────────────────────────────────

class RetryConfig(BaseModel):
    max_attempts: int = 3
    backoff_ms: int = 250
    jitter_ms: int = 50


# ─────────────────────────────────────────────────────────────
# Execution — flat structure (ADR-011)
# One tool per skill; base_url at top level (not nested transport)
# ─────────────────────────────────────────────────────────────

class SkillMcpExecution(BaseModel):
    mode: Literal["mcp"]
    transport: Literal["http", "stdio"] = "http"
    base_url: str                                           # ${ENV_VAR} substitution supported
    protocol_path: str = "/mcp"
    health_path: Optional[str] = None
    tool_name: str                                          # single string — NOT an array (ADR-011)
    timeout_sec: int = Field(default=60, ge=1)
    verify_tls: bool = True
    retry: RetryConfig = Field(default_factory=RetryConfig)
    headers: Dict[str, str] = Field(default_factory=dict)
    auth: AuthAlias = Field(default_factory=AuthAlias)


class SkillLlmExecution(BaseModel):
    mode: Literal["llm"]
    llm_config_ref: str


SkillExecution = Annotated[
    Union[SkillMcpExecution, SkillLlmExecution],
    Field(discriminator="mode"),
]


# ─────────────────────────────────────────────────────────────
# Skill Pack — playbook structures
# ─────────────────────────────────────────────────────────────

class SkillPlaybookStep(BaseModel):
    skill_id: str                   # sk.* reference


class SkillPlaybook(BaseModel):
    steps: List[SkillPlaybookStep] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# Skill status
# ─────────────────────────────────────────────────────────────

class SkillStatus(str, Enum):
    draft = "draft"
    published = "published"
    deprecated = "deprecated"


# ─────────────────────────────────────────────────────────────
# Global Skill
# ─────────────────────────────────────────────────────────────

class GlobalSkill(BaseModel):
    name: str = Field(..., description="Stable skill id, e.g. sk.cobol.copybook.parse")
    description: str
    execution: SkillExecution
    produces_kinds: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    status: SkillStatus = SkillStatus.draft
    version: str = "1.0.0"
    parameters_schema: Optional[Dict[str, Any]] = None
    skill_md_body: str = ""             # full SKILL.md markdown body
    references: Dict[str, str] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GlobalSkillCreate(BaseModel):
    name: str
    description: str
    execution: SkillExecution
    produces_kinds: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    status: SkillStatus = SkillStatus.draft
    version: str = "1.0.0"
    parameters_schema: Optional[Dict[str, Any]] = None
    skill_md_body: str = ""
    references: Dict[str, str] = Field(default_factory=dict)


class GlobalSkillUpdate(BaseModel):
    description: Optional[str] = None
    execution: Optional[SkillExecution] = None
    produces_kinds: Optional[List[str]] = None
    depends_on: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    status: Optional[SkillStatus] = None
    version: Optional[str] = None
    parameters_schema: Optional[Dict[str, Any]] = None
    skill_md_body: Optional[str] = None
    references: Optional[Dict[str, str]] = None


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
