from typing import Optional
from valkey.asyncio import Valkey
import structlog
from core.config import settings

logger = structlog.get_logger()

# Global valkey client reference
_valkey_client: Optional[Valkey] = None


def get_valkey() -> Valkey:
    """
    Returns the global active Valkey client instance.
    Uses lazy initialization to create the client pool when requested.
    """
    global _valkey_client
    if _valkey_client is None:
        # Rebranded MIT licensed valkey client using VALKEY_URL
        _valkey_client = Valkey.from_url(
            settings.VALKEY_URL,
            decode_responses=True
        )
    return _valkey_client


async def init_valkey() -> None:
    """
    Initializes and verifies the Valkey connection pool.
    """
    client = get_valkey()
    try:
        await client.ping()
        await logger.ainfo("valkey_connected", url=settings.VALKEY_URL)
    except Exception as e:
        await logger.aerror("valkey_connection_failed", error=str(e))
        raise


async def close_valkey() -> None:
    """
    Gracefully shuts down the Valkey connection pool.
    """
    global _valkey_client
    if _valkey_client is not None:
        await _valkey_client.close()
        _valkey_client = None
        await logger.ainfo("valkey_connection_closed")
