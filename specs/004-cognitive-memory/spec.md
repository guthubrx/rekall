# Feature Specification: Système de Mémoire Cognitive pour Rekall

**Feature Branch**: `004-cognitive-memory`
**Created**: 2025-12-08
**Status**: Draft
**Input**: User description: "Système de mémoire cognitive pour Rekall - Évolutions basées sur les mécanismes cognitifs de la mémoire humaine incluant: liens entre entrées (knowledge graph), distinction épisodique/sémantique, répétition espacée, tracking de consolidation, et skill Claude pour consultation/capture automatique"

## Research Findings

Cette spécification s'appuie sur une recherche approfondie documentée dans `docs/research-memory-mechanisms.md` couvrant :
- 12 mécanismes cognitifs de la mémoire humaine (consolidation, spacing effect, testing effect, etc.)
- 11 études académiques (arXiv) sur les applications en informatique
- Validation via Research Hub SpecKit

### Points clés de la recherche

| Mécanisme | Impact prouvé | Application Rekall |
|-----------|---------------|-------------------|
| Knowledge Graphs | +20% précision récupération | Liens entre entrées |
| History-based fault localization | Meilleure prédiction bugs | Consultation avant action |
| Spaced repetition | +6-9% rétention | Commande review |
| Épisodique vs Sémantique | Crucial pour agents long-terme | Distinction memory_type |
| Testing effect | 80% vs 30% rétention | Récupération active |

### Red Flags identifiés (Gartner 2025)

- 50% des projets AI abandonnés au stade pilote → **Mitigation** : Approche incrémentale par US indépendantes
- 100% des projets AI sans KM moderne échouent → **Mitigation** : Structure de données enrichie
- Échecs viennent des données, pas des algorithmes → **Mitigation** : Focus sur la qualité de capture

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Liens entre entrées (Priority: P1)

En tant que développeur, je veux pouvoir créer des connexions entre mes entrées Rekall afin de construire un graphe de connaissances interconnecté qui améliore la pertinence des recherches.

**Why this priority**: La recherche montre que les Knowledge Graphs améliorent la précision de récupération de +20%. C'est la fonctionnalité avec le meilleur ratio impact/effort.

**Independent Test**: Peut être testé en créant 3 entrées, les liant entre elles, puis en vérifiant que `rekall related <id>` retourne les entrées connectées.

**Acceptance Scenarios**:

1. **Given** deux entrées existantes dans Rekall, **When** l'utilisateur exécute `rekall link <id1> <id2>`, **Then** une connexion bidirectionnelle est créée entre les deux entrées
2. **Given** une entrée avec des liens, **When** l'utilisateur exécute `rekall related <id>`, **Then** toutes les entrées connectées sont affichées avec le type de relation
3. **Given** une entrée avec des liens, **When** l'utilisateur exécute `rekall show <id>`, **Then** les entrées liées sont listées dans une section "Related"
4. **Given** une recherche Rekall, **When** des résultats ont des entrées liées pertinentes, **Then** les entrées liées sont suggérées comme "Voir aussi"

---

### User Story 2 - Consultation automatique avant action (Priority: P1)

En tant que développeur utilisant Claude Code, je veux que Claude consulte automatiquement Rekall avant de commencer une tâche de développement afin de bénéficier de mon expérience passée et éviter de répéter des erreurs.

**Why this priority**: La recherche sur "history-based fault localization" montre que les fichiers avec un historique de bugs sont plus susceptibles d'en contenir. La consultation préventive est le cœur de la valeur de Rekall.

**Independent Test**: Peut être testé en installant le skill Claude, en demandant de fixer un bug, et en vérifiant que Claude consulte Rekall avant de proposer une solution.

**Acceptance Scenarios**:

1. **Given** un skill Claude installé et une base Rekall avec des entrées, **When** l'utilisateur demande à Claude de corriger un bug, **Then** Claude exécute une recherche Rekall pertinente avant de proposer une solution
2. **Given** un contexte de développement (projet, fichiers), **When** Claude consulte Rekall, **Then** la recherche utilise le contexte pour filtrer les résultats
3. **Given** des résultats Rekall pertinents trouvés, **When** Claude présente sa solution, **Then** il cite les entrées Rekall utilisées avec leurs IDs
4. **Given** aucun résultat Rekall pertinent, **When** Claude procède à la tâche, **Then** il indique "Aucune connaissance préalable trouvée dans Rekall"

---

### User Story 3 - Capture automatique après résolution (Priority: P1)

En tant que développeur utilisant Claude Code, je veux que Claude me propose de capturer les nouvelles connaissances acquises (bugs résolus, décisions prises, patterns découverts) afin d'enrichir ma base Rekall pour le futur.

**Why this priority**: Sans capture, la base reste vide. La recherche montre que les "lessons learned" sont rarement capturées intentionnellement, ce qui cause des pertes de $31.5B/an dans les Fortune 500.

**Independent Test**: Peut être testé en résolvant un bug avec Claude, puis en vérifiant qu'il propose de sauvegarder et que l'entrée est créée correctement.

**Acceptance Scenarios**:

1. **Given** Claude vient de résoudre un bug, **When** la résolution est confirmée, **Then** Claude propose de capturer cette connaissance dans Rekall
2. **Given** Claude propose une capture, **When** l'utilisateur accepte, **Then** une entrée est créée avec titre, type, tags, et contenu structuré
3. **Given** Claude a fait une recherche web qui a aidé à résoudre un problème, **When** la tâche est terminée, **Then** Claude propose de sauvegarder la référence trouvée
4. **Given** une décision technique importante a été prise, **When** l'utilisateur confirme le choix, **Then** Claude propose de documenter cette décision avec le contexte et les alternatives considérées

---

### User Story 4 - Distinction épisodique/sémantique (Priority: P2)

En tant que développeur, je veux pouvoir distinguer mes connaissances "épisodiques" (événements spécifiques) de mes connaissances "sémantiques" (concepts généralisés) afin d'avoir une organisation plus naturelle de ma mémoire.

**Why this priority**: La recherche sur les agents LLM montre que cette distinction est cruciale pour le comportement long-terme. Dépend des US1-3 pour avoir du contenu à catégoriser.

**Independent Test**: Peut être testé en créant une entrée épisodique, puis en la généralisant, et en vérifiant que les deux versions existent avec le bon type.

**Acceptance Scenarios**:

1. **Given** une nouvelle entrée, **When** l'utilisateur la crée avec `rekall add`, **Then** il peut spécifier `--memory-type episodic|semantic`
2. **Given** plusieurs entrées épisodiques similaires, **When** l'utilisateur exécute `rekall generalize <id>`, **Then** une entrée sémantique est créée qui synthétise les patterns communs
3. **Given** une entrée sémantique généralisée, **When** elle est affichée, **Then** les entrées épisodiques sources sont référencées
4. **Given** une recherche Rekall, **When** l'utilisateur filtre par `--memory-type`, **Then** seules les entrées du type spécifié sont retournées

---

### User Story 5 - Tracking d'accès et consolidation (Priority: P2)

En tant que développeur, je veux que Rekall suive quand et combien de fois j'accède à chaque entrée afin d'identifier les connaissances "consolidées" vs "fragiles" et les entrées "mortes" non consultées.

**Why this priority**: La recherche sur la courbe de l'oubli montre que les mémoires non réactivées s'affaiblissent. Ce tracking est nécessaire pour la répétition espacée (US6).

**Independent Test**: Peut être testé en consultant une entrée plusieurs fois, puis en vérifiant que les métadonnées d'accès sont mises à jour.

**Acceptance Scenarios**:

1. **Given** une entrée existante, **When** elle est consultée via `show` ou `search`, **Then** `last_accessed` et `access_count` sont mis à jour
2. **Given** des entrées avec différents historiques d'accès, **When** l'utilisateur exécute `rekall stale --days 30`, **Then** les entrées non consultées depuis 30 jours sont listées
3. **Given** une entrée consultée régulièrement, **When** elle est affichée, **Then** un indicateur de "consolidation" est visible (ex: score ou badge)
4. **Given** le TUI Rekall, **When** l'utilisateur parcourt ses entrées, **Then** les indicateurs de fraîcheur/consolidation sont visibles

---

### User Story 6 - Répétition espacée (Priority: P3)

En tant que développeur, je veux une commande de révision espacée qui me présente les connaissances à consolider afin de maintenir ma mémoire active selon les principes scientifiques de rétention.

**Why this priority**: La répétition espacée améliore la rétention de +6-9% selon la recherche. Dépend du tracking d'accès (US5) pour calculer les intervalles.

**Independent Test**: Peut être testé en créant des entrées avec différentes dates d'accès, puis en exécutant `rekall review` et en vérifiant que les bonnes entrées sont présentées.

**Acceptance Scenarios**:

1. **Given** des entrées avec des dates d'accès variées, **When** l'utilisateur exécute `rekall review`, **Then** les entrées "dues" pour révision sont présentées par ordre de priorité
2. **Given** une session de révision, **When** l'utilisateur consulte une entrée, **Then** son prochain intervalle de révision est recalculé
3. **Given** une entrée marquée comme "connue", **When** le prochain intervalle est calculé, **Then** il est plus long que le précédent (espacement croissant)
4. **Given** une entrée marquée comme "à revoir", **When** le prochain intervalle est calculé, **Then** il est plus court (renforcement nécessaire)

---

### User Story 7 - Généralisation assistée (Priority: P3)

En tant que développeur utilisant Claude Code, je veux que Claude m'aide à généraliser mes connaissances épisodiques en patterns sémantiques réutilisables afin d'extraire la valeur maximale de mes expériences.

**Why this priority**: La généralisation transforme les expériences uniques en connaissances transférables. Dépend de US4 (distinction épisodique/sémantique).

**Independent Test**: Peut être testé en demandant à Claude de généraliser 3 bugs similaires en un pattern, et en vérifiant que l'entrée sémantique créée synthétise correctement les points communs.

**Acceptance Scenarios**:

1. **Given** plusieurs entrées épisodiques similaires identifiées, **When** Claude propose une généralisation, **Then** il présente un draft d'entrée sémantique synthétisant les patterns communs
2. **Given** un draft de généralisation, **When** l'utilisateur l'approuve, **Then** l'entrée sémantique est créée avec des liens vers les entrées épisodiques sources
3. **Given** une entrée sémantique généralisée, **When** une nouvelle entrée épisodique similaire est créée, **Then** Claude suggère de la lier à l'entrée sémantique existante

---

### Edge Cases

- **Entrées orphelines** : Que faire des entrées sans liens après X mois ? → Suggérer des liens potentiels basés sur similarité
- **Liens circulaires** : Comment gérer A→B→C→A ? → Autoriser (graphe, pas arbre) mais détecter pour éviter boucles infinies
- **Conflits de généralisation** : Deux patterns sémantiques contradictoires ? → Permettre la coexistence avec mention du conflit
- **Base vide au démarrage** : Skill consulte mais ne trouve rien ? → Mode "bootstrap" qui propose de capturer plus activement
- **Entrées obsolètes non dépréciées** : Connaissance fausse mais toujours active ? → Mécanisme de validation/contestation

---

## Requirements *(mandatory)*

### Functional Requirements

#### Liens entre entrées (US1)

- **FR-001**: Le système DOIT permettre de créer des liens bidirectionnels entre deux entrées existantes
- **FR-002**: Le système DOIT permettre de spécifier un type de relation lors de la création d'un lien (ex: "related", "supersedes", "derived_from", "contradicts")
- **FR-003**: Le système DOIT afficher les entrées liées lors de la consultation d'une entrée
- **FR-004**: Le système DOIT proposer les entrées liées comme "Voir aussi" dans les résultats de recherche
- **FR-005**: Le système DOIT permettre de supprimer un lien existant

#### Consultation automatique (US2)

- **FR-006**: Le skill DOIT effectuer une recherche Rekall avant toute tâche de développement (bug fix, feature, refactor)
- **FR-007**: Le skill DOIT utiliser le contexte actuel (projet, fichiers mentionnés, stack technique) pour affiner la recherche
- **FR-008**: Le skill DOIT citer les entrées Rekall utilisées avec leurs IDs dans ses réponses
- **FR-009**: Le skill DOIT indiquer explicitement quand aucune connaissance préalable n'est trouvée

#### Capture automatique (US3)

- **FR-010**: Le skill DOIT proposer de capturer les connaissances après résolution d'un bug
- **FR-011**: Le skill DOIT proposer de capturer les décisions techniques importantes
- **FR-012**: Le skill DOIT proposer de capturer les références web utiles découvertes
- **FR-013**: Le skill DOIT générer automatiquement un titre, type, et tags suggérés
- **FR-014**: L'utilisateur DOIT pouvoir modifier ou refuser la capture proposée

#### Distinction épisodique/sémantique (US4)

- **FR-015**: Le système DOIT supporter un attribut `memory_type` avec valeurs "episodic" ou "semantic"
- **FR-016**: Le système DOIT permettre de filtrer les recherches par `memory_type`
- **FR-017**: Le système DOIT permettre de créer une entrée sémantique à partir d'entrées épisodiques
- **FR-018**: Les entrées sémantiques DOIVENT référencer leurs sources épisodiques via liens

#### Tracking et consolidation (US5)

- **FR-019**: Le système DOIT enregistrer la date de dernière consultation (`last_accessed`) de chaque entrée
- **FR-020**: Le système DOIT compter le nombre total de consultations (`access_count`) de chaque entrée
- **FR-021**: Le système DOIT permettre de lister les entrées non consultées depuis N jours
- **FR-022**: Le système DOIT calculer un score de consolidation basé sur la fréquence et régularité des accès

#### Répétition espacée (US6)

- **FR-023**: Le système DOIT calculer un intervalle de révision pour chaque entrée basé sur l'historique d'accès
- **FR-024**: Le système DOIT permettre de lister les entrées "dues" pour révision
- **FR-025**: Le système DOIT ajuster l'intervalle après chaque révision (plus long si maîtrisé, plus court sinon)

#### Généralisation assistée (US7)

- **FR-026**: Le skill DOIT pouvoir identifier des entrées épisodiques similaires
- **FR-027**: Le skill DOIT pouvoir proposer un draft de généralisation sémantique
- **FR-028**: Le skill DOIT créer les liens appropriés lors de la généralisation

### Key Entities

- **Entry** (existant, enrichi): Représente une connaissance. Attributs ajoutés : `memory_type`, `last_accessed`, `access_count`, `consolidation_score`, `next_review`
- **Link**: Représente une connexion entre deux entrées. Attributs : `source_id`, `target_id`, `relation_type`, `created_at`. **Note**: Plusieurs liens de types différents sont autorisés entre les mêmes deux entrées (ex: A→B "related" ET A→B "supersedes"). L'unicité est sur le triplet (source_id, target_id, relation_type).
- **ReviewSchedule**: Représente le planning de révision d'une entrée. Attributs : `entry_id`, `interval_days`, `next_review_date`, `ease_factor`

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les développeurs peuvent créer et naviguer des liens entre entrées en moins de 10 secondes par opération
- **SC-002**: Le skill Claude consulte Rekall dans 100% des cas de bug fix/feature/refactor détectés
- **SC-003**: Au moins 50% des connaissances acquises en session sont proposées pour capture
- **SC-004**: Les recherches avec entrées liées montrent une amélioration perçue de pertinence par l'utilisateur
- **SC-005**: Les entrées "stale" (non consultées >30 jours) sont identifiables en une seule commande
- **SC-006**: Le système de révision espacée identifie correctement les entrées dues pour révision
- **SC-007**: La distinction épisodique/sémantique permet un filtrage efficace des résultats de recherche

---

## Clarifications

Réponses obtenues lors du processus `/speckit.clarify` :

1. **Multiplicité des liens** : Plusieurs liens de types différents sont autorisés entre les mêmes deux entrées. Contrainte d'unicité sur (source_id, target_id, relation_type).

2. **Migration memory_type** : Les entrées existantes reçoivent `memory_type = "episodic"` par défaut lors de la migration. Rationale : les entrées sont des expériences spécifiques (bugs vécus, décisions prises dans un contexte).

3. **Suppression d'entrée liée** : Refuser la suppression si des liens existent, lister les entrées liées, et demander confirmation explicite avec `--force` pour supprimer en cascade.

4. **Types de relation** : Enum fermé pour V1 avec 4 types fixes : `related`, `supersedes`, `derived_from`, `contradicts`. Garantit cohérence et simplifie les requêtes.

5. **Initialisation tracking** : Entrées existantes migrées avec `access_count=1` et `last_accessed=created_at`. Considère 1 accès historique avec la date de création originale.

---

## Assumptions

- L'utilisateur a déjà Rekall installé avec une base initialisée
- L'utilisateur utilise Claude Code comme assistant de développement
- Les commandes Rekall sont accessibles depuis le terminal
- Le skill Claude a accès aux commandes `rekall` via Bash
- Les entrées existantes peuvent être migrées vers le nouveau schéma (ajout de champs avec valeurs par défaut)

---

## Out of Scope

- Interface graphique web pour visualiser le graphe de connaissances
- Synchronisation multi-utilisateurs / collaborative
- Algorithme de répétition espacée avancé (FSRS) - version simple suffisante pour V1
- Intégration avec d'autres assistants IA (Cursor, Copilot) - focus sur Claude Code
- Import/export vers d'autres systèmes de knowledge management (Notion, Obsidian)
