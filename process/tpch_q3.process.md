---
use_case_id: TPCH-Q3-001
use_case_name: Top 10 Shipping Priorities
version: 0.8.0
status: certified
owner: PoC Author (Use-Case Owner)
created: 2026-03-31
last_modified: 2026-10-25
approved_by: PoC Author (Use-Case Manager)   # PoC limitation: same person as owner
approved_date: 2026-10-25
next_recertification: 2027-04-25
change_log:
  - date: 2026-03-31
    change: "v0.1.0 — Initial draft"
  - date: 2026-04-02
    change: "v0.2.1 — SQL certified, governance controls"
  - date: 2026-04-04
    change: "v0.3.0–v0.5.0 — skill_hashes, admin_recipients, skill_error_log"
  - date: 2026-04-06
    change: "v0.6.0/v0.7.0 — all 6 skills re-hashed, E2E test passed, weekly schedule, status → certified"
  - date: 2026-06-15
    change: "ABORT SKILL-GATE 2 (hash mismatch) → status → suspended; repeated weekly until 2026-10-19 (17 runs)"
  - date: 2026-09-27
    change: "Obsidian MCP migration prepared (3 skills re-hashed)"
  - date: 2026-10-25
    change: "v0.8.0 — drift reviewed, new baseline approved, status suspended → certified"
db_connection_ref: tpch
db_schema: public
db_access_mode: read_only
admin_recipients:
  - admin@example.com
skill_sequence:
  - skill_read_process_md
  - skill_execute_sql_postgres
  - skill_narrativize_result
  - skill_send_html_email
  - skill_log_run_to_obsidian
  - skill_error_log
certified_script: q3_shipping_priority.sql
certified_script_hash: a9e321d99225f11a243b881861a0728b23862b20d6991f3e0099b3c703217cc5
script_certification_date: 2026-04-02
skill_hashes:
  skill_error_log: 961098c00d971e466ac69f0fbc2252851e3809d26eda42c5c3caaada9f92aefd
  skill_execute_sql_postgres: ab073f24760d8473881ea5da3117b644cd8153b251e3f93d11b7bdc0bdfdfd88
  skill_log_run_to_obsidian: 794fb9354b3e757bcba761089248f117aaf46efd6c1cfad8903f9c3c944c7801
  skill_narrativize_result: 983030953c097605a672b8b87f7d225b2ef2ba737b944cd3022d274e2ef9ce3c
  skill_read_process_md: 947fbda0abc3876305ed4ae6f9c3720be881f95ef3dcd05d07f2995c2e2a0e5d
  skill_send_html_email: bf75bbc6899a83c69ff238aec6e5b713116e5e273790acf5ac6e0b12efa097f4   # published (redacted) copy; vault original: de8b95b1…b8d5
skill_hashes_certified_date: 2026-10-25
max_result_rows: 10
output_format: table
email_recipients:
  - business-recipient@example.com
email_subject_template: "[ContextSafe] Top 10 Shipping Priorities — {date}"
schedule_enabled: true
schedule_cron: 5 8 * * 1
schedule_note: "Every Monday 08:05. German public holiday → next working day."
---

# Top 10 Shipping Priorities (TPC-H Query 3)

> English rendering of the certified vault contract. The `change_log` is condensed, and email addresses are replaced with placeholders.

## Business question

Identify the 10 unshipped orders with the highest potential revenue to prioritise shipping decisions: which open orders bring the most revenue if shipped first?

**Business context:** a logistics manager wants to know every week which orders from market segment `BUILDING` matter most for revenue, to allocate shipping capacity.

## Data structure

**Database:** `tpch` (PostgreSQL, Docker). Scale factor: *to be verified* (see [Claims & Evidence](../docs/claims-and-evidence.md) #8).

| Table | TPC-H equivalent | Description |
|-------|------------------|-------------|
| `tpch_customer` | `customer` | Customer master data, market segment |
| `tpch_orders` | `orders` | Order header, order date, ship priority |
| `tpch_lineitems` | `lineitem` | Line items, prices, discounts, ship dates |

## Business rules

- Market segment `BUILDING` · order date < 1995-03-15 · ship date > 1995-03-15
- Revenue: `ROUND(CAST(SUM(l_extendedprice * (1 - l_discount)) AS numeric), 2)`
  > ⚠️ Known divergence: the certified script does not round yet (ROADMAP R, S1).
- Order by revenue DESC, order date ASC · limit 10

## Expected result

| Column | Type | Description |
|--------|------|-------------|
| `o_orderkey` | INTEGER | Order key |
| `revenue` | DECIMAL | Aggregated revenue |
| `o_orderdate` | DATE | Order date |
| `o_shippriority` | INTEGER | Ship priority |

## Notes for the agent

1. Table names: `tpch_customer`, `tpch_orders`, `tpch_lineitems`.
2. Date columns are `varchar` → `CAST(column AS DATE)`.
3. Only these 3 tables are available.
