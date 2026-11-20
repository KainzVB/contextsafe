---
regel_id:
owner:
verbindung: abo_welt
schluessel:
ausgabe: anzahl
max_zeilen: 50
nutzt:
status: draft
version: 0
siegel:
freigegeben_von:
freigegeben_am:
naechste_rezertifizierung:
grenzfaelle_bestanden:
festigkeit:
offene_fragen:
letzte_pruefung:
letzter_lauf:
tags:
  - typ/regel-vorlage
---
# Regel-Vorlage

> Kopieren nach `Regeln/<Titel>.md`, dann den Tag `typ/regel-vorlage` durch `typ/regel` ersetzen.
> `ausgabe`: `anzahl` gibt nur die Trefferzahl aus, `tabelle` die ersten `max_zeilen` Zeilen.

## Frage

Welche Frage beantwortet diese Regel?

## Regel in Klartext

Die Regel in den Worten des Fachbereichs.

## Parameter

| Name | Typ | Standard | Im Test |
|---|---|---|---|
| stichtag | datum | heute | 2026-11-11 |

## Grenzfälle

> Jede Zeile ist eine fachliche Entscheidung. „Erwartet“ ändert nur der Owner.

| ID | Situation | Prüfobjekt | Erwartet | Entschieden von | Am |
|---|---|---|---|---|---|

## Beispieldaten

> Je Grenzfall eine kleine eigene Welt. Die Spalte „fall“ ordnet die Zeile dem Grenzfall zu, „alle“ gilt für jeden.

### tabellenname

| fall | spalte |
|---|---|

## Bewusst offen

| Lücke | Begründung | Entschieden von |
|---|---|---|

## SQL

> [!abstract]- Kompilat – von Claude aus dem Klartext erzeugt. Bewiesen wird es durch die Grenzfälle, nicht durch Lesen.
> ```sql
> SELECT 1 AS schluessel
> ```

## Rückübersetzung

> So liest eine unabhängige Instanz das Kompilat – ohne den Klartext oben zu kennen.

## Prüfprotokoll

## Änderungshistorie

| Version | Datum | Freigegeben von | Änderung | Siegel |
|---|---|---|---|---|
