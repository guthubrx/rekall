# Implementation Plan: Optimisation Performance Embeddings

**Branch**: `020-embedding-perf` | **Date**: 2025-12-13 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/020-embedding-perf/spec.md`

## Summary

Optimiser la recherche sémantique de Rekall en remplaçant la boucle O(n) brute-force par des opérations numpy vectorisées, en ajoutant un cache LRU pour les embeddings, en intégrant sqlite-vec pour les recherches O(log n), et en implémentant le lazy unload du modèle sentence-transformers.

**Gains attendus** : Recherche 10-50x plus rapide, -80% RAM par recherche, -100MB RAM idle.

## Technical Context

**Language/Version**: Python 3.10+ (existant)
**Primary Dependencies**: sentence-transformers, numpy, sqlite-vec (nouvelle), functools.lru_cache
**Storage**: SQLite + FTS5 (existant), sqlite-vec (nouveau)
**Testing**: pytest, pytest-cov (existant)
**Target Platform**: macOS, Linux, Windows (CLI/TUI cross-platform)
**Project Type**: single (CLI + TUI + MCP server)
**Performance Goals**: <500ms recherche sur 1000 entrées, <1s sur 10K entrées
**Constraints**: <100MB RAM au repos, <200MB pic, sqlite-vec optionnel (fallback)
**Scale/Scope**: 100 à 50 000 entrées (usage personnel à équipe)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Règle | Status | Notes |
|---------|-------|--------|-------|
| III | Processus SpecKit | ✅ Pass | /speckit.specify → /speckit.clarify → /speckit.plan |
| IV | Disjoncteur (3 tentatives) | ✅ N/A | Pas de debug en cours |
| V | Anti Scope-Creep | ✅ Pass | Feature isolée, pas de nouvelles demandes |
| VII | ADR si décision structurante | ⚠️ À faire | Créer ADR pour sqlite-vec vs FAISS |
| XV | Test-Before-Next | ✅ À appliquer | Batterie tests obligatoire |
| XVI | Workflow Worktree | ⚠️ Partiel | Branche créée, worktree dans repo principal |
| XVII | DevKMS Capture | ✅ Fait | Décision sqlite-vec déjà capturée dans Rekall |

**Gates OK** - Aucune violation bloquante. ADR à créer pendant Phase 1.

## Project Structure

### Documentation (this feature)

```text
specs/020-embedding-perf/
├── plan.md              # Ce fichier
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # N/A (pas d'API externe)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
rekall/
├── embeddings.py        # MODIFIER: EmbeddingService, semantic_search, find_similar
├── db.py                # MODIFIER: get_all_embeddings → batch numpy, sqlite-vec
├── cache.py             # CRÉER: EmbeddingCache LRU avec invalidation
├── vector_index.py      # CRÉER: VectorIndex (sqlite-vec + fallback)
├── model_manager.py     # CRÉER: ModelManager (lazy load/unload)
└── config.py            # MODIFIER: Ajouter configs performance

tests/
├── test_embeddings.py   # MODIFIER: Tests performance
├── test_cache.py        # CRÉER: Tests cache LRU
├── test_vector_index.py # CRÉER: Tests sqlite-vec
└── test_model_manager.py # CRÉER: Tests lazy unload
```

**Structure Decision**: Projet single existant. Ajout de 3 nouveaux modules (cache, vector_index, model_manager) + modification des existants.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Aucune | - | - |

L'architecture reste simple : 3 nouveaux modules avec responsabilités claires, pas de sur-engineering.

## Phase 0: Research Output

Voir [research.md](research.md) pour les détails.

**Résumé des décisions techniques :**

| Sujet | Décision | Rationale |
|-------|----------|-----------|
| Index vectoriel | sqlite-vec | Intégration SQLite native, léger, suffisant <500K vecteurs |
| Cache | functools.lru_cache + dict invalidable | Simple, stdlib, pas de dépendance externe |
| Vectorisation | numpy.dot() batch | Déjà dépendance, ~50x plus rapide que boucle Python |
| Lazy unload | Timer + gc.collect() | Pas de thread complexe, juste cleanup après timeout |

## Phase 1: Design Output

Voir [data-model.md](data-model.md) et [quickstart.md](quickstart.md).

**Entités clés :**

1. **EmbeddingCache** : Cache LRU des vecteurs avec TTL et invalidation on-write
2. **VectorIndex** : Abstraction sqlite-vec avec fallback numpy brute-force
3. **ModelManager** : Singleton gérant chargement/déchargement du modèle

**Interfaces principales :**

```python
# VectorIndex
class VectorIndex:
    def search(query_vec: np.ndarray, k: int) -> list[tuple[str, float]]: ...
    def add(entry_id: str, vector: np.ndarray) -> None: ...
    def delete(entry_id: str) -> None: ...
    def rebuild() -> None: ...

# EmbeddingCache
class EmbeddingCache:
    def get_all_vectors() -> np.ndarray: ...  # Matrice batch
    def get_entry_ids() -> list[str]: ...
    def invalidate(entry_id: str) -> None: ...

# ModelManager
class ModelManager:
    def get_model() -> SentenceTransformer: ...
    def unload_if_idle(timeout_minutes: int) -> bool: ...
```

## Prochaine étape

Exécuter `/speckit.tasks` pour générer les tâches d'implémentation détaillées.
