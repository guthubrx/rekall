# Feature Specification: Sources Organisation

**Feature Branch**: `012-sources-organisation`
**Created**: 2025-12-11
**Status**: Draft
**Input**: Améliorer l'organisation des sources dans la TUI avec tags multiples et filtres multi-critères
**Design Reference**: `docs/plans/2025-12-11-sources-enhancements-design.md`

## Contexte

Les sources documentaires dans Rekall peuvent actuellement avoir un seul thème (issu de la migration SpecKit). Les utilisateurs ont besoin de :
1. Taguer les sources avec plusieurs thèmes pour une meilleure organisation
2. Rechercher et filtrer les sources selon plusieurs critères combinés
3. Sauvegarder des filtres fréquents comme "vues" réutilisables

---

## User Scenarios & Testing

### User Story 1 - Tags à la création (Priority: P1)

En tant qu'utilisateur, je veux pouvoir assigner plusieurs tags à une source lors de sa création, afin de l'organiser dès le départ.

**Why this priority**: C'est le point d'entrée principal - chaque nouvelle source doit pouvoir être bien taguée immédiatement.

**Independent Test**: Créer une source avec 3 tags, vérifier qu'ils sont tous associés.

**Acceptance Scenarios**:

1. **Given** l'écran d'ajout de source, **When** je saisis des tags séparés par virgule (ex: "go, concurrency, backend"), **Then** la source est créée avec les 3 tags
2. **Given** l'écran d'ajout de source, **When** je commence à taper un tag, **Then** les tags existants correspondants sont suggérés (auto-complétion)
3. **Given** l'écran d'ajout de source, **When** je ne saisis aucun tag, **Then** la source est créée sans tag (optionnel)

---

### User Story 2 - Édition des tags (Priority: P1)

En tant qu'utilisateur, je veux pouvoir modifier les tags d'une source existante, afin de corriger ou enrichir son organisation.

**Why this priority**: Complémentaire à US1, permet de corriger les erreurs et d'améliorer l'organisation au fil du temps.

**Independent Test**: Ouvrir une source, ajouter un tag, retirer un autre, vérifier les changements.

**Acceptance Scenarios**:

1. **Given** la fiche détail d'une source, **When** je sélectionne "Modifier les tags", **Then** je vois la liste des tags actuels avec possibilité de les retirer
2. **Given** l'écran de modification des tags, **When** j'ajoute un nouveau tag, **Then** il est immédiatement associé à la source
3. **Given** l'écran de modification des tags, **When** je retire un tag existant, **Then** l'association est supprimée

---

### User Story 3 - Navigation par tag (Priority: P1)

En tant qu'utilisateur, je veux voir la liste de tous mes tags avec le nombre de sources associées, afin de naviguer dans mes sources par thématique.

**Why this priority**: Permet de visualiser l'organisation globale et d'accéder rapidement aux sources par thème.

**Independent Test**: Accéder à "Parcourir par tag", sélectionner un tag, voir les sources correspondantes.

**Acceptance Scenarios**:

1. **Given** le dashboard Sources, **When** je sélectionne "Parcourir par tag", **Then** je vois la liste des tags avec compteurs (ex: "go (15)")
2. **Given** la liste des tags, **When** je sélectionne un tag, **Then** je vois toutes les sources associées à ce tag
3. **Given** la liste des tags, **When** un tag n'a aucune source, **Then** il n'apparaît pas dans la liste

---

### User Story 4 - Édition en vrac (Priority: P2)

En tant qu'utilisateur, je veux pouvoir sélectionner plusieurs sources et leur ajouter/retirer un tag commun, afin de réorganiser rapidement ma collection.

**Why this priority**: Utile mais moins fréquent que la gestion tag par tag.

**Independent Test**: Sélectionner 5 sources, ajouter le tag "archive", vérifier que les 5 ont le tag.

**Acceptance Scenarios**:

1. **Given** la liste des sources, **When** j'active le mode sélection, **Then** je peux cocher plusieurs sources
2. **Given** plusieurs sources sélectionnées, **When** je choisis "Ajouter tag", **Then** le tag est ajouté à toutes les sources sélectionnées
3. **Given** plusieurs sources sélectionnées, **When** je choisis "Retirer tag", **Then** le tag est retiré de toutes les sources sélectionnées

---

### User Story 5 - Filtres multi-critères (Priority: P2)

En tant qu'utilisateur, je veux filtrer mes sources selon plusieurs critères combinés (tags, score, statut, etc.), afin de trouver rapidement les sources pertinentes.

**Why this priority**: Améliore significativement la recherche mais nécessite d'abord que les tags soient bien gérés.

**Independent Test**: Filtrer par tag "go" + score > 50 + statut "active", voir uniquement les sources correspondantes.

**Acceptance Scenarios**:

1. **Given** le dashboard Sources, **When** je sélectionne "Recherche avancée", **Then** je vois un formulaire de filtres
2. **Given** le formulaire de filtres, **When** je sélectionne plusieurs tags, **Then** seules les sources ayant AU MOINS UN de ces tags sont affichées
3. **Given** le formulaire de filtres, **When** je définis une plage de score (ex: 30-80), **Then** seules les sources dans cette plage sont affichées
4. **Given** le formulaire de filtres, **When** je combine plusieurs critères, **Then** tous les critères sont appliqués (ET logique entre types de critères)

---

### User Story 6 - Vues sauvegardées (Priority: P3)

En tant qu'utilisateur, je veux sauvegarder mes combinaisons de filtres fréquentes comme "vues", afin de les réappliquer rapidement.

**Why this priority**: Confort d'usage, mais les filtres manuels fonctionnent déjà.

**Independent Test**: Créer un filtre, le sauvegarder comme "Sources Go actives", le réappliquer depuis le menu.

**Acceptance Scenarios**:

1. **Given** des filtres appliqués, **When** je clique "Sauvegarder cette vue", **Then** je peux donner un nom à cette combinaison
2. **Given** des vues sauvegardées, **When** j'accède à "Mes vues", **Then** je vois la liste de mes vues avec leur nom
3. **Given** la liste des vues, **When** je sélectionne une vue, **Then** les filtres correspondants sont appliqués
4. **Given** une vue sauvegardée, **When** je la supprime, **Then** elle n'apparaît plus dans la liste

---

### Edge Cases

- **Tag vide** : Si l'utilisateur entre une virgule sans texte, ignorer silencieusement
- **Tag en double** : Si un tag est ajouté deux fois, ne pas créer de doublon
- **Suppression tag utilisé** : Si on essaie de supprimer un tag utilisé par plusieurs sources, demander confirmation
- **Aucun résultat filtre** : Afficher un message "Aucune source ne correspond à ces critères"
- **Vue avec critères obsolètes** : Si un tag référencé dans une vue n'existe plus, l'ignorer dans le filtre

---

## Requirements

### Functional Requirements

**Tags multiples :**
- **FR-001**: Le système DOIT permettre d'associer plusieurs tags à une source
- **FR-002**: Le système DOIT proposer l'auto-complétion des tags existants
- **FR-003**: Le système DOIT afficher le nombre de sources par tag dans la navigation
- **FR-004**: Le système DOIT permettre l'ajout/retrait de tags sur une source existante
- **FR-005**: Le système DOIT permettre l'édition de tags en vrac (sélection multiple)

**Filtres :**
- **FR-006**: Le système DOIT permettre de filtrer par tags (multi-sélection, OU logique)
- **FR-007**: Le système DOIT permettre de filtrer par plage de score (min-max)
- **FR-008**: Le système DOIT permettre de filtrer par statut (seed, promoted, active, dormant, inaccessible)
- **FR-009**: Le système DOIT permettre de filtrer par rôle (authority, hub, unclassified)
- **FR-010**: Le système DOIT permettre de filtrer par fraîcheur (dernière utilisation)
- **FR-011**: Le système DOIT permettre de rechercher dans le texte (domaine, notes)
- **FR-012**: Le système DOIT combiner les filtres avec un ET logique entre types de critères

**Vues :**
- **FR-013**: Le système DOIT permettre de sauvegarder une combinaison de filtres comme "vue"
- **FR-014**: Le système DOIT permettre de lister et réappliquer les vues sauvegardées
- **FR-015**: Le système DOIT permettre de supprimer une vue sauvegardée

### Key Entities

- **Tag** : Libellé court associé à une ou plusieurs sources (relation N:N via `source_themes`)
- **SavedFilter (Vue)** : Nom + combinaison de critères de filtrage persistée
- **Source** : Entité existante, enrichie de la relation tags multiples

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: L'utilisateur peut associer 5+ tags à une source en moins de 30 secondes
- **SC-002**: La navigation par tag affiche les résultats en moins de 1 seconde pour 1000 sources
- **SC-003**: L'utilisateur peut trouver une source spécifique avec 3 critères combinés en moins de 15 secondes
- **SC-004**: 100% des sources existantes restent accessibles après migration (pas de régression)
- **SC-005**: Les vues sauvegardées persistent entre les sessions

---

## Assumptions

- La table `source_themes` existe déjà et supporte les tags multiples
- L'auto-complétion sera basée sur les tags existants en base
- Les filtres utilisent un ET logique entre types différents (tags ET score ET statut) mais un OU au sein d'un même type (tag1 OU tag2)
- Une nouvelle table `saved_filters` sera nécessaire pour les vues

---

## Out of Scope

- Hiérarchie de tags (rester flat)
- Import/export de tags
- Suggestions de tags par IA (feature 013)
- Fusion de tags
