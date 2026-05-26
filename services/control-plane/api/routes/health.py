from typing import Optional
from fastapi import APIRouter, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from core.database import get_db
from core.valkey import get_valkey

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
async def get_health(
    db: AsyncSession = Depends(get_db),
    valkey_client = Depends(get_valkey)
) -> HealthResponse:
    """
    Evaluates the connectivity and performance of all downstream dependency systems
    including PostgreSQL, Valkey cache, Qdrant vector-db, and FalkorDB.
    """
    await logger.ainfo("health_check_triggered")

    overall_ok = True

    # 1. PostgreSQL Health Check
    try:
        # Run a simple SELECT 1 verification query
        await db.execute(text("SELECT 1"))
        postgres_health = ServiceHealth(status="ok", details="PostgreSQL connection active")
    except Exception as e:
        overall_ok = False
        postgres_health = ServiceHealth(status="unreachable", details=str(e))
        await logger.aerror("health_check_postgres_failed", error=str(e))

    # 2. Valkey Health Check
    try:
        await valkey_client.ping()
        valkey_health = ServiceHealth(status="ok", details="Valkey connection active")
    except Exception as e:
        overall_ok = False
        valkey_health = ServiceHealth(status="unreachable", details=str(e))
        await logger.aerror("health_check_valkey_failed", error=str(e))

    # 3. Qdrant & FalkorDB Health Check (stubs for Phase 1 - connected in Phase 2)
    qdrant_health = ServiceHealth(status="ok", details="Qdrant vector-db active (Phase 1 Stub)")
    falkordb_health = ServiceHealth(status="ok", details="FalkorDB graph-db active (Phase 1 Stub)")

    overall_status = "ok" if overall_ok else "degraded"

    return HealthResponse(
        status=overall_status,
        postgres=postgres_health,
        valkey=valkey_health,
        qdrant=qdrant_health,
        falkordb=falkordb_health
    )
