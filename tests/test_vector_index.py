"""Tests for VectorIndex (Feature 020)."""

from __future__ import annotations

import sqlite3
from unittest.mock import patch

import numpy as np
import pytest

from rekall.vector_index import (
    SQLITE_VEC_AVAILABLE,
    VectorIndex,
    create_embeddings_vec_table,
)


def create_test_connection() -> sqlite3.Connection:
    """Create an in-memory SQLite connection for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn


class TestVectorIndexBasics:
    """Test basic VectorIndex operations."""

    def test_init_defaults(self) -> None:
        """Test index initializes with default values."""
        conn = create_test_connection()
        index = VectorIndex(conn, dimensions=384, backend="numpy")

        assert index.dimensions == 384
        assert index.backend == "numpy"

    def test_init_auto_backend_without_sqlite_vec(self) -> None:
        """Test auto backend falls back to numpy when sqlite-vec unavailable."""
        conn = create_test_connection()

        with patch("rekall.vector_index.SQLITE_VEC_AVAILABLE", False):
            index = VectorIndex(conn, backend="auto")

            assert index.backend == "numpy"

    def test_stats(self) -> None:
        """Test stats property."""
        conn = create_test_connection()
        index = VectorIndex(conn, dimensions=384, backend="numpy")

        stats = index.stats

        assert stats["backend"] == "numpy"
        assert stats["dimensions"] == 384
        assert "sqlite_vec_available" in stats

    def test_is_available_numpy(self) -> None:
        """Test is_available returns False for numpy backend."""
        conn = create_test_connection()
        index = VectorIndex(conn, backend="numpy")

        assert index.is_available() is False


class TestVectorIndexNumpySearch:
    """Test numpy fallback search."""

    def test_search_numpy_basic(self) -> None:
        """Test basic numpy search."""
        conn = create_test_connection()
        index = VectorIndex(conn, dimensions=384, backend="numpy")

        # Create test data
        np.random.seed(42)
        entry_ids = ["entry1", "entry2", "entry3", "entry4", "entry5"]
        vectors = np.random.randn(5, 384).astype(np.float32)

        # Normalize vectors
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / norms

        # Query vector (use first vector as query)
        query_vec = vectors[0]

        results = index.search(
            query_vec=query_vec,
            k=3,
            entry_ids=entry_ids,
            vectors=vectors,
        )

        assert len(results) == 3
        # First result should be entry1 (query itself)
        assert results[0][0] == "entry1"
        assert results[0][1] > 0.99  # Should be ~1.0 (same vector)

    def test_search_numpy_returns_sorted(self) -> None:
        """Test numpy search returns results sorted by similarity."""
        conn = create_test_connection()
        index = VectorIndex(conn, dimensions=384, backend="numpy")

        np.random.seed(42)
        entry_ids = [f"entry{i}" for i in range(10)]
        vectors = np.random.randn(10, 384).astype(np.float32)

        # Normalize
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / norms

        query_vec = np.random.randn(384).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)

        results = index.search(
            query_vec=query_vec,
            k=5,
            entry_ids=entry_ids,
            vectors=vectors,
        )

        # Results should be in descending order of similarity
        similarities = [score for _, score in results]
        assert similarities == sorted(similarities, reverse=True)

    def test_search_numpy_empty_data(self) -> None:
        """Test numpy search with empty data."""
        conn = create_test_connection()
        index = VectorIndex(conn, backend="numpy")

        query_vec = np.random.randn(384).astype(np.float32)

        results = index.search(
            query_vec=query_vec,
            k=10,
            entry_ids=[],
            vectors=np.array([]).reshape(0, 384).astype(np.float32),
        )

        assert results == []

    def test_search_numpy_k_larger_than_data(self) -> None:
        """Test numpy search when k > number of vectors."""
        conn = create_test_connection()
        index = VectorIndex(conn, dimensions=384, backend="numpy")

        np.random.seed(42)
        entry_ids = ["entry1", "entry2", "entry3"]
        vectors = np.random.randn(3, 384).astype(np.float32)

        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / norms

        query_vec = np.random.randn(384).astype(np.float32)
        query_vec = query_vec / np.linalg.norm(query_vec)

        results = index.search(
            query_vec=query_vec,
            k=10,  # More than available
            entry_ids=entry_ids,
            vectors=vectors,
        )

        assert len(results) == 3  # Returns all available

    def test_search_numpy_normalizes_query(self) -> None:
        """Test numpy search normalizes query vector."""
        conn = create_test_connection()
        index = VectorIndex(conn, dimensions=384, backend="numpy")

        np.random.seed(42)
        entry_ids = ["entry1"]
        vectors = np.random.randn(1, 384).astype(np.float32)

        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / norms

        # Non-normalized query
        query_vec = vectors[0] * 5  # Scale up

        results = index.search(
            query_vec=query_vec,
            k=1,
            entry_ids=entry_ids,
            vectors=vectors,
        )

        # Should still match (query is normalized internally)
        assert len(results) == 1
        assert results[0][1] > 0.99

    def test_search_without_data_logs_warning(self) -> None:
        """Test search without entry_ids/vectors logs warning."""
        conn = create_test_connection()
        index = VectorIndex(conn, backend="numpy")

        query_vec = np.random.randn(384).astype(np.float32)

        # Missing data
        results = index.search(query_vec=query_vec, k=10)

        assert results == []


class TestVectorIndexAddDelete:
    """Test add/delete operations."""

    def test_add_numpy_backend(self) -> None:
        """Test add is no-op for numpy backend."""
        conn = create_test_connection()
        index = VectorIndex(conn, backend="numpy")

        vec = np.random.randn(384).astype(np.float32)
        result = index.add("entry1", vec)

        # Should return True (no-op success)
        assert result is True

    def test_delete_numpy_backend(self) -> None:
        """Test delete is no-op for numpy backend."""
        conn = create_test_connection()
        index = VectorIndex(conn, backend="numpy")

        result = index.delete("entry1")

        # Should return True (no-op success)
        assert result is True

    def test_rebuild_numpy_backend(self) -> None:
        """Test rebuild returns 0 for numpy backend."""
        conn = create_test_connection()
        index = VectorIndex(conn, backend="numpy")

        count = index.rebuild()

        assert count == 0


class TestVectorIndexSqliteVec:
    """Test sqlite-vec integration (skipped if not available)."""

    @pytest.mark.skipif(not SQLITE_VEC_AVAILABLE, reason="sqlite-vec not installed")
    def test_init_sqlite_vec_backend(self) -> None:
        """Test initialization with sqlite-vec backend."""
        conn = create_test_connection()
        index = VectorIndex(conn, backend="sqlite-vec")

        assert index.backend == "sqlite-vec"
        assert index.is_available() is True

    @pytest.mark.skipif(not SQLITE_VEC_AVAILABLE, reason="sqlite-vec not installed")
    def test_create_embeddings_vec_table(self) -> None:
        """Test creating embeddings_vec virtual table."""
        conn = create_test_connection()

        result = create_embeddings_vec_table(conn, dimensions=384)

        assert result is True

        # Verify table exists
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings_vec'"
        )
        assert cursor.fetchone() is not None


class TestVectorIndexSqliteVecFallback:
    """Test sqlite-vec fallback behavior."""

    def test_sqlite_vec_requested_but_unavailable(self) -> None:
        """Test fallback to numpy when sqlite-vec requested but unavailable."""
        conn = create_test_connection()

        with patch("rekall.vector_index.SQLITE_VEC_AVAILABLE", False):
            index = VectorIndex(conn, backend="sqlite-vec")

            # Should fall back to numpy
            assert index.backend == "numpy"
            assert index.is_available() is False

    def test_create_table_returns_false_without_sqlite_vec(self) -> None:
        """Test create_embeddings_vec_table returns False without sqlite-vec."""
        conn = create_test_connection()

        with patch("rekall.vector_index.SQLITE_VEC_AVAILABLE", False):
            result = create_embeddings_vec_table(conn)

            assert result is False


class TestVectorIndexCosineSimularity:
    """Test cosine similarity computation."""

    def test_identical_vectors_similarity_one(self) -> None:
        """Test identical vectors have similarity ~1.0."""
        conn = create_test_connection()
        index = VectorIndex(conn, backend="numpy")

        vec = np.random.randn(384).astype(np.float32)
        vec = vec / np.linalg.norm(vec)

        results = index.search(
            query_vec=vec,
            k=1,
            entry_ids=["entry1"],
            vectors=vec.reshape(1, -1),
        )

        assert len(results) == 1
        assert abs(results[0][1] - 1.0) < 0.01  # ~1.0

    def test_orthogonal_vectors_similarity_zero(self) -> None:
        """Test orthogonal vectors have similarity ~0."""
        conn = create_test_connection()
        index = VectorIndex(conn, backend="numpy")

        # Create orthogonal vectors
        vec1 = np.zeros(384, dtype=np.float32)
        vec1[0] = 1.0

        vec2 = np.zeros(384, dtype=np.float32)
        vec2[1] = 1.0

        results = index.search(
            query_vec=vec1,
            k=1,
            entry_ids=["entry1"],
            vectors=vec2.reshape(1, -1),
        )

        assert len(results) == 1
        assert abs(results[0][1]) < 0.01  # ~0

    def test_opposite_vectors_similarity_negative(self) -> None:
        """Test opposite vectors have similarity ~-1.0."""
        conn = create_test_connection()
        index = VectorIndex(conn, backend="numpy")

        vec = np.random.randn(384).astype(np.float32)
        vec = vec / np.linalg.norm(vec)

        opposite = -vec

        results = index.search(
            query_vec=vec,
            k=1,
            entry_ids=["entry1"],
            vectors=opposite.reshape(1, -1),
        )

        assert len(results) == 1
        assert abs(results[0][1] - (-1.0)) < 0.01  # ~-1.0
