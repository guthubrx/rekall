"""
Backend Interfaces Contract
Feature: 022-open-core

This file defines the API contracts for backend interfaces.
It serves as documentation and can be used for type checking.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict, TypeVar

T = TypeVar('T')


class DatabaseBackend(ABC):
    """
    Abstract interface for database backends.

    All database backends MUST implement this interface.

    Lifecycle:
    1. Instantiate
    2. connect() - establish connection
    3. execute/fetch operations
    4. close() - cleanup

    Error handling:
    - Operations MUST retry 3 times with exponential backoff
    - After 3 failures, raise the original exception
    """

    @abstractmethod
    def connect(self) -> None:
        """
        Establish database connection.

        Raises:
            ConnectionError: If connection cannot be established
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
            query: SQL query string with ? placeholders
            params: Optional tuple of parameters

        Returns:
            Cursor or result object (implementation-specific)

        Raises:
            DatabaseError: On query failure after retries
        """
        pass

    @abstractmethod
    def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[Dict[str, Any]]:
        """
        Execute query and return single row as dict.

        Args:
            query: SQL SELECT query
            params: Optional tuple of parameters

        Returns:
            Dict with column names as keys, or None if no row
        """
        pass

    @abstractmethod
    def fetch_all(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        Execute query and return all rows as list of dicts.

        Args:
            query: SQL SELECT query
            params: Optional tuple of parameters

        Returns:
            List of dicts, empty list if no rows
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connection is active.

        Returns:
            True if connected and healthy, False otherwise
        """
        pass


class CacheBackend(ABC):
    """
    Abstract interface for cache backends.

    All cache backends MUST implement this interface.

    Thread safety:
    - All operations MUST be thread-safe
    - Implementations may use internal locking
    """

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve value from cache.

        Args:
            key: Cache key (string)

        Returns:
            Cached value or None if not found/expired
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Store value in cache.

        Args:
            key: Cache key (string)
            value: Value to cache (must be serializable)
            ttl: Time-to-live in seconds (None = no expiration)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Remove entry from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key existed and was deleted, False otherwise
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
            key: Cache key to check

        Returns:
            True if key exists and is not expired
        """
        pass


class ServiceContainer:
    """
    Singleton service container for backend registration.

    Usage:
        container = ServiceContainer.get_instance()
        container.register('database', MyDatabaseBackend())
        db = container.get('database')

    Thread safety:
    - All operations are thread-safe
    - Uses internal lock for register/get
    """

    @classmethod
    def get_instance(cls) -> 'ServiceContainer':
        """
        Get singleton instance.

        Returns:
            The global ServiceContainer instance
        """
        ...

    def register(self, name: str, backend: Any) -> None:
        """
        Register a backend with a name.

        Args:
            name: Unique identifier for the backend
            backend: Backend instance (should implement appropriate ABC)

        Raises:
            ValueError: If name already registered (use reset() first)
        """
        ...

    def get(self, name: str) -> Any:
        """
        Retrieve registered backend.

        Args:
            name: Backend identifier

        Returns:
            The registered backend instance

        Raises:
            KeyError: If name not registered
        """
        ...

    def has(self, name: str) -> bool:
        """
        Check if backend is registered.

        Args:
            name: Backend identifier

        Returns:
            True if registered
        """
        ...

    def reset(self) -> None:
        """
        Clear all registrations.

        Primarily for testing. Use with caution.
        """
        ...


# Convenience functions (public API)

def get_database() -> DatabaseBackend:
    """
    Get the registered database backend.

    Returns:
        DatabaseBackend instance

    Raises:
        RuntimeError: If no database backend registered
    """
    ...


def get_cache() -> CacheBackend:
    """
    Get the registered cache backend.

    Returns:
        CacheBackend instance

    Raises:
        RuntimeError: If no cache backend registered
    """
    ...


def register_backend(name: str, backend: Any) -> None:
    """
    Register a custom backend.

    Args:
        name: Backend identifier ('database' or 'cache' for defaults)
        backend: Backend instance implementing appropriate ABC
    """
    ...
