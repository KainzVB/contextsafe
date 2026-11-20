# Changelog: project timeline

All dates are ISO 8601. "Contract" refers to the Process Contract of use case `TPCH-Q3-001`.

## 2026-11-20: Rule Workshop MVP published (roadmap item J)
- New folder [`rule-workshop/`](rule-workshop/README.md), built 2026-11-11: domain experts write rules in plain language and decide edge cases; Claude proposes sample data and SQL; a deterministic engine proves the SQL against the edge cases, finds undecided questions with mutation probes, seals the content after a human approval dialog and runs only sealed rules.
- Three rules on two data sources (SQLite demo data, PostgreSQL TPC-H). One rule is sealed (*Aktiver Kunde* v1, approved 2026-11-11). Four runs are logged: three successful, one refused before the approval.
- Exercised: 15 automated tests (Python 3.9 and 3.14), MCP server and guard mod loaded in Claude Desktop, one real approval. Not yet exercised: the skills with a domain expert, the cockpit pane and the Obsidian Bases view, scheduled runs. See [concept](rule-workshop/docs/concept.md#evidence-and-limits).
- The root README is now available in German ([README.de.md](README.de.md)); English stays the default. The PoC itself is unchanged.

## 2026-10-25: Re-certification (contract v0.8.0)
- The drift in `skill_read_process_md` and `skill_send_html_email` was reviewed. The current content was approved as the new baseline; the cause of the drift cannot be reconstructed.
- `skill_hashes` updated for 4 skills, `skill_hashes_certified_date` set, next recertification set to 2027-04-25.
- Status `suspended` → `certified`.
- Run `run_20261025_001`: success (8/8 gates, pre-flight 6/6). Deviations: Sonnet narrated instead of Haiku, as in every run since April, and the run executed on a Sunday.
- Documentation brought up to date. Assessment against current market practice added. Item I (deterministic orchestrator) proposed.

## 2026-09-27: Connector migration (roadmap item H)
- The Obsidian MCP connector was replaced: the archived community plugin had returned 404 for every file in a subfolder.
- Tool calls migrated to `vault_read` / `vault_write` / `vault_list` in 3 skills, the orchestrator and 3 specs. Change package prepared for the approver.
- The automated git backup now versions all skills. Before this date, no certified skill version existed in history.

## 2026-06-15 → 2026-10-19: Outage (17 aborted runs)
- Every scheduled run aborted at pre-flight SKILL-GATE 2: the hashes of 2 skills, from 2026-09-28 of 4, no longer matched the certified values.
- Status automatically set to `suspended`. An error log and an admin email were written every week.
- No human reaction for 18 weeks. See [lessons learned](docs/lessons-learned.md).

## 2026-05-14: Architecture Review v1
- Reusable review harness (reference spec 13).
- Maturity Level 2 → 3. Findings S1–S7 (see [ROADMAP](ROADMAP.md), item R).

## 2026-04-27: Policy enforcement landscape
- Reference spec 12: runtime policy enforcement across 5 layers, threat mapping, EU AI Act.
- Roadmap items F (OTel correlation) and G (skill threat self-assessment) added.

## 2026-04-06 → 2026-06-08: Weekly production runs
- 10 successful runs on file (2026-04-02, 04-06 ×2, 04-07, 04-14, 04-20, 04-27, 05-04, 05-18, 06-08).

## 2026-04-08: Demo package + read-only proof
- Read-only enforcement verified: `INSERT` rejected with "cannot execute INSERT in a read-only transaction".
- Demo README (DE/EN) and before/after comparison published.

## 2026-04-07: Idea log started
- Items A (dashboard), B (lifecycle assistant), C (collection pipeline) and E (pre-flight integrity) documented.

## 2026-04-06: Contract v0.6.0 / v0.7.0: certified + scheduled
- All 6 skills re-hashed. `skill_error_log` added as the sixth skill.
- First end-to-end test in CoWork successful. Status `certified`. Schedule: every Monday 08:05 (German public holiday → next working day).

## 2026-04-04: Contract v0.3.0 – v0.5.0: skills enter the hash regime
- `skill_hashes` added to the contract; pre-flight skill-hash verification introduced.
- First pre-flight abort on a skill-hash mismatch → `suspended` (the gate works as designed).
- `admin_recipients` and `skill_error_log` added to the sequence.

## 2026-04-02: First certified run
- Schema verified via MCP. SQL generated under determinism rules, hashed and certified.
- First test run `run_20260402_001`: success, 10 rows.

## 2026-03-31: Contract v0.1.0 / v0.2.0
- Initial draft of the Process Contract. Database structure corrected (single DB `tpch`, prefixed table names).
