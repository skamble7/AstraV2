# seeds/capabilities.py
from __future__ import annotations

import inspect
import logging

from app.models import GlobalCapabilityCreate, HTTPTransport, McpExecution
from app.services import CapabilityService

log = logging.getLogger("app.seeds.capabilities")


async def _try_wipe_all(svc: CapabilityService) -> bool:
    """
    Best-effort collection wipe without relying on list_all().
    Tries common method names; returns True if any succeeded.
    """
    candidates = [
        "delete_all",
        "purge_all",
        "purge",
        "truncate",
        "clear",
        "reset",
        "drop_all",
        "wipe_all",
    ]
    for name in candidates:
        method = getattr(svc, name, None)
        if callable(method):
            try:
                result = method()
                if inspect.isawaitable(result):
                    await result
                log.info("[capability.seeds] wiped existing via CapabilityService.%s()", name)
                return True
            except Exception as e:
                log.warning("[capability.seeds] %s() failed: %s", name, e)
    return False


async def seed_capabilities() -> None:
    """
    Seed only the core capabilities still referenced by retained packs.
    """
    log.info("[capability.seeds] Begin")

    svc = CapabilityService()
    wiped = await _try_wipe_all(svc)
    if not wiped:
        log.info("[capability.seeds] No wipe method found; proceeding with replace-by-id")

    long_timeout = 3600

    targets = [
        GlobalCapabilityCreate(
            id="cap.diagram.generate_arch",
            name="Generate Data Pipeline Architecture Guidance Document",
            description=(
                "Calls the MCP server to produce a Markdown architecture guidance document grounded on "
                "discovered data-engineering artifacts and RUN INPUTS; emits "
                "cam.governance.data_pipeline_arch_guidance."
            ),
            tags=["data", "diagram", "docs", "guidance", "mcp"],
            parameters_schema=None,
            produces_kinds=["cam.governance.data_pipeline_arch_guidance"],
            agent=None,
            execution=McpExecution(
                mode="mcp",
                transport=HTTPTransport(
                    kind="http",
                    base_url="http://host.docker.internal:8004",
                    timeout_sec=long_timeout,
                    verify_tls=False,
                    protocol_path="/mcp",
                ),
                tool_name="generate_data_pipeline_arch_guidance",
            ),
        ),
        GlobalCapabilityCreate(
            id="cap.diagram.mermaid",
            name="Generate Mermaid Diagrams from Artifact JSON",
            description=(
                "Given an artifact JSON payload and requested diagram views, returns validated Mermaid instructions."
            ),
            tags=[],
            parameters_schema=None,
            produces_kinds=[],
            agent=None,
            execution=McpExecution(
                mode="mcp",
                transport=HTTPTransport(
                    kind="http",
                    base_url="http://host.docker.internal:8001",
                    headers={"host": "localhost:8001"},
                    timeout_sec=120,
                    verify_tls=False,
                    protocol_path="/mcp",
                ),
                tool_name="diagram.mermaid.generate",
            ),
        ),
    ]

    created = 0
    for cap in targets:
        try:
            existing = await svc.get(cap.id)
            if existing:
                try:
                    await svc.delete(cap.id, actor="seed")
                    log.info("[capability.seeds] replaced: %s (deleted old)", cap.id)
                except AttributeError:
                    log.warning(
                        "[capability.seeds] delete() not available; attempting create() which may fail on unique ID"
                    )
        except Exception:
            pass

        await svc.create(cap, actor="seed")
        log.info("[capability.seeds] created: %s", cap.id)
        created += 1

    log.info("[capability.seeds] Done (created=%d)", created)
