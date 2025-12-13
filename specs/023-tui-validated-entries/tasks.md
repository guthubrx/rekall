# Tasks: TUI Enriched Entries Tab

**Feature**: 023-tui-validated-entries
**Input**: Design documents from `/specs/023-tui-validated-entries/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/tui-enriched-tab.md, research.md

**Tests**: Tests unitaires inclus (Phase finale) car mentionnes dans le plan.

**Organization**: Taches groupees par user story pour implementation et test independants.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'executer en parallele (fichiers differents, pas de dependances)
- **[Story]**: User story concernee (US1, US2, US3)
- Chemins exacts dans les descriptions

## Path Conventions

- **Fichier principal TUI**: `rekall/tui_main.py`
- **Base de donnees**: `rekall/db.py`
- **Tests**: `tests/test_tui_enriched.py`

---

## Phase 1: Setup (Prerequis partages)

**Purpose**: Verification de l'environnement et preparation

- [ ] T001 Verifier que le worktree est a jour avec `git fetch origin && git status` dans `.worktrees/023-tui-validated-entries/`
- [ ] T002 Verifier les sources enrichies existantes via `SELECT COUNT(*) FROM sources WHERE enrichment_status != 'none'` dans `rekall/db.py`
- [ ] T003 [P] Creer une source enrichie de test si aucune n'existe via `rekall_enrich_source` dans le MCP

---

## Phase 2: Foundational (Database Layer)

**Purpose**: Methodes DB qui DOIVENT etre completes avant toute implementation TUI

**CRITICAL**: La TUI depend de ces methodes - pas de parallelisation avec les phases suivantes

- [ ] T004 Implementer `get_enriched_sources(status, limit)` dans `rekall/db.py` - requete SQL avec tri par statut puis confidence
- [ ] T005 [P] Implementer `validate_enrichment(source_id)` dans `rekall/db.py` - UPDATE proposed -> validated + timestamp
- [ ] T006 [P] Implementer `reject_enrichment(source_id)` dans `rekall/db.py` - UPDATE proposed -> none (FR-009)
- [ ] T007 [P] Implementer `count_enriched_sources()` dans `rekall/db.py` - retourne dict {total, proposed, validated}

**Checkpoint**: Methodes DB pretes - les phases TUI peuvent maintenant commencer

---

## Phase 3: User Story 1 - Consulter les entrees enrichies (Priority: P1) MVP

**Goal**: L'utilisateur peut voir un onglet "Enrichies" distinct affichant les sources avec metadonnees IA

**Independent Test**: Ouvrir TUI > appuyer `n` > voir liste des sources enrichies avec leurs colonnes (domain, ai_type, confidence, status, tags)

### Implementation for User Story 1

- [ ] T008 [US1] Ajouter `enriched_entries: list[Source] = []` et `selected_enriched = None` dans `UnifiedSourcesApp.__init__` de `rekall/tui_main.py`
- [ ] T009 [US1] Ajouter le chargement `self.enriched_entries = list(self.db.get_enriched_sources(limit=500))` dans `_load_all_data()` de `rekall/tui_main.py`
- [ ] T010 [US1] Ajouter le TabPane `"Enrichies (0)"` avec DataTable `id="enriched-table"` dans `compose()` de `rekall/tui_main.py` - APRES tab-sources, AVANT tab-inbox
- [ ] T011 [US1] Implementer `_setup_enriched_table()` dans `rekall/tui_main.py` - colonnes: Domain(22), Type(12), Conf.(6), Status(10), Tags(25), Validated(12)
- [ ] T012 [US1] Implementer `_populate_enriched_table()` dans `rekall/tui_main.py` - formater rows avec indicateurs visuels (proposed=orange, validated=vert)
- [ ] T013 [US1] Appeler `_setup_enriched_table()` dans `on_mount()` de `rekall/tui_main.py`
- [ ] T014 [US1] Ajouter gestion `current_tab == "enriched"` dans `_update_detail_panel()` de `rekall/tui_main.py` - afficher ai_type, ai_tags, ai_summary, confidence

**Checkpoint**: US1 complete - l'onglet Enrichies affiche les sources avec leurs metadonnees IA

---

## Phase 4: User Story 2 - Voir et gerer les entrees en attente (Priority: P2)

**Goal**: L'utilisateur peut distinguer proposed/validated et effectuer des actions (validate/reject)

**Independent Test**: Selectionner une entree proposed > appuyer Enter > choisir "Validate" ou "Reject" > verifier changement de statut

### Implementation for User Story 2

- [ ] T015 [US2] Modifier `_populate_enriched_table()` pour trier par statut (proposed en premier) via FR-008 dans `rekall/tui_main.py`
- [ ] T016 [US2] Ajouter indicateurs visuels distincts: `[orange1]horloge proposed[/orange1]` vs `[green]coche validated[/green]` dans `rekall/tui_main.py`
- [ ] T017 [US2] Implementer `_get_enriched_actions()` dans `rekall/tui_main.py` - retourne liste actions (view, validate, reject si proposed)
- [ ] T018 [US2] Ajouter gestion `current_tab == "enriched"` dans `action_show_actions()` de `rekall/tui_main.py`
- [ ] T019 [US2] Implementer `_action_validate_enrichment()` dans `rekall/tui_main.py` - appelle db.validate_enrichment + refresh
- [ ] T020 [US2] Implementer `_action_reject_enrichment()` dans `rekall/tui_main.py` - appelle db.reject_enrichment + refresh (FR-009)
- [ ] T021 [US2] Implementer `_refresh_enriched()` dans `rekall/tui_main.py` - recharge donnees + repopule table + update stats
- [ ] T022 [US2] Ajouter dispatch actions "validate" et "reject" dans `on_list_view_selected()` de `rekall/tui_main.py`

**Checkpoint**: US2 complete - actions validate/reject fonctionnelles sur entrees proposed

---

## Phase 5: User Story 3 - Navigation fluide (Priority: P3)

**Goal**: L'utilisateur navigue entre les 4 onglets avec raccourcis clavier coherents

**Independent Test**: Depuis n'importe quel onglet > appuyer `n` > l'onglet Enrichies devient actif

### Implementation for User Story 3

- [ ] T023 [US3] Ajouter `Binding("n", "tab_enriched", "Enrichies", show=True)` dans BINDINGS de `rekall/tui_main.py`
- [ ] T024 [US3] Implementer `action_tab_enriched()` qui appelle `_switch_to_tab("enriched")` dans `rekall/tui_main.py`
- [ ] T025 [US3] Modifier `_switch_to_tab()` pour gerer `tab == "enriched"` - set entries, active tab, selected_enriched dans `rekall/tui_main.py`
- [ ] T026 [US3] Ajouter gestion `enriched` dans `_update_stats()` de `rekall/tui_main.py` - mettre a jour label tab "Enrichies (N)"
- [ ] T027 [US3] Ajouter gestion `enriched` dans `_apply_filter()` de `rekall/tui_main.py` - filtrer par domain, ai_type, tags
- [ ] T028 [US3] Ajouter gestion `enriched` dans `on_data_table_row_highlighted()` de `rekall/tui_main.py` - mettre a jour selected_enriched

**Checkpoint**: US3 complete - navigation clavier fonctionne entre les 4 onglets

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Tests, edge cases, documentation

- [ ] T029 [P] Implementer message empty state "Aucune source enrichie" dans `_populate_enriched_table()` de `rekall/tui_main.py`
- [ ] T030 [P] Creer fichier `tests/test_tui_enriched.py` avec structure de base
- [ ] T031 [P] Implementer `test_get_enriched_sources()` dans `tests/test_tui_enriched.py`
- [ ] T032 [P] Implementer `test_validate_enrichment()` dans `tests/test_tui_enriched.py`
- [ ] T033 [P] Implementer `test_reject_enrichment()` dans `tests/test_tui_enriched.py`
- [ ] T034 Executer `uv run pytest tests/test_tui_enriched.py -v` et corriger si echecs
- [ ] T035 Test manuel complet: lancer TUI > naviguer vers Enrichies > validate/reject > verifier
- [ ] T036 Executer `uv run pytest` pour verifier absence de regressions

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
     │
     ▼
Phase 2 (Foundational/DB) ◄─── BLOQUE toutes les phases suivantes
     │
     ├──────────────────────────────────────┐
     ▼                                      ▼
Phase 3 (US1)                          Phase 5 (US3) - peut demarrer en parallele
     │                                      │
     ▼                                      │
Phase 4 (US2) - depend de US1              │
     │                                      │
     └──────────────────────────────────────┘
                      │
                      ▼
              Phase 6 (Polish)
```

### User Story Dependencies

| Story | Depend de | Peut paralleliser avec |
|-------|-----------|------------------------|
| **US1** (P1) | Phase 2 (DB) | US3 |
| **US2** (P2) | US1 (table doit exister) | - |
| **US3** (P3) | Phase 2 (DB) | US1 |

### Within Each User Story

- DB methods avant TUI modifications
- compose() avant setup_table()
- setup_table() avant populate_table()
- Data avant UI

### Parallel Opportunities

**Phase 2 (DB)**: T005, T006, T007 peuvent s'executer en parallele apres T004

**Phase 6 (Tests)**: T030, T031, T032, T033 peuvent s'executer en parallele

---

## Parallel Example: Phase 2 (Database)

```bash
# Apres T004 (get_enriched_sources), lancer en parallele:
Task: "T005 - Implementer validate_enrichment dans rekall/db.py"
Task: "T006 - Implementer reject_enrichment dans rekall/db.py"
Task: "T007 - Implementer count_enriched_sources dans rekall/db.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: DB Layer (T004-T007) - **CRITIQUE**
3. Complete Phase 3: User Story 1 (T008-T014)
4. **STOP and VALIDATE**: Test US1 - onglet visible avec donnees
5. Deploy si MVP suffisant

### Incremental Delivery

1. Setup + DB → Foundation prete
2. Add US1 → Test: onglet Enrichies visible avec colonnes
3. Add US2 → Test: actions validate/reject fonctionnelles
4. Add US3 → Test: raccourci `n` et navigation complete
5. Add Polish → Tests automatises + edge cases

---

## Task Summary

| Phase | Taches | Parallelisables |
|-------|--------|-----------------|
| 1. Setup | 3 | 1 |
| 2. Foundational (DB) | 4 | 3 |
| 3. US1 - Consulter | 7 | 0 |
| 4. US2 - Actions | 8 | 0 |
| 5. US3 - Navigation | 6 | 0 |
| 6. Polish | 8 | 4 |
| **Total** | **36** | **8** |

---

## Notes

- [P] = fichiers differents, pas de dependances croisees
- [US1/2/3] = mapping vers user stories de spec.md
- Phase 2 (DB) BLOQUE tout le reste - priorite absolue
- Commit apres chaque tache ou groupe logique
- Stop a tout checkpoint pour valider independamment
