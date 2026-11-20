# Einrichtung: ContextSafe Regelwerkstatt

[English](setup.md) · **Deutsch**

Wie die Umgebung eingerichtet wird, von „läuft auf der Kommandozeile“ bis „Fachexperte arbeitet in Claude“. Jede Stufe baut auf der vorherigen auf und endet mit einer Prüfung.

---

## Überblick

| Stufe | Ergebnis | Braucht |
|---|---|---|
| 1. Engine | Beweis, Gegenproben, Siegel und Lauf im Terminal | Python 3.9+ |
| 2. Claude | Gespräch mit Claude, MCP-Werkzeuge, Skills | Stufe 1, Claude Code oder Claude Desktop |
| 3. Cockpit | Übersicht aller Regeln in Obsidian | Stufe 1, Obsidian 1.9+ |
| 4. Claude-Mod | Cockpit-Pane neben dem Chat, Sperre gegen direkten Datenzugriff | Stufe 2 |
| 5. TPC-H-Regel | Der ursprüngliche PoC-Use-Case auf PostgreSQL | Stufe 1, Docker, die PoC-Datenbank |

Stufe 1 und 2 genügen für die Demo mit den SQLite-Beispieldaten. Stufe 3 bis 5 sind optional und voneinander unabhängig.

## Voraussetzungen

| Komponente | Version | Hinweis |
|---|---|---|
| Python | 3.9 oder neuer | Nur Standardbibliothek, kein `pip install`. Getestet mit 3.9 und 3.14. macOS bringt 3.9 mit den Xcode-Kommandozeilen-Tools mit |
| Git | beliebig | Zum Klonen und zum Zurücknehmen von Demo-Änderungen |
| macOS | aktuell | Nur für den Freigabe-Dialog. Sonst im Terminal freigeben (siehe [Freigabe auf anderen Systemen](#freigabe-auf-anderen-systemen)) |
| Claude Code oder Claude Desktop (Code-Tab) | aktuell | Für Stufe 2 und 4 |
| Obsidian | 1.9 oder neuer | Für Stufe 3. Bases ist seit 1.9 ein Kern-Plugin |
| Docker | beliebig | Nur für Stufe 5 |

## Stufe 1: Engine

```bash
git clone https://github.com/KainzVB/contextsafe.git
cd contextsafe/rule-workshop
python3 engine/tests/test_regelwerk.py
python3 engine/regelwerk.py liste
```

**Prüfung**

- Die Tests enden mit `OK` (15 Tests).
- `liste` zeigt drei Regeln. *Aktiver Kunde* ist `certified` und ausführbar. *Upselling-Kandidat* ist `draft`, *Top 10 Shipping Priorities* ist `review`.

Hinweise

- Die Demo-Datenbank `daten/abo_welt.sqlite` liegt im Repository. Neu erzeugen: `python3 daten/demo_daten_erzeugen.py` (fester Seed).
- Das versiegelte Beispiel läuft am **2027-05-11** ab (Rezertifizierungs-Intervall: 6 Monate, `rezertifizierung_monate` in `engine/regelwerk.config.json`). Danach zeigt `liste` es als `suspended` mit dem Grund „Rezertifizierung überfällig“. Das ist gewollt: neu freigeben.
- Die Arbeitskopie nicht in einem Cloud-Sync-Ordner halten. Die Engine schreibt Notizen und Protokolle, und Sync-Konflikte sähen aus wie manuelle Änderungen.

## Stufe 2: Claude

1. Den **Ordner `rule-workshop/` selbst** als Arbeitsordner in Claude Code (`cd rule-workshop && claude`) oder im Code-Tab von Claude Desktop öffnen. Wird die Repository-Wurzel geöffnet, werden MCP-Server und Projektanweisungen nicht geladen.
2. Beim ersten Start den MCP-Server **`regelwerk`** zulassen. Er steht in `.mcp.json` und startet `engine/mcp_server.py` mit deinem `python3`.
3. Die Skills `regel-werkstatt` (Regeln erstellen und ändern) und `regel-ausfuehren` (Datenfragen beantworten) werden automatisch aus `.claude/skills/` geladen.

**Prüfung**

- In Claude fragen: „Welche Regeln gibt es?“. Claude ruft `regel_liste` auf und nennt drei Regeln.
- Fragen: „Wie viele aktive Kunden haben wir?“. Claude ruft `regel_ausfuehren` auf und antwortet mit Regel, Version, Owner und einem Lauf-Protokoll unter `Protokoll/Läufe/`.

Was der MCP-Server anbietet: fünf Werkzeuge, kein freies SQL. Siehe [README](../README.de.md#die-fünf-werkzeuge).

### Rollen

| Rolle | Tut | Braucht |
|---|---|---|
| Plattform (einmalig) | Lesender Datenzugang, [Glossar.md](../Glossar.md), Verbindungseintrag in `engine/regelwerk.config.json` | Zugriff auf die Datenquelle |
| Owner (je Regel) | Entscheidet Grenzfälle, gibt frei | Den eigenen Namen in der Eigenschaft `owner` der Regel-Notiz, einen Mac für den Dialog |

Um selbst eine Freigabe auszuprobieren, zuerst den eigenen Namen als `owner` in `Regeln/Upselling-Kandidat.md` eintragen. Die Freigabe funktioniert nur, wenn der übergebene Name genau dem Eintrag `owner` entspricht.

### Freigabe auf anderen Systemen

Der Dialog nutzt macOS `osascript`. Fehlt er, fragt die Engine über die Tastatur, was nur in einem Terminal geht. Der MCP-Server hat kein Terminal, deshalb unter Linux und Windows in einer Shell freigeben:

```bash
python3 engine/regelwerk.py freigeben "Upselling-Kandidat" --von "Dein Name" --aenderung "Erstfreigabe"
```

Der Dialog erscheint auf dem Rechner, auf dem der MCP-Server läuft. In einer Remote- oder Cloud-Sitzung siehst du ihn nicht, und die Freigabe wird nicht bestätigt.

## Stufe 3: Obsidian-Cockpit

1. In Obsidian den Ordner `rule-workshop/` (oder das ganze Repository) als Vault öffnen.
2. `Regel-Cockpit.base` öffnen. Fünf Ansichten: alle Regeln, Handlungsbedarf, Rezertifizierung fällig, Läufe, Freigaben.

**Prüfung:** Die Ansicht *Alle Regeln* listet drei Regeln mit Status, Grenzfällen (bestanden) und Festigkeit.

Hinweise

- Das Cockpit filtert nach den Tags `typ/regel`, `typ/freigabe` und der Eigenschaft `typ: lauf`. Beim Kopieren einer Regel-Notiz beibehalten.
- Automatische Formatierer (zum Beispiel das Linter-Plugin beim Speichern) können Regel-Notizen verändern. Groß- und Kleinschreibung sowie Leerraum in Überschriften und Tabellen werden toleriert und brechen das Siegel nicht. Wird eine Abschnittsüberschrift umbenannt, bricht das Parsen, deshalb diesen Ordner von Überschrift-Regeln ausnehmen.

## Stufe 4: Claude-Mod

```bash
cd rule-workshop
claude --plugin-dir mod/regel-cockpit
```

Er ergänzt eine Pane **Regel-Cockpit** (Befehl `/regel-cockpit`) und lehnt Befehle ab, die direkt an Daten gehen: alles mit `sqlite3`, `psql`, `pg_dump`, `duckdb` oder `.sqlite` sowie Datenbank-Werkzeuge anderer MCP-Server.

- Claude aus `rule-workshop/` starten. Der Mod schaltet sich nur dort ein, wo `engine/regelwerk.py` existiert.
- Die Sperre vergleicht Text. Ein harmloser Befehl, der nur eine `.sqlite`-Datei erwähnt, wird ebenfalls abgelehnt. Sie ist eine Leitplanke, kein Tresor (siehe [Grenzen](concept.de.md#grenzen)).
- Das Laden aus diesem Ordner mit `--plugin-dir` folgt der Dokumentation für Claude-Code-Mods. Erprobt ist er als heiß geladener Mod in Claude Desktop, nicht aus diesem Repository-Ordner.

## Stufe 5: TPC-H-Regel auf PostgreSQL

Die Regel *Top 10 Shipping Priorities* liest die Datenbank des ursprünglichen PoC.

| Einstellung | Wert in `engine/regelwerk.config.json` |
|---|---|
| Verbindungsart | `postgres-docker` |
| Container | `tpch-postgres` (an den eigenen Containernamen anpassen) |
| Datenbank | `tpch` |
| Benutzer | `readonly_user` (braucht `SELECT` auf die drei Tabellen) |
| Schema | `public` |
| Tabellen | `tpch_customer`, `tpch_orders`, `tpch_lineitems` (Datumsspalten sind Text) |

So verbindet sich die Engine: Sie ruft `docker exec <container> psql ...` auf und setzt die Sitzung auf nur lesend mit einem Zeitlimit je Abfrage. Passwörter werden nicht behandelt, der Benutzer muss sich also innerhalb des Containers ohne Passwort verbinden dürfen. Alles andere braucht eine Erweiterung des Connectors.

**Prüfung**

```bash
python3 engine/regelwerk.py pruefen "Top 10 Shipping Priorities"
```

Erwartet: sechs von sechs Grenzfällen bestanden, keine Fehler. Fehlt der Container, meldet das Ergebnis, dass die Datenbank nicht erreichbar ist. Die beiden anderen Regeln sind davon nicht betroffen.

Das Repository enthält keinen Loader für die TPC-H-Daten. Sie selbst laden (der PoC nutzte etwa Scale Factor 1), in eine Datenbank `tpch` mit den oben genannten Tabellennamen. Der Datenpfad des PoC steht in [architecture](../../docs/architecture.md) (Englisch).

---

## Fehlersuche

| Symptom | Ursache | Abhilfe |
|---|---|---|
| `regelwerk` wird in Claude nicht angeboten | Ordner an der Repository-Wurzel geöffnet | `rule-workshop/` selbst öffnen |
| MCP-Server startet nicht | `python3` fehlt im PATH des Claude-Prozesses | `python3 --version` in derselben Shell prüfen, Claude aus dieser Shell starten |
| „Ausführung verweigert – noch nie freigegeben“ | Regel nie freigegeben | Erwartet. Als Owner freigeben |
| „… geändert seit Freigabe: Grenzfälle“ | Entscheidung oder SQL nach der Freigabe geändert | Gewollt. Prüfen, dann neu freigeben. Bei einer Demo-Änderung: `git checkout -- Regeln/` |
| „… Rezertifizierung überfällig“ | Rezertifizierungsdatum überschritten | Neu freigeben |
| „Nur der Owner (...) darf diese Regel freigeben“ | `von` weicht von der Eigenschaft `owner` ab | Genau den Namen aus der Notiz verwenden |
| Kein Dialog erscheint | Nicht macOS oder Remote-Sitzung | Im Terminal auf dem Rechner freigeben, auf dem die Engine läuft |
| „Freigabe nicht bestätigt“ | Dialog abgebrochen oder nach 120 s abgelaufen | Freigabe erneut anstoßen |
| „Direkter Datenzugriff ist hier gesperrt“ | Die Sperre im Mod hat einen Befehl erkannt | Die Regel-Werkzeuge nutzen. Bei Dateiarbeit die erkannten Wörter im Befehl vermeiden |
| „Verbindung ... nicht eingerichtet“ oder Datenbank nicht erreichbar | Verbindung fehlt oder Container aus | `engine/regelwerk.config.json` und `docker ps` prüfen |
| „Das Kompilat läuft nicht: ...“ | Das SQL passt nicht zur Datenquelle | SQL in der Notiz korrigieren, Tabellen- und Spaltennamen im [Glossar.md](../Glossar.md) |
| Ordner `Protokoll/Läufe` fehlt oder doppelt | Andere Unicode-Form des Umlauts (NFC/NFD) nach dem Kopieren | Das Repository speichert NFC. Neu klonen statt über ein Werkzeug zu kopieren, das Namen umschreibt |

## Deinstallation

Es wird nichts installiert. Den Ordner löschen. Der MCP-Eintrag steht in `.mcp.json` im Ordner, und der Mod wird nur für die Sitzung geladen, die ihn nennt.
