---
name: skill_read_process_md
description: >
  Reads a ContextSafe Prozess-MD from the Obsidian Vault, parses its YAML frontmatter,
  runs all governance and integrity checks, and passes a validated execution context
  to the next skill in the pipeline. This is the mandatory entry gate for every
  ContextSafe run — no SQL is ever executed without this skill passing first.
  Use whenever a ContextSafe pipeline starts, when phrases like "starte den Run",
  "führe den Use Case aus", "start the pipeline", or "check the process MD" appear,
  or when skill_execute_sql_postgres is about to be called. Always runs before
  skill_execute_sql_postgres. Never skip this skill — it is the only place where
  certification status, approver identity, recertification deadline, and script
  hash integrity are verified. On any ABORT, calls skill_error_log before returning.
---

# skill_read_process_md

## Verantwortung

Prozess-MD aus dem Vault lesen, Frontmatter validieren, alle Governance-Gates prüfen,
validierten Kontext an `skill_execute_sql_postgres` übergeben.

**Bei jedem ABORT:** `skill_error_log` aufrufen bevor dieser Skill endet.

---

## Eingabe

| Parameter | Quelle | Beschreibung |
|-----------|--------|-------------|
| `process_md_path` | CoWork Projekt-Kontext | Vollständiger Vault-Pfad zum Prozess-MD |
| `admin_recipients` | Prozess-MD oder Fallback | Für skill_error_log bei frühem ABORT |

Standard-Pfad: `zDevPlayground/determinismArchitecture/assets/specs/poc_tpch_q3_process.md`

---

## Ablauf (Schritt Für Schritt)

### Schritt 1 — Prozess-MD Lesen

`vault_read(path = process_md_path)`

Antwort ist JSON: Markdown-Text in `content`, bereits geparstes YAML in `frontmatter`.
Für Schritt 2 und Hash-Prüfungen immer `content` bzw. `frontmatter` verwenden.

Bei Fehler → ABORT + `skill_error_log` aufrufen:
```
abort_step:   "Step 1 — skill_read_process_md"
abort_gate:   "Datei-Zugriff"
abort_reason: "Prozess-MD nicht gefunden / leer"
```

### Schritt 2 — Frontmatter Parsen

Pflichtfelder — bei Fehlen → ABORT + `skill_error_log`:
`status`, `owner`, `approved_by`, `next_recertification`, `certified_script`,
`certified_script_hash`, `db_connection_ref`, `max_result_rows`, `db_access_mode`

### Schritt 3 — Governance-Gates

Bei jedem FAIL: ABORT + **`skill_error_log` aufrufen** mit:
- `abort_step`: `"Step 1 — skill_read_process_md"`
- `abort_gate`: Gate-Nummer + Name
- `abort_reason`: Fehlermeldung
- `use_case_id`, `admin_recipients`: aus Frontmatter
- `status_set_to_suspended`: true wenn Gate 4 oder Gate 8

```
[GATE 1] status == "certified"?
  FAIL → ABORT + error_log: "Status '{status}' — nur 'certified' erlaubt"

[GATE 2] owner gesetzt?
  FAIL → ABORT + error_log: "Kein Owner definiert"

[GATE 3] approved_by gesetzt?
  FAIL → ABORT + error_log: "Kein Approver — Art. 14 Freigabe fehlt"

[GATE 4] next_recertification >= heute?
  FAIL → status → "suspended" + change_log Eintrag
         ABORT + error_log: "Rezertifizierung fällig seit {datum}"
         status_set_to_suspended: true

[GATE 5] db_access_mode == "read_only"?
  FAIL → ABORT + error_log: "db_access_mode '{mode}' — nur 'read_only' erlaubt"

[GATE 6] certified_script_hash gesetzt?
  FAIL → ABORT + error_log: "Kein Hash hinterlegt"

[GATE 7] Script-Datei lesbar?
  FAIL → ABORT + error_log: "Script nicht gefunden: {pfad}"

[GATE 8] SHA-256(script) == certified_script_hash?
  FAIL → status → "suspended" + change_log Eintrag
         ABORT + error_log: "Hash-Mismatch — Script verändert"
         status_set_to_suspended: true
```

### Schritt 4 — execution_context Aufbauen

Alle Gates grün → Kontext für `skill_execute_sql_postgres`:

```
execution_context:
  use_case_id, use_case_name, db_connection_ref, db_access_mode,
  certified_script, certified_script_hash, script_content,
  max_result_rows, output_format, email_recipients, admin_recipients,
  email_subject_template, approved_by, version,
  validated_at, gates_passed: "8/8"
```

> `admin_recipients` wird weitergegeben damit alle nachfolgenden Skills
> bei ABORT den `skill_error_log` korrekt befüllen können.

---

## Ausgabe Bei Erfolg

```
✅ Prozess-MD validiert — Run freigegeben
Gates: 8/8 | Approver: {approved_by} | Bis: {next_recertification}
→ Übergabe an skill_execute_sql_postgres
```

## Ausgabe Bei ABORT

```
⛔ ABORT — skill_read_process_md
Gate:   {Gate + Name}
Grund:  {Fehlermeldung}
→ skill_error_log aufgerufen
```

---

## EU AI Act Mapping

| Gate | Artikel |
|------|---------|
| Gate 1 status certified | Art. 14 |
| Gate 3 approved_by | Art. 14 |
| Gate 4 Rezertifizierung | Art. 17 |
| Gate 8 Hash | Art. 9 |
| skill_error_log bei ABORT | Art. 12 |

---

## Wichtige Hinweise

1. **Niemals überspringen** — Eingangstor für alle Governance-Checks
2. **Bei jedem ABORT** `skill_error_log` aufrufen — kein stiller Fehler
3. **Status-Änderungen** (→ suspended) sofort in Vault schreiben
4. **admin_recipients** immer im execution_context weitergeben
