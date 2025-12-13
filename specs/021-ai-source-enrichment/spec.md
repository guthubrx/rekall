# Feature Specification: AI Source Enrichment

**Feature Branch**: `021-ai-source-enrichment`
**Created**: 2025-12-13
**Status**: Draft
**Input**: Enrichissement AI des sources Rekall : classification automatique, tagging, scoring qualité, résumés. Architecture agent-first où Claude Code fait l'enrichissement via MCP tools.

## Research Findings

### Sources Consultées
- [Enterprise Knowledge: Auto-Classification](https://enterprise-knowledge.com/auto-classification-when-ai-vs-semantic-models/) - Distinction auto-classification vs auto-tagging
- [Springer: Capabilities and Challenges of LLMs in Metadata Extraction](https://link.springer.com/chapter/10.1007/978-981-96-0865-2_23) - Accuracy challenges
- [IBM Research: Lessons Learned in Knowledge Extraction](https://research.ibm.com/publications/lessons-learned-in-knowledge-extraction-from-unstructured-data-with-llms-for-material-discovery) - Practical lessons
- [Ontotext: LLM Integration for Knowledge Graph Enrichment](https://www.ontotext.com/company/news/ontotext-metadata-studio-3-9-features-llm-integration-for-knowledge-graph-enrichment-users-can-trust/) - Human-in-the-loop pattern

### Key Learnings
1. **Auto-classification vs Auto-tagging** : Classification = taxonomie prédéfinie, Tagging = keywords libres
2. **Accuracy not guaranteed** : LLMs can extract metadata extensively but accuracy varies
3. **Format matters** : JSON format recommended, temperature = 0 for deterministic outputs
4. **Human-in-the-loop critical** : Entities not linkable should be suggested to knowledge manager

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Voir les URLs individuelles d'une entrée (Priority: P1)

En tant qu'utilisateur Rekall, je veux voir les URLs individuelles stockées pour chaque entrée, afin de vérifier quelles sources ont été consultées et pouvoir les revisiter.

**Why this priority**: Quick win - les données existent déjà en base (`entry_sources.source_ref`), il suffit de les exposer. Valeur immédiate sans coût API.

**Independent Test**: Peut être testé en créant une entrée avec 3 URLs puis en vérifiant qu'elles sont toutes affichées individuellement.

**Acceptance Scenarios**:

1. **Given** une entrée avec 3 URLs stockées, **When** j'appelle l'outil MCP de listage, **Then** je vois les 3 URLs avec leur domaine associé
2. **Given** une entrée sans URLs, **When** j'appelle l'outil MCP, **Then** je reçois une liste vide avec un message explicite

---

### User Story 2 - Enrichir une source avec l'aide de l'agent (Priority: P1)

En tant qu'utilisateur travaillant avec Claude Code, je veux que l'agent puisse enrichir une source (ajouter tags, résumé, type), afin de gagner du temps sur la curation manuelle.

**Why this priority**: Cœur de la feature - l'agent Claude analyse la source et propose un enrichissement structuré.

**Independent Test**: Peut être testé en donnant une URL à l'agent et en vérifiant que les champs enrichis sont écrits en base.

**Acceptance Scenarios**:

1. **Given** une source existante sans tags, **When** l'agent enrichit cette source, **Then** des tags pertinents sont proposés et enregistrés
2. **Given** une source avec URL accessible, **When** l'agent enrichit, **Then** un résumé de 2-3 phrases est généré
3. **Given** une source avec URL inaccessible, **When** l'agent enrichit, **Then** l'enrichissement se base sur le domaine et les métadonnées existantes

---

### User Story 3 - Enrichissement batch de plusieurs sources (Priority: P2)

En tant qu'utilisateur avec beaucoup de sources non classifiées, je veux pouvoir lancer un enrichissement sur plusieurs sources à la fois, afin de rattraper le backlog efficacement.

**Why this priority**: Efficacité - traiter 10-50 sources en une seule commande plutôt qu'une par une.

**Independent Test**: Peut être testé en créant 5 sources vierges puis en lançant l'enrichissement batch et vérifiant que toutes sont enrichies.

**Acceptance Scenarios**:

1. **Given** 10 sources sans tags, **When** je lance l'enrichissement batch, **Then** les 10 sources sont enrichies avec un rapport de progression
2. **Given** un batch avec 2 erreurs sur 10, **When** le batch termine, **Then** je vois un résumé clair (8 succès, 2 échecs avec raisons)

---

### User Story 4 - Valider ou rejeter une suggestion de l'agent (Priority: P2)

En tant qu'utilisateur, je veux pouvoir valider ou rejeter les enrichissements proposés par l'agent, afin de garder le contrôle sur la qualité de ma base de connaissances.

**Why this priority**: Human-in-the-loop - essentiel pour la confiance et l'amélioration continue.

**Independent Test**: Peut être testé en enrichissant une source, puis en validant/rejetant et vérifiant l'état final.

**Acceptance Scenarios**:

1. **Given** un enrichissement proposé avec confiance > 80%, **When** je valide, **Then** l'enrichissement devient permanent et le statut passe à "validated"
2. **Given** un enrichissement proposé, **When** je rejette avec correction, **Then** ma correction est enregistrée à la place de la proposition

---

### User Story 5 - Obtenir des suggestions de sources de qualité (Priority: P3)

En tant qu'utilisateur ajoutant une nouvelle entrée, je veux que l'agent me suggère des sources de qualité pertinentes à partir du Research Hub, afin d'enrichir mes entrées avec des références fiables.

**Why this priority**: Découverte - utilise les fichiers `rekall/research/*.md` comme seed de sources validées.

**Independent Test**: Peut être testé en créant une entrée sur "RAG" et vérifiant que des sources du Research Hub sont suggérées.

**Acceptance Scenarios**:

1. **Given** une entrée sur le thème "vector databases", **When** je demande des suggestions, **Then** je reçois des sources pertinentes du Research Hub avec leur score de fiabilité
2. **Given** une entrée sur un thème sans correspondance, **When** je demande des suggestions, **Then** je reçois un message indiquant qu'aucune source connue ne correspond

---

### Edge Cases

- Que se passe-t-il si l'URL d'une source retourne une 404 lors de l'enrichissement ?
- Comment gérer une source avec du contenu dans une langue non supportée ?
- Que faire si l'agent propose des tags qui n'existent pas dans la taxonomie ?
- Comment traiter une source derrière un paywall ou login ?

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST permettre de lister les URLs individuelles stockées pour une entrée
- **FR-002**: System MUST permettre à l'agent d'enrichir une source avec tags, résumé, et type
- **FR-003**: System MUST stocker les enrichissements avec un niveau de confiance (0-100%)
- **FR-004**: System MUST distinguer les enrichissements "proposed" (non validés) des "validated" (confirmés par l'humain)
- **FR-005**: System MUST permettre de lancer un enrichissement batch sur N sources (limite configurable)
- **FR-006**: System MUST permettre à l'utilisateur de valider ou rejeter un enrichissement proposé
- **FR-007**: System MUST suggérer des sources de qualité depuis le Research Hub basé sur le thème d'une entrée
- **FR-008**: System MUST retourner des réponses structurées en JSON pour tous les outils MCP

### Key Entities

- **Source** : Représente une référence web (URL, domaine, tags, résumé, type, score, statut enrichissement)
- **Enrichment** : Proposition d'enrichissement (source_id, type, tags[], summary, confidence, status: proposed|validated|rejected)
- **ResearchSource** : Source de qualité du Research Hub (theme, url, reliability, description)

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Les utilisateurs peuvent voir toutes les URLs individuelles d'une entrée en moins de 2 secondes
- **SC-002**: L'enrichissement d'une source unique prend moins de 10 secondes (hors temps de fetch URL)
- **SC-003**: L'enrichissement batch de 10 sources affiche une progression et complète en moins de 2 minutes
- **SC-004**: 90% des enrichissements proposés avec confiance > 80% sont validés par l'utilisateur (mesure qualité)
- **SC-005**: Le système supporte 100% des sources stockées en base sans erreur de lecture
- **SC-006**: Les suggestions du Research Hub correspondent au thème demandé dans 80% des cas

---

## Architecture Decision

### Agent-First Approach

L'intelligence (classification, tagging, résumé) vient de l'agent Claude Code lui-même, pas d'un service backend qui appelle une API LLM externe.

**Pourquoi** :
- Pas de clé API à gérer côté utilisateur
- L'agent EST déjà un LLM (Sonnet)
- Coût inclus dans l'utilisation de Claude Code

**Conséquence** :
- Les MCP tools sont des outils de lecture/écriture, pas des outils "intelligents"
- L'agent analyse, puis appelle le tool pour persister
- Le backend Rekall ne fait pas d'appels LLM

---

## Out of Scope

- Interface TUI pour l'enrichissement (sera Feature 022)
- Scoring CRAAP multi-dimensions (v2)
- Clustering automatique par embeddings (v2)
- Apprentissage des validations/rejets (v2)
