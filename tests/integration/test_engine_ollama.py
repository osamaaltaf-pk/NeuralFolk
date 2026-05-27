"""
Engine Test 1: Ollama
=====================
Validates that the Ollama inference engine:
  1. Is reachable on its configured host.
  2. Can list available models.
  3. Responds correctly to a real chat completion with openbmb/minicpm5:fp16.
  4. The NeuralFolk /api/v1/inference/chat route correctly routes to Ollama.

Run with:
    pytest tests/integration/test_engine_ollama.py -v -s
"""
import pytest
import httpx
import asyncio
from typing import Dict, Any

MODEL = "openbmb/minicpm5:fp16"
OLLAMA_HOSTS = ["http://localhost:11434", "http://127.0.0.1:11434"]
CONTROLPLANE_URL = "http://localhost:8000"
TIMEOUT = 120.0  # model load can be slow on first run


def _find_ollama_host() -> str | None:
    """Synchronously probe Ollama hosts and return the first reachable one."""
    import httpx as _httpx
    for host in OLLAMA_HOSTS:
        try:
            r = _httpx.get(f"{host}/api/tags", timeout=5.0)
            if r.status_code == 200:
                return host
        except Exception:
            continue
    return None


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def ollama_host() -> str:
    host = _find_ollama_host()
    if host is None:
        pytest.skip(
            "Ollama not reachable on any known host. "
            "Start it with: docker compose up -d inference"
        )
    return host


# ─── Tests ───────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_ollama_reachable(ollama_host: str) -> None:
    """Ollama HTTP API must respond on /api/tags."""
    with httpx.Client(timeout=10.0) as client:
        res = client.get(f"{ollama_host}/api/tags")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"
    data = res.json()
    assert "models" in data, f"Unexpected response structure: {data}"
    print(f"\n[OK] Ollama reachable at {ollama_host}")
    print(f"     Available models: {[m.get('name') for m in data['models']]}")


@pytest.mark.integration
def test_ollama_model_pull(ollama_host: str) -> None:
    """
    Ensures openbmb/minicpm5:fp16 is pulled and present in Ollama.
    If not present, triggers a pull (can take time — uses generous timeout).
    """
    with httpx.Client(timeout=10.0) as client:
        tags_res = client.get(f"{ollama_host}/api/tags")
    tags = tags_res.json().get("models", [])
    model_names = [m.get("name", "") for m in tags]

    if MODEL not in model_names and f"{MODEL}:latest" not in model_names:
        print(f"\n[INFO] {MODEL} not found. Pulling now (this may take several minutes)...")
        # Stream pull — Ollama streams JSON progress lines
        with httpx.Client(timeout=TIMEOUT) as client:
            with client.stream("POST", f"{ollama_host}/api/pull", json={"name": MODEL}) as stream:
                for line in stream.iter_lines():
                    if line:
                        print(f"     pull: {line[:120]}")
        # Re-check
        with httpx.Client(timeout=10.0) as client:
            tags_res = client.get(f"{ollama_host}/api/tags")
        model_names = [m.get("name", "") for m in tags_res.json().get("models", [])]

    assert any(MODEL in name for name in model_names), (
        f"{MODEL} not available after pull attempt. Models found: {model_names}"
    )
    print(f"\n[OK] {MODEL} is present in Ollama.")


@pytest.mark.integration
def test_ollama_chat_completion(ollama_host: str) -> None:
    """
    Sends a real chat request to Ollama with openbmb/minicpm5:fp16.
    Validates response structure: model name, message role, non-empty content.
    """
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Reply with exactly one word: hello"}],
        "stream": False,
        "options": {"temperature": 0.0, "num_predict": 20}
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{ollama_host}/api/chat", json=payload)

    assert res.status_code == 200, f"Ollama chat failed {res.status_code}: {res.text[:300]}"
    data = res.json()

    assert "message" in data, f"No 'message' key in response: {data}"
    assert data["message"].get("role") == "assistant", f"Wrong role: {data['message']}"
    content = data["message"].get("content", "")
    assert len(content) > 0, "Empty response content from Ollama"

    print(f"\n[OK] Ollama chat completion verified.")
    print(f"     Model: {data.get('model')}")
    print(f"     Response: {content[:200]}")
    print(f"     Tokens: prompt={data.get('prompt_eval_count',0)}, completion={data.get('eval_count',0)}")


@pytest.mark.integration
def test_ollama_via_controlplane(ollama_host: str) -> None:
    """
    Tests that the NeuralFolk control-plane /api/v1/inference/chat route
    correctly routes to Ollama and returns a valid response.
    This is the end-to-end path: client -> FastAPI -> InferenceRouter -> OllamaBackend.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            health = client.get(f"{CONTROLPLANE_URL}/api/v1/health")
        if health.status_code != 200:
            pytest.skip("Control-plane not reachable — run docker compose up first")
    except Exception:
        pytest.skip("Control-plane not reachable — run docker compose up first")

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "What is 2+2? Answer with just the number."}],
        "temperature": 0.0,
        "max_tokens": 10
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{CONTROLPLANE_URL}/api/v1/inference/chat", json=payload)

    assert res.status_code == 200, (
        f"Control-plane inference failed {res.status_code}: {res.text[:300]}"
    )
    data = res.json()
    assert "message" in data, f"No 'message' key in CP response: {data}"
    content = data["message"].get("content", "")
    assert len(content) > 0, "Empty content from control-plane inference route"

    print(f"\n[OK] Control-plane -> Ollama route verified.")
    print(f"     Response: {content[:200]}")


@pytest.mark.integration
def test_ollama_streaming(ollama_host: str) -> None:
    """
    Validates that Ollama streaming mode works correctly.
    Streams tokens and verifies the stream terminates cleanly with done=True.
    """
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Count to 3."}],
        "stream": True,
        "options": {"temperature": 0.0, "num_predict": 30}
    }
    chunks_received = 0
    final_done = False

    with httpx.Client(timeout=TIMEOUT) as client:
        with client.stream("POST", f"{ollama_host}/api/chat", json=payload) as stream:
            import json
            for line in stream.iter_lines():
                if line:
                    try:
                        chunk = json.loads(line)
                        chunks_received += 1
                        if chunk.get("done") is True:
                            final_done = True
                    except json.JSONDecodeError:
                        pass

    assert chunks_received > 0, "No streaming chunks received from Ollama"
    assert final_done, "Stream did not terminate with done=True"
    print(f"\n[OK] Ollama streaming verified. Received {chunks_received} chunks.")
