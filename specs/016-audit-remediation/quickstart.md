# Quickstart: Audit Remediation

## Résumé des changements

Cette feature corrige les issues identifiées dans l'audit v0.3.0 (score B-).

## Fichiers à créer/modifier

### Nouveaux fichiers

| Fichier | Description |
|---------|-------------|
| `.github/workflows/ci.yml` | Pipeline CI principal |
| `uv.lock` | Lockfile des dépendances |
| `LICENSE` | Licence MIT |

### Fichiers à modifier

| Fichier | Changements |
|---------|-------------|
| `pyproject.toml` | Bornes versions + extra `[embeddings]` |
| `rekall/connectors/base.py` | Hardening SSRF validate_url() |
| `rekall/config.py` | Migration vers tomlkit |
| `docs/getting-started.md` | Correction doc embeddings |

## Commandes de développement

```bash
# Installer uv (si pas déjà fait)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Générer le lockfile
uv lock

# Installer les dépendances
uv sync

# Installer avec extras embeddings
uv sync --extra embeddings

# Lancer les tests
uv run pytest

# Lancer le linting
uv run ruff check .

# Audit sécurité local
uv run pip-audit
```

## Vérification locale avant push

```bash
# Simuler le CI localement
uv run pytest -q
uv run ruff check --output-format=github .
uv run pip-audit
```

## Structure CI

```yaml
# .github/workflows/ci.yml
jobs:
  test:      # pytest matrix 3.10-3.13
  lint:      # ruff check
  security:  # pip-audit + gitleaks
```
