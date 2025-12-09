"""Tests for Rekall CLI commands (TDD - written before implementation)."""

from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from conftest import make_config_with_db_path

runner = CliRunner()


# ============================================================================
# US1: Search Tests (T021-T025)
# ============================================================================


class TestSearchCommand:
    """Tests for `mem search` command."""

    def test_search_returns_results(self, temp_rekall_dir: Path):
        """T021: Search should return relevant results."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        # Setup
        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))
        db = Database(db_path)
        db.init()
        db.add(Entry(id=generate_ulid(), title="Fix circular import React", type="bug"))
        db.close()

        # Test
        result = runner.invoke(app, ["search", "circular import"])
        assert result.exit_code == 0
        assert "circular import" in result.stdout.lower()

    def test_search_empty_database(self, temp_rekall_dir: Path):
        """T022: Search on empty database should show no results message."""
        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(app, ["search", "nonexistent"])
        assert result.exit_code == 0
        assert "no results" in result.stdout.lower() or "aucun" in result.stdout.lower()

    def test_search_filter_by_type(self, temp_rekall_dir: Path):
        """T023: Search with --type should filter results."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))
        db = Database(db_path)
        db.init()
        db.add(Entry(id=generate_ulid(), title="Cache pattern", type="pattern"))
        db.add(Entry(id=generate_ulid(), title="Cache bug", type="bug"))
        db.close()

        result = runner.invoke(app, ["search", "cache", "--type", "bug"])
        assert result.exit_code == 0
        assert "bug" in result.stdout.lower()
        # Should not show pattern
        lines = [l for l in result.stdout.split("\n") if "pattern" in l.lower()]
        assert len(lines) == 0 or all("type" not in l.lower() for l in lines)

    def test_search_filter_by_project(self, temp_rekall_dir: Path):
        """T024: Search with --project should filter results."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))
        db = Database(db_path)
        db.init()
        db.add(
            Entry(
                id=generate_ulid(),
                title="React cache",
                type="pattern",
                project="frontend",
            )
        )
        db.add(
            Entry(
                id=generate_ulid(), title="Python cache", type="pattern", project="backend"
            )
        )
        db.close()

        result = runner.invoke(app, ["search", "cache", "--project", "frontend"])
        assert result.exit_code == 0
        assert "react" in result.stdout.lower()


# ============================================================================
# US2: Add Tests (T032-T036)
# ============================================================================


class TestAddCommand:
    """Tests for `mem add` command."""

    def test_add_creates_entry(self, temp_rekall_dir: Path):
        """T032: Add should create entry with type, title, tags."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(
            app, ["add", "bug", "Fix import issue", "-t", "react,import"]
        )
        assert result.exit_code == 0

        # Verify entry was created
        db = Database(db_path)
        db.init()
        entries = db.list_all()
        assert len(entries) == 1
        assert entries[0].title == "Fix import issue"
        assert entries[0].type == "bug"
        assert set(entries[0].tags) == {"react", "import"}
        db.close()

    def test_add_invalid_type(self, temp_rekall_dir: Path):
        """T033: Add with invalid type should show error and valid types."""
        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(app, ["add", "invalid", "Title"])
        assert result.exit_code != 0 or "invalid" in result.stdout.lower()
        # Should list valid types
        assert "bug" in result.stdout.lower() or "pattern" in result.stdout.lower()

    def test_add_with_confidence(self, temp_rekall_dir: Path):
        """T034: Add with -c should set confidence level."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(app, ["add", "pattern", "Best practice", "-c", "5"])
        assert result.exit_code == 0

        db = Database(db_path)
        db.init()
        entries = db.list_all()
        assert entries[0].confidence == 5
        db.close()

    def test_add_with_project(self, temp_rekall_dir: Path):
        """T035: Add with -p should set project."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(
            app, ["add", "decision", "Use TypeScript", "-p", "my-project"]
        )
        assert result.exit_code == 0

        db = Database(db_path)
        db.init()
        entries = db.list_all()
        assert entries[0].project == "my-project"
        db.close()

    def test_add_then_search(self, temp_rekall_dir: Path):
        """T036: Entry added should appear in search."""
        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Add entry
        runner.invoke(app, ["add", "bug", "Webpack bundler issue"])

        # Search for it
        result = runner.invoke(app, ["search", "webpack"])
        assert result.exit_code == 0
        assert "webpack" in result.stdout.lower()


# ============================================================================
# US3: Install Tests (T042-T045)
# ============================================================================


class TestInitCommand:
    """Tests for `mem init` command."""

    def test_init_creates_database(self, temp_rekall_dir: Path):
        """T042: Init should create database file."""
        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert db_path.exists()

    def test_init_preserves_existing_data(self, temp_rekall_dir: Path):
        """T043: Init on existing database should preserve data."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Create db with data
        db = Database(db_path)
        db.init()
        db.add(Entry(id=generate_ulid(), title="Existing entry", type="pattern"))
        db.close()

        # Run init again
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0

        # Verify data preserved
        db = Database(db_path)
        db.init()
        entries = db.list_all()
        assert len(entries) == 1
        assert entries[0].title == "Existing entry"
        db.close()


class TestVersionHelp:
    """Tests for version command and --help."""

    def test_version_shows_version(self):
        """T044: version command should display version."""
        from rekall.cli import app

        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        # Check version format (0.x.x) - dynamic version check
        from rekall import __version__
        assert __version__ in result.stdout

    def test_help_shows_commands(self):
        """T045: --help should list available commands."""
        from rekall.cli import app

        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "search" in result.stdout.lower()
        assert "add" in result.stdout.lower()


# ============================================================================
# US5: Research Tests (T064-T066)
# ============================================================================


class TestResearchCommand:
    """Tests for `mem research` command."""

    def test_research_shows_content(self):
        """T064: mem research ai-agents should show content."""
        from rekall.cli import app

        result = runner.invoke(app, ["research", "ai-agents"])
        assert result.exit_code == 0
        # Should contain some content about AI agents
        assert "agent" in result.stdout.lower() or "ai" in result.stdout.lower()

    def test_research_unknown_shows_list(self):
        """T065: mem research unknown should show available topics."""
        from rekall.cli import app

        result = runner.invoke(app, ["research", "unknown-topic"])
        # Should either exit with error or show available topics
        assert "ai-agents" in result.stdout.lower() or "available" in result.stdout.lower()

    def test_research_list_shows_topics(self):
        """T066: mem research --list should show available topics."""
        from rekall.cli import app

        result = runner.invoke(app, ["research", "--list"])
        assert result.exit_code == 0
        assert "ai-agents" in result.stdout.lower()
        assert "security" in result.stdout.lower()


# ============================================================================
# US6: Semantic Search Tests (T070-T071)
# ============================================================================


class TestSimilarCommand:
    """Tests for `mem similar` command."""

    def test_similar_fallback_to_fts(self, temp_rekall_dir: Path):
        """T070: mem similar without provider should fallback to FTS."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        # Setup
        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))
        db = Database(db_path)
        db.init()
        db.add(Entry(id=generate_ulid(), title="Python async patterns", type="pattern"))
        db.add(Entry(id=generate_ulid(), title="JavaScript promises", type="pattern"))
        db.close()

        # Test - should work even without embeddings provider
        result = runner.invoke(app, ["similar", "async programming"])
        assert result.exit_code == 0
        # Should indicate fallback or show results
        assert "fallback" in result.stdout.lower() or "result" in result.stdout.lower() or "python" in result.stdout.lower()

    def test_similar_empty_db(self, temp_rekall_dir: Path):
        """mem similar on empty database should show no results."""
        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(app, ["similar", "anything"])
        assert result.exit_code == 0
        assert "no" in result.stdout.lower() or "0" in result.stdout
