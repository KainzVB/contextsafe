---
name: skill_error_log
description: >
  Writes a structured error log to the Obsidian Vault and sends an admin
  notification email whenever a ContextSafe pipeline is aborted. Must be called
  by any skill or pre-flight step that issues an ABORT — regardless of which
  step fails. Triggers automatically on ABORT in: Pre-Flight (skill-hash mismatch),
  skill_read_process_md (gate failures), skill_execute_sql_postgres (execution
  failure), skill_narrativize_result (unrecoverable failure), skill_send_html_email
  (unrecoverable failure). Never called on normal pipeline completion.
  Writes to runs/errors/ — separate from normal run logs in runs/.
---

# skill_error_log

## Verantwortung

Bei jedem ABORT in der ContextSafe-Pipeline einen strukturierten Fehler-Log
in den Vault schreiben und eine Admin-Benachrichtigung versenden.

**Kernprinzip:** Kein ABORT ohne Spur. Jeder Fehler ist auditierbar —
unabhängig davon ob der normale Run-Log (Step 5) je erreicht wurde.

---

## Wann Wird Dieser Skill Aufgerufen?

| Auslöser | Beispiel |
|----------|---------|
| Pre-Flight ABORT | Skill-Hash-Mismatch |
| Step 1 ABORT | Gate-Failure (status nicht certified, Hash-Mismatch, Rezertifizierung fällig) |
| Step 2 ABORT | SQL-Execution fehlgeschlagen, Read-Only Pattern verletzt |
| Step 3 ABORT | Haiku API nicht erreichbar UND kein Fallback möglich |
| Step 4 ABORT | Gmail MCP nicht erreichbar UND kein Fallback möglich |

> **Hinweis:** Step 3 und Step 4 haben Fallback-Mechanismen — `skill_error_log`
> wird nur bei echtem ABORT aufgerufen, nicht bei Fallback-Aktivierung.

---

## Erwarteter Eingabe-Kontext

| Feld | Pflicht | Beschreibung |
|------|---------|-------------|
| `abort_step` | ✅ | Wo der ABORT passiert ist (z.B. `"Pre-Flight"`, `"Step 1 — skill_read_process_md"`) |
| `abort_gate` | ✅ | Welcher Gate/Check fehlschlug (z.B. `"SKILL-GATE 2"`, `"GATE 4"`) |
| `abort_reason` | ✅ | Fehlermeldung im Klartext |
| `abort_timestamp` | ✅ | ISO-Zeitstempel |
| `use_case_id` | ❌ | Falls bereits aus Prozess-MD gelesen |
| `use_case_name` | ❌ | Falls bereits aus Prozess-MD gelesen |
| `process_md_path` | ❌ | Pfad zum Prozess-MD |
| `status_set_to_suspended` | ❌ | `true` wenn status → suspended gesetzt wurde |
| `admin_recipients` | ✅ | Aus Prozess-MD Frontmatter oder Fallback-Wert |

**Fallback wenn `admin_recipients` nicht verfügbar:**
Falls Prozess-MD noch nicht gelesen werden konnte (z.B. Pre-Flight Fehler vor Gate 1),
`admin_recipients` aus `cowork/CLAUDE.md` Fallback-Konfiguration verwenden.

---

## Ablauf (Schritt Für Schritt)

### Schritt 1 — Error-Log Dateinamen Bestimmen

```
Datum:      YYYYMMDD aus abort_timestamp
Slug:       abort_step → lowercase, Leerzeichen → _, Sonderzeichen entfernen
            z.B. "Pre-Flight" → "pre_flight"
Error-ID:   error_{YYYYMMDD}_{NNN}
Log-Pfad:   zDevPlayground/determinismArchitecture/runs/errors/
            error_{YYYYMMDD}_{NNN}_{slug}.md
```

`runs/errors/` Ordner wird automatisch angelegt falls nicht vorhanden.

### Schritt 2 — Error-Log MD Aufbauen

```markdown
---
error_id: {error_id}
use_case_id: {use_case_id | "unbekannt"}
abort_step: {abort_step}
abort_gate: {abort_gate}
abort_timestamp: {ISO-Zeitstempel}
status_suspended: {true | false}
admin_notified: {true | false}
tags:
  - typ/error-log
  - thema/tpch
  - status/error
---

# Error-Log: {abort_step} — {YYYY-MM-DD}

## Fehler-Details

| Parameter | Wert |
|-----------|------|
| Error-ID | `{error_id}` |
| Use Case | {use_case_id} — {use_case_name} |
| Abbruch in | {abort_step} |
| Gate/Check | {abort_gate} |
| Zeitstempel | {abort_timestamp} |
| Status → suspended | {Ja / Nein} |

## Fehlermeldung

```
{abort_reason}
```

## Prozess-MD

| Feld | Wert |
|------|------|
| Pfad | {process_md_path | "nicht verfügbar"} |
| Use Case ID | {use_case_id | "nicht gelesen"} |

## Erforderliche Maßnahmen

{Automatisch generiert je nach abort_gate:}

SKILL-GATE 2 (Hash-Mismatch):
→ Betroffene SKILL.md-Dateien identifizieren
→ Claude Code: neu hashen → Approver trägt Hashes in Prozess-MD ein

GATE 4 (Rezertifizierung fällig):
→ Prozess-MD durch Approver rezertifizieren
→ next_recertification aktualisieren, status → certified setzen

GATE 8 (Script Hash-Mismatch):
→ SQL-Script prüfen — wurde es verändert?
→ Claude Code: neu hashen → Approver einträgt, oder Script neu zertifizieren

GATE 5 (db_access_mode):
→ Prozess-MD prüfen: db_access_mode muss "read_only" sein

SQL-Pattern-Verletzung:
→ SQL-Script prüfen — enthält verbotene Keywords?
→ Script neu generieren und zertifizieren

## Admin-Benachrichtigung

{✅ Email gesendet an {admin_recipients} / ⚠️ Email-Versand fehlgeschlagen}
```

### Schritt 3 — Error-Log in Vault Schreiben

```
vault_write(path = log_pfad, content = error_log_md)
```

Bei Fehler: Plain-Text auf Kontext-Output ausgeben (letzter Fallback).

### Schritt 4 — Admin-Email Senden

**Subject:** `⛔ [ContextSafe] ABORT — {abort_step} | {use_case_id} | {YYYY-MM-DD}`

**Body:**

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px;
           margin: 0 auto; padding: 24px; color: #1a1a1a; }
    .abort-header { background: #fef2f2; border-left: 4px solid #dc2626;
                    padding: 16px; margin-bottom: 24px; border-radius: 4px; }
    .abort-header h1 { margin: 0 0 8px; color: #dc2626; font-size: 18px; }
    table { border-collapse: collapse; width: 100%; margin: 16px 0; }
    th, td { border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }
    th { background: #f9fafb; font-weight: 600; }
    .action { background: #fffbeb; border-left: 4px solid #f59e0b;
              padding: 12px; margin-top: 16px; border-radius: 4px; }
    .footer { margin-top: 24px; font-size: 12px; color: #9ca3af; }
  </style>
</head>
<body>
  <div class="abort-header">
    <h1>⛔ ContextSafe Pipeline ABORT</h1>
    <p>{abort_step} — {YYYY-MM-DD HH:MM}</p>
  </div>

  <table>
    <tr><th>Use Case</th><td>{use_case_id} — {use_case_name}</td></tr>
    <tr><th>Abbruch in</th><td>{abort_step}</td></tr>
    <tr><th>Gate/Check</th><td>{abort_gate}</td></tr>
    <tr><th>Status → suspended</th><td>{Ja / Nein}</td></tr>
  </table>

  <p><strong>Fehlermeldung:</strong><br>
  <code>{abort_reason}</code></p>

  <div class="action">
    <strong>Erforderliche Maßnahme:</strong><br>
    {Maßnahme je nach abort_gate — siehe Error-Log im Vault}
  </div>

  <div class="footer">
    ContextSafe PoC &nbsp;|&nbsp; Error-ID: {error_id} &nbsp;|&nbsp;
    Log: runs/errors/{log_dateiname}
  </div>
</body>
</html>
```

```
gmail:send_email(
  to:      admin_recipients,
  subject: "⛔ [ContextSafe] ABORT — {abort_step} | {use_case_id} | {YYYY-MM-DD}",
  body:    html_body,
  isHtml:  true
)
```

Bei Gmail-Fehler: Fehlermeldung in Error-Log ergänzen (`admin_notified: false`).

---

## Ausgabe-Format

```
⛔ Error-Log geschrieben

Error-ID:  {error_id}
Log:       runs/errors/{log_dateiname}
Admin:     {admin_recipients} — ✅ benachrichtigt / ⚠️ fehlgeschlagen
Suspended: {Ja / Nein}
```

---

## Fallback-Konfiguration (wenn Prozess-MD Nicht verfügbar)

Wenn der ABORT vor dem Lesen der Prozess-MD passiert (z.B. Pre-Flight),
sind `use_case_id`, `use_case_name` und `admin_recipients` nicht bekannt.

```
use_case_id:    "unbekannt"
use_case_name:  "unbekannt"
admin_recipients: → aus cowork/CLAUDE.md Abschnitt "Fallback Admin"
                   oder hardcoded Fallback-Adresse
```

> **Empfehlung:** `admin_recipients` als Fallback-Konstante in `cowork/CLAUDE.md`
> definieren — unabhängig vom Prozess-MD.

---

## EU AI Act Mapping

| Element | Artikel | Anforderung |
|---------|---------|-------------|
| Error-Log in Vault | Art. 12 | Lückenlose Protokollierung auch bei Fehler |
| Admin-Benachrichtigung | Art. 14 | Menschliche Aufsicht bei Anomalien |
| Maßnahmen im Log | Art. 9 | Risikomanagement — nächste Schritte klar |
| `status_suspended` dokumentiert | Art. 9 | Automatische Risikoreduktion nachweisbar |

---

## Wichtige Hinweise

1. **Immer aufrufen bei ABORT** — kein ABORT ohne Error-Log
2. **Eigener Fehler-Ordner** — `runs/errors/` getrennt von `runs/` (normale Logs)
3. **Auch bei eigenem Fehler** — wenn Vault-Write fehlschlägt, Plain-Text auf Output
4. **admin_recipients ≠ email_recipients** — Admin-Kanal strikt getrennt vom Business-Report
