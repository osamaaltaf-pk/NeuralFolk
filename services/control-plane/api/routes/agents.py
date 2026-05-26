from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from models.models import AgentModel
from schemas.schemas import AgentSpawnRequest, AgentSpawnResponse
from core.events import publish_event
from celery import Celery
import structlog

router = APIRouter()
logger = structlog.get_logger()
celery_client = Celery(broker="redis://cache:6379/0")

@router.post("/spawn", response_model=AgentSpawnResponse, status_code=status.HTTP_201_CREATED)
async def spawn_agent(
    request: AgentSpawnRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
    # 1. Store agent state in Database
    agent = AgentModel(
        model=request.model,
        task_summary=request.task_summary,
        status="pending"
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    
    # 2. Emit spawn event
    await publish_event("agent.spawned", {
        "agent_id": agent.id,
        "model": agent.model,
        "task_summary": agent.task_summary
    })
    
    # 3. Enqueue the task via Celery
    try:
        celery_client.send_task(
            "worker.tasks.run_agent_loop",
            args=[agent.id, agent.model, agent.task_summary, request.hardware]
        )
    except Exception as e:
        await logger.aerror("celery_spawn_enqueue_failed", agent_id=agent.id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue agent task execution: {str(e)}"
        )
        
    return {
        "agent_id": agent.id,
        "status": agent.status,
        "created_at": agent.created_at
    }
