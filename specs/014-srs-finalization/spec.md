# Feature Specification: SRS Finalization

**Feature Branch**: `014-srs-finalization`
**Created**: 2025-12-12
**Status**: Abandoned
**Abandoned**: 2025-12-12
**Input**: Finalisation du système SRS (Spaced Repetition System) pour rekall

## Reason for Abandonment

Le système SRS (Spaced Repetition System) est conçu pour renforcer la mémoire humaine via la courbe d'oubli d'Ebbinghaus. Or, rekall est principalement utilisé par des **agents IA** qui :

1. **N'ont pas de courbe d'oubli** : Un agent peut accéder à toute la base instantanément via `rekall_search`
2. **Ne mémorisent pas entre sessions** : Chaque session est indépendante, pas de renforcement possible
3. **N'ont pas besoin de révision** : L'information est toujours accessible à 100%

**Conclusion** : Le SRS apporte peu de valeur dans un contexte agent-first. Les ressources sont mieux investies dans les outils MCP (Feature 015) qui améliorent directement les capacités des agents.

**Infrastructure conservée** : Les champs `next_review`, `review_interval`, `ease_factor` et la commande `rekall review` restent disponibles pour un usage humain occasionnel, mais ne seront pas étendus (pas de TUI, pas de dashboard).

---

## Context (Original)

Le système SRS existe partiellement dans rekall :
- **Modèle Entry** : champs `next_review`, `review_interval`, `ease_factor`
- **Modèle ReviewItem** : représente une entrée due pour révision
- **DB** : `get_due_entries()` et `record_review()` avec algorithme SM-2
- **CLI** : commande `rekall review` basique

Ce qui manque : interface TUI, statistiques, initialisation automatique.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Session de révision interactive TUI (Priority: P1)

En tant qu'utilisateur de rekall, je veux réviser mes entrées via une interface interactive dans la TUI pour renforcer ma mémorisation des connaissances stockées.

**Why this priority**: C'est la fonctionnalité principale du SRS - sans interface interactive, le système n'est pas utilisable efficacement.

**Independent Test**: Peut être testé en lançant `rekall tui`, en naviguant vers le menu Review, et en complétant une session de révision avec notation (Again/Hard/Good/Easy).

**Acceptance Scenarios**:

1. **Given** des entrées existent avec `next_review` passé, **When** l'utilisateur accède au mode Review dans la TUI, **Then** les entrées dues sont affichées une par une avec leur contenu complet
2. **Given** une entrée est affichée en révision, **When** l'utilisateur note sa réponse (1-4), **Then** `record_review()` est appelé et la prochaine entrée s'affiche
3. **Given** aucune entrée n'est due, **When** l'utilisateur accède au mode Review, **Then** un message indique qu'il n'y a rien à réviser aujourd'hui
4. **Given** une session de révision en cours, **When** l'utilisateur appuie sur [q], **Then** la session se termine avec un résumé (entrées révisées, score moyen)

---

### User Story 2 - Dashboard SRS (Priority: P2)

En tant qu'utilisateur, je veux voir un tableau de bord de mes révisions pour suivre ma progression et planifier mes sessions d'étude.

**Why this priority**: Améliore l'expérience mais n'est pas bloquant pour utiliser le SRS de base.

**Independent Test**: Peut être testé en accédant au dashboard SRS depuis la TUI ou via `rekall review --stats`.

**Acceptance Scenarios**:

1. **Given** des entrées avec historique de révisions, **When** l'utilisateur consulte le dashboard SRS, **Then** il voit : entrées dues aujourd'hui, dues cette semaine, entrées jamais révisées
2. **Given** un dashboard affiché, **When** l'utilisateur sélectionne une catégorie, **Then** il peut démarrer une session ciblée (ex: "Réviser les 5 plus en retard")

---

### User Story 3 - Initialisation automatique SRS (Priority: P3)

En tant qu'utilisateur, je veux que les nouvelles entrées soient automatiquement incluses dans le système SRS pour ne pas oublier de les réviser.

**Why this priority**: Amélioration de workflow, le système fonctionne sans (révisions manuelles).

**Independent Test**: Peut être testé en créant une nouvelle entrée et vérifiant que `next_review` est automatiquement défini.

**Acceptance Scenarios**:

1. **Given** une configuration `srs_auto_init = true`, **When** une nouvelle entrée est créée, **Then** `next_review` est défini à demain (J+1)
2. **Given** une entrée existante sans `next_review`, **When** l'utilisateur exécute `rekall review --init`, **Then** toutes les entrées sans révision programmée sont initialisées

---

### User Story 4 - Révision depuis CLI améliorée (Priority: P3)

En tant qu'utilisateur qui préfère le terminal, je veux une commande CLI complète pour les révisions avec options de filtrage et statistiques.

**Why this priority**: La TUI couvre le cas principal, CLI est une alternative.

**Independent Test**: Peut être testé via `rekall review --project X --limit 5 --stats`.

**Acceptance Scenarios**:

1. **Given** des entrées dues, **When** `rekall review --limit 5`, **Then** les 5 entrées les plus prioritaires sont présentées interactivement
2. **Given** des révisions effectuées, **When** `rekall review --stats`, **Then** les statistiques de révision s'affichent (total révisé, taux de succès, streak)

---

### Edge Cases

- Que se passe-t-il si l'utilisateur quitte en pleine révision ? → Révisions partielles sont sauvegardées, entrée en cours non comptée
- Comment gérer les entrées dépréciées ? → Exclues automatiquement du SRS
- Que faire si `ease_factor` devient trop bas (< 1.3) ? → Plancher à 1.3 (déjà implémenté dans `record_review`)
- Comment gérer une base avec 0 entrées initialisées pour SRS ? → Proposer `rekall review --init` pour initialiser

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Le système DOIT afficher les entrées dues dans un mode TUI dédié avec contenu complet
- **FR-002**: Le système DOIT permettre de noter chaque révision sur une échelle 1-4 (Again/Hard/Good/Easy)
- **FR-003**: Le système DOIT appliquer l'algorithme SM-2 existant pour calculer la prochaine date de révision
- **FR-004**: Le système DOIT exclure les entrées avec status `deprecated` ou `superseded` du SRS
- **FR-005**: Le système DOIT afficher un résumé à la fin de chaque session (nombre révisé, temps, score moyen)
- **FR-006**: Le système DOIT permettre de filtrer les révisions par projet
- **FR-007**: Le système DOIT sauvegarder les révisions partielles si la session est interrompue
- **FR-008**: Le dashboard DOIT afficher : entrées dues aujourd'hui, cette semaine, jamais révisées
- **FR-009**: La commande CLI DOIT supporter `--stats` pour afficher les statistiques de révision
- **FR-010**: Le système PEUT initialiser automatiquement `next_review` pour les nouvelles entrées (configurable)

### Key Entities

- **ReviewItem**: Entrée due pour révision avec métadonnées (days_overdue, priority) - existe déjà
- **ReviewSession**: Session de révision (entrées révisées, scores, durée) - à créer pour stats
- **ReviewStats**: Statistiques agrégées (total révisé, taux succès, streak actuel) - à créer

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les utilisateurs peuvent compléter une session de 10 révisions en moins de 5 minutes
- **SC-002**: 100% des révisions effectuées sont correctement enregistrées avec mise à jour SM-2
- **SC-003**: Le dashboard affiche les statistiques en moins de 1 seconde
- **SC-004**: Les entrées dépréciées ne sont jamais présentées en révision
- **SC-005**: Le système supporte 10 000+ entrées sans dégradation de performance

## Assumptions

- L'algorithme SM-2 existant dans `db.record_review()` est correct et ne nécessite pas de modification
- Les traductions i18n pour le système Review existent déjà dans `rekall/i18n.py`
- La TUI existante (Textual) peut être étendue avec un nouveau mode Review
- Les champs `next_review`, `review_interval`, `ease_factor` existent déjà dans le schéma DB
