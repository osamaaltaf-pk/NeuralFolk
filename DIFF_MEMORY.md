# DIFF_MEMORY.md — Break Investigations & Key Decisions
> This is NOT a change log. Git is the change log.
> This file exists for ONE reason: to explain WHY something broke, and WHY a non-obvious
> decision was made — things that git diff and commit messages cannot capture.
>
> AGENT: Write here only for (1) break investigations, (2) risky decisions, (3) "why not X" reasoning.
> AGENT: At session start, run `git log --oneline -10` and `git diff HEAD~3..HEAD --stat` FIRST.
>        Read this file SECOND, to understand the reasoning behind what git shows you.
> DEVELOPER: Prune resolved entries to DIFF_ARCHIVE.md monthly to keep this file small.

---

## When to Write an Entry

| Situation | Write entry? |
|---|---|
| Normal feature commit | ❌ No — git commit message is enough |
| Refactor with clear intent | ❌ No — commit message explains it |
| A bug broke something | ✅ Yes — BREAK + FIX entries |
| Chose approach A over B for non-obvious reason | ✅ Yes — DECISION entry |
| Changed a public interface/signature | ✅ Yes — note what callers were affected |
| Tried something that didn't work | ✅ Yes — saves next session from repeating it |
| Discovered a hidden constraint/gotcha | ✅ Yes — prevents future breakage |

---

## Entry Formats

### BREAK entry
```
--- BREAK {N} ---
DATE: YYYY-MM-DD
COMMIT_THAT_BROKE: {hash} or "pre-existing"
SYMPTOM: One sentence — what failed and how it manifested.
ROOT_CAUSE: One sentence — the actual reason it broke.
AFFECTED_FILES: list of files involved
HOW_FOUND: git diff / test failure / runtime error / etc.
---
```

### FIX entry (always follows a BREAK entry)
```
--- FIX {N} ---
DATE: YYYY-MM-DD
FIXES_BREAK: {N}
COMMIT: {hash}
WHAT_CHANGED: One sentence — the actual fix.
WHY_THIS_WORKS: One sentence — why the fix addresses the root cause.
REGRESSION_RISK: low | medium | high + one sentence if not low.
TESTS_CREATED: list of test_*.py files verifying the fix and accuracy.
---
```

### DECISION entry
```
--- DECISION {N} ---
DATE: YYYY-MM-DD
COMMIT: {hash} or "pre-code"
CONTEXT: One sentence — what were you implementing when this came up.
CHOICE: What you chose to do.
REJECTED: What you didn't do and why (the important part).
CONSTRAINT: What external fact forced or shaped this choice.
TESTS_CREATED: list of test_*.py files verifying this decision's correct operation.
REVISIT_IF: Condition under which this decision should be re-evaluated.
---
```

### GOTCHA entry
```
--- GOTCHA {N} ---
DATE: YYYY-MM-DD
COMPONENT: which service/file/library
DISCOVERY: What you found that wasn't obvious.
IMPACT: What breaks if you ignore this.
WORKAROUND: What the code does to handle it.
---
```

---

## Entries

--- DECISION 1 ---
DATE: project-start
COMMIT: pre-code
CONTEXT: Choosing event/messaging system for local dev.
CHOICE: Valkey Streams for local (phase 1-2), NATS JetStream for cloud (phase 3).
REJECTED: Kafka — massive operational overhead for a solo dev machine; Redis Streams — Redis changed to non-MIT license in 2024.
CONSTRAINT: Must be MIT licensed; must run in Docker with minimal RAM; must have Python async client.
REVISIT_IF: Valkey project gets abandoned or loses MIT status.
---

--- DECISION 2 ---
DATE: project-start
COMMIT: pre-code
CONTEXT: Choosing vector DB.
CHOICE: Qdrant (local Docker).
REJECTED: Pinecone (cloud-only, has API keys); Weaviate (heavier, more complex); pgvector (no dedicated similarity ops, tighter Postgres coupling).
CONSTRAINT: Must run fully local; must have best-in-class Python async SDK.
REVISIT_IF: Need >10M vectors or multi-tenancy — then evaluate Weaviate.
---

--- DECISION 3 ---
DATE: project-start
COMMIT: pre-code
CONTEXT: Choosing knowledge graph DB.
CHOICE: FalkorDB (local Docker).
REJECTED: Neo4j (not MIT in its useful form); ArangoDB (more complex, less Redis-compatible).
CONSTRAINT: Redis-compatible API (can reuse Valkey tooling); MIT license; Cypher query support.
REVISIT_IF: Graph queries exceed FalkorDB performance at scale — evaluate Neo4j Community then.
---

<!-- Agent appends new entries below. Newest = last entry in file. Keep file under 300 lines. -->

--- DECISION 4 ---
DATE: project-start
COMMIT: pre-code
CONTEXT: Choosing Docker base image for Python services.
CHOICE: python:3.12-slim
REJECTED: python:3.12-alpine — musl libc causes binary wheel failures with numpy, torch, asyncpg; significant debugging overhead with no meaningful size benefit for this stack.
CONSTRAINT: Must install pre-compiled wheels for GPU-adjacent libraries without recompilation.
REVISIT_IF: Image size becomes a CI concern AND all binary deps have confirmed Alpine wheels.
---

--- DECISION 5 ---
DATE: project-start
COMMIT: pre-code
CONTEXT: Choosing Python dependency manager for Makefile and Dockerfiles.
CHOICE: uv — `uv pip install -r requirements.txt` as drop-in in all Docker layers.
REJECTED: pip — 10-100x slower in Docker layer rebuilds; developer iteration time matters; no lockfile performance. pip-tools considered but uv supersedes it.
CONSTRAINT: Must be installable via `pip install uv` bootstrap; must not require Rust toolchain at runtime.
REVISIT_IF: uv breaks a CI environment or a dependency has uv incompatibility.
---

--- DECISION 6 ---
DATE: project-start
COMMIT: pre-code
CONTEXT: Deciding JS package structure for dashboard service.
CHOICE: Single package.json inside services/dashboard/ only.
REJECTED: Monorepo with turborepo/nx — only one JS service exists; premature abstraction adds tooling overhead and complicates Docker COPY steps.
CONSTRAINT: Docker COPY must be simple; CI must not require workspace hoisting.
REVISIT_IF: A second JS service (e.g. a separate admin panel or CLI web UI) is added to the repo.
---

--- DECISION 7 ---
DATE: project-start
COMMIT: pre-code
CONTEXT: Choosing license for the neuralfolk project.
CHOICE: Apache 2.0
REJECTED: MIT — simpler but no patent protection. For an infrastructure/runtime tool that companies will embed, Apache 2.0's explicit patent grant matters.
CONSTRAINT: Must be OSI-approved; must allow commercial use; must not be GPL (copyleft would block enterprise adoption).
REVISIT_IF: Legal counsel advises otherwise or a key dependency forces license compatibility change.
---

--- BREAK 1 ---
DATE: 2026-05-26
COMMIT_THAT_BROKE: pre-existing
SYMPTOM: Running pytest failed due to TypeError in test_health_api.py AsyncClient instantiation.
ROOT_CAUSE: Modern versions of HTTPX (0.27.0+) deprecated the `app` keyword argument in AsyncClient.
AFFECTED_FILES: tests/unit/test_health_api.py
HOW_FOUND: test failure (pytest tests/)
---

--- FIX 1 ---
DATE: 2026-05-26
FIXES_BREAK: 1
COMMIT: c42703d
WHAT_CHANGED: Refactored test_health_api.py to use `ASGITransport(app=app)` under `httpx.AsyncClient`.
WHY_THIS_WORKS: ASGI transport abstracts the FastAPI app routing cleanly in modern HTTPX versions.
REGRESSION_RISK: low
TESTS_CREATED: tests/unit/test_health_api.py
---

--- BREAK 2 ---
DATE: 2026-05-26
COMMIT_THAT_BROKE: pre-existing
SYMPTOM: Docker compose failed to bring up cache and graph-db services due to port 6379 being in use.
ROOT_CAUSE: Both Valkey and FalkorDB containers attempted to bind host port 6379 on the same local network interface.
AFFECTED_FILES: .env, .env.example
HOW_FOUND: runtime error (docker compose up)
---

--- FIX 2 ---
DATE: 2026-05-26
FIXES_BREAK: 2
COMMIT: c42703d
WHAT_CHANGED: Remapped FalkorDB host port to 6380 in .env and .env.example.
WHY_THIS_WORKS: Exposes FalkorDB on host port 6380 while preserving internal Docker network port 6379.
REGRESSION_RISK: low
TESTS_CREATED: none (verified via docker compose up and docker ps status checks)
---

--- DECISION 8 ---
DATE: 2026-05-26
COMMIT: local
CONTEXT: Designing the InferenceRouter and its backend integrations.
CHOICE: Implemented skeletons and adapters for the entire multi-backend inference matrix (Ollama, vLLM, SGLang, llama.cpp, TensorRT-LLM, LiteRT) in Phase 1, using miniCPM5-1B as canonical 32k model.
REJECTED: Postponing other backends until Phase 2; implementing them now enables verification of the complete intelligent routing heuristics and graceful Ollama fallback logic immediately.
CONSTRAINT: Must allow graceful Ollama fallback if target backends are offline/unconfigured.
TESTS_CREATED: tests/unit/test_inference.py
REVISIT_IF: A new major local inference backend engine emerges that is not in the stack.
---

--- DECISION 9 ---
DATE: 2026-05-26
COMMIT: local
CONTEXT: Packaging the shared `services/inference` folder for both control-plane and worker containers.
CHOICE: Adjusted Docker build context to workspace root `.` and updated COPY/volume mount instructions.
REJECTED: Duplicating the codebase inside both control-plane and worker folders (which breaks monorepo style), or packaging as a private wheel (which complicates local dev builds).
CONSTRAINT: Must permit rapid local dev hot-reloads of shared library files.
TESTS_CREATED: none (verified via docker compose up and mock tests)
REVISIT_IF: We transition to a strictly decentralized microservices layout with separate repositories.
---