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

Rekall is a developer knowledge management system with **cognitive memory** and **semantic search**. It doesn't just store your knowledge — it helps you *remember* and *find* it like your brain does.

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-brightgreen.svg)](LICENSE)

**Translations:** [Français](README.fr.md) | [Español](README.es.md) | [Deutsch](README.de.md) | [中文](README.zh-CN.md)

---

## Why Rekall?

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

With Rekall:

```
┌─────────────────────────────────────────┐
│ $ rekall search "circular import"       │
│                                         │
│ [1] bug: Fix: circular import in models │
│     Score: ████████░░ 85%               │
│     Situation: Import cycle between     │
│                user.py and profile.py   │
│     Solution: Extract shared types to   │
│               types/common.py           │
└─────────────────────────────────────────┘
```

**Found in 5 seconds. No cloud. No subscription.**

---

## Features

| Feature | Description |
|---------|-------------|
| **Semantic Search** | Find by meaning, not just keywords |
| **Structured Context** | Capture situation, solution, and keywords |
| **Knowledge Graph** | Link related entries together |
| **Cognitive Memory** | Distinguish episodes from patterns |
| **Spaced Repetition** | Review knowledge at optimal intervals |
| **MCP Server** | AI agent integration (Claude, etc.) |
| **100% Local** | Your data never leaves your machine |
| **TUI Interface** | Beautiful terminal UI with Textual |

---

## Installation

```bash
# With uv (recommended)
uv tool install git+https://github.com/guthubrx/rekall.git

# With pipx
pipx install git+https://github.com/guthubrx/rekall.git

# Verify installation
rekall version
```

---

## Quick Start

### 1. Capture knowledge with context

```bash
# Simple entry
rekall add bug "Fix: circular import in models" -t python,import

# With structured context (recommended)
rekall add bug "Fix: circular import" --context-interactive
# > Situation: Import cycle between user.py and profile.py
# > Solution: Extract shared types to types/common.py
# > Keywords: circular, import, cycle, refactor
```

### 2. Search semantically

```bash
# Text search
rekall search "circular import"

# Semantic search (finds related concepts)
rekall search "module dependency cycle" --semantic

# By keywords
rekall search --keywords "import,cycle"
```

### 3. Explore in TUI

```bash
rekall          # Launch interactive interface
```

```
┌─ Rekall ──────────────────────────────────────────────┐
│  Search: circular import                              │
├───────────────────────────────────────────────────────┤
│  [1] bug: Fix: circular import in models    85% █████ │
│      python, import | 2024-12-10                      │
│                                                       │
│  [2] pattern: Dependency injection          72% ████  │
│      architecture | 2024-11-15                        │
├───────────────────────────────────────────────────────┤
│  [/] Search  [a] Add  [Enter] View  [s] Settings      │
└───────────────────────────────────────────────────────┘
```

---

## Structured Context

Every entry can have rich context that makes it findable:

```bash
rekall add bug "CORS error on Safari" --context-json '{
  "situation": "Safari blocks cross-origin requests even with CORS headers",
  "solution": "Add credentials: include and proper Access-Control headers",
  "trigger_keywords": ["cors", "safari", "cross-origin", "credentials"]
}'
```

Or use interactive mode:

```bash
rekall add bug "CORS error on Safari" --context-interactive
```

This captures:
- **Situation**: What was happening? What were the symptoms?
- **Solution**: What fixed it? What was the root cause?
- **Keywords**: Trigger words for finding this later

---

## Semantic Search

Rekall uses local embeddings to find entries by meaning:

```bash
# Enable semantic search
rekall embeddings --status      # Check status
rekall embeddings --migrate     # Generate embeddings for existing entries

# Search by meaning
rekall search "authentication timeout" --semantic
```

The search combines:
- **Full-text search** (50%) - Exact keyword matching
- **Semantic similarity** (30%) - Meaning-based matching
- **Keyword matching** (20%) - Structured context keywords

---

## Knowledge Graph

Connect related entries to build a knowledge network:

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
    │   (Generalized knowledge)  │
    └────────────────────────────┘
```

```bash
rekall link 01HXYZ 01HABC                      # Create link
rekall link 01HXYZ 01HABC --type supersedes    # With relationship type
rekall related 01HXYZ                          # Show connections
rekall graph 01HXYZ                            # ASCII visualization
```

**Link types:** `related`, `supersedes`, `derived_from`, `contradicts`

---

## Cognitive Memory

Like your brain, Rekall distinguishes two types of memory:

### Episodic Memory (What happened)
Specific events with full context:
```bash
rekall add bug "Auth timeout on prod API 15/12" --memory-type episodic
```

### Semantic Memory (What you learned)
Abstract patterns and principles:
```bash
rekall add pattern "Always add retry backoff for external APIs" --memory-type semantic
```

### Generalization
Extract patterns from multiple episodes:
```bash
rekall generalize 01HA 01HB 01HC --title "Retry pattern for timeouts"
```

---

## Spaced Repetition

Review knowledge at optimal intervals using SM-2 algorithm:

```bash
rekall review              # Start review session
rekall review --limit 10   # Review 10 entries
rekall stale               # Find forgotten knowledge (30+ days)
rekall stale --days 7      # Custom threshold
```

Rating scale:
- **1** = Completely forgot
- **3** = Remembered with effort
- **5** = Perfect recall

---

## MCP Server (AI Integration)

Rekall includes an MCP server for AI assistant integration:

```bash
# Start MCP server
rekall mcp

# Or configure in Claude Desktop / Claude Code
```

**Available tools:**
- `rekall_search` - Search the knowledge base
- `rekall_add` - Add new entries
- `rekall_show` - Get entry details
- `rekall_link` - Connect entries
- `rekall_suggest` - Get suggestions based on embeddings

---

## IDE Integrations

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
1. Search Rekall before solving problems
2. Cite your past solutions in responses
3. Suggest capturing new knowledge after fixes

---

## Migration & Maintenance

```bash
rekall version             # Show version + schema info
rekall changelog           # Display version history
rekall migrate             # Upgrade database schema (with backup)
rekall migrate --dry-run   # Preview changes
rekall migrate --enrich-context  # Add structured context to legacy entries
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
│  ├── config.toml  (Settings)        │
│  └── backups/     (Auto backups)    │
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
| `rekall search --semantic` | Semantic search |
| `rekall search --keywords` | Keyword search |
| `rekall search --json` | JSON output for AI |
| `rekall show <id>` | Entry details + score |
| `rekall browse` | Browse all entries |
| `rekall link <a> <b>` | Connect entries |
| `rekall unlink <a> <b>` | Remove connection |
| `rekall related <id>` | Show linked entries |
| `rekall graph <id>` | ASCII graph visualization |
| `rekall stale` | Forgotten entries |
| `rekall review` | Spaced repetition session |
| `rekall generalize <ids>` | Episodes to Pattern |
| `rekall deprecate <id>` | Mark obsolete |
| `rekall export <file>` | Export database |
| `rekall import <file>` | Import archive |
| `rekall install <ide>` | IDE integration |
| `rekall embeddings` | Manage semantic embeddings |
| `rekall mcp` | Start MCP server |
| `rekall version` | Version and schema info |
| `rekall changelog` | Version history |
| `rekall migrate` | Upgrade database |

---

## Requirements

- Python 3.9+
- No external services
- No internet required (except for optional embedding model download)
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
