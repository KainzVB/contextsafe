---
name: skill_log_run_to_obsidian
description: >
  Writes a complete, auditable run log (Markdown) and result archive (HTML) to
  the Obsidian Vault as the final step of the ContextSafe pipeline. Use this skill
  after skill_send_html_email has completed — it receives the full context of all
  previous steps including execution results, narrative report, and email status.
  Triggers on phrases like "schreibe den Run-Log", "logge den Run", "speichere das
  Ergebnis im Vault", "log the run", or automatically as the last step of the pipeline.
  Always runs as the final step, even if upstream steps (email, narrativization) failed
  — the log is the primary audit artifact and must capture the complete run status.
---

# skill_log_run_to_obsidian

## Verantwortung

Vollständigen, auditierbaren Run-Log als Markdown-Datei und Ergebnis-HTML-Archiv
ins Obsidian Vault schreiben. **Letzter Step** in der ContextSafe-Pipeline —
hat dadurch den vollständigen Kontext aller vorherigen Steps.

**Kernprinzip:** Der Run-Log ist das primäre Audit-Artefakt. Er dokumentiert
nicht nur das Ergebnis, sondern auch den Email-Status und alle Warnungen.
Muss ausgeführt werden, auch wenn Steps 3 oder 4 fehlschlugen.

---

## Erwarteter Eingabe-Kontext

Aus `execution_context` (von `skill_execute_sql_postgres`, vollständig):

| Feld | Pflicht | Beschreibung |
|------|---------|-------------|
| `use_case_id` | ✅ | z.B. `TPCH-Q3-001` |
| `use_case_name` | ✅ | z.B. `Top 10 Shipping Priorities` |
| `certified_script` | ✅ | Dateiname des Scripts |
| `certified_script_hash` | ✅ | SHA-256 |
| `rows` | ✅ | Ergebniszeilen |
| `row_count` | ✅ | Anzahl Zeilen |
| `timestamp` | ✅ | ISO-Zeitstempel der Execution |
| `gates_passed` | ✅ | z.B. `8/8` |
| `approved_by` | ✅ | Approver |
| `version` | ✅ | Prozess-MD Version |
| `db_connection_ref` | ✅ | DB-Connector |
| `email_recipients` | ✅ | Empfängerliste |

Aus `narrative_context` (von `skill_narrativize_result`, optional):

| Feld | Pflicht | Beschreibung |
|------|---------|-------------|
| `html_report` | ❌ | HTML-Report für Result-HTML |
| `narrative_text` | ❌ | Plain-Text für Log-MD |
| `fallback_used` | ❌ | War Haiku-Fallback aktiv? |

Aus `email_context` (von `skill_send_html_email`):

| Feld | Pflicht | Beschreibung |
|------|---------|-------------|
| `email_sent` | ✅ | `true` oder `false` |
| `email_timestamp` | ❌ | ISO-Zeitstempel des Versands |
| `email_recipients` | ✅ | Tatsächliche Empfänger |
| `email_subject` | ❌ | Gesendeter Subject-String |
| `email_error` | ❌ | Fehlermeldung bei Versandproblem |

---

## Ablauf (Schritt für Schritt)

### Schritt 1 — Dateinamen und Pfade bestimmen

```
Datum:       YYYYMMDD aus timestamp
Slug:        use_case_name → lowercase, Leerzeichen → _
             "Top 10 Shipping Priorities" → "top_10_shipping_priorities"
Run-ID:      run_{YYYYMMDD}_{NNN} — NNN aufsteigend aus bestehenden Logs
Log-Pfad:    zDevPlayground/determinismArchitecture/runs/run_{YYYYMMDD}_{NNN}_{slug}.md
Result-Pfad: zDevPlayground/determinismArchitecture/results/result_{YYYYMMDD}_{NNN}_{slug}.html
```

Kein Überschreiben — NNN erhöhen falls Pfad bereits existiert.

### Schritt 2 — Ergebnistabelle als Markdown

Konvertiere `rows` in Markdown-Tabelle:
- Revenue: Tausender-Punkt, Dezimal-Komma, 2 Stellen

### Schritt 3 — Run-Log MD aufbauen

```markdown
---
run_id: {run_id}
use_case_id: {use_case_id}
use_case_name: {use_case_name}
script: {certified_script}
script_hash_certified: {certified_script_hash}
executed_by: CoWork (Sonnet)
run_date: {YYYY-MM-DD}
status: success | partial | failed
rows_returned: {row_count}
gates_passed: {gates_passed}
narrative_available: true | false
email_sent: true | false
tags:
  - typ/run-log
  - thema/tpch
  - status/{success|partial|failed}
---

# Run-Log: {use_case_name} — {YYYY-MM-DD}

## Ausführungskontext

| Parameter | Wert |
|-----------|------|
| Run-ID | `{run_id}` |
| Use Case | {use_case_id} — {use_case_name} |
| Script | `assets/scripts/{certified_script}` |
| DB-Connector | `{db_connection_ref}` |
| Ausgeführt | {timestamp} |
| Gates | {gates_passed} bestanden |
| Modell | Sonnet (Orchestrierung) + Haiku (Narrativierung) |

## Prozess-MD Referenz

| Feld | Wert |
|------|------|
| Version | {version} |
| Approver | {approved_by} |

## Ergebnis

{markdown_tabelle}

## Narrativ

{narrative_text — oder "⚠️ Nicht verfügbar (Haiku-Fallback aktiv)" wenn fallback_used}

## Email-Versand

| Feld | Wert |
|------|------|
| Gesendet | ✅ Ja / ⚠️ Fehlgeschlagen |
| Zeitstempel | {email_timestamp} |
| Empfänger | {email_recipients} |
| Subject | {email_subject} |
| Fehler | {email_error oder "—"} |

## Auffälligkeiten & Warnungen

{Leer wenn keine — sonst alle Warnungen aus Steps 1–4}

## Archiv

→ `results/result_{YYYYMMDD}_{NNN}_{slug}.html`
```

### Schritt 4 — Result-HTML aufbauen

Verwende `html_report` aus `narrative_context` als Basis.
Fallback wenn nicht verfügbar: Ergebnistabelle ohne Narrativ.

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <title>ContextSafe — {use_case_name} — {YYYY-MM-DD}</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 800px;
           margin: 40px auto; padding: 0 20px; color: #1a1a1a; }
    table { border-collapse: collapse; width: 100%; margin: 16px 0; }
    th, td { border: 1px solid #ddd; padding: 8px 12px; text-align: left; }
    th { background: #f5f5f5; font-weight: 600; }
    .governance { background: #f0f4ff; padding: 12px; border-radius: 4px;
                  font-size: 0.85em; color: #444; margin-top: 24px; }
    .email-status { background: #f0fdf4; padding: 8px 12px; border-radius: 4px;
                    font-size: 0.85em; margin-top: 12px; }
    .email-failed { background: #fef2f2; }
  </style>
</head>
<body>
  {html_report_inhalt}

  <div class="email-status {email-failed wenn nicht gesendet}">
    📧 Email: {✅ Gesendet an {email_recipients} / ⚠️ Fehlgeschlagen: {email_error}}
  </div>

  <div class="governance">
    <strong>ContextSafe Audit-Trail</strong><br>
    Run-ID: {run_id} &nbsp;|&nbsp;
    Use Case: {use_case_id} &nbsp;|&nbsp;
    Script-Hash: {certified_script_hash} &nbsp;|&nbsp;
    Approver: {approved_by}
  </div>
</body>
</html>
```

### Schritt 5 — In Vault schreiben

```
1. vault_write(path = log_pfad, content = log_md)
2. vault_write(path = result_pfad, content = result_html)
```

`vault_write` überschreibt ohne Warnung. Deshalb vorher per `vault_list` auf den Zielordner prüfen,
ob der Pfad frei ist, sonst NNN erhöhen (Regel „Kein Überschreiben“).

Bei Fehler: 3 Retry-Versuche mit 5s Pause.
Bei weiterhin Fehler: Log als Plain-Text auf Kontext-Output ausgeben.

---

## Ausgabe-Format bei Erfolg

```
✅ Run-Log geschrieben — Pipeline abgeschlossen

Run-ID:  {run_id}
Log:     runs/{log_filename}
Archiv:  results/{result_filename}
Email:   ✅ gesendet / ⚠️ fehlgeschlagen
Status:  {success | partial}
```

---

## EU AI Act Mapping

| Schritt | Artikel | Anforderung |
|---------|---------|-------------|
| Run-Log mit Script-Hash | Art. 12 | Protokollierungspflicht |
| Email-Status im Log | Art. 12 | Vollständiger Audit-Trail |
| Approver im Log | Art. 14 | Menschliche Aufsicht nachweisbar |
| Prozess-MD Version | Art. 17 | Qualitätsmanagement |
| Result-HTML als Archiv | Art. 12 | Langzeitprotokollierung |

---

## Wichtige Hinweise

1. **Immer als letzter Step** — hat dadurch vollständigen Kontext aller vorherigen Steps
2. **email_context auswerten** — Email-Status immer dokumentieren, auch bei Fehler
3. **Narrative optional** — wenn Step 3 fehlschlug, trotzdem schreiben
4. **Kein Überschreiben** — NNN erhöhen falls Run-ID bereits existiert
5. **Letzter Fallback** — wenn Vault nicht erreichbar, Log als Plain-Text ausgeben
