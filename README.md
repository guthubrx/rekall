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

**Stop losing knowledge. Start remembering.**

Rekall is a developer knowledge management system with **cognitive memory** - it doesn't just store your knowledge, it helps you *remember* it like your brain does.

---

## The Problem

```
You (3 months ago)          You (today)
     │                           │
     ▼                           ▼
┌─────────────┐           ┌─────────────┐
│ Fix bug X   │           │ Same bug X  │
│ 2h research │           │ starts from │
│ Found fix!  │           │ scratch...  │
└─────────────┘           └─────────────┘
     │                           │
     ▼                           ▼
   (lost)                    (2h again)
```

**You've already solved this.** But where was that fix again?

---

## The Solution

```
You (3 months ago)          You (today)
     │                           │
     ▼                           ▼
┌─────────────┐           ┌─────────────┐
│ Fix bug X   │           │ Same bug X  │
│ 2h research │           │             │
│ Found fix!  │           │ rekall      │
└─────────────┘           │ search      │
     │                    └──────┬──────┘
     ▼                           │
┌─────────────┐                  │
│   REKALL    │◄─────────────────┘
│  DATABASE   │
│             │────► Found in 5 seconds!
└─────────────┘
```

**No cloud. No subscription. Just your knowledge, instantly searchable.**

---

## Installation

```bash
# With uv (recommended)
uv tool install git+https://github.com/guthubrx/rekall.git

# With pipx
pipx install git+https://github.com/guthubrx/rekall.git

# Verify
rekall version
```

---

## Quick Start (2 minutes)

### 1. Capture knowledge

```bash
rekall add bug "Fix: circular import in models" -t python,import
```

### 2. Search later

```bash
rekall search "circular import"
```

### 3. Never solve the same problem twice

```
┌────────────────────────────────────────────────────────┐
│ $ rekall search "circular import"                      │
│                                                        │
│ [1] bug: Fix: circular import in models                │
│     Tags: python, import                               │
│     Score: ████████░░ 85%                              │
│                                                        │
│     Solution: Extract shared types to types/common.py  │
└────────────────────────────────────────────────────────┘
```

---

## Cognitive Memory System

Rekall doesn't just store entries - it builds a **knowledge graph** that mimics how your brain works.

### Knowledge Graph

Connect related knowledge to discover patterns:

```
              ┌──────────────────┐
              │  Timeout Auth    │
              │  (Bug #1)        │
              └────────┬─────────┘
                       │ related
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │ Timeout  │ │ Timeout  │ │ Timeout  │
    │ DB #2    │ │ API #3   │ │ Cache #4 │
    └────┬─────┘ └────┬─────┘ └──────────┘
         │            │
         └─────┬──────┘
               │ derived_from
               ▼
    ┌────────────────────────────┐
    │   PATTERN: Retry Backoff   │
    │   (Semantic knowledge)     │
    └────────────────────────────┘
```

```bash
rekall link 01HXYZ 01HABC                    # Create link
rekall link 01HXYZ 01HABC --type supersedes  # With type
rekall related 01HXYZ                        # See connections
```

**Link types:** `related`, `supersedes`, `derived_from`, `contradicts`

---

### Two Types of Memory

Like your brain, Rekall distinguishes **episodes** from **concepts**:

```
EPISODIC MEMORY                    SEMANTIC MEMORY
(What happened)                    (What you learned)
      │                                  │
      ▼                                  ▼
┌─────────────────┐              ┌─────────────────┐
│ "15/12/2024     │              │ "Always add     │
│  Auth timeout   │  generalize  │  retry backoff  │
│  on prod API"   │ ──────────►  │  for timeouts"  │
└─────────────────┘              └─────────────────┘
      │                                  │
      │                                  │
Context-rich                       Reusable pattern
Dated event                        Abstract principle
```

```bash
rekall add bug "Auth timeout 15/12" --memory-type episodic    # Default
rekall add pattern "Retry backoff" --memory-type semantic     # Pattern
rekall search "timeout" --memory-type semantic                # Filter
```

**Why both?**
- **Episodic** = Raw material, context, evidence
- **Semantic** = Distilled wisdom, reusable patterns
- Use `rekall generalize` to extract patterns from episodes

---

### Access Tracking & Consolidation

Rekall tracks how often you access each entry:

```
CONSOLIDATION SCORE
(How well you remember)

   Access        Time since
   count         last access
     │               │
     ▼               ▼
  ┌─────┐  60%   ┌─────┐  40%
  │░░░░░│ ────►  │░░░░░│ ────►  FINAL SCORE
  │Freq │        │Fresh│        0% - 100%
  └─────┘        └─────┘
     │               │
     └───────┬───────┘
             ▼
   🔴 <30%  = Fragile (risk of forgetting)
   🟡 30-70% = Stable
   🟢 >70%  = Consolidated
```

```bash
rekall stale              # Find forgotten knowledge (30+ days)
rekall stale --days 7     # Custom threshold
rekall show <id>          # See consolidation score
```

---

### Spaced Repetition

Review knowledge at optimal intervals using the **SM-2 algorithm**:

```
REVIEW SCHEDULE (SM-2 Algorithm)

     ┌─────────────────────────────────────────────────►
     │               TIME
     │
  R  │    ┌──┐      ┌──┐         ┌──┐              ┌──┐
  E  │    │R1│      │R2│         │R3│              │R4│
  V  │    │  │      │  │         │  │              │  │
  I  │    └──┘      └──┘         └──┘              └──┘
  E  │      │         │            │                 │
  W  │      ▼         ▼            ▼                 ▼
     │    1 day     3 days       7 days           21 days
     │
     │    Intervals grow if you remember well (score 4-5)
     │    Intervals shrink if you struggle (score 1-2)
```

```bash
rekall review             # Start review session
rekall review --limit 5   # Review 5 entries
```

**Rating during review:**
- 1 = Completely forgot
- 3 = Remembered with effort
- 5 = Perfect recall

---

### From Episodes to Patterns

When you notice recurring problems, extract patterns:

```
BEFORE (3 similar bugs)          AFTER (generalized)

┌─────────────┐                  ┌─────────────┐
│ Auth timeout│                  │ Auth timeout│
│ (episodic)  │──┐               │ (episodic)  │───┐
└─────────────┘  │               └─────────────┘   │
                 │                                 │ derived_from
┌─────────────┐  │               ┌─────────────┐   │
│ DB timeout  │──┼───────►       │ DB timeout  │───┼──►┌─────────────┐
│ (episodic)  │  │ generalize    │ (episodic)  │   │   │   PATTERN   │
└─────────────┘  │               └─────────────┘   │   │   Retry     │
                 │                                 │   │   Backoff   │
┌─────────────┐  │               ┌─────────────┐   │   │  (semantic) │
│ API timeout │──┘               │ API timeout │───┘   └─────────────┘
│ (episodic)  │                  │ (episodic)  │
└─────────────┘                  └─────────────┘
```

```bash
rekall generalize 01HA 01HB 01HC                # Create pattern
rekall generalize 01HA 01HB --dry-run           # Preview first
rekall generalize 01HA 01HB --title "Retry pattern"
```

---

## AI Assistant Integration

Teach your AI coding assistant to use your knowledge base:

```
┌─────────────────────────────────────────────────────────┐
│                    WORKFLOW                             │
│                                                         │
│   ┌──────────┐    search     ┌──────────┐              │
│   │  Claude  │ ────────────► │  Rekall  │              │
│   │  Code    │               │   CLI    │              │
│   └────┬─────┘               └────┬─────┘              │
│        │                          │                     │
│        │  ◄───── JSON ────────────┘                    │
│        │   (relevance scores,                          │
│        │    links, metadata)                           │
│        ▼                                               │
│   ┌──────────┐                                         │
│   │  Human   │ ◄── Formatted answer with citations    │
│   │   You    │                                         │
│   └──────────┘                                         │
└─────────────────────────────────────────────────────────┘
```

```bash
rekall install claude     # Claude Code
rekall install cursor     # Cursor AI
rekall install copilot    # GitHub Copilot
rekall install windsurf   # Windsurf
rekall install cline      # Cline
rekall install zed        # Zed
rekall install gemini     # Gemini CLI
rekall install continue   # Continue.dev
```

The AI assistant will:
1. **Search Rekall** before solving problems
2. **Cite your past solutions** in responses
3. **Suggest capturing** new knowledge after fixes

### JSON Output for Agents

```bash
rekall search "auth" --json
```

```json
{
  "query": "auth",
  "results": [{
    "id": "01HXYZ...",
    "type": "bug",
    "title": "Auth timeout fix",
    "relevance_score": 0.85,
    "consolidation_score": 0.72,
    "links": {
      "outgoing": [{"target_id": "01HABC", "type": "related"}],
      "incoming": []
    }
  }],
  "total_count": 3
}
```

---

## Entry Types

| Type | Use for | Example |
|------|---------|---------|
| `bug` | Bugs fixed | "Fix: CORS error on Safari" |
| `pattern` | Best practices | "Pattern: Repository pattern for DB" |
| `decision` | Architecture choices | "Decision: Use Redis for sessions" |
| `pitfall` | Mistakes to avoid | "Pitfall: Don't use SELECT *" |
| `config` | Setup tips | "Config: VS Code debug Python" |
| `reference` | External docs | "Ref: React Hooks documentation" |
| `snippet` | Code blocks | "Snippet: Debounce function" |
| `til` | Quick learnings | "TIL: Git rebase -i for squash" |

---

## Data & Privacy

**100% local. Zero cloud.**

```
Your machine
     │
     ▼
┌─────────────────────────────────────┐
│  ~/.local/share/rekall/             │
│  ├── rekall.db    (SQLite + FTS5)   │
│  └── config.toml  (Settings)        │
└─────────────────────────────────────┘
     │
     ▼
  Nowhere else
```

| Platform | Location |
|----------|----------|
| Linux | `~/.local/share/rekall/` |
| macOS | `~/Library/Application Support/rekall/` |
| Windows | `%APPDATA%\rekall\` |

### Team Sharing

```bash
rekall init --local   # Creates .rekall/ in project
git add .rekall/      # Commit to share with team
```

### Export & Backup

```bash
rekall export backup.rekall.zip                    # Full backup
rekall export frontend.zip --project frontend      # Filtered
rekall import backup.rekall.zip --dry-run          # Preview import
```

---

## Commands Reference

| Command | Description |
|---------|-------------|
| `rekall` | Interactive TUI |
| `rekall add <type> "title"` | Capture knowledge |
| `rekall search "query"` | Search entries |
| `rekall search --json` | JSON output for AI |
| `rekall show <id>` | Entry details + score |
| `rekall browse` | Browse all entries |
| `rekall link <a> <b>` | Connect entries |
| `rekall unlink <a> <b>` | Remove connection |
| `rekall related <id>` | Show linked entries |
| `rekall stale` | Forgotten entries |
| `rekall review` | Spaced repetition session |
| `rekall generalize <ids>` | Episodes → Pattern |
| `rekall deprecate <id>` | Mark obsolete |
| `rekall export <file>` | Export database |
| `rekall import <file>` | Import archive |
| `rekall install <ide>` | IDE integration |

---

## Requirements

- Python 3.9+
- No external services
- No internet required
- No account needed

---

## License

MIT

---

**Stop losing knowledge. Start remembering.**

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
rekall
```
