# Tasks: Optimisation Performance Embeddings

**Input**: Design documents from `/specs/020-embedding-perf/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Tests**: Inclus (Constitution Article XV - Test-Before-Next)

**Organization**: Tasks groupées par user story pour implémentation/test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut tourner en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User story concernée (US1, US2, US3)
- Chemins exacts dans les descriptions

## Path Conventions

- **Projet single**: `rekall/` (source), `tests/` (tests) à la racine

---

## Phase 1: Setup

**Purpose**: Configuration projet et dépendances

- [X] T001 Ajouter sqlite-vec aux dépendances optionnelles dans pyproject.toml
- [X] T002 [P] Ajouter options performance dans rekall/config.py (cache_max_size, cache_ttl, model_timeout, vector_backend)
- [X] T003 [P] Créer ADR pour sqlite-vec vs FAISS dans docs/decisions/020-sqlite-vec-choice.md

---

## Phase 2: Foundational (Modules de base)

**Purpose**: Infrastructure de base - DOIT être complétée avant les user stories

**⚠️ CRITIQUE**: Aucune tâche user story ne peut commencer avant cette phase

- [X] T004 [P] Créer rekall/cache.py avec classe EmbeddingCache (LRU + invalidation)
- [X] T005 [P] Créer rekall/model_manager.py avec classe ModelManager (lazy load/unload)
- [X] T006 [P] Créer rekall/vector_index.py avec classe VectorIndex (sqlite-vec + fallback numpy)
- [X] T007 [P] Créer tests/test_cache.py avec tests unitaires EmbeddingCache
- [X] T008 [P] Créer tests/test_model_manager.py avec tests unitaires ModelManager
- [X] T009 [P] Créer tests/test_vector_index.py avec tests unitaires VectorIndex

**Checkpoint**: Modules de base créés et testés - implémentation user stories peut commencer

---

## Phase 3: User Story 1 - Recherche Sémantique Rapide (Priority: P1) 🎯 MVP

**Goal**: Recherches sémantiques <500ms sur 1000 entrées (actuellement 2-5s)

**Independent Test**: `time rekall search "test query"` sur base 1000 entrées → <500ms

### Tests pour User Story 1

- [ ] T010 [P] [US1] Test de performance recherche dans tests/test_embeddings.py (assert <500ms pour 1000 entrées)
- [ ] T011 [P] [US1] Test vectorisation numpy dans tests/test_embeddings.py (batch vs boucle)

### Implementation User Story 1

- [X] T012 [US1] Ajouter méthode get_all_vectors_batch() dans rekall/db.py retournant ndarray
- [X] T013 [US1] Remplacer boucle par numpy.dot() batch dans rekall/embeddings.py:semantic_search()
- [X] T014 [US1] Remplacer boucle par numpy.dot() batch dans rekall/embeddings.py:find_similar()
- [X] T015 [US1] Intégrer EmbeddingCache dans rekall/embeddings.py:EmbeddingService
- [X] T016 [US1] Ajouter invalidation cache sur add/update/delete dans rekall/db.py
- [X] T017 [US1] Afficher message "Chargement du modèle en cours" si recherche pendant loading dans rekall/embeddings.py

**Checkpoint**: Recherche <500ms sur 1000 entrées - MVP fonctionnel

---

## Phase 4: User Story 2 - Empreinte Mémoire Réduite (Priority: P2)

**Goal**: RAM au repos <100MB (actuellement 150-200MB avec modèle)

**Independent Test**: Mesurer RAM après 10min d'inactivité → modèle déchargé

### Tests pour User Story 2

- [ ] T018 [P] [US2] Test lazy unload dans tests/test_model_manager.py (timeout → modèle None)
- [ ] T019 [P] [US2] Test check_idle() dans tests/test_model_manager.py

### Implementation User Story 2

- [ ] T020 [US2] Intégrer ModelManager singleton dans rekall/embeddings.py remplaçant _embedding_service
- [ ] T021 [US2] Appeler check_idle() après chaque opération embedding dans rekall/embeddings.py
- [ ] T022 [US2] Ajouter config model_idle_timeout_minutes dans rekall/config.py (défaut: 10)
- [ ] T023 [US2] Ajouter gc.collect() après unload dans rekall/model_manager.py

**Checkpoint**: Modèle déchargé après timeout, RAM <100MB au repos

---

## Phase 5: User Story 3 - Scalabilité Future (Priority: P3)

**Goal**: Recherche <1s sur 10 000 entrées, indexation <2s sur 50 000 entrées

**Independent Test**: Générer base synthétique 10K entrées, mesurer temps recherche

### Tests pour User Story 3

- [ ] T024 [P] [US3] Test performance sqlite-vec dans tests/test_vector_index.py (10K vecteurs)
- [ ] T025 [P] [US3] Test fallback numpy si sqlite-vec indisponible dans tests/test_vector_index.py

### Implementation User Story 3

- [ ] T026 [US3] Ajouter détection sqlite-vec au démarrage dans rekall/vector_index.py
- [ ] T027 [US3] Implémenter VectorIndex.search() avec sqlite-vec query dans rekall/vector_index.py
- [ ] T028 [US3] Implémenter fallback brute-force vectorisé si sqlite-vec absent dans rekall/vector_index.py
- [ ] T029 [US3] Ajouter migration schema v12 (embeddings_vec) dans rekall/db.py
- [ ] T030 [US3] Intégrer VectorIndex dans hybrid_search() de rekall/embeddings.py
- [ ] T031 [US3] Ajouter rebuild index sur demand (CLI rekall index rebuild) dans rekall/cli.py

**Checkpoint**: Recherche <1s sur 10K entrées avec sqlite-vec ou fallback

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finalisation, documentation, validation

- [ ] T032 [P] Mettre à jour README.md avec section performance
- [ ] T033 [P] Ajouter commande `rekall stats --memory` pour debug dans rekall/cli.py
- [ ] T034 Exécuter validation quickstart.md (tous les scénarios)
- [ ] T035 Exécuter tests complets `pytest tests/ -v`
- [ ] T036 Vérifier lint `ruff check rekall/`
- [ ] T037 Commit final et tag v0.4.0

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dépendances - peut commencer immédiatement
- **Foundational (Phase 2)**: Dépend de Setup - BLOQUE toutes les user stories
- **User Stories (Phase 3-5)**: Toutes dépendent de Foundational
  - US1 → US2 → US3 (ordre de priorité recommandé)
  - Ou en parallèle si plusieurs développeurs
- **Polish (Phase 6)**: Dépend de toutes les user stories désirées

### User Story Dependencies

- **User Story 1 (P1)**: Peut commencer après Phase 2 - Indépendant
- **User Story 2 (P2)**: Peut commencer après Phase 2 - Utilise ModelManager de Phase 2
- **User Story 3 (P3)**: Peut commencer après Phase 2 - Utilise VectorIndex de Phase 2

### Within Each User Story

- Tests FIRST → doivent FAIL avant implémentation
- Modifications db.py avant embeddings.py
- Core implementation avant CLI/intégration

### Parallel Opportunities

**Phase 2** - Tous les modules peuvent être créés en parallèle :
```
T004 (cache.py) || T005 (model_manager.py) || T006 (vector_index.py)
T007 (test_cache) || T008 (test_model_manager) || T009 (test_vector_index)
```

**User Stories** - Peuvent être développées en parallèle après Phase 2 :
```
US1 (T010-T017) || US2 (T018-T023) || US3 (T024-T031)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational (T004-T009)
3. Complete Phase 3: User Story 1 (T010-T017)
4. **STOP and VALIDATE**: `time rekall search "test"` → <500ms
5. Deploy si satisfait (gain 10-50x immédiat)

### Incremental Delivery

1. Setup + Foundational → Infrastructure prête
2. Add User Story 1 → Test → Deploy (MVP! Recherche rapide)
3. Add User Story 2 → Test → Deploy (RAM réduite)
4. Add User Story 3 → Test → Deploy (Scalabilité 10K+)
5. Chaque story ajoute de la valeur sans casser les précédentes

---

## Summary

| Métrique | Valeur |
|----------|--------|
| **Total tâches** | 37 |
| **Phase 1 (Setup)** | 3 |
| **Phase 2 (Foundational)** | 6 |
| **US1 (P1 - MVP)** | 8 |
| **US2 (P2)** | 6 |
| **US3 (P3)** | 8 |
| **Phase 6 (Polish)** | 6 |
| **Tâches parallélisables** | 18 (49%) |

**MVP Scope**: Phases 1-3 (17 tâches) → Recherche 10-50x plus rapide

---

## Notes

- [P] = fichiers différents, pas de dépendances
- [US*] = label de traçabilité vers user story
- Chaque user story est testable indépendamment
- Commit après chaque tâche logique
- Constitution Article XV : Tests before next task
