from __future__ import annotations

import logging

from app.models import GlobalSkillCreate
from app.seeds._skill_md import SKILL_MD
from app.services import SkillService

log = logging.getLogger("app.seeds.data_pipeline_skills")


async def seed_data_pipeline_skills() -> None:
    """
    Seeds data-pipeline skills.
    skill_md_body contains the complete SKILL.md (frontmatter + body).
    All skills are domain='astra', is_artifact_skill=True.
    """
    log.info("[skills.seeds.data_pipeline] Begin")

    svc = SkillService()

    targets: list[GlobalSkillCreate] = [
        GlobalSkillCreate(
            name="sk.asset.fetch_raina_input",
            description=(
                "Fetches a Raina input JSON (AVC/FSS/PSS) from a URL via the MCP raina-input-fetcher "
                "and emits a validated cam.asset.raina_input artifact. "
                "Use when a workspace run requires architecture discovery inputs and a URL pointing to "
                "an AVC/FSS/PSS JSON payload is available. This is typically the first skill invoked "
                "in any RAINA-domain run — no upstream artifacts are required."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.asset.fetch_raina_input"],
        ),
        GlobalSkillCreate(
            name="sk.data.discover_logical_model",
            description=(
                "Derives entities, attributes, keys, and relationships from AVC/FSS/PSS and goals/NFRs. "
                "Use after cam.asset.raina_input is available to produce the logical data model."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.data.discover_logical_model"],
        ),
        GlobalSkillCreate(
            name="sk.workflow.discover_business_flows",
            description=(
                "Extracts actor-centric flows mapped to datasets from AVC/FSS and architectural context. "
                "Use after cam.asset.raina_input is available."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.workflow.discover_business_flows"],
        ),
        GlobalSkillCreate(
            name="sk.architecture.select_pipeline_patterns",
            description=(
                "Evaluates Batch/Stream/Lambda/Microservices/Event-driven patterns against FR/NFRs and constraints. "
                "Use after logical model and business flows are available."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.architecture.select_pipeline_patterns"],
        ),
        GlobalSkillCreate(
            name="sk.contract.define_dataset",
            description=(
                "Produces implementation-grade dataset contracts with schema, keys, PII flags, stewardship, "
                "quality rules, and retention. Use after pipeline patterns are selected."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.contract.define_dataset"],
        ),
        GlobalSkillCreate(
            name="sk.architecture.assemble_pipeline",
            description=(
                "Synthesizes stages, routing, idempotency strategy, SLAs, and ranked tech stack recommendations. "
                "Use after all component specs (transforms, jobs, orchestration) are complete."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.architecture.assemble_pipeline"],
        ),
        GlobalSkillCreate(
            name="sk.workflow.spec_batch_job",
            description=(
                "Creates batch job schedules and steps (ETL/ELT/validate) aligned to pipeline SLAs and idempotency. "
                "Use after pipeline patterns and dataset contracts are defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.workflow.spec_batch_job"],
        ),
        GlobalSkillCreate(
            name="sk.workflow.spec_stream_job",
            description=(
                "Defines streaming jobs with sources, sinks, windowing, processing ops, and consistency settings. "
                "Use after pipeline patterns and dataset contracts are defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.workflow.spec_stream_job"],
        ),
        GlobalSkillCreate(
            name="sk.data.spec_transforms",
            description=(
                "Specifies dataset-to-dataset transforms with logic and associated data quality checks. "
                "Use after dataset contracts are defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.data.spec_transforms"],
        ),
        GlobalSkillCreate(
            name="sk.data.map_lineage",
            description=(
                "Builds dataset/job/source lineage graph (reads/writes/derives/publishes) from specs and contracts. "
                "Use after transforms, batch jobs, and stream jobs are specified."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.data.map_lineage"],
        ),
        GlobalSkillCreate(
            name="sk.governance.derive_policies",
            description=(
                "Outputs classification, access/retention, and lineage requirements from AVC/NFR and contracts. "
                "Use after dataset contracts and lineage map are available."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.governance.derive_policies"],
        ),
        GlobalSkillCreate(
            name="sk.security.define_access_control",
            description=(
                "Generates dataset-role access rules (read/write/admin/mask) from classifications and governance policy. "
                "Use after governance policies are derived."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.security.define_access_control"],
        ),
        GlobalSkillCreate(
            name="sk.security.define_masking",
            description=(
                "Emits field-level masking/tokenization/generalization policies for PII and sensitive data. "
                "Use after governance policies and access control are defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.security.define_masking"],
        ),
        GlobalSkillCreate(
            name="sk.qa.define_data_sla",
            description=(
                "Sets SLA targets and monitoring plan (freshness, latency, availability, DQ pass rate). "
                "Use after pipeline architecture and dataset contracts are assembled."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.qa.define_data_sla"],
        ),
        GlobalSkillCreate(
            name="sk.observability.define_spec",
            description=(
                "Declares required metrics, logs, traces, and exporters to enforce SLAs and diagnose issues. "
                "Use after SLAs are defined to produce the observability specification."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.observability.define_spec"],
        ),
        GlobalSkillCreate(
            name="sk.workflow.define_orchestration",
            description=(
                "Wires batch/stream jobs into a dependency graph with failure policy, consistent with selected orchestrator. "
                "Use after batch and stream job specs are defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.workflow.define_orchestration"],
        ),
        GlobalSkillCreate(
            name="sk.catalog.rank_tech_stack",
            description=(
                "Produces category-wise ranked tooling (streaming, batch compute, storage, orchestration, DQ, catalog, "
                "observability) with rationale. Use after pipeline patterns and architecture are selected."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.catalog.rank_tech_stack"],
        ),
        GlobalSkillCreate(
            name="sk.catalog.inventory_sources",
            description=(
                "Enumerates principal data sources and sinks implied by flows, entities, and constraints. "
                "Use early in a data pipeline discovery run, after cam.asset.raina_input is available."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.catalog.inventory_sources"],
        ),
        GlobalSkillCreate(
            name="sk.catalog.data_products",
            description=(
                "Bundles datasets into Data-as-a-Product entries with ownership and SLO commitment. "
                "Use after dataset contracts and pipeline architecture are assembled."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.catalog.data_products"],
        ),
        GlobalSkillCreate(
            name="sk.diagram.topology",
            description=(
                "Declares platform components and links (ingest, queue, compute, storage, orchestration, catalog, DQ, "
                "observability) across environments. Use after orchestration and tech stack are defined."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.diagram.topology"],
        ),
        GlobalSkillCreate(
            name="sk.deployment.plan_pipeline",
            description=(
                "Creates deployment plan with phased rollout, backfill/migration, and backout across environments. "
                "Use as the final step after the pipeline architecture is assembled."
            ),
            domain="astra",
            is_artifact_skill=True,
            skill_md_body=SKILL_MD["sk.deployment.plan_pipeline"],
        ),
    ]

    created = 0
    for skill in targets:
        try:
            existing = await svc.get(skill.name)
            if existing:
                await svc.delete(skill.name, actor="seed")
                log.info("[skills.seeds.data_pipeline] replaced: %s", skill.name)
        except Exception:
            pass
        await svc.create(skill, actor="seed")
        log.info("[skills.seeds.data_pipeline] created: %s", skill.name)
        created += 1

    log.info("[skills.seeds.data_pipeline] Done (created=%d)", created)
