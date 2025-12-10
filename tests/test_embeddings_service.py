"""Tests for embedding service (Phase 1 - Smart Embeddings)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


class TestCosineSimilarity:
    """Tests for cosine_similarity function."""

    def test_identical_vectors(self):
        """Identical vectors should have similarity 1.0."""
        from rekall.embeddings import cosine_similarity

        vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        assert cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        """Orthogonal vectors should have similarity 0.0."""
        from rekall.embeddings import cosine_similarity

        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        assert cosine_similarity(vec1, vec2) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        """Opposite vectors should have similarity -1.0."""
        from rekall.embeddings import cosine_similarity

        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
        assert cosine_similarity(vec1, vec2) == pytest.approx(-1.0)

    def test_similar_vectors(self):
        """Similar vectors should have high similarity."""
        from rekall.embeddings import cosine_similarity

        vec1 = np.array([1.0, 0.1, 0.0], dtype=np.float32)
        vec2 = np.array([1.0, 0.2, 0.0], dtype=np.float32)
        sim = cosine_similarity(vec1, vec2)
        assert sim > 0.99  # Very similar

    def test_zero_vector(self):
        """Zero vector should return 0.0 similarity."""
        from rekall.embeddings import cosine_similarity

        vec1 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        vec2 = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        assert cosine_similarity(vec1, vec2) == 0.0


class TestEmbeddingService:
    """Tests for EmbeddingService class."""

    def test_service_creation(self):
        """Service should be created with default values."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService()
        assert service.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        assert service.dimensions == 384
        assert service.similarity_threshold == 0.75
        assert service._model is None

    def test_service_custom_params(self):
        """Service should accept custom parameters."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService(
            model_name="custom-model",
            dimensions=128,
            similarity_threshold=0.8,
        )
        assert service.model_name == "custom-model"
        assert service.dimensions == 128
        assert service.similarity_threshold == 0.8

    def test_availability_check(self):
        """Should check if dependencies are available."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService()
        # This will be True or False depending on environment
        assert isinstance(service.available, bool)

    def test_get_model_status(self):
        """Should return status dict."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService()
        status = service.get_model_status()

        assert "available" in status
        assert "model_name" in status
        assert "target_dimensions" in status
        assert "model_loaded" in status
        assert status["model_loaded"] is False  # Not loaded yet


class TestTextTruncation:
    """Tests for text truncation."""

    def test_short_text_not_truncated(self):
        """Short text should not be truncated."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService()
        text = "Short text"
        result = service._truncate_text(text)
        assert result == text

    def test_long_text_truncated(self):
        """Long text should be truncated to MAX_CONTEXT_CHARS."""
        from rekall.embeddings import MAX_CONTEXT_CHARS, EmbeddingService

        service = EmbeddingService()
        text = "x" * (MAX_CONTEXT_CHARS + 1000)
        result = service._truncate_text(text)
        assert len(result) == MAX_CONTEXT_CHARS

    def test_custom_max_chars(self):
        """Should respect custom max_chars parameter."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService()
        text = "x" * 200
        result = service._truncate_text(text, max_chars=100)
        assert len(result) == 100


class TestMatryoshka:
    """Tests for Matryoshka dimension reduction."""

    def test_no_reduction_needed(self):
        """Should not reduce if vector already smaller."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService(dimensions=384)
        vec = np.random.randn(128).astype(np.float32)
        result = service._apply_matryoshka(vec)
        assert len(result) == 128  # Unchanged

    def test_dimension_reduction(self):
        """Should truncate to target dimensions."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService(dimensions=128)
        vec = np.random.randn(384).astype(np.float32)
        result = service._apply_matryoshka(vec)
        assert len(result) == 128

    def test_renormalization(self):
        """Should re-normalize after truncation."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService(dimensions=128)
        vec = np.random.randn(384).astype(np.float32)
        result = service._apply_matryoshka(vec)
        norm = np.linalg.norm(result)
        assert norm == pytest.approx(1.0, abs=1e-5)


class TestCalculateWithMock:
    """Tests for calculate() using mocked model."""

    def test_calculate_empty_text(self):
        """Empty text should return None."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService()
        assert service.calculate("") is None
        assert service.calculate("   ") is None

    @patch("rekall.embeddings.EmbeddingService._check_availability")
    def test_calculate_unavailable(self, mock_check):
        """Should return None if model not available."""
        from rekall.embeddings import EmbeddingService

        mock_check.return_value = False
        service = EmbeddingService()
        service._available = False

        result = service.calculate("Some text")
        assert result is None

    @patch("rekall.embeddings.EmbeddingService._load_model")
    def test_calculate_with_mock_model(self, mock_load):
        """Should calculate embedding with mocked model."""
        from rekall.embeddings import EmbeddingService

        service = EmbeddingService(dimensions=384)
        service._available = True

        # Mock the model
        mock_model = MagicMock()
        mock_model.encode.return_value = np.random.randn(384).astype(np.float32)
        service._model = mock_model

        result = service.calculate("Test text")

        assert result is not None
        assert len(result) == 384
        mock_model.encode.assert_called_once()


class TestCalculateForEntry:
    """Tests for calculate_for_entry()."""

    @patch("rekall.embeddings.EmbeddingService.calculate")
    def test_summary_only(self, mock_calculate):
        """Should calculate summary embedding."""
        from rekall.embeddings import EmbeddingService
        from rekall.models import Entry, generate_ulid

        mock_calculate.return_value = np.random.randn(384).astype(np.float32)

        service = EmbeddingService()
        entry = Entry(
            id=generate_ulid(),
            title="Test Entry",
            type="bug",
            content="Some content",
            tags=["python", "test"],
        )

        result = service.calculate_for_entry(entry)

        assert "summary" in result
        assert "context" in result
        assert result["summary"] is not None
        assert result["context"] is None

    @patch("rekall.embeddings.EmbeddingService.calculate")
    def test_with_context(self, mock_calculate):
        """Should calculate both summary and context embeddings."""
        from rekall.embeddings import EmbeddingService
        from rekall.models import Entry, generate_ulid

        mock_calculate.return_value = np.random.randn(384).astype(np.float32)

        service = EmbeddingService()
        entry = Entry(
            id=generate_ulid(),
            title="Test Entry",
            type="bug",
        )

        result = service.calculate_for_entry(entry, context="Conversation context")

        assert result["summary"] is not None
        assert result["context"] is not None
        assert mock_calculate.call_count == 2


class TestFindSimilar:
    """Tests for find_similar()."""

    @pytest.fixture
    def temp_db_path(self, tmp_path: Path) -> Path:
        """Create temporary database path."""
        return tmp_path / "test.db"

    def test_find_similar_no_embedding(self, temp_db_path: Path):
        """Should return empty list if entry has no embedding."""
        from rekall.db import Database
        from rekall.embeddings import EmbeddingService
        from rekall.models import Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        db.add(entry)

        service = EmbeddingService()
        result = service.find_similar(entry.id, db)

        assert result == []
        db.close()

    def test_find_similar_with_embeddings(self, temp_db_path: Path):
        """Should find similar entries based on embeddings."""
        from rekall.db import Database
        from rekall.embeddings import EmbeddingService
        from rekall.models import Embedding, Entry, generate_ulid

        db = Database(temp_db_path)
        db.init()

        # Create entries
        entry1 = Entry(id=generate_ulid(), title="Python bug", type="bug")
        entry2 = Entry(id=generate_ulid(), title="Python error", type="bug")
        entry3 = Entry(id=generate_ulid(), title="JavaScript issue", type="bug")
        db.add(entry1)
        db.add(entry2)
        db.add(entry3)

        # Create similar embeddings for entry1 and entry2
        vec1 = np.array([1.0, 0.0, 0.0] + [0.0] * 381, dtype=np.float32)
        vec2 = np.array([0.99, 0.1, 0.0] + [0.0] * 381, dtype=np.float32)
        vec3 = np.array([0.0, 1.0, 0.0] + [0.0] * 381, dtype=np.float32)

        # Normalize
        vec1 = vec1 / np.linalg.norm(vec1)
        vec2 = vec2 / np.linalg.norm(vec2)
        vec3 = vec3 / np.linalg.norm(vec3)

        emb1 = Embedding.from_numpy(entry1.id, "summary", vec1, "test")
        emb2 = Embedding.from_numpy(entry2.id, "summary", vec2, "test")
        emb3 = Embedding.from_numpy(entry3.id, "summary", vec3, "test")
        db.add_embedding(emb1)
        db.add_embedding(emb2)
        db.add_embedding(emb3)

        service = EmbeddingService(similarity_threshold=0.9)
        result = service.find_similar(entry1.id, db)

        # Should find entry2 (similar) but not entry3 (different)
        assert len(result) == 1
        assert result[0][0].id == entry2.id
        assert result[0][1] > 0.9

        db.close()


class TestSingleton:
    """Tests for singleton pattern."""

    def test_get_embedding_service(self):
        """Should return singleton instance."""
        from rekall.embeddings import get_embedding_service, reset_embedding_service

        reset_embedding_service()
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        assert service1 is service2

    def test_reset_service(self):
        """Should reset singleton."""
        from rekall.embeddings import get_embedding_service, reset_embedding_service

        service1 = get_embedding_service()
        reset_embedding_service()
        service2 = get_embedding_service()
        assert service1 is not service2


class TestExceptionClass:
    """Tests for custom exception."""

    def test_exception_message(self):
        """Exception should have message."""
        from rekall.embeddings import EmbeddingModelNotAvailable

        exc = EmbeddingModelNotAvailable("Test error")
        assert str(exc) == "Test error"

    def test_exception_inheritance(self):
        """Should inherit from Exception."""
        from rekall.embeddings import EmbeddingModelNotAvailable

        assert issubclass(EmbeddingModelNotAvailable, Exception)
