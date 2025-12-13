# Feature Specification: Architecture Open Core

**Feature Branch**: `022-open-core`
**Created**: 2025-12-13
**Status**: Draft
**Input**: User description: "Architecture Open Core: interfaces abstraites pour séparer Home (repo public) et Server (repo privé) sans fork"

## Research Findings

### Modèle Open Core validé

Sources consultées :
- [Open Core Model - TechTarget](https://www.techtarget.com/searchitoperations/definition/open-core-model-open-core-software)
- [Open Core Model - Wikipedia](https://en.wikipedia.org/wiki/Open-core_model)
- [Plugin Architecture in Python](https://alysivji.com/simple-plugin-system.html)

**Patterns validés** :
- Le modèle Open Core est utilisé par Odoo (30 modules core + milliers de modules community/paid)
- L'Adapter Pattern combiné à une architecture plugin permet une séparation des préoccupations claire
- La clé : interfaces abstraites dans le core, implémentations concrètes swappables

**Red flags évités** :
- Pas de vendor lock-in : les interfaces sont dans le repo public
- Pas de dépendance inverse : le privé dépend du public, jamais l'inverse
- Documentation claire des failure modes via les interfaces abstraites

---

## Contexte & Objectif

Rekall est actuellement un outil monolithique optimisé pour usage personnel (Home). L'objectif est de préparer une architecture permettant :

1. **Repo Public (rekall)** : Version "Home" pour développeurs individuels
2. **Repo Privé (rekall-server)** : Version "Server" avec backends scalables

Sans jamais créer de fork ni de duplication de code.

### Contraintes architecturales

| Contrainte | Exigence |
|------------|----------|
| Direction des dépendances | `rekall-server` → `rekall` (jamais l'inverse) |
| Impact utilisateur Home | ZÉRO changement de comportement |
| Overhead de code | Maximum ~300 lignes d'interfaces |
| Temps de refactoring | 2-3 jours maximum |

---

## User Scenarios & Testing

### User Story 1 - Utilisateur Home standard (Priority: P1)

Un développeur utilise rekall comme aujourd'hui, sans aucun changement visible. L'introduction des interfaces abstraites est transparente.

**Why this priority**: C'est le cas d'usage principal. 95% des utilisateurs sont en mode Home. Aucune régression n'est acceptable.

**Independent Test**: Installation standard de rekall (`uv pip install rekall`) et utilisation de toutes les commandes MCP sans configuration supplémentaire.

**Acceptance Scenarios**:

1. **Given** un utilisateur avec rekall installé, **When** il exécute `rekall search "query"`, **Then** les résultats s'affichent comme avant (même vitesse, même format)
2. **Given** un utilisateur sans fichier de configuration, **When** rekall démarre, **Then** les backends par défaut (SQLite, cache local) sont utilisés automatiquement
3. **Given** un utilisateur qui met à jour rekall, **When** il relance ses commandes habituelles, **Then** tout fonctionne sans migration ni configuration

---

### User Story 2 - Opérateur Server avec backends par défaut (Priority: P2)

Un opérateur installe `rekall-server` pour déployer une instance multi-utilisateurs. Au premier lancement, les backends par défaut (SQLite, cache local) fonctionnent immédiatement.

**Why this priority**: Première étape vers le mode Server. Doit fonctionner out-of-the-box avant toute optimisation.

**Independent Test**: Installation de `rekall-server` et lancement d'une instance accessible via API, sans configuration de Redis/PostgreSQL.

**Acceptance Scenarios**:

1. **Given** rekall-server installé, **When** l'opérateur lance le serveur sans config, **Then** le serveur démarre avec les backends par défaut
2. **Given** un serveur en mode défaut, **When** 10 utilisateurs accèdent simultanément, **Then** le système fonctionne (avec performances limitées attendues)

---

### User Story 3 - Opérateur Server avec backends optimisés (Priority: P3)

Un opérateur configure des backends optimisés (Redis pour le cache, pool de connexions pour la DB) via le fichier de configuration.

**Why this priority**: Optimisation optionnelle. Nécessite que P1 et P2 fonctionnent d'abord.

**Independent Test**: Configuration d'un backend Redis et vérification que le cache utilise Redis au lieu du cache local.

**Acceptance Scenarios**:

1. **Given** rekall-server avec `cache_backend = "redis"` dans la config, **When** le serveur démarre, **Then** le cache utilise Redis
2. **Given** un backend Redis configuré, **When** le serveur redémarre, **Then** le cache persiste (test de survie au redémarrage)
3. **Given** une erreur de connexion Redis, **When** le serveur démarre, **Then** un message d'erreur clair indique le problème de configuration

---

### Edge Cases

- **Backend mal configuré au démarrage** : Redis configuré mais indisponible ?
  - Comportement attendu : Erreur claire au démarrage, pas de fallback silencieux
- **Backend indisponible pendant l'exécution** : Connexion perdue en cours d'opération ?
  - Comportement attendu : Retry with backoff (3 tentatives, délai exponentiel), puis erreur propagée à l'appelant
- **Migration Home → Server** : Un utilisateur Home veut passer en Server
  - Comportement attendu : Ses données SQLite restent compatibles, migration documentée
- **Plugin incompatible** : Un plugin Server utilise une API dépréciée
  - Comportement attendu : Erreur explicite avec version minimale requise

---

## Requirements

### Functional Requirements - Repo Home (rekall)

- **FR-H01**: Le système DOIT définir une interface abstraite `DatabaseBackend` avec les méthodes essentielles (connect, execute, fetch)
- **FR-H02**: Le système DOIT définir une interface abstraite `CacheBackend` avec les méthodes essentielles (get, set, delete, clear)
- **FR-H03**: Le système DOIT fournir un conteneur de services (`ServiceContainer`) permettant d'enregistrer et récupérer les backends
- **FR-H04**: Le système DOIT fournir des implémentations par défaut (SQLite, cache local) compatibles avec les interfaces
- **FR-H05**: Les fichiers existants (db.py, cache.py) DOIVENT continuer à fonctionner sans modification pour les utilisateurs Home
- **FR-H06**: Le système DOIT permettre l'enregistrement de backends personnalisés via `register_backend(name, implementation)`
- **FR-H07**: Le système DOIT supporter un mode debug optionnel (`debug = true` dans config) pour activer le logging détaillé des opérations backend

### Functional Requirements - Repo Server (rekall-server)

- **FR-S01**: Le package DOIT déclarer rekall comme dépendance (`rekall >= X.Y.Z`)
- **FR-S02**: Le système DOIT fournir une implémentation `PooledDatabaseBackend` utilisant un pool de connexions
- **FR-S03**: Le système DOIT fournir une implémentation `RedisCacheBackend` utilisant Redis
- **FR-S04**: Le système DOIT enregistrer automatiquement ses backends au démarrage via le hook d'extension
- **FR-S05**: Le système DOIT pouvoir servir l'API MCP via FastMCP/FastAPI
- **FR-S06**: La configuration DOIT se faire via fichier TOML ou variables d'environnement

### Key Entities

- **ServiceContainer**: Registre central des backends, point d'accès unique aux services
- **DatabaseBackend (ABC)**: Interface abstraite pour tous les backends de base de données
- **CacheBackend (ABC)**: Interface abstraite pour tous les backends de cache
- **DefaultDatabaseBackend**: Implémentation SQLite actuelle, adaptée pour implémenter l'interface
- **DefaultCacheBackend**: Implémentation cache local actuelle, adaptée pour implémenter l'interface

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Tous les tests existants de rekall passent sans modification après l'introduction des interfaces
- **SC-002**: Le temps de démarrage de rekall en mode Home ne dépasse pas 50ms de plus qu'avant
- **SC-003**: Un développeur peut créer et enregistrer un backend personnalisé en moins de 50 lignes de code
- **SC-004**: La documentation du système de plugins permet à un développeur de créer un backend en moins de 30 minutes
- **SC-005**: rekall-server peut gérer 100 requêtes concurrentes avec les backends optimisés

---

## Architecture Proposée

### Structure des repos

```
rekall/ (repo public)
├── rekall/
│   ├── infra/
│   │   ├── __init__.py
│   │   ├── interfaces.py      # ABC: DatabaseBackend, CacheBackend
│   │   ├── container.py       # ServiceContainer
│   │   └── defaults.py        # Implémentations par défaut
│   ├── db.py                  # Utilise get_database() du container
│   └── cache.py               # Utilise get_cache() du container (déjà fait)

rekall-server/ (repo privé)
├── rekall_server/
│   ├── backends/
│   │   ├── pooled_db.py       # PooledDatabaseBackend
│   │   └── redis_cache.py     # RedisCacheBackend
│   └── server.py              # FastMCP + enregistrement backends
└── pyproject.toml             # dépend de rekall
```

### Flux de dépendances

```
┌──────────────────────────────────────────────────┐
│                rekall-server                      │
│  (repo privé - backends optimisés)                │
│                                                  │
│  ┌─────────────┐  ┌──────────────────┐          │
│  │PooledDB     │  │ RedisCacheBackend│          │
│  │Backend      │  │                  │          │
│  └──────┬──────┘  └────────┬─────────┘          │
│         │ implements       │ implements         │
└─────────┼──────────────────┼────────────────────┘
          │                  │
          ▼                  ▼
┌──────────────────────────────────────────────────┐
│                    rekall                         │
│  (repo public - interfaces + defaults)            │
│                                                  │
│  ┌─────────────┐  ┌──────────────────┐          │
│  │DatabaseBack │  │ CacheBackend     │  ← ABC   │
│  │end (ABC)    │  │ (ABC)            │          │
│  └──────┬──────┘  └────────┬─────────┘          │
│         │ default impl     │ default impl       │
│         ▼                  ▼                    │
│  ┌─────────────┐  ┌──────────────────┐          │
│  │SQLite       │  │ Local Cache      │          │
│  │Backend      │  │ Backend          │          │
│  └─────────────┘  └──────────────────┘          │
└──────────────────────────────────────────────────┘
```

---

## Assumptions

- Python 3.10+ est requis (déjà le cas)
- Le pattern singleton avec getter (`get_cache()`) déjà utilisé sera étendu à la database
- Les ABC (Abstract Base Classes) de Python seront utilisées pour définir les interfaces
- La configuration se fera via `config.toml` existant avec de nouvelles sections optionnelles
- Aucun changement de schéma de base de données n'est nécessaire
- **Versioning des interfaces** : Semver strict avec dépréciation (warnings pendant 2 versions majeures avant tout breaking change)

---

## Out of Scope

- Implémentation de backends PostgreSQL, MySQL
- Système de migration de données Home → Server
- Interface d'administration web pour le Server
- Système de queue (RabbitMQ, Celery) - prévu pour une phase ultérieure
- Authentification et autorisation multi-utilisateurs

---

## Clarifications

### Session 2025-12-13

- Q: Gestion des pannes de backend pendant l'exécution → A: Retry with backoff (3 tentatives avec délai exponentiel, puis erreur)
- Q: Observabilité pour la version Home → A: Optionnel via config (désactivé par défaut, activable via `debug = true`)
- Q: Stratégie de versioning des interfaces → A: Semver + deprecation (warnings pendant 2 versions majeures avant breaking change)

---

## Risks & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Régression sur les tests existants | Faible | Critique | Exécuter tous les tests après chaque modification |
| Overhead de performance | Faible | Moyen | Profiling avant/après, limite de 50ms |
| Complexité excessive des interfaces | Moyen | Moyen | Limiter à 2 interfaces (DB, Cache), itérer ensuite |
| Breaking changes pour les utilisateurs | Faible | Critique | Pas de changement d'API publique |
