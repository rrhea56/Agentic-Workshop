---
id: SPEC-epic-1
companions: [../../../seed/tickets.csv, ../../../seed/customers.csv, ../../../mcp/triage_server.py]
sources: [../../../INTENT.md]
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Epic 1: triage data and schema

## Why

The triage workflow needs a stable decision contract and repeatable local data before an agent or evaluation can be built. This epic establishes the validated JSON shape for decisions and loads the read-only seed data into the SQLite database already used by the triage server.

## Capabilities

- **CAP-1**
  - **intent:** The system can accept only triage decisions that contain a supported category, priority, route, and one-sentence rationale.
  - **success:** A valid decision is a JSON object with category `billing`, `bug`, `access`, `performance`, or `how-to`; priority `P1`, `P2`, `P3`, or `P4`; the matching route `billing-team`, `bug-team`, `access-team`, `performance-team`, or `how-to-team`; and a one-sentence rationale. Any other shape is rejected with a clear error.

- **CAP-2**
  - **intent:** A person can initialize a deterministic local database containing the ticket and customer seed data.
  - **success:** `uv run python load_seed.py` loads `seed/tickets.csv` and `seed/customers.csv` into `app.db` tables named `tickets` and `customers`, preserving each CSV's columns. Running the command twice produces the same database.

## Constraints

- Python 3.12 or newer is required, and the project is managed with uv.
- Every file under `seed/` is read-only.
- This epic makes no network calls and uses no API keys.
- `mcp/triage_server.py` already reads `app.db`; its required table and column names must continue working.

## Non-goals

- The agent and MCP tool implementation.
- Evaluation workflows.
- Any user interface.

## Success signal

The decision contract rejects malformed or unsupported triage output with a clear error, while valid output has the five allowed categories, four priorities, matching route, and one-sentence rationale. Running `uv run python load_seed.py` twice leaves a deterministic `app.db` with `tickets` and `customers` tables that `mcp/triage_server.py` can read.
