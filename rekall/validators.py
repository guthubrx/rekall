"""Pydantic validation models for Rekall.

This module provides validation for entries, config, and archives
using Pydantic v2 for type-safe data handling and clear error messages.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from rekall.constants import (
    MAX_CONTENT_LENGTH,
    MAX_ENTRIES_COUNT,
    MAX_INTEGRATIONS,
    MAX_TAG_LENGTH,
    MAX_TAGS_COUNT,
    MAX_TITLE_LENGTH,
)


class EntryValidator(BaseModel):
    """Validation model for Rekall entries.

    Used to validate user input before storing in the database.
    """

    title: str = Field(
        min_length=1,
        max_length=MAX_TITLE_LENGTH,
        description="Title of the entry",
    )
    content: str = Field(
        default="",
        max_length=MAX_CONTENT_LENGTH,
        description="Content/body of the entry",
    )
    tags: list[str] = Field(
        default_factory=list,
        max_length=MAX_TAGS_COUNT,
        description="Tags for categorization",
    )
    entry_type: str = Field(
        default="note",
        pattern=r"^(bug|pattern|decision|config|pitfall|reference|note)$",
        description="Type of entry",
    )
    confidence: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Confidence level (0-5)",
    )
    project: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Associated project name",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        """Validate and normalize tags."""
        validated = []
        for tag in tags:
            tag = tag.strip().lower()
            if not tag:
                continue
            if len(tag) > MAX_TAG_LENGTH:
                msg = f"Tag too long: {len(tag)} chars (max: {MAX_TAG_LENGTH})"
                raise ValueError(msg)
            validated.append(tag)
        return validated

    @field_validator("title")
    @classmethod
    def validate_title(cls, title: str) -> str:
        """Validate and normalize title."""
        title = title.strip()
        if not title:
            msg = "Title cannot be empty"
            raise ValueError(msg)
        return title


class ConfigValidator(BaseModel):
    """Validation model for Rekall configuration."""

    db_path: Optional[str] = Field(
        default=None,
        description="Path to the SQLite database",
    )
    active_integrations: list[str] = Field(
        default_factory=list,
        max_length=MAX_INTEGRATIONS,
        description="List of active IDE integrations",
    )
    embeddings_provider: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Embeddings provider (if enabled)",
    )
    language: str = Field(
        default="en",
        pattern=r"^[a-z]{2}(-[A-Z]{2})?$",
        description="Language code (e.g., 'en', 'fr', 'de')",
    )


class ArchiveMetadataValidator(BaseModel):
    """Validation model for archive metadata."""

    version: str = Field(
        pattern=r"^\d+\.\d+\.\d+$",
        description="Rekall version that created the archive",
    )
    created_at: datetime = Field(
        description="When the archive was created",
    )
    entry_count: int = Field(
        ge=0,
        le=MAX_ENTRIES_COUNT,
        description="Number of entries in the archive",
    )
    checksum: Optional[str] = Field(
        default=None,
        max_length=64,
        description="SHA-256 checksum of the data",
    )


class ArchiveEntryValidator(BaseModel):
    """Validation model for entries within an archive."""

    id: str = Field(
        max_length=36,
        description="Entry UUID",
    )
    title: str = Field(
        max_length=MAX_TITLE_LENGTH,
        description="Entry title",
    )
    content: str = Field(
        max_length=MAX_CONTENT_LENGTH,
        description="Entry content",
    )
    tags: list[str] = Field(
        default_factory=list,
        max_length=MAX_TAGS_COUNT,
        description="Entry tags",
    )
    entry_type: str = Field(
        default="note",
        description="Type of entry",
    )
    confidence: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Confidence level",
    )
    project: Optional[str] = Field(
        default=None,
        description="Associated project",
    )
    created_at: str = Field(
        description="Creation timestamp (ISO format)",
    )
    updated_at: Optional[str] = Field(
        default=None,
        description="Last update timestamp",
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        """Validate tag lengths."""
        for tag in tags:
            if len(tag) > MAX_TAG_LENGTH:
                msg = f"Tag too long: {len(tag)} chars (max: {MAX_TAG_LENGTH})"
                raise ValueError(msg)
        return tags


class ArchiveValidator(BaseModel):
    """Validation model for complete archives."""

    metadata: ArchiveMetadataValidator
    entries: list[ArchiveEntryValidator] = Field(
        default_factory=list,
        max_length=MAX_ENTRIES_COUNT,
    )


def validate_entry(data: dict[str, Any]) -> EntryValidator:
    """Validate entry data and return validated model.

    Args:
        data: Dictionary with entry data

    Returns:
        Validated EntryValidator instance

    Raises:
        pydantic.ValidationError: If validation fails
    """
    return EntryValidator(**data)


def validate_archive_entry(data: dict[str, Any]) -> ArchiveEntryValidator:
    """Validate archive entry data.

    Args:
        data: Dictionary with archive entry data

    Returns:
        Validated ArchiveEntryValidator instance

    Raises:
        pydantic.ValidationError: If validation fails
    """
    return ArchiveEntryValidator(**data)
