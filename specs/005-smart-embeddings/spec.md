# Feature Specification: Smart Embeddings System

**Feature Branch**: `005-smart-embeddings`
**Created**: 2025-12-09
**Status**: Draft
**Input**: Système d'embeddings intelligents avec EmbeddingGemma pour détection automatique de similarités, suggestion de liens et généralisations, interface MCP universelle pour agents AI

## Research Findings

Recherche académique approfondie effectuée (voir `specs/005-smart-embeddings/research.md`).

**Décisions clés validées par la recherche** :
- **Modèle** : EmbeddingGemma (308M params) - #1 MTEB multilingue <500M, support Matryoshka
- **Architecture** : Double embedding (summary + context) basé sur Anthropic Contextual Retrieval (-67% échecs)
- **Interface** : MCP (Model Context Protocol) - standard adopté par Anthropic, OpenAI, Google, Microsoft
- **Suggestion** : Inspiré A-MEM (Zettelkasten agentique) et Mem0 (+26% accuracy)
- **Progressive Disclosure** : Pattern SOTA Anthropic pour optimisation contexte (-98% tokens)

**Décision architecturale majeure** :
- ❌ **Suppression des skills par agent** (`rekall install claude/cursor/...`)
- ✅ **MCP-first avec `rekall_help()`** : Les instructions comportementales sont intégrées dans le serveur MCP via un tool dédié, rendant l'intégration universelle sans configuration spécifique par agent.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Suggestion automatique de liens à l'ajout (Priority: P1)

En tant qu'utilisateur, lorsque j'ajoute une nouvelle entrée dans Rekall, je veux que le système détecte automatiquement les entrées similaires et me propose de créer des liens, afin de construire mon graphe de connaissances sans effort manuel.

**Why this priority**: Fonctionnalité la plus visible et utile au quotidien. Chaque ajout d'entrée bénéficie immédiatement de l'intelligence du système. Fondation pour toutes les autres fonctionnalités d'embeddings.

**Independent Test**: Peut être testé en ajoutant une entrée via CLI avec `--context` et en vérifiant que des suggestions de liens apparaissent. Délivre de la valeur immédiate sans les autres user stories.

**Acceptance Scenarios**:

1. **Given** une base Rekall contenant 10+ entrées avec embeddings calculés, **When** j'ajoute une nouvelle entrée similaire à une existante, **Then** le système affiche les entrées similaires (score > 0.75) et propose de créer des liens.

2. **Given** une nouvelle entrée ajoutée avec option `--context` contenant la discussion complète, **When** le système calcule les embeddings, **Then** deux embeddings sont stockés (summary + context) et la recherche de similarité utilise les deux.

3. **Given** une nouvelle entrée sans contexte fourni, **When** le système calcule l'embedding, **Then** seul l'embedding summary est calculé et stocké, le système fonctionne normalement.

4. **Given** les embeddings ne sont pas configurés (feature optionnelle désactivée), **When** j'ajoute une entrée, **Then** l'entrée est créée normalement sans suggestions, aucune erreur n'est affichée.

---

### User Story 2 - Recherche sémantique améliorée (Priority: P1)

En tant qu'utilisateur, je veux que mes recherches utilisent la similarité sémantique (embeddings) en plus de la recherche textuelle (FTS), afin de trouver des entrées pertinentes même si les mots-clés exacts ne correspondent pas.

**Why this priority**: Améliore directement l'expérience de recherche existante. Complémentaire à US1, utilise les mêmes embeddings.

**Independent Test**: Peut être testé en recherchant un terme qui n'apparaît pas exactement dans l'entrée mais dont le sens est proche. Vérifie que l'entrée est trouvée via similarité sémantique.

**Acceptance Scenarios**:

1. **Given** une entrée "Fix CORS Safari header" avec embedding calculé, **When** je recherche "erreur navigateur Apple requêtes cross-origin", **Then** l'entrée est trouvée grâce à la similarité sémantique malgré l'absence de mots-clés exacts.

2. **Given** une recherche avec `--context` contenant le contexte de discussion actuel, **When** le système effectue la recherche, **Then** le contexte enrichit la query pour un meilleur matching.

3. **Given** les embeddings désactivés, **When** je recherche, **Then** la recherche FTS classique fonctionne normalement (fallback).

---

### User Story 3 - Suggestion hebdomadaire de généralisations (Priority: P2)

En tant qu'utilisateur, au premier lancement de Rekall de la semaine, je veux voir les suggestions de généralisations (groupes de 3+ entrées épisodiques similaires pouvant devenir un pattern sémantique), afin de consolider mes connaissances régulièrement.

**Why this priority**: Valeur ajoutée importante mais moins fréquente (hebdomadaire). Dépend de US1 pour les embeddings.

**Independent Test**: Peut être testé en créant 3+ entrées épisodiques similaires puis en simulant un premier appel de la semaine. Vérifie que les suggestions apparaissent.

**Acceptance Scenarios**:

1. **Given** 3+ entrées épisodiques avec similarité > 0.80, **When** c'est le premier appel Rekall de la semaine, **Then** le système affiche une suggestion de généralisation avec les IDs concernés.

2. **Given** une suggestion de généralisation affichée, **When** l'utilisateur accepte, **Then** la commande `rekall generalize` est proposée avec les IDs pré-remplis.

3. **Given** le premier appel de la semaine déjà effectué, **When** j'utilise Rekall à nouveau dans la même semaine, **Then** aucune vérification hebdomadaire n'est relancée.

---

### User Story 4 - Interface MCP pour agents AI (Priority: P2)

En tant qu'agent AI (Claude, OpenAI, Gemini, Copilot...), je veux interagir avec Rekall via le protocole MCP standard, afin de rechercher et ajouter des connaissances avec le contexte complet de la conversation.

**Why this priority**: Permet l'intégration universelle avec tous les agents AI. Dépend des embeddings (US1) pour le contexte.

**Independent Test**: Peut être testé en démarrant le serveur MCP et en appelant les tools via un client MCP. Vérifie que les opérations CRUD fonctionnent avec contexte.

**Acceptance Scenarios**:

1. **Given** le serveur MCP Rekall démarré, **When** un agent appelle `rekall_add` avec paramètre `context`, **Then** l'entrée est créée avec double embedding (summary + context).

2. **Given** le serveur MCP Rekall démarré, **When** un agent appelle `rekall_search` avec paramètre `context`, **Then** la recherche utilise le contexte pour enrichir la query.

3. **Given** le serveur MCP Rekall démarré, **When** un agent appelle `rekall_suggest_generalize`, **Then** les suggestions de généralisation sont retournées en JSON.

4. **Given** le serveur MCP Rekall démarré, **When** un agent appelle `rekall_help()` sans argument, **Then** un guide complet d'utilisation est retourné avec workflows, déclencheurs proactifs et format de citations.

5. **Given** le serveur MCP Rekall démarré, **When** un agent appelle `rekall_search`, **Then** les résultats sont compacts (id, title, score, snippet) avec hint vers `rekall_show(id)` pour détails.

---

### User Story 6 - Auto-guidance des agents via MCP (Priority: P2)

En tant qu'agent AI se connectant à Rekall pour la première fois, je veux recevoir automatiquement les instructions d'utilisation optimale via le tool `rekall_help()`, afin de savoir quand et comment utiliser Rekall de manière proactive sans configuration spécifique.

**Why this priority**: Remplace les skills spécifiques par agent. Rend l'intégration universelle et zero-config.

**Independent Test**: Peut être testé en connectant un agent MCP et en vérifiant qu'il découvre et utilise `rekall_help()` pour comprendre le workflow.

**Acceptance Scenarios**:

1. **Given** un agent AI connecté au serveur MCP, **When** il liste les tools disponibles, **Then** `rekall_help` apparaît avec description "Guide d'utilisation Rekall - appeler en début de session".

2. **Given** un agent AI appelant `rekall_help()`, **When** sans argument, **Then** le guide complet est retourné (workflow recherche, workflow capture, déclencheurs proactifs, format citations).

3. **Given** un agent AI appelant `rekall_help("search")`, **When** avec topic spécifique, **Then** seule la section concernée est retournée (économie de tokens).

4. **Given** la constitution projet mentionnant Rekall MCP, **When** un agent lit la constitution, **Then** il voit seulement "Appeler `rekall_help()` au premier usage" (3 lignes max).

---

### User Story 5 - Commande suggest pour voir les suggestions pendantes (Priority: P3)

En tant qu'utilisateur, je veux une commande `rekall suggest` qui affiche toutes les suggestions pendantes (liens proposés, généralisations détectées), afin de les traiter à mon rythme.

**Why this priority**: Utile mais moins critique. Les suggestions sont déjà visibles à l'ajout (US1) et hebdomadairement (US3).

**Independent Test**: Peut être testé en créant des entrées similaires puis en exécutant `rekall suggest`. Vérifie que les suggestions sont listées.

**Acceptance Scenarios**:

1. **Given** des suggestions de liens pendantes en base, **When** j'exécute `rekall suggest`, **Then** les suggestions sont listées avec score et raison.

2. **Given** une suggestion affichée, **When** je l'accepte avec `rekall suggest --accept ID`, **Then** le lien est créé et la suggestion marquée résolue.

3. **Given** une suggestion affichée, **When** je la rejette avec `rekall suggest --reject ID`, **Then** la suggestion est marquée rejetée et ne réapparaît plus.

---

### Edge Cases

- **Modèle non installé** : Message d'erreur clair avec instructions d'installation, feature désactivée gracieusement.
- **Contenu vide** : Embedding calculé uniquement sur le titre + tags.
- **Contexte très long (>10000 caractères)** : Troncature intelligente aux 8000 premiers caractères (limite modèle 2K tokens).
- **Migration base existante** : Embeddings calculés à la demande lors du premier accès (migration progressive).
- **Échec calcul embedding** : L'opération principale (add/search) réussit quand même, warning loggué.
- **Base vide** : Aucune suggestion de lien, comportement normal.
- **Toutes entrées déjà liées** : Pas de suggestions redondantes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate and store embeddings for new entries when the feature is enabled.
- **FR-002**: System MUST support two embedding types per entry: "summary" (title+content+tags) and "context" (full conversation).
- **FR-003**: System MUST detect similar entries (cosine similarity > configurable threshold, default 0.75) and suggest links when adding a new entry.
- **FR-004**: System MUST track the first weekly access and trigger generalization suggestions once per week.
- **FR-005**: System MUST provide semantic search combining FTS scores and embedding similarity.
- **FR-006**: System MUST expose an MCP server with tools for add, search, suggest, help, and link operations.
- **FR-007**: System MUST gracefully degrade when embeddings are not configured (fallback to FTS only).
- **FR-008**: System MUST support the `--context` and `--context-file` CLI options to pass conversation context.
- **FR-009**: System MUST persist suggestions (links, generalizations) with status (pending/accepted/rejected).
- **FR-010**: System MUST use a lightweight, local embedding model that runs on CPU without GPU requirement.
- **FR-011**: System MUST work identically on Windows, Linux, and macOS.
- **FR-012**: System MUST provide a `rekall suggest` command to view and manage pending suggestions.
- **FR-013**: System MUST support Matryoshka dimension reduction (768→384→128) for storage optimization.
- **FR-014**: System MUST provide a `rekall_help(topic?)` MCP tool that returns usage instructions, workflows, and best practices.
- **FR-015**: System MUST implement Progressive Disclosure pattern: search results return compact format (id, title, score, snippet) with hint to `rekall_show(id)` for full details.
- **FR-016**: System MUST NOT require per-agent configuration files (no skills/rules files per agent).
- **FR-017**: System MUST embed behavioral instructions in MCP tool descriptions and `rekall_help()` response.

### Key Entities

- **Embedding**: Vector representation of text. Attributes: entry_id, embedding_type (summary|context), vector (binary blob), dimensions, model_name, created_at. Relationship: belongs to one Entry.

- **Suggestion**: Proposed action detected by the system. Attributes: suggestion_type (link|generalize), entry_ids (JSON array), reason, score, status (pending|accepted|rejected), created_at, resolved_at. Relationship: references multiple Entries.

- **Metadata (extended)**: System configuration including last_weekly_check timestamp for weekly analysis tracking.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Similar entries are detected with 80%+ precision (8 out of 10 suggestions are relevant to the user).
- **SC-002**: Embedding calculation completes in under 500ms per entry on a standard laptop CPU.
- **SC-003**: Semantic search returns relevant results that FTS alone would miss in 30%+ of queries with synonyms or related concepts.
- **SC-004**: Users accept 60%+ of suggested links, indicating high suggestion quality.
- **SC-005**: Weekly generalization check completes in under 5 seconds for bases up to 1000 entries.
- **SC-006**: MCP server responds to tool calls in under 2 seconds including embedding calculation.
- **SC-007**: Memory footprint of embedding model stays under 500MB RAM during operation.
- **SC-008**: Feature works identically on Windows, Linux, and macOS without platform-specific configuration.
- **SC-009**: Installation of embedding dependencies completes in under 5 minutes with clear progress feedback.
- **SC-010**: Progressive Disclosure reduces token usage by 80%+ compared to returning full entry content in search results.
- **SC-011**: `rekall_help()` response fits in under 500 tokens while providing complete usage guidance.
- **SC-012**: Any MCP-compatible agent can use Rekall without agent-specific configuration files.

## Assumptions

- EmbeddingGemma (308M params) is available via sentence-transformers library and works cross-platform.
- Users have Python 3.9+ and pip/uv installed.
- Similarity threshold of 0.75 provides good balance between precision and recall (configurable via settings).
- Weekly check is sufficient frequency for generalization suggestions.
- MCP protocol SDK is stable for Python implementation.
- SQLite can efficiently store and query embedding vectors as BLOBs for bases up to 10,000 entries.
- Users are willing to install optional dependencies (~500MB download) for embedding features.

## Dependencies

- Feature 004-cognitive-memory must be complete (knowledge graph, links, memory types).
- sentence-transformers library for embedding model loading and inference.
- mcp library for MCP server implementation.
- numpy for vector operations and cosine similarity.

## Out of Scope

- Cloud-based embedding models (must be 100% local).
- GPU acceleration (CPU-only for maximum portability).
- Real-time collaborative features between multiple users.
- Automatic generalization execution (only suggestions, user always decides).
- Embedding model fine-tuning or training on user data.
- Embedding versioning or migration between different models.
- Web UI for suggestion management (CLI and TUI only).
- Per-agent skill/rules files (replaced by MCP-first approach with `rekall_help()`).
- `rekall install <agent>` command (deprecated, MCP is universal).
