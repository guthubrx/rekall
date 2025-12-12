# Tasks: Sources Medallion Architecture

**Input**: Design documents from `/specs/013-sources-medallion/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓, contracts/ ✓

**Tests**: Tests inclus dans chaque User Story conformément à la constitution (Article XV).

**Organization**: Tâches groupées par User Story pour permettre implémentation et tests indépendants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'exécuter en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User Story concernée (US1, US2, US3, etc.)
- Chemins exacts inclus dans les descriptions

## Path Conventions

```text
rekall/                   # Module principal
├── connectors/           # NOUVEAU - Plugin architecture
│   ├── __init__.py
│   ├── base.py
│   ├── claude_cli.py
│   └── cursor.py
├── enrichment.py         # NOUVEAU
├── promotion.py          # NOUVEAU
├── db.py                 # MODIFIER
├── models.py             # MODIFIER
├── cli.py                # MODIFIER
├── tui.py                # MODIFIER
├── i18n.py               # MODIFIER
└── config.py             # MODIFIER

tests/
├── test_connectors/
├── test_enrichment.py
├── test_promotion.py
└── test_db.py            # MODIFIER
```

---

## Phase 1: Setup (Infrastructure Partagée)

**Purpose**: Initialisation projet et dépendances

- [x] T001 Ajouter httpx et beautifulsoup4 dans pyproject.toml section [project.dependencies]
- [x] T002 [P] Créer le répertoire rekall/connectors/ avec __init__.py vide
- [x] T003 [P] Créer le répertoire tests/test_connectors/ avec __init__.py vide

---

## Phase 2: Foundational (Prérequis Bloquants)

**Purpose**: Infrastructure core qui DOIT être complète avant toute User Story

**⚠️ CRITICAL**: Aucun travail sur les User Stories ne peut commencer avant cette phase

### Modèles de Données

- [x] T004 [P] Ajouter dataclass InboxEntry dans rekall/models.py (Bronze layer)
- [x] T005 [P] Ajouter dataclass StagingEntry dans rekall/models.py (Silver layer)
- [x] T006 [P] Ajouter dataclass ConnectorImport dans rekall/models.py (CDC tracking)
- [x] T007 Ajouter constantes VALID_CONTENT_TYPES dans rekall/models.py

### Migration Database

- [x] T008 Incrémenter CURRENT_SCHEMA_VERSION à 11 dans rekall/db.py
- [x] T009 Ajouter MIGRATIONS[11] avec CREATE TABLE sources_inbox dans rekall/db.py
- [x] T010 Ajouter CREATE TABLE sources_staging dans la migration 11 rekall/db.py
- [x] T011 Ajouter CREATE TABLE connector_imports dans la migration 11 rekall/db.py
- [x] T012 Ajouter les index sur sources_inbox (url, domain, cli_source, captured_at, is_valid, enriched_at)
- [x] T013 Ajouter les index sur sources_staging (domain, score, promoted_at, content_type)

### CRUD Database

- [x] T014 Ajouter méthodes add_inbox_entry, get_inbox_entries dans rekall/db.py
- [x] T015 Ajouter méthode get_inbox_not_enriched(limit) dans rekall/db.py
- [x] T016 Ajouter méthode mark_inbox_enriched(id) dans rekall/db.py
- [x] T017 Ajouter méthodes add_staging_entry, get_staging_by_url, update_staging dans rekall/db.py
- [x] T018 Ajouter méthode get_staging_eligible_for_promotion(threshold) dans rekall/db.py
- [x] T019 Ajouter méthodes upsert_connector_import, get_connector_import dans rekall/db.py

### Traductions i18n

- [x] T020 Ajouter traductions inbox dans rekall/i18n.py (en + fr)
- [x] T021 [P] Ajouter traductions staging dans rekall/i18n.py (en + fr)
- [x] T022 [P] Ajouter traductions promotion dans rekall/i18n.py (en + fr)

### Tests Foundation

- [x] T023 Ajouter tests migration v11 dans tests/test_db.py
- [x] T024 [P] Ajouter tests CRUD inbox dans tests/test_db.py
- [x] T025 [P] Ajouter tests CRUD staging dans tests/test_db.py

**Checkpoint**: Foundation ready - implémentation User Stories peut commencer

---

## Phase 3: User Story 1 - Import Claude CLI (Priority: P1) 🎯 MVP

**Goal**: Importer les URLs depuis l'historique Claude Code dans l'inbox Bronze

**Independent Test**: `rekall sources inbox import --cli claude` importe les URLs WebFetch avec contexte

### Implementation for US1

- [x] T026 [US1] Créer classe abstraite BaseConnector dans rekall/connectors/base.py
- [x] T027 [US1] Implémenter méthode validate_url() dans BaseConnector rekall/connectors/base.py
- [x] T028 [US1] Créer ClaudeCLIConnector dans rekall/connectors/claude_cli.py
- [x] T029 [US1] Implémenter is_available() pour détecter ~/.claude/projects/ dans claude_cli.py
- [x] T030 [US1] Implémenter get_history_paths() pour lister les fichiers JSONL dans claude_cli.py
- [x] T031 [US1] Implémenter extract_urls() pour parser JSONL et extraire WebFetch URLs dans claude_cli.py
- [x] T032 [US1] Ajouter extraction du contexte (user_query, project, conversation_id) dans extract_urls()
- [x] T033 [US1] Implémenter import incrémental CDC via connector_imports dans claude_cli.py
- [x] T034 [US1] Créer registry get_connector() et list_connectors() dans rekall/connectors/__init__.py
- [x] T035 [US1] Ajouter commande CLI `sources inbox import` dans rekall/cli.py
- [x] T036 [US1] Implémenter options --cli, --since, --dry-run pour import dans cli.py

### Tests for US1

- [x] T037 [P] [US1] Créer fixture JSONL de test dans tests/test_connectors/fixtures/
- [x] T038 [P] [US1] Tester is_available() dans tests/test_connectors/test_claude_cli.py
- [x] T039 [US1] Tester extract_urls() avec parsing JSONL dans test_claude_cli.py
- [x] T040 [US1] Tester validation URL (quarantine localhost, file://) dans test_claude_cli.py
- [x] T041 [US1] Tester import incrémental CDC dans test_claude_cli.py

**Checkpoint**: US1 fonctionnelle - import Claude CLI opérationnel

---

## Phase 4: User Story 2 - Enrichissement Automatique (Priority: P1) 🎯 MVP

**Goal**: Enrichir automatiquement les URLs Bronze avec métadonnées et les consolider en Silver

**Independent Test**: Après import, les sources staging ont titre et type de contenu

### Implementation for US2

- [x] T042 [US2] Créer module rekall/enrichment.py avec fonction enrich_inbox_entries()
- [x] T043 [US2] Implémenter fetch_metadata() avec httpx pour récupérer HTML dans enrichment.py
- [x] T044 [US2] Implémenter extraction titre (title, og:title) avec BeautifulSoup dans enrichment.py
- [x] T045 [US2] Implémenter extraction description (meta description, og:description) dans enrichment.py
- [x] T046 [US2] Implémenter classify_content_type() par heuristique domaine/URL dans enrichment.py
- [x] T047 [US2] Implémenter detect_language() depuis attribut html lang dans enrichment.py
- [x] T048 [US2] Implémenter déduplication: merge_into_staging() si URL existe déjà dans enrichment.py
- [x] T049 [US2] Gérer timeout et erreurs HTTP (marquer is_accessible=false) dans enrichment.py
- [x] T050 [US2] Ajouter commande CLI `sources staging enrich` dans rekall/cli.py
- [x] T051 [US2] Implémenter options --batch et --timeout pour enrich dans cli.py

### Tests for US2

- [x] T052 [P] [US2] Tester fetch_metadata() avec mocking httpx dans tests/test_enrichment.py
- [x] T053 [P] [US2] Tester classify_content_type() dans test_enrichment.py
- [x] T054 [US2] Tester déduplication merge_into_staging() dans test_enrichment.py
- [x] T055 [US2] Tester gestion timeout et erreurs HTTP dans test_enrichment.py

**Checkpoint**: US2 fonctionnelle - pipeline Bronze → Silver opérationnel

---

## Phase 5: User Story 3 - TUI Inbox Bronze (Priority: P2)

**Goal**: Interface tableau pour visualiser et gérer l'inbox des sources capturées

**Independent Test**: `rekall sources inbox` affiche DataTable avec URL/CLI/Projet/Date

### Implementation for US3

- [x] T056 [US3] Créer InboxScreen héritant de Screen dans rekall/tui.py
- [x] T057 [US3] Implémenter DataTable avec colonnes URL, CLI Source, Projet, Date dans InboxScreen
- [x] T058 [US3] Ajouter binding 'i' pour déclencher import dans InboxScreen
- [x] T059 [US3] Ajouter binding 'e' pour déclencher enrichissement dans InboxScreen
- [x] T060 [US3] Ajouter binding 'q' pour basculer vue quarantine dans InboxScreen
- [x] T061 [US3] Ajouter binding 'd' pour supprimer entrée sélectionnée dans InboxScreen
- [x] T062 [US3] Implémenter formatage date relatif ("il y a 2h") dans tui.py
- [x] T063 [US3] Ajouter commande CLI `sources inbox browse` qui lance InboxScreen dans cli.py
- [x] T064 [US3] Ajouter commande CLI `sources inbox stats` dans cli.py
- [x] T065 [US3] Ajouter commande CLI `sources inbox quarantine` via browse --quarantine dans cli.py
- [x] T066 [US3] Ajouter commande CLI `sources inbox clear` avec --all --force dans cli.py

**Checkpoint**: US3 fonctionnelle - TUI Inbox opérationnel

---

## Phase 6: User Story 4 - TUI Staging Silver (Priority: P2)

**Goal**: Interface tableau staging avec scores et indicateurs de promotion

**Independent Test**: `rekall sources staging` affiche DataTable avec indicateurs ⬆/→

### Implementation for US4

- [x] T067 [US4] Créer module rekall/promotion.py avec calculate_promotion_score()
- [x] T068 [US4] Implémenter formule score avec poids (citation, project, recency) dans promotion.py
- [x] T069 [US4] Implémenter decay temporel basé sur last_seen dans calculate_promotion_score()
- [x] T070 [US4] Implémenter is_eligible_for_promotion(staging, threshold) dans promotion.py
- [x] T071 [US4] Créer StagingScreen héritant de Screen dans rekall/tui.py
- [x] T072 [US4] Implémenter DataTable avec colonnes Domaine, Titre, Type, Citations, Projets, Score dans StagingScreen
- [x] T073 [US4] Ajouter colonne indicateur (⬆ éligible, → proche 80%) dans StagingScreen
- [x] T074 [US4] Ajouter binding 'r' pour rafraîchir les scores dans StagingScreen
- [x] T075 [US4] Ajouter binding 'Enter' pour afficher détails source dans StagingScreen
- [x] T076 [US4] Ajouter commande CLI `sources staging browse` qui lance StagingScreen dans cli.py

### Tests for US4

- [x] T077 [P] [US4] Tester calculate_promotion_score() dans tests/test_promotion.py
- [x] T078 [P] [US4] Tester decay temporel dans test_promotion.py
- [x] T079 [US4] Tester is_eligible_for_promotion() dans test_promotion.py

**Checkpoint**: US4 fonctionnelle - TUI Staging avec scores opérationnel

---

## Phase 7: User Story 5 - Promotion Automatique (Priority: P2)

**Goal**: Promouvoir automatiquement les sources atteignant le seuil vers Gold

**Independent Test**: Source avec score > seuil apparaît dans sources Gold après job

### Implementation for US5

- [x] T080 [US5] Implémenter promote_source(staging_id) dans rekall/promotion.py
- [x] T081 [US5] Créer Source Gold depuis StagingEntry avec is_promoted=true dans promote_source()
- [x] T082 [US5] Mettre à jour StagingEntry.promoted_to et promoted_at après promotion
- [x] T083 [US5] Implémenter auto_promote_eligible(threshold) pour promotion batch dans promotion.py
- [x] T084 [US5] Ajouter vérification unicité URL avant création Source Gold dans promote_source()
- [x] T085 [US5] Ajouter commande CLI `sources staging promote --auto` dans cli.py
- [x] T086 [US5] Ajouter binding 'a' pour auto-promote dans StagingScreen tui.py

### Tests for US5

- [x] T087 [P] [US5] Tester promote_source() dans tests/test_promotion.py
- [x] T088 [US5] Tester unicité URL (pas de duplication Gold) dans test_promotion.py
- [x] T089 [US5] Tester auto_promote_eligible() batch dans test_promotion.py

**Checkpoint**: US5 fonctionnelle - promotion automatique opérationnelle

---

## Phase 8: User Story 6 - Promotion/Dépromouvoir Manuelles (Priority: P2)

**Goal**: Permettre promotion manuelle et dépromouvoir des sources

**Independent Test**: Promouvoir manuellement une source sous-seuil, puis la dépromouvoir

### Implementation for US6

- [x] T090 [US6] Ajouter commande CLI `sources staging promote <URL_OR_ID>` (manuel) dans cli.py
- [x] T091 [US6] Ajouter binding 'p' pour promotion manuelle dans StagingScreen tui.py
- [x] T092 [US6] Implémenter demote_source(source_id) dans rekall/promotion.py
- [x] T093 [US6] Supprimer Source Gold et reset StagingEntry.promoted_* dans demote_source()
- [x] T094 [US6] Ajouter validation: seules sources is_promoted=true peuvent être dépromotues
- [x] T095 [US6] Ajouter commande CLI `sources demote <SOURCE_ID>` dans cli.py
- [x] T096 [US6] Ajouter action dépromouvoir dans TUI Sources Gold existant dans tui.py
- [x] T097 [US6] Ajouter commande CLI `sources staging drop <URL_OR_ID>` dans cli.py

### Tests for US6

- [x] T098 [P] [US6] Tester demote_source() dans tests/test_promotion.py
- [x] T099 [US6] Tester erreur sur dépromouvoir source non-promue dans test_promotion.py

**Checkpoint**: US6 fonctionnelle - promotion/dépromouvoir manuelles opérationnelles

---

## Phase 9: User Story 7 - Import Cursor IDE (Priority: P3)

**Goal**: Importer les URLs depuis l'historique Cursor pour consolidation

**Independent Test**: `rekall sources inbox import --cli cursor` extrait URLs depuis SQLite Cursor

### Implementation for US7

- [x] T100 [US7] Créer CursorConnector dans rekall/connectors/cursor.py
- [x] T101 [US7] Implémenter is_available() pour détecter workspaceStorage Cursor dans cursor.py
- [x] T102 [US7] Implémenter get_history_paths() pour lister state.vscdb dans cursor.py
- [x] T103 [US7] Implémenter extract_urls() pour parser SQLite et extraire URLs dans cursor.py
- [x] T104 [US7] Ajouter extraction URLs via regex depuis contenu JSON chat dans cursor.py
- [x] T105 [US7] Enregistrer CursorConnector dans registry connectors/__init__.py

### Tests for US7

- [x] T106 [P] [US7] Créer fixture SQLite de test dans tests/test_connectors/fixtures/
- [x] T107 [US7] Tester extract_urls() avec parsing SQLite dans tests/test_connectors/test_cursor.py
- [x] T108 [US7] Tester gestion Cursor non installé (fallback gracieux) dans test_cursor.py

**Checkpoint**: US7 fonctionnelle - import Cursor opérationnel

---

## Phase 10: User Story 8 - Configuration Promotion (Priority: P3)

**Goal**: Permettre de configurer les poids et seuil de promotion

**Independent Test**: Modifier seuil via CLI, vérifier indicateurs changent dans TUI

### Implementation for US8

- [x] T109 [US8] Ajouter DEFAULT_PROMOTION_CONFIG dans rekall/config.py
- [x] T110 [US8] Ajouter méthodes get_promotion_config(), set_promotion_config() dans config.py
- [x] T111 [US8] Persister config promotion dans metadata table ou fichier config
- [x] T112 [US8] Ajouter commande CLI `sources promotion-config --threshold` dans cli.py
- [x] T113 [US8] Ajouter commande CLI `sources promotion-config --weights` avec options dans cli.py
- [x] T114 [US8] Intégrer config dans calculate_promotion_score() et auto_promote_eligible()

**Checkpoint**: US8 fonctionnelle - configuration promotion opérationnelle

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Améliorations transversales

- [x] T115 [P] Vérifier tous les messages d'erreur sont traduits dans i18n.py
- [ ] T116 [P] Ajouter logging pour debug dans enrichment.py et promotion.py (optionnel)
- [x] T117 Exécuter `ruff check --fix rekall/` pour lint et formatting
- [x] T118 Exécuter `pytest tests/ -v` et corriger les échecs
- [ ] T119 Valider quickstart.md avec test manuel du workflow complet (optionnel)
- [x] T120 Documenter les nouvelles commandes dans README ou help strings (via docstrings)

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1: Setup          → Aucune dépendance
Phase 2: Foundational   → Dépend de Phase 1, BLOQUE toutes les US
Phase 3: US1 (Import)   → Dépend de Phase 2
Phase 4: US2 (Enrich)   → Dépend de Phase 2 + US1 (données à enrichir)
Phase 5: US3 (TUI Inbox)→ Dépend de Phase 2, peut paralléliser avec US1/US2
Phase 6: US4 (TUI Stage)→ Dépend de Phase 2 + US2 (données staging)
Phase 7: US5 (Auto-prom)→ Dépend de US4 (scoring)
Phase 8: US6 (Manual)   → Dépend de US5 (promotion logic)
Phase 9: US7 (Cursor)   → Dépend de Phase 2, parallélisable avec US1
Phase 10: US8 (Config)  → Dépend de US5 (promotion config)
Phase 11: Polish        → Dépend de toutes US complétées
```

### User Story Dependencies

| Story | Peut commencer après | Indépendamment testable |
|-------|---------------------|------------------------|
| US1 (Import Claude) | Phase 2 | ✅ Oui - import seul |
| US2 (Enrichissement) | US1 | ✅ Oui - avec données test |
| US3 (TUI Inbox) | Phase 2 | ✅ Oui - avec données mock |
| US4 (TUI Staging) | US2 | ✅ Oui - avec données test |
| US5 (Auto-promote) | US4 | ✅ Oui - avec données test |
| US6 (Manual promote) | US5 | ✅ Oui - avec données test |
| US7 (Import Cursor) | Phase 2 | ✅ Oui - import seul |
| US8 (Config) | US5 | ✅ Oui - config seule |

### Within Each User Story

1. Tests (si inclus) DOIVENT être écrits et ÉCHOUER avant implémentation
2. Modèles avant services
3. Services avant endpoints CLI
4. CLI avant TUI
5. Story complète avant passage à la suivante

### Parallel Opportunities

**Phase 2 (Foundational)**:
```bash
# Modèles en parallèle:
Task T004: "InboxEntry dans models.py"
Task T005: "StagingEntry dans models.py"
Task T006: "ConnectorImport dans models.py"

# Traductions en parallèle:
Task T020: "inbox i18n"
Task T021: "staging i18n"
Task T022: "promotion i18n"
```

**US1 + US7 en parallèle** (connecteurs indépendants):
```bash
# Développeur A: US1 Claude
Task T026-T041

# Développeur B: US7 Cursor
Task T100-T108
```

**US3 + US4 en parallèle** (TUI indépendants si données mock):
```bash
# Développeur A: TUI Inbox
Task T056-T066

# Développeur B: TUI Staging
Task T067-T079
```

---

## Parallel Example: Phase 2 Foundation

```bash
# Batch 1: Tous les modèles en parallèle
Task: "Ajouter dataclass InboxEntry dans rekall/models.py"
Task: "Ajouter dataclass StagingEntry dans rekall/models.py"
Task: "Ajouter dataclass ConnectorImport dans rekall/models.py"

# Batch 2: Toutes les traductions en parallèle
Task: "Ajouter traductions inbox dans rekall/i18n.py"
Task: "Ajouter traductions staging dans rekall/i18n.py"
Task: "Ajouter traductions promotion dans rekall/i18n.py"

# Batch 3: Migration (séquentiel car même fichier)
Task: "Ajouter MIGRATIONS[11] sources_inbox"
Task: "Ajouter sources_staging dans migration 11"
Task: "Ajouter connector_imports dans migration 11"
```

---

## Implementation Strategy

### MVP First (US1 + US2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 - Import Claude CLI
4. Complete Phase 4: US2 - Enrichissement
5. **STOP and VALIDATE**: Tester import + enrichissement end-to-end
6. Deploy/demo si prêt

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (Import Claude) → Test → MVP minimal
3. US2 (Enrichissement) → Test → Pipeline complet Bronze→Silver
4. US3 (TUI Inbox) → Test → Visualisation Bronze
5. US4 (TUI Staging) + US5 (Auto-promote) → Test → Cycle complet
6. US6 (Manual) + US7 (Cursor) + US8 (Config) → Test → Feature complète
7. Polish → Release

### Suggested MVP Scope

**MVP = US1 + US2** (Import Claude + Enrichissement)
- Permet de capturer et enrichir les URLs
- Pas d'interface TUI (vérification via CLI ou SQL directe)
- ~41 tâches au lieu de 120
- Fournit la valeur core immédiatement

---

## Summary

| Metric | Value |
|--------|-------|
| **Total Tasks** | 120 |
| **Setup Tasks** | 3 |
| **Foundational Tasks** | 22 |
| **US1 Tasks** | 16 |
| **US2 Tasks** | 14 |
| **US3 Tasks** | 11 |
| **US4 Tasks** | 13 |
| **US5 Tasks** | 10 |
| **US6 Tasks** | 10 |
| **US7 Tasks** | 9 |
| **US8 Tasks** | 6 |
| **Polish Tasks** | 6 |
| **Parallel Opportunities** | ~35 tâches [P] |
| **MVP Scope** | US1 + US2 (~55 tâches) |

---

## Notes

- [P] tasks = fichiers différents, pas de dépendances
- [Story] label mappe la tâche à la User Story pour traçabilité
- Chaque User Story devrait être indépendamment complétable et testable
- Vérifier que les tests échouent avant d'implémenter
- Commit après chaque tâche ou groupe logique
- S'arrêter à n'importe quel checkpoint pour valider la story
- Éviter: tâches vagues, conflits sur même fichier, dépendances cross-story qui cassent l'indépendance
