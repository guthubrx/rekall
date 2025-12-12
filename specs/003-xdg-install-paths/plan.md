# Implementation Plan: XDG-Compliant Installation Paths

**Branch**: `003-xdg-install-paths` | **Date**: 2024-12-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-xdg-install-paths/spec.md`

## Summary

Refactoriser le module `config.py` de Rekall pour supporter les chemins XDG standard (`~/.config/rekall/`, `~/.local/share/rekall/`) au lieu du chemin legacy `~/.rekall/`. Implémenter la détection de projet local (`.rekall/`), les variables d'environnement (`REKALL_HOME`), la commande `rekall config --show`, et la migration automatique des anciennes installations.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: Click (CLI), pathlib (stdlib), platformdirs (nouveau - résolution XDG cross-platform)
**Storage**: SQLite (fichier `knowledge.db`)
**Testing**: pytest
**Target Platform**: Linux, macOS, Windows
**Project Type**: Single project (CLI tool)
**Performance Goals**: Résolution des chemins < 10ms
**Constraints**: Zero-config par défaut, rétrocompatibilité avec `~/.rekall/`
**Scale/Scope**: CLI local, usage développeur individuel ou équipe

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Règle | Statut | Notes |
|-------|--------|-------|
| I. Français | ✅ | Documentation en français |
| III. Process SpecKit | ✅ | Spec → Plan → Tasks → Implement |
| VII. ADR | ✅ | Décision XDG documentée dans spec |
| XV. Test-Before-Next | ✅ | Tests unitaires prévus |
| XVI. Worktree | ✅ | Worktree créé `.worktrees/003-xdg-install-paths/` |

**Résultat**: PASS - Aucune violation

## Project Structure

### Documentation (this feature)

```text
specs/003-xdg-install-paths/
├── plan.md              # Ce fichier
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
rekall/
├── __init__.py
├── __main__.py
├── cli.py               # Ajout commande `config --show`
├── config.py            # REFACTORING MAJEUR - Paths class
├── paths.py             # NOUVEAU - PathResolver class
├── db.py
├── models.py
├── tui.py
├── archive.py
├── sync.py
├── exporters.py
└── integrations/
    └── __init__.py

tests/
├── test_paths.py        # NOUVEAU - Tests PathResolver
├── test_config.py       # MISE À JOUR - Tests Config
└── test_migration.py    # NOUVEAU - Tests migration legacy
```

**Structure Decision**: Single project Python. Nouveau module `paths.py` pour isoler la logique de résolution des chemins. Le module `config.py` existant utilisera `PathResolver` pour obtenir les chemins.

## Phase 0: Research Technique

### Dépendances Évaluées

| Bibliothèque | Usage | Décision |
|--------------|-------|----------|
| `platformdirs` | XDG cross-platform | ✅ Utiliser - Standard Python, léger |
| `appdirs` | XDG (deprecated) | ❌ Remplacé par platformdirs |
| `xdg` | XDG Linux only | ❌ Pas cross-platform |

### Pattern de Résolution des Chemins

```python
# Ordre de priorité (spec FR-001 à FR-009)
1. CLI args (--db-path, --config-path)
2. Env vars (REKALL_HOME, REKALL_DB_PATH)
3. Local project (.rekall/ in cwd)
4. User config file
5. XDG env vars ($XDG_CONFIG_HOME, $XDG_DATA_HOME)
6. Platform defaults (platformdirs)
```

### Migration Strategy

- Détecter `~/.rekall/` existant au démarrage
- Prompt interactif pour migration (skip si --quiet)
- Copie des données (pas déplacement - safe)
- Option `--legacy` pour forcer l'ancien chemin

## Phase 1: Data Model

### PathResolver Class

```python
@dataclass
class ResolvedPaths:
    """Chemins résolus avec leur source."""
    config_dir: Path
    data_dir: Path
    cache_dir: Path
    db_path: Path
    source: str  # "cli" | "env" | "local" | "config" | "xdg" | "default"
    is_local_project: bool
```

### Config Updates

```python
@dataclass
class Config:
    """Configuration étendue avec chemins XDG."""
    # Existant
    editor: Optional[str] = None
    default_project: Optional[str] = None
    embeddings_provider: Optional[str] = None
    embeddings_model: Optional[str] = None

    # Nouveau - géré par PathResolver
    paths: ResolvedPaths = field(default_factory=PathResolver.resolve)

    @property
    def db_path(self) -> Path:
        """Rétrocompatibilité."""
        return self.paths.db_path
```

### CLI Extensions

```bash
# Nouvelle commande
rekall config --show

# Output exemple:
Configuration Rekall
────────────────────
Source: xdg (default)

Chemins:
  Config:  ~/.config/rekall/
  Data:    ~/.local/share/rekall/
  Cache:   ~/.cache/rekall/
  DB:      ~/.local/share/rekall/knowledge.db

Variables d'environnement:
  REKALL_HOME:    (not set)
  XDG_CONFIG_HOME: (not set)
  XDG_DATA_HOME:   (not set)

Projet local: Non détecté
```

## Quickstart

### Utilisation Standard (99% des cas)

```bash
# Rien à configurer - XDG par défaut
pip install rekall
rekall add bug "Mon premier bug"
# → DB créée dans ~/.local/share/rekall/knowledge.db
```

### Projet Local (équipe)

```bash
cd mon-projet/
rekall init --local
# → Crée .rekall/ dans le projet
git add .rekall/
git commit -m "Add Rekall knowledge base"
```

### Chemin Personnalisé

```bash
export REKALL_HOME=/mnt/nas/rekall
rekall add pattern "Pattern partagé"
```

### Voir la Configuration

```bash
rekall config --show
```

## Generated Artifacts

| Artifact | Status | Description |
|----------|--------|-------------|
| [spec.md](./spec.md) | ✅ | Spécification fonctionnelle (4 user stories, 9 FRs) |
| [research.md](./research.md) | ✅ | Recherche technique (platformdirs, patterns) |
| [data-model.md](./data-model.md) | ✅ | Structures de données (ResolvedPaths, PathSource) |
| [quickstart.md](./quickstart.md) | ✅ | Guide utilisateur rapide |
| [tasks.md](./tasks.md) | ✅ | 24 tâches, 7 phases, 8 parallélisables |

## Complexity Tracking

Aucune violation de la Constitution - pas de justification requise.
