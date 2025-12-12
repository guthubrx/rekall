# Tasks: Système de Mémoire Cognitive

**Input**: Design documents from `/specs/004-cognitive-memory/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Non demandés explicitement - tests optionnels non inclus.

**Organization**: Tasks groupées par User Story pour implémentation et test indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut être exécuté en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User Story concernée (US1, US2, etc.)
- Chemins exacts inclus dans les descriptions

---

## Phase 1: Setup (Infrastructure Partagée)

**Purpose**: Migration schéma et infrastructure de base pour toutes les User Stories

- [x] T001 Ajouter les types MemoryType et RelationType dans rekall/models.py
- [x] T002 [P] Ajouter les champs cognitifs à la dataclass Entry dans rekall/models.py
- [x] T003 [P] Créer la dataclass Link dans rekall/models.py
- [x] T004 [P] Créer la dataclass ReviewItem dans rekall/models.py
- [x] T005 Implémenter la migration du schéma SQLite dans rekall/db.py (méthode _migrate_schema) - SOTA avec PRAGMA user_version
- [x] T006 Créer la table `links` dans rekall/db.py (via MIGRATIONS[2])
- [x] T007 [P] Ajouter les index pour memory_type, next_review, last_accessed dans rekall/db.py

**Checkpoint**: ✅ Schema migré, modèles prêts - Les User Stories peuvent commencer

---

## Phase 2: Foundational (Prérequis Bloquants)

**Purpose**: Opérations CRUD de base pour Link et tracking d'accès - BLOQUE toutes les US

**CRITIQUE**: Aucune User Story ne peut démarrer avant la fin de cette phase

- [x] T008 Implémenter Database.add_link() dans rekall/db.py
- [x] T009 [P] Implémenter Database.get_links() dans rekall/db.py
- [x] T010 [P] Implémenter Database.delete_link() dans rekall/db.py
- [x] T011 Implémenter Database.get_related_entries() dans rekall/db.py
- [x] T012 [P] Implémenter Database.update_access_tracking() dans rekall/db.py (appelé par get/search)
- [x] T013 Modifier Database.get() pour appeler update_access_tracking() dans rekall/db.py
- [x] T014 Modifier Database.search() pour appeler update_access_tracking() dans rekall/db.py
- [x] T015 [P] Implémenter calculate_consolidation_score() dans rekall/models.py

**Checkpoint**: ✅ Foundation prête - Les User Stories peuvent maintenant être implémentées

---

## Phase 3: User Story 1 - Liens entre entrées (Priority: P1) MVP

**Goal**: Créer et naviguer des connexions entre entrées Rekall pour construire un knowledge graph

**Independent Test**: Créer 3 entrées, les lier, vérifier que `rekall related <id>` retourne les entrées connectées

### Implementation US1

- [x] T016 [US1] Ajouter commande `rekall link <source_id> <target_id>` dans rekall/cli.py
- [x] T017 [US1] Ajouter option `--type` (related|supersedes|derived_from|contradicts) à `rekall link` dans rekall/cli.py
- [x] T018 [P] [US1] Ajouter commande `rekall unlink <source_id> <target_id>` dans rekall/cli.py
- [x] T019 [US1] Ajouter commande `rekall related <id>` dans rekall/cli.py
- [x] T020 [P] [US1] Ajouter option `--type` et `--depth` à `rekall related` dans rekall/cli.py
- [x] T021 [US1] Modifier `rekall show` pour afficher section "Related" dans rekall/cli.py
- [x] T022 [US1] N/A - Pas de commande delete (seulement deprecate qui ne supprime pas)
- [x] T023 [US1] Modifier `rekall search` pour afficher "Voir aussi" (entrées liées) dans rekall/cli.py
- [x] T024 [P] [US1] Ajouter messages i18n pour link/unlink/related dans rekall/i18n.py

**Checkpoint**: ✅ US1 complète - Liens fonctionnels, navigables, affichés dans show/search

---

## Phase 4: User Story 2 - Consultation automatique avant action (Priority: P1)

**Goal**: Claude consulte automatiquement Rekall avant bug fix/feature/refactor

**Independent Test**: Installer le skill, demander un bug fix, vérifier que Claude consulte Rekall d'abord

### Implementation US2

- [x] T025 [US2] Créer le fichier skill rekall/integrations/skill-rekall.md (template) - REKALL_SKILL dans __init__.py
- [x] T026 [US2] Définir les déclencheurs de consultation (bug fix, feature, refactor) dans skill-rekall.md
- [x] T027 [P] [US2] Définir le format de présentation des résultats Rekall dans skill-rekall.md
- [x] T028 [P] [US2] Définir le comportement si aucun résultat trouvé dans skill-rekall.md
- [x] T029 [US2] Ajouter option --json à rekall search pour agents AI dans rekall/cli.py
- [x] T030 [P] [US2] Messages i18n déjà présents (skill.installed, etc.)

**Checkpoint**: ✅ US2 complète - Skill installable, Claude consulte Rekall avant les tâches

---

## Phase 5: User Story 3 - Capture automatique après résolution (Priority: P1)

**Goal**: Claude propose de capturer les connaissances acquises après résolution

**Independent Test**: Résoudre un bug avec Claude, vérifier qu'il propose de sauvegarder

### Implementation US3

- [x] T031 [US3] Section "Capture automatique" dans REKALL_SKILL (rekall/integrations/__init__.py)
- [x] T032 [US3] Déclencheurs de capture (bug résolu, décision, pattern, pitfall, config, reference)
- [x] T033 [P] [US3] Format de proposition avec exemple concret (timeout auth API)
- [x] T034 [P] [US3] Génération automatique titre/type/tags/memory avec règles d'extraction
- [x] T035 [US3] Workflow modif/refus + règles (pas re-proposer, vérifier avant, pas trivial)

**Checkpoint**: ✅ US3 complète - Skill propose la capture, utilisateur peut accepter/modifier/refuser

---

## Phase 6: User Story 4 - Distinction épisodique/sémantique (Priority: P2)

**Goal**: Distinguer les connaissances épisodiques (événements) des sémantiques (concepts)

**Independent Test**: Créer une entrée épisodique, généraliser, vérifier les deux types existent

### Implementation US4

- [x] T036 [US4] Option `--memory-type` à `rekall add` - DÉJÀ IMPLÉMENTÉ (ligne 453)
- [x] T037 [P] [US4] Option `--memory-type` à `rekall search` - DÉJÀ IMPLÉMENTÉ (ligne 299)
- [x] T038 [P] [US4] Option `--memory-type` à `rekall browse` - DÉJÀ IMPLÉMENTÉ (ligne 651)
- [x] T039 [US4] Database.search() filtre par memory_type - DÉJÀ IMPLÉMENTÉ
- [x] T040 [P] [US4] Database.list_all() filtre par memory_type - DÉJÀ IMPLÉMENTÉ
- [x] T041 [US4] Commande `rekall generalize <ids>` - DÉJÀ IMPLÉMENTÉ (ligne 1490)
- [x] T042 [US4] Logique de généralisation (draft, liens derived_from) - DÉJÀ IMPLÉMENTÉ
- [x] T043 [P] [US4] `rekall show` affiche memory_type - DÉJÀ IMPLÉMENTÉ (ligne 567)
- [x] T044 [P] [US4] Messages i18n pour memory_type et generalize - DÉJÀ IMPLÉMENTÉ

**Checkpoint**: ✅ US4 complète - Distinction episodic/semantic, filtrage, généralisation fonctionnels

---

## Phase 7: User Story 5 - Tracking d'accès et consolidation (Priority: P2)

**Goal**: Suivre les accès pour identifier connaissances consolidées vs fragiles

**Independent Test**: Consulter une entrée plusieurs fois, vérifier métadonnées d'accès mises à jour

### Implementation US5

- [x] T045 [US5] `rekall show` affiche consolidation_score et accès - DÉJÀ IMPLÉMENTÉ
- [x] T046 [US5] Commande `rekall stale [--days N]` - DÉJÀ IMPLÉMENTÉ
- [x] T047 [P] [US5] Database.get_stale_entries(days) - DÉJÀ IMPLÉMENTÉ
- [x] T048 [US5] Indicateur consolidation (emoji 🔴🟡🟢 + barre) - DÉJÀ IMPLÉMENTÉ
- [x] T049 [P] [US5] TUI affiche indicateurs fraîcheur/consolidation - DÉJÀ IMPLÉMENTÉ
- [x] T050 [P] [US5] Messages i18n pour stale et consolidation - DÉJÀ IMPLÉMENTÉ

**Checkpoint**: ✅ US5 complète - Tracking d'accès automatique, stale visible, consolidation affichée

---

## Phase 8: User Story 6 - Répétition espacée (Priority: P3)

**Goal**: Commande de révision espacée pour maintenir la mémoire active

**Independent Test**: Créer entrées avec dates d'accès variées, exécuter `rekall review`, vérifier les bonnes entrées présentées

**Dépendance**: Nécessite US5 (tracking d'accès) complète

### Implementation US6

- [x] T051 [US6] calculate_next_interval() SM-2 - DÉJÀ IMPLÉMENTÉ dans rekall/models.py
- [x] T052 [US6] Database.get_due_entries() - DÉJÀ IMPLÉMENTÉ
- [x] T053 [US6] Database.update_review_schedule() - DÉJÀ IMPLÉMENTÉ
- [x] T054 [US6] Commande `rekall review` (mode interactif) - DÉJÀ IMPLÉMENTÉ
- [x] T055 [P] [US6] Options `--limit` et `--project` à review - DÉJÀ IMPLÉMENTÉ
- [x] T056 [US6] Prompt de notation (1-5) et recalcul intervalle - DÉJÀ IMPLÉMENTÉ
- [x] T057 [P] [US6] Messages i18n pour review - DÉJÀ IMPLÉMENTÉ

**Checkpoint**: ✅ US6 complète - Révision espacée fonctionnelle avec SM-2

---

## Phase 9: User Story 7 - Généralisation assistée (Priority: P3)

**Goal**: Claude aide à généraliser les épisodiques en patterns sémantiques

**Independent Test**: Demander à Claude de généraliser 3 bugs similaires, vérifier l'entrée sémantique créée

**Dépendance**: Nécessite US4 (distinction épisodique/sémantique) complète

### Implementation US7

- [x] T058 [US7] Section "Généralisation" dans REKALL_SKILL - DÉJÀ IMPLÉMENTÉ (ligne 922)
- [x] T059 [US7] Détection entrées épisodiques similaires - DÉJÀ IMPLÉMENTÉ (3+ entrées)
- [x] T060 [P] [US7] Format proposition généralisation - DÉJÀ IMPLÉMENTÉ
- [x] T061 [US7] Création liens derived_from - DÉJÀ IMPLÉMENTÉ via `generalize`
- [x] T062 [P] [US7] Section "Liens et Knowledge Graph" suggère liens - DÉJÀ IMPLÉMENTÉ (ligne 881)

**Checkpoint**: ✅ US7 complète - Claude peut généraliser et suggérer des liens

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Améliorations affectant plusieurs User Stories

- [x] T063 [P] Valider le quickstart.md - ✅ Ajouté section JSON, renuméroté sections
- [x] T064 [P] Mettre à jour README.md - ✅ Ajouté section Cognitive Memory + commandes
- [x] T065 Code cleanup et vérification cohérence nommage - FAIT
- [x] T066 [P] Performance OK (FTS < 100ms)
- [x] T067 Exécuter `ruff check` et corriger les erreurs lint - ✅ All checks passed
- [x] T068 [P] Exécuter `pytest` et vérifier tous les tests passent - ✅ 128/128 passent

---

## Phase 11: Amélioration TUI - Colonnes cognitives (2025-12-09)

**Purpose**: Exploiter les champs cognitifs dans l'affichage TUI browse

- [x] T069 Ajouter `count_links_by_direction()` dans rekall/db.py pour compter liens IN/OUT séparément
- [x] T070 Ajouter 5 colonnes au DataTable BrowseApp: Confiance, Accès, Score, In, Out
- [x] T071 [P] Ajouter traductions browse.access, browse.score, browse.links_in, browse.links_out dans rekall/i18n.py
- [x] T072 Modifier `_populate_table()` pour remplir les nouvelles colonnes

**Checkpoint**: ✅ Colonnes cognitives visibles dans `rekall browse`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Pas de dépendances - peut démarrer immédiatement
- **Foundational (Phase 2)**: Dépend de Setup - BLOQUE toutes les User Stories
- **US1-US5 (Phases 3-7)**: Dépendent de Foundational - peuvent ensuite être parallélisées
- **US6 (Phase 8)**: Dépend de US5 (tracking d'accès)
- **US7 (Phase 9)**: Dépend de US4 (distinction épisodique/sémantique)
- **Polish (Phase 10)**: Dépend de toutes les US désirées

### User Story Dependencies

```
Setup → Foundational → ┬─ US1 (Liens) ─────────────────────────────┐
                       ├─ US2 (Consultation) ──────────────────────┤
                       ├─ US3 (Capture) ───────────────────────────┤
                       ├─ US4 (Episodic/Semantic) → US7 (Général.) ┼→ Polish
                       └─ US5 (Tracking) ────────→ US6 (Review) ───┘
```

### Within Each User Story

- Models avant services
- Services avant commandes CLI
- Core implementation avant intégration
- Story complète avant de passer à la priorité suivante

### Parallel Opportunities

**Setup (Phase 1)**:
```bash
# Parallèle: T002, T003, T004 (modèles indépendants)
# Parallèle: T006, T007 (schéma après migration)
```

**Foundational (Phase 2)**:
```bash
# Parallèle: T009, T010 (get_links, delete_link)
# Parallèle: T012, T015 (tracking, consolidation score)
```

**US1 (Phase 3)**:
```bash
# Parallèle: T018, T020, T024 (unlink, options related, i18n)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Compléter Phase 1: Setup (T001-T007)
2. Compléter Phase 2: Foundational (T008-T015)
3. Compléter Phase 3: User Story 1 (T016-T024)
4. **STOP et VALIDER**: Tester US1 indépendamment
5. Déployer si prêt - MVP avec Knowledge Graph fonctionnel

### Incremental Delivery

1. Setup + Foundational → Infrastructure prête
2. Ajouter US1 (Liens) → Test → **MVP livrable**
3. Ajouter US2+US3 (Skill) → Test → Skill Claude fonctionnel
4. Ajouter US4+US5 (Memory type + Tracking) → Test → Mémoire cognitive de base
5. Ajouter US6+US7 (Review + Généralisation) → Test → Système complet

### Parallel Team Strategy

Avec plusieurs développeurs après Foundational:

- **Dev A**: US1 (Liens) + US4 (Memory type)
- **Dev B**: US2 + US3 (Skill Claude)
- **Dev C**: US5 (Tracking) → US6 (Review)

---

## Summary

| Métrique | Valeur |
|----------|--------|
| **Total tâches** | 68 |
| **Phase 1 (Setup)** | 7 |
| **Phase 2 (Foundational)** | 8 |
| **US1 (Liens) P1** | 9 |
| **US2 (Consultation) P1** | 6 |
| **US3 (Capture) P1** | 5 |
| **US4 (Épisodique/Sémantique) P2** | 9 |
| **US5 (Tracking) P2** | 6 |
| **US6 (Review) P3** | 7 |
| **US7 (Généralisation) P3** | 5 |
| **Polish** | 6 |
| **Tâches parallélisables [P]** | 28 |

### MVP Scope

**User Story 1 seule** (15 tâches: Setup + Foundational + US1):
- Knowledge graph fonctionnel
- Commandes link, unlink, related
- Affichage des liens dans show et search
- Temps estimé: ~4-6 heures développeur

### Independent Test Criteria

| US | Test indépendant |
|----|------------------|
| US1 | Créer 3 entrées, lier, `rekall related <id>` retourne les connexions |
| US2 | Installer skill, demander bug fix, Claude consulte Rekall d'abord |
| US3 | Résoudre bug avec Claude, il propose de sauvegarder |
| US4 | Créer entrée épisodique, généraliser, vérifier les deux types |
| US5 | Consulter entrée plusieurs fois, métadonnées d'accès mises à jour |
| US6 | Entrées avec dates variées, `rekall review` présente les bonnes |
| US7 | Demander généralisation 3 bugs, entrée sémantique créée |
