#!/usr/bin/env python3
"""MCP-Server (stdio) der ContextSafe Regelwerkstatt.

Der einzige Weg der KI zu den Daten. Er bietet bewusst KEIN freies SQL an:
- Entwürfe laufen nur gegen Beispieldaten (regel_pruefen) oder liefern nur Summenwerte (regel_wirkung).
- Echte Ergebnisse gibt es nur aus versiegelten Regeln (regel_ausfuehren).
- Die Freigabe (regel_freigeben) verlangt eine Bestätigung durch einen Menschen außerhalb des Chats.

Nur Python-Standardbibliothek. Start:  python3 engine/mcp_server.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regelwerk as rw  # noqa: E402

REGEL = {"type": "string", "description": "Titel der Regel-Notiz (z. B. „Aktiver Kunde“) oder ihre regel_id"}
PARAMETER = {"type": "object", "description": "Optionale Parameterwerte, z. B. {\"stichtag\": \"2026-11-11\"}. Ohne Angabe gilt der Standard aus der Regel.",
             "additionalProperties": {"type": "string"}}

WERKZEUGE = [
    {"name": "regel_liste",
     "description": "Alle Regeln mit Frage, Owner, Status und ob sie ausführbar sind. Immer zuerst aufrufen, um die passende freigegebene Regel für eine Fachfrage zu finden.",
     "inputSchema": {"type": "object", "properties": {}}},
    {"name": "regel_pruefen",
     "description": "Beweist das SQL-Kompilat einer Regel gegen ihre Grenzfälle (läuft nur auf Beispieldaten, nie auf echten Daten), sucht Lücken per Gegenprobe und schreibt das Prüfprotokoll in die Notiz. Nach jeder Änderung an der Notiz aufrufen.",
     "inputSchema": {"type": "object", "properties": {"regel": REGEL}, "required": ["regel"]}},
    {"name": "regel_wirkung",
     "description": "Wirkungsvorschau auf den echten Daten: wie viele Treffer die Regel jetzt liefert und was sich gegenüber der freigegebenen Version ändert. Gibt ausschließlich Summenwerte zurück, nie Einzelzeilen.",
     "inputSchema": {"type": "object", "properties": {"regel": REGEL, "parameter": PARAMETER}, "required": ["regel"]}},
    {"name": "regel_freigeben",
     "description": "Versiegelt eine freigabefähige Regel. Nur aufrufen, wenn der Owner im Gespräch ausdrücklich darum bittet. Auf dem Rechner des Owners erscheint ein Bestätigungsdialog – ohne dessen Klick gibt es keine Freigabe.",
     "inputSchema": {"type": "object", "properties": {
         "regel": REGEL,
         "von": {"type": "string", "description": "Name des freigebenden Menschen; muss dem Owner der Regel entsprechen"},
         "aenderung": {"type": "string", "description": "Ein Satz: was sich mit dieser Version fachlich ändert (bei der ersten Version: „Erstfreigabe“)"}},
         "required": ["regel", "von", "aenderung"]}},
    {"name": "regel_ausfuehren",
     "description": "Führt eine freigegebene Regel auf den echten Daten aus und protokolliert den Lauf. Verweigert, wenn das Siegel fehlt, gebrochen oder überfällig ist. Das ist der einzige Weg zu echten Ergebnissen.",
     "inputSchema": {"type": "object", "properties": {"regel": REGEL, "parameter": PARAMETER}, "required": ["regel"]}},
]

HINWEIS = ("ContextSafe Regelwerkstatt: Fachfragen werden nur über freigegebene Regeln beantwortet (regel_liste → regel_ausfuehren). "
           "Es gibt kein freies SQL. Regeln entstehen und ändern sich in Markdown-Notizen; nach jeder Änderung regel_pruefen.")


def rufe(name: str, a: dict):
    if name == "regel_liste":
        return rw.liste()
    if name == "regel_pruefen":
        return rw.pruefen(a["regel"])
    if name == "regel_wirkung":
        return rw.wirkung(a["regel"], a.get("parameter"))
    if name == "regel_freigeben":
        return rw.freigeben(a["regel"], a["von"], a["aenderung"])
    if name == "regel_ausfuehren":
        return rw.ausfuehren(a["regel"], a.get("parameter"), "Claude (MCP)")
    raise rw.RegelFehler(f"Unbekanntes Werkzeug: {name}")


def bearbeite(msg: dict):
    methode, params = msg.get("method"), msg.get("params") or {}
    if methode == "initialize":
        return {"protocolVersion": params.get("protocolVersion", "2025-06-18"), "capabilities": {"tools": {}},
                "serverInfo": {"name": "regelwerk", "version": rw.VERSION}, "instructions": HINWEIS}
    if methode == "ping":
        return {}
    if methode == "tools/list":
        return {"tools": WERKZEUGE}
    if methode == "tools/call":
        try:
            text, fehler = json.dumps(rufe(params.get("name"), params.get("arguments") or {}), ensure_ascii=False, indent=2, default=str), False
        except rw.RegelFehler as e:
            text, fehler = str(e), True
        except Exception as e:  # unerwartet: dem Modell melden statt den Server zu beenden
            text, fehler = f"Interner Fehler der Engine: {type(e).__name__}: {e}", True
        return {"content": [{"type": "text", "text": text}], "isError": fehler}
    return None


def main():
    for strom in (sys.stdin, sys.stdout):
        strom.reconfigure(encoding="utf-8")
    for zeile in sys.stdin:
        try:
            msg = json.loads(zeile)
        except ValueError:
            continue
        if "id" not in msg:  # Benachrichtigung: keine Antwort
            continue
        ergebnis = bearbeite(msg)
        antwort = {"jsonrpc": "2.0", "id": msg["id"]}
        if ergebnis is None:
            antwort["error"] = {"code": -32601, "message": f"Methode nicht unterstützt: {msg.get('method')}"}
        else:
            antwort["result"] = ergebnis
        sys.stdout.write(json.dumps(antwort, ensure_ascii=False) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
