"""Vector index abstraction for similarity search.

Feature 020: sqlite-vec integration with numpy fallback.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)

# Check sqlite-vec availability at import time
SQLITE_VEC_AVAILABLE = False
_sqlite_vec_path: str | None = None

try:
    import sqlite_vec

    _sqlite_vec_path = sqlite_vec.loadable_path()
    SQLITE_VEC_AVAILABLE = True
    logger.debug("sqlite-vec available at: %s", _sqlite_vec_path)
except ImportError:
    logger.debug("sqlite-vec not installed, will use numpy fallback")
except Exception as e:
    logger.warning("sqlite-vec import error: %s", e)


class VectorIndex:
    """Vector similarity search with sqlite-vec or numpy fallback.

    Provides O(log n) similarity search when sqlite-vec is available,
    falls back to O(n) vectorized numpy operations otherwise.

    The numpy fallback is still ~50x faster than Python loops due to
    vectorized operations.

    Attributes:
        backend: Current backend ("sqlite-vec" or "numpy")
        dimensions: Vector dimensions (default: 384 for all-MiniLM-L6-v2)
    """

    def __init__(
        self,
        conn: sqlite3.Connection,
        dimensions: int = 384,
        backend: str = "auto",
    ) -> None:
        """Initialize the vector index.

        Args:
            conn: SQLite connection to use
            dimensions: Vector dimensions (default: 384)
            backend: "auto", "sqlite-vec", or "numpy"
        """
        self._conn = conn
        self._dimensions = dimensions
        self._requested_backend = backend

        # Determine actual backend
        if backend == "auto":
            self._backend = "sqlite-vec" if SQLITE_VEC_AVAILABLE else "numpy"
        elif backend == "sqlite-vec":
            if not SQLITE_VEC_AVAILABLE:
                logger.warning("sqlite-vec requested but not available, using numpy")
                self._backend = "numpy"
            else:
                self._backend = "sqlite-vec"
        else:
            self._backend = "numpy"

        self._vec_loaded = False

        # Initialize sqlite-vec if using it
        if self._backend == "sqlite-vec":
            self._init_sqlite_vec()

        logger.info("VectorIndex initialized with backend: %s", self._backend)

    def _init_sqlite_vec(self) -> None:
        """Initialize sqlite-vec extension."""
        if not SQLITE_VEC_AVAILABLE or _sqlite_vec_path is None:
            return

        try:
            self._conn.enable_load_extension(True)
            self._conn.load_extension(_sqlite_vec_path)
            self._conn.enable_load_extension(False)
            self._vec_loaded = True
            logger.debug("sqlite-vec extension loaded successfully")
        except Exception as e:
            logger.warning("Failed to load sqlite-vec: %s", e)
            self._backend = "numpy"

    def search(
        self,
        query_vec: NDArray[np.float32],
        k: int = 10,
        entry_ids: list[str] | None = None,
        vectors: NDArray[np.float32] | None = None,
    ) -> list[tuple[str, float]]:
        """Search for k most similar vectors.

        Args:
            query_vec: Query vector (1D array, normalized)
            k: Number of results to return
            entry_ids: Optional list of entry IDs (for numpy fallback)
            vectors: Optional matrix of vectors (for numpy fallback)

        Returns:
            List of (entry_id, similarity_score) tuples, sorted by similarity descending
        """
        if self._backend == "sqlite-vec" and self._vec_loaded:
            return self._search_sqlite_vec(query_vec, k)
        else:
            if entry_ids is None or vectors is None:
                logger.warning("Numpy fallback requires entry_ids and vectors")
                return []
            return self._search_numpy(query_vec, k, entry_ids, vectors)

    def _search_sqlite_vec(
        self,
        query_vec: NDArray[np.float32],
        k: int,
    ) -> list[tuple[str, float]]:
        """Search using sqlite-vec virtual table.

        Note: sqlite-vec uses L2 distance, we convert to cosine similarity.
        For normalized vectors: cosine_sim = 1 - (L2_dist^2 / 2)
        """
        try:
            # Query sqlite-vec virtual table
            cursor = self._conn.execute(
                """
                SELECT entry_id, distance
                FROM embeddings_vec
                WHERE vector MATCH ?
                ORDER BY distance
                LIMIT ?
                """,
                (query_vec.astype(np.float32).tobytes(), k),
            )

            results = []
            for row in cursor:
                entry_id = row[0]
                l2_distance = row[1]
                # Convert L2 distance to cosine similarity
                # For normalized vectors: cos_sim ≈ 1 - (dist² / 2)
                similarity = 1.0 - (l2_distance * l2_distance / 2.0)
                results.append((entry_id, float(similarity)))

            return results

        except sqlite3.OperationalError as e:
            logger.warning("sqlite-vec search failed: %s", e)
            return []

    def _search_numpy(
        self,
        query_vec: NDArray[np.float32],
        k: int,
        entry_ids: list[str],
        vectors: NDArray[np.float32],
    ) -> list[tuple[str, float]]:
        """Search using vectorized numpy operations.

        Computes cosine similarity via dot product (assumes normalized vectors).
        Uses argpartition for O(n + k log k) top-k selection.
        """
        if len(entry_ids) == 0:
            return []

        # Ensure query is normalized
        query_norm = np.linalg.norm(query_vec)
        if query_norm > 0:
            query_vec = query_vec / query_norm

        # Batch dot product: (N, D) @ (D,) -> (N,)
        # For normalized vectors, dot product = cosine similarity
        similarities = np.dot(vectors, query_vec)

        # Get top-k indices using argpartition (O(n + k log k))
        k = min(k, len(similarities))
        if k == len(similarities):
            top_indices = np.argsort(similarities)[::-1]
        else:
            # argpartition is faster than full sort for large arrays
            partition_idx = np.argpartition(similarities, -k)[-k:]
            # Sort the top k by similarity
            top_indices = partition_idx[np.argsort(similarities[partition_idx])[::-1]]

        # Build results
        results = [(entry_ids[i], float(similarities[i])) for i in top_indices]
        return results

    def add(self, entry_id: str, vector: NDArray[np.float32]) -> bool:
        """Add a vector to the index.

        Args:
            entry_id: Entry ID
            vector: Embedding vector (will be normalized)

        Returns:
            True if successful
        """
        if self._backend != "sqlite-vec" or not self._vec_loaded:
            # Numpy fallback doesn't maintain persistent index
            return True

        try:
            # Normalize vector
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm

            self._conn.execute(
                """
                INSERT OR REPLACE INTO embeddings_vec (entry_id, vector)
                VALUES (?, ?)
                """,
                (entry_id, vector.astype(np.float32).tobytes()),
            )
            return True

        except sqlite3.OperationalError as e:
            logger.warning("Failed to add vector to index: %s", e)
            return False

    def delete(self, entry_id: str) -> bool:
        """Delete a vector from the index.

        Args:
            entry_id: Entry ID to delete

        Returns:
            True if successful
        """
        if self._backend != "sqlite-vec" or not self._vec_loaded:
            return True

        try:
            self._conn.execute(
                "DELETE FROM embeddings_vec WHERE entry_id = ?",
                (entry_id,),
            )
            return True

        except sqlite3.OperationalError as e:
            logger.warning("Failed to delete vector from index: %s", e)
            return False

    def rebuild(self) -> int:
        """Rebuild the index from the embeddings table.

        Returns:
            Number of vectors indexed
        """
        if self._backend != "sqlite-vec" or not self._vec_loaded:
            logger.info("Rebuild skipped (not using sqlite-vec)")
            return 0

        try:
            # Clear existing index
            self._conn.execute("DELETE FROM embeddings_vec")

            # Copy vectors from embeddings table
            cursor = self._conn.execute(
                """
                SELECT entry_id, vector
                FROM embeddings
                WHERE embedding_type = 'summary'
                """
            )

            count = 0
            for row in cursor:
                entry_id = row[0]
                vector = np.frombuffer(row[1], dtype=np.float32)

                # Normalize
                norm = np.linalg.norm(vector)
                if norm > 0:
                    vector = vector / norm

                self._conn.execute(
                    "INSERT INTO embeddings_vec (entry_id, vector) VALUES (?, ?)",
                    (entry_id, vector.tobytes()),
                )
                count += 1

            self._conn.commit()
            logger.info("Index rebuilt with %d vectors", count)
            return count

        except sqlite3.OperationalError as e:
            logger.error("Index rebuild failed: %s", e)
            return 0

    def is_available(self) -> bool:
        """Check if sqlite-vec is available and loaded.

        Returns:
            True if sqlite-vec is active, False if using numpy fallback
        """
        return self._backend == "sqlite-vec" and self._vec_loaded

    @property
    def backend(self) -> str:
        """Get the current backend name."""
        return self._backend

    @property
    def dimensions(self) -> int:
        """Get the vector dimensions."""
        return self._dimensions

    @property
    def stats(self) -> dict[str, str | int | bool]:
        """Get vector index statistics.

        Returns:
            Dict with backend, dimensions, sqlite_vec_available, vec_loaded
        """
        return {
            "backend": self._backend,
            "requested_backend": self._requested_backend,
            "dimensions": self._dimensions,
            "sqlite_vec_available": SQLITE_VEC_AVAILABLE,
            "vec_loaded": self._vec_loaded,
        }


def create_embeddings_vec_table(conn: sqlite3.Connection, dimensions: int = 384) -> bool:
    """Create the embeddings_vec virtual table if sqlite-vec is available.

    Args:
        conn: SQLite connection
        dimensions: Vector dimensions

    Returns:
        True if table was created, False if sqlite-vec unavailable
    """
    if not SQLITE_VEC_AVAILABLE or _sqlite_vec_path is None:
        logger.debug("Cannot create embeddings_vec: sqlite-vec not available")
        return False

    try:
        conn.enable_load_extension(True)
        conn.load_extension(_sqlite_vec_path)
        conn.enable_load_extension(False)

        # Create virtual table
        conn.execute(
            f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS embeddings_vec USING vec0(
                entry_id TEXT PRIMARY KEY,
                vector FLOAT[{dimensions}]
            )
            """
        )
        conn.commit()
        logger.info("Created embeddings_vec table (dimensions: %d)", dimensions)
        return True

    except Exception as e:
        logger.warning("Failed to create embeddings_vec table: %s", e)
        return False
