# Feature Specification: MCP Tools Expansion

**Feature Branch**: `015-mcp-tools-expansion`
**Created**: 2025-12-12
**Status**: Draft
**Input**: Extension des outils MCP avec P1 (unlink, related, similar, sources_suggest) et P3 (generalize, stale, info, sources_verify)

## Context

Le serveur MCP de rekall expose actuellement 7 outils :
- `rekall_help` : Guide d'utilisation
- `rekall_search` : Recherche dans la base
- `rekall_show` : Afficher une entrée
- `rekall_add` : Ajouter une entrée
- `rekall_link` : Créer un lien
- `rekall_suggest` : Suggestions de liens
- `rekall_get_context` : Récupérer le contexte

Cette feature ajoute 8 nouveaux outils pour compléter la couverture fonctionnelle.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Supprimer un lien via MCP (Priority: P1)

En tant qu'agent IA utilisant rekall, je veux pouvoir supprimer un lien erroné entre deux entrées pour corriger le graphe de connaissances.

**Why this priority**: L'outil `rekall_link` existe mais sans possibilité de correction. Critique pour la maintenance du graphe.

**Independent Test**: Appeler `rekall_unlink(source_id, target_id)` sur un lien existant et vérifier sa suppression.

**Acceptance Scenarios**:

1. **Given** un lien existe entre A et B, **When** `rekall_unlink(A, B)` est appelé, **Then** le lien est supprimé et un message de confirmation est retourné
2. **Given** aucun lien n'existe entre A et B, **When** `rekall_unlink(A, B)` est appelé, **Then** un message d'erreur explicite est retourné

---

### User Story 2 - Explorer le graphe de connaissances (Priority: P1)

En tant qu'agent IA, je veux explorer les entrées reliées à une entrée donnée pour comprendre le contexte et les dépendances.

**Why this priority**: Essentiel pour la navigation dans le graphe et la découverte de connaissances connexes.

**Independent Test**: Appeler `rekall_related(entry_id)` et vérifier que les entrées liées (entrantes/sortantes) sont retournées.

**Acceptance Scenarios**:

1. **Given** une entrée A avec liens vers B et C, **When** `rekall_related(A)` est appelé, **Then** B et C sont retournées avec leur type de relation
2. **Given** une entrée A sans liens, **When** `rekall_related(A)` est appelé, **Then** un message indique qu'aucune entrée reliée n'existe
3. **Given** une entrée A, **When** `rekall_related(A, depth=2)` est appelé, **Then** les entrées à 2 niveaux de profondeur sont retournées

---

### User Story 3 - Trouver des entrées similaires (Priority: P1)

En tant qu'agent IA, je veux trouver les entrées sémantiquement similaires à une entrée donnée pour éviter les doublons et découvrir des patterns.

**Why this priority**: Complémente `rekall_search` pour la découverte basée sur le contenu plutôt que les mots-clés.

**Independent Test**: Appeler `rekall_similar(entry_id)` et vérifier que des entrées avec scores de similarité sont retournées.

**Acceptance Scenarios**:

1. **Given** une entrée A avec embeddings calculés, **When** `rekall_similar(A)` est appelé, **Then** les entrées les plus similaires sont retournées avec scores
2. **Given** les embeddings ne sont pas activés, **When** `rekall_similar(A)` est appelé, **Then** un message indique que la fonctionnalité nécessite les embeddings

---

### User Story 4 - Suggérer des sources pour une entrée (Priority: P1)

En tant qu'agent IA, je veux obtenir des suggestions de sources web pour enrichir une entrée avec des références.

**Why this priority**: Intégration avec le système Sources Medallion (Feature 013). Améliore la qualité des entrées.

**Independent Test**: Appeler `rekall_sources_suggest(entry_id)` et vérifier que des sources pertinentes (staging/gold) sont suggérées.

**Acceptance Scenarios**:

1. **Given** une entrée sur "nginx timeout", **When** `rekall_sources_suggest(entry_id)` est appelé, **Then** des sources web pertinentes sur nginx sont suggérées
2. **Given** aucune source pertinente n'existe, **When** `rekall_sources_suggest(entry_id)` est appelé, **Then** un message indique qu'aucune source n'a été trouvée

---

### User Story 5 - Statistiques de la base (Priority: P3)

En tant qu'agent IA, je veux obtenir des statistiques sur la base de connaissances pour contextualiser mes réponses.

**Why this priority**: Utile mais pas critique pour les opérations principales.

**Independent Test**: Appeler `rekall_info()` et vérifier que les statistiques (nombre d'entrées, types, projets) sont retournées.

**Acceptance Scenarios**:

1. **Given** une base avec 100 entrées, **When** `rekall_info()` est appelé, **Then** le nombre total, la répartition par type/projet, et les stats de liens sont retournés

---

### User Story 6 - Trouver les entrées obsolètes (Priority: P3)

En tant qu'agent IA, je veux identifier les entrées qui n'ont pas été consultées depuis longtemps pour proposer une maintenance.

**Why this priority**: Fonctionnalité de maintenance, pas critique pour les opérations quotidiennes.

**Independent Test**: Appeler `rekall_stale(days=90)` et vérifier que les entrées non accédées depuis 90 jours sont retournées.

**Acceptance Scenarios**:

1. **Given** des entrées non consultées depuis 90+ jours, **When** `rekall_stale(days=90)` est appelé, **Then** ces entrées sont listées avec leur date de dernier accès
2. **Given** toutes les entrées sont récentes, **When** `rekall_stale(days=90)` est appelé, **Then** un message indique qu'aucune entrée obsolète n'existe

---

### User Story 7 - Créer une généralisation (Priority: P3)

En tant qu'agent IA, je veux pouvoir créer une entrée générique à partir de plusieurs entrées similaires pour consolider les connaissances.

**Why this priority**: Fonctionnalité avancée de curation, CLI `rekall generalize` existe déjà.

**Independent Test**: Appeler `rekall_generalize(entry_ids=[A, B, C])` et vérifier qu'une nouvelle entrée est créée avec liens "derived_from".

**Acceptance Scenarios**:

1. **Given** trois entrées similaires sur des bugs nginx, **When** `rekall_generalize([A, B, C], title="Pattern nginx timeout")` est appelé, **Then** une nouvelle entrée pattern est créée avec liens vers A, B, C
2. **Given** moins de 2 entrées fournies, **When** `rekall_generalize` est appelé, **Then** une erreur indique qu'il faut au moins 2 entrées

---

### User Story 8 - Vérifier les sources (link rot) (Priority: P3)

En tant qu'agent IA, je veux vérifier si les URLs dans les sources sont encore accessibles pour maintenir la qualité des références.

**Why this priority**: Maintenance de qualité, la CLI `rekall sources verify` existe déjà.

**Independent Test**: Appeler `rekall_sources_verify()` et obtenir le statut des URLs vérifiées.

**Acceptance Scenarios**:

1. **Given** des sources avec URLs, **When** `rekall_sources_verify(limit=10)` est appelé, **Then** le statut (accessible/broken) de chaque URL est retourné
2. **Given** des URLs cassées détectées, **When** le résultat est retourné, **Then** les URLs cassées sont clairement identifiées pour correction

---

### Edge Cases

- Que se passe-t-il si `rekall_similar` est appelé sans embeddings activés ? → Message explicite indiquant la configuration requise
- Que se passe-t-il si `rekall_unlink` est appelé avec des IDs invalides ? → Message d'erreur avec les IDs non trouvés
- Comment gérer les timeouts lors de `rekall_sources_verify` ? → Timeout de 10s par URL, marquer comme "timeout"
- Que faire si `rekall_generalize` est appelé avec des entrées non reliées ? → Avertissement mais création autorisée

## Requirements *(mandatory)*

### Functional Requirements

**P1 - Priorité haute**

- **FR-001**: `rekall_unlink` DOIT supprimer un lien existant entre deux entrées
- **FR-002**: `rekall_unlink` DOIT retourner une erreur si le lien n'existe pas
- **FR-003**: `rekall_related` DOIT retourner les entrées liées (entrantes et sortantes)
- **FR-004**: `rekall_related` DOIT supporter un paramètre `depth` pour la profondeur de traversée
- **FR-005**: `rekall_similar` DOIT retourner les entrées sémantiquement similaires avec scores
- **FR-006**: `rekall_similar` DOIT gérer gracieusement l'absence d'embeddings
- **FR-007**: `rekall_sources_suggest` DOIT suggérer des sources pertinentes basées sur le contenu de l'entrée

**P3 - Priorité basse**

- **FR-008**: `rekall_info` DOIT retourner les statistiques de la base (entrées, types, projets, liens)
- **FR-009**: `rekall_stale` DOIT retourner les entrées non accédées depuis N jours
- **FR-010**: `rekall_generalize` DOIT créer une entrée générique avec liens "derived_from"
- **FR-011**: `rekall_sources_verify` DOIT vérifier l'accessibilité des URLs et retourner les statuts

### Key Entities

- **Link**: Relation entre deux entrées (existe déjà)
- **Embedding**: Vecteur sémantique pour similarité (existe déjà)
- **Source**: URL avec métadonnées et statut de validité (existe déjà, Feature 013)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les 8 nouveaux outils sont listés par `list_tools()` du serveur MCP
- **SC-002**: Chaque outil retourne une réponse en moins de 2 secondes (sauf `sources_verify`)
- **SC-003**: Les outils P1 (unlink, related, similar, sources_suggest) fonctionnent sans configuration supplémentaire
- **SC-004**: 100% des appels avec paramètres invalides retournent des messages d'erreur explicites
- **SC-005**: `rekall_sources_verify` vérifie au moins 10 URLs en moins de 30 secondes

## Assumptions

- Le serveur MCP existant (`rekall/mcp_server.py`) peut être étendu sans refactoring majeur
- Les fonctions sous-jacentes existent déjà dans `db.py` et `link_rot.py`
- Le système Sources Medallion (Feature 013) est fonctionnel pour `sources_suggest`
- Les embeddings sont optionnels - `similar` dégrade gracieusement sans eux
