"""
Shared pytest fixtures and configuration for NeuralFolk integration tests.
All engine tests use these base fixtures for consistent setup.
"""
import pytest
import os
import sys

# ── Path resolution ────────────────────────────────────────────────────────
# Allow importing from services/control-plane when running pytest from root
_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CP_PATH = os.path.join(_ROOT, "services", "control-plane")
_INFERENCE_PATH = os.path.join(_ROOT, "services")

for p in (_CP_PATH, _INFERENCE_PATH):
    if p not in sys.path:
        sys.path.insert(0, p)

# ── Constants ──────────────────────────────────────────────────────────────
TEST_MODEL = "openbmb/minicpm5:fp16"
CONTROLPLANE_URL = os.getenv("CONTROLPLANE_URL", "http://localhost:8000")

# Engine host resolution — env vars take precedence for CI/CD overrides
OLLAMA_HOST    = os.getenv("OLLAMA_HOST",    "http://localhost:11434")
VLLM_HOST      = os.getenv("VLLM_HOST",      "http://localhost:8001")
SGLANG_HOST    = os.getenv("SGLANG_HOST",    "http://localhost:30000")
LLAMACPP_HOST  = os.getenv("LLAMACPP_HOST",  "http://localhost:8080")
TENSORRT_HOST  = os.getenv("TENSORRT_HOST",  "http://localhost:8002")

# ── Markers ────────────────────────────────────────────────────────────────
def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "integration: live integration test requiring running services")
    config.addinivalue_line("markers", "ollama: requires Ollama inference engine")
    config.addinivalue_line("markers", "vllm: requires vLLM inference engine")
    config.addinivalue_line("markers", "sglang: requires SGLang inference engine")
    config.addinivalue_line("markers", "llamacpp: requires llama.cpp inference server")
    config.addinivalue_line("markers", "tensorrt: requires TensorRT-LLM with NVIDIA GPU")
