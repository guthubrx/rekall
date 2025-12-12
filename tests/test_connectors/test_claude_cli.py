"""Tests for Claude CLI connector (US1)."""

from pathlib import Path
from unittest.mock import patch

import pytest


class TestBaseConnectorValidation:
    """Tests for BaseConnector.validate_url() (T040)."""

    def test_validate_valid_https_url(self):
        """Should accept valid HTTPS URLs."""
        from rekall.connectors.base import BaseConnector

        # Create a concrete implementation for testing
        class TestConnector(BaseConnector):
            @property
            def cli_source(self):
                return "test"

            def is_available(self):
                return True

            def get_history_paths(self):
                return []

            def extract_urls(self, since_marker=None, project_filter=None):
                from rekall.connectors.base import ExtractionResult
                return ExtractionResult()

        connector = TestConnector()

        # Valid URLs
        is_valid, error = connector.validate_url("https://docs.python.org/3/")
        assert is_valid is True
        assert error is None

        is_valid, error = connector.validate_url("https://github.com/user/repo")
        assert is_valid is True
        assert error is None

    def test_validate_valid_http_url(self):
        """Should accept valid HTTP URLs."""
        from rekall.connectors.base import BaseConnector

        class TestConnector(BaseConnector):
            @property
            def cli_source(self):
                return "test"

            def is_available(self):
                return True

            def get_history_paths(self):
                return []

            def extract_urls(self, since_marker=None, project_filter=None):
                from rekall.connectors.base import ExtractionResult
                return ExtractionResult()

        connector = TestConnector()

        is_valid, error = connector.validate_url("http://example.com/page")
        assert is_valid is True
        assert error is None

    def test_validate_quarantine_localhost(self):
        """Should quarantine localhost URLs."""
        from rekall.connectors.base import BaseConnector

        class TestConnector(BaseConnector):
            @property
            def cli_source(self):
                return "test"

            def is_available(self):
                return True

            def get_history_paths(self):
                return []

            def extract_urls(self, since_marker=None, project_filter=None):
                from rekall.connectors.base import ExtractionResult
                return ExtractionResult()

        connector = TestConnector()

        is_valid, error = connector.validate_url("http://localhost:8000/api")
        assert is_valid is False
        assert "localhost" in error.lower()

        is_valid, error = connector.validate_url("http://127.0.0.1:3000/")
        assert is_valid is False
        assert "127.0.0.1" in error.lower()

    def test_validate_quarantine_file_urls(self):
        """Should quarantine file:// URLs."""
        from rekall.connectors.base import BaseConnector

        class TestConnector(BaseConnector):
            @property
            def cli_source(self):
                return "test"

            def is_available(self):
                return True

            def get_history_paths(self):
                return []

            def extract_urls(self, since_marker=None, project_filter=None):
                from rekall.connectors.base import ExtractionResult
                return ExtractionResult()

        connector = TestConnector()

        is_valid, error = connector.validate_url("file:///Users/test/secret.txt")
        assert is_valid is False
        assert "file:" in error.lower() or "scheme" in error.lower()

    def test_validate_quarantine_private_ips(self):
        """Should quarantine private IP ranges."""
        from rekall.connectors.base import BaseConnector

        class TestConnector(BaseConnector):
            @property
            def cli_source(self):
                return "test"

            def is_available(self):
                return True

            def get_history_paths(self):
                return []

            def extract_urls(self, since_marker=None, project_filter=None):
                from rekall.connectors.base import ExtractionResult
                return ExtractionResult()

        connector = TestConnector()

        # 192.168.x.x
        is_valid, error = connector.validate_url("http://192.168.1.1/admin")
        assert is_valid is False

        # 10.x.x.x
        is_valid, error = connector.validate_url("http://10.0.0.1/")
        assert is_valid is False

        # 172.16-31.x.x
        is_valid, error = connector.validate_url("http://172.16.0.1/")
        assert is_valid is False

    def test_validate_empty_url(self):
        """Should reject empty URLs."""
        from rekall.connectors.base import BaseConnector

        class TestConnector(BaseConnector):
            @property
            def cli_source(self):
                return "test"

            def is_available(self):
                return True

            def get_history_paths(self):
                return []

            def extract_urls(self, since_marker=None, project_filter=None):
                from rekall.connectors.base import ExtractionResult
                return ExtractionResult()

        connector = TestConnector()

        is_valid, error = connector.validate_url("")
        assert is_valid is False

        is_valid, error = connector.validate_url("   ")
        assert is_valid is False

    def test_validate_missing_scheme(self):
        """Should reject URLs without scheme."""
        from rekall.connectors.base import BaseConnector

        class TestConnector(BaseConnector):
            @property
            def cli_source(self):
                return "test"

            def is_available(self):
                return True

            def get_history_paths(self):
                return []

            def extract_urls(self, since_marker=None, project_filter=None):
                from rekall.connectors.base import ExtractionResult
                return ExtractionResult()

        connector = TestConnector()

        is_valid, error = connector.validate_url("example.com/page")
        assert is_valid is False
        assert "scheme" in error.lower()


class TestClaudeCLIConnectorAvailability:
    """Tests for ClaudeCLIConnector.is_available() (T038)."""

    def test_is_available_with_projects(self, tmp_path: Path):
        """Should return True when projects directory exists with content."""
        from rekall.connectors.claude_cli import ClaudeCLIConnector

        # Create mock Claude directory structure
        projects_dir = tmp_path / ".claude" / "projects" / "project1" / "conversations"
        projects_dir.mkdir(parents=True)
        (projects_dir / "conv1.jsonl").write_text('{"type": "test"}')

        connector = ClaudeCLIConnector()
        # Patch the paths
        with patch.object(connector, "CLAUDE_DIR", tmp_path / ".claude"):
            with patch.object(connector, "PROJECTS_DIR", tmp_path / ".claude" / "projects"):
                assert connector.is_available() is True

    def test_is_available_no_directory(self, tmp_path: Path):
        """Should return False when Claude directory doesn't exist."""
        from rekall.connectors.claude_cli import ClaudeCLIConnector

        connector = ClaudeCLIConnector()
        with patch.object(connector, "PROJECTS_DIR", tmp_path / "nonexistent"):
            assert connector.is_available() is False

    def test_is_available_empty_directory(self, tmp_path: Path):
        """Should return False when projects directory is empty."""
        from rekall.connectors.claude_cli import ClaudeCLIConnector

        projects_dir = tmp_path / ".claude" / "projects"
        projects_dir.mkdir(parents=True)

        connector = ClaudeCLIConnector()
        with patch.object(connector, "PROJECTS_DIR", projects_dir):
            assert connector.is_available() is False


class TestClaudeCLIConnectorExtraction:
    """Tests for ClaudeCLIConnector.extract_urls() (T039)."""

    def test_extract_webfetch_urls(self, tmp_path: Path):
        """Should extract URLs from WebFetch tool calls."""
        from rekall.connectors.claude_cli import ClaudeCLIConnector

        # Create mock structure
        project_dir = tmp_path / ".claude" / "projects" / "test-project"
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir(parents=True)

        # Copy fixture
        fixture_path = Path(__file__).parent / "fixtures" / "sample_claude.jsonl"
        if fixture_path.exists():
            (conv_dir / "conv1.jsonl").write_text(fixture_path.read_text())
        else:
            # Create inline fixture
            (conv_dir / "conv1.jsonl").write_text(
                '{"type": "human", "content": "Help with Python"}\n'
                '{"type": "tool_use", "name": "WebFetch", "input": {"url": "https://docs.python.org/3/"}}\n'
                '{"type": "assistant", "content": "Check https://realpython.com/ for tutorials"}\n'
            )

        connector = ClaudeCLIConnector()
        with patch.object(connector, "CLAUDE_DIR", tmp_path / ".claude"):
            with patch.object(connector, "PROJECTS_DIR", tmp_path / ".claude" / "projects"):
                result = connector.extract_urls()

        assert result.files_processed >= 1
        assert len(result.urls) >= 2  # At least WebFetch URL + inline URL

        # Check domains
        domains = {u.domain for u in result.urls}
        assert "docs.python.org" in domains

    def test_extract_inline_urls(self, tmp_path: Path):
        """Should extract inline URLs from assistant responses."""
        from rekall.connectors.claude_cli import ClaudeCLIConnector

        project_dir = tmp_path / ".claude" / "projects" / "test-project"
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir(parents=True)

        (conv_dir / "conv1.jsonl").write_text(
            '{"type": "human", "content": "Resources?"}\n'
            '{"type": "assistant", "content": "Try https://github.com/user/repo and https://stackoverflow.com/questions/123"}\n'
        )

        connector = ClaudeCLIConnector()
        with patch.object(connector, "CLAUDE_DIR", tmp_path / ".claude"):
            with patch.object(connector, "PROJECTS_DIR", tmp_path / ".claude" / "projects"):
                result = connector.extract_urls()

        domains = {u.domain for u in result.urls}
        assert "github.com" in domains
        assert "stackoverflow.com" in domains

    def test_extract_with_quarantine(self, tmp_path: Path):
        """Should identify quarantined URLs but still include them."""
        from rekall.connectors.claude_cli import ClaudeCLIConnector

        project_dir = tmp_path / ".claude" / "projects" / "test-project"
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir(parents=True)

        (conv_dir / "conv1.jsonl").write_text(
            '{"type": "tool_use", "name": "WebFetch", "input": {"url": "https://valid.com/"}}\n'
            '{"type": "tool_use", "name": "WebFetch", "input": {"url": "http://localhost:8000/"}}\n'
            '{"type": "tool_use", "name": "WebFetch", "input": {"url": "file:///etc/passwd"}}\n'
        )

        connector = ClaudeCLIConnector()
        with patch.object(connector, "CLAUDE_DIR", tmp_path / ".claude"):
            with patch.object(connector, "PROJECTS_DIR", tmp_path / ".claude" / "projects"):
                result = connector.extract_urls()

        # All URLs should be extracted
        urls = {u.url for u in result.urls}
        assert "https://valid.com/" in urls
        assert "http://localhost:8000/" in urls

        # Validate them
        for extracted in result.urls:
            is_valid, _ = connector.validate_url(extracted.url)
            if extracted.url == "https://valid.com/":
                assert is_valid is True
            elif "localhost" in extracted.url:
                assert is_valid is False

    def test_extract_with_context(self, tmp_path: Path):
        """Should extract user query context with URLs."""
        from rekall.connectors.claude_cli import ClaudeCLIConnector

        project_dir = tmp_path / ".claude" / "projects" / "test-project"
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir(parents=True)

        (conv_dir / "conv1.jsonl").write_text(
            '{"type": "human", "content": "How do I use asyncio in Python?"}\n'
            '{"type": "tool_use", "name": "WebFetch", "input": {"url": "https://docs.python.org/3/library/asyncio.html"}}\n'
        )

        connector = ClaudeCLIConnector()
        with patch.object(connector, "CLAUDE_DIR", tmp_path / ".claude"):
            with patch.object(connector, "PROJECTS_DIR", tmp_path / ".claude" / "projects"):
                result = connector.extract_urls()

        assert len(result.urls) >= 1
        url = result.urls[0]
        assert url.user_query is not None
        assert "asyncio" in url.user_query.lower()


class TestClaudeCLIConnectorCDC:
    """Tests for incremental import CDC (T041)."""

    def test_incremental_import_skips_old_files(self, tmp_path: Path):
        """Should skip files before the marker for CDC."""
        from rekall.connectors.claude_cli import ClaudeCLIConnector
        import time

        project_dir = tmp_path / ".claude" / "projects" / "test-project"
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir(parents=True)

        # Create old file
        old_file = conv_dir / "old.jsonl"
        old_file.write_text(
            '{"type": "tool_use", "name": "WebFetch", "input": {"url": "https://old.com/"}}\n'
        )
        time.sleep(0.01)  # Ensure different mtime

        # Create new file
        new_file = conv_dir / "new.jsonl"
        new_file.write_text(
            '{"type": "tool_use", "name": "WebFetch", "input": {"url": "https://new.com/"}}\n'
        )

        connector = ClaudeCLIConnector()
        with patch.object(connector, "CLAUDE_DIR", tmp_path / ".claude"):
            with patch.object(connector, "PROJECTS_DIR", tmp_path / ".claude" / "projects"):
                # Full extraction
                full_result = connector.extract_urls()
                assert len(full_result.urls) == 2

                # Incremental from old file marker
                incremental_result = connector.extract_urls(since_marker=str(old_file))
                assert len(incremental_result.urls) == 1
                assert incremental_result.urls[0].url == "https://new.com/"

    def test_incremental_import_returns_marker(self, tmp_path: Path):
        """Should return last file marker for CDC tracking."""
        from rekall.connectors.claude_cli import ClaudeCLIConnector

        project_dir = tmp_path / ".claude" / "projects" / "test-project"
        conv_dir = project_dir / "conversations"
        conv_dir.mkdir(parents=True)

        (conv_dir / "conv1.jsonl").write_text(
            '{"type": "tool_use", "name": "WebFetch", "input": {"url": "https://test.com/"}}\n'
        )

        connector = ClaudeCLIConnector()
        with patch.object(connector, "CLAUDE_DIR", tmp_path / ".claude"):
            with patch.object(connector, "PROJECTS_DIR", tmp_path / ".claude" / "projects"):
                result = connector.extract_urls()

        assert result.last_file_marker is not None
        assert "conv1.jsonl" in result.last_file_marker


class TestConnectorRegistry:
    """Tests for connector registry."""

    def test_get_connector_claude(self):
        """Should return Claude connector by name."""
        from rekall.connectors import get_connector

        connector = get_connector("claude")
        assert connector is not None
        assert connector.cli_source == "claude"

    def test_get_connector_unknown(self):
        """Should return None for unknown connector."""
        from rekall.connectors import get_connector

        connector = get_connector("unknown")
        assert connector is None

    def test_list_connectors(self):
        """Should list available connector names."""
        from rekall.connectors import list_connectors

        connectors = list_connectors()
        assert "claude" in connectors
