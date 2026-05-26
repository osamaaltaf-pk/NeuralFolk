import pytest
from httpx import AsyncClient
from main import app
from core.database import get_db
from core.valkey import get_valkey


# ==========================================
# Mock Dependencies
# ==========================================
class MockDbSession:
    """
    Mock SQLAlchemy AsyncSession for API health check route testing.
    """
    async def execute(self, statement) -> bool:
        return True


async def mock_get_db():
    yield MockDbSession()


class MockValkeyClient:
    """
    Mock Valkey client for API health check route testing.
    """
    async def ping(self) -> bool:
        return True


def mock_get_valkey():
    return MockValkeyClient()


# Apply dependency overrides for the duration of the test module
app.dependency_overrides[get_db] = mock_get_db
app.dependency_overrides[get_valkey] = mock_get_valkey


@pytest.mark.asyncio
async def test_health_check_endpoint_success() -> None:
    """
    Verifies that the /health endpoint returns an OK status and correct JSON
    schema structure when downstream services are operational.
    """
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    # Verify Pydantic schema keys and overall states
    assert data["status"] == "ok"
    
    assert "postgres" in data
    assert data["postgres"]["status"] == "ok"
    assert "PostgreSQL" in data["postgres"]["details"]

    assert "valkey" in data
    assert data["valkey"]["status"] == "ok"
    assert "Valkey" in data["valkey"]["details"]

    assert "qdrant" in data
    assert "falkordb" in data
