---
regel_id: aktiver_kunde
owner: Christian Kainzmeier (UseCase Owner)
verbindung: abo_welt
schluessel: kunde_id
ausgabe: anzahl
max_zeilen: 50
status: certified
version: 1
siegel: "18cf817737770e02c09c2f18df4248ba7ed6a9326326f3b0c1ce12d2f4f0437a"
freigegeben_von: "Christian Kainzmeier (UseCase Owner)"
freigegeben_am: 2026-11-11
naechste_rezertifizierung: 2027-05-11
grenzfaelle_bestanden: "8/8"
festigkeit: 100
offene_fragen: 0
letzte_pruefung: 2026-11-11
letzter_lauf:
tags:
  - typ/freigabe
  - thema/determinismus
---
# Aktiver Kunde

## Frage

Welche Kunden gelten zum Stichtag als aktiv?

## Regel in Klartext

Ein Kunde ist **aktiv**, wenn er mindestens ein Abo hat, das

- den Status „aktiv“ hat, **oder**
- gekündigt ist, dessen Laufzeit am Stichtag aber noch nicht vorbei ist (Enddatum am oder nach dem Stichtag).

Pausierte und beendete Abos zählen nicht. Jeder Kunde zählt nur einmal, egal wie viele Abos er hat.

## Parameter

| Name | Typ | Standard | Im Test |
|---|---|---|---|
| stichtag | datum | heute | 2026-11-11 |

## Grenzfälle

> Jede Zeile ist eine fachliche Entscheidung. „Erwartet“ ändert nur der Owner.

| ID | Situation | Prüfobjekt | Erwartet | Entschieden von | Am |
|---|---|---|---|---|---|
| G1 | Kunde mit einem aktiven Abo | 1 | ja | Vorlage | 2026-11-11 |
| G2 | Abo gekündigt, Laufzeit endet erst in 30 Tagen | 2 | ja | Vorlage | 2026-11-11 |
| G3 | Abo pausiert | 3 | nein | Vorlage | 2026-11-11 |
| G4 | Abo gekündigt, Laufzeit endete gestern | 4 | nein | Vorlage | 2026-11-11 |
| G5 | Abo gekündigt, Laufzeit endet genau am Stichtag | 5 | ja | Vorlage | 2026-11-11 |
| G6 | Kunde ganz ohne Abo | 6 | nein | Vorlage | 2026-11-11 |
| G7 | Abo beendet | 7 | nein | Vorlage | 2026-11-11 |
| G8 | Kunde mit zwei aktiven Abos (zählt einmal) | 8 | ja | Vorlage | 2026-11-11 |

## Beispieldaten

> Je Grenzfall eine kleine eigene Welt. Die Spalte „fall“ ordnet die Zeile dem Grenzfall zu.

### kunden

| fall | kunde_id | name |
|---|---|---|
| G1 | 1 | Anna Aktiv |
| G2 | 2 | Gerd Gekündigt |
| G3 | 3 | Paula Pausiert |
| G4 | 4 | Vera Vorbei |
| G5 | 5 | Stefan Stichtag |
| G6 | 6 | Olaf Ohne |
| G7 | 7 | Bea Beendet |
| G8 | 8 | Doris Doppelt |

### abos

| fall | abo_id | kunde_id | produkt_id | status | enddatum |
|---|---|---|---|---|---|
| G1 | 11 | 1 | 2 | aktiv | |
| G2 | 21 | 2 | 2 | gekündigt | 2026-12-11 |
| G3 | 31 | 3 | 2 | pausiert | |
| G4 | 41 | 4 | 2 | gekündigt | 2026-11-10 |
| G5 | 51 | 5 | 2 | gekündigt | 2026-11-11 |
| G7 | 71 | 7 | 2 | beendet | 2026-10-01 |
| G8 | 81 | 8 | 2 | aktiv | |
| G8 | 82 | 8 | 3 | aktiv | |

## Bewusst offen

| Lücke | Begründung | Entschieden von |
|---|---|---|

## SQL

> [!abstract]- Kompilat – von Claude aus dem Klartext erzeugt. Bewiesen wird es durch die Grenzfälle, nicht durch Lesen.
> ```sql
> SELECT DISTINCT a.kunde_id
> FROM abos a
> WHERE a.status = 'aktiv'
>    OR (a.status = 'gekündigt' AND a.enddatum >= :stichtag)
> ORDER BY a.kunde_id
> ```

## Rückübersetzung

> So liest eine unabhängige Instanz das Kompilat – ohne den Klartext oben zu kennen.

Gib jede Kundennummer genau einmal aus, zu der es mindestens ein Abo gibt, das entweder den Status „aktiv“ hat oder den Status „gekündigt“ und ein Enddatum, das am Stichtag oder später liegt. Sortiert nach Kundennummer.

## Prüfprotokoll

> Automatisch erzeugt am 2026-11-11 18:34 (Engine 0.1.0). Nicht von Hand ändern.

**✅ Freigegeben und unverändert**

- Grenzfälle: 8 von 8 bestanden
- Festigkeit: 8 von 8 Gegenproben erkannt (100 %)
- Siegel: gültig (Version 1, Christian Kainzmeier (UseCase Owner), 2026-11-11)
- Nächster Schritt: Regel ist freigegeben und unverändert – sie darf ausgeführt werden.

| Grenzfall | Erwartet | Ergebnis | |
|---|---|---|---|
| G1 | ja | ja | ✅ |
| G2 | ja | ja | ✅ |
| G3 | nein | nein | ✅ |
| G4 | nein | nein | ✅ |
| G5 | ja | ja | ✅ |
| G6 | nein | nein | ✅ |
| G7 | nein | nein | ✅ |
| G8 | ja | ja | ✅ |

## Änderungshistorie

| Version | Datum | Freigegeben von | Änderung | Siegel |
|---|---|---|---|---|
| 1 | 2026-11-11 | Christian Kainzmeier (UseCase Owner) | Erstfreigabe | `18cf81773777` |
