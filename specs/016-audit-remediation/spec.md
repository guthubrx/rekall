# Feature Specification: Audit Remediation v0.3.0

**Feature Branch**: `016-audit-remediation`
**Created**: 2025-12-12
**Status**: Draft
**Input**: Corrections issues from security/quality audit v0.3.0. Score global B- avec lacunes CI/supply-chain et incohérences produit-doc.

## Research Findings

Sources consultées:
- [GitHub Actions Python CI - GitHub Docs](https://docs.github.com/en/actions/tutorials/build-and-test-code/python)
- [pip-audit - PyPA](https://github.com/pypa/pip-audit)
- [SSRF Prevention - OWASP Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP Top 10 2025](https://juanrodriguezmonti.github.io/blog/owasp-top-10-2025/)

**Best practices identifiées:**
- CI moderne avec uv/ruff/pytest/pip-audit
- Validation URL SSRF: utiliser `parsed.hostname` (pas `netloc`), bloquer IP privées IPv4/IPv6
- Lockfile obligatoire pour reproductibilité

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CI Pipeline Setup (Priority: P1)

En tant que mainteneur du projet, je veux que chaque push/PR déclenche automatiquement les tests, le linting et l'audit de sécurité des dépendances, afin de détecter les régressions et vulnérabilités avant merge.

**Why this priority**: Score D en CI/CD - aucune automatisation actuellement. Bloque la détection de régressions et vulnérabilités.

**Independent Test**: Créer une PR avec un bug ou une dépendance vulnérable et vérifier que le CI échoue.

**Acceptance Scenarios**:

1. **Given** un push sur main ou une PR ouverte, **When** GitHub Actions se déclenche, **Then** les tests pytest s'exécutent sur Python 3.10-3.13
2. **Given** du code avec des violations ruff, **When** le CI s'exécute, **Then** le job lint échoue avec annotations GitHub
3. **Given** une dépendance avec CVE connue, **When** pip-audit s'exécute, **Then** le job échoue et affiche la CVE
4. **Given** un secret dans le code, **When** gitleaks s'exécute, **Then** le job échoue

---

### User Story 2 - Dependency Lockfile (Priority: P1)

En tant que développeur, je veux un fichier de verrouillage des dépendances pour garantir des builds reproductibles et éviter les surprises lors des mises à jour transitives.

**Why this priority**: Score D supply-chain - versions `>=` trop larges, pas de lockfile. Risque de CVE via update transitive.

**Independent Test**: Installer le projet sur deux machines différentes et vérifier que les versions exactes sont identiques.

**Acceptance Scenarios**:

1. **Given** pyproject.toml avec dépendances, **When** je génère le lockfile, **Then** toutes les versions transitives sont pinnées
2. **Given** un lockfile existant, **When** j'installe les dépendances, **Then** les versions correspondent exactement au lock
3. **Given** une nouvelle dépendance ajoutée, **When** je mets à jour le lockfile, **Then** seule cette dépendance et ses transitives changent

---

### User Story 3 - SSRF Hardening (Priority: P2)

En tant qu'utilisateur, je veux que les URLs fournies aux connecteurs/enrichment soient validées de manière robuste pour éviter les requêtes vers des hôtes internes non autorisés.

**Why this priority**: Vulnérabilité SSRF soft identifiée - bypass possible via userinfo dans netloc ou IPv6 privées.

**Independent Test**: Tenter d'accéder à `https://localhost@evil.com/`, `http://127.0.0.1.nip.io/`, `http://[::1]/` et vérifier le rejet.

**Acceptance Scenarios**:

1. **Given** une URL avec userinfo `https://localhost@evil.com/`, **When** je la valide, **Then** elle est rejetée
2. **Given** une URL pointant vers une IP privée IPv4 (10.x, 172.16-31.x, 192.168.x, 127.x), **When** je la valide, **Then** elle est rejetée
3. **Given** une URL pointant vers une IP privée IPv6 (::1, fc00::/7, fe80::/10), **When** je la valide, **Then** elle est rejetée
4. **Given** une URL DNS rebinding (127.0.0.1.nip.io), **When** je la résous et valide l'IP, **Then** elle est rejetée

---

### User Story 4 - TOML Config Robustness (Priority: P2)

En tant qu'utilisateur, je veux que les erreurs de configuration TOML soient signalées clairement plutôt que ignorées silencieusement.

**Why this priority**: Config TOML fragile - exceptions avalées, écriture manuelle fragile.

**Independent Test**: Créer un fichier TOML malformé et vérifier qu'un message d'erreur clair est affiché.

**Acceptance Scenarios**:

1. **Given** un fichier TOML avec syntaxe invalide, **When** je charge la config, **Then** un message d'erreur explicite est affiché
2. **Given** une valeur avec caractères spéciaux (guillemets, backslash), **When** je sauvegarde la config, **Then** l'échappement TOML est correct
3. **Given** une liste ou un dict complexe, **When** je sauvegarde la config, **Then** le format TOML est valide

---

### User Story 5 - Embeddings Documentation Alignment (Priority: P2)

En tant qu'utilisateur, je veux que la documentation reflète correctement le modèle d'embeddings utilisé et que les dépendances soient clairement déclarées.

**Why this priority**: Incohérence docs/code - doc mentionne EmbeddingGemma, code utilise all-MiniLM-L6-v2.

**Independent Test**: Suivre la doc et vérifier que le modèle mentionné correspond au comportement réel.

**Acceptance Scenarios**:

1. **Given** la documentation embeddings, **When** je la lis, **Then** le modèle mentionné correspond au code
2. **Given** pyproject.toml, **When** j'installe avec `[embeddings]` extra, **Then** sentence-transformers et numpy sont installés
3. **Given** embeddings activés, **When** le modèle n'est pas téléchargé, **Then** un message clair indique le téléchargement réseau à venir

---

### User Story 6 - LICENSE File (Priority: P3)

En tant que contributeur ou utilisateur, je veux un fichier LICENSE à la racine du projet pour clarifier les droits d'utilisation.

**Why this priority**: Conformité - LICENSE non présent à la racine malgré MIT déclaré dans pyproject.toml.

**Independent Test**: Vérifier que le fichier LICENSE existe à la racine et contient le texte MIT.

**Acceptance Scenarios**:

1. **Given** le projet cloné, **When** je cherche LICENSE, **Then** il existe à la racine
2. **Given** le fichier LICENSE, **When** je le lis, **Then** il contient la licence MIT avec l'année et le titulaire corrects

---

### Edge Cases

- Que se passe-t-il si le CI échoue à cause d'un timeout réseau pip-audit ?
- Comment gérer une URL valide qui résout vers une IP privée après DNS rebinding ?
- Que faire si le lockfile devient corrompu ?
- Comment migrer les utilisateurs existants sans lockfile vers la nouvelle structure ?

## Requirements *(mandatory)*

### Functional Requirements

**CI/CD (US1):**
- **FR-001**: Le projet DOIT avoir un workflow GitHub Actions exécuté sur push/PR
- **FR-002**: Le CI DOIT exécuter pytest sur une matrice Python 3.10, 3.11, 3.12, 3.13
- **FR-003**: Le CI DOIT exécuter ruff check avec annotations GitHub
- **FR-004**: Le CI DOIT exécuter pip-audit pour détecter les CVE
- **FR-005**: Le CI DOIT exécuter gitleaks pour détecter les secrets

**Supply Chain (US2):**
- **FR-006**: Le projet DOIT utiliser **uv** comme outil de lock (lockfile `uv.lock`)
- **FR-007**: Le lockfile `uv.lock` DOIT être committé et versionné
- **FR-008**: Les versions dans pyproject.toml DOIVENT avoir des bornes supérieures (`>=x,<y`)

**Sécurité (US3):**
- **FR-009**: La validation d'URL DOIT utiliser `parsed.hostname` au lieu de `parsed.netloc`
- **FR-010**: La validation DOIT bloquer les plages IP privées IPv4 (10/8, 172.16/12, 192.168/16, 127/8)
- **FR-011**: La validation DOIT bloquer les plages IP privées IPv6 (::1, fc00::/7, fe80::/10)
- **FR-012**: La validation DOIT résoudre le DNS et vérifier l'IP résultante

**Configuration (US4):**
- **FR-013**: Les erreurs de parsing TOML DOIVENT être signalées à l'utilisateur
- **FR-014**: L'écriture TOML DOIT utiliser une bibliothèque (tomlkit) pour l'échappement correct

**Documentation (US5):**
- **FR-015**: La doc embeddings DOIT mentionner le modèle réellement utilisé (all-MiniLM-L6-v2)
- **FR-016**: pyproject.toml DOIT déclarer un extra `[embeddings]` avec sentence-transformers et numpy

**Conformité (US6):**
- **FR-017**: Un fichier LICENSE MIT DOIT exister à la racine du projet

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Le CI s'exécute en moins de 5 minutes pour les cas standards
- **SC-002**: 100% des PRs passent par le CI avant merge
- **SC-003**: Les builds sont reproductibles - même lockfile = mêmes versions installées
- **SC-004**: Aucune URL avec IP privée ne passe la validation (0% faux négatifs)
- **SC-005**: Les erreurs de config TOML affichent un message compréhensible dans 100% des cas
- **SC-006**: La documentation embeddings correspond au comportement réel (0 incohérence)
- **SC-007**: Score audit passe de D à B+ minimum pour CI/CD après implémentation

## Clarifications

### Session 2025-12-12

- Q: Quel outil de lock utiliser pour le projet ? → A: **uv** (moderne, rapide, compatible ruff/Astral)
