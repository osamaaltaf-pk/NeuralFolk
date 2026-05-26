import pytest
from core.config import settings
from core.database import get_db
from core.valkey import get_valkey


def test_settings_loaded() -> None:
    """
    Verifies settings schema properties parse environment variables correctly.
    """
    assert settings.PROJECT_NAME == "NeuralFolk"
    assert settings.API_V1_STR == "/api/v1"
    assert isinstance(settings.DEBUG, bool)


def test_valkey_lazy_loading() -> None:
    """
    Verifies that get_valkey returns a valid client reference and loads lazily.
    """
    client = get_valkey()
    assert client is not None
    # Subsequent calls should return the same singleton reference
    client2 = get_valkey()
    assert client is client2


@pytest.mark.asyncio
async def test_get_db_yield() -> None:
    """
    Verifies database dependency yields async generator objects.
    """
    db_gen = get_db()
    assert hasattr(db_gen, "__anext__")
