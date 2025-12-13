# rekall/infra/container.py
"""
Service Container for backend registration and retrieval.

This module provides a singleton container that manages backend instances,
enabling the Open Core architecture where backends can be swapped at runtime.

Usage:
    from rekall.infra.container import get_database, get_cache, register_backend

    # Get default backends (auto-registered)
    db = get_database()
    cache = get_cache()

    # Register custom backend
    register_backend('cache', MyRedisCacheBackend())
"""

from __future__ import annotations

import threading
from typing import Any, Optional

from rekall.infra.interfaces import CacheBackend, DatabaseBackend


class ServiceContainer:
    """
    Singleton service container for backend registration.

    Thread-safe container that manages backend instances.
    Backends are registered by name and can be retrieved or replaced.

    Example:
        container = ServiceContainer.get_instance()
        container.register('database', MyDatabaseBackend())
        db = container.get('database')
    """

    _instance: Optional[ServiceContainer] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self) -> None:
        """Initialize the container. Use get_instance() instead."""
        self._backends: dict[str, Any] = {}
        self._backend_lock = threading.Lock()

    @classmethod
    def get_instance(cls) -> ServiceContainer:
        """
        Get the singleton instance.

        Returns:
            The global ServiceContainer instance.
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register(self, name: str, backend: Any) -> None:
        """
        Register a backend with a name.

        Args:
            name: Unique identifier for the backend ('database', 'cache', etc.)
            backend: Backend instance (should implement appropriate ABC).

        Note:
            Registering with an existing name will replace the old backend.
            This allows runtime swapping of backends.
        """
        with self._backend_lock:
            self._backends[name] = backend

    def get(self, name: str) -> Any:
        """
        Retrieve registered backend.

        Args:
            name: Backend identifier.

        Returns:
            The registered backend instance.

        Raises:
            KeyError: If name not registered.
        """
        with self._backend_lock:
            if name not in self._backends:
                raise KeyError(f"Backend '{name}' not registered")
            return self._backends[name]

    def has(self, name: str) -> bool:
        """
        Check if backend is registered.

        Args:
            name: Backend identifier.

        Returns:
            True if registered.
        """
        with self._backend_lock:
            return name in self._backends

    def reset(self) -> None:
        """
        Clear all registrations.

        Primarily for testing. Use with caution in production.
        """
        with self._backend_lock:
            self._backends.clear()

    @classmethod
    def reset_instance(cls) -> None:
        """
        Reset the singleton instance.

        Primarily for testing. Use with caution.
        """
        with cls._lock:
            cls._instance = None


# =============================================================================
# Convenience functions (public API)
# =============================================================================


def get_database() -> DatabaseBackend:
    """
    Get the registered database backend.

    Returns:
        DatabaseBackend instance.

    Raises:
        RuntimeError: If no database backend registered.
    """
    container = ServiceContainer.get_instance()
    try:
        return container.get("database")
    except KeyError:
        raise RuntimeError(
            "No database backend registered. "
            "Call register_backend('database', backend) first or import rekall to auto-register defaults."
        )


def get_cache() -> CacheBackend:
    """
    Get the registered cache backend.

    Returns:
        CacheBackend instance.

    Raises:
        RuntimeError: If no cache backend registered.
    """
    container = ServiceContainer.get_instance()
    try:
        return container.get("cache")
    except KeyError:
        raise RuntimeError(
            "No cache backend registered. "
            "Call register_backend('cache', backend) first or import rekall to auto-register defaults."
        )


def register_backend(name: str, backend: Any) -> None:
    """
    Register a custom backend.

    Args:
        name: Backend identifier ('database' or 'cache' for defaults).
        backend: Backend instance implementing appropriate ABC.

    Example:
        from rekall.infra.container import register_backend

        class MyRedisCache(CacheBackend):
            # ... implementation

        register_backend('cache', MyRedisCache())
    """
    container = ServiceContainer.get_instance()
    container.register(name, backend)


def has_backend(name: str) -> bool:
    """
    Check if a backend is registered.

    Args:
        name: Backend identifier.

    Returns:
        True if registered.
    """
    container = ServiceContainer.get_instance()
    return container.has(name)
