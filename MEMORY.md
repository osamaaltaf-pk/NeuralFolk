## Last Updated
<!-- AGENT: update this timestamp every session -->
DATE: 2026-05-28
SESSION: 6

---

## What Has Been Built
<!-- AGENT: tick boxes and add notes as features are completed -->

### Phase 1 — Local Foundation
- [x] Repo initialized with structure from AGENT.md
- [x] docker-compose.yml (postgres, valkey, qdrant, control-plane, worker, dashboard)
- [x] .env.example with all variables documented
- [x] Makefile with dev commands
- [x] FastAPI skeleton with /health endpoint
- [x] Postgres connected (async SQLAlchemy)
- [x] Valkey connected (aioredis pointing to Valkey)
- [x] Pydantic settings (core/config.py)
- [x] Test-Mandate Integration (created tests/TESTS.md and test guidelines implemented in constitution)
- [x] InferenceRouter skeleton
- [x] Ollama backend connected
- [x] miniCPM5-1B test model responding via /api/v1/inference/chat (32k context size)
- [x] Event publisher (events.py) — XADD to Valkey streams
- [x] Basic agent loop (plan → execute → result)
- [x] Filesystem tool
- [x] Web search tool (DuckDuckGo)
- [x] /api/agents/spawn endpoint
- [x] Celery worker connected
- [x] Next.js dashboard scaffold
- [x] Dashboard: system overview page
- [x] Dashboard: live event stream (WebSocket → Valkey XREAD)
- [x] Dashboard: workflow trigger UI
- [ ] ngrok tunnel working
- [x] README.md written with architecture diagram

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
None. All Phase 1 Docker containers healthy. All 7 services running. Next: inference engine sequential live testing (Ollama first, then vLLM etc).

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
| Primary local model | miniCPM5-1B (32k context, primary for all tests) | Canonical test model across all inference stacks; qwen2.5:3b/7b remain as optional alternatives |
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
| Complete Inference Stack | 6 backends + InferenceRouter | Phase 1 skeleton designed with active Ollama and canonical miniCPM5-1B model |
| Docker Context Adjustment | Workspace-root context `.` | Permits control-plane and worker to cleanly share import paths inside the services folder |

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
| InferenceRouter | services/inference/router.py | completed |
| Event publisher | services/control-plane/core/events.py | completed |
| Agent base class | services/worker/agent/base.py | completed |
| Celery worker app | services/worker/celery_app.py | completed |
| Agent task runner | services/worker/tasks.py | completed |
| Filesystem tool | services/worker/tools/filesystem.py | completed |
| Web search tool | services/worker/tools/search.py | completed |
| Agents API route | services/control-plane/api/routes/agents.py | completed |
| Events WebSocket | services/control-plane/api/routes/events_ws.py | completed |
| DB Models | services/control-plane/models/models.py | completed |
| Pydantic Schemas | services/control-plane/schemas/schemas.py | completed |
| Dashboard home | services/dashboard/app/page.tsx | completed |
| Dashboard events page | services/dashboard/app/events/page.tsx | completed |
| Dashboard agents page | services/dashboard/app/agents/page.tsx | completed |

---

## Last Session Notes
<!-- AGENT: paste your own summary here at end of session -->
Session 1: Initialized Git repository with author `osamaaltaf-pk`. Created folder skeleton and delivered configuration files (docker-compose, Makefile, .env, etc.) and basic FastAPI skeleton. Committed as chore(repo): initial scaffold (822f6f6).
Session 2: Connected PostgreSQL (async SQLAlchemy 2.0 + asyncpg) and Valkey (valkey-py async client) to FastAPI. Configured async lifespan context manager in main.py for resource pools, and integrated live connection checks in health endpoint. Wrote automated test suite. Committed as feat(control-plane): add postgres and valkey core connectivity (b807baf).
Session 3-4: Built complete Phase 1: event publisher (events.py + XADD), SQLAlchemy models, Pydantic schemas, agents spawn API, WebSocket event feed, Celery worker (celery_app.py + tasks.py), ReactiveAgent loop, FilesystemTool, SearchTool (DuckDuckGo), full Next.js dashboard (home + events + agents pages). Committed as feat(control-plane): implement full phase 1 (afad16f).
Session 5: Fixed all Docker health regressions — worker NameError (Optional import), control-plane healthcheck 404 (wrong URL), Qdrant healthcheck curl-not-found (switched to TCP), worker inherited HTTP healthcheck (overrode with celery inspect ping). All 7 containers now healthy. Committed as fix: resolve all container health issues (ccd6a4d).
Session 6: Completed Ollama integration engine verification using canonical `openbmb/minicpm5:fp16` model inside container. Resolved CP1252 character-encoding bugs in integration printouts. Cleaned up redundant background tasks to resolve Windows virtual memory page file limitations. All 5/5 Ollama integration tests verified successfully passing end-to-end. Committed as fix(integration): use CP1252-safe arrows in test_engine_ollama.py (0ddfbe1).
