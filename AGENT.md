# AGENT.md — Neuralfolk Agent Operating Constitution
> You are a coding agent building Neuralfolk — "Neural networks for everyone."
> This file is your law. Read it first, every session, before touching anything.

---

## What You Are Building

**Neuralfolk** — A self-hosted, open-source AI runtime OS.
Runs agents, workflows, and LLM inference on any machine — RTX 2070 laptop to Kubernetes cluster.
No API keys. No vendor lock-in. Air-gap capable.

> "What Docker did for containers, Neuralfolk does for AI inference."

---

## Developer Hardware (assume this unless told otherwise)

```
GPU:    RTX 2070 · 8GB VRAM · CUDA 12 · Turing arch
RAM:    16GB DDR4
OS:     Ubuntu 24.04 or Windows WSL2
Models: miniCPM5-1B (primary test, 32k ctx) via Ollama; qwen2.5:3b/7b optional
```

---

## Core Principle: Git Is Ground Truth. DIFF_MEMORY.md Is Why.

You do NOT read the full codebase. Ever.
Git tells you **what** changed. DIFF_MEMORY.md tells you **why it broke and what was decided**.
CONTEXT.md tells you **where you are right now**.

Token waste = context loss = mistakes. Every file you read unnecessarily
is tokens you cannot spend on writing correct code.

---

## Session Startup Protocol (MANDATORY — every session, in order)

### Step 1 — Orient with git (run these exact commands)
```bash
git log --oneline -10                        # last 10 commits, see the story
git diff HEAD~3..HEAD --stat                 # what files changed in last 3 commits
git diff HEAD~1 -- <file>                    # read a specific file's last change only
git stash list                               # any uncommitted work from last session?
```

> **Session 1 / empty repo exception:** If `git log` returns nothing or "does not have any commits",
> skip git steps entirely. Read CONTEXT.md → it will say `LAST_COMMIT: none`.
> Your first task is: `git init`, create the repo skeleton from the Repo Structure section,
> then `git add -A && git commit -m "chore(repo): initial scaffold"`.
> Do NOT run `git diff HEAD~3` on an empty repo — it will error.

### Step 2 — Read state files (in this order, nothing else yet)
```
CONTEXT.md         ~400 tokens   current task, active files, blockers
DIFF_MEMORY.md     ~300 tokens   root causes and decisions (not a change log)
REVIEW.md          ~200 tokens   open items needing your attention
```

**CONTEXT.md required fields** (do not invent new fields — fill these exactly):
```
SESSION, DATE, LAST_COMMIT
PHASE, TASK, STATUS, DESCRIPTION, BLOCKED_BY
Active Files list
What Was Done Last Session
Next Session Should Start With
Known Gotchas for Current Task
```

**Hard token read cap:** If cumulative file reads in a session exceed ~4000 tokens, stop coding.
Write to developer: "Approaching read budget. Recommend splitting task into: [A] [B]."

### Step 3 — State your understanding
Write back to the developer in **≤50 words**:
- What was done last session (from git log)
- What the current task is (from CONTEXT.md)
- What you are about to do next

### Step 4 — Ask one question if blocked, otherwise proceed
If CONTEXT.md says "BLOCKED_BY: X" — ask about X only.
If everything is clear — start coding immediately.

**Do not ask questions you can answer by reading the files above.**

---

## How to Read Code (Diff-First, Always)

### Before modifying any file:
```bash
git diff HEAD~3..HEAD -- services/path/to/file.py   # what changed recently
git log --oneline -5 -- services/path/to/file.py    # commit history for this file
```
Read the diff. Then read only the lines you need to change — use line ranges, not whole files.

### File reading priority:
```
1. git diff output          (free — no token cost, always run first)
2. CONTEXT.md active files  (must read, small)
3. Files you will MODIFY    (read before touching)
4. Direct importers         (check signatures only if you change a public interface)
5. Everything else          (AVOID — ask git log first, read only if truly blocked)
```

### If you need to understand a function from another file:
```bash
grep -n "def function_name" services/           # find the line number
# then read only that function using line range, not the whole file
```

---

## How to Write Code

### Non-negotiable rules (from original AGENT.md):
- **Test-Mandate** — For each new feature, stack update, or resolved issue, you MUST create corresponding `test_*.py` files in `tests/` and document/track tests in a `tests/TESTS.md` file to verify accuracy before proceeding to the next step.
- **Async everywhere** — no blocking calls in async context, ever
- **Pydantic v2** for all schemas and config
- **SQLAlchemy 2.0 async** — not 1.x style
- **httpx** not requests for HTTP
- **Type hints on every function** — no bare `Any`
- **structlog** not print() for logging
- **Custom exceptions** in `core/exceptions.py` — never silent `except: pass`

### Event emission is not optional:
Every significant action MUST emit a Valkey stream event:
```python
await events.publish("workflow.started", {
    "workflow_id": wf.id,
    "triggered_by": user_id,
    "timestamp": utcnow_iso(),
})
```
Skipping this breaks the live dashboard feed. No exceptions.

### Docker rules:
- Every service has its own multi-stage Dockerfile (builder → runtime)
- Non-root user in every container
- Health check on every service

### Completeness rule:
Write complete, working code. No `# TODO: implement this`, no placeholder functions.
A half-written function costs more tokens to fix next session than to write correctly now.

### Comment policy:
- Docstring on every class and public method
- One-line comment on non-obvious logic
- No commented-out code in commits — delete it
- No `# type: ignore` without an explanation comment

---

## Naming Conventions (non-negotiable)

```
Python files:       snake_case.py
Classes:            PascalCase
Functions:          snake_case
Constants:          UPPER_SNAKE_CASE
Env variables:      UPPER_SNAKE_CASE
Docker services:    kebab-case
API routes:         /kebab-case
Valkey stream keys: neuralfolk:category:subcategory
```

---

## Git Workflow

### Commit message format (strict):
```
<type>(<scope>): <what changed in 10 words or less>

type:  feat | fix | refactor | docs | chore | test
scope: control-plane | worker | dashboard | inference | memory | deploy | agent

Examples:
feat(inference): add Ollama backend with qwen routing
fix(worker): resolve Celery task serialization on retry
docs(agent): update CONTEXT.md active files list
chore(docker): pin Qdrant image to stable version
```

### Before every commit:
```bash
make lint          # ruff + mypy — must pass
make test          # pytest — must not break green tests
make docker-check  # docker compose config --quiet
```

### After every commit:
1. Update `CONTEXT.md` → Last Commit field + task status
2. If the commit fixed a break or made a non-obvious decision → append to `DIFF_MEMORY.md`
3. Tick completed items in `MEMORY.md`

**Dual-write rule — MEMORY.md vs DIFF_MEMORY.md:**
```
MEMORY.md   → the lookup table. One-line entry in Decisions Made table. Agent reads this to
               know what was decided. Update every time a decision is made.
DIFF_MEMORY.md → the reasoning. Full DECISION entry with REJECTED + CONSTRAINT.
               MEMORY.md is authoritative for "what". DIFF_MEMORY.md is authoritative for "why".
               Always write BOTH when making an architecture decision.
```

---

## Error Protocol

When something breaks, follow this order exactly:

```
1. STOP. Do not immediately try random fixes.
2. Run: git diff HEAD~3..HEAD --stat        (did a recent commit touch the broken area?)
3. Run: git diff HEAD~1 -- <broken_file>   (what exactly changed in that file?)
4. Identify root cause in one sentence.
5. Append a BREAK entry to DIFF_MEMORY.md.
6. Write the fix.
7. Append a FIX entry to DIFF_MEMORY.md.
8. Commit with: fix(<scope>): <what was broken and how fixed>
```

If the root cause isn't obvious after steps 2-3, read only the failing file + its direct imports.
Do not read files that are not in the call stack of the error.

---

## Architecture Discipline

Before making ANY architecture decision:
1. Check `MEMORY.md` → Decisions Made table
2. Check `STACK.md` → is the technology already chosen?
3. If it's already decided → follow the decision, do not re-debate it
4. If it's not decided → write an `ARCH_DECISIONS` entry in `REVIEW.md` and flag it to the developer

**Do NOT use a technology not in STACK.md without a REVIEW.md entry.**

---

## What You Must NEVER Do

```
❌ Add Gemini, Claude, OpenAI, or any closed API backends — open models only
❌ Use the `redis` package — always `valkey` (different license)
❌ Use `requests` — use `httpx`
❌ Use synchronous SQLAlchemy — async only
❌ Hardcode model names — always from config/env
❌ Self-host Kafka — use Valkey Streams (phase 1-2) or NATS JetStream (phase 3)
❌ Use print() for logging — use structlog
❌ Skip Pydantic validation on API inputs
❌ Skip creating corresponding test_*.py files or updating tests/TESTS.md for any new feature, stack update, or fixed bug.
❌ Read an entire file when you need one function — use line ranges + grep
❌ Skip updating CONTEXT.md after finishing a task
❌ Write a DIFF_MEMORY.md entry for every commit — only breaks and decisions
❌ Use synchronous file I/O (open(), read()) in any async function — use aiofiles
❌ Call asyncio.run() inside an async function — it will deadlock
❌ Write bare `except Exception: pass` or `except: pass` — always log + raise custom exception
❌ Emit the same Valkey event from two different services — check ownership table in STACK.md
```

---

## Token Budget (treat context like RAM)

```
Approximate costs per read:
  CONTEXT.md:              ~400 tokens
  DIFF_MEMORY.md:          ~300 tokens  (keep it short — only breaks/decisions)
  REVIEW.md:               ~200 tokens
  git diff HEAD~3 --stat:  ~100 tokens  (nearly free — always run this)
  git diff one file:       ~200-500 tokens
  Typical Python file:     ~800-2000 tokens
  Full docker-compose.yml: ~600 tokens
  Full STACK.md:           ~2000 tokens  (read only when adding new tech)
```

If a task requires reading >5 full files: break the task into subtasks.
Tell the developer: "This needs X files. I recommend splitting into: [A] [B]."

---

## Repo Structure (source of truth)

```
neuralfolk/
├── AGENT.md                    ← you are here
├── CONTEXT.md                  ← current session state (agent updates every session)
├── DIFF_MEMORY.md              ← break investigations + key decisions only
├── REVIEW.md                   ← open issues flagged for human review
├── MEMORY.md                   ← build checklist + all architecture decisions
├── STACK.md                    ← every technology choice + why
├── docker-compose.yml
├── docker-compose.dev.yml      ← dev overrides (hot reload)
├── .env.example
├── Makefile
│
├── services/
│   ├── control-plane/          ← FastAPI backend (Python 3.12)
│   │   ├── main.py
│   │   ├── api/routes/
│   │   │   ├── workflows.py
│   │   │   ├── agents.py
│   │   │   ├── inference.py
│   │   │   ├── models.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py       ← pydantic settings
│   │   │   ├── database.py     ← postgres async
│   │   │   ├── events.py       ← valkey stream publisher
│   │   │   ├── exceptions.py   ← custom exception classes
│   │   │   └── auth.py
│   │   ├── models/             ← SQLAlchemy models
│   │   └── schemas/            ← Pydantic schemas
│   │
│   ├── inference/
│   │   ├── router.py           ← InferenceRouter (core abstraction)
│   │   ├── backends/
│   │   │   ├── base.py
│   │   │   ├── ollama.py       ← phase 1
│   │   │   ├── vllm.py         ← phase 2
│   │   │   ├── sglang.py
│   │   │   ├── llamacpp.py
│   │   │   ├── tensorrt.py
│   │   │   └── litert.py
│   │   ├── quantization/turboquant.py
│   │   └── kv_cache/mla.py
│   │
│   ├── worker/
│   │   ├── celery_app.py
│   │   ├── agent/
│   │   │   ├── base.py
│   │   │   ├── planner.py
│   │   │   ├── executor.py
│   │   │   └── orchestrator.py
│   │   ├── tools/
│   │   │   ├── base.py
│   │   │   ├── filesystem.py
│   │   │   ├── web_search.py
│   │   │   ├── http_request.py
│   │   │   ├── python_exec.py
│   │   │   ├── browser.py
│   │   │   └── memory.py
│   │   └── workflows/
│   │       ├── engine.py
│   │       └── definitions/
│   │
│   ├── memory/
│   │   ├── graph.py
│   │   ├── vector.py
│   │   ├── hybrid.py
│   │   └── turbovec.py
│   │
│   └── dashboard/              ← Next.js 14
│       ├── app/
│       │   ├── page.tsx
│       │   ├── workflows/
│       │   ├── agents/
│       │   ├── inference/
│       │   ├── events/
│       │   └── deploy/
│       └── components/
│
├── skills/
│   ├── registry.py
│   ├── base.py
│   └── builtin/
│       ├── web_research.skill/
│       ├── code_review.skill/
│       ├── data_extract.skill/
│       └── summarize.skill/
│
├── deployment/
│   ├── configurator/
│   │   ├── recommender.py
│   │   └── generator.py
│   ├── providers/
│   │   ├── local.py
│   │   ├── hetzner.py
│   │   ├── runpod.py
│   │   └── vastai.py
│   └── k8s/
│
├── templates/
│   ├── research-agent/
│   ├── invoice-processor/
│   ├── competitor-monitor/
│   └── daily-briefing/
│
├── scripts/
│   ├── setup.sh
│   ├── pull-models.sh
│   └── health-check.sh
│
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## Current Phase

**PHASE 1 — Local Foundation**
Goal: `docker compose up` → working AI agent on local GPU, no API keys needed.

See MEMORY.md for checklist. See CONTEXT.md for today's task.

---

## Agent Self-Check (before ending every session)

- [ ] Did I run `git log --oneline -5` to confirm my commits landed?
- [ ] Did I update CONTEXT.md with current task status and last commit hash?
- [ ] Did I tick completed items in MEMORY.md?
- [ ] If something broke or I made a non-obvious decision → did I write to DIFF_MEMORY.md?
- [ ] Did I flag anything risky in REVIEW.md?
- [ ] Did I create/update test.py files and tests/TESTS.md to verify accuracy of my changes?
- [ ] Does `make lint` pass?
- [ ] Are there any broken imports or unfinished functions?

If any box is unchecked — complete it before ending.