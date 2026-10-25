---
name: skill_narrativize_result
description: >
  Transforms a compact SQL result table into a readable, business-contextualized
  report in German using Claude Haiku. Use this skill whenever a ContextSafe
  execution result needs to be communicated to a human audience — after
  skill_execute_sql_postgres has returned its result and before
  skill_send_html_email is called. Triggers on phrases like "narrativisiere das
  Ergebnis", "erstelle den Bericht", "bereite das Ergebnis auf", "schreibe die
  Zusammenfassung", or when an execution_context with rows is present and an
  email is about to be sent. Always runs after skill_execute_sql_postgres and
  before skill_send_html_email.
---

# skill_narrativize_result

## Verantwortung

Ergebnistabelle aus `skill_execute_sql_postgres` via Claude Haiku in einen
business-tauglichen HTML-Report überführen. Dieser Schritt ist der einzige in
der Pipeline mit inhärentem LLM-Non-Determinismus — bewusst akzeptiert, weil
der narrative Text kein Governance-Artefakt ist. Das SQL-Script ist es.

---

## Erwarteter Eingabe-Kontext

Aus `execution_context` (übergeben von `skill_execute_sql_postgres`):

| Feld | Pflicht | Beschreibung |
|------|---------|-------------|
| `rows` | ✅ | Ergebniszeilen als Objekte |
| `row_count` | ✅ | Anzahl Zeilen |
| `use_case_name` | ✅ | Name des Use Case |
| `use_case_id` | ✅ | ID des Use Case |
| `timestamp` | ✅ | Ausführungszeitpunkt (ISO) |
| `script` | ✅ | Dateiname des ausgeführten Scripts |

Aus `assets/specs/poc_tpch_q3_process.md` Frontmatter:
- `output_format` — `table`, `csv`, oder `json`

---

## Ablauf (Schritt Für Schritt)

### Schritt 1 — Ergebnistabelle Als Markdown Aufbauen

Konvertiere `rows` aus dem `execution_context` in eine Markdown-Tabelle:

```
| o_orderkey | revenue    | o_orderdate | o_shippriority |
|-----------|------------|-------------|----------------|
| 18869634  | 541.426,17 | 1995-01-10  | 0              |
| ...       | ...        | ...         | ...            |
```

Revenue-Werte: auf 2 Dezimalstellen runden, Tausender-Trennzeichen (`.`), Dezimal (`,`).

### Schritt 2 — Use-Case-Kontext Aus Prozess-MD Holen

Lese den Body-Abschnitt "Aufgabenstellung" aus dem Prozess-MD — dieser liefert
den Business-Kontext für den Haiku-Prompt.

Fallback falls nicht verfügbar: Use-Case-Name und -ID als Kontext verwenden.

### Schritt 3 — Haiku API-Call

Rufe Claude Haiku mit folgendem Prompt auf:

**Modell:** `claude-haiku-4-5-20251001`
**temperature:** `0` (maximale Reproduzierbarkeit)
**max_tokens:** `1000`

**System-Prompt:**
```
Du bist ein Business-Analyst. Erstelle aus der folgenden Ergebnistabelle
einen kurzen, prägnanten Bericht in 2–4 Absätzen.
Sprache: Deutsch. Tonalität: sachlich, professionell.
Fokussiere auf: Kernaussage, Auffälligkeiten, Handlungsempfehlung.
Formatiere die Ausgabe als HTML mit ausschließlich <p>-Tags.
Keine Überschriften, keine Listen, keine anderen HTML-Tags.
```

**User-Prompt:**
```
## Kontext
{aufgabenstellung_aus_prozess_md}

## Ausführung
- Use Case: {use_case_name} ({use_case_id})
- Script: {script}
- Ausgeführt: {timestamp}
- Ergebnisse: {row_count} Zeilen

## Ergebnistabelle
{markdown_tabelle}

Erstelle den Bericht.
```

### Schritt 4 — Response Validieren

```
[VAL 1] Response nicht leer?
  LEER → Fallback: Tabelle ohne Narrativ

[VAL 2] Response enthält <p>-Tags?
  NEIN → Response trotzdem verwenden, in <p> einwickeln

[VAL 3] Response länger als 2000 Zeichen?
  JA → Warnung loggen, trotzdem verwenden (kein Abbruch)
```

### Schritt 5 — HTML-Report Zusammenbauen

Baue den vollständigen HTML-Report auf:

```html
<div class="contextsafe-report">

  <div class="report-header">
    <h2>{use_case_name}</h2>
    <p class="meta">
      Ausgeführt: {timestamp} &nbsp;|&nbsp;
      Script: {script} &nbsp;|&nbsp;
      Ergebnisse: {row_count} Zeilen
    </p>
  </div>

  <div class="report-narrative">
    {haiku_response_html}
  </div>

  <div class="report-table">
    <h3>Detailergebnisse</h3>
    {markdown_tabelle_als_html_table}
  </div>

  <div class="report-footer">
    <p class="governance">
      ContextSafe PoC &nbsp;|&nbsp; Use Case: {use_case_id} &nbsp;|&nbsp;
      Certified Script Hash: {certified_script_hash_kurz}...
    </p>
  </div>

</div>
```

---

## Ausgabe-Kontext Für Nachfolgende Skills

```
narrative_context:
  html_report:          {vollständiger HTML-Report}
  narrative_text:       {haiku_response_plain}
  use_case_name:        {use_case_name}
  use_case_id:          {use_case_id}
  timestamp:            {timestamp}
  row_count:            {row_count}
  fallback_used:        true/false
```

Dieser Kontext wird von `skill_send_html_email` und `skill_log_run_to_obsidian` benötigt.

---

## Fehlerbehandlung

| Fehler | Verhalten |
|--------|-----------|
| Haiku API nicht erreichbar | 3 Retry-Versuche mit 5s Pause, dann Fallback |
| Haiku Response leer | Fallback: Report ohne Narrativ, nur Tabelle |
| Haiku Response invalide | Fallback: Response als Plain-Text in `<p>` einwickeln |
| Prozess-MD Kontext nicht verfügbar | Use-Case-Name + ID als Minimalkontext verwenden |

**Fallback-Report** (bei Haiku-Fehler):
```html
<div class="contextsafe-report">
  <div class="report-header"><h2>{use_case_name}</h2></div>
  <p class="fallback-notice">
    ⚠️ Narrativisierung nicht verfügbar — Haiku API nicht erreichbar.
  </p>
  <div class="report-table">{html_table}</div>
</div>
```

---

## Determinismus-Hinweis

`temperature: 0` sorgt für maximale Reproduzierbarkeit, garantiert aber keinen
identischen Output bei jedem Run. Das ist für diesen Schritt **bewusst akzeptiert**:

- Der narrative Text ist kein Governance-Artefakt — er wird nicht gehashed
- Das SQL-Script und sein Hash sind die Grundlage der Auditierbarkeit
- Narrativisierung dient der menschlichen Lesbarkeit, nicht der Zertifizierung

**EU AI Act:** Art. 13 (Transparenz) wird durch den Governance-Footer im HTML-Report
erfüllt — der Hash des zertifizierten Scripts ist direkt sichtbar.
