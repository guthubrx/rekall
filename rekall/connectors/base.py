"""Base connector for URL extraction from AI CLI tools.

This module provides the abstract base class for all connectors that extract
URLs from AI CLI tool histories (Claude Code, Cursor IDE, etc.).
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional
from urllib.parse import urlparse


@dataclass
class ExtractedURL:
    """A URL extracted from CLI history with context."""

    url: str
    domain: str
    project: Optional[str] = None
    conversation_id: Optional[str] = None
    user_query: Optional[str] = None
    assistant_snippet: Optional[str] = None
    surrounding_text: Optional[str] = None
    captured_at: datetime = field(default_factory=datetime.now)
    raw_json: Optional[str] = None
    source_file: Optional[str] = None


@dataclass
class ExtractionResult:
    """Result of URL extraction from a source."""

    urls: list[ExtractedURL] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    files_processed: int = 0
    last_file_marker: Optional[str] = None


class BaseConnector(ABC):
    """Abstract base class for AI CLI history connectors.

    Each connector implements extraction logic for a specific AI CLI tool.
    Connectors should support:
    - Detection of tool availability
    - Incremental import (CDC) via file markers
    - URL validation and filtering
    """

    # URL patterns to quarantine (invalid for sources)
    QUARANTINE_PATTERNS = [
        r"^file://",  # Local file URLs
        r"^localhost",  # Localhost
        r"^127\.0\.0\.1",  # IPv4 loopback
        r"^\[::1\]",  # IPv6 loopback
        r"^0\.0\.0\.0",  # All interfaces
        r"^192\.168\.",  # Private IPv4
        r"^10\.",  # Private IPv4
        r"^172\.(1[6-9]|2[0-9]|3[01])\.",  # Private IPv4
    ]

    # Compiled patterns for performance
    _quarantine_regex: Optional[re.Pattern] = None

    @property
    def name(self) -> str:
        """Human-readable name for this connector."""
        return self.__class__.__name__.replace("Connector", "")

    @property
    @abstractmethod
    def cli_source(self) -> str:
        """Identifier for this CLI source (e.g., 'claude', 'cursor')."""
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this CLI tool is installed and history is accessible.

        Returns:
            True if the CLI tool history can be accessed
        """
        ...

    @abstractmethod
    def get_history_paths(self) -> list[Path]:
        """Get paths to history files for this CLI tool.

        Returns:
            List of paths to history files (JSONL, SQLite, etc.)
        """
        ...

    @abstractmethod
    def extract_urls(
        self,
        since_marker: Optional[str] = None,
        project_filter: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract URLs from CLI history.

        Args:
            since_marker: Optional file marker for incremental import (CDC)
            project_filter: Optional project name to filter by

        Returns:
            ExtractionResult with extracted URLs and metadata
        """
        ...

    def validate_url(self, url: str) -> tuple[bool, Optional[str]]:
        """Validate a URL for inclusion in the inbox.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if URL should be included, False if quarantined
            - error_message: Reason for quarantine if is_valid is False
        """
        # Empty or whitespace URL
        if not url or not url.strip():
            return False, "Empty URL"

        url = url.strip()

        # Must have a scheme
        parsed = urlparse(url)
        if not parsed.scheme:
            return False, "Missing URL scheme"

        # Only allow http/https schemes
        if parsed.scheme.lower() not in ("http", "https"):
            return False, f"Invalid scheme: {parsed.scheme}"

        # Must have a netloc (host)
        if not parsed.netloc:
            return False, "Missing host"

        # Check quarantine patterns
        if self._quarantine_regex is None:
            pattern = "|".join(f"({p})" for p in self.QUARANTINE_PATTERNS)
            self._quarantine_regex = re.compile(pattern, re.IGNORECASE)

        # Check host against quarantine patterns
        host = parsed.netloc.lower()
        if self._quarantine_regex.search(host):
            return False, f"Quarantined host: {host}"

        # Check for file:// that might have bypassed scheme check
        if url.lower().startswith("file:"):
            return False, "file:// URLs not allowed"

        return True, None

    def extract_domain(self, url: str) -> str:
        """Extract domain from a URL.

        Args:
            url: URL to extract domain from

        Returns:
            Domain string (e.g., 'docs.python.org')
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""

    def iter_urls(
        self,
        since_marker: Optional[str] = None,
        project_filter: Optional[str] = None,
    ) -> Iterator[ExtractedURL]:
        """Iterator interface for URL extraction.

        Convenience method that yields URLs one at a time.

        Args:
            since_marker: Optional file marker for incremental import
            project_filter: Optional project name to filter by

        Yields:
            ExtractedURL objects
        """
        result = self.extract_urls(since_marker, project_filter)
        yield from result.urls
