# Feature Specification: Code Modularization

**Feature Branch**: `017-code-modularization`
**Created**: 2025-12-12
**Status**: Draft
**Input**: Roadmap audit "moyen terme" - Modularisation modules monolithiques

## Context

L'audit v0.3.0 a identifié que trois fichiers principaux dépassent les seuils de maintenabilité :

| Fichier | LOC actuelles | Seuil recommandé |
|---------|---------------|------------------|
| `rekall/tui.py` | 7875 | < 2000 |
| `rekall/db.py` | 4499 | < 1500 |
| `rekall/cli.py` | 4441 | < 1500 |

Cette dette technique impacte :
- La complexité cognitive pour les contributeurs
- Le risque de régressions lors de modifications
- La difficulté d'onboarding de nouveaux développeurs
- La testabilité unitaire des composants

## User Scenarios & Testing

### User Story 1 - CLI Commands Refactoring (Priority: P1)

En tant que contributeur, je veux que les commandes CLI soient organisées par domaine fonctionnel pour pouvoir modifier une fonctionnalité sans risquer d'impacter les autres.

**Why this priority**: Le CLI est l'interface principale de Rekall. Sa modularisation facilite les contributions et réduit les régressions.

**Independent Test**: Après refactoring, `rekall --help` affiche les mêmes commandes et `pytest tests/test_cli.py` passe sans modification.

**Acceptance Scenarios**:

1. **Given** le CLI actuel monolithique, **When** je restructure en sous-modules par domaine, **Then** toutes les commandes existantes fonctionnent identiquement
2. **Given** un nouveau contributeur, **When** il veut modifier la commande `add`, **Then** il trouve facilement le fichier dédié sans parcourir 4000+ lignes

---

### User Story 2 - Database Layer Extraction (Priority: P1)

En tant que développeur, je veux que les opérations de base de données soient séparées en repositories par entité pour pouvoir tester et maintenir chaque partie indépendamment.

**Why this priority**: Le module DB est le cœur du système. Sa modularisation améliore la testabilité et permet l'évolution du schéma sans risque.

**Independent Test**: Après refactoring, `pytest tests/test_db.py` passe sans modification et les migrations fonctionnent.

**Acceptance Scenarios**:

1. **Given** db.py monolithique, **When** j'extrais les repositories par entité, **Then** chaque repository peut être testé unitairement
2. **Given** une modification du schéma sources, **When** je modifie le repository sources, **Then** les autres repositories ne sont pas impactés

---

### User Story 3 - TUI Components Separation (Priority: P2)

En tant que développeur UI, je veux que les composants TUI soient séparés en widgets Textual distincts pour pouvoir réutiliser et tester chaque composant.

**Why this priority**: Le TUI est le fichier le plus volumineux. Sa modularisation améliore la maintenabilité mais est moins critique que CLI/DB pour le fonctionnement de base.

**Independent Test**: Après refactoring, `rekall` (mode interactif) fonctionne identiquement et les raccourcis clavier sont préservés.

**Acceptance Scenarios**:

1. **Given** tui.py monolithique, **When** j'extrais les widgets en composants, **Then** chaque widget peut être testé indépendamment
2. **Given** un bug dans le panneau de détails, **When** je le corrige, **Then** les autres composants TUI ne sont pas affectés

---

### User Story 4 - Architecture Layers Definition (Priority: P2)

En tant qu'architecte, je veux une séparation claire entre présentation/domaine/infrastructure pour découpler les couches et faciliter l'évolution.

**Why this priority**: Cette séparation est fondamentale pour la scalabilité mais peut être réalisée progressivement avec les autres US.

**Independent Test**: L'import d'un module de domaine ne doit pas déclencher d'import de modules UI.

**Acceptance Scenarios**:

1. **Given** les frontières actuellement floues, **When** je définis services/infra/ui, **Then** les dépendances sont unidirectionnelles (ui → services → infra)
2. **Given** le serveur MCP, **When** il utilise les services, **Then** il n'a pas besoin d'importer le CLI ou le TUI

---

### Edge Cases

- Que se passe-t-il si un import circulaire est introduit pendant le refactoring ? → Détecté et bloqué par ruff (règle I001)
- Comment gérer les singletons globaux (config, db) pendant la transition ? → Conserver en place, nouveaux modules les importent
- Comment préserver la compatibilité des commandes CLI existantes ? → Ré-exports dans `__init__.py`

## Requirements

### Functional Requirements

- **FR-001**: Le refactoring DOIT préserver 100% des fonctionnalités existantes (aucune régression)
- **FR-002**: Le refactoring DOIT maintenir la compatibilité CLI (mêmes commandes, mêmes options)
- **FR-003**: Chaque nouveau module DOIT avoir moins de 500 LOC (seuil cible)
- **FR-004**: Les imports circulaires DOIVENT être détectés et bloqués par le linter
- **FR-005**: Les tests existants DOIVENT continuer à passer sans modification
- **FR-006**: La documentation des imports publics DOIT être maintenue via `__all__`
- **FR-007**: Les anciens chemins d'import DOIVENT continuer à fonctionner via ré-exports dans les `__init__.py` (compatibilité descendante totale)

### Structure Cible

```
rekall/
├── cli/
│   ├── __init__.py          # Entry point, app = typer.Typer()
│   ├── entries.py            # add, show, edit, delete, search
│   ├── sources.py            # source commands
│   ├── config_cmd.py         # config commands
│   ├── backup_cmd.py         # backup, restore
│   └── utils.py              # shared CLI utilities
├── services/
│   ├── __init__.py
│   ├── entries.py            # business logic entries
│   ├── sources.py            # business logic sources
│   ├── promotion.py          # promotion logic
│   └── embeddings.py         # embeddings service
├── infra/
│   ├── __init__.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py     # Database class, connection
│   │   ├── migrations.py     # schema migrations
│   │   ├── entries_repo.py   # entries CRUD
│   │   ├── sources_repo.py   # sources CRUD
│   │   └── embeddings_repo.py
│   └── http/
│       └── enrichment.py     # HTTP clients
├── ui/
│   ├── __init__.py
│   ├── app.py                # RekallApp main
│   ├── screens/
│   │   ├── main.py           # MainScreen
│   │   └── settings.py       # SettingsScreen
│   └── widgets/
│       ├── entry_list.py
│       ├── detail_panel.py
│       └── search_bar.py
└── [existing files]          # models.py, config.py, etc.
```

## Success Criteria

### Measurable Outcomes

- **SC-001**: Aucun fichier ne dépasse 500 LOC (vs 7875 actuellement)
- **SC-002**: 100% des tests existants passent après refactoring
- **SC-003**: Temps de compréhension d'un module réduit (mesurable via onboarding)
- **SC-004**: Couverture de tests unitaires possible sur chaque composant isolé
- **SC-005**: Score audit qualité de code passe de B- à B+ minimum

## Assumptions

- Le refactoring peut se faire progressivement (pas de big bang)
- Les imports publics sont documentés via `__all__` pour la compatibilité
- Les tests existants sont suffisants pour détecter les régressions
- Le CI (Feature 016) est en place pour valider chaque étape

## Out of Scope

- Nouvelles fonctionnalités (focus sur refactoring pur)
- Changement de framework (Typer, Textual restent)
- Migration de base de données
- Chiffrement SQLite (audit long terme)

## Clarifications

### Session 2025-12-12

- Q: Les anciens chemins d'import doivent-ils continuer à fonctionner après refactoring ? → A: Compatibilité totale - anciens imports fonctionnent via ré-exports dans `__init__.py`
- Q: Comment gérer les singletons globaux (config, db) pendant la transition ? → A: Conserver singletons en place - nouveaux modules les importent
