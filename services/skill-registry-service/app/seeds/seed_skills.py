from __future__ import annotations

import logging

from app.models import GlobalSkillCreate, SkillMcpExecution, SkillStatus
from app.services import SkillService

log = logging.getLogger("app.seeds.skills")


async def seed_skills() -> None:
    """
    Seed core skills (converted from seed_capabilities.py: diagram skills).
    cap.* → sk.* prefix conversion; transport flattened to base_url.
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
            tags=["data", "diagram", "docs", "guidance", "mcp"],
            produces_kinds=["cam.governance.data_pipeline_arch_guidance"],
            status=SkillStatus.published,
            execution=SkillMcpExecution(
                mode="mcp",
                base_url="http://host.docker.internal:8004",
                timeout_sec=3600,
                verify_tls=False,
                protocol_path="/mcp",
                tool_name="generate_data_pipeline_arch_guidance",
            ),
        ),
        GlobalSkillCreate(
            name="sk.diagram.mermaid",
            description=(
                "Given an artifact JSON payload and requested diagram views, returns validated Mermaid instructions. "
                "Use as an enrichment skill after any discovery step to attach visual diagrams to artifacts."
            ),
            tags=["diagram", "mermaid", "enrichment"],
            produces_kinds=[],
            status=SkillStatus.published,
            execution=SkillMcpExecution(
                mode="mcp",
                base_url="http://host.docker.internal:8001",
                headers={"host": "localhost:8001"},
                timeout_sec=120,
                verify_tls=False,
                protocol_path="/mcp",
                tool_name="diagram.mermaid.generate",
            ),
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
