# Feature Specification: Sources Medallion Architecture

**Feature Branch**: `013-sources-medallion`
**Created**: 2025-12-11
**Status**: Draft
**Input**: Architecture Medallion pour capture automatique des URLs depuis les CLIs IA (Claude, Cursor), enrichissement progressif, et promotion vers sources curées
**Design Document**: [docs/plans/2025-12-11-sources-medallion-design.md](../../docs/plans/2025-12-11-sources-medallion-design.md)

## Overview

Cette feature implémente une architecture en 3 couches (Bronze/Silver/Gold) pour :
1. **Capturer automatiquement** les URLs citées dans les conversations avec les CLIs IA
2. **Enrichir progressivement** les métadonnées (titre, description, classification)
3. **Promouvoir intelligemment** les sources pertinentes vers le système curé existant

L'objectif est de ne jamais perdre une source documentaire utile et de réduire le travail manuel de curation.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Import des URLs depuis l'historique Claude CLI (Priority: P1)

L'utilisateur veut récupérer toutes les URLs documentaires mentionnées dans ses conversations Claude Code passées pour les ajouter à sa base de connaissances.

**Why this priority**: C'est la fonctionnalité fondamentale - sans capture, pas de données à enrichir. Claude CLI est le CLI principal de l'utilisateur.

**Independent Test**: Lancer `rekall sources inbox import --cli claude`, vérifier que les URLs WebFetch apparaissent dans l'inbox avec leur contexte (question posée, projet).

**Acceptance Scenarios**:

1. **Given** un historique Claude CLI avec 50 conversations contenant 100 URLs, **When** j'exécute l'import Claude, **Then** les URLs valides sont ajoutées à l'inbox avec le projet et la question associée
2. **Given** un import déjà effectué il y a 2 jours, **When** j'exécute un nouvel import, **Then** seules les nouvelles URLs depuis le dernier import sont ajoutées (import incrémental CDC)
3. **Given** des URLs invalides (localhost, file://), **When** j'importe l'historique, **Then** elles sont marquées comme invalides et placées en quarantaine

---

### User Story 2 - Enrichissement automatique des sources (Priority: P1)

L'utilisateur veut que les URLs importées soient automatiquement enrichies avec les métadonnées (titre, description, type de contenu) sans intervention manuelle.

**Why this priority**: L'enrichissement transforme les URLs brutes en informations exploitables. Sans lui, l'inbox reste une liste d'URLs sans contexte.

**Independent Test**: Après import, attendre le job d'enrichissement et vérifier que les sources en staging ont un titre et un type de contenu classifié.

**Acceptance Scenarios**:

1. **Given** 20 URLs dans l'inbox Bronze, **When** le job d'enrichissement s'exécute, **Then** les métadonnées sont extraites et les sources passent en Silver staging
2. **Given** une même URL citée 3 fois dans des projets différents, **When** l'enrichissement s'exécute, **Then** une seule entrée Silver existe avec citation_count=3 et project_count=3
3. **Given** une URL inaccessible (404), **When** l'enrichissement s'exécute, **Then** la source est marquée is_accessible=false avec le code HTTP

---

### User Story 3 - Consultation et tri de l'inbox Bronze (Priority: P2)

L'utilisateur veut voir les sources capturées dans une interface tableau et pouvoir filtrer par CLI source ou projet.

**Why this priority**: Permet de visualiser ce qui a été capturé avant enrichissement et d'identifier les sources invalides.

**Independent Test**: Ouvrir le TUI inbox, vérifier l'affichage des colonnes URL/CLI/Projet/Date, tester le filtrage.

**Acceptance Scenarios**:

1. **Given** 50 sources dans l'inbox, **When** j'ouvre le TUI inbox, **Then** je vois un tableau avec URL, CLI source, projet et date de capture
2. **Given** des sources de Claude et Cursor, **When** je filtre par CLI=claude, **Then** seules les sources Claude sont affichées
3. **Given** 5 sources invalides, **When** j'ouvre la vue quarantine, **Then** je vois les URLs avec la raison d'invalidité

---

### User Story 4 - Consultation du staging Silver avec scores (Priority: P2)

L'utilisateur veut voir les sources enrichies avec leur score de promotion et identifier celles éligibles à la promotion automatique.

**Why this priority**: Permet de comprendre quelles sources sont les plus pertinentes et prêtes pour la promotion.

**Independent Test**: Ouvrir le TUI staging, vérifier les colonnes et indicateurs de promotion (⬆ = éligible, → = proche).

**Acceptance Scenarios**:

1. **Given** 30 sources en staging, **When** j'ouvre le TUI staging, **Then** je vois domaine, titre, type, citations, projets et score avec indicateur
2. **Given** une source avec score ≥ seuil, **When** j'affiche le staging, **Then** elle a l'indicateur ⬆ (éligible promotion)
3. **Given** une source avec score ≥ 80% du seuil, **When** j'affiche le staging, **Then** elle a l'indicateur → (proche)

---

### User Story 5 - Promotion automatique sur seuil (Priority: P2)

L'utilisateur veut que les sources atteignant un score de promotion configurable soient automatiquement promues vers les sources Gold curées.

**Why this priority**: Réduit le travail manuel en promouvant automatiquement les sources fréquemment utilisées.

**Independent Test**: Créer une source avec score > seuil, vérifier qu'elle apparaît dans les sources Gold après le job de promotion.

**Acceptance Scenarios**:

1. **Given** une source Silver avec score 8.5 et seuil 5.0, **When** le job de promotion s'exécute, **Then** la source est ajoutée aux sources Gold avec is_promoted=true
2. **Given** une source promue, **When** je consulte les sources Gold, **Then** elle apparaît avec l'indicateur "promu automatiquement"
3. **Given** une source déjà promue, **When** le job s'exécute à nouveau, **Then** elle n'est pas dupliquée

---

### User Story 6 - Promotion et dépromouvoir manuelles (Priority: P2)

L'utilisateur veut pouvoir promouvoir manuellement une source Silver ou dépromouvoir une source Gold vers Silver.

**Why this priority**: Permet un contrôle fin sur les sources curées, indépendamment du score automatique.

**Independent Test**: Promouvoir manuellement une source depuis le TUI staging, puis la dépromouvoir depuis le TUI Gold.

**Acceptance Scenarios**:

1. **Given** une source Silver avec score 3.0 (sous le seuil), **When** je la promeut manuellement, **Then** elle passe en Gold
2. **Given** une source Gold promue, **When** je la dépromeut, **Then** elle retourne en Silver et disparaît des sources Gold
3. **Given** une tentative de dépromouvoir une source non-promue, **When** j'exécute la commande, **Then** un message d'erreur m'informe que seules les sources promues peuvent être dépromotues

---

### User Story 7 - Import depuis Cursor IDE (Priority: P3)

L'utilisateur veut importer les URLs de ses conversations Cursor pour les consolider avec celles de Claude.

**Why this priority**: Extension naturelle pour les utilisateurs multi-CLI, mais moins critique que Claude CLI.

**Independent Test**: Lancer `rekall sources inbox import --cli cursor`, vérifier que les URLs sont extraites depuis la base SQLite Cursor.

**Acceptance Scenarios**:

1. **Given** un historique Cursor avec 30 conversations, **When** j'importe depuis Cursor, **Then** les URLs sont ajoutées à l'inbox avec cli_source=cursor
2. **Given** une même URL présente dans Claude et Cursor, **When** les deux imports sont enrichis, **Then** une seule entrée Silver existe avec project_count=2

---

### User Story 8 - Configuration des poids et seuil de promotion (Priority: P3)

L'utilisateur veut ajuster les paramètres de promotion (poids citations, poids projets, seuil) selon ses préférences.

**Why this priority**: Permet la personnalisation, mais les valeurs par défaut couvrent la majorité des cas d'usage.

**Independent Test**: Modifier le seuil via CLI, vérifier que les indicateurs d'éligibilité changent dans le TUI staging.

**Acceptance Scenarios**:

1. **Given** un seuil par défaut de 5.0, **When** je le modifie à 3.0, **Then** plus de sources deviennent éligibles à la promotion
2. **Given** un poids project=2.0, **When** je le modifie à 4.0, **Then** les sources multi-projets ont un score plus élevé

---

### Edge Cases

- **Que se passe-t-il si** le fichier historique Claude est corrompu (JSON invalide) ?
  - Les lignes invalides sont ignorées, le reste est importé, un compteur d'erreurs est affiché
- **Que se passe-t-il si** Cursor n'est pas installé et l'utilisateur tente un import ?
  - Message d'erreur clair : "Cursor non détecté. Vérifiez que Cursor est installé."
- **Que se passe-t-il si** une URL devient inaccessible après promotion Gold ?
  - La vérification périodique marque is_accessible=false mais ne dépromeut pas automatiquement
- **Que se passe-t-il si** l'historique Claude a été nettoyé (rétention 30 jours par défaut) ?
  - L'import ne trouve que les conversations récentes, avertissement affiché
- **Que se passe-t-il si** le fetch de métadonnées timeout (site lent) ?
  - La source est créée sans titre/description, marquée pour retry ultérieur

---

## Requirements *(mandatory)*

### Functional Requirements

#### Capture (Bronze)

- **FR-001**: Le système DOIT extraire les URLs des conversations Claude CLI stockées dans `~/.claude/projects/`
- **FR-002**: Le système DOIT extraire les URLs des conversations Cursor stockées dans le répertoire workspaceStorage de Cursor
- **FR-003**: Le système DOIT capturer le contexte de chaque URL : question utilisateur, extrait réponse assistant, projet, conversation
- **FR-004**: Le système DOIT supporter l'import incrémental (CDC) en ne traitant que les nouvelles données depuis le dernier import
- **FR-005**: Le système DOIT valider les URLs et mettre en quarantaine les invalides (localhost, file://, etc.)
- **FR-006**: Le système DOIT fournir une architecture de connecteurs extensible pour ajouter d'autres CLIs

#### Enrichissement (Silver)

- **FR-007**: Le système DOIT extraire automatiquement le titre et la description des pages web
- **FR-008**: Le système DOIT classifier le type de contenu (documentation, repository, forum, blog, api, paper, other)
- **FR-009**: Le système DOIT détecter la langue de la page
- **FR-010**: Le système DOIT dédupliquer les URLs en fusionnant les entrées Bronze vers une seule Silver
- **FR-011**: Le système DOIT tracker le nombre de citations et le nombre de projets distincts par source
- **FR-012**: Le système DOIT vérifier l'accessibilité des URLs et enregistrer le code HTTP

#### Promotion (Gold)

- **FR-013**: Le système DOIT calculer un score de promotion basé sur : citations × poids + projets × poids + récence × poids
- **FR-014**: Le système DOIT appliquer un decay temporel au score (sources non vues récemment perdent du boost)
- **FR-015**: Le système DOIT promouvoir automatiquement les sources dépassant le seuil configurable
- **FR-016**: Le système DOIT permettre la promotion manuelle indépendamment du score
- **FR-017**: Le système DOIT permettre la dépromouvoir (Gold → Silver)
- **FR-018**: Le système DOIT marquer les sources promues dans la table Gold existante

#### Interface

- **FR-019**: Le système DOIT fournir un TUI DataTable pour l'inbox Bronze
- **FR-020**: Le système DOIT fournir un TUI DataTable pour le staging Silver avec indicateurs de promotion
- **FR-021**: Le système DOIT ajouter une action "Dépromouvoir" dans le TUI des sources Gold
- **FR-022**: Le système DOIT fournir des commandes CLI pour import, enrichissement, promotion, stats

### Key Entities

- **InboxEntry (Bronze)**: URL capturée brute avec contexte de conversation (cli_source, project, user_query, assistant_snippet), timestamp, validation status
- **StagingEntry (Silver)**: URL enrichie unique avec métadonnées (title, description, content_type, language), compteurs (citations, projets), score de promotion, status d'accessibilité
- **Source (Gold)**: Source curée existante, étendue avec flag is_promoted et timestamp promoted_at
- **ConnectorImport**: Tracking des imports par connecteur (last_import, last_marker) pour le CDC

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: L'utilisateur peut importer 100 conversations Claude en moins de 30 secondes
- **SC-002**: L'enrichissement de 50 URLs (fetch métadonnées) prend moins de 2 minutes
- **SC-003**: Les sources citées 3+ fois ou utilisées dans 2+ projets atteignent le seuil de promotion avec les poids par défaut
- **SC-004**: Le taux de faux positifs en quarantaine (URLs valides marquées invalides) est inférieur à 5%
- **SC-005**: La classification de type de contenu est correcte pour 80% des domaines connus (GitHub, StackOverflow, Medium, etc.)
- **SC-006**: Zéro source dupliquée en Gold après promotion (unicité URL garantie)
- **SC-007**: L'utilisateur peut naviguer dans 100 sources staging en moins de 2 secondes (TUI responsive)

---

## Assumptions

- L'historique Claude CLI est accessible dans `~/.claude/projects/` au format JSONL standard
- L'historique Cursor est accessible dans la base SQLite `state.vscdb`
- Les utilisateurs acceptent un délai de 5 secondes max pour le fetch de métadonnées par URL
- Les poids par défaut (citation=1.0, project=2.0, recency=0.5, seuil=5.0) conviennent à la majorité des utilisateurs
- La rétention de 30 jours de l'historique Claude est connue des utilisateurs

---

## Research Findings

Sources consultées pour ce design :

### Medallion Architecture
- [Databricks - Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture) : Pattern standard Bronze/Silver/Gold
- [Azure Databricks Guide](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion) : Best practices quarantine, CDC

### CLI History Extraction
- [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor) : Format JSONL Claude
- [cursor-chat-export](https://github.com/somogyijanos/cursor-chat-export) : Structure SQLite Cursor

### Scoring & Recommendation
- [Google ML - Recommendation Scoring](https://developers.google.com/machine-learning/recommendation/dnn/scoring) : Patterns multi-stage scoring
