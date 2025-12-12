# Research: XDG-Compliant Installation Paths

**Date**: 2024-12-07
**Feature**: 003-xdg-install-paths

## Résumé des Recherches

Cette recherche technique couvre les choix de bibliothèques et patterns pour implémenter le support XDG dans Rekall.

---

## 1. Bibliothèque XDG Cross-Platform

### Problème
Rekall doit fonctionner sur Linux, macOS et Windows avec les conventions de chemins natives.

### Options Évaluées

| Bibliothèque | Maintenu | Cross-platform | Stars | Décision |
|--------------|----------|----------------|-------|----------|
| `platformdirs` | ✅ Actif | ✅ Oui | 5k+ | **Choisi** |
| `appdirs` | ❌ Deprecated | ✅ Oui | 2.5k | Remplacé par platformdirs |
| `xdg` | ✅ Actif | ❌ Linux only | 100+ | Non adapté |
| stdlib `pathlib` | ✅ | ✅ | - | Insuffisant seul |

### Décision
**Utiliser `platformdirs`** - C'est le successeur officiel de `appdirs`, maintenu par la Python Packaging Authority (PyPA).

### Rationale
- Standard de facto pour les apps Python
- Gère automatiquement XDG sur Linux, ~/Library/ sur macOS, %APPDATA% sur Windows
- Léger (aucune dépendance)
- Déjà utilisé par pip, virtualenv, poetry

### Exemple d'utilisation
```python
from platformdirs import user_config_dir, user_data_dir, user_cache_dir

config_dir = user_config_dir("rekall")  # ~/.config/rekall (Linux/Mac)
data_dir = user_data_dir("rekall")      # ~/.local/share/rekall (Linux/Mac)
cache_dir = user_cache_dir("rekall")    # ~/.cache/rekall (Linux/Mac)
```

---

## 2. Pattern de Résolution des Chemins

### Problème
Multiples sources possibles pour les chemins (CLI, env, local, config, XDG). Comment gérer la priorité ?

### Pattern Choisi: Chain of Responsibility simplifié

```python
class PathResolver:
    """Résout les chemins selon l'ordre de priorité défini dans la spec."""

    SOURCES = [
        "_from_cli",      # --db-path, --config-path
        "_from_env",      # REKALL_HOME, REKALL_DB_PATH
        "_from_local",    # .rekall/ in cwd
        "_from_config",   # User config file
        "_from_xdg",      # $XDG_* vars
        "_from_default",  # platformdirs
    ]

    @classmethod
    def resolve(cls, cli_args: dict = None) -> ResolvedPaths:
        for source_method in cls.SOURCES:
            result = getattr(cls, source_method)(cli_args)
            if result is not None:
                return result
        raise RuntimeError("No valid path found")  # Should never happen
```

### Rationale
- Facile à tester (chaque source isolée)
- Extensible (ajouter une source = ajouter une méthode)
- Priorité claire et documentée

---

## 3. Migration des Anciennes Installations

### Problème
Les utilisateurs existants ont `~/.rekall/`. Comment migrer sans perte de données ?

### Stratégie Choisie: Copie avec Prompt

1. **Détection au démarrage**
   ```python
   legacy_path = Path.home() / ".rekall"
   if legacy_path.exists() and not new_path.exists():
       prompt_migration()
   ```

2. **Migration interactive**
   ```
   Rekall a détecté une installation existante dans ~/.rekall/

   Voulez-vous migrer vers le nouvel emplacement XDG ?
     ~/.local/share/rekall/ (recommandé)

   [M]igrer  [C]onserver ancien  [Q]uitter
   ```

3. **Copie (pas déplacement)**
   - Copier knowledge.db et config
   - Créer `.rekall-migrated` marker dans ancien dossier
   - Permet rollback si problème

### Option --legacy
```bash
rekall --legacy add bug "..."  # Force ancien chemin
```

---

## 4. Structure du Projet Local

### Problème
Quelle structure pour `.rekall/` dans un projet ?

### Structure Choisie

```
.rekall/
├── config.toml      # Config spécifique projet (optionnel)
├── knowledge.db     # Base de données
└── .gitignore       # Ignore la DB si sensible
```

### Contenu .gitignore généré
```gitignore
# Uncomment to exclude database from version control
# knowledge.db
```

### Rationale
- Simple et minimal
- L'utilisateur choisit si la DB est versionnée
- Config projet peut overrider config globale

---

## 5. Fichier de Configuration

### Format Choisi: TOML

```toml
# ~/.config/rekall/config.toml

# Chemins personnalisés (optionnel)
data_dir = "/mnt/nas/rekall"

# Préférences
editor = "vim"
default_project = "mon-projet"

# Embeddings (existant)
embeddings_provider = "ollama"
embeddings_model = "nomic-embed-text"
```

### Rationale
- TOML est standard pour les configs Python (pyproject.toml)
- Plus lisible que JSON
- Support natif Python 3.11+ (`tomllib`)
- Fallback `tomli` pour Python 3.10

---

## Sources

- [platformdirs documentation](https://platformdirs.readthedocs.io/)
- [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html)
- [Python Packaging Authority (PyPA)](https://www.pypa.io/)
