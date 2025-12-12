# Research: Audit Remediation v0.3.0

**Date**: 2025-12-12
**Feature**: 016-audit-remediation

## Technical Decisions

### 1. CI/CD Tool Chain

**Decision**: GitHub Actions avec workflow matrix

**Rationale**:
- Intégration native GitHub (annotations, checks, status)
- Gratuit pour repos publics, minutes incluses pour privés
- Écosystème d'actions mature (setup-python, astral-sh/setup-uv)

**Alternatives considérées**:
- GitLab CI: Nécessite migration, pas de valeur ajoutée
- CircleCI/Travis: Dépendance externe, coût supplémentaire

**Sources**:
- [GitHub Actions Python CI](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [A Github Actions setup for Python projects in 2025](https://ber2.github.io/posts/2025_github_actions_python/)

---

### 2. Dependency Lock Tool

**Decision**: **uv** (Astral)

**Rationale**:
- 10-100x plus rapide que pip/poetry
- Compatible pyproject.toml natif (PEP 621)
- Même éditeur que ruff (déjà utilisé)
- Lockfile `uv.lock` avec résolution déterministe
- Support `uv pip compile` pour requirements.txt si besoin

**Alternatives considérées**:
- poetry: Plus mature mais plus lent, format propriétaire
- pip-tools: Minimaliste mais moins de features (pas de venv intégré)

**Sources**:
- [uv documentation](https://docs.astral.sh/uv/)
- [astral-sh/setup-uv action](https://github.com/astral-sh/setup-uv)

---

### 3. Security Scanning Tools

**Decision**: pip-audit + gitleaks

**Rationale**:
- **pip-audit** (PyPA): Scan CVE officiel, base PyPI Advisory Database
- **gitleaks**: Standard industrie pour secrets, rapide, configurable

**Configuration pip-audit**:
```yaml
- uses: pypa/gh-action-pip-audit@v1.1.0
  with:
    inputs: uv.lock
    require-hashes: true
```

**Configuration gitleaks**:
```yaml
- uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

**Sources**:
- [pip-audit](https://github.com/pypa/pip-audit)
- [gitleaks-action](https://github.com/gitleaks/gitleaks-action)

---

### 4. SSRF Hardening Strategy

**Decision**: Validation multi-couches avec résolution DNS

**Rationale**:
- **Couche 1**: Parse URL avec `urllib.parse`, utiliser `hostname` (pas `netloc`)
- **Couche 2**: Valider contre patterns (userinfo, schéma non-http/https)
- **Couche 3**: Résoudre DNS et valider IP résultante
- **Couche 4**: Bloquer plages privées IPv4/IPv6

**Plages à bloquer**:
```python
PRIVATE_IPV4 = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # link-local
]
PRIVATE_IPV6 = [
    ipaddress.ip_network("::1/128"),         # loopback
    ipaddress.ip_network("fc00::/7"),        # unique local
    ipaddress.ip_network("fe80::/10"),       # link-local
]
```

**Sources**:
- [OWASP SSRF Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)

---

### 5. TOML Serialization Library

**Decision**: **tomlkit**

**Rationale**:
- Préserve les commentaires (contrairement à tomli-w)
- Round-trip editing (lecture + modification + écriture)
- Gestion correcte de tous types TOML (arrays, inline tables, etc.)
- Déjà utilisé par poetry

**Alternatives considérées**:
- tomli-w: Write-only, perd les commentaires
- toml: Deprecated, remplacé par tomllib stdlib

**Sources**:
- [tomlkit documentation](https://tomlkit.readthedocs.io/)

---

### 6. Python Version Matrix

**Decision**: Python 3.10, 3.11, 3.12, 3.13

**Rationale**:
- 3.10: Version minimale (match, pattern matching)
- 3.11: Performance boost significatif
- 3.12: Version stable actuelle
- 3.13: Dernière version, free-threading preview

**Sources**:
- [Python Release Schedule](https://devguide.python.org/versions/)

---

## Resolved Questions

| Question | Decision | Rationale |
|----------|----------|-----------|
| Outil de lock | uv | Moderne, rapide, compatible Astral |
| CI platform | GitHub Actions | Native, gratuit, mature |
| Secret scanning | gitleaks | Standard industrie |
| CVE scanning | pip-audit | Officiel PyPA |
| TOML library | tomlkit | Round-trip, préserve commentaires |
| Python versions | 3.10-3.13 | Couverture large |
