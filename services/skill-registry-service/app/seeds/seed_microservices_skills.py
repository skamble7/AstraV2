from __future__ import annotations

import logging

from app.models import GlobalSkillCreate
from app.seeds._skill_md import SKILL_MD
from app.services import SkillService

log = logging.getLogger("app.seeds.microservices_skills")


async def seed_microservices_skills() -> None:
    """
    Seeds microservices-architecture discovery skills.
    skill_md_body contains the complete SKILL.md (frontmatter + body).
    Note: sk.asset.fetch_raina_input and sk.observability.define_spec are seeded elsewhere.
    """
    log.info("[skills.seeds.microservices] Begin")

    svc = SkillService()

    targets: list[GlobalSkillCreate] = [
        # ---- Domain decomposition ----
        GlobalSkillCreate(
            name="sk.domain.discover_ubiquitous_language",
            description=(
                "Derives a concise ubiquitous language from cam.asset.raina_input (AVC/FSS/PSS). "
                "Use as the first analytical step after the Raina input is fetched in a microservices discovery run."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.domain.discover_ubiquitous_language"],
        ),
        GlobalSkillCreate(
            name="sk.domain.discover_bounded_contexts",
            description=(
                "Discovers bounded contexts and relationships using cam.asset.raina_input and cam.domain.ubiquitous_language. "
                "Use after ubiquitous language is derived."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.domain.discover_bounded_contexts"],
        ),
        GlobalSkillCreate(
            name="sk.architecture.discover_microservices",
            description=(
                "Derives candidate microservices aligned to bounded contexts from cam.domain.bounded_context_map. "
                "Use after bounded contexts are discovered."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.architecture.discover_microservices"],
        ),
        # ---- Contracts & interactions ----
        GlobalSkillCreate(
            name="sk.contract.define_service_apis",
            description=(
                "Defines APIs per service using cam.catalog.microservice_inventory and cam.asset.raina_input "
                "user stories and constraints. Use after microservice inventory is produced."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.contract.define_service_apis"],
        ),
        GlobalSkillCreate(
            name="sk.contract.define_event_catalog",
            description=(
                "Defines domain events for services using cam.catalog.microservice_inventory and "
                "cam.domain.ubiquitous_language. Use after microservice inventory is produced."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.contract.define_event_catalog"],
        ),
        GlobalSkillCreate(
            name="sk.data.define_ownership",
            description=(
                "Assigns data ownership boundaries and persistence strategy per service using "
                "cam.catalog.microservice_inventory and cam.asset.raina_input. "
                "Use after service APIs and event catalog are defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.data.define_ownership"],
        ),
        GlobalSkillCreate(
            name="sk.architecture.map_service_interactions",
            description=(
                "Maps service interactions based on service APIs and events (sync/async, direction, contracts). "
                "Use after service APIs, events, and data ownership are defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.architecture.map_service_interactions"],
        ),
        # ---- Cross-cutting & synthesis ----
        GlobalSkillCreate(
            name="sk.architecture.select_integration_patterns",
            description=(
                "Selects integration patterns (sync/async, saga, outbox, retries, idempotency) using "
                "interactions and data ownership. Use after service interaction matrix is produced."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.architecture.select_integration_patterns"],
        ),
        GlobalSkillCreate(
            name="sk.security.define_architecture",
            description=(
                "Defines identity, edge security, service-to-service trust, data protection, and mitigations "
                "using service inventory, API contracts, and inputs. "
                "Use after interactions and integration patterns are defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.security.define_architecture"],
        ),
        GlobalSkillCreate(
            name="sk.deployment.define_topology",
            description=(
                "Defines runtime topology, networking, environments, and dependencies using service inventory "
                "and security architecture. Use after security architecture is defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.deployment.define_topology"],
        ),
        GlobalSkillCreate(
            name="sk.catalog.rank_tech_stack_microservices",
            description=(
                "Ranks tech choices aligned to integration patterns, deployment topology, and "
                "cam.asset.raina_input constraints/tech hints. "
                "Use after integration patterns and deployment topology are defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.catalog.rank_tech_stack_microservices"],
        ),
        GlobalSkillCreate(
            name="sk.architecture.assemble_microservices",
            description=(
                "Synthesizes the end-to-end microservices architecture from all preceding artifacts into "
                "the primary deliverable. Use as the final synthesis step in a microservices discovery run."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.architecture.assemble_microservices"],
        ),
        # ---- Delivery plan ----
        GlobalSkillCreate(
            name="sk.deployment.plan_migration",
            description=(
                "Creates a phased migration and rollout plan using the final architecture and "
                "cam.asset.raina_input constraints. Use as the final step after the microservices "
                "architecture is assembled."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.deployment.plan_migration"],
        ),
        # ---- Guidance document (MCP) ----
        GlobalSkillCreate(
            name="sk.architecture.generate_guidance",
            description=(
                "Calls the MCP server to produce a Markdown microservices architecture guidance document grounded on "
                "discovered microservices artifacts and RUN INPUTS; emits cam.governance.microservices_arch_guidance. "
                "Use when a completed microservices discovery run is available and a prose-style guidance document "
                "is required for stakeholder review."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.architecture.generate_guidance"],
        ),
    ]

    created = 0
    for skill in targets:
        try:
            existing = await svc.get(skill.name)
            if existing:
                await svc.delete(skill.name, actor="seed")
                log.info("[skills.seeds.microservices] replaced: %s", skill.name)
        except Exception:
            pass
        await svc.create(skill, actor="seed")
        log.info("[skills.seeds.microservices] created: %s", skill.name)
        created += 1

    log.info("[skills.seeds.microservices] Done (created=%d)", created)
