"""Tests for IDE detection functionality."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch


class TestDetectIDE:
    """Tests for detect_ide() function."""

    def test_detect_claude_local(self, tmp_path: Path):
        """Test detection of Claude Code in local project."""
        # Create .claude directory
        (tmp_path / ".claude").mkdir()

        from rekall.integrations import detect_ide, Scope

        result = detect_ide(tmp_path)

        assert result.ide is not None
        assert result.ide.id == "claude"
        assert result.scope == Scope.LOCAL

    def test_detect_claude_global(self, tmp_path: Path):
        """Test detection of Claude Code in global home."""
        from rekall.integrations import detect_ide, Scope

        with patch.object(Path, "home", return_value=tmp_path):
            # Create ~/.claude directory
            (tmp_path / ".claude").mkdir()

            result = detect_ide(Path("/some/project"))

            assert result.ide is not None
            assert result.ide.id == "claude"
            assert result.scope == Scope.GLOBAL

    def test_detect_cursor_local(self, tmp_path: Path):
        """Test detection of Cursor in local project."""
        (tmp_path / ".cursor").mkdir()

        from rekall.integrations import detect_ide, Scope

        result = detect_ide(tmp_path)

        assert result.ide is not None
        assert result.ide.id == "cursor"
        assert result.scope == Scope.LOCAL

    def test_detect_no_ide(self, tmp_path: Path):
        """Test when no IDE is detected."""
        from rekall.integrations import detect_ide

        with patch.object(Path, "home", return_value=tmp_path):
            result = detect_ide(tmp_path)

            assert result.ide is None

    def test_priority_claude_over_cursor(self, tmp_path: Path):
        """Test that Claude has priority over Cursor when both present."""
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".cursor").mkdir()

        from rekall.integrations import detect_ide

        result = detect_ide(tmp_path)

        assert result.ide is not None
        assert result.ide.id == "claude"

    def test_local_priority_over_global(self, tmp_path: Path):
        """Test that local detection has priority over global."""
        from rekall.integrations import detect_ide, Scope

        # Create cursor locally, claude globally
        (tmp_path / ".cursor").mkdir()

        home_dir = tmp_path / "home"
        home_dir.mkdir()
        (home_dir / ".claude").mkdir()

        with patch.object(Path, "home", return_value=home_dir):
            result = detect_ide(tmp_path)

            # Local Cursor should be detected, not global Claude
            assert result.ide is not None
            assert result.ide.id == "cursor"
            assert result.scope == Scope.LOCAL


class TestGetAllDetectedIDEs:
    """Tests for get_all_detected_ides() function."""

    def test_returns_all_detected(self, tmp_path: Path):
        """Test that all detected IDEs are returned."""
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".cursor").mkdir()

        from rekall.integrations import get_all_detected_ides

        result = get_all_detected_ides(tmp_path)

        assert len(result) >= 2
        ids = [ide.id for ide, _ in result]
        assert "claude" in ids
        assert "cursor" in ids

    def test_sorted_by_priority(self, tmp_path: Path):
        """Test that results are sorted by IDE priority."""
        (tmp_path / ".cursor").mkdir()
        (tmp_path / ".claude").mkdir()

        from rekall.integrations import get_all_detected_ides

        result = get_all_detected_ides(tmp_path)

        # Claude (priority 1) should come before Cursor (priority 2)
        ids = [ide.id for ide, _ in result]
        if "claude" in ids and "cursor" in ids:
            assert ids.index("claude") < ids.index("cursor")
