"""Tests for Article 99 version recommendation system."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch


class TestArticle99Versions:
    """Tests for Article 99 version constants."""

    def test_micro_version_exists(self):
        """Test that ARTICLE_99_MICRO constant exists."""
        from rekall.integrations import ARTICLE_99_MICRO

        assert ARTICLE_99_MICRO is not None
        assert isinstance(ARTICLE_99_MICRO, str)
        # Should be ~50 tokens (very short)
        assert len(ARTICLE_99_MICRO) < 500

    def test_short_version_exists(self):
        """Test that ARTICLE_99_SHORT constant exists."""
        from rekall.integrations import ARTICLE_99_SHORT

        assert ARTICLE_99_SHORT is not None
        assert isinstance(ARTICLE_99_SHORT, str)
        # Should be ~350 tokens
        assert len(ARTICLE_99_SHORT) > 500
        assert len(ARTICLE_99_SHORT) < 5000

    def test_extensive_version_exists(self):
        """Test that ARTICLE_99_EXTENSIVE constant exists."""
        from rekall.integrations import ARTICLE_99_EXTENSIVE

        assert ARTICLE_99_EXTENSIVE is not None
        assert isinstance(ARTICLE_99_EXTENSIVE, str)
        # Should be ~1000 tokens (longest)
        assert len(ARTICLE_99_EXTENSIVE) > 2000

    def test_versions_ordered_by_length(self):
        """Test that versions are ordered: MICRO < SHORT < EXTENSIVE."""
        from rekall.integrations import (
            ARTICLE_99_MICRO,
            ARTICLE_99_SHORT,
            ARTICLE_99_EXTENSIVE,
        )

        assert len(ARTICLE_99_MICRO) < len(ARTICLE_99_SHORT)
        assert len(ARTICLE_99_SHORT) < len(ARTICLE_99_EXTENSIVE)


class TestArticle99Recommendation:
    """Tests for get_article99_recommendation() function."""

    def test_recommends_micro_with_skill_installed(self, tmp_path: Path):
        """Test that MICRO is recommended when Claude skill is installed."""
        from rekall.integrations import get_article99_recommendation, Article99Version

        # Create Claude skill directory
        claude_dir = tmp_path / ".claude" / "commands"
        claude_dir.mkdir(parents=True)
        (claude_dir / "rekall.md").write_text("# Rekall skill")

        with patch.object(Path, "home", return_value=tmp_path):
            result = get_article99_recommendation(tmp_path)

        assert result.recommended == Article99Version.MICRO
        assert "skill" in result.reason.lower()

    def test_recommends_short_with_mcp_only(self, tmp_path: Path):
        """Test that SHORT is recommended when MCP is configured but no skill."""
        from rekall.integrations import get_article99_recommendation, Article99Version

        # Create Claude MCP config (settings.json) without skill
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(parents=True)
        # Create settings.json to simulate MCP config
        (claude_dir / "settings.json").write_text('{"mcpServers": {}}')
        # No commands/rekall.md (no skill)

        with patch.object(Path, "home", return_value=tmp_path):
            result = get_article99_recommendation(tmp_path)

        assert result.recommended == Article99Version.SHORT
        assert "mcp" in result.reason.lower()

    def test_recommends_extensive_cli_only(self, tmp_path: Path):
        """Test that EXTENSIVE is recommended when only CLI is available."""
        from rekall.integrations import get_article99_recommendation, Article99Version

        # No IDE integration at all
        with patch.object(Path, "home", return_value=tmp_path):
            result = get_article99_recommendation(tmp_path)

        assert result.recommended == Article99Version.EXTENSIVE
        assert "cli" in result.reason.lower()

    def test_recommendation_includes_reason(self, tmp_path: Path):
        """Test that recommendation always includes a reason."""
        from rekall.integrations import get_article99_recommendation

        with patch.object(Path, "home", return_value=tmp_path):
            result = get_article99_recommendation(tmp_path)

        assert result.reason is not None
        assert len(result.reason) > 0


class TestArticle99Installation:
    """Tests for install_article99() function."""

    def test_install_micro_version(self, tmp_path: Path):
        """Test installing MICRO version of Article 99."""
        from rekall.integrations import install_article99, Article99Version

        # Create speckit directory
        speckit_dir = tmp_path / ".speckit"
        speckit_dir.mkdir()
        constitution = speckit_dir / "constitution.md"
        constitution.write_text("# Constitution\n\n## Existing content")

        with patch.object(Path, "home", return_value=tmp_path):
            result = install_article99(Article99Version.MICRO)

        assert result is True
        content = constitution.read_text()
        # Article 99 uses Roman numeral XCIX
        assert "XCIX" in content or "Rekall" in content

    def test_install_requires_speckit_dir(self, tmp_path: Path):
        """Test that installation fails if speckit directory doesn't exist."""
        from rekall.integrations import install_article99, Article99Version

        with patch.object(Path, "home", return_value=tmp_path):
            result = install_article99(Article99Version.MICRO)

        assert result is False

    def test_install_replaces_existing_article99(self, tmp_path: Path):
        """Test that installing a new version replaces existing Article 99."""
        from rekall.integrations import install_article99, Article99Version

        # Create speckit directory with existing Article 99
        speckit_dir = tmp_path / ".speckit"
        speckit_dir.mkdir()
        constitution = speckit_dir / "constitution.md"
        constitution.write_text(
            "# Constitution\n\n"
            "## Article 99 - Rekall\n"
            "Old content here\n\n"
            "## Article 100"
        )

        with patch.object(Path, "home", return_value=tmp_path):
            install_article99(Article99Version.EXTENSIVE)

        content = constitution.read_text()
        # Should have new content, not old
        assert "Old content here" not in content
        assert "Article 100" in content  # Other articles preserved
