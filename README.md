# ContextSafe

**English** · [Deutsch](README.de.md)

**Deterministic, governed data processing with LLM agents (Claude + MCP + Agent Skills).**

> The model interprets. A certified, deterministic artifact computes. A human approves. Every run leaves evidence.

ContextSafe is a proof of concept (PoC) that answers one question:

> *How can an LLM agent work with enterprise data without raw data entering the model context, and with every run being reproducible, tamper-evident and auditable?*

> **New (2026-11):** the [Rule Workshop](rule-workshop/README.md), an MVP that addresses the open question behind this PoC: who creates and owns the certified artifact? The answer: the domain expert, who decides edge cases instead of reading code.

---

## Scope

| In scope | Out of scope |
|----------|--------------|
| Recurring, decision-support questions over structured data | Ad-hoc, open-ended data exploration ("chat with your data") |
| A **certified** computation artifact (here: one SQL script) | LLM-generated SQL at runtime |
| Governance contract per use case (Process Contract, Markdown + YAML) | Production IAM, secrets management, multi-tenant RBAC |
| Integrity gates (SHA-256) for SQL **and** agent skills | Cryptographic signing / PKI (see [ROADMAP](ROADMAP.md), H/I) |
| Human-in-the-loop certification and recertification | Autonomous decisions or write-back into operational systems |
| Run logs, error logs, change log as audit trail | Formal EU AI Act conformity assessment |

**Reference use case:** TPC-H Query 3, "Top 10 Shipping Priorities": the 10 unshipped orders with the highest revenue in market segment `BUILDING` (cut-off date 1995-03-15), delivered weekly as an HTML email report.

**Status (2026-10-25):** PoC complete. Process contract `v0.8.0` re-certified, last run successful. See [CHANGELOG](CHANGELOG.md) for the full dated history, including a 17-week outage that the integrity gate correctly caused.

---

## Core principle

```
Naive:        User → LLM → ad-hoc SQL → DB → thousands of raw rows → LLM context

ContextSafe:  Explore schema once → codify → certify (hash + approver)
              → execute certified artifact (read-only) → only the result set → LLM
```

Three properties the PoC demonstrates. Each one is graded honestly in [Claims & Evidence](docs/claims-and-evidence.md):

1. **Context minimisation:** only the certified result set (here: 10 aggregated rows) enters the model context.
2. **Tamper evidence:** SQL and all six skills are pinned by SHA-256 in the Process Contract. A mismatch aborts the run and suspends the process.
3. **Auditability:** every run and every abort writes a log. Every change to the contract is recorded in its `change_log`.

---

## The holistic approach: a lifecycle, not a tool

ContextSafe is less a piece of software than a **lifecycle pattern** that applies to almost any recurring, data-driven use case:

```
 1. EXPLORE      LLM sees schema/metadata only, never data
 2. CODIFY       Computation becomes a deterministic artifact
                 (SQL, dbt model, Python, Alteryx workflow, API call)
 3. CONTRACT     A human-readable Process Contract binds artifact, skills,
                 roles, recipients, schedule and hashes
 4. CERTIFY      Hash every executable piece; a human approver signs off
 5. EXECUTE      Gates first (fail closed), then run read-only; the LLM only
                 narrates the result
 6. EVIDENCE     Run log, error log, change log, versioned history
 7. RECERTIFY    Expiry date, drift detection, diff review before re-hashing
```

The same seven steps work whether the artifact is a SQL query, a forecast notebook, a document-extraction pipeline or a KPI report. The LLM moves to the edges, to exploration and narration, and the deterministic core stays certifiable. See [Applying ContextSafe to other use cases](docs/applying-to-other-use-cases.md), which also covers where the pattern does **not** fit.

---

## Repository layout

```
contextsafe/
├── README.md, README.de.md            ← this file (scope, principle, approach), English and German
├── ROADMAP.md                         ← development items A–J with dates and status
├── CHANGELOG.md                       ← dated project timeline
├── LICENSE                            ← MIT
├── docs/
│   ├── architecture.md                ← contexts, pipeline, data path
│   ├── governance-model.md            ← Process Contract, lifecycle, gates, roles, EU AI Act alignment
│   ├── claims-and-evidence.md         ← every claim, graded against evidence
│   ├── lessons-learned.md             ← 2026-06-15 → 2026-10-19 outage post-mortem
│   └── applying-to-other-use-cases.md ← generalisation + limits
├── process/
│   ├── process-contract.template.md   ← template for new use cases
│   └── tpch_q3.process.md             ← reference contract (EN, PII replaced)
├── sql/q3_shipping_priority.sql       ← certified script (hash identical to the original)
├── skills/                            ← 6 Agent Skills (SKILL.md, German originals)
├── hashes/SHA256SUMS                  ← hashes of all certified artifacts in this repo
├── scripts/verify.sh                  ← deterministic pre-flight (no LLM involved)
└── rule-workshop/                     ← Rule Workshop (MVP): domain experts create and own rules
```

> **Language note:** the six `SKILL.md` files are published in their original German. Translating them would change their hashes and invalidate the certification chain. All other content is English; the main documents also exist in German.
>
> **Redaction note:** one example email address in `skills/skill_send_html_email/SKILL.md` was replaced with `example.com`. That file's hash therefore differs from the vault original (`de8b95b1…b8d5` → `bf75bbc6…97f4`). `hashes/SHA256SUMS` and the reference contract use the published value.

---

## Quick start: verify the certification chain

```bash
./scripts/verify.sh process/tpch_q3.process.md
```

The script recomputes every SHA-256, compares it with the Process Contract and checks status and recertification date. It is deterministic and runs without an LLM. It also closes a gap the PoC itself had: there, the orchestrating LLM reported its own hash checks.

---

## Technology (reference implementation)

| Concern | Choice |
|---------|--------|
| Development / specs | Claude.ai Chat |
| Certification (hashing, SQL generation) | Claude Code (`shasum -a 256`) |
| Orchestration | Claude CoWork (Sonnet), scheduled weekly |
| Narration | Designed for Claude Haiku. In practice, every run so far used Sonnet (Haiku not available in CoWork) |
| Database | PostgreSQL (Docker), TPC-H data, `@sarmadparvez/postgresql-mcp` with `?mode=readonly` |
| Contract + logs | Obsidian vault (Markdown + YAML, Meta-Bind widgets), Local REST API MCP |
| Delivery | Gmail MCP |
| Versioning | Automated git backup of the vault (every 10 min) |

---

## Positioning (as of 2026-10)

- **Agent Skills are not the novelty.** Anthropic introduced them in October 2025, and "build skills, not agents" was Anthropic's own message in late 2025. ContextSafe started in March 2026 and *uses* skills.
- **The novelty is treating skills as certified, hash-pinned artifacts** inside a governance lifecycle: fail-closed gates, approver, recertification, audit trail. In late 2025 the open questions were versioning, dependency management and runtime predictability. Industry checklists (e.g. OWASP Agentic Skills Top 10) now ask for exactly this: pin content by hash, re-verify on load, refuse on change.
- **The pattern is mainstream in data platforms:** Snowflake *verified queries* and Databricks Genie *trusted assets* also let an LLM pick from pre-approved, deterministic queries. ContextSafe applies the same idea one level up, to the agent's own instructions.
- **Honest limitation:** for a fixed weekly report, a deterministic workflow engine (e.g. n8n, Alteryx Server) with a single LLM step for narration is simpler and more reliable than an LLM orchestrator. See [ROADMAP](ROADMAP.md) item **I**.

---

## Author

Christian Kainzmeier. Built with Claude (Chat, Code, CoWork).

License: [MIT](LICENSE). Free to use, modify and redistribute.
