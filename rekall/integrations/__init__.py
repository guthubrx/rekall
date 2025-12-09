"""IDE/Agent integration templates for Rekall."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

# Registry of available integrations
# Format: name -> (installer_function, description, local_target, global_target or None)
INTEGRATIONS: dict[str, tuple[Callable[[Path, bool], Path], str, str, str | None]] = {}


def register(name: str, description: str, local_target: str, global_target: str | None = None):
    """Decorator to register an integration.

    Args:
        name: Integration name
        description: Human-readable description
        local_target: Path for local (project) installation
        global_target: Path for global (home) installation, or None if not supported
    """
    def decorator(func: Callable[[Path, bool], Path]):
        INTEGRATIONS[name] = (func, description, local_target, global_target)
        return func
    return decorator


def get_available() -> list[tuple[str, str, str, str | None]]:
    """Get list of available integrations.

    Returns:
        List of (name, description, local_target, global_target) tuples.
        Local paths are prefixed with './' to indicate project-local installation.
        global_target is None if global installation not supported.
    """
    result = []
    for name, (_, desc, local_target, global_target) in INTEGRATIONS.items():
        # Add ./ prefix for local paths
        local_display = f"./{local_target}" if not local_target.startswith("~") else local_target
        result.append((name, desc, local_display, global_target))
    return result


def supports_global(name: str) -> bool:
    """Check if an integration supports global installation."""
    if name not in INTEGRATIONS:
        return False
    _, _, _, global_target = INTEGRATIONS[name]
    return global_target is not None


def install(name: str, base_path: Path, global_install: bool = False) -> Path:
    """Install an integration.

    Args:
        name: Integration name
        base_path: Base path for installation (usually cwd)
        global_install: If True and supported, install globally

    Returns:
        Path to created file

    Raises:
        ValueError: If integration not found or global not supported
    """
    if name not in INTEGRATIONS:
        available = ", ".join(INTEGRATIONS.keys())
        raise ValueError(f"Unknown integration '{name}'. Available: {available}")

    installer, _, _, global_target = INTEGRATIONS[name]

    if global_install and global_target is None:
        raise ValueError(f"Integration '{name}' does not support global installation")

    return installer(base_path, global_install)


def get_ide_status(base_path: Path) -> dict[str, dict]:
    """Get installation status of each IDE integration.

    Args:
        base_path: Base path to check (usually cwd)

    Returns:
        Dict mapping integration name to status dict:
        {
            "local": True/False (installed locally),
            "global": True/False/None (installed globally, None if not supported),
            "supports_global": bool
        }
    """
    status = {}

    for name, (_, _, local_target, global_target) in INTEGRATIONS.items():
        # Skip speckit - it has its own detailed status
        if name == "speckit":
            continue

        # Check local installation
        local_path = base_path / local_target
        local_installed = local_path.exists()

        # Check global installation (if supported)
        if global_target:
            global_path = Path.home() / global_target[2:]  # Remove ~/
            global_installed = global_path.exists()
        else:
            global_installed = None

        status[name] = {
            "local": local_installed,
            "global": global_installed,
            "supports_global": global_target is not None
        }

    return status


def get_ide_target_path(name: str, base_path: Path, global_install: bool = False) -> Path:
    """Get the target file path for an IDE integration.

    Args:
        name: Integration name
        base_path: Base path (usually cwd)
        global_install: If True, return global path

    Returns:
        Path to the integration file
    """
    if name not in INTEGRATIONS:
        raise ValueError(f"Unknown integration: {name}")

    _, _, local_target, global_target = INTEGRATIONS[name]

    if global_install:
        if global_target is None:
            raise ValueError(f"Integration '{name}' does not support global installation")
        return Path.home() / global_target[2:]  # Remove ~/
    else:
        return base_path / local_target


def uninstall_ide(name: str, base_path: Path, global_install: bool = False) -> bool:
    """Uninstall an IDE integration by removing its file.

    Args:
        name: Integration name
        base_path: Base path (usually cwd)
        global_install: If True and supported, uninstall from global location

    Returns:
        True if file was removed, False if it didn't exist
    """
    target = get_ide_target_path(name, base_path, global_install)

    if target.exists():
        target.unlink()
        # Clean up empty parent directories (but not .cursor, .github, etc.)
        parent = target.parent
        if parent.name in ("rules", "commands") and not any(parent.iterdir()):
            parent.rmdir()
        return True
    return False


def install_all_ide(base_path: Path, global_install: bool = False) -> dict:
    """Install all IDE integrations (except speckit).

    Args:
        base_path: Base path for installation
        global_install: If True, install globally where supported

    Returns:
        Dict with installed and failed lists
    """
    results = {"installed": [], "failed": [], "skipped_no_global": []}

    for name in INTEGRATIONS.keys():
        if name == "speckit":
            continue

        # Skip if requesting global but integration doesn't support it
        if global_install and not supports_global(name):
            results["skipped_no_global"].append(name)
            continue

        try:
            install(name, base_path, global_install)
            results["installed"].append(name)
        except Exception as e:
            results["failed"].append(f"{name}: {e}")

    return results


def uninstall_all_ide(base_path: Path, global_install: bool = False) -> dict:
    """Uninstall all IDE integrations (except speckit).

    Args:
        base_path: Base path
        global_install: If True, uninstall from global location where supported

    Returns:
        Dict with removed and skipped lists
    """
    results = {"removed": [], "skipped": []}

    for name in INTEGRATIONS.keys():
        if name == "speckit":
            continue

        # Skip if requesting global but integration doesn't support it
        if global_install and not supports_global(name):
            continue

        if uninstall_ide(name, base_path, global_install):
            results["removed"].append(name)
        else:
            results["skipped"].append(name)

    return results


# =============================================================================
# Shared Content - Rekall Instructions
# =============================================================================

REKALL_INSTRUCTIONS = """
## Rekall - Developer Knowledge Management

This project uses Rekall for capturing and retrieving development knowledge.

### Available Commands

- `rekall search "query"` - Search for bugs, patterns, decisions
- `rekall add <type> "title"` - Add new knowledge entry
- `rekall show <id>` - Show entry details
- `rekall browse` - List all entries
- `rekall export backup.rekall.zip` - Export knowledge base
- `rekall import backup.rekall.zip` - Import from archive

### Entry Types

| Type | When to use |
|------|-------------|
| `bug` | Bug fixed, error resolved |
| `pattern` | Reusable code, best practice |
| `decision` | Architecture choice, trade-off |
| `pitfall` | Mistake to avoid, anti-pattern |
| `config` | Configuration snippet, setup |
| `reference` | External doc, useful link |

### Workflow

**Before solving a problem**, search existing knowledge:
```bash
rekall search "error message or topic"
```

**After solving a problem**, capture the knowledge:
```bash
echo "## Problem
Description of the issue...

## Solution
How it was fixed...

## Why
Explanation of root cause..." | rekall add bug "Fix: description" -t tag1,tag2 -p project-name -c 3
```
"""


# =============================================================================
# Integration Installers
# =============================================================================

@register("cursor", "Cursor AI rules", ".cursorrules", None)
def install_cursor(base_path: Path, global_install: bool = False) -> Path:
    """Install Cursor integration (.cursorrules)."""
    content = f"""# Cursor Rules - Rekall Integration

## Knowledge Management
{REKALL_INSTRUCTIONS}

### Cursor-Specific Instructions

When helping with code:
1. First search for existing solutions: `rekall search "topic"`
2. After solving issues, suggest capturing with `rekall add`
3. Reference relevant entries by ID when applicable
"""

    target = base_path / ".cursorrules"
    target.write_text(content)
    return target


@register("claude", "Claude Code skills", ".claude/commands/rekall.md + rekall.save.md", "~/.claude/commands/rekall.md + rekall.save.md")
def install_claude(base_path: Path, global_install: bool = False) -> Path:
    """Install Claude Code integration (skill files: /rekall and /rekall.save)."""
    # Install main /rekall skill
    if global_install:
        claude_dir = Path.home() / ".claude" / "commands"
    else:
        claude_dir = base_path / ".claude" / "commands"

    claude_dir.mkdir(parents=True, exist_ok=True)

    # Install rekall.md (main skill)
    rekall_skill_path = claude_dir / "rekall.md"
    rekall_skill_path.write_text(REKALL_SKILL)

    # Install rekall.save.md (capture skill)
    content = '''# Capture Rekall - Mémoire Cognitive

Tu dois capturer une connaissance dans Rekall. Suis ce workflow :

## 1. Identifier le Type et la Mémoire

Analyse le contexte de la conversation :

| Type | Quand l'utiliser |
|------|------------------|
| `bug` | Bug résolu, erreur corrigée, fix appliqué |
| `pattern` | Code réutilisable, best practice, technique découverte |
| `decision` | Choix architectural, technologie choisie, trade-off |
| `pitfall` | Piège à éviter, erreur à ne pas répéter, anti-pattern |
| `config` | Configuration technique, setup, paramétrage |
| `reference` | Documentation, lien utile, ressource externe |

| Memory Type | Quand l'utiliser |
|-------------|------------------|
| `episodic` | Événement spécifique (bug particulier, incident) - **défaut** |
| `semantic` | Concept général (pattern réutilisable, best practice) |

## 2. Extraire les Informations

Depuis le contexte de la conversation, extrais :
- **Titre** : Court et descriptif (max 60 caractères)
- **Projet** : Nom du projet concerné (depuis pwd ou contexte)
- **Tags** : 2-5 tags pertinents en kebab-case
- **Memory Type** : episodic (défaut) ou semantic
- **Confiance** : 0-5 selon la source (2 par défaut)
- **Contenu** : Description complète incluant :
  - Problème/Contexte
  - Solution/Décision
  - Pourquoi ça fonctionne
  - Code exemple si pertinent
  - URL source si recherche web

## 3. Exécuter la Capture

```bash
echo "CONTENU_MARKDOWN" | rekall add TYPE "TITRE" -p PROJET -t TAGS -m MEMORY_TYPE -c CONFIANCE
```

## 4. Proposer des Liens

Après la capture, cherche si des entrées similaires existent :

```bash
rekall search "KEYWORDS" --limit 5
```

Si des entrées similaires existent, propose de les lier :

```bash
rekall link NOUVEL_ID ANCIEN_ID --type related
```

Types de liens :
- `related` - Connexion thématique
- `supersedes` - Remplace une entrée obsolète
- `derived_from` - Généralisé depuis épisodiques
- `contradicts` - Information conflictuelle

## 5. Confirmer

Affiche :
```
💾 Connaissance capturée dans Rekall :
   Type: TYPE | Memory: MEMORY_TYPE
   Titre: "TITRE"
   Projet: PROJET | Tags: TAGS
   ID: [ID retourné]

🔗 Liens créés : X (si applicable)
```

## Exemple Complet

```bash
echo "## Problème
Import circulaire entre models.py et services.py causant ImportError.

## Solution
Déplacer les types partagés dans types/shared.ts.

## Code
\\`\\`\\`python
# Après (types partagés)
from types.shared import UserType
\\`\\`\\`

## Pourquoi
Casse la dépendance circulaire." | rekall add bug "Fix import circulaire Python" -p mon-projet -t python,import,architecture -m episodic -c 3
```

## Commandes Utiles

```bash
# Recherche et consultation
rekall search "query"                    # Full-text
rekall search "q" --memory-type semantic # Par type mémoire
rekall show <id>                         # Détails avec liens

# Capture
rekall add <type> "titre" -m episodic    # Ajouter épisodique
rekall add pattern "titre" -m semantic   # Ajouter sémantique

# Liens
rekall link ID1 ID2 --type related       # Créer lien
rekall related <id>                      # Voir liens

# Généralisation (si 3+ entrées similaires)
rekall generalize ID1 ID2 ID3            # Créer pattern sémantique
```

---

**IMPORTANT** : `/rekall.save` est pour les captures MANUELLES. Pense à proposer des liens avec les entrées existantes !
'''

    rekall_save_path = claude_dir / "rekall.save.md"
    rekall_save_path.write_text(content)

    # Return main skill path
    return rekall_skill_path


@register("copilot", "GitHub Copilot instructions", ".github/copilot-instructions.md", None)
def install_copilot(base_path: Path, global_install: bool = False) -> Path:
    """Install GitHub Copilot integration."""
    content = f"""# GitHub Copilot Instructions - Rekall Integration
{REKALL_INSTRUCTIONS}

### Copilot Guidelines

When generating code suggestions:
- Consider searching Rekall for existing patterns: `rekall search "topic"`
- Suggest capturing new patterns discovered during development
- Reference entry IDs when applicable
"""

    github_dir = base_path / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)

    target = github_dir / "copilot-instructions.md"
    target.write_text(content)
    return target


@register("windsurf", "Windsurf AI rules", ".windsurfrules", None)
def install_windsurf(base_path: Path, global_install: bool = False) -> Path:
    """Install Windsurf integration."""
    content = f"""# Windsurf Rules - Rekall Integration
{REKALL_INSTRUCTIONS}

### Windsurf Guidelines

- Search before solving: `rekall search "error or topic"`
- Capture after fixing: `rekall add bug "Fix description"`
"""

    target = base_path / ".windsurfrules"
    target.write_text(content)
    return target


@register("cline", "Cline AI rules", ".clinerules", None)
def install_cline(base_path: Path, global_install: bool = False) -> Path:
    """Install Cline integration."""
    content = f"""# Cline Rules - Rekall Integration
{REKALL_INSTRUCTIONS}

### Cline Guidelines

- Search before solving: `rekall search "error or topic"`
- Capture after fixing: `rekall add bug "Fix description"`
"""

    target = base_path / ".clinerules"
    target.write_text(content)
    return target


@register("aider", "Aider conventions", ".aider.conf.yml", None)
def install_aider(base_path: Path, global_install: bool = False) -> Path:
    """Install Aider integration."""
    content = """# Aider Configuration - Rekall Integration
#
# Rekall Commands:
# - rekall search "query" - Search knowledge base
# - rekall add <type> "title" - Add entry
# - rekall browse - List all entries
#
# Before working on issues, search: rekall search "topic"
# After fixing bugs, capture: rekall add bug "description"

# Aider settings
auto-commits: true
"""

    target = base_path / ".aider.conf.yml"
    target.write_text(content)
    return target


@register("continue", "Continue.dev config", ".continue/config.json", None)
def install_continue(base_path: Path, global_install: bool = False) -> Path:
    """Install Continue.dev integration."""
    import json

    config = {
        "customCommands": [
            {
                "name": "rekall-search",
                "description": "Search Rekall knowledge base",
                "prompt": "Search Rekall with: rekall search \"{{{input}}}\""
            },
            {
                "name": "rekall-save",
                "description": "Save knowledge to Rekall",
                "prompt": "Capture this knowledge with rekall add"
            }
        ],
        "docs": [
            {
                "title": "Rekall",
                "description": "Developer knowledge management",
                "content": REKALL_INSTRUCTIONS
            }
        ]
    }

    continue_dir = base_path / ".continue"
    continue_dir.mkdir(parents=True, exist_ok=True)

    target = continue_dir / "config.json"
    target.write_text(json.dumps(config, indent=2))
    return target


@register("zed", "Zed AI assistant context", ".zed/settings.json", None)
def install_zed(base_path: Path, global_install: bool = False) -> Path:
    """Install Zed integration."""
    import json

    config = {
        "assistant": {
            "default_model": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514"
            },
            "context": f"""
Rekall - Developer Knowledge Management:
{REKALL_INSTRUCTIONS}
"""
        }
    }

    zed_dir = base_path / ".zed"
    zed_dir.mkdir(parents=True, exist_ok=True)

    target = zed_dir / "settings.json"
    target.write_text(json.dumps(config, indent=2))
    return target


@register("gemini", "Gemini CLI context", "GEMINI.md", "~/.gemini/GEMINI.md")
def install_gemini(base_path: Path, global_install: bool = False) -> Path:
    """Install Gemini CLI integration (GEMINI.md)."""
    content = f"""# Gemini CLI - Rekall Integration
{REKALL_INSTRUCTIONS}

## Gemini-Specific Instructions

When helping with code in this project:
1. First search for existing solutions: `rekall search "topic"`
2. After solving issues, suggest capturing with `rekall add`
3. Reference relevant entries by ID when applicable

Use `/memory add` to save important context to your global memory.
"""

    if global_install:
        gemini_dir = Path.home() / ".gemini"
        gemini_dir.mkdir(parents=True, exist_ok=True)
        target = gemini_dir / "GEMINI.md"
    else:
        target = base_path / "GEMINI.md"

    target.write_text(content)
    return target


@register("cursor-agent", "Cursor Agent rules (.mdc)", ".cursor/rules/rekall.mdc", None)
def install_cursor_agent(base_path: Path, global_install: bool = False) -> Path:
    """Install Cursor Agent integration (.cursor/rules/rekall.mdc)."""
    content = f"""---
description: Rekall knowledge management integration
globs: ["**/*"]
alwaysApply: true
---

# Rekall - Developer Knowledge Management
{REKALL_INSTRUCTIONS}

## Cursor Agent Instructions

When working on this project:
1. Search existing knowledge before implementing: `rekall search "topic"`
2. After fixing bugs or discovering patterns, suggest capturing with `rekall add`
3. Reference entry IDs when applicable
"""

    cursor_rules_dir = base_path / ".cursor" / "rules"
    cursor_rules_dir.mkdir(parents=True, exist_ok=True)

    target = cursor_rules_dir / "rekall.mdc"
    target.write_text(content)
    return target


@register("qwen", "Qwen Code context", "QWEN.md", "~/.qwen/QWEN.md")
def install_qwen(base_path: Path, global_install: bool = False) -> Path:
    """Install Qwen Code integration (QWEN.md)."""
    content = f"""# Qwen Code - Rekall Integration
{REKALL_INSTRUCTIONS}

## Qwen-Specific Instructions

When helping with code in this project:
1. First search for existing solutions: `rekall search "topic"`
2. After solving issues, suggest capturing with `rekall add`
3. Reference relevant entries by ID when applicable
"""

    if global_install:
        qwen_dir = Path.home() / ".qwen"
        qwen_dir.mkdir(parents=True, exist_ok=True)
        target = qwen_dir / "QWEN.md"
    else:
        target = base_path / "QWEN.md"

    target.write_text(content)
    return target


@register("opencode", "opencode AGENTS.md", "AGENTS.md", "~/.config/opencode/AGENTS.md")
def install_opencode(base_path: Path, global_install: bool = False) -> Path:
    """Install opencode integration (AGENTS.md)."""
    content = f"""# OpenCode - Rekall Integration
{REKALL_INSTRUCTIONS}

## OpenCode Instructions

When working on this project:
1. Search existing knowledge before implementing: `rekall search "topic"`
2. After fixing bugs or discovering patterns, suggest capturing with `rekall add`
3. Use `@general` for complex searches across the codebase
4. Reference entry IDs when applicable
"""

    if global_install:
        opencode_dir = Path.home() / ".config" / "opencode"
        opencode_dir.mkdir(parents=True, exist_ok=True)
        target = opencode_dir / "AGENTS.md"
    else:
        target = base_path / "AGENTS.md"

    target.write_text(content)
    return target


# =============================================================================
# Speckit Integration (Complex - multiple files)
# =============================================================================

REKALL_SKILL = '''# Rekall - Memoire Developpeur Cognitive

Ce fichier contient les instructions pour utiliser Rekall, le systeme de memoire persistante cross-projets avec support de memoire cognitive.

## Principe

- **Consulter AVANT** d'agir - chercher les connaissances existantes
- **Capturer APRES** avoir resolu - documenter les solutions
- **Lier** les connaissances - construire un graphe de savoir
- **Generaliser** les patterns - transformer l'episodique en semantique

---

## 1. Consultation Automatique (OBLIGATOIRE)

**AVANT de commencer** tout bug fix, feature ou refactor, tu DOIS consulter Rekall :

| Contexte detecte | Commande Rekall |
|------------------|-----------------|
| Bug fix demande | `rekall search "bug KEYWORDS" --json --limit 5` |
| Feature/refactor | `rekall search "pattern KEYWORDS" --json --limit 5` |
| Choix technique | `rekall search "decision KEYWORDS" --json --limit 5` |
| Configuration | `rekall search "config KEYWORDS" --json --limit 5` |

### Extraction des Keywords

Extrais de la demande utilisateur :
- Technologies mentionnees (Python, React, SQLite...)
- Noms de fichiers/modules
- Descriptions d'erreur
- Concepts techniques

### Architecture Deux Audiences

Tu recois des donnees JSON completes pour raisonner, puis tu presentes un resume lisible a l'humain.

```
Rekall CLI (--json) → Toi (logique) → Humain (lecture)
```

### Format JSON Recu (pour ton analyse)

```json
{
  "query": "auth timeout",
  "results": [{
    "id": "01HXYZ...",
    "type": "bug",
    "title": "Timeout auth API",
    "content": "## Probleme\\nTimeout 5s insuffisant...",
    "tags": ["auth", "api", "timeout"],
    "project": "backend-api",
    "confidence": 4,
    "consolidation_score": 0.89,
    "access_count": 12,
    "last_accessed": "2025-12-07",
    "relevance_score": 0.85,
    "links": {
      "outgoing": [{"target_id": "01HABC", "type": "related"}],
      "incoming": []
    }
  }],
  "total_count": 3,
  "context_matches": {"project": true, "tags": ["auth"]}
}
```

### Format de Presentation a l'Humain

**Si resultats trouves** - Utilise des citations inline :

```
🧠 Rekall: 3 connaissances pertinentes

D'apres « Timeout auth API » [1], le timeout par defaut de 5s est
insuffisant en production. La solution recommandee selon
« Pattern retry backoff » [2] est d'implementer un retry exponentiel.

---
References:
[1] 01HXYZ - bug - Timeout auth API
[2] 01HABC - pattern - Pattern retry backoff
[3] 01HDEF - config - Config timeout services
```

**Si aucun resultat :**

```
🧠 Rekall: Aucune connaissance trouvee pour "nouveau-sujet"

Je procede sans contexte historique.
💡 Si cette tache produit des connaissances utiles, je proposerai
   de les capturer a la fin.
```

### Score de Pertinence

Priorise les resultats selon leur `relevance_score` :
- `> 0.7` : Detail complet dans ta reponse
- `0.4 - 0.7` : Resume seulement
- `< 0.4` : Ne pas mentionner

---

## 2. Capture Automatique (Apres Resolution)

**APRES avoir resolu** un probleme, propose de capturer :

| Evenement | Type suggere |
|-----------|--------------|
| Bug resolu | `bug` |
| Decision technique prise | `decision` |
| Pattern decouvert/utilise | `pattern` |
| Piege evite | `pitfall` |
| Config trouvee | `config` |
| Reference web utile | `reference` |

### Generation Automatique (titre, tags, type)

Extrais automatiquement depuis le contexte de la conversation :

**Titre** (max 60 caracteres):
- Format: "Verbe + Objet + Contexte"
- Exemples: "Fix timeout auth API Python", "Pattern retry avec backoff"

**Tags** (2-5 tags en kebab-case):
- Technologies: `python`, `react`, `sqlite`
- Concepts: `auth`, `cache`, `async`
- Fichiers: nom du module concerne

**Type**: Deduis selon l'evenement (voir tableau ci-dessus)

**Memory Type**:
- `episodic` (defaut): Evenement specifique, bug particulier
- `semantic`: Pattern reutilisable, best practice generale

### Format de Proposition

```
💾 Connaissance acquise detectee

Je propose de sauvegarder dans Rekall :

**Titre**: Fix timeout auth API - augmenter a 30s
**Type**: bug
**Tags**: auth, api, timeout, python
**Memory**: episodic
**Confiance**: 4/5

Contenu suggere:
---
## Probleme
Timeout de 5s insuffisant pour l'auth API en production.

## Solution
Augmenter le timeout a 30s dans config.py ligne 42.

## Contexte
Fichier: `src/auth/client.py`
Commit: abc1234
---

Voulez-vous :
1. ✅ Sauvegarder tel quel
2. ✏️ Modifier avant sauvegarde
3. ❌ Ne pas sauvegarder
```

### Execution de la Capture

```bash
echo "CONTENU_MARKDOWN" | rekall add TYPE "TITRE" \\
  -p PROJET \\
  -t TAGS \\
  --memory-type episodic \\
  -c CONFIANCE
```

### Regles de Capture

1. **Proposer UNE SEULE fois** - Si l'utilisateur refuse (option 3), ne pas re-proposer dans la meme session
2. **Verifier avant** - Chercher si une entree similaire existe deja :
   ```bash
   rekall search "KEYWORDS" --limit 3
   ```
3. **Ne pas capturer le trivial** - Questions simples, typos, commandes basiques
4. **Confiance par defaut**: 3/5 (ajuster selon la source)

---

## 3. Liens et Knowledge Graph

Apres creation d'une entree, propose de la lier si similaires existent :

```
🔗 Entrees potentiellement liees detectees

L'entree que vous venez de creer pourrait etre liee a :

1. [type] "Titre" (ID_COURT)
   → Similarite: X% (raison)

Voulez-vous creer des liens ?
- [1] Lier comme "related"
- [2] Lier comme "derived_from"
- [3] Ignorer
```

### Types de Liens

| Type | Usage |
|------|-------|
| `related` | Connexion thematique |
| `supersedes` | Remplace une entree obsolete |
| `derived_from` | Generalise depuis episodiques |
| `contradicts` | Information conflictuelle |

```bash
rekall link SOURCE_ID TARGET_ID --type TYPE
rekall related ENTRY_ID  # Voir les liens
```

---

## 4. Memory Types

| Type | Usage |
|------|-------|
| `episodic` | Evenement specifique (bug, incident) - defaut |
| `semantic` | Concept general (pattern, best practice) |

### Generalisation

Si 3+ entrees episodiques similaires :

```
💡 Opportunite de generalisation

Vous avez 3 entrees episodiques similaires sur "SUJET":
- ID1 "Titre 1"
- ID2 "Titre 2"
- ID3 "Titre 3"

Voulez-vous generaliser en pattern semantique ?
→ `rekall generalize ID1 ID2 ID3`
```

---

## 5. Commandes Rekall

```bash
# Recherche
rekall search "query"                    # Full-text
rekall search "q" --type bug             # Par type
rekall search "q" --memory-type semantic # Par memory type

# Ajout
rekall add <type> "titre"                # Ajouter
rekall add pattern "titre" --memory-type semantic  # Semantique

# Liens
rekall link ID1 ID2 --type related       # Creer lien
rekall unlink ID1 ID2                    # Supprimer lien
rekall related ID                        # Voir liens

# Tracking
rekall stale                             # Entrees non consultees
rekall review                            # Session de revision

# General
rekall show <id>                         # Details
rekall browse                            # Parcourir
rekall export backup.rekall.zip          # Exporter
```

---

## 6. Regles de Comportement

### Priorites

1. **Consultation AVANT action** - Toujours chercher avant de proposer
2. **Citation des sources** - Mentionner les IDs Rekall utilises
3. **Capture NON intrusive** - Proposer, ne jamais forcer
4. **Liens suggeres** - Proposer, ne jamais creer sans confirmation

### Limitations

- Ne PAS capturer les conversations triviales
- Ne PAS consulter pour les questions non-techniques
- Ne PAS creer de liens sans confirmation utilisateur
- Respecter les refus de capture (ne pas re-proposer meme session)
'''

ARTICLE_99_CONTENT = '''
---

## Memoire Developpeur Persistante

### XCIX. Rekall - Memoire Cognitive (OPTIONNEL)

**Rekall** est un systeme de memoire cognitive persistante cross-projets avec knowledge graph.

#### 1. Principe

- **Consulter AVANT** d'agir - chercher les connaissances existantes
- **Capturer APRES** avoir resolu - documenter les solutions
- **Lier** les connaissances - construire un graphe de savoir
- **Reviser** regulierement - maintenir la memoire active

#### 2. Types de Memoire

| Type | Usage |
|------|-------|
| `episodic` | Evenement specifique (bug, incident) - defaut |
| `semantic` | Concept general (pattern, best practice) |

#### 3. Commandes Principales

| Commande | Usage |
|----------|-------|
| `rekall search "query"` | Rechercher (--memory-type pour filtrer) |
| `rekall add <type> "titre"` | Ajouter (-m episodic/semantic) |
| `rekall show <id>` | Afficher avec liens et consolidation |
| `rekall link ID1 ID2` | Creer un lien (--type related/supersedes/derived_from/contradicts) |
| `rekall related <id>` | Voir les entrees liees |
| `rekall stale` | Entrees non consultees >30j |
| `rekall review` | Session de revision espacee (SM-2) |
| `rekall generalize ID1 ID2` | Creer pattern semantique depuis episodiques |

#### 4. Types de Liens

| Type | Usage |
|------|-------|
| `related` | Connexion thematique |
| `supersedes` | Remplace une entree obsolete |
| `derived_from` | Generalise depuis episodiques |
| `contradicts` | Information conflictuelle |

#### 5. Integration Speckit

Voir `/rekall` pour les instructions detaillees de consultation automatique et capture.

'''

# Patches for Speckit command files
# Format: filename -> (search_term, types, insert_after)
# Note: speckit.hotfix.md may not exist in standard installations - handled gracefully
SPECKIT_PATCHES = {
    "speckit.implement.md": ("NOM_PROJET", "pitfall,bug", "## Outline\n"),
    "speckit.hotfix.md": ("DESCRIPTION_BUG", "bug,pitfall", "Tu exécutes le workflow de hotfix pour SpecKit.\n"),
    "speckit.clarify.md": ("SUJET_DE_LA_SPEC", "decision", "## Outline\n"),
    "speckit.specify.md": ("MOTS_CLES_DE_LA_FEATURE", "decision,pattern", "Given that feature description, do this:\n"),
    "speckit.plan.md": ("architecture pattern", "pattern,decision", "## Outline\n"),
    "speckit.tasks.md": ("TECHNOS_UTILISEES", "pattern,bug", "## Outline\n"),
}


def _make_rekall_section(search_term: str, types: str) -> str:
    """Generate a Rekall consultation section."""
    return f'''### 0. Consultation Rekall (OPTIONNEL)

**Voir `/rekall` pour les instructions completes.**

```bash
# Recherche par type
rekall search "{search_term}" --type {types} --limit 5

# Recherche par memoire (patterns consolides)
rekall search "{search_term}" --memory-type semantic --limit 3
```

'''


@register("speckit", "Speckit workflow integration", "~/.claude/commands/ + ~/.speckit/constitution.md", None)
def install_speckit(base_path: Path, global_install: bool = False) -> Path:
    """Install Speckit integration (article + patches).

    This integration:
    1. Adds Article XCIX (99) to ~/.speckit/constitution.md
    2. Patches Speckit command files with Rekall consultation sections

    Note: The /rekall skill is installed via the Claude Code IDE integration.

    Returns:
        Path to the constitution file (or commands dir if no constitution)
    """
    results = {"article": False, "patched": [], "skipped": []}
    claude_dir = Path.home() / ".claude" / "commands"
    claude_dir.mkdir(parents=True, exist_ok=True)

    # 1. Add Article 99 to constitution
    constitution_path = Path.home() / ".speckit" / "constitution.md"
    if constitution_path.exists():
        content = constitution_path.read_text()
        if "XCIX. Rekall" not in content:
            new_content = content.rstrip() + "\n" + ARTICLE_99_CONTENT
            constitution_path.write_text(new_content)
            results["article"] = True

    # 2. Patch Speckit command files
    for filename, (search_term, types, insert_after) in SPECKIT_PATCHES.items():
        filepath = claude_dir / filename
        if not filepath.exists():
            results["skipped"].append(filename)
            continue

        content = filepath.read_text()

        # Skip if already patched
        if "Consultation Rekall" in content or "rekall search" in content:
            results["skipped"].append(filename)
            continue

        # Find insertion point and insert section
        if insert_after in content:
            section = _make_rekall_section(search_term, types)
            new_content = content.replace(insert_after, insert_after + section)
            filepath.write_text(new_content)
            results["patched"].append(filename)
        else:
            results["skipped"].append(filename)

    # Print summary
    print("Rekall-Speckit integration installed:")
    print(f"  - Article 99: {'Added' if results['article'] else 'Skipped (exists or no constitution)'}")
    print(f"  - Patched: {', '.join(results['patched']) or 'None'}")
    if results["skipped"]:
        print(f"  - Skipped: {', '.join(results['skipped'])}")

    return constitution_path if constitution_path.exists() else claude_dir


def is_speckit_installed() -> bool:
    """Check if Speckit integration is installed.

    Returns:
        True if any part of the integration is present
    """
    status = get_speckit_status()
    return any(status.values())


def get_speckit_status() -> dict:
    """Get detailed installation status of each Speckit component.

    Returns:
        Dict mapping component names to their installation status (bool)
    """
    claude_dir = Path.home() / ".claude" / "commands"
    status = {}

    # Check constitution article
    constitution_path = Path.home() / ".speckit" / "constitution.md"
    if constitution_path.exists():
        content = constitution_path.read_text()
        status["article"] = "XCIX. Rekall" in content
    else:
        status["article"] = False

    # Check each Speckit command file
    for filename in SPECKIT_PATCHES.keys():
        filepath = claude_dir / filename
        if filepath.exists():
            content = filepath.read_text()
            status[filename] = "Consultation Rekall" in content
        else:
            status[filename] = None  # File doesn't exist

    return status


def get_speckit_preview(components: list[str]) -> dict[str, str]:
    """Generate preview of changes for selected components.

    Args:
        components: List of component names to preview

    Returns:
        Dict mapping component names to their preview text (diff or content)
    """
    previews = {}
    claude_dir = Path.home() / ".claude" / "commands"

    for component in components:
        if component == "article":
            # Show the article content
            previews["article"] = f"[APPEND TO] ~/.speckit/constitution.md\n{'─' * 50}\n{ARTICLE_99_CONTENT}"

        elif component in SPECKIT_PATCHES:
            filepath = claude_dir / component
            if not filepath.exists():
                previews[component] = f"[SKIP] {component} - file not found"
                continue

            content = filepath.read_text()
            if "Consultation Rekall" in content:
                previews[component] = f"[SKIP] {component} - already patched"
                continue

            search_term, types, insert_after = SPECKIT_PATCHES[component]
            section = _make_rekall_section(search_term, types)

            # Find context around insertion point
            if insert_after in content:
                idx = content.find(insert_after)
                before = content[max(0, idx-50):idx + len(insert_after)]
                previews[component] = f"[PATCH] {component}\n{'─' * 50}\n...{before}\n[+] {section.strip()}\n..."
            else:
                previews[component] = f"[SKIP] {component} - insertion point not found"

    return previews


def get_speckit_uninstall_preview(components: list[str]) -> dict[str, str]:
    """Generate preview of uninstall changes for selected components.

    Args:
        components: List of component names to preview

    Returns:
        Dict mapping component names to their preview text
    """
    import re
    previews = {}
    claude_dir = Path.home() / ".claude" / "commands"

    for component in components:
        if component == "article":
            constitution_path = Path.home() / ".speckit" / "constitution.md"
            if constitution_path.exists():
                content = constitution_path.read_text()
                if "XCIX. Rekall" in content:
                    previews["article"] = f"[REMOVE FROM] ~/.speckit/constitution.md\n{'─' * 50}\n[-] Article XCIX (Rekall - Capture de Connaissances)"
                else:
                    previews["article"] = "[SKIP] article - not in constitution"
            else:
                previews["article"] = "[SKIP] article - constitution not found"

        elif component in SPECKIT_PATCHES:
            filepath = claude_dir / component
            if not filepath.exists():
                previews[component] = f"[SKIP] {component} - file not found"
                continue

            content = filepath.read_text()
            if "Consultation Rekall" not in content:
                previews[component] = f"[SKIP] {component} - not patched"
                continue

            # Find the section that will be removed
            pattern = r'### \d+[ab]?\. Consultation Rekall[^\n]*\n+(?:\*\*[^\n]*\n+)?```bash\n[^`]*```\n+'
            match = re.search(pattern, content)
            if match:
                previews[component] = f"[CLEAN] {component}\n{'─' * 50}\n[-] {match.group(0).strip()[:200]}..."
            else:
                previews[component] = f"[CLEAN] {component} - Rekall section will be removed"

    return previews


def install_speckit_partial(components: list[str]) -> dict:
    """Install selected Speckit components.

    Args:
        components: List of component names to install

    Returns:
        Dict with installation results
    """
    results = {"installed": [], "skipped": [], "errors": []}
    claude_dir = Path.home() / ".claude" / "commands"
    claude_dir.mkdir(parents=True, exist_ok=True)

    for component in components:
        try:
            if component == "article":
                constitution_path = Path.home() / ".speckit" / "constitution.md"
                if constitution_path.exists():
                    content = constitution_path.read_text()
                    if "XCIX. Rekall" not in content:
                        new_content = content.rstrip() + "\n" + ARTICLE_99_CONTENT
                        constitution_path.write_text(new_content)
                        results["installed"].append("article")
                    else:
                        results["skipped"].append("article (exists)")
                else:
                    results["skipped"].append("article (no constitution)")

            elif component in SPECKIT_PATCHES:
                filepath = claude_dir / component
                if not filepath.exists():
                    results["skipped"].append(f"{component} (not found)")
                    continue

                content = filepath.read_text()
                if "Consultation Rekall" in content:
                    results["skipped"].append(f"{component} (exists)")
                    continue

                search_term, types, insert_after = SPECKIT_PATCHES[component]
                if insert_after in content:
                    section = _make_rekall_section(search_term, types)
                    new_content = content.replace(insert_after, insert_after + section)
                    filepath.write_text(new_content)
                    results["installed"].append(component)
                else:
                    results["skipped"].append(f"{component} (no insertion point)")

        except Exception as e:
            results["errors"].append(f"{component}: {e}")

    return results


def uninstall_speckit_partial(components: list[str]) -> dict:
    """Uninstall selected Speckit components.

    Args:
        components: List of component names to uninstall

    Returns:
        Dict with uninstallation results
    """
    import re

    results = {"removed": [], "skipped": [], "errors": []}
    claude_dir = Path.home() / ".claude" / "commands"

    for component in components:
        try:
            if component == "article":
                constitution_path = Path.home() / ".speckit" / "constitution.md"
                if constitution_path.exists():
                    content = constitution_path.read_text()
                    if "XCIX. Rekall" in content or "Rekall - Capture de Connaissances" in content:
                        patterns = [
                            r'\n---\n+## Memoire Developpeur Persistante\n+### XCIX\. Rekall[^\n]*\n.*?(?=\n---\n|\Z)',
                            r'\n### XCIX\. Rekall[^\n]*\n.*?(?=\n### [A-Z]|\n---\n|\Z)',
                        ]
                        new_content = content
                        for pattern in patterns:
                            new_content = re.sub(pattern, '', new_content, flags=re.DOTALL)
                        new_content = re.sub(r'\n{3,}$', '\n', new_content)

                        if new_content != content:
                            constitution_path.write_text(new_content)
                            results["removed"].append("article")
                        else:
                            results["skipped"].append("article (no change)")
                    else:
                        results["skipped"].append("article (not in constitution)")
                else:
                    results["skipped"].append("article (no constitution)")

            elif component in SPECKIT_PATCHES:
                filepath = claude_dir / component
                if not filepath.exists():
                    results["skipped"].append(f"{component} (not found)")
                    continue

                content = filepath.read_text()
                if "Consultation Rekall" not in content:
                    results["skipped"].append(f"{component} (not patched)")
                    continue

                original_content = content
                pattern1 = r'### \d+[ab]?\. Consultation Rekall[^\n]*\n+(?:\*\*[^\n]*\n+)?```bash\n[^`]*```\n+'
                content = re.sub(pattern1, '', content)
                pattern2 = r'```bash\nrekall search "[^"]*" --type [^\n]+ --limit \d+\n```\n+'
                content = re.sub(pattern2, '', content)

                if content != original_content:
                    filepath.write_text(content)
                    results["removed"].append(component)
                else:
                    results["skipped"].append(f"{component} (no change)")

        except Exception as e:
            results["errors"].append(f"{component}: {e}")

    return results


def uninstall_speckit() -> dict:
    """Remove Speckit integration.

    Uses regex patterns to cleanly remove added sections without needing backups.
    This allows the user to modify their files between install/uninstall.

    Returns:
        Dict with uninstallation results
    """
    import re

    results = {"article_removed": False, "cleaned": []}

    claude_dir = Path.home() / ".claude" / "commands"

    # 1. Remove Article XCIX from constitution
    constitution_path = Path.home() / ".speckit" / "constitution.md"
    if constitution_path.exists():
        content = constitution_path.read_text()
        if "XCIX. Rekall" in content or "Rekall - Capture de Connaissances" in content:
            # Pattern: Match from "---" before article to end of article
            # Handles variations in whitespace and content
            patterns = [
                # Full section with header
                r'\n---\n+## Memoire Developpeur Persistante\n+### XCIX\. Rekall[^\n]*\n.*?(?=\n---\n|\Z)',
                # Just the article without header (if header was modified)
                r'\n### XCIX\. Rekall[^\n]*\n.*?(?=\n### [A-Z]|\n---\n|\Z)',
            ]
            new_content = content
            for pattern in patterns:
                new_content = re.sub(pattern, '', new_content, flags=re.DOTALL)

            # Clean up any double newlines at end
            new_content = re.sub(r'\n{3,}$', '\n', new_content)

            if new_content != content:
                constitution_path.write_text(new_content)
                results["article_removed"] = True

    # 3. Clean Speckit command files - remove Rekall consultation sections
    for filename in SPECKIT_PATCHES.keys():
        filepath = claude_dir / filename
        if not filepath.exists():
            continue

        content = filepath.read_text()
        original_content = content

        # Pattern 1: Standard "### 0. Consultation Rekall" section
        # Matches: ### 0. Consultation Rekall (OPTIONNEL)\n...\n```\n\n
        pattern1 = r'### \d+[ab]?\. Consultation Rekall[^\n]*\n+(?:\*\*[^\n]*\n+)?```bash\n[^`]*```\n+'
        content = re.sub(pattern1, '', content)

        # Pattern 2: Any remaining "rekall search" in code blocks we added
        # Only remove if it's our generated pattern (with --type and --limit)
        # Don't remove user-added rekall commands
        pattern2 = r'```bash\nrekall search "[^"]*" --type [^\n]+ --limit \d+\n```\n+'
        content = re.sub(pattern2, '', content)

        if content != original_content:
            filepath.write_text(content)
            results["cleaned"].append(filename)

    return results
