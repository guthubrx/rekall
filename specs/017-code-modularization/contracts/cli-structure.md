# Contract: CLI Module Structure

**Feature**: 017-code-modularization
**Component**: rekall/cli/
**Date**: 2025-12-12

## Overview

Réorganisation de `cli.py` (4643 LOC, 55 commandes) en 11 sous-modules thématiques.

## Target Structure

```
rekall/cli/
├── __init__.py          # App Typer + exports (~100 LOC)
├── helpers.py           # get_db, decorators, utilities (~200 LOC)
├── core.py              # version, config, init, info (~150 LOC)
├── entries.py           # search, add, show, browse, deprecate (~400 LOC)
├── memory.py            # review, stale, generalize (~300 LOC)
├── knowledge_graph.py   # link, unlink, related, graph (~250 LOC)
├── import_export.py     # export, import_archive (~200 LOC)
├── research.py          # research, similar, suggest (~300 LOC)
├── sources.py           # 12 sources_* commands (~500 LOC)
├── inbox.py             # 6 inbox_* commands (~300 LOC)
├── staging.py           # 6 staging_* commands (~300 LOC)
└── system.py            # backup, restore, migrate, embeddings, mcp (~400 LOC)
```

**Total estimé**: ~3,400 LOC (vs 4,643 actuel - réduction via helpers partagés)

## Module Contracts

### helpers.py

```python
"""Utilitaires partagés pour les commandes CLI."""

from pathlib import Path
from rekall.infra.db import Database
from rekall.config import get_config

__all__ = ["get_db", "require_db", "display_entry", "display_error"]

def get_db(path: Path | None = None) -> Database:
    """Retourne une instance Database configurée."""
    ...

def require_db(func):
    """Décorateur injectant db comme premier argument."""
    ...

def display_entry(entry: Entry, format: str = "rich") -> None:
    """Affiche une entrée selon le format demandé."""
    ...

def display_error(message: str, exit_code: int = 1) -> None:
    """Affiche une erreur formatée et exit."""
    ...
```

### core.py

```python
"""Commandes système de base."""

import typer
from rekall.cli.helpers import get_db

__all__ = ["version", "config", "init", "info"]

def version() -> None:
    """Affiche la version de Rekall."""
    ...

def config(key: str | None = None, value: str | None = None) -> None:
    """Lit ou écrit une configuration."""
    ...

def init(path: Path | None = None) -> None:
    """Initialise une nouvelle base Rekall."""
    ...

def info() -> None:
    """Affiche les informations système."""
    ...
```

### entries.py

```python
"""Commandes CRUD pour les entrées."""

import typer
from rekall.cli.helpers import get_db, display_entry

__all__ = ["search", "add", "show", "browse", "deprecate", "install"]

def search(query: str, limit: int = 20, format: str = "table") -> None:
    """Recherche dans les entrées."""
    ...

def add(
    title: str,
    url: str | None = None,
    content: str | None = None,
    tags: list[str] | None = None,
) -> None:
    """Ajoute une nouvelle entrée."""
    ...

def show(id: int | str) -> None:
    """Affiche une entrée par ID ou titre."""
    ...

def browse() -> None:
    """Lance le navigateur interactif TUI."""
    from rekall.ui import run_tui
    run_tui()

def deprecate(id: int) -> None:
    """Marque une entrée comme dépréciée."""
    ...
```

### sources.py

```python
"""Commandes de gestion des sources curées."""

import typer

__all__ = ["sources_app"]

sources_app = typer.Typer(name="sources", help="Gestion des sources curées")

@sources_app.command("list")
def sources_list(theme: str | None = None, format: str = "table") -> None:
    """Liste les sources."""
    ...

@sources_app.command("add")
def sources_add(url: str, title: str | None = None) -> None:
    """Ajoute une source."""
    ...

@sources_app.command("stats")
def sources_stats() -> None:
    """Statistiques des sources."""
    ...

# ... autres commandes sources_*
```

### __init__.py

```python
"""
CLI Rekall - Interface en ligne de commande.

Usage:
    rekall [COMMAND] [OPTIONS]
"""

import typer
from rekall.cli.core import version, config, init, info
from rekall.cli.entries import search, add, show, browse, deprecate
from rekall.cli.memory import review, stale, generalize
from rekall.cli.knowledge_graph import link, unlink, related, graph
from rekall.cli.import_export import export_cmd, import_archive
from rekall.cli.research import research, similar, suggest
from rekall.cli.sources import sources_app
from rekall.cli.inbox import inbox_app
from rekall.cli.staging import staging_app
from rekall.cli.system import backup, restore, migrate, embeddings_cmd, mcp_server

__all__ = [
    "app",
    "version", "config", "init", "info",
    "search", "add", "show", "browse", "deprecate",
    "review", "stale", "generalize",
    "link", "unlink", "related", "graph",
    "export_cmd", "import_archive",
    "research", "similar", "suggest",
    "sources_app", "inbox_app", "staging_app",
    "backup", "restore", "migrate", "embeddings_cmd", "mcp_server",
]

app = typer.Typer(
    name="rekall",
    help="Knowledge management for developers",
    no_args_is_help=True,
)

# Enregistrement des commandes
app.command()(version)
app.command()(config)
app.command()(init)
app.command()(info)
app.command()(search)
app.command()(add)
app.command()(show)
app.command()(browse)
# ...

# Enregistrement des sous-apps
app.add_typer(sources_app, name="sources")
app.add_typer(inbox_app, name="inbox")
app.add_typer(staging_app, name="staging")
```

## Command Mapping

| Commande CLI | Fichier source | Fonction |
|--------------|----------------|----------|
| `rekall version` | core.py | `version()` |
| `rekall config [key] [value]` | core.py | `config()` |
| `rekall init` | core.py | `init()` |
| `rekall info` | core.py | `info()` |
| `rekall search <query>` | entries.py | `search()` |
| `rekall add <title>` | entries.py | `add()` |
| `rekall show <id>` | entries.py | `show()` |
| `rekall browse` | entries.py | `browse()` |
| `rekall review` | memory.py | `review()` |
| `rekall stale` | memory.py | `stale()` |
| `rekall link <from> <to>` | knowledge_graph.py | `link()` |
| `rekall graph` | knowledge_graph.py | `graph()` |
| `rekall export` | import_export.py | `export_cmd()` |
| `rekall research <query>` | research.py | `research()` |
| `rekall sources list` | sources.py | `sources_list()` |
| `rekall inbox add` | inbox.py | `inbox_add()` |
| `rekall staging promote` | staging.py | `staging_promote()` |
| `rekall backup` | system.py | `backup()` |
| `rekall mcp-server` | system.py | `mcp_server()` |

## Validation Criteria

- [ ] `rekall --help` liste toutes les commandes
- [ ] Chaque commande fonctionne identiquement
- [ ] `pytest tests/test_cli.py` passe à 100%
- [ ] Aucun fichier > 500 LOC
- [ ] `ruff check rekall/cli/` sans erreur
