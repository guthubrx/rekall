"""Tests for ModelManager (Feature 020)."""

from __future__ import annotations

import sys
from time import sleep
from unittest.mock import MagicMock, patch

import pytest

from rekall.model_manager import (
    ModelManager,
    get_model_manager,
    reset_model_manager,
)


# Helper to mock sentence_transformers module
@pytest.fixture
def mock_sentence_transformers():
    """Inject a mock sentence_transformers module."""
    mock_module = MagicMock()
    mock_model = MagicMock()
    mock_model.get_sentence_embedding_dimension.return_value = 384
    mock_module.SentenceTransformer.return_value = mock_model

    # Store original if exists
    original = sys.modules.get("sentence_transformers")

    # Inject mock
    sys.modules["sentence_transformers"] = mock_module

    yield mock_module, mock_model

    # Restore original
    if original is not None:
        sys.modules["sentence_transformers"] = original
    else:
        sys.modules.pop("sentence_transformers", None)


class TestModelManagerBasics:
    """Test basic ModelManager operations."""

    def test_init_defaults(self) -> None:
        """Test manager initializes with default values."""
        manager = ModelManager()
        assert manager.model_name == "all-MiniLM-L6-v2"
        assert manager.timeout_minutes == 10
        assert not manager.is_loaded()
        assert not manager.is_loading()

    def test_init_custom(self) -> None:
        """Test manager initializes with custom values."""
        manager = ModelManager(
            model_name="custom-model",
            timeout_minutes=5,
        )
        assert manager.model_name == "custom-model"
        assert manager.timeout_minutes == 5

    def test_is_loaded_false_initially(self) -> None:
        """Test model is not loaded initially."""
        manager = ModelManager()
        assert manager.is_loaded() is False

    def test_dimensions_none_before_load(self) -> None:
        """Test dimensions is None before model is loaded."""
        manager = ModelManager()
        assert manager.dimensions is None


class TestModelManagerLoading:
    """Test model loading behavior."""

    def test_get_model_loads_model(self, mock_sentence_transformers) -> None:
        """Test get_model loads the model."""
        mock_module, mock_model = mock_sentence_transformers
        manager = ModelManager()

        model = manager.get_model()

        assert model is mock_model
        assert manager.is_loaded() is True
        mock_module.SentenceTransformer.assert_called_once_with("all-MiniLM-L6-v2")

    def test_get_model_returns_cached_model(self, mock_sentence_transformers) -> None:
        """Test get_model returns cached model on subsequent calls."""
        mock_module, mock_model = mock_sentence_transformers
        manager = ModelManager()

        model1 = manager.get_model()
        model2 = manager.get_model()

        assert model1 is model2
        # Should only be called once (cached)
        mock_module.SentenceTransformer.assert_called_once()

    def test_get_model_updates_last_used(self, mock_sentence_transformers) -> None:
        """Test get_model updates last_used timestamp."""
        mock_module, mock_model = mock_sentence_transformers
        manager = ModelManager()

        manager.get_model()

        assert manager._last_used > 0

    def test_get_model_import_error(self) -> None:
        """Test get_model raises ImportError if sentence-transformers not installed."""
        manager = ModelManager()

        # Ensure module is not in sys.modules
        original = sys.modules.pop("sentence_transformers", None)
        try:
            with pytest.raises(ImportError, match="sentence-transformers"):
                manager.get_model()
        finally:
            # Restore if was present
            if original is not None:
                sys.modules["sentence_transformers"] = original

    def test_is_loading_during_load(self) -> None:
        """Test is_loading returns True during model loading."""
        manager = ModelManager()
        loading_states = []

        def capture_loading(*args, **kwargs):
            loading_states.append(manager.is_loading())
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            return mock_model

        # Create mock module with side effect
        mock_module = MagicMock()
        mock_module.SentenceTransformer.side_effect = capture_loading
        sys.modules["sentence_transformers"] = mock_module

        try:
            manager.get_model()
        finally:
            sys.modules.pop("sentence_transformers", None)

        # Should have captured True during loading
        assert True in loading_states

        # Should be False after loading
        assert manager.is_loading() is False


class TestModelManagerIdleUnload:
    """Test idle timeout and unload behavior."""

    def test_check_idle_no_unload_before_timeout(self, mock_sentence_transformers) -> None:
        """Test check_idle doesn't unload before timeout."""
        mock_module, mock_model = mock_sentence_transformers
        manager = ModelManager(timeout_minutes=1)

        manager.get_model()
        assert manager.is_loaded() is True

        # Check idle immediately (should not unload)
        unloaded = manager.check_idle()

        assert unloaded is False
        assert manager.is_loaded() is True

    def test_check_idle_unloads_after_timeout(self, mock_sentence_transformers) -> None:
        """Test check_idle unloads after timeout."""
        mock_module, mock_model = mock_sentence_transformers
        # Use very short timeout for testing
        manager = ModelManager(timeout_minutes=0.01)  # 0.6 seconds

        manager.get_model()
        assert manager.is_loaded() is True

        # Wait for timeout
        sleep(1)

        unloaded = manager.check_idle()

        assert unloaded is True
        assert manager.is_loaded() is False

    def test_check_idle_returns_false_if_not_loaded(self) -> None:
        """Test check_idle returns False if model not loaded."""
        manager = ModelManager()
        assert manager.check_idle() is False

    def test_unload_frees_model(self, mock_sentence_transformers) -> None:
        """Test unload frees the model."""
        mock_module, mock_model = mock_sentence_transformers
        manager = ModelManager()

        manager.get_model()
        assert manager.is_loaded() is True
        assert manager.dimensions == 384

        manager.unload()

        assert manager.is_loaded() is False
        assert manager.dimensions is None

    def test_unload_triggers_gc(self, mock_sentence_transformers) -> None:
        """Test unload triggers garbage collection."""
        mock_module, mock_model = mock_sentence_transformers
        manager = ModelManager()

        manager.get_model()

        with patch("rekall.model_manager.gc.collect") as mock_gc:
            manager.unload()
            mock_gc.assert_called_once()


class TestModelManagerTouch:
    """Test touch behavior."""

    def test_touch_updates_last_used(self) -> None:
        """Test touch updates last_used without loading model."""
        manager = ModelManager()

        assert manager._last_used == 0

        manager.touch()

        assert manager._last_used > 0
        assert manager.is_loaded() is False  # Model not loaded


class TestModelManagerStats:
    """Test statistics reporting."""

    def test_stats_before_load(self) -> None:
        """Test stats before model is loaded."""
        manager = ModelManager(model_name="test-model", timeout_minutes=5)

        stats = manager.stats

        assert stats["model_name"] == "test-model"
        assert stats["is_loaded"] is False
        assert stats["is_loading"] is False
        assert stats["timeout_minutes"] == 5
        assert stats["dimensions"] is None

    def test_stats_after_load(self, mock_sentence_transformers) -> None:
        """Test stats after model is loaded."""
        mock_module, mock_model = mock_sentence_transformers
        manager = ModelManager()

        manager.get_model()

        stats = manager.stats

        assert stats["is_loaded"] is True
        assert stats["dimensions"] == 384

    def test_idle_seconds(self) -> None:
        """Test idle_seconds property."""
        manager = ModelManager()

        # Before any use
        assert manager.idle_seconds == 0

        manager.touch()
        sleep(0.1)

        assert manager.idle_seconds > 0


class TestModelManagerSingleton:
    """Test singleton pattern."""

    def setup_method(self) -> None:
        """Reset singleton before each test."""
        reset_model_manager()

    def teardown_method(self) -> None:
        """Reset singleton after each test."""
        reset_model_manager()

    def test_get_model_manager_singleton(self) -> None:
        """Test that get_model_manager returns same instance."""
        with patch("rekall.config.get_config") as mock_config:
            mock_config.return_value.smart_embeddings_model = "test-model"
            mock_config.return_value.perf_model_idle_timeout_minutes = 5

            manager1 = get_model_manager()
            manager2 = get_model_manager()

            assert manager1 is manager2

    def test_reset_model_manager(self) -> None:
        """Test that reset creates new instance."""
        with patch("rekall.config.get_config") as mock_config:
            mock_config.return_value.smart_embeddings_model = "test-model"
            mock_config.return_value.perf_model_idle_timeout_minutes = 5

            manager1 = get_model_manager()
            reset_model_manager()
            manager2 = get_model_manager()

            assert manager1 is not manager2

    def test_reset_unloads_model(self, mock_sentence_transformers) -> None:
        """Test that reset unloads any loaded model."""
        mock_module, mock_model = mock_sentence_transformers

        with patch("rekall.config.get_config") as mock_config:
            mock_config.return_value.smart_embeddings_model = "test-model"
            mock_config.return_value.perf_model_idle_timeout_minutes = 5

            manager = get_model_manager()
            manager.get_model()
            assert manager.is_loaded() is True

            reset_model_manager()

            # Old manager should have been unloaded
            assert manager.is_loaded() is False
