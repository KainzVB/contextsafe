---
name: skill_execute_sql_postgres
description: >
  Executes a certified SQL script against a PostgreSQL database via MCP and returns
  only the compact aggregate result — never raw row data. Use this skill whenever
  a certified Prozess-MD is present and the execution phase of the ContextSafe pipeline
  begins. Triggers on phrases like "run the query", "execute the script", "start the
  pipeline", "führe die Query aus", "starte den Run", or when skill_read_process_md
  has already validated the Prozess-MD and passed context forward. Do NOT use for
  schema exploration (use skill_postgres_schema_explore) or SQL generation (use
  skill_generate_sql_script).
---

# skill_execute_sql_postgres

## Verantwortung

Zertifiziertes SQL-Script auf Postgres ausführen via `tpch:query` MCP-Tool.
Ausschließlich das kompakte Aggregat-Ergebnis zurückgeben.

**Kernprinzip:** Rohdaten verlassen die Datenbank nie in Richtung LLM-Kontext.

---

## Erwarteter Eingabe-Kontext

Übergeben von `skill_read_process_md` via `execution_context`:

| Feld | Pflicht | Beschreibung |
|------|---------|-------------|
| `certified_script` | ✅ | Dateiname des SQL-Scripts (z.B. `q3_shipping_priority.sql`) |
| `certified_script_hash` | ✅ | SHA-256 Hash des Scripts |
| `script_content` | ✅ | Vollständiger SQL-Inhalt (bereits gelesen von Step 1) |
| `db_connection_ref` | ✅ | MCP-Connector-Name (z.B. `tpch`) |
| `max_result_rows` | ✅ | Maximale Zeilenanzahl (z.B. `10`) |
| `db_access_mode` | ✅ | Muss `read_only` sein |
| `status` | ✅ | Muss `certified` sein |
| `use_case_id` | ✅ | Für Kontext-Übergabe |
| `use_case_name` | ✅ | Für Kontext-Übergabe |
| `email_recipients` | ✅ | Weitergabe an nachfolgende Skills |
| `email_subject_template` | ✅ | Weitergabe an nachfolgende Skills |
| `approved_by` | ✅ | Weitergabe an nachfolgende Skills |
| `version` | ✅ | Weitergabe an nachfolgende Skills |

---

## Ablauf (Schritt für Schritt)

### Schritt 1 — Pre-Execution Checks

```
[CHECK 1] db_access_mode == "read_only"?
  FAIL → ⛔ ABORT: "db_access_mode ist nicht read_only — Execution verweigert"

[CHECK 2] status == "certified"?
  FAIL → ⛔ ABORT: "Prozess-MD Status ist '{status}' — nur 'certified' erlaubt"

[CHECK 3] certified_script_hash gesetzt (nicht leer)?
  FAIL → ⛔ ABORT: "Kein Hash hinterlegt — Script nicht zertifiziert"

[CHECK 4] Read-Only Pattern Check auf script_content:
  Verbotene Keywords (case-insensitive):
  INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, TRUNCATE,
  GRANT, REVOKE, EXECUTE, COPY, MERGE
  FAIL → ⛔ ABORT + status → "suspended": "Verbotenes SQL-Pattern: {keyword}"

[CHECK 5] LIMIT vorhanden im script_content?
  FAIL → ⛔ ABORT: "SQL hat kein LIMIT — Execution verweigert"

[CHECK 6] LIMIT-Wert ≤ max_result_rows?
  FAIL → ⛔ ABORT: "LIMIT ({limit}) überschreitet max_result_rows ({max})"
```

### Schritt 2 — SQL Ausführen

```
tpch:query(sql = script_content)
```

Bei Fehler:
- DB-Verbindungsfehler → 3 Retry-Versuche mit 5s Pause, dann ABORT
- SQL-Syntaxfehler → ABORT mit Fehlermeldung, kein Retry
- Timeout (>60s) → ABORT: "Query-Timeout"

### Schritt 3 — Ergebnis-Validierung

```
[VAL 1] Zeilenanzahl ≤ max_result_rows?
  FAIL → ⛔ ABORT: "Ergebnis ({n} Zeilen) überschreitet max_result_rows ({max})"

[VAL 2] Ergebnis nicht leer?
  LEER → Warnung: "Query lieferte 0 Zeilen" (kein Abbruch)
```

### Schritt 4 — Kontext Erweitern und Übergeben

Den `execution_context` von Step 1 um Ergebnis-Felder erweitern:

```
execution_context (erweitert):
  # Alle Felder aus Step 1 bleiben erhalten, plus:
  rows:       [{o_orderkey, revenue, o_orderdate, o_shippriority}, ...]
  row_count:  10
  timestamp:  {ISO-Zeitstempel}
  gates_passed: "8/8"
```

Dieser erweiterte Kontext wird an **alle** nachfolgenden Skills übergeben:
- Step 3 (`skill_narrativize_result`) — benötigt `rows`, `row_count`, `use_case_name`
- Step 4 (`skill_send_html_email`) — benötigt `email_recipients`, `email_subject_template`, etc.
- Step 5 (`skill_log_run_to_obsidian`) — benötigt den vollständigen Kontext für den Log

---

## Ausgabe-Format

```
✅ Execution erfolgreich

## Ergebnis: {use_case_name}

| o_orderkey | revenue    | o_orderdate | o_shippriority |
|-----------|------------|-------------|----------------|
| 18869634  | 541.426,17 | 1995-01-10  | 0              |
| ...

Zeilen: {row_count}/{max_result_rows} | Script: {certified_script}
Connector: {db_connection_ref} | Timestamp: {ISO}
```

---

## Safety Guards

| Guard | Bei Verstoß |
|-------|-------------|
| `db_access_mode == read_only` | ABORT |
| `status == certified` | ABORT |
| Hash gesetzt | ABORT |
| Read-Only SQL Pattern | ABORT + suspended |
| LIMIT vorhanden | ABORT |
| LIMIT ≤ max_result_rows | ABORT |
| Ergebnis ≤ max_result_rows | ABORT |
| MCP `?mode=readonly` | Automatisch (Infrastruktur) |

---

## Fehler-Ausgabe-Format

```
⛔ Execution abgebrochen
- Grund:   {Fehlermeldung}
- Check:   {Welcher Check fehlschlug}
- Script:  {certified_script}
- Aktion:  {was zu tun ist}
```
