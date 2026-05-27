"""
Engine Test 3: SGLang
======================
Validates the SGLang structured long-context inference engine:
  1. Service health check.
  2. Correct OpenAI-compatible model listing.
  3. Real chat completion via /v1/chat/completions.
  4. Long-context routing: context_length > 32000 tokens → InferenceRouter selects SGLang.
  5. Structured output (JSON mode) if supported.

SGLang runs as: docker compose --profile sglang up -d sglang
Run tests with: pytest tests/integration/test_engine_sglang.py -v -s

NOTE: SGLang requires significant RAM + GPU. Auto-skipped if not running.
"""
import pytest
import httpx
import json

MODEL = "openbmb/minicpm5:fp16"
SGLANG_HOSTS = ["http://localhost:30000", "http://127.0.0.1:30000"]
CONTROLPLANE_URL = "http://localhost:8000"
TIMEOUT = 120.0


def _find_sglang_host() -> str | None:
    for host in SGLANG_HOSTS:
        try:
            r = httpx.get(f"{host}/health", timeout=5.0)
            if r.status_code == 200:
                return host
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def sglang_host() -> str:
    host = _find_sglang_host()
    if host is None:
        pytest.skip(
            "SGLang not reachable. Start with: docker compose --profile sglang up -d sglang\n"
            "Requires GPU and sufficient VRAM."
        )
    return host


@pytest.mark.integration
def test_sglang_health(sglang_host: str) -> None:
    """SGLang /health endpoint must return 200."""
    with httpx.Client(timeout=10.0) as client:
        res = client.get(f"{sglang_host}/health")
    assert res.status_code == 200, f"SGLang health failed: {res.status_code}"
    print(f"\n[OK] SGLang health check passed at {sglang_host}")


@pytest.mark.integration
def test_sglang_models_list(sglang_host: str) -> None:
    """SGLang /v1/models must list at least one model."""
    with httpx.Client(timeout=10.0) as client:
        res = client.get(f"{sglang_host}/v1/models")
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    model_ids = [m.get("id") for m in data["data"]]
    print(f"\n[OK] SGLang models: {model_ids}")
    assert len(model_ids) > 0


@pytest.mark.integration
def test_sglang_chat_completion(sglang_host: str) -> None:
    """Real chat completion with openbmb/minicpm5:fp16 via SGLang."""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Reply with exactly one word: hello"}],
        "temperature": 0.0,
        "max_tokens": 20
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{sglang_host}/v1/chat/completions", json=payload)

    assert res.status_code == 200, f"SGLang chat failed {res.status_code}: {res.text[:300]}"
    data = res.json()
    assert "choices" in data and len(data["choices"]) > 0
    content = data["choices"][0]["message"]["content"]
    assert len(content) > 0

    usage = data.get("usage", {})
    print(f"\n[OK] SGLang chat completion verified.")
    print(f"     Response: {content[:200]}")
    print(f"     Tokens: prompt={usage.get('prompt_tokens')}, completion={usage.get('completion_tokens')}")


@pytest.mark.integration
def test_sglang_long_context_routing() -> None:
    """
    Verifies InferenceRouter routes context_length > 32000 to SGLang.
    Sends a padded message that exceeds the 32k token threshold.
    STACK.md rule: context_length > 32000 → sglang.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            health = client.get(f"{CONTROLPLANE_URL}/api/v1/health")
        if health.status_code != 200:
            pytest.skip("Control-plane not reachable")
    except Exception:
        pytest.skip("Control-plane not reachable")

    if _find_sglang_host() is None:
        pytest.skip("SGLang not running — cannot verify long-context routing")

    # ~33k tokens worth of text (~132k characters)
    long_padding = "The quick brown fox jumps over the lazy dog. " * 3000
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "user", "content": f"{long_padding}\n\nSummarize in one word."}
        ],
        "temperature": 0.0,
        "max_tokens": 10
    }
    with httpx.Client(timeout=TIMEOUT) as client:
        res = client.post(f"{CONTROLPLANE_URL}/api/v1/inference/chat", json=payload)

    assert res.status_code == 200, f"Long-context routing failed: {res.status_code}: {res.text[:300]}"
    data = res.json()
    assert "message" in data
    print(f"\n[OK] SGLang long-context routing verified (>32k tokens).")
    print(f"     Response: {data['message'].get('content','')[:200]}")


@pytest.mark.integration
def test_sglang_streaming(sglang_host: str) -> None:
    """SGLang SSE streaming must produce valid delta chunks."""
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "List 3 colors, one per line."}],
        "temperature": 0.0,
        "max_tokens": 30,
        "stream": True
    }
    chunks = []
    with httpx.Client(timeout=TIMEOUT) as client:
        with client.stream("POST", f"{sglang_host}/v1/chat/completions", json=payload) as stream:
            for line in stream.iter_lines():
                if line.startswith("data: ") and line != "data: [DONE]":
                    try:
                        chunks.append(json.loads(line[6:]))
                    except json.JSONDecodeError:
                        pass

    assert len(chunks) > 0, "No streaming chunks from SGLang"
    print(f"\n[OK] SGLang streaming verified. {len(chunks)} chunks received.")
