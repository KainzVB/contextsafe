#!/usr/bin/env python3
"""Erzeugt die Demo-Datenbank „Abo-Welt“ (SQLite). Fester Zufalls-Seed: jeder Lauf ergibt dieselben Daten."""
import datetime as dt
import random
import sqlite3
from pathlib import Path

ZIEL = Path(__file__).resolve().parent / "abo_welt.sqlite"
STICHTAG = dt.date(2026, 11, 11)
rnd = random.Random(42)

ZIEL.unlink(missing_ok=True)
con = sqlite3.connect(ZIEL)
con.executescript("""
CREATE TABLE kunden   (kunde_id INTEGER PRIMARY KEY, name TEXT, segment TEXT, region TEXT);
CREATE TABLE produkte (produkt_id INTEGER PRIMARY KEY, name TEXT, kategorie TEXT);
CREATE TABLE abos     (abo_id INTEGER PRIMARY KEY, kunde_id INTEGER, produkt_id INTEGER, status TEXT, startdatum TEXT, enddatum TEXT);
CREATE TABLE tickets  (ticket_id INTEGER PRIMARY KEY, kunde_id INTEGER, prioritaet TEXT, offen INTEGER);
""")
produkte = [(1, "Tageszeitung Print", "print"), (2, "E-Paper", "digital"), (3, "News-App Plus", "digital"),
            (4, "Podcast Premium", "digital"), (5, "Wochenmagazin Print", "print"), (6, "Archiv-Zugang", "digital")]
con.executemany("INSERT INTO produkte VALUES (?,?,?)", produkte)
abo_id = ticket_id = 0
for k in range(1, 1201):
    con.execute("INSERT INTO kunden VALUES (?,?,?,?)",
                (k, f"Kunde {k:04d}", rnd.choice(["Privat", "Privat", "Privat", "Geschäft"]), rnd.choice(["Nord", "Süd", "Ost", "West"])))
    for _ in range(rnd.choices([0, 1, 2, 3, 4], [5, 40, 30, 18, 7])[0]):
        abo_id += 1
        status = rnd.choices(["aktiv", "gekündigt", "pausiert", "beendet"], [62, 12, 8, 18])[0]
        start = STICHTAG - dt.timedelta(days=rnd.randint(30, 1500))
        ende = None
        if status == "gekündigt":
            ende = STICHTAG + dt.timedelta(days=rnd.randint(-45, 90))
        elif status == "beendet":
            ende = STICHTAG - dt.timedelta(days=rnd.randint(1, 400))
        con.execute("INSERT INTO abos VALUES (?,?,?,?,?,?)",
                    (abo_id, k, rnd.choice(produkte)[0], status, start.isoformat(), ende.isoformat() if ende else None))
    for _ in range(rnd.choices([0, 1, 2], [70, 24, 6])[0]):
        ticket_id += 1
        con.execute("INSERT INTO tickets VALUES (?,?,?,?)",
                    (ticket_id, k, rnd.choices(["niedrig", "mittel", "hoch"], [50, 35, 15])[0], rnd.choices([1, 0], [35, 65])[0]))
con.commit()
print(f"{ZIEL.name}: 1200 Kunden, {len(produkte)} Produkte, {abo_id} Abos, {ticket_id} Tickets")
con.close()
