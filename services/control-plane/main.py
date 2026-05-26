import logging
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from core.config import settings
from core.valkey import init_valkey, close_valkey
from api.routes import health
from api.routes import inference
from api.routes import agents
from api.routes import events_ws

# Configure structlog
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.ExtraAdder(),
        structlog.processors.JSONRenderer() if not settings.DEBUG else structlog.processors.KeyValueRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Handles application startup and shutdown lifecycle events,
    initializing and disposing resource connection pools gracefully.
    """
    # 1. Startup: Database DDL auto-generation & Valkey connect
    try:
        from core.database import Base, engine
        from models.models import AgentModel, WorkflowModel # noqa: F401
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        await init_valkey()
        from core.events import publish_event
        await publish_event("system.startup", {"version": "0.1.0", "hardware_detected": "CPU/GPU"})
    except Exception as e:
        await logger.acritical("lifespan_startup_failed", error=str(e))
        # In production, we might want to block startup; here we allow fallback for stubs
        pass

    yield

    # 2. Shutdown: Dispose Valkey pool
    await close_valkey()
    await logger.ainfo("system_shutdown_completed")


# Initialize FastAPI App with modern lifespan manager
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="The self-hosted AI runtime OS control plane.",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["System"])
app.include_router(inference.router, prefix=settings.API_V1_STR, tags=["Inference"])
app.include_router(agents.router, prefix=settings.API_V1_STR, tags=["Agents"])
app.include_router(events_ws.router, prefix=settings.API_V1_STR, tags=["Events"])

