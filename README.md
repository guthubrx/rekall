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

Rekall is a developer knowledge management system that captures bugs, patterns, and decisions directly from your terminal. Search your past solutions before solving the same problem twice.

## Why Rekall?

You fix a bug. Three months later, same bug. *Where was that fix again?*

Rekall solves this by giving you a local, searchable database of everything you've learned:
- **Bugs** you've fixed
- **Patterns** you've discovered
- **Decisions** you've made
- **Pitfalls** to avoid

No cloud. No subscription. Just your knowledge, instantly searchable.

## Installation

### With uv (recommended)

```bash
uv tool install git+https://github.com/guthubrx/rekall.git
```

### With pipx

```bash
pipx install git+https://github.com/guthubrx/rekall.git
```

### With pip

```bash
pip install git+https://github.com/guthubrx/rekall.git
```

### From source

```bash
git clone https://github.com/guthubrx/rekall.git
cd rekall
uv tool install .
# or: pip install .
```

### Verify

```bash
rekall version
```

## Quick Start

### Interactive mode

```bash
rekall
```

Navigate with arrow keys, select with Enter.

### Search your knowledge

```bash
rekall search "circular import"
rekall search "authentication" --type pattern
rekall search "react" --project frontend
```

### Capture knowledge

```bash
# Quick entry
rekall add bug "Fix: circular import in models" -t python,import -p myproject

# With detailed content
echo "## Problem
Module A imports B, B imports A.

## Solution
Extract shared types to types/common.py

## Why
Breaks the circular dependency chain." | rekall add bug "Fix circular import" -t python -c 4
```

### Browse entries

```bash
rekall browse
rekall browse --type pattern
rekall show <id>
```

## Entry Types

| Type | Use for |
|------|---------|
| `bug` | Bugs fixed, errors resolved |
| `pattern` | Reusable code, best practices |
| `decision` | Architecture choices, trade-offs |
| `pitfall` | Mistakes to avoid, anti-patterns |
| `config` | Configuration tips, setup notes |
| `reference` | Documentation links, resources |
| `snippet` | Code snippets |
| `til` | Today I Learned |

## IDE Integration

Rekall integrates with your AI coding assistant:

```bash
rekall install --list          # Show available integrations
rekall install cursor          # Cursor AI
rekall install claude          # Claude Code
rekall install copilot         # GitHub Copilot
rekall install windsurf        # Windsurf
rekall install cline           # Cline
rekall install zed             # Zed
rekall install gemini          # Gemini CLI
rekall install continue        # Continue.dev
```

The integration teaches your AI assistant to:
1. Search Rekall before solving problems
2. Suggest capturing new knowledge after fixes

## Export & Backup

```bash
# Export to portable archive
rekall export backup.rekall.zip

# Export filtered
rekall export frontend.rekall.zip --project frontend

# Import from archive
rekall import backup.rekall.zip
rekall import backup.rekall.zip --dry-run  # Preview first
```

## Data Location

Rekall follows XDG conventions:

| Platform | Config | Data |
|----------|--------|------|
| Linux | `~/.config/rekall/` | `~/.local/share/rekall/` |
| macOS | `~/Library/Application Support/rekall/` | Same |
| Windows | `%APPDATA%\rekall\` | Same |

Override with `REKALL_HOME` environment variable.

### Local project mode

```bash
rekall init --local  # Creates .rekall/ in current directory
```

Share knowledge with your team by committing `.rekall/` to Git.

## Commands Reference

| Command | Description |
|---------|-------------|
| `rekall` | Interactive TUI |
| `rekall add <type> "title"` | Add entry |
| `rekall search "query"` | Search entries |
| `rekall show <id>` | Show entry details |
| `rekall browse` | Browse all entries |
| `rekall deprecate <id>` | Mark entry obsolete |
| `rekall export <file>` | Export database |
| `rekall import <file>` | Import archive |
| `rekall install <ide>` | Install IDE integration |
| `rekall config --show` | Show configuration |
| `rekall version` | Version info |

## Requirements

- Python 3.9+
- No external services required

## License

MIT
