# CONTEXT.md — Current Session State
> Agent: read this second (after git log). Update before ending every session.
> Format is fixed — do not restructure it. Fill in the fields, nothing else.

---

## Session Info

```
SESSION:        6
DATE:           2026-05-28
LAST_COMMIT:    0ddfbe1 — fix(integration): use CP1252-safe arrows in test_engine_ollama.py
```

---

## Current Task

```
PHASE:          1 — Local Foundation
TASK:           Sequential Inference Engine Integration Testing (Ollama completed, next engines)
STATUS:         in-progress

DESCRIPTION:
  Fully verified and stabilized Phase 1 inference engine integration for Ollama. 
  Model openbmb/minicpm5:fp16 is 100% pulled inside container neuralfolk-inference.
  All 5/5 Ollama integration tests verified successfully passing end-to-end.
  Stopped and cleaned up redundant containers (IBM Granite 3.1 8B in llamacpp) and 
  background CLI tasks to resolve Windows host virtual page file exhaustion issues.
  Configured llama.cpp test suite to use granite-3.1-8b-instruct for future sequential run.

BLOCKED_BY:     none
```

---

## Active Files
> Only files the agent is currently reading or modifying. Keep this list small.

```
none — session ended cleanly
```

---

## What Was Done Last Session

```
Session 6 (Ollama Engine Integration Test Success):
- Staged, committed, and pushed uncommitted openbmb/minicpm5:fp16 model name mappings across 13 files.
- Re-aligned and optimized docker-compose.engines.yml served-model-name for SGLang and vLLM.
- Proactively ran and monitored the 2.2GB model pull for openbmb/minicpm5:fp16 inside Ollama container.
- Cleaned up redundant background tasks to free up Windows host virtual page file handles.
- Stopped secondary/stale inference engine containers to enforce strict "one-engine-at-a-time" sequential resource limits.
- Configured llamacpp container and tests to use local redhat/granite-3.1-8b-instruct:latest image.
- Resolved Windows CP1252 arrow encoding printout crashes in integration test files.
- Executed Ollama integration tests: all 5/5 tests verified passing successfully end-to-end.
- Updated MEMORY.md, CONTEXT.md and pushed clean state to origin.
```

---

## Next Session Should Start With

```
1. git log --oneline -5                   (confirm push landed)
2. docker ps                              (confirm Ollama + core base services are healthy)
3. Proceed to Engine 2: vLLM or Engine 4: llama.cpp depending on user preference:
   - To test llama.cpp: docker compose -f docker-compose.yml -f docker-compose.engines.yml --profile llamacpp up -d llamacpp
   - Then run: pytest tests/integration/test_engine_llamacpp.py -v -s
```

---

## Known Gotchas for Current Task

```
- Parallel Ollama Pulls: Never invoke parallel pulls (exec + HTTP API) for the same model; it triggers a layer registry download reset.
- Windows CP1252 Terminal encoding: Emitting literal arrow characters (→) or emojis to stdout in pytest crashes the suite. Use CP1252-safe ASCII replacements (e.g., ->).
- Resource limits: Do not run multiple GPU/heavy model inference containers (like llamacpp + Ollama) at the same time to avoid Windows paging file limits (error 800705af).
```

---

## Token Budget Remaining This Session
> Agent: rough estimate. If you hit ~4000 tokens of file reads, stop and tell developer.

```
Hard cap: stop reading files if cumulative file reads exceed ~4000 tokens.
Tell developer: "Approaching read budget. Recommend splitting task."
```
