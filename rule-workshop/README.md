# ContextSafe Rule Workshop (MVP)

**English** · [Deutsch](README.de.md)

**Domain experts create, change and own business rules themselves. They decide the edge cases, Claude translates, a deterministic engine proves and seals.**

> Models estimate. A deterministic engine proves. Humans approve. Every run leaves evidence.

The ContextSafe PoC (see the [main README](../README.md)) shows how a *certified* artifact is executed under governance. It leaves one question open: **who creates and owns that artifact?** In practice it was IT, because the artifact is code. The business rules live in the heads of the domain experts, who cannot write or review code.

The Rule Workshop moves what is certified from the code to the **decisions**. The full reasoning is in the [concept](docs/concept.md).

**Status (2026-11-20):** MVP. Three rules on two data sources, one of them sealed. Not production software. See [Evidence and limits](docs/concept.md#evidence-and-limits).

---

## How it works

```
Domain expert     writes the rule in plain language, decides every edge case
Claude            proposes edge cases, writes sample data and the SQL
Engine            proves the SQL against each edge case (shadow tables),
                  corrupts the SQL on purpose to find undecided questions (mutation probes)
Domain expert     sees the effect on real data (totals only) and approves via an OS dialog
Engine            seals the content (SHA-256) and only then executes the rule, with a run log
```

| Property | How it is enforced |
|---|---|
| The AI cannot approve | Approval opens a macOS dialog outside the chat. Only the registered owner may approve |
| The AI cannot run free SQL | The MCP server has no such tool. Real data comes only from sealed rules |
| Edits cannot slip through | The seal covers question, rule text, parameters, edge cases, sample data and SQL. Change one and execution is refused |
| Raw data stays out of the context | Drafts run on sample data or return totals only. Sealed rules return the capped result |
| Every run is evidenced | Each run, and each refusal, writes a log under `Protokoll/Läufe/` |

---

## Quick start

Requirements: Python 3.9 or newer, standard library only. No installation.

```bash
cd rule-workshop
python3 engine/tests/test_regelwerk.py        # 15 tests
python3 engine/regelwerk.py liste             # state of all rules
python3 engine/regelwerk.py pruefen "Upselling-Kandidat"   # proof + open questions
```

The rule *Aktiver Kunde* ships sealed (version 1), so `liste` shows it as `certified`. *Upselling-Kandidat* has two open questions on purpose.

### With Claude

1. Open the `rule-workshop/` folder as the working folder in Claude Code or the Claude Desktop Code tab. `.mcp.json`, `CLAUDE.md` and the two skills load from there.
2. Allow the MCP server `regelwerk`.
3. Try, in this order:

| # | Say | What you see |
|---|---|---|
| 1 | "How many active customers do we have?" | Answer from the sealed rule, with version, owner and run log |
| 2 | In `Regeln/Aktiver Kunde.md`, change the expected value of edge case G3 from `nein` to `ja`, then ask again | Execution is refused: the decision changed since approval |
| 3 | Undo the change with `git checkout -- Regeln/` | The rule runs again |
| 4 | "Let's clear the open questions of Upselling-Kandidat." Enter yourself as `owner` in the note first | Claude turns each gap into a concrete situation for you to decide |
| 5 | "Release Upselling-Kandidat. I am the owner." | A dialog appears on your Mac. Without your click there is no seal |

Without Claude, the owner releases from a terminal: `python3 engine/regelwerk.py freigeben "<rule>" --von "<owner>" --aenderung "<one sentence>"`.

### Optional

- **Obsidian:** open the repository as a vault, or just this folder. `Regel-Cockpit.base` shows all rules, those needing action, due recertifications, runs and approvals (Bases, Obsidian 1.9 or newer).
- **Claude mod:** `claude --plugin-dir mod/regel-cockpit` adds a cockpit pane beside the chat and refuses direct database commands in this folder.
- **TPC-H rule:** *Top 10 Shipping Priorities* needs the PostgreSQL container of the original PoC. Connection settings are in `engine/regelwerk.config.json`. It stays unreachable without that container.
- **Demo data:** `python3 daten/demo_daten_erzeugen.py` rebuilds the SQLite demo database (fixed seed).

---

## The five tools

| Tool | Purpose | Sees real data |
|---|---|---|
| `regel_liste` | Rules and their actual state | no |
| `regel_pruefen` | Proof against edge cases, mutation probes, audit note | no, sample data only |
| `regel_wirkung` | Hit count and difference to the approved version | yes, returns totals only |
| `regel_freigeben` | Seal after confirmation by the owner | no |
| `regel_ausfuehren` | Run of a sealed rule, with log | yes |

---

## Layout

```
rule-workshop/
├── README.md, README.de.md
├── docs/concept.md, concept.de.md      ← the reasoning, alternatives, limits
├── Regeln/                             ← one note per rule: the system of record
├── Vorlagen/Regel-Vorlage.md           ← template for a new rule
├── Glossar.md                          ← the data and what it means to the business
├── Regel-Cockpit.base                  ← Obsidian Bases overview
├── Protokoll/
│   ├── Freigaben/                      ← approved state per version, read-only
│   └── Läufe/                          ← one log per run, including refusals
├── engine/
│   ├── regelwerk.py                    ← deterministic core, no LLM
│   ├── mcp_server.py                   ← the five tools for Claude
│   ├── regelwerk.config.json           ← connections and limits, no credentials
│   └── tests/test_regelwerk.py
├── daten/                              ← demo database and its generator
├── mod/regel-cockpit/                  ← Claude mod: cockpit pane and guard
├── .mcp.json, CLAUDE.md, .claude/skills/   ← wiring into Claude (2 skills, 1 MCP server)
```

> **Language note:** the rule layer is German on purpose. Rule notes, the section headings the parser expects, the skills and the project instructions are written for German-speaking domain experts. The documentation is bilingual (English default). A language-neutral rule format is listed as a limit in the [concept](docs/concept.md#limits).
>
> **Demo data:** the owner in the sealed example rule is the repository author. The `Protokoll/` folder holds the real approval and run logs of the MVP as examples. In a real deployment, that archive belongs in the customer's own store, not in git.

---

## Relation to the PoC

| | PoC (repository root) | Rule Workshop (this folder) |
|---|---|---|
| Certified object | SQL script and six skills, pinned by hash | The decisions: edge cases and rule text, sealed with the SQL |
| Who creates it | IT, with Claude | Domain expert, with Claude |
| Who proves it | A human reads the SQL | The engine, against the edge cases |
| Orchestration | An LLM (CoWork) | Deterministic engine, LLM only for the conversation |

The PoC is unchanged. See [ROADMAP](../ROADMAP.md), item J.

License: [MIT](../LICENSE).
