"""Centralized serialization functions for Rekall entries.

This module provides DRY serialization/deserialization functions used by
exporters.py, archive.py, and other modules that need to convert entries
to/from dictionary format.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from rekall.models import Entry


def entry_to_dict(entry: Entry) -> dict[str, Any]:
    """Convert an Entry to a dictionary for serialization.

    Args:
        entry: Entry object to convert

    Returns:
        Dictionary representation of the entry

    Example:
        >>> entry = Entry(id="123", title="Bug fix", ...)
        >>> data = entry_to_dict(entry)
        >>> data["title"]
        'Bug fix'
    """
    return {
        "id": entry.id,
        "title": entry.title,
        "type": entry.type,
        "content": entry.content,
        "project": entry.project,
        "tags": entry.tags,
        "confidence": entry.confidence,
        "status": entry.status,
        "superseded_by": entry.superseded_by,
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
        # Cognitive memory fields (if present)
        "memory_type": getattr(entry, "memory_type", "episodic"),
        "last_accessed": (
            entry.last_accessed.isoformat() if entry.last_accessed else None
        ),
        "access_count": getattr(entry, "access_count", 0),
        "consolidation_score": getattr(entry, "consolidation_score", 0.0),
        "next_review": (
            entry.next_review.isoformat() if entry.next_review else None
        ),
    }


def dict_to_entry(data: dict[str, Any]) -> Entry:
    """Convert a dictionary to an Entry object.

    Args:
        data: Dictionary with entry data

    Returns:
        Entry object

    Raises:
        KeyError: If required fields are missing
        ValueError: If date parsing fails

    Example:
        >>> data = {"id": "123", "title": "Bug fix", ...}
        >>> entry = dict_to_entry(data)
        >>> entry.title
        'Bug fix'
    """
    # Parse datetime fields
    created_at = data.get("created_at")
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    elif created_at is None:
        created_at = datetime.now()

    updated_at = data.get("updated_at")
    if isinstance(updated_at, str):
        updated_at = datetime.fromisoformat(updated_at)
    elif updated_at is None:
        updated_at = created_at

    last_accessed = data.get("last_accessed")
    if isinstance(last_accessed, str):
        last_accessed = datetime.fromisoformat(last_accessed)

    next_review = data.get("next_review")
    if isinstance(next_review, str):
        next_review = datetime.fromisoformat(next_review)

    return Entry(
        id=data["id"],
        title=data["title"],
        type=data.get("type", "note"),
        content=data.get("content", ""),
        project=data.get("project"),
        tags=data.get("tags", []),
        confidence=data.get("confidence", 2),
        status=data.get("status", "active"),
        superseded_by=data.get("superseded_by"),
        created_at=created_at,
        updated_at=updated_at,
        # Cognitive memory fields
        memory_type=data.get("memory_type", "episodic"),
        last_accessed=last_accessed,
        access_count=data.get("access_count", 0),
        consolidation_score=data.get("consolidation_score", 0.0),
        next_review=next_review,
    )


def entries_to_json(entries: list[Entry], indent: int = 2) -> str:
    """Serialize a list of entries to JSON string.

    Args:
        entries: List of Entry objects
        indent: JSON indentation level (default: 2)

    Returns:
        JSON string representation
    """
    data = [entry_to_dict(entry) for entry in entries]
    return json.dumps(data, indent=indent, ensure_ascii=False)


def entries_from_json(json_str: str) -> list[Entry]:
    """Deserialize entries from JSON string.

    Args:
        json_str: JSON string representation

    Returns:
        List of Entry objects

    Raises:
        json.JSONDecodeError: If JSON is invalid
    """
    data = json.loads(json_str)
    return [dict_to_entry(item) for item in data]
