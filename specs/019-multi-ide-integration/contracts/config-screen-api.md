# API Contract: Config Screen TUI

**Feature**: 019-multi-ide-integration
**Module**: `rekall/tui_main.py` (class `ConfigApp`)
**Date**: 2025-12-13

---

## Vue d'ensemble

L'écran de configuration est divisé en 2 sections principales :

1. **INTÉGRATIONS** - Liste des IDEs avec colonnes Global/Local
2. **SPECKIT** - Configuration Article 99 et patches (si Speckit installé)

---

## Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ ╔═══════════════════════════════════════════════════════════╗  │
│ ║  ██████  ███████ ██   ██  █████  ██      ██               ║  │
│ ║  ██   ██ ██      ██  ██  ██   ██ ██      ██               ║  │
│ ║  ██████  █████   █████   ███████ ██      ██               ║  │
│ ║  ██   ██ ██      ██  ██  ██   ██ ██      ██               ║  │
│ ║  ██   ██ ███████ ██   ██ ██   ██ ███████ ███████          ║  │
│ ╚═══════════════════════════════════════════════════════════╝  │
├─────────────────────────────────────────────────────────────────┤
│ IDE détecté: Claude Code (global)                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ ═══ INTÉGRATIONS ═══════════════════════════════════════════   │
│                                                                 │
│                          Global    Local                        │
│  ► Claude Code            [✓]      [ ]                          │
│    Cursor                 [n/a]    [ ]                          │
│    GitHub Copilot         [n/a]    [ ]                          │
│    Windsurf               [n/a]    [ ]                          │
│    Cline                  [n/a]    [ ]                          │
│    Zed                    [ ]      [ ]                          │
│    Continue.dev           [ ]      [ ]                          │
│                                                                 │
│ ═══ SPECKIT ════════════════════════════════════════════════   │
│                                                                 │
│  Article 99: Court                                              │
│  ★ recommandé: Micro (skill Claude installée en global)         │
│                                                                 │
│    ( ) Micro     (~50 tokens)                                   │
│    (●) Court     (~350 tokens)                                  │
│    ( ) Extensif  (~1000 tokens)                                 │
│                                                                 │
│  Patches: 3/6 installés                                         │
│    [✓] speckit.implement.md                                     │
│    [✓] speckit.plan.md                                          │
│    [✓] speckit.tasks.md                                         │
│    [ ] speckit.clarify.md                                       │
│    [ ] speckit.specify.md                                       │
│    [ ] speckit.hotfix.md                                        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│ ↑↓ navigate • Space toggle • i install • r remove • ? help     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Widgets

### `IDEStatusRow`

Widget représentant une ligne IDE avec checkboxes Global/Local.

```python
class IDEStatusRow(Widget):
    """Ligne de statut pour un IDE."""

    def __init__(
        self,
        ide: IDE,
        local_installed: bool,
        global_installed: bool,
        global_supported: bool,
        is_detected: bool = False,
    ):
        ...

    # Messages émis
    class LocalToggled(Message):
        ide_id: str
        enabled: bool

    class GlobalToggled(Message):
        ide_id: str
        enabled: bool
```

**Affichage**:
- `[✓]` = installé
- `[ ]` = non installé
- `[n/a]` = non supporté (grisé)
- `►` = IDE détecté (highlight)

---

### `Article99Selector`

Widget pour sélectionner la version de l'Article 99.

```python
class Article99Selector(Widget):
    """Sélecteur de version Article 99 avec recommandation."""

    def __init__(
        self,
        current_version: Article99Version | None,
        recommended_version: Article99Version,
        recommendation_reason: str,
    ):
        ...

    # Messages émis
    class VersionChanged(Message):
        new_version: Article99Version
```

**Affichage**:
- RadioButtons pour les 3 versions
- Badge `★ recommandé` sur la version recommandée
- Raison affichée en dessous

---

### `SpeckitPatchList`

Widget pour la liste des patches Speckit.

```python
class SpeckitPatchList(Widget):
    """Liste des patches Speckit avec toggle."""

    def __init__(self, patches: list[SpeckitPatch]):
        ...

    # Messages émis
    class PatchToggled(Message):
        command_name: str
        enabled: bool
```

---

## Actions / Bindings

| Touche | Action | Description |
|--------|--------|-------------|
| `↑/↓` | `action_navigate` | Naviguer dans la liste |
| `Space` | `action_toggle` | Toggle l'élément sélectionné |
| `i` | `action_install_selected` | Installer l'intégration sélectionnée |
| `r` | `action_remove_selected` | Désinstaller l'intégration sélectionnée |
| `Tab` | `action_switch_section` | Basculer entre INTÉGRATIONS et SPECKIT |
| `?` | `action_show_help` | Afficher l'aide |
| `Esc` | `action_quit` | Fermer l'écran |
| `q` | `action_quit` | Fermer l'écran |

---

## États de l'écran

```python
@dataclass
class ConfigScreenState:
    # Section active
    active_section: Literal["integrations", "speckit"]

    # Sélection
    selected_row_idx: int  # Index dans la section active

    # Données chargées
    detected_ide: DetectedIDE
    ide_statuses: dict[str, IntegrationStatus]
    speckit_visible: bool  # False si ~/.speckit/ absent
    speckit_status: SpeckitStatus | None

    # UI state
    show_help_overlay: bool
    notification_message: str | None
    notification_timeout: float
```

---

## Flux de données

### Initialisation

```
on_mount()
    │
    ├─► detect_ide(cwd) ───► detected_ide
    │
    ├─► get_all_bundle_statuses(cwd) ───► ide_statuses
    │
    ├─► is_speckit_installed() ───► speckit_visible
    │
    └─► if speckit_visible:
            get_article99_recommendation(cwd) ───► speckit_status
            get_speckit_patches_status() ───► patches
```

### Toggle IDE Global

```
Space pressed on IDE row (Global column)
    │
    ├─► if not installed:
    │       install_bundle(ide_id, cwd, GLOBAL)
    │       ───► refresh_status()
    │       ───► show_notification("✓ Installé")
    │
    └─► if installed:
            uninstall_bundle(ide_id, cwd, GLOBAL)
            ───► refresh_status()
            ───► show_notification("✓ Désinstallé")
```

### Changement Article 99

```
Article99Selector.VersionChanged
    │
    ├─► install_article99(new_version)
    │
    └─► refresh_speckit_status()
```

---

## Notifications

Le widget de notification affiche des messages temporaires :

```python
def show_notification(self, message: str, timeout: float = 3.0):
    """Affiche une notification temporaire."""
    ...
```

**Messages types**:
- `✓ Claude Code installé (global)`
- `✓ Article 99 mis à jour (Court → Micro)`
- `⚠ Fichier existant - backup créé`
- `✗ Erreur: permission denied`

---

## Accessibilité

- Navigation complète au clavier
- Labels explicites pour screen readers
- Couleurs avec contraste suffisant (WCAG AA)
- Focus visible sur l'élément sélectionné
