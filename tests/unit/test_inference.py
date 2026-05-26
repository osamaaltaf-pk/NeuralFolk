import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from inference.router import InferenceRouter
import ollama
import httpx

# ==========================================
# Mock Clients
# ==========================================
class MockHttpxResponse:
    def __init__(self, json_data: dict, status_code: int = 200) -> None:
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("Mock error", request=None, response=self)

    def json(self) -> dict:
        return self._json_data

# ==========================================
# Fixtures
# ==========================================
@pytest.fixture(autouse=True)
def patch_clients(monkeypatch) -> None:
    # 1. Mock ollama.AsyncClient.chat method directly
    async def mock_ollama_chat(self, *args, **kwargs) -> dict:
        model = kwargs.get("model", "miniCPM5-1B")
        return {
            "model": model,
            "message": {
                "role": "assistant",
                "content": f"Mocked Ollama response for {model}"
            },
            "prompt_eval_count": 12,
            "eval_count": 24
        }
    monkeypatch.setattr(ollama.AsyncClient, "chat", mock_ollama_chat)

    original_post = httpx.AsyncClient.post
    async def mock_httpx_post(self, url: str, json: dict = None, **kwargs) -> MockHttpxResponse:
        # If the URL is a relative path (e.g. starting with /), it is destined for the test client app - do not intercept
        if not str(url).startswith("http"):
            return await original_post(self, url, json=json, **kwargs)
            
        model = (json or {}).get("model", "test-model")
        return MockHttpxResponse({
            "model": model,
            "choices": [{
                "message": {
                    "role": "assistant",
                    "content": f"Mocked response from {url}"
                }
            }],
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 30,
                "total_tokens": 45
            }
        })
    monkeypatch.setattr(httpx.AsyncClient, "post", mock_httpx_post)


# ==========================================
# Unit Tests
# ==========================================
@pytest.mark.asyncio
async def test_router_routing_decision_ollama() -> None:
    """
    Verifies that standard request sizes route to the default Ollama backend.
    """
    router = InferenceRouter()
    result = await router.chat(
        model="miniCPM5-1B",
        messages=[{"role": "user", "content": "Hello world"}]
    )
    assert result["model"] == "miniCPM5-1B"
    assert "Mocked Ollama response" in result["message"]["content"]
    assert result["usage"]["total_tokens"] == 36

@pytest.mark.asyncio
async def test_router_routing_decision_sglang_context() -> None:
    """
    Verifies that requests with high estimated or explicit context lengths (>32k)
    route to SGLang.
    """
    router = InferenceRouter()
    # Explicit context length override
    result = await router.chat(
        model="miniCPM5-1B",
        messages=[{"role": "user", "content": "Hello"}],
        context_length=35000
    )
    # Mock Httpx client is used since SGLang executes via standard POST
    assert "Mocked response from http://sglang:30000/v1/chat/completions" in result["message"]["content"]
    assert result["usage"]["total_tokens"] == 45

@pytest.mark.asyncio
async def test_router_routing_decision_llamacpp_hardware() -> None:
    """
    Verifies that CPU-only configurations target llama.cpp.
    """
    router = InferenceRouter()
    result = await router.chat(
        model="miniCPM5-1B",
        messages=[{"role": "user", "content": "Hello"}],
        hardware="no_gpu"
    )
    assert "Mocked response from http://llamacpp:8080/v1/chat/completions" in result["message"]["content"]

@pytest.mark.asyncio
async def test_router_routing_decision_vllm_batching() -> None:
    """
    Verifies that high batch sizes target vLLM.
    """
    router = InferenceRouter()
    result = await router.chat(
        model="miniCPM5-1B",
        messages=[{"role": "user", "content": "Hello"}],
        batch_size=5
    )
    assert "Mocked response from http://vllm:8000/v1/chat/completions" in result["message"]["content"]

@pytest.mark.asyncio
async def test_router_routing_decision_tensorrt_gpu() -> None:
    """
    Verifies that NVIDIA GPU constraints target TensorRT-LLM.
    """
    router = InferenceRouter()
    result = await router.chat(
        model="miniCPM5-1B",
        messages=[{"role": "user", "content": "Hello"}],
        hardware="nvidia"
    )
    assert "Mocked response from http://tensorrt:8000/v1/chat/completions" in result["message"]["content"]

@pytest.mark.asyncio
async def test_router_routing_decision_litert_edge() -> None:
    """
    Verifies that edge constraints target LiteRT.
    """
    router = InferenceRouter()
    result = await router.chat(
        model="miniCPM5-1B",
        messages=[{"role": "user", "content": "Hello"}],
        hardware="edge"
    )
    assert "LiteRT Local Runner Executed" in result["message"]["content"]

@pytest.mark.asyncio
async def test_router_graceful_fallback(monkeypatch) -> None:
    """
    Verifies that if a chosen target backend fails (e.g. SGLang offline),
    the router gracefully logs and falls back to Ollama.
    """
    async def mock_broken_httpx_post(self, url: str, json: dict = None, **kwargs) -> MockHttpxResponse:
        return MockHttpxResponse({}, status_code=500)

    monkeypatch.setattr(httpx.AsyncClient, "post", mock_broken_httpx_post)
    
    router = InferenceRouter()
    # Forces routing to SGLang via high context, which fails and triggers Ollama fallback
    result = await router.chat(
        model="miniCPM5-1B",
        messages=[{"role": "user", "content": "Hello"}],
        context_length=40000
    )
    
    assert "Mocked Ollama response" in result["message"]["content"]

# ==========================================
# API endpoint tests
# ==========================================
@pytest.mark.asyncio
async def test_api_chat_route_success() -> None:
    """
    Verifies the FastAPI routing, input validation (Pydantic v2), and output response schema.
    """
    payload = {
        "model": "miniCPM5-1B",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain 32k context size."}
        ],
        "temperature": 0.5,
        "max_tokens": 100
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/inference/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["model"] == "miniCPM5-1B"
    assert data["message"]["role"] == "assistant"
    assert "Mocked Ollama response" in data["message"]["content"]
    assert "total_tokens" in data["usage"]
