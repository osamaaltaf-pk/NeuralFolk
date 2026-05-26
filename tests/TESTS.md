# NeuralFolk Test Ledger (TESTS.md)
> This is a living document tracking all test suites, verification commands, and execution history.
> MANDATE: Every new feature, stack update, or bug fix MUST have corresponding test.py files and an entry in this file before advancing to the next step.

---

## Testing Guidelines

1. **Test-First Development**: Before writing complex feature logic, outline the target behaviors in a `test_*.py` file under `tests/`.
2. **Accuracy Verification**: No task is marked "completed" in `CONTEXT.md` or `MEMORY.md` until its tests are written, executed, and confirmed green.
3. **No Placeholders**: Never write dummy tests. Every test must perform genuine logic verification (e.g. validating payload structures, connections, logic bounds).

---

## Active Test Suites

| Component | Test File | Scope / Purpose | Status |
|---|---|---|---|
| control-plane | [test_connections.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/unit/test_connections.py) | Verifies Pydantic settings loading and database/Valkey lazy connection generators. | 🟢 Passing |
| control-plane | [test_health_api.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/unit/test_health_api.py) | Verifies FastAPI health route response structure using mock dependencies overrides. | 🟢 Passing |
| control-plane | [test_live_connections.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/integration/test_live_connections.py) | Integration check making live database/broker connections, skipping if offline. | 🟡 Skipped |
| inference | [test_inference.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/unit/test_inference.py) | Unit tests for InferenceRouter routing heuristics with miniCPM5-1B. | 🟢 Passing |
| agent | [test_agent_flow.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/unit/test_agent_flow.py) | Unit tests for ReactiveAgent loop, tool calls, and event emission. | 🟢 Passing |
| all stacks | [test_live_inference.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/integration/test_live_inference.py) | Probes all 5 engines sequentially, logs OK/SKIP per engine. No assertions — diagnostic. | 🟡 Live |
| **Ollama engine** | [test_engine_ollama.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/integration/test_engine_ollama.py) | Full Ollama validation: reachable → pull miniCPM5-1B → chat → CP route → streaming. | ⏳ Pending Ollama pull |
| **vLLM engine** | [test_engine_vllm.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/integration/test_engine_vllm.py) | vLLM: health → models → chat → batch routing via CP → SSE streaming. | ⏳ Requires `--profile vllm` |
| **SGLang engine** | [test_engine_sglang.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/integration/test_engine_sglang.py) | SGLang: health → models → chat → long-context (>32k) routing → streaming. | ⏳ Requires `--profile sglang` |
| **llama.cpp engine** | [test_engine_llamacpp.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/integration/test_engine_llamacpp.py) | llama.cpp: health → models → CPU chat → no_gpu routing via CP → format validation. | ⏳ Requires `--profile llamacpp` + GGUF |
| **TensorRT-LLM** | [test_engine_tensorrt.py](file:///c:/Users/Microsoft/Downloads/NeuralFolk/tests/integration/test_engine_tensorrt.py) | TensorRT: health → models → GPU chat → nvidia routing via CP → throughput stats. | ⏳ Requires `--profile tensorrt` + TRT engine |

---

## Test Execution Reference

```bash
# Run all tests
pytest tests/

# Run unit tests only (no live services needed)
pytest tests/unit/ -v

# Run Ollama engine test (requires: docker compose up -d inference)
pytest tests/integration/test_engine_ollama.py -v -s

# Run vLLM engine test (requires: docker compose -f docker-compose.yml -f docker-compose.engines.yml --profile vllm up -d vllm)
pytest tests/integration/test_engine_vllm.py -v -s

# Run SGLang engine test
pytest tests/integration/test_engine_sglang.py -v -s

# Run llama.cpp engine test (requires GGUF model at ./models/miniCPM5-1B.gguf)
pytest tests/integration/test_engine_llamacpp.py -v -s

# Run TensorRT engine test (requires pre-compiled TRT engine)
pytest tests/integration/test_engine_tensorrt.py -v -s

# Run all engine tests at once (skips unavailable engines automatically)
pytest tests/integration/ -v -s -m integration

# Run only connection tests
pytest tests/unit/test_connections.py -v
```

---

## Engine Test What-Is-Verified

| Engine | Port | Routing Trigger | Test Coverage |
|--------|------|----------------|---------------|
| Ollama | 11434 | default fallback | reachable, pull, chat, CP route, streaming |
| vLLM | 8001 | batch_size > 4 | health, models, chat, batch routing, SSE |
| SGLang | 30000 | context_length > 32000 | health, models, chat, long-ctx routing, stream |
| llama.cpp | 8080 | hardware=no_gpu | health, models, CPU chat, no_gpu routing, format |
| TensorRT | 8002 | hardware=nvidia | health, models, GPU chat, nvidia routing, throughput |

---

## Test Execution History Log

| Date | Session | Commits Verified | Result | Notes |
|---|---|---|---|---|
| 2026-05-26 | 2 | `b807baf`, `db0217b` | 🟢 3/3 passed | Initial connection suite verifying database and Valkey client code. |
| 2026-05-26 | 2 | `127c761`, `2b915c1` | 🟢 4/4 passed / 2 skipped | Added health route unit checks and connection integration tests. |
| 2026-05-26 | 2 | `67f03ea` | 🟢 6/6 passed | Resolved HTTPX AsyncClient deprecation, resolved falkordb host port collision, and verified live database integration connections. |
| 2026-05-26 | 5 | `ccd6a4d` | 🟢 All containers healthy | Docker health regression fixes — all 7 services verified via docker ps. |
| 2026-05-26 | 6 | `aadcfb4` | ⏳ In progress | Per-engine test suites created. Ollama image downloading. Engine profiles added to docker-compose.engines.yml. |
