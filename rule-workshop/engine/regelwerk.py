#!/usr/bin/env python3
"""ContextSafe Regelwerkstatt — deterministischer Kern.

Kein LLM, keine Fremdbibliotheken (nur Python-Standardbibliothek, ab 3.9).

Die Engine liest Regel-Notizen (Markdown), beweist das SQL-Kompilat gegen die
vom Fachexperten entschiedenen Grenzfälle, sucht Lücken (Gegenproben),
versiegelt nach menschlicher Freigabe und führt nur versiegelte Regeln aus.

Aufruf:  python3 engine/regelwerk.py {liste|pruefen|wirkung|freigeben|ausfuehren} ...
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import quote

VERSION = "0.1.0"
ROOT = Path(os.environ.get("REGELWERK_ROOT") or Path(__file__).resolve().parent.parent)


class RegelFehler(Exception):
    """Fehler in fachlich lesbarer Sprache (wird dem Menschen gezeigt)."""


def konfig() -> dict:
    return json.loads((ROOT / "engine" / "regelwerk.config.json").read_text(encoding="utf-8"))


def heute() -> str:
    return dt.date.today().isoformat()


# ───────────────────────── Notiz lesen ─────────────────────────

FM_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.S)


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s)


def norm(s: str) -> str:
    """Vergleichsform: Groß/Klein, Leerraum und Unicode-Form egal."""
    return re.sub(r"\s+", " ", nfc(str(s))).strip().lower()


def _wert(v: str) -> str:
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        v = v[1:-1]
    return v


def lies_frontmatter(text: str) -> dict:
    """Flaches YAML (Skalare und einfache Listen) — das, was Obsidian-Properties können."""
    m = FM_RE.match(text)
    fm: dict = {}
    key = None
    for line in (m.group(1).splitlines() if m else []):
        k = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if k:
            key = k.group(1)
            fm[key] = _wert(k.group(2))
        elif key and re.match(r"^\s*-\s+", line):
            if not isinstance(fm[key], list):
                fm[key] = []
            fm[key].append(_wert(re.sub(r"^\s*-\s+", "", line)))
    return fm


def _entzitiere(line: str) -> str:
    return re.sub(r"^\s*>\s?", "", line)


def abschnitte(body: str) -> dict:
    """H2-Abschnitte als {titel: text}. Überschriften in Codeblöcken zählen nicht."""
    out: dict = {}
    cur, buf, fence = None, [], False
    for line in body.splitlines():
        if _entzitiere(line).lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{1,2})\s+(.*?)\s*$", line)
        if m:
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = (norm(m.group(2)) if len(m.group(1)) == 2 else None), []
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def _rein(v: str) -> str:
    return re.sub(r"^(\*\*|`)(.+)\1$", r"\2", v.strip())


def tabellen(text: str) -> list:
    """Alle Markdown-Tabellen eines Textes; jede als Liste von Zeilen-Dicts."""
    result, kopf, rows = [], None, []
    for line in text.splitlines() + [""]:
        s = line.strip()
        if s.startswith("|"):
            s = s[1:-1] if s.endswith("|") and len(s) > 1 else s[1:]
            zellen = [_rein(c.replace("\\|", "|")) for c in re.split(r"(?<!\\)\|", s)]
            if kopf is None:
                kopf = [norm(c) for c in zellen]
            elif not all(re.fullmatch(r":?-+:?", c) for c in zellen):
                rows.append({k: (zellen[i] if i < len(zellen) else "") for i, k in enumerate(kopf)})
        elif kopf is not None:
            result.append(rows)
            kopf, rows = None, []
    return result


def _beispieldaten(text: str) -> dict:
    out, name, buf = {}, None, []

    def flush():
        if name:
            t = tabellen("\n".join(buf))
            out[name] = t[0] if t else []

    for line in text.splitlines():
        m = re.match(r"^###\s+(.*?)\s*$", line)
        if m:
            flush()
            name, buf = norm(m.group(1).strip("`")), []
        else:
            buf.append(line)
    flush()
    return out


def _fliesstext(text: str) -> str:
    zeilen = [l.rstrip() for l in text.strip().splitlines()]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(zeilen))


def lade_regel(pfad) -> dict:
    pfad = Path(pfad)
    text = nfc(pfad.read_text(encoding="utf-8"))
    fm = lies_frontmatter(text)
    m = FM_RE.match(text)
    ab = abschnitte(text[m.end():] if m else text)

    def tab(name):
        t = tabellen(ab.get(name, ""))
        return t[0] if t else []

    sql_text = "\n".join(_entzitiere(l) for l in ab.get("sql", "").splitlines())
    sql_m = re.search(r"```sql[^\n]*\n(.*?)```", sql_text, re.S | re.I)
    try:
        max_zeilen = int(fm.get("max_zeilen") or 50)
    except ValueError:
        max_zeilen = 50
    return {
        "pfad": pfad, "titel": pfad.stem, "text": text, "fm": fm,
        "regel_id": fm.get("regel_id", ""), "verbindung": fm.get("verbindung", ""),
        "schluessel": norm(fm.get("schluessel", "")), "ausgabe": norm(fm.get("ausgabe") or "anzahl"),
        "max_zeilen": max_zeilen,
        "nutzt": re.findall(r"\[\[([^\]|#]+)", json.dumps(fm.get("nutzt", ""), ensure_ascii=False)),
        "frage": _fliesstext(ab.get("frage", "")),
        "klartext": _fliesstext(ab.get("regel in klartext", "")),
        "parameter": tab("parameter"), "grenzfaelle": tab("grenzfälle"),
        "beispieldaten": _beispieldaten(ab.get("beispieldaten", "")),
        "bewusst_offen": tab("bewusst offen"),
        "sql": (sql_m.group(1) if sql_m else "").strip(),
    }


def regel_ordner() -> Path:
    return ROOT / konfig()["ordner"]["regeln"]


def finde_regel(name) -> Path:
    p = Path(str(name))
    for kandidat in (p, ROOT / p):
        if kandidat.suffix == ".md" and kandidat.is_file():
            return kandidat
    ziel = norm(p.stem if p.suffix == ".md" else str(name))
    for f in sorted(regel_ordner().glob("*.md")):
        if norm(f.stem) == ziel or norm(lies_frontmatter(nfc(f.read_text(encoding="utf-8"))).get("regel_id", "")) == ziel:
            return f
    raise RegelFehler(f"Regel „{name}“ nicht gefunden (gesucht in {regel_ordner().name}/).")


def abhaengigkeiten(r: dict, _kette=()) -> list:
    """Alle direkt und indirekt genutzten Regeln, in Ausführungsreihenfolge."""
    out: list = []
    for name in r["nutzt"]:
        d = lade_regel(finde_regel(name))
        if d["regel_id"] == r["regel_id"] or d["regel_id"] in _kette:
            raise RegelFehler(f"Regeln nutzen sich im Kreis: {r['titel']} ↔ {d['titel']}.")
        for x in abhaengigkeiten(d, _kette + (r["regel_id"],)) + [d]:
            if x["regel_id"] not in [o["regel_id"] for o in out]:
                out.append(x)
    return out


# ───────────────────────── Notiz schreiben ─────────────────────────

def _yaml(v) -> str:
    if isinstance(v, (int, float)):
        return str(v)
    v = str(v)
    if v == "" or re.fullmatch(r"\d{4}-\d{2}-\d{2}|[A-Za-zäöüÄÖÜß_][\w.+\-/äöüÄÖÜß]*", v):
        return v
    return json.dumps(v, ensure_ascii=False)


def setze_frontmatter(text: str, werte: dict) -> str:
    m = FM_RE.match(text)
    zeilen = m.group(1).splitlines() if m else []
    for k, v in werte.items():
        neu = f"{k}: {_yaml(v)}".rstrip()
        idx = next((i for i, l in enumerate(zeilen) if re.match(rf"^{re.escape(k)}:", l)), None)
        if idx is None:
            zeilen.append(neu)
        else:
            zeilen[idx] = neu
    return "---\n" + "\n".join(zeilen) + "\n---\n" + (text[m.end():] if m else text)


def setze_abschnitt(text: str, titel: str, inhalt: str) -> str:
    """Ersetzt den Inhalt eines H2-Abschnitts (legt ihn am Ende an, falls er fehlt)."""
    zeilen = text.split("\n")
    start = ende = None
    fence = False
    for i, line in enumerate(zeilen):
        if _entzitiere(line).lstrip().startswith("```"):
            fence = not fence
        m = None if fence else re.match(r"^(#{1,2})\s+(.*?)\s*$", line)
        if m and start is None and len(m.group(1)) == 2 and norm(m.group(2)) == norm(titel):
            start = i
        elif m and start is not None:
            ende = i
            break
    block = [f"## {titel}", "", inhalt.strip(), ""]
    if start is None:
        return text.rstrip("\n") + "\n\n" + "\n".join(block)
    return "\n".join(zeilen[:start] + block + (zeilen[ende:] if ende is not None else []))


# ───────────────────────── SQL: Zerlegen, Regeln, Gegenproben ─────────────────────────

TOKEN = re.compile(r"""
   (?P<kommentar>--[^\n]*|/\*.*?\*/)
 | (?P<text>'(?:[^']|'')*')
 | (?P<name>"(?:[^"]|"")*")
 | (?P<param>(?<!:):[A-Za-z_][A-Za-z0-9_]*)
 | (?P<zahl>\b\d+(?:\.\d+)?\b)
 | (?P<wort>[A-Za-z_][A-Za-z0-9_$]*)
 | (?P<op><>|!=|>=|<=|::|=|<|>)
 | (?P<leer>\s+)
 | (?P<sonst>.)
""", re.S | re.X)

VERBOTEN = {"INSERT", "UPDATE", "DELETE", "MERGE", "DROP", "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE",
            "ATTACH", "DETACH", "PRAGMA", "VACUUM", "COPY", "CALL", "DO", "EXECUTE", "SET", "RESET", "LOCK",
            "REINDEX", "ANALYZE", "COMMENT", "LISTEN", "NOTIFY", "INTO", "RECURSIVE"}
UHR = {"NOW", "CURRENT_DATE", "CURRENT_TIME", "CURRENT_TIMESTAMP", "LOCALTIME", "LOCALTIMESTAMP", "RANDOM",
       "CLOCK_TIMESTAMP", "STATEMENT_TIMESTAMP", "TRANSACTION_TIMESTAMP", "TIMEOFDAY", "GETDATE", "SYSDATE",
       "GEN_RANDOM_UUID", "JULIANDAY", "UNIXEPOCH"}
SYSTEM = {"PUBLIC", "MAIN", "TEMP", "INFORMATION_SCHEMA", "PG_CATALOG"}


def tokens(sql: str) -> list:
    return [(m.lastgroup, m.group()) for m in TOKEN.finditer(sql)]


def _bedeutsam(toks: list) -> list:
    return [(a, t) for a, t in toks if a not in ("leer", "kommentar")]


def ohne_semikolon(sql: str) -> str:
    return re.sub(r";\s*\Z", "", sql.strip())


def einzeilig(sql: str) -> str:
    return "".join(" " if a in ("leer", "kommentar") else t for a, t in tokens(sql)).strip()


def sql_regeln(sql: str, erlaubte_parameter: set) -> list:
    """Feste Bauregeln für jedes Kompilat. Rückgabe: Liste von Verstößen."""
    t = _bedeutsam(tokens(ohne_semikolon(sql)))
    if not t:
        return ["Der Abschnitt „SQL“ ist leer."]
    v = []
    woerter = [x.upper() for a, x in t if a == "wort"]
    if t[0][1].upper() not in ("SELECT", "WITH"):
        v.append("Das Kompilat muss eine reine Abfrage sein (beginnt mit SELECT oder WITH).")
    if any(x == ";" for _, x in t):
        v.append("Nur eine einzige Anweisung ist erlaubt (kein „;“ im Kompilat).")
    for w in sorted(set(woerter) & VERBOTEN):
        v.append(f"„{w}“ ist nicht erlaubt (nur lesende Abfragen).")
    for w in sorted(set(woerter) & UHR):
        v.append(f"„{w}“ macht das Ergebnis vom Ausführungszeitpunkt abhängig. Nimm stattdessen einen Parameter wie :stichtag.")
    if any(a == "text" and x.strip("'").lower() in ("now", "today", "localtime") for a, x in t):
        v.append("'now'/'today' macht das Ergebnis zeitabhängig. Nimm stattdessen einen Parameter wie :stichtag.")
    for i, (a, x) in enumerate(t):
        vor = t[i - 1][1].upper() if i else ""
        nach = t[i + 1][1] if i + 1 < len(t) else ""
        if x == "*" and vor in ("SELECT", "DISTINCT", "ALL", ",", "."):
            v.append("„SELECT *“ ist nicht erlaubt: Spalten ausdrücklich benennen.")
        if a == "wort" and (x.upper() in SYSTEM and nach == "." or re.match(r"(?i)(pg_|sqlite_)", x)):
            v.append(f"Zugriff auf Systembereich „{x}“ ist nicht erlaubt (Tabellen ohne Schema-Präfix ansprechen).")
        if a == "param" and norm(x[1:]) not in erlaubte_parameter:
            v.append(f"Parameter „{x}“ steht nicht in der Tabelle „Parameter“.")
    if "LIMIT" in woerter and "ORDER" not in woerter:
        v.append("LIMIT ohne ORDER BY liefert ein zufälliges Ergebnis. Sortierung ergänzen.")
    return list(dict.fromkeys(v))


OP_TAUSCH = {">=": ">", ">": ">=", "<=": "<", "<": "<=", "=": "<>", "<>": "=", "!=": "="}
GRENZWERT = "Kein Grenzfall legt fest, ob der Grenzwert selbst (genau gleich) noch dazugehört."


def gegenproben(sql: str) -> list:
    """Kleine, gezielte Verfälschungen des Kompilats. Bemerkt sie kein Grenzfall, ist die Regel dort nicht festgelegt."""
    toks = tokens(sql)
    out, zaehler = [], {}

    def stelle(i):
        pos = sum(len(x) for _, x in toks[:i])
        return sql[sql.rfind("\n", 0, pos) + 1:(sql.find("\n", pos) if sql.find("\n", pos) != -1 else len(sql))].strip()

    def neu(i, ersatz, art, frage, schlucke_leer=False):
        key = (art, toks[i][1].upper())
        zaehler[key] = zaehler.get(key, 0) + 1
        mid = "L-" + hashlib.sha256(f"{art}|{toks[i][1]}|{zaehler[key]}".encode()).hexdigest()[:6]
        rest = toks[i + 2:] if schlucke_leer and i + 1 < len(toks) and toks[i + 1][0] == "leer" else toks[i + 1:]
        out.append({"id": mid, "frage": frage, "stelle": stelle(i),
                    "sql": "".join(x for _, x in toks[:i]) + ersatz + "".join(x for _, x in rest)})

    vor = ""
    for i, (a, x) in enumerate(toks):
        if a in ("leer", "kommentar"):
            continue
        X = x.upper()
        if a == "op" and x in OP_TAUSCH:
            frage = GRENZWERT if x in (">=", ">", "<=", "<") else \
                "Kein Grenzfall hängt an dieser Bedingung: Ins Gegenteil verkehrt, fiele es keinem Beispiel auf."
            neu(i, OP_TAUSCH[x], "op" + x, frage)
        elif a == "wort" and X == "AND":
            neu(i, "OR", "and", "Kein Grenzfall unterscheidet, ob beide Bedingungen zugleich gelten müssen oder eine genügt.")
        elif a == "wort" and X == "OR":
            neu(i, "AND", "or", "Kein Grenzfall zeigt, dass schon eine der beiden Bedingungen allein genügt.")
        elif a == "wort" and X == "NOT":
            neu(i, "", "not", "Kein Grenzfall prüft die Verneinung (NICHT) an dieser Stelle.", True)
        elif a == "wort" and X == "DISTINCT":
            neu(i, "", "distinct", "Kein Grenzfall prüft Mehrfachzählung (derselbe Wert kommt mehrfach vor).", True)
        elif a == "zahl" and vor not in ("SELECT", "LIMIT", "OFFSET") and "." not in x:
            for n in (int(x) + 1, int(x) - 1):
                if n >= 0:
                    neu(i, str(n), f"zahl{n - int(x):+d}", f"Kein Grenzfall legt die Zahl {x} fest: Mit {n} kämen alle Beispiele zum selben Ergebnis.")
        elif a == "text":
            neu(i, x[:-1] + "__x'", "text", f"Kein Grenzfall hängt am Wert {x}.")
        vor = X
    return out


# ───────────────────────── Verbindungen (nur lesend) ─────────────────────────

class Sqlite:
    def __init__(self, c: dict):
        self.pfad = ROOT / c["datei"]

    def _con(self):
        if not self.pfad.is_file():
            raise RegelFehler(f"Datenbank {self.pfad.name} fehlt. Demo-Daten erzeugen: python3 daten/demo_daten_erzeugen.py")
        con = sqlite3.connect(f"file:{quote(str(self.pfad))}?mode=ro", uri=True)
        con.execute("PRAGMA query_only = ON")
        return con

    def katalog(self) -> dict:
        con = self._con()
        try:
            namen = [z[0] for z in con.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view') AND name NOT LIKE 'sqlite_%'")]
            return {n.lower(): [(z[1].lower(), z[2]) for z in con.execute(f'PRAGMA table_info("{n}")')] for n in namen}
        finally:
            con.close()

    def ausfuehren(self, sqls: list, zeitlimit: float) -> list:
        con, out = self._con(), []
        try:
            for s in sqls:
                ende = time.monotonic() + zeitlimit
                con.set_progress_handler(lambda: int(time.monotonic() > ende), 100000)
                try:
                    cur = con.execute(s)
                    out.append({"spalten": [d[0].lower() for d in cur.description], "zeilen": [list(z) for z in cur.fetchall()]})
                except sqlite3.Error as e:
                    out.append({"fehler": "Zeitlimit überschritten" if "interrupted" in str(e) else str(e)})
        finally:
            con.close()
        return out

    def schatten(self, tabelle: str, spalten: list, zeilen: list) -> str:
        def lit(typ, v):
            if v is None:
                return "NULL"
            ist_text = any(x in typ.upper() for x in ("CHAR", "CLOB", "TEXT"))
            return v if not ist_text and re.fullmatch(r"-?\d+(\.\d+)?", v) else "'" + v.replace("'", "''") + "'"
        if not zeilen:
            return f"{tabelle} AS (SELECT " + ", ".join(f"NULL AS {s}" for s, _ in spalten) + " WHERE 1 = 0)"
        werte = ", ".join("(" + ", ".join(lit(t, z.get(s)) for s, t in spalten) + ")" for z in zeilen)
        return f"{tabelle} AS (SELECT " + ", ".join(f"column{i + 1} AS {s}" for i, (s, _) in enumerate(spalten)) + f" FROM (VALUES {werte}) AS v)"


class PostgresDocker:
    """Postgres im Docker-Container, erreicht über `docker exec … psql` (kein Passwort im Projekt nötig)."""
    NULL = "__RW_NULL__"
    PFADE = ("/usr/local/bin/docker", "/opt/homebrew/bin/docker", "/Applications/Docker.app/Contents/Resources/bin/docker")

    def __init__(self, c: dict):
        self.c = c
        for k in ("container", "datenbank", "benutzer", "schema"):
            if not re.fullmatch(r"[\w.-]+", str(c.get(k, ""))):
                raise RegelFehler(f"Verbindung: Angabe „{k}“ fehlt oder ist ungültig.")

    def _psql(self, skript: str, zeitlimit: float):
        docker = shutil.which("docker") or next((p for p in self.PFADE if Path(p).exists()), None)
        if not docker:
            raise RegelFehler("Docker wurde nicht gefunden – die Verbindung ist auf diesem Rechner nicht erreichbar.")
        opt = f"-c default_transaction_read_only=on -c statement_timeout={int(zeitlimit * 1000)} -c search_path={self.c['schema']}"
        cmd = [docker, "exec", "-i", "-e", "PGOPTIONS=" + opt, self.c["container"], "psql", "-X", "-q", "--csv",
               "-P", "null=" + self.NULL, "-U", self.c["benutzer"], "-d", self.c["datenbank"], "-f", "-"]
        try:
            p = subprocess.run(cmd, input=skript, capture_output=True, text=True, timeout=zeitlimit * 3 + 60)
        except subprocess.TimeoutExpired:
            raise RegelFehler("Die Datenbank hat nicht rechtzeitig geantwortet (Zeitlimit).")
        if p.returncode != 0 and "@@RW" not in p.stdout:
            raise RegelFehler("Datenbank nicht erreichbar: " + (p.stderr.strip().splitlines() or ["unbekannter Fehler"])[-1])
        return p.stdout, p.stderr

    def ausfuehren(self, sqls: list, zeitlimit: float) -> list:
        skript = "".join(f"\\echo @@RW {i}\n{einzeilig(ohne_semikolon(s))};\n" for i, s in enumerate(sqls)) + "\\echo @@RW ENDE\n"
        aus, err = self._psql(skript, zeitlimit)
        fehler = {}
        for m in re.finditer(r"psql:<stdin>:(\d+): (?:ERROR|FEHLER):\s*(.*)", err):
            fehler.setdefault((int(m.group(1)) - 2) // 2, m.group(2))
        teile = re.split(r"^@@RW (?:\d+|ENDE)\n", aus, flags=re.M)[1:]
        out = []
        for i in range(len(sqls)):
            roh = list(csv.reader(io.StringIO(teile[i]))) if i < len(teile) else []
            if i in fehler or not roh:
                out.append({"fehler": fehler.get(i, "Abfrage lieferte kein Ergebnis (" + (err.strip().splitlines() or ["?"])[-1] + ")")})
            else:
                out.append({"spalten": [s.lower() for s in roh[0]],
                            "zeilen": [[None if v == self.NULL else v for v in z] for z in roh[1:]]})
        return out

    def katalog(self) -> dict:
        r = self.ausfuehren(["SELECT table_name, column_name, data_type FROM information_schema.columns "
                             f"WHERE table_schema = '{self.c['schema']}' ORDER BY table_name, ordinal_position"], 30)[0]
        if "fehler" in r:
            raise RegelFehler("Datenkatalog nicht lesbar: " + r["fehler"])
        kat: dict = {}
        for t, s, typ in r["zeilen"]:
            kat.setdefault(t.lower(), []).append((s.lower(), typ))
        return kat

    def schatten(self, tabelle: str, spalten: list, zeilen: list) -> str:
        def typ(t):
            return "text" if t.upper() in ("ARRAY", "USER-DEFINED") else t

        def lit(v):
            return "NULL" if v is None else "'" + v.replace("'", "''") + "'"
        if not zeilen:
            return f"{tabelle} AS (SELECT " + ", ".join(f"CAST(NULL AS {typ(t)}) AS {s}" for s, t in spalten) + " WHERE 1 = 0)"
        werte = ", ".join("(" + ", ".join(lit(z.get(s)) for s, _ in spalten) + ")" for z in zeilen)
        return (f"{tabelle} AS (SELECT " + ", ".join(f"CAST(column{i + 1} AS {typ(t)}) AS {s}" for i, (s, t) in enumerate(spalten))
                + f" FROM (VALUES {werte}) AS v)")


def verbindung(name: str):
    c = konfig()["verbindungen"].get(name)
    if not c:
        raise RegelFehler(f"Verbindung „{name}“ ist nicht eingerichtet (bekannt: {', '.join(konfig()['verbindungen'])}).")
    return {"sqlite": Sqlite, "postgres-docker": PostgresDocker}[c["art"]](c)


# ───────────────────────── SQL zusammensetzen ─────────────────────────

def _literal(typ: str, wert: str, name: str) -> str:
    typ, wert = norm(typ), str(wert).strip()
    if typ == "datum":
        wert = heute() if norm(wert) == "heute" else wert
        try:
            dt.date.fromisoformat(wert)
        except ValueError:
            raise RegelFehler(f"Parameter „{name}“: „{wert}“ ist kein Datum (JJJJ-MM-TT).")
        return f"'{wert}'"
    if typ == "zahl":
        if not re.fullmatch(r"-?\d+(\.\d+)?", wert):
            raise RegelFehler(f"Parameter „{name}“: „{wert}“ ist keine Zahl.")
        return wert
    if typ == "text":
        if any(ord(c) < 32 for c in wert):
            raise RegelFehler(f"Parameter „{name}“ enthält unzulässige Zeichen.")
        return "'" + wert.replace("'", "''") + "'"
    raise RegelFehler(f"Parameter „{name}“: Typ „{typ}“ unbekannt (erlaubt: datum, zahl, text).")


def parameter_werte(r: dict, deps: list, im_test: bool, vorgaben: dict = None) -> dict:
    defs = {}
    for x in deps + [r]:
        for p in x["parameter"]:
            if p.get("name"):
                defs[norm(p["name"])] = p
    vorgaben = {norm(k): v for k, v in (vorgaben or {}).items()}
    fremd = set(vorgaben) - set(defs)
    if fremd:
        raise RegelFehler(f"Unbekannte Parameter: {', '.join(sorted(fremd))} (erlaubt: {', '.join(sorted(defs)) or 'keine'}).")
    werte = {}
    for n, p in defs.items():
        roh = p.get("im test", "") if im_test else vorgaben.get(n, p.get("standard", ""))
        if str(roh).strip() == "":
            raise RegelFehler(f"Parameter „{n}“: Wert für {'den Test' if im_test else 'den Lauf'} fehlt.")
        werte[n] = _literal(p.get("typ", ""), roh, n)
    return werte


def zusammensetzen(sql: str, deps: list, schatten: list, werte: dict) -> str:
    """Schattentabellen + genutzte Regeln als CTEs voranstellen, Parameter einsetzen."""
    ctes = list(schatten) + [f"{d['regel_id']} AS (\n{ohne_semikolon(d['sql'])}\n)" for d in deps]
    eigen = ohne_semikolon(sql)
    if ctes:
        m = re.match(r"\s*(?:--[^\n]*\n\s*|/\*.*?\*/\s*)*WITH\b", eigen, re.I | re.S)
        eigen = "WITH " + ",\n".join(ctes) + (",\n" + eigen[m.end():] if m else "\n" + eigen)
    return "".join(werte.get(norm(t[1:]), t) if a == "param" else t for a, t in tokens(eigen))


def _schatten_fuer(r: dict, deps: list, kat: dict, verb, fall_id: str) -> list:
    gesamt = " ".join([r["sql"]] + [d["sql"] for d in deps])
    worte = {norm(t.strip('"')) for a, t in tokens(gesamt) if a in ("wort", "name")}
    ctes = []
    for tab in sorted((set(kat) & worte) | set(r["beispieldaten"])):
        zeilen = []
        for z in r["beispieldaten"].get(tab, []):
            faelle = {norm(f) for f in re.split(r"[,\s]+", z.get("fall", "")) if f}
            if faelle & {norm(fall_id), "*", "alle"}:
                zeilen.append({s: (z.get(s) if z.get(s, "") != "" else None) for s, _ in kat[tab]})
        ctes.append(verb.schatten(tab, kat[tab], zeilen))
    return ctes


# ───────────────────────── Bewerten ─────────────────────────

def _zahl(s):
    s = str(s).strip()
    if re.fullmatch(r"-?\d{1,3}(\.\d{3})*,\d+|-?\d+,\d+", s):
        s = s.replace(".", "").replace(",", ".")
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def _gleich(soll: str, ist) -> bool:
    ist = "" if ist is None else str(ist).strip()
    a, b = _zahl(soll), _zahl(ist)
    return a == b if a is not None and b is not None else norm(soll) in (norm(ist), "leer" if ist == "" else norm(ist))


def bewerte(fall: dict, erg: dict, schluessel: str):
    """(bestanden, tatsächliches Ergebnis in Worten)"""
    if "fehler" in erg:
        return False, "technischer Fehler"
    sp, zeilen = erg["spalten"], erg["zeilen"]
    erw, obj = fall.get("erwartet", "").strip(), fall.get("prüfobjekt", "").strip()
    paare = [(norm(k), v.strip()) for k, _, v in (p.partition("=") for p in erw.split(";")) if _]
    if norm(obj) in ("", "-", "*", "alle"):
        soll = dict(paare).get("anzahl")
        if soll is None:
            return False, "ohne Prüfobjekt ist nur „anzahl = N“ prüfbar"
        return _zahl(soll) == len(zeilen), f"anzahl = {len(zeilen)}"
    key = schluessel or sp[0]
    if key not in sp:
        return False, f"Schlüsselspalte „{key}“ fehlt im Ergebnis"
    treffer = [z for z in zeilen if str(z[sp.index(key)]).strip() == obj]
    if len(treffer) > 1:
        return False, f"kommt {len(treffer)}-mal vor (Mehrfachzählung)"
    if norm(erw) in ("ja", "nein"):
        ist = "ja" if treffer else "nein"
        return ist == norm(erw), ist
    if not paare:
        return False, "„Erwartet“ nicht lesbar (ja, nein oder spalte = wert)"
    if not treffer:
        return False, "nicht im Ergebnis"
    fehlt = [k for k, _ in paare if k not in sp]
    if fehlt:
        return False, f"Spalte „{fehlt[0]}“ fehlt im Ergebnis"
    ist = {k: treffer[0][sp.index(k)] for k, _ in paare}
    return all(_gleich(v, ist[k]) for k, v in paare), "; ".join(f"{k} = {'leer' if v is None else v}" for k, v in ist.items())


# ───────────────────────── Siegel ─────────────────────────

TEILE = {"frage": "Frage", "klartext": "Regel in Klartext", "parameter": "Parameter", "grenzfaelle": "Grenzfälle",
         "beispieldaten": "Beispieldaten", "bewusst_offen": "Bewusst offen", "sql": "SQL",
         "regel_id": "Einstellungen", "verbindung": "Einstellungen", "schluessel": "Einstellungen",
         "ausgabe": "Einstellungen", "max_zeilen": "Einstellungen"}


def kanon(r: dict, genutzte_siegel: dict) -> dict:
    """Der fachliche Inhalt, auf den sich die Freigabe bezieht — unabhängig von Formatierung."""
    k = {x: r[x] for x in ("regel_id", "verbindung", "schluessel", "ausgabe", "max_zeilen", "frage", "klartext",
                           "parameter", "grenzfaelle", "beispieldaten", "bewusst_offen")}
    k["sql"] = "\n".join(l.rstrip() for l in r["sql"].splitlines())
    k["nutzt"] = genutzte_siegel
    return k


def siegel_von(k: dict) -> str:
    return hashlib.sha256(json.dumps(k, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def freigabe_pfad(r: dict, version) -> Path:
    return ROOT / konfig()["ordner"]["freigaben"] / f"{r['titel']} v{version}.md"


def siegel_stand(r: dict, _tiefe: int = 0) -> dict:
    """Prüft, ob der aktuelle Inhalt exakt dem freigegebenen entspricht (inkl. genutzter Regeln)."""
    if _tiefe > 20:
        raise RegelFehler("Regeln nutzen sich im Kreis.")
    genutzt = {}
    for name in r["nutzt"]:
        d = lade_regel(finde_regel(name))
        genutzt[d["regel_id"]] = d["fm"].get("siegel", "") if siegel_stand(d, _tiefe + 1)["gueltig"] else "UNGÜLTIG"
    h, gesiegelt = siegel_von(kanon(r, genutzt)), r["fm"].get("siegel", "")
    stand = {"gueltig": bool(gesiegelt) and gesiegelt == h, "hash": h, "grund": "", "geaendert": [], "ueberfaellig": False}
    if not gesiegelt:
        stand["grund"] = "noch nie freigegeben"
    elif not stand["gueltig"]:
        snap = freigabe_pfad(r, r["fm"].get("version", ""))
        if snap.is_file():
            alt, neu = kanon(lade_regel(snap), {}), kanon(r, {})
            stand["geaendert"] = list(dict.fromkeys(TEILE[x] for x in TEILE if alt[x] != neu[x]))
        stand["geaendert"] = stand["geaendert"] or ["eine genutzte Regel"]
        stand["grund"] = "geändert seit Freigabe: " + ", ".join(stand["geaendert"])
    frist = r["fm"].get("naechste_rezertifizierung", "")
    if stand["gueltig"] and frist and frist < heute():
        stand.update(ueberfaellig=True, grund=f"Rezertifizierung überfällig seit {frist}")
    return stand


# ───────────────────────── Prüfen ─────────────────────────

def _struktur(r: dict, kat: dict) -> list:
    f = []
    if not re.fullmatch(r"[a-z][a-z0-9_]*", r["regel_id"]):
        f.append("Eigenschaft „regel_id“ fehlt oder ist ungültig (Kleinbuchstaben, Ziffern, Unterstrich).")
    if not r["klartext"]:
        f.append("Der Abschnitt „Regel in Klartext“ ist leer.")
    if r["ausgabe"] not in ("anzahl", "tabelle"):
        f.append("Eigenschaft „ausgabe“ muss „anzahl“ oder „tabelle“ sein.")
    ids = [norm(g.get("id", "")) for g in r["grenzfaelle"]]
    if len(ids) < 2:
        f.append("Mindestens zwei Grenzfälle sind nötig (sonst ist nichts entschieden).")
    if "" in ids or len(set(ids)) != len(ids):
        f.append("Jeder Grenzfall braucht eine eindeutige ID.")
    for g in r["grenzfaelle"]:
        if not g.get("erwartet", "").strip():
            f.append(f"Grenzfall {g.get('id', '?')}: „Erwartet“ ist leer – hier fehlt die Entscheidung.")
    for tab, zeilen in r["beispieldaten"].items():
        if tab not in kat:
            f.append(f"Beispieldaten: Tabelle „{tab}“ gibt es in der Datenquelle nicht (siehe Glossar).")
            continue
        spalten = {s for s, _ in kat[tab]}
        for z in zeilen[:1]:
            if "fall" not in z:
                f.append(f"Beispieldaten „{tab}“: Spalte „fall“ fehlt.")
            for s in sorted(set(z) - spalten - {"fall"}):
                f.append(f"Beispieldaten „{tab}“: Spalte „{s}“ gibt es in der Datenquelle nicht (siehe Glossar).")
        for z in zeilen:
            for fall in re.split(r"[,\s]+", z.get("fall", "")):
                if fall and norm(fall) not in ids and norm(fall) not in ("*", "alle"):
                    f.append(f"Beispieldaten „{tab}“: Zeile verweist auf unbekannten Grenzfall „{fall}“.")
    for b in r["bewusst_offen"]:
        if not b.get("begründung", "").strip() or not b.get("entschieden von", "").strip():
            f.append(f"Bewusst offen {b.get('lücke', '?')}: Begründung und „Entschieden von“ sind Pflicht.")
    return list(dict.fromkeys(f))


def pruefen(name, schreiben: bool = True) -> dict:
    """Beweist das Kompilat gegen die Grenzfälle, sucht Lücken, stellt den Siegel-Stand fest."""
    r = lade_regel(finde_regel(name))
    cfg = konfig()
    b = {"regel": r["titel"], "regel_id": r["regel_id"], "fehler": [], "grenzfaelle": [], "luecken": [],
         "gegenproben": 0, "erkannt": 0, "freigabefaehig": False}
    deps, kat, verb = [], {}, None
    try:
        deps = abhaengigkeiten(r)
        verb = verbindung(r["verbindung"])
        kat = verb.katalog()
        b["fehler"] += _struktur(r, kat)
        erlaubt = {norm(p.get("name", "")) for x in deps + [r] for p in x["parameter"]}
        b["fehler"] += sql_regeln(r["sql"], erlaubt)
    except RegelFehler as e:
        b["fehler"].append(str(e))

    if not b["fehler"]:
        try:
            werte = parameter_werte(r, deps, im_test=True)
            schatten = {norm(g["id"]): _schatten_fuer(r, deps, kat, verb, g["id"]) for g in r["grenzfaelle"]}

            def lauf(sql):
                return verb.ausfuehren([zusammensetzen(sql, deps, schatten[norm(g["id"])], werte) for g in r["grenzfaelle"]],
                                       cfg["zeitlimit_sekunden"])
            erg = lauf(r["sql"])
            for g, e in zip(r["grenzfaelle"], erg):
                ok, ist = bewerte(g, e, r["schluessel"])
                b["grenzfaelle"].append({"id": g["id"], "situation": g.get("situation", ""), "erwartet": g["erwartet"],
                                         "ergebnis": ist, "bestanden": ok})
            technisch = [e["fehler"] for e in erg if "fehler" in e]
            if technisch:
                b["fehler"].append("Das Kompilat läuft nicht: " + technisch[0])
            if all(g["bestanden"] for g in b["grenzfaelle"]):
                proben = gegenproben(r["sql"])[: cfg["max_gegenproben"]]
                akzeptiert = {norm(x.get("lücke", "")) for x in r["bewusst_offen"]}
                n = len(r["grenzfaelle"])
                alle = verb.ausfuehren([zusammensetzen(p["sql"], deps, schatten[norm(g["id"])], werte)
                                        for p in proben for g in r["grenzfaelle"]], cfg["zeitlimit_sekunden"])
                b["gegenproben"] = len(proben)
                for i, p in enumerate(proben):
                    if all(bewerte(g, e, r["schluessel"])[0] for g, e in zip(r["grenzfaelle"], alle[i * n:(i + 1) * n])):
                        b["luecken"].append({"id": p["id"], "frage": p["frage"], "stelle": p["stelle"],
                                             "bewusst_offen": norm(p["id"]) in akzeptiert})
                b["erkannt"] = len(proben) - len(b["luecken"])
        except RegelFehler as e:
            b["fehler"].append(str(e))

    gruen = bool(b["grenzfaelle"]) and all(g["bestanden"] for g in b["grenzfaelle"]) and not b["fehler"]
    offen = [l for l in b["luecken"] if not l["bewusst_offen"]]
    b["freigabefaehig"] = gruen and not offen
    b["festigkeit"] = round(100 * b["erkannt"] / b["gegenproben"]) if b["gegenproben"] else (100 if gruen else 0)
    try:
        stand = siegel_stand(r)
    except RegelFehler as e:
        stand = {"gueltig": False, "hash": "", "grund": str(e), "geaendert": [], "ueberfaellig": False}
    b["siegel"] = {k: stand[k] for k in ("gueltig", "grund", "geaendert", "ueberfaellig")}
    b["version"] = int(r["fm"].get("version") or 0)
    b["status"] = ("certified" if stand["gueltig"] and gruen and not stand["ueberfaellig"]
                   else "suspended" if stand["gueltig"] else "review" if b["freigabefaehig"] else "draft")
    b["naechster_schritt"] = _naechster_schritt(b, offen)
    if schreiben:
        text = nfc(r["pfad"].read_text(encoding="utf-8"))
        text = setze_frontmatter(text, {
            "status": b["status"], "grenzfaelle_bestanden": f"{sum(g['bestanden'] for g in b['grenzfaelle'])}/{len(r['grenzfaelle'])}",
            "festigkeit": b["festigkeit"], "offene_fragen": len(offen), "letzte_pruefung": heute()})
        r["pfad"].write_text(setze_abschnitt(text, "Prüfprotokoll", _protokoll(b, r)), encoding="utf-8")
    return b


def _naechster_schritt(b: dict, offen: list) -> str:
    if b["fehler"]:
        return "Fehler beheben (siehe „fehler“), dann erneut prüfen."
    rot = [g["id"] for g in b["grenzfaelle"] if not g["bestanden"]]
    if rot:
        return f"Grenzfälle {', '.join(rot)} schlagen fehl: Kompilat (SQL) oder Beispieldaten korrigieren. Die Entscheidung im Grenzfall ändert nur der Owner."
    if offen:
        return f"{len(offen)} offene Frage(n): je Lücke den Owner fachlich fragen → neuer Grenzfall oder Eintrag unter „Bewusst offen“."
    if b["status"] == "certified":
        return "Regel ist freigegeben und unverändert – sie darf ausgeführt werden."
    if b["status"] == "suspended":
        return "Freigabe ruht (" + (b["siegel"]["grund"] or "Grenzfälle schlagen fehl – Datenquelle geändert?") + "). Owner muss neu freigeben."
    return "Freigabefähig: Rückübersetzung und Wirkung zeigen, dann bittet der Owner um Freigabe."


def _protokoll(b: dict, r: dict) -> str:
    s = b["siegel"]
    kopf = {"certified": "✅ Freigegeben und unverändert", "review": "🟡 Freigabefähig – wartet auf die Freigabe durch den Owner",
            "suspended": "⛔ Freigabe ruht", "draft": "✏️ In Arbeit – noch nicht freigabefähig"}[b["status"]]
    z = [f"> Automatisch erzeugt am {dt.datetime.now():%Y-%m-%d %H:%M} (Engine {VERSION}). Nicht von Hand ändern.", "",
         f"**{kopf}**", "",
         f"- Grenzfälle: {sum(g['bestanden'] for g in b['grenzfaelle'])} von {len(r['grenzfaelle'])} bestanden",
         f"- Festigkeit: {b['erkannt']} von {b['gegenproben']} Gegenproben erkannt ({b['festigkeit']} %)",
         "- Siegel: " + (f"gültig (Version {b['version']}, {r['fm'].get('freigegeben_von', '')}, {r['fm'].get('freigegeben_am', '')})"
                         if s["gueltig"] and not s["ueberfaellig"] else s["grund"]),
         f"- Nächster Schritt: {b['naechster_schritt']}"]
    if b["fehler"]:
        z += ["", "**Fehler**", ""] + [f"- {f}" for f in b["fehler"]]
    if b["grenzfaelle"]:
        z += ["", "| Grenzfall | Erwartet | Ergebnis | |", "|---|---|---|---|"]
        z += [f"| {g['id']} | {g['erwartet']} | {g['ergebnis']} | {'✅' if g['bestanden'] else '❌'} |" for g in b["grenzfaelle"]]
    if b["luecken"]:
        z += ["", "**Lücken – das legt bisher kein Grenzfall fest**", "", "| Lücke | Was offen ist | Stelle | Stand |", "|---|---|---|---|"]
        z += [f"| {l['id']} | {l['frage']} | `{l['stelle'].replace('|', chr(92) + '|')}` | {'bewusst offen' if l['bewusst_offen'] else '❓ offen'} |"
              for l in b["luecken"]]
    return "\n".join(z)


# ───────────────────────── Wirkung (echte Daten, nur Summenwerte) ─────────────────────────

def _echt(r: dict, deps: list, sql: str, werte: dict) -> dict:
    erg = verbindung(r["verbindung"]).ausfuehren([zusammensetzen(sql, deps, [], werte)], konfig()["zeitlimit_sekunden"])[0]
    if "fehler" in erg:
        raise RegelFehler("Abfrage auf den echten Daten fehlgeschlagen: " + erg["fehler"])
    return erg


def _kennzahlen(erg: dict, schluessel: str) -> dict:
    summen = {}
    for i, s in enumerate(erg["spalten"]):
        werte = [_zahl(z[i]) for z in erg["zeilen"] if z[i] is not None]
        if s != (schluessel or erg["spalten"][0]) and werte and None not in werte:
            summen[s] = str(sum(werte))
    return {"zeilen": len(erg["zeilen"]), "summen": summen}


def wirkung(name, parameter: dict = None) -> dict:
    """Was die Regel auf den echten Daten bewirkt — und was sich gegenüber der freigegebenen Version ändert. Nur Summenwerte."""
    r = lade_regel(finde_regel(name))
    deps = abhaengigkeiten(r)
    verstoesse = sql_regeln(r["sql"], {norm(p.get("name", "")) for x in deps + [r] for p in x["parameter"]})
    if verstoesse:
        raise RegelFehler("Kompilat verletzt die Bauregeln: " + " ".join(verstoesse))
    werte = parameter_werte(r, deps, im_test=False, vorgaben=parameter)
    neu = _echt(r, deps, r["sql"], werte)
    out = {"regel": r["titel"], "parameter": werte, "neu": _kennzahlen(neu, r["schluessel"]), "freigegeben": None}
    snap = freigabe_pfad(r, r["fm"].get("version", ""))
    if snap.is_file():
        alt = _echt(r, deps, lade_regel(snap)["sql"], werte)
        ki = lambda e: {str(z[e["spalten"].index(r["schluessel"] or e["spalten"][0])]) for z in e["zeilen"]}
        a, n = ki(alt), ki(neu)
        out["freigegeben"] = dict(_kennzahlen(alt, r["schluessel"]), version=int(r["fm"].get("version") or 0))
        out["unterschied"] = {"kommen_dazu": len(n - a), "fallen_weg": len(a - n), "bleiben": len(a & n)}
    return out


# ───────────────────────── Freigeben (nur durch einen Menschen) ─────────────────────────

def mensch_bestaetigt(text: str) -> bool:
    """Bestätigung über einen Kanal, den die KI nicht bedienen kann: macOS-Dialog oder Tastatur am Terminal."""
    if sys.platform == "darwin" and shutil.which("osascript"):
        skript = ('on run argv\n display dialog (item 1 of argv) with title "ContextSafe Regelwerkstatt – Freigabe" '
                  'buttons {"Abbrechen", "Freigeben"} default button "Abbrechen" cancel button "Abbrechen" '
                  'with icon caution giving up after 120\n return button returned of result\nend run')
        p = subprocess.run(["osascript", "-e", skript, text], capture_output=True, text=True)
        return p.returncode == 0 and p.stdout.strip() == "Freigeben"
    if sys.stdin.isatty():
        print(text, file=sys.stderr)
        return input('Zum Freigeben "Freigeben" eintippen: ').strip() == "Freigeben"
    return False


def freigeben(name, von: str, aenderung: str, bestaetiger=None) -> dict:
    """Versiegelt die Regel. Nur wenn alles bewiesen ist, nur durch den Owner, nur nach menschlicher Bestätigung."""
    b = pruefen(name)
    r = lade_regel(finde_regel(name))
    owner = r["fm"].get("owner", "")
    if not b["freigabefaehig"]:
        raise RegelFehler("Nicht freigabefähig. " + b["naechster_schritt"])
    if b["siegel"]["gueltig"] and not b["siegel"]["ueberfaellig"]:
        raise RegelFehler("Die Regel ist bereits freigegeben und seitdem unverändert.")
    if not owner:
        raise RegelFehler("Kein Owner eingetragen (Eigenschaft „owner“). Ohne Owner keine Freigabe.")
    if norm(von) != norm(owner):
        raise RegelFehler(f"Nur der Owner ({owner}) darf diese Regel freigeben, nicht „{von}“.")
    if not str(aenderung).strip():
        raise RegelFehler("Bitte kurz angeben, was sich mit dieser Version ändert.")
    for d in (lade_regel(finde_regel(n)) for n in r["nutzt"]):
        if not siegel_stand(d)["gueltig"]:
            raise RegelFehler(f"Die genutzte Regel „{d['titel']}“ ist nicht freigegeben. Erst diese freigeben.")
    version = int(r["fm"].get("version") or 0) + 1
    offen = sum(l["bewusst_offen"] for l in b["luecken"])
    text = (f"Regel: {r['titel']}  (Version {version})\nFreigabe durch: {owner}\n\n"
            f"Geprüft: {len(b['grenzfaelle'])} von {len(b['grenzfaelle'])} Grenzfällen bestanden, "
            f"Festigkeit {b['festigkeit']} %, {offen} Lücke(n) bewusst offen.\n"
            f"Änderung: {aenderung}\n\n"
            "Mit „Freigeben“ bestätigst du, dass Regel in Klartext und Grenzfälle fachlich richtig entschieden sind, "
            "und übernimmst die Verantwortung für diese Regel.")
    if not (bestaetiger or mensch_bestaetigt)(text):
        raise RegelFehler("Freigabe nicht bestätigt. Die Bestätigung muss ein Mensch geben (Dialog am Mac oder Eingabe am Terminal).")
    monate = konfig()["rezertifizierung_monate"]
    j, m = divmod(dt.date.today().month - 1 + monate, 12)
    frist = dt.date(dt.date.today().year + j, m + 1, min(dt.date.today().day, 28)).isoformat()
    siegel = siegel_stand(r)["hash"]
    text_neu = setze_frontmatter(nfc(r["pfad"].read_text(encoding="utf-8")), {
        "status": "certified", "version": version, "siegel": siegel, "freigegeben_von": owner,
        "freigegeben_am": heute(), "naechste_rezertifizierung": frist})
    hist = lade_regel(r["pfad"])["text"]
    alt = abschnitte(hist[FM_RE.match(hist).end():]).get("änderungshistorie", "")
    kopf = "| Version | Datum | Freigegeben von | Änderung | Siegel |\n|---|---|---|---|---|"
    zeilen = [l for l in alt.splitlines() if l.strip().startswith("|")][2:]
    zeilen.append(f"| {version} | {heute()} | {owner} | {str(aenderung).replace('|', '/')} | `{siegel[:12]}` |")
    r["pfad"].write_text(setze_abschnitt(text_neu, "Änderungshistorie", kopf + "\n" + "\n".join(zeilen)), encoding="utf-8")
    pruefen(r["pfad"])
    snap = freigabe_pfad(r, version)
    snap.parent.mkdir(parents=True, exist_ok=True)
    if snap.exists():
        os.chmod(snap, 0o644)
    snap.write_text(nfc(r["pfad"].read_text(encoding="utf-8")).replace("  - typ/regel\n", "  - typ/freigabe\n", 1), encoding="utf-8")
    os.chmod(snap, 0o444)  # Freigabestand ist unveränderlich festgehalten
    return {"regel": r["titel"], "version": version, "siegel": siegel, "freigegeben_von": owner,
            "naechste_rezertifizierung": frist, "festgehalten_in": str(snap.relative_to(ROOT))}


# ───────────────────────── Ausführen (nur versiegelte Regeln) ─────────────────────────

def _lauf_protokoll(r: dict, kopf: dict, rumpf: str) -> str:
    ordner = ROOT / konfig()["ordner"]["laeufe"]
    ordner.mkdir(parents=True, exist_ok=True)
    jetzt = dt.datetime.now()
    pfad = ordner / f"{jetzt:%Y-%m-%d %H%M%S} {r['titel']}.md"
    fm = {"typ": "lauf", "regel": f"[[{r['titel']}]]", "regel_id": r["regel_id"], "version": int(r["fm"].get("version") or 0),
          "siegel": r["fm"].get("siegel", ""), "zeitpunkt": f"{jetzt:%Y-%m-%dT%H:%M:%S}", "engine": VERSION}
    fm.update(kopf)
    pfad.write_text("---\n" + "\n".join(f"{k}: {_yaml(v)}" for k, v in fm.items()) + "\n---\n"
                    + f"# Lauf {jetzt:%Y-%m-%d %H:%M:%S} – {r['titel']}\n\n{rumpf}\n", encoding="utf-8")
    return str(pfad.relative_to(ROOT))


def ausfuehren(name, parameter: dict = None, ausgeloest_von: str = "unbekannt") -> dict:
    """Führt eine Regel auf den echten Daten aus — ausschließlich, wenn ihr Siegel gültig ist."""
    r = lade_regel(finde_regel(name))
    stand = siegel_stand(r)
    if not stand["gueltig"] or stand["ueberfaellig"]:
        grund = "Ausführung verweigert – " + stand["grund"] + ". Der Owner muss die Regel prüfen und (neu) freigeben."
        _lauf_protokoll(r, {"ergebnis": "verweigert", "ausgeloest_von": ausgeloest_von}, f"**Verweigert:** {grund}")
        raise RegelFehler(grund)
    deps = abhaengigkeiten(r)
    try:
        werte = parameter_werte(r, deps, im_test=False, vorgaben=parameter)
        erg = _echt(r, deps, r["sql"], werte)
    except RegelFehler as e:
        _lauf_protokoll(r, {"ergebnis": "fehler", "ausgeloest_von": ausgeloest_von}, f"**Fehler:** {e}")
        raise
    n = len(erg["zeilen"])
    gezeigt = erg["zeilen"][: r["max_zeilen"]] if r["ausgabe"] == "tabelle" else []
    ergebnis_hash = hashlib.sha256(json.dumps(erg["zeilen"], default=str, ensure_ascii=False).encode("utf-8")).hexdigest()
    rumpf = [f"**Parameter:** {', '.join(f'{k} = {v}' for k, v in werte.items()) or 'keine'}", "",
             f"**Ergebnis:** {n} Zeile(n)" + (f", davon {len(gezeigt)} gezeigt" if r["ausgabe"] == "tabelle" else " (nur Anzahl ausgegeben)")]
    if gezeigt:
        rumpf += ["", "| " + " | ".join(erg["spalten"]) + " |", "|" + "---|" * len(erg["spalten"])]
        rumpf += ["| " + " | ".join("" if v is None else str(v) for v in z) + " |" for z in gezeigt]
    log = _lauf_protokoll(r, {"ergebnis": "erfolgreich", "zeilen": n, "ergebnis_hash": ergebnis_hash,
                              "ausgeloest_von": ausgeloest_von}, "\n".join(rumpf))
    r["pfad"].write_text(setze_frontmatter(nfc(r["pfad"].read_text(encoding="utf-8")), {"letzter_lauf": heute()}), encoding="utf-8")
    out = {"regel": r["titel"], "version": int(r["fm"].get("version") or 0), "freigegeben_von": r["fm"].get("freigegeben_von", ""),
           "parameter": werte, "anzahl": n, "protokoll": log}
    if r["ausgabe"] == "tabelle":
        out.update(spalten=erg["spalten"], zeilen=gezeigt, gekuerzt=n > len(gezeigt))
    return out


# ───────────────────────── Übersicht ─────────────────────────

def liste() -> list:
    """Alle Regeln mit ihrem tatsächlichen Stand. Gleicht dabei veraltete Status-Angaben in den Notizen ab."""
    out = []
    for f in sorted(regel_ordner().glob("*.md")):
        r = lade_regel(f)
        if not r["regel_id"]:
            continue
        try:
            stand = siegel_stand(r)
        except RegelFehler as e:
            stand = {"gueltig": False, "grund": str(e), "ueberfaellig": False}
        status = r["fm"].get("status", "draft")
        ausfuehrbar = stand["gueltig"] and not stand["ueberfaellig"]
        soll = ("certified" if ausfuehrbar else "suspended" if stand["ueberfaellig"]
                else "draft" if status == "certified" else status)
        if soll != status:
            f.write_text(setze_frontmatter(r["text"], {"status": soll}), encoding="utf-8")
        out.append({"regel": r["titel"], "regel_id": r["regel_id"], "frage": r["frage"], "status": soll,
                    "ausfuehrbar": ausfuehrbar, "hinweis": stand["grund"], "owner": r["fm"].get("owner", ""),
                    "version": int(r["fm"].get("version") or 0), "ausgabe": r["ausgabe"],
                    "grenzfaelle": r["fm"].get("grenzfaelle_bestanden", ""), "festigkeit": r["fm"].get("festigkeit", ""),
                    "offene_fragen": r["fm"].get("offene_fragen", ""),
                    "parameter": [p.get("name", "") for p in r["parameter"]],
                    "naechste_rezertifizierung": r["fm"].get("naechste_rezertifizierung", "")})
    return out


# ───────────────────────── Kommandozeile ─────────────────────────

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="ContextSafe Regelwerkstatt")
    sub = ap.add_subparsers(dest="befehl", required=True)
    sub.add_parser("liste")
    for n in ("pruefen", "wirkung", "ausfuehren"):
        p = sub.add_parser(n)
        p.add_argument("regel")
        if n != "pruefen":
            p.add_argument("--parameter", action="append", default=[], metavar="name=wert")
    p = sub.add_parser("freigeben")
    p.add_argument("regel")
    p.add_argument("--von", required=True)
    p.add_argument("--aenderung", required=True)
    a = ap.parse_args(argv)
    params = dict(x.split("=", 1) for x in getattr(a, "parameter", []))
    try:
        erg = (liste() if a.befehl == "liste" else pruefen(a.regel) if a.befehl == "pruefen"
               else wirkung(a.regel, params) if a.befehl == "wirkung"
               else freigeben(a.regel, a.von, a.aenderung) if a.befehl == "freigeben"
               else ausfuehren(a.regel, params, "Kommandozeile"))
    except RegelFehler as e:
        print(json.dumps({"fehler": str(e)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(erg, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
