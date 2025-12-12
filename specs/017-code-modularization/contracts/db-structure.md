# Contract: Database Module Structure

**Feature**: 017-code-modularization
**Component**: rekall/infra/db/
**Date**: 2025-12-12

## Overview

Réorganisation de `db.py` (4502 LOC, 150+ méthodes dans une classe) en repositories spécialisés.

## Target Structure

```
rekall/infra/
├── __init__.py              # Exports infra (~10 LOC)
└── db/
    ├── __init__.py          # Database class + exports (~150 LOC)
    ├── connection.py        # Connexion, migrations (~300 LOC)
    ├── entries_repo.py      # CRUD entries, FTS (~400 LOC)
    ├── access_tracking.py   # Spaced repetition, review (~150 LOC)
    ├── knowledge_graph.py   # Links, graph rendering (~250 LOC)
    ├── embeddings_repo.py   # Vectors, similarity (~200 LOC)
    ├── suggestions_repo.py  # IA suggestions (~150 LOC)
    ├── context_repo.py      # Context storage (~250 LOC)
    ├── sources_repo.py      # CRUD sources (~300 LOC)
    ├── source_scoring.py    # Calculs scores (~300 LOC)
    ├── source_filtering.py  # Recherche avancée (~300 LOC)
    ├── source_promotion.py  # Promotion/demotion (~300 LOC)
    ├── inbox_repo.py        # Inbox entries (~150 LOC)
    ├── staging_repo.py      # Staging entries (~150 LOC)
    └── filters_repo.py      # Saved filters (~100 LOC)
```

**Total estimé**: ~3,500 LOC (vs 4,502 actuel - réduction via utils partagés)

## Repository Contracts

### connection.py

```python
"""Gestion de la connexion et des migrations."""

import sqlite3
from pathlib import Path

__all__ = ["create_connection", "get_schema_version", "migrate_schema", "DatabaseError", "MigrationError"]

class DatabaseError(Exception):
    """Erreur générique de base de données."""
    pass

class MigrationError(DatabaseError):
    """Erreur lors d'une migration."""
    pass

def create_connection(db_path: Path) -> sqlite3.Connection:
    """Crée une connexion SQLite avec configuration optimale."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def get_schema_version(conn: sqlite3.Connection) -> int:
    """Retourne la version du schéma actuel."""
    ...

def migrate_schema(conn: sqlite3.Connection, target_version: int | None = None) -> None:
    """Applique les migrations jusqu'à target_version."""
    ...
```

### entries_repo.py

```python
"""Repository pour les entrées knowledge base."""

import sqlite3
from rekall.models import Entry

__all__ = ["EntriesRepository"]

class EntriesRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, title: str, url: str | None = None, **kwargs) -> int:
        """Ajoute une entrée et retourne son ID."""
        ...

    def get(self, id: int) -> Entry | None:
        """Récupère une entrée par ID."""
        ...

    def update(self, id: int, **kwargs) -> bool:
        """Met à jour une entrée."""
        ...

    def delete(self, id: int) -> bool:
        """Supprime une entrée."""
        ...

    def list_all(self, limit: int = 100, offset: int = 0) -> list[Entry]:
        """Liste toutes les entrées avec pagination."""
        ...

    def search(self, query: str, limit: int = 20) -> list[Entry]:
        """Recherche full-text dans les entrées."""
        ...

    def search_by_keywords(self, keywords: list[str]) -> list[Entry]:
        """Recherche par mots-clés."""
        ...
```

### sources_repo.py

```python
"""Repository pour les sources curées."""

import sqlite3
from rekall.models import Source

__all__ = ["SourcesRepository"]

class SourcesRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, url: str, title: str | None = None, **kwargs) -> int:
        """Ajoute une source."""
        ...

    def get(self, id: int) -> Source | None:
        """Récupère une source par ID."""
        ...

    def get_by_domain(self, domain: str) -> Source | None:
        """Récupère une source par domaine."""
        ...

    def update(self, id: int, **kwargs) -> bool:
        """Met à jour une source."""
        ...

    def delete(self, id: int) -> bool:
        """Supprime une source."""
        ...

    def list(
        self,
        theme: str | None = None,
        tier: str | None = None,
        limit: int = 100,
    ) -> list[Source]:
        """Liste les sources avec filtres."""
        ...

    def link_entry(self, source_id: int, entry_id: int) -> bool:
        """Lie une entrée à une source."""
        ...

    def unlink_entry(self, source_id: int, entry_id: int) -> bool:
        """Délie une entrée d'une source."""
        ...

    def get_entry_sources(self, entry_id: int) -> list[Source]:
        """Récupère les sources d'une entrée."""
        ...
```

### __init__.py

```python
"""
Database Rekall - Couche d'accès aux données.

Usage:
    from rekall.infra.db import Database
    db = Database()
    entry = db.entries.add(title="Test")
"""

import sqlite3
from pathlib import Path
from rekall.infra.db.connection import create_connection, migrate_schema
from rekall.infra.db.entries_repo import EntriesRepository
from rekall.infra.db.sources_repo import SourcesRepository
from rekall.infra.db.embeddings_repo import EmbeddingsRepository
from rekall.infra.db.knowledge_graph import KnowledgeGraphRepository
from rekall.infra.db.access_tracking import AccessTrackingRepository
from rekall.infra.db.suggestions_repo import SuggestionsRepository
from rekall.infra.db.context_repo import ContextRepository
from rekall.infra.db.source_scoring import SourceScoringMixin
from rekall.infra.db.source_filtering import SourceFilteringMixin
from rekall.infra.db.source_promotion import SourcePromotionMixin
from rekall.infra.db.inbox_repo import InboxRepository
from rekall.infra.db.staging_repo import StagingRepository
from rekall.infra.db.filters_repo import FiltersRepository

__all__ = [
    "Database",
    "DatabaseError",
    "MigrationError",
    "EntriesRepository",
    "SourcesRepository",
    # ... autres exports
]

class Database:
    """Classe principale d'accès à la base de données."""

    def __init__(self, path: Path | None = None):
        from rekall.config import get_config
        if path is None:
            path = get_config().db_path
        self.path = path
        self.conn = create_connection(path)
        migrate_schema(self.conn)

        # Repositories
        self.entries = EntriesRepository(self.conn)
        self.sources = SourcesRepository(self.conn)
        self.embeddings = EmbeddingsRepository(self.conn)
        self.knowledge_graph = KnowledgeGraphRepository(self.conn)
        self.access_tracking = AccessTrackingRepository(self.conn)
        self.suggestions = SuggestionsRepository(self.conn)
        self.context = ContextRepository(self.conn)
        self.inbox = InboxRepository(self.conn)
        self.staging = StagingRepository(self.conn)
        self.filters = FiltersRepository(self.conn)

    # ========== MÉTHODES DE COMPATIBILITÉ ==========
    # Ces méthodes délèguent aux repositories pour compatibilité

    def add(self, **kwargs) -> int:
        """COMPAT: Délègue à entries.add()"""
        return self.entries.add(**kwargs)

    def get(self, id: int):
        """COMPAT: Délègue à entries.get()"""
        return self.entries.get(id)

    def search(self, query: str, **kwargs):
        """COMPAT: Délègue à entries.search()"""
        return self.entries.search(query, **kwargs)

    def add_source(self, **kwargs) -> int:
        """COMPAT: Délègue à sources.add()"""
        return self.sources.add(**kwargs)

    def get_source(self, id: int):
        """COMPAT: Délègue à sources.get()"""
        return self.sources.get(id)

    # ... autres méthodes de compatibilité
```

## Method Mapping

| Méthode actuelle | Repository | Nouvelle méthode |
|------------------|------------|------------------|
| `db.add()` | entries | `db.entries.add()` |
| `db.get()` | entries | `db.entries.get()` |
| `db.search()` | entries | `db.entries.search()` |
| `db.delete()` | entries | `db.entries.delete()` |
| `db.add_link()` | knowledge_graph | `db.knowledge_graph.add_link()` |
| `db.get_links()` | knowledge_graph | `db.knowledge_graph.get_links()` |
| `db.render_graph_ascii()` | knowledge_graph | `db.knowledge_graph.render_ascii()` |
| `db.add_embedding()` | embeddings | `db.embeddings.add()` |
| `db.get_embedding()` | embeddings | `db.embeddings.get()` |
| `db.add_source()` | sources | `db.sources.add()` |
| `db.get_source()` | sources | `db.sources.get()` |
| `db.list_sources()` | sources | `db.sources.list()` |
| `db.calculate_source_score()` | source_scoring | `db.calculate_source_score()` |
| `db.promote_source()` | source_promotion | `db.promote_source()` |
| `db.add_inbox_entry()` | inbox | `db.inbox.add()` |
| `db.get_inbox_entries()` | inbox | `db.inbox.list()` |
| `db.add_staging_entry()` | staging | `db.staging.add()` |

## Validation Criteria

- [ ] `from rekall.db import Database` fonctionne (façade)
- [ ] Toutes les méthodes de compatibilité fonctionnent
- [ ] `pytest tests/test_db.py` passe à 100%
- [ ] Chaque repository testable indépendamment
- [ ] Aucun fichier > 500 LOC
- [ ] `ruff check rekall/infra/` sans erreur
