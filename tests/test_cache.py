"""Tests for EmbeddingCache (Feature 020)."""

from __future__ import annotations

from time import sleep
from unittest.mock import patch

import numpy as np
import pytest

from rekall.cache import EmbeddingCache, get_embedding_cache, reset_embedding_cache


class TestEmbeddingCacheBasics:
    """Test basic cache operations."""

    def test_init_defaults(self) -> None:
        """Test cache initializes with default values."""
        cache = EmbeddingCache()
        assert cache.maxsize == 1000
        assert cache.ttl == 600
        assert len(cache) == 0

    def test_init_custom(self) -> None:
        """Test cache initializes with custom values."""
        cache = EmbeddingCache(maxsize=100, ttl_seconds=60)
        assert cache.maxsize == 100
        assert cache.ttl == 60

    def test_put_and_get(self) -> None:
        """Test putting and getting vectors."""
        cache = EmbeddingCache()
        vec = np.random.randn(384).astype(np.float32)

        cache.put("entry1", vec)
        result = cache.get("entry1")

        assert result is not None
        np.testing.assert_array_almost_equal(result, vec)

    def test_get_missing(self) -> None:
        """Test getting non-existent entry returns None."""
        cache = EmbeddingCache()
        assert cache.get("nonexistent") is None

    def test_contains(self) -> None:
        """Test __contains__ method."""
        cache = EmbeddingCache()
        vec = np.random.randn(384).astype(np.float32)

        assert "entry1" not in cache
        cache.put("entry1", vec)
        assert "entry1" in cache


class TestEmbeddingCacheLRU:
    """Test LRU eviction behavior."""

    def test_lru_eviction(self) -> None:
        """Test oldest entries are evicted when cache is full."""
        cache = EmbeddingCache(maxsize=3)
        vecs = [np.random.randn(384).astype(np.float32) for _ in range(4)]

        cache.put("entry1", vecs[0])
        cache.put("entry2", vecs[1])
        cache.put("entry3", vecs[2])

        # Cache is full, adding entry4 should evict entry1
        cache.put("entry4", vecs[3])

        assert "entry1" not in cache  # Evicted
        assert "entry2" in cache
        assert "entry3" in cache
        assert "entry4" in cache

    def test_lru_access_updates_order(self) -> None:
        """Test that accessing an entry updates its LRU position."""
        cache = EmbeddingCache(maxsize=3)
        vecs = [np.random.randn(384).astype(np.float32) for _ in range(4)]

        cache.put("entry1", vecs[0])
        cache.put("entry2", vecs[1])
        cache.put("entry3", vecs[2])

        # Access entry1 to move it to end (most recently used)
        cache.get("entry1")

        # Now add entry4 - should evict entry2 (oldest unused)
        cache.put("entry4", vecs[3])

        assert "entry1" in cache  # Was accessed, kept
        assert "entry2" not in cache  # Evicted (oldest)
        assert "entry3" in cache
        assert "entry4" in cache


class TestEmbeddingCacheTTL:
    """Test TTL expiration behavior."""

    def test_ttl_expiration_on_get(self) -> None:
        """Test that expired entries return None on get."""
        cache = EmbeddingCache(ttl_seconds=1)  # 1 second TTL
        vec = np.random.randn(384).astype(np.float32)

        cache.put("entry1", vec)
        assert cache.get("entry1") is not None

        # Wait for expiration
        sleep(1.1)

        # Should return None and remove from cache
        assert cache.get("entry1") is None

    def test_ttl_expiration_updates_matrix_valid(self) -> None:
        """Test that TTL expiration invalidates matrix cache."""
        cache = EmbeddingCache(ttl_seconds=1)
        vec = np.random.randn(384).astype(np.float32)

        cache.put("entry1", vec)
        cache.get_all_as_matrix()  # Build matrix cache
        assert cache._matrix_valid is True

        sleep(1.1)

        # Getting expired entry should invalidate matrix
        cache.get("entry1")
        assert cache._matrix_valid is False


class TestEmbeddingCacheInvalidation:
    """Test invalidation behavior."""

    def test_invalidate_existing(self) -> None:
        """Test invalidating an existing entry."""
        cache = EmbeddingCache()
        vec = np.random.randn(384).astype(np.float32)

        cache.put("entry1", vec)
        assert "entry1" in cache

        result = cache.invalidate("entry1")

        assert result is True
        assert "entry1" not in cache

    def test_invalidate_nonexistent(self) -> None:
        """Test invalidating a non-existent entry."""
        cache = EmbeddingCache()
        result = cache.invalidate("nonexistent")
        assert result is False

    def test_invalidate_updates_matrix_valid(self) -> None:
        """Test that invalidation invalidates matrix cache."""
        cache = EmbeddingCache()
        vec = np.random.randn(384).astype(np.float32)

        cache.put("entry1", vec)
        cache.get_all_as_matrix()  # Build matrix cache
        assert cache._matrix_valid is True

        cache.invalidate("entry1")
        assert cache._matrix_valid is False

    def test_clear(self) -> None:
        """Test clearing all entries."""
        cache = EmbeddingCache()
        vecs = [np.random.randn(384).astype(np.float32) for _ in range(5)]

        for i, vec in enumerate(vecs):
            cache.put(f"entry{i}", vec)

        assert len(cache) == 5

        cache.clear()

        assert len(cache) == 0
        assert cache._matrix_cache is None
        assert cache._matrix_valid is False


class TestEmbeddingCacheMatrix:
    """Test batch matrix operations."""

    def test_get_all_as_matrix_empty(self) -> None:
        """Test getting matrix from empty cache."""
        cache = EmbeddingCache()
        result = cache.get_all_as_matrix()
        assert result is None

    def test_get_all_as_matrix(self) -> None:
        """Test getting all vectors as matrix."""
        cache = EmbeddingCache()
        vecs = [np.random.randn(384).astype(np.float32) for _ in range(5)]

        for i, vec in enumerate(vecs):
            cache.put(f"entry{i}", vec)

        result = cache.get_all_as_matrix()

        assert result is not None
        matrix, ids = result

        assert matrix.shape == (5, 384)
        assert len(ids) == 5
        assert set(ids) == {f"entry{i}" for i in range(5)}

    def test_matrix_cache_validity(self) -> None:
        """Test that matrix is cached and reused."""
        cache = EmbeddingCache()
        vec = np.random.randn(384).astype(np.float32)

        cache.put("entry1", vec)

        # First call builds cache
        result1 = cache.get_all_as_matrix()
        assert result1 is not None
        assert cache._matrix_valid is True

        # Second call reuses cache
        result2 = cache.get_all_as_matrix()
        assert result2 is not None

        # Should be same object (cached)
        assert result1[0] is result2[0]

    def test_matrix_invalidated_on_put(self) -> None:
        """Test that matrix is invalidated on put."""
        cache = EmbeddingCache()
        vec1 = np.random.randn(384).astype(np.float32)
        vec2 = np.random.randn(384).astype(np.float32)

        cache.put("entry1", vec1)
        cache.get_all_as_matrix()
        assert cache._matrix_valid is True

        cache.put("entry2", vec2)
        assert cache._matrix_valid is False

    def test_matrix_filters_expired(self) -> None:
        """Test that matrix excludes expired entries."""
        cache = EmbeddingCache(ttl_seconds=1)
        vec1 = np.random.randn(384).astype(np.float32)

        cache.put("entry1", vec1)

        sleep(1.1)

        # Add fresh entry
        vec2 = np.random.randn(384).astype(np.float32)
        cache.put("entry2", vec2)

        result = cache.get_all_as_matrix()

        assert result is not None
        matrix, ids = result

        # Only entry2 should be in matrix (entry1 expired)
        assert matrix.shape == (1, 384)
        assert ids == ["entry2"]


class TestEmbeddingCacheStats:
    """Test statistics reporting."""

    def test_stats(self) -> None:
        """Test stats property."""
        cache = EmbeddingCache(maxsize=100, ttl_seconds=60)
        vec = np.random.randn(384).astype(np.float32)

        cache.put("entry1", vec)

        stats = cache.stats

        assert stats["size"] == 1
        assert stats["maxsize"] == 100
        assert stats["ttl"] == 60
        assert stats["matrix_valid"] is False


class TestEmbeddingCacheSingleton:
    """Test singleton pattern."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        reset_embedding_cache()

    def teardown_method(self) -> None:
        """Reset singleton after each test."""
        reset_embedding_cache()

    def test_get_embedding_cache_singleton(self) -> None:
        """Test that get_embedding_cache returns same instance."""
        with patch("rekall.config.get_config") as mock_config:
            mock_config.return_value.perf_cache_max_size = 500
            mock_config.return_value.perf_cache_ttl_seconds = 300

            cache1 = get_embedding_cache()
            cache2 = get_embedding_cache()

            assert cache1 is cache2

    def test_reset_embedding_cache(self) -> None:
        """Test that reset creates new instance."""
        with patch("rekall.config.get_config") as mock_config:
            mock_config.return_value.perf_cache_max_size = 500
            mock_config.return_value.perf_cache_ttl_seconds = 300

            cache1 = get_embedding_cache()
            reset_embedding_cache()
            cache2 = get_embedding_cache()

            assert cache1 is not cache2
