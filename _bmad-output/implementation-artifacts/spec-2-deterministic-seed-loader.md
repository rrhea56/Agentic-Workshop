---
title: 'Deterministic seed loader'
type: 'feature'
created: '2026-09-26'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: 'cf0f2110b5ba04b76abf8ab9d2c3b52d9f7f4cfe'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The triage MCP server expects a local SQLite database, but the repository has no repeatable way to initialize it from the read-only ticket and customer seed data.

**Approach:** Add a root-level `load_seed.py` command that rebuilds the repository-root `app.db` from both CSV files, preserving their headers and rows in the `tickets` and `customers` tables.

## Boundaries & Constraints

**Always:** Read `seed/tickets.csv` and `seed/customers.csv` without modifying them; create `app.db` at the repository root; preserve each CSV's column names and row values; make repeated runs deterministic and compatible with `mcp/triage_server.py`; use only the Python standard library and local files.

**Never:** Add network calls, API-key requirements, new dependencies, or changes to `seed/`, `mcp/triage_server.py`, the Epic 1 schema, or the MCP query contract. Do not commit `app.db`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| HAPPY_PATH | Both seed CSVs exist and contain their headers and rows | `app.db` contains `tickets` and `customers` with matching columns and data | Command exits successfully |
| REPEAT_RUN | Existing `app.db` contains data from an earlier run | Tables are replaced with the same seed-derived contents, without duplicate rows | Command remains successful and deterministic |
| MISSING_SEED | A required seed CSV is unavailable or unreadable | No successful database load is reported | Exit non-zero with a clear file-related error |

</frozen-after-approval>

## Code Map

- `seed/tickets.csv` -- read-only source with `ticket_id`, `customer_id`, `created_at`, and `text` columns; includes untrusted ticket text.
- `seed/customers.csv` -- read-only source with `customer_id`, `name`, `plan`, and `open_tickets` columns.
- `mcp/triage_server.py:8-39` -- existing repository-root `app.db` path and required `tickets`/`customers` query contract; do not modify.
- `run_agent.py:1-20` -- root-level CLI conventions for a guarded `main()` entry point.
- `tests/test_schema.py` -- pytest style and test location to follow; no loader behavior exists yet.
- `.gitignore:1-5` -- `app.db` is ignored and must remain generated locally.

## Tasks & Acceptance

**Execution:**
- [x] `load_seed.py` -- implement a guarded CLI that resolves repository-relative paths, reads both CSV headers and rows, recreates the two SQLite tables transactionally, and reports clear failures -- provide the specified deterministic initialization command without changing read-only inputs.
- [x] `tests/test_seed_loader.py` -- verify table names, exact column names, row contents, repeatability, and missing-input failure behavior -- protect the loader contract and edge cases.

**Acceptance Criteria:**
- Given a clean checkout with both seed files present, when `uv run python load_seed.py` runs, then it exits successfully and creates `app.db` with `tickets` and `customers` tables whose columns and rows match the source CSVs.
- Given an existing generated `app.db`, when the loader runs a second time, then both tables contain exactly the same seed-derived contents as after the first run and no duplicate rows exist.
- Given a missing or unreadable required seed file, when the loader runs, then it exits non-zero with a clear error and does not report a successful load.
- Given the generated database, when `mcp/triage_server.py` queries a known ticket and customer, then the existing MCP query contract continues to work without changes to that server.

## Implementation Notes

## Review Triage Log

- **medium — patched:** The loader did not explicitly begin a transaction before rebuilding both tables; `BEGIN` now covers both replacements so a later SQLite failure rolls back the earlier table work.
- **false — rejected:** Retaining unrelated tables or views was not shown to violate the story; the contract requires the `tickets` and `customers` tables and does not require deleting unrelated database objects.
- **low — patched:** The unreadable-seed matrix row lacked a test; the suite now exercises a directory at the expected CSV path and verifies non-zero exit, clear stderr, and no success output.
- **low — patched:** The MCP compatibility acceptance criterion lacked direct test coverage; the suite now invokes the existing `get_ticket` and `get_customer_history` functions after loading.
- **false — rejected:** Leaving the generated `app.db` after tests is expected for this CLI, and the file is ignored by Git; the test always initializes it before inspecting contents.
- **medium — patched:** A second reviewer independently identified the same transaction-boundary risk; the explicit `BEGIN` fix addresses it.
- **low — patched:** The missing-seed test did not assert that failures omit the success message; it now asserts `Loaded` is absent from stdout.

## Verification

**Commands:**
- `uv run pytest` -- expected: all existing and loader tests pass.
- `uv run python load_seed.py` -- expected: successful local database initialization.
- `uv run python -c "..."` or an equivalent test assertion -- expected: tables and columns match both CSV headers and repeated runs have identical contents.
