# Implementation Tasks: Multi-IDE Rekall Integration

**Feature**: 019-multi-ide-integration
**Branch**: `019-multi-ide-integration`
**Generated**: 2025-12-13
**Total Tasks**: 28

---

## Existing Code (Already Implemented)

Le module `rekall/integrations/__init__.py` contient déjà :
- ✅ 12 IDEs enregistrés via `@register` (claude, cursor, copilot, windsurf, cline, zed, continue, aider, gemini, cursor-agent, qwen, opencode)
- ✅ `REKALL_SKILL_MAIN`, `REKALL_SKILL_CONSULTATION`, etc. (progressive disclosure)
- ✅ `ARTICLE_99_SHORT` (~350 tokens), `ARTICLE_99_EXTENSIVE` (~1000 tokens)
- ✅ `install()`, `uninstall_ide()`, `get_ide_status()`, `supports_global()`
- ✅ `install_speckit()`, `get_speckit_status()`, `uninstall_speckit()`
- ✅ Hooks Claude (rekall-webfetch.sh, rekall-reminder.sh)

**Manquant** pour cette feature :
- `ARTICLE_99_MICRO` (~50 tokens)
- Dataclasses formelles (`IDE`, `Scope`, `DetectedIDE`, etc.)
- `detect_ide()` avec priorité
- Nouvel écran TUI `ConfigApp` avec 2 sections (INTÉGRATIONS + SPECKIT)
- Colonnes Global/Local dans l'interface
- Recommandation dynamique Article 99

---

## Summary

| Phase | Description | Task Count |
|-------|-------------|------------|
| Phase 1 | Setup (fichiers tests) | 2 |
| Phase 2 | Foundational (dataclasses + detect_ide) | 5 |
| Phase 3 | US1 - Interface de configuration simplifiée | 6 |
| Phase 4 | US2 - Détection IDE affichée | 3 |
| Phase 5 | US3 - Bundles install/uninstall | 3 |
| Phase 6 | US4 - Article 99 recommandation dynamique | 4 |
| Phase 7 | US5 - Patches Speckit adaptatifs | 2 |
| Phase 8 | US6 - Multi-IDE multi-scope | 2 |
| Phase 9 | Polish & Integration | 1 |

---

## Phase 1: Setup

> Création des fichiers de test

- [ ] T001 [P] Créer les fichiers de test `tests/unit/test_ide_detection.py`, `tests/unit/test_article99_versions.py`
- [ ] T002 [P] Créer le fichier `tests/integration/test_config_screen.py` avec structure de base

---

## Phase 2: Foundational (Data Models + detect_ide)

> Prérequis bloquants pour toutes les User Stories

- [ ] T003 Définir les dataclasses `IDE`, `Scope`, `DetectedIDE` dans `rekall/integrations/__init__.py`
- [ ] T004 Définir les dataclasses `Article99Version`, `Article99Config` dans `rekall/integrations/__init__.py`
- [ ] T005 Créer la constante `ARTICLE_99_MICRO` (~50 tokens) dans `rekall/integrations/__init__.py`
- [ ] T006 Créer la constante `SUPPORTED_IDES: list[IDE]` basée sur `INTEGRATIONS` existant dans `rekall/integrations/__init__.py`
- [ ] T007 Implémenter `detect_ide(base_path) -> DetectedIDE` avec priorité (Claude > Cursor > ...) dans `rekall/integrations/__init__.py`

---

## Phase 3: US1 - Interface TUI de configuration simplifiée (P1)

> **Goal**: L'écran `rekall config` affiche 2 sections (INTÉGRATIONS + SPECKIT) avec tous les IDEs comme bundles
>
> **Independent Test**: Lancer `rekall config` et vérifier que les 2 sections sont visibles avec les IDEs listés

- [ ] T008 [US1] Créer la classe `ConfigApp(App)` dans `rekall/tui_main.py` avec layout 2 sections (INTÉGRATIONS + SPECKIT)
- [ ] T009 [US1] Implémenter la section INTÉGRATIONS avec liste des IDEs et colonnes Global/Local
- [ ] T010 [US1] Implémenter la section SPECKIT conditionnelle (visible si `~/.speckit/` existe)
- [ ] T011 [US1] Ajouter widget `Article99Selector` avec RadioButtons (MICRO/COURT/EXTENSIF)
- [ ] T012 [US1] Ajouter les bindings clavier (↑↓ navigate, Space toggle, i install, r remove, Tab switch, Esc quit)
- [ ] T013 [US1] Migrer l'appel `rekall config` pour utiliser `ConfigApp` au lieu de `MCPConfigApp` dans `rekall/cli_main.py`

---

## Phase 4: US2 - Détection IDE affichée (P1)

> **Goal**: Le système détecte l'IDE automatiquement (local puis global) et l'affiche
>
> **Independent Test**: Créer un dossier `.claude/` et vérifier que `rekall config` affiche "IDE détecté: Claude Code"

- [ ] T014 [US2] Ajouter l'affichage "IDE détecté: {nom}" en haut de l'écran dans `ConfigApp`
- [ ] T015 [US2] Implémenter le highlight de la ligne IDE détectée (marqueur `►`)
- [ ] T016 [US2] Ajouter tests unitaires pour `detect_ide()` dans `tests/unit/test_ide_detection.py`

---

## Phase 5: US3 - Bundles install/uninstall via TUI (P1)

> **Goal**: Toggle Global/Local installe/désinstalle le bundle complet pour chaque IDE
>
> **Independent Test**: Cocher Claude Global, vérifier `~/.claude/commands/rekall.md` créé

- [ ] T017 [US3] Connecter le toggle Global à `install(ide, base_path, global_install=True)` existant
- [ ] T018 [US3] Connecter le toggle Local à `install(ide, base_path, global_install=False)` existant
- [ ] T019 [US3] Afficher notification après install/uninstall ("✓ Claude Code installé (global)")

---

## Phase 6: US4 - Article 99 recommandation dynamique (P2)

> **Goal**: La section SPECKIT affiche une recommandation Article 99 basée sur les intégrations installées
>
> **Independent Test**: Installer skill Claude et vérifier que "★ recommandé: Micro" s'affiche

- [ ] T020 [US4] Implémenter `get_article99_recommendation(base_path) -> Article99Config` dans `rekall/integrations/__init__.py`
- [ ] T021 [US4] Afficher la recommandation dans `Article99Selector` ("★ recommandé: Micro (skill Claude installée)")
- [ ] T022 [US4] Implémenter `install_article99(version)` pour les 3 versions (MICRO/COURT/EXTENSIF)
- [ ] T023 [US4] Ajouter tests unitaires dans `tests/unit/test_article99_versions.py`

---

## Phase 7: US5 - Patches Speckit adaptatifs MCP/CLI (P2)

> **Goal**: Les patches /speckit.* utilisent MCP ou CLI selon l'IDE installé
>
> **Independent Test**: Installer MCP et vérifier que le patch contient `rekall_search`

- [ ] T024 [US5] Modifier `_make_rekall_section()` pour accepter `use_mcp: bool` et générer version MCP ou CLI
- [ ] T025 [US5] Ajouter liste des patches dans section SPECKIT avec toggle install/uninstall

---

## Phase 8: US6 - Multi-IDE multi-scope (P3)

> **Goal**: Installer plusieurs IDEs avec différents scopes simultanément
>
> **Independent Test**: Installer Claude (global) + Cursor (local) et vérifier les deux cases cochées

- [ ] T026 [US6] Permettre plusieurs IDEs cochés simultanément dans `ConfigApp`
- [ ] T027 [US6] Gérer désinstallation partielle (un scope sans l'autre)

---

## Phase 9: Polish & Integration

> Tests d'intégration et finalisation

- [ ] T028 Ajouter tests d'intégration complets dans `tests/integration/test_config_screen.py`

---

## Dependencies

```
Phase 1 (Setup - tests)
    │
    ▼
Phase 2 (Foundational - dataclasses + detect_ide)
    │
    ├───► Phase 3 (US1: Interface TUI) ──┐
    │                                    │
    └───► Phase 4 (US2: Détection) ──────┼───► Phase 5 (US3: Bundles)
                                         │              │
                                         │              ▼
                                         └───► Phase 6 (US4: Article 99)
                                                        │
                                                        ▼
                                               Phase 7 (US5: Patches)
                                                        │
                                                        ▼
                                               Phase 8 (US6: Multi-IDE)
                                                        │
                                                        ▼
                                               Phase 9 (Polish)
```

---

## Parallel Execution Opportunities

### Phase 1 (2 tasks)
```
T001, T002 → parallel (independent test files)
```

### Phase 2 (5 tasks)
```
T003, T004 → sequential (dependent dataclasses)
T005, T006 → parallel (constants)
T007 → sequential (uses dataclasses)
```

### Phase 3 (6 tasks)
```
T008 → sequential (base ConfigApp)
T009, T010, T011 → sequential (sections)
T012 → sequential (bindings)
T013 → sequential (migration)
```

---

## Implementation Strategy

### MVP Scope (Recommended First Iteration)
- **Phase 1**: Setup (2 tâches)
- **Phase 2**: Foundational (5 tâches)
- **Phase 3**: US1 - Interface TUI (6 tâches)
- **Phase 4**: US2 - Détection IDE (3 tâches)

**Deliverable MVP** (16 tâches): `rekall config` affiche la nouvelle interface avec 2 sections et détection IDE.

### Second Iteration
- **Phase 5**: US3 - Bundles via TUI (3 tâches)
- **Phase 6**: US4 - Article 99 recommandation (4 tâches)

**Deliverable** (7 tâches): Installation/désinstallation fonctionnelle avec recommandation Speckit.

### Third Iteration
- **Phase 7**: US5 - Patches Speckit (2 tâches)
- **Phase 8**: US6 - Multi-IDE (2 tâches)
- **Phase 9**: Polish (1 tâche)

**Deliverable** (5 tâches): Feature complète avec tous les edge cases.

---

## Files Modified/Created

### New Files
- `tests/unit/test_ide_detection.py`
- `tests/unit/test_article99_versions.py`
- `tests/integration/test_config_screen.py`

### Modified Files
- `rekall/integrations/__init__.py` (dataclasses `IDE`, `Scope`, `DetectedIDE`, `Article99Version`, + `detect_ide()`, `get_article99_recommendation()`, `ARTICLE_99_MICRO`)
- `rekall/tui_main.py` (nouveau `ConfigApp` remplaçant `MCPConfigApp`)
- `rekall/cli_main.py` (migration appel config)
