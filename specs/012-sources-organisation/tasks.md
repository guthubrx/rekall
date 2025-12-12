# Implementation Tasks: Sources Organisation

**Branch**: `012-sources-organisation`
**Generated**: 2025-12-11
**Total Tasks**: 35

---

## User Stories Summary

| Story | Priority | Description | Tasks |
|-------|----------|-------------|-------|
| US1 | P1 | Tags à la création | 5 |
| US2 | P1 | Édition des tags | 4 |
| US3 | P1 | Navigation par tag | 4 |
| US4 | P2 | Édition en vrac | 4 |
| US5 | P2 | Filtres multi-critères | 7 |
| US6 | P3 | Vues sauvegardées | 6 |

---

## Phase 1: Setup (Traductions + Migration DB)

**Goal**: Préparer l'infrastructure (traductions, migration schema).

- [X] T001 [P] Ajouter les traductions tags (`tags.*`) dans `rekall/i18n.py`
- [X] T002 [P] Ajouter les traductions filtres (`filter.*`) dans `rekall/i18n.py`
- [X] T003 Ajouter MIGRATIONS[10] avec CREATE TABLE saved_filters dans `rekall/db.py`
- [X] T004 Mettre à jour CURRENT_SCHEMA_VERSION = 10 dans `rekall/db.py`
- [X] T005 Ajouter test_migration_v10() dans `tests/test_db.py`

---

## Phase 2: Foundational (Fonctions DB partagées)

**Goal**: Fonctions DB utilisées par plusieurs user stories.

**Blocking**: Toutes les user stories dépendent de cette phase.

- [X] T006 Implémenter `get_all_tags_with_counts()` dans `rekall/db.py`
- [X] T007 Implémenter `get_sources_by_tags(tags: list[str])` dans `rekall/db.py`
- [X] T008 Ajouter test_get_all_tags_with_counts() dans `tests/test_db.py`
- [X] T009 Ajouter test_get_sources_by_tags() dans `tests/test_db.py`

**Checkpoint**: Fonctions DB pour tags disponibles.

---

## Phase 3: User Story 1 - Tags à la création (Priority: P1) 🎯 MVP

**Goal**: Permettre de saisir plusieurs tags lors de la création d'une source.

**Independent Test**: Créer une source avec 3 tags séparés par virgule, vérifier qu'ils sont tous associés.

**Acceptance Criteria**:
1. Champ tags dans formulaire création (virgules)
2. Auto-complétion sur tags existants
3. Tags optionnels (peut être vide)

### Implementation for User Story 1

- [X] T010 [US1] Implémenter `get_tags_suggestions(prefix: str)` pour auto-complétion dans `rekall/db.py`
- [X] T011 [US1] Modifier `_add_standalone_source()` pour ajouter champ tags avec prompt dans `rekall/tui.py`
- [X] T012 [US1] Implémenter `_parse_tags_input(text: str) -> list[str]` helper dans `rekall/tui.py`
- [X] T013 [US1] Appeler `add_source_theme()` pour chaque tag après création source dans `rekall/tui.py`
- [X] T014 [US1] Ajouter test_tags_at_creation() dans `tests/test_db.py`

**Checkpoint**: Sources créées avec tags multiples.

---

## Phase 4: User Story 2 - Édition des tags (Priority: P1)

**Goal**: Permettre de modifier les tags d'une source existante.

**Independent Test**: Ouvrir une source, ajouter un tag, retirer un autre, vérifier les changements.

**Acceptance Criteria**:
1. Action "Modifier les tags" dans fiche source
2. Voir tags actuels avec option de retirer
3. Ajouter nouveaux tags

### Implementation for User Story 2

- [X] T015 [US2] Créer `_edit_source_tags(db, source)` fonction dans `rekall/tui.py`
- [X] T016 [US2] Afficher tags actuels avec checkboxes pour retirer dans `_edit_source_tags()`
- [X] T017 [US2] Ajouter champ saisie pour nouveaux tags dans `_edit_source_tags()`
- [X] T018 [US2] Intégrer action "Modifier les tags" dans `_show_source_detail()` de `rekall/tui.py`

**Checkpoint**: Tags modifiables depuis fiche source.

---

## Phase 5: User Story 3 - Navigation par tag (Priority: P1)

**Goal**: Voir la liste des tags avec compteurs et naviguer vers les sources.

**Independent Test**: Accéder à "Parcourir par tag", sélectionner un tag, voir les sources correspondantes.

**Acceptance Criteria**:
1. Menu "Parcourir par tag" dans dashboard Sources
2. Liste tags avec compteurs
3. Sélection tag → liste sources

### Implementation for User Story 3

- [X] T019 [US3] Créer `_browse_by_tag(db)` fonction dans `rekall/tui.py`
- [X] T020 [US3] Afficher liste tags avec compteurs via `get_all_tags_with_counts()` dans `_browse_by_tag()`
- [X] T021 [US3] Afficher sources du tag sélectionné via `get_sources_by_tags()` dans `_browse_by_tag()`
- [X] T022 [US3] Ajouter action "Parcourir par tag" dans `action_sources()` de `rekall/tui.py`

**Checkpoint**: Navigation tag → sources fonctionnelle.

---

## Phase 6: User Story 4 - Édition en vrac (Priority: P2)

**Goal**: Sélectionner plusieurs sources et leur ajouter/retirer un tag commun.

**Independent Test**: Sélectionner 5 sources, ajouter le tag "archive", vérifier que les 5 ont le tag.

**Acceptance Criteria**:
1. Mode sélection multiple dans liste sources
2. Action "Ajouter tag à sélection"
3. Action "Retirer tag de sélection"

### Implementation for User Story 4

- [X] T023 [US4] Créer `_bulk_select_sources(db)` avec mode checkbox dans `rekall/tui.py`
- [X] T024 [US4] Implémenter `_bulk_add_tag(db, source_ids: list[int], tag: str)` dans `rekall/tui.py`
- [X] T025 [US4] Implémenter `_bulk_remove_tag(db, source_ids: list[int], tag: str)` dans `rekall/tui.py`
- [X] T026 [US4] Intégrer actions bulk dans menu `_list_all_sources()` de `rekall/tui.py`

**Checkpoint**: Édition tags en masse fonctionnelle.

---

## Phase 7: User Story 5 - Filtres multi-critères (Priority: P2)

**Goal**: Filtrer les sources selon plusieurs critères combinés.

**Independent Test**: Filtrer par tag "go" + score > 50 + statut "active", voir uniquement les sources correspondantes.

**Acceptance Criteria**:
1. Formulaire de filtres multi-critères
2. Filtrage par tags (OU), score, statut, rôle, fraîcheur, texte
3. Combinaison des critères (ET entre types)

### Implementation for User Story 5

- [X] T027 [US5] Implémenter `search_sources_advanced()` avec tous les paramètres dans `rekall/db.py`
- [X] T028 [US5] Ajouter test_search_sources_advanced() dans `tests/test_db.py`
- [X] T029 [US5] Créer `_advanced_search_sources(db)` formulaire dans `rekall/tui.py`
- [X] T030 [US5] Implémenter sélection multi-tags dans formulaire de `_advanced_search_sources()`
- [X] T031 [US5] Implémenter sélection score/statut/rôle/fraîcheur dans `_advanced_search_sources()`
- [X] T032 [US5] Afficher résultats filtrés avec tri dans `_advanced_search_sources()`
- [X] T033 [US5] Ajouter action "Recherche avancée" dans `action_sources()` de `rekall/tui.py`

**Checkpoint**: Filtres combinés fonctionnels.

---

## Phase 8: User Story 6 - Vues sauvegardées (Priority: P3)

**Goal**: Sauvegarder et réappliquer des combinaisons de filtres.

**Independent Test**: Créer un filtre, le sauvegarder comme "Sources Go actives", le réappliquer depuis le menu.

**Acceptance Criteria**:
1. Sauvegarder filtre actif avec nom
2. Lister les vues sauvegardées
3. Appliquer une vue
4. Supprimer une vue

### Implementation for User Story 6

- [X] T034 [US6] Ajouter dataclass `SavedFilter` dans `rekall/models.py`
- [X] T035 [US6] Implémenter `save_filter(name, filter_dict)` dans `rekall/db.py`
- [X] T036 [US6] Implémenter `get_saved_filters()` dans `rekall/db.py`
- [X] T037 [US6] Implémenter `delete_saved_filter(filter_id)` dans `rekall/db.py`
- [X] T038 [US6] Créer `_manage_saved_views(db)` dans `rekall/tui.py`
- [X] T039 [US6] Intégrer "Sauvegarder vue" après filtrage et "Mes vues" dans `action_sources()` de `rekall/tui.py`

**Checkpoint**: Vues persistantes fonctionnelles.

---

## Phase 9: Polish & Validation

**Goal**: Tests finaux et validation.

- [X] T040 Exécuter `ruff check rekall/` et corriger erreurs lint
- [X] T041 Exécuter `python -m pytest tests/` et vérifier 100% pass
- [X] T042 Test manuel TUI : parcours complet tags + filtres + vues

---

## Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational DB)
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
Phase 3 (US1)     Phase 4 (US2)     Phase 5 (US3)
Tags création     Édition tags      Navigation tag
    │                  │                  │
    └──────────────────┴──────────────────┘
                       │
                       ▼
                 Phase 6 (US4)
                 Édition vrac
                       │
                       ▼
                 Phase 7 (US5)
                 Filtres
                       │
                       ▼
                 Phase 8 (US6)
                 Vues sauvegardées
                       │
                       ▼
                 Phase 9 (Polish)
```

---

## Parallel Execution Opportunities

### Phase 1 (Setup)
```
T001 (traductions tags) ─── [P] parallel avec T002 (traductions filtres)
T003-T005 (migration) → Séquentiel
```

### Phases 3-4-5 (US1, US2, US3)
```
Après Phase 2, ces 3 user stories peuvent être développées en parallèle
car elles touchent des fonctions TUI différentes.
```

### Phase 7 (US5)
```
T027-T028 (DB) → Séquentiel
T029-T032 (TUI) → Séquentiel (même fonction)
```

---

## Implementation Strategy

### MVP First (User Stories 1-3)

1. Compléter Phase 1: Setup
2. Compléter Phase 2: Foundational
3. Compléter Phase 3-4-5: Tags multiples (US1, US2, US3)
4. **STOP et VALIDER**: Tester le cycle complet tags

### Incremental Delivery

| Livrable | Phases | Valeur |
|----------|--------|--------|
| **MVP Tags** | 1-5 | Tags création + édition + navigation |
| **+ Vrac** | 6 | Édition massive |
| **+ Filtres** | 7 | Recherche avancée |
| **+ Vues** | 8 | Persistance filtres |
| **Release** | 9 | Version stable |

---

## Notes

- Les fonctions `add_source_theme()`, `get_source_themes()`, `remove_source_theme()` existent déjà (Feature 010)
- La table `source_themes` existe déjà - pas besoin de migration pour les tags
- Seule la table `saved_filters` nécessite une migration (v10)
- Tests manuels TUI recommandés à chaque checkpoint
