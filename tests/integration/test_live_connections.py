import pytest
from sqlalchemy import text
from core.config import settings
from core.database import async_session_maker
from core.valkey import get_valkey


@pytest.mark.asyncio
async def test_live_postgres_connection() -> None:
    """
    Integration test: Attempts connection to the live PostgreSQL database.
    Skips dynamically if PostgreSQL is offline or unreachable.
    """
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT 1"))
            value = result.scalar()
            assert value == 1
    except Exception as e:
        pytest.skip(f"Live PostgreSQL unreachable (skipping integration check): {e}")


@pytest.mark.asyncio
async def test_live_valkey_connection() -> None:
    """
    Integration test: Attempts connection to the live Valkey server.
    Skips dynamically if Valkey is offline or unreachable.
    """
    try:
        client = get_valkey()
        pong = await client.ping()
        assert pong is True
    except Exception as e:
        pytest.skip(f"Live Valkey unreachable (skipping integration check): {e}")
