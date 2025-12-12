# Feature Specification: Sources Autonomes

**Feature Branch**: `010-sources-autonomes`
**Created**: 2025-12-11
**Status**: Draft
**Input**: User description: "Système de curation autonome de sources documentaires remplaçant les fichiers statiques speckit par une base de données dynamique avec promotion automatique, scoring SOTA et intégration speckit"

## Context

Cette feature étend Feature 009 (Sources Integration) pour transformer le système de sources documentaires en un écosystème autonome et intelligent. Elle remplace les fichiers statiques `~/.speckit/research/*.md` par une base de données dynamique dans Rekall.

### Research Findings

La recherche SOTA (voir `specs/010-sources-autonomes/research.md`) a identifié plusieurs approches à intégrer :

- **HITS Algorithm** (Kleinberg) : Distinction Hub vs Authority pour classifier les sources
- **TrustRank** : Propagation de confiance depuis des "seed sites" validés
- **PR-Index** : Qualité des citations vs quantité brute
- **Admiralty Code** : Séparation source reliability vs information credibility (déjà en A/B/C)

### Tendances KM 2025 (sources validées)

- AI pour curation automatique avec human-in-the-loop (APQC)
- Purge automatique du contenu obsolète avec supervision humaine
- Emphasis sur la qualité des données vs quantité

---

## Clarifications

### Session 2025-12-11

- Q: Quel format de sortie pour l'API Speckit (CLI) ? → A: JSON (format structuré, parsable par scripts)
- Q: Quelle fréquence de recalcul des scores ? → A: Batch quotidien + à la demande via CLI
- Q: Comment stocker les thèmes des sources (many-to-many) ? → A: Table de jonction `source_themes` (source_id, theme)

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Migrer les Sources Existantes (Priority: P1)

L'utilisateur possède 10 fichiers de recherche curatés dans `~/.speckit/research/*.md`. Il veut les importer dans Rekall comme "seed sources" de confiance qui serviront de base au système autonome.

**Why this priority**: Sans migration, l'utilisateur perd ses sources curatées manuellement. C'est le fondement du système de confiance (TrustRank).

**Independent Test**: Exécuter la migration, vérifier que toutes les sources des 10 fichiers sont importées avec le flag `is_seed=true` et un bonus de confiance.

**Acceptance Scenarios**:

1. **Given** les fichiers `~/.speckit/research/*.md` existent avec des URLs/domaines documentés, **When** l'utilisateur lance la commande de migration, **Then** toutes les sources uniques sont créées dans la base avec `is_seed=true`.
2. **Given** une source existe déjà dans la base (créée via Feature 009), **When** elle est trouvée dans les fichiers speckit, **Then** elle est mise à jour avec `is_seed=true` sans duplication.
3. **Given** un fichier speckit contient un thème (ex: "AI Agents"), **When** la migration s'exécute, **Then** les sources sont taguées avec ce thème.

---

### User Story 2 - Promotion Automatique des Sources (Priority: P1)

Le système doit automatiquement promouvoir les sources fréquemment utilisées. Quand une source atteint certains critères (usage, score, fraîcheur), elle devient visible dans les suggestions sans intervention manuelle.

**Why this priority**: C'est le coeur de l'autonomie du système. Sans promotion automatique, le système reste statique comme les fichiers qu'il remplace.

**Independent Test**: Créer plusieurs souvenirs citant la même source, vérifier qu'elle apparaît dans les suggestions après avoir atteint les seuils.

**Acceptance Scenarios**:

1. **Given** une source a été citée 3+ fois dans les 6 derniers mois, **When** son score dépasse le seuil de promotion, **Then** elle est marquée comme "promoted" et visible dans les suggestions.
2. **Given** une source promue n'est plus utilisée depuis 6+ mois, **When** le système recalcule les scores, **Then** elle perd son statut promu (rétrogradation).
3. **Given** une source est seed (migrée de speckit), **When** elle n'atteint pas les critères normaux, **Then** elle reste visible car les seeds ont un bonus permanent.

---

### User Story 3 - Classification Hub vs Authority (Priority: P2)

Le système doit distinguer automatiquement les sources qui agrègent du contenu (hubs comme Reddit, HN) des sources qui font autorité (documentation officielle, specs). Cette classification influence le scoring.

**Why this priority**: Améliore la pertinence du scoring. Une citation par Stack Overflow (hub de qualité) vaut plus qu'une citation par un blog random.

**Independent Test**: Ajouter des sources de différents types, vérifier que la classification automatique fonctionne et influence le score.

**Acceptance Scenarios**:

1. **Given** une source avec domaine connu (ex: `news.ycombinator.com`), **When** elle est créée, **Then** elle est automatiquement classifiée comme "hub".
2. **Given** une source avec domaine officiel (ex: `developer.mozilla.org`), **When** elle est créée, **Then** elle est automatiquement classifiée comme "authority".
3. **Given** une source sans domaine connu, **When** elle est créée, **Then** elle reste "unclassified" jusqu'à classification manuelle ou heuristique.

---

### User Story 4 - Scoring Avancé avec Citation Quality (Priority: P2)

Le score d'une source doit prendre en compte non seulement le nombre d'usages mais aussi la qualité des "citations". Une source citée par d'autres sources à haut score vaut plus qu'une source citée isolément.

**Why this priority**: Apporte la sophistication SOTA (PR-Index). Différencie popularité (nombre) de prestige (qualité).

**Independent Test**: Créer une chaîne de citations entre sources, vérifier que le score propage correctement la qualité.

**Acceptance Scenarios**:

1. **Given** une source A est citée par des souvenirs qui citent aussi une source B à score élevé, **When** le score de A est recalculé, **Then** A bénéficie d'un bonus de citation quality.
2. **Given** une source est citée uniquement de manière isolée, **When** son score est calculé, **Then** elle n'a pas de bonus citation quality mais reste scorée sur usage/fraîcheur.

---

### User Story 5 - Intégration Speckit pour Suggestions (Priority: P2)

Speckit doit pouvoir interroger Rekall pour obtenir les sources pertinentes par thème. Les sources promues et seeds apparaissent en priorité dans les suggestions de recherche.

**Why this priority**: C'est l'intégration qui justifie le remplacement des fichiers statiques. Speckit devient client de Rekall.

**Independent Test**: Depuis speckit, demander les sources pour un thème, vérifier que les sources appropriées sont retournées triées par score.

**Acceptance Scenarios**:

1. **Given** des sources existent avec le tag "security", **When** speckit demande les sources pour le thème security, **Then** les sources sont retournées triées par score décroissant.
2. **Given** un thème n'a pas de sources taguées, **When** speckit le demande, **Then** une liste vide est retournée (pas d'erreur).
3. **Given** des sources seeds et promues existent, **When** speckit demande les suggestions, **Then** les seeds et promues apparaissent avant les sources normales à score égal.

---

### User Story 6 - Dashboard Sources Enrichi (Priority: P3)

Le dashboard sources existant (Feature 009) est enrichi avec les nouvelles métriques : sources promues, seeds, classification hub/authority, et statistiques de promotion.

**Why this priority**: Nice-to-have pour la visibilité. Le système fonctionne sans mais l'utilisateur apprécie de voir l'état du système.

**Independent Test**: Ouvrir le dashboard, vérifier que les nouvelles sections sont visibles et les données correctes.

**Acceptance Scenarios**:

1. **Given** des sources seeds existent, **When** l'utilisateur ouvre le dashboard, **Then** une section "Sources Seeds" les liste avec leur origine (fichier speckit source).
2. **Given** des sources ont été promues automatiquement, **When** l'utilisateur consulte le dashboard, **Then** il voit la liste des sources promues avec la date de promotion.
3. **Given** des sources sont classifiées hub/authority, **When** le dashboard affiche une source, **Then** son rôle est visible (icône ou label).

---

### Edge Cases

- Que se passe-t-il si un fichier speckit est malformé (pas d'URLs extractibles) ?
  - La migration continue avec un warning, les fichiers problématiques sont loggés.
- Que se passe-t-il si une source seed est supprimée manuellement ?
  - Elle perd son statut seed mais peut redevenir "promue" si elle atteint les critères.
- Que se passe-t-il si le seuil de promotion change après que des sources ont été promues ?
  - Les sources existantes gardent leur statut jusqu'au prochain recalcul global.
- Que se passe-t-il si speckit demande un thème qui n'existe pas ?
  - Retourner liste vide, pas d'erreur.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Migration

- **FR-001**: System MUST parse les fichiers `~/.speckit/research/*.md` pour extraire les URLs et domaines documentés.
- **FR-002**: System MUST créer des sources avec `is_seed=true` pour chaque URL/domaine extrait.
- **FR-003**: System MUST associer le thème du fichier source (nom du fichier) à chaque source importée.
- **FR-004**: System MUST détecter les doublons et mettre à jour plutôt que créer.
- **FR-005**: System MUST logger les fichiers/sections non parsables sans interrompre la migration.

#### Promotion Automatique

- **FR-006**: System MUST définir des seuils de promotion configurables (usage minimum, score minimum, fraîcheur maximum).
- **FR-007**: System MUST marquer automatiquement les sources atteignant les critères comme "promoted".
- **FR-008**: System MUST révoquer le statut "promoted" si une source ne remplit plus les critères (rétrogradation).
- **FR-009**: System MUST exempter les sources seeds de la rétrogradation (bonus permanent).

#### Classification Hub/Authority

- **FR-010**: System MUST maintenir une liste de domaines connus avec leur classification (hub/authority).
- **FR-011**: System MUST classifier automatiquement les nouvelles sources basées sur cette liste.
- **FR-012**: System MUST permettre la classification manuelle pour les domaines non reconnus.
- **FR-013**: System MUST appliquer un bonus de score aux sources "authority" par rapport aux "hub".

#### Scoring Avancé

- **FR-014**: System MUST calculer un facteur "citation quality" basé sur le score des co-citations.
- **FR-015**: System MUST intégrer le facteur citation quality dans la formule de score existante.
- **FR-016**: System MUST recalculer les scores automatiquement une fois par jour (batch quotidien) et à la demande via commande CLI.

#### Intégration Speckit

- **FR-017**: System MUST exposer une API (CLI ou fonction) pour lister les sources par thème.
- **FR-018**: System MUST trier les résultats par score décroissant.
- **FR-019**: System MUST prioriser seeds et promoted à score égal.
- **FR-020**: System MUST retourner les métadonnées utiles (domain, score, role, is_seed, is_promoted).
- **FR-021**: System MUST retourner les résultats au format JSON pour l'intégration programmatique.

#### Dashboard

- **FR-022**: System MUST afficher une section "Sources Seeds" dans le dashboard.
- **FR-023**: System MUST afficher une section "Sources Promues" dans le dashboard.
- **FR-024**: System MUST afficher le rôle (hub/authority/unclassified) de chaque source.

### Key Entities

- **Source** (extension de Feature 009):
  - Nouveaux attributs : `is_seed`, `is_promoted`, `promoted_at`, `role` (hub/authority/unclassified), `seed_origin` (fichier source si seed), `citation_quality_factor`

- **SourceTheme** (nouvelle entité - table de jonction):
  - Relation many-to-many entre sources et thèmes
  - Attributs : `source_id` (FK), `theme` (string)

- **KnownDomain** (nouvelle entité):
  - Représente un domaine avec classification pré-définie
  - Attributs : `domain`, `role`, `notes`

- **PromotionConfig** (configuration):
  - Seuils de promotion : `min_usage`, `min_score`, `max_days_since_use`
  - Pourrait être en config fichier plutôt qu'en base

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% des sources des fichiers speckit sont migrées sans perte de données.
- **SC-002**: Les sources fréquemment utilisées (3+ citations en 6 mois) sont automatiquement promues dans les 24h suivant l'atteinte des critères.
- **SC-003**: Les suggestions speckit retournent des résultats en moins de 500ms pour n'importe quel thème.
- **SC-004**: Le dashboard affiche les nouvelles métriques (seeds, promoted, role) sans dégradation de performance perceptible.
- **SC-005**: La classification automatique hub/authority a un taux de précision de 90%+ sur les domaines connus.
- **SC-006**: Le scoring avec citation quality différencie correctement les sources à haute qualité (test A/B sur corpus connu).

---

## Assumptions

- Les fichiers `~/.speckit/research/*.md` suivent un format parsable (sections avec URLs en markdown).
- L'utilisateur accepte que les seuils de promotion soient des valeurs par défaut ajustables.
- La liste des domaines connus (hub/authority) sera initialisée avec ~50 domaines courants et extensible.
- Speckit appellera Rekall via CLI (`rekall sources suggest --theme X`) plutôt que via import Python direct.
- Le recalcul des scores peut être déclenché manuellement ou via cron, pas en temps réel à chaque ajout.

---

## Out of Scope

- Enrichissement automatique via recherche web (scraping de nouvelles sources)
- Machine learning pour classification automatique au-delà des heuristiques simples
- Synchronisation bidirectionnelle speckit ↔ Rekall (Rekall est la source de vérité)
- Interface web pour la gestion des sources (TUI uniquement)
- Vérification de contenu des sources (link rot de Feature 009 suffit)
