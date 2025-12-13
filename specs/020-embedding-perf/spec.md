# Feature Specification: Optimisation Performance Embeddings

**Feature Branch**: `020-embedding-perf`
**Created**: 2025-12-13
**Status**: Draft
**Input**: Optimisation performance Rekall: vectorisation numpy, cache LRU, sqlite-vec, lazy unload

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recherche Sémantique Rapide (Priority: P1)

En tant qu'utilisateur Rekall, je veux que mes recherches sémantiques soient instantanées, même avec des centaines d'entrées dans ma base de connaissances, afin de ne pas interrompre mon flux de travail.

**Why this priority**: La recherche est l'action la plus fréquente. Une recherche lente (>1s) casse l'expérience utilisateur et décourage l'usage.

**Independent Test**: Peut être testé en mesurant le temps de réponse d'une recherche sur une base de 1000 entrées. Valeur immédiate : recherche fluide.

**Acceptance Scenarios**:

1. **Given** une base de 1000 entrées avec embeddings, **When** l'utilisateur lance une recherche sémantique, **Then** les résultats s'affichent en moins de 500ms
2. **Given** une base de 100 entrées, **When** l'utilisateur lance une recherche, **Then** les résultats s'affichent en moins de 100ms
3. **Given** une recherche en cours, **When** une seconde recherche est lancée, **Then** la première est annulée et la seconde s'exécute normalement

---

### User Story 2 - Empreinte Mémoire Réduite (Priority: P2)

En tant qu'utilisateur Rekall sur une machine avec ressources limitées, je veux que l'application consomme moins de mémoire, afin de pouvoir l'utiliser en parallèle d'autres outils de développement.

**Why this priority**: La consommation mémoire impacte l'expérience globale système. Important mais moins critique que la vitesse de recherche.

**Independent Test**: Peut être testé en mesurant la RAM avant/après lancement et pendant utilisation. Valeur : application plus légère.

**Acceptance Scenarios**:

1. **Given** l'application au repos (pas d'action depuis 5 minutes), **When** on mesure la mémoire, **Then** elle est inférieure à 100 MB
2. **Given** une recherche sémantique en cours, **When** on mesure la mémoire, **Then** le pic ne dépasse pas 200 MB
3. **Given** le modèle d'embedding chargé et inactif depuis 10 minutes, **When** on mesure la mémoire, **Then** le modèle a été déchargé

---

### User Story 3 - Scalabilité Future (Priority: P3)

En tant que développeur qui utilise Rekall intensivement, je veux que l'application puisse gérer des dizaines de milliers d'entrées sans dégradation, afin d'accumuler des connaissances sur plusieurs années.

**Why this priority**: Prépare le futur mais n'impacte pas l'usage actuel (bases < 1000 entrées).

**Independent Test**: Peut être testé avec une base synthétique de 10 000 entrées. Valeur : tranquillité long terme.

**Acceptance Scenarios**:

1. **Given** une base de 10 000 entrées, **When** l'utilisateur lance une recherche, **Then** les résultats s'affichent en moins de 1 seconde
2. **Given** une base de 50 000 entrées, **When** l'utilisateur ajoute une nouvelle entrée, **Then** l'indexation se fait en moins de 2 secondes

---

### Edge Cases

- Que se passe-t-il si la base SQLite est corrompue pendant une migration ? → Rollback automatique, conserver backup
- Recherche pendant chargement du modèle → Bloquer avec message "Chargement du modèle en cours"
- sqlite-vec non disponible → Fallback vers recherche brute-force vectorisée numpy

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le système DOIT vectoriser les calculs de similarité pour traiter tous les embeddings en une seule opération
- **FR-002**: Le système DOIT maintenir un cache des embeddings fréquemment utilisés pour éviter les rechargements
- **FR-003**: Le système DOIT utiliser un index vectoriel pour les recherches de similarité
- **FR-004**: Le système DOIT décharger automatiquement le modèle d'embedding après une période d'inactivité
- **FR-005**: Le système DOIT fournir un fallback si l'index vectoriel n'est pas disponible
- **FR-006**: Le système DOIT invalider le cache lorsqu'une entrée est ajoutée, modifiée ou supprimée
- **FR-007**: Le système DOIT être rétrocompatible avec les bases existantes (migration transparente)

### Key Entities

- **EmbeddingCache**: Cache LRU des vecteurs d'embedding avec invalidation sur modification
- **VectorIndex**: Index de recherche vectorielle (sqlite-vec ou fallback brute-force)
- **ModelManager**: Gestionnaire du cycle de vie du modèle sentence-transformers (chargement/déchargement)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les recherches sémantiques sur 1000 entrées s'exécutent en moins de 500ms (actuellement ~2-5s)
- **SC-002**: L'empreinte mémoire au repos est inférieure à 100 MB (actuellement ~150-200 MB avec modèle)
- **SC-003**: Le pic mémoire pendant une recherche ne dépasse pas 200 MB (actuellement ~300 MB)
- **SC-004**: Les recherches sur 10 000 entrées s'exécutent en moins de 1 seconde
- **SC-005**: La migration depuis une base existante se fait sans perte de données
- **SC-006**: Les performances sans sqlite-vec restent acceptables (<1s pour 1000 entrées via fallback vectorisé)

## Assumptions

- Les utilisateurs ont des bases de connaissances de 100 à 10 000 entrées (cas typique)
- La dépendance sqlite-vec peut être optionnelle (fallback nécessaire)
- Le modèle sentence-transformers all-MiniLM-L6-v2 reste le modèle par défaut
- Le timeout d'inactivité pour décharger le modèle est configurable (défaut : 10 minutes)
- La taille du cache LRU est configurable (défaut : 1000 entrées)

## Research Findings

### sqlite-vec vs FAISS (Benchmarks août 2024)

| Outil | Build Time | Query Time (1M vecteurs, k=20) |
|-------|------------|--------------------------------|
| FAISS | 126ms | 10ms |
| sqlite-vec static | 1ms | 17ms |

**Décision**: sqlite-vec recommandé jusqu'à 500K vecteurs. Intégration native SQLite, léger (~2MB), transactions ACID.

**Source**: https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/

## Clarifications

### Session 2025-12-13

- Q: Comment gérer une recherche pendant que le modèle se charge ? → A: Bloquer avec message "Chargement du modèle en cours"

## Out of Scope

- Support GPU pour les embeddings
- Changement du modèle d'embedding par défaut
- Interface de configuration graphique pour les paramètres de performance
- Métriques de performance exposées dans la TUI
