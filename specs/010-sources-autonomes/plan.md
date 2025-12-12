# Implementation Plan: Sources Autonomes

**Branch**: `010-sources-autonomes` | **Date**: 2025-12-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-sources-autonomes/spec.md`

## Summary

Cette feature transforme le système de sources documentaires de Rekall (Feature 009) en un écosystème autonome et intelligent. Elle permet :
1. Migration des fichiers statiques `~/.speckit/research/*.md` vers la base de données
2. Promotion automatique des sources fréquemment utilisées
3. Classification Hub/Authority basée sur l'algorithme HITS
4. Scoring avancé avec citation quality (PR-Index)
5. API JSON pour intégration Speckit

## Technical Context

**Language/Version**: Python 3.9+ (compatible 3.9-3.13)
**Primary Dependencies**: Typer (CLI), Rich (output), Textual (TUI), SQLite (storage)
**Storage**: SQLite via `rekall/db.py` (schema v8 existant pour sources)
**Testing**: pytest + pytest-cov + ruff (lint)
**Target Platform**: macOS/Linux CLI
**Project Type**: Single project (CLI + TUI)
**Performance Goals**: <500ms pour requêtes sources par thème (SC-003)
**Constraints**: Pas de dépendances externes additionnelles (stdlib HTTP pour link rot)
**Scale/Scope**: ~100-500 sources, ~10 thèmes, usage personnel

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Vérification | Status |
|---------|-------------|--------|
| **III. Processus SpecKit** | Cycle complet respecté (specify → plan → tasks) | ✅ Pass |
| **VII. ADR** | Décision HITS+TrustRank documentée dans research.md | ✅ Pass |
| **IX. Recherche** | Research Hub consulté, validation live effectuée | ✅ Pass |
| **XV. Test-Before-Next** | Tests obligatoires définis | ✅ Pass |
| **XVI. Worktree** | Worktree créé `.worktrees/010-sources-autonomes/` | ✅ Pass |
| **XVII. DevKMS** | Capture automatique prévue | ✅ Pass |

**Aucune violation détectée.**

## Project Structure

### Documentation (this feature)

```text
specs/010-sources-autonomes/
├── spec.md              # Spécification (complète)
├── research.md          # Recherche SOTA (complète)
├── plan.md              # This file
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI API)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
rekall/
├── db.py                # Extension: nouvelles tables, fonctions scoring
├── models.py            # Extension: nouveaux types/dataclasses
├── cli.py               # Extension: commandes sources suggest/migrate
├── tui.py               # Extension: dashboard enrichi
├── i18n.py              # Extension: traductions
├── utils.py             # Existant: URL helpers
├── link_rot.py          # Existant: vérification URLs
└── migration/           # Nouveau: parseur fichiers speckit
    └── speckit_parser.py

tests/
├── test_db.py           # Extension: tests nouvelles fonctions
├── test_migration.py    # Nouveau: tests parseur speckit
└── test_integration_sources.py  # Extension: tests E2E
```

**Structure Decision**: Extension du projet existant (pas de nouveau module racine). Le parseur speckit est isolé dans un sous-module `migration/` car c'est une fonctionnalité one-shot.

## Complexity Tracking

> **Aucune violation - section vide**

---

## Phase 0: Research Output

Voir `research.md` (déjà complet) pour :
- Algorithmes HITS, PageRank, TrustRank, PR-Index
- Admiralty Code simplifié (A/B/C)
- Formule de scoring recommandée
- Sources académiques et industrielles

**Pas de NEEDS CLARIFICATION restant.**

---

## Phase 1: Design Output

### Data Model

Voir `data-model.md` pour le schéma complet.

**Résumé des changements v8 → v9 :**

| Table | Action | Description |
|-------|--------|-------------|
| `sources` | ALTER | Ajout colonnes: `is_seed`, `is_promoted`, `promoted_at`, `role`, `seed_origin`, `citation_quality_factor` |
| `source_themes` | CREATE | Table de jonction (source_id FK, theme TEXT) |
| `known_domains` | CREATE | Liste domaines avec classification hub/authority |

### API Contracts

Voir `contracts/cli-api.md` pour les commandes CLI.

**Résumé des nouvelles commandes :**

| Commande | Description |
|----------|-------------|
| `rekall sources migrate` | Importe fichiers speckit |
| `rekall sources suggest --theme X` | Retourne JSON sources triées |
| `rekall sources recalculate` | Recalcule tous les scores |
| `rekall sources classify <id> <role>` | Classification manuelle |

### Quickstart

Voir `quickstart.md` pour le guide de démarrage rapide.
