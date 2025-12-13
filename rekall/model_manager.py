"""Model lifecycle manager for sentence-transformers.

Feature 020: Lazy load/unload to reduce memory footprint.
"""

from __future__ import annotations

import gc
import logging
from time import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages the lifecycle of sentence-transformers model.

    Features:
    - Lazy loading: Model only loaded on first use
    - Idle unload: Model unloaded after timeout period of inactivity
    - Loading state tracking: Prevents concurrent loads, enables "loading" messages

    Attributes:
        model_name: Name of the sentence-transformers model
        timeout_minutes: Minutes of inactivity before model is unloaded
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        timeout_minutes: int = 10,
    ) -> None:
        """Initialize the model manager.

        Args:
            model_name: sentence-transformers model name (default: all-MiniLM-L6-v2)
            timeout_minutes: Minutes of inactivity before unload (default: 10)
        """
        self.model_name = model_name
        self.timeout_minutes = timeout_minutes

        self._model: Any = None  # SentenceTransformer instance
        self._last_used: float = 0.0
        self._loading: bool = False
        self._model_dimensions: int | None = None

    def get_model(self) -> Any:
        """Get the model, loading it if necessary.

        Updates last_used timestamp on each call.

        Returns:
            SentenceTransformer model instance

        Raises:
            ImportError: If sentence-transformers is not installed
            RuntimeError: If model fails to load
        """
        self._last_used = time()

        if self._model is not None:
            return self._model

        # Load model
        self._loading = True
        try:
            logger.info("Loading model: %s", self.model_name)
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
            self._model_dimensions = self._model.get_sentence_embedding_dimension()
            logger.info(
                "Model loaded: %s (dimensions: %d)",
                self.model_name,
                self._model_dimensions,
            )
            return self._model
        except ImportError:
            logger.error("sentence-transformers not installed")
            raise ImportError(
                "sentence-transformers is required for embeddings. "
                "Install with: pip install rekall[embeddings]"
            )
        except Exception as e:
            logger.error("Failed to load model %s: %s", self.model_name, e)
            raise RuntimeError(f"Failed to load model {self.model_name}: {e}") from e
        finally:
            self._loading = False

    def is_loaded(self) -> bool:
        """Check if the model is currently loaded in memory.

        Returns:
            True if model is loaded, False otherwise
        """
        return self._model is not None

    def is_loading(self) -> bool:
        """Check if the model is currently being loaded.

        Returns:
            True if model load is in progress, False otherwise
        """
        return self._loading

    def check_idle(self) -> bool:
        """Check if model should be unloaded due to inactivity.

        Call this periodically (e.g., after each embedding operation).
        If idle timeout has passed, unloads the model and triggers GC.

        Returns:
            True if model was unloaded, False otherwise
        """
        if self._model is None:
            return False

        timeout_seconds = self.timeout_minutes * 60
        idle_seconds = time() - self._last_used

        if idle_seconds > timeout_seconds:
            logger.info(
                "Model idle for %.1f minutes, unloading",
                idle_seconds / 60,
            )
            self.unload()
            return True

        return False

    def unload(self) -> None:
        """Force unload the model and free memory.

        Triggers garbage collection to ensure memory is released.
        """
        if self._model is None:
            return

        logger.info("Unloading model: %s", self.model_name)
        self._model = None
        self._model_dimensions = None

        # Force garbage collection to release memory
        gc.collect()
        logger.debug("Model unloaded, GC triggered")

    def touch(self) -> None:
        """Update last_used timestamp without loading model.

        Useful to prevent unload when model is about to be used.
        """
        self._last_used = time()

    @property
    def dimensions(self) -> int | None:
        """Get the model's embedding dimensions (None if not loaded)."""
        return self._model_dimensions

    @property
    def idle_seconds(self) -> float:
        """Get seconds since last model use."""
        if self._last_used == 0:
            return 0.0
        return time() - self._last_used

    @property
    def stats(self) -> dict[str, Any]:
        """Get model manager statistics.

        Returns:
            Dict with model_name, is_loaded, is_loading, idle_seconds, dimensions
        """
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded(),
            "is_loading": self.is_loading(),
            "idle_seconds": round(self.idle_seconds, 1),
            "timeout_minutes": self.timeout_minutes,
            "dimensions": self._model_dimensions,
        }


# Global model manager instance (singleton pattern)
_model_manager: ModelManager | None = None


def get_model_manager(
    model_name: str | None = None,
    timeout_minutes: int | None = None,
) -> ModelManager:
    """Get or create the global model manager.

    Args:
        model_name: Override model name (only on first call)
        timeout_minutes: Override timeout (only on first call)

    Returns:
        Global ModelManager instance
    """
    global _model_manager

    if _model_manager is None:
        from rekall.config import get_config

        config = get_config()
        _model_manager = ModelManager(
            model_name=model_name or config.smart_embeddings_model,
            timeout_minutes=timeout_minutes or config.perf_model_idle_timeout_minutes,
        )

    return _model_manager


def reset_model_manager() -> None:
    """Reset the global model manager (for testing).

    Also unloads any loaded model.
    """
    global _model_manager

    if _model_manager is not None:
        _model_manager.unload()

    _model_manager = None
