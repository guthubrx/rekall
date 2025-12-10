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

**Übersetzungen:** [English](README.md) | [Français](README.fr.md) | [Español](README.es.md) | [中文](README.zh-CN.md)

---

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

### Verbinde deinen KI-Assistenten

Für Claude Code, Cursor oder jedes MCP-kompatible Tool:

```bash
rekall mcp  # Stellt Rekall deiner KI zur Verfügung
```

---

## Basiert auf Wissenschaft

Rekall ist nicht nur praktisch — es basiert auf kognitiver Forschung:

- **Wissensgraphen** verbessern die Abrufgenauigkeit um 20%
- **Verteilte Wiederholung** verbessert die Retention um 6-9%
- **Episodisches vs. semantisches Gedächtnis** ist, wie dein Gehirn Informationen tatsächlich organisiert
- **History-basierte Fehler-Lokalisierung** zeigt, dass Dateien mit früheren Bugs eher neue haben

Wir haben die Paper gelesen, damit du es nicht musst. Dann haben wir ein Tool gebaut, das sie anwendet.

---

## Anforderungen

- Python 3.9+
- Das ist alles. Keine Cloud-Dienste. Keine API-Schlüssel (es sei denn, du willst semantische Suche). Keine Konten.

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
