# Implementation Tasks: Intégration Sources & Souvenirs

**Branch**: `009-sources-integration`
**Generated**: 2025-12-11
**Total Tasks**: 47

---

## User Stories Summary

| Story | Priority | Description | Tasks |
|-------|----------|-------------|-------|
| US1 | P1 | Lier un Souvenir à ses Sources | 10 |
| US2 | P1 | Voir les Backlinks d'une Source | 6 |
| US3 | P2 | Scoring Automatique des Sources | 6 |
| US4 | P2 | Boost des Recherches Speckit | 4 |
| US5 | P3 | Dashboard Sources | 6 |
| US6 | P3 | Détection Link Rot | 5 |

---

## Phase 1: Setup

**Goal**: Préparer l'infrastructure de base pour la feature.

- [x] T001 Ajouter les dataclasses Source et EntrySource dans `rekall/models.py`
- [x] T002 Ajouter les fonctions de validation validate_source() et validate_entry_source() dans `rekall/models.py`
- [x] T003 Ajouter les traductions sources (source.*, entry_source.*) dans `rekall/i18n.py`

---

## Phase 2: Foundational (Database Migration)

**Goal**: Créer les tables et la migration v7→v8.
**Blocking**: Toutes les user stories dépendent de cette phase.

- [x] T004 Ajouter MIGRATIONS[8] avec CREATE TABLE sources dans `rekall/db.py`
- [x] T005 Ajouter CREATE TABLE entry_sources dans MIGRATIONS[8] dans `rekall/db.py`
- [x] T006 Ajouter les index (idx_sources_domain, idx_sources_score, idx_entry_sources_*) dans `rekall/db.py`
- [x] T007 Mettre à jour EXPECTED_TABLES et EXPECTED_COLUMNS pour v8 dans `rekall/db.py`
- [x] T008 Ajouter test_migration_v8() dans `tests/test_db.py`

---

## Phase 3: User Story 1 - Lier un Souvenir à ses Sources (P1)

**Goal**: Permettre l'association souvenir↔source à la création et en édition.

**Independent Test**: Créer un souvenir, lui associer une source (thème ou URL), vérifier que le lien est persisté et visible.

**Acceptance Criteria**:
1. Lien créé à l'ajout d'un souvenir avec source
2. Lien ajouté/modifié sur souvenir existant
3. Sources visibles dans le détail du souvenir

### Database Layer

- [x] T009 [US1] Implémenter add_source() dans `rekall/db.py`
- [x] T010 [US1] Implémenter get_source() et get_source_by_domain() dans `rekall/db.py`
- [x] T011 [US1] Implémenter link_entry_to_source() dans `rekall/db.py`
- [x] T012 [US1] Implémenter get_entry_sources() dans `rekall/db.py`
- [x] T013 [US1] Implémenter unlink_entry_from_source() dans `rekall/db.py`

### Helpers

- [x] T014 [P] [US1] Ajouter extract_domain() et normalize_url() dans `rekall/utils.py` (nouveau fichier si nécessaire)

### TUI Layer

- [x] T015 [US1] Ajouter widget SourceInput (autocomplete thèmes/URLs) dans `rekall/tui.py`
- [x] T016 [US1] Modifier AddEntryScreen pour inclure champ Sources dans `rekall/tui.py`
- [x] T017 [US1] Modifier EditEntryScreen pour gérer les sources dans `rekall/tui.py`
- [x] T018 [US1] Modifier EntryDetailScreen pour afficher les sources liées dans `rekall/tui.py`

---

## Phase 4: User Story 2 - Voir les Backlinks d'une Source (P1)

**Goal**: Afficher les souvenirs citant une source avec navigation.

**Independent Test**: Consulter une source, vérifier qu'elle affiche "Cité par N souvenirs" avec la liste cliquable.

**Acceptance Criteria**:
1. Affichage "Cité par N souvenirs" sur une source
2. Message "Aucun souvenir lié" si pas de backlinks
3. Navigation vers le détail du souvenir au clic

### Database Layer

- [x] T019 [US2] Implémenter get_source_backlinks() dans `rekall/db.py`
- [x] T020 [US2] Implémenter count_source_backlinks() dans `rekall/db.py`

### TUI Layer

- [x] T021 [US2] Créer SourceDetailScreen avec affichage backlinks dans `rekall/tui.py`
- [x] T022 [US2] Ajouter widget BacklinksListView (liste cliquable) dans `rekall/tui.py`
- [x] T023 [US2] Implémenter navigation backlink → EntryDetailScreen dans `rekall/tui.py`
- [x] T024 [US2] Ajouter traductions backlinks (backlinks.*, source_detail.*) dans `rekall/i18n.py`

---

## Phase 5: User Story 3 - Scoring Automatique des Sources (P2)

**Goal**: Calculer et maintenir le score personnel de chaque source.

**Independent Test**: Citer une source dans plusieurs souvenirs, vérifier que son score augmente et qu'elle remonte dans le classement.

**Acceptance Criteria**:
1. usage_count incrémenté à chaque citation
2. Score augmente proportionnellement
3. Pénalité de fraîcheur appliquée après 6 mois
4. Tri par score fonctionnel

### Database Layer

- [x] T025 [US3] Implémenter calculate_source_score() (formule composite) dans `rekall/db.py`
- [x] T026 [US3] Implémenter update_source_usage() (increment + recalcul) dans `rekall/db.py`
- [x] T027 [US3] Implémenter recalculate_source_score() dans `rekall/db.py`
- [x] T028 [US3] Implémenter get_top_sources() dans `rekall/db.py`

### Integration

- [x] T029 [US3] Modifier link_entry_to_source() pour appeler update_source_usage() dans `rekall/db.py`
- [x] T030 [US3] Ajouter test_scoring_algorithm() dans `tests/test_db.py`

---

## Phase 6: User Story 4 - Boost des Recherches Speckit (P2)

**Goal**: Prioriser les sources à haut score dans les suggestions de recherche.

**Independent Test**: Lancer une recherche sur un thème, vérifier que les sources à haut score apparaissent en premier.

**Acceptance Criteria**:
1. Sources triées par score dans suggestions
2. Sources à score < 20 déprioritisées
3. Requêtes site:domain.com générées dans l'ordre du score

### Integration Layer

- [x] T031 [US4] Créer get_prioritized_sources_for_theme() dans `rekall/db.py`
- [x] T032 [US4] Créer generate_search_queries() (site:domain par score) dans `rekall/search.py` (nouveau fichier)
- [x] T033 [P] [US4] Exposer API sources triées pour Speckit dans `rekall/cli.py` (commande `rekall sources suggest`)
- [x] T034 [US4] Ajouter traductions search (search.suggestions.*) dans `rekall/i18n.py`

---

## Phase 7: User Story 5 - Dashboard Sources (P3)

**Goal**: Vue d'ensemble des sources avec métriques et catégorisation.

**Independent Test**: Accéder au dashboard, vérifier l'affichage des top sources, sources dormantes, et métriques.

**Acceptance Criteria**:
1. Top 20 sources par score affichées
2. Section "Sources dormantes" (>6 mois)
3. Section "Sources émergentes" (3+ citations/30j)

### Database Layer

- [x] T035 [US5] Implémenter get_dormant_sources() dans `rekall/db.py`
- [x] T036 [US5] Implémenter get_emerging_sources() dans `rekall/db.py`
- [x] T037 [US5] Implémenter list_sources() avec pagination dans `rekall/db.py`

### TUI Layer

- [x] T038 [US5] Créer SourceDashboardScreen dans `rekall/tui.py`
- [x] T039 [US5] Ajouter entrée menu "Sources Documentaires" → SourceDashboardScreen dans `rekall/tui.py`
- [x] T040 [US5] Ajouter traductions dashboard (dashboard.*) dans `rekall/i18n.py`

---

## Phase 8: User Story 6 - Détection Link Rot (P3)

**Goal**: Vérifier quotidiennement l'accessibilité des URLs sources.

**Independent Test**: Ajouter une source avec URL invalide, vérifier que le système détecte et signale le problème.

**Acceptance Criteria**:
1. Vérification HTTP HEAD quotidienne
2. Statut "inaccessible" si 404/erreur
3. Marquage visuel dans le dashboard

### Core

- [x] T041 [P] [US6] Créer check_url_accessibility() (HTTP HEAD) dans `rekall/link_rot.py` (nouveau fichier)
- [x] T042 [US6] Implémenter get_sources_to_verify() dans `rekall/db.py`
- [x] T043 [US6] Implémenter update_source_status() dans `rekall/db.py`

### CLI/Integration

- [x] T044 [US6] Ajouter commande `rekall sources verify` dans `rekall/cli.py`
- [x] T045 [US6] Afficher icône ⚠️ pour sources inaccessibles dans SourceDashboardScreen dans `rekall/tui.py`

---

## Phase 9: Polish & Cross-Cutting

**Goal**: Finalisation, documentation et tests d'intégration.

- [x] T046 Ajouter tests d'intégration end-to-end dans `tests/test_integration_sources.py`
- [x] T047 Mettre à jour le README avec documentation sources dans `README.md`

---

## Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (DB Migration) ─────────────────────────────────────┐
    │                                                        │
    ├──────────────────┬──────────────────┐                  │
    ▼                  ▼                  ▼                  │
Phase 3 (US1)      Phase 4 (US2)      (blocked)             │
    │                  │                                     │
    └────────┬─────────┘                                     │
             ▼                                               │
         Phase 5 (US3) ◄─────────────────────────────────────┘
             │
    ┌────────┴────────┐
    ▼                 ▼
Phase 6 (US4)    Phase 7 (US5)
                      │
                      ▼
                 Phase 8 (US6)
                      │
                      ▼
                 Phase 9 (Polish)
```

---

## Parallel Execution Opportunities

### Within Phase 3 (US1)
```
T009-T013 (DB) → T015-T018 (TUI)  # Sequential
T014 (utils) ─── [P] parallel with T009-T013
```

### Within Phase 6 (US4)
```
T031-T032 → T033  # Sequential
T033, T034 ─── [P] parallel
```

### Within Phase 8 (US6)
```
T041 (link_rot.py) ─── [P] parallel with T042-T043 (DB)
T044-T045 after T041-T043
```

### Cross-Phase Parallelism
```
Phase 3 (US1) ─── [P] parallel with Phase 4 (US2)
Phase 6 (US4) ─── [P] parallel with Phase 7 (US5)
```

---

## MVP Scope

**Minimum Viable Product**: Phase 1 + Phase 2 + Phase 3 (US1)

Avec seulement US1 implémentée :
- ✅ Lier des sources aux souvenirs
- ✅ Voir les sources dans le détail d'un souvenir
- ❌ Backlinks (US2)
- ❌ Scoring (US3)
- ❌ Boost recherche (US4)
- ❌ Dashboard (US5)
- ❌ Link rot (US6)

**Recommandation**: Implémenter US1 + US2 ensemble (P1) pour les backlinks bidirectionnels complets.

---

## Implementation Strategy

1. **Phase 1-2**: Setup + Migration (bloquant)
2. **Phase 3-4**: US1 + US2 en parallèle (P1, value core)
3. **Phase 5**: US3 Scoring (P2, value différenciante)
4. **Phase 6-7**: US4 + US5 en parallèle (P2/P3)
5. **Phase 8**: US6 Link Rot (P3, nice-to-have)
6. **Phase 9**: Polish (tests, docs)

**Incremental Delivery**: Chaque phase produit une feature testable indépendamment.
