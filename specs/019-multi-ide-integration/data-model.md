# Data Model: Multi-IDE Rekall Integration

**Feature**: 019-multi-ide-integration
**Date**: 2025-12-13

---

## Entités Principales

### 1. IDE

Représente un environnement de développement supporté avec ses capacités.

```python
@dataclass
class IDE:
    """Définition d'un IDE supporté par Rekall."""

    # Identifiant unique
    id: str  # ex: "claude", "cursor", "copilot"

    # Affichage
    name: str  # ex: "Claude Code", "Cursor"

    # Capacités
    supports_mcp: bool  # Supporte le protocole MCP
    supports_progressive_disclosure: bool  # Supporte les skills/commandes
    supports_hooks: bool  # Supporte les hooks (pre/post)

    # Chemins de détection
    local_detection_path: str  # ex: ".claude/"
    global_detection_path: str | None  # ex: "~/.claude/" ou None

    # Chemins d'installation
    local_instructions_path: str  # ex: ".claude/commands/rekall.md"
    global_instructions_path: str | None  # ex: "~/.claude/commands/rekall.md"
    local_mcp_config_path: str | None  # ex: None (dans instructions) ou ".vscode/mcp.json"
    global_mcp_config_path: str | None  # ex: "~/.claude.json"

    # Format
    instructions_format: str  # "markdown", "mdc", "json"

    # Priorité de détection (plus bas = plus prioritaire)
    priority: int  # Claude=1, Cursor=2, Copilot=3, ...
```

**Instances prédéfinies**:

| id | name | supports_mcp | priority | instructions_format |
|----|------|--------------|----------|---------------------|
| claude | Claude Code | ✅ | 1 | markdown |
| cursor | Cursor | ✅ | 2 | mdc |
| copilot | GitHub Copilot | ✅ | 3 | markdown |
| windsurf | Windsurf | ❌ | 4 | markdown |
| cline | Cline | ✅ | 5 | markdown |
| zed | Zed | ✅ | 6 | json |
| continue | Continue.dev | ✅ | 7 | json |

---

### 2. Integration

Configuration Rekall pour un IDE spécifique dans un scope donné.

```python
@dataclass
class Integration:
    """État d'installation d'une intégration Rekall."""

    # Identifiants
    ide_id: str  # Référence à IDE.id
    scope: Scope  # GLOBAL ou LOCAL

    # État
    installed: bool
    version: str | None  # Version installée, None si pas installée

    # Fichiers installés
    installed_files: list[str]  # Chemins absolus des fichiers installés

    # Métadonnées
    installed_at: datetime | None
    last_checked_at: datetime | None


class Scope(Enum):
    """Scope d'installation d'une intégration."""
    GLOBAL = "global"  # ~/.* (home directory)
    LOCAL = "local"    # ./* (projet courant)
```

---

### 3. Article99Version

Version de l'article constitution pour Speckit.

```python
class Article99Version(Enum):
    """Versions de l'Article 99 pour la constitution Speckit."""

    MICRO = "micro"      # ~50 tokens - Juste le rappel
    COURT = "court"      # ~350 tokens - Workflow compact
    EXTENSIF = "extensif"  # ~1000 tokens - Documentation complète


@dataclass
class Article99Config:
    """Configuration de l'Article 99 dans Speckit."""

    version: Article99Version
    installed: bool
    recommended_version: Article99Version  # Basée sur intégrations installées
    recommendation_reason: str  # Ex: "skill Claude installée en global"
```

---

### 4. SpeckitPatch

Modification d'une commande Speckit avec mode adaptatif.

```python
@dataclass
class SpeckitPatch:
    """Patch pour une commande Speckit."""

    # Identification
    command_name: str  # ex: "speckit.implement.md"

    # Contenu adaptatif
    search_term: str  # Terme de recherche par défaut
    types: str  # Types d'entrées à chercher (ex: "bug,pitfall")

    # État
    installed: bool

    # Contenu
    mcp_version: str  # Contenu si MCP disponible
    cli_version: str  # Contenu si CLI seulement
```

---

### 5. DetectedIDE

Résultat de la détection automatique d'IDE.

```python
@dataclass
class DetectedIDE:
    """Résultat de la détection d'IDE."""

    ide: IDE | None  # IDE détecté, None si aucun
    scope: Scope  # Où il a été détecté (LOCAL ou GLOBAL)
    detection_path: str  # Chemin qui a permis la détection

    # Autres IDEs détectés (pour info)
    other_detected: list[tuple[IDE, Scope]]
```

---

### 6. ConfigScreenState

État de l'écran de configuration TUI.

```python
@dataclass
class ConfigScreenState:
    """État de l'écran de configuration."""

    # Section active
    active_section: str  # "integrations" ou "speckit"

    # IDE sélectionné
    selected_ide_idx: int

    # Données
    detected_ide: DetectedIDE
    ide_statuses: dict[str, IntegrationStatus]  # ide_id -> status
    speckit_status: SpeckitStatus | None  # None si Speckit pas installé

    # Préférences
    show_speckit_section: bool  # False si ~/.speckit/ absent


@dataclass
class IntegrationStatus:
    """Statut d'installation d'un IDE."""

    ide_id: str
    local_installed: bool
    global_installed: bool
    global_supported: bool  # L'IDE supporte-t-il l'installation globale?


@dataclass
class SpeckitStatus:
    """Statut de l'intégration Speckit."""

    article_version: Article99Version | None  # Version installée
    recommended_version: Article99Version
    recommendation_reason: str
    patches_installed: list[str]  # Noms des fichiers patchés
    patches_available: list[str]  # Fichiers disponibles pour patch
```

---

## Relations

```
┌─────────────┐
│    IDE      │ 1
└──────┬──────┘
       │
       │ N
┌──────▼──────┐     ┌─────────────────┐
│ Integration │────►│     Scope       │
└──────┬──────┘     │ (GLOBAL/LOCAL)  │
       │            └─────────────────┘
       │
       │ installe
       ▼
┌─────────────────┐
│ Fichiers config │
│ (instructions,  │
│  MCP, hooks)    │
└─────────────────┘


┌─────────────────┐
│ Article99Config │
└────────┬────────┘
         │ recommandé selon
         ▼
┌─────────────────┐
│ Integrations    │
│ installées      │
└─────────────────┘


┌─────────────────┐
│ SpeckitPatch    │
└────────┬────────┘
         │ adapté selon
         ▼
┌─────────────────┐
│ MCP disponible? │
└─────────────────┘
```

---

## Validation Rules

### IDE
- `id` doit être unique
- `priority` doit être unique
- Si `supports_mcp` est False, `mcp_config_path` doit être None
- Si `global_detection_path` est None, `global_instructions_path` doit être None

### Integration
- `ide_id` doit référencer un IDE existant
- `installed_files` ne doit contenir que des chemins absolus
- `version` doit suivre semver

### Article99Config
- `recommended_version` doit être calculée dynamiquement
- `recommendation_reason` doit être non-vide

### SpeckitPatch
- `command_name` doit correspondre à un fichier existant dans `~/.claude/commands/`
- `mcp_version` et `cli_version` doivent être différents

---

## State Transitions

### Installation d'une intégration IDE

```
[Non installé] ──install()──► [Installé]
                                  │
                                  │ fichiers créés
                                  ▼
                             installed=True
                             installed_files=[...]
                             installed_at=now()
```

### Désinstallation

```
[Installé] ──uninstall()──► [Non installé]
               │
               │ fichiers supprimés
               ▼
          installed=False
          installed_files=[]
```

### Détection IDE

```
[Démarrage] ──detect()──► [IDE détecté] ou [unknown]
                │
                │ 1. Check local paths
                │ 2. Check global paths
                │ 3. Appliquer priorité
                ▼
           DetectedIDE(ide=..., scope=...)
```

### Recommandation Article 99

```
[Check integrations] ──recommend()──► [Version recommandée]
        │
        │ 1. Skill Claude installée? → MICRO
        │ 2. MCP configuré? → COURT
        │ 3. Sinon → EXTENSIF
        ▼
   Article99Config(recommended_version=..., reason=...)
```
