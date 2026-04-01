from __future__ import annotations

import logging
import os

from app.seeds.seed_skills import seed_skills
from app.seeds.seed_data_pipeline_skills import seed_data_pipeline_skills
from app.seeds.seed_microservices_skills import seed_microservices_skills
from app.seeds.seed_data_pipeline_skill_packs import seed_data_pipeline_skill_packs
from app.seeds.seed_microservices_skill_packs import seed_microservices_skill_packs

log = logging.getLogger("app.seeds")


async def run_all_seeds() -> None:
    """Run all skill and skill pack seeders (idempotent, controlled by env flags)."""

    do_skills = os.getenv("SEED_SKILLS", "1") in ("1", "true", "True")
    do_skills_data_pipeline = os.getenv("SEED_SKILLS_DATA_PIPELINE", "1") in ("1", "true", "True")
    do_skills_microservices = os.getenv("SEED_SKILLS_MICROSERVICES", "1") in ("1", "true", "True")
    do_packs_data_pipeline = os.getenv("SEED_SKILL_PACKS_DATA_PIPELINE", "1") in ("1", "true", "True")
    do_packs_microservices = os.getenv("SEED_SKILL_PACKS_MICROSERVICES", "1") in ("1", "true", "True")

    if do_skills:
        await seed_skills()
    else:
        log.info("[skills.seeds] Skipped via env (SEED_SKILLS=0)")

    if do_skills_data_pipeline:
        await seed_data_pipeline_skills()
    else:
        log.info("[skills.seeds.data_pipeline] Skipped via env (SEED_SKILLS_DATA_PIPELINE=0)")

    if do_skills_microservices:
        await seed_microservices_skills()
    else:
        log.info("[skills.seeds.microservices] Skipped via env (SEED_SKILLS_MICROSERVICES=0)")

    if do_packs_data_pipeline:
        await seed_data_pipeline_skill_packs()
    else:
        log.info("[skill_packs.seeds.data_pipeline] Skipped via env (SEED_SKILL_PACKS_DATA_PIPELINE=0)")

    if do_packs_microservices:
        await seed_microservices_skill_packs()
    else:
        log.info("[skill_packs.seeds.microservices] Skipped via env (SEED_SKILL_PACKS_MICROSERVICES=0)")
