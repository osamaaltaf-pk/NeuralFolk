# STACK.md — Neuralfolk Technology Stack
> Every technology choice with the reason why. If you want to change something, update here first and record the decision in MEMORY.md.

---

## Core Services (docker-compose)

| Service | Technology | Version | Purpose |
|---|---|---|---|
| control-plane | FastAPI | 0.115+ | REST API, WebSockets, orchestration |
| worker | Celery | 5.x | Agent task execution, workflow engine |
| database | PostgreSQL | 16 | Persistent storage for workflows, agents, configs |
| cache/broker | Valkey | 7.2+ | Celery broker, cache, event streams (MIT fork of Redis) |
| vector-db | Qdrant | latest | Vector embeddings for semantic memory |
| graph-db | FalkorDB | latest | Knowledge graph memory (Redis-compatible graph API) |
| inference | Ollama | latest | Local LLM inference (phase 1) |
| dashboard | Next.js | 14 | Frontend UI |

---

## Python Dependencies (control-plane + worker)

> Canonical list. Agent uses these exact package names. Do not add packages not listed here
> without a REVIEW.md ARCH_DECISIONS entry.

```toml
# pyproject.toml — shared core
[tool.uv.sources]

[project.dependencies]
# API
fastapi = ">=0.115"
uvicorn = {extras = ["standard"], version = ">=0.30"}
httpx = ">=0.27"

# Data / validation
pydantic = ">=2.7"
pydantic-settings = ">=2.3"

# Database
sqlalchemy = {extras = ["asyncio"], version = ">=2.0"}
asyncpg = ">=0.29"          # postgres async driver
alembic = ">=1.13"

# Cache / events
valkey = {extras = ["asyncio"], version = ">=6.0"}   # NOT redis

# Worker
celery = {extras = ["redis"], version = ">=5.4"}     # 'redis' extra works with valkey
# NOTE: Celery + Pydantic v2: use model.model_dump() not model.dict() in tasks

# Logging
structlog = ">=24.0"

# File I/O (async only)
aiofiles = ">=23.0"

# Vector DB
qdrant-client = {extras = ["fastembed"], version = ">=1.9"}

# Graph DB
falkordb = ">=1.0"          # redis-compatible client

# Inference
ollama = ">=0.3"            # official async client
```

---

## Dashboard Tech Decisions (services/dashboard/)

| Decision | Choice | Reason |
|---|---|---|
| Router | App Router (Next.js 14) | Server components, better streaming support |
| Styling | Tailwind CSS + shadcn/ui | Fastest UI assembly, consistent design tokens |
| State management | Zustand | Lightweight, no boilerplate, works well with streaming |
| WebSocket | Native browser WebSocket | No socket.io overhead; dashboard connects to FastAPI WS endpoint |
| Package manager | npm (single package.json in services/dashboard/) | No monorepo tooling needed until second JS service exists |
| Charts / graphs | Recharts | Works with shadcn, React-native, no canvas setup |

---

| Backend | Use Case | Hardware | Phase |
|---|---|---|---|
| Ollama | Phase 1 dev, easy setup | RTX 2070, any GPU | Phase 1 |
| vLLM | High throughput, batching | NVIDIA GPU | Phase 2 |
| SGLang | Structured output, function calling | NVIDIA GPU | Phase 2 |
| llama.cpp | CPU inference, low VRAM, edge | CPU or any GPU | Phase 2 |
| TensorRT-LLM | Max NVIDIA performance | NVIDIA GPU | Phase 3 |
| LiteRT (Google) | Mobile/edge/Raspberry Pi | ARM, x86 edge | Phase 3 |

**Router logic:**
```python
task_type      → "tool_call"    → local-fast  (qwen2.5:3b, Ollama)
task_type      → "reasoning"    → local-smart (qwen2.5:7b, Ollama)
hardware       → "no_gpu"       → llama.cpp CPU backend
context_length → ">32k"         → SGLang (better long context handling)
batch_size     → ">4 requests"  → vLLM (continuous batching)
```

---

## Models (local only, no API keys)

| Model | Size | VRAM (Q4) | Speed (RTX2070) | Use |
|---|---|---|---|---|
| qwen2.5:3b | 3B | ~2.2GB | 40–55 tok/s | Agent tool calls, fast routing |
| qwen2.5:7b | 7B | ~4.5GB | 20–28 tok/s | Complex reasoning, planning |
| gemma3:1b | 1B | ~0.8GB | 70–90 tok/s | Intent detection, routing only |
| phi3.5-mini | 3.8B | ~2.6GB | 35–50 tok/s | Code generation |
| deepseek-r1:7b | 7B | ~4.5GB | 18–25 tok/s | Chain-of-thought reasoning |

---

## Valkey Streams — Full Event Schema

Every system action emits one of these events. NEVER add an event without documenting it here.

```
# Workflow events
workflow.created        {workflow_id, name, steps_count, created_by}
workflow.started        {workflow_id, triggered_by, model_used}
workflow.step.started   {workflow_id, step_index, step_name, agent_id}
workflow.step.completed {workflow_id, step_index, duration_ms, tokens_used}
workflow.step.failed    {workflow_id, step_index, error, retry_count}
workflow.completed      {workflow_id, total_duration_ms, steps_completed}
workflow.failed         {workflow_id, failed_at_step, error}

# Agent events
agent.spawned           {agent_id, model, task_summary, workflow_id?}
agent.plan.created      {agent_id, steps_planned, model_used}
agent.tool.called       {agent_id, tool_name, input_summary}
agent.tool.completed    {agent_id, tool_name, duration_ms, success}
agent.tool.failed       {agent_id, tool_name, error}
agent.memory.stored     {agent_id, memory_type, key, vector_id?}
agent.memory.recalled   {agent_id, query, results_count, latency_ms}
agent.completed         {agent_id, steps_taken, tokens_used, duration_ms}
agent.failed            {agent_id, step, error, retry_count}

# Inference events
inference.requested     {request_id, model, backend, prompt_tokens}
inference.routing       {request_id, selected_backend, reason}
inference.completed     {request_id, model, tokens_per_sec, total_tokens, latency_ms}
inference.failed        {request_id, model, backend, error}
inference.cache.hit     {request_id, cache_type}

# System events
system.startup          {version, hardware_detected, models_loaded}
system.gpu.utilization  {vram_used_mb, vram_total_mb, utilization_pct}
system.worker.online    {worker_id, capabilities}
system.worker.offline   {worker_id, last_task}
system.health.check     {all_services_ok, details}
```

**Valkey Stream keys:**
```
neuralfolk:events:workflow
neuralfolk:events:agent
neuralfolk:events:inference
neuralfolk:events:system
neuralfolk:events:all        ← fan-out copy of all events (for dashboard)
```

**Event ownership — one service emits each event, no exceptions:**

| Event prefix | Emitting service | Notes |
|---|---|---|
| `workflow.*` | control-plane | Workflow lifecycle is owned by the API layer |
| `agent.*` | worker | Agent loop runs in Celery worker |
| `inference.*` | inference service | Router emits all inference events |
| `system.*` | control-plane | Health/startup owned by orchestrator |

> Rule: if you are in worker and need to record a workflow state change,
> call the control-plane API — do NOT emit `workflow.*` events from worker directly.

---

## Memory System

### Two-layer hybrid memory:

**Layer 1 — Knowledge Graph (FalkorDB)**
- Stores: entities, relationships, facts
- Query: Cypher / graph traversal
- Use: "What did the agent learn about company X?" → traverse entity graph
- Schema:
  ```
  (Agent)-[:EXECUTED]->(Task)
  (Task)-[:USED]->(Tool)
  (Task)-[:PRODUCED]->(Memory)
  (Memory)-[:ABOUT]->(Entity)
  (Entity)-[:RELATED_TO]->(Entity)
  ```

**Layer 2 — Vector Store (Qdrant)**
- Stores: embedded text chunks from agent outputs
- Query: cosine similarity search
- Use: "Find similar past tasks" → vector similarity
- Collections: `workflow_memory`, `user_memory`, `tool_outputs`

**Hybrid recall:**
```python
async def recall(query: str, top_k: int = 5) -> list[Memory]:
    # 1. vector search for semantic similarity
    vector_results = await qdrant.search(query, top_k=top_k*2)
    # 2. graph traversal from top vector results
    entity_ids = extract_entities(vector_results)
    graph_context = await falkordb.traverse(entity_ids, depth=2)
    # 3. merge + rerank
    return rerank(vector_results, graph_context)[:top_k]
```

**TurboVec — embedding compression:**
- Compress 1536-dim embeddings → 256-dim using scalar quantization
- ~6x storage reduction, ~2% recall loss
- Applied before storing in Qdrant

**DeepSeek MLA-style KV cache optimization:**
- Compress KV cache using low-rank decomposition
- Reduces VRAM usage during inference by up to 40%
- Applied in inference layer, transparent to agent code

---

## Skills System (skills.sh inspired)

A skill is a versioned, typed, installable agent capability.

```python
# Every skill follows this interface
class NeuralfolkSkill:
    name: str           # "web_research"
    version: str        # "1.2.0"
    description: str    # used by agent to decide when to use it
    input_schema: dict  # Pydantic schema
    output_schema: dict

    async def execute(self, input: SkillInput) -> SkillOutput: ...
    async def validate(self, input: SkillInput) -> bool: ...
```

Install command: `neuralfolk skill add web-research`
List: `neuralfolk skill list`
Community registry: `skills/registry.json` (local) → `neuralfolk.dev/skills` (cloud)

---

## Deployment Configurator

The dashboard `/deploy` page lets users configure and generate deployment YAMLs.

**Input parameters (UI form):**
- Provider: local / hetzner / runpod / vastai / aws
- Hardware: CPU-only / GPU model / RAM size
- Models: select from supported list
- Inference backend: ollama / vllm / sglang / llamacpp / tensorrt / litert
- KV technique: standard / MLA-compressed / sliding-window
- Vector DB: qdrant-local / qdrant-cloud / pgvector
- Graph DB: falkordb / neo4j / none
- Event system: valkey-streams / nats-jetstream
- Observability: none / prometheus+grafana / opentelemetry

**Output:**
- `docker-compose.generated.yml` — download + run
- `neuralfolk.config.yaml` — platform config
- Shell command: `neuralfolk deploy --config neuralfolk.config.yaml`

**Recommender logic:**
```python
if hardware.vram_gb < 8:    recommend_backend("llamacpp")
if hardware.vram_gb >= 8:   recommend_backend("ollama")
if hardware.vram_gb >= 16:  recommend_backend("vllm")
if hardware.gpu == "nvidia": recommend_backend("tensorrt")
if hardware.cpu_only:        recommend_backend("llamacpp")
if hardware.is_edge:         recommend_backend("litert")
```

---

## TurboQuant Layer

Sits between model weights and inference backend. Automatically selects best quantization:

| Quant Method | Use Case | Tool |
|---|---|---|
| GGUF Q4_K_M | Best quality/size balance for llama.cpp | llama.cpp |
| GGUF Q2_K | Minimum VRAM, acceptable quality | llama.cpp |
| AWQ | Fast GPU inference, low VRAM | vLLM, TGI |
| GPTQ | Alternative GPU quant | vLLM, AutoGPTQ |
| INT8 | TensorRT optimization | TensorRT-LLM |
| INT4 | Edge/mobile deployment | LiteRT |

Auto-selector:
```python
def select_quant(vram_gb: float, backend: str) -> QuantMethod:
    if backend == "llamacpp":
        return "Q4_K_M" if vram_gb >= 6 else "Q2_K"
    if backend in ("vllm", "sglang"):
        return "AWQ" if vram_gb < 12 else "none"
    if backend == "tensorrt":
        return "INT8"
    if backend == "litert":
        return "INT4"
```
