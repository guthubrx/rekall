# Rekall

```
        ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗
        ██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║
        ██████╔╝█████╗  █████╔╝ ███████║██║     ██║
        ██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║
        ██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗
        ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
```

> *"Get your ass to Mars. Quaid... crush those bugs"*

**Hör auf, Wissen zu verlieren. Fang an, dich zu erinnern.**

Rekall ist ein Wissensmanagement-System für Entwickler mit **kognitivem Gedächtnis** und **semantischer Suche**. Es speichert nicht nur dein Wissen — es hilft dir, dich daran zu *erinnern* und es zu *finden*, wie dein Gehirn es tut.

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

**Übersetzungen:** [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [中文](README.zh-CN.md)

---

## Warum Rekall?

```
Du (vor 3 Monaten)           Du (heute)
     │                           │
     ▼                           ▼
┌─────────────┐           ┌─────────────┐
│ Fix Bug X   │           │ Gleicher    │
│ 2h Recherche│           │ Bug X von   │
│ Gefunden!   │           │ vorne...    │
└─────────────┘           └─────────────┘
     │                           │
     ▼                           ▼
  (verloren)                 (2h wieder)
```

**Du hast das schon gelöst.** Aber wo war diese Lösung nochmal?

Mit Rekall:

```
┌─────────────────────────────────────────┐
│ $ rekall search "zirkulärer import"     │
│                                         │
│ [1] bug: Fix: zirkulärer Import models  │
│     Score: ████████░░ 85%               │
│     Situation: Import-Zyklus zwischen   │
│                user.py und profile.py   │
│     Lösung: Gemeinsame Typen nach       │
│             types/common.py extrahieren │
└─────────────────────────────────────────┘
```

**In 5 Sekunden gefunden. Keine Cloud. Kein Abo.**

---

## Funktionen

| Funktion | Beschreibung |
|----------|--------------|
| **Semantische Suche** | Nach Bedeutung suchen, nicht nur Schlüsselwörtern |
| **Strukturierter Kontext** | Situation, Lösung und Schlüsselwörter erfassen |
| **Wissensgraph** | Verwandte Einträge verknüpfen |
| **Kognitives Gedächtnis** | Episoden von Mustern unterscheiden |
| **Verteilte Wiederholung** | Optimal zeitlich wiederholen |
| **MCP-Server** | KI-Agenten-Integration (Claude, etc.) |
| **100% Lokal** | Deine Daten verlassen nie deinen Rechner |
| **TUI-Oberfläche** | Schöne Terminal-UI mit Textual |

---

## Installation

```bash
# Mit uv (empfohlen)
uv tool install git+https://github.com/guthubrx/rekall.git

# Mit pipx
pipx install git+https://github.com/guthubrx/rekall.git

# Installation überprüfen
rekall version
```

---

## Schnellstart

### 1. Wissen mit Kontext erfassen

```bash
# Einfacher Eintrag
rekall add bug "Fix: zirkulärer Import in models" -t python,import

# Mit strukturiertem Kontext (empfohlen)
rekall add bug "Fix: zirkulärer Import" --context-interactive
# > Situation: Import-Zyklus zwischen user.py und profile.py
# > Lösung: Gemeinsame Typen nach types/common.py extrahieren
# > Schlüsselwörter: zirkulär, import, zyklus, refactor
```

### 2. Semantisch suchen

```bash
# Textsuche
rekall search "zirkulärer import"

# Semantische Suche (findet verwandte Konzepte)
rekall search "Modul Abhängigkeitszyklus" --semantic

# Nach Schlüsselwörtern
rekall search --keywords "import,zyklus"
```

### 3. Im TUI erkunden

```bash
rekall          # Interaktive Oberfläche starten
```

---

## Strukturierter Kontext

Jeder Eintrag kann reichhaltigen Kontext haben, der ihn auffindbar macht:

```bash
rekall add bug "CORS-Fehler auf Safari" --context-json '{
  "situation": "Safari blockiert Cross-Origin-Anfragen trotz CORS-Headern",
  "solution": "credentials: include und korrekte Access-Control-Header hinzufügen",
  "trigger_keywords": ["cors", "safari", "cross-origin", "credentials"]
}'
```

Oder im interaktiven Modus:

```bash
rekall add bug "CORS-Fehler auf Safari" --context-interactive
```

---

## Semantische Suche

Rekall verwendet lokale Embeddings, um nach Bedeutung zu suchen:

```bash
# Semantische Suche aktivieren
rekall embeddings --status      # Status prüfen
rekall embeddings --migrate     # Embeddings für bestehende Einträge generieren

# Nach Bedeutung suchen
rekall search "Authentifizierung Timeout" --semantic
```

Die Suche kombiniert:
- **Volltextsuche** (50%) - Exakte Schlüsselwort-Übereinstimmung
- **Semantische Ähnlichkeit** (30%) - Bedeutungsbasierte Übereinstimmung
- **Schlüsselwort-Übereinstimmung** (20%) - Schlüsselwörter aus strukturiertem Kontext

---

## Wissensgraph

Verbinde verwandte Einträge, um ein Wissensnetzwerk aufzubauen:

```bash
rekall link 01HXYZ 01HABC                      # Verknüpfung erstellen
rekall link 01HXYZ 01HABC --type supersedes    # Mit Beziehungstyp
rekall related 01HXYZ                          # Verbindungen anzeigen
rekall graph 01HXYZ                            # ASCII-Visualisierung
```

**Verknüpfungstypen:** `related`, `supersedes`, `derived_from`, `contradicts`

---

## Kognitives Gedächtnis

Wie dein Gehirn unterscheidet Rekall zwei Arten von Gedächtnis:

### Episodisches Gedächtnis (Was passiert ist)
```bash
rekall add bug "Auth Timeout auf Prod API 15/12" --memory-type episodic
```

### Semantisches Gedächtnis (Was du gelernt hast)
```bash
rekall add pattern "Immer Retry-Backoff für externe APIs hinzufügen" --memory-type semantic
```

### Generalisierung
```bash
rekall generalize 01HA 01HB 01HC --title "Retry-Muster für Timeouts"
```

---

## Verteilte Wiederholung

Wiederhole Wissen in optimalen Intervallen mit dem SM-2-Algorithmus:

```bash
rekall review              # Wiederholungssitzung starten
rekall review --limit 10   # 10 Einträge wiederholen
rekall stale               # Vergessenes Wissen finden (30+ Tage)
```

---

## MCP-Server (KI-Integration)

Rekall enthält einen MCP-Server für KI-Assistenten-Integration:

```bash
rekall mcp    # MCP-Server starten
```

**Verfügbare Tools:**
- `rekall_search` - In der Wissensbasis suchen
- `rekall_add` - Einträge hinzufügen
- `rekall_show` - Eintragsdetails abrufen
- `rekall_link` - Einträge verbinden
- `rekall_suggest` - Vorschläge basierend auf Embeddings erhalten

---

## IDE-Integrationen

```bash
rekall install claude     # Claude Code
rekall install cursor     # Cursor AI
rekall install copilot    # GitHub Copilot
rekall install windsurf   # Windsurf
rekall install cline      # Cline
rekall install zed        # Zed
```

---

## Migration & Wartung

```bash
rekall version             # Version + Schema-Info anzeigen
rekall changelog           # Versionshistorie anzeigen
rekall migrate             # Datenbankschema aktualisieren (mit Backup)
rekall migrate --dry-run   # Änderungen vorschauen
```

---

## Eintragstypen

| Typ | Verwendung | Beispiel |
|-----|------------|----------|
| `bug` | Behobene Bugs | "Fix: CORS-Fehler auf Safari" |
| `pattern` | Best Practices | "Pattern: Repository-Muster für DB" |
| `decision` | Architekturentscheidungen | "Decision: Redis für Sessions verwenden" |
| `pitfall` | Zu vermeidende Fehler | "Pitfall: SELECT * nicht verwenden" |
| `config` | Setup-Tipps | "Config: Python Debug in VS Code" |
| `reference` | Externe Docs | "Ref: React Hooks Dokumentation" |
| `snippet` | Codeblöcke | "Snippet: Debounce-Funktion" |
| `til` | Schnelle Erkenntnisse | "TIL: Git rebase -i für Squash" |

---

## Daten & Privatsphäre

**100% lokal. Null Cloud.**

| Plattform | Speicherort |
|-----------|-------------|
| Linux | `~/.local/share/rekall/` |
| macOS | `~/Library/Application Support/rekall/` |
| Windows | `%APPDATA%\rekall\` |

---

## Anforderungen

- Python 3.9+
- Keine externen Dienste
- Kein Internet erforderlich (außer optionaler Embedding-Modell-Download)
- Kein Konto nötig

---

## Lizenz

MIT

---

**Hör auf, Wissen zu verlieren. Fang an, dich zu erinnern.**

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
