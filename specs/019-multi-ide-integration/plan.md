# Implementation Plan: Multi-IDE Rekall Integration

**Branch**: `019-multi-ide-integration` | **Date**: 2025-12-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/019-multi-ide-integration/spec.md`

## Summary

Restructurer l'écran `rekall config` pour offrir une interface unifiée d'intégration IDE avec bundles complets (instructions + MCP + hooks) par IDE, section SPECKIT séparée avec recommandation dynamique Article 99 (MICRO/COURT/EXTENSIF), et gestion du scope Global/Local. Support de 7 IDEs : Claude Code, Cursor, Copilot, Windsurf, Cline, Zed, Continue.dev.

## Technical Context

**Language/Version**: Python 3.10+ (compatible 3.10, 3.11, 3.12, 3.13)
**Primary Dependencies**: Textual 0.89+, Typer, Rich, Pydantic 2.0+, MCP 1.0+
**Storage**: Fichiers JSON/MD pour configurations IDE, pas de DB (lecture/écriture fichiers système)
**Testing**: pytest 8.0+, ruff pour linting
**Target Platform**: macOS, Linux (cross-platform CLI)
**Project Type**: Single CLI application avec TUI Textual
**Performance Goals**: Installation < 5 secondes, détection IDE instantanée
**Constraints**: Pas de dépendances additionnelles, compatibilité avec IDEs existants
**Scale/Scope**: 7 IDEs supportés, ~15 fichiers de configuration possibles

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Conformité | Notes |
|---------|------------|-------|
| I. Langue Française | ✅ PASS | Documentation et UI en français |
| II. Rôle Agent Co-Pilote | ✅ PASS | Feature n'impacte pas le comportement agent |
| III. Processus SpecKit | ✅ PASS | Utilisation /speckit.specify → /speckit.plan → /speckit.tasks |
| IV. Règle du Disjoncteur | ✅ PASS | Feature TUI, debugging standard |
| V. Gestion du Périmètre | ✅ PASS | Scope défini : écran config, pas d'autres features |
| VII. Mémoire ADR | ⚠️ ACTION | Créer ADR pour choix architecture bundles |
| IX. Recherche Préalable | ✅ PASS | Brainstorming fait, research.md à générer |
| XV. Test-Before-Next | ✅ PASS | Tests TUI via pytest, ruff lint |
| XVI. Workflow Worktree | ✅ PASS | Branche 019-multi-ide-integration créée |

**Gate Status**: ✅ PASS - Aucune violation bloquante

## Project Structure

### Documentation (this feature)

```text
specs/019-multi-ide-integration/
├── spec.md              # Specification validée
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
rekall/
├── integrations/
│   └── __init__.py      # MODIFIER: Ajouter détection IDE, bundles, Article 99 versions
├── tui_main.py          # MODIFIER: Nouvel écran config avec 2 sections
├── ui/
│   └── screens/
│       └── config.py    # CRÉER: Extraction logique écran config
└── data/
    └── instructions/    # CRÉER: Templates instructions par IDE
        ├── claude/
        ├── cursor/
        ├── copilot/
        ├── windsurf/
        ├── cline/
        ├── zed/
        └── continue/

tests/
├── unit/
│   ├── test_ide_detection.py     # CRÉER
│   ├── test_integration_bundles.py # CRÉER
│   └── test_article99_versions.py  # CRÉER
└── integration/
    └── test_config_screen.py     # CRÉER
```

**Structure Decision**: Single project structure. Modification principalement dans `rekall/integrations/__init__.py` et `rekall/tui_main.py`. Pas de nouveau module majeur, extension du système existant.

## Complexity Tracking

> Aucune violation de constitution nécessitant justification.

| Aspect | Décision | Justification |
|--------|----------|---------------|
| Bundles IDE | 1 fonction install par IDE | Chaque IDE a des spécificités (paths, formats) |
| Article 99 | 3 versions (MICRO/COURT/EXTENSIF) | Optimisation tokens selon contexte |
| Détection | Ordre de priorité fixe | Claude > Cursor > ... (usage typique) |

