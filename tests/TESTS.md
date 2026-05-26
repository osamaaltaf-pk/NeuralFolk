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

---

## Test Execution Reference

To execute the test suites, utilize the following pytest commands:

```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/

# Run connection tests specifically
pytest tests/unit/test_connections.py -v
```

---

## Test Execution History Log

| Date | Session | Commits Verified | Result | Notes |
|---|---|---|---|---|
| 2026-05-26 | 2 | `b807baf`, `db0217b` | 🟢 3/3 passed | Initial connection suite verifying database and Valkey client code. |
| 2026-05-26 | 2 | `127c761`, `2b915c1` | 🟢 4/4 passed / 2 skipped | Added health route unit checks and connection integration tests. |
| 2026-05-26 | 2 | `67f03ea` | 🟢 6/6 passed | Resolved HTTPX AsyncClient deprecation, resolved falkordb host port collision, and verified live database integration connections. |
