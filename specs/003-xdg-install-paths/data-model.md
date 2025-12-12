# Data Model: XDG-Compliant Installation Paths

**Feature**: 003-xdg-install-paths
**Date**: 2024-12-07

## Core Data Structures

### ResolvedPaths

Structure principale contenant tous les chemins résolus avec leur source.

```python
@dataclass
class ResolvedPaths:
    """Chemins résolus avec métadonnées de source."""

    config_dir: Path
    """Répertoire de configuration (config.toml, etc.)
    Ex: ~/.config/rekall/ ou .rekall/"""

    data_dir: Path
    """Répertoire de données (knowledge.db, etc.)
    Ex: ~/.local/share/rekall/ ou .rekall/"""

    cache_dir: Path
    """Répertoire de cache (index temporaires, etc.)
    Ex: ~/.cache/rekall/"""

    db_path: Path
    """Chemin complet vers knowledge.db
    Dérivé: data_dir / "knowledge.db" """

    source: PathSource
    """Source ayant déterminé ces chemins"""

    is_local_project: bool
    """True si utilise .rekall/ local"""
```

### PathSource

Énumération des sources possibles pour la résolution des chemins.

```python
class PathSource(Enum):
    """Source de résolution des chemins, par ordre de priorité."""

    CLI = "cli"           # --db-path, --config-path
    ENV = "env"           # REKALL_HOME, REKALL_DB_PATH
    LOCAL = "local"       # .rekall/ dans dossier courant
    CONFIG = "config"     # data_dir dans config.toml
    XDG = "xdg"           # $XDG_CONFIG_HOME, $XDG_DATA_HOME
    DEFAULT = "default"   # platformdirs (défaut plateforme)
```

### Config (mise à jour)

Extension de la configuration existante pour intégrer les chemins.

```python
@dataclass
class Config:
    """Configuration Rekall étendue."""

    # Existant
    editor: Optional[str] = None
    default_project: Optional[str] = None
    embeddings_provider: Optional[str] = None
    embeddings_model: Optional[str] = None

    # Nouveau - chemins personnalisés (optionnel)
    data_dir: Optional[Path] = None
    """Override du répertoire data (dans config.toml)"""

    # Résolu au runtime
    paths: ResolvedPaths = field(default_factory=lambda: None)
    """Chemins résolus (calculé, pas stocké)"""
```

## File Formats

### config.toml (User Config)

```toml
# ~/.config/rekall/config.toml

# Chemins personnalisés (optionnel - override défauts)
data_dir = "/mnt/nas/rekall"

# Préférences existantes
editor = "vim"
default_project = "mon-projet"

# Embeddings (existant)
embeddings_provider = "ollama"
embeddings_model = "nomic-embed-text"
```

### config.toml (Project Local)

```toml
# .rekall/config.toml

# Config spécifique projet (override config globale)
default_project = "team-knowledge"

# Note: data_dir ignoré en mode local
# (la DB est toujours .rekall/knowledge.db)
```

## Resolution Flow

```
┌─────────────────────────────────────────────────────────┐
│                    PathResolver.resolve()                │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. CLI args?  ──yes──> ResolvedPaths(source=CLI)       │
│       │                                                  │
│       no                                                 │
│       ↓                                                  │
│  2. REKALL_HOME/REKALL_DB_PATH?  ──yes──> source=ENV    │
│       │                                                  │
│       no                                                 │
│       ↓                                                  │
│  3. .rekall/ exists in cwd?  ──yes──> source=LOCAL      │
│       │                                                  │
│       no                                                 │
│       ↓                                                  │
│  4. data_dir in config.toml?  ──yes──> source=CONFIG    │
│       │                                                  │
│       no                                                 │
│       ↓                                                  │
│  5. $XDG_* vars set?  ──yes──> source=XDG               │
│       │                                                  │
│       no                                                 │
│       ↓                                                  │
│  6. platformdirs defaults  ──────> source=DEFAULT       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Platform Defaults (via platformdirs)

| Platform | config_dir | data_dir | cache_dir |
|----------|------------|----------|-----------|
| Linux | ~/.config/rekall | ~/.local/share/rekall | ~/.cache/rekall |
| macOS | ~/.config/rekall | ~/.local/share/rekall | ~/.cache/rekall |
| Windows | %APPDATA%\rekall | %APPDATA%\rekall | %LOCALAPPDATA%\rekall\Cache |

**Note macOS**: On utilise les chemins XDG (pas ~/Library/) pour cohérence cross-platform.

## Migration Data

```python
@dataclass
class MigrationInfo:
    """Informations sur une migration legacy."""

    legacy_path: Path
    """Ancien chemin (~/.rekall/)"""

    new_config_dir: Path
    new_data_dir: Path

    has_db: bool
    """True si knowledge.db existe dans legacy"""

    has_config: bool
    """True si config.toml existe dans legacy"""

    migrated_marker: Path = field(init=False)
    """Fichier marqueur post-migration"""

    def __post_init__(self):
        self.migrated_marker = self.legacy_path / ".rekall-migrated"
```

## Validation Rules

1. **Permissions**: Tous les répertoires doivent être accessibles en écriture
2. **DB Lock**: Un seul processus Rekall peut accéder à une DB à la fois
3. **Config Format**: TOML valide, clés inconnues ignorées (forward compat)
4. **Path Normalization**: Tous les chemins convertis en absolus et résolus
