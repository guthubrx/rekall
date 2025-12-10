"""Tests for Rekall CLI commands (TDD - written before implementation)."""

from pathlib import Path
from unittest.mock import patch

from conftest import make_config_with_db_path
from typer.testing import CliRunner

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
        lines = [line for line in result.stdout.split("\n") if "pattern" in line.lower()]
        assert len(lines) == 0 or all("type" not in line.lower() for line in lines)

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
        # Use optional context_mode for legacy tests without structured context
        set_config(make_config_with_db_path(db_path, context_mode="optional"))

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
        set_config(make_config_with_db_path(db_path, context_mode="optional"))

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
        set_config(make_config_with_db_path(db_path, context_mode="optional"))

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
        set_config(make_config_with_db_path(db_path, context_mode="optional"))

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


# ============================================================================
# Phase 2: Smart Embeddings CLI Tests (T021-T024)
# ============================================================================


class TestAddCommandWithContext:
    """Tests for `rekall add` with --context option (Phase 2)."""

    def test_add_with_context_option(self, temp_rekall_dir: Path):
        """T021: Add should accept --context option for AI agent use."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(
            app,
            [
                "add", "bug", "Fix timeout error",
                "--context", "User asked about network errors in the API calls"
            ],
        )
        assert result.exit_code == 0
        assert "created" in result.stdout.lower()

        # Verify entry was created
        db = Database(db_path)
        db.init()
        entries = db.list_all()
        assert len(entries) == 1
        assert entries[0].title == "Fix timeout error"
        db.close()

    def test_add_with_context_and_content(self, temp_rekall_dir: Path):
        """Add should accept both --context and --content."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(
            app,
            [
                "add", "pattern", "Retry pattern",
                "--content", "Implement exponential backoff",
                "--context", "Discussion about resilient network calls"
            ],
        )
        assert result.exit_code == 0

        db = Database(db_path)
        db.init()
        entries = db.list_all()
        assert entries[0].content == "Implement exponential backoff"
        db.close()


class TestAddEmbeddingCalculation:
    """Tests for embedding calculation in add command (Phase 2)."""

    @patch("rekall.embeddings.EmbeddingService.calculate")
    @patch("rekall.embeddings.EmbeddingService._check_availability")
    def test_add_calculates_embedding_when_enabled(
        self, mock_check, mock_calculate, temp_rekall_dir: Path
    ):
        """T022: Add should calculate embedding when smart_embeddings_enabled."""
        import numpy as np

        from rekall.cli import app
        from rekall.config import Config, set_config
        from rekall.db import Database
        from rekall.paths import PathSource, ResolvedPaths

        db_path = temp_rekall_dir / "knowledge.db"
        paths = ResolvedPaths(
            config_dir=temp_rekall_dir,
            data_dir=temp_rekall_dir,
            cache_dir=temp_rekall_dir / "cache",
            db_path=db_path,
            source=PathSource.CLI,
        )
        config = Config(paths=paths, smart_embeddings_enabled=True)
        config.smart_embeddings_context_mode = "optional"  # Allow add without context
        set_config(config)

        # Mock the embedding service
        mock_check.return_value = True
        mock_calculate.return_value = np.random.randn(384).astype(np.float32)

        result = runner.invoke(app, ["add", "bug", "Test embedding"])
        assert result.exit_code == 0
        # Should show embedding calculated
        assert "embedding" in result.stdout.lower()

        # Verify embedding was saved
        db = Database(db_path)
        db.init()
        entries = db.list_all()
        embeddings = db.get_embeddings(entries[0].id)
        assert len(embeddings) >= 1
        assert embeddings[0].embedding_type == "summary"
        db.close()

    def test_add_without_embeddings_enabled(self, temp_rekall_dir: Path):
        """Add should not calculate embedding when disabled (default)."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path, context_mode="optional"))

        result = runner.invoke(app, ["add", "bug", "Simple bug fix"])
        assert result.exit_code == 0
        # Should not mention embedding calculation (📊 symbol)
        assert "📊" not in result.stdout

        # Verify no embedding was saved
        db = Database(db_path)
        db.init()
        entries = db.list_all()
        embeddings = db.get_embeddings(entries[0].id)
        assert len(embeddings) == 0
        db.close()


class TestShowEmbeddingStatus:
    """Tests for embedding status display in show command (Phase 2)."""

    def test_show_displays_embedding_status(self, temp_rekall_dir: Path):
        """T023: Show should display embedding status when present."""
        import numpy as np

        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Embedding, Entry, generate_ulid

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Create entry with embedding
        db = Database(db_path)
        db.init()
        entry = Entry(id=generate_ulid(), title="Entry with embedding", type="bug")
        db.add(entry)

        # Add embedding
        vec = np.random.randn(384).astype(np.float32)
        emb = Embedding.from_numpy(entry.id, "summary", vec, "test-model")
        db.add_embedding(emb)
        db.close()

        # Test show
        result = runner.invoke(app, ["show", entry.id])
        assert result.exit_code == 0
        assert "embedding" in result.stdout.lower()
        assert "summary" in result.stdout.lower()

    def test_show_no_embedding_status(self, temp_rekall_dir: Path):
        """Show should not display embedding section when no embeddings."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Create entry without embedding
        db = Database(db_path)
        db.init()
        entry = Entry(id=generate_ulid(), title="Entry without embedding", type="bug")
        db.add(entry)
        db.close()

        # Test show
        result = runner.invoke(app, ["show", entry.id])
        assert result.exit_code == 0
        # Should not show embedding section
        assert "embedding" not in result.stdout.lower() or "📊" not in result.stdout

    def test_show_multiple_embeddings(self, temp_rekall_dir: Path):
        """Show should display all embedding types when multiple present."""
        import numpy as np

        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Embedding, Entry, generate_ulid

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Create entry with multiple embeddings
        db = Database(db_path)
        db.init()
        entry = Entry(id=generate_ulid(), title="Entry with both embeddings", type="bug")
        db.add(entry)

        # Add both embeddings
        vec = np.random.randn(384).astype(np.float32)
        emb_summary = Embedding.from_numpy(entry.id, "summary", vec, "test-model")
        emb_context = Embedding.from_numpy(entry.id, "context", vec, "test-model")
        db.add_embedding(emb_summary)
        db.add_embedding(emb_context)
        db.close()

        # Test show
        result = runner.invoke(app, ["show", entry.id])
        assert result.exit_code == 0
        assert "summary" in result.stdout.lower()
        assert "context" in result.stdout.lower()


class TestAddWithStructuredContext:
    """Tests for add command with --context-json (Feature 006)."""

    def test_add_with_context_json(self, temp_rekall_dir: Path):
        """Should create entry with structured context."""
        import json

        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        context = {
            "situation": "API timeout on long requests",
            "solution": "Increase nginx proxy_read_timeout to 120s",
            "trigger_keywords": ["nginx", "timeout", "504"],
        }
        context_json = json.dumps(context)

        result = runner.invoke(app, [
            "add", "bug", "Fix 504 timeout",
            "--context-json", context_json,
        ])
        assert result.exit_code == 0
        assert "Entry created" in result.stdout
        assert "keywords stored" in result.stdout

        # Verify context was stored
        db = Database(db_path)
        db.init()
        entries = db.list_all(limit=1)
        assert len(entries) == 1

        ctx = db.get_structured_context(entries[0].id)
        assert ctx is not None
        assert ctx.situation == "API timeout on long requests"
        assert "nginx" in ctx.trigger_keywords
        db.close()

    def test_add_with_invalid_context_json(self, temp_rekall_dir: Path):
        """Should reject invalid JSON."""
        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(app, [
            "add", "bug", "Test",
            "--context-json", "not valid json",
        ])
        assert result.exit_code == 1
        assert "Invalid JSON" in result.stdout

    def test_add_with_incomplete_context_json(self, temp_rekall_dir: Path):
        """Should reject context missing required fields."""
        import json

        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Missing trigger_keywords
        context = {
            "situation": "Test situation",
            "solution": "Test solution",
            # trigger_keywords missing
        }
        result = runner.invoke(app, [
            "add", "bug", "Test",
            "--context-json", json.dumps(context),
        ])
        assert result.exit_code == 1
        assert "Invalid structured context" in result.stdout

    def test_add_context_json_with_all_fields(self, temp_rekall_dir: Path):
        """Should accept context with all optional fields."""
        import json

        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        context = {
            "situation": "Database connection failures",
            "solution": "Add connection pooling with retry logic",
            "trigger_keywords": ["database", "connection", "pool"],
            "what_failed": "Increasing max connections didn't help",
            "files_modified": ["db.py", "config.py"],
            "error_messages": ["Connection refused", "Too many connections"],
        }

        result = runner.invoke(app, [
            "add", "bug", "Fix DB connections",
            "--context-json", json.dumps(context),
        ])
        assert result.exit_code == 0

        # Verify all fields stored
        db = Database(db_path)
        db.init()
        entries = db.list_all(limit=1)
        ctx = db.get_structured_context(entries[0].id)

        assert ctx.what_failed == "Increasing max connections didn't help"
        assert ctx.files_modified == ["db.py", "config.py"]
        assert "Connection refused" in ctx.error_messages
        db.close()


# ============================================================================
# Feature 007: Migration & Maintenance Tests
# ============================================================================


class TestVersionCommand:
    """Tests for enhanced version command (Feature 007)."""

    def test_version_shows_schema_version(self, temp_rekall_dir: Path):
        """Version should display schema version when DB exists."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Create database
        db = Database(db_path)
        db.init()
        db.close()

        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Schema Version" in result.stdout
        # Should show current schema version
        assert "v6" in result.stdout or "(current)" in result.stdout

    def test_version_shows_no_db_schema(self, temp_rekall_dir: Path):
        """Version should show latest schema when no DB exists."""
        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "Schema Version" in result.stdout


class TestMigrateCommand:
    """Tests for migrate command (Feature 007)."""

    def test_migrate_no_pending(self, temp_rekall_dir: Path):
        """Migrate should report no pending migrations when current."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Create fully migrated database
        db = Database(db_path)
        db.init()
        db.close()

        result = runner.invoke(app, ["migrate"])
        assert result.exit_code == 0
        assert "current" in result.stdout.lower() or "no" in result.stdout.lower()

    def test_migrate_dry_run(self, temp_rekall_dir: Path):
        """Migrate --dry-run should preview without applying."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        db = Database(db_path)
        db.init()
        db.close()

        result = runner.invoke(app, ["migrate", "--dry-run"])
        assert result.exit_code == 0
        # Should show dry run message or current status
        assert "dry run" in result.stdout.lower() or "current" in result.stdout.lower()

    def test_migrate_no_database(self, temp_rekall_dir: Path):
        """Migrate should fail gracefully when no database."""
        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(app, ["migrate"])
        assert result.exit_code == 1
        assert "no database" in result.stdout.lower()

    def test_migrate_enrich_context_dry_run(self, temp_rekall_dir: Path):
        """Migrate --enrich-context --dry-run should show legacy entries."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Create entries without context
        db = Database(db_path)
        db.init()
        db.add(Entry(id=generate_ulid(), title="Legacy entry 1", type="bug"))
        db.add(Entry(id=generate_ulid(), title="Legacy entry 2", type="pattern"))
        db.close()

        result = runner.invoke(app, ["migrate", "--enrich-context", "--dry-run"])
        assert result.exit_code == 0
        assert "2" in result.stdout  # 2 entries
        assert "dry run" in result.stdout.lower()

    def test_migrate_enrich_context_applies(self, temp_rekall_dir: Path):
        """Migrate --enrich-context should add structured context."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Create entry without context
        db = Database(db_path)
        db.init()
        entry = Entry(
            id=generate_ulid(),
            title="Fix nginx timeout",
            type="bug",
            content="Increase proxy_read_timeout to 120s",
        )
        db.add(entry)
        db.close()

        result = runner.invoke(app, ["migrate", "--enrich-context", "--yes"])
        assert result.exit_code == 0
        assert "Enriched" in result.stdout

        # Verify context was added
        db = Database(db_path)
        db.init()
        ctx = db.get_structured_context(entry.id)
        assert ctx is not None
        assert ctx.extraction_method == "migrated"
        assert len(ctx.trigger_keywords) > 0
        db.close()


class TestChangelogCommand:
    """Tests for changelog command (Feature 007)."""

    def test_changelog_shows_content(self, temp_rekall_dir: Path):
        """Changelog should display CHANGELOG.md content."""
        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        # Note: CHANGELOG.md should exist at project root
        result = runner.invoke(app, ["changelog"])
        # Either shows content or reports not found
        assert result.exit_code == 0 or "not found" in result.stdout.lower()

    def test_changelog_version_filter(self, temp_rekall_dir: Path, tmp_path: Path):
        """Changelog with version should filter content."""
        from rekall.cli import app
        from rekall.config import set_config

        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))

        result = runner.invoke(app, ["changelog", "0.2.0"])
        # Either shows version content or reports not found
        if result.exit_code == 0:
            assert "0.2.0" in result.stdout or "Feature" in result.stdout


class TestContextModeRequired:
    """Tests for context_mode = 'required' (Feature 007 Phase 6)."""

    def test_add_rejected_without_context_when_required(self, temp_rekall_dir: Path):
        """Add should reject entries without context when mode is required."""
        from rekall.cli import app
        from rekall.config import Config, set_config
        from rekall.paths import PathSource, ResolvedPaths

        db_path = temp_rekall_dir / "knowledge.db"
        paths = ResolvedPaths(
            config_dir=temp_rekall_dir,
            data_dir=temp_rekall_dir,
            cache_dir=temp_rekall_dir / "cache",
            db_path=db_path,
            source=PathSource.CLI,
        )
        # Set context_mode to required
        config = Config(paths=paths, smart_embeddings_context_mode="required")
        set_config(config)

        # Try to add without context
        result = runner.invoke(app, ["add", "bug", "Test without context"])
        assert result.exit_code == 1
        assert "required" in result.stdout.lower() or "context" in result.stdout.lower()

    def test_add_allowed_without_context_when_optional(self, temp_rekall_dir: Path):
        """Add should allow entries without context when mode is optional."""
        from rekall.cli import app
        from rekall.config import Config, set_config
        from rekall.paths import PathSource, ResolvedPaths

        db_path = temp_rekall_dir / "knowledge.db"
        paths = ResolvedPaths(
            config_dir=temp_rekall_dir,
            data_dir=temp_rekall_dir,
            cache_dir=temp_rekall_dir / "cache",
            db_path=db_path,
            source=PathSource.CLI,
        )
        # Set context_mode to optional
        config = Config(paths=paths, smart_embeddings_context_mode="optional")
        set_config(config)

        # Try to add without context - should succeed
        result = runner.invoke(app, ["add", "bug", "Test without context"])
        assert result.exit_code == 0
        assert "Entry created" in result.stdout

    def test_default_context_mode_is_required(self):
        """Config default should be context_mode = required."""
        from rekall.config import Config

        config = Config()
        assert config.smart_embeddings_context_mode == "required"
