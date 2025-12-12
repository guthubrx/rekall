# Phase 0 Research: Base de Connaissances Menu

**Branch**: `011-knowledge-base-menu`
**Date**: 2025-12-11

## Résumé

Feature de refactoring UI simple. Pas de recherche technique nécessaire.

## Points vérifiés

### Structure du menu actuel

- **Fichier**: `rekall/tui.py`, fonction `get_menu_items()` (lignes 5794-5817)
- **Format**: Tuples `(action_key, label, description)`
- **Sections**: Marqueurs `("__section__", "NOM", "")`
- **Spacers**: `("__spacer__", "", "")`

### Actions existantes

- `action_browse()` : Navigation des entrées ✅
- `action_search()` : Recherche avec prompt ✅
- `action_sources()` : Dashboard Sources ✅

### Traductions existantes

- `menu.browse` : "Parcourir les entrées" ✅
- `menu.sources` : "Sources documentaires" ✅
- `menu.search` : À vérifier existence

## Décisions

Aucune décision architecturale requise - refactoring simple du menu.

## Risques identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression actions existantes | Faible | Moyen | Test manuel TUI |
| Traduction manquante | Faible | Faible | Vérifier i18n.py avant |

## Conclusion

**READY TO PROCEED** - Pas de bloqueur technique.
