"""Cursor IDE connector for URL extraction.

This module extracts URLs from Cursor IDE conversation history,
stored in SQLite databases (state.vscdb) under workspaceStorage.
"""

from __future__ import annotations

import json
import os
import platform
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from rekall.connectors.base import BaseConnector, ExtractedURL, ExtractionResult


class CursorConnector(BaseConnector):
    """Connector for Cursor IDE history.

    Cursor stores conversation history in SQLite databases (state.vscdb) under:
    - macOS: ~/Library/Application Support/Cursor/User/workspaceStorage/
    - Linux: ~/.config/Cursor/User/workspaceStorage/
    - Windows: %APPDATA%\\Cursor\\User\\workspaceStorage\\

    Each workspace has its own state.vscdb file containing AI conversations
    in the ItemTable with keys like 'cursorDiskKV.aiconversation.*'.
    """

    # URL extraction pattern
    URL_PATTERN = re.compile(
        r'https?://[^\s<>"\'`\]\)\\]+',
        re.IGNORECASE,
    )

    @property
    def cli_source(self) -> str:
        """Identifier for Cursor IDE."""
        return "cursor"

    def _get_cursor_path(self) -> Optional[Path]:
        """Get the Cursor application data path for the current OS.

        Returns:
            Path to Cursor User directory, or None if not found
        """
        system = platform.system()

        if system == "Darwin":  # macOS
            base = Path.home() / "Library" / "Application Support" / "Cursor"
        elif system == "Linux":
            # Check XDG first, then default
            xdg_config = os.environ.get("XDG_CONFIG_HOME")
            if xdg_config:
                base = Path(xdg_config) / "Cursor"
            else:
                base = Path.home() / ".config" / "Cursor"
            # Also check Flatpak location
            if not base.exists():
                flatpak = Path.home() / ".var" / "app" / "com.cursor.Cursor" / "config" / "Cursor"
                if flatpak.exists():
                    base = flatpak
        elif system == "Windows":
            appdata = os.environ.get("APPDATA")
            if appdata:
                base = Path(appdata) / "Cursor"
            else:
                base = Path.home() / "AppData" / "Roaming" / "Cursor"
        else:
            return None

        user_dir = base / "User"
        return user_dir if user_dir.exists() else None

    def _get_workspace_storage_path(self) -> Optional[Path]:
        """Get the workspaceStorage directory.

        Returns:
            Path to workspaceStorage directory, or None if not found
        """
        user_dir = self._get_cursor_path()
        if not user_dir:
            return None

        ws_storage = user_dir / "workspaceStorage"
        return ws_storage if ws_storage.exists() else None

    def is_available(self) -> bool:
        """Check if Cursor IDE is installed and has history.

        Returns:
            True if Cursor workspaceStorage exists and has content
        """
        ws_storage = self._get_workspace_storage_path()
        if not ws_storage:
            return False

        # Check if there are any workspace directories with state.vscdb
        for ws_dir in ws_storage.iterdir():
            if ws_dir.is_dir():
                state_db = ws_dir / "state.vscdb"
                if state_db.exists():
                    return True
        return False

    def get_history_paths(self) -> list[Path]:
        """Get paths to all Cursor state.vscdb files.

        Returns:
            List of paths to state.vscdb files, sorted by modification time
        """
        ws_storage = self._get_workspace_storage_path()
        if not ws_storage:
            return []

        db_files = []
        for ws_dir in ws_storage.iterdir():
            if not ws_dir.is_dir():
                continue
            state_db = ws_dir / "state.vscdb"
            if state_db.exists():
                db_files.append(state_db)

        # Sort by modification time (oldest first for incremental processing)
        return sorted(db_files, key=lambda p: p.stat().st_mtime)

    def extract_urls(
        self,
        since_marker: Optional[str] = None,
        project_filter: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract URLs from Cursor IDE history.

        Parses SQLite databases to find AI conversations containing URLs.

        Args:
            since_marker: Optional file path marker for CDC (skip files before this)
            project_filter: Optional project name to filter by

        Returns:
            ExtractionResult with extracted URLs
        """
        result = ExtractionResult()

        if not self.is_available():
            result.errors.append("Cursor IDE not available or no history found")
            return result

        history_files = self.get_history_paths()
        if not history_files:
            return result

        # Find starting point for incremental import
        start_idx = 0
        if since_marker:
            try:
                marker_path = Path(since_marker)
                for idx, path in enumerate(history_files):
                    if path == marker_path or str(path) == since_marker:
                        start_idx = idx + 1  # Start after the marker
                        break
            except Exception:
                pass  # Invalid marker, start from beginning

        # Process files
        seen_urls: set[str] = set()  # Dedup within this extraction

        for file_path in history_files[start_idx:]:
            result.files_processed += 1
            result.last_file_marker = str(file_path)

            # Determine workspace/project from path
            project = self._extract_project_from_path(file_path)
            if project_filter and project != project_filter:
                continue

            try:
                urls = self._extract_urls_from_db(file_path, project, seen_urls)
                result.urls.extend(urls)
            except Exception as e:
                result.errors.append(f"Error processing {file_path}: {e}")

        return result

    def _extract_project_from_path(self, file_path: Path) -> Optional[str]:
        """Extract project identifier from file path.

        The path structure is: .../workspaceStorage/{hash}/state.vscdb
        We try to find workspace info from the database or path.
        """
        try:
            # Navigate to workspace directory
            ws_dir = file_path.parent

            # Try to read workspace.json for the actual folder path
            workspace_json = ws_dir / "workspace.json"
            if workspace_json.exists():
                with open(workspace_json, encoding="utf-8") as f:
                    data = json.load(f)
                    # Extract folder name from URI
                    folder = data.get("folder")
                    if folder:
                        # Parse file:// URI or path
                        if folder.startswith("file://"):
                            folder = folder[7:]  # Remove file://
                        return Path(folder).name

            # Fall back to directory hash
            return ws_dir.name
        except Exception:
            return None

    def _extract_urls_from_db(
        self,
        db_path: Path,
        project: Optional[str],
        seen_urls: set[str],
    ) -> list[ExtractedURL]:
        """Extract URLs from a single state.vscdb file.

        Args:
            db_path: Path to the SQLite database
            project: Project identifier
            seen_urls: Set of already-seen URLs for deduplication

        Returns:
            List of ExtractedURL objects
        """
        urls: list[ExtractedURL] = []

        try:
            # Connect read-only to avoid locking issues
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            cursor = conn.cursor()

            # Find AI conversation entries
            # Cursor stores conversations with keys like:
            # - cursorDiskKV.aiconversation.conversations.*
            # - cursorDiskKV.composerData.*
            cursor.execute(
                """SELECT key, value FROM ItemTable
                   WHERE key LIKE '%aiconversation%'
                      OR key LIKE '%composerData%'
                      OR key LIKE '%chat%'"""
            )

            for key, value in cursor.fetchall():
                if not value:
                    continue

                try:
                    # Parse JSON value
                    data = json.loads(value)
                    conversation_urls = self._extract_urls_from_conversation(
                        data, project, str(db_path), key, seen_urls
                    )
                    urls.extend(conversation_urls)
                except json.JSONDecodeError:
                    # Not JSON, try direct URL extraction from text
                    if isinstance(value, str):
                        text_urls = self._extract_urls_from_text(
                            value, project, str(db_path), key, seen_urls
                        )
                        urls.extend(text_urls)

            conn.close()
        except sqlite3.Error as e:
            raise RuntimeError(f"SQLite error: {e}")

        return urls

    def _extract_urls_from_conversation(
        self,
        data: dict | list,
        project: Optional[str],
        source_file: str,
        conversation_key: str,
        seen_urls: set[str],
    ) -> list[ExtractedURL]:
        """Extract URLs from a conversation data structure.

        Cursor conversation JSON can have various structures depending on version.
        """
        urls: list[ExtractedURL] = []

        # Convert to string for URL extraction
        text = json.dumps(data) if isinstance(data, (dict, list)) else str(data)

        # Extract context for better understanding
        user_query = None
        if isinstance(data, dict):
            # Try to find user query
            user_query = (
                data.get("query")
                or data.get("userMessage")
                or data.get("prompt")
            )
            if isinstance(user_query, dict):
                user_query = user_query.get("text") or user_query.get("content")

        # Find all URLs
        found_urls = self.URL_PATTERN.findall(text)

        for url in found_urls:
            # Clean URL
            url = url.rstrip(".,;:!?)]}>\"'\\")
            if len(url) < 10:  # Skip too short
                continue

            if url in seen_urls:
                continue

            is_valid, error = self.validate_url(url)
            extracted = ExtractedURL(
                url=url,
                domain=self.extract_domain(url),
                project=project,
                conversation_id=conversation_key,
                user_query=user_query[:500] if user_query else None,
                captured_at=datetime.now(),
                source_file=source_file,
            )

            if not is_valid:
                extracted.raw_json = json.dumps({"validation_error": error})

            urls.append(extracted)
            seen_urls.add(url)

        return urls

    def _extract_urls_from_text(
        self,
        text: str,
        project: Optional[str],
        source_file: str,
        key: str,
        seen_urls: set[str],
    ) -> list[ExtractedURL]:
        """Extract URLs from plain text content."""
        urls: list[ExtractedURL] = []

        found_urls = self.URL_PATTERN.findall(text)

        for url in found_urls:
            url = url.rstrip(".,;:!?)]}>\"'\\")
            if len(url) < 10:
                continue

            if url in seen_urls:
                continue

            is_valid, error = self.validate_url(url)
            extracted = ExtractedURL(
                url=url,
                domain=self.extract_domain(url),
                project=project,
                conversation_id=key,
                surrounding_text=text[:200] if text else None,
                captured_at=datetime.now(),
                source_file=source_file,
            )

            if not is_valid:
                extracted.raw_json = json.dumps({"validation_error": error})

            urls.append(extracted)
            seen_urls.add(url)

        return urls
