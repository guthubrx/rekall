# Implementation Plan: Audit Remediation v0.3.0

**Branch**: `016-audit-remediation` | **Date**: 2025-12-12 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification + audit report `audits/audit-2025-12-12-v0.3.0.md`

## Summary

Corrections des issues identifiées dans l'audit de sécurité/qualité v0.3.0 :
- **Score actuel**: B- (CI/CD: D, Supply Chain: D)
- **Score cible**: B+ minimum
- **6 User Stories**: CI Pipeline, Lockfile, SSRF Hardening, TOML Config, Embeddings Doc, LICENSE

## Technical Context

**Language/Version**: Python 3.10-3.13 (matrice CI)
**Primary Dependencies**: uv, ruff, pytest, pip-audit, gitleaks, tomlkit, httpx
**Storage**: N/A (feature DevOps/config)
**Testing**: pytest (existant)
**Target Platform**: GitHub Actions (Linux ubuntu-latest)
**Project Type**: Single project (CLI Python)
**Performance Goals**: CI < 5 minutes
**Constraints**: Aucun breaking change pour les utilisateurs existants
**Scale/Scope**: 1 workflow CI, ~100 LOC modifications

## Constitution Check

*Constitution non trouvée - check bypassed*

## Project Structure

### Documentation (this feature)

```text
specs/016-audit-remediation/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Technical decisions
├── quickstart.md        # Developer guide
├── contracts/
│   └── ci-workflow.yml  # Target CI structure
├── checklists/
│   └── requirements.md  # Spec validation
└── tasks.md             # (à générer via /speckit.tasks)
```

### Source Code (repository root)

```text
# Fichiers à créer
.github/
└── workflows/
    └── ci.yml           # GitHub Actions workflow
LICENSE                  # MIT license file
uv.lock                  # Dependency lockfile

# Fichiers à modifier
pyproject.toml           # Versions + extras
rekall/
├── connectors/
│   └── base.py          # SSRF hardening
└── config.py            # tomlkit migration
docs/
└── getting-started.md   # Embeddings doc fix
```

**Structure Decision**: Projet existant, ajout de fichiers CI/config à la racine.

## Implementation Approach

### US1: CI Pipeline Setup (P1)

**Approche**: Créer `.github/workflows/ci.yml` avec 3 jobs parallèles

| Job | Outils | Trigger |
|-----|--------|---------|
| test | pytest + uv | push/PR |
| lint | ruff | push/PR |
| security | pip-audit + gitleaks | push/PR |

**Risques**:
- Timeout pip-audit sur réseau lent → `continue-on-error: true` optionnel
- gitleaks faux positifs → fichier `.gitleaks.toml` si besoin

### US2: Dependency Lockfile (P1)

**Approche**:
1. Installer uv
2. Générer `uv.lock` avec `uv lock`
3. Resserrer bornes dans pyproject.toml (`>=x.y,<x+1`)
4. Committer `uv.lock`

**Risques**:
- Conflits de versions → résoudre manuellement

### US3: SSRF Hardening (P2)

**Approche**: Modifier `rekall/connectors/base.py:validate_url()`

```python
# Avant: parsed.netloc
# Après: parsed.hostname + DNS resolution + IP validation
```

**Changements**:
1. Utiliser `parsed.hostname` au lieu de `netloc`
2. Ajouter module `ipaddress` pour validation IP
3. Résoudre DNS et valider IP résultante
4. Bloquer IPv4/IPv6 privées

### US4: TOML Config Robustness (P2)

**Approche**: Migrer vers tomlkit

1. Ajouter dépendance `tomlkit`
2. Remplacer écriture manuelle par `tomlkit.dumps()`
3. Propager exceptions au lieu de `except: return {}`
4. Logger les erreurs clairement

### US5: Embeddings Doc Alignment (P2)

**Approche**:
1. Corriger `docs/getting-started.md`: EmbeddingGemma → all-MiniLM-L6-v2
2. Ajouter extra `[embeddings]` dans pyproject.toml
3. Ajouter message de téléchargement réseau

### US6: LICENSE File (P3)

**Approche**: Créer `LICENSE` à la racine avec texte MIT standard

## Artifacts générés

| Artifact | Chemin | Description |
|----------|--------|-------------|
| Plan | `specs/016-audit-remediation/plan.md` | Ce fichier |
| Research | `specs/016-audit-remediation/research.md` | Décisions techniques |
| Quickstart | `specs/016-audit-remediation/quickstart.md` | Guide développeur |
| CI Contract | `specs/016-audit-remediation/contracts/ci-workflow.yml` | Structure cible CI |

## Prochaine étape

Exécuter `/speckit.tasks` pour générer les tâches d'implémentation.
