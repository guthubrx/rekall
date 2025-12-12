# Plan d'Implémentation - Feature 018: Auto-Capture Contexte Enrichi

**Date**: 2025-12-12
**Branche**: `018-auto-context-capture`
**Spec**: [spec.md](./spec.md)
**Status**: ✅ Prêt pour `/speckit.tasks`

---

## Contexte Technique

### Stack Existante
- **Langage**: Python 3.11+
- **CLI**: Typer 0.12+
- **MCP**: mcp-python (stdio-based)
- **DB**: SQLite + FTS5 + zlib compression
- **Tests**: pytest

### Fichiers Clés à Modifier
| Fichier | Lignes | Modifications |
|---------|--------|---------------|
| `rekall/mcp_server.py` | 1411 | Handler `_handle_add` + nouveaux params |
| `rekall/models.py` | 764 | Extension `StructuredContext` |
| `rekall/cli_main.py` | 4643 | Commande `rekall hooks install` |
| `rekall/context_extractor.py` | ~150 | Temporal markers auto |
| `rekall/data/hooks/` | - | Nouveau hook `rekall-reminder.sh` |

### Nouvelles Entités
- `TranscriptFormat` (Enum)
- `TranscriptMessage` (Dataclass)
- `CandidateExchanges` (Dataclass)
- `TemporalMarkers` (Dataclass)
- `HookConfig` (Dataclass)
- `TranscriptParser` (Interface + 4 implémentations)

---

## Constitution Check

| Article | Statut | Notes |
|---------|--------|-------|
| I. Langue Français | ✅ | Docs en français |
| III. Processus SpecKit | ✅ | Cycle complet |
| IV. Circuit Breaker | ✅ | À respecter pendant implémentation |
| VII. ADR | ✅ | research.md créé |
| XV. Test-Before-Next | ✅ | Tests unitaires pour chaque parser |
| XVI. Worktree | ✅ | Branche 018 isolée |

---

## Architecture Proposée

```
rekall/
├── transcript/                    # NOUVEAU module
│   ├── __init__.py
│   ├── parser_base.py            # Interface TranscriptParser
│   ├── parser_claude.py          # ClaudeTranscriptParser (JSONL)
│   ├── parser_cline.py           # ClineTranscriptParser (JSON)
│   ├── parser_continue.py        # ContinueTranscriptParser (JSON)
│   ├── parser_generic.py         # GenericJsonParser (fallback)
│   └── detector.py               # Auto-détection format
├── git_detector.py               # NOUVEAU: Auto-détection fichiers git
├── temporal.py                   # NOUVEAU: Marqueurs temporels
├── data/hooks/
│   ├── rekall-webfetch.sh        # Existant
│   └── rekall-reminder.sh        # NOUVEAU: Hook Stop
└── mcp_server.py                 # Modifié: nouveaux params + Mode 2
```

---

## Phases d'Implémentation

### Phase 1: Infrastructure (P0)
**Objectif**: Créer les entités et parsers de base

1. **T1.1**: Créer module `rekall/transcript/`
   - Interface `TranscriptParser`
   - Dataclasses `TranscriptMessage`, `CandidateExchanges`

2. **T1.2**: Implémenter `ClaudeTranscriptParser`
   - Parse JSONL Claude Code
   - Tests unitaires avec fixtures

3. **T1.3**: Implémenter `ClineTranscriptParser`
   - Parse JSON Cline
   - Tests unitaires

4. **T1.4**: Implémenter `ContinueTranscriptParser` + `GenericJsonParser`
   - Fallback générique
   - Tests unitaires

5. **T1.5**: Implémenter `detector.py`
   - Auto-détection format par extension/path
   - Factory pattern

### Phase 2: Mode 2 MCP (P0)
**Objectif**: Intégrer l'extraction transcript dans rekall_add

6. **T2.1**: Modifier schema MCP `rekall_add`
   - Nouveaux params: `auto_capture_conversation`, `_transcript_path`, etc.
   - Backward compatible

7. **T2.2**: Implémenter logique Mode 2 Step 1
   - Lecture transcript → CandidateExchanges
   - Session temporaire ULID

8. **T2.3**: Implémenter logique Mode 2 Step 2
   - `conversation_excerpt_indices` → filtrage
   - Finalisation entrée

9. **T2.4**: Tests intégration Mode 2
   - Mock transcripts
   - Flow complet 2 étapes

### Phase 3: Auto-Détection Git (P1)
**Objectif**: Enrichir automatiquement files_modified

10. **T3.1**: Créer `rekall/git_detector.py`
    - `get_modified_files(cwd, timeout=5)`
    - Combine staged + unstaged
    - Filtre binaires

11. **T3.2**: Intégrer dans `_handle_add`
    - Si `auto_detect_files=True` + `_cwd`
    - Fallback gracieux si git absent

12. **T3.3**: Tests git_detector
    - Repo mock avec modifications
    - Timeout + erreurs

### Phase 4: Marqueurs Temporels (P2)
**Objectif**: Auto-génération time_of_day/day_of_week

13. **T4.1**: Créer `rekall/temporal.py`
    - `TemporalMarkers.from_datetime()`
    - Mapping heures → time_of_day

14. **T4.2**: Intégrer dans `_handle_add`
    - Auto-génération si non fourni
    - Override manuel respecté

15. **T4.3**: Tests temporels
    - Différentes heures/jours
    - Override

### Phase 5: Hook Rappel Proactif (P1)
**Objectif**: Rappeler l'agent de sauvegarder après résolution

16. **T5.1**: Créer `rekall/data/hooks/rekall-reminder.sh`
    - Pattern matching résolution
    - Anti-spam (skip si "rekall" mentionné)
    - Output JSON pour Claude hooks

17. **T5.2**: Ajouter commande CLI `rekall hooks install`
    - `--cli claude|cline|continue|generic`
    - Installation idempotente
    - Backup existant

18. **T5.3**: Tests hook
    - Pattern matching
    - Installation/désinstallation

### Phase 6: Documentation & Finition
**Objectif**: Compléter docs et tests e2e

19. **T6.1**: Mettre à jour README/docs
    - Nouveaux params documentés
    - Exemples utilisation

20. **T6.2**: Tests e2e complets
    - Mode 1 + Mode 2
    - Multi-CLI simulation

---

## Risques et Mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Format transcript change | Moyen | Parsers versionnés, fallback générique |
| Git timeout sur gros repos | Faible | Timeout 5s, fallback gracieux |
| Hook spam | Moyen | Cooldown configurable, anti-spam |
| Session Mode 2 perdue | Faible | Session timeout + cleanup auto |

---

## Critères de Succès

- [ ] SC-001: 80%+ entrées avec `conversation_excerpt` non vide (Mode 1 ou 2)
- [ ] SC-002: 70%+ entrées avec `files_modified` non vide (quand git disponible)
- [ ] SC-003: 100% entrées avec temporal markers (auto ou manuel)
- [ ] SC-004: Hook rappel > 50% détection patterns résolution
- [ ] SC-005: Extraction transcript < 500ms pour 1000 échanges
- [ ] SC-006: 0 régression tests existants

---

## Estimation

| Phase | Complexité | LOC estimées |
|-------|------------|--------------|
| 1. Infrastructure | Moyenne | ~400 |
| 2. Mode 2 MCP | Haute | ~300 |
| 3. Git Detector | Faible | ~100 |
| 4. Temporal | Faible | ~80 |
| 5. Hook Rappel | Moyenne | ~150 |
| 6. Docs/Tests | Faible | ~200 |
| **Total** | | **~1230 LOC** |

---

## Prochaine Étape

```
/speckit.tasks
```

Générer les tâches détaillées à partir de ce plan.
