# services/capability-service/app/seeds/__init__.py
from __future__ import annotations

import logging
import os

from app.seeds.seed_capabilities import seed_capabilities
from app.seeds.seed_data_pipeline_capabilities import seed_capabilities as seed_capabilities_data_pipeline
from app.seeds.seed_data_pipeline_packs import seed_data_pipeline_packs

from app.seeds.seed_microservices_capabilities import seed_microservices_capabilities
from app.seeds.seed_microservices_packs import seed_microservices_packs

log = logging.getLogger("app.seeds")


async def run_all_seeds() -> None:
    """
    Run only the retained capability and pack seeders.
    """

    do_capabilities = os.getenv("SEED_CAPABILITIES", "1") in ("1", "true", "True")
    do_capabilities_data_pipeline = os.getenv("SEED_CAPABILITIES_DATA_PIPELINE", "1") in ("1", "true", "True")
    do_capabilities_microservices = os.getenv("SEED_CAPABILITIES_MICROSERVICES", "1") in ("1", "true", "True")

    do_packs_data_pipeline = os.getenv("SEED_PACKS_DATA_PIPELINE", "1") in ("1", "true", "True")
    do_packs_microservices = os.getenv("SEED_PACKS_MICROSERVICES", "1") in ("1", "true", "True")

    if do_capabilities:
        await seed_capabilities()
    else:
        log.info("[capability.seeds.capabilities] Skipped via env")

    if do_capabilities_data_pipeline:
        await seed_capabilities_data_pipeline()
    else:
        log.info("[capability.seeds.data_pipeline_capabilities] Skipped via env")

    if do_capabilities_microservices:
        await seed_microservices_capabilities()
    else:
        log.info("[capability.seeds.microservices_capabilities] Skipped via env")

    if do_packs_data_pipeline:
        await seed_data_pipeline_packs()
    else:
        log.info("[capability.seeds.data_pipeline_packs] Skipped via env")

    if do_packs_microservices:
        await seed_microservices_packs()
    else:
        log.info("[capability.seeds.microservices_packs] Skipped via env")
