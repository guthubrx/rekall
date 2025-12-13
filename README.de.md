<div align="center">

<!-- LOGO: Auskommentieren wenn logo.png bereit ist
<img src="docs/images/logo.png" alt="Rekall Logo" width="120">
-->

# Rekall

**Dein Entwicklerwissen, sofort abrufbar.**

<p>
  <img src="https://img.shields.io/badge/100%25-Lokal-blue?style=flat-square" alt="100% Lokal">
  <img src="https://img.shields.io/badge/Keine_API_Keys-green?style=flat-square" alt="Keine API Keys">
  <img src="https://img.shields.io/badge/MCP-Kompatibel-purple?style=flat-square" alt="MCP Kompatibel">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=flat-square" alt="Python 3.10+">
</p>

*"Get your ass to Mars. Quaid... crush those bugs"*

[Dokumentation](#inhalt) · [Installation](#erste-schritte) · [MCP-Integration](#mcp-server-funktioniert-mit-jedem-ki-assistenten)

**Übersetzungen:** [🇬🇧 English](README.md) | [🇫🇷 Français](README.fr.md) | [🇪🇸 Español](README.es.md) | [🇨🇳 中文](README.zh-CN.md)

</div>

---

## Inhalt

- [TL;DR](#tldr)
- [Das Problem](#du-hast-dieses-problem-schon-mal-gelöst)
- [Die Lösung](#was-wäre-wenn-dein-ki-assistent-sich-für-dich-erinnern-würde)
- [Wie es in der Praxis funktioniert](#wie-es-in-der-praxis-funktioniert)
- [Das Interface](#das-interface)
- [Was es automatisiert](#was-rekall-für-dich-tut)
- [Eintragstypen](#was-kannst-du-erfassen)
- [Quellen](#verfolge-deine-quellen)
- [Datenschutz](#100-lokal-100-deins)
- [Erste Schritte](#erste-schritte)
- [MCP Server](#mcp-server-funktioniert-mit-jedem-ki-assistenten)
- [Speckit-Integration](#integration-mit-speckit)
- [Unter der Haube](#unter-der-haube-wie-die-suche-funktioniert) *(technisch)*
- [Basiert auf Wissenschaft](#basiert-auf-wissenschaft) *(Forschung)*

---

### TL;DR

**Das Problem:** Jeder Entwickler hat schon mal denselben Bug zweimal gelöst. Nicht weil er unachtsam war — sondern weil Menschen vergessen. Forschung zeigt, dass Fortune-500-Unternehmen jährlich 31,5 Milliarden Dollar verlieren durch Wissen, das nie erfasst wurde.

**Unser Ansatz:** Rekall ist eine persönliche Wissensdatenbank (personal knowledge base), die auf kognitionswissenschaftlicher Forschung basiert. Wir haben untersucht, wie menschliches Gedächtnis tatsächlich funktioniert — episodisches vs. semantisches Gedächtnis (episodic vs semantic memory), verteilte Wiederholung (spaced repetition), Wissensgraphen (knowledge graphs) — und es auf Entwickler-Workflows angewendet.

**Was es tut:** Erfasse Bugs, Patterns, Entscheidungen, Configs während du arbeitest. Suche nach Bedeutung, nicht nur Keywords — Rekall nutzt optionale lokale Embeddings (all-MiniLM-L6-v2) kombiniert mit Volltextsuche (full-text search), um relevante Einträge zu finden, selbst wenn deine Wörter nicht exakt übereinstimmen. Speichere reichhaltigen Kontext (Situation, Lösung, was nicht funktioniert hat), um ähnliche Probleme später zu unterscheiden.

**Funktioniert mit deinen Tools:** Rekall stellt einen MCP-Server (Model Context Protocol) bereit, der mit den meisten KI-gestützten Entwicklungstools kompatibel ist — Claude Code, Claude Desktop, Cursor, Windsurf, Continue.dev und jedem MCP-kompatiblen Client. Ein Befehl (`rekall mcp`) und deine KI konsultiert dein Wissen vor jedem Fix.

**Was es automatisiert:** Keyword-Extraktion, Konsolidierungs-Scoring (consolidation scoring), Pattern-Erkennung, Link-Vorschläge, Review-Planung (SM-2 spaced repetition). Du konzentrierst dich aufs Erfassen — Rekall kümmert sich um den Rest.

```bash
# Installation
uv tool install git+https://github.com/guthubrx/rekall.git

# Erfassen (interaktiver Modus führt dich durch den Prozess)
rekall add bug "CORS funktioniert nicht in Safari" --context-interactive

# Suchen (versteht Bedeutung, nicht nur Keywords)
rekall search "Browser blockiert API"

# Mit KI verbinden (ein Befehl, funktioniert mit Claude/Cursor/Windsurf)
rekall mcp
```

---

<br>

## Du hast dieses Problem schon mal gelöst.

Vor drei Monaten hast du zwei Stunden mit dem Debugging eines kryptischen Fehlers verbracht. Du hast den Fix gefunden. Du bist weitergezogen.

Heute taucht derselbe Fehler wieder auf. Du starrst ihn an. Er sieht bekannt aus. Aber wo war nochmal die Lösung?

Du fängst von vorne an. Weitere zwei Stunden weg.

**Das passiert jedem Entwickler.** Laut Forschung verlieren Fortune-500-Unternehmen jährlich 31,5 Milliarden Dollar, weil gelernte Lektionen nie erfasst werden. Nicht weil Menschen unachtsam sind — sondern weil wir Menschen sind, und Menschen vergessen.

<br>

## Was wäre, wenn dein KI-Assistent sich für dich erinnern würde?

Stell dir vor: Du bittest Claude oder Cursor, einen Bug zu fixen. Bevor es eine einzige Zeile Code schreibt, prüft es deine persönliche Wissensdatenbank:

```
🔍 Durchsuche dein Wissen...

2 relevante Einträge gefunden:

[1] bug: CORS-Fehler in Safari (85% Übereinstimmung)
    "Füge credentials: include und korrekte Access-Control-Header hinzu"
    → Du hast das vor 3 Monaten gelöst

[2] pattern: Cross-origin Request-Handling (72% Übereinstimmung)
    "Teste immer in Safari - es hat strengere CORS-Regeln"
    → Pattern extrahiert aus 4 ähnlichen Bugs
```

Dein KI-Assistent hat jetzt Kontext. Er weiß, was vorher funktioniert hat. Er wird das Rad nicht neu erfinden — er baut auf deiner früheren Erfahrung auf.

**Das ist Rekall.**

<p align="center">
  <img src="docs/screenshots/demo.gif" alt="Rekall in Aktion" width="700">
</p>

<!--
Screenshots Platzhalter - füge deine Bilder zu docs/screenshots/ hinzu
Optionen:
- demo.gif: Animiertes GIF, das den Workflow zeigt (empfohlen)
- tui.png: Terminal-UI Screenshot
- search.png: Suchergebnisse
- mcp.png: MCP-Integration mit Claude/Cursor
-->

<br>

## Ein zweites Gehirn, das denkt wie du

> **Kernidee:** Rekall basiert darauf, wie menschliches Gedächtnis tatsächlich funktioniert — verwandtes Wissen verbinden, Patterns aus Episoden extrahieren und vergessene Informationen wieder an die Oberfläche bringen, bevor sie verblassen.

Rekall ist nicht nur eine Notiz-App. Es basiert darauf, wie menschliches Gedächtnis tatsächlich funktioniert:

### Dein Wissen, verbunden

Wenn du etwas löst, taucht automatisch verwandtes Wissen auf. Einen Timeout-Bug gefixt? Rekall zeigt dir die drei anderen Timeout-Probleme, die du gelöst hast, und das Retry-Pattern, das du daraus extrahiert hast.

```
              ┌──────────────┐
              │ Auth Timeout │
              │   (heute)    │
              └──────┬───────┘
                     │ ähnlich zu...
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │ DB #47   │ │ API #52  │ │ Cache #61│
  │(2 Wochen)│ │(1 Monat) │ │(3 Monate)│
  └────┬─────┘ └────┬─────┘ └──────────┘
       └──────┬─────┘
              ▼
     ┌─────────────────┐
     │ PATTERN: Retry  │
     │ mit Backoff     │
     └─────────────────┘
```

### Ereignisse werden zu Weisheit

Jeder Bug, den du fixst, ist eine **Episode** — ein spezifisches Ereignis mit Kontext. Aber Patterns entstehen. Nachdem du drei ähnliche Timeout-Bugs gefixt hast, hilft dir Rekall, das **Prinzip** zu extrahieren: "Füge immer Retry mit exponentiellem Backoff für externe APIs hinzu."

Episoden sind Rohmaterial. Patterns sind wiederverwendbares Wissen.

<br>

### Vergessenes Wissen taucht wieder auf

Rekall trackt, was du wann aufrufst. Wissen, das du seit Monaten nicht berührt hast? Es erinnert dich daran, bevor es komplett verblasst. Denk daran wie an verteilte Wiederholung (spaced repetition) für dein Entwickler-Gehirn.

---

## Wie es in der Praxis funktioniert

### 1. Erfasse Wissen während du arbeitest

Nachdem du etwas Kniffliges gelöst hast, erfasse es in 10 Sekunden:

```bash
rekall add bug "CORS funktioniert nicht in Safari" --context-interactive
```

Rekall fragt: *Was ist passiert? Was hat es gefixt? Welche Keywords sollen das triggern?*

```
> Situation: Safari blockiert Anfragen, obwohl CORS-Header gesetzt sind
> Lösung: Füge credentials: 'include' und explizites Allow-Origin hinzu
> Keywords: cors, safari, cross-origin, fetch, credentials
```

Fertig. Dein zukünftiges Ich wird dir danken.

### 2. Suche nach Bedeutung, nicht nur Keywords

Kannst du dich nicht erinnern, ob du es "CORS" oder "cross-origin" genannt hast? Egal.

```bash
rekall search "Browser blockiert meine API-Aufrufe"
```

Rekall versteht Bedeutung. Es findet relevante Einträge, selbst wenn deine Wörter nicht exakt übereinstimmen.

### 3. Lass deinen KI-Assistenten es nutzen

Verbinde Rekall mit Claude, Cursor oder jeder KI, die MCP unterstützt:

```bash
rekall mcp  # Server starten
```

Jetzt konsultiert deine KI dein Wissen vor jedem Fix. Sie zitiert deine früheren Lösungen. Sie schlägt vor, neue zu speichern. Dein Wissen wächst im Laufe der Zeit.

---

## Das Interface

> **Warum Terminal-First?** Rekalls Interface ist eine vollwertige Terminal UI (TUI) — und das ist Absicht. Moderne Entwicklung findet überall statt: auf deinem Laptop, auf Remote-Servern, in Containern, über SSH. Ein Terminal-Interface bedeutet, dass du von überall auf deine Wissensdatenbank zugreifen kannst, ohne einen Browser zu öffnen oder Ports weiterzuleiten.
>
> Ob du um 2 Uhr nachts einen Produktionsserver über SSH debuggst, in einer headless VM arbeitest, oder einfach die Geschwindigkeit und Tastatur-Effizienz von Terminal-Apps bevorzugst — Rekall ist direkt bei dir. Keine GUI-Abhängigkeiten. Kein Kontextwechsel. Nur dein Wissen, einen Befehl entfernt.
>
> *Ein Web-Interface steht auf der Roadmap für Teams, die Browser-basierte Workflows bevorzugen.*

### Terminal UI
```bash
rekall  # Startet das visuelle Interface
```

```
┌─ Rekall ────────────────────────────────────────────────┐
│  🔍 Suche: cors safari                                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  [1] bug: CORS funktioniert nicht in Safari 85% ██████  │
│      safari, cors, fetch  •  vor 3 Monaten              │
│      "Füge credentials: include hinzu..."               │
│                                                         │
│  [2] pattern: Cross-origin Handling         72% █████   │
│      architecture  •  vor 1 Monat                       │
│      "Safari hat strengere CORS-Regeln"                 │
│                                                         │
│  [3] reference: MDN CORS-Guide              68% ████    │
│      docs, mdn  •  vor 6 Monaten                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  [/] Suche  [a] Hinzufügen  [Enter] Ansehen  [q] Beenden│
└─────────────────────────────────────────────────────────┘
```

### Kommandozeile
```bash
rekall add bug "Fix: null pointer in auth" -t auth,null
rekall search "authentication error"
rekall show 01HX7...
rekall link 01HX7 01HY2 --type related
rekall review  # Spaced-Repetition-Session
```

<br>

## Was Rekall für dich tut

> **Philosophie:** Du konzentrierst dich aufs Erfassen von Wissen. Rekall kümmert sich um alles andere.

### Bei jedem Eintrag, den du hinzufügst

- **Keyword-Extraktion** — Analysiert deinen Titel und Inhalt, schlägt relevante Keywords vor
- **Kontext-Validierung** — Warnt, wenn Situation/Lösung zu vage oder generisch ist
- **Embedding-Generierung** — Erstellt semantische Vektoren für intelligente Suche (wenn aktiviert)
- **Automatisches Indexing** — Volltextsuche-Index wird in Echtzeit aktualisiert

### Bei jeder Suche

- **Hybrid-Matching** — Kombiniert exakte Wörter (FTS5) + Bedeutung (embeddings) + Trigger (keywords)
- **Keine Konfiguration** — Funktioniert out of the box, kein Tuning nötig
- **Verwandte Einträge** — Zeigt verknüpftes Wissen automatisch

### Im Hintergrund (du tust nichts)

- **Access-Tracking** — Jede Ansicht aktualisiert Häufigkeits- und Aktualitäts-Statistiken
- **Konsolidierungs-Scoring** — Berechnet, wie "stabil" jede Erinnerung ist (60% Häufigkeit + 40% Frische)
- **Pattern-Erkennung** — Findet Cluster ähnlicher Einträge, schlägt Erstellung eines Patterns vor
- **Link-Vorschläge** — Erkennt verwandte Einträge, schlägt Verbindungen vor
- **Review-Planung** — SM-2-Algorithmus plant optimale Review-Zeiten (spaced repetition)
- **Kontext-Kompression** — Speichert ausführlichen Kontext 70-85% kleiner

### Wenn du `rekall review` ausführst

- **Lädt fällige Einträge** — Basierend auf SM-2-Planung, nicht auf willkürlichen Daten
- **Passt Schwierigkeit an** — Deine Bewertung (0-5) aktualisiert den Ease-Factor automatisch
- **Plant neu** — Berechnet das nächste optimale Review-Datum

---

## Was kannst du erfassen?

| Typ | Für | Beispiel |
|------|-----|---------|
| `bug` | Probleme, die du gelöst hast | "Safari CORS mit credentials" |
| `pattern` | Wiederverwendbare Ansätze | "Retry mit exponentiellem Backoff" |
| `decision` | Warum du X statt Y gewählt hast | "PostgreSQL statt MongoDB für dieses Projekt" |
| `pitfall` | Fehler, die zu vermeiden sind | "Nutze nie SELECT * in Produktion" |
| `config` | Setup, das funktioniert | "VS Code Python Debugging Config" |
| `reference` | Nützliche Docs/Links | "Die eine StackOverflow-Antwort" |
| `snippet` | Code, der es wert ist, behalten zu werden | "Generische Debounce-Funktion" |
| `til` | Schnelle Learnings | "Git rebase -i kann Commits umsortieren" |

---

## Verfolge deine Quellen

> **Philosophie:** Jedes Wissen kam von irgendwoher. Rekall hilft dir zu verfolgen, *woher* — um Zuverlässigkeit zu bewerten, Originalquellen erneut zu besuchen und zu sehen, welche Quellen für dich am wertvollsten sind.

### Verknüpfe Einträge mit ihren Quellen

Wenn du Wissen erfasst, kannst du Quellen anhängen:

```bash
# Füge einen Bug mit einer URL-Quelle hinzu
rekall add bug "Safari CORS fix" -t cors,safari
# Dann verknüpfe die Quell-URL
rekall source link 01HX7... --url "https://stackoverflow.com/q/12345"

# Oder nutze das TUI: öffne Eintrag → Quelle hinzufügen
rekall
```

### Drei Quellentypen

| Typ | Für | Beispiel |
|-----|-----|----------|
| `url` | Webseiten, Dokumentation | Stack Overflow, MDN, Blog-Posts |
| `theme` | Wiederkehrende Themen oder Mentoren | "Code Reviews mit Alice", "Architektur-Meetings" |
| `file` | Lokale Dokumente | PDFs, interne Docs, Notizen |

### Zuverlässigkeitsbewertungen (Admiralty-System)

Nicht alle Quellen sind gleich vertrauenswürdig. Rekall nutzt ein vereinfachtes **Admiralty-System**:

| Bewertung | Bedeutung | Beispiele |
|-----------|-----------|-----------|
| **A** | Sehr zuverlässig, autoritativ | Offizielle Docs, peer-reviewed, bekannte Experten |
| **B** | Generell zuverlässig | Renommierte Blogs, akzeptierte SO-Antworten |
| **C** | Fragwürdig oder unbestätigt | Zufällige Forum-Posts, ungetestete Vorschläge |

### Persönlicher Score: Was *für dich* zählt

Jede Quelle bekommt einen **persönlichen Score** (0-100) basierend auf:

```
Score = Nutzung × Aktualität × Zuverlässigkeit

- Nutzung: Wie oft du diese Quelle zitierst
- Aktualität: Wann du sie zuletzt genutzt hast (verfällt mit der Zeit)
- Zuverlässigkeit: A=1.0, B=0.8, C=0.6
```

Quellen, die du häufig und kürzlich nutzt, ranken höher — unabhängig davon, wie "autoritativ" sie global sind. Deine persönliche Erfahrung zählt.

### Backlinks: Siehe alle Einträge einer Quelle

Klicke auf eine beliebige Quelle, um alle Einträge zu sehen, die sie referenzieren:

```
┌─ Quelle: stackoverflow.com/questions/* ─────────────────┐
│  Zuverlässigkeit: B  │  Score: 85  │  Genutzt: 12 mal   │
├─────────────────────────────────────────────────────────┤
│  Einträge, die diese Quelle zitieren:                   │
│                                                         │
│  [1] bug: CORS funktioniert nicht in Safari             │
│  [2] bug: Fetch-Timeout bei langsamen Netzwerken        │
│  [3] pattern: Fehlerbehandlung für API-Aufrufe          │
└─────────────────────────────────────────────────────────┘
```

### Link-Rot-Erkennung

Web-Quellen können offline gehen. Rekall prüft regelmäßig URL-Quellen und markiert unzugängliche:

```bash
rekall sources --verify  # Alle Quellen prüfen
rekall sources --status inaccessible  # Defekte Links auflisten
```

Das Quellen-Dashboard im TUI zeigt:
- **Top-Quellen** nach persönlichem Score
- **Aufsteigende Quellen** (kürzlich mehrfach zitiert)
- **Ruhende Quellen** (nicht genutzt seit 6+ Monaten)
- **Unzugängliche Quellen** (Link-Rot erkannt)

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
│  Keine Cloud. Kein Account.         │
│  Kein Tracking.                     │
│                                     │
└─────────────────────────────────────┘
     │
     ▼
  Nirgendwo sonst. Niemals.
```

Dein Wissen gehört dir. Rekall telefoniert nicht nach Hause. Es benötigt keinen Account. Es funktioniert offline. Deine Debugging-History, deine Architektur-Entscheidungen, deine hart erkämpfte Weisheit — alles privat, alles lokal.

---

## Erste Schritte

### Installation

```bash
# Mit uv (empfohlen)
uv tool install git+https://github.com/guthubrx/rekall.git

# Mit pipx
pipx install git+https://github.com/guthubrx/rekall.git
```

### Ausprobieren

```bash
# Füge deinen ersten Eintrag hinzu
rekall add bug "Mein erster erfasster Bug" -t test

# Suche danach
rekall search "erster"

# Öffne das visuelle Interface
rekall
```

---

## MCP Server: Funktioniert mit jedem KI-Assistenten

Rekall stellt deine Wissensdatenbank über das **Model Context Protocol (MCP)** bereit — der offene Standard zum Verbinden von KI-Assistenten mit externen Tools.

### Ein Befehl, universeller Zugriff

```bash
rekall mcp  # MCP-Server starten
```

### Kompatibel mit wichtigen KI-Tools

| Tool | Status | Konfiguration |
|------|--------|---------------|
| **Claude Code** | ✅ Nativ | Auto-erkannt |
| **Claude Desktop** | ✅ Nativ | Zu `claude_desktop_config.json` hinzufügen |
| **Cursor** | ✅ Unterstützt | MCP-Einstellungen |
| **Windsurf** | ✅ Unterstützt | MCP-Einstellungen |
| **Continue.dev** | ✅ Unterstützt | MCP-Konfiguration |
| **Jeder MCP-Client** | ✅ Kompatibel | Standard-MCP-Protokoll |

### Konfigurations-Beispiel (Claude Desktop)

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

Sobald verbunden, kann dein KI-Assistent:

- **Durchsuchen** — Deine Wissensdatenbank durchsuchen, bevor er antwortet
- **Zitieren** — Deine früheren Lösungen in seinen Antworten zitieren
- **Vorschlagen** — Vorschlagen, neues Wissen nach dem Lösen von Problemen zu erfassen
- **Verknüpfen** — Automatisch verwandte Einträge verlinken
- **Aufdecken** — Patterns in deiner Debugging-History aufdecken

Dein Wissen wächst automatisch — je mehr du es nutzt, desto schlauer wird es.

---

## Integration mit Speckit

[Speckit](https://github.com/YOUR_USERNAME/speckit) ist ein spezifikationsgesteuertes Entwicklungs-Toolkit (specification-driven development toolkit). In Kombination mit Rekall entsteht ein kraftvoller Workflow, bei dem deine Spezifikationen deine Wissensdatenbank füttern.

### Warum integrieren?

- **Specs werden zu durchsuchbarem Wissen**: Entscheidungen, die während des Spec-Schreibens getroffen wurden, werden erfasst
- **Patterns entstehen**: Häufige Architektur-Entscheidungen tauchen projektübergreifend auf
- **Kontext bleibt erhalten**: Das "Warum" hinter Specs geht nie verloren

### Setup

1. Installiere beide Tools:
```bash
uv tool install git+https://github.com/guthubrx/rekall.git
uv tool install git+https://github.com/YOUR_USERNAME/speckit.git
```

2. Konfiguriere Speckit zur Nutzung von Rekall (in deiner `.speckit/config.yaml`):
```yaml
integrations:
  rekall:
    enabled: true
    auto_capture: true  # Entscheidungen automatisch erfassen
    types:
      - decision
      - pattern
      - pitfall
```

3. Während der Spec-Arbeit wird Speckit:
   - Rekall nach relevanten früheren Entscheidungen abfragen
   - Vorschlagen, neue Architektur-Entscheidungen zu erfassen
   - Specs mit verwandten Wissenseinträgen verknüpfen

### Beispiel-Workflow

```bash
# Spezifiziere ein Feature
speckit specify "User-Authentifizierungssystem"

# Speckit fragt Rekall: "Hast du vorher Auth-Entscheidungen getroffen?"
# → Zeigt deine frühere OAuth vs JWT Entscheidung aus einem anderen Projekt

# Nach Finalisierung der Spec
speckit plan

# Rekall erfasst: decision "JWT für stateless Auth in Microservices"
```

<br>

<details>
<summary><h2>Unter der Haube: Wie die Suche funktioniert</h2></summary>

> **TL;DR:** Hybrid-Suche kombiniert FTS5 (50%) + semantische Embeddings (30%) + Keywords (20%). Optionales lokales Modell, keine API-Keys.

Rekall macht nicht nur Keyword-Matching. Es versteht, was du meinst.

### Das Problem mit einfacher Suche

Du hast einen Bug über "CORS-Fehler in Safari" erfasst. Später suchst du nach "Browser blockiert API-Aufrufe". Eine einfache Keyword-Suche findet nichts — die Wörter stimmen nicht überein.

### Hybrid-Suche: Erschöpfend UND schnell

Rekall kombiniert drei Such-Strategien:

```
┌──────────────────────────────────────────────────────────────┐
│                     DEINE ANFRAGE                            │
│              "Browser blockiert API-Aufrufe"                 │
└──────────────────────────────────┬───────────────────────────┘
                                   │
           ┌───────────────────────┼───────────────────────┐
           ▼                       ▼                       ▼
    ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
    │   FTS5      │        │  Semantisch │        │  Keywords   │
    │  (50%)      │        │   (30%)     │        │   (20%)     │
    │             │        │             │        │             │
    │ Exakte Wort-│        │ Bedeutung   │        │ Struktur.   │
    │ Übereinstim.│        │ via Embeddi.│        │ Trigger     │
    └──────┬──────┘        └──────┬──────┘        └──────┬──────┘
           │                      │                      │
           └───────────────────────┼───────────────────────┘
                                   ▼
                        ┌─────────────────┐
                        │  FINALER SCORE  │
                        │  85% Match      │
                        └─────────────────┘
```

- **Volltextsuche (50%)**: SQLite FTS5 findet exakte und partielle Wort-Übereinstimmungen
- **Semantische Suche (30%)**: Embeddings finden konzeptionell ähnlichen Inhalt — "Browser" passt zu "Safari", "blockiert" passt zu "CORS-Fehler"
- **Keywords-Index (20%)**: Deine strukturierten Kontext-Keywords liefern explizite Trigger

### Lokale Embeddings: Optional aber mächtig

Semantische Suche ist **optional**. Rekall funktioniert perfekt mit FTS5-Volltextsuche allein — kein Modell erforderlich.

Aber wenn du semantisches Verständnis möchtest, nutzt Rekall **all-MiniLM-L6-v2** (23M Parameter), ein schnelles und effizientes Embedding-Modell, das vollständig auf deinem Rechner läuft:

- **100% lokal**: Keine Daten verlassen deinen Computer, keine API-Keys, keine Cloud
- **Schnell**: ~50ms pro Embedding auf einem Standard-Laptop-CPU
- **Klein**: ~100MB Speicherbedarf
- **Konfigurierbar**: Wechsle zu mehrsprachigen Modellen (z.B. `paraphrase-multilingual-MiniLM-L12-v2`) über die Config

```bash
# Nur-FTS-Modus (Standard, kein Modell nötig)
rekall search "CORS-Fehler"

# Semantische Suche aktivieren (lädt Modell beim ersten Gebrauch)
rekall config set embeddings.enabled true
```

### Doppeltes Embedding: Kontext zählt

Wenn du Wissen erfasst, speichert Rekall zwei Embeddings:

1. **Summary-Embedding**: Titel + Inhalt + Tags — für fokussierte Suchen
2. **Kontext-Embedding**: Die volle Situation/Lösung — für explorative Suchen

Das löst ein fundamentales Problem beim Retrieval: Zusammenfassungen verlieren Kontext. Wenn du nach "stack trace Safari" suchst, passt die Zusammenfassung "Fix CORS" nicht — aber der vollständige Kontext, den du erfasst hast (der den Stack-Trace erwähnt), wird passen.

### Strukturierter Kontext: Disambiguierung, die funktioniert

Du hast 5 verschiedene "Timeout"-Bugs gefixt. Wie findest du später den richtigen? Keywords allein helfen nicht — sie sind alle mit "timeout" getaggt.

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

Wenn du suchst, nutzt Rekall diesen Kontext zur Disambiguierung:

- **"timeout nach deploy"** → Findet den Connection-Pool-Bug (passt zur Situation)
- **"ETIMEDOUT"** → Findet Einträge mit genau dieser Fehlermeldung
- **"retry hat nicht funktioniert"** → Findet Einträge, wo Retry versucht und gescheitert ist

Das `--context-interactive` Flag führt dich durch die Erfassung:

```bash
rekall add bug "Timeout in Produktion" --context-interactive
# Rekall fragt: Was ist passiert? Was hat es gefixt? Was hat nicht funktioniert?
# Deine Antworten werden zu durchsuchbarem Disambiguierungs-Kontext
```

### Komprimierter Speicher

Kontext kann ausführlich sein. Rekall komprimiert strukturierten Kontext mit zlib und pflegt einen separaten Keywords-Index für schnelle Suche:

```
┌─────────────────────────────────────────────────────────────┐
│                    EINTRAG-SPEICHER                         │
├─────────────────────────────────────────────────────────────┤
│  context_blob     │  Komprimiertes JSON (zlib) │ ~70% kleiner│
│  context_keywords │  Indexierte Tabelle für    │ O(1) Lookup │
│                   │  Suche                     │             │
│  emb_summary      │  384-dim Vektor (Summary)  │ Semantisch  │
│  emb_context      │  384-dim Vektor (Kontext)  │ Semantisch  │
└─────────────────────────────────────────────────────────────┘
```

Das Ergebnis: **Erschöpfende** Suche (nichts wird übersehen) mit **Geschwindigkeit** (sub-Sekunden-Antworten bei Tausenden Einträgen).

</details>

<br>

<details>
<summary><h2>Basiert auf Wissenschaft</h2></summary>

> **TL;DR:** Wissensgraphen (+20% Genauigkeit), Spaced Repetition (+6-9% Retention), Kontextuelles Retrieval (-67% Fehler), alles untermauert durch peer-reviewed Forschung.

Rekall ist keine Sammlung von Vermutungen — es basiert auf peer-reviewed kognitionswissenschaftlicher und Information-Retrieval-Forschung. Hier ist, was wir gelernt und wie wir es angewendet haben:

### Wissensgraphen: +20% Retrieval-Genauigkeit

**Forschung**: Studien zu Wissensgraphen in RAG-Systemen zeigen, dass verbundene Informationen einfacher abzurufen sind als isolierte Fakten.

**Anwendung**: Rekall lässt dich Einträge mit typisierten Beziehungen verknüpfen (`related`, `supersedes`, `derived_from`, `contradicts`). Wenn du suchst, boosten verknüpfte Einträge gegenseitig ihre Scores. Wenn du einen neuen Timeout-Bug fixst, zeigt Rekall die drei anderen Timeout-Probleme, die du gelöst hast — und das Pattern, das du daraus extrahiert hast.

### Episodisches vs. semantisches Gedächtnis: Wie dein Gehirn organisiert

**Forschung**: Tulving (1972) etablierte, dass menschliches Gedächtnis zwei unterschiedliche Systeme hat — episodisch (spezifische Ereignisse: "Ich habe diesen Bug am Dienstag gefixt") und semantisch (allgemeines Wissen: "Füge immer Retry für externe APIs hinzu").

**Anwendung**: Rekall unterscheidet `episodische` Einträge (was ist passiert) von `semantischen` Einträgen (was du gelernt hast). Der `generalize`-Befehl hilft dir, Patterns aus Episoden zu extrahieren. Das spiegelt wider, wie sich Expertise entwickelt: Du sammelst Erfahrungen, destillierst sie dann zu Prinzipien.

### Spaced Repetition: +6-9% Retention

**Forschung**: Der Spacing-Effekt (Ebbinghaus, 1885) und SM-2-Algorithmus zeigen, dass das Wiederholen von Information in zunehmenden Intervallen die Retention dramatisch verbessert.

**Anwendung**: Rekall trackt, wann du jeden Eintrag aufrufst und berechnet einen Konsolidierungs-Score. Der `review`-Befehl bringt Wissen an die Oberfläche, das zu verblassen droht. Der `stale`-Befehl findet Einträge, die du seit Monaten nicht berührt hast — bevor sie vergessen werden.

### Kontextuelles Retrieval: -67% Such-Fehler

**Forschung**: Anthropics Contextual Retrieval Paper zeigte, dass traditionelle RAG-Systeme scheitern, weil sie Kontext beim Encoding entfernen. Das Hinzufügen von 50-100 Tokens Kontext reduziert Retrieval-Fehler um 67%.

**Anwendung**: Rekalls strukturierter Kontext (Situation, Lösung, Keywords) bewahrt das "Warum" neben dem "Was". Die Doppel-Embedding-Strategie stellt sicher, dass sowohl fokussierte Anfragen als auch explorative Suchen relevante Einträge finden.

### Progressive Disclosure: -98% Token-Nutzung

**Forschung**: Anthropics Engineering-Blog dokumentierte, dass das Zurückgeben kompakter Zusammenfassungen statt vollständigem Inhalt die Token-Nutzung um 98% reduziert, während der Task-Erfolg erhalten bleibt.

**Anwendung**: Rekalls MCP-Server gibt kompakte Ergebnisse zurück (id, Titel, Score, Snippet) mit einem Hinweis, vollständige Details abzurufen. Dein KI-Assistent bekommt, was er braucht, ohne sein Kontext-Fenster zu sprengen.

### Konsolidierungs-Score: Vergessen modellieren

**Forschung**: Die Forgetting-Curve zeigt, dass Erinnerungen exponentiell zerfallen ohne Verstärkung. Zugriffshäufigkeit und Aktualität zählen beide.

**Anwendung**: Rekall berechnet einen Konsolidierungs-Score für jeden Eintrag:

```python
score = 0.6 × frequency_factor + 0.4 × freshness_factor
```

Einträge, die du oft und kürzlich aufrufst, haben hohe Konsolidierung (stabiles Wissen). Einträge, die du seit Monaten nicht berührt hast, haben niedrige Konsolidierung (Risiko vergessen zu werden).

**Wir haben die Papers gelesen, damit du es nicht musst. Dann haben wir ein Tool gebaut, das sie anwendet.**

</details>

<br>

## Mehr erfahren

| Ressource | Beschreibung |
|----------|-------------|
| [Erste Schritte](docs/getting-started.md) | Installation und erste Schritte |
| [CLI-Referenz](docs/usage.md) | Vollständige Befehls-Dokumentation |
| [MCP-Integration](docs/mcp-integration.md) | Verbindung mit KI-Assistenten |
| [Architektur](docs/architecture.md) | Technische Diagramme und Interna |
| [Contributing](CONTRIBUTING.md) | Wie du beitragen kannst |
| [Changelog](CHANGELOG.md) | Release-Historie |

---

## Anforderungen

- Python 3.10+
- Das war's. Keine Cloud-Services. Keine API-Keys. Keine Accounts.

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
