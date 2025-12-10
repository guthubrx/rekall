# Rekall

```
        ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗
        ██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║
        ██████╔╝█████╗  █████╔╝ ███████║██║     ██║
        ██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║
        ██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗
        ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
```

<p align="center">
  <img src="https://img.shields.io/badge/100%25-Local-blue?style=flat-square" alt="100% Local">
  <img src="https://img.shields.io/badge/No_API_Keys-green?style=flat-square" alt="No API Keys">
  <img src="https://img.shields.io/badge/MCP-Compatible-purple?style=flat-square" alt="MCP Compatible">
  <img src="https://img.shields.io/badge/Python-3.9+-yellow?style=flat-square" alt="Python 3.9+">
</p>

> *"Get your ass to Mars. Quaid... crush those bugs"*

**Übersetzungen:** [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [中文](README.zh-CN.md)

---

### TL;DR

**Das Problem:** Jeder Entwickler hat denselben Bug zweimal gelöst. Nicht aus Nachlässigkeit — weil wir Menschen sind, und Menschen vergessen. Studien zeigen, dass Fortune-500-Unternehmen jährlich 31,5 Milliarden Dollar durch nie erfasstes Wissen verlieren.

**Unser Ansatz:** Rekall ist eine persönliche Wissensbasis, die auf kognitionswissenschaftlicher Forschung aufbaut. Wir haben studiert, wie das menschliche Gedächtnis wirklich funktioniert — episodisches vs. semantisches Gedächtnis, verteilte Wiederholung, Wissensgraphen — und es auf Entwickler-Workflows angewandt.

**Was es macht:** Erfasse Bugs, Patterns, Entscheidungen, Konfigurationen während du arbeitest. Suche nach Bedeutung, nicht nur Keywords — Rekall verwendet optionale lokale Embeddings (EmbeddingGemma) kombiniert mit Volltextsuche, um relevante Einträge zu finden, auch wenn deine Wörter nicht genau übereinstimmen. Speichert reichen Kontext (Situation, Lösung, was fehlschlug) um ähnliche Probleme später eindeutig zuzuordnen.

**Funktioniert mit deinen Tools:** Rekall stellt einen MCP-Server bereit, der mit den meisten KI-gestützten Entwicklungstools kompatibel ist — Claude Code, Claude Desktop, Cursor, Windsurf, Continue.dev und jedem MCP-Client. Ein Befehl (`rekall mcp`) und deine KI konsultiert dein Wissen vor jedem Fix.

**Was es automatisiert:** Keyword-Extraktion, Konsolidierungs-Scoring, Pattern-Erkennung, Link-Vorschläge, Review-Planung (SM-2 verteilte Wiederholung). Du konzentrierst dich aufs Erfassen — Rekall kümmert sich um den Rest.

```bash
# Installation
uv tool install git+https://github.com/guthubrx/rekall.git

# Erfassen (interaktiver Modus führt dich)
rekall add bug "CORS schlägt auf Safari fehl" --context-interactive

# Suchen (versteht Bedeutung, nicht nur Keywords)
rekall search "Browser blockiert API"

# KI verbinden (ein Befehl, funktioniert mit Claude/Cursor/Windsurf)
rekall mcp
```

---

<br>

## Du hast dieses Problem schon gelöst.

Vor drei Monaten hast du zwei Stunden damit verbracht, einen kryptischen Fehler zu debuggen. Du hast die Lösung gefunden. Du bist weitergezogen.

Heute erscheint derselbe Fehler. Du starrst ihn an. Er kommt dir bekannt vor. Aber wo war diese Lösung nochmal?

Du fängst von vorne an. Noch zwei Stunden verloren.

**Das passiert jedem Entwickler.** Laut Studien verlieren Fortune-500-Unternehmen jährlich 31,5 Milliarden Dollar, weil gelernte Lektionen nie festgehalten werden. Nicht aus Nachlässigkeit — sondern weil wir Menschen sind, und Menschen vergessen.

---

## Was wäre, wenn dein KI-Assistent sich für dich erinnern würde?

Stell dir vor: Du bittest Claude oder Cursor, einen Bug zu beheben. Bevor eine einzige Zeile Code geschrieben wird, durchsucht er deine persönliche Wissensdatenbank:

```
🔍 Durchsuche dein Wissen...

2 relevante Einträge gefunden:

[1] bug: CORS-Fehler auf Safari (85% Übereinstimmung)
    "credentials: include und korrekte Access-Control-Header hinzufügen"
    → Du hast das vor 3 Monaten gelöst

[2] pattern: Cross-Origin-Request-Behandlung (72% Übereinstimmung)
    "Immer auf Safari testen - strengere CORS-Durchsetzung"
    → Pattern aus 4 ähnlichen Bugs extrahiert
```

Dein KI-Assistent hat jetzt Kontext. Er weiß, was vorher funktioniert hat. Er wird das Rad nicht neu erfinden — er baut auf deiner vergangenen Erfahrung auf.

**Das ist Rekall.**

<p align="center">
  <img src="docs/screenshots/demo.gif" alt="Rekall in Aktion" width="700">
</p>

---

## Ein zweites Gehirn, das denkt wie du

Rekall ist nicht nur eine Notiz-App. Es basiert auf der tatsächlichen Funktionsweise des menschlichen Gedächtnisses:

### Dein Wissen, verbunden

Wenn du etwas löst, taucht verwandtes Wissen automatisch auf. Hast du einen Timeout-Bug behoben? Rekall zeigt dir die drei anderen Timeout-Probleme, die du gelöst hast, und das Retry-Pattern, das du daraus extrahiert hast.

```
              ┌──────────────┐
              │ Auth Timeout │
              │   (heute)    │
              └──────┬───────┘
                     │ ähnlich wie...
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ DB #47   │ │ API #52  │ │ Cache #61│
  │(2 Wochen)│ │ (1 Monat)│ │(3 Monate)│
  └────┬─────┘ └────┬─────┘ └──────────┘
       └──────┬─────┘
              ▼
     ┌─────────────────┐
     │ PATTERN: Retry  │
     │ mit Backoff     │
     └─────────────────┘
```

### Ereignisse werden zu Weisheit

Jeder Bug, den du behebst, ist eine **Episode** — ein spezifisches Ereignis mit Kontext. Aber Muster entstehen. Nach dem Beheben von drei ähnlichen Timeout-Bugs hilft dir Rekall, das **Prinzip** zu extrahieren: "Immer Retry mit exponentiellem Backoff für externe APIs hinzufügen."

Episoden sind Rohmaterial. Patterns sind wiederverwendbares Wissen.

### Vergessenes Wissen taucht wieder auf

Rekall verfolgt, was du abrufst und wann. Wissen, das du seit Monaten nicht berührt hast? Es erinnert dich daran, bevor es vollständig verblasst. Denk daran als Spaced Repetition für dein Entwickler-Gehirn.

---

## Wie es in der Praxis funktioniert

### 1. Erfasse Wissen während der Arbeit

Nach dem Lösen von etwas Kniffligem, erfasse es in 10 Sekunden:

```bash
rekall add bug "CORS schlägt auf Safari fehl" --context-interactive
```

Rekall fragt: *Was ist passiert? Was hat es behoben? Welche Schlüsselwörter sollten das auslösen?*

```
> Situation: Safari blockiert Anfragen trotz gesetzter CORS-Header
> Lösung: credentials: 'include' und explizites Allow-Origin hinzufügen
> Schlüsselwörter: cors, safari, cross-origin, fetch, credentials
```

Fertig. Dein zukünftiges Ich wird es dir danken.

### 2. Suche nach Bedeutung, nicht nur Schlüsselwörtern

Erinnerst du dich nicht, ob du es "CORS" oder "Cross-Origin" genannt hast? Egal.

```bash
rekall search "Browser blockiert meine API-Aufrufe"
```

Rekall versteht die Bedeutung. Es findet relevante Einträge, auch wenn deine Wörter nicht genau übereinstimmen.

### 3. Lass deinen KI-Assistenten es nutzen

Verbinde Rekall mit Claude, Cursor oder jeder MCP-kompatiblen KI:

```bash
rekall mcp  # Startet den Server
```

Jetzt konsultiert deine KI dein Wissen vor jeder Korrektur. Sie zitiert deine vergangenen Lösungen. Sie schlägt vor, neue zu speichern. Dein Wissen akkumuliert sich über die Zeit.

---

## Die Oberfläche

### Terminal UI
```bash
rekall  # Startet die visuelle Oberfläche
```

```
┌─ Rekall ────────────────────────────────────────────────┐
│  🔍 Suche: cors safari                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] bug: CORS schlägt auf Safari fehl     85% ██████   │
│      safari, cors, fetch  •  vor 3 Monaten              │
│      "credentials: include hinzufügen..."               │
│                                                         │
│  [2] pattern: Cross-Origin-Behandlung      72% █████    │
│      architektur  •  vor 1 Monat                        │
│      "Safari ist strenger bei CORS"                     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [/] Suchen  [a] Hinzufügen  [Enter] Ansehen  [q] Ende  │
└─────────────────────────────────────────────────────────┘
```

### Kommandozeile
```bash
rekall add bug "Fix: null pointer in auth" -t auth,null
rekall search "Authentifizierungsfehler"
rekall show 01HX7...
rekall link 01HX7 01HY2 --type related
rekall review  # Spaced-Repetition-Sitzung
```

<br>

## Was Rekall für dich tut

> **Philosophie:** Du konzentrierst dich auf das Erfassen deines Wissens. Rekall kümmert sich um alles andere.

### Bei jedem Eintrag, den du hinzufügst

- **Keyword-Extraktion** — Analysiert Titel und Inhalt, schlägt relevante Keywords vor
- **Kontext-Validierung** — Warnt, wenn Situation/Lösung zu vage oder generisch ist
- **Embedding-Generierung** — Erstellt semantische Vektoren für intelligente Suche (wenn aktiviert)
- **Automatische Indexierung** — Der Volltext-Suchindex wird in Echtzeit aktualisiert

### Bei jeder Suche

- **Hybrides Matching** — Kombiniert exakte Wörter (FTS5) + Bedeutung (Embeddings) + Trigger (Keywords)
- **Null Konfiguration** — Funktioniert out of the box, kein Tuning nötig
- **Verknüpfte Einträge** — Zeigt automatisch verwandtes Wissen

### Im Hintergrund (du tust nichts)

- **Zugriffs-Tracking** — Jede Abfrage aktualisiert Häufigkeits- und Aktualitäts-Statistiken
- **Konsolidierungs-Score** — Berechnet, wie "stabil" jede Erinnerung ist (60% Häufigkeit + 40% Frische)
- **Pattern-Erkennung** — Findet Cluster ähnlicher Einträge, schlägt Pattern-Erstellung vor
- **Link-Vorschläge** — Erkennt verwandte Einträge, schlägt Verbindungen vor
- **Review-Planung** — SM-2-Algorithmus plant optimale Wiederholungszeitpunkte (Spaced Repetition)
- **Kontext-Komprimierung** — Speichert ausführlichen Kontext mit 70-85% weniger Größe

### Wenn du `rekall review` ausführst

- **Lädt fällige Einträge** — Basierend auf SM-2-Planung, nicht willkürlichen Daten
- **Passt Schwierigkeit an** — Deine Bewertung (0-5) aktualisiert den Leichtigkeitsfaktor automatisch
- **Plant um** — Berechnet das nächste optimale Review-Datum

---

## Was kannst du erfassen?

| Typ | Für | Beispiel |
|-----|-----|----------|
| `bug` | Gelöste Probleme | "Safari CORS mit credentials" |
| `pattern` | Wiederverwendbare Ansätze | "Retry mit exponentiellem Backoff" |
| `decision` | Warum X statt Y | "PostgreSQL statt MongoDB für dieses Projekt" |
| `pitfall` | Zu vermeidende Fehler | "Niemals SELECT * in Produktion" |
| `config` | Funktionierende Konfiguration | "VS Code Python Debug-Konfiguration" |
| `reference` | Nützliche Docs/Links | "Diese eine StackOverflow-Antwort" |
| `snippet` | Code zum Aufheben | "Generische Debounce-Funktion" |
| `til` | Schnelle Erkenntnisse | "Git rebase -i kann Commits umsortieren" |

---

## 100% lokal. 100% deins.

```
Dein Rechner
     │
     ▼
┌─────────────────────────────────────┐
│  ~/.local/share/rekall/             │
│                                     │
│  Alles bleibt hier.                 │
│  Keine Cloud. Kein Konto.           │
│  Kein Tracking.                     │
│                                     │
└─────────────────────────────────────┘
     │
     ▼
  Nirgendwo anders. Niemals.
```

Dein Wissen gehört dir. Rekall telefoniert nicht nach Hause. Es erfordert kein Konto. Es funktioniert offline. Deine Debug-Historie, deine Architekturentscheidungen, deine hart erarbeitete Weisheit — alles privat, alles lokal.

---

## Erste Schritte

### Installation

```bash
# Mit uv (empfohlen)
uv tool install git+https://github.com/guthubrx/rekall.git

# Mit pipx
pipx install git+https://github.com/guthubrx/rekall.git
```

### Probiere es aus

```bash
# Füge deinen ersten Eintrag hinzu
rekall add bug "Mein erster erfasster Bug" -t test

# Suche danach
rekall search "erster"

# Öffne die visuelle Oberfläche
rekall
```

---

## MCP-Server: Funktioniert mit jedem KI-Assistenten

Rekall stellt deine Wissensbasis über das **Model Context Protocol (MCP)** bereit — der offene Standard zur Verbindung von KI-Assistenten mit externen Tools.

### Ein Befehl, universeller Zugang

```bash
rekall mcp  # Startet den MCP-Server
```

### Kompatibel mit führenden KI-Tools

| Tool | Status | Konfiguration |
|------|--------|---------------|
| **Claude Code** | ✅ Nativ | Automatisch erkannt |
| **Claude Desktop** | ✅ Nativ | Zu `claude_desktop_config.json` hinzufügen |
| **Cursor** | ✅ Unterstützt | MCP-Einstellungen |
| **Windsurf** | ✅ Unterstützt | MCP-Einstellungen |
| **Continue.dev** | ✅ Unterstützt | MCP-Konfiguration |
| **Jeder MCP-Client** | ✅ Kompatibel | Standard-MCP-Protokoll |

### Konfigurationsbeispiel (Claude Desktop)

Füge zu deiner `claude_desktop_config.json` hinzu:

```json
{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp"]
    }
  }
}
```

### Was deine KI tun kann

Einmal verbunden, kann dein KI-Assistent:

- **Suchen** in deiner Wissensbasis vor dem Antworten
- **Zitieren** deiner vergangenen Lösungen in seinen Antworten
- **Vorschlagen** neues Wissen nach dem Lösen von Problemen zu erfassen
- **Verknüpfen** verwandter Einträge automatisch
- **Aufzeigen** von Patterns in deiner Debug-Historie

Dein Wissen akkumuliert sich automatisch — je mehr du es nutzt, desto intelligenter wird es.

---

## Integration mit Speckit

[Speckit](https://github.com/YOUR_USERNAME/speckit) ist ein spezifikationsgetriebenes Entwicklungs-Toolkit. Kombiniert mit Rekall entsteht ein leistungsstarker Workflow, bei dem deine Spezifikationen deine Wissensbasis füttern.

### Warum integrieren?

- **Specs werden zu durchsuchbarem Wissen**: Entscheidungen während des Spec-Schreibens werden erfasst
- **Patterns entstehen**: Gemeinsame Architekturentscheidungen tauchen projektübergreifend auf
- **Kontext bleibt erhalten**: Das "Warum" hinter Specs geht nie verloren

### Installation

1. Installiere beide Tools:
```bash
uv tool install git+https://github.com/guthubrx/rekall.git
uv tool install git+https://github.com/YOUR_USERNAME/speckit.git
```

2. Konfiguriere Speckit für Rekall (in deiner `.speckit/config.yaml`):
```yaml
integrations:
  rekall:
    enabled: true
    auto_capture: true  # Automatische Erfassung von Entscheidungen
    types:
      - decision
      - pattern
      - pitfall
```

3. Während der Spec-Arbeit wird Speckit:
   - Rekall nach relevanten vergangenen Entscheidungen befragen
   - Vorschlagen, neue Architekturentscheidungen zu erfassen
   - Specs mit verwandten Wissenseinträgen verknüpfen

### Beispiel-Workflow

```bash
# Beginne eine Feature zu spezifizieren
speckit specify "Benutzer-Authentifizierungssystem"

# Speckit fragt Rekall: "Hast du schon Auth-Entscheidungen getroffen?"
# → Zeigt deine vergangene OAuth vs JWT Entscheidung aus einem anderen Projekt

# Nach Abschluss der Spec
speckit plan

# Rekall erfasst: decision "JWT für stateless Auth in Microservices"
```

<br>

<details>
<summary><h2>Unter der Haube: Wie die Suche funktioniert</h2></summary>

> **TL;DR:** Hybridsuche kombiniert FTS5 (50%) + semantische Embeddings (30%) + Keywords (20%). Optionales lokales Modell, keine API-Schlüssel.

Rekall macht nicht nur Keyword-Matching. Es versteht, was du meinst.

### Das Problem mit einfacher Suche

Du hast einen Bug erfasst: "CORS-Fehler auf Safari." Später suchst du nach "Browser blockiert meine API-Aufrufe." Eine einfache Keyword-Suche findet nichts — die Wörter stimmen nicht überein.

### Hybridsuche: vollständig UND schnell

Rekall kombiniert drei Suchstrategien:

```
┌──────────────────────────────────────────────────────────────┐
│                     DEINE ANFRAGE                            │
│              "Browser blockiert API-Aufrufe"                 │
└──────────────────────────────────┬───────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
    ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
    │   FTS5      │        │ Semantisch  │        │ Schlüssel-  │
    │  (50%)      │        │   (30%)     │        │ wörter (20%)│
    │             │        │             │        │             │
    │ Exakte      │        │ Bedeutung   │        │ Strukturierte│
    │ Übereinstim.│        │ via Embed.  │        │ Trigger     │
    └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
           │                      │                      │
           └───────────────────────┼───────────────────────┘
                                   ▼
                        ┌─────────────────┐
                        │  FINAL SCORE    │
                        │  85% match      │
                        └─────────────────┘
```

- **Volltextsuche (50%)**: SQLite FTS5 findet exakte und partielle Übereinstimmungen
- **Semantische Suche (30%)**: Embeddings finden konzeptuell ähnlichen Inhalt — "Browser" passt zu "Safari", "blockiert" passt zu "CORS-Fehler"
- **Keyword-Index (20%)**: Deine strukturierten Kontext-Keywords liefern explizite Trigger

### Lokale Embeddings: Optional aber leistungsstark

Semantische Suche ist **optional**. Rekall funktioniert perfekt mit FTS5-Volltextsuche allein — kein Modell erforderlich.

Aber wenn du semantisches Verständnis möchtest, verwendet Rekall **EmbeddingGemma** (308M Parameter), ein State-of-the-Art Embedding-Modell, das vollständig auf deinem Rechner läuft:

- **100% lokal**: Keine Daten verlassen deinen Computer, keine API-Schlüssel, keine Cloud
- **Mehrsprachig**: Funktioniert in über 100 Sprachen
- **Schnell**: ~500ms pro Embedding auf einem Standard-Laptop-CPU
- **Kompakt**: ~200MB RAM mit int8-Quantisierung

```bash
# Nur-FTS-Modus (Standard, kein Modell nötig)
rekall search "CORS Fehler"

# Semantische Suche aktivieren (lädt Modell bei erster Verwendung)
rekall config set embeddings.enabled true
```

### Doppeltes Embedding: Kontext zählt

Wenn du Wissen erfasst, speichert Rekall zwei Embeddings:

1. **Summary-Embedding**: Titel + Inhalt + Tags — für fokussierte Suchen
2. **Kontext-Embedding**: Die vollständige Situation/Lösung — für explorative Suchen

Das löst ein fundamentales Problem beim Retrieval: Zusammenfassungen verlieren Kontext. Wenn du nach "Stack Trace Safari" suchst, wird das Summary "Fix CORS" nicht passen — aber der vollständige Kontext, den du erfasst hast (der den Stack Trace erwähnt), schon.

### Strukturierter Kontext: Eindeutige Zuordnung

Du hast 5 verschiedene "Timeout"-Bugs behoben. Wie findest du später den richtigen? Keywords allein helfen nicht — alle sind mit "Timeout" getaggt.

Rekall erfasst **strukturierten Kontext** für jeden Eintrag:

```
┌─────────────────────────────────────────────────────────────┐
│  situation        │  "API-Aufrufe timeout nach Deploy"      │
│  solution         │  "Connection-Pool-Größe erhöht"         │
│  what_failed      │  "Retry-Logik hat nicht geholfen"       │
│  trigger_keywords │  ["timeout", "deploy", "connection pool"]│
│  error_messages   │  "ETIMEDOUT nach 30s"                   │
│  files_modified   │  ["config/database.yml"]                │
└─────────────────────────────────────────────────────────────┘
```

Bei der Suche nutzt Rekall diesen Kontext zur eindeutigen Zuordnung:

- **"Timeout nach Deploy"** → Findet den Connection-Pool-Bug (Situations-Match)
- **"ETIMEDOUT"** → Findet Einträge mit genau dieser Fehlermeldung
- **"Retry hat nicht funktioniert"** → Findet Einträge, wo Retry versucht wurde und fehlschlug

Das `--context-interactive` Flag führt dich durch die Erfassung:

```bash
rekall add bug "Timeout in Prod" --context-interactive
# Rekall fragt: Was ist passiert? Was hat es behoben? Was hat nicht funktioniert?
# Deine Antworten werden zu durchsuchbarem Disambiguierungs-Kontext
```

### Komprimierte Speicherung

Kontext kann ausführlich sein. Rekall komprimiert strukturierten Kontext mit zlib und pflegt einen separaten Keyword-Index für schnelle Suche:

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTRY-SPEICHERUNG                        │
├─────────────────────────────────────────────────────────────┤
│  context_blob     │  Komprimiertes JSON (zlib) │  ~70% kleiner│
│  context_keywords │  Indexierte Tabelle        │  O(1) Lookup │
│  emb_summary      │  768-dim Vektor            │  Semantisch  │
│  emb_context      │  768-dim Vektor            │  Semantisch  │
└─────────────────────────────────────────────────────────────┘
```

Das Ergebnis: **vollständige** Suche (nichts wird übersehen) mit **Geschwindigkeit** (Sub-Sekunden-Antworten bei tausenden Einträgen).

</details>

<br>

<details>
<summary><h2>Basiert auf Wissenschaft</h2></summary>

Rekall ist keine Sammlung von Vermutungen — es basiert auf peer-reviewed Forschung in Kognitionswissenschaft und Information Retrieval. Hier ist, was wir gelernt haben und wie wir es anwenden:

### Wissensgraphen: +20% Abrufgenauigkeit

**Forschung**: Studien zu Wissensgraphen in RAG-Systemen zeigen, dass verbundene Information leichter abzurufen ist als isolierte Fakten.

**Anwendung**: Rekall lässt dich Einträge mit typisierten Beziehungen verknüpfen (`related`, `supersedes`, `derived_from`, `contradicts`). Bei der Suche boosten verknüpfte Einträge gegenseitig ihre Scores. Wenn du einen neuen Timeout-Bug behebst, zeigt Rekall dir die drei anderen Timeout-Probleme, die du gelöst hast — und das Pattern, das du daraus extrahiert hast.

### Episodisches vs. semantisches Gedächtnis: Wie dein Gehirn organisiert

**Forschung**: Tulving (1972) stellte fest, dass das menschliche Gedächtnis zwei unterschiedliche Systeme hat — episodisch (spezifische Ereignisse: "Ich habe diesen Bug am Dienstag behoben") und semantisch (allgemeines Wissen: "Immer Retry für externe APIs hinzufügen").

**Anwendung**: Rekall unterscheidet `episodic`-Einträge (was passiert ist) von `semantic`-Einträgen (was du gelernt hast). Der `generalize`-Befehl hilft dir, Patterns aus Episoden zu extrahieren. Das spiegelt wider, wie sich Expertise entwickelt: Du sammelst Erfahrungen, dann destillierst du sie zu Prinzipien.

### Verteilte Wiederholung: +6-9% Retention

**Forschung**: Der Spacing-Effekt (Ebbinghaus, 1885) und der SM-2-Algorithmus zeigen, dass Wiederholung in wachsenden Intervallen die Retention dramatisch verbessert.

**Anwendung**: Rekall verfolgt, wann du auf jeden Eintrag zugreifst, und berechnet einen Konsolidierungs-Score. Der `review`-Befehl zeigt Wissen, das kurz vor dem Verblassen steht. Der `stale`-Befehl findet Einträge, die du seit Monaten nicht berührt hast — bevor sie vergessen werden.

### Kontextuelles Retrieval: -67% Suchfehler

**Forschung**: Anthropics Contextual Retrieval Paper zeigte, dass traditionelle RAG-Systeme scheitern, weil sie beim Encoding den Kontext entfernen. Das Hinzufügen von 50-100 Token Kontext reduziert Retrieval-Fehler um 67%.

**Anwendung**: Rekalls strukturierter Kontext (Situation, Lösung, Keywords) bewahrt das "Warum" neben dem "Was". Die Doppel-Embedding-Strategie stellt sicher, dass sowohl fokussierte Anfragen als auch explorative Suchen relevante Einträge finden.

### Progressive Offenlegung: -98% Token-Nutzung

**Forschung**: Anthropics Engineering-Blog dokumentierte, dass kompakte Zusammenfassungen statt vollständigem Inhalt die Token-Nutzung um 98% reduzieren, während der Aufgabenerfolg erhalten bleibt.

**Anwendung**: Rekalls MCP-Server gibt kompakte Ergebnisse zurück (ID, Titel, Score, Snippet) mit einem Hinweis zum Abrufen vollständiger Details. Dein KI-Assistent bekommt, was er braucht, ohne sein Kontextfenster zu sprengen.

### Konsolidierungs-Score: Vergessen modellieren

**Forschung**: Die Vergessenskurve zeigt, dass Erinnerungen ohne Verstärkung exponentiell verfallen. Sowohl Zugriffshäufigkeit als auch Aktualität zählen.

**Anwendung**: Rekall berechnet einen Konsolidierungs-Score für jeden Eintrag:

```python
score = 0.6 × frequency_factor + 0.4 × freshness_factor
```

Einträge, auf die du oft und kürzlich zugreifst, haben hohe Konsolidierung (stabiles Wissen). Einträge, die du seit Monaten nicht berührt hast, haben niedrige Konsolidierung (Gefahr des Vergessens).

---

**Wir haben die Paper gelesen, damit du es nicht musst. Dann haben wir ein Tool gebaut, das sie anwendet.**

</details>

<br>

---

## Mehr erfahren

| Ressource | Beschreibung |
|-----------|--------------|
| `rekall --help` | Vollständige Befehlsreferenz |
| `rekall version` | Version und Datenbank-Info |
| `rekall changelog` | Was ist neu |
| [CHANGELOG.md](CHANGELOG.md) | Detaillierter Versionsverlauf |

---

## Anforderungen

- Python 3.9+
- Das ist alles. Keine Cloud-Dienste. Keine API-Schlüssel. Keine Konten.

---

## Lizenz

MIT — Mach damit, was du willst.

---

<p align="center">
<strong>Hör auf, Wissen zu verlieren. Fang an, dich zu erinnern.</strong>
<br><br>

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
</p>
