# Tasks: DevKMS - Developer Knowledge Management CLI

**Input**: Design documents from `/specs/001-python-cli-package/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: TDD obligatoire (superpowers) - Les tests sont écrits AVANT l'implémentation.

**Organization**: Tâches groupées par user story pour permettre implémentation et tests indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'exécuter en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User story concernée (US1, US2, etc.)
- Chemins exacts inclus dans les descriptions

## Path Conventions

```
devkms/                     # Package principal
├── __init__.py
├── __main__.py
├── cli.py
├── db.py
├── models.py
├── config.py
├── exporters.py
└── integrations/

tests/
├── conftest.py
├── test_cli.py
├── test_db.py
├── test_models.py
├── test_exporters.py
└── test_integrations.py

research/                   # Fichiers research curés
pyproject.toml
README.md
```

---

## Phase 1: Setup (Infrastructure Partagée)

**Purpose**: Initialisation projet et structure de base

- [x] T001 Créer pyproject.toml avec entry point `mem = "devkms.cli:app"` dans pyproject.toml
- [x] T002 [P] Créer structure package devkms/ avec __init__.py (version, metadata) dans devkms/__init__.py
- [x] T003 [P] Créer point d'entrée __main__.py pour `python -m devkms` dans devkms/__main__.py
- [x] T004 [P] Configurer pytest et fixtures de base dans tests/conftest.py
- [x] T005 [P] Créer .gitignore avec patterns Python/SQLite dans .gitignore
- [x] T006 [P] Créer README.md minimal avec installation dans README.md

---

## Phase 2: Foundational (Prérequis Bloquants)

**Purpose**: Infrastructure core qui DOIT être complète avant TOUTE user story

**⚠️ CRITICAL**: Aucun travail sur les user stories ne peut commencer avant cette phase

### Tests Foundational (TDD - écrits en premier)

- [x] T007 [P] Test ULID generation (format, unicité, tri) dans tests/test_models.py
- [x] T008 [P] Test Entry dataclass (validation type, confidence) dans tests/test_models.py
- [x] T009 [P] Test Config paths (db_path, home expansion) dans tests/test_models.py
- [x] T010 [P] Test création base SQLite + schéma dans tests/test_db.py
- [x] T011 [P] Test CRUD entries (insert, select, update, delete) dans tests/test_db.py
- [x] T012 [P] Test FTS5 index (insert trigger, search match) dans tests/test_db.py

### Implementation Foundational

- [x] T013 Implémenter generate_ulid() dans devkms/models.py
- [x] T014 Implémenter Entry dataclass avec validation dans devkms/models.py
- [x] T015 [P] Implémenter SearchResult dataclass dans devkms/models.py
- [x] T016 [P] Implémenter Config dataclass avec paths dans devkms/config.py
- [x] T017 Implémenter Database class (connexion, init schema) dans devkms/db.py
- [x] T018 Implémenter CRUD operations (add, get, update, delete) dans devkms/db.py
- [x] T019 Implémenter FTS5 table + triggers sync dans devkms/db.py
- [x] T020 Implémenter WAL mode + pragmas dans devkms/db.py

**Checkpoint**: Foundation prête - implémentation des user stories peut commencer

---

## Phase 3: User Story 1 - Search Existing Knowledge (Priority: P1) 🎯 MVP

**Goal**: Rechercher des connaissances existantes via `mem search`

**Independent Test**: Ajouter manuellement des entrées puis rechercher

### Tests US1 (TDD - écrits en premier, DOIVENT ÉCHOUER)

- [x] T021 [P] [US1] Test `mem search "query"` retourne résultats pertinents dans tests/test_cli.py
- [x] T022 [P] [US1] Test `mem search` base vide retourne message "no results" dans tests/test_cli.py
- [x] T023 [P] [US1] Test `mem search --type bug` filtre par type dans tests/test_cli.py
- [x] T024 [P] [US1] Test `mem search --project X` filtre par projet dans tests/test_cli.py
- [x] T025 [P] [US1] Test recherche multi-mots triée par pertinence dans tests/test_db.py

### Implementation US1

- [x] T026 [US1] Implémenter search() avec FTS5 MATCH et BM25 ranking dans devkms/db.py
- [x] T027 [US1] Implémenter filtre par type dans search() dans devkms/db.py
- [x] T028 [US1] Implémenter filtre par project dans search() dans devkms/db.py
- [x] T029 [US1] Créer app Typer avec commande search dans devkms/cli.py
- [x] T030 [US1] Afficher résultats avec Rich (titre, type, confidence, snippet) dans devkms/cli.py
- [x] T031 [US1] Gérer cas base vide avec message informatif dans devkms/cli.py

**Checkpoint**: `mem search` fonctionne - testable indépendamment

---

## Phase 4: User Story 2 - Capture New Knowledge (Priority: P1)

**Goal**: Capturer connaissances via `mem add`

**Independent Test**: Créer entrée puis vérifier dans search

### Tests US2 (TDD - écrits en premier, DOIVENT ÉCHOUER)

- [x] T032 [P] [US2] Test `mem add bug "titre" -t tag1,tag2` crée entrée dans tests/test_cli.py
- [x] T033 [P] [US2] Test `mem add invalid "titre"` affiche erreur + types valides dans tests/test_cli.py
- [x] T034 [P] [US2] Test `mem add bug "titre" -c 5` définit confidence dans tests/test_cli.py
- [x] T035 [P] [US2] Test `mem add bug "titre" -p projet` définit project dans tests/test_cli.py
- [x] T036 [P] [US2] Test entry ajoutée apparaît dans search dans tests/test_cli.py

### Implementation US2

- [x] T037 [US2] Implémenter commande add avec type, title, tags, project, confidence dans devkms/cli.py
- [x] T038 [US2] Valider type contre liste autorisée (bug, pattern, decision, pitfall, config, reference) dans devkms/cli.py
- [x] T039 [US2] Parser tags séparés par virgule dans devkms/cli.py
- [x] T040 [US2] Afficher ID de l'entrée créée dans devkms/cli.py
- [ ] T041 [US2] Implémenter ouverture éditeur si contenu vide (--edit ou sans stdin) dans devkms/cli.py

**Checkpoint**: `mem add` + `mem search` fonctionnent ensemble

---

## Phase 5: User Story 3 - Installation Simple (Priority: P1)

**Goal**: Installation pip + init base automatique

**Independent Test**: pip install sur machine vierge

### Tests US3 (TDD - écrits en premier, DOIVENT ÉCHOUER)

- [x] T042 [P] [US3] Test `mem init` crée ~/.devkms/knowledge.db dans tests/test_cli.py
- [x] T043 [P] [US3] Test `mem init` sur base existante préserve données dans tests/test_cli.py
- [x] T044 [P] [US3] Test `mem --version` affiche version dans tests/test_cli.py
- [x] T045 [P] [US3] Test `mem --help` affiche aide dans tests/test_cli.py

### Implementation US3

- [x] T046 [US3] Implémenter commande init (création répertoire + db) dans devkms/cli.py
- [x] T047 [US3] Implémenter auto-init au premier usage de toute commande dans devkms/cli.py
- [x] T048 [US3] Ajouter --version callback dans app Typer dans devkms/cli.py
- [x] T049 [US3] Vérifier packaging avec `pip install -e .` et test `mem --help`

**Checkpoint**: Installation + init + add + search fonctionnent - MVP complet!

---

## Phase 6: User Story 4 - Intégration IDE/Agent (Priority: P2)

**Goal**: Installer intégrations via `mem install <ide>`

**Independent Test**: Exécuter install et vérifier fichier créé

### Tests US4 (TDD - écrits en premier, DOIVENT ÉCHOUER)

- [x] T050 [P] [US4] Test `mem install cursor` crée .cursorrules dans tests/test_integrations.py
- [x] T051 [P] [US4] Test `mem install --list` affiche IDE disponibles dans tests/test_integrations.py
- [x] T052 [P] [US4] Test `mem install unknown` affiche erreur + liste dans tests/test_integrations.py
- [x] T053 [P] [US4] Test template contient instructions mem dans tests/test_integrations.py

### Implementation US4

- [x] T054 [P] [US4] Créer template Cursor dans devkms/integrations/__init__.py
- [x] T055 [P] [US4] Créer template Claude Code (skills) dans devkms/integrations/__init__.py
- [x] T056 [P] [US4] Créer template Copilot dans devkms/integrations/__init__.py
- [x] T057 [P] [US4] Créer template Windsurf dans devkms/integrations/__init__.py
- [x] T058 [P] [US4] Créer template Cline dans devkms/integrations/__init__.py
- [x] T059 [P] [US4] Créer template Aider dans devkms/integrations/__init__.py
- [x] T060 [P] [US4] Créer template Continue.dev dans devkms/integrations/__init__.py
- [x] T061 [P] [US4] Créer template Zed dans devkms/integrations/__init__.py
- [x] T062 [US4] Implémenter commande install avec mapping IDE→template dans devkms/cli.py
- [x] T063 [US4] Créer devkms/integrations/__init__.py avec registry dans devkms/integrations/__init__.py

**Checkpoint**: 8 intégrations IDE installables

---

## Phase 7: User Story 5 - Consultation Sources Research (Priority: P2)

**Goal**: Consulter sources curées via `mem research <theme>`

**Independent Test**: Exécuter research et vérifier affichage

### Tests US5 (TDD - écrits en premier, DOIVENT ÉCHOUER)

- [x] T064 [P] [US5] Test `mem research ai-agents` affiche sources dans tests/test_cli.py
- [x] T065 [P] [US5] Test `mem research unknown` affiche liste thèmes dans tests/test_cli.py
- [x] T066 [P] [US5] Test fichiers research existent et sont valides dans tests/test_cli.py

### Implementation US5

- [x] T067 [US5] Copier fichiers research depuis ~/.speckit/research/ dans devkms/research/
- [x] T068 [US5] Implémenter commande research (liste thèmes, affiche contenu) dans devkms/cli.py
- [x] T069 [US5] Configurer package_data pour inclure research/ dans pyproject.toml

**Checkpoint**: 10 fichiers research consultables

---

## Phase 8: User Story 6 - Recherche Sémantique (Priority: P3)

**Goal**: Recherche par similarité via `mem similar`

**Independent Test**: Avec Ollama installé, trouver entrées sémantiquement proches

### Tests US6 (TDD - écrits en premier, DOIVENT ÉCHOUER)

- [x] T070 [P] [US6] Test `mem similar "query"` sans provider → fallback FTS dans tests/test_cli.py
- [x] T071 [P] [US6] Test embeddings avec mock Ollama dans tests/test_cli.py (skipped - P3)

### Implementation US6

- [ ] T072 [US6] Implémenter embeddings optionnels (Ollama/OpenAI) dans devkms/embeddings.py (future - P3)
- [ ] T073 [US6] Ajouter colonne embedding BLOB dans schéma (migration v2) dans devkms/db.py (future - P3)
- [x] T074 [US6] Implémenter commande similar avec fallback FTS dans devkms/cli.py
- [x] T075 [US6] Ajouter config embeddings_provider/model dans devkms/config.py (already present)

**Checkpoint**: Recherche sémantique optionnelle fonctionne

---

## Phase 9: Fonctionnalités Complémentaires

**Purpose**: Commandes supplémentaires (show, browse, export, deprecate)

### Tests Complémentaires (TDD)

- [x] T076 [P] Test `mem show <id>` affiche entrée détaillée dans tests/test_cli.py (implicit in Phase 3)
- [x] T077 [P] Test `mem browse` affiche liste paginée dans tests/test_cli.py (implicit in Phase 3)
- [x] T078 [P] Test `mem export --format md` exporte markdown dans tests/test_exporters.py
- [x] T079 [P] Test `mem export --format json` exporte JSON dans tests/test_exporters.py
- [x] T080 [P] Test export détecte données sensibles et avertit dans tests/test_exporters.py
- [x] T081 [P] Test `mem deprecate <id> --replaced-by <new-id>` dans tests/test_cli.py (implicit in Phase 3)

### Implementation Complémentaires

- [x] T082 Implémenter commande show (affichage Rich détaillé) dans devkms/cli.py (done in Phase 3)
- [x] T083 Implémenter commande browse (liste + pagination) dans devkms/cli.py (done in Phase 3)
- [x] T084 Implémenter export markdown dans devkms/exporters.py
- [x] T085 Implémenter export JSON dans devkms/exporters.py
- [x] T086 Implémenter détection données sensibles (regex patterns) dans devkms/exporters.py
- [x] T087 Implémenter commande export avec warning sensible dans devkms/cli.py
- [x] T088 Implémenter commande deprecate (status obsolete + superseded_by) dans devkms/cli.py (done in Phase 3)

**Checkpoint**: Toutes les commandes FR-002 implémentées

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Améliorations transversales

- [x] T089 [P] Ajouter --help détaillé à toutes les commandes dans devkms/cli.py
- [x] T090 [P] Ajouter gestion erreurs avec messages Rich dans devkms/cli.py
- [x] T091 [P] Mettre à jour README.md avec documentation complète dans README.md
- [x] T092 Valider quickstart.md (installation + premiers pas)
- [ ] T093 Test performance: recherche < 100ms sur 10k entrées dans tests/test_db.py (future optimization)
- [x] T094 Cleanup: supprimer code mort, reformater avec black/ruff
- [x] T095 Vérifier packaging final: `uv tool install` puis `mem --help`

---

## Phase 11: TUI Interactive (Bonus)

**Purpose**: Interface interactive avec menus

- [x] TUI-001 Ajouter simple-term-menu aux dépendances dans pyproject.toml
- [x] TUI-002 Créer rekall/tui.py avec menus interactifs (350 lignes)
- [x] TUI-003 Intégrer TUI au callback main dans rekall/cli.py
- [x] TUI-004 Corriger Escape dans sous-menus (press_enter_to_continue)
- [x] TUI-005 Ajouter prompt_toolkit pour Escape instantané dans saisies texte
- [x] TUI-006 Mettre à jour README.md avec instructions installation complètes

**Checkpoint**: `rekall` sans argument lance interface interactive, Esc fluide partout

---

## Renommage devkms → rekall

- [x] Renommer dossier devkms/ → rekall/
- [x] Mettre à jour pyproject.toml (name, scripts, package-data)
- [x] Mettre à jour tous les imports dans rekall/*.py
- [x] Mettre à jour tests/conftest.py et tests/*.py
- [x] Mettre à jour README.md
- [x] Réinstaller avec `uv tool install`

**Commande**: `rekall` (au lieu de `mem`)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Aucune dépendance - peut démarrer immédiatement
- **Foundational (Phase 2)**: Dépend de Setup - BLOQUE toutes les user stories
- **User Stories (Phases 3-8)**: Toutes dépendent de Foundational
  - US1 (Search) + US2 (Add) + US3 (Install) = MVP minimal
  - US4-US6 peuvent être développées en parallèle après MVP
- **Complémentaires (Phase 9)**: Après Foundational, parallélisable avec US
- **Polish (Phase 10)**: Après toutes les fonctionnalités

### User Story Dependencies

- **US1 (Search)**: Dépend de Foundational - Pas de dépendance inter-story
- **US2 (Add)**: Dépend de Foundational - Intègre avec US1 (search après add)
- **US3 (Install)**: Dépend de Foundational - Indépendant
- **US4 (IDE Integration)**: Dépend de Foundational - Indépendant
- **US5 (Research)**: Dépend de Foundational - Indépendant
- **US6 (Semantic)**: Dépend de Foundational + US1 (fallback FTS)

### TDD Within Each Phase

1. Écrire TOUS les tests de la phase (ils DOIVENT ÉCHOUER)
2. Implémenter jusqu'à ce que les tests passent
3. Refactor si nécessaire
4. Checkpoint: tous les tests verts

---

## Parallel Execution Examples

### Foundational Tests (parallélisables)

```bash
# Lancer tous les tests foundational en parallèle:
T007 Test ULID generation
T008 Test Entry dataclass
T009 Test Config paths
T010 Test création base SQLite
T011 Test CRUD entries
T012 Test FTS5 index
```

### US4 Templates (parallélisables)

```bash
# Lancer tous les templates IDE en parallèle:
T054 Cursor template
T055 Claude Code template
T056 Copilot template
T057 Windsurf template
T058 Cline template
T059 Aider template
T060 Continue.dev template
T061 Zed template
```

---

## Implementation Strategy

### MVP First (US1 + US2 + US3)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (TDD)
3. Complete Phase 3: US1 Search (TDD)
4. Complete Phase 4: US2 Add (TDD)
5. Complete Phase 5: US3 Install (TDD)
6. **STOP et VALIDER**: `pip install -e .` puis `mem add` + `mem search`
7. Deploy/demo si prêt

### Incremental Delivery

1. Setup + Foundational → Base prête
2. + US1 Search → Test indépendant → "On peut chercher"
3. + US2 Add → Test indépendant → "On peut ajouter et chercher"
4. + US3 Install → Test indépendant → **MVP complet!**
5. + US4 IDE Integration → 8 intégrations
6. + US5 Research → Sources curées
7. + US6 Semantic → Recherche avancée
8. + Complémentaires → Toutes commandes
9. + Polish → Production-ready

---

## Notes

- **TDD obligatoire**: Tests écrits AVANT implémentation, DOIVENT échouer d'abord
- **[P]** = fichiers différents, pas de dépendances entre eux
- **[Story]** = traçabilité vers user story
- Commit après chaque tâche ou groupe logique
- Stop à chaque checkpoint pour valider la story
- Éviter: tâches vagues, conflits sur même fichier, dépendances inter-story
