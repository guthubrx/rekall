# Getting Started with Rekall

This guide will get you up and running with Rekall in under 5 minutes.

## Installation

### Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer:

```bash
# Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Rekall
uv tool install git+https://github.com/guthubrx/rekall.git
```

### Using pipx

```bash
# Install pipx if you don't have it
python -m pip install --user pipx
pipx ensurepath

# Install Rekall
pipx install git+https://github.com/guthubrx/rekall.git
```

### Verify Installation

```bash
rekall version
# Output: Rekall v0.3.x
```

## Your First Entry

Capture your first piece of knowledge:

```bash
rekall add bug "My first captured bug" -t test,first
```

Output:
```
✓ Entry created: 01HX7...
  Type: bug
  Title: My first captured bug
  Tags: test, first
```

## Interactive Context Capture

For richer entries, use interactive mode:

```bash
rekall add bug "CORS fails on Safari" --context-interactive
```

Rekall will prompt you:
```
> Situation: What was happening when the problem occurred?
Safari blocks fetch requests even with CORS headers configured

> Solution: What fixed it?
Add credentials: 'include' and explicit Access-Control-Allow-Origin

> What didn't work? (optional)
Adding just the CORS headers without credentials

> Keywords (comma-separated):
cors, safari, fetch, credentials, cross-origin
```

## Searching Your Knowledge

### Basic Search

```bash
rekall search "browser API problem"
```

Output:
```
Found 2 entries:

[1] bug: CORS fails on Safari                    85%
    cors, safari, fetch  •  just now
    "Add credentials: include..."

[2] pattern: Cross-origin handling               72%
    architecture  •  2 months ago
    "Always test on Safari..."
```

### Search by Type

```bash
rekall search "timeout" --type bug
rekall search "retry" --type pattern
```

## The Terminal UI

Launch the interactive interface:

```bash
rekall
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `/` | Search |
| `a` | Add new entry |
| `Enter` | View entry details |
| `e` | Edit entry |
| `d` | Delete entry |
| `l` | Link entries |
| `↑/↓` | Navigate |
| `q` | Quit |

## Entry Types

| Type | Use for | Example |
|------|---------|---------|
| `bug` | Solved problems | "CORS Safari fix" |
| `pattern` | Reusable approaches | "Retry with backoff" |
| `decision` | Why X over Y | "PostgreSQL over MongoDB" |
| `pitfall` | Mistakes to avoid | "Never SELECT * in prod" |
| `config` | Working configurations | "VS Code debug settings" |
| `reference` | Useful docs/links | "That StackOverflow answer" |
| `snippet` | Code to keep | "Generic debounce function" |
| `til` | Quick learnings | "Git rebase -i reorders commits" |

## Enable Semantic Search (Optional)

By default, Rekall uses FTS5 full-text search. To enable semantic understanding:

```bash
rekall config set embeddings.enabled true
```

On first search, Rekall downloads EmbeddingGemma (~200MB). After that:
- Searches understand meaning, not just keywords
- "browser blocking API" finds "CORS error on Safari"
- ~500ms per embedding on standard CPU

## Connect Your AI Assistant

See [MCP Integration Guide](mcp-integration.md) for connecting Rekall to:
- Claude Code
- Claude Desktop
- Cursor
- Windsurf
- Continue.dev

## Spaced Repetition Review

Rekall uses SM-2 algorithm to schedule reviews:

```bash
rekall review
```

Rate your recall from 0-5:
- **0-2**: Failed to recall (review sooner)
- **3**: Recalled with difficulty
- **4**: Good recall
- **5**: Perfect recall (review later)

## Data Location

All data stays local:

```
~/.local/share/rekall/
├── rekall.db       # SQLite database
├── config.toml     # Your settings
└── backups/        # Automatic backups
```

## Next Steps

- [Usage Guide](usage.md) - All CLI commands
- [MCP Integration](mcp-integration.md) - Connect to AI assistants
- [Architecture](architecture.md) - How Rekall works internally
