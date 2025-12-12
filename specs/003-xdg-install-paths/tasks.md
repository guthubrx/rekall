# Tasks: XDG-Compliant Installation Paths

**Feature**: 003-xdg-install-paths
**Generated**: 2024-12-07
**Source**: [plan.md](./plan.md), [spec.md](./spec.md), [data-model.md](./data-model.md)

## Summary

| Métrique | Valeur |
|----------|--------|
| Total tâches | 24 |
| Phase 1 (Setup) | 3 tâches |
| Phase 2 (Foundational) | 5 tâches |
| Phase 3 (US1 - XDG Default) | 5 tâches |
| Phase 4 (US2 - Local Project) | 4 tâches |
| Phase 5 (US3 - Custom Path) | 3 tâches |
| Phase 6 (US4 - Migration) | 3 tâches |
| Phase 7 (Polish) | 1 tâche |
| Parallélisables | 8 tâches |

---

## Phase 1: Setup

**Objectif**: Initialiser les dépendances et la structure du projet.

- [x] T001 Ajouter `platformdirs>=4.0` dans `pyproject.toml` dependencies
- [x] T002 Ajouter `tomli>=2.0` dans `pyproject.toml` dependencies (fallback Python <3.11)
- [x] T003 Créer le fichier `rekall/paths.py` avec imports et docstring module

---

## Phase 2: Foundational

**Objectif**: Implémenter les structures de données et le resolver de base (bloquant pour toutes les user stories).

- [x] T004 Implémenter `PathSource` enum dans `rekall/paths.py`
- [x] T005 Implémenter `ResolvedPaths` dataclass dans `rekall/paths.py`
- [x] T006 Implémenter `PathResolver._from_default()` méthode utilisant platformdirs dans `rekall/paths.py`
- [x] T007 [P] Créer `tests/test_paths.py` avec tests pour PathSource et ResolvedPaths
- [x] T008 Implémenter `PathResolver.resolve()` squelette avec chaîne de priorité dans `rekall/paths.py`

---

## Phase 3: User Story 1 - Default Installation Experience (P1)

**Objectif**: XDG par défaut sur Linux/macOS, %APPDATA% sur Windows - "ça marche tout seul".

**Test indépendant**: `rekall` sans config → fichiers créés dans chemins XDG.

- [x] T009 [US1] Implémenter `PathResolver._from_xdg()` pour variables $XDG_* dans `rekall/paths.py`
- [x] T010 [P] [US1] Ajouter tests `test_paths.py::test_xdg_vars_respected` et `test_default_paths_linux_macos`
- [x] T011 [US1] Mettre à jour `rekall/config.py` pour utiliser `PathResolver.resolve()` au lieu du chemin hardcodé
- [x] T012 [US1] Implémenter `rekall config --show` dans `rekall/cli.py` (FR-007)
- [x] T013 [P] [US1] Ajouter test `test_cli.py::test_config_show_command` (couvert par tests existants + validation manuelle)

---

## Phase 4: User Story 2 - Local Project Installation (P2)

**Objectif**: `.rekall/` dans le projet pour travail en équipe.

**Test indépendant**: `rekall init --local` → crée `.rekall/` dans cwd.

- [x] T014 [US2] Implémenter `PathResolver._from_local()` détection `.rekall/` dans cwd dans `rekall/paths.py`
- [x] T015 [US2] Implémenter `rekall init --local` dans `rekall/cli.py` (FR-003)
- [x] T016 [P] [US2] Ajouter tests `test_paths.py::test_local_project_detection` et `test_local_priority_over_global`
- [x] T017 [US2] Générer `.gitignore` dans `.rekall/` lors de `init --local` dans `rekall/cli.py`

---

## Phase 5: User Story 3 - Custom Path (P3)

**Objectif**: REKALL_HOME et config.toml pour chemins personnalisés.

**Test indépendant**: `REKALL_HOME=/custom rekall` → utilise `/custom/`.

- [x] T018 [US3] Implémenter `PathResolver._from_env()` pour REKALL_HOME/REKALL_DB_PATH dans `rekall/paths.py`
- [x] T019 [US3] Implémenter `PathResolver._from_config()` pour data_dir dans config.toml dans `rekall/paths.py`
- [x] T020 [P] [US3] Ajouter tests `test_paths.py::test_env_vars_priority` et `test_config_data_dir`

---

## Phase 6: User Story 4 - Migration (P3)

**Objectif**: Migrer `~/.rekall/` vers nouveaux chemins XDG.

**Test indépendant**: Avec `~/.rekall/` existant → prompt migration au démarrage.

- [x] T021 [US4] Implémenter `MigrationInfo` dataclass dans `rekall/paths.py`
- [x] T022 [US4] Implémenter `check_legacy_migration()` détection et prompt dans `rekall/paths.py`
- [x] T023 [US4] Implémenter `perform_migration()` copie avec marker dans `rekall/paths.py`

---

## Phase 7: Polish & Cross-Cutting

**Objectif**: Options CLI globales et finalisation.

- [x] T024 Ajouter options `--global` et `--legacy` aux commandes CLI dans `rekall/cli.py` (FR-009)

---

## Dependencies

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Foundational) ──────────────────┐
    │                                     │
    ▼                                     │
Phase 3 (US1 - XDG Default) ◄────────────┘
    │
    ├──────────────────┬──────────────────┐
    ▼                  ▼                  ▼
Phase 4 (US2)    Phase 5 (US3)    Phase 6 (US4)
    │                  │                  │
    └──────────────────┴──────────────────┘
                       │
                       ▼
              Phase 7 (Polish)
```

**Notes**:
- US1 doit être complète avant US2/US3/US4 (PathResolver de base requis)
- US2, US3, US4 sont parallélisables entre elles
- Phase 7 dépend de toutes les user stories

---

## Parallel Execution Examples

### Exemple 1: Setup (Phase 1)
```bash
# T001, T002, T003 peuvent être faites en parallèle (fichiers différents)
```

### Exemple 2: Foundational Tests (Phase 2)
```bash
# T007 peut être fait en parallèle avec T004-T006 (TDD)
```

### Exemple 3: User Stories parallèles (Phases 4-6)
```bash
# Après Phase 3 complète:
# - Agent A: T014-T017 (US2 - Local)
# - Agent B: T018-T020 (US3 - Custom)
# - Agent C: T021-T023 (US4 - Migration)
```

---

## Implementation Strategy

### MVP (Minimum Viable Product)
**Scope**: Phase 1 + Phase 2 + Phase 3 (User Story 1)
**Résultat**: Rekall fonctionne avec chemins XDG par défaut + `rekall config --show`

### Increment 2
**Scope**: Phase 4 (User Story 2)
**Résultat**: Support projet local `.rekall/`

### Increment 3
**Scope**: Phase 5 + Phase 6 (User Stories 3 & 4)
**Résultat**: Chemins personnalisés + migration legacy

### Increment 4
**Scope**: Phase 7 (Polish)
**Résultat**: Options `--global` et `--legacy`

---

## File Paths Summary

| Fichier | Action | Tâches |
|---------|--------|--------|
| `pyproject.toml` | UPDATE | T001, T002 |
| `rekall/paths.py` | CREATE | T003-T006, T008-T009, T014, T018-T019, T021-T023 |
| `rekall/config.py` | UPDATE | T011 |
| `rekall/cli.py` | UPDATE | T012, T015, T017, T024 |
| `tests/test_paths.py` | CREATE | T007, T010, T016, T020 |
| `tests/test_cli.py` | UPDATE | T013 |

---

## Validation Checklist

- [x] Toutes les tâches ont un ID (T001-T024)
- [x] Toutes les tâches ont un chemin de fichier
- [x] Les tâches parallélisables sont marquées [P]
- [x] Les tâches user story sont marquées [US1-4]
- [x] Chaque user story a un test indépendant
- [x] Les dépendances sont documentées
- [x] La stratégie MVP est définie
