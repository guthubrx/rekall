# Implementation Plan: Smart Embeddings System

**Branch**: `005-smart-embeddings` | **Date**: 2025-12-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-smart-embeddings/spec.md`

## Summary

Système d'embeddings intelligents pour Rekall utilisant EmbeddingGemma (308M params) avec :
- Double embedding (summary + context) pour recherche sémantique améliorée
- Détection automatique de similarités et suggestion de liens
- Serveur MCP universel pour intégration avec tous les agents AI
- Progressive Disclosure pour optimisation des tokens (-80%)

## Technical Context

**Language/Version**: Python 3.9+
**Primary Dependencies**: sentence-transformers, mcp, numpy, Rich
**Storage**: SQLite (extension schéma v3 avec tables embeddings, suggestions, metadata)
**Testing**: pytest avec fixtures SQLite in-memory
**Target Platform**: Windows, Linux, macOS (cross-platform, CPU-only)
**Project Type**: Single project (CLI + TUI + MCP Server)
**Performance Goals**: <500ms/embedding, <2s MCP response, <5s weekly check (1000 entries)
**Constraints**: <500MB RAM, 100% local (no cloud), optional dependencies
**Scale/Scope**: Jusqu'à 10,000 entrées, bases personnelles

## Constitution Check

*GATE: Passed*

- ✅ Article III : Processus SpecKit suivi (/specify → /plan → /tasks → /implement)
- ✅ Article VII : ADR créé si nécessaire (décisions dans research.md)
- ✅ Article IX : Recherche préalable effectuée (research.md complet)
- ✅ Article XV : Tests obligatoires définis (pytest, cross-platform)
- ✅ Article XVI : Worktree/branche isolée (005-smart-embeddings)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         REKALL (le cœur)                        │
│                                                                 │
│   db.py │ embeddings.py │ suggest.py │ models.py │ config.py   │
│                                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌──────────┐    ┌──────────┐    ┌──────────────┐
    │   CLI    │    │   TUI    │    │  MCP Server  │
    │ (humains)│    │ (browse) │    │  (agents AI) │
    └──────────┘    └──────────┘    └──────────────┘
         │               │                  │
         ▼               ▼                  ▼
    $ rekall add     $ rekall tui     Claude/OpenAI/
    $ rekall search                   Gemini/Copilot
```

### MCP Server Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    AGENTS AI (Clients)                   │
│  Claude | OpenAI | Gemini | Copilot | Cursor | Zed      │
└─────────────────────────┬───────────────────────────────┘
                          │ JSON-RPC 2.0 (stdio)
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   REKALL MCP SERVER                      │
│                                                          │
│  Tools (9):                                              │
│  1. rekall_help(topic?)     → Guide agent, <500 tokens   │
│  2. rekall_search(query)    → Compact output (Prog.Disc.)│
│  3. rekall_add(...)         → Avec context optionnel     │
│  4. rekall_show(id)         → Détails complets           │
│  5. rekall_suggest_links()  → Liens pendants             │
│  6. rekall_suggest_gen...   → Généralisations            │
│  7. rekall_link(...)        → Créer lien                 │
│  8. rekall_accept_sugg(id)  → Accepter suggestion        │
│  9. rekall_reject_sugg(id)  → Rejeter suggestion         │
│                                                          │
│  Progressive Disclosure:                                 │
│  • rekall_search → compact (id, title, score, snippet)   │
│  • rekall_show → full content (à la demande)             │
│  • Économie: -80% tokens                                 │
└─────────────────────────────────────────────────────────┘
```

## Décisions Architecturales

| Décision | Choix | Rationale |
|----------|-------|-----------|
| Modèle embedding | EmbeddingGemma 308M | #1 MTEB multilingue <500M, Matryoshka |
| Double embedding | summary + context | Anthropic Contextual Retrieval (-67% échecs) |
| Interface agents | MCP (pas skills) | Standard universel, zéro config par agent |
| Agent guidance | rekall_help() tool | Instructions dans MCP, pas de fichiers externes |
| Progressive Disclosure | Output compact + hint | SOTA Anthropic (-98% tokens) |
| Stockage vecteurs | SQLite BLOB | Simplicité, pas de dépendance externe |

## Project Structure

### Documentation (this feature)

```text
specs/005-smart-embeddings/
├── spec.md              # Spécification (6 User Stories, 17 FR)
├── plan.md              # Ce fichier
├── research.md          # Recherche SOTA (embeddings, MCP, Progressive Disclosure)
├── data-model.md        # Schéma SQLite v3, dataclasses Python
├── contracts/           # Contrats MCP (mcp-tools.md)
├── checklists/          # Checklists validation
└── tasks.md             # 93 tâches organisées en 8 phases
```

### Source Code (repository root)

```text
rekall/
├── __init__.py
├── cli.py               # Commandes Typer (add --context, search, suggest, mcp-server)
├── db.py                # CRUD + embeddings + suggestions
├── embeddings.py        # EmbeddingEngine (sentence-transformers)
├── suggest.py           # SuggestionEngine (liens, généralisations)
├── mcp_server.py        # Serveur MCP (9 tools)
├── models.py            # Dataclasses (Embedding, Suggestion)
├── config.py            # Configuration embeddings + MCP
├── i18n.py              # Messages multilingues
└── tui.py               # Interface TUI

tests/
├── test_embeddings.py           # Tests service embeddings
├── test_suggestions.py          # Tests détection similarités
├── test_search_semantic.py      # Tests recherche hybride
├── test_mcp_server.py           # Tests unitaires MCP
├── test_mcp_integration.py      # Tests intégration MCP
├── test_mcp_tokens.py           # Tests Progressive Disclosure
├── test_mcp_help.py             # Tests rekall_help() <500 tokens
├── test_migration_embeddings.py # Tests migration base existante
└── test_e2e_embeddings.py       # Tests workflow complet
```

---

## Phases de Développement

### Phase 0: Infrastructure DB (T001-T010)

**Objectif**: Migration schéma SQLite v2 → v3

| ID | Tâche | Fichiers | Priorité |
|----|-------|----------|----------|
| T001 | Créer table embeddings | `rekall/db.py` | P0 |
| T002 | Créer table suggestions | `rekall/db.py` | P0 |
| T003 | Créer table metadata | `rekall/db.py` | P0 |
| T004 | Migration v3 avec MIGRATIONS dict | `rekall/db.py` | P0 |
| T005 | Dataclass Embedding avec validation | `rekall/models.py` | P0 |
| T006 | Dataclass Suggestion avec validation | `rekall/models.py` | P0 |
| T007 | CRUD embeddings (add, get, delete) | `rekall/db.py` | P0 |
| T008 | CRUD suggestions (add, get, update_status) | `rekall/db.py` | P0 |
| T009 | CRUD metadata (get, set) | `rekall/db.py` | P0 |
| T010 | Tests migration + CRUD | `tests/test_db_v3.py` | P0 |

---

### Phase 1: Service Embeddings (T011-T020)

**Objectif**: Calcul et stockage des embeddings

| ID | Tâche | Fichiers | Priorité |
|----|-------|----------|----------|
| T011 | Créer module rekall/embeddings.py | `rekall/embeddings.py` | P1 |
| T012 | Classe EmbeddingEngine avec lazy loading | `rekall/embeddings.py` | P1 |
| T013 | Méthode embed(text) avec normalisation | `rekall/embeddings.py` | P1 |
| T014 | Méthode embed_entry_summary(entry) | `rekall/embeddings.py` | P1 |
| T015 | Méthode embed_context(context) | `rekall/embeddings.py` | P1 |
| T016 | Support Matryoshka (768→384→128) | `rekall/embeddings.py` | P1 |
| T017 | Cosine similarity optimisé | `rekall/embeddings.py` | P1 |
| T018 | find_similar(query_emb, threshold) | `rekall/embeddings.py` | P1 |
| T019 | Gestion gracieuse si modèle absent | `rekall/embeddings.py` | P1 |
| T020 | Tests embeddings (mock modèle) | `tests/test_embeddings.py` | P1 |

---

### Phase 2: CLI Add avec Context (T021-T030) - US1

**Objectif**: Intégration embeddings dans `rekall add`

| ID | Tâche | Fichiers | Priorité |
|----|-------|----------|----------|
| T021 | Option --context pour rekall add | `rekall/cli.py` | P1 |
| T022 | Option --context-file pour fichier | `rekall/cli.py` | P1 |
| T023 | Calcul embedding summary à l'ajout | `rekall/cli.py` | P1 |
| T024 | Calcul embedding context si fourni | `rekall/cli.py` | P1 |
| T025 | Troncature contexte >8000 chars | `rekall/embeddings.py` | P1 |
| T026 | Recherche similaires après ajout | `rekall/cli.py` | P1 |
| T027 | Affichage suggestions de liens | `rekall/cli.py` | P1 |
| T028 | Création suggestions en base | `rekall/db.py` | P1 |
| T029 | Messages i18n pour suggestions | `rekall/i18n.py` | P1 |
| T030 | Tests CLI add avec context | `tests/test_cli_add_context.py` | P1 |

---

### Phase 3: Recherche Sémantique (T031-T040) - US2

**Objectif**: Recherche hybride FTS + embeddings

| ID | Tâche | Fichiers | Priorité |
|----|-------|----------|----------|
| T031 | Option --context pour rekall search | `rekall/cli.py` | P1 |
| T032 | Embed query (+context si fourni) | `rekall/cli.py` | P1 |
| T033 | Recherche sémantique parallèle à FTS | `rekall/db.py` | P1 |
| T034 | Scoring hybride (60% FTS + 40% semantic) | `rekall/db.py` | P1 |
| T035 | Fallback FTS si embeddings désactivés | `rekall/db.py` | P1 |
| T036 | Affichage score sémantique dans résultats | `rekall/cli.py` | P1 |
| T037 | Configuration seuil similarité | `rekall/config.py` | P1 |
| T038 | Configuration pondération FTS/semantic | `rekall/config.py` | P1 |
| T039 | Tests recherche sémantique | `tests/test_search_semantic.py` | P1 |
| T040 | Tests fallback FTS | `tests/test_search_fallback.py` | P1 |

---

### Phase 4: Suggestions Hebdomadaires (T041-T050) - US3

**Objectif**: Détection automatique de généralisations

| ID | Tâche | Fichiers | Priorité |
|----|-------|----------|----------|
| T041 | Créer module rekall/suggest.py | `rekall/suggest.py` | P2 |
| T042 | SuggestionEngine.suggest_generalizations() | `rekall/suggest.py` | P2 |
| T043 | Clustering entrées épisodiques par similarité | `rekall/suggest.py` | P2 |
| T044 | Détection premier appel de la semaine | `rekall/suggest.py` | P2 |
| T045 | Stockage last_weekly_check en metadata | `rekall/db.py` | P2 |
| T046 | Hook weekly_check() au démarrage CLI | `rekall/cli.py` | P2 |
| T047 | Affichage suggestions généralisations | `rekall/cli.py` | P2 |
| T048 | Proposition commande generalize pré-remplie | `rekall/cli.py` | P2 |
| T049 | Tests suggestions hebdomadaires | `tests/test_weekly_suggestions.py` | P2 |
| T050 | Performance <5s pour 1000 entrées | `tests/test_weekly_perf.py` | P2 |

---

### Phase 5: Commande Suggest (T051-T060) - US5

**Objectif**: Gestion des suggestions pendantes

| ID | Tâche | Fichiers | Priorité |
|----|-------|----------|----------|
| T051 | Commande `rekall suggest` (liste pending) | `rekall/cli.py` | P3 |
| T052 | Affichage formaté suggestions avec scores | `rekall/cli.py` | P3 |
| T053 | Option --accept ID pour accepter | `rekall/cli.py` | P3 |
| T054 | Option --reject ID pour rejeter | `rekall/cli.py` | P3 |
| T055 | Création lien automatique si accepté | `rekall/db.py` | P3 |
| T056 | Marquage suggestion resolved_at | `rekall/db.py` | P3 |
| T057 | Option --type pour filtrer (link|generalize) | `rekall/cli.py` | P3 |
| T058 | Tests commande suggest | `tests/test_suggest_cmd.py` | P3 |
| T059 | Messages i18n suggest | `rekall/i18n.py` | P3 |
| T060 | Aide intégrée `rekall suggest --help` | `rekall/cli.py` | P3 |

---

### Phase 6: Serveur MCP + Progressive Disclosure (T061-T080) - US4 & US6

**Objectif**: Interface universelle pour agents AI

| ID | Tâche | Fichiers | Priorité |
|----|-------|----------|----------|
| T061 | Créer module rekall/mcp_server.py | `rekall/mcp_server.py` | P2 |
| T062 | **Tool rekall_help(topic?) - Guide agent** | `rekall/mcp_server.py` | P2 |
| T063 | Contenu rekall_help: workflows, déclencheurs, citations | `rekall/mcp_server.py` | P2 |
| T064 | Tool rekall_search avec **output compact** (Progressive Disclosure) | `rekall/mcp_server.py` | P2 |
| T065 | Tool rekall_show(id) - détails complets à la demande | `rekall/mcp_server.py` | P2 |
| T066 | Tool rekall_add(type, title, content, tags, context) | `rekall/mcp_server.py` | P2 |
| T067 | Tool rekall_suggest_links() | `rekall/mcp_server.py` | P2 |
| T068 | Tool rekall_suggest_generalize() | `rekall/mcp_server.py` | P2 |
| T069 | Tool rekall_link(source, target, type) | `rekall/mcp_server.py` | P2 |
| T070 | Tool rekall_accept_suggestion(id) | `rekall/mcp_server.py` | P2 |
| T071 | Tool rekall_reject_suggestion(id) | `rekall/mcp_server.py` | P2 |
| T072 | Commande `rekall mcp-server` pour démarrer | `rekall/cli.py` | P2 |
| T073 | Configuration MCP dans config.py | `rekall/config.py` | P2 |
| T074 | Tests unitaires MCP server | `tests/test_mcp_server.py` | P2 |
| T075 | Tests intégration avec client MCP | `tests/test_mcp_integration.py` | P2 |
| T076 | Test Progressive Disclosure (-80% tokens) | `tests/test_mcp_tokens.py` | P2 |
| T077 | Test rekall_help contenu complet <500 tokens | `tests/test_mcp_help.py` | P2 |
| T078 | Gestion erreurs MCP (timeout, invalid params) | `rekall/mcp_server.py` | P2 |
| T079 | Messages i18n MCP | `rekall/i18n.py` | P2 |
| T080 | **Supprimer `rekall install <agent>`** (deprecated) | `rekall/cli.py` | P2 |

**Critères de validation Phase 6**:
- [ ] `rekall mcp-server` démarre serveur MCP
- [ ] `rekall_help()` retourne guide complet en <500 tokens
- [ ] `rekall_search()` retourne format compact (id, title, score, snippet)
- [ ] Hint "Use rekall_show(id)" dans résultats search
- [ ] Tous les tools répondent en <2s
- [ ] Pas de skills/rules files par agent nécessaires
- [ ] Erreurs retournées proprement en JSON

---

### Phase 7: Migration Progressive (T081-T085)

**Objectif**: Migration embeddings pour base existante

| ID | Tâche | Fichiers | Priorité |
|----|-------|----------|----------|
| T081 | Commande `rekall embeddings migrate` | `rekall/cli.py` | P2 |
| T082 | Calcul embeddings batch avec progress bar | `rekall/embeddings.py` | P2 |
| T083 | Option --limit pour migration partielle | `rekall/cli.py` | P2 |
| T084 | Calcul à la demande (lazy) si embedding absent | `rekall/embeddings.py` | P2 |
| T085 | Tests migration base existante | `tests/test_migration_embeddings.py` | P2 |

**Critères de validation Phase 7**:
- [ ] `rekall embeddings migrate` calcule tous les embeddings manquants
- [ ] Progress bar affiche avancement
- [ ] Lazy calculation fonctionne pour entrées non migrées

---

### Phase 8: Polish & Documentation (T086-T093)

**Objectif**: Finalisation et documentation

| ID | Tâche | Fichiers | Priorité |
|----|-------|----------|----------|
| T086 | Instructions installation dépendances embeddings | `docs/embeddings.md` | P3 |
| T087 | Guide MCP universel (pas par agent) | `docs/mcp-setup.md` | P3 |
| T088 | Mise à jour README avec fonctionnalités | `README.md` | P3 |
| T089 | Tests e2e workflow complet | `tests/test_e2e_embeddings.py` | P3 |
| T090 | Vérification cross-platform (Linux/macOS/Windows) | - | P3 |
| T091 | Benchmark mémoire (<500MB RAM) | `tests/test_memory.py` | P3 |
| T092 | Messages d'erreur utilisateur-friendly | `rekall/i18n.py` | P3 |
| T093 | Checklist validation feature complète | `checklists/implementation.md` | P3 |

**Critères de validation Phase 8**:
- [ ] Documentation complète et claire
- [ ] Tests e2e passent sur les 3 plateformes
- [ ] Mémoire <500MB pendant calcul embeddings

---

## Résumé des Phases

| Phase | Tâches | Priorité | Dépend de |
|-------|--------|----------|-----------|
| Phase 0: Infrastructure | T001-T010 (10) | P0 | - |
| Phase 1: Service Embeddings | T011-T020 (10) | P1 | Phase 0 |
| Phase 2: CLI Add | T021-T030 (10) | P1 | Phase 1 |
| Phase 3: Recherche Sémantique | T031-T040 (10) | P1 | Phase 1 |
| Phase 4: Suggestions Hebdo | T041-T050 (10) | P2 | Phase 1 |
| Phase 5: Commande Suggest | T051-T060 (10) | P3 | Phase 2, 4 |
| Phase 6: Serveur MCP + Progressive Disclosure | T061-T080 (20) | P2 | Phase 1, 2, 3 |
| Phase 7: Migration | T081-T085 (5) | P2 | Phase 1 |
| Phase 8: Polish | T086-T093 (8) | P3 | Toutes |

**Total: 93 tâches**

**Changements clés vs version précédente:**
- Phase 6 étendue: +5 tâches pour `rekall_help()` et Progressive Disclosure
- Suppression `rekall install <agent>` (tâche T080)
- Pas de skills/rules files par agent

---

## Risques et Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Modèle trop lent sur CPU | Moyenne | Élevé | Matryoshka 128 dims, batch processing |
| Dépendances lourdes (~500MB) | Faible | Moyen | Installation optionnelle, message clair |
| MCP SDK instable | Faible | Moyen | Abstraction, fallback CLI |
| Précision embeddings insuffisante | Faible | Moyen | Seuils configurables, feedback utilisateur |

---

## Validation Finale

### Critères de Succès (spec.md)

- [ ] SC-001: 80%+ précision suggestions (8/10 pertinentes)
- [ ] SC-002: <500ms par embedding sur CPU laptop
- [ ] SC-003: 30%+ queries trouvent résultats via sémantique seule
- [ ] SC-004: 60%+ suggestions acceptées
- [ ] SC-005: <5s check hebdomadaire (1000 entrées)
- [ ] SC-006: <2s réponse MCP tools
- [ ] SC-007: <500MB RAM pendant opération
- [ ] SC-008: Fonctionne identiquement Win/Linux/macOS
- [ ] SC-009: Installation <5 minutes avec feedback
- [ ] SC-010: Progressive Disclosure réduit tokens de 80%+ (search compact)
- [ ] SC-011: `rekall_help()` guide complet en <500 tokens
- [ ] SC-012: Zéro configuration par agent (MCP universel)
