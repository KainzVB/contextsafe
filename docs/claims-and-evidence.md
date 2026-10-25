# Claims & Evidence

Every claim made in the original project documentation (demo README of 2026-04-08, before/after comparison, index, agent instructions) is checked here against the evidence in run logs, error logs, the contract and the artifacts. Checked on 2026-10-25.

| Verdict | Meaning |
|---------|---------|
| ✅ Supported | Evidence on file |
| ⚠️ Partly | True with a caveat, or not demonstrated in isolation |
| ❌ Not supported | Contradicted by evidence. Rephrase or fix |

---

## Data & determinism

| # | Original claim | Verdict | Evidence / caveat | Defensible wording |
|---|----------------|---------|-------------------|--------------------|
| 1 | "Raw data never leaves the database. Only aggregate results return." | ✅ / ⚠️ | `GROUP BY` + `LIMIT 10` in Postgres; every run log shows 10 rows. **Caveat:** the rows are order-level (`o_orderkey`), aggregated over line items, so they still identify records. On personal data, "aggregate" ≠ anonymous. The schema is visible to the model during exploration. | "Only the certified result set enters the model context (here: 10 aggregated rows)." |
| 2 | "SQL is immutably certified." | ⚠️ | A hash *detects* change and does not *prevent* it. Script and hash sit in the same writable folder, so whoever can edit one can edit both. | "SQL is **tamper-evident**: any change is detected before execution." |
| 3 | "Read-only enforced at DB level." | ✅ | 2026-04-08: `INSERT` rejected with "cannot execute INSERT in a read-only transaction". In addition, a `readonly_user` with SELECT grants only. | Keep. |
| 4 | "Same question → same query → same result." | ✅ | Fixed SQL, deterministic `ORDER BY` with tie-breaker, no `NOW()`/`RANDOM()`. The top-ranked order (`18869634`, revenue 541,426.17) is identical in every run report on file. Where run logs list the full top 10 (6 of 11 runs), the lists are identical. | Keep. |
| 5 | "Haiku at temperature 0 → deterministic output." | ❌ | Temperature 0 *reduces* variance but does not guarantee identical output. **No run on file used Haiku.** All 11 run logs record Sonnet for narration (2026-04-06: "Haiku not available"). | "Narration is explicitly **non-deterministic and not a governance artifact**. The numbers in the report come from the certified result set." |
| 5b | "Haiku for narration: cost-efficient." | ❌ | Never executed (see #5). The CoWork environment offers no separate Haiku call. | "Narration model: configurable. A small model is planned (→ ROADMAP R11, I)." |
| 6 | "Certified once, so no drift." (before/after) | ❌ | Unexplained drift in 2 skills, detected on 2026-06-15. | "Drift is **detected and blocked**, not prevented." |
| 7 | "The certified artifact is the contract." | ❌ | Review v1, S1: the contract requires `ROUND(CAST(… AS numeric), 2)`, while the certified SQL does not round. *Revenue* is defined in 3 places. | Fix S1, then keep. |
| 8 | Data foundation "~SF1, ~1.5M orders, lineitem 4.1 GB" | ⚠️ | Inconsistent: the result contains `o_orderkey` 28,708,865. In TPC-H the max order key is SF × 6,000,000, so SF ≥ 5 (≈ 7.5M orders). 4.1 GB also fits SF5 better than SF1. | Verify with `SELECT COUNT(*) FROM tpch_orders`, then state the actual scale factor. |
| 9 | "Which 10 order clusters (shipping priorities) …" | ❌ | The query returns 10 **individual unshipped orders** ranked by revenue. `o_shippriority` is 0 for all of them. | "The 10 unshipped orders with the highest revenue …" |

## Governance

| # | Original claim | Verdict | Evidence / caveat | Defensible wording |
|---|----------------|---------|-------------------|--------------------|
| 10 | "Pre-flight verifies 6× SHA-256 (SQL + skills)." | ⚠️ | Pre-flight checks the 6 skills. The SQL is checked in Step 1, Gate 8. That makes 7 hashes in total. | "7 artifacts hash-pinned: 6 skills (pre-flight) + 1 SQL script (gate 8)." |
| 11 | "Mismatch → abort + automatic suspension." | ✅ | 17 aborts from 2026-06-15 to 2026-10-19, each with an error log, an admin email, `status: suspended` and a change-log entry. | Keep. This is the strongest evidence in the project. |
| 12 | "Automatic suspension when recertification is overdue." | ⚠️ | Gate 4 exists (`next_recertification >= today`). It was never triggered on its own: when the date passed (2026-10-02), the process was already suspended. | "Gate implemented. Not yet demonstrated in isolation." |
| 13 | "Owner/approver separation, never the same person; architecturally anchored." | ❌ | Owner and approver are the same person. Gates 2 and 3 only check that the fields are *present*. | "Roles are modelled. Separation is **not yet enforced** (single-person PoC)." → ROADMAP R8 |
| 14 | "Every run is fully auditable." | ⚠️ | A log exists for every run and every abort. **But:** the logs are written by the orchestrating LLM, so the hash checks are self-reported. The orchestrator context is not hashed (S4), and the contract has no trust anchor (S7). | "Every run and abort leaves a log. Independent verification is available via `scripts/verify.sh` and planned via OTel (F)." |
| 15 | "Git versioning of the entire vault." | ⚠️ | The backup covers text files only. Backup commits failed from 2026-03-18 to September (local toolchain licence lock). Skills first appear in history on 2026-09-27, so the certified April versions are lost. | "Automated git backup every 10 min (complete since 2026-09-27)." |
| 16 | "Status change only via MCP/source mode, four-eyes principle." | ⚠️ | Convention, not enforced. Meta-Bind widgets write directly to the frontmatter, and anyone with vault access can edit it. | "Status changes are recorded in `change_log`." |

## Operations

| # | Original claim | Verdict | Evidence / caveat | Defensible wording |
|---|----------------|---------|-------------------|--------------------|
| 17 | "Live: runs automatically every Monday 08:05." | ⚠️ | 10 successful runs from 2026-04-02 to 2026-06-08, then 17 weeks of aborts. Resumed 2026-10-25, on a Sunday, outside the schedule. | "Weekly schedule. 10 successful runs, then 17 correctly blocked runs, resumed after re-certification." |
| 18 | "Scheduling is native in the Process Contract." | ⚠️ | `schedule_cron` is declarative. The actual trigger is a CoWork scheduled task, and the contract does not drive it. | "Schedule declared in the contract, executed by the orchestrator." |
| 19 | "Error handling: abort persisted + admin alert." | ✅ / ⚠️ | Persisted and alerted 17 times. **But** there was no escalation: alerts went to the same inbox for 18 weeks. | Keep, and add an escalation path (R9). |
| 20 | "Minimal token usage." | ⚠️ | Plausible, since only 10 rows enter the context. **Not measured.** | "Context limited to the result set." Or measure it and report the number. |

## Compliance

| # | Original claim | Verdict | Evidence / caveat | Defensible wording |
|---|----------------|---------|-------------------|--------------------|
| 21 | "EU AI Act requirements addressed structurally (Art. 9, 12, 13, 14, 17)." | ⚠️ | The mapping is consistent and concrete. **But:** these articles are obligations for *high-risk* AI systems (Annex III), and a shipping-priority report is not one. Art. 17 (QMS) is a provider obligation. Art. 12 expects automatic logging by the system, and LLM-written logs are a weaker form of that. | "Designed to **align with** the logging, transparency and human-oversight principles of the EU AI Act. Not a conformity claim." |

---

## Summary

- **Strong and proven:** context minimisation, read-only execution, deterministic SQL, fail-closed hash gates (17 correct aborts), auditable change log.
- **Overstated:** immutability, owner/approver separation, deterministic narration, "no drift", completeness of the git history, EU AI Act "compliance".
- **To fix in the data:** scale factor, the description of Query 3, and the definition of the revenue metric.
