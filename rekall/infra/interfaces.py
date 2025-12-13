# rekall/infra/interfaces.py
"""
Abstract Base Classes for backend interfaces.

These interfaces enable pluggable backends where:
- Default implementations use SQLite and in-memory cache
- Custom backends can provide optimized implementations (Redis, pooled DB)

Usage:
    from rekall.infra.interfaces import DatabaseBackend, CacheBackend

    class MyCustomDatabase(DatabaseBackend):
        def connect(self) -> None: ...
        # implement all abstract methods
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class DatabaseBackend(ABC):
    """
    Abstract interface for database backends.

    All database backends MUST implement this interface to be compatible
    with the rekall ecosystem.

    Lifecycle:
        1. Instantiate the backend
        2. Call connect() to establish connection
        3. Use execute/fetch methods for operations
        4. Call close() for cleanup

    Error handling:
        Operations SHOULD retry 3 times with exponential backoff
        before raising the original exception.
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Establish database connection.

        Raises:
            ConnectionError: If connection cannot be established after retries.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close database connection gracefully.

        Should be idempotent (safe to call multiple times).
        """
        pass

    @abstractmethod
    def execute(self, query: str, params: Optional[tuple] = None) -> Any:
        """
        Execute a SQL query (INSERT, UPDATE, DELETE).

        Args:
            query: SQL query string with ? placeholders.
            params: Optional tuple of parameters.

        Returns:
            Cursor or result object (implementation-specific).

        Raises:
            DatabaseError: On query failure after retries.
        """
        pass

    @abstractmethod
    def fetch_one(
        self, query: str, params: Optional[tuple] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Execute query and return single row as dict.

        Args:
            query: SQL SELECT query.
            params: Optional tuple of parameters.

        Returns:
            Dict with column names as keys, or None if no row found.
        """
        pass

    @abstractmethod
    def fetch_all(
        self, query: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute query and return all rows as list of dicts.

        Args:
            query: SQL SELECT query.
            params: Optional tuple of parameters.

        Returns:
            List of dicts, empty list if no rows.
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connection is active.

        Returns:
            True if connected and healthy, False otherwise.
        """
        pass


class CacheBackend(ABC):
    """
    Abstract interface for cache backends.

    All cache backends MUST implement this interface to be compatible
    with the rekall ecosystem.

    Thread safety:
        All operations MUST be thread-safe.
        Implementations may use internal locking.

    Serialization:
        Values should be serializable (JSON-compatible recommended).
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key (string).

        Returns:
            Cached value or None if not found/expired.
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key (string).
            value: Value to cache (must be serializable).
            ttl: Time-to-live in seconds (None = no expiration).
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Remove entry from cache.

        Args:
            key: Cache key to delete.

        Returns:
            True if key existed and was deleted, False otherwise.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Remove all entries from cache.

        Use with caution in production.
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check.

        Returns:
            True if key exists and is not expired.
        """
        pass


# Type aliases for convenience
BackendType = DatabaseBackend | CacheBackend
