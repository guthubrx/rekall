# Tasks : Feature 007 - Migration & Maintenance

**Date** : 2025-12-10
**Statut** : Terminé

---

## Tableau de Suivi

| ID | Tâche | Phase | Statut | Fichiers |
|----|-------|-------|--------|----------|
| T001 | CLI `rekall version` | 1 | done | cli.py |
| T002 | CLI `rekall migrate` avec backup | 1 | done | cli.py, db.py |
| T003 | CLI `rekall migrate --dry-run` | 1 | done | cli.py |
| T004 | CLI `rekall changelog` | 1 | done | cli.py |
| T005 | Fichier CHANGELOG.md | 1 | done | CHANGELOG.md |
| T006 | Tests Phase 1 | 1 | done | test_cli.py |
| T007 | Overlay TUI migration | 2 | done | tui.py |
| T008 | Navigation < > Migration/Changelog | 2 | done | tui.py |
| T009 | Boutons Migrer/Plus tard | 2 | done | tui.py |
| T010 | Tests Phase 2 | 2 | done | test_tui.py |
| T011 | Compression zlib context_structured | 3 | done | db.py |
| T012 | Migration context_compressed → nouveau | 3 | done | db.py |
| T013 | Table context_keywords + intégration CLI | 3 | done | db.py, cli.py |
| T014 | Tests Phase 3 | 3 | done | test_db.py |
| T015 | CLI `migrate --enrich-context` | 4 | done | cli.py |
| T016 | Extraction keywords legacy | 4 | done | context_extractor.py |
| T017 | Génération situation/solution | 4 | done | context_extractor.py |
| T018 | Tests Phase 4 | 4 | done | test_context_extractor.py |
| T019 | Écran TUI Settings | 5 | done | tui.py |
| T020 | Option context_mode dans Settings | 5 | done | tui.py, config.py |
| T021 | Option max_context_size dans Settings | 5 | done | tui.py, config.py |
| T022 | Tests Phase 5 | 5 | done | test_tui.py |
| T023 | Changer défaut context_mode → required | 6 | done | config.py |
| T024 | Vérifier CLI refuse sans contexte | 6 | done | cli.py |
| T025 | Vérifier MCP refuse sans contexte | 6 | done | mcp_server.py |
| T026 | Tests Phase 6 | 6 | done | test_cli.py, test_mcp.py |

---

## Progression

```
Phase 1: ██████████ 6/6 (100%) ✓
Phase 2: ██████████ 4/4 (100%) ✓
Phase 3: ██████████ 4/4 (100%) ✓
Phase 4: ██████████ 4/4 (100%) ✓
Phase 5: ██████████ 4/4 (100%) ✓
Phase 6: ██████████ 4/4 (100%) ✓
─────────────────────────────
Total:   ██████████ 26/26 (100%) ✓
```

---

*Créé le 2025-12-10*
