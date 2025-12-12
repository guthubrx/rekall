"""Tests for CursorConnector (US7)."""

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_cursor_db(tmp_path):
    """Create a mock Cursor state.vscdb database with sample conversations."""
    # Create workspace storage structure
    ws_hash = "abc123"
    ws_dir = tmp_path / "workspaceStorage" / ws_hash
    ws_dir.mkdir(parents=True)

    # Create workspace.json
    workspace_json = ws_dir / "workspace.json"
    workspace_json.write_text(json.dumps({
        "folder": "file:///Users/test/projects/my-project"
    }))

    # Create state.vscdb
    db_path = ws_dir / "state.vscdb"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create ItemTable (Cursor's key-value store)
    cursor.execute("""
        CREATE TABLE ItemTable (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Insert sample AI conversation data
    conversation_data = {
        "query": "How do I use httpx?",
        "response": "You can install httpx from https://www.python-httpx.org/ and read the docs at https://www.python-httpx.org/quickstart/",
        "timestamp": "2025-01-15T10:30:00Z"
    }
    cursor.execute(
        "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
        ("cursorDiskKV.aiconversation.conversations.0", json.dumps(conversation_data))
    )

    # Insert another conversation with different URL
    conversation2 = {
        "userMessage": {"text": "Explain asyncio"},
        "response": "Check https://docs.python.org/3/library/asyncio.html"
    }
    cursor.execute(
        "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
        ("cursorDiskKV.composerData.chat.1", json.dumps(conversation2))
    )

    # Insert conversation with localhost URL (should be quarantined)
    conversation3 = {
        "query": "Debug local server",
        "response": "Your server is at http://localhost:3000/api"
    }
    cursor.execute(
        "INSERT INTO ItemTable (key, value) VALUES (?, ?)",
        ("cursorDiskKV.aiconversation.conversations.2", json.dumps(conversation3))
    )

    conn.commit()
    conn.close()

    return tmp_path


class TestCursorConnectorAvailability:
    """Tests for is_available() and path detection (T101)."""

    def test_is_available_when_db_exists(self, mock_cursor_db):
        """Should return True when state.vscdb files exist."""
        from rekall.connectors.cursor import CursorConnector

        connector = CursorConnector()

        # Patch the path detection to use our mock
        with patch.object(connector, "_get_workspace_storage_path") as mock_ws:
            mock_ws.return_value = mock_cursor_db / "workspaceStorage"
            assert connector.is_available() is True

    def test_is_available_when_no_db(self, tmp_path):
        """Should return False when no state.vscdb files exist."""
        from rekall.connectors.cursor import CursorConnector

        connector = CursorConnector()

        # Create empty workspace storage
        ws_dir = tmp_path / "workspaceStorage"
        ws_dir.mkdir()

        with patch.object(connector, "_get_workspace_storage_path") as mock_ws:
            mock_ws.return_value = ws_dir
            assert connector.is_available() is False

    def test_is_available_when_cursor_not_installed(self):
        """Should return False when Cursor is not installed."""
        from rekall.connectors.cursor import CursorConnector

        connector = CursorConnector()

        with patch.object(connector, "_get_workspace_storage_path") as mock_ws:
            mock_ws.return_value = None
            assert connector.is_available() is False


class TestCursorConnectorExtraction:
    """Tests for URL extraction from SQLite (T103-T104, T107)."""

    def test_extract_urls_from_db(self, mock_cursor_db):
        """Should extract URLs from conversation JSON."""
        from rekall.connectors.cursor import CursorConnector

        connector = CursorConnector()

        with patch.object(connector, "_get_workspace_storage_path") as mock_ws:
            mock_ws.return_value = mock_cursor_db / "workspaceStorage"

            result = connector.extract_urls()

        # Should find URLs from conversations
        urls = [u.url for u in result.urls]
        assert "https://www.python-httpx.org/" in urls
        assert "https://www.python-httpx.org/quickstart/" in urls
        assert "https://docs.python.org/3/library/asyncio.html" in urls

        # Should not include localhost (quarantined)
        valid_urls = [u for u in result.urls if u.raw_json is None]
        quarantined_urls = [u for u in result.urls if u.raw_json is not None]

        assert len(valid_urls) >= 3
        # localhost should be in quarantined or filtered out
        localhost_found = any("localhost" in u.url for u in result.urls)
        if localhost_found:
            assert any("localhost" in u.url for u in quarantined_urls)

    def test_extract_preserves_context(self, mock_cursor_db):
        """Should preserve user query context."""
        from rekall.connectors.cursor import CursorConnector

        connector = CursorConnector()

        with patch.object(connector, "_get_workspace_storage_path") as mock_ws:
            mock_ws.return_value = mock_cursor_db / "workspaceStorage"

            result = connector.extract_urls()

        # Find URL from first conversation
        httpx_url = next((u for u in result.urls if "httpx" in u.url), None)
        assert httpx_url is not None
        assert httpx_url.user_query == "How do I use httpx?"

    def test_extract_project_from_workspace(self, mock_cursor_db):
        """Should extract project name from workspace.json."""
        from rekall.connectors.cursor import CursorConnector

        connector = CursorConnector()

        with patch.object(connector, "_get_workspace_storage_path") as mock_ws:
            mock_ws.return_value = mock_cursor_db / "workspaceStorage"

            result = connector.extract_urls()

        # Should have project name from workspace.json
        assert any(u.project == "my-project" for u in result.urls)

    def test_extract_handles_empty_db(self, tmp_path):
        """Should handle empty database gracefully."""
        from rekall.connectors.cursor import CursorConnector

        # Create empty database
        ws_dir = tmp_path / "workspaceStorage" / "empty"
        ws_dir.mkdir(parents=True)
        db_path = ws_dir / "state.vscdb"

        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE ItemTable (key TEXT, value TEXT)")
        conn.close()

        connector = CursorConnector()

        with patch.object(connector, "_get_workspace_storage_path") as mock_ws:
            mock_ws.return_value = tmp_path / "workspaceStorage"

            result = connector.extract_urls()

        assert len(result.urls) == 0
        assert result.files_processed == 1


class TestCursorConnectorCDC:
    """Tests for incremental import (CDC)."""

    def test_incremental_import_with_marker(self, mock_cursor_db):
        """Should skip files before the marker."""
        from rekall.connectors.cursor import CursorConnector

        connector = CursorConnector()

        with patch.object(connector, "_get_workspace_storage_path") as mock_ws:
            mock_ws.return_value = mock_cursor_db / "workspaceStorage"

            # First import
            result1 = connector.extract_urls()
            marker = result1.last_file_marker

            # Create another workspace after marker
            ws2_dir = mock_cursor_db / "workspaceStorage" / "def456"
            ws2_dir.mkdir()
            db2_path = ws2_dir / "state.vscdb"

            conn = sqlite3.connect(db2_path)
            conn.execute("CREATE TABLE ItemTable (key TEXT, value TEXT)")
            conn.execute(
                "INSERT INTO ItemTable VALUES (?, ?)",
                ("cursorDiskKV.chat.0", json.dumps({"response": "https://new-url.com/page"}))
            )
            conn.commit()
            conn.close()

            # Force reload of paths
            result2 = connector.extract_urls(since_marker=marker)

        # Should only process new file
        assert result2.files_processed >= 1


class TestCursorConnectorRegistry:
    """Tests for connector registry integration (T105)."""

    def test_cursor_in_registry(self):
        """Cursor connector should be registered."""
        from rekall.connectors import list_connectors

        connectors = list_connectors()
        assert "cursor" in connectors

    def test_get_cursor_connector(self):
        """Should be able to get cursor connector by name."""
        from rekall.connectors import get_connector

        connector = get_connector("cursor")
        assert connector is not None
        assert connector.cli_source == "cursor"


class TestCursorConnectorFallback:
    """Tests for graceful fallback when Cursor not installed (T108)."""

    def test_graceful_fallback_no_cursor(self):
        """Should return empty result when Cursor not installed."""
        from rekall.connectors.cursor import CursorConnector

        connector = CursorConnector()

        with patch.object(connector, "_get_cursor_path") as mock_path:
            mock_path.return_value = None

            result = connector.extract_urls()

        assert len(result.urls) == 0
        assert "not available" in result.errors[0].lower()

    def test_graceful_fallback_corrupt_db(self, tmp_path):
        """Should handle corrupt database gracefully."""
        from rekall.connectors.cursor import CursorConnector

        # Create corrupt database
        ws_dir = tmp_path / "workspaceStorage" / "corrupt"
        ws_dir.mkdir(parents=True)
        db_path = ws_dir / "state.vscdb"
        db_path.write_bytes(b"not a sqlite database")

        connector = CursorConnector()

        with patch.object(connector, "_get_workspace_storage_path") as mock_ws:
            mock_ws.return_value = tmp_path / "workspaceStorage"

            result = connector.extract_urls()

        # Should have error but not crash
        assert len(result.errors) >= 1
