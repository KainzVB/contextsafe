# Roadmap

Development items from the project's idea log (started 2026-04-07), plus the consistency backlog from Architecture Review v1 (2026-05-14) and the recommendation from the 2026-10-25 assessment.

Legend: ✅ done · 🟡 partly done · ⏳ open · 💡 idea (not yet spec-ready)

---

## Overview

| ID | Item | Proposed | Status | Depends on |
|----|------|----------|--------|------------|
| **E** | Pre-flight integrity of the instruction base | 2026-04-07 | 🟡 skill hashes done (2026-04-04); commit-anchored verification open | — |
| **A** | Process Governance Dashboard + Frontmatter Store | 2026-04-07 | 💡 | E |
| **B** | Lifecycle Assistant (guided setup + recertification) | 2026-04-07 | 💡 | A |
| **C** | Use-case collection → research → draft architecture | 2026-04-07 | 💡 | A (status tracking) |
| **F** | OpenTelemetry correlation (agent telemetry ↔ run logs) | 2026-04-27 | 💡 | — |
| **G** | Skill threat self-assessment (ToxicSkills categories) | 2026-04-27 | ⏳ | — |
| **H** | MCP connector migration + tool abstraction layer | 2026-09-27 | 🟡 migration ✅ 2026-09-27, re-certified 2026-10-25; abstraction layer open | — |
| **I** | Deterministic orchestrator (LLM as a single step) | 2026-10-25 | ⏳ spike proposed | E, G |
| **J** | Rule Workshop (self-service rule authoring) | 2026-11-11 | 🟡 MVP 2026-11-11, published 2026-11-20 | — |
| **R** | Consistency backlog from Architecture Review v1 | 2026-05-14 | ⏳ S1–S7 open | — |

> There is no item D in the original idea log.

**Suggested order:** R (quick wins) → E → I → G → A → F → C → B

---

## E: Pre-flight integrity of the instruction base
*Proposed 2026-04-07*

**Goal:** before every run, prove that *everything* the agent is instructed by is the certified version. That covers the skills, the orchestrator context and the Process Contract itself.

- ✅ 2026-04-04: SHA-256 per `SKILL.md`, pinned in `skill_hashes`, checked in pre-flight (SKILL-GATE 2).
- ⏳ Pin the certified state to a **git commit hash** in the contract and verify it at pre-flight.
- ⏳ Include the orchestrator (`cowork/CLAUDE.md`) and the contract itself in the hash regime (Review findings S4, S7).
- ⏳ Use `stat.mtime` from the vault API as an extra gate: was the contract modified after certification?

**Why it matters:** the 2026-06-15 drift was *detected* but could not be *explained*, because no certified copy existed in version control. See [lessons learned](docs/lessons-learned.md).

---

## A: Process Governance Dashboard + Frontmatter Store
*Proposed 2026-04-07*

- Web app with the status of all Process Contracts (in review, scheduled, recertification due, suspended).
- Structured contract fields (`status`, `approved_by`, hashes, dates) move to a permissioned database as the *single source of truth* for machine logic. Markdown remains the human-readable document.
- Approval triggers and relative recertification dates (e.g. `+6 months` after approval).

**Open:** which database, how to sync it with the vault, who may write which field.

---

## B: Lifecycle Assistant
*Proposed 2026-04-07*

A guided but escape-capable assistant workflow for first-time setup and recertification of a use case. It walks owner and approver through contract, artifact, hashing, diff review and sign-off. The assistant guides, and the human decides.

---

## C: Use-case collection → research → draft architecture
*Proposed 2026-04-07*

Three phases, each human-in-the-loop:

1. **Collection:** structured interview of domain experts. Output: use-case card.
2. **Research:** AI-assisted synthesis, producing a review document with status "to review".
3. **Draft architecture:** which skills, which order, which data flows. This phase can also be triggered on its own as a final check before deployment.

---

## F: OpenTelemetry correlation
*Proposed 2026-04-27, derived from the policy-enforcement research (reference spec 12)*

Correlate agent runtime telemetry (tool calls, file touches) with ContextSafe run logs through a shared run ID. The run log then holds independent evidence instead of the agent's self-report.

**Open:** DLP and redaction at the collector (prompt content is included in the stream by default), retention, and the available telemetry surface.

---

## G: Skill threat self-assessment
*Proposed 2026-04-27*

Assess the project's own six `SKILL.md` files against published agent-skill threat categories (e.g. prompt injection surface, excessive permissions, hidden instructions, data exfiltration paths). Record the result as `threat_assessment_date` in the contract.

Since 2026-09-27, also covers **connector maintenance status** as a supply-chain risk: an archived community MCP plugin silently broke the pipeline.

---

## H: MCP connector migration + tool abstraction
*Proposed and executed 2026-09-27*

- ✅ The Obsidian connector was replaced (archived `obsidian-mcp-tools` → built-in MCP of Local REST API). 8 files were migrated and 3 skills re-hashed.
- ✅ 2026-10-25: re-certification (contract `v0.8.0`) and a successful run.
- ⏳ **Tool abstraction layer:** skills reference capabilities (`read_document`, `write_log`) and not connector-specific tool names. A connector swap then touches one mapping file instead of eight certified artifacts.

---

## I: Deterministic orchestrator
*Proposed 2026-10-25*

**Problem:** today an LLM (CoWork) orchestrates a deterministic pipeline and reports its own hash checks. The 2026-10-25 run also showed:
- a model substitution (Sonnet instead of Haiku),
- an off-schedule execution (Sunday instead of Monday).

**Proposal:** move scheduling, gates, hashing, SQL execution, delivery and logging into a deterministic workflow engine (e.g. n8n). The LLM becomes a single, sandboxed step that only narrates the result rows. Process Contract, hashes and approver stay unchanged as the governance layer.

**Done when:** pre-flight pass and a deliberately provoked mismatch-abort both run without an LLM in the control path.

---

## J: Rule Workshop (self-service rule authoring)
*Proposed and prototyped 2026-11-11*

**Problem:** the PoC certifies a script that IT wrote. The business rules live in the heads of domain experts, who can neither write nor review code. As long as the certified object is code, a central data team stays in the loop for every rule.

**Approach:** certify the **decisions**, not the code. The expert writes the rule in plain language and decides edge cases. Claude writes sample data and SQL. A deterministic engine proves the SQL against every edge case, finds undecided questions with mutation probes, and seals the content after a human approval. Only sealed rules run. See the [concept](rule-workshop/docs/concept.md).

- ✅ MVP in [`rule-workshop/`](rule-workshop/README.md): engine, MCP server (5 tools), 2 skills, Obsidian Bases cockpit, Claude mod, 3 rules, 15 tests.
- ✅ One real approval and four logged runs (2026-11-11 to 2026-11-17).
- ⏳ Run through the skills with a domain expert who has not seen the system.
- ⏳ Signature instead of hash; second approver; cross-platform approval dialog; language-neutral rule format; more mutation probes (sorting, join type, missing conditions).
- ⏳ Scheduled execution of sealed rules (shares the open question of item I).

**Relation to other items:** touches A (cockpit), B (lifecycle assistant), C (collection to draft) and R (S1/S2/S3/S5 are handled by design for new use cases; the findings for the original pipeline stay open).

**Done when:** a domain expert creates, changes and releases a rule in one session without help from IT, and a deliberately wrong edge case is caught before release.

---

## R: Consistency backlog (Architecture Review v1, 2026-05-14)

Overall maturity in review v1: **Level 2, transitioning to 3.** Governance scaffolding reached L3–L4. The semantic layer was at L1–L2.

| ID | Severity | Finding | Action |
|----|----------|---------|--------|
| S1 | high | The *revenue* metric is defined in 3 places and diverges: the certified SQL has no `ROUND`, while the contract requires it | Consolidate the metric into the certified SQL (requires script re-certification) |
| S2 | high | Rounding logic is duplicated in two skills | Remove it once S1 is fixed |
| S3 | medium | `skill_sequence` in the contract is decorative, because the real order is hard-coded in the orchestrator | Make it authoritative or remove it |
| S4 | medium | The orchestrator context is not hashed | Add it to the hash regime (→ E) |
| S5 | medium | Error logging is anchored asymmetrically across skills | Anchor `skill_error_log` in every aborting skill |
| S6 | low | Stale specs | Partly fixed 2026-10-25 (index and instructions updated) |
| S7 | low | The Process Contract has no trust anchor | Document git as the anchor or hash the contract (→ E) |

Added 2026-10-25:

| ID | Finding | Action |
|----|---------|--------|
| R8 | Owner and approver are the same person; no gate enforces separation | Add a gate `owner != approved_by` (warn in single-person PoC mode) |
| R9 | 17 consecutive aborts without escalation | After 2 aborts in a row: pause the schedule and alert through a second channel |
| R10 | Hashes are stored next to the files they protect | Store hashes or signatures outside the writable area (signing → E) |
| R11 | Narration model is not enforced: all 11 runs used Sonnet instead of the designed Haiku | Fail the step or flag the report when the configured model is unavailable |
