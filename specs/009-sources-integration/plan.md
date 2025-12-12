# Implementation Plan: Intégration Souvenirs & Sources Documentaires

**Branch**: `009-sources-integration` | **Date**: 2025-12-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-sources-integration/spec.md`

## Summary

Cette feature ajoute des **liens bidirectionnels** entre les souvenirs Rekall et les sources documentaires avec un **scoring adaptatif basé sur l'usage**. L'objectif est de prioriser automatiquement les sources les plus utiles lors des futures recherches en trackant leur utilisation réelle.

## Technical Context

**Language/Version**: Python 3.9+ (compatible 3.9-3.13)
**Primary Dependencies**: Typer, Rich, Textual (TUI), SQLite (base existante)
**Storage**: SQLite avec FTS5 (schéma existant v7, à migrer vers v8)
**Testing**: pytest avec pytest-cov
**Target Platform**: macOS, Linux, Windows (CLI cross-platform)
**Project Type**: Single project (CLI avec TUI Textual)
**Performance Goals**: Calcul du score < 100ms, recherche triée < 1s
**Constraints**: Pas de dépendances réseau sauf vérification link rot (HTTP HEAD)
**Scale/Scope**: 100-1000 sources, 1000-10000 souvenirs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Règle | Conformité | Notes |
|---------|-------|------------|-------|
| III | Process SpecKit obligatoire | ✅ PASS | Spec créée via `/speckit.specify` |
| VII | ADR pour décisions structurantes | ⏳ DEFERRED | ADR à créer si choix majeur |
| IX | Recherche préalable | ✅ PASS | Voir `docs/research-sources-souvenirs-integration.md` |
| XV | Test-Before-Next | ✅ WILL COMPLY | Tests à créer pour chaque tâche |
| XVI | Worktree obligatoire | ⚠️ N/A | Branche sur main (pas de worktree isolé) |

## Project Structure

### Documentation (this feature)

```text
specs/009-sources-integration/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
rekall/
├── __init__.py
├── __main__.py
├── cli.py               # CLI Typer (à modifier: commandes sources)
├── db.py                # Database SQLite (à modifier: tables sources)
├── models.py            # Modèles dataclass (à modifier: Source, EntrySource)
├── tui.py               # TUI Textual (à modifier: écrans sources, liaison)
├── i18n.py              # Traductions (à modifier: clés sources)
├── config.py            # Configuration
├── exporters.py         # Export données
├── embeddings.py        # Embeddings sémantiques
└── ...

tests/
├── conftest.py
├── test_db.py           # Tests DB (à étendre: sources)
├── test_models.py       # Tests modèles (à étendre: Source)
├── test_tui.py          # Tests TUI (à étendre: écrans sources)
└── ...
```

**Structure Decision**: Single project existant. Pas de modification de structure, extension du code existant.

## Complexity Tracking

> Aucune violation détectée - feature s'intègre dans l'architecture existante.

| Aspect | Décision | Justification |
|--------|----------|---------------|
| Nouvelles tables | 2 tables (sources, entry_sources) | Extension naturelle du schéma v7 |
| Nouveau schéma | Migration v7 → v8 | Pattern migrations existant |
| Scoring | Calcul côté Python | Simplicité vs trigger SQL |
| Link rot | HTTP HEAD async | Pas de dépendance lourde |
