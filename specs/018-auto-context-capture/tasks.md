# Tâches d'Implémentation - Feature 018: Auto-Capture Contexte Enrichi

**Date**: 2025-12-12
**Branche**: `018-auto-context-capture`
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)

---

## Vue d'Ensemble

| Phase | Description | Tâches | Priorité |
|-------|-------------|--------|----------|
| 1 | Setup & Infrastructure | 5 | P0 |
| 2 | Fondations (Parsers) | 5 | P0 |
| 3 | US1 - Auto-Capture Conversation | 6 | P0 |
| 4 | US2 - Auto-Détection Git | 4 | P1 |
| 5 | US3 - Temporal Markers | 3 | P2 |
| 6 | US4 - Hook Rappel Proactif | 4 | P1 |
| 7 | US5 - Installation Multi-CLI | 3 | P3 |
| 8 | Polish & Documentation | 3 | - |
| **Total** | | **33** | |

---

## Phase 1: Setup & Infrastructure

**Objectif**: Créer la structure de base du module transcript

- [x] T001 Créer le module `rekall/transcript/__init__.py` avec exports publics
- [x] T002 [P] Créer les dataclasses `TranscriptFormat`, `TranscriptMessage` dans `rekall/transcript/models.py`
- [x] T003 [P] Créer la dataclass `CandidateExchanges` dans `rekall/transcript/models.py`
- [x] T004 [P] Créer la dataclass `TemporalMarkers` dans `rekall/temporal.py`
- [x] T005 [P] Créer la dataclass `HookConfig` dans `rekall/hooks/models.py`

---

## Phase 2: Fondations - Parsers Transcript

**Objectif**: Implémenter l'interface et les parsers de base (bloquant pour US1)

- [x] T006 Créer l'interface abstraite `TranscriptParser` dans `rekall/transcript/parser_base.py`
- [x] T007 [P] Implémenter `ClaudeTranscriptParser` (JSONL) dans `rekall/transcript/parser_claude.py`
- [x] T008 [P] Implémenter `ClineTranscriptParser` (JSON) dans `rekall/transcript/parser_cline.py`
- [x] T009 [P] Implémenter `ContinueTranscriptParser` et `GenericJsonParser` dans `rekall/transcript/parser_continue.py` et `rekall/transcript/parser_generic.py`
- [x] T010 Créer le détecteur de format avec factory dans `rekall/transcript/detector.py`

---

## Phase 3: US1 - Auto-Capture Conversation (P0)

**User Story**: L'agent IA sauvegarde automatiquement le contexte de conversation pertinent lors de la création d'un souvenir.

**Test Indépendant**: Créer un souvenir via MCP en Mode 1 (agent fournit `conversation_excerpt`) et en Mode 2 (système propose depuis transcript).

**Critères d'Acceptation**:
- Mode 1: `conversation_excerpt` fourni directement → stocké sans traitement
- Mode 2 Step 1: `auto_capture_conversation: true` → retourne 20 candidats
- Mode 2 Step 2: `conversation_excerpt_indices` → stocke les échanges sélectionnés
- Erreur explicite si transcript inaccessible ou format non supporté

### Tâches

- [x] T011 [US1] Étendre le schema MCP `rekall_add` avec nouveaux params (`auto_capture_conversation`, `_transcript_path`, `_transcript_format`, `conversation_excerpt_indices`, `_session_id`) dans `rekall/mcp_server.py`
- [x] T012 [US1] Implémenter la logique Mode 2 Step 1 (lecture transcript → CandidateExchanges) dans `rekall/mcp_server.py:_handle_add()`
- [x] T013 [US1] Créer le gestionnaire de sessions temporaires Mode 2 dans `rekall/transcript/session_manager.py`
- [x] T014 [US1] Implémenter la logique Mode 2 Step 2 (filtrage par indices → finalisation) dans `rekall/mcp_server.py:_handle_add()`
- [x] T015 [US1] Ajouter les tests unitaires parsers dans `tests/test_transcript_parsers.py`
- [x] T016 [US1] Ajouter les tests intégration Mode 2 complet dans `tests/test_mcp_auto_capture.py`

---

## Phase 4: US2 - Auto-Détection Fichiers Modifiés (P1)

**User Story**: Le système détecte automatiquement les fichiers modifiés via git lors de la création d'un souvenir.

**Test Indépendant**: Créer un souvenir avec `auto_detect_files: true` dans un repo git avec des fichiers modifiés et vérifier que `files_modified` les liste.

**Critères d'Acceptation**:
- Combine staged + unstaged en liste dédupliquée
- Fallback gracieux si pas un repo git
- Timeout 5s pour éviter blocage

### Tâches

- [x] T017 [US2] Créer le module `rekall/git_detector.py` avec `get_modified_files(cwd, timeout=5)`
- [x] T018 [US2] Intégrer l'auto-détection git dans `rekall/mcp_server.py:_handle_add()` (si `auto_detect_files=True`)
- [x] T019 [US2] Ajouter le filtrage des fichiers binaires dans `rekall/git_detector.py`
- [x] T020 [US2] Ajouter les tests git_detector dans `tests/test_git_detector.py`

---

## Phase 5: US3 - Temporal Markers Auto-Générés (P2)

**User Story**: Le système ajoute automatiquement des marqueurs temporels pour situer le souvenir dans le temps.

**Test Indépendant**: Créer un souvenir à 14h30 un mercredi et vérifier que `time_of_day: afternoon` et `day_of_week: wednesday` sont auto-générés.

**Critères d'Acceptation**:
- Auto-génération si non fournis
- Override manuel respecté
- Mapping heures correct (morning/afternoon/evening/night)

### Tâches

- [x] T021 [US3] Implémenter `TemporalMarkers.from_datetime()` dans `rekall/temporal.py`
- [x] T022 [US3] Intégrer les temporal markers dans `rekall/mcp_server.py:_handle_add()` (auto-génération + override)
- [x] T023 [US3] Ajouter les tests temporal markers dans `tests/test_temporal.py`

---

## Phase 6: US4 - Hook de Rappel Proactif (P1)

**User Story**: Le système rappelle à l'agent de sauvegarder dans Rekall quand il détecte qu'un problème vient d'être résolu.

**Test Indépendant**: Configurer le hook Stop, résoudre un bug (message contenant "fixed"), et vérifier que le rappel Rekall est injecté.

**Critères d'Acceptation**:
- Détection patterns résolution (fixed, résolu, corrigé, ✅)
- Anti-spam (skip si "rekall" déjà mentionné)
- Output JSON compatible Claude hooks

### Tâches

- [x] T024 [US4] Créer le script `rekall/data/hooks/rekall-reminder.sh` avec pattern matching
- [x] T025 [US4] Créer le fichier de configuration patterns dans `rekall/data/hooks/resolution-patterns.txt`
- [x] T026 [US4] Implémenter la logique anti-spam (skip si rekall mentionné) dans `rekall/data/hooks/rekall-reminder.sh`
- [x] T027 [US4] Ajouter les tests du hook dans `tests/test_reminder_hook.py`

---

## Phase 7: US5 - Installation Multi-CLI (P3)

**User Story**: L'utilisateur peut installer les hooks et configurations spécifiques à son CLI via une commande dédiée.

**Test Indépendant**: Exécuter `rekall hooks install --cli claude` et vérifier que le hook est installé dans `~/.claude/hooks/`.

**Critères d'Acceptation**:
- Support `--cli claude|cline|continue|generic`
- Installation idempotente
- Backup de l'existant avant écrasement

### Tâches

- [x] T028 [US5] Créer le groupe de commandes `rekall hooks` dans `rekall/cli_main.py`
- [x] T029 [US5] Implémenter `rekall hooks install --cli <cli>` dans `rekall/cli_main.py`
- [x] T030 [US5] Ajouter les tests CLI hooks dans `tests/test_cli_hooks.py`

---

## Phase 8: Polish & Documentation

**Objectif**: Finaliser la documentation et les tests e2e

- [x] T031 Mettre à jour la docstring du tool `rekall_add` dans `rekall/mcp_server.py` avec les nouveaux params
- [ ] T032 Ajouter les exemples d'utilisation dans `rekall/README.md` ou `docs/`
- [ ] T033 Créer les tests e2e multi-mode dans `tests/test_e2e_auto_capture.py`

---

## Dépendances

```
Phase 1 (Setup)
    │
    ▼
Phase 2 (Parsers) ──────────────────────────────────────┐
    │                                                   │
    ▼                                                   │
Phase 3 (US1 - Capture) ◄───────────────────────────────┤
    │                                                   │
    ├───────────────────┐                               │
    ▼                   ▼                               │
Phase 4 (US2 - Git)   Phase 5 (US3 - Temporal)          │
    │                   │                               │
    └─────────┬─────────┘                               │
              │                                         │
              ▼                                         │
        Phase 6 (US4 - Hook) ◄──────────────────────────┘
              │
              ▼
        Phase 7 (US5 - Install CLI)
              │
              ▼
        Phase 8 (Polish)
```

**Légende**:
- US1 dépend de Phase 2 (parsers nécessaires)
- US2 et US3 peuvent être parallélisés après US1
- US4 peut démarrer après Phase 2 (utilise les parsers pour tests)
- US5 dépend de US4 (install le hook créé)

---

## Opportunités de Parallélisation

### Intra-Phase (même développeur)

| Phase | Tâches Parallélisables |
|-------|------------------------|
| 1 | T002, T003, T004, T005 (dataclasses indépendantes) |
| 2 | T007, T008, T009 (parsers indépendants après T006) |

### Inter-Phase (plusieurs développeurs/agents)

| Agent 1 | Agent 2 | Condition |
|---------|---------|-----------|
| Phase 3 (US1) | Phase 4 (US2) | Après Phase 2 terminée |
| Phase 4 (US2) | Phase 5 (US3) | En parallèle |
| Phase 6 (US4) | Phase 5 (US3) | Après Phase 2 terminée |

---

## Stratégie d'Implémentation

### MVP (Minimum Viable Product)

**Scope MVP = Phase 1 + Phase 2 + Phase 3 (US1)**

Livrable MVP:
- Mode 1 fonctionnel (agent fournit directement)
- Mode 2 fonctionnel (système extrait, agent filtre)
- 4 parsers transcript (Claude, Cline, Continue, Generic)
- Tests unitaires et intégration

**Après MVP**: US2, US3, US4, US5 en incréments indépendants

### Ordre d'Exécution Recommandé

1. **Sprint 1**: Phases 1-3 (MVP complet)
2. **Sprint 2**: Phases 4-5 (enrichissement auto)
3. **Sprint 3**: Phases 6-7 (hooks proactifs)
4. **Sprint 4**: Phase 8 (polish)

---

## Validation Format

✅ Toutes les tâches suivent le format: `- [ ] TXXX [P?] [US?] Description avec chemin fichier`
✅ IDs séquentiels T001-T033
✅ [P] marqué pour tâches parallélisables
✅ [USx] marqué pour phases User Story (3-7)
✅ Chemins de fichiers explicites pour chaque tâche
