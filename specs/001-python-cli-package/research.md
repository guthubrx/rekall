# Research Technique: DevKMS CLI

**Date**: 2025-12-07
**Phase**: 0 - Research

## Sources Consultées

### Sources Primaires
- [SQLite FTS5 Extension](https://www.sqlite.org/fts5.html) - Documentation officielle
- [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/) - Packaging best practices
- [Typer - Building a Package](https://typer.tiangolo.com/tutorial/package/) - CLI framework docs
- [Simon Willison - pyproject.toml](https://til.simonwillison.net/python/pyproject) - Practical guide
- [Charles Leifer - SQLite FTS with Python](https://charlesleifer.com/blog/using-sqlite-full-text-search-with-python/) - Implementation patterns

### Sources Secondaires
- [Real Python - pyproject.toml](https://realpython.com/python-pyproject-toml/) - Tutorial complet
- [Datasette FTS docs](https://docs.datasette.io/en/stable/full_text_search.html) - FTS5 patterns

---

## Décisions Techniques

### D1: Build System et Packaging

**Décision**: Utiliser `setuptools` avec `pyproject.toml` moderne (PEP 621)

**Rationale**:
- Standard Python officiel depuis PEP 621
- Compatible avec pip, uv, pipx sans configuration supplémentaire
- Plus simple que Poetry pour un CLI léger
- Support natif des entry points `[project.scripts]`

**Alternatives considérées**:
- Poetry : Plus lourd, lock file inutile pour un CLI
- Hatchling : Moins répandu, documentation plus sparse
- Flit : Trop minimaliste, manque de flexibilité

**Configuration retenue**:
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "devkms"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["typer>=0.12.0", "rich>=13.0.0"]

[project.scripts]
mem = "devkms.cli:app"
```

---

### D2: Structure du Package

**Décision**: Layout flat (package à la racine, pas de `src/`)

**Rationale**:
- Plus simple pour un projet de cette taille
- Pas de confusion avec imports relatifs
- Convention utilisée par typer, click, rich eux-mêmes

**Alternatives considérées**:
- `src/` layout : Recommandé pour bibliothèques, overkill ici
- Single file : Pas assez modulaire pour nos besoins

**Structure finale**:
```
devkms/
├── __init__.py
├── __main__.py      # Pour `python -m devkms`
├── cli.py           # Commandes typer
├── db.py            # SQLite + FTS5
├── models.py        # Dataclasses
├── config.py        # Paths, settings
├── exporters.py     # Export formats
└── integrations/    # Templates IDE
```

---

### D3: SQLite FTS5 Configuration

**Décision**: Tokenizer `porter unicode61` avec table virtuelle FTS5

**Rationale**:
- `porter` : Stemming pour recherche flexible (running → run)
- `unicode61` : Support multilingue (français, accents)
- Combinaison recommandée par documentation SQLite

**Configuration retenue**:
```sql
CREATE VIRTUAL TABLE entries_fts USING fts5(
    title,
    content,
    tags,
    tokenize = 'porter unicode61'
);
```

**Alternatives considérées**:
- Trigram : Trop lent pour > 1000 entrées
- unicode61 seul : Pas de stemming, recherche trop stricte
- Whoosh/Tantivy : Dépendances externes, overkill

---

### D4: Identifiants des Entrées

**Décision**: ULID (Universally Unique Lexicographically Sortable Identifier)

**Rationale**:
- Triable chronologiquement (préfixe timestamp)
- Plus court que UUID (26 chars vs 36)
- Collision-free sans coordination
- Implémentable en Python pur (pas de dépendance)

**Implémentation**:
```python
import time
import secrets
import string

ENCODING = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

def generate_ulid() -> str:
    timestamp = int(time.time() * 1000)
    time_part = ""
    for _ in range(10):
        time_part = ENCODING[timestamp % 32] + time_part
        timestamp //= 32
    random_part = "".join(secrets.choice(ENCODING) for _ in range(16))
    return time_part + random_part
```

**Alternatives considérées**:
- UUID4 : Pas triable, plus long
- Auto-increment : Pas portable entre bases
- Snowflake : Nécessite machine ID, complexe

---

### D5: Mode WAL pour Concurrence

**Décision**: Activer WAL mode par défaut

**Rationale**:
- Permet lectures pendant écriture
- Meilleure performance pour pattern read-heavy
- Récupération crash plus robuste
- Standard pour SQLite moderne

**Configuration**:
```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
```

**Alternatives considérées**:
- DELETE mode (default) : Moins performant, bloque les reads
- MEMORY : Perte de données en cas de crash

---

### D6: Détection de Données Sensibles (FR-013)

**Décision**: Regex patterns pour API keys, passwords, tokens

**Rationale**:
- Détection heuristique suffisante pour avertissement
- Pas de faux négatifs critiques (mieux vaut trop que pas assez)
- Pas de dépendance externe

**Patterns retenus**:
```python
SENSITIVE_PATTERNS = [
    r'(?i)(api[_-]?key|apikey)\s*[=:]\s*[\'"]?[\w-]{20,}',
    r'(?i)(password|passwd|pwd)\s*[=:]\s*[\'"]?[^\s]{8,}',
    r'(?i)(secret|token)\s*[=:]\s*[\'"]?[\w-]{20,}',
    r'(?i)(bearer|authorization)\s+[\w-]{20,}',
    r'sk-[a-zA-Z0-9]{20,}',  # OpenAI
    r'ghp_[a-zA-Z0-9]{36}',  # GitHub
]
```

---

### D7: Stratégie de Tests

**Décision**: Pytest avec fixtures SQLite in-memory

**Rationale**:
- Pytest = standard Python, bien supporté
- In-memory DB = tests rapides, isolation parfaite
- Pas besoin de mocks complexes

**Structure tests**:
```
tests/
├── conftest.py          # Fixtures (db, entries)
├── test_cli.py          # Tests commandes (CliRunner)
├── test_db.py           # Tests FTS5, CRUD
├── test_models.py       # Tests validation
├── test_exporters.py    # Tests formats export
└── test_integrations.py # Tests génération templates
```

**Alternatives considérées**:
- unittest : Plus verbeux, moins moderne
- nose2 : Moins maintenu

---

### D8: Intégrations IDE - Approche Template

**Décision**: Fichiers templates générés par `mem install <ide>`

**Rationale**:
- Un fichier par IDE, contenu adapté
- Installation one-command (SC-005)
- Pas de complexité runtime

**Mapping IDE → Fichier**:
| IDE | Fichier cible | Type |
|-----|---------------|------|
| Claude Code | `.claude-plugin/skills/*.md` | Skills |
| Cursor | `.cursorrules` ou `~/.cursor/rules/*.md` | Rules |
| GitHub Copilot | `.github/copilot-instructions.md` | Instructions |
| Windsurf | `.windsurfrules` | Rules |
| Cline | `.clinerules` | Rules |
| Aider | `CONVENTIONS.md` | Conventions |
| Continue.dev | `.continue/rules/*.md` | Rules |
| Zed | `.rules` | Rules |

---

## Red Flags Identifiés

Aucun red flag majeur :
- ✅ FTS5 est stable et bien documenté (SQLite core depuis 3.9.0)
- ✅ Typer/Rich sont matures (> 5 ans, millions de downloads)
- ✅ Architecture simple, pas de framework complexe
- ✅ Pas de vendor lock-in

---

## Prochaines Étapes

Phase 1 : Design
- [ ] data-model.md : Schéma SQLite détaillé
- [ ] quickstart.md : Guide installation
- [ ] Pas de contracts/ (CLI, pas d'API REST)
