---
regel_id: top_10_shipping_priorities
owner:
verbindung: tpch
schluessel: o_orderkey
ausgabe: tabelle
max_zeilen: 10
status: review
version: 0
siegel:
freigegeben_von:
freigegeben_am:
naechste_rezertifizierung:
grenzfaelle_bestanden: "6/6"
festigkeit: 100
offene_fragen: 0
letzte_pruefung: 2026-11-11
letzter_lauf:
tags:
  - typ/regel
  - thema/determinismus
  - thema/tpch
---
# Top 10 Shipping Priorities

> Der Use Case des ursprünglichen ContextSafe-PoC (`TPCH-Q3-001`, siehe [Process Contract](../../process/tpch_q3.process.md)) – hier als Regel, die ein Fachexperte selbst verantwortet.

## Frage

Welche zehn noch nicht ausgelieferten Bestellungen eines Marktsegments bringen den höchsten Umsatz, wenn sie zuerst versendet werden?

## Regel in Klartext

Betrachtet werden Bestellungen von Kunden des gewählten **Marktsegments**, die **vor dem Stichtag** bestellt wurden.

Zum **Umsatz** einer Bestellung zählen nur ihre Positionen, die **nach dem Stichtag** versendet werden. Je Position gilt: Preis × (1 − Rabatt). Die Summe wird auf zwei Nachkommastellen gerundet.

Ausgegeben werden die **zehn Bestellungen mit dem höchsten Umsatz** – bei gleichem Umsatz die ältere Bestellung zuerst.

## Parameter

| Name | Typ | Standard | Im Test |
|---|---|---|---|
| stichtag | datum | 1995-03-15 | 1995-03-15 |
| segment | text | BUILDING | BUILDING |

## Grenzfälle

> Jede Zeile ist eine fachliche Entscheidung. „Erwartet“ ändert nur der Owner.

| ID | Situation | Prüfobjekt | Erwartet | Entschieden von | Am |
|---|---|---|---|---|---|
| G1 | Zwei offene Positionen: 100,00 mit 10 % Rabatt und 200,55 ohne Rabatt | 100 | revenue = 290.55 | Vorlage | 2026-11-11 |
| G2 | Kunde gehört zu einem anderen Marktsegment | 200 | nein | Vorlage | 2026-11-11 |
| G3 | Bestellung genau am Stichtag aufgegeben | 300 | nein | Vorlage | 2026-11-11 |
| G4 | Eine Position genau am Stichtag versendet (zählt nicht), eine danach (50,00) | 400 | revenue = 50.00 | Vorlage | 2026-11-11 |
| G5 | Alle Positionen bereits vor dem Stichtag versendet | 500 | nein | Vorlage | 2026-11-11 |
| G6 | Rundung: 33,33 mit 7 % Rabatt ergibt 30,9969 | 600 | revenue = 31.00 | Vorlage | 2026-11-11 |

## Beispieldaten

> Je Grenzfall eine kleine eigene Welt. Die Spalte „fall“ ordnet die Zeile dem Grenzfall zu.

### tpch_customer

| fall | c_custkey | c_mktsegment |
|---|---|---|
| G1 | 1 | BUILDING |
| G2 | 2 | AUTOMOBILE |
| G3 | 3 | BUILDING |
| G4 | 4 | BUILDING |
| G5 | 5 | BUILDING |
| G6 | 6 | BUILDING |

### tpch_orders

| fall | o_orderkey | o_custkey | o_orderdate | o_shippriority |
|---|---|---|---|---|
| G1 | 100 | 1 | 1995-03-01 | 0 |
| G2 | 200 | 2 | 1995-03-01 | 0 |
| G3 | 300 | 3 | 1995-03-15 | 0 |
| G4 | 400 | 4 | 1995-03-01 | 0 |
| G5 | 500 | 5 | 1995-03-01 | 0 |
| G6 | 600 | 6 | 1995-03-01 | 0 |

### tpch_lineitems

| fall | l_orderkey | l_linenumber | l_extendedprice | l_discount | l_shipdate |
|---|---|---|---|---|---|
| G1 | 100 | 1 | 100.00 | 0.10 | 1995-03-20 |
| G1 | 100 | 2 | 200.55 | 0 | 1995-03-25 |
| G2 | 200 | 1 | 100.00 | 0 | 1995-03-20 |
| G3 | 300 | 1 | 100.00 | 0 | 1995-03-20 |
| G4 | 400 | 1 | 100.00 | 0 | 1995-03-15 |
| G4 | 400 | 2 | 50.00 | 0 | 1995-03-20 |
| G5 | 500 | 1 | 100.00 | 0 | 1995-03-10 |
| G6 | 600 | 1 | 33.33 | 0.07 | 1995-03-20 |

## Bewusst offen

| Lücke | Begründung | Entschieden von |
|---|---|---|

## SQL

> [!abstract]- Kompilat – von Claude aus dem Klartext erzeugt. Bewiesen wird es durch die Grenzfälle, nicht durch Lesen.
> ```sql
> SELECT o.o_orderkey,
>        ROUND(CAST(SUM(l.l_extendedprice * (1 - l.l_discount)) AS numeric), 2) AS revenue,
>        o.o_orderdate,
>        o.o_shippriority
> FROM tpch_customer c
> JOIN tpch_orders o ON c.c_custkey = o.o_custkey
> JOIN tpch_lineitems l ON o.o_orderkey = l.l_orderkey
> WHERE c.c_mktsegment = :segment
>   AND CAST(o.o_orderdate AS DATE) < CAST(:stichtag AS DATE)
>   AND CAST(l.l_shipdate AS DATE) > CAST(:stichtag AS DATE)
> GROUP BY o.o_orderkey, o.o_orderdate, o.o_shippriority
> ORDER BY revenue DESC, o.o_orderdate ASC, o.o_orderkey ASC
> LIMIT 10
> ```

## Rückübersetzung

> So liest eine unabhängige Instanz das Kompilat – ohne den Klartext oben zu kennen.

Verbinde Kunden mit ihren Bestellungen und deren Positionen. Behalte nur Kunden des angegebenen Marktsegments, Bestellungen mit Bestelldatum vor dem Stichtag und Positionen mit Versanddatum nach dem Stichtag. Summiere je Bestellung Preis × (1 − Rabatt) über die verbliebenen Positionen und runde auf zwei Nachkommastellen. Gib die zehn Bestellungen mit der höchsten Summe aus; bei Gleichstand zuerst das frühere Bestelldatum, dann die kleinere Bestellnummer.

## Prüfprotokoll

> Automatisch erzeugt am 2026-11-11 18:12 (Engine 0.1.0). Nicht von Hand ändern.

**🟡 Freigabefähig – wartet auf die Freigabe durch den Owner**

- Grenzfälle: 6 von 6 bestanden
- Festigkeit: 11 von 11 Gegenproben erkannt (100 %)
- Siegel: noch nie freigegeben
- Nächster Schritt: Freigabefähig: Rückübersetzung und Wirkung zeigen, dann bittet der Owner um Freigabe.

| Grenzfall | Erwartet | Ergebnis | |
|---|---|---|---|
| G1 | revenue = 290.55 | revenue = 290.55 | ✅ |
| G2 | nein | nein | ✅ |
| G3 | nein | nein | ✅ |
| G4 | revenue = 50.00 | revenue = 50.00 | ✅ |
| G5 | nein | nein | ✅ |
| G6 | revenue = 31.00 | revenue = 31.00 | ✅ |

## Änderungshistorie

| Version | Datum | Freigegeben von | Änderung | Siegel |
|---|---|---|---|---|
