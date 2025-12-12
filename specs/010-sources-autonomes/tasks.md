# Implementation Tasks: Sources Autonomes

**Branch**: `010-sources-autonomes`
**Generated**: 2025-12-11
**Total Tasks**: 52

---

## User Stories Summary

| Story | Priority | Description | Tasks |
|-------|----------|-------------|-------|
| US1 | P1 | Migrer les Sources Existantes | 9 |
| US2 | P1 | Promotion Automatique des Sources | 8 |
| US3 | P2 | Classification Hub vs Authority | 6 |
| US4 | P2 | Scoring Avancé (Citation Quality) | 5 |
| US5 | P2 | Intégration Speckit (API JSON) | 6 |
| US6 | P3 | Dashboard Sources Enrichi | 6 |

---

## Phase 1: Setup

**Goal**: Préparer l'infrastructure de base pour la feature.

- [X] T001 Ajouter les types SourceRole et PromotionStatus dans `rekall/models.py`
- [X] T002 Ajouter les constantes PROMOTION_THRESHOLDS et ROLE_BONUS dans `rekall/models.py`
- [X] T003 Ajouter les traductions sources autonomes (source.seed, source.promoted, source.role.*) dans `rekall/i18n.py`

---

## Phase 2: Foundational (Database Migration v9)

**Goal**: Créer les nouvelles tables et colonnes pour schema v9.
**Blocking**: Toutes les user stories dépendent de cette phase.

- [X] T004 Ajouter MIGRATIONS[9] avec ALTER TABLE sources (is_seed, is_promoted, promoted_at, role, seed_origin, citation_quality_factor) dans `rekall/db.py`
- [X] T005 Ajouter CREATE TABLE source_themes dans MIGRATIONS[9] dans `rekall/db.py`
- [X] T006 Ajouter CREATE TABLE known_domains dans MIGRATIONS[9] dans `rekall/db.py`
- [X] T007 Ajouter INSERT INTO known_domains avec ~25 domaines initiaux (authorities + hubs) dans `rekall/db.py`
- [X] T008 Ajouter les index (idx_sources_is_seed, idx_sources_is_promoted, idx_sources_role, idx_source_themes_theme) dans `rekall/db.py`
- [X] T009 Mettre à jour EXPECTED_TABLES et EXPECTED_COLUMNS pour v9 dans `rekall/db.py`
- [X] T010 Ajouter test_migration_v9() dans `tests/test_db.py`

---

## Phase 3: User Story 1 - Migrer les Sources Existantes (P1)

**Goal**: Permettre l'import des fichiers `~/.speckit/research/*.md` comme sources seed.

**Independent Test**: Exécuter `rekall sources migrate --dry-run`, vérifier que les sources sont détectées avec leurs thèmes.

**Acceptance Criteria**:
1. Toutes les URLs/domaines des fichiers speckit sont importés avec `is_seed=true`
2. Les sources existantes sont mises à jour sans duplication
3. Chaque source est taguée avec le thème du fichier source

### Parser Speckit

- [X] T011 [P] [US1] Créer le module `rekall/migration/__init__.py`
- [X] T012 [US1] Implémenter parse_research_file() pour extraire URLs/domaines d'un fichier markdown dans `rekall/migration/speckit_parser.py`
- [X] T013 [US1] Implémenter extract_theme_from_filename() pour déduire le thème du nom de fichier dans `rekall/migration/speckit_parser.py`
- [X] T014 [US1] Implémenter scan_research_directory() pour parcourir tous les fichiers *.md dans `rekall/migration/speckit_parser.py`

### Database Layer

- [X] T015 [US1] Implémenter add_source_theme() dans `rekall/db.py`
- [X] T016 [US1] Implémenter get_source_themes() dans `rekall/db.py`
- [X] T017 [US1] Implémenter update_source_as_seed() dans `rekall/db.py`

### CLI Layer

- [X] T018 [US1] Ajouter commande `rekall sources migrate` avec options --path, --dry-run, --force dans `rekall/cli.py`
- [X] T019 [US1] Ajouter test_migration_speckit() dans `tests/test_db.py` (test_speckit_parser_*)

---

## Phase 4: User Story 2 - Promotion Automatique des Sources (P1)

**Goal**: Promouvoir automatiquement les sources atteignant les critères.

**Independent Test**: Créer 3+ souvenirs citant la même source, exécuter `rekall sources recalculate`, vérifier que la source est marquée "promoted".

**Acceptance Criteria**:
1. Sources avec usage ≥ 3, score ≥ 30, last_used ≤ 180 jours → promoted
2. Rétrogradation si critères non remplis (sauf seeds)
3. Seeds exemptés de rétrogradation

### Database Layer

- [X] T020 [US2] Implémenter check_promotion_criteria() dans `rekall/db.py`
- [X] T021 [US2] Implémenter promote_source() dans `rekall/db.py`
- [X] T022 [US2] Implémenter demote_source() dans `rekall/db.py`
- [X] T023 [US2] Implémenter get_promoted_sources() dans `rekall/db.py`
- [X] T024 [US2] Implémenter recalculate_all_promotions() dans `rekall/db.py`

### CLI Layer

- [X] T025 [US2] Ajouter commande `rekall sources recalculate` avec options --source-id, --update-promotions, --verbose dans `rekall/cli.py`
- [X] T026 [US2] Ajouter test_promotion_criteria() dans `tests/test_db.py`
- [X] T027 [US2] Ajouter test_promotion_seeds_exemption() dans `tests/test_db.py`

---

## Phase 5: User Story 3 - Classification Hub vs Authority (P2)

**Goal**: Classifier automatiquement les sources selon leur type.

**Independent Test**: Ajouter une source avec domaine `stackoverflow.com`, vérifier qu'elle est classifiée "hub".

**Acceptance Criteria**:
1. Domaines connus → classification automatique
2. Domaines inconnus → "unclassified"
3. Classification manuelle possible

### Database Layer

- [X] T028 [US3] Implémenter get_known_domain() dans `rekall/db.py`
- [X] T029 [US3] Implémenter add_known_domain() dans `rekall/db.py`
- [X] T030 [US3] Implémenter classify_source_auto() dans `rekall/db.py`
- [X] T031 [US3] Modifier add_source() pour appeler classify_source_auto() dans `rekall/db.py`

### CLI Layer

- [X] T032 [US3] Ajouter commande `rekall sources classify <SOURCE_ID> <ROLE>` dans `rekall/cli.py`
- [X] T033 [US3] Ajouter test_auto_classification() dans `tests/test_db.py`

---

## Phase 6: User Story 4 - Scoring Avancé avec Citation Quality (P2)

**Goal**: Intégrer le facteur citation quality dans le scoring.

**Independent Test**: Créer des souvenirs citant plusieurs sources, vérifier que le score reflète la qualité des co-citations.

**Acceptance Criteria**:
1. citation_quality_factor calculé à partir des co-citations
2. Formule de score v2 intégrée
3. Recalcul batch fonctionnel

### Database Layer

- [X] T034 [US4] Implémenter calculate_citation_quality() dans `rekall/db.py`
- [X] T035 [US4] Implémenter calculate_source_score_v2() (remplace calculate_source_score) dans `rekall/db.py`
- [X] T036 [US4] Modifier recalculate_source_score() pour utiliser score_v2 dans `rekall/db.py`
- [X] T037 [US4] Ajouter test_citation_quality_calculation() dans `tests/test_db.py`
- [X] T038 [US4] Ajouter test_score_v2_formula() dans `tests/test_db.py`

---

## Phase 7: User Story 5 - Intégration Speckit (API JSON) (P2)

**Goal**: Exposer une API CLI retournant les sources par thème en JSON.

**Independent Test**: Exécuter `rekall sources suggest --theme security`, vérifier que le JSON contient les sources triées par score.

**Acceptance Criteria**:
1. Sortie JSON avec métadonnées complètes
2. Tri par score décroissant
3. Seeds et promoted prioritaires à score égal

### Database Layer

- [X] T039 [US5] Implémenter get_sources_by_theme() dans `rekall/db.py`
- [X] T040 [US5] Implémenter list_themes_with_counts() dans `rekall/db.py`

### CLI Layer

- [X] T041 [US5] Ajouter commande `rekall sources suggest --theme X` avec sortie JSON dans `rekall/cli.py`
- [X] T042 [US5] Ajouter commande `rekall sources list-themes` dans `rekall/cli.py`
- [X] T043 [US5] Ajouter commande `rekall sources add-theme <SOURCE_ID> <THEME>` dans `rekall/cli.py`
- [X] T044 [US5] Ajouter commande `rekall sources stats` dans `rekall/cli.py`

---

## Phase 8: User Story 6 - Dashboard Sources Enrichi (P3)

**Goal**: Enrichir le dashboard TUI avec les nouvelles métriques.

**Independent Test**: Ouvrir le dashboard, vérifier que les sections Seeds et Promoted sont visibles.

**Acceptance Criteria**:
1. Section "Sources Seeds" avec origine fichier
2. Section "Sources Promues" avec date de promotion
3. Affichage du rôle (hub/authority/unclassified)

### TUI Layer

- [X] T045 [US6] Ajouter widget SeedSourcesListView dans `rekall/tui.py` (intégré dans action_sources)
- [X] T046 [US6] Ajouter widget PromotedSourcesListView dans `rekall/tui.py` (intégré dans action_sources)
- [X] T047 [US6] Modifier SourceDashboardScreen pour afficher rôle (icône) dans `rekall/tui.py`
- [X] T048 [US6] Ajouter section "Sources Seeds" dans SourceDashboardScreen dans `rekall/tui.py`
- [X] T049 [US6] Ajouter section "Sources Promues" dans SourceDashboardScreen dans `rekall/tui.py`
- [X] T050 [US6] Ajouter traductions dashboard (dashboard.seeds, dashboard.promoted, dashboard.role.*) dans `rekall/i18n.py`

---

## Phase 9: Polish & Cross-Cutting

**Goal**: Finalisation, documentation et tests d'intégration.

- [ ] T051 Ajouter tests d'intégration end-to-end pour sources autonomes dans `tests/test_integration_sources.py`
- [ ] T052 Mettre à jour le README avec documentation sources autonomes dans `README.md`

---

## Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (DB Migration v9) ─────────────────────────────────────┐
    │                                                           │
    ├──────────────────┬──────────────────┐                     │
    ▼                  ▼                  ▼                     │
Phase 3 (US1)      Phase 4 (US2)      Phase 5 (US3)            │
(Migration)        (Promotion)        (Classification)          │
    │                  │                  │                     │
    └────────┬─────────┴──────────────────┘                     │
             ▼                                                   │
         Phase 6 (US4) ◄────────────────────────────────────────┘
         (Citation Quality)
             │
    ┌────────┴────────┐
    ▼                 ▼
Phase 7 (US5)    Phase 8 (US6)
(API JSON)       (Dashboard)
                      │
                      ▼
                 Phase 9 (Polish)
```

---

## Parallel Execution Opportunities

### Within Phase 3 (US1)
```
T011 (module init) ─── [P] standalone
T012-T014 (parser) → Sequential (depend on T011)
T015-T017 (DB) ─── [P] parallel with T012-T014
T018-T019 (CLI + tests) after T012-T017
```

### Within Phase 5 (US3)
```
T028-T030 (DB) → Sequential
T031 after T028-T030
T032-T033 (CLI + tests) ─── [P] parallel after T031
```

### Within Phase 7 (US5)
```
T039-T040 (DB) → Sequential
T041-T044 (CLI) ─── [P] parallel after T039-T040
```

### Cross-Phase Parallelism
```
Phase 3 (US1) ─── [P] parallel with Phase 4 (US2) ─── [P] parallel with Phase 5 (US3)
Phase 7 (US5) ─── [P] parallel with Phase 8 (US6)
```

---

## MVP Scope

**Minimum Viable Product**: Phase 1 + Phase 2 + Phase 3 (US1)

Avec seulement US1 implémentée :
- ✅ Import des sources speckit comme seeds
- ✅ Association des thèmes
- ✅ Détection doublons
- ❌ Promotion automatique (US2)
- ❌ Classification hub/authority (US3)
- ❌ Citation quality (US4)
- ❌ API JSON (US5)
- ❌ Dashboard enrichi (US6)

**Recommandation**: Implémenter US1 + US2 ensemble (P1) pour le système de promotion complet.

---

## Implementation Strategy

1. **Phase 1-2**: Setup + Migration v9 (bloquant)
2. **Phase 3-4-5**: US1 + US2 + US3 en parallèle (P1 + début P2)
3. **Phase 6**: US4 Citation Quality (P2, dépend de US1-US3)
4. **Phase 7-8**: US5 + US6 en parallèle (P2/P3)
5. **Phase 9**: Polish (tests, docs)

**Incremental Delivery**: Chaque phase produit une feature testable indépendamment.
