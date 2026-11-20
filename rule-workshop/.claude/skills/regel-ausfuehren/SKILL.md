---
name: regel-ausfuehren
description: Fachfragen zu Daten ausschließlich über freigegebene Regeln der ContextSafe Regelwerkstatt beantworten. Verwenden, wenn jemand eine Zahl, Liste oder Auswertung aus den Daten will ("Wie viele aktive Kunden haben wir?", "Zeig mir die Upselling-Kandidaten", "Top 10 Bestellungen") oder eine Regel regelmäßig laufen lassen möchte.
---

# Regel ausführen

Antworten auf Datenfragen kommen nur aus freigegebenen Regeln. Du wählst die Regel, die Engine rechnet.

## Ablauf

1. `regel_liste` aufrufen. Die Regel suchen, deren „frage“ zur gestellten Frage passt.
2. Passt eine Regel und ist sie `ausfuehrbar`: `regel_ausfuehren` aufrufen. Parameter nur setzen, wenn der Mensch einen Wert genannt hat (z. B. einen Stichtag). Sonst gilt der Standard der Regel.
3. Antworten mit:
   - dem Ergebnis,
   - der Regel, ihrer Version und dem Owner („nach Regel *Aktiver Kunde*, Version 2, freigegeben von …“),
   - den verwendeten Parametern,
   - dem Verweis auf das Lauf-Protokoll.

## Wenn es nicht geht

| Lage | Was du tust |
|---|---|
| Keine Regel passt | Das sagen. Keine eigene Abfrage, keine Schätzung. Anbieten, die Regel gemeinsam zu erstellen (Skill `regel-werkstatt`) |
| Regel passt nur ungefähr | Den Unterschied benennen und fragen, ob das Ergebnis trotzdem hilft |
| Ausführung verweigert | Den Grund in Alltagssprache nennen (geändert seit Freigabe, nie freigegeben, Rezertifizierung überfällig) und wer handeln muss: der Owner |

## Grenzen

- Kein SQL schreiben, keine anderen Datenbank-Werkzeuge nutzen, keine Datenbankdatei öffnen.
- Ergebnisse nicht umrechnen oder umdeuten. Formatieren und erklären ist in Ordnung.
- Eine verweigerte Regel nicht selbst „reparieren“, um die Frage doch zu beantworten.

## Ohne MCP-Werkzeuge

- `python3 engine/regelwerk.py liste`
- `python3 engine/regelwerk.py ausfuehren "<Titel>" --parameter stichtag=2026-11-11`
