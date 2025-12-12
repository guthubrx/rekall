# Modèle de Données: Smart Embeddings System

**Feature**: 005-smart-embeddings
**Version schéma**: 3 (upgrade depuis v2)
**Créé**: 2025-12-09

---

## Vue d'Ensemble

### Tables Existantes (v2)
- `entries` - Entrées de connaissance avec champs cognitifs
- `tags` - Tags associés aux entrées
- `links` - Liens entre entrées (knowledge graph)
- `entries_fts` - Index FTS5 pour recherche full-text

### Nouvelles Tables (v3)
- `embeddings` - Vecteurs d'embeddings par entrée
- `suggestions` - Suggestions de liens/généralisations
- `metadata` - Métadonnées système (ex: last_weekly_check)

---

## Schéma SQLite

### Table: embeddings

```sql
CREATE TABLE IF NOT EXISTS embeddings (
    id TEXT PRIMARY KEY,
    entry_id TEXT NOT NULL,
    embedding_type TEXT NOT NULL,
    vector BLOB NOT NULL,
    dimensions INTEGER NOT NULL,
    model_name TEXT NOT NULL,
    created_at TEXT NOT NULL,

    FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
    CHECK (embedding_type IN ('summary', 'context')),
    CHECK (dimensions IN (128, 384, 768)),
    UNIQUE(entry_id, embedding_type)
);

CREATE INDEX IF NOT EXISTS idx_embeddings_entry ON embeddings(entry_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_type ON embeddings(embedding_type);
```

**Colonnes**:

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | TEXT | ULID unique |
| `entry_id` | TEXT | FK vers entries.id |
| `embedding_type` | TEXT | 'summary' ou 'context' |
| `vector` | BLOB | Vecteur binaire (numpy.tobytes()) |
| `dimensions` | INTEGER | 128, 384, ou 768 (Matryoshka) |
| `model_name` | TEXT | Ex: "EmbeddingGemma-2B-v1" |
| `created_at` | TEXT | ISO 8601 timestamp |

**Contraintes**:
- `UNIQUE(entry_id, embedding_type)` - Max 2 embeddings par entrée (summary + context)
- `ON DELETE CASCADE` - Suppression auto si entrée supprimée

---

### Table: suggestions

```sql
CREATE TABLE IF NOT EXISTS suggestions (
    id TEXT PRIMARY KEY,
    suggestion_type TEXT NOT NULL,
    entry_ids TEXT NOT NULL,
    reason TEXT,
    score REAL NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    resolved_at TEXT,

    CHECK (suggestion_type IN ('link', 'generalize')),
    CHECK (status IN ('pending', 'accepted', 'rejected')),
    CHECK (score >= 0.0 AND score <= 1.0)
);

CREATE INDEX IF NOT EXISTS idx_suggestions_status ON suggestions(status);
CREATE INDEX IF NOT EXISTS idx_suggestions_type ON suggestions(suggestion_type);
CREATE INDEX IF NOT EXISTS idx_suggestions_created ON suggestions(created_at);
```

**Colonnes**:

| Colonne | Type | Description |
|---------|------|-------------|
| `id` | TEXT | ULID unique |
| `suggestion_type` | TEXT | 'link' ou 'generalize' |
| `entry_ids` | TEXT | JSON array des IDs concernés |
| `reason` | TEXT | Explication de la suggestion |
| `score` | REAL | Score de similarité (0.0-1.0) |
| `status` | TEXT | 'pending', 'accepted', 'rejected' |
| `created_at` | TEXT | ISO 8601 timestamp |
| `resolved_at` | TEXT | ISO 8601 timestamp (nullable) |

**Format entry_ids**:
```json
// Pour suggestion type 'link' (2 entrées)
["01HX123...", "01HX456..."]

// Pour suggestion type 'generalize' (3+ entrées)
["01HX123...", "01HX456...", "01HX789..."]
```

---

### Table: metadata

```sql
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

**Clés utilisées**:

| Clé | Valeur | Description |
|-----|--------|-------------|
| `last_weekly_check` | ISO 8601 date | Dernière vérification hebdomadaire |
| `embeddings_model` | String | Modèle utilisé (pour migration) |
| `embeddings_dimensions` | Integer | Dimensions configurées |

---

## Migration v3

### SQL de Migration

```python
MIGRATIONS[3] = [
    # Table embeddings
    """CREATE TABLE IF NOT EXISTS embeddings (
        id TEXT PRIMARY KEY,
        entry_id TEXT NOT NULL,
        embedding_type TEXT NOT NULL,
        vector BLOB NOT NULL,
        dimensions INTEGER NOT NULL,
        model_name TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (entry_id) REFERENCES entries(id) ON DELETE CASCADE,
        CHECK (embedding_type IN ('summary', 'context')),
        CHECK (dimensions IN (128, 384, 768)),
        UNIQUE(entry_id, embedding_type)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_embeddings_entry ON embeddings(entry_id)",
    "CREATE INDEX IF NOT EXISTS idx_embeddings_type ON embeddings(embedding_type)",

    # Table suggestions
    """CREATE TABLE IF NOT EXISTS suggestions (
        id TEXT PRIMARY KEY,
        suggestion_type TEXT NOT NULL,
        entry_ids TEXT NOT NULL,
        reason TEXT,
        score REAL NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        created_at TEXT NOT NULL,
        resolved_at TEXT,
        CHECK (suggestion_type IN ('link', 'generalize')),
        CHECK (status IN ('pending', 'accepted', 'rejected')),
        CHECK (score >= 0.0 AND score <= 1.0)
    )""",
    "CREATE INDEX IF NOT EXISTS idx_suggestions_status ON suggestions(status)",
    "CREATE INDEX IF NOT EXISTS idx_suggestions_type ON suggestions(suggestion_type)",
    "CREATE INDEX IF NOT EXISTS idx_suggestions_created ON suggestions(created_at)",

    # Table metadata
    """CREATE TABLE IF NOT EXISTS metadata (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    )""",
]
```

### Vérification Post-Migration

```python
EXPECTED_TABLES = {
    "entries", "tags", "links", "entries_fts",
    "embeddings", "suggestions", "metadata"  # v3
}

EXPECTED_EMBEDDING_COLUMNS = {
    "id", "entry_id", "embedding_type", "vector",
    "dimensions", "model_name", "created_at"
}

EXPECTED_SUGGESTION_COLUMNS = {
    "id", "suggestion_type", "entry_ids", "reason",
    "score", "status", "created_at", "resolved_at"
}
```

---

## Modèles Python (dataclasses)

### Embedding

```python
@dataclass
class Embedding:
    """Vector representation of an entry."""

    id: str
    entry_id: str
    embedding_type: Literal["summary", "context"]
    vector: bytes  # numpy array serialized
    dimensions: Literal[128, 384, 768]
    model_name: str
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if self.embedding_type not in ("summary", "context"):
            raise ValueError(f"Invalid embedding_type: {self.embedding_type}")
        if self.dimensions not in (128, 384, 768):
            raise ValueError(f"Invalid dimensions: {self.dimensions}")

    def to_numpy(self) -> np.ndarray:
        """Deserialize vector bytes to numpy array."""
        return np.frombuffer(self.vector, dtype=np.float32)

    @classmethod
    def from_numpy(cls, entry_id: str, emb_type: str,
                   array: np.ndarray, model: str) -> "Embedding":
        """Create Embedding from numpy array."""
        return cls(
            id=generate_ulid(),
            entry_id=entry_id,
            embedding_type=emb_type,
            vector=array.astype(np.float32).tobytes(),
            dimensions=len(array),
            model_name=model,
        )
```

### Suggestion

```python
SuggestionType = Literal["link", "generalize"]
SuggestionStatus = Literal["pending", "accepted", "rejected"]

@dataclass
class Suggestion:
    """A proposed action detected by the system."""

    id: str
    suggestion_type: SuggestionType
    entry_ids: list[str]
    score: float
    reason: str = ""
    status: SuggestionStatus = "pending"
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        if self.suggestion_type not in ("link", "generalize"):
            raise ValueError(f"Invalid suggestion_type: {self.suggestion_type}")
        if self.status not in ("pending", "accepted", "rejected"):
            raise ValueError(f"Invalid status: {self.status}")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be 0.0-1.0, got: {self.score}")
        if self.suggestion_type == "link" and len(self.entry_ids) != 2:
            raise ValueError("Link suggestion must have exactly 2 entry_ids")
        if self.suggestion_type == "generalize" and len(self.entry_ids) < 3:
            raise ValueError("Generalize suggestion must have 3+ entry_ids")

    def entry_ids_json(self) -> str:
        """Serialize entry_ids for SQLite storage."""
        import json
        return json.dumps(self.entry_ids)

    @classmethod
    def from_row(cls, row: dict) -> "Suggestion":
        """Create Suggestion from database row."""
        import json
        return cls(
            id=row["id"],
            suggestion_type=row["suggestion_type"],
            entry_ids=json.loads(row["entry_ids"]),
            score=row["score"],
            reason=row.get("reason", ""),
            status=row["status"],
            created_at=datetime.fromisoformat(row["created_at"]),
            resolved_at=datetime.fromisoformat(row["resolved_at"]) if row.get("resolved_at") else None,
        )
```

---

## Opérations CRUD

### Embeddings

```python
# db.py

def add_embedding(self, embedding: Embedding) -> None:
    """Store an embedding vector."""

def get_embedding(self, entry_id: str, emb_type: str) -> Optional[Embedding]:
    """Get embedding for entry by type."""

def get_embeddings(self, entry_id: str) -> list[Embedding]:
    """Get all embeddings for an entry (summary + context)."""

def delete_embedding(self, entry_id: str, emb_type: Optional[str] = None) -> int:
    """Delete embedding(s) for entry. Returns count deleted."""

def get_all_embeddings(self, emb_type: Optional[str] = None) -> list[Embedding]:
    """Get all embeddings, optionally filtered by type."""

def count_embeddings(self) -> int:
    """Count total embeddings in database."""

def get_entries_without_embeddings(self, emb_type: str = "summary") -> list[Entry]:
    """Get entries missing embeddings (for migration)."""
```

### Suggestions

```python
# db.py

def add_suggestion(self, suggestion: Suggestion) -> None:
    """Create a new suggestion."""

def get_suggestion(self, suggestion_id: str) -> Optional[Suggestion]:
    """Get suggestion by ID."""

def get_suggestions(
    self,
    status: Optional[str] = None,
    suggestion_type: Optional[str] = None,
    limit: int = 100
) -> list[Suggestion]:
    """Get suggestions with optional filters."""

def update_suggestion_status(
    self,
    suggestion_id: str,
    status: str
) -> bool:
    """Update suggestion status (accept/reject). Returns success."""

def suggestion_exists(self, entry_ids: list[str], suggestion_type: str) -> bool:
    """Check if similar suggestion already exists (avoid duplicates)."""
```

### Metadata

```python
# db.py

def get_metadata(self, key: str) -> Optional[str]:
    """Get metadata value by key."""

def set_metadata(self, key: str, value: str) -> None:
    """Set metadata key-value pair (upsert)."""

def delete_metadata(self, key: str) -> bool:
    """Delete metadata entry. Returns success."""
```

---

## Stockage des Vecteurs

### Sérialisation NumPy → BLOB

```python
import numpy as np

# Stockage
vector = np.array([0.1, 0.2, ...], dtype=np.float32)
blob = vector.tobytes()  # bytes

# Récupération
vector = np.frombuffer(blob, dtype=np.float32)
```

**Taille BLOB par dimensions**:
- 128 dims × 4 bytes = 512 bytes
- 384 dims × 4 bytes = 1,536 bytes
- 768 dims × 4 bytes = 3,072 bytes

### Calcul Similarité Cosine

```python
def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    dot = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))
```

---

## Exemples d'Utilisation

### Ajout d'entrée avec embeddings

```python
# 1. Créer entrée
entry = Entry(id=generate_ulid(), title="Fix CORS Safari", type="bug", ...)
db.add(entry)

# 2. Calculer embeddings
summary_text = f"{entry.title} {entry.content} {' '.join(entry.tags)}"
summary_vec = embedding_service.calculate(summary_text)
db.add_embedding(Embedding.from_numpy(entry.id, "summary", summary_vec, model_name))

# Si contexte fourni
if context:
    context_vec = embedding_service.calculate(context)
    db.add_embedding(Embedding.from_numpy(entry.id, "context", context_vec, model_name))

# 3. Chercher similaires
similar = embedding_service.find_similar(entry.id, threshold=0.75)
for (similar_entry, score) in similar:
    suggestion = Suggestion(
        id=generate_ulid(),
        suggestion_type="link",
        entry_ids=[entry.id, similar_entry.id],
        score=score,
        reason=f"Similarité {score:.0%} basée sur le contenu",
    )
    db.add_suggestion(suggestion)
```

### Recherche hybride

```python
# 1. Recherche FTS
fts_results = db.search(query)  # [(Entry, rank), ...]

# 2. Recherche sémantique
query_vec = embedding_service.calculate(query + " " + context)
semantic_results = []
for entry in all_entries:
    emb = db.get_embedding(entry.id, "summary")
    if emb:
        score = cosine_similarity(query_vec, emb.to_numpy())
        semantic_results.append((entry, score))

# 3. Combiner scores (pondération configurable)
combined = {}
for entry, fts_rank in fts_results:
    combined[entry.id] = {"entry": entry, "fts": fts_rank, "semantic": 0}
for entry, sem_score in semantic_results:
    if entry.id in combined:
        combined[entry.id]["semantic"] = sem_score
    else:
        combined[entry.id] = {"entry": entry, "fts": 0, "semantic": sem_score}

# Score final = 60% FTS + 40% sémantique
for data in combined.values():
    data["final"] = 0.6 * (1 / (1 + data["fts"])) + 0.4 * data["semantic"]
```
