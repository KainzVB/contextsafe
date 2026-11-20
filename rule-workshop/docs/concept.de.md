# Konzept: ContextSafe Regelwerkstatt

[English](concept.md) · **Deutsch**

Wie Fachexperten Geschäftslogik ohne zentrales Daten-Team erstellen, ändern, pflegen und *verantworten* können, und was dafür gegenüber dem PoC anders sein musste.

---

## Executive Summary

1. **Leitidee:** Der Fachexperte zertifiziert **Entscheidungen**, nicht Code. Er schreibt die Regel in Worten und entscheidet Grenzfälle. Das SQL ist ein Kompilat, das eine Maschine gegen diese Entscheidungen beweist.
2. **Warum das den Engpass löst:** Im PoC musste der Freigebende SQL lesen, Hashes eintragen und YAML pflegen. Das kann nur IT. Grenzfälle entscheiden kann nur der Fachbereich, und genau dort liegt die Verantwortung.
3. **Was es ersetzt:** Code-Review wird zu Grenzfall-Tests, Testabdeckung zu Gegenproben, Deployment zum Siegel, Change-Management zum Siegelbruch mit Wirkungsvorschau.
4. **Was bleibt:** IT stellt einmalig die Plattform (lesender Zugang, Glossar, Engine). Pro Regel wird sie nicht mehr gebraucht.
5. **Stand:** MVP läuft mit drei Regeln auf zwei Datenquellen, darunter der ursprüngliche TPC-H-Use-Case auf PostgreSQL. Siehe [Nachweis und Grenzen](#nachweis-und-grenzen).

## Das Problem hinter dem Paradigma

„Sobald Code entsteht, braucht es IT“ gilt, weil vier Dinge am Code hängen. Keines davon kann ein Fachexperte leisten, solange das Prüfobjekt Code ist.

| Am Code hängt | Bisher im PoC | Warum das den Fachbereich ausschließt |
|---|---|---|
| Schreiben | Claude erzeugt SQL | gelöst, aber nicht ausreichend |
| Prüfen | Mensch liest SQL, Vier-Augen | Fachexperte kann SQL nicht beurteilen |
| Freigeben | SHA-256 von Hand ins Frontmatter | Terminal, YAML, 6 Skill-Hashes |
| Betreiben | Hash-Gates über 6 Skills | 17 Abbrüche durch Hash-Drift (06–10/2026), Behebung nur durch IT (siehe [Lessons Learned](../../docs/lessons-learned.md)) |

## Die Beweiskette

Jeder Schritt hat genau einen Verantwortlichen. Probabilistisch ist nur, was danach bewiesen wird.

| # | Schritt | Wer | Art | Was es ersetzt |
|---|---|---|---|---|
| 1 | Regel in Klartext | Fachexperte | menschlich | Fachkonzept |
| 2 | Grenzfälle entscheiden | Fachexperte, Claude schlägt vor | menschlich | Abnahmekriterien |
| 3 | Kompilat (SQL) und Beispieldaten | Claude | probabilistisch | Entwicklung |
| 4 | Beweis: Kompilat gegen jeden Grenzfall | Engine | deterministisch | Code-Review, Tests |
| 5 | Gegenproben: Wo legt kein Grenzfall die Regel fest? | Engine | deterministisch | Testabdeckung |
| 6 | Rückübersetzung des Kompilats in Alltagssprache | Claude, frischer Kontext | probabilistisch | zweites Augenpaar |
| 7 | Wirkung auf echten Daten, nur Summen | Engine | deterministisch | Abnahmetest |
| 8 | Freigabe per Dialog außerhalb des Chats | Fachexperte | menschlich | Deployment |
| 9 | Ausführung nur bei gültigem Siegel, mit Protokoll | Engine | deterministisch | Betrieb |

## Vier Mechaniken, die das tragen

### 1. Schattentabellen: gleicher Code, gleiche Datenbank, andere Daten

- Je Grenzfall stellt die Engine die Beispielzeilen als gleichnamige Zwischentabellen vor das Kompilat. Die Abfrage sieht dann nur noch die Beispielwelt.
- Getestet wird damit exakt der Text, der später läuft, auf exakt der Datenbank, mit lesendem Zugriff. Kein Test-Schema, kein zweiter SQL-Dialekt.
- Erfundene Tabellen oder Spalten fallen sofort auf, weil die Engine den echten Datenkatalog kennt.

### 2. Gegenproben: die Maschine findet die Frage, die noch niemand gestellt hat

- Die Engine verfälscht das Kompilat gezielt (`>=` zu `>`, UND zu ODER, Zahl ±1, Textwert, Verneinung, Mehrfachzählung).
- Bemerkt kein Grenzfall die Verfälschung, ist die Regel an dieser Stelle fachlich nicht festgelegt. Daraus wird eine Frage an den Owner.
- Beispiel aus dem MVP: Bei „Upselling-Kandidat“ ließen sechs Grenzfälle zwei Dinge offen: welche Zahl für einen Kunden mit mehreren Abos auf dasselbe Produkt angezeigt wird, und wie sich der Join auf die Produkttabelle verhält. Die Gegenproben haben beides gefunden.
- Der Owner entscheidet (neuer Grenzfall) oder lässt die Lücke mit Begründung und Namen bewusst offen. Auch das Nicht-Entscheiden ist damit dokumentiert.

### 3. Siegel über den fachlichen Inhalt

- Der Hash umfasst Frage, Klartext, Parameter, Grenzfälle, Beispieldaten, bewusst offene Lücken, SQL und die Siegel genutzter Regeln.
- Er wird aus dem gelesenen Inhalt gebildet, nicht aus dem Dateitext. Umformatierte Tabellen brechen ihn nicht, eine geänderte Entscheidung schon.
- Das Feld `status` ist nur Anzeige. Die Engine rechnet das Siegel vor jedem Lauf neu.
- Ändert sich eine Regel, auf der andere aufbauen, ruht die Freigabe aller abhängigen Regeln.

### 4. Freigabe über einen Kanal, den die KI nicht bedient

- `regel_freigeben` öffnet einen macOS-Dialog. Ohne Klick eines Menschen entsteht kein Siegel.
- Freigeben darf nur der eingetragene Owner, nur bei bestandenem Beweis.
- Jede Version wird schreibgeschützt unter `Protokoll/Freigaben/` festgehalten.

## Was sich gegenüber dem PoC ändert

| Befund (siehe [ROADMAP](../../ROADMAP.md), Punkt R) | Antwort der Regelwerkstatt |
|---|---|
| S1/S2: Revenue dreifach definiert, Rundung in Skills dupliziert | Eine Stelle: das Kompilat der Regel. Rundung ist ein Grenzfall (G6 der TPC-H-Regel) |
| „Hash zertifiziert Selbst-Konsistenz, nicht Intent“ | Siegel gibt es nur, wenn das Kompilat die Grenzfälle erfüllt |
| S3/S4: Ablauf steht im Prompt, Orchestrator ungehasht | Ablauf steht in der Engine (Code mit Tests). Skills steuern nur das Gespräch |
| S5: Fehlerprotokoll nicht überall | Engine protokolliert jeden Lauf, auch jede Verweigerung |
| Hash-Drift der Skills, 17 Abbrüche | Skills liegen nicht mehr im *Ausführungs*-Vertrauenspfad und brauchen keine Hashes. Sie bleiben Teil der *Erstellung*, deren Ergebnis ein Mensch weiter freigibt |
| S7: Vertrauensanker unbenannt | Weiter offen: Hash statt Signatur (siehe Grenzen) |

Der PoC selbst bleibt unverändert. Die Zeilen zeigen, wie das neue Design dieselben Schwächen für neue Use Cases behandelt; sie schließen die Befunde der ursprünglichen Pipeline nicht.

Das ContextSafe-Prinzip bleibt und ist jetzt erzwungen statt erbeten: Der MCP-Server bietet kein freies SQL an.

| Werkzeug | SQL | Daten | Rückgabe |
|---|---|---|---|
| `regel_pruefen` | Entwurf | nur Beispieldaten | bestanden oder nicht |
| `regel_wirkung` | Entwurf | echt, lesend | nur Summenwerte |
| `regel_ausfuehren` | nur versiegelt | echt, lesend | Ergebnis laut Regel, begrenzt |

## Zuordnung der Technologien

| Baustein | Aufgabe | Im MVP |
|---|---|---|
| Obsidian-Notiz | System of Record je Regel | `Regeln/*.md` |
| Obsidian Properties | Stand, Owner, Version | Frontmatter, flach gehalten |
| Obsidian Bases | Cockpit über alle Regeln, Läufe, Freigaben | `Regel-Cockpit.base` |
| Obsidian Graph und Links | Abhängigkeiten zwischen Regeln | `nutzt` mit Wikilink |
| Claude Skills | Gesprächsführung mit dem Fachexperten | `regel-werkstatt`, `regel-ausfuehren` |
| MCP-Server | Einziger Weg zu den Daten | `engine/mcp_server.py` |
| Claude-Mod | Cockpit-Pane neben dem Chat, Sperre für direkten Datenzugriff | `mod/regel-cockpit` |
| Subagent | Unabhängige Rückübersetzung | im Skill vorgesehen |
| Engine | Beweis, Siegel, Ausführung | `engine/regelwerk.py`, nur Python-Standardbibliothek |

## Geprüfte Alternativen

| Weg | Warum nicht |
|---|---|
| Eigene Regel-Sprache mit festem Übersetzer | Baut einen Semantic Layer nach, braucht wieder ein Daten-Team für die Sprache |
| Entscheidungstabellen ohne Code (DMN) | Trägt Einzelfall-Entscheidungen, nicht Joins und Kennzahlen über Tabellen |
| Fachexperte prüft Pseudocode | Besser als SQL, bleibt aber Lesen statt Beweisen. Als Rückübersetzung übernommen |
| Zweites Modell bewertet das SQL | Ersetzt eine Schätzung durch zwei. Kein Beweis |

## Nachweis und Grenzen

### Was geprüft ist

| Bereich | Stand |
|---|---|
| Engine: Beweis, Gegenproben, Siegel, Lauf, Wirkung, Abhängigkeiten | 15 automatische Tests, Python 3.9 und 3.14 |
| Drei Regeln gegen ihre Grenzfälle | bestanden auf SQLite und PostgreSQL |
| MCP-Server, fünf Werkzeuge | in Claude Desktop (Code-Tab) geladen; Liste, Freigabe und Lauf live ausgeführt |
| Freigabe-Dialog | eine echte Freigabe durchgeführt (Regel *Aktiver Kunde* v1, 2026-11-11) |
| Sperre im Mod | live: ein Befehl mit `sqlite3` wurde abgelehnt |
| Skills | erkannt und gelistet; noch nicht mit einem Fachexperten durchgespielt |
| Cockpit-Pane, Bases-Cockpit in Obsidian | nicht angesehen |
| Cowork, Zeitplanung | nicht geprüft |

### Grenzen

| Grenze | Folge | Ausbaustufe |
|---|---|---|
| Siegel ist ein Hash, keine Signatur | Wer Schreibrecht und Shell hat, kann es nachrechnen | Signatur mit Schlüssel des Owners, Engine als Dienst |
| Beispieldaten schreibt Claude | Falsche Daten und falsches SQL könnten sich decken | Owner liest die Beispieltabellen; Wirkung als dritte Sicht |
| Gegenproben prüfen keine Sortierung, Join-Art oder fehlende Bedingung | Solche Fehler fängt nur Rückübersetzung oder Wirkung | Weitere Gegenproben |
| Ein Owner, kein Vier-Augen-Prinzip | Reicht nicht für regulierte Regeln | Zweitprüfer mit eigener Bestätigung |
| Demo-Datenbank liegt als Datei im Ordner | Die Sperre im Mod ist Leitplanke, kein Tresor | Datenbank hinter dem Server, Zugang nur dort |
| Freigabe-Dialog nur unter macOS | Anderswo geht nur der Terminal-Befehl | Plattformübergreifende Bestätigung |
| Die Regelebene ist deutsch | Regel-Notizen, Parser-Überschriften und Skills sind deutsch | Sprachneutrales Regelformat |

## Bezug zum Rest dieses Repositories

- Der PoC beweist, dass ein zertifiziertes Artefakt unter Governance ausgeführt werden kann. Die Regelwerkstatt beantwortet, *wer dieses Artefakt erstellt und verantwortet*. Sie berührt die Roadmap-Punkte A (Cockpit), B (Lifecycle-Assistent), C (Erfassung bis Entwurf) und R (Konsistenz-Backlog) von der Seite. Siehe [ROADMAP](../../ROADMAP.md), Punkt J.
- Die Grenzfall-Tabelle ist die „editierbare Mittelstufe“ zwischen Klartext und Code; die Wirkungsvorschau ist ihre Prüfung am Beispielergebnis.
- Es gelten dieselben Zustände wie im [Governance-Modell](../../docs/governance-model.md): draft, review, certified, suspended. Der Unterschied: `certified` wird aus dem Siegel berechnet, nicht getippt.
