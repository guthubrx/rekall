# Rekall CLI Reference

Complete reference for all Rekall commands.

## Global Options

```bash
rekall --help          # Show help
rekall --version       # Show version
rekall -v              # Verbose output
```

## Commands Overview

| Command | Description |
|---------|-------------|
| `rekall` | Launch interactive TUI |
| `rekall add` | Create new entry |
| `rekall search` | Search entries |
| `rekall show` | View entry details |
| `rekall edit` | Edit entry |
| `rekall delete` | Delete entry |
| `rekall link` | Link two entries |
| `rekall review` | Spaced repetition session |
| `rekall stale` | Find forgotten entries |
| `rekall export` | Export entries |
| `rekall import` | Import entries |
| `rekall config` | Manage configuration |
| `rekall mcp` | Start MCP server |

---

## `rekall add`

Create a new knowledge entry.

### Basic Usage

```bash
rekall add <type> "<title>" [options]
```

### Types

`bug`, `pattern`, `decision`, `pitfall`, `config`, `reference`, `snippet`, `til`

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--tags` | `-t` | Comma-separated tags |
| `--content` | `-c` | Entry content/body |
| `--context-interactive` | | Interactive context capture |
| `--source` | `-s` | Source URL or reference |

### Examples

```bash
# Quick entry
rekall add bug "Fix null pointer in auth" -t auth,null

# With content
rekall add pattern "Retry with backoff" -t resilience \
  -c "Always use exponential backoff for external API calls"

# Interactive context (recommended)
rekall add bug "CORS Safari" --context-interactive
```

---

## `rekall search`

Search your knowledge base.

### Basic Usage

```bash
rekall search "<query>" [options]
```

### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--type` | `-t` | Filter by entry type |
| `--limit` | `-n` | Max results (default: 10) |
| `--tags` | | Filter by tags |
| `--json` | | Output as JSON |

### Examples

```bash
# Basic search
rekall search "browser API problem"

# Filter by type
rekall search "timeout" --type bug

# Multiple filters
rekall search "auth" --type decision --tags jwt

# JSON output for scripting
rekall search "cors" --json | jq '.entries[0].id'
```

---

## `rekall show`

View full entry details.

### Usage

```bash
rekall show <entry_id>
```

### Example

```bash
rekall show 01HX7ABCD...

# Output:
# ┌─────────────────────────────────────────┐
# │ bug: CORS fails on Safari               │
# ├─────────────────────────────────────────┤
# │ Tags: cors, safari, fetch               │
# │ Created: 2024-01-15 14:32               │
# │ Accessed: 12 times                      │
# │ Consolidation: 85%                      │
# ├─────────────────────────────────────────┤
# │ Situation:                              │
# │ Safari blocks requests even with CORS   │
# │                                         │
# │ Solution:                               │
# │ Add credentials: 'include'              │
# └─────────────────────────────────────────┘
```

---

## `rekall edit`

Edit an existing entry.

### Usage

```bash
rekall edit <entry_id> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--title` | Update title |
| `--content` | Update content |
| `--tags` | Update tags |
| `--type` | Change entry type |

### Example

```bash
rekall edit 01HX7... --tags "cors,safari,fixed"
```

---

## `rekall delete`

Delete an entry.

### Usage

```bash
rekall delete <entry_id> [--force]
```

### Example

```bash
rekall delete 01HX7...
# Confirm: Delete "CORS fails on Safari"? [y/N]

rekall delete 01HX7... --force  # Skip confirmation
```

---

## `rekall link`

Create relationships between entries.

### Usage

```bash
rekall link <entry_id_1> <entry_id_2> --type <relation>
```

### Relation Types

| Type | Meaning |
|------|---------|
| `related` | General relationship |
| `derived_from` | Entry 2 was extracted from Entry 1 |
| `supersedes` | Entry 1 replaces Entry 2 |
| `contradicts` | Entries conflict (flag for review) |

### Example

```bash
# Pattern derived from multiple bug fixes
rekall link 01HX7... 01HY8... --type derived_from
```

---

## `rekall review`

Start a spaced repetition review session.

### Usage

```bash
rekall review [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--limit` | Max entries to review |
| `--type` | Filter by entry type |

### How It Works

1. Rekall shows entries due for review (based on SM-2 algorithm)
2. You rate your recall: 0 (forgot) to 5 (perfect)
3. Rekall schedules the next review based on your rating

### Example Session

```bash
rekall review --limit 5

# ┌─────────────────────────────────────────┐
# │ [1/5] bug: CORS Safari                  │
# │                                         │
# │ What was the solution?                  │
# │                                         │
# │ Press Enter to reveal...                │
# └─────────────────────────────────────────┘
#
# Add credentials: 'include' and explicit Allow-Origin
#
# Rate your recall [0-5]: 4
# → Next review in 6 days
```

---

## `rekall stale`

Find entries you haven't accessed recently.

### Usage

```bash
rekall stale [--days N]
```

### Example

```bash
rekall stale --days 90

# Entries not accessed in 90+ days:
# - config: Docker compose for dev (124 days)
# - reference: JWT validation docs (98 days)
```

---

## `rekall export`

Export entries to file.

### Usage

```bash
rekall export [options] > output.json
```

### Options

| Option | Description |
|--------|-------------|
| `--format` | `json` (default) or `csv` |
| `--type` | Filter by entry type |
| `--tags` | Filter by tags |

### Example

```bash
rekall export --format json > backup.json
rekall export --type bug --tags cors > cors-bugs.json
```

---

## `rekall import`

Import entries from file.

### Usage

```bash
rekall import <file> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--merge` | Merge with existing entries |
| `--replace` | Replace duplicates |

### Example

```bash
rekall import backup.json --merge
```

---

## `rekall config`

Manage Rekall configuration.

### Usage

```bash
rekall config get <key>
rekall config set <key> <value>
rekall config list
```

### Available Settings

| Key | Default | Description |
|-----|---------|-------------|
| `embeddings.enabled` | `false` | Enable semantic search |
| `embeddings.model` | `embedding-gemma` | Embedding model |
| `search.fts_weight` | `0.5` | FTS search weight |
| `search.semantic_weight` | `0.3` | Semantic search weight |
| `search.keyword_weight` | `0.2` | Keyword search weight |

### Example

```bash
rekall config set embeddings.enabled true
rekall config get embeddings.enabled
rekall config list
```

---

## `rekall mcp`

Start the MCP server for AI assistant integration.

### Usage

```bash
rekall mcp [options]
```

### Options

| Option | Description |
|--------|-------------|
| `--port` | Server port (default: auto) |
| `--stdio` | Use stdio transport (for MCP clients) |

See [MCP Integration Guide](mcp-integration.md) for full setup instructions.

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `REKALL_DATA_DIR` | Override data directory |
| `REKALL_CONFIG` | Override config file path |
| `NO_COLOR` | Disable colored output |

```bash
REKALL_DATA_DIR=/custom/path rekall search "query"
```
