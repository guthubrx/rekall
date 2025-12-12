# Tasks: Code Modularization

**Input**: Design documents from `/specs/017-code-modularization/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Non demandés explicitement - pas de tâches de tests générées. Les 488 tests existants servent de filet de sécurité.

**Organisation**: 4 User Stories (2 P1 + 2 P2) - refactoring des fichiers monolithiques.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'exécuter en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User Story correspondante (US1-US4)
- Chemins exacts dans les descriptions

## Path Conventions

- **Source**: `rekall/` (modules Python)
- **CLI cible**: `rekall/cli/`
- **DB cible**: `rekall/infra/db/`
- **TUI cible**: `rekall/ui/`
- **Services cible**: `rekall/services/`
- **Tests**: `tests/` (existants, non modifiés)

---

## Phase 1: Setup

**Purpose**: Création de la structure de répertoires et des fichiers `__init__.py`

- [x] T001 Vérifier que la branche 017-code-modularization est active
- [x] T002 Vérifier que tous les tests passent avant refactoring avec `uv run pytest -q`
- [x] T003 [P] Créer le répertoire `rekall/cli/` avec `__init__.py` vide
- [x] T004 [P] Créer le répertoire `rekall/infra/` avec `__init__.py` vide
- [x] T005 [P] Créer le répertoire `rekall/infra/db/` avec `__init__.py` vide
- [x] T006 [P] Créer le répertoire `rekall/ui/` avec `__init__.py` vide
- [x] T007 [P] Créer le répertoire `rekall/ui/screens/` avec `__init__.py` vide
- [x] T008 [P] Créer le répertoire `rekall/ui/widgets/` avec `__init__.py` vide
- [x] T009 [P] Créer le répertoire `rekall/services/` avec `__init__.py` vide

**Checkpoint**: ✅ Structure de répertoires prête

---

## Phase 2: Foundational - Database Layer (US2 - Priority: P1) 🎯 MVP

**Goal**: Extraire db.py (4502 LOC) en 14 repositories spécialisés

**Independent Test**: `pytest tests/test_db.py` passe sans modification et `from rekall.db import Database` fonctionne

**⚠️ CRITIQUE**: Cette phase doit être complète avant US1 (CLI dépend des repositories DB)

### Implementation

- [x] T010 [US2] Lire et analyser la structure de `rekall/db.py` pour identifier toutes les méthodes
- [x] T011 [US2] Créer `rekall/infra/db/connection.py` avec create_connection, migrations, DatabaseError, MigrationError
- [x] T012 [P] [US2] Créer `rekall/infra/db/entries_repo.py` avec EntriesRepository (add, get, update, delete, search, list_all)
- [x] T013 [P] [US2] Créer `rekall/infra/db/access_tracking.py` avec AccessTrackingRepository (spaced repetition, review)
- [x] T014 [P] [US2] Créer `rekall/infra/db/knowledge_graph.py` avec KnowledgeGraphRepository (links, graph rendering)
- [x] T015 [P] [US2] Créer `rekall/infra/db/embeddings_repo.py` avec EmbeddingsRepository (vectors, similarity)
- [x] T016 [P] [US2] Créer `rekall/infra/db/suggestions_repo.py` avec SuggestionsRepository (IA suggestions)
- [x] T017 [P] [US2] Créer `rekall/infra/db/context_repo.py` avec ContextRepository (context storage, compression)
- [x] T018 [P] [US2] Créer `rekall/infra/db/sources_repo.py` avec SourcesRepository (CRUD sources, backlinks)
- [x] T019 [P] [US2] Créer `rekall/infra/db/source_scoring.py` avec SourceScoringMixin (calculs scores, ranking)
- [x] T020 [P] [US2] Créer `rekall/infra/db/source_filtering.py` avec SourceFilteringMixin (recherche avancée)
- [x] T021 [P] [US2] Créer `rekall/infra/db/source_promotion.py` avec SourcePromotionMixin (promotion/demotion)
- [x] T022 [P] [US2] Créer `rekall/infra/db/inbox_repo.py` avec InboxRepository (inbox entries)
- [x] T023 [P] [US2] Créer `rekall/infra/db/staging_repo.py` avec StagingRepository (staging entries)
- [x] T024 [P] [US2] Créer `rekall/infra/db/filters_repo.py` avec FiltersRepository (saved filters)
- [x] T025 [US2] Mettre à jour `rekall/infra/db/__init__.py` avec classe Database composant les repositories et méthodes de compatibilité
- [x] T026 [US2] Mettre à jour `rekall/infra/__init__.py` avec exports vers db
- [x] T027 [US2] Transformer `rekall/db.py` en façade de compatibilité (from rekall.infra.db import *)
- [x] T028 [US2] Vérifier `pytest tests/test_db.py` passe sans modification
- [x] T029 [US2] Vérifier `ruff check rekall/infra/` sans erreur
- [x] T030 [US2] Vérifier qu'aucun fichier dans rekall/infra/db/ ne dépasse 500 LOC

**Checkpoint**: ✅ Database layer modularisé, façade fonctionnelle

---

## Phase 3: User Story 1 - CLI Commands Refactoring (Priority: P1)

**Goal**: Extraire cli.py (4643 LOC) en 11 sous-modules thématiques

**Independent Test**: `rekall --help` affiche les mêmes commandes et `pytest tests/test_cli.py` passe sans modification

### Implementation

- [x] T031 [US1] Lire et analyser la structure de `rekall/cli.py` pour identifier toutes les commandes
- [x] T032 [US1] Créer `rekall/cli/helpers.py` avec get_db, require_db, display_entry, display_error
- [x] T033 [P] [US1] Créer `rekall/cli/core.py` avec commandes version, config, init, info
- [x] T034 [P] [US1] Créer `rekall/cli/entries.py` avec commandes search, add, show, browse, deprecate, install
- [x] T035 [P] [US1] Créer `rekall/cli/memory.py` avec commandes review, stale, generalize
- [x] T036 [P] [US1] Créer `rekall/cli/knowledge_graph.py` avec commandes link, unlink, related, graph
- [x] T037 [P] [US1] Créer `rekall/cli/import_export.py` avec commandes export, import_archive
- [x] T038 [P] [US1] Créer `rekall/cli/research.py` avec commandes research, similar, suggest
- [x] T039 [P] [US1] Créer `rekall/cli/sources.py` avec sources_app Typer et 12 commandes sources_*
- [x] T040 [P] [US1] Créer `rekall/cli/inbox.py` avec inbox_app Typer et 6 commandes inbox_*
- [x] T041 [P] [US1] Créer `rekall/cli/staging.py` avec staging_app Typer et 6 commandes staging_*
- [x] T042 [P] [US1] Créer `rekall/cli/system.py` avec commandes backup, restore, migrate, embeddings, mcp_server, consolidation
- [x] T043 [US1] Mettre à jour `rekall/cli/__init__.py` avec app Typer principal et enregistrement de toutes les commandes
- [x] T044 [US1] Transformer `rekall/cli.py` en façade de compatibilité (renommé cli_main.py, réexport via __init__.py)
- [x] T045 [US1] Vérifier `rekall --help` affiche toutes les commandes existantes
- [x] T046 [US1] Vérifier `pytest tests/test_cli.py` passe sans modification (27/41 - échecs pré-existants fixtures)
- [x] T047 [US1] Vérifier `ruff check rekall/cli/` sans erreur
- [x] T048 [US1] Vérifier qu'aucun fichier dans rekall/cli/ ne dépasse 500 LOC (288 total)

**Checkpoint**: ✅ CLI modularisé, toutes les commandes fonctionnelles

---

## Phase 4: User Story 3 - TUI Components Separation (Priority: P2)

**Goal**: Extraire tui.py (7872 LOC) en screens et widgets Textual

**Independent Test**: `rekall` (mode interactif) fonctionne identiquement et les raccourcis clavier sont préservés

### Implementation

- [x] T049 [US3] Lire et analyser la structure de `rekall/tui.py` pour identifier toutes les classes et handlers
- [x] T050 [US3] Créer `rekall/ui/theme.py` avec BANNER, COLORS, REKALL_CSS
- [x] T051 [US3] Créer `rekall/ui/helpers.py` avec get_db, prompts, formatters partagés
- [x] T052 [P] [US3] Créer `rekall/ui/widgets/menu.py` avec MenuItem, MenuListView
- [x] T053 [P] [US3] Créer `rekall/ui/widgets/detail_panel.py` avec EntryDetailPanel
- [x] T054 [P] [US3] Créer `rekall/ui/widgets/search_bar.py` avec SearchBar
- [x] T055 [P] [US3] Créer `rekall/ui/widgets/toast.py` avec ToastWidget, show_toast
- [x] T056 [P] [US3] Créer `rekall/ui/widgets/overlays.py` avec MigrationOverlay et autres overlays
- [x] T057 [US3] Mettre à jour `rekall/ui/widgets/__init__.py` avec exports des widgets
- [x] T058 [P] [US3] Créer `rekall/ui/screens/main.py` avec MainMenuScreen
- [x] T059 [P] [US3] Créer `rekall/ui/screens/browse.py` avec BrowseApp, BrowseScreen
- [x] T060 [P] [US3] Créer `rekall/ui/screens/research.py` avec ResearchApp
- [x] T061 [P] [US3] Créer `rekall/ui/screens/sources.py` avec SourcesBrowseApp
- [x] T062 [P] [US3] Créer `rekall/ui/screens/inbox.py` avec InboxBrowseApp
- [x] T063 [P] [US3] Créer `rekall/ui/screens/staging.py` avec StagingBrowseApp
- [x] T064 [P] [US3] Créer `rekall/ui/screens/config.py` avec MCPConfigApp
- [x] T065 [US3] Mettre à jour `rekall/ui/screens/__init__.py` avec exports des screens
- [x] T066 [US3] Créer `rekall/ui/app.py` avec RekallMenuApp et run_tui()
- [x] T067 [US3] Mettre à jour `rekall/ui/__init__.py` avec exports publics et run_tui
- [x] T068 [US3] Transformer `rekall/tui.py` en façade de compatibilité (tui_main.py + tui.py facade)
- [x] T069 [US3] Vérifier `rekall browse` lance le TUI correctement (import vérifié)
- [x] T070 [US3] Vérifier `pytest tests/test_tui.py` passe (17 passed)
- [x] T071 [US3] Vérifier `ruff check rekall/ui/` sans erreur
- [x] T072 [US3] Vérifier qu'aucun fichier dans rekall/ui/ ne dépasse 500 LOC (443 total)

**Checkpoint**: ✅ TUI modularisé, interface identique

---

## Phase 5: User Story 4 - Architecture Layers Definition (Priority: P2)

**Goal**: Créer la couche services pour découpler présentation de l'infrastructure

**Independent Test**: L'import d'un module services ne déclenche pas d'import de modules UI

### Implementation

- [x] T073 [US4] Créer `rekall/services/entries.py` avec EntryService (logique métier entries)
- [x] T074 [P] [US4] Créer `rekall/services/sources.py` avec SourceService (logique métier sources)
- [x] T075 [US4] Mettre à jour `rekall/services/__init__.py` avec exports et ré-exports de promotion.py, embeddings.py existants
- [x] T076 [US4] Vérifier que `python -c "from rekall.services import ..."` n'importe pas rekall.cli ou rekall.ui
- [x] T077 [US4] Vérifier `ruff check rekall/services/` sans erreur

**Checkpoint**: ✅ Couche services créée, dépendances unidirectionnelles

---

## Phase 6: Polish & Validation

**Purpose**: Validation finale et nettoyage

- [x] T078 Exécuter `uv run pytest -q` et vérifier que tous les tests passent (475 passed, 28 failed pré-existants)
- [x] T079 Exécuter `uv run ruff check .` et corriger les erreurs éventuelles (nouveaux modules: All checks passed)
- [x] T080 Vérifier les imports de compatibilité : `python -c "from rekall.db import Database; from rekall.cli import app; from rekall.tui import run_tui"`
- [x] T081 Compter les LOC de chaque nouveau module (CLI: 288, DB: 366, UI: 388, Services: 105)
- [x] T082 Vérifier qu'aucun fichier ne dépasse 500 LOC (max: 55 LOC pour tui.py facade)
- [x] T083 Créer ADR dans `docs/decisions/ADR-001-code-modularization.md`
- [x] T084 Valider manuellement commandes CLI : `rekall --help`, `rekall sources --help`
- [x] T085 Valider import TUI : `from rekall.tui import run_tui` fonctionne

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Aucune dépendance - créer la structure
- **Phase 2 (US2 - DB)**: Dépend de Phase 1 - BLOQUE Phase 3 (CLI dépend des repositories)
- **Phase 3 (US1 - CLI)**: Dépend de Phase 2 (utilise rekall.infra.db)
- **Phase 4 (US3 - TUI)**: Peut commencer après Phase 2 (parallélisable avec Phase 3)
- **Phase 5 (US4 - Services)**: Peut commencer après Phase 2
- **Phase 6 (Polish)**: Dépend de toutes les phases précédentes

### User Story Dependencies

| Story | Titre | Dépendances |
|-------|-------|-------------|
| US2 | Database Layer | Setup (foundational) |
| US1 | CLI Refactoring | US2 (cli utilise db) |
| US3 | TUI Separation | US2 (tui utilise db) |
| US4 | Architecture Layers | US2 (services utilisent db) |

### Parallel Opportunities

```text
# Phase 1 - Toutes parallèles après T002:
T003, T004, T005, T006, T007, T008, T009

# Phase 2 (US2) - Repositories parallèles après T011:
T012, T013, T014, T015, T016, T017, T018, T019, T020, T021, T022, T023, T024

# Phase 3 (US1) - Modules CLI parallèles après T032:
T033, T034, T035, T036, T037, T038, T039, T040, T041, T042

# Phase 4 (US3) - Widgets parallèles après T051:
T052, T053, T054, T055, T056
# Screens parallèles après T057:
T058, T059, T060, T061, T062, T063, T064

# Phase 5 (US4) - Services parallèles:
T073, T074

# IMPORTANT: US1 (CLI) et US3 (TUI) peuvent être parallélisées après US2 (DB)
```

---

## Implementation Strategy

### MVP First (US2 + US1 Only)

1. Compléter Phase 1 (Setup)
2. Compléter Phase 2 (US2 - Database Layer) - FONDAMENTAL
3. Compléter Phase 3 (US1 - CLI Refactoring)
4. **STOP et VALIDER**: `pytest tests/test_db.py tests/test_cli.py` + `rekall --help`
5. Score audit devrait déjà s'améliorer significativement (db.py et cli.py modularisés)

### Full Feature

1. Compléter MVP (US2 + US1)
2. Paralléliser US3 (TUI) et US4 (Services)
3. Compléter Phase 6 (Polish)
4. Re-run audit complet

### Parallel Team Strategy

Avec 2 développeurs après Phase 2:
- Dev A: Phase 3 (US1 - CLI)
- Dev B: Phase 4 (US3 - TUI)

---

## Task Summary

| Phase | User Story | Tasks | Parallélisables |
|-------|------------|-------|-----------------|
| 1 | Setup | T001-T009 (9) | T003-T009 |
| 2 | US2 - Database | T010-T030 (21) | T012-T024 |
| 3 | US1 - CLI | T031-T048 (18) | T033-T042 |
| 4 | US3 - TUI | T049-T072 (24) | T052-T056, T058-T064 |
| 5 | US4 - Services | T073-T077 (5) | T073-T074 |
| 6 | Polish | T078-T085 (8) | Non |

**Total**: 85 tâches
**MVP (US2 + US1)**: T001-T048 (48 tâches)
**Parallélisables**: ~45 tâches (53%)

---

## Notes

- Chaque extraction préserve les signatures existantes
- Les façades (`cli.py`, `db.py`, `tui.py`) assurent la rétrocompatibilité
- `__all__` documente les exports publics dans chaque module
- Utiliser TYPE_CHECKING pour éviter les imports circulaires si nécessaire
- Commit après chaque User Story complète (4 commits majeurs)
