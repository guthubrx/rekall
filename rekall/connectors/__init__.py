"""Connectors package for AI CLI history extraction.

This package provides a plugin-based architecture for extracting URLs
from various AI CLI tool histories (Claude Code, Cursor IDE, etc.).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from rekall.connectors.base import BaseConnector

# Registry of available connectors (lazy loaded)
_connectors: dict[str, type["BaseConnector"]] = {}
_loaded = False


def _load_connectors() -> None:
    """Lazy load all connector implementations."""
    global _loaded
    if _loaded:
        return

    # Import connector implementations
    from rekall.connectors.claude_cli import ClaudeCLIConnector
    from rekall.connectors.cursor import CursorConnector

    # Register connectors
    _connectors["claude"] = ClaudeCLIConnector
    _connectors["cursor"] = CursorConnector

    _loaded = True


def get_connector(name: str) -> Optional["BaseConnector"]:
    """Get a connector instance by name.

    Args:
        name: Connector identifier (e.g., 'claude', 'cursor')

    Returns:
        Connector instance or None if not found
    """
    _load_connectors()

    connector_cls = _connectors.get(name.lower())
    if connector_cls:
        return connector_cls()
    return None


def list_connectors() -> list[str]:
    """List all available connector names.

    Returns:
        List of connector identifiers
    """
    _load_connectors()
    return list(_connectors.keys())


def get_available_connectors() -> list["BaseConnector"]:
    """Get instances of all connectors that are available on this system.

    Returns:
        List of connector instances that have accessible history
    """
    _load_connectors()

    available = []
    for connector_cls in _connectors.values():
        try:
            instance = connector_cls()
            if instance.is_available():
                available.append(instance)
        except Exception:
            continue

    return available


__all__ = [
    "get_connector",
    "list_connectors",
    "get_available_connectors",
]
