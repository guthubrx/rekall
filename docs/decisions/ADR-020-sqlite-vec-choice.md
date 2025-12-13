# ADR-020: sqlite-vec for Vector Search

**Status**: Accepted
**Date**: 2024-12-13
**Feature**: 020-embedding-perf

## Context

Rekall uses semantic search with sentence-transformers embeddings. The current implementation uses O(n) brute-force similarity search via Python loops, which becomes slow (2-5s) at 1000+ entries.

We need a vector index for O(log n) similarity search while maintaining:
- SQLite integration (existing DB infrastructure)
- Cross-platform support (macOS, Linux, Windows)
- Lightweight footprint (<10MB dependency)
- Optional dependency (fallback for systems without extension support)

## Decision

Use **sqlite-vec** as the primary vector index with numpy brute-force fallback.

### Alternatives Considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **sqlite-vec** | Native SQLite, ~2MB, ACID transactions, no sync issues | Extension compilation on exotic platforms | **Chosen** |
| **FAISS** | Fastest at scale, GPU support | ~200MB, separate file sync, overkill <500K | Rejected |
| **hnswlib** | Fast, lightweight | Separate index file, no ACID, sync complexity | Rejected |
| **Chromadb** | Full-featured | Heavy dependency, separate server mode | Rejected |
| **Numpy brute-force** | Zero dependencies, simple | O(n) linear, slow at scale | Fallback only |

### Performance Comparison (1M vectors, 384 dimensions)

| Operation | sqlite-vec | FAISS | Brute-force |
|-----------|------------|-------|-------------|
| Build index | 1ms | 126ms | N/A |
| Query (k=10) | 17ms | 10ms | ~500ms |
| Memory | In-DB | Separate | In-memory |

sqlite-vec is 7ms slower per query than FAISS but offers:
- Native SQLite transactions (no sync issues)
- Single-file database (no index corruption)
- Simpler code (no external file management)

For Rekall's target scale (<50K entries), 17ms is acceptable.

## Implementation

### Detection & Fallback

```python
# At startup
SQLITE_VEC_AVAILABLE = False
try:
    import sqlite_vec
    SQLITE_VEC_AVAILABLE = True
except ImportError:
    pass

# Usage
if SQLITE_VEC_AVAILABLE:
    # Use sqlite-vec virtual table
    results = conn.execute(
        "SELECT entry_id, distance FROM embeddings_vec WHERE vector MATCH ? LIMIT ?",
        (query_vec.tobytes(), k)
    )
else:
    # Fallback to numpy batch dot product
    all_vectors = np.vstack([...])  # Load all vectors
    scores = np.dot(all_vectors, query_vec)
    top_k = np.argpartition(scores, -k)[-k:]
```

### Schema Migration (v12)

```sql
-- Only if sqlite-vec available
CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_vec USING vec0(
    entry_id TEXT PRIMARY KEY,
    vector FLOAT[384]
);
```

## Consequences

### Positive
- 10-50x faster similarity search (<500ms for 1000 entries)
- ACID transactions for vector index
- Single-file database (portable, no sync issues)
- Optional dependency (graceful fallback)

### Negative
- Extension not available on all platforms
- sqlite-vec is v0.x (API may change)
- Requires rebuild on embedding dimension change

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Extension unavailable | Numpy fallback (still 10x faster than Python loops) |
| API changes | VectorIndex abstraction layer |
| Dimension mismatch | Validation at add/search time |

## Verification

```bash
# Install optional dependency
pip install sqlite-vec

# Verify extension loads
python -c "import sqlite_vec; print(sqlite_vec.loadable_path())"

# Performance test (after implementation)
time rekall search "test query"  # Target: <500ms on 1000 entries
```

## References

- [sqlite-vec v0.1.0 release](https://alexgarcia.xyz/blog/2024/sqlite-vec-stable-release/)
- [Feature 020 spec](../../specs/020-embedding-perf/spec.md)
- [Research notes](../../specs/020-embedding-perf/research.md)
