# Research Technique - Optimisation Performance Embeddings

**Feature**: 020-embedding-perf
**Date**: 2025-12-13

## 1. Index Vectoriel : sqlite-vec

### Décision
Utiliser **sqlite-vec** comme index vectoriel principal avec fallback numpy.

### Rationale
- Intégration native SQLite (déjà utilisé par Rekall)
- Léger (~2MB vs ~200MB pour FAISS)
- Performance suffisante jusqu'à 500K vecteurs (17ms vs 10ms FAISS sur 1M)
- Transactions ACID automatiques
- Pas de fichier séparé à synchroniser

### Alternatives considérées

| Option | Pour | Contre | Verdict |
|--------|------|--------|---------|
| FAISS | Plus rapide à grande échelle, GPU | Lourd, sync séparée, overkill <500K | Rejeté |
| hnswlib | Rapide, léger | Fichier séparé, pas d'ACID | Rejeté |
| Brute-force numpy | Simple, pas de dépendance | O(n) linéaire | Fallback uniquement |

### Source
- [sqlite-vec v0.1.0 release](https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/)

### Installation
```bash
# Via pip (wheels disponibles pour major platforms)
pip install sqlite-vec

# Vérification
python -c "import sqlite_vec; print(sqlite_vec.loadable_path())"
```

### Risques
- Extension non disponible sur certaines plateformes exotiques → Fallback numpy
- API potentiellement instable (v0.x) → Wrapper abstrait pour migration future

---

## 2. Cache LRU pour Embeddings

### Décision
Utiliser un **dict Python + invalidation manuelle** plutôt que `functools.lru_cache`.

### Rationale
- `lru_cache` ne supporte pas l'invalidation sélective (cache_clear() vide tout)
- Besoin d'invalider uniquement les entrées modifiées
- Dict avec timestamps permet TTL + LRU manuel

### Implémentation
```python
from collections import OrderedDict
from time import time

class EmbeddingCache:
    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 600):
        self._cache: OrderedDict[str, tuple[np.ndarray, float]] = OrderedDict()
        self.maxsize = maxsize
        self.ttl = ttl_seconds

    def get(self, entry_id: str) -> np.ndarray | None:
        if entry_id in self._cache:
            vec, ts = self._cache[entry_id]
            if time() - ts < self.ttl:
                self._cache.move_to_end(entry_id)  # LRU update
                return vec
            del self._cache[entry_id]  # Expired
        return None

    def invalidate(self, entry_id: str) -> None:
        self._cache.pop(entry_id, None)
```

---

## 3. Vectorisation NumPy

### Décision
Remplacer la boucle Python par **opérations batch numpy**.

### Code actuel (lent)
```python
for emb in all_embeddings:
    score = cosine_similarity(query_vec, emb.to_numpy())  # Appel par appel
```

### Code optimisé
```python
# Charger tous les vecteurs en une matrice (N x D)
all_vectors = np.vstack([emb.to_numpy() for emb in all_embeddings])

# Calcul batch : tous les scores en une opération
scores = np.dot(all_vectors, query_vec)  # (N,) scores

# Top-k en O(n log k)
top_indices = np.argpartition(scores, -k)[-k:]
```

### Gain estimé
- Boucle Python : ~2-5s pour 1000 entrées
- Batch numpy : ~10-50ms pour 1000 entrées
- **Facteur 50-100x**

---

## 4. Lazy Unload du Modèle

### Décision
Décharger le modèle après **10 minutes d'inactivité** (configurable).

### Implémentation
```python
import gc
from time import time

class ModelManager:
    def __init__(self, timeout_minutes: int = 10):
        self._model = None
        self._last_used = 0
        self.timeout = timeout_minutes * 60

    def get_model(self):
        self._last_used = time()
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer("all-MiniLM-L6-v2")
        return self._model

    def check_idle(self):
        if self._model and (time() - self._last_used > self.timeout):
            self._model = None
            gc.collect()  # Force garbage collection
            return True
        return False
```

### Intégration
- Appeler `check_idle()` périodiquement (ex: après chaque opération)
- Ou via timer background (plus complexe, éviter si possible)

---

## 5. Migration et Rétrocompatibilité

### Stratégie
1. **Détection automatique** : Vérifier si sqlite-vec est disponible au démarrage
2. **Migration transparente** : Les embeddings existants restent dans la table actuelle
3. **Index incrémental** : Construire l'index sqlite-vec au premier usage
4. **Fallback gracieux** : Si sqlite-vec échoue, utiliser numpy vectorisé

### Schema migration
```sql
-- Nouvelle table virtuelle sqlite-vec (si extension disponible)
CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_vec USING vec0(
    entry_id TEXT PRIMARY KEY,
    embedding FLOAT[384]
);

-- Index de migration
CREATE INDEX IF NOT EXISTS idx_embeddings_migration
ON embeddings(entry_id) WHERE embedding_type = 'summary';
```

---

## Checklist Recherche

- [x] sqlite-vec vs FAISS : benchmarks vérifiés
- [x] Cache LRU : stratégie d'invalidation définie
- [x] Vectorisation numpy : gain estimé vérifié
- [x] Lazy unload : pattern simple sans threads
- [x] Migration : stratégie de compatibilité ascendante
