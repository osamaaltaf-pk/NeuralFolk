# CONTEXT.md — Current Session State
> Agent: read this second (after git log). Update before ending every session.
> Format is fixed — do not restructure it. Fill in the fields, nothing else.

---

## Session Info

```
SESSION:        1
DATE:           not started
LAST_COMMIT:    none — repo not initialized
```

---

## Current Task

```
PHASE:          1 — Local Foundation
TASK:           Initialize repo structure
STATUS:         not started

DESCRIPTION:
  Create the full directory skeleton from AGENT.md Repo Structure section.
  Then: docker-compose.yml, .env.example, Makefile, FastAPI /health endpoint.
  Stop after those four deliverables and update this file.

BLOCKED_BY:     none
```

---

## Active Files
> Only files the agent is currently reading or modifying. Keep this list small.

```
none yet
```

---

## What Was Done Last Session
> Agent fills this in at END of session before handing off.

```
Session 0 (planning): No code written. Architecture decisions made.
All decisions recorded in MEMORY.md and DIFF_MEMORY.md.
Repo not yet initialized.
```

---

## Next Session Should Start With
> Agent fills this at END of session.

```
1. git log --oneline -10
2. Read CONTEXT.md (this file)
3. Read DIFF_MEMORY.md
4. Check REVIEW.md for any new OPEN items
5. Continue Phase 1: repo init → docker-compose → Makefile → FastAPI skeleton
```

---

## Known Gotchas for Current Task

```
- Celery + Pydantic v2: task serialization requires pydantic_settings; see STACK.md note
- Valkey client: use `valkey` pip package, NOT `redis` — see AGENT.md NEVER DO list
- SQLAlchemy: use 2.0 async style only, not 1.x legacy style
- Docker base image: python:3.12-slim (resolved in REVIEW.md AD-001)
```

---

## Token Budget Remaining This Session
> Agent: rough estimate. If you hit ~4000 tokens of file reads, stop and tell developer.

```
Hard cap: stop reading files if cumulative file reads exceed ~4000 tokens.
Tell developer: "Approaching read budget. Recommend splitting task."
```
