# Implementation Plan: Système de Mémoire Cognitive

**Branch**: `004-cognitive-memory` | **Date**: 2025-12-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-cognitive-memory/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Évolution de Rekall vers un système de mémoire cognitive inspiré des mécanismes de la mémoire humaine. Inclut :
- **Liens entre entrées** (knowledge graph) avec 4 types de relations
- **Distinction épisodique/sémantique** pour catégoriser les connaissances
- **Tracking d'accès et consolidation** pour identifier les connaissances fragiles
- **Répétition espacée** pour révision optimale
- **Skill Claude Code** pour consultation automatique avant action et capture après résolution

Basé sur une recherche approfondie (30+ sources académiques) documentée dans `docs/research-memory-mechanisms.md`.

## Technical Context

**Language/Version**: Python 3.9+ (support 3.9-3.13)
**Primary Dependencies**: Typer 0.12+, Rich 13+, Textual 0.89+, prompt_toolkit 3+, platformdirs 4+
**Storage**: SQLite 3 + FTS5 (Full-Text Search)
**Testing**: pytest 8+ avec pytest-cov, ruff pour linting
**Target Platform**: Cross-platform (macOS, Linux, Windows)
**Project Type**: Single project (CLI + TUI)
**Performance Goals**: <100ms pour recherche FTS, <10s pour opérations link (SC-001)
**Constraints**: Base locale (fichier SQLite), pas de serveur, offline-capable
**Scale/Scope**: ~1000 entrées typique, single-user

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Règle | Statut | Notes |
|---------|-------|--------|-------|
| I | Documentation en français | ✅ PASS | Spec et plan en français |
| III | Cycle SpecKit obligatoire | ✅ PASS | `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` |
| VII | ADR pour décisions structurantes | ✅ PASS | À créer lors de l'implémentation |
| IX | Recherche préalable | ✅ PASS | `docs/research-memory-mechanisms.md` (30+ sources) |
| XV | Test-Before-Next | ⏳ N/A | À appliquer lors de l'implémentation |
| XVI | Worktree obligatoire | ⏳ N/A | Branche créée, worktree à utiliser |

**Résultat** : GATE PASS - Aucune violation

## Project Structure

### Documentation (this feature)

```text
specs/004-cognitive-memory/
├── plan.md              # Ce fichier
├── spec.md              # Spécification validée
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI commands)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
rekall/
├── __init__.py
├── __main__.py
├── cli.py               # CLI Typer (à étendre: link, related, stale, review)
├── db.py                # Database SQLite+FTS5 (à étendre: tables links, tracking)
├── models.py            # Dataclasses Entry, SearchResult (à étendre: Link, ReviewSchedule)
├── tui.py               # TUI Textual (à étendre: affichage liens, consolidation)
├── config.py
├── paths.py
├── i18n.py
├── exporters.py
├── sync.py
├── archive.py
└── integrations/
    └── __init__.py      # Installation IDE (à étendre: skill Claude)

tests/
├── test_cli.py
├── test_db.py
└── test_models.py       # (à créer: test_links.py, test_review.py)
```

**Structure Decision**: Projet single (CLI Python). Extension du code existant, pas de nouveau module majeur. Les liens et le tracking sont intégrés aux modules existants (db.py, models.py, cli.py).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

*Aucune violation détectée. Pas de tracking de complexité requis.*
