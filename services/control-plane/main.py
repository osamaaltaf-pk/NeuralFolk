import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from core.config import settings
from api.routes import health

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

# Initialize FastAPI App
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="The self-hosted AI runtime OS control plane.",
    version="0.1.0",
    debug=settings.DEBUG,
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


@app.on_event("startup")
async def startup_event() -> None:
    """
    Triggers startup log output and events when the control plane launches.
    """
    await logger.ainfo(
        "system_startup",
        project_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
    )
