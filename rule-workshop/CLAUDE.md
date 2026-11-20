# ContextSafe Regelwerkstatt

Fachexperten erstellen, ändern und verantworten hier Geschäftsregeln selbst. Einstieg: `README.de.md` (English: `README.md`). Hintergrund: `docs/concept.de.md`.

## Was hier gilt

1. **Datenfragen nur über freigegebene Regeln.** `regel_liste` → `regel_ausfuehren` (Skill `regel-ausfuehren`). Kein freies SQL, kein direkter Zugriff auf Datenbanken oder Datenbankdateien.
2. **Regeln entstehen in Notizen** unter `Regeln/` (Skill `regel-werkstatt`). Der Mensch entscheidet Grenzfälle, du übersetzt, die Engine beweist.
3. **Nach jeder Änderung an einer Regel-Notiz `regel_pruefen`.** Das Urteil der Engine gilt.
4. **Freigabe nur auf ausdrücklichen Wunsch des Owners** über `regel_freigeben`. Siegel, Version und Status nie von Hand setzen.
5. **Mit dem Menschen in Fachsprache sprechen.** Kein SQL zeigen, außer er fragt danach.
6. `Protokoll/` ist das Prüfarchiv: nichts darin ändern oder löschen.
7. Änderungen an `engine/` sind Plattform-Arbeit, keine Regel-Arbeit: nur auf ausdrücklichen Auftrag, danach `python3 engine/tests/test_regelwerk.py`.
