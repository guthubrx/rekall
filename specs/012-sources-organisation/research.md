# Phase 0 Research: Sources Organisation

**Branch**: `012-sources-organisation`
**Date**: 2025-12-11

## Résumé

Feature d'amélioration UI. Recherche technique minimale - les patterns sont connus.

## Points Vérifiés

### Tables existantes

- **`source_themes`** : Table de jonction N:N existante (Feature 010)
  - Colonnes : `source_id`, `theme`
  - Index : `idx_source_themes_theme`
  - Fonctions : `add_source_theme()`, `get_source_themes()`, `remove_source_theme()`

### Fonctions DB existantes

| Fonction | Fichier | Usage |
|----------|---------|-------|
| `add_source_theme(source_id, theme)` | db.py | Ajouter un tag |
| `get_source_themes(source_id)` | db.py | Lister les tags d'une source |
| `remove_source_theme(source_id, theme)` | db.py | Retirer un tag |
| `get_sources_by_theme(theme)` | db.py | Sources d'un tag |
| `list_themes_with_counts()` | db.py | Liste tags + compteurs |

### Pattern TUI existant

- Menus : `SimpleMenuApp(title, options)` → retourne index sélectionné
- Saisie : `prompt_input(label)` → retourne texte
- Info : `show_info(message)`, `show_toast(message)`
- Liste sources : Pattern existant dans `_list_all_sources()`

## Décisions Techniques

### Auto-complétion tags

**Décision** : Utiliser les tags existants en base comme suggestions
**Rationale** : Simple, pas de dépendance externe, données déjà disponibles
**Alternative rejetée** : Bibliothèque d'auto-complétion externe (over-engineering)

### Stockage filtres sauvegardés

**Décision** : JSON sérialisé dans colonne TEXT
**Rationale** : Flexible, pas de schéma rigide, SQLite supporte bien
**Alternative rejetée** : Colonnes séparées par critère (trop rigide)

### Logique de filtrage

**Décision** :
- OU entre valeurs d'un même type (tag1 OU tag2)
- ET entre types différents (tags ET score ET statut)

**Rationale** : Comportement intuitif, standard dans les apps de recherche

## Risques Identifiés

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Performance filtres complexes | Faible | Moyen | Index sur colonnes filtrées |
| UI trop complexe | Moyen | Faible | UX progressive (simple → avancé) |

## Conclusion

**READY TO PROCEED** - Pas de bloqueur technique. Infrastructure DB existante.
