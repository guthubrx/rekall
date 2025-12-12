# Implementation Plan: Sources Organisation

**Branch**: `012-sources-organisation` | **Date**: 2025-12-11 | **Spec**: [spec.md](spec.md)

## Summary

Améliorer l'organisation des sources documentaires dans la TUI Rekall avec :
1. Gestion complète des tags multiples (CRUD, navigation, vrac)
2. Filtres multi-critères combinables
3. Vues sauvegardées pour filtres fréquents

Feature issue du brainstorming - voir `docs/plans/2025-12-11-sources-enhancements-design.md`.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: Textual (TUI), SQLite (via db.py)
**Storage**: SQLite - tables existantes `sources`, `source_themes` + nouvelle table `saved_filters`
**Testing**: pytest + test manuel TUI
**Target Platform**: Terminal (macOS, Linux)
**Project Type**: single (CLI Python)
**Performance Goals**: < 1 seconde pour afficher 1000 sources filtrées
**Constraints**: Rétrocompatibilité avec sources existantes, pas de migration destructive
**Scale/Scope**: ~600 lignes de code (estimation brainstorming)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Exigence | Statut |
|---------|----------|--------|
| I | Documentation en français | ✅ |
| III | Process SpecKit suivi | ✅ |
| VII | ADR si décision structurante | N/A (pas de nouvelle archi) |
| XV | Tests avant commit | ✅ À faire |
| XVI | Worktree dédié | ✅ Branche créée |
| XVII | Capture DevKMS si applicable | ✅ À évaluer |

**Résultat** : ✅ PASS - Pas de violation

## Project Structure

### Documentation (this feature)

```text
specs/012-sources-organisation/
├── spec.md              # Spécification (fait)
├── plan.md              # Ce fichier
├── research.md          # Phase 0 (minimal)
├── quickstart.md        # Guide démarrage rapide
└── tasks.md             # Phase 2 (via /speckit.tasks)
```

### Source Code (repository root)

```text
rekall/
├── db.py                # MODIFIÉ - Nouvelles fonctions DB (tags, filtres, vues)
├── tui.py               # MODIFIÉ - UI pour tags et filtres
├── i18n.py              # MODIFIÉ - Nouvelles traductions
└── models.py            # MODIFIÉ - Dataclass SavedFilter

tests/
└── test_db.py           # Nouveaux tests pour tags/filtres
```

**Structure Decision**: Projet single Python existant. Modifications localisées dans les fichiers existants + nouvelle table DB.

## Implementation Approach

### Phase 1 : Tags Multiples (US1-US3)

**Base de données** (`rekall/db.py`):
- Table `source_themes` existe déjà (relation N:N)
- Fonctions existantes : `add_source_theme()`, `get_source_themes()`, `remove_source_theme()`
- À ajouter : `get_all_tags_with_counts()`, `get_sources_by_tags()`

**TUI** (`rekall/tui.py`):
- Modifier `_add_standalone_source()` : champ tags (virgules)
- Nouveau `_edit_source_tags()` : ajouter/retirer tags
- Nouveau `_browse_by_tag()` : liste tags → sources
- Auto-complétion basée sur tags existants

### Phase 2 : Édition en vrac (US4)

**TUI** (`rekall/tui.py`):
- Mode sélection multiple dans liste sources
- Actions "Ajouter tag à sélection", "Retirer tag de sélection"

### Phase 3 : Filtres Multi-critères (US5)

**Base de données** (`rekall/db.py`):
- Nouvelle fonction `search_sources_advanced()` avec paramètres :
  - `tags: list[str]` (OU logique)
  - `score_min: int`, `score_max: int`
  - `statuses: list[str]`
  - `roles: list[str]`
  - `last_used_days: int`
  - `text_search: str`

**TUI** (`rekall/tui.py`):
- Nouveau `_advanced_search_sources()` : formulaire de filtres
- Affichage résultats avec tri par colonne

### Phase 4 : Vues Sauvegardées (US6)

**Base de données** (`rekall/db.py`):
- Nouvelle table `saved_filters`:
  ```sql
  CREATE TABLE saved_filters (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    filter_json TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
  )
  ```
- Fonctions : `save_filter()`, `get_saved_filters()`, `delete_saved_filter()`, `apply_saved_filter()`

**TUI** (`rekall/tui.py`):
- Action "Sauvegarder cette vue" après filtrage
- Menu "Mes vues" avec liste et application

### Traductions (i18n.py)

Nouvelles clés :
- `tags.title`, `tags.add`, `tags.remove`, `tags.edit`
- `tags.browse_by_tag`, `tags.no_tags`
- `filter.title`, `filter.apply`, `filter.save`, `filter.saved_views`
- `filter.no_results`, `filter.by_score`, `filter.by_status`, etc.

## Complexity Tracking

> Aucune violation de complexité - Feature d'amélioration UI.

| Métrique | Valeur | Limite |
|----------|--------|--------|
| Fichiers modifiés | 4 | < 10 ✅ |
| Lignes de code | ~600 | < 1000 ✅ |
| Nouvelles tables | 1 | < 3 ✅ |
| Nouvelles dépendances | 0 | 0 ✅ |

## Tests Requis

| Test | Type | Critère |
|------|------|---------|
| Lint (ruff) | Auto | 0 erreur |
| pytest | Auto | 100% pass |
| Import check | Auto | Pas d'erreur import |
| TUI tags | Manuel | CRUD tags fonctionne |
| TUI filtres | Manuel | Filtres combinés OK |
| TUI vues | Manuel | Save/load vues OK |
