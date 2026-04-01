from __future__ import annotations

import logging

from app.models import GlobalSkillCreate, SkillMcpExecution, SkillLlmExecution, SkillStatus
from app.services import SkillService

log = logging.getLogger("app.seeds.data_pipeline_skills")


def _llm_skill(
    name: str,
    skill_name: str,
    description: str,
    produces_kinds: list[str],
    tags: list[str] | None = None,
) -> GlobalSkillCreate:
    return GlobalSkillCreate(
        name=name,
        description=description,
        tags=tags or ["astra", "data", "pipeline"],
        produces_kinds=produces_kinds,
        status=SkillStatus.published,
        execution=SkillLlmExecution(
            mode="llm",
            llm_config_ref="dev.llm.openai.fast",
        ),
    )


async def seed_data_pipeline_skills() -> None:
    """
    Seeds data-pipeline skills (converted from seed_data_pipeline_capabilities.py).
    cap.* → sk.* prefix; transport flattened to base_url for MCP skills.
    """
    log.info("[skills.seeds.data_pipeline] Begin")

    svc = SkillService()

    targets: list[GlobalSkillCreate] = [
        # ---- MCP skill: fetch raina input ----
        GlobalSkillCreate(
            name="sk.asset.fetch_raina_input",
            description=(
                "Fetches a Raina input JSON (AVC/FSS/PSS) from a URL via the MCP raina-input-fetcher "
                "and emits a validated cam.asset.raina_input artifact. "
                "Use when a workspace run requires architecture discovery inputs and a URL pointing to "
                "an AVC/FSS/PSS JSON payload is available. This is typically the first skill invoked "
                "in any RAINA-domain run — no upstream artifacts are required."
            ),
            tags=["inputs", "raina", "discovery", "mcp"],
            produces_kinds=["cam.asset.raina_input"],
            status=SkillStatus.published,
            execution=SkillMcpExecution(
                mode="mcp",
                base_url="http://host.docker.internal:8003",
                headers={"host": "localhost:8003"},
                timeout_sec=180,
                verify_tls=False,
                protocol_path="/mcp",
                tool_name="raina.input.fetch",
            ),
        ),
        # ---- LLM skills (data-pipeline discovery chain) ----
        GlobalSkillCreate(
            name="sk.data.discover_logical_model",
            description=(
                "Derives entities, attributes, keys, and relationships from AVC/FSS/PSS and goals/NFRs. "
                "Use after cam.asset.raina_input is available to produce the logical data model."
            ),
            tags=["astra", "data", "modeling"],
            produces_kinds=["cam.data.model_logical"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.workflow.discover_business_flows",
            description=(
                "Extracts actor-centric flows mapped to datasets from AVC/FSS and architectural context. "
                "Use after cam.asset.raina_input is available."
            ),
            tags=["astra", "workflow", "discovery"],
            produces_kinds=["cam.workflow.business_flow_catalog"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.architecture.select_pipeline_patterns",
            description=(
                "Evaluates Batch/Stream/Lambda/Microservices/Event-driven patterns against FR/NFRs and constraints. "
                "Use after logical model and business flows are available."
            ),
            tags=["astra", "architecture", "patterns"],
            produces_kinds=["cam.architecture.pipeline_patterns"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.contract.define_dataset",
            description=(
                "Produces implementation-grade dataset contracts with schema, keys, PII flags, stewardship, "
                "quality rules, and retention. Use after pipeline patterns are selected."
            ),
            tags=["astra", "data", "contracts"],
            produces_kinds=["cam.data.dataset_contract"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.architecture.assemble_pipeline",
            description=(
                "Synthesizes stages, routing, idempotency strategy, SLAs, and ranked tech stack recommendations. "
                "Use after all component specs (transforms, jobs, orchestration) are complete."
            ),
            tags=["astra", "workflow", "architecture"],
            produces_kinds=["cam.workflow.data_pipeline_architecture"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.workflow.spec_batch_job",
            description=(
                "Creates batch job schedules and steps (ETL/ELT/validate) aligned to pipeline SLAs and idempotency. "
                "Use after pipeline patterns and dataset contracts are defined."
            ),
            tags=["astra", "workflow", "batch"],
            produces_kinds=["cam.workflow.batch_job_spec"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.workflow.spec_stream_job",
            description=(
                "Defines streaming jobs with sources, sinks, windowing, processing ops, and consistency settings. "
                "Use after pipeline patterns and dataset contracts are defined."
            ),
            tags=["astra", "workflow", "streaming"],
            produces_kinds=["cam.workflow.stream_job_spec"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.data.spec_transforms",
            description=(
                "Specifies dataset-to-dataset transforms with logic and associated data quality checks. "
                "Use after dataset contracts are defined."
            ),
            tags=["astra", "data", "transform"],
            produces_kinds=["cam.workflow.transform_spec"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.data.map_lineage",
            description=(
                "Builds dataset/job/source lineage graph (reads/writes/derives/publishes) from specs and contracts. "
                "Use after transforms, batch jobs, and stream jobs are specified."
            ),
            tags=["astra", "data", "lineage"],
            produces_kinds=["cam.data.lineage_map"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.governance.derive_policies",
            description=(
                "Outputs classification, access/retention, and lineage requirements from AVC/NFR and contracts. "
                "Use after dataset contracts and lineage map are available."
            ),
            tags=["astra", "governance", "policy"],
            produces_kinds=["cam.governance.data_governance_policies"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.security.define_access_control",
            description=(
                "Generates dataset-role access rules (read/write/admin/mask) from classifications and governance policy. "
                "Use after governance policies are derived."
            ),
            tags=["astra", "security", "policy"],
            produces_kinds=["cam.security.data_access_control"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.security.define_masking",
            description=(
                "Emits field-level masking/tokenization/generalization policies for PII and sensitive data. "
                "Use after governance policies and access control are defined."
            ),
            tags=["astra", "security", "privacy"],
            produces_kinds=["cam.security.data_masking_policy"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.qa.define_data_sla",
            description=(
                "Sets SLA targets and monitoring plan (freshness, latency, availability, DQ pass rate). "
                "Use after pipeline architecture and dataset contracts are assembled."
            ),
            tags=["astra", "quality", "sla"],
            produces_kinds=["cam.qa.data_sla"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.observability.define_spec",
            description=(
                "Declares required metrics, logs, traces, and exporters to enforce SLAs and diagnose issues. "
                "Use after SLAs are defined to produce the observability specification."
            ),
            tags=["astra", "observability", "otel"],
            produces_kinds=["cam.observability.data_observability_spec"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.workflow.define_orchestration",
            description=(
                "Wires batch/stream jobs into a dependency graph with failure policy, consistent with selected orchestrator. "
                "Use after batch and stream job specs are defined."
            ),
            tags=["astra", "workflow", "orchestration"],
            produces_kinds=["cam.workflow.orchestration_spec"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.catalog.rank_tech_stack",
            description=(
                "Produces category-wise ranked tooling (streaming, batch compute, storage, orchestration, DQ, catalog, "
                "observability) with rationale. Use after pipeline patterns and architecture are selected."
            ),
            tags=["astra", "architecture", "stack"],
            produces_kinds=["cam.catalog.tech_stack_rankings"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.catalog.inventory_sources",
            description=(
                "Enumerates principal data sources and sinks implied by flows, entities, and constraints. "
                "Use early in a data pipeline discovery run, after cam.asset.raina_input is available."
            ),
            tags=["astra", "data", "inventory"],
            produces_kinds=["cam.catalog.data_source_inventory"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.catalog.data_products",
            description=(
                "Bundles datasets into Data-as-a-Product entries with ownership and SLO commitment. "
                "Use after dataset contracts and pipeline architecture are assembled."
            ),
            tags=["astra", "data", "product"],
            produces_kinds=["cam.catalog.data_products"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.diagram.topology",
            description=(
                "Declares platform components and links (ingest, queue, compute, storage, orchestration, catalog, DQ, "
                "observability) across environments. Use after orchestration and tech stack are defined."
            ),
            tags=["astra", "deployment", "topology"],
            produces_kinds=["cam.deployment.data_platform_topology"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
        ),
        GlobalSkillCreate(
            name="sk.deployment.plan_pipeline",
            description=(
                "Creates deployment plan with phased rollout, backfill/migration, and backout across environments. "
                "Use as the final step after the pipeline architecture is assembled."
            ),
            tags=["astra", "deployment", "plan"],
            produces_kinds=["cam.deployment.pipeline_deployment_plan"],
            status=SkillStatus.published,
            execution=SkillLlmExecution(mode="llm", llm_config_ref="dev.llm.openai.fast"),
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
