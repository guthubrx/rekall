# Data Model: Module Dependencies & Exports

**Feature**: 017-code-modularization
**Date**: 2025-12-12
**Phase**: 1 - Design

## Vue d'Ensemble des Dépendances

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
├──────────────────────────────┬──────────────────────────────────┤
│        rekall/cli/           │          rekall/ui/              │
│  (Typer commands)            │  (Textual screens/widgets)       │
└──────────────┬───────────────┴────────────────┬─────────────────┘
               │                                 │
               ▼                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER                            │
│                       rekall/services/                           │
│  entries.py | sources.py | (réutilise: promotion.py, etc.)      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                        │
│                       rekall/infra/db/                           │
│  connection | entries_repo | sources_repo | embeddings_repo     │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                             │
│  rekall/models.py | rekall/config.py | rekall/constants.py      │
└─────────────────────────────────────────────────────────────────┘
```

## Règles de Dépendance

| Couche | Peut importer | Ne peut PAS importer |
|--------|---------------|---------------------|
| cli/ | services/, infra/db/, models, config | ui/ |
| ui/ | services/, infra/db/, models, config | cli/ |
| services/ | infra/db/, models, config | cli/, ui/ |
| infra/db/ | models, config, utils | cli/, ui/, services/ |
| models | config, constants | Rien d'autre |

## Exports par Package

### rekall/cli/__init__.py

```python
# Public API
__all__ = [
    # App principale
    "app",
    # Commandes core
    "version", "config", "init", "info",
    # Commandes entries
    "search", "add", "show", "browse", "deprecate",
    # Commandes memory
    "review", "stale", "generalize",
    # Commandes knowledge graph
    "link", "unlink", "related", "graph",
    # Commandes import/export
    "export_cmd", "import_archive",
    # Commandes research
    "research", "similar", "suggest",
    # Sub-apps
    "sources_app", "inbox_app", "staging_app",
    # Commandes système
    "backup", "restore", "migrate", "embeddings_cmd", "mcp_server",
]

# Type exports
from rekall.cli.helpers import get_db

# Typer app
from typer import Typer
app = Typer()
```

### rekall/infra/db/__init__.py

```python
# Public API
__all__ = [
    # Classe principale
    "Database",
    # Repositories (pour tests)
    "EntriesRepository",
    "SourcesRepository",
    "EmbeddingsRepository",
    "SuggestionsRepository",
    "ContextRepository",
    "InboxRepository",
    "StagingRepository",
    "FiltersRepository",
    # Exceptions
    "DatabaseError",
    "MigrationError",
]

from rekall.infra.db.connection import Database, DatabaseError, MigrationError
from rekall.infra.db.entries_repo import EntriesRepository
from rekall.infra.db.sources_repo import SourcesRepository
# ... autres repos
```

### rekall/ui/__init__.py

```python
# Public API
__all__ = [
    # Fonction principale
    "run_tui",
    # Apps (pour customisation)
    "RekallMenuApp",
    "BrowseApp",
    "ResearchApp",
    "SourcesBrowseApp",
    # Widgets réutilisables
    "MenuItem",
    "MenuListView",
    "EntryDetailPanel",
    "SearchBar",
    # Theme
    "BANNER",
    "REKALL_CSS",
]

from rekall.ui.app import run_tui, RekallMenuApp
from rekall.ui.screens.browse import BrowseApp
# ... autres exports
```

### rekall/services/__init__.py

```python
# Public API
__all__ = [
    "EntryService",
    "SourceService",
    # Réexports des modules existants
    "PromotionService",
    "EmbeddingService",
]

from rekall.services.entries import EntryService
from rekall.services.sources import SourceService
# Réexports
from rekall.promotion import PromotionService
from rekall.embeddings import get_embedding_service as EmbeddingService
```

## Fichiers Façade (Compatibilité)

### rekall/cli.py (FAÇADE)

```python
"""
Façade de compatibilité pour les anciens imports.
Déprécié: utiliser `from rekall.cli import ...` à la place.
"""
from rekall.cli import *  # noqa: F401, F403
from rekall.cli import app, get_db

# Compatibilité totale - tous les anciens imports fonctionnent
```

### rekall/db.py (FAÇADE)

```python
"""
Façade de compatibilité pour les anciens imports.
Déprécié: utiliser `from rekall.infra.db import ...` à la place.
"""
from rekall.infra.db import *  # noqa: F401, F403
from rekall.infra.db import Database

# Compatibilité totale - `from rekall.db import Database` fonctionne
```

### rekall/tui.py (FAÇADE)

```python
"""
Façade de compatibilité pour les anciens imports.
Déprécié: utiliser `from rekall.ui import ...` à la place.
"""
from rekall.ui import *  # noqa: F401, F403
from rekall.ui import run_tui

# Compatibilité totale - `from rekall.tui import run_tui` fonctionne
```

## Mapping Méthodes Database → Repositories

| Méthode actuelle db.py | Repository cible | Méthode |
|------------------------|------------------|---------|
| `db.add()` | `entries_repo` | `add()` |
| `db.get()` | `entries_repo` | `get()` |
| `db.search()` | `entries_repo` | `search()` |
| `db.add_link()` | `knowledge_graph` | `add_link()` |
| `db.get_related_entries()` | `knowledge_graph` | `get_related()` |
| `db.add_embedding()` | `embeddings_repo` | `add()` |
| `db.get_embedding()` | `embeddings_repo` | `get()` |
| `db.add_source()` | `sources_repo` | `add()` |
| `db.get_source()` | `sources_repo` | `get()` |
| `db.calculate_source_score()` | `source_scoring` | `calculate()` |
| `db.promote_source()` | `source_promotion` | `promote()` |
| `db.add_inbox_entry()` | `inbox_repo` | `add()` |
| `db.add_staging_entry()` | `staging_repo` | `add()` |

## Mapping Commandes CLI → Modules

| Commande actuelle | Module cible | Fonction |
|-------------------|--------------|----------|
| `rekall version` | `cli/core.py` | `version()` |
| `rekall config` | `cli/core.py` | `config()` |
| `rekall search` | `cli/entries.py` | `search()` |
| `rekall add` | `cli/entries.py` | `add()` |
| `rekall link` | `cli/knowledge_graph.py` | `link()` |
| `rekall review` | `cli/memory.py` | `review()` |
| `rekall sources list` | `cli/sources.py` | `sources_list()` |
| `rekall inbox add` | `cli/inbox.py` | `inbox_add()` |
| `rekall staging promote` | `cli/staging.py` | `staging_promote()` |
| `rekall backup` | `cli/system.py` | `backup()` |

## Mapping Classes TUI → Modules

| Classe actuelle | Module cible | Nom |
|-----------------|--------------|-----|
| `RekallMenuApp` | `ui/app.py` | `RekallMenuApp` |
| `BrowseApp` | `ui/screens/browse.py` | `BrowseApp` |
| `ResearchApp` | `ui/screens/research.py` | `ResearchApp` |
| `SourcesBrowseApp` | `ui/screens/sources.py` | `SourcesBrowseApp` |
| `InboxBrowseApp` | `ui/screens/inbox.py` | `InboxBrowseApp` |
| `StagingBrowseApp` | `ui/screens/staging.py` | `StagingBrowseApp` |
| `MCPConfigApp` | `ui/screens/config.py` | `MCPConfigApp` |
| `MenuItem` | `ui/widgets/menu.py` | `MenuItem` |
| `MenuListView` | `ui/widgets/menu.py` | `MenuListView` |
