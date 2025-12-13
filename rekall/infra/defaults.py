# rekall/infra/defaults.py
"""
Default backend implementations for Home users.

These implementations provide zero-configuration defaults using:
- SQLite for database (existing rekall behavior)
- In-memory dict for generic caching

For optimized backends (Redis, connection pooling), implement custom backends.
"""

from __future__ import annotations

import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from rekall.infra.interfaces import CacheBackend, DatabaseBackend

logger = logging.getLogger(__name__)


def _retry_with_backoff(
    func: Any,
    max_retries: int = 3,
    base_delay: float = 0.1,
) -> Any:
    """
    Execute a function with exponential backoff retry.

    Args:
        func: Callable to execute
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 0.1)

    Returns:
        Result of the function call

    Raises:
        The last exception if all retries fail
    """
    last_exception: Optional[Exception] = None

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_exception = e
            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt)
                logger.debug(
                    "Retry %d/%d after %.2fs: %s",
                    attempt + 1,
                    max_retries,
                    delay,
                    str(e),
                )
                time.sleep(delay)

    if last_exception:
        raise last_exception
    raise RuntimeError("Retry failed with no exception")


class DefaultDatabaseBackend(DatabaseBackend):
    """
    Default SQLite database backend for Home users.

    This backend provides a simple SQLite connection with:
    - WAL mode for concurrent access
    - Automatic retry with exponential backoff
    - Row factory for dict results

    Note:
        This is a low-level interface. Most code should use
        rekall.db.Database for full functionality.
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """
        Initialize the database backend.

        Args:
            db_path: Path to SQLite database file. If None, uses default location.
        """
        self._path = db_path
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()

    def connect(self) -> None:
        """Establish database connection with WAL mode."""
        if self._connection is not None:
            return

        def _connect() -> None:
            if self._path is None:
                from rekall.config import get_config

                config = get_config()
                self._path = config.db_path

            self._connection = sqlite3.connect(
                str(self._path),
                check_same_thread=False,
                timeout=30.0,
            )
            self._connection.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent access
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
            logger.debug("Database connected: %s", self._path)

        _retry_with_backoff(_connect)

    def close(self) -> None:
        """Close database connection gracefully."""
        with self._lock:
            if self._connection is not None:
                try:
                    self._connection.close()
                except Exception as e:
                    logger.warning("Error closing database: %s", e)
                finally:
                    self._connection = None
                    logger.debug("Database connection closed")

    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a SQL query with retry."""
        self._ensure_connected()

        def _execute() -> Any:
            with self._lock:
                cursor = self._connection.execute(query, params or ())  # type: ignore
                self._connection.commit()  # type: ignore
                return cursor

        return _retry_with_backoff(_execute)

    def fetch_one(
        self, query: str, params: Optional[tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """Execute query and return single row as dict."""
        self._ensure_connected()

        def _fetch() -> Optional[Dict[str, Any]]:
            with self._lock:
                cursor = self._connection.execute(query, params or ())  # type: ignore
                row = cursor.fetchone()
                return dict(row) if row else None

        return _retry_with_backoff(_fetch)

    def fetch_all(
        self, query: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """Execute query and return all rows as list of dicts."""
        self._ensure_connected()

        def _fetch() -> List[Dict[str, Any]]:
            with self._lock:
                cursor = self._connection.execute(query, params or ())  # type: ignore
                return [dict(row) for row in cursor.fetchall()]

        return _retry_with_backoff(_fetch)

    def is_connected(self) -> bool:
        """Check if connection is active."""
        if self._connection is None:
            return False
        try:
            self._connection.execute("SELECT 1")
            return True
        except Exception:
            return False

    def _ensure_connected(self) -> None:
        """Ensure connection is established."""
        if not self.is_connected():
            self.connect()


class DefaultCacheBackend(CacheBackend):
    """
    Default in-memory cache backend for Home users.

    This backend provides a simple thread-safe dict cache with:
    - TTL-based expiration (lazy eviction)
    - LRU eviction when max size reached
    - Thread-safe operations

    Note:
        For embedding caching, use rekall.cache.EmbeddingCache which
        is optimized for numpy vectors and batch operations.
    """

    def __init__(self, max_size: int = 1000, default_ttl: int = 600) -> None:
        """
        Initialize the cache backend.

        Args:
            max_size: Maximum number of entries (default: 1000)
            default_ttl: Default TTL in seconds (default: 600 = 10 min)
        """
        self._cache: Dict[str, tuple[Any, float, Optional[float]]] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value from cache."""
        with self._lock:
            if key not in self._cache:
                return None

            value, timestamp, ttl = self._cache[key]

            # Check expiration
            if ttl is not None and time.time() - timestamp > ttl:
                del self._cache[key]
                return None

            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Store value in cache."""
        with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self._max_size and key not in self._cache:
                # Remove oldest entry (first key)
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]

            effective_ttl = ttl if ttl is not None else self._default_ttl
            self._cache[key] = (value, time.time(), effective_ttl)

    def delete(self, key: str) -> bool:
        """Remove entry from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self) -> None:
        """Remove all entries from cache."""
        with self._lock:
            self._cache.clear()

    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        with self._lock:
            if key not in self._cache:
                return False

            _, timestamp, ttl = self._cache[key]

            # Check expiration
            if ttl is not None and time.time() - timestamp > ttl:
                del self._cache[key]
                return False

            return True


# =============================================================================
# Auto-registration of default backends
# =============================================================================


def register_defaults() -> None:
    """
    Register default backends in the ServiceContainer.

    This is called automatically when rekall is imported.
    Custom backends can override these by calling register_backend() after.
    """
    from rekall.infra.container import has_backend, register_backend

    if not has_backend("database"):
        register_backend("database", DefaultDatabaseBackend())
        logger.debug("Registered default database backend")

    if not has_backend("cache"):
        register_backend("cache", DefaultCacheBackend())
        logger.debug("Registered default cache backend")
