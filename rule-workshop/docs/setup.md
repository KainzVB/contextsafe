# Setup: ContextSafe Rule Workshop

**English** · [Deutsch](setup.de.md)

How to set up the environment, from "runs on the command line" to "domain expert works in Claude". Each level builds on the previous one, and each ends with a check.

---

## Overview

| Level | What you get | Needs |
|---|---|---|
| 1. Engine | Proof, probes, seal and run from the terminal | Python 3.9+ |
| 2. Claude | Conversation with Claude, MCP tools, skills | Level 1, Claude Code or Claude Desktop |
| 3. Cockpit | Overview of all rules in Obsidian | Level 1, Obsidian 1.9+ |
| 4. Claude mod | Cockpit pane beside the chat, guard against direct data access | Level 2 |
| 5. TPC-H rule | The original PoC use case on PostgreSQL | Level 1, Docker, the PoC database |

Levels 1 and 2 are enough for the demo with the SQLite sample data. Levels 3 to 5 are optional and independent of each other.

## Requirements

| Component | Version | Notes |
|---|---|---|
| Python | 3.9 or newer | Standard library only, no `pip install`. Tested on 3.9 and 3.14. macOS ships 3.9 with the Xcode command line tools |
| Git | any | To clone and to undo demo edits |
| macOS | any current | Only for the approval dialog. Elsewhere, approve from a terminal (see [Approval](#approval-on-other-platforms)) |
| Claude Code or Claude Desktop (Code tab) | current | For levels 2 and 4 |
| Obsidian | 1.9 or newer | For level 3. Bases is a core plugin since 1.9 |
| Docker | any | Only for level 5 |

## Level 1: Engine

```bash
git clone https://github.com/KainzVB/contextsafe.git
cd contextsafe/rule-workshop
python3 engine/tests/test_regelwerk.py
python3 engine/regelwerk.py liste
```

**Check**

- The tests end with `OK` (15 tests).
- `liste` shows three rules. *Aktiver Kunde* is `certified` and executable. *Upselling-Kandidat* is `draft`, *Top 10 Shipping Priorities* is `review`.

Notes

- The demo database `daten/abo_welt.sqlite` is in the repository. To rebuild it: `python3 daten/demo_daten_erzeugen.py` (fixed seed).
- The sealed example expires on **2027-05-11** (recertification interval: 6 months, `rezertifizierung_monate` in `engine/regelwerk.config.json`). After that date `liste` shows it as `suspended` with the reason "recertification overdue". That is the intended behaviour: release it again.
- Do not keep the working copy in a cloud-synced folder. The engine writes notes and logs, and sync conflicts would look like manual edits.

## Level 2: Claude

1. Open the **`rule-workshop/` folder itself** as the working folder in Claude Code (`cd rule-workshop && claude`) or in the Claude Desktop Code tab. Opening the repository root does not load the MCP server or the project instructions.
2. On the first start, allow the MCP server **`regelwerk`**. It is defined in `.mcp.json` and starts `engine/mcp_server.py` with your `python3`.
3. The skills `regel-werkstatt` (create and change rules) and `regel-ausfuehren` (answer data questions) load automatically from `.claude/skills/`.

**Check**

- In Claude, ask: "Which rules exist?". Claude calls `regel_liste` and names three rules.
- Ask: "How many active customers do we have?". Claude calls `regel_ausfuehren` and answers with the rule, version, owner and a run log under `Protokoll/Läufe/`.

What the MCP server offers: five tools, no free SQL. See the [README](../README.md#the-five-tools).

### Roles

| Role | Does | Needs |
|---|---|---|
| Platform (once) | Read-only data access, [Glossar.md](../Glossar.md), connection entry in `engine/regelwerk.config.json` | Access to the data source |
| Owner (per rule) | Decides edge cases, approves | His or her name in the `owner` property of the rule note, a Mac for the dialog |

To try a release yourself, enter your name as `owner` in `Regeln/Upselling-Kandidat.md` first. The approval only works if the name you pass equals the `owner` entry.

### Approval on other platforms

The dialog is built on macOS `osascript`. Where it is missing, the engine asks on the keyboard, which works in a terminal only. The MCP server has no terminal, so on Linux and Windows release from a shell:

```bash
python3 engine/regelwerk.py freigeben "Upselling-Kandidat" --von "Your Name" --aenderung "First release"
```

The dialog appears on the machine where the MCP server runs. In a remote or cloud session you will not see it, and the release is not confirmed.

## Level 3: Obsidian cockpit

1. In Obsidian, open the folder `rule-workshop/` (or the whole repository) as a vault.
2. Open `Regel-Cockpit.base`. It has five views: all rules, needing action, recertification due, runs, approvals.

**Check:** the *Alle Regeln* view lists three rules with status, grenzfälle (edge cases passed) and festigkeit (strength).

Notes

- The cockpit filters on the tags `typ/regel`, `typ/freigabe` and the property `typ: lauf`. Keep them when you copy a rule note.
- Automatic formatters (for example the Linter plugin on save) may touch rule notes. Capitalisation and whitespace in headings and tables are tolerated and do not break the seal. Renaming a section heading does break parsing, so exclude this folder from heading rules.

## Level 4: Claude mod

```bash
cd rule-workshop
claude --plugin-dir mod/regel-cockpit
```

It adds a **Regel-Cockpit** pane (command `/regel-cockpit`) and refuses commands that reach data directly: anything containing `sqlite3`, `psql`, `pg_dump`, `duckdb` or `.sqlite`, and database tools of other MCP servers.

- Start Claude from `rule-workshop/`. The mod switches itself on only where `engine/regelwerk.py` exists.
- The guard matches text. A harmless command that merely mentions a `.sqlite` file is refused too. It is a guard rail, not a vault (see [limits](concept.md#limits)).
- Loading from this folder with `--plugin-dir` follows the Claude Code mod documentation. It has been exercised as a hot-loaded mod in Claude Desktop, not from this repository folder.

## Level 5: TPC-H rule on PostgreSQL

The rule *Top 10 Shipping Priorities* reads the database of the original PoC.

| Setting | Value in `engine/regelwerk.config.json` |
|---|---|
| Connection type | `postgres-docker` |
| Container | `n8n-db-1` (change to your container name) |
| Database | `tpch` |
| User | `readonly_user` (needs `SELECT` on the three tables) |
| Schema | `public` |
| Tables | `tpch_customer`, `tpch_orders`, `tpch_lineitems` (date columns are text) |

How it connects: the engine runs `docker exec <container> psql ...` and sets the session read-only and a statement timeout. There is no password handling, so the user must be allowed to connect from inside the container without one. Anything else needs a connector extension.

**Check**

```bash
python3 engine/regelwerk.py pruefen "Top 10 Shipping Priorities"
```

Expected: six of six edge cases passed, no errors. If the container is missing, the result says the database is not reachable. The other two rules are unaffected.

The repository does not include a loader for the TPC-H data. Load it yourself (the PoC used about scale factor 1) into a database `tpch` with the table names above. The data path of the PoC is described in [architecture](../../docs/architecture.md).

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `regelwerk` is not offered in Claude | Folder opened at the repository root | Open `rule-workshop/` itself |
| MCP server fails to start | `python3` not on the PATH of the Claude process | Check `python3 --version` in the same shell; start Claude from that shell |
| "Ausführung verweigert – noch nie freigegeben" | Rule never approved | Expected. Approve it as its owner |
| "… geändert seit Freigabe: Grenzfälle" | A decision or the SQL changed after approval | Intended. Check, then approve again. For a demo edit: `git checkout -- Regeln/` |
| "… Rezertifizierung überfällig" | Recertification date passed | Approve again |
| "Nur der Owner (...) darf diese Regel freigeben" | `von` differs from the `owner` property | Use exactly the name in the note |
| No dialog appears | Not macOS, or a remote session | Release from a terminal on the machine that runs the engine |
| "Freigabe nicht bestätigt" | Dialog cancelled or timed out after 120 s | Ask for the release again |
| "Direkter Datenzugriff ist hier gesperrt" | The mod's guard matched a command | Use the rule tools. For file work, avoid the matched words in the command |
| "Verbindung ... nicht eingerichtet" or database not reachable | Connection missing or container down | Check `engine/regelwerk.config.json`, `docker ps` |
| "Das Kompilat läuft nicht: ..." | The SQL does not fit the data source | Fix the SQL in the note, see [Glossar.md](../Glossar.md) for table and column names |
| Folder `Protokoll/Läufe` missing or doubled | Different Unicode form of the umlaut (NFC/NFD) after copying | The repository stores NFC. Re-clone instead of copying through a tool that rewrites names |

## Uninstall

Nothing is installed. Delete the folder. The MCP entry lives in `.mcp.json` inside the folder, and the mod is loaded only for the session that names it.
