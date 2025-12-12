# Implementation Plan: Base de Connaissances Menu

**Branch**: `011-knowledge-base-menu` | **Date**: 2025-12-11 | **Spec**: [spec.md](spec.md)

## Summary

Réorganiser le menu principal de la TUI Rekall pour créer une section unifiée "BASE DE CONNAISSANCES" regroupant :
- Parcourir les entrées (browse)
- Rechercher (search)
- Sources documentaires (sources)

Feature de refactoring UI simple, sans nouvelles entités de données.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: Textual (TUI), Typer (CLI)
**Storage**: N/A (pas de changement de données)
**Testing**: pytest + test manuel TUI
**Target Platform**: Terminal (macOS, Linux)
**Project Type**: single (CLI Python)
**Performance Goals**: N/A (UI statique)
**Constraints**: Maintenir la compatibilité avec toutes les fonctionnalités existantes
**Scale/Scope**: ~50 lignes de code modifiées dans `tui.py` + traductions i18n

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Exigence | Statut |
|---------|----------|--------|
| I | Documentation en français | ✅ |
| III | Process SpecKit suivi | ✅ |
| VII | ADR si décision structurante | N/A (pas de décision archi) |
| XV | Tests avant commit | ✅ À faire |
| XVI | Worktree dédié | ✅ Branche créée |
| XVII | Capture DevKMS si applicable | ✅ À évaluer |

**Résultat** : ✅ PASS - Pas de violation

## Project Structure

### Documentation (this feature)

```text
specs/011-knowledge-base-menu/
├── spec.md              # Spécification
├── plan.md              # Ce fichier
├── research.md          # Phase 0 (minimal)
├── quickstart.md        # Guide démarrage rapide
└── tasks.md             # Phase 2 (via /speckit.tasks)
```

### Source Code (repository root)

```text
rekall/
├── tui.py               # MODIFIÉ - Réorganisation menu
├── i18n.py              # MODIFIÉ - Nouvelles traductions
└── cli.py               # Non modifié

tests/
└── test_tui.py          # Test manuel de la TUI
```

**Structure Decision**: Projet single Python existant. Modifications localisées dans `tui.py` (fonction `get_menu_items()`) et `i18n.py` (nouvelles clés).

## Implementation Approach

### Modifications requises

1. **`rekall/tui.py`** - Fonction `get_menu_items()` (lignes 5794-5817)
   - Supprimer sections "RECHERCHE" et "SOURCES"
   - Retirer "browse" de section "GÉNÉRAL"
   - Créer section "BASE DE CONNAISSANCES" avec browse, search, sources

2. **`rekall/tui.py`** - Dictionnaire `actions` (ligne 5834)
   - Ajouter action "search" → `action_search`

3. **`rekall/i18n.py`** - Nouvelles traductions
   - `menu.knowledge_base` : "Base de connaissances"
   - `menu.knowledge_base.desc` : Description de la section
   - `menu.search` : "Rechercher" (si non existant)
   - `menu.search.desc` : Description recherche

### Tests requis

| Test | Type | Critère |
|------|------|---------|
| Lint (ruff) | Auto | 0 erreur |
| Import check | Auto | `python -c "from rekall.tui import get_menu_items"` |
| TUI manual | Manuel | Menu affiche 4 sections, actions fonctionnent |

## Complexity Tracking

> Aucune violation de complexité - Feature simple de refactoring UI.

| Métrique | Valeur | Limite |
|----------|--------|--------|
| Fichiers modifiés | 2 | < 5 ✅ |
| Lignes de code | ~50 | < 200 ✅ |
| Nouvelles dépendances | 0 | 0 ✅ |
