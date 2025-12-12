# Implementation Plan: DevKMS - Developer Knowledge Management CLI

**Branch**: `001-python-cli-package` | **Date**: 2025-12-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-python-cli-package/spec.md`

## Summary

CLI Python cross-platform (`mem`) pour capturer et retrouver bugs, patterns, décisions techniques. Distribution via PyPI. Base SQLite locale avec FTS5. Intégrations multi-IDE (Claude Code skills, Cursor rules, Copilot instructions, etc.). Recherche sémantique optionnelle via Ollama/OpenAI.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: typer (CLI), rich (affichage), sqlite3 (stdlib)
**Storage**: SQLite avec FTS5 dans `~/.devkms/knowledge.db`
**Testing**: pytest
**Target Platform**: Windows, macOS, Linux (cross-platform)
**Project Type**: Single CLI package
**Performance Goals**: Recherche < 100ms pour 10 000 entrées (SC-002)
**Constraints**: 2 dépendances externes max, package < 500KB, Python 3.11+
**Scale/Scope**: Usage personnel, base locale, pas de sync cloud

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Règle | Statut | Notes |
|---------|-------|--------|-------|
| III | Processus SpecKit Obligatoire | ✅ PASS | On suit /speckit.specify → plan → tasks → implement |
| VII | Mémoire Architecturale (ADR) | ✅ PASS | Décisions capturées dans plan.md + future DevKMS |
| IX | Recherche Préalable | ✅ PASS | Phase 0 research à faire |
| XV | Test-Before-Next | ✅ PASS | pytest + lint prévu |
| XVI | Workflow Worktree | ⚠️ DÉROGÉ | Pas de worktree - c'est un nouveau projet standalone |
| XVII | DevKMS Capture | ⚠️ N/A | DevKMS n'existe pas encore - c'est ce qu'on crée |

**Violations justifiées** :
- Article XVI : Nouveau projet standalone, pas de repo principal à protéger
- Article XVII : Bootstrapping - DevKMS n'existe pas encore

## Project Structure

### Documentation (this feature)

```text
specs/001-python-cli-package/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # N/A - CLI, pas d'API REST
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
devkms/                     # Package Python principal
├── __init__.py             # Version, metadata
├── __main__.py             # Point d'entrée: python -m devkms
├── cli.py                  # Commandes Typer (add, search, show, etc.)
├── db.py                   # Gestion SQLite + FTS5
├── models.py               # Dataclasses (Entry, Tag, etc.)
├── config.py               # Paths, settings (~/.devkms/)
├── exporters.py            # Export markdown, JSON, etc.
├── integrations/           # Templates IDE
│   ├── __init__.py
│   ├── claude_code.py      # Skills generator
│   ├── cursor.py           # .cursorrules generator
│   ├── copilot.py          # copilot-instructions generator
│   ├── windsurf.py         # .windsurfrules generator
│   ├── cline.py            # .clinerules generator
│   ├── aider.py            # CONVENTIONS.md generator
│   ├── continue_dev.py     # .continue/rules/*.md generator
│   └── zed.py              # .rules generator
└── embeddings.py           # Recherche sémantique optionnelle (P3)

research/                   # Fichiers research curés (distribués)
├── 01-ai-agents.md
├── 02-roi-business.md
├── ...
└── 10-data-privacy.md

tests/
├── conftest.py
├── test_cli.py
├── test_db.py
├── test_models.py
├── test_exporters.py
└── test_integrations.py

pyproject.toml              # Build config, dépendances, entry point
README.md                   # Documentation utilisateur
LICENSE                     # MIT
```

**Structure Decision**: Single project Python avec package `devkms/`. Les fichiers `research/` sont distribués avec le package (via `package_data` dans pyproject.toml).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Article XVI (worktree) | Nouveau projet standalone | Pas de repo existant à protéger |
| Article XVII (DevKMS) | Bootstrapping | On crée DevKMS lui-même |
