from __future__ import annotations

import logging
import os
from typing import Iterable

from app.models import SkillPackCreate, SkillPlaybook, SkillPlaybookStep
from app.services import SkillPackService

log = logging.getLogger("app.seeds.skill_packs.data_pipeline")


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
                log.info("[skill_packs.seeds.data_pipeline] replaced existing: %s", pack_id)
            else:
                log.warning("[skill_packs.seeds.data_pipeline] delete returned falsy for %s; continuing to create", pack_id)
        except Exception as e:
            log.warning("[skill_packs.seeds.data_pipeline] delete failed for %s: %s (continuing)", pack_id, e)

    created = await svc.create(pack, actor="seed")
    log.info("[skill_packs.seeds.data_pipeline] created: %s", created.id)


async def _publish_all(svc: SkillPackService, ids: Iterable[str]) -> None:
    for pack_id in ids:
        try:
            published = await svc.publish(pack_id, actor="seed")
            if published:
                log.info("[skill_packs.seeds.data_pipeline] published: %s", published.id)
        except Exception as e:
            log.warning("[skill_packs.seeds.data_pipeline] publish failed for %s: %s", pack_id, e)


def _steps(*skill_ids: str) -> SkillPlaybook:
    return SkillPlaybook(steps=[SkillPlaybookStep(skill_id=s) for s in skill_ids])


async def seed_data_pipeline_skill_packs() -> None:
    """
    Seeds Data Engineering Architecture Discovery skill packs
    (converted from seed_data_pipeline_packs.py).
    cap.* → sk.* prefix; single playbook (primary discovery flow).
    """
    svc = SkillPackService()
    publish_on_seed = os.getenv("SKILL_PACK_SEED_PUBLISH", "1").lower() in ("1", "true", "yes")

    # v1.0 — without MCP fetch step
    pack_v1_0 = SkillPackCreate(
        key="data-pipeline-arch",
        version="v1.0",
        title="Data Engineering Architecture Discovery Pack (v1.0)",
        description=(
            "Generates an implementation-ready data pipeline architecture from AVC/FSS/PSS inputs, including patterns "
            "(batch/stream/lambda/event-driven), dataset contracts, transformations, lineage, governance, SLAs/observability, "
            "orchestration, topology, tech stack ranking, data products, and a concrete deployment plan."
        ),
        skill_ids=[
            "sk.catalog.inventory_sources",
            "sk.workflow.discover_business_flows",
            "sk.data.discover_logical_model",
            "sk.architecture.select_pipeline_patterns",
            "sk.contract.define_dataset",
            "sk.data.spec_transforms",
            "sk.workflow.spec_batch_job",
            "sk.workflow.spec_stream_job",
            "sk.workflow.define_orchestration",
            "sk.data.map_lineage",
            "sk.governance.derive_policies",
            "sk.security.define_access_control",
            "sk.security.define_masking",
            "sk.qa.define_data_sla",
            "sk.observability.define_spec",
            "sk.diagram.topology",
            "sk.catalog.rank_tech_stack",
            "sk.catalog.data_products",
            "sk.architecture.assemble_pipeline",
            "sk.deployment.plan_pipeline",
            "sk.diagram.generate_arch",
        ],
        agent_skill_ids=["sk.diagram.mermaid"],
        playbook=_steps(
            "sk.catalog.inventory_sources",
            "sk.workflow.discover_business_flows",
            "sk.data.discover_logical_model",
            "sk.architecture.select_pipeline_patterns",
            "sk.contract.define_dataset",
            "sk.data.spec_transforms",
            "sk.workflow.spec_batch_job",
            "sk.workflow.spec_stream_job",
            "sk.workflow.define_orchestration",
            "sk.data.map_lineage",
            "sk.governance.derive_policies",
            "sk.security.define_access_control",
            "sk.security.define_masking",
            "sk.qa.define_data_sla",
            "sk.observability.define_spec",
            "sk.diagram.topology",
            "sk.catalog.rank_tech_stack",
            "sk.catalog.data_products",
            "sk.architecture.assemble_pipeline",
            "sk.deployment.plan_pipeline",
        ),
    )

    # v1.1 — with MCP fetch step as first step
    pack_v1_1 = SkillPackCreate(
        key="data-pipeline-arch",
        version="v1.1",
        title="Data Engineering Architecture Discovery Pack (v1.1)",
        description=(
            "Generates an implementation-ready data pipeline architecture from AVC/FSS/PSS inputs. "
            "This version fetches the Raina input via MCP as the first step, then runs the full discovery chain."
        ),
        skill_ids=[
            "sk.asset.fetch_raina_input",
            "sk.catalog.inventory_sources",
            "sk.workflow.discover_business_flows",
            "sk.data.discover_logical_model",
            "sk.architecture.select_pipeline_patterns",
            "sk.contract.define_dataset",
            "sk.data.spec_transforms",
            "sk.workflow.spec_batch_job",
            "sk.workflow.spec_stream_job",
            "sk.workflow.define_orchestration",
            "sk.data.map_lineage",
            "sk.governance.derive_policies",
            "sk.security.define_access_control",
            "sk.security.define_masking",
            "sk.qa.define_data_sla",
            "sk.observability.define_spec",
            "sk.diagram.topology",
            "sk.catalog.rank_tech_stack",
            "sk.catalog.data_products",
            "sk.architecture.assemble_pipeline",
            "sk.deployment.plan_pipeline",
            "sk.diagram.generate_arch",
        ],
        agent_skill_ids=["sk.diagram.mermaid"],
        playbook=_steps(
            "sk.asset.fetch_raina_input",
            "sk.catalog.inventory_sources",
            "sk.workflow.discover_business_flows",
            "sk.data.discover_logical_model",
            "sk.architecture.select_pipeline_patterns",
            "sk.contract.define_dataset",
            "sk.data.spec_transforms",
            "sk.workflow.spec_batch_job",
            "sk.workflow.spec_stream_job",
            "sk.workflow.define_orchestration",
            "sk.data.map_lineage",
            "sk.governance.derive_policies",
            "sk.security.define_access_control",
            "sk.security.define_masking",
            "sk.qa.define_data_sla",
            "sk.observability.define_spec",
            "sk.diagram.topology",
            "sk.catalog.rank_tech_stack",
            "sk.catalog.data_products",
            "sk.architecture.assemble_pipeline",
            "sk.deployment.plan_pipeline",
        ),
    )

    await _replace_by_id(svc, pack_v1_0)
    await _replace_by_id(svc, pack_v1_1)

    if publish_on_seed:
        await _publish_all(svc, ids=("data-pipeline-arch@v1.0", "data-pipeline-arch@v1.1"))
