# Concept: ContextSafe Rule Workshop

**English** · [Deutsch](concept.de.md)

How domain experts can create, change, maintain and *own* business logic without a central data team, and what the PoC needed to change for that.

---

## Executive summary

1. **Core idea:** the domain expert certifies **decisions**, not code. They write the rule in words and decide the edge cases. The SQL is a compiled artifact that a machine proves against those decisions.
2. **Why this removes the bottleneck:** in the PoC the approver had to read SQL, enter hashes and maintain YAML. Only IT can do that. Deciding edge cases can only be done by the business side, and that is where the accountability sits.
3. **What it replaces:** code review becomes edge-case tests, test coverage becomes mutation probes, deployment becomes a seal, change management becomes a broken seal with an impact preview.
4. **What remains:** IT provides the platform once (read-only access, glossary, engine). It is no longer needed per rule.
5. **Status:** MVP running with three rules on two data sources, including the original TPC-H use case on PostgreSQL. See [Evidence and limits](#evidence-and-limits).

## The problem behind the paradigm

"As soon as code exists, IT is needed" holds because four things hang on the code. A domain expert can do none of them while the object under review is code.

| What hangs on the code | In the PoC | Why it excludes the business side |
|---|---|---|
| Writing | Claude generates the SQL | solved, but not sufficient |
| Reviewing | A human reads the SQL (four-eyes) | a domain expert cannot judge SQL |
| Approving | SHA-256 entered by hand into front matter | terminal, YAML, 6 skill hashes |
| Operating | Hash gates over 6 skills | 17 aborted runs from hash drift (2026-06 to 2026-10), fixable only by IT (see [lessons learned](../../docs/lessons-learned.md)) |

## The chain of proof

Every step has exactly one responsible party. Only what is afterwards proven is allowed to be probabilistic.

| # | Step | Who | Kind | What it replaces |
|---|---|---|---|---|
| 1 | Rule in plain language | domain expert | human | functional spec |
| 2 | Decide edge cases | domain expert, Claude proposes | human | acceptance criteria |
| 3 | Compiled SQL and sample data | Claude | probabilistic | development |
| 4 | Proof: compiled SQL against every edge case | engine | deterministic | code review, tests |
| 5 | Mutation probes: where does no edge case fix the rule? | engine | deterministic | test coverage |
| 6 | Back-translation of the SQL into everyday language | Claude, fresh context | probabilistic | second pair of eyes |
| 7 | Effect on real data, totals only | engine | deterministic | acceptance test |
| 8 | Approval by dialog outside the chat | domain expert | human | deployment |
| 9 | Execution only with a valid seal, with a run log | engine | deterministic | operations |

## Four mechanics that carry it

### 1. Shadow tables: same code, same database, different data

- For each edge case the engine puts that case's sample rows in front of the SQL as common table expressions named like the real tables. The query then sees only the sample world.
- The tested text is exactly the text that runs later, on the same database, with read-only access. No test schema, no second SQL dialect.
- Invented tables or columns are caught immediately, because the engine knows the real data catalog.

### 2. Mutation probes: the machine finds the question nobody asked

- The engine deliberately corrupts the SQL (`>=` to `>`, AND to OR, number ±1, text value, negation, distinct counting).
- If no edge case notices the corruption, the rule is not pinned down at that point. That becomes a question for the owner.
- Example from the MVP: for the rule *Upselling candidate*, six edge cases left two things open: which number is shown for a customer with several subscriptions to the same product, and how the join to the product table behaves. The probes found both.
- The owner either decides (new edge case) or leaves the gap open on purpose, with a reason and their name. Not deciding is documented too.

### 3. A seal over the business content

- The hash covers question, plain-language rule, parameters, edge cases, sample data, deliberately open gaps, the SQL, and the seals of the rules it uses.
- It is computed from the parsed content, not from the file text. Reformatted tables do not break it; a changed decision does.
- The `status` field is display only. The engine recomputes the seal before every run.
- If a rule that others build on changes, the approval of all dependent rules is suspended.

### 4. Approval through a channel the AI cannot operate

- `regel_freigeben` opens a macOS dialog. Without a human click there is no seal.
- Only the registered owner may approve, and only if the proof passed.
- Every version is kept read-only under `Protokoll/Freigaben/`.

## What changes compared with the PoC

| Finding (see [ROADMAP](../../ROADMAP.md), item R) | Answer in the Rule Workshop |
|---|---|
| S1/S2: revenue defined three times, rounding duplicated in skills | One place: the compiled SQL of the rule. Rounding is an edge case (G6 of the TPC-H rule) |
| "The hash certifies self-consistency, not intent" | A seal exists only if the SQL satisfies the edge cases |
| S3/S4: sequence lives in the prompt, orchestrator not hashed | The sequence lives in the engine (code with tests). Skills only drive the conversation |
| S5: error logging not anchored everywhere | The engine logs every run, including every refusal |
| Skill hash drift, 17 aborts | Skills are no longer in the *execution* trust path and need no hashes. They remain part of *authoring*, whose output a human still approves |
| S7: trust anchor not named | Still open: a hash, not a signature (see limits) |

The PoC itself is unchanged. These rows describe how the new design handles the same weaknesses for new use cases; they do not close the findings for the original pipeline.

The ContextSafe principle stays and is now enforced instead of requested: the MCP server offers no free SQL.

| Tool | SQL | Data | Returns |
|---|---|---|---|
| `regel_pruefen` | draft | sample data only | passed or not |
| `regel_wirkung` | draft | real, read-only | totals only |
| `regel_ausfuehren` | sealed only | real, read-only | result per rule, capped |

## Technology mapping

| Building block | Role | In the MVP |
|---|---|---|
| Obsidian note | System of record per rule | `Regeln/*.md` |
| Obsidian properties | State, owner, version | front matter, kept flat |
| Obsidian Bases | Cockpit over all rules, runs, approvals | `Regel-Cockpit.base` |
| Obsidian graph and links | Dependencies between rules | `nutzt` with a wikilink |
| Claude Skills | Guiding the conversation with the domain expert | `regel-werkstatt`, `regel-ausfuehren` |
| MCP server | The only path to the data | `engine/mcp_server.py` |
| Claude mod | Cockpit pane beside the chat, guard against direct data access | `mod/regel-cockpit` |
| Subagent | Independent back-translation | foreseen in the skill |
| Engine | Proof, seal, execution | `engine/regelwerk.py`, Python standard library only |

## Alternatives considered

| Way | Why not |
|---|---|
| Own rule language with a fixed translator | Rebuilds a semantic layer and needs a data team again for the language |
| Decision tables without code (DMN) | Carries single-case decisions, not joins and measures across tables |
| Domain expert reviews pseudocode | Better than SQL, but still reading instead of proving. Adopted as back-translation |
| A second model grades the SQL | Replaces one estimate by two. No proof |

## Evidence and limits

### What has been exercised

| Area | State |
|---|---|
| Engine: proof, probes, seal, run, impact, dependencies | 15 automated tests, Python 3.9 and 3.14 |
| Three rules against their edge cases | passed on SQLite and PostgreSQL |
| MCP server, five tools | loaded in Claude Desktop (Code tab); list, release and run exercised live |
| Approval dialog | one real approval performed (rule *Aktiver Kunde* v1, 2026-11-11) |
| Guard in the mod | live: a command containing `sqlite3` was refused |
| Skills | recognised and listed; not yet run through with a domain expert |
| Cockpit pane, Bases cockpit in Obsidian | not looked at |
| Cowork, scheduled runs | not tested |

### Limits

| Limit | Consequence | Next stage |
|---|---|---|
| The seal is a hash, not a signature | Anyone with write access and a shell can recompute it | Signature with the owner's key, engine as a service |
| Claude writes the sample data | Wrong data and wrong SQL could agree with each other | Owner reads the sample tables; impact as a third view |
| Probes do not cover sorting, join type or a missing condition | Such errors are caught only by back-translation or impact | More probes |
| One owner, no four-eyes principle | Not enough for regulated rules | Second approver with their own confirmation |
| The demo database is a file in the folder | The guard in the mod is a guard rail, not a vault | Database behind the server, access only there |
| The approval dialog is macOS-only | Elsewhere only the terminal command works | Cross-platform confirmation |
| The rule layer is German | Rule notes, parser headings and skills are German | Language-neutral rule format |

## Relation to the rest of this repository

- The PoC proves that a certified artifact can be executed under governance. The Rule Workshop answers *who creates and owns that artifact*. It touches roadmap items A (cockpit), B (lifecycle assistant), C (collection to draft) and R (consistency backlog) from the side. See [ROADMAP](../../ROADMAP.md), item J.
- The edge-case table is the "editable middle level" between plain language and code; the effect preview is its sample-result check.
- The same states as in the [governance model](../../docs/governance-model.md) apply: draft, review, certified, suspended. The difference is that `certified` is computed from the seal, not typed.
