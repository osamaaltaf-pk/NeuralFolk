## Last Updated
<!-- AGENT: update this timestamp every session -->
DATE: not started yet
SESSION: 0

---

## What Has Been Built
<!-- AGENT: tick boxes and add notes as features are completed -->

### Phase 1 — Local Foundation
- [ ] Repo initialized with structure from AGENT.md
- [ ] docker-compose.yml (postgres, valkey, qdrant, control-plane, worker, dashboard)
- [ ] .env.example with all variables documented
- [ ] Makefile with dev commands
- [ ] FastAPI skeleton with /health endpoint
- [ ] Postgres connected (async SQLAlchemy)
- [ ] Valkey connected (aioredis pointing to Valkey)
- [ ] Pydantic settings (core/config.py)
- [ ] InferenceRouter skeleton
- [ ] Ollama backend connected
- [ ] qwen2.5:3b responding via /api/inference/chat
- [ ] qwen2.5:7b responding via /api/inference/chat
- [ ] Event publisher (events.py) — XADD to Valkey streams
- [ ] Basic agent loop (plan → execute → result)
- [ ] Filesystem tool
- [ ] Web search tool (DuckDuckGo)
- [ ] /api/agents/spawn endpoint
- [ ] Celery worker connected
- [ ] Next.js dashboard scaffold
- [ ] Dashboard: system overview page
- [ ] Dashboard: live event stream (WebSocket → Valkey XREAD)
- [ ] Dashboard: workflow trigger UI
- [ ] ngrok tunnel working
- [ ] README.md written with architecture diagram

### Phase 2 — Kafka+ (Valkey Streams upgrade)
- [ ] Full Valkey Streams event schema (all events from STACK.md)
- [ ] Dashboard: live event timeline viewer
- [ ] Multi-agent orchestrator (parallel + pipeline strategies)
- [ ] Qdrant vector memory connected
- [ ] FalkorDB knowledge graph connected
- [ ] Hybrid memory (graph + vector recall)
- [ ] Playwright browser agent
- [ ] python_exec tool (sandboxed)
- [ ] Skills registry + base class
- [ ] 3 builtin skills working

### Phase 3 — Cloud
- [ ] Hetzner deployment working
- [ ] NATS JetStream replacing Valkey Streams in cloud
- [ ] nginx + SSL
- [ ] GitHub Actions CI/CD
- [ ] Prometheus metrics
- [ ] Grafana dashboards
- [ ] K8s manifests
- [ ] Deployment YAML configurator (dashboard page)
- [ ] `neuralfolk deploy` CLI command

### Phase 4 — Community
- [ ] 5 workflow templates
- [ ] Plugin/skill system public API
- [ ] CONTRIBUTING.md
- [ ] ProductHunt launch

---

## Current Blockers
<!-- AGENT: list anything that is stuck or needs a decision -->
None yet — project not started.

---

## Decisions Made
<!-- AGENT: record every architecture decision here so we don't re-debate it -->

| Decision | Choice | Reason |
|---|---|---|
| Event system (local) | Valkey Streams | MIT license, zero extra container, already in stack |
| Event system (cloud) | NATS JetStream | Single binary, 20MB RAM, production-grade |
| Cache / broker | Valkey (not Redis) | Redis changed license 2024, Valkey is MIT fork |
| Inference phase 1 | Ollama | Easiest local GPU setup, supports GGUF |
| Inference phase 2+ | vLLM + SGLang + llama.cpp + TensorRT + LiteRT | Full backend matrix |
| Primary local model | qwen2.5:7b (smart) + qwen2.5:3b (fast) | Fits in 8GB VRAM, good instruction following |
| Workflow engine | Celery + Valkey (phase 1), consider Temporal (phase 3) | MVP first |
| Vector DB | Qdrant (local Docker) | Best Python SDK, good performance |
| Knowledge graph | FalkorDB (local Docker) | Redis-compatible API, graph queries, MIT license |
| Memory strategy | Hybrid: graph entities + vector embeddings | Better recall than vector-only |
| Dashboard | Next.js 14 + Tailwind + shadcn/ui | Speed of development |
| Dashboard router | App Router | Server components, streaming support |
| Dashboard state | Zustand | Lightweight, no boilerplate |
| Dashboard WebSocket | Native browser WebSocket | No socket.io overhead |
| API framework | FastAPI + Python 3.12 | Async, typed, fast |
| Docker base image | python:3.12-slim | No musl libc issues; smaller than full image |
| Dependency manager | uv | 10-100x faster than pip; `uv pip install` is drop-in |
| ORM | SQLAlchemy 2.0 async | Modern, typed |
| HTTP client | httpx | Async-native |
| Logging | structlog | JSON structured logs, great for observability |
| Async file I/O | aiofiles | Never use sync open() in async context |
| Closed API backends | NONE | Open models only — core mission |
| Kafka | NOT USED | Replaced by Valkey Streams (local) / NATS (cloud) |
| JS package structure | Single package.json in services/dashboard/ | No second JS service yet; revisit if one is added |
| License | Apache 2.0 | Patent protection matters for infrastructure layer |
| Event ownership | One service per event prefix — see STACK.md table | Prevents duplicate events in dashboard |
| MEMORY.md vs DIFF_MEMORY.md | MEMORY.md = what was decided; DIFF_MEMORY.md = why | Both must be updated on every architecture decision |

---

## Open Questions
<!-- AGENT: things not yet decided, revisit when relevant -->

- [ ] TurboQuant: implement as wrapper over llama.cpp quantization or build custom GGUF pipeline?
- [ ] TurboVec: use product quantization or scalar quantization for embedding compression?
- [ ] Skills system: follow skills.sh spec exactly or adapt for agent use case?
- [ ] Knowledge graph schema: define entity types and relation types for agent memory
- [ ] Deployment configurator: web UI form → YAML, need to define all config parameters
- [ ] neuralfolk CLI: Python Click or Go binary?
- [ ] License: MIT or Apache 2.0? (Apache protects against patent trolls — probably better for infra)

---

## File Locations of Key Code
<!-- AGENT: update as files are created -->

| Component | File | Status |
|---|---|---|
| InferenceRouter | services/inference/router.py | not created |
| Event publisher | services/control-plane/core/events.py | not created |
| Agent base class | services/worker/agent/base.py | not created |
| Valkey config | docker-compose.yml | not created |
| Dashboard events page | services/dashboard/app/events/page.tsx | not created |

---

## Last Session Notes
<!-- AGENT: paste your own summary here at end of session -->
Project planning phase. No code written yet. Ready to start Phase 1 Week 1.
