# API Contract: Integrations Module

**Feature**: 019-multi-ide-integration
**Module**: `rekall/integrations/__init__.py`
**Date**: 2025-12-13

---

## Fonctions Publiques

### Détection IDE

#### `detect_ide(base_path: Path) -> DetectedIDE`

Détecte l'IDE installé en vérifiant les paths locaux puis globaux.

**Paramètres**:
- `base_path`: Chemin du projet (généralement `Path.cwd()`)

**Retourne**:
- `DetectedIDE` avec l'IDE prioritaire détecté

**Algorithme**:
1. Pour chaque IDE par ordre de priorité (Claude=1, Cursor=2, ...)
2. Vérifier `base_path / local_detection_path`
3. Si trouvé → retourner avec `scope=LOCAL`
4. Vérifier `Path.home() / global_detection_path`
5. Si trouvé → retourner avec `scope=GLOBAL`
6. Si aucun IDE trouvé → retourner `DetectedIDE(ide=None, ...)`

**Exemple**:
```python
result = detect_ide(Path.cwd())
# DetectedIDE(ide=IDE(id="claude", ...), scope=Scope.LOCAL, detection_path=".claude/")
```

---

#### `get_all_detected_ides(base_path: Path) -> list[tuple[IDE, Scope]]`

Retourne tous les IDEs détectés (pas seulement le prioritaire).

**Paramètres**:
- `base_path`: Chemin du projet

**Retourne**:
- Liste de tuples (IDE, Scope) triés par priorité

**Exemple**:
```python
ides = get_all_detected_ides(Path.cwd())
# [(IDE(id="claude"), Scope.GLOBAL), (IDE(id="cursor"), Scope.LOCAL)]
```

---

### Gestion des Bundles

#### `install_bundle(ide_id: str, base_path: Path, scope: Scope) -> list[str]`

Installe le bundle complet pour un IDE (instructions + MCP + hooks).

**Paramètres**:
- `ide_id`: Identifiant de l'IDE ("claude", "cursor", etc.)
- `base_path`: Chemin du projet
- `scope`: `Scope.GLOBAL` ou `Scope.LOCAL`

**Retourne**:
- Liste des chemins de fichiers créés

**Exceptions**:
- `ValueError`: IDE inconnu ou scope non supporté
- `FileExistsError`: Fichier existe déjà avec contenu différent

**Exemple**:
```python
files = install_bundle("claude", Path.cwd(), Scope.GLOBAL)
# ["/Users/x/.claude/commands/rekall.md", "/Users/x/.claude/commands/rekall/...", ...]
```

---

#### `uninstall_bundle(ide_id: str, base_path: Path, scope: Scope) -> bool`

Désinstalle le bundle complet pour un IDE.

**Paramètres**:
- `ide_id`: Identifiant de l'IDE
- `base_path`: Chemin du projet
- `scope`: Scope à désinstaller

**Retourne**:
- `True` si des fichiers ont été supprimés, `False` sinon

**Exemple**:
```python
removed = uninstall_bundle("claude", Path.cwd(), Scope.GLOBAL)
# True
```

---

#### `get_bundle_status(ide_id: str, base_path: Path) -> IntegrationStatus`

Retourne le statut d'installation d'un IDE.

**Paramètres**:
- `ide_id`: Identifiant de l'IDE
- `base_path`: Chemin du projet

**Retourne**:
- `IntegrationStatus` avec les statuts local/global

**Exemple**:
```python
status = get_bundle_status("claude", Path.cwd())
# IntegrationStatus(ide_id="claude", local_installed=False, global_installed=True, global_supported=True)
```

---

#### `get_all_bundle_statuses(base_path: Path) -> dict[str, IntegrationStatus]`

Retourne le statut de tous les IDEs.

**Retourne**:
- Dict `{ide_id: IntegrationStatus}`

---

### Article 99

#### `get_article99_recommendation(base_path: Path) -> Article99Config`

Calcule la version recommandée de l'Article 99.

**Paramètres**:
- `base_path`: Chemin du projet

**Retourne**:
- `Article99Config` avec version recommandée et raison

**Logique**:
1. Vérifier si skill Claude installée (global OU local)
   - Si oui → MICRO, raison="skill Claude installée en {scope}"
2. Vérifier si MCP configuré pour n'importe quel IDE
   - Si oui → COURT, raison="MCP configuré"
3. Sinon → EXTENSIF, raison="CLI seulement"

**Exemple**:
```python
config = get_article99_recommendation(Path.cwd())
# Article99Config(
#     version=None,
#     installed=False,
#     recommended_version=Article99Version.MICRO,
#     recommendation_reason="skill Claude installée en global"
# )
```

---

#### `install_article99(version: Article99Version) -> bool`

Installe ou met à jour l'Article 99 dans la constitution Speckit.

**Paramètres**:
- `version`: Version à installer (MICRO, COURT, EXTENSIF)

**Retourne**:
- `True` si installé/mis à jour, `False` si déjà à jour

**Préconditions**:
- `~/.speckit/constitution.md` doit exister

**Exemple**:
```python
installed = install_article99(Article99Version.COURT)
# True
```

---

#### `uninstall_article99() -> bool`

Supprime l'Article 99 de la constitution.

**Retourne**:
- `True` si supprimé, `False` si n'existait pas

---

### Patches Speckit

#### `get_speckit_patches_status() -> list[SpeckitPatch]`

Retourne le statut de tous les patches Speckit disponibles.

**Retourne**:
- Liste de `SpeckitPatch` avec statut d'installation

---

#### `install_speckit_patch(command_name: str, use_mcp: bool) -> bool`

Installe un patch dans une commande Speckit.

**Paramètres**:
- `command_name`: Nom du fichier (ex: "speckit.implement.md")
- `use_mcp`: Si True, utilise la version MCP du patch

**Retourne**:
- `True` si patché, `False` si déjà patché ou fichier inexistant

---

#### `uninstall_speckit_patch(command_name: str) -> bool`

Supprime un patch d'une commande Speckit.

---

### Utilitaires

#### `is_speckit_installed() -> bool`

Vérifie si Speckit est installé (`~/.speckit/` existe).

---

#### `get_ide_by_id(ide_id: str) -> IDE | None`

Retourne la définition d'un IDE par son identifiant.

---

#### `get_all_ides() -> list[IDE]`

Retourne la liste de tous les IDEs supportés, triés par priorité.

---

## Constantes Exportées

```python
# Liste des IDEs supportés
SUPPORTED_IDES: list[IDE]

# Versions Article 99
ARTICLE_99_MICRO: str    # ~50 tokens
ARTICLE_99_COURT: str    # ~350 tokens
ARTICLE_99_EXTENSIF: str # ~1000 tokens

# Contenu des instructions par IDE
IDE_INSTRUCTIONS: dict[str, str]  # ide_id -> contenu

# Configuration MCP par IDE
IDE_MCP_CONFIGS: dict[str, dict]  # ide_id -> config JSON
```

---

## Événements / Callbacks

### `on_bundle_installed(ide_id: str, scope: Scope, files: list[str])`

Callback appelé après installation réussie d'un bundle.

### `on_bundle_uninstalled(ide_id: str, scope: Scope)`

Callback appelé après désinstallation d'un bundle.

### `on_article99_changed(old_version: Article99Version | None, new_version: Article99Version | None)`

Callback appelé après modification de l'Article 99.
