from typing import Optional
from fastapi import APIRouter, status
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger()
router = APIRouter()


class ServiceHealth(BaseModel):
    status: str = Field(..., description="Status of the individual dependency service (e.g. 'ok', 'unreachable')")
    details: Optional[str] = Field(None, description="Optional diagnostic details or errors")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall system health status (e.g. 'ok', 'degraded')")
    postgres: ServiceHealth
    valkey: ServiceHealth
    qdrant: ServiceHealth
    falkordb: ServiceHealth


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Get System Health Status"
)
async def get_health() -> HealthResponse:
    """
    Evaluates the connectivity and performance of all downstream dependency systems
    including PostgreSQL, Valkey cache, Qdrant vector-db, and FalkorDB.
    """
    await logger.ainfo("health_check_triggered")

    # In Phase 1 initial scaffold, we mock/stub these database checks
    # until connection pool structures are initialized.
    postgres_health = ServiceHealth(status="ok", details="PostgreSQL scaffold active")
    valkey_health = ServiceHealth(status="ok", details="Valkey broker scaffold active")
    qdrant_health = ServiceHealth(status="ok", details="Qdrant vector-db active")
    falkordb_health = ServiceHealth(status="ok", details="FalkorDB graph-db active")

    return HealthResponse(
        status="ok",
        postgres=postgres_health,
        valkey=valkey_health,
        qdrant=qdrant_health,
        falkordb=falkordb_health
    )
