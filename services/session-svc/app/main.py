from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.logging_conf import setup_logging
from app.middleware import add_cors, install_request_logging, add_error_handlers
from app.db.mongo import init_indexes
from app.events import get_bus
from app.routers import health_router, session_router

logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting %s on %s:%s", settings.app_name, settings.host, settings.port)

    try:
        await init_indexes()
        logger.info("Mongo indexes initialized")
    except Exception as e:
        logger.exception("Failed to initialize Mongo indexes: %s", e)

    try:
        await get_bus().connect()
    except Exception as e:
        logger.warning("RabbitMQ connect failed (will continue without bus): %s", e)

    yield

    try:
        await get_bus().close()
    except Exception:
        pass
    logger.info("Shutdown complete")


app = FastAPI(title=settings.app_name, lifespan=lifespan)

add_cors(app)
install_request_logging(app)
add_error_handlers(app)

app.include_router(health_router)
app.include_router(session_router)


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "name": settings.app_name,
        "status": "ok",
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn

    reload_flag = os.getenv("RELOAD", "0") in ("1", "true", "True")
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=reload_flag,
        log_level="info",
    )
