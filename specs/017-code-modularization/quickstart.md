# Quickstart: Migration des Imports

**Feature**: 017-code-modularization
**Date**: 2025-12-12
**Phase**: 1 - Design

## TL;DR

**Aucune action requise**. Les anciens imports continuent de fonctionner grâce aux fichiers façade.

```python
# ✅ Continue de fonctionner (façade)
from rekall.db import Database
from rekall.cli import search, add
from rekall.tui import run_tui

# ✅ Nouvelle syntaxe (recommandée)
from rekall.infra.db import Database
from rekall.cli import search, add  # Identique
from rekall.ui import run_tui
```

## Pour les Développeurs

### Avant le Refactoring

```python
# Ancien code
from rekall.db import Database
from rekall.cli import search, add, show
from rekall.tui import run_tui, BrowseApp

db = Database()
entry = db.add(title="Test", url="https://example.com")
results = db.search("test")
```

### Après le Refactoring

```python
# Même code - fonctionne toujours !
from rekall.db import Database  # Façade vers rekall.infra.db
from rekall.cli import search, add, show
from rekall.tui import run_tui, BrowseApp

db = Database()
entry = db.add(title="Test", url="https://example.com")
results = db.search("test")
```

### Nouvelle Syntaxe (Optionnelle)

```python
# Nouvelle syntaxe explicite
from rekall.infra.db import Database, EntriesRepository
from rekall.cli.entries import search, add
from rekall.ui.screens.browse import BrowseApp

# Accès aux repositories (nouveau)
db = Database()
entry = db.entries.add(title="Test", url="https://example.com")
results = db.entries.search("test")
```

## Changements pour les Tests

### Tests Existants

**Aucun changement requis**. Les mocks et fixtures existants continuent de fonctionner.

```python
# test_cli.py - INCHANGÉ
from rekall.cli import search
from rekall.db import Database

def test_search(mock_db):
    # Fonctionne toujours
    results = search("test")
    assert len(results) > 0
```

### Nouveaux Tests (Recommandé)

```python
# tests/db/test_entries_repo.py
from rekall.infra.db.entries_repo import EntriesRepository

def test_entries_add(connection):
    repo = EntriesRepository(connection)
    entry_id = repo.add(title="Test", url="https://example.com")
    assert entry_id > 0
```

## Structure des Fichiers

### Avant

```
rekall/
├── cli.py              # 4643 LOC - Toutes les commandes
├── db.py               # 4502 LOC - Toutes les opérations DB
└── tui.py              # 7872 LOC - Toute l'interface TUI
```

### Après

```
rekall/
├── cli.py              # ~10 LOC - Façade (from rekall.cli import *)
├── db.py               # ~10 LOC - Façade (from rekall.infra.db import *)
├── tui.py              # ~10 LOC - Façade (from rekall.ui import *)
├── cli/
│   ├── __init__.py     # Exports publics
│   ├── core.py         # ~150 LOC
│   ├── entries.py      # ~400 LOC
│   └── ...
├── infra/db/
│   ├── __init__.py     # Database class + exports
│   ├── connection.py   # ~300 LOC
│   ├── entries_repo.py # ~400 LOC
│   └── ...
└── ui/
    ├── __init__.py     # run_tui() + exports
    ├── app.py          # ~400 LOC
    ├── screens/
    └── widgets/
```

## FAQ

### Q: Dois-je mettre à jour mes imports ?

**R**: Non. Les fichiers façade (`cli.py`, `db.py`, `tui.py`) ré-exportent tout. Vos imports existants fonctionnent.

### Q: Puis-je utiliser les nouveaux chemins ?

**R**: Oui. `from rekall.infra.db import Database` est équivalent à `from rekall.db import Database`.

### Q: Les méthodes de Database changent-elles ?

**R**: Non. `db.add()`, `db.search()`, etc. fonctionnent identiquement. Les repositories sont accessibles en plus via `db.entries`, `db.sources`, etc.

### Q: Comment tester un repository isolément ?

**R**:
```python
from rekall.infra.db.entries_repo import EntriesRepository
repo = EntriesRepository(connection)
repo.add(...)
```

### Q: Que faire si j'ai un import qui ne fonctionne plus ?

**R**: C'est un bug. Ouvrir une issue avec l'import exact. Tous les imports publics doivent continuer à fonctionner.

## Vérification

Après modularisation, exécuter :

```bash
# Vérifier que les anciens imports fonctionnent
python -c "from rekall.db import Database; print('✅ db.py facade OK')"
python -c "from rekall.cli import search; print('✅ cli.py facade OK')"
python -c "from rekall.tui import run_tui; print('✅ tui.py facade OK')"

# Vérifier les nouveaux imports
python -c "from rekall.infra.db import Database; print('✅ infra/db OK')"
python -c "from rekall.cli.entries import search; print('✅ cli/entries OK')"
python -c "from rekall.ui import run_tui; print('✅ ui OK')"

# Exécuter tous les tests
uv run pytest -q
```
