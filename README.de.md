# ContextSafe

[English](README.md) · **Deutsch**

**Deterministische, kontrollierte Datenverarbeitung mit LLM-Agents (Claude + MCP + Agent Skills).**

> Das Modell interpretiert. Ein zertifiziertes, deterministisches Artefakt rechnet. Ein Mensch gibt frei. Jeder Lauf hinterlässt Nachweise.

ContextSafe ist ein Proof of Concept (PoC), der eine Frage beantwortet:

> *Wie kann ein LLM-Agent mit Unternehmensdaten arbeiten, ohne dass Rohdaten in den Modellkontext gelangen, und so, dass jeder Lauf reproduzierbar, manipulationssicher nachweisbar und prüfbar ist?*

> **Neu (2026-11):** [Regelwerkstatt / Rule Workshop](rule-workshop/README.de.md), ein MVP, der die offene Frage hinter diesem PoC angeht: Wer erstellt und verantwortet das zertifizierte Artefakt? Antwort: der Fachexperte, der Grenzfälle entscheidet statt Code zu lesen.

---

## Umfang

| Im Umfang | Nicht im Umfang |
|----------|--------------|
| Wiederkehrende Fragen zur Entscheidungsunterstützung auf strukturierten Daten | Ad-hoc, offene Datenexploration („chat with your data“) |
| Ein **zertifiziertes** Berechnungsartefakt (hier: ein SQL-Skript) | LLM-generiertes SQL zur Laufzeit |
| Governance-Vertrag je Use Case (Process Contract, Markdown + YAML) | Produktives IAM, Secrets-Management, mandantenfähiges RBAC |
| Integritäts-Gates (SHA-256) für SQL **und** Agent Skills | Kryptografische Signatur / PKI (siehe [ROADMAP](ROADMAP.md), H/I) |
| Zertifizierung und Rezertifizierung mit Mensch im Prozess | Autonome Entscheidungen oder Rückschreiben in operative Systeme |
| Lauf-, Fehler- und Änderungsprotokoll als Audit-Trail | Formelle Konformitätsbewertung nach EU AI Act |

**Referenz-Use-Case:** TPC-H Query 3, „Top 10 Shipping Priorities“: die 10 nicht ausgelieferten Bestellungen mit dem höchsten Umsatz im Marktsegment `BUILDING` (Stichtag 1995-03-15), wöchentlich als HTML-E-Mail-Report zugestellt.

**Stand (2026-10-25):** PoC abgeschlossen. Process Contract `v0.8.0` rezertifiziert, letzter Lauf erfolgreich. Die vollständige datierte Historie steht im [CHANGELOG](CHANGELOG.md), einschließlich eines 17-wöchigen Ausfalls, den das Integritäts-Gate korrekt ausgelöst hat.

---

## Kernprinzip

```
Naiv:         Nutzer → LLM → Ad-hoc-SQL → DB → tausende Rohzeilen → LLM-Kontext

ContextSafe:  Schema einmal erkunden → kodifizieren → zertifizieren (Hash + Freigeber)
              → zertifiziertes Artefakt ausführen (nur lesend) → nur die Ergebnismenge → LLM
```

Drei Eigenschaften, die der PoC zeigt. Jede ist in [Claims & Evidence](docs/claims-and-evidence.md) ehrlich bewertet (auf Englisch):

1. **Kontext-Minimierung:** Nur die zertifizierte Ergebnismenge (hier: 10 aggregierte Zeilen) gelangt in den Modellkontext.
2. **Manipulationsnachweis:** SQL und alle sechs Skills sind per SHA-256 im Process Contract fixiert. Eine Abweichung bricht den Lauf ab und setzt den Prozess auf „suspended“.
3. **Prüfbarkeit:** Jeder Lauf und jeder Abbruch schreibt ein Protokoll. Jede Änderung am Vertrag steht in seinem `change_log`.

---

## Der ganzheitliche Ansatz: ein Lebenszyklus, kein Werkzeug

ContextSafe ist weniger eine Software als ein **Lebenszyklus-Muster**, das auf fast jeden wiederkehrenden, datengetriebenen Use Case passt:

```
 1. ERKUNDEN     LLM sieht nur Schema/Metadaten, nie Daten
 2. KODIFIZIEREN Die Berechnung wird ein deterministisches Artefakt
                 (SQL, dbt-Modell, Python, Alteryx-Workflow, API-Aufruf)
 3. VERTRAG      Ein lesbarer Process Contract bindet Artefakt, Skills,
                 Rollen, Empfänger, Zeitplan und Hashes
 4. ZERTIFIZIEREN Jedes ausführbare Teil hashen; ein Freigeber zeichnet ab
 5. AUSFÜHREN    Erst die Gates (fail closed), dann lesend ausführen; das LLM
                 erzählt nur das Ergebnis
 6. NACHWEIS     Lauf-, Fehler-, Änderungsprotokoll, versionierte Historie
 7. REZERTIFIZIEREN Ablaufdatum, Drift-Erkennung, Diff-Review vor dem Neu-Hashen
```

Dieselben sieben Schritte funktionieren, ob das Artefakt eine SQL-Abfrage, ein Prognose-Notebook, eine Dokumenten-Extraktions-Pipeline oder ein KPI-Report ist. Das LLM wandert an die Ränder, zu Erkundung und Erzählung, und der deterministische Kern bleibt zertifizierbar. Siehe [Applying ContextSafe to other use cases](docs/applying-to-other-use-cases.md) (Englisch), das auch behandelt, wo das Muster **nicht** passt.

---

## Aufbau des Repositories

```
contextsafe/
├── README.md, README.de.md            ← diese Datei (Umfang, Prinzip, Ansatz)
├── ROADMAP.md                         ← Entwicklungspunkte A–J mit Datum und Stand
├── CHANGELOG.md                       ← datierte Projekt-Zeitleiste
├── LICENSE                            ← MIT
├── docs/                              ← (Englisch)
│   ├── architecture.md                ← Kontexte, Pipeline, Datenpfad
│   ├── governance-model.md            ← Process Contract, Lebenszyklus, Gates, Rollen, EU-AI-Act-Bezug
│   ├── claims-and-evidence.md         ← jede Aussage, gegen Belege bewertet
│   ├── lessons-learned.md             ← Post-Mortem des Ausfalls 2026-06-15 → 2026-10-19
│   └── applying-to-other-use-cases.md ← Verallgemeinerung + Grenzen
├── process/
│   ├── process-contract.template.md   ← Vorlage für neue Use Cases
│   └── tpch_q3.process.md             ← Referenzvertrag (EN, personenbezogene Daten ersetzt)
├── sql/q3_shipping_priority.sql       ← zertifiziertes Skript (Hash identisch zum Original)
├── skills/                            ← 6 Agent Skills (SKILL.md, deutsche Originale)
├── hashes/SHA256SUMS                  ← Hashes aller zertifizierten Artefakte in diesem Repository
├── scripts/verify.sh                  ← deterministischer Pre-Flight (ohne LLM)
└── rule-workshop/                     ← Regelwerkstatt (MVP): Fachexperten erstellen und verantworten Regeln
```

> **Sprachhinweis:** Die sechs `SKILL.md`-Dateien sind im deutschen Original veröffentlicht. Eine Übersetzung würde ihre Hashes ändern und die Zertifizierungskette ungültig machen. Alle übrigen Inhalte sind englisch, die Hauptdokumente zusätzlich deutsch.
>
> **Schwärzungshinweis:** Eine Beispiel-E-Mail-Adresse in `skills/skill_send_html_email/SKILL.md` wurde durch `example.com` ersetzt. Der Hash dieser Datei weicht deshalb vom Vault-Original ab (`de8b95b1…b8d5` → `bf75bbc6…97f4`). `hashes/SHA256SUMS` und der Referenzvertrag verwenden den veröffentlichten Wert.

---

## Schnellstart: Zertifizierungskette prüfen

```bash
./scripts/verify.sh process/tpch_q3.process.md
```

Das Skript berechnet jeden SHA-256 neu, vergleicht ihn mit dem Process Contract und prüft Status und Rezertifizierungsdatum. Es ist deterministisch und läuft ohne LLM. Es schließt außerdem eine Lücke des PoC selbst: Dort meldete das orchestrierende LLM seine eigenen Hash-Prüfungen.

---

## Technologie (Referenzimplementierung)

| Thema | Wahl |
|---------|--------|
| Entwicklung / Specs | Claude.ai Chat |
| Zertifizierung (Hashing, SQL-Erzeugung) | Claude Code (`shasum -a 256`) |
| Orchestrierung | Claude CoWork (Sonnet), wöchentlich geplant |
| Erzählung | Für Claude Haiku ausgelegt. In der Praxis nutzte bisher jeder Lauf Sonnet (Haiku in CoWork nicht verfügbar) |
| Datenbank | PostgreSQL (Docker), TPC-H-Daten, `@sarmadparvez/postgresql-mcp` mit `?mode=readonly` |
| Vertrag + Protokolle | Obsidian-Vault (Markdown + YAML, Meta-Bind-Widgets), Local-REST-API-MCP |
| Zustellung | Gmail-MCP |
| Versionierung | Automatisches Git-Backup des Vaults (alle 10 Minuten) |

---

## Einordnung (Stand 2026-10)

- **Agent Skills sind nicht die Neuheit.** Anthropic hat sie im Oktober 2025 eingeführt, und „build skills, not agents“ war Anthropics eigene Botschaft Ende 2025. ContextSafe startete im März 2026 und *nutzt* Skills.
- **Die Neuheit ist, Skills als zertifizierte, per Hash fixierte Artefakte zu behandeln**, innerhalb eines Governance-Lebenszyklus: fail-closed Gates, Freigeber, Rezertifizierung, Audit-Trail. Ende 2025 waren Versionierung, Abhängigkeitsverwaltung und Laufzeit-Vorhersagbarkeit offene Fragen. Branchen-Checklisten (z. B. OWASP Agentic Skills Top 10) fordern heute genau das: Inhalt per Hash fixieren, beim Laden neu prüfen, bei Änderung verweigern.
- **Das Muster ist in Datenplattformen etabliert:** Snowflake *Verified Queries* und Databricks Genie *Trusted Assets* lassen ein LLM ebenfalls aus vorab freigegebenen, deterministischen Abfragen wählen. ContextSafe wendet dieselbe Idee eine Ebene höher an, auf die Anweisungen des Agents selbst.
- **Ehrliche Einschränkung:** Für einen festen Wochenreport ist eine deterministische Workflow-Engine (z. B. n8n, Alteryx Server) mit einem einzigen LLM-Schritt für die Erzählung einfacher und zuverlässiger als ein LLM als Orchestrator. Siehe [ROADMAP](ROADMAP.md), Punkt **I**.

---

## Autor

Christian Kainzmeier. Gebaut mit Claude (Chat, Code, CoWork).

Lizenz: [MIT](LICENSE). Frei nutzbar, veränderbar und weiterverteilbar.
