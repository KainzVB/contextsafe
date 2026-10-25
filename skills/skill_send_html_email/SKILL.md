---
name: skill_send_html_email
description: >
  Sends a formatted HTML email with the ContextSafe execution result — including
  narrative text and result table — to the recipients defined in the Prozess-MD.
  Use this skill as Step 4 in the ContextSafe pipeline, after skill_narrativize_result
  and before skill_log_run_to_obsidian. Triggers on phrases like "sende die Email",
  "verschicke den Report", "send the report", "Email versenden", or automatically
  as part of the pipeline. Recipient list is always read exclusively from the
  Prozess-MD frontmatter — never from runtime data or user input. Passes
  email_context to skill_log_run_to_obsidian for complete audit logging.
---

# skill_send_html_email

## Verantwortung

HTML-Email mit Ergebnistabelle und narrativem Text an die im Prozess-MD
definierten Empfänger versenden. Step 4 in der ContextSafe-Pipeline —
nach Narrativierung, vor dem abschließenden Run-Log.

**Sicherheitsprinzip:** Empfänger ausschließlich aus `email_recipients` im
Prozess-MD Frontmatter. Ergebnis des Versands wird als `email_context` an
`skill_log_run_to_obsidian` übergeben — ob Erfolg oder Fehler.

---

## Erwarteter Eingabe-Kontext

Aus `execution_context` (von `skill_execute_sql_postgres`, erweitert):

| Feld | Pflicht | Beschreibung |
|------|---------|-------------|
| `use_case_id` | ✅ | Für Header + Footer |
| `use_case_name` | ✅ | Für Subject + Header |
| `certified_script_hash` | ✅ | Für Footer (Transparenz) |
| `db_connection_ref` | ✅ | Für Header |
| `version` | ✅ | Für Footer |
| `approved_by` | ✅ | Für Footer |
| `timestamp` | ✅ | Für Subject-Datum |
| `row_count` | ✅ | Für Header |
| `email_recipients` | ✅ | Empfängerliste — aus Prozess-MD |
| `email_subject_template` | ✅ | Subject-Vorlage |

Aus `narrative_context` (von `skill_narrativize_result`):

| Feld | Pflicht | Beschreibung |
|------|---------|-------------|
| `html_report` | ❌ | HTML-Report-Block (Narrativ + Tabelle) |
| `narrative_text` | ❌ | Plain-Text (Fallback) |
| `fallback_used` | ✅ | War Haiku-Fallback aktiv? |

---

## Ablauf (Schritt Für Schritt)

### Schritt 1 — Validierung

```
[CHECK 1] email_recipients nicht leer?
  FAIL → ⛔ ABORT: "Keine Empfänger definiert"

[CHECK 2] html_report vorhanden?
  NEIN → Fallback: Email nur mit Ergebnistabelle + Warnung

[CHECK 3] row_count > 0?
  NEIN → Warnung im Email-Body: "Query lieferte 0 Ergebnisse"
```

### Schritt 2 — Subject Aufbauen

```
{use_case_name} → aus execution_context
{date}          → YYYY-MM-DD aus timestamp
Beispiel: "[ContextSafe] Top 10 Shipping Priorities — 2026-04-04"
```

### Schritt 3 — HTML-Body Aufbauen

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           color: #1a1a1a; max-width: 680px; margin: 0 auto; padding: 24px; }
    .header { border-bottom: 3px solid #2563eb; padding-bottom: 16px; margin-bottom: 24px; }
    .header h1 { font-size: 20px; margin: 0; color: #2563eb; }
    .header .meta { font-size: 13px; color: #6b7280; margin-top: 4px; }
    .narrative { line-height: 1.6; margin-bottom: 24px; }
    .warning { background: #fef3c7; border-left: 4px solid #f59e0b;
               padding: 10px 14px; margin-bottom: 16px; font-size: 13px; }
    table { border-collapse: collapse; width: 100%; margin-bottom: 24px; }
    th { background: #f3f4f6; text-align: left; padding: 10px 12px;
         font-size: 13px; border-bottom: 2px solid #d1d5db; }
    td { padding: 8px 12px; border-bottom: 1px solid #e5e7eb; font-size: 14px; }
    tr:hover { background: #f9fafb; }
    .footer { border-top: 1px solid #e5e7eb; padding-top: 12px;
              font-size: 12px; color: #9ca3af; line-height: 1.6; }
  </style>
</head>
<body>
  <div class="header">
    <h1>{use_case_name}</h1>
    <div class="meta">
      {YYYY-MM-DD} &nbsp;|&nbsp; {row_count} Ergebnisse &nbsp;|&nbsp;
      DB: {db_connection_ref} &nbsp;|&nbsp; v{version}
    </div>
  </div>

  {warning_block — wenn fallback_used == true}

  <div class="narrative">
    {html_report}
  </div>

  <div class="footer">
    ContextSafe PoC &nbsp;|&nbsp; Use Case: {use_case_id} &nbsp;|&nbsp;
    Zertifiziert durch: {approved_by} &nbsp;|&nbsp;
    Script-Hash: {certified_script_hash ersten 8 Zeichen}...
  </div>
</body>
</html>
```

### Schritt 4 — Email Senden via Gmail MCP

```
gmail:send_email(
  to:      email_recipients,
  subject: generierter Subject-String,
  body:    vollständiger HTML-String,
  isHtml:  true
)
```

Bei Fehler: 3 Retry-Versuche mit 10s Pause, dann Fehler dokumentieren.

### Schritt 5 — email_context Aufbauen Und Übergeben

**Immer** — egal ob Versand erfolgreich oder fehlgeschlagen:

```
email_context:
  email_sent:        true | false
  email_timestamp:   {ISO-Zeitstempel oder null}
  email_recipients:  [{emails}]
  email_subject:     {gesendeter Subject-String}
  email_error:       null | {Fehlermeldung}
```

Dieser Kontext wird an `skill_log_run_to_obsidian` (Step 5) übergeben,
damit der Run-Log den vollständigen Email-Status dokumentiert.

---

## Ausgabe-Format Bei Erfolg

```
✅ Email gesendet → skill_log_run_to_obsidian

Subject:    [ContextSafe] Top 10 Shipping Priorities — 2026-04-04
Empfänger:  business-recipient@example.com
Timestamp:  2026-04-04T14:45:00Z
→ email_context übergeben an Step 5
```

## Ausgabe-Format Bei Fehler

```
⚠️ Email-Versand fehlgeschlagen → skill_log_run_to_obsidian

Fehler:    {Fehlermeldung}
→ email_context mit Fehler übergeben an Step 5 (Log dokumentiert Fehler)
```

---

## Sicherheitsregeln

| Regel | Begründung |
|-------|-----------|
| Empfänger nur aus Prozess-MD | Keine unbeabsichtigte Datenweiterleitung |
| Kein CC/BCC aus Runtime-Daten | Auditierbarkeit |
| Kein Anhang mit Rohdaten | ContextSafe-Prinzip |
| Script-Hash im Footer | Art. 13 — Transparenz |
| email_context immer übergeben | Step 5 braucht vollständigen Status |

---

## Fehlerbehandlung

| Fehler | Verhalten |
|--------|-----------|
| `email_recipients` leer | ABORT |
| Gmail MCP nicht erreichbar | 3 Retries à 10s, email_context mit Fehler → Step 5 |
| Einzelne Adresse fehlgeschlagen | Weiter, Fehler in email_context |
| HTML-Body leer | Fallback: Plain-Text Email |

---

## EU AI Act Mapping

| Element | Artikel | Anforderung |
|---------|---------|-------------|
| Empfänger aus Prozess-MD | Art. 14 | Menschlich kontrolliert |
| Script-Hash im Footer | Art. 13 | Transparenz |
| email_context an Step 5 | Art. 12 | Vollständiger Audit-Trail im Log |
| Kein Anhang mit Rohdaten | Art. 9 | Datenminimierung |
