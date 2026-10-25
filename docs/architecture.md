# Architecture

## Three contexts, three responsibilities

```
┌────────────────────────────────────────────────────────────┐
│ DEVELOPMENT        Claude.ai Chat                          │
│ Explore schema (metadata only) → write specs and skills    │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│ CERTIFICATION      Claude Code + human approver            │
│ Generate SQL → SHA-256 for SQL and skills → diff report    │
│ → approver enters hashes in the Process Contract           │
└────────────────────────────────────────────────────────────┘
                              ↓
┌────────────────────────────────────────────────────────────┐
│ EXECUTION          Claude CoWork (scheduled)               │
│ Pre-flight → Steps 1–5 → logs; skill_error_log on abort    │
└────────────────────────────────────────────────────────────┘
```

Claude Code never connects to the database and never sends email. The execution context never generates SQL.

## Pipeline

| Step | Skill | Responsibility | On failure |
|------|-------|----------------|------------|
| Pre-flight | — | Verify SHA-256 of all 6 `SKILL.md` against `skill_hashes`; certified date set | **ABORT** → `skill_error_log`, status → `suspended` |
| 1 | `skill_read_process_md` | Load the contract, run 8 gates, build `execution_context` | **ABORT** → `skill_error_log` |
| 2 | `skill_execute_sql_postgres` | Run the certified SQL read-only via MCP and return the result set only | **ABORT** → `skill_error_log` |
| 3 | `skill_narrativize_result` | Write the HTML report and a short narrative | Fallback: report without narrative |
| 4 | `skill_send_html_email` | Send the report to `email_recipients` from the contract | Recorded in `email_context`, run continues |
| 5 | `skill_log_run_to_obsidian` | Write the run log with the full context. **Always runs** | Plain-text fallback |

### The 8 gates of Step 1

1. `status == certified`
2. `owner` set
3. `approved_by` set
4. `next_recertification >= today` (fail → `suspended`)
5. `db_access_mode == read_only`
6. `certified_script_hash` set
7. Script file readable
8. `SHA-256(script) == certified_script_hash` (fail → `suspended`)

## Data path

```
Postgres (tpch, read-only session)
   │  certified SQL: GROUP BY + ORDER BY + LIMIT 10
   ▼
10 result rows ──► execution_context ──► narration ──► HTML report ──► email
                         │
                         └────────────► run log (vault)
```

The model context never contains more than the result set and the contract.

## Context hand-over

| Context | Produced by | Contents |
|---------|-------------|----------|
| `execution_context` | Step 1, extended by Step 2 | use case, script + hash, recipients, approver, version, gates passed, `rows`, `row_count`, timestamp |
| `narrative_context` | Step 3 | `html_report`, `narrative_text`, `fallback_used` |
| `email_context` | Step 4 | `email_sent`, timestamp, error |
| `error_context` | any abort | step, gate, reason, timestamp, `status_set_to_suspended` |

## SQL determinism rules

1. No `SELECT *`
2. Explicit `INNER JOIN … ON`
3. Deterministic `ORDER BY` with tie-breaker
4. Explicit `LIMIT`
5. No `NOW()`, `RANDOM()`, `CURRENT_TIMESTAMP`
6. `SELECT` only
7. Parameters documented in a header comment
8. Exact table names
9. Explicit `CAST(… AS DATE)` for date columns stored as `varchar`
10. `ROUND(CAST(… AS numeric), 2)` for monetary values. **Not yet applied in the certified script** (ROADMAP R, S1)

## Connectors

| Connector | Tools used | Mode |
|-----------|-----------|------|
| PostgreSQL (`@sarmadparvez/postgresql-mcp`) | `list_tables`, `schema`, `query` | `?mode=readonly` → `SET TRANSACTION READ ONLY` |
| Obsidian (Local REST API MCP) | `vault_read`, `vault_write`, `vault_list` | `vault_list` before every write (no overwrite) |
| Gmail MCP | `send_email` | Recipients only from the contract |
