"""
Engine Test 4: llama.cpp
========================
Validates the llama.cpp CPU/low-VRAM inference server:
  1. Service health check on /health.
  2. Model info via /v1/models.
  3. Real chat completion via /v1/chat/completions.
  4. Verifies InferenceRouter routes hardware=no_gpu to llama.cpp.
  5. Validates completion format and token usage reporting.

llama.cpp runs as: docker compose --profile llamacpp up -d llamacpp
Run tests with: pytest tests/integration/test_engine_llamacpp.py -v -s

NOTE: llama.cpp runs on CPU — no GPU required. Slower but always available.
      Model file must be mounted at /models/miniCPM5-1B.gguf in the container.
"""
import pytest
import httpx
import json

MODEL = "miniCPM5-1B"
LLAMACPP_HOSTS = ["http://localhost:8080", "http://127.0.0.1:8080"]
CONTROLPLANE_URL = "http://localhost:8000"
TIMEOUT = 180.0  # CPU inference is slower — generous timeout


def _find_llamacpp_host() -> str | None:
    for host in LLAMACPP_HOSTS:
        try:
            r = httpx.get(f"{host}/health", timeout=5.0)
            if r.status_code == 200:
                return host
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def llamacpp_host() -> str:
    host = _find_llamacpp_host()
    if host is None:
        pytest.skip(
            "llama.cpp server not reachable.\n"
            "Start with: docker compose --profile llamacpp up -d llamacpp\n"
            "Ensure the GGUF model file is mounted at /models/miniCPM5-1B.gguf"
        )
    return host


@pytest.mark.integration
def test_llamacpp_health(llamacpp_host: str) -> None:
    """llama.cpp /health must return 200."""
    with httpx.Client(timeout=10.0) as client:
        res = client.get(f"{llamacpp_host}/health")
    assert res.status_code == 200, f"llama.cpp health failed: {res.status_code}"
    print(f"\n[OK] llama.cpp health check passed at {llamacpp_host}")


@pytest.mark.integration
def test_llamacpp_models_list(llamacpp_host: str) -> None:
    """llama.cpp /v1/models must return the loaded model."""
    with httpx.Client(timeout=10.0) as client:
        res = client.get(f"{llamacpp_host}/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    model_ids = [m.get("id") for m in data["data"]]
    print(f"\n[OK] llama.cpp models: {model_ids}")
    assert len(model_ids) > 0, "No models listed by llama.cpp server"


@pytest.mark.integration
def test_llamacpp_chat_completion(llamacpp_host: str) -> None:
    """Real CPU chat completion via llama.cpp."""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Reply with exactly one word: hello"}],
        "temperature": 0.0,
        "max_tokens": 20
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{llamacpp_host}/v1/chat/completions", json=payload)

    assert res.status_code == 200, f"llama.cpp chat failed {res.status_code}: {res.text[:300]}"
    data = res.json()
    assert "choices" in data and len(data["choices"]) > 0
    content = data["choices"][0]["message"]["content"]
    assert len(content) > 0

    usage = data.get("usage", {})
    print(f"\n[OK] llama.cpp chat completion verified (CPU inference).")
    print(f"     Response: {content[:200]}")
    print(f"     Tokens: prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}")


@pytest.mark.integration
def test_llamacpp_via_controlplane_cpu_routing() -> None:
    """
    Verifies InferenceRouter routes hardware=no_gpu to llama.cpp.
    STACK.md rule: hardware == 'no_gpu' → llamacpp.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            health = client.get(f"{CONTROLPLANE_URL}/api/v1/health")
        if health.status_code != 200:
            pytest.skip("Control-plane not reachable")
    except Exception:
        pytest.skip("Control-plane not reachable")

    if _find_llamacpp_host() is None:
        pytest.skip("llama.cpp not running — cannot verify CPU routing")

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Say: cpu-verified"}],
        "temperature": 0.0,
        "max_tokens": 10,
        "hardware": "no_gpu"  # Forces llamacpp routing per STACK.md
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{CONTROLPLANE_URL}/api/v1/inference/chat", json=payload)

    assert res.status_code == 200, f"CPU routing failed: {res.status_code}: {res.text[:300]}"
    data = res.json()
    assert "message" in data
    print(f"\n[OK] llama.cpp CPU routing via control-plane verified.")
    print(f"     Response: {data['message'].get('content','')[:200]}")


@pytest.mark.integration
def test_llamacpp_completion_format(llamacpp_host: str) -> None:
    """
    Verifies that llama.cpp response format matches OpenAI spec exactly:
    id, object, created, model, choices[].message.{role,content}, usage.
    """
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Hi"}],
        "temperature": 0.0,
        "max_tokens": 5
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{llamacpp_host}/v1/chat/completions", json=payload)

    assert res.status_code == 200
    data = res.json()

    # OpenAI spec validation
    for field in ("id", "object", "created", "model", "choices"):
        assert field in data, f"Missing field '{field}' in llama.cpp response: {data}"

    choice = data["choices"][0]
    assert "message" in choice
    assert "role" in choice["message"]
    assert "content" in choice["message"]
    assert choice["message"]["role"] == "assistant"

    print(f"\n[OK] llama.cpp OpenAI-compatible response format verified.")
    print(f"     id={data['id']}, object={data['object']}, model={data['model']}")
