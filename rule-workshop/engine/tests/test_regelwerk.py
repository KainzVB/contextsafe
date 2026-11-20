#!/usr/bin/env python3
"""Tests der Regelwerkstatt-Engine. Aufruf:  python3 engine/tests/test_regelwerk.py

Jeder Test arbeitet auf einer Wegwerf-Kopie des Projekts. Die menschliche Bestätigung der
Freigabe wird hier durch eine Attrappe ersetzt – nur so lässt sich die Freigabe automatisch testen.
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

PROJEKT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJEKT / "engine"))
import regelwerk as rw  # noqa: E402

JA = lambda text: True
NEIN = lambda text: False
LEER_OFFEN = "| Lücke | Begründung | Entschieden von |\n|---|---|---|\n"


class RegelwerkTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="regel werk "))
        for teil in ("engine/regelwerk.config.json", "daten/abo_welt.sqlite", "Regeln/Aktiver Kunde.md", "Regeln/Upselling-Kandidat.md"):
            (self.tmp / teil).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(PROJEKT / teil, self.tmp / teil)
        rw.ROOT = self.tmp
        for name in ("Aktiver Kunde", "Upselling-Kandidat"):  # Ausgangszustand: unversiegelt, Owner gesetzt
            self.aendere(name, lambda t: rw.setze_frontmatter(t, {"owner": "Erika Muster", "siegel": "", "version": 0, "status": "draft"}))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def aendere(self, name, fn):
        p = self.tmp / "Regeln" / f"{name}.md"
        neu = fn(p.read_text(encoding="utf-8"))
        p.write_text(neu, encoding="utf-8")

    def ersetze(self, name, alt, neu):
        def fn(t):
            self.assertIn(alt, t)
            return t.replace(alt, neu)
        self.aendere(name, fn)

    def siegle(self, name):
        return rw.freigeben(name, "Erika Muster", "Testfreigabe", bestaetiger=JA)

    # ── Beweis gegen Grenzfälle ──
    def test_gruene_regel_ist_freigabefaehig(self):
        b = rw.pruefen("Aktiver Kunde")
        self.assertEqual([], b["fehler"])
        self.assertTrue(all(g["bestanden"] for g in b["grenzfaelle"]))
        self.assertEqual((8, 8, 100, "review"), (b["gegenproben"], b["erkannt"], b["festigkeit"], b["status"]))

    def test_grenzfaelle_laufen_abgeschottet_von_echten_daten(self):
        r = rw.lade_regel(rw.finde_regel("Aktiver Kunde"))
        verb = rw.verbindung("abo_welt")
        schatten = rw._schatten_fuer(r, [], verb.katalog(), verb, "G1")
        sql = rw.zusammensetzen(r["sql"], [], schatten, {"stichtag": "'2026-11-11'"})
        self.assertEqual([[1]], verb.ausfuehren([sql], 10)[0]["zeilen"])  # echte DB hätte Hunderte Treffer

    def test_falsche_entscheidung_faellt_auf(self):
        self.ersetze("Aktiver Kunde", "| Abo pausiert | 3 | nein |", "| Abo pausiert | 3 | ja |")
        b = rw.pruefen("Aktiver Kunde")
        self.assertEqual(["G3"], [g["id"] for g in b["grenzfaelle"] if not g["bestanden"]])
        self.assertEqual("draft", b["status"])

    def test_luecken_werden_gefunden_und_blockieren(self):
        b = rw.pruefen("Upselling-Kandidat")
        self.assertEqual(2, len(b["luecken"]))
        self.assertFalse(b["freigabefaehig"])
        with self.assertRaises(rw.RegelFehler):
            self.siegle("Upselling-Kandidat")

    def test_neuer_grenzfall_schliesst_luecke(self):
        self.ersetze("Upselling-Kandidat", "| G6 | Wie G1, aber ein offenes Ticket mit Priorität niedrig | 6 | ja | Vorlage | 2026-11-11 |",
                     "| G6 | Wie G1, aber ein offenes Ticket mit Priorität niedrig | 6 | ja | Vorlage | 2026-11-11 |\n"
                     "| G7 | Ein digitales und ein Print-Produkt | 7 | nein | Erika Muster | 2026-11-11 |")
        self.ersetze("Upselling-Kandidat", "| G6 | 62 | 6 | 3 | aktiv | |", "| G6 | 62 | 6 | 3 | aktiv | |\n| G7 | 71 | 7 | 2 | aktiv | |\n| G7 | 72 | 7 | 1 | aktiv | |")
        self.assertEqual(1, len(rw.pruefen("Upselling-Kandidat")["luecken"]))

    def test_erfundene_spalte_wird_abgefangen(self):
        self.ersetze("Aktiver Kunde", "a.enddatum >= :stichtag", "a.laufzeit_ende >= :stichtag")
        b = rw.pruefen("Aktiver Kunde")
        self.assertTrue(any("laufzeit_ende" in f for f in b["fehler"]))

    def test_bauregeln(self):
        def v(sql):
            return " ".join(rw.sql_regeln(sql, {"stichtag"}))
        self.assertIn("DELETE", v("DELETE FROM abos"))
        self.assertIn("eine einzige Anweisung", v("SELECT kunde_id FROM abos; SELECT 1"))
        self.assertIn("NOW", v("SELECT kunde_id FROM abos WHERE enddatum > NOW()"))
        self.assertIn("SELECT *", v("SELECT * FROM abos"))
        self.assertIn("LIMIT ohne ORDER BY", v("SELECT kunde_id FROM abos LIMIT 5"))
        self.assertIn("Systembereich", v("SELECT name FROM sqlite_master"))
        self.assertIn("Systembereich", v("SELECT kunde_id FROM main.abos"))
        self.assertIn(":heute", v("SELECT kunde_id FROM abos WHERE enddatum > :heute"))
        self.assertEqual("", v("SELECT COUNT(*) AS n FROM abos WHERE enddatum >= :stichtag"))

    # ── Siegel, Freigabe, Lauf ──
    def test_ohne_siegel_kein_lauf(self):
        with self.assertRaises(rw.RegelFehler) as e:
            rw.ausfuehren("Aktiver Kunde")
        self.assertIn("noch nie freigegeben", str(e.exception))
        self.assertEqual(1, len(list((self.tmp / "Protokoll" / "Läufe").glob("*.md"))))  # auch die Verweigerung ist protokolliert

    def test_freigabe_nur_durch_owner_und_nur_mit_mensch(self):
        with self.assertRaises(rw.RegelFehler):
            rw.freigeben("Aktiver Kunde", "Claude", "x", bestaetiger=JA)
        with self.assertRaises(rw.RegelFehler):
            rw.freigeben("Aktiver Kunde", "Erika Muster", "x", bestaetiger=NEIN)
        self.assertEqual("", rw.lade_regel(rw.finde_regel("Aktiver Kunde"))["fm"]["siegel"])

    def test_freigabe_dann_lauf(self):
        f = self.siegle("Aktiver Kunde")
        self.assertEqual(1, f["version"])
        self.assertTrue((self.tmp / f["festgehalten_in"]).is_file())
        self.assertEqual("certified", rw.pruefen("Aktiver Kunde")["status"])
        erg = rw.ausfuehren("Aktiver Kunde", {"stichtag": "2026-11-11"})
        self.assertGreater(erg["anzahl"], 100)
        self.assertNotIn("zeilen", erg)  # ausgabe: anzahl → keine Einzelzeilen in den Kontext
        with self.assertRaises(rw.RegelFehler):
            rw.ausfuehren("Aktiver Kunde", {"stichtag": "2026-11-11'; DROP TABLE abos; --"})
        with self.assertRaises(rw.RegelFehler):
            self.siegle("Aktiver Kunde")  # unverändert → keine zweite Freigabe

    def test_formatierung_bricht_das_siegel_nicht(self):
        self.siegle("Aktiver Kunde")
        self.aendere("Aktiver Kunde", lambda t: t.replace("| G1 | Kunde mit einem aktiven Abo | 1 | ja |",
                                                         "|  G1  |   Kunde mit einem aktiven Abo   |  1  |  **ja**  |").replace("## Grenzfälle", "## GRENZFÄLLE"))
        self.assertTrue(rw.ausfuehren("Aktiver Kunde")["anzahl"] > 0)

    def test_fachliche_aenderung_bricht_das_siegel(self):
        self.siegle("Aktiver Kunde")
        self.ersetze("Aktiver Kunde", "| Abo pausiert | 3 | nein |", "| Abo pausiert | 3 | ja |")
        with self.assertRaises(rw.RegelFehler) as e:
            rw.ausfuehren("Aktiver Kunde")
        self.assertIn("Grenzfälle", str(e.exception))
        self.assertEqual("draft", [x for x in rw.liste() if x["regel"] == "Aktiver Kunde"][0]["status"])

    def test_status_von_hand_auf_certified_nuetzt_nichts(self):
        self.aendere("Aktiver Kunde", lambda t: rw.setze_frontmatter(t, {"status": "certified", "siegel": "0" * 64, "version": 1}))
        with self.assertRaises(rw.RegelFehler):
            rw.ausfuehren("Aktiver Kunde")

    def test_wirkung_zeigt_nur_summen_und_den_unterschied(self):
        self.siegle("Aktiver Kunde")
        self.ersetze("Aktiver Kunde", "WHERE a.status = 'aktiv'", "WHERE a.status IN ('aktiv', 'pausiert')")
        w = rw.wirkung("Aktiver Kunde", {"stichtag": "2026-11-11"})
        self.assertGreater(w["unterschied"]["kommen_dazu"], 0)
        self.assertEqual(0, w["unterschied"]["fallen_weg"])
        self.assertNotIn("zeilen", {k for k in w if k != "neu"} | set(w["neu"]) - {"zeilen"})
        self.assertIsInstance(w["neu"]["zeilen"], int)

    def test_aenderung_der_genutzten_regel_bricht_die_abhaengige(self):
        self.siegle("Aktiver Kunde")
        offen = "".join(f"| {l['id']} | im Test akzeptiert | Erika Muster |\n" for l in rw.pruefen("Upselling-Kandidat")["luecken"])
        self.ersetze("Upselling-Kandidat", LEER_OFFEN, LEER_OFFEN + offen)
        self.siegle("Upselling-Kandidat")
        erg = rw.ausfuehren("Upselling-Kandidat", {"stichtag": "2026-11-11"})
        self.assertEqual(["kunde_id", "anzahl_produkte"], erg["spalten"])
        self.assertLessEqual(len(erg["zeilen"]), 20)
        self.ersetze("Aktiver Kunde", "WHERE a.status = 'aktiv'", "WHERE a.status IN ('aktiv', 'pausiert')")
        with self.assertRaises(rw.RegelFehler) as e:
            rw.ausfuehren("Upselling-Kandidat")
        self.assertIn("eine genutzte Regel", str(e.exception))


if __name__ == "__main__":
    unittest.main(verbosity=1)
