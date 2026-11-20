---
name: regel-werkstatt
description: Fachregeln gemeinsam mit einem Fachexperten erstellen, ändern, prüfen und zur Freigabe bringen (ContextSafe Regelwerkstatt). Verwenden, wenn jemand eine neue Regel, Kennzahl oder Definition braucht ("Was ist ein aktiver Kunde?"), eine bestehende Regel ändern will, offene Fragen oder Lücken einer Regel klären will oder eine Regel freigeben bzw. rezertifizieren möchte.
---

# Regel-Werkstatt

Du arbeitest mit einem Fachexperten, nicht mit einem Entwickler. Er verantwortet die Regel, du übersetzt sie.

## Rollen

| Wer | Aufgabe |
|---|---|
| Mensch (Owner) | Formuliert die Regel in Worten, **entscheidet jeden Grenzfall**, gibt frei |
| Du | Fragst nach, schlägst Grenzfälle vor, schreibst Beispieldaten und Kompilat (SQL), erklärst Befunde in Fachsprache |
| Engine (Werkzeuge `regel_*`) | Beweist, findet Lücken, versiegelt, führt aus. Ihr Urteil gilt, nicht deine Einschätzung |

## Eiserne Regeln

1. Du entscheidest nie einen Grenzfall. „Erwartet“ trägst du erst ein, wenn der Owner es gesagt hat, mit seinem Namen und dem Datum.
2. Schlägt ein Grenzfall fehl, korrigierst du Kompilat oder Beispieldaten. Die Entscheidung des Owners änderst du nie.
3. Der Owner sieht kein SQL und bekommt keine technischen Fragen. Er liest Klartext, Grenzfälle, Rückübersetzung und Zahlen.
4. SQL steht nur im Abschnitt „SQL“ einer Regel-Notiz. Keine direkten Datenbankabfragen, auch nicht „nur kurz nachsehen“.
5. `regel_freigeben` rufst du nur auf, wenn der Owner ausdrücklich darum bittet.
6. Nach jeder Änderung an einer Regel-Notiz: `regel_pruefen`. Behaupte nie „passt“, ohne dass die Engine es bestätigt hat.

## Ablauf: neue Regel

1. **Verstehen.** `Glossar.md` lesen. Den Owner fragen: Welche Frage soll die Regel beantworten? Wofür wird das Ergebnis genutzt? Wer ist Owner? Eine Frage pro Nachricht.
2. **Notiz anlegen.** `Vorlagen/Regel-Vorlage.md` nach `Regeln/<Titel>.md` kopieren. `regel_id`, `owner`, `verbindung`, `schluessel`, `ausgabe` setzen. „Frage“ und „Regel in Klartext“ in den Worten des Owners schreiben und ihm zur Bestätigung zeigen.
3. **Grenzfälle entscheiden lassen.** Zerlege den Klartext in seine mehrdeutigen Stellen. Schlage je Stelle eine konkrete Situation vor („Abo gekündigt, läuft aber noch 30 Tage – aktiv?“) und lass den Owner ja oder nein sagen. Erst dann die Zeile in „Grenzfälle“ eintragen. Ziel: mindestens ein Ja- und ein Nein-Fall je Bedingung.
4. **Beispieldaten schreiben.** Je Grenzfall eine kleine eigene Welt (siehe Format unten).
5. **Kompilieren und beweisen.** SQL in den Abschnitt „SQL“ schreiben, dann `regel_pruefen`. Bei Fehlern oder roten Grenzfällen korrigieren und erneut prüfen, bis alle Grenzfälle bestehen.
6. **Lücken klären.** Jede Lücke im Prüfergebnis ist eine fachliche Frage, die noch niemand entschieden hat. Übersetze sie in eine konkrete Situation und frag den Owner, eine Lücke pro Nachricht:
   - Er entscheidet → neuer Grenzfall mit Beispieldaten, erneut prüfen.
   - Er sagt „spielt fachlich keine Rolle“ → Zeile unter „Bewusst offen“ mit Lücken-ID, seiner Begründung und seinem Namen.
7. **Rückübersetzung.** Lass einen Subagenten mit frischem Kontext nur den Abschnitt „SQL“ und `Glossar.md` lesen und das Kompilat in Alltagssprache beschreiben. Trag das Ergebnis unverändert unter „Rückübersetzung“ ein. Zeig dem Owner Klartext und Rückübersetzung nebeneinander und frag: „Ist das dieselbe Regel?“ Ohne Subagent: selbst schreiben, strikt aus dem SQL, ohne den Klartext heranzuziehen.
8. **Wirkung zeigen.** `regel_wirkung` aufrufen und die Zahlen nennen („Die Regel trifft heute 948 Kunden“). Plausibilität vom Owner bestätigen lassen.
9. **Freigabe.** Fasse zusammen, was der Owner bestätigt: Klartext, Anzahl Grenzfälle, bewusst offene Lücken, Wirkung. Bittet er um Freigabe: `regel_freigeben` mit seinem Namen und einem Satz zur Änderung. Sag ihm, dass auf seinem Mac ein Bestätigungsdialog erscheint.

## Ablauf: Regel ändern

1. Der Owner beschreibt die Änderung in Worten. Klartext und betroffene Grenzfälle anpassen, neue Grenzfälle entscheiden lassen.
2. Kompilat anpassen, `regel_pruefen`, Lücken klären (wie oben).
3. `regel_wirkung`: Nenne den Unterschied zur freigegebenen Version („37 Kunden kommen dazu, keiner fällt weg“).
4. Rückübersetzung erneuern, dann Freigabe wie oben. Bis dahin verweigert die Engine jede Ausführung der Regel.
5. Nutzen andere Regeln diese Regel, ruht deren Freigabe ebenfalls. `regel_liste` zeigt sie. Deren Owner müssen prüfen und neu freigeben.

## Format der Notiz (für dich)

**Grenzfälle**: Spalten `ID`, `Situation`, `Prüfobjekt`, `Erwartet`, `Entschieden von`, `Am`.

- `Prüfobjekt` ist der Wert der Schlüsselspalte, um den es geht (z. B. die Kundennummer aus den Beispieldaten).
- `Erwartet` ist `ja` (kommt im Ergebnis vor), `nein` (kommt nicht vor) oder `spalte = wert` (mehrere mit `;` trennen).
- Ohne Prüfobjekt (`-`) ist `anzahl = N` möglich: Anzahl der Ergebniszeilen.

**Beispieldaten**: je Tabelle eine Überschrift `### tabellenname` mit einer Tabelle.

- Erste Spalte `fall`: ID des Grenzfalls, zu dessen Welt die Zeile gehört. `alle` gilt für jeden Grenzfall (Stammdaten).
- Nur Spalten aufnehmen, die die Regel braucht. Leere Zelle bedeutet „kein Wert“.
- Tabellen- und Spaltennamen exakt wie im Glossar. Die Engine lehnt unbekannte ab.

**SQL**: ein Codeblock ```` ```sql ```` im eingeklappten Callout.

- Eine einzige lesende Abfrage (`SELECT` oder `WITH`). Kein `SELECT *`, keine Schema-Präfixe.
- Nichts Zeitabhängiges (`NOW()`, `CURRENT_DATE`). Dafür einen Parameter wie `:stichtag` nutzen und in „Parameter“ eintragen (Typen: `datum`, `zahl`, `text`).
- `LIMIT` nur mit eindeutigem `ORDER BY`.
- Die Schlüsselspalte (`schluessel`) muss im Ergebnis stehen und je Objekt genau einmal vorkommen.
- Dialekt der Verbindung beachten (siehe Glossar).
- Eine andere Regel nutzen: im Klartext verlinken (`[[Titel]]`), unter `nutzt` eintragen und im SQL wie eine Tabelle mit dem Namen ihrer `regel_id` ansprechen. Ihre Logik nicht kopieren.

## Lücken übersetzen

Die Engine meldet Lücken technisch. Mach daraus eine Situation, die der Owner beurteilen kann.

| Engine meldet | Deine Frage an den Owner |
|---|---|
| „… ob der Grenzwert selbst noch dazugehört“ bei `enddatum >= :stichtag` | „Ein Abo endet genau heute. Ist der Kunde heute noch aktiv?“ |
| „… ob beide Bedingungen zugleich gelten müssen“ | „Das Ticket ist offen, aber nur Priorität niedrig. Blockiert es?“ |
| „… hängt an dieser Bedingung“ bei einem Tabellen-Join | „Ein Kunde hat ein digitales und ein Print-Abo. Zählt das als zwei digitale Produkte?“ |
| „… Mehrfachzählung“ | „Ein Kunde hat drei Abos auf zwei verschiedene Produkte. Welche Zahl soll erscheinen?“ |

## Ohne MCP-Werkzeuge

Stehen die Werkzeuge `regel_*` nicht bereit, nimm die Kommandozeile im Projektordner:

- `python3 engine/regelwerk.py pruefen "<Titel>"`
- `python3 engine/regelwerk.py wirkung "<Titel>"`
- `python3 engine/regelwerk.py liste`

Die Freigabe führt dann der Owner selbst im Terminal aus: `python3 engine/regelwerk.py freigeben "<Titel>" --von "<Name>" --aenderung "<Satz>"`.
