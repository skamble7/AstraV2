from __future__ import annotations

import logging
import os
from typing import Iterable

from app.models import SkillPackCreate, SkillPlaybook, SkillPlaybookStep
from app.services import SkillPackService

log = logging.getLogger("app.seeds.skill_packs.microservices")


async def _replace_by_id(svc: SkillPackService, pack: SkillPackCreate) -> None:
    """Idempotently replace a skill pack by its id (key@version)."""
    pack_id = f"{pack.key}@{pack.version}"
    try:
        existing = await svc.get(pack_id)
    except Exception:
        existing = None

    if existing:
        try:
            ok = await svc.delete(pack_id, actor="seed")
            if ok:
                log.info("[skill_packs.seeds.microservices] replaced existing: %s", pack_id)
            else:
                log.warning("[skill_packs.seeds.microservices] delete returned falsy for %s; continuing to create", pack_id)
        except Exception as e:
            log.warning("[skill_packs.seeds.microservices] delete failed for %s: %s (continuing)", pack_id, e)

    created = await svc.create(pack, actor="seed")
    log.info("[skill_packs.seeds.microservices] created: %s", created.id)


async def _publish_all(svc: SkillPackService, ids: Iterable[str]) -> None:
    for pack_id in ids:
        try:
            published = await svc.publish(pack_id, actor="seed")
            if published:
                log.info("[skill_packs.seeds.microservices] published: %s", published.id)
        except Exception as e:
            log.warning("[skill_packs.seeds.microservices] publish failed for %s: %s", pack_id, e)


def _steps(*skill_ids: str) -> SkillPlaybook:
    return SkillPlaybook(steps=[SkillPlaybookStep(skill_id=s) for s in skill_ids])


async def seed_microservices_skill_packs() -> None:
    """
    Seeds RAINA Microservices Architecture Discovery skill pack
    (converted from seed_microservices_packs.py).
    cap.* → sk.* prefix; single playbook (primary discovery flow).
    """
    svc = SkillPackService()
    publish_on_seed = os.getenv("SKILL_PACK_SEED_PUBLISH", "1").lower() in ("1", "true", "yes")

    pack_v1_0_0 = SkillPackCreate(
        key="raina-microservices-arch",
        version="v1.0.0",
        title="Microservices Architecture Discovery Pack (v1.0.0)",
        description=(
            "Discovers a target microservices architecture from Raina inputs (AVC/FSS/PSS). "
            "The playbook fetches and validates the input via MCP, decomposes the domain into bounded contexts, "
            "derives candidate microservices, defines service APIs and domain events, assigns data ownership, "
            "maps interactions, selects integration patterns, defines security/observability/deployment topology, "
            "ranks the tech stack, synthesizes the final architecture, and produces a phased migration plan."
        ),
        skill_ids=[
            "sk.asset.fetch_raina_input",
            "sk.domain.discover_ubiquitous_language",
            "sk.domain.discover_bounded_contexts",
            "sk.architecture.discover_microservices",
            "sk.contract.define_service_apis",
            "sk.contract.define_event_catalog",
            "sk.data.define_ownership",
            "sk.architecture.map_service_interactions",
            "sk.architecture.select_integration_patterns",
            "sk.security.define_architecture",
            "sk.observability.define_spec",
            "sk.deployment.define_topology",
            "sk.catalog.rank_tech_stack_microservices",
            "sk.architecture.assemble_microservices",
            "sk.deployment.plan_migration",
            "sk.architecture.generate_guidance",
        ],
        agent_skill_ids=["sk.diagram.mermaid"],
        playbook=_steps(
            "sk.asset.fetch_raina_input",
            "sk.domain.discover_ubiquitous_language",
            "sk.domain.discover_bounded_contexts",
            "sk.architecture.discover_microservices",
            "sk.contract.define_service_apis",
            "sk.contract.define_event_catalog",
            "sk.data.define_ownership",
            "sk.architecture.map_service_interactions",
            "sk.architecture.select_integration_patterns",
            "sk.security.define_architecture",
            "sk.observability.define_spec",
            "sk.deployment.define_topology",
            "sk.catalog.rank_tech_stack_microservices",
            "sk.architecture.assemble_microservices",
            "sk.deployment.plan_migration",
        ),
    )

    await _replace_by_id(svc, pack_v1_0_0)

    if publish_on_seed:
        await _publish_all(svc, ids=("raina-microservices-arch@v1.0.0",))
