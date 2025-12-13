# Data Model - Optimisation Performance Embeddings

**Feature**: 020-embedding-perf
**Date**: 2025-12-13

## Entités

### 1. EmbeddingCache

**Responsabilité** : Cache LRU des vecteurs d'embedding avec invalidation sélective.

| Attribut | Type | Description |
|----------|------|-------------|
| `_cache` | OrderedDict[str, tuple[ndarray, float]] | Mapping entry_id → (vecteur, timestamp) |
| `maxsize` | int | Taille max du cache (défaut: 1000) |
| `ttl` | int | Time-to-live en secondes (défaut: 600) |
| `_matrix_cache` | ndarray \| None | Matrice batch précalculée |
| `_matrix_valid` | bool | Flag de validité de la matrice |

**Méthodes principales** :
- `get(entry_id) → ndarray | None` : Récupère un vecteur (update LRU)
- `put(entry_id, vector)` : Ajoute/met à jour un vecteur
- `invalidate(entry_id)` : Supprime une entrée (après modification)
- `get_all_as_matrix() → tuple[ndarray, list[str]]` : Matrice batch + IDs
- `clear()` : Vide le cache

**Invariants** :
- `len(_cache) <= maxsize`
- Entrées expirées supprimées à l'accès (lazy eviction)
- `_matrix_valid = False` après tout `put()` ou `invalidate()`

---

### 2. VectorIndex

**Responsabilité** : Abstraction pour recherche vectorielle (sqlite-vec ou fallback).

| Attribut | Type | Description |
|----------|------|-------------|
| `_backend` | str | "sqlite-vec" ou "numpy" |
| `_conn` | sqlite3.Connection | Connexion DB |
| `_vec_available` | bool | sqlite-vec chargé avec succès |
| `_dimensions` | int | Dimensions des vecteurs (défaut: 384) |

**Méthodes principales** :
- `search(query_vec, k) → list[tuple[str, float]]` : Top-k similarité
- `add(entry_id, vector)` : Ajoute un vecteur à l'index
- `update(entry_id, vector)` : Met à jour un vecteur existant
- `delete(entry_id)` : Supprime un vecteur
- `rebuild()` : Reconstruit l'index depuis la table embeddings
- `is_available() → bool` : Vérifie si sqlite-vec est utilisable

**État** :
- `Initialized` → `Ready` (après rebuild ou premier add)
- `Ready` → `Stale` (après modification sans rebuild)

---

### 3. ModelManager

**Responsabilité** : Gestion du cycle de vie du modèle sentence-transformers.

| Attribut | Type | Description |
|----------|------|-------------|
| `_model` | SentenceTransformer \| None | Instance du modèle (lazy loaded) |
| `_last_used` | float | Timestamp dernière utilisation |
| `_loading` | bool | Flag de chargement en cours |
| `timeout_minutes` | int | Délai avant unload (défaut: 10) |
| `model_name` | str | Nom du modèle (défaut: "all-MiniLM-L6-v2") |

**Méthodes principales** :
- `get_model() → SentenceTransformer` : Charge et retourne le modèle
- `is_loaded() → bool` : Vérifie si le modèle est en mémoire
- `is_loading() → bool` : Vérifie si le chargement est en cours
- `check_idle() → bool` : Décharge si inactif, retourne True si déchargé
- `unload()` : Force le déchargement

**États** :
```
Unloaded ─[get_model()]→ Loading ─[complete]→ Loaded
    ↑                                            │
    └──────────[check_idle() timeout]────────────┘
```

---

## Relations

```
┌─────────────────┐     uses      ┌─────────────────┐
│ EmbeddingService│──────────────▶│  EmbeddingCache │
│   (existant)    │               └─────────────────┘
└────────┬────────┘                       │
         │                                │ invalidates
         │ uses                           ▼
         │                        ┌─────────────────┐
         ├───────────────────────▶│   VectorIndex   │
         │                        └─────────────────┘
         │ uses                           │
         │                                │ reads from
         │                                ▼
         │                        ┌─────────────────┐
         └───────────────────────▶│  ModelManager   │
                                  └─────────────────┘
```

---

## Configuration

Nouvelles options dans `config.toml` :

```toml
[performance]
# Cache embeddings
cache_max_size = 1000          # Nombre max d'entrées en cache
cache_ttl_seconds = 600        # TTL du cache (10 min)

# Modèle
model_idle_timeout_minutes = 10  # Délai avant unload du modèle

# Index vectoriel
vector_index_backend = "auto"    # "auto", "sqlite-vec", "numpy"
```

---

## Migrations DB

### Schema v12 (nouveau)

```sql
-- Si sqlite-vec disponible
CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_vec USING vec0(
    entry_id TEXT PRIMARY KEY,
    vector FLOAT[384]
);
```

### Migration

1. Au démarrage, détecter sqlite-vec
2. Si disponible et table `embeddings_vec` n'existe pas → créer
3. Migrer les embeddings existants (background, non-bloquant)
4. Flag `embeddings_vec_ready` dans metadata table
