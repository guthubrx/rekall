# Implementation Plan: Code Modularization

**Branch**: `017-code-modularization` | **Date**: 2025-12-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/017-code-modularization/spec.md`

## Summary

Modularisation des trois fichiers monolithiques (cli.py 4643 LOC, db.py 4502 LOC, tui.py 7872 LOC) en sous-modules cohérents de moins de 500 LOC. L'approche est progressive (refactoring pur sans nouvelles fonctionnalités) avec maintien de la compatibilité descendante via ré-exports dans `__init__.py`.

## Technical Context

**Language/Version**: Python 3.10+ (compatible 3.10-3.13)
**Primary Dependencies**: Typer (CLI), Textual (TUI), SQLite (DB)
**Storage**: SQLite via `sqlite3` stdlib
**Testing**: pytest avec 488 tests existants
**Target Platform**: macOS/Linux (CLI/TUI desktop)
**Project Type**: Single project (CLI + TUI + DB)
**Performance Goals**: Aucune régression de performance (temps de démarrage < 500ms)
**Constraints**: 100% compatibilité CLI existante, imports rétrocompatibles
**Scale/Scope**: ~17,000 LOC à refactoriser en ~35 modules

## Constitution Check

*GATE: Passé - Prêt pour Phase 0 research.*

| Article | Vérification | Statut |
|---------|--------------|--------|
| III. Processus SpecKit | Workflow specify → plan → tasks → implement | ✅ Respecté |
| IV. Disjoncteur | N/A (refactoring, pas debugging) | ✅ N/A |
| V. Anti Scope-Creep | Refactoring pur, aucune nouvelle fonctionnalité | ✅ Respecté |
| VII. ADR | Décision architecture sera documentée | ✅ À créer |
| XV. Test-Before-Next | Tests existants (488) comme filet de sécurité | ✅ Applicable |
| XVI. Worktree | Branche dédiée 017-code-modularization | ✅ Respecté |

**Complexité estimée**: Élevée (refactoring majeur) mais risque faible (tests existants)

## Project Structure

### Documentation (this feature)

```text
specs/017-code-modularization/
├── plan.md              # This file
├── research.md          # Phase 0 output - patterns de modularisation
├── data-model.md        # Phase 1 output - structure des imports/exports
├── quickstart.md        # Phase 1 output - guide de migration imports
├── contracts/           # Phase 1 output
│   ├── cli-structure.md     # Structure cible CLI
│   ├── db-structure.md      # Structure cible DB
│   └── tui-structure.md     # Structure cible TUI
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (current → target)

```text
# ACTUEL (monolithes)
rekall/
├── cli.py              (4643 LOC) → cli/
├── db.py               (4502 LOC) → infra/db/
├── tui.py              (7872 LOC) → ui/
└── [existing files]    (conservés)

# CIBLE (modulaire)
rekall/
├── cli/                         # Interface CLI (Typer)
│   ├── __init__.py              # app = typer.Typer() + ré-exports
│   ├── core.py                  # version, config, init, info (~150 LOC)
│   ├── entries.py               # search, add, show, browse (~400 LOC)
│   ├── memory.py                # review, stale, generalize (~300 LOC)
│   ├── knowledge_graph.py       # link, unlink, related, graph (~250 LOC)
│   ├── import_export.py         # export, import_archive (~200 LOC)
│   ├── research.py              # research, similar, suggest (~300 LOC)
│   ├── sources.py               # 12 sources_* commands (~500 LOC)
│   ├── inbox.py                 # 6 inbox_* commands (~300 LOC)
│   ├── staging.py               # 6 staging_* commands (~300 LOC)
│   ├── system.py                # backup, restore, migrate, mcp (~400 LOC)
│   └── helpers.py               # get_db, decorators, utilities (~200 LOC)
│
├── services/                    # Business logic (découplée)
│   ├── __init__.py              # ré-exports
│   ├── entries.py               # logique métier entries (~200 LOC)
│   ├── sources.py               # logique métier sources (~200 LOC)
│   ├── promotion.py             # → réutilise rekall/promotion.py existant
│   └── embeddings.py            # → réutilise rekall/embeddings.py existant
│
├── infra/                       # Infrastructure layer
│   ├── __init__.py
│   └── db/                      # Database repositories
│       ├── __init__.py          # Database class + ré-exports
│       ├── connection.py        # connexion, migrations (~300 LOC)
│       ├── entries_repo.py      # CRUD entries (~400 LOC)
│       ├── access_tracking.py   # spaced repetition (~150 LOC)
│       ├── knowledge_graph.py   # links, graph (~250 LOC)
│       ├── embeddings_repo.py   # vectors (~200 LOC)
│       ├── suggestions_repo.py  # IA suggestions (~150 LOC)
│       ├── context_repo.py      # context storage (~250 LOC)
│       ├── sources_repo.py      # CRUD sources (~300 LOC)
│       ├── source_scoring.py    # calculs scores (~300 LOC)
│       ├── source_filtering.py  # recherche avancée (~300 LOC)
│       ├── source_promotion.py  # promotion/demotion (~300 LOC)
│       ├── inbox_repo.py        # inbox entries (~150 LOC)
│       ├── staging_repo.py      # staging entries (~150 LOC)
│       └── filters_repo.py      # saved filters (~100 LOC)
│
├── ui/                          # TUI (Textual)
│   ├── __init__.py              # run_tui() + ré-exports
│   ├── app.py                   # RekallMenuApp principal (~400 LOC)
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── main.py              # écran principal (~300 LOC)
│   │   ├── browse.py            # BrowseApp, navigation (~500 LOC)
│   │   ├── research.py          # ResearchApp (~300 LOC)
│   │   ├── sources.py           # SourcesBrowseApp (~400 LOC)
│   │   ├── inbox.py             # InboxBrowseApp (~300 LOC)
│   │   ├── staging.py           # StagingBrowseApp (~300 LOC)
│   │   └── config.py            # MCPConfigApp, settings (~300 LOC)
│   └── widgets/
│       ├── __init__.py
│       ├── menu.py              # MenuItem, MenuListView (~200 LOC)
│       ├── detail_panel.py      # panneau détails (~200 LOC)
│       ├── search_bar.py        # barre recherche (~150 LOC)
│       ├── toast.py             # notifications (~100 LOC)
│       └── theme.py             # BANNER, CSS, styling (~200 LOC)
│
├── cli.py                       # COMPAT: from rekall.cli import *
├── db.py                        # COMPAT: from rekall.infra.db import *
├── tui.py                       # COMPAT: from rekall.ui import *
└── [existing modules]           # Non modifiés (models, config, etc.)

tests/
├── cli/                         # Tests CLI par module
├── db/                          # Tests DB par repository
├── ui/                          # Tests TUI par screen/widget
└── [existing tests]             # Non modifiés
```

**Structure Decision**: Architecture en couches (CLI → Services → Infra/DB → Models) avec séparation TUI. Les anciens fichiers `cli.py`, `db.py`, `tui.py` deviennent des façades de compatibilité.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| 35+ sous-modules | 17K LOC à <500 LOC/fichier | Garder monolithes impossible (seuil audit) |
| Couche services/ | Découplage CLI/TUI du DB | Imports directs créeraient couplage fort |
| Façades compatibilité | Migration douce pour utilisateurs | Breaking changes des imports inacceptable |

## Phase 0: Research Output

Voir [research.md](./research.md) pour l'analyse des patterns de modularisation Python et les best practices.

## Phase 1: Design Output

Voir:
- [data-model.md](./data-model.md) - Structure des imports/exports
- [quickstart.md](./quickstart.md) - Guide de migration
- [contracts/](./contracts/) - Structures détaillées par domaine

## Risk Analysis

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Imports circulaires | Moyenne | Bloquant | ruff I001, TYPE_CHECKING |
| Régression tests | Faible | Haute | Tests existants comme gate |
| Performance démarrage | Faible | Moyenne | Lazy imports |
| Breaking changes API | Faible | Haute | Façades compatibilité |

## Estimation

| Phase | User Story | Modules | LOC estimé |
|-------|------------|---------|------------|
| CLI | US1 | 11 | ~3,300 |
| DB | US2 | 14 | ~3,500 |
| TUI | US3 | 12 | ~3,900 |
| Services | US4 | 4 | ~600 |
| **Total** | | **41** | **~11,300** |

**Note**: Estimation conservative. Le code est réorganisé, pas réécrit.
