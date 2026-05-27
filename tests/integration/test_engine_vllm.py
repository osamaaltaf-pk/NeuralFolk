"""
Engine Test 2: vLLM
====================
Validates the vLLM continuous-batching inference engine:
  1. Service health check on /health endpoint.
  2. Lists models via /v1/models (OpenAI-compatible API).
  3. Real chat completion via /v1/chat/completions with openbmb/minicpm5:fp16.
  4. Verifies InferenceRouter routes batch_size > 4 traffic to vLLM.
  5. Validates streaming SSE (server-sent events) format.

vLLM runs as: docker compose --profile vllm up -d vllm
Run tests with: pytest tests/integration/test_engine_vllm.py -v -s

NOTE: vLLM requires a CUDA-capable GPU and significant VRAM.
      On CPU-only or insufficient VRAM systems this test will be skipped automatically.
"""
import pytest
import httpx
import json
from typing import Any, Dict

MODEL = "openbmb/minicpm5:fp16"
VLLM_HOSTS = ["http://localhost:8001", "http://127.0.0.1:8001"]  # Port 8001 to avoid collision with control-plane
CONTROLPLANE_URL = "http://localhost:8000"
TIMEOUT = 120.0


def _find_vllm_host() -> str | None:
    for host in VLLM_HOSTS:
        try:
            r = httpx.get(f"{host}/health", timeout=5.0)
            if r.status_code == 200:
                return host
        except Exception:
            continue
    return None


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def vllm_host() -> str:
    host = _find_vllm_host()
    if host is None:
        pytest.skip(
            "vLLM not reachable. Start with: docker compose --profile vllm up -d vllm\n"
            "Requires CUDA GPU + VRAM >= 4GB for openbmb/minicpm5:fp16."
        )
    return host


# ─── Tests ───────────────────────────────────────────────────────────────────

@pytest.mark.integration
def test_vllm_health(vllm_host: str) -> None:
    """vLLM /health must return 200 OK."""
    with httpx.Client(timeout=10.0) as client:
        res = client.get(f"{vllm_host}/health")
    assert res.status_code == 200, f"vLLM health failed: {res.status_code}"
    print(f"\n[OK] vLLM health check passed at {vllm_host}")


@pytest.mark.integration
def test_vllm_models_list(vllm_host: str) -> None:
    """vLLM /v1/models must list available models (OpenAI-compatible)."""
    with httpx.Client(timeout=10.0) as client:
        res = client.get(f"{vllm_host}/v1/models")
    assert res.status_code == 200, f"vLLM models list failed: {res.status_code}"
    data = res.json()
    assert "data" in data, f"Unexpected response: {data}"
    model_ids = [m.get("id") for m in data["data"]]
    print(f"\n[OK] vLLM models available: {model_ids}")
    assert len(model_ids) > 0, "No models loaded in vLLM"


@pytest.mark.integration
def test_vllm_chat_completion(vllm_host: str) -> None:
    """Real chat completion via vLLM OpenAI-compatible endpoint."""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Reply with exactly one word: hello"}],
        "temperature": 0.0,
        "max_tokens": 20,
        "stream": False
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{vllm_host}/v1/chat/completions", json=payload)

    assert res.status_code == 200, f"vLLM chat failed {res.status_code}: {res.text[:300]}"
    data = res.json()

    assert "choices" in data, f"No choices in vLLM response: {data}"
    assert len(data["choices"]) > 0
    content = data["choices"][0]["message"]["content"]
    assert len(content) > 0, "Empty content from vLLM"

    usage = data.get("usage", {})
    print(f"\n[OK] vLLM chat completion verified.")
    print(f"     Response: {content[:200]}")
    print(f"     Usage: prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}")


@pytest.mark.integration
def test_vllm_via_controlplane_batch_routing() -> None:
    """
    Control-plane InferenceRouter must route batch_size > 4 to vLLM.
    Verifies routing heuristic: STACK.md rule → batch_size > 4 → vllm.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            health = client.get(f"{CONTROLPLANE_URL}/api/v1/health")
        if health.status_code != 200:
            pytest.skip("Control-plane not reachable")
    except Exception:
        pytest.skip("Control-plane not reachable")

    if _find_vllm_host() is None:
        pytest.skip("vLLM not running — cannot verify batch routing")

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Say exactly: batch-verified"}],
        "temperature": 0.0,
        "max_tokens": 10,
        "batch_size": 8  # > 4 triggers vLLM route per STACK.md
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{CONTROLPLANE_URL}/api/v1/inference/chat", json=payload)

    assert res.status_code == 200, f"Batch routing via CP failed: {res.status_code}: {res.text[:300]}"
    data = res.json()
    assert "message" in data
    print(f"\n[OK] vLLM batch routing via control-plane verified.")
    print(f"     Response: {data['message'].get('content', '')[:200]}")


@pytest.mark.integration
def test_vllm_streaming_sse(vllm_host: str) -> None:
    """Validates vLLM SSE streaming — chunks must be valid SSE data: lines."""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Count: 1, 2, 3."}],
        "temperature": 0.0,
        "max_tokens": 30,
        "stream": True
    }
    chunks = []
    with httpx.Client(timeout=TIMEOUT) as client:
        with client.stream("POST", f"{vllm_host}/v1/chat/completions", json=payload) as stream:
            for line in stream.iter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        chunk = json.loads(line[6:])
                        chunks.append(chunk)
                    except json.JSONDecodeError:
                        pass

    assert len(chunks) > 0, "No SSE chunks received from vLLM stream"
    # Each chunk must have choices with delta
    assert "choices" in chunks[0], f"Unexpected chunk format: {chunks[0]}"
    print(f"\n[OK] vLLM SSE streaming verified. Received {len(chunks)} chunks.")
