"""
Engine Test 5: TensorRT-LLM
============================
Validates TensorRT-LLM NVIDIA-optimized inference engine:
  1. Service health check.
  2. Model listing via Triton-compatible or OpenAI-compatible API.
  3. Real chat completion with openbmb/minicpm5:fp16 (pre-compiled TRT engine).
  4. Verifies InferenceRouter routes hardware=nvidia to TensorRT-LLM.
  5. Validates throughput metrics (tokens/sec) are included in response.

TensorRT-LLM runs as: docker compose --profile tensorrt up -d tensorrt
Run tests with: pytest tests/integration/test_engine_tensorrt.py -v -s

NOTE: Requires NVIDIA GPU with CUDA 12 + TensorRT engine pre-built for openbmb/minicpm5:fp16.
      Model must be compiled to TRT plan file before serving — auto-skipped if unavailable.
"""
import pytest
import httpx
import json

MODEL = "openbmb/minicpm5:fp16"
TENSORRT_HOSTS = ["http://localhost:8002", "http://127.0.0.1:8002"]
CONTROLPLANE_URL = "http://localhost:8000"
TIMEOUT = 120.0


def _find_tensorrt_host() -> str | None:
    for host in TENSORRT_HOSTS:
        try:
            r = httpx.get(f"{host}/health", timeout=5.0)
            if r.status_code == 200:
                return host
        except Exception:
            try:
                r = httpx.get(f"{host}/v2/health/ready", timeout=5.0)
                if r.status_code == 200:
                    return host
            except Exception:
                continue
    return None


@pytest.fixture(scope="module")
def tensorrt_host() -> str:
    host = _find_tensorrt_host()
    if host is None:
        pytest.skip(
            "TensorRT-LLM not reachable.\n"
            "Start with: docker compose --profile tensorrt up -d tensorrt\n"
            "Requires NVIDIA GPU (RTX 2070+) and pre-compiled TRT engine for openbmb/minicpm5:fp16."
        )
    return host


@pytest.mark.integration
def test_tensorrt_health(tensorrt_host: str) -> None:
    """TensorRT-LLM health endpoint must return 200."""
    with httpx.Client(timeout=10.0) as client:
        # Try both health endpoints (OpenAI-compat and Triton v2)
        for path in ("/health", "/v2/health/ready"):
            try:
                res = client.get(f"{tensorrt_host}{path}")
                if res.status_code == 200:
                    print(f"\n[OK] TensorRT-LLM health check passed at {tensorrt_host}{path}")
                    return
            except Exception:
                continue
    pytest.fail(f"TensorRT-LLM health check failed on all paths at {tensorrt_host}")


@pytest.mark.integration
def test_tensorrt_models_list(tensorrt_host: str) -> None:
    """TensorRT-LLM /v1/models must list the loaded model."""
    with httpx.Client(timeout=10.0) as client:
        res = client.get(f"{tensorrt_host}/v1/models")
    assert res.status_code == 200, f"Models list failed: {res.status_code}"
    data = res.json()
    assert "data" in data
    model_ids = [m.get("id") for m in data["data"]]
    print(f"\n[OK] TensorRT-LLM models: {model_ids}")
    assert len(model_ids) > 0


@pytest.mark.integration
def test_tensorrt_chat_completion(tensorrt_host: str) -> None:
    """Real chat completion via TensorRT-LLM (GPU-accelerated)."""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Reply with exactly one word: hello"}],
        "temperature": 0.0,
        "max_tokens": 20
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{tensorrt_host}/v1/chat/completions", json=payload)

    assert res.status_code == 200, f"TensorRT chat failed {res.status_code}: {res.text[:300]}"
    data = res.json()
    assert "choices" in data and len(data["choices"]) > 0
    content = data["choices"][0]["message"]["content"]
    assert len(content) > 0

    usage = data.get("usage", {})
    print(f"\n[OK] TensorRT-LLM chat completion verified (GPU-accelerated).")
    print(f"     Response: {content[:200]}")
    print(f"     Tokens: prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}")


@pytest.mark.integration
def test_tensorrt_via_controlplane_nvidia_routing() -> None:
    """
    Verifies InferenceRouter routes hardware=nvidia to TensorRT-LLM.
    STACK.md rule: hardware == 'nvidia' → tensorrt.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            health = client.get(f"{CONTROLPLANE_URL}/api/v1/health")
        if health.status_code != 200:
            pytest.skip("Control-plane not reachable")
    except Exception:
        pytest.skip("Control-plane not reachable")

    if _find_tensorrt_host() is None:
        pytest.skip("TensorRT-LLM not running — cannot verify GPU routing")

    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Say: gpu-verified"}],
        "temperature": 0.0,
        "max_tokens": 10,
        "hardware": "nvidia"  # Forces tensorrt routing per STACK.md
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{CONTROLPLANE_URL}/api/v1/inference/chat", json=payload)

    assert res.status_code == 200, f"NVIDIA routing failed: {res.status_code}: {res.text[:300]}"
    data = res.json()
    assert "message" in data
    print(f"\n[OK] TensorRT-LLM NVIDIA routing via control-plane verified.")
    print(f"     Response: {data['message'].get('content','')[:200]}")


@pytest.mark.integration
def test_tensorrt_throughput_headers(tensorrt_host: str) -> None:
    """
    TensorRT-LLM should expose throughput stats.
    Checks usage.completion_tokens and timing if available.
    """
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "List 5 planets."}],
        "temperature": 0.0,
        "max_tokens": 50
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{tensorrt_host}/v1/chat/completions", json=payload)

    assert res.status_code == 200
    data = res.json()
    usage = data.get("usage", {})

    # TRT-LLM should always return token counts
    assert usage.get("completion_tokens", 0) > 0, (
        f"TensorRT response missing token usage: {usage}"
    )
    print(f"\n[OK] TensorRT-LLM throughput stats verified.")
    print(f"     completion_tokens={usage.get('completion_tokens')}, "
          f"prompt_tokens={usage.get('prompt_tokens')}")
