# ContextSafe Regelwerkstatt (MVP)

[English](README.md) · **Deutsch**

**Fachexperten erstellen, ändern und verantworten Geschäftsregeln selbst. Sie entscheiden die Grenzfälle, Claude übersetzt, eine deterministische Engine beweist und versiegelt.**

> Modelle schätzen. Eine deterministische Engine beweist. Menschen geben frei. Jeder Lauf hinterlässt Nachweise.

Der ContextSafe-PoC (siehe [Haupt-README](../README.de.md)) zeigt, wie ein *zertifiziertes* Artefakt unter Governance ausgeführt wird. Eine Frage lässt er offen: **Wer erstellt und verantwortet dieses Artefakt?** In der Praxis war es die IT, weil das Artefakt Code ist. Die Geschäftsregeln liegen aber in den Köpfen der Fachexperten, die Code weder schreiben noch prüfen können.

Die Regelwerkstatt verlagert, was zertifiziert wird, vom Code auf die **Entscheidungen**. Die ausführliche Begründung steht im [Konzept](docs/concept.de.md).

**Stand (2026-11-20):** MVP. Drei Regeln auf zwei Datenquellen, eine davon versiegelt. Keine Produktivsoftware. Siehe [Nachweis und Grenzen](docs/concept.de.md#nachweis-und-grenzen).

---

## So funktioniert es

```
Fachexperte   schreibt die Regel in Klartext und entscheidet jeden Grenzfall
Claude        schlägt Grenzfälle vor, schreibt Beispieldaten und das SQL
Engine        beweist das SQL gegen jeden Grenzfall (Schattentabellen),
              verfälscht es gezielt, um unentschiedene Fragen zu finden (Gegenproben)
Fachexperte   sieht die Wirkung auf echten Daten (nur Summen) und gibt per System-Dialog frei
Engine        versiegelt den Inhalt (SHA-256) und führt die Regel erst dann aus, mit Lauf-Protokoll
```

| Eigenschaft | So wird sie erzwungen |
|---|---|
| Die KI kann nicht freigeben | Die Freigabe öffnet einen macOS-Dialog außerhalb des Chats. Freigeben darf nur der eingetragene Owner |
| Die KI kann kein freies SQL ausführen | Der MCP-Server hat kein solches Werkzeug. Echte Daten kommen nur aus versiegelten Regeln |
| Änderungen rutschen nicht durch | Das Siegel umfasst Frage, Regeltext, Parameter, Grenzfälle, Beispieldaten und SQL. Ändert sich eines, wird die Ausführung verweigert |
| Rohdaten bleiben aus dem Kontext | Entwürfe laufen auf Beispieldaten oder liefern nur Summen. Versiegelte Regeln liefern das begrenzte Ergebnis |
| Jeder Lauf ist belegt | Jeder Lauf und jede Verweigerung schreibt ein Protokoll unter `Protokoll/Läufe/` |

---

## Schnellstart

Voraussetzung: Python 3.9 oder neuer, nur Standardbibliothek. Keine Installation.

```bash
cd rule-workshop
python3 engine/tests/test_regelwerk.py        # 15 Tests
python3 engine/regelwerk.py liste             # Stand aller Regeln
python3 engine/regelwerk.py pruefen "Upselling-Kandidat"   # Beweis + offene Fragen
```

Die Regel *Aktiver Kunde* ist versiegelt (Version 1), `liste` zeigt sie daher als `certified`. *Upselling-Kandidat* hat bewusst zwei offene Fragen.

### Mit Claude

1. Den Ordner `rule-workshop/` in Claude Code oder im Code-Tab von Claude Desktop als Arbeitsordner öffnen. `.mcp.json`, `CLAUDE.md` und die zwei Skills werden von dort geladen.
2. Den MCP-Server `regelwerk` zulassen.
3. In dieser Reihenfolge ausprobieren:

| # | Sagen | Was passiert |
|---|---|---|
| 1 | „Wie viele aktive Kunden haben wir?“ | Antwort aus der versiegelten Regel, mit Version, Owner und Lauf-Protokoll |
| 2 | In `Regeln/Aktiver Kunde.md` beim Grenzfall G3 den Erwartungswert von `nein` auf `ja` ändern, dann erneut fragen | Die Ausführung wird verweigert: Die Entscheidung hat sich seit der Freigabe geändert |
| 3 | Änderung mit `git checkout -- Regeln/` zurücknehmen | Die Regel läuft wieder |
| 4 | „Lass uns die offenen Fragen von Upselling-Kandidat klären.“ Vorher sich selbst als `owner` in die Notiz eintragen | Claude macht aus jeder Lücke eine konkrete Situation, die du entscheidest |
| 5 | „Gib Upselling-Kandidat frei. Ich bin der Owner.“ | Auf dem Mac erscheint ein Dialog. Ohne deinen Klick entsteht kein Siegel |

Ohne Claude gibt der Owner im Terminal frei: `python3 engine/regelwerk.py freigeben "<Regel>" --von "<Owner>" --aenderung "<ein Satz>"`.

### Optional

- **Obsidian:** das Repository oder nur diesen Ordner als Vault öffnen. `Regel-Cockpit.base` zeigt alle Regeln, Handlungsbedarf, fällige Rezertifizierungen, Läufe und Freigaben (Bases, Obsidian 1.9 oder neuer).
- **Claude-Mod:** `claude --plugin-dir mod/regel-cockpit` ergänzt eine Cockpit-Pane neben dem Chat und lehnt direkte Datenbank-Befehle in diesem Ordner ab.
- **TPC-H-Regel:** *Top 10 Shipping Priorities* braucht den PostgreSQL-Container des ursprünglichen PoC. Die Verbindung steht in `engine/regelwerk.config.json`. Ohne diesen Container bleibt sie nicht erreichbar.
- **Demo-Daten:** `python3 daten/demo_daten_erzeugen.py` erzeugt die SQLite-Demo-Datenbank neu (fester Seed).

---

## Die fünf Werkzeuge

| Werkzeug | Zweck | Sieht echte Daten |
|---|---|---|
| `regel_liste` | Regeln und ihr tatsächlicher Stand | nein |
| `regel_pruefen` | Beweis gegen Grenzfälle, Gegenproben, Prüfprotokoll | nein, nur Beispieldaten |
| `regel_wirkung` | Trefferzahl und Unterschied zur freigegebenen Version | ja, gibt nur Summen zurück |
| `regel_freigeben` | Siegel nach Bestätigung durch den Owner | nein |
| `regel_ausfuehren` | Lauf einer versiegelten Regel mit Protokoll | ja |

---

## Struktur

```
rule-workshop/
├── README.md, README.de.md
├── docs/concept.md, concept.de.md      ← Begründung, Alternativen, Grenzen
├── Regeln/                             ← eine Notiz je Regel: das System of Record
├── Vorlagen/Regel-Vorlage.md           ← Vorlage für eine neue Regel
├── Glossar.md                          ← die Daten und ihre fachliche Bedeutung
├── Regel-Cockpit.base                  ← Obsidian-Bases-Übersicht
├── Protokoll/
│   ├── Freigaben/                      ← freigegebener Stand je Version, schreibgeschützt
│   └── Läufe/                          ← ein Protokoll je Lauf, auch bei Verweigerung
├── engine/
│   ├── regelwerk.py                    ← deterministischer Kern, kein LLM
│   ├── mcp_server.py                   ← die fünf Werkzeuge für Claude
│   ├── regelwerk.config.json           ← Verbindungen und Grenzwerte, keine Zugangsdaten
│   └── tests/test_regelwerk.py
├── daten/                              ← Demo-Datenbank und ihr Erzeuger
├── mod/regel-cockpit/                  ← Claude-Mod: Cockpit-Pane und Sperre
├── .mcp.json, CLAUDE.md, .claude/skills/   ← Einbindung in Claude (2 Skills, 1 MCP-Server)
```

> **Sprachhinweis:** Die Regelebene ist bewusst deutsch. Regel-Notizen, die vom Parser erwarteten Abschnittsüberschriften, die Skills und die Projektanweisungen sind für deutschsprachige Fachexperten geschrieben. Die Dokumentation ist zweisprachig (Englisch als Standard). Ein sprachneutrales Regelformat steht als Grenze im [Konzept](docs/concept.de.md#grenzen).
>
> **Demo-Daten:** Der Owner der versiegelten Beispiel-Regel ist der Autor des Repositories. Der Ordner `Protokoll/` enthält die echten Freigabe- und Lauf-Protokolle des MVP als Beispiele. In einem echten Einsatz gehört dieses Archiv in den Speicher des Kunden, nicht in Git.

---

## Bezug zum PoC

| | PoC (Repository-Wurzel) | Regelwerkstatt (dieser Ordner) |
|---|---|---|
| Zertifiziertes Objekt | SQL-Skript und sechs Skills, per Hash fixiert | Die Entscheidungen: Grenzfälle und Regeltext, mit dem SQL versiegelt |
| Wer erstellt es | IT, mit Claude | Fachexperte, mit Claude |
| Wer beweist es | Ein Mensch liest das SQL | Die Engine, gegen die Grenzfälle |
| Orchestrierung | Ein LLM (CoWork) | Deterministische Engine, LLM nur für das Gespräch |

Der PoC bleibt unverändert. Siehe [ROADMAP](../ROADMAP.md), Punkt J.

Lizenz: [MIT](../LICENSE).
