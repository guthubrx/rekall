# Research: Code Modularization Patterns

**Feature**: 017-code-modularization
**Date**: 2025-12-12
**Phase**: 0 - Research

## Contexte

Refactoring de trois fichiers monolithiques Python :
- `cli.py` : 4643 LOC, 55 commandes Typer
- `db.py` : 4502 LOC, 150+ méthodes dans une seule classe
- `tui.py` : 7872 LOC, 14 classes Textual + 100+ handlers

## Patterns de Modularisation Python

### 1. Package avec `__init__.py` comme Façade

**Pattern recommandé pour ce projet.**

```python
# rekall/cli/__init__.py
from rekall.cli.core import version, config, init
from rekall.cli.entries import search, add, show
from rekall.cli.sources import sources_app

# Re-export pour compatibilité
__all__ = ["version", "config", "init", "search", "add", "show", "sources_app"]

# App principale
app = typer.Typer()
app.add_typer(sources_app, name="sources")
```

**Avantages** :
- Import simple : `from rekall.cli import search`
- Compatibilité descendante préservée
- Organisation interne cachée aux consommateurs

### 2. Lazy Loading pour Performance

**Pattern recommandé pour éviter régression temps de démarrage.**

```python
# rekall/cli/__init__.py
def __getattr__(name):
    if name == "sources_app":
        from rekall.cli.sources import sources_app
        return sources_app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

**Avantages** :
- Import initial rapide
- Sous-modules chargés seulement si utilisés
- Compatible Python 3.7+

### 3. Repository Pattern pour Database

**Pattern recommandé pour db.py.**

```python
# rekall/infra/db/entries_repo.py
class EntriesRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add(self, entry: Entry) -> int: ...
    def get(self, id: int) -> Entry | None: ...
    def search(self, query: str) -> list[Entry]: ...

# rekall/infra/db/__init__.py
class Database:
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(path)
        self.entries = EntriesRepository(self.conn)
        self.sources = SourcesRepository(self.conn)
        # ...
```

**Avantages** :
- Méthodes groupées par entité
- Testabilité unitaire par repository
- Single Responsibility Principle

### 4. Mixins pour Classe Database Existante

**Pattern alternatif si restructuration complète trop risquée.**

```python
# rekall/infra/db/mixins/entries.py
class EntriesMixin:
    def add_entry(self, entry: Entry) -> int: ...
    def get_entry(self, id: int) -> Entry | None: ...

# rekall/infra/db/__init__.py
class Database(EntriesMixin, SourcesMixin, EmbeddingsMixin):
    def __init__(self, path: Path):
        self.conn = sqlite3.connect(path)
```

**Avantages** :
- Migration plus douce
- API externe identique
- Composition vs héritage

**Inconvénients** :
- Moins clair que repositories
- Résolution ordre méthodes (MRO) complexe

### 5. Screens et Widgets Textual

**Pattern natif Textual recommandé pour tui.py.**

```python
# rekall/ui/screens/browse.py
class BrowseScreen(Screen):
    BINDINGS = [("q", "quit", "Quit")]

    def compose(self) -> ComposeResult:
        yield Header()
        yield EntryListWidget()
        yield Footer()

# rekall/ui/widgets/entry_list.py
class EntryListWidget(Widget):
    def on_mount(self) -> None: ...
    def on_key(self, event: Key) -> None: ...
```

**Avantages** :
- Pattern officiel Textual
- CSS-in-file pour styling
- Réutilisabilité widgets

## Gestion des Imports Circulaires

### Technique 1: TYPE_CHECKING Guard

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rekall.infra.db import Database

def get_entries(db: "Database") -> list[Entry]: ...
```

### Technique 2: Import Local

```python
def search(query: str) -> list[Entry]:
    from rekall.infra.db import Database
    db = Database()
    return db.entries.search(query)
```

### Technique 3: Injection de Dépendance

```python
# Préféré pour testabilité
class EntryService:
    def __init__(self, db: Database):
        self.db = db

    def search(self, query: str) -> list[Entry]:
        return self.db.entries.search(query)
```

## Ordre de Migration Recommandé

### 1. DB First (US2)

**Rationale** :
- db.py est indépendant (pas d'import de cli/tui)
- Foundation pour CLI et TUI
- Tests existants nombreux (test_db.py: 3789 LOC)

**Étapes** :
1. Créer `rekall/infra/db/` avec `__init__.py`
2. Extraire `connection.py` (migrations, schema)
3. Extraire `entries_repo.py` (CRUD entries)
4. Extraire autres repositories un par un
5. `db.py` devient façade importation

### 2. CLI Second (US1)

**Rationale** :
- Dépend de DB (déjà modularisé)
- Commandes clairement groupées
- Tests existants (test_cli.py: 926 LOC)

**Étapes** :
1. Créer `rekall/cli/` avec `__init__.py`
2. Extraire `helpers.py` (get_db, decorators)
3. Extraire commandes par groupe
4. `cli.py` devient façade importation

### 3. TUI Third (US3)

**Rationale** :
- Plus gros fichier mais isolé
- Dépend de DB (déjà modularisé)
- Moins de tests existants (test_tui.py: 344 LOC)

**Étapes** :
1. Créer `rekall/ui/` avec screens/ et widgets/
2. Extraire widgets réutilisables d'abord
3. Extraire screens avec leurs handlers
4. `tui.py` devient façade importation

### 4. Services Layer (US4)

**Rationale** :
- Découple logique métier de CLI/TUI
- Réutilise modules existants (promotion.py, embeddings.py)
- Optionnel si temps contraint

## Tools et Vérifications

### Détection Imports Circulaires

```bash
# ruff vérifie automatiquement (I001)
uv run ruff check rekall/ --select=I

# ou avec pydeps pour visualisation
pip install pydeps
pydeps rekall --cluster --max-bacon 2
```

### Vérification Compatibilité Imports

```python
# test_imports_compat.py
def test_old_imports_work():
    # Ancien style (doit continuer à fonctionner)
    from rekall.cli import search, add, show
    from rekall.db import Database
    from rekall.tui import run_tui

    assert callable(search)
    assert callable(Database)
    assert callable(run_tui)
```

### Mesure LOC par Module

```bash
# Vérifier qu'aucun module ne dépasse 500 LOC
find rekall -name "*.py" -exec wc -l {} + | sort -n
```

## Références

- [Python Package Structure](https://docs.python.org/3/tutorial/modules.html#packages)
- [Textual Screens Guide](https://textual.textualize.io/guide/screens/)
- [Repository Pattern in Python](https://www.cosmicpython.com/book/chapter_02_repository.html)
- [Lazy Loading Modules PEP 562](https://peps.python.org/pep-0562/)

## Conclusion

**Approche recommandée** :
1. Repository pattern pour DB
2. Package avec façade pour CLI
3. Screens/Widgets natifs pour TUI
4. Lazy loading pour performance
5. TYPE_CHECKING pour éviter circulaires

**Risque principal** : Imports circulaires → Mitigation par injection de dépendance et guards TYPE_CHECKING.
