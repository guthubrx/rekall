# Tasks: Audit Remediation v0.3.0

**Input**: Design documents from `/specs/016-audit-remediation/`
**Prerequisites**: plan.md, spec.md, research.md, contracts/ci-workflow.yml

**Tests**: Non demandés explicitement - pas de tâches de tests générées.

**Organisation**: 6 User Stories (2 P1 + 3 P2 + 1 P3) - corrections issues audit.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Peut s'exécuter en parallèle (fichiers différents, pas de dépendances)
- **[Story]**: User Story correspondante (US1-US6)
- Chemins exacts dans les descriptions

## Path Conventions

- **CI Workflow**: `.github/workflows/ci.yml`
- **Config**: `pyproject.toml`, `rekall/config.py`
- **Security**: `rekall/connectors/base.py`
- **Documentation**: `docs/getting-started.md`
- **License**: `LICENSE`

---

## Phase 1: Setup

**Purpose**: Préparation de l'environnement et vérification des prérequis

- [x] T001 Vérifier que la branche 016-audit-remediation est active
- [x] T002 Vérifier que uv est installé (`uv --version`)
- [x] T003 Lire le code existant de `rekall/connectors/base.py` pour comprendre `validate_url()`
- [x] T004 Lire le code existant de `rekall/config.py` pour comprendre la gestion TOML

---

## Phase 2: Foundational - Lockfile & Versions (US2 - Priority: P1)

**Purpose**: Créer le lockfile uv.lock - BLOQUANT pour le CI (US1)

**⚠️ CRITIQUE**: Cette phase doit être complète avant US1 (CI utilise `uv sync --frozen`)

**Goal**: Builds reproductibles avec dépendances verrouillées

**Independent Test**: `uv sync --frozen` installe exactement les mêmes versions sur toute machine

### Implementation

- [x] T005 [US2] Ajouter dépendance `tomlkit` dans `pyproject.toml`
- [x] T006 [US2] Ajouter dépendance `pip-audit` dans `[project.optional-dependencies].dev` de `pyproject.toml`
- [x] T007 [US2] Resserrer les bornes de versions dans `pyproject.toml` (`>=x.y.z,<x+1`)
- [x] T008 [US2] Ajouter extra `[embeddings]` dans `pyproject.toml` avec `sentence-transformers>=2.2,<3` et `numpy>=1.24,<2`
- [x] T009 [US2] Générer `uv.lock` avec `uv lock`
- [x] T010 [US2] Vérifier que `uv sync --frozen` fonctionne sans erreur

**Checkpoint**: ✅ uv.lock généré et versionné

---

## Phase 3: User Story 1 - CI Pipeline Setup (Priority: P1)

**Goal**: Automatiser tests, linting et audit sécurité sur chaque push/PR

**Independent Test**: Créer une PR avec violation ruff et vérifier que le CI échoue

### Implementation

- [x] T011 [US1] Créer le répertoire `.github/workflows/`
- [x] T012 [US1] Créer `.github/workflows/ci.yml` avec job `test` (pytest matrix Python 3.10-3.13)
- [x] T013 [US1] Ajouter job `lint` (ruff check avec annotations GitHub) dans `.github/workflows/ci.yml`
- [x] T014 [US1] Ajouter job `security` (pip-audit + gitleaks) dans `.github/workflows/ci.yml`
- [x] T015 [US1] Vérifier la syntaxe du workflow avec `actionlint` ou push de test

**Checkpoint**: ✅ CI fonctionnel avec 3 jobs parallèles

---

## Phase 4: User Story 3 - SSRF Hardening (Priority: P2)

**Goal**: Renforcer la validation d'URL contre les bypasses SSRF

**Independent Test**: `validate_url("https://localhost@evil.com/")` retourne False

### Implementation

- [x] T016 [P] [US3] Ajouter constantes `PRIVATE_IPV4_NETWORKS` et `PRIVATE_IPV6_NETWORKS` dans `rekall/connectors/base.py`
- [x] T017 [US3] Créer fonction `_is_private_ip(ip_str)` dans `rekall/connectors/base.py`
- [x] T018 [US3] Créer fonction `_resolve_and_validate_ip(hostname)` dans `rekall/connectors/base.py`
- [x] T019 [US3] Modifier `validate_url()` pour utiliser `parsed.hostname` au lieu de `parsed.netloc` dans `rekall/connectors/base.py`
- [x] T020 [US3] Ajouter appel à `_resolve_and_validate_ip()` dans `validate_url()` de `rekall/connectors/base.py`

**Checkpoint**: ✅ URLs bypass SSRF rejetées

---

## Phase 5: User Story 4 - TOML Config Robustness (Priority: P2)

**Goal**: Migrer vers tomlkit et remonter les erreurs clairement

**Independent Test**: Fichier TOML malformé → message d'erreur explicite (pas `{}` silencieux)

### Implementation

- [x] T021 [P] [US4] Ajouter import `tomlkit` dans `rekall/config.py`
- [x] T022 [US4] Remplacer `_format_toml_value()` par `tomlkit.dumps()` dans `rekall/config.py`
- [x] T023 [US4] Modifier `_load_toml()` pour logger et re-raise les exceptions au lieu de `return {}` dans `rekall/config.py`
- [x] T024 [US4] Ajouter message d'erreur utilisateur clair dans CLI si config invalide dans `rekall/config.py`

**Checkpoint**: ✅ Erreurs TOML visibles et actionables

---

## Phase 6: User Story 5 - Embeddings Doc Alignment (Priority: P2)

**Goal**: Aligner documentation et code pour les embeddings

**Independent Test**: Doc mentionne `all-MiniLM-L6-v2`, pas `EmbeddingGemma`

### Implementation

- [x] T025 [P] [US5] Corriger mention du modèle embeddings dans `docs/getting-started.md` (EmbeddingGemma → all-MiniLM-L6-v2)
- [x] T026 [P] [US5] Ajouter avertissement téléchargement réseau dans `docs/getting-started.md`
- [x] T027 [US5] Vérifier que l'extra `[embeddings]` est bien documenté dans `docs/getting-started.md`

**Checkpoint**: ✅ Documentation cohérente avec le code

---

## Phase 7: User Story 6 - LICENSE File (Priority: P3)

**Goal**: Ajouter fichier LICENSE MIT à la racine

**Independent Test**: Fichier `LICENSE` existe et contient "MIT License"

### Implementation

- [x] T028 [P] [US6] Créer fichier `LICENSE` à la racine avec texte MIT standard (année 2024, titulaire du pyproject.toml)

**Checkpoint**: ✅ Conformité licence

---

## Phase 8: Polish & Validation

**Purpose**: Validation finale et nettoyage

- [x] T029 Exécuter `uv run pytest -q` et vérifier que tous les tests passent
- [x] T030 Exécuter `uv run ruff check .` et corriger les erreurs éventuelles
- [x] T031 Exécuter `uv run pip-audit` et vérifier aucune CVE
- [x] T032 Créer une PR de test pour valider le CI sur GitHub

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Aucune dépendance
- **Phase 2 (Foundational/US2)**: Dépend de Phase 1 - BLOQUE Phase 3
- **Phase 3 (US1)**: Dépend de Phase 2 (lockfile requis pour `--frozen`)
- **Phases 4-7 (US3-US6)**: Peuvent s'exécuter en parallèle après Phase 2
- **Phase 8 (Polish)**: Dépend de toutes les phases précédentes

### User Story Dependencies

| Story | Titre | Dépendances |
|-------|-------|-------------|
| US2 | Lockfile | Aucune (foundational) |
| US1 | CI Pipeline | US2 (lockfile requis) |
| US3 | SSRF Hardening | Aucune |
| US4 | TOML Config | US2 (tomlkit ajouté) |
| US5 | Embeddings Doc | US2 (extra ajouté) |
| US6 | LICENSE | Aucune |

### Parallel Opportunities

```text
# Après Phase 2 (Foundational), paralléliser :
Phase 3 (US1 - CI) + Phase 4 (US3 - SSRF) + Phase 5 (US4 - TOML) + Phase 6 (US5 - Doc) + Phase 7 (US6 - LICENSE)

# Dans Phase 4 (US3), T016 peut être parallélisé (fichier différent des autres)
# Dans Phase 5 (US4), T021 peut être parallélisé
# Dans Phase 6 (US5), T025 et T026 peuvent être parallélisés
# Phase 7 (US6) est une seule tâche indépendante
```

---

## Implementation Strategy

### MVP First (P1 Only)

1. Compléter Phase 1 (Setup)
2. Compléter Phase 2 (US2 - Lockfile) - FONDAMENTAL
3. Compléter Phase 3 (US1 - CI Pipeline)
4. **STOP et VALIDER**: Pusher et vérifier CI fonctionnel
5. Score audit CI/CD devrait passer de D à B+

### Full Feature

1. Compléter MVP (US1 + US2)
2. Paralléliser US3, US4, US5, US6
3. Compléter Phase 8 (Polish)
4. Re-run audit complet

---

## Task Summary

| Phase | User Story | Tasks | Parallélisables |
|-------|------------|-------|-----------------|
| 1 | Setup | T001-T004 (4) | Non |
| 2 | US2 - Lockfile | T005-T010 (6) | Non |
| 3 | US1 - CI | T011-T015 (5) | Non |
| 4 | US3 - SSRF | T016-T020 (5) | T016 |
| 5 | US4 - TOML | T021-T024 (4) | T021 |
| 6 | US5 - Doc | T025-T027 (3) | T025, T026 |
| 7 | US6 - LICENSE | T028 (1) | T028 |
| 8 | Polish | T029-T032 (4) | Non |

**Total**: 32 tâches
**MVP (P1)**: T001-T015 (15 tâches)
