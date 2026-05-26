import asyncio
import os
from typing import Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from worker.celery_app import app
from worker.agent.base import ReactiveAgent
import structlog

logger = structlog.get_logger()

# Resolve Database URL dynamically for container vs host environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@database:5432/neuralfolk")

# Local host fallback resolution
if "database" in DATABASE_URL:
    try:
        # Check if database is reachable locally on the container hostname 'database'
        # If not, rewrite hostname to 'localhost' for local host pytest suites
        import socket
        socket.gethostbyname("database")
    except Exception:
        DATABASE_URL = DATABASE_URL.replace("@database:", "@localhost:")

# Initialize database components
engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@app.task(name="worker.tasks.run_agent_loop")
def run_agent_loop(agent_id: str, model: str, task_summary: str, hardware: Optional[str] = None) -> str:
    """
    Runs the agent loop asynchronously inside Celery consumer threads.
    """
    # Enforce loop context inside thread
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    async def _async_run():
        await logger.ainfo("celery_task_started", agent_id=agent_id, model=model)
        
        # 1. Update database agent status to 'executing'
        async with async_session() as session:
            await session.execute(
                text("UPDATE agents SET status = :status WHERE id = :id"),
                {"status": "executing", "id": agent_id}
            )
            await session.commit()
            
        # 2. Instantiate and run mock-free ReactiveAgent
        agent = ReactiveAgent(
            agent_id=agent_id,
            model=model,
            task=task_summary
        )
        
        try:
            await agent.run(hardware=hardware)
            # Update database status to completed
            async with async_session() as session:
                await session.execute(
                    text("UPDATE agents SET status = :status, completed_at = NOW(), steps_count = 3 WHERE id = :id"),
                    {"status": "completed", "id": agent_id}
                )
                await session.commit()
            await logger.ainfo("celery_task_completed", agent_id=agent_id)
        except Exception as e:
            await logger.aerror("agent_execution_failed", agent_id=agent_id, error=str(e))
            # Update database status to failed
            async with async_session() as session:
                await session.execute(
                    text("UPDATE agents SET status = :status, completed_at = NOW() WHERE id = :id"),
                    {"status": "failed", "id": agent_id}
                )
                await session.commit()
                
    loop.run_until_complete(_async_run())
    return f"Completed execution for agent {agent_id}"
