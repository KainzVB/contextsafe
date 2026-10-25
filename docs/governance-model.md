# Governance Model

## The Process Contract

Each use case has exactly one Process Contract: a Markdown file with YAML frontmatter. It is *human-readable* (approvers review it like a document) and *machine-verifiable* (gates read it before every run).

It binds together:

| Concern | Fields |
|---------|--------|
| Identity | `use_case_id`, `use_case_name`, `version` |
| Lifecycle | `status`, `approved_by`, `approved_date`, `next_recertification`, `change_log` |
| Roles | `owner`, `approved_by` |
| Artifact | `certified_script`, `certified_script_hash`, `script_certification_date` |
| Agent instructions | `skill_sequence`, `skill_hashes`, `skill_hashes_certified_date` |
| Data access | `db_connection_ref`, `db_schema`, `db_access_mode` |
| Output | `max_result_rows`, `output_format`, `email_recipients`, `email_subject_template` |
| Operations | `admin_recipients`, `schedule_enabled`, `schedule_cron` |

Template: [`process/process-contract.template.md`](../process/process-contract.template.md)

## Status lifecycle

```
draft ──► review ──► certified ──► deprecated
                        │  ▲
          gate failure  ▼  │  re-certification (diff review + approver)
                     suspended
```

- **Suspension is automatic:** a hash mismatch at pre-flight or gate 8, or an expired recertification date (gate 4), sets `status: suspended` and appends to `change_log`.
- **Re-certification is manual:** re-hash, diff report, approver review, new hashes entered by hand, status → `certified`.

## Integrity: what is pinned

| Artifact | Pinned by | Checked at |
|----------|-----------|------------|
| SQL script | `certified_script_hash` | Step 1, gate 8 |
| 6 × `SKILL.md` | `skill_hashes` | Pre-flight, SKILL-GATE 2 |
| Orchestrator context | — | **not pinned** (ROADMAP E / S4) |
| Process Contract | — | **no trust anchor** (ROADMAP E / S7) |

## Re-hashing lifecycle

```
SKILL.md changed
  → Claude Code re-hashes and produces a diff report
  → Approver reviews what changed
  → Approver enters the new hashes in the contract
  → change_log entry, status → certified
```

Claude Code computes hashes but never writes them into the contract. That step stays with a human (four-eyes intent; see the limitation below).

## Roles

| Role | Responsibility |
|------|----------------|
| Owner | Business owner of the use case and its question |
| Approver | Reviews diffs, enters hashes, sets status |
| Claude Code | Generates SQL, computes hashes, prepares change packages |
| Orchestrator | Executes; may only *suspend*, never *certify* |

> **Limitation (PoC):** owner and approver are the same person, and no gate enforces separation. See [Claims & Evidence](claims-and-evidence.md) #13, ROADMAP R8.

## EU AI Act alignment

The design follows the *principles* of the articles below. It does **not** claim conformity: the reference use case is not a high-risk system under Annex III, where these obligations apply.

| Article | Principle | ContextSafe mechanism |
|---------|-----------|-----------------------|
| Art. 9: risk management | Identify and mitigate risks | Hash gates, read-only access, suspension, error log |
| Art. 12: record-keeping | Automatic logging over the lifecycle | Run log per execution, error log per abort, `change_log`, git history |
| Art. 13: transparency | Understandable operation | Contract and SQL as readable artifacts; hash in the report footer |
| Art. 14: human oversight | Human can oversee and intervene | Approver sign-off, manual re-certification, admin alert on abort |
| Art. 17: quality management | Documented procedures | Status lifecycle, recertification date, diff review |
