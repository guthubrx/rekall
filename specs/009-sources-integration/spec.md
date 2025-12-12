# Feature Specification: Intégration Souvenirs & Sources Documentaires

**Feature Branch**: `009-sources-integration`
**Created**: 2025-12-10
**Status**: Draft
**Input**: User description: "Intégration souvenirs et sources documentaires avec scoring adaptatif"
**Research**: [docs/research-sources-souvenirs-integration.md](../../docs/research-sources-souvenirs-integration.md)

---

## Résumé Exécutif

Cette feature permet de créer des **liens bidirectionnels** entre les souvenirs Rekall et les sources documentaires Speckit, avec un **système de scoring adaptatif** basé sur l'usage réel. L'objectif est de prioriser automatiquement les sources les plus utiles lors des futures recherches.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lier un Souvenir à ses Sources (Priority: P1)

En tant qu'utilisateur, je veux pouvoir associer une ou plusieurs sources à un souvenir lors de sa création ou après, afin de tracer l'origine de mes connaissances.

**Why this priority**: C'est la fonctionnalité fondamentale qui permet toutes les autres. Sans liaison, pas de tracking d'usage ni de scoring.

**Independent Test**: Créer un souvenir, lui associer une source (thème ou URL), vérifier que le lien est persisté et visible.

**Acceptance Scenarios**:

1. **Given** je crée un nouveau souvenir, **When** j'ajoute une source via le champ optionnel "Sources", **Then** le lien souvenir↔source est enregistré en base
2. **Given** un souvenir existant sans source, **When** je l'édite pour ajouter une source, **Then** le lien est créé et visible dans le détail du souvenir
3. **Given** un souvenir avec sources, **When** je consulte le détail, **Then** je vois la liste des sources liées avec leur type (thème/URL/fichier)

---

### User Story 2 - Voir les Backlinks d'une Source (Priority: P1)

En tant qu'utilisateur, je veux voir tous les souvenirs qui citent une source donnée, afin de comprendre comment j'utilise réellement mes sources.

**Why this priority**: Les backlinks bidirectionnels sont essentiels pour la découverte et le scoring. Cette user story complète la US1.

**Independent Test**: Consulter une source, vérifier qu'elle affiche "Cité par N souvenirs" avec la liste cliquable.

**Acceptance Scenarios**:

1. **Given** une source citée par 3 souvenirs, **When** je consulte cette source, **Then** je vois "Cité par 3 souvenirs" avec les titres
2. **Given** une source jamais citée, **When** je consulte cette source, **Then** je vois "Aucun souvenir lié"
3. **Given** une source avec backlinks, **When** je clique sur un souvenir lié, **Then** je navigue vers le détail de ce souvenir

---

### User Story 3 - Scoring Automatique des Sources (Priority: P2)

En tant qu'utilisateur, je veux que les sources accumulent automatiquement un score basé sur mon usage réel, afin de distinguer mes sources les plus précieuses.

**Why this priority**: Le scoring est la valeur différenciante de cette feature. Il dépend de US1/US2 pour les données d'usage.

**Independent Test**: Citer une source dans plusieurs souvenirs, vérifier que son score augmente et qu'elle remonte dans le classement.

**Acceptance Scenarios**:

1. **Given** une nouvelle source sans usage, **When** je la cite dans un premier souvenir, **Then** son `usage_count` passe à 1 et son score augmente
2. **Given** une source avec usage_count=5, **When** je la cite dans un nouveau souvenir, **Then** son score augmente proportionnellement
3. **Given** une source non utilisée depuis 6 mois, **When** je consulte son score, **Then** il reflète une pénalité de fraîcheur
4. **Given** je consulte la liste des sources, **When** je trie par score, **Then** les sources les plus utilisées récemment sont en tête

---

### User Story 4 - Boost des Recherches Speckit (Priority: P2)

En tant qu'utilisateur, je veux que mes recherches documentaires Speckit priorisent automatiquement mes sources à haut score, afin de trouver l'information pertinente plus rapidement.

**Why this priority**: C'est l'application concrète du scoring - la valeur métier directe.

**Independent Test**: Lancer une recherche sur un thème, vérifier que les sources à haut score apparaissent en premier dans les requêtes suggérées.

**Acceptance Scenarios**:

1. **Given** pinecone.io a un score de 95 et medium.com un score de 15, **When** je recherche "RAG chunking", **Then** la recherche `site:pinecone.io` est suggérée avant `site:medium.com`
2. **Given** une source avec score < 20, **When** je lance une recherche sur son thème, **Then** elle est omise ou déprioritisée des suggestions
3. **Given** le workflow `/speckit.plan`, **When** je démarre une recherche, **Then** les sources sont présentées triées par score personnel

---

### User Story 5 - Dashboard Sources (Priority: P3)

En tant qu'utilisateur, je veux une vue d'ensemble de mes sources avec leurs scores, usages et statuts, afin de gérer mon catalogue de sources.

**Why this priority**: Fonctionnalité de confort et de visualisation, utile mais pas bloquante.

**Independent Test**: Accéder au dashboard, vérifier l'affichage des top sources, sources dormantes, et métriques.

**Acceptance Scenarios**:

1. **Given** j'ai 20 sources enregistrées, **When** j'ouvre le dashboard sources, **Then** je vois les top 10 triées par score
2. **Given** une source non utilisée depuis 6+ mois, **When** j'ouvre le dashboard, **Then** elle apparaît dans "Sources dormantes"
3. **Given** j'ai cité une nouvelle URL 3 fois ce mois, **When** j'ouvre le dashboard, **Then** elle apparaît dans "Sources émergentes" avec suggestion de l'ajouter

---

### User Story 6 - Détection Link Rot (Priority: P3)

En tant qu'utilisateur, je veux être alerté quand une de mes sources n'est plus accessible, afin de maintenir un catalogue de sources valides.

**Why this priority**: Maintenance et qualité des données, importante mais non critique pour le MVP.

**Independent Test**: Ajouter une source avec URL invalide, vérifier que le système détecte et signale le problème.

**Acceptance Scenarios**:

1. **Given** une source avec URL valide, **When** le système vérifie périodiquement, **Then** le statut reste "accessible"
2. **Given** une source dont l'URL retourne 404, **When** le système vérifie, **Then** le statut passe à "inaccessible" avec date de détection
3. **Given** une source inaccessible, **When** je consulte le dashboard, **Then** elle est marquée visuellement avec un avertissement

---

### Edge Cases

- **Suppression d'un souvenir** : Les liens vers ses sources sont supprimés (CASCADE), mais les sources conservent leur score historique
- **Source citée par URL puis par thème** : Les deux types de liens sont distincts et comptabilisés séparément
- **URL avec variantes** (http/https, www/sans www) : Normalisation automatique pour éviter les doublons
- **Thème research inexistant** : Validation que le thème existe dans `~/.speckit/research/`
- **Score négatif impossible** : Le score minimum est 0, pas de valeur négative
- **Première utilisation** : Si aucune source n'existe, le système fonctionne sans erreur

---

## Requirements *(mandatory)*

### Functional Requirements

#### Modèle de Données

- **FR-001**: Le système DOIT persister les liens souvenir↔source dans une table dédiée avec type (theme/url/file), référence, et note optionnelle
- **FR-002**: Le système DOIT persister les métadonnées des sources (domaine, score, usage_count, last_used, reliability, decay_rate)
- **FR-003**: Le système DOIT supprimer automatiquement les liens quand un souvenir est supprimé (intégrité référentielle)

#### Liaison Souvenir↔Source

- **FR-004**: Les utilisateurs DOIVENT pouvoir ajouter une ou plusieurs sources lors de la création d'un souvenir
- **FR-005**: Les utilisateurs DOIVENT pouvoir ajouter/modifier/supprimer les sources d'un souvenir existant
- **FR-006**: Le système DOIT supporter 3 types de sources : thème research, URL externe, fichier local
- **FR-007**: Les utilisateurs DOIVENT pouvoir ajouter une note contextuelle à chaque lien (ex: "Section sur chunking")

#### Backlinks

- **FR-008**: Le système DOIT afficher le nombre de souvenirs citant une source
- **FR-009**: Le système DOIT permettre de naviguer d'une source vers ses souvenirs liés
- **FR-010**: Le système DOIT permettre de naviguer d'un souvenir vers ses sources liées

#### Scoring

- **FR-011**: Le système DOIT incrémenter `usage_count` automatiquement quand une source est citée
- **FR-012**: Le système DOIT mettre à jour `last_used` automatiquement lors d'une citation
- **FR-013**: Le système DOIT calculer un score personnel (0-100) basé sur usage_count, recency, et decay_rate
- **FR-014**: Le système DOIT supporter 3 niveaux de fiabilité (A/B/C) assignables manuellement
- **FR-015**: Le système DOIT supporter 3 taux de déclin configurables par domaine : fast (demi-vie 3 mois), medium (demi-vie 6 mois), slow (demi-vie 12 mois)

#### Intégration Recherche

- **FR-016**: Le système DOIT trier les sources par score personnel dans les suggestions de recherche
- **FR-017**: Le système DOIT générer des requêtes `site:domain.com` priorisées par score

#### Dashboard

- **FR-018**: Le système DOIT afficher les top sources triées par score (nombre configurable, défaut 20)
- **FR-019**: Le système DOIT identifier les sources dormantes (non utilisées depuis 6 mois)
- **FR-020**: Le système DOIT identifier les sources émergentes (3+ citations dans les 30 derniers jours)

#### Link Rot

- **FR-021**: Le système DOIT vérifier quotidiennement l'accessibilité des URLs (une fois par jour)
- **FR-022**: Le système DOIT marquer les sources inaccessibles avec un statut visuel

---

### Key Entities

- **Source**: Représente une source documentaire avec son domaine, URL pattern, score, fiabilité, et métadonnées d'usage. Une source peut être liée à plusieurs souvenirs et appartenir à plusieurs thèmes.

- **EntrySource** (Lien): Représente la relation entre un souvenir et une source, avec le type de lien (theme/url/file), la référence exacte, et une note optionnelle.

- **SourceTheme**: Représente l'association entre une source et un thème research, avec un score de pertinence.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% des souvenirs peuvent être liés à au moins une source en moins de 30 secondes
- **SC-002**: Les backlinks affichent correctement le nombre de souvenirs liés avec 100% de précision
- **SC-003**: Le score d'une source augmente de manière cohérente après chaque citation (vérifiable par test)
- **SC-004**: Les recherches Speckit présentent les sources triées par score en moins de 1 seconde
- **SC-005**: 80% des utilisateurs trouvent la source pertinente dans les 3 premières suggestions
- **SC-006**: Les sources dormantes (>6 mois sans usage) sont identifiées avec 100% de précision
- **SC-007**: Les URLs inaccessibles sont détectées dans les 24h suivant leur indisponibilité

---

## Assumptions

- Les thèmes research existent dans `~/.speckit/research/` avec le format `XX-nom.md`
- La base de données SQLite existante de Rekall est accessible et modifiable
- Les utilisateurs ont accès à Internet pour la vérification des URLs
- Le système de recherche Speckit expose des hooks pour injecter le tri par score
- Les domaines des URLs peuvent être extraits de manière fiable pour le regroupement

---

## Clarifications

### Session 2025-12-11

- Q: Fréquence de vérification Link Rot → A: Une fois par jour
- Q: Valeurs des taux de déclin (decay_rate) → A: Modéré (demi-vie : fast=3 mois, medium=6 mois, slow=12 mois)
- Q: Seuil "source dormante" → A: 6 mois sans usage
- Q: Nombre de sources dans le dashboard → A: Configurable, défaut 20
- Q: Critère "source émergente" → A: 3+ citations dans les 30 derniers jours

---

## Out of Scope (Phase 1)

- Recherche sémantique de souvenirs similaires (nécessite embeddings)
- Graph de connaissances visuel
- Spaced repetition pour révision des souvenirs
- Import automatique depuis Readwise/Zotero
- Domaine d'expertise par source (scoring par thème)
- Curation progressive (layers L1-L4)
