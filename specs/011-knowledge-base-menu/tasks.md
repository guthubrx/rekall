# Implementation Tasks: Base de Connaissances Menu

**Branch**: `011-knowledge-base-menu`
**Generated**: 2025-12-11
**Total Tasks**: 11

---

## User Stories Summary

| Story | Priority | Description | Tasks |
|-------|----------|-------------|-------|
| US1 | P1 | Navigation unifiée vers les connaissances | 4 |
| US2 | P2 | Recherche intégrée | 2 |

---

## Phase 1: Setup (Traductions i18n)

**Goal**: Préparer les traductions nécessaires pour la nouvelle section.

- [X] T001 Ajouter la traduction `menu.knowledge_base` ("BASE DE CONNAISSANCES") dans `rekall/i18n.py`
- [X] T002 Ajouter la traduction `menu.search` ("Rechercher") si absente dans `rekall/i18n.py`
- [X] T003 Ajouter la traduction `menu.search.desc` ("Rechercher dans les entrées") dans `rekall/i18n.py`

---

## Phase 2: User Story 1 - Navigation Unifiée (Priority: P1) 🎯 MVP

**Goal**: Créer la section "BASE DE CONNAISSANCES" regroupant browse, search, sources.

**Independent Test**: Lancer `rekall tui`, vérifier que la section "BASE DE CONNAISSANCES" existe avec les 3 sous-entrées et que "RECHERCHE"/"SOURCES" ont disparu.

**Acceptance Criteria**:
1. Section "BASE DE CONNAISSANCES" visible dans le menu
2. Contient : Parcourir, Rechercher, Sources (dans cet ordre)
3. Sections "RECHERCHE" et "SOURCES" supprimées
4. "Parcourir" retiré de la section "GÉNÉRAL"

### Implementation for User Story 1

- [X] T004 [US1] Supprimer les sections "RECHERCHE" et "SOURCES" dans `get_menu_items()` de `rekall/tui.py` (lignes ~5794-5817)
- [X] T005 [US1] Retirer l'entrée "browse" de la section "GÉNÉRAL" dans `get_menu_items()` de `rekall/tui.py`
- [X] T006 [US1] Créer la section "BASE DE CONNAISSANCES" avec browse, search, sources dans `get_menu_items()` de `rekall/tui.py`
- [X] T007 [US1] Ajouter l'action "search" → `action_search` dans le dictionnaire `actions` de `rekall/tui.py` (~ligne 5834)

**Checkpoint**: Menu réorganisé avec 4 sections (GÉNÉRAL, BASE DE CONNAISSANCES, DONNÉES, Quitter)

---

## Phase 3: User Story 2 - Recherche Intégrée (Priority: P2)

**Goal**: Permettre le lancement de la recherche directement depuis le menu.

**Independent Test**: Sélectionner "Rechercher" depuis le menu, entrer un terme, voir les résultats.

**Acceptance Criteria**:
1. L'action "Rechercher" déclenche une invite de saisie
2. La recherche affiche les résultats correspondants

### Implementation for User Story 2

- [X] T008 [US2] Vérifier que `action_search()` existe et fonctionne correctement dans `rekall/tui.py`
- [X] T009 [US2] Tester manuellement le flux complet : menu → Rechercher → saisie → résultats

**Checkpoint**: Fonctionnalité de recherche accessible depuis le menu "BASE DE CONNAISSANCES"

---

## Phase 4: Polish & Validation

**Goal**: Vérification finale et lint.

- [X] T010 Exécuter `ruff check rekall/tui.py rekall/i18n.py` et corriger erreurs
- [X] T011 Exécuter `python -c "from rekall.tui import get_menu_items"` pour vérifier import

---

## Dependencies

```
Phase 1 (Setup i18n)
    │
    ▼
Phase 2 (US1 - Menu restructure)
    │
    ▼
Phase 3 (US2 - Search validation)
    │
    ▼
Phase 4 (Polish)
```

**Note**: Cette feature est linéaire (pas de parallélisme possible car toutes les modifications touchent les mêmes fichiers `tui.py` et `i18n.py`).

---

## Parallel Execution Opportunities

Aucune opportunité de parallélisme - toutes les tâches modifient les mêmes fichiers.

**Exécution recommandée**: Séquentielle T001 → T011

---

## Implementation Strategy

### MVP First (User Story 1)

1. Compléter Phase 1: Setup (T001-T003)
2. Compléter Phase 2: US1 (T004-T007)
3. **STOP et VALIDER**: Tester le menu avec `rekall tui`

### Incremental Delivery

Cette feature étant simple, l'implémentation complète est recommandée en une seule session (~15-30 minutes).

---

## Notes

- Modifications localisées dans 2 fichiers seulement
- Pas de nouvelles dépendances
- Pas de changement de données/schema
- Test manuel TUI requis pour validation finale
