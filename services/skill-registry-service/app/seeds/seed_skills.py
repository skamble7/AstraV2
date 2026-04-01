from __future__ import annotations

import logging

from app.models import GlobalSkillCreate
from app.seeds._skill_md import SKILL_MD
from app.services import SkillService

log = logging.getLogger("app.seeds.skills")


async def seed_skills() -> None:
    """
    Seed core skills (diagram skills).
    skill_md_body contains the complete SKILL.md (frontmatter + body).
    """
    log.info("[skills.seeds] Begin")

    svc = SkillService()

    targets = [
        GlobalSkillCreate(
            name="sk.diagram.generate_arch",
            description=(
                "Calls the MCP server to produce a Markdown architecture guidance document grounded on "
                "discovered data-engineering artifacts and RUN INPUTS; emits "
                "cam.governance.data_pipeline_arch_guidance. "
                "Use when a completed data pipeline discovery run is available in the workspace and a "
                "prose-style architecture guidance document is required for stakeholder review."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.diagram.generate_arch"],
        ),
        GlobalSkillCreate(
            name="sk.diagram.mermaid",
            description=(
                "Given an artifact JSON payload and requested diagram views, returns validated Mermaid instructions. "
                "Use as an enrichment skill after any discovery step to attach visual diagrams to artifacts."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.diagram.mermaid"],
        ),
    ]

    created = 0
    for skill in targets:
        try:
            existing = await svc.get(skill.name)
            if existing:
                await svc.delete(skill.name, actor="seed")
                log.info("[skills.seeds] replaced: %s", skill.name)
        except Exception:
            pass
        await svc.create(skill, actor="seed")
        log.info("[skills.seeds] created: %s", skill.name)
        created += 1

    log.info("[skills.seeds] Done (created=%d)", created)
