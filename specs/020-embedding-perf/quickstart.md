# Quickstart - Optimisation Performance Embeddings

**Feature**: 020-embedding-perf
**Date**: 2025-12-13

## Objectif

Améliorer les performances de recherche sémantique et réduire l'empreinte mémoire de Rekall.

## Avant / Après

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| Recherche 1000 entrées | ~2-5s | <500ms | **10x** |
| Recherche 10K entrées | ~20-50s | <1s | **50x** |
| RAM au repos (avec modèle) | ~150-200 MB | <100 MB | **-50%** |
| RAM pic recherche | ~300 MB | <200 MB | **-33%** |

## Changements clés

### 1. Vectorisation NumPy
La boucle Python `for emb in embeddings` est remplacée par une opération batch numpy.

### 2. Cache LRU
Les embeddings fréquemment utilisés sont gardés en mémoire avec invalidation automatique.

### 3. Index sqlite-vec
Recherche O(log n) au lieu de O(n) grâce à l'extension sqlite-vec.

### 4. Lazy unload modèle
Le modèle sentence-transformers est déchargé après 10 minutes d'inactivité.

## Comment tester

```bash
# Générer une base de test avec 1000 entrées
rekall test generate --count 1000

# Mesurer le temps de recherche
time rekall search "test query"

# Vérifier la mémoire
rekall stats --memory
```

## Configuration

```toml
# ~/.config/rekall/config.toml

[performance]
cache_max_size = 1000              # Taille du cache (entrées)
cache_ttl_seconds = 600            # TTL cache (10 min)
model_idle_timeout_minutes = 10    # Timeout avant unload modèle
vector_index_backend = "auto"      # "auto", "sqlite-vec", "numpy"
```

## Dépendances

**Nouvelle dépendance optionnelle** :
```bash
pip install sqlite-vec
```

Si sqlite-vec n'est pas installé, Rekall utilise automatiquement le fallback numpy vectorisé (toujours plus rapide que l'implémentation actuelle).

## Fichiers modifiés

| Fichier | Action | Description |
|---------|--------|-------------|
| `rekall/cache.py` | CRÉER | Cache LRU avec invalidation |
| `rekall/vector_index.py` | CRÉER | Abstraction sqlite-vec |
| `rekall/model_manager.py` | CRÉER | Lazy load/unload modèle |
| `rekall/embeddings.py` | MODIFIER | Utiliser les nouveaux modules |
| `rekall/db.py` | MODIFIER | Méthodes batch numpy |
| `rekall/config.py` | MODIFIER | Options performance |
