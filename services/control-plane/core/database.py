from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import structlog
from core.config import settings

logger = structlog.get_logger()

# Create standard 2.0 async engine using asyncpg driver
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True for SQL log outputs if needed in debug
    pool_pre_ping=True,  # Enables connection health pings
    pool_size=10,
    max_overflow=20
)

# Async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession
)


class Base(DeclarativeBase):
    """
    Standard declarative base for SQLAlchemy 2.0 models.
    """
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding asynchronous database sessions.
    Handles session cleanup automatically upon request termination.
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await logger.aerror("database_session_error", error=str(e))
            raise
        finally:
            await session.close()
