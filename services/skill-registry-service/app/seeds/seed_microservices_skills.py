from __future__ import annotations

import logging

from app.models import GlobalSkillCreate, SkillMcpExecution, SkillLlmExecution, SkillStatus
from app.services import SkillService

log = logging.getLogger("app.seeds.microservices_skills")


async def seed_microservices_skills() -> None:
    """
    Seeds microservices-architecture discovery skills (converted from seed_microservices_capabilities.py).
    cap.* → sk.* prefix; transport flattened to base_url for MCP skills.
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
            tags=["astra", "raina", "microservices", "domain"],
            produces_kinds=["cam.domain.ubiquitous_language"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.domain.discover_bounded_contexts",
            description=(
                "Discovers bounded contexts and relationships using cam.asset.raina_input and cam.domain.ubiquitous_language. "
                "Use after ubiquitous language is derived."
            ),
            tags=["astra", "raina", "microservices", "domain", "ddd"],
            produces_kinds=["cam.domain.bounded_context_map"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.architecture.discover_microservices",
            description=(
                "Derives candidate microservices aligned to bounded contexts from cam.domain.bounded_context_map. "
                "Use after bounded contexts are discovered."
            ),
            tags=["astra", "raina", "microservices", "service-design"],
            produces_kinds=["cam.catalog.microservice_inventory"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        # ---- Contracts & interactions ----
        GlobalSkillCreate(
            name="sk.contract.define_service_apis",
            description=(
                "Defines APIs per service using cam.catalog.microservice_inventory and cam.asset.raina_input "
                "user stories and constraints. Use after microservice inventory is produced."
            ),
            tags=["astra", "raina", "microservices", "contracts", "api"],
            produces_kinds=["cam.contract.service_api"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.contract.define_event_catalog",
            description=(
                "Defines domain events for services using cam.catalog.microservice_inventory and "
                "cam.domain.ubiquitous_language. Use after microservice inventory is produced."
            ),
            tags=["astra", "raina", "microservices", "events"],
            produces_kinds=["cam.catalog.events"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.data.define_ownership",
            description=(
                "Assigns data ownership boundaries and persistence strategy per service using "
                "cam.catalog.microservice_inventory and cam.asset.raina_input. "
                "Use after service APIs and event catalog are defined."
            ),
            tags=["astra", "raina", "microservices", "data"],
            produces_kinds=["cam.data.service_data_ownership"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.architecture.map_service_interactions",
            description=(
                "Maps service interactions based on service APIs and events (sync/async, direction, contracts). "
                "Use after service APIs, events, and data ownership are defined."
            ),
            tags=["astra", "raina", "microservices", "interactions"],
            produces_kinds=["cam.architecture.service_interaction_matrix"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        # ---- Cross-cutting & synthesis ----
        GlobalSkillCreate(
            name="sk.architecture.select_integration_patterns",
            description=(
                "Selects integration patterns (sync/async, saga, outbox, retries, idempotency) using "
                "interactions and data ownership. Use after service interaction matrix is produced."
            ),
            tags=["astra", "raina", "microservices", "integration"],
            produces_kinds=["cam.architecture.integration_patterns"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.security.define_architecture",
            description=(
                "Defines identity, edge security, service-to-service trust, data protection, and mitigations "
                "using service inventory, API contracts, and inputs. "
                "Use after interactions and integration patterns are defined."
            ),
            tags=["astra", "raina", "microservices", "security"],
            produces_kinds=["cam.security.microservices_security_architecture"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.deployment.define_topology",
            description=(
                "Defines runtime topology, networking, environments, and dependencies using service inventory "
                "and security architecture. Use after security architecture is defined."
            ),
            tags=["astra", "raina", "microservices", "deployment"],
            produces_kinds=["cam.deployment.microservices_topology"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.catalog.rank_tech_stack_microservices",
            description=(
                "Ranks tech choices aligned to integration patterns, deployment topology, and "
                "cam.asset.raina_input constraints/tech hints. "
                "Use after integration patterns and deployment topology are defined."
            ),
            tags=["astra", "raina", "microservices", "tech-stack"],
            produces_kinds=["cam.catalog.tech_stack_rankings"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.architecture.assemble_microservices",
            description=(
                "Synthesizes the end-to-end microservices architecture from all preceding artifacts into "
                "the primary deliverable. Use as the final synthesis step in a microservices discovery run."
            ),
            tags=["astra", "raina", "microservices", "synthesis"],
            produces_kinds=["cam.architecture.microservices_architecture"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        # ---- Delivery plan ----
        GlobalSkillCreate(
            name="sk.deployment.plan_migration",
            description=(
                "Creates a phased migration and rollout plan using the final architecture and "
                "cam.asset.raina_input constraints. Use as the final step after the microservices "
                "architecture is assembled."
            ),
            tags=["astra", "raina", "microservices", "migration"],
            produces_kinds=["cam.deployment.microservices_migration_plan"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
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
            tags=["microservices", "docs", "guidance", "mcp", "raina", "astra"],
            produces_kinds=["cam.governance.microservices_arch_guidance"],
            status=SkillStatus.published,
            execution=SkillMcpExecution(
                mode="mcp",
                base_url="http://host.docker.internal:8004",
                timeout_sec=180,
                verify_tls=False,
                protocol_path="/mcp",
                tool_name="generate_microservices_arch_guidance",
            ),
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
