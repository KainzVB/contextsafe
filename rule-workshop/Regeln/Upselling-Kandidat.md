---
regel_id: upselling_kandidat
owner:
verbindung: abo_welt
schluessel: kunde_id
ausgabe: tabelle
max_zeilen: 20
nutzt:
  - "[[Aktiver Kunde]]"
status: draft
version: 0
siegel:
freigegeben_von:
freigegeben_am:
naechste_rezertifizierung:
grenzfaelle_bestanden: "6/6"
festigkeit: 91
offene_fragen: 2
letzte_pruefung: 2026-11-11
letzter_lauf:
tags:
  - typ/regel
  - thema/determinismus
---
# Upselling-Kandidat

## Frage

Welche aktiven Kunden sind Upselling-Kandidaten?

## Regel in Klartext

Upselling-Kandidat ist ein [[Aktiver Kunde]], der

- in **aktiven** Abos mindestens **zwei unterschiedliche digitale Produkte** hat und
- **kein offenes Ticket mit Priorität „hoch“** hat.

Ausgegeben wird je Kandidat die Anzahl seiner unterschiedlichen digitalen Produkte – die Kandidaten mit den meisten Produkten zuerst.

## Parameter

| Name | Typ | Standard | Im Test |
|---|---|---|---|
| stichtag | datum | heute | 2026-11-11 |

## Grenzfälle

> Jede Zeile ist eine fachliche Entscheidung. „Erwartet“ ändert nur der Owner.

| ID | Situation | Prüfobjekt | Erwartet | Entschieden von | Am |
|---|---|---|---|---|---|
| G1 | Zwei aktive Abos auf zwei verschiedene Digitalprodukte | 1 | anzahl_produkte = 2 | Vorlage | 2026-11-11 |
| G2 | Nur ein Abo, gekündigt, Laufzeit endet in 30 Tagen | 2 | nein | Vorlage | 2026-11-11 |
| G3 | Nur ein Abo, pausiert | 3 | nein | Vorlage | 2026-11-11 |
| G4 | Zwei aktive Abos auf dasselbe Digitalprodukt | 4 | nein | Vorlage | 2026-11-11 |
| G5 | Wie G1, aber ein offenes Ticket mit Priorität hoch | 5 | nein | Vorlage | 2026-11-11 |
| G6 | Wie G1, aber ein offenes Ticket mit Priorität niedrig | 6 | ja | Vorlage | 2026-11-11 |

## Beispieldaten

> Je Grenzfall eine kleine eigene Welt. „alle“ in der Spalte „fall“ gilt für jeden Grenzfall.

### produkte

| fall | produkt_id | name | kategorie |
|---|---|---|---|
| alle | 1 | Tageszeitung Print | print |
| alle | 2 | E-Paper | digital |
| alle | 3 | News-App Plus | digital |

### abos

| fall | abo_id | kunde_id | produkt_id | status | enddatum |
|---|---|---|---|---|---|
| G1 | 11 | 1 | 2 | aktiv | |
| G1 | 12 | 1 | 3 | aktiv | |
| G2 | 21 | 2 | 2 | gekündigt | 2026-12-11 |
| G3 | 31 | 3 | 2 | pausiert | |
| G4 | 41 | 4 | 2 | aktiv | |
| G4 | 42 | 4 | 2 | aktiv | |
| G5 | 51 | 5 | 2 | aktiv | |
| G5 | 52 | 5 | 3 | aktiv | |
| G6 | 61 | 6 | 2 | aktiv | |
| G6 | 62 | 6 | 3 | aktiv | |

### tickets

| fall | ticket_id | kunde_id | prioritaet | offen |
|---|---|---|---|---|
| G5 | 501 | 5 | hoch | 1 |
| G6 | 601 | 6 | niedrig | 1 |

## Bewusst offen

| Lücke | Begründung | Entschieden von |
|---|---|---|

## SQL

> [!abstract]- Kompilat – von Claude aus dem Klartext erzeugt. Bewiesen wird es durch die Grenzfälle, nicht durch Lesen.
> ```sql
> SELECT a.kunde_id, COUNT(DISTINCT a.produkt_id) AS anzahl_produkte
> FROM abos a
> JOIN produkte p ON p.produkt_id = a.produkt_id
> JOIN aktiver_kunde ak ON ak.kunde_id = a.kunde_id
> WHERE a.status = 'aktiv'
>   AND p.kategorie = 'digital'
>   AND NOT EXISTS (
>         SELECT 1 FROM tickets t
>         WHERE t.kunde_id = a.kunde_id AND t.offen = 1 AND t.prioritaet = 'hoch')
> GROUP BY a.kunde_id
> HAVING COUNT(DISTINCT a.produkt_id) >= 2
> ORDER BY anzahl_produkte DESC, a.kunde_id
> ```

## Rückübersetzung

> So liest eine unabhängige Instanz das Kompilat – ohne den Klartext oben zu kennen.

Nimm alle Abos mit Status „aktiv“, deren Produkt zur Kategorie „digital“ gehört und deren Kunde nach der Regel „Aktiver Kunde“ aktiv ist. Lass Kunden weg, für die es ein offenes Ticket mit Priorität „hoch“ gibt. Zähle je Kunde die unterschiedlichen Produkte und gib nur Kunden mit mindestens zwei aus – zuerst die mit den meisten Produkten, bei Gleichstand nach Kundennummer.

## Prüfprotokoll

> Automatisch erzeugt am 2026-11-11 18:12 (Engine 0.1.0). Nicht von Hand ändern.

**✏️ In Arbeit – noch nicht freigabefähig**

- Grenzfälle: 6 von 6 bestanden
- Festigkeit: 20 von 22 Gegenproben erkannt (91 %)
- Siegel: noch nie freigegeben
- Nächster Schritt: 2 offene Frage(n): je Lücke den Owner fachlich fragen → neuer Grenzfall oder Eintrag unter „Bewusst offen“.

| Grenzfall | Erwartet | Ergebnis | |
|---|---|---|---|
| G1 | anzahl_produkte = 2 | anzahl_produkte = 2 | ✅ |
| G2 | nein | nein | ✅ |
| G3 | nein | nein | ✅ |
| G4 | nein | nein | ✅ |
| G5 | nein | nein | ✅ |
| G6 | ja | ja | ✅ |

**Lücken – das legt bisher kein Grenzfall fest**

| Lücke | Was offen ist | Stelle | Stand |
|---|---|---|---|
| L-17e128 | Kein Grenzfall prüft Mehrfachzählung (derselbe Wert kommt mehrfach vor). | `SELECT a.kunde_id, COUNT(DISTINCT a.produkt_id) AS anzahl_produkte` | ❓ offen |
| L-a5f8a1 | Kein Grenzfall hängt an dieser Bedingung: Ins Gegenteil verkehrt, fiele es keinem Beispiel auf. | `JOIN produkte p ON p.produkt_id = a.produkt_id` | ❓ offen |

## Änderungshistorie

| Version | Datum | Freigegeben von | Änderung | Siegel |
|---|---|---|---|---|
