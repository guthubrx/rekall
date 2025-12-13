"""Embedding cache with LRU eviction and selective invalidation.

Feature 020: Performance optimization for semantic search.
"""

from __future__ import annotations

import logging
from collections import OrderedDict
from time import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """LRU cache for embedding vectors with TTL and invalidation support.

    This cache stores embedding vectors by entry_id, supporting:
    - LRU eviction when maxsize is reached
    - TTL-based expiration (lazy eviction on access)
    - Selective invalidation on entry modification
    - Batch retrieval as numpy matrix for vectorized operations

    Attributes:
        maxsize: Maximum number of entries in cache
        ttl: Time-to-live in seconds for cache entries
    """

    def __init__(self, maxsize: int = 1000, ttl_seconds: int = 600) -> None:
        """Initialize the embedding cache.

        Args:
            maxsize: Maximum number of entries to cache (default: 1000)
            ttl_seconds: Time-to-live in seconds (default: 600 = 10 minutes)
        """
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.maxsize = maxsize
        self.ttl = ttl_seconds

        # Matrix cache for batch operations
        self._matrix_cache: Any = None
        self._matrix_ids: list[str] | None = None
        self._matrix_valid: bool = False

    def get(self, entry_id: str) -> Any:
        """Get a cached embedding vector.

        Updates LRU order on hit. Returns None if not found or expired.

        Args:
            entry_id: The entry ID to look up

        Returns:
            Numpy array of the embedding vector, or None if not cached/expired
        """
        if entry_id not in self._cache:
            return None

        vec, ts = self._cache[entry_id]

        # Check TTL expiration
        if time() - ts > self.ttl:
            del self._cache[entry_id]
            self._matrix_valid = False
            logger.debug("Cache entry expired: %s", entry_id)
            return None

        # Update LRU order (move to end = most recently used)
        self._cache.move_to_end(entry_id)
        return vec

    def put(self, entry_id: str, vector: Any) -> None:
        """Add or update a cached embedding vector.

        Evicts oldest entries if cache is full.

        Args:
            entry_id: The entry ID to cache
            vector: Numpy array of the embedding vector (float32)
        """
        import numpy as np

        # Invalidate matrix cache
        self._matrix_valid = False

        # Update existing entry (moves to end)
        if entry_id in self._cache:
            self._cache.move_to_end(entry_id)
            self._cache[entry_id] = (vector.astype(np.float32), time())
            return

        # Evict oldest if at capacity
        while len(self._cache) >= self.maxsize:
            oldest_id, _ = self._cache.popitem(last=False)
            logger.debug("Cache evicted (LRU): %s", oldest_id)

        # Add new entry
        self._cache[entry_id] = (vector.astype(np.float32), time())

    def invalidate(self, entry_id: str) -> bool:
        """Remove a specific entry from cache.

        Called when an entry is modified or deleted.

        Args:
            entry_id: The entry ID to invalidate

        Returns:
            True if entry was in cache, False otherwise
        """
        if entry_id in self._cache:
            del self._cache[entry_id]
            self._matrix_valid = False
            logger.debug("Cache invalidated: %s", entry_id)
            return True
        return False

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._matrix_cache = None
        self._matrix_ids = None
        self._matrix_valid = False
        logger.debug("Cache cleared")

    def get_all_as_matrix(self) -> tuple[Any, list[str]] | None:
        """Get all cached vectors as a single numpy matrix.

        This method is optimized for batch similarity computation.
        The matrix is cached and only rebuilt when cache content changes.

        Returns:
            Tuple of (matrix, entry_ids) where matrix shape is (N, D),
            or None if cache is empty.
        """
        import numpy as np

        if len(self._cache) == 0:
            return None

        # Return cached matrix if still valid
        if self._matrix_valid and self._matrix_cache is not None:
            return self._matrix_cache, self._matrix_ids  # type: ignore

        # Rebuild matrix (filter expired entries)
        current_time = time()
        valid_entries: list[tuple[str, Any]] = []

        for entry_id, (vec, ts) in list(self._cache.items()):
            if current_time - ts <= self.ttl:
                valid_entries.append((entry_id, vec))
            else:
                # Lazy eviction of expired entries
                del self._cache[entry_id]

        if not valid_entries:
            self._matrix_cache = None
            self._matrix_ids = None
            self._matrix_valid = True
            return None

        # Build matrix and ID list
        self._matrix_ids = [entry_id for entry_id, _ in valid_entries]
        self._matrix_cache = np.vstack([vec for _, vec in valid_entries])
        self._matrix_valid = True

        return self._matrix_cache, self._matrix_ids

    def __len__(self) -> int:
        """Return number of cached entries (may include expired)."""
        return len(self._cache)

    def __contains__(self, entry_id: str) -> bool:
        """Check if entry_id is in cache (doesn't check expiration)."""
        return entry_id in self._cache

    @property
    def stats(self) -> dict[str, int | bool]:
        """Get cache statistics.

        Returns:
            Dict with size, maxsize, ttl, matrix_valid
        """
        return {
            "size": len(self._cache),
            "maxsize": self.maxsize,
            "ttl": self.ttl,
            "matrix_valid": self._matrix_valid,
        }


# Global cache instance (singleton pattern)
_embedding_cache: EmbeddingCache | None = None


def get_embedding_cache(
    maxsize: int | None = None,
    ttl_seconds: int | None = None,
) -> EmbeddingCache:
    """Get or create the global embedding cache.

    Args:
        maxsize: Override default maxsize (only on first call)
        ttl_seconds: Override default TTL (only on first call)

    Returns:
        Global EmbeddingCache instance
    """
    global _embedding_cache

    if _embedding_cache is None:
        from rekall.config import get_config

        config = get_config()
        _embedding_cache = EmbeddingCache(
            maxsize=maxsize or config.perf_cache_max_size,
            ttl_seconds=ttl_seconds or config.perf_cache_ttl_seconds,
        )

    return _embedding_cache


def reset_embedding_cache() -> None:
    """Reset the global embedding cache (for testing)."""
    global _embedding_cache
    _embedding_cache = None
