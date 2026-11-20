---
tags:
  - bereich/ai-governance
  - typ/glossar
  - thema/determinismus
---
# Glossar

> Welche Daten es gibt und was sie fachlich bedeuten. Einmalig von der Plattform-Rolle eingerichtet, danach die gemeinsame Sprache von Fachexperte und Claude. Regeln dürfen nur ansprechen, was hier steht.

## Verbindung `abo_welt`

- Demo-Datenbank eines Verlags mit Abonnements (SQLite, Datei `daten/abo_welt.sqlite`, nur lesend).
- Datumswerte stehen als Text im Format `JJJJ-MM-TT` und lassen sich direkt vergleichen.

### kunden

| Spalte | Bedeutung | Werte |
|---|---|---|
| kunde_id | Kundennummer (Schlüssel) | Ganzzahl |
| name | Name des Kunden | Text |
| segment | Kundensegment | `Privat`, `Geschäft` |
| region | Vertriebsregion | `Nord`, `Süd`, `Ost`, `West` |

### produkte

| Spalte | Bedeutung | Werte |
|---|---|---|
| produkt_id | Produktnummer (Schlüssel) | Ganzzahl |
| name | Produktname | Text |
| kategorie | Produktart | `digital`, `print` |

### abos

| Spalte | Bedeutung | Werte |
|---|---|---|
| abo_id | Abonummer (Schlüssel) | Ganzzahl |
| kunde_id | Kunde, dem das Abo gehört | verweist auf `kunden` |
| produkt_id | Abonniertes Produkt | verweist auf `produkte` |
| status | Stand des Abos | `aktiv`, `gekündigt`, `pausiert`, `beendet` |
| startdatum | Beginn der Laufzeit | Datum |
| enddatum | Ende der Laufzeit, nur bei `gekündigt` und `beendet` gefüllt | Datum oder leer |

### tickets

| Spalte | Bedeutung | Werte |
|---|---|---|
| ticket_id | Ticketnummer (Schlüssel) | Ganzzahl |
| kunde_id | Kunde, der das Ticket gemeldet hat | verweist auf `kunden` |
| prioritaet | Dringlichkeit | `niedrig`, `mittel`, `hoch` |
| offen | Ticket noch offen | `1` ja, `0` nein |

## Verbindung `tpch`

- Datenbank des ursprünglichen ContextSafe-PoC (Postgres im Docker-Container, nur lesender Benutzer, 750.000 Kunden).
- Dialekt Postgres. **Datumsspalten sind Text**: vor Vergleichen `CAST(spalte AS DATE)`.
- Auf einem Rechner ohne diesen Container ist die Verbindung nicht erreichbar.

### tpch_customer

| Spalte | Bedeutung | Werte |
|---|---|---|
| c_custkey | Kundennummer (Schlüssel) | Ganzzahl |
| c_mktsegment | Marktsegment | z. B. `BUILDING`, `AUTOMOBILE`, `MACHINERY`, `HOUSEHOLD`, `FURNITURE` |

### tpch_orders

| Spalte | Bedeutung | Werte |
|---|---|---|
| o_orderkey | Bestellnummer (Schlüssel) | Ganzzahl |
| o_custkey | Bestellender Kunde | verweist auf `tpch_customer` |
| o_orderdate | Bestelldatum | Datum als Text |
| o_shippriority | Versandpriorität | Ganzzahl |

### tpch_lineitems

| Spalte | Bedeutung | Werte |
|---|---|---|
| l_orderkey | Bestellung, zu der die Position gehört | verweist auf `tpch_orders` |
| l_linenumber | Positionsnummer | Ganzzahl |
| l_extendedprice | Preis der Position vor Rabatt | Betrag |
| l_discount | Rabatt als Anteil | `0.07` bedeutet 7 % |
| l_shipdate | Versanddatum der Position | Datum als Text |
