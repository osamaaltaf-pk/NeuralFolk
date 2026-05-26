# REVIEW.md — Agent Review Queue
> Agent writes here. Developer reads and clears.
> Three sections: OPEN (needs action), RESOLVED (for reference), ARCH_DECISIONS (needs human input).

---

## How This File Works

- Agent adds items to OPEN when it finds something risky, uncertain, or needing human review
- Developer reads OPEN before each session, makes decisions, moves items to RESOLVED
- Neither agent nor developer deletes RESOLVED entries — they're audit history
- ARCH_DECISIONS is for anything that would change STACK.md or MEMORY.md Decisions table

---

## OPEN — Needs Action
> Developer: clear these before telling the agent to proceed.

```
none yet — project not started
```

---

## ARCH_DECISIONS — Needs Human Input Before Agent Proceeds

| ID | Question | Context | Blocking? | RESOLVED |
|---|---|---|---|---|
| AD-001 | Which Python version in Docker? | STACK.md says 3.12 but doesn't specify base image (python:3.12-slim vs python:3.12-alpine) | yes, blocks Dockerfile creation | **python:3.12-slim** — alpine causes binary compatibility issues with numpy/torch wheels; slim is smaller than full and avoids musl libc pain |
| AD-002 | Makefile: use `uv` or `pip` for dependency management? | uv is 10–100x faster but less familiar; pip is universal | yes, blocks Makefile | **uv** — speed matters in CI and Docker layer rebuilds; `uv pip install` is a drop-in; add `pip install uv` as bootstrap step |
| AD-003 | Monorepo or separate package.json per service? | Affects how `npm install` works in CI | yes, blocks dashboard scaffold | **single package.json in services/dashboard/** — only one JS service exists; monorepo tooling (turborepo/nx) is premature; revisit if a second JS service is added |
| AD-004 | neuralfolk CLI license: MIT or Apache 2.0? | Apache protects against patent claims; MIT is simpler | no, Phase 4 | **Apache 2.0** — infrastructure tool; patent protection matters more than simplicity at this layer |

---

## CODE_REVIEW — Agent Self-Flagged Issues

> Agent adds here when it writes code it's not confident in.
> Format: FILE | ISSUE | SEVERITY (low/med/high) | TESTS_CREATED (yes/no - specify file) | SUGGESTED_FIX

```
none yet
```

---

## RESOLVED — Cleared Items
> Don't delete. Add date resolved and outcome.

```
none yet
```

---

## How Agent Should Add an OPEN Item

```markdown
### REVIEW-{N}: {Short title}
DATE: YYYY-MM-DD
SESSION: {N}
TYPE: code_risk | arch_decision | blocked | needs_test | security
TESTS_CREATED: yes/no (specify test file in tests/ and update tests/TESTS.md)

CONTEXT:
  What the agent was doing when it found this.

ISSUE:
  What is uncertain or risky. One paragraph max.

OPTIONS:
  A) ...
  B) ...

RECOMMENDATION:
  What the agent recommends and why.

IMPACT_IF_IGNORED:
  What breaks or accumulates technical debt if this isn't addressed.
```
