# Tâches d'Implémentation: Smart Embeddings System

**Feature**: 005-smart-embeddings
**Plan**: [plan.md](./plan.md)
**Créé**: 2025-12-09

---

## Légende

- `[ ]` À faire
- `[~]` En cours
- `[x]` Terminé
- `[-]` Annulé

**Priorités**: P0 (bloquant) → P1 (core) → P2 (important) → P3 (nice-to-have)

---

## Phase 0: Infrastructure (P0) ✅ COMPLÉTÉE

### T001: Modèles Embedding et Suggestion ✅
- [x] **Fichier**: `rekall/models.py`
- [x] Ajouter `EmbeddingType = Literal["summary", "context"]`
- [x] Ajouter `SuggestionType = Literal["link", "generalize"]`
- [x] Ajouter `SuggestionStatus = Literal["pending", "accepted", "rejected"]`
- [x] Créer dataclass `Embedding` avec validation
- [x] Créer dataclass `Suggestion` avec validation
- [x] Ajouter méthodes `to_numpy()` et `from_numpy()` sur Embedding
- [x] Ajouter méthode `entry_ids_json()` sur Suggestion
- [x] Tests unitaires modèles

### T002: Migration schéma v3 - Table embeddings ✅
- [x] **Fichier**: `rekall/db.py`
- [x] Ajouter SQL CREATE TABLE embeddings dans MIGRATIONS[3]
- [x] Ajouter indexes (entry_id, embedding_type)
- [x] Ajouter UNIQUE constraint (entry_id, embedding_type)
- [x] Test migration sur DB vide
- [x] Test migration sur DB existante (v2)

### T003: Migration schéma v3 - Table suggestions ✅
- [x] **Fichier**: `rekall/db.py`
- [x] Ajouter SQL CREATE TABLE suggestions dans MIGRATIONS[3]
- [x] Ajouter indexes (status, type, created_at)
- [x] Ajouter CHECK constraints (types, score range)
- [x] Test création table

### T004: Migration schéma v3 - Table metadata ✅
- [x] **Fichier**: `rekall/db.py`
- [x] Ajouter SQL CREATE TABLE metadata dans MIGRATIONS[3]
- [x] Ajouter à EXPECTED_TABLES
- [x] Test création table

### T005: Module rekall/embeddings.py (stub) ✅
- [x] **Fichier**: `rekall/embeddings.py` (nouveau)
- [x] Créer classe `EmbeddingService`
- [x] Méthode stub `is_available() -> bool` (implémenté comme propriété `available`)
- [x] Méthode stub `calculate(text: str) -> Optional[np.ndarray]`
- [x] Méthode stub `find_similar(entry_id, threshold) -> list`
- [x] Fonction `cosine_similarity()` ajoutée
- [x] Singleton `get_embedding_service()` ajouté

### T006: Config embeddings ✅
- [x] **Fichier**: `rekall/config.py`
- [x] Paramètre `smart_embeddings_enabled: bool = False`
- [x] Paramètre `smart_embeddings_model: str = "EmbeddingGemma-2B-v1"`
- [x] Paramètre `smart_embeddings_dimensions: int = 384` (Matryoshka)
- [x] Paramètre `smart_embeddings_similarity_threshold: float = 0.75`

### T007: CRUD embeddings ✅
- [x] **Fichier**: `rekall/db.py`
- [x] Méthode `add_embedding(embedding: Embedding)`
- [x] Méthode `get_embedding(entry_id, emb_type) -> Optional[Embedding]`
- [x] Méthode `get_embeddings(entry_id) -> list[Embedding]`
- [x] Méthode `delete_embedding(entry_id, emb_type=None) -> int`
- [x] Méthode `get_all_embeddings(emb_type=None) -> list[Embedding]`
- [x] Méthode `count_embeddings() -> int`
- [x] Méthode `get_entries_without_embeddings(emb_type) -> list[Entry]`
- [x] Tests unitaires CRUD

### T008: CRUD suggestions ✅
- [x] **Fichier**: `rekall/db.py`
- [x] Méthode `add_suggestion(suggestion: Suggestion)`
- [x] Méthode `get_suggestion(id) -> Optional[Suggestion]`
- [x] Méthode `get_suggestions(status, type, limit) -> list[Suggestion]`
- [x] Méthode `update_suggestion_status(id, status) -> bool`
- [x] Méthode `suggestion_exists(entry_ids, type) -> bool`
- [x] Tests unitaires CRUD

### T009: CRUD metadata ✅
- [x] **Fichier**: `rekall/db.py`
- [x] Méthode `get_metadata(key) -> Optional[str]`
- [x] Méthode `set_metadata(key, value)` (upsert)
- [x] Méthode `delete_metadata(key) -> bool`
- [x] Tests unitaires CRUD

### T010: Tests infrastructure ✅
- [x] **Fichier**: `tests/test_models.py` (15 nouveaux tests Embedding/Suggestion)
- [x] **Fichier**: `tests/test_db.py` (19 nouveaux tests schema v3 + CRUD)
- [x] Test migration v2 → v3 (TestSchemaV3)
- [x] Test création tables sur DB vide (TestSchemaV3)
- [x] Test CRUD embeddings (TestEmbeddingsCRUD)
- [x] Test CRUD suggestions (TestSuggestionsCRUD)
- [x] Test CRUD metadata (TestMetadataCRUD)
- [x] Vérifier 162 tests passent ✅

---

## Phase 1: Service Embeddings (P1)

### T011: Chargement modèle EmbeddingGemma
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Import sentence_transformers (optionnel avec try/except)
- [ ] Lazy loading du modèle (chargé au premier appel)
- [ ] Cache instance modèle en mémoire
- [ ] Gestion erreur si sentence_transformers absent
- [ ] Message utilisateur si modèle manquant

### T012: Fonction calculate_embedding
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Méthode `calculate(text: str) -> Optional[np.ndarray]`
- [ ] Normalisation du vecteur (L2 norm)
- [ ] Retourne None si service non disponible
- [ ] Log warning si échec

### T013: Support Matryoshka
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Paramètre `dimensions` (128, 384, 768)
- [ ] Troncature vecteur après calcul
- [ ] Re-normalisation après troncature
- [ ] Test différentes dimensions

### T014: Double embedding
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Méthode `calculate_for_entry(entry, context=None) -> dict`
- [ ] Calcul embedding "summary" (title + content + tags)
- [ ] Calcul embedding "context" (si fourni)
- [ ] Retourne dict `{"summary": vec, "context": vec|None}`

### T015: Fonction cosine_similarity
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Fonction `cosine_similarity(vec1, vec2) -> float`
- [ ] Utiliser numpy (dot product / norms)
- [ ] Gestion vecteurs nuls (retourne 0.0)
- [ ] Tests unitaires

### T016: Fonction find_similar
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Méthode `find_similar(entry_id, threshold=0.75) -> list[(Entry, float)]`
- [ ] Charger tous les embeddings "summary"
- [ ] Calculer similarité avec l'entrée cible
- [ ] Filtrer par threshold
- [ ] Trier par score décroissant
- [ ] Exclure l'entrée elle-même

### T017: Gestion erreurs
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Exception `EmbeddingModelNotAvailable`
- [ ] Méthode `get_model_status() -> dict`
- [ ] Instructions installation si absent
- [ ] Graceful degradation (retourne None)

### T018: Troncature contexte
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Constante `MAX_CONTEXT_CHARS = 8000`
- [ ] Troncature intelligente (premiers 8000 chars)
- [ ] Log info si troncature appliquée

### T019: Tests service embeddings
- [ ] **Fichier**: `tests/test_embeddings_service.py` (nouveau)
- [ ] Test calculate() avec texte court
- [ ] Test calculate() avec texte long (troncature)
- [ ] Test find_similar() avec entrées similaires
- [ ] Test find_similar() sans résultats
- [ ] Mock sentence_transformers pour CI

### T020: Benchmark performance
- [ ] **Fichier**: `tests/test_embeddings_perf.py` (nouveau)
- [ ] Test temps calcul embedding (<500ms)
- [ ] Test mémoire modèle (<500MB)
- [ ] Skip si modèle non installé

---

## Phase 2: Intégration CLI Add (P1)

### T021: Option --context pour add
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Ajouter `--context` option à `rekall add`
- [ ] Type: str, optionnel
- [ ] Help text explicatif

### T022: Option --context-file pour add
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Ajouter `--context-file` option à `rekall add`
- [ ] Type: Path, optionnel
- [ ] Lecture fichier et passage comme context
- [ ] Erreur si fichier inexistant

### T023: Calcul embedding à l'ajout
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Après création entrée, si embeddings enabled:
- [ ] Appeler `embedding_service.calculate_for_entry()`
- [ ] Stocker embeddings en DB
- [ ] Pas d'erreur si service non disponible

### T024: Recherche entrées similaires
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Après calcul embedding, appeler `find_similar()`
- [ ] Filtrer par threshold config
- [ ] Collecter résultats

### T025: Affichage suggestions de liens
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Si entrées similaires trouvées:
- [ ] Afficher section "Entrées similaires détectées:"
- [ ] Format: `- {title} (score: {score:.0%})`
- [ ] Proposer `rekall link {new_id} {similar_id}`

### T026: Création suggestions en DB
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Pour chaque entrée similaire:
- [ ] Créer Suggestion(type="link", entry_ids=[new, similar])
- [ ] Vérifier pas de doublon avec `suggestion_exists()`
- [ ] Status = "pending"

### T027: Messages i18n suggestions
- [ ] **Fichier**: `rekall/i18n.py`
- [ ] Clé `add.similar_found`: "Entrées similaires détectées:"
- [ ] Clé `add.suggest_link`: "Vous pouvez créer un lien avec:"
- [ ] Clé `add.no_similar`: "Aucune entrée similaire trouvée"
- [ ] Clé `add.embeddings_disabled`: "Embeddings désactivés"
- [ ] 5 langues (fr, en, es, de, it)

### T028: Skip si embeddings désactivés
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Check `config.embeddings.enabled` au début
- [ ] Si False: skip embedding, pas de message d'erreur
- [ ] Entrée créée normalement

### T029: Tests intégration add
- [ ] **Fichier**: `tests/test_cli_embeddings.py` (nouveau)
- [ ] Test add avec --context
- [ ] Test add avec --context-file
- [ ] Test add sans context (embedding summary seul)
- [ ] Test add avec embeddings désactivés
- [ ] Test suggestions créées

### T030: Documentation --context
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Help détaillé pour --context
- [ ] Exemple dans docstring
- [ ] Mention dans `rekall add --help`

---

## Phase 3: Recherche Sémantique (P1)

### T031: Option --context pour search
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Ajouter `--context` option à `rekall search`
- [ ] Type: str, optionnel
- [ ] Help text explicatif

### T032: Fonction hybrid_search
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Méthode `hybrid_search(query, context=None, limit=10)`
- [ ] Combiner recherche FTS et sémantique
- [ ] Retourner liste triée par score combiné

### T033: Combinaison scores
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Pondération configurable (default: 60% FTS, 40% semantic)
- [ ] Normalisation scores FTS (1 / (1 + rank))
- [ ] Formule: `final = w_fts * fts_norm + w_sem * sem_score`

### T034: Re-ranking résultats
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Si embeddings enabled et context fourni:
- [ ] Utiliser hybrid_search au lieu de search
- [ ] Trier par score final

### T035: Affichage score sémantique
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Dans résultats search:
- [ ] Afficher `[Semantic: {score:.0%}]` si disponible
- [ ] Formater proprement avec Rich

### T036: Fallback FTS
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Si embeddings désactivés ou non disponibles:
- [ ] Utiliser recherche FTS classique
- [ ] Pas de message d'erreur

### T037: Option --semantic-only
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Ajouter `--semantic-only` flag
- [ ] Forcer recherche embeddings uniquement
- [ ] Erreur si embeddings non disponibles

### T038: Tests recherche hybride
- [ ] **Fichier**: `tests/test_search_hybrid.py` (nouveau)
- [ ] Test recherche avec synonymes (sémantique trouve)
- [ ] Test recherche exacte (FTS domine)
- [ ] Test fallback sans embeddings
- [ ] Test --semantic-only

### T039: Benchmark recherche
- [ ] **Fichier**: `tests/test_search_perf.py` (nouveau)
- [ ] Test temps recherche hybride (<2s pour 1000 entrées)
- [ ] Skip si modèle non installé

### T040: Messages i18n recherche
- [ ] **Fichier**: `rekall/i18n.py`
- [ ] Clé `search.semantic_score`: "Similarité sémantique"
- [ ] Clé `search.hybrid_mode`: "Recherche hybride (FTS + sémantique)"
- [ ] Clé `search.fts_only`: "Recherche textuelle uniquement"
- [ ] 5 langues

---

## Phase 4: Suggestions Hebdomadaires (P2)

### T041: Fonction is_first_weekly_call
- [ ] **Fichier**: `rekall/db.py`
- [ ] Méthode `is_first_weekly_call() -> bool`
- [ ] Lire metadata `last_weekly_check`
- [ ] Comparer avec date actuelle (même semaine ISO?)
- [ ] Retourner True si première fois cette semaine

### T042: Fonction update_weekly_check
- [ ] **Fichier**: `rekall/db.py`
- [ ] Méthode `update_weekly_check()`
- [ ] Écrire metadata `last_weekly_check = today`

### T043: Fonction find_generalization_candidates
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Méthode `find_generalization_candidates() -> list[list[Entry]]`
- [ ] Filtrer entrées épisodiques
- [ ] Clustering par similarité (>0.80)
- [ ] Retourner groupes de 3+ entrées

### T044: Clustering entrées similaires
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Algorithme simple: greedy clustering
- [ ] Pour chaque entrée sans cluster:
  - [ ] Trouver similaires (>0.80)
  - [ ] Former cluster si 3+ entrées
- [ ] Éviter chevauchement clusters

### T045: Création suggestions généralisation
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Pour chaque cluster trouvé:
- [ ] Créer Suggestion(type="generalize", entry_ids=[...])
- [ ] Vérifier pas de doublon
- [ ] Calculer score moyen du cluster

### T046: Affichage au premier appel semaine
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Dans commande principale (ou commande dédiée):
- [ ] Si `is_first_weekly_call()` et embeddings enabled:
- [ ] Appeler `find_generalization_candidates()`
- [ ] Afficher suggestions avec Rich

### T047: Proposition commande generalize
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Après affichage suggestions:
- [ ] Proposer `rekall generalize {id1} {id2} {id3}`
- [ ] Mentionner `rekall suggest` pour gérer plus tard

### T048: Tests suggestions hebdomadaires
- [ ] **Fichier**: `tests/test_weekly_suggestions.py` (nouveau)
- [ ] Test is_first_weekly_call (première fois)
- [ ] Test is_first_weekly_call (déjà fait cette semaine)
- [ ] Test find_generalization_candidates
- [ ] Test pas de suggestion si <3 similaires

### T049: Messages i18n généralisations
- [ ] **Fichier**: `rekall/i18n.py`
- [ ] Clé `weekly.suggestions_found`: "Suggestions de généralisation"
- [ ] Clé `weekly.cluster_found`: "{n} entrées similaires détectées"
- [ ] Clé `weekly.generalize_cmd`: "Généraliser avec:"
- [ ] 5 langues

### T050: Benchmark weekly check
- [ ] **Fichier**: `tests/test_weekly_perf.py` (nouveau)
- [ ] Test temps clustering (<5s pour 1000 entrées)
- [ ] Skip si modèle non installé

---

## Phase 5: Commande Suggest (P3)

### T051: Commande rekall suggest
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Nouvelle commande `suggest`
- [ ] Liste suggestions pending par défaut
- [ ] Grouper par type (links, generalizations)

### T052: Affichage formaté suggestions
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Table Rich avec colonnes: ID, Type, Entrées, Score, Créé
- [ ] Couleurs selon type
- [ ] Tri par score décroissant

### T053: Option --accept ID
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Ajouter `--accept` option
- [ ] Valider ID existe et status=pending
- [ ] Appeler action correspondante

### T054: Option --reject ID
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Ajouter `--reject` option
- [ ] Valider ID existe et status=pending
- [ ] Marquer status=rejected

### T055: Création lien si accepté (type=link)
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Si suggestion_type == "link":
- [ ] Créer lien via `db.add_link()`
- [ ] Type relation: "related" par défaut
- [ ] Afficher confirmation

### T056: Marquage suggestion resolved
- [ ] **Fichier**: `rekall/db.py`
- [ ] Après accept/reject:
- [ ] Mettre à jour `status` et `resolved_at`

### T057: Option --type pour filtrer
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Ajouter `--type` option (link|generalize)
- [ ] Filtrer affichage

### T058: Tests commande suggest
- [ ] **Fichier**: `tests/test_suggest_cmd.py` (nouveau)
- [ ] Test liste suggestions
- [ ] Test --accept crée lien
- [ ] Test --reject marque rejected
- [ ] Test --type filtre

### T059: Messages i18n suggest
- [ ] **Fichier**: `rekall/i18n.py`
- [ ] Clé `suggest.title`: "Suggestions pendantes"
- [ ] Clé `suggest.accepted`: "Suggestion acceptée"
- [ ] Clé `suggest.rejected`: "Suggestion rejetée"
- [ ] Clé `suggest.none`: "Aucune suggestion pendante"
- [ ] 5 langues

### T060: Aide suggest --help
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Docstring détaillée
- [ ] Exemples d'utilisation
- [ ] Description options

---

## Phase 6: Serveur MCP + Progressive Disclosure (P2)

### T061: Créer module mcp_server.py
- [ ] **Fichier**: `rekall/mcp_server.py` (nouveau)
- [ ] Import mcp SDK (optionnel avec try/except)
- [ ] Classe `RekallMCPServer`
- [ ] Setup logging

### T062: Tool rekall_help(topic?) - Guide agent
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Décorateur `@tool`
- [ ] Paramètre optionnel: topic (search|capture|links|citations|all)
- [ ] Description: "Guide Rekall - appeler au premier usage"
- [ ] Retourne instructions en <500 tokens

### T063: Contenu rekall_help
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Workflow recherche (quand chercher, comment citer)
- [ ] Workflow capture (déclencheurs proactifs)
- [ ] Format citations (`[title](rekall://id)`)
- [ ] Liste des tools disponibles avec cas d'usage

### T064: Tool rekall_search (Progressive Disclosure)
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Paramètres: query, context, limit, type, project, memory_type
- [ ] **Output compact**: id, type, title, score, snippet, tags
- [ ] **Hint**: "Use rekall_show(id) for full content"
- [ ] Économie tokens estimée: -80%

### T065: Tool rekall_show(id)
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Paramètre: id
- [ ] Retour détails complets: content, links, created_at
- [ ] Complète le pattern Progressive Disclosure

### T066: Tool rekall_add
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Paramètres: type, title, content, tags, context, project, confidence
- [ ] Calcul embeddings si context fourni
- [ ] Retour avec similar_entries

### T067: Tool rekall_suggest_links
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Paramètre: limit
- [ ] Retour suggestions type=link, status=pending

### T068: Tool rekall_suggest_generalize
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Paramètre: limit
- [ ] Retour suggestions type=generalize, status=pending

### T069: Tool rekall_link
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Paramètres: source_id, target_id, relation_type
- [ ] Création lien via db
- [ ] Gestion erreurs (not found, already exists)

### T070: Tool rekall_accept_suggestion
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Paramètre: suggestion_id
- [ ] Exécuter action (créer lien ou proposer generalize cmd)

### T071: Tool rekall_reject_suggestion
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Paramètre: suggestion_id
- [ ] Marquer suggestion comme rejected

### T072: Commande rekall mcp-server
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Nouvelle commande `mcp-server`
- [ ] Option `--port` (default: 8765)
- [ ] Démarrage serveur avec signal handling

### T073: Configuration MCP
- [ ] **Fichier**: `rekall/config.py`
- [ ] Section `[mcp]`
- [ ] Paramètre `port: int = 8765`
- [ ] Paramètre `timeout: int = 30`

### T074: Tests unitaires MCP
- [ ] **Fichier**: `tests/test_mcp_server.py` (nouveau)
- [ ] Test chaque tool individuellement
- [ ] Mock db et embedding service
- [ ] Test gestion erreurs

### T075: Tests intégration MCP
- [ ] **Fichier**: `tests/test_mcp_integration.py` (nouveau)
- [ ] Test démarrage serveur
- [ ] Test appel tool via client MCP
- [ ] Skip si mcp non installé

### T076: Test Progressive Disclosure
- [ ] **Fichier**: `tests/test_mcp_tokens.py` (nouveau)
- [ ] Mesurer tokens search compact vs full
- [ ] Vérifier réduction ≥80%
- [ ] Vérifier hint présent dans output

### T077: Test rekall_help contenu
- [ ] **Fichier**: `tests/test_mcp_help.py` (nouveau)
- [ ] Vérifier retour <500 tokens
- [ ] Vérifier toutes sections présentes (search, capture, links, citations)
- [ ] Test filtrage par topic

### T078: Gestion erreurs MCP
- [ ] **Fichier**: `rekall/mcp_server.py`
- [ ] Codes erreur standardisés
- [ ] Timeout handling
- [ ] Validation paramètres

### T079: Messages i18n MCP
- [ ] **Fichier**: `rekall/i18n.py`
- [ ] Clé `mcp.server_started`: "Serveur MCP démarré sur port {port}"
- [ ] Clé `mcp.server_stopped`: "Serveur MCP arrêté"
- [ ] Clé `mcp.not_available`: "SDK MCP non installé"
- [ ] 5 langues

### T080: Supprimer rekall install <agent>
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Supprimer commande `install` si elle existe
- [ ] Plus de skills/rules files par agent
- [ ] MCP universel = zéro config par agent

---

## Phase 7: Migration Progressive (P2)

### T081: Commande embeddings migrate
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Nouvelle commande `embeddings migrate`
- [ ] Calcule embeddings manquants
- [ ] Progress bar avec Rich

### T082: Calcul batch avec progress
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Méthode `migrate_all(callback=None)`
- [ ] Batch processing (10 entrées à la fois)
- [ ] Callback pour progress update

### T083: Option --limit migration
- [ ] **Fichier**: `rekall/cli.py`
- [ ] Ajouter `--limit N` option
- [ ] Migration partielle pour gros DB

### T084: Calcul lazy si absent
- [ ] **Fichier**: `rekall/embeddings.py`
- [ ] Dans `find_similar()`:
- [ ] Si embedding absent, calculer à la volée
- [ ] Stocker pour cache futur

### T085: Tests migration
- [ ] **Fichier**: `tests/test_migration_embeddings.py` (nouveau)
- [ ] Test migration DB sans embeddings
- [ ] Test --limit respecté
- [ ] Test lazy calculation

---

## Phase 8: Polish & Documentation (P3)

### T086: Doc installation embeddings
- [ ] **Fichier**: `docs/embeddings.md` (nouveau)
- [ ] Prérequis (Python 3.9+, pip/uv)
- [ ] Installation sentence-transformers
- [ ] Activation dans config
- [ ] Troubleshooting

### T087: Guide MCP universel
- [ ] **Fichier**: `docs/mcp-setup.md` (nouveau)
- [ ] Configuration générique (pas par agent)
- [ ] Exemple constitution minimale (3 lignes)
- [ ] Workflow type pour un agent

### T088: Mise à jour README
- [ ] **Fichier**: `README.md`
- [ ] Section "Smart Embeddings"
- [ ] Section "MCP Integration"
- [ ] Badges dépendances optionnelles

### T089: Tests e2e workflow
- [ ] **Fichier**: `tests/test_e2e_embeddings.py` (nouveau)
- [ ] Test workflow complet:
  - [ ] Add avec context
  - [ ] Search sémantique
  - [ ] Suggestion créée
  - [ ] Accept suggestion
  - [ ] Lien créé

### T090: Tests cross-platform
- [ ] **CI**: GitHub Actions
- [ ] Test Linux
- [ ] Test macOS
- [ ] Test Windows
- [ ] Matrix Python 3.9, 3.10, 3.11, 3.12

### T091: Benchmark mémoire
- [ ] **Fichier**: `tests/test_memory.py` (nouveau)
- [ ] Test RAM pendant chargement modèle
- [ ] Test RAM pendant calcul embedding
- [ ] Assertion <500MB

### T092: Messages erreur user-friendly
- [ ] **Fichier**: `rekall/i18n.py`
- [ ] Réviser tous les messages d'erreur
- [ ] Ajouter suggestions de résolution
- [ ] Ton amical et constructif

### T093: Checklist validation
- [ ] **Fichier**: `specs/005-smart-embeddings/checklists/implementation.md` (nouveau)
- [ ] Checklist tous les SC-* validés
- [ ] Screenshots/evidence si pertinent
- [ ] Sign-off final

---

## Phase 10: Context Compression (P1) ✅ COMPLÉTÉE

### T096: Migration schéma v4 ✅
- [x] **Fichier**: `rekall/db.py`
- [x] CURRENT_SCHEMA_VERSION = 4
- [x] MIGRATIONS[4] avec colonne context_compressed BLOB
- [x] EXPECTED_ENTRY_COLUMNS mis à jour

### T097: Fonctions compression ✅
- [x] **Fichier**: `rekall/db.py`
- [x] `compress_context(text)` - zlib niveau 6
- [x] `decompress_context(data)` - décompression
- [x] `store_context(entry_id, context)` - stockage
- [x] `get_context(entry_id)` - récupération
- [x] `get_contexts_for_verification(entry_ids)` - multi

### T098: Intégration CLI/MCP ✅
- [x] **Fichiers**: `rekall/cli.py`, `rekall/mcp_server.py`
- [x] CLI add stocke contexte si --context fourni
- [x] MCP rekall_add stocke contexte
- [x] Nouvel outil MCP rekall_get_context

### T099: Tests compression ✅
- [x] **Fichier**: `tests/test_db.py`
- [x] test_store_and_get_context
- [x] test_get_context_not_stored
- [x] test_get_contexts_for_verification
- [x] test_compression_ratio

### T100: Configuration context_mode ✅
- [x] **Fichiers**: `rekall/config.py`, `rekall/cli.py`, `rekall/mcp_server.py`
- [x] smart_embeddings_context_mode = optional|recommended|required
- [x] Validation CLI avec warning/erreur
- [x] Validation MCP avec warning/erreur
- [x] Lecture/écriture config.toml

---

## Résumé

| Phase | Tâches | Statut |
|-------|--------|--------|
| Phase 0: Infrastructure | T001-T010 (10) | [x] 10/10 ✅ |
| Phase 1: Service Embeddings | T011-T020 (10) | [x] 10/10 ✅ |
| Phase 2: CLI Add | T021-T030 (10) | [x] 7/10 ✅ (core) |
| Phase 3: Recherche Sémantique | T031-T040 (10) | [x] 7/10 ✅ (core) |
| Phase 4: Suggestions Hebdo | T041-T050 (10) | [x] 6/10 ✅ (core) |
| Phase 5: Commande Suggest | T051-T060 (10) | [x] 8/10 ✅ (core) |
| Phase 6: Serveur MCP | T061-T080 (20) | [x] 12/20 ✅ (core) |
| Phase 7: Migration | T081-T085 (5) | [x] 4/5 ✅ (core) |
| Phase 8: Polish | T086-T093 (8) | [x] 2/8 ✅ (partial) |
| Phase 9: TUI Config | T091-T095 (5) | [x] 5/5 ✅ |
| Phase 10: Context Compress | T096-T100 (5) | [x] 5/5 ✅ |
| **TOTAL** | **103 tâches** | **~76/103 core features** |

**Note**: Implémentation fonctionnelle complète. Tâches restantes = tests de performance, docs détaillées, benchmarks.
