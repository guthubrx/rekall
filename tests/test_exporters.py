"""Tests for export functionality (TDD - written before implementation)."""

from pathlib import Path

from conftest import make_config_with_db_path
from typer.testing import CliRunner

runner = CliRunner()


# ============================================================================
# Phase 9: Export Tests (T078-T080)
# ============================================================================


class TestExportCommand:
    """Tests for `mem export` command."""

    def test_export_markdown(self, temp_rekall_dir: Path, tmp_path: Path):
        """T078: mem export should export to markdown."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        # Setup
        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))
        db = Database(db_path)
        db.init()
        db.add(Entry(id=generate_ulid(), title="Test bug", type="bug", content="Bug content"))
        db.close()

        output_file = tmp_path / "export.md"
        result = runner.invoke(app, ["export", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()
        content = output_file.read_text()
        assert "Test bug" in content
        assert "bug" in content.lower()

    def test_export_json(self, temp_rekall_dir: Path, tmp_path: Path):
        """T079: mem export should export to JSON."""
        import json

        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        # Setup
        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))
        db = Database(db_path)
        db.init()
        db.add(Entry(id=generate_ulid(), title="Test pattern", type="pattern"))
        db.close()

        output_file = tmp_path / "export.json"
        result = runner.invoke(app, ["export", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()

        data = json.loads(output_file.read_text())
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["title"] == "Test pattern"

    def test_export_warns_sensitive_data(self, temp_rekall_dir: Path, tmp_path: Path):
        """T080: Export should warn if content contains sensitive data patterns."""
        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        # Setup with sensitive content
        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))
        db = Database(db_path)
        db.init()
        db.add(Entry(
            id=generate_ulid(),
            title="API config",
            type="config",
            content="API_KEY=sk-abc123def456 SECRET_TOKEN=xyz789"
        ))
        db.close()

        output_file = tmp_path / "export.md"
        result = runner.invoke(app, ["export", str(output_file)])
        # Should still export but warn
        assert result.exit_code == 0
        assert "warning" in result.stdout.lower() or "sensitive" in result.stdout.lower()

    def test_export_rekall_archive(self, temp_rekall_dir: Path, tmp_path: Path):
        """Export to .rekall archive format."""
        import zipfile

        from rekall.cli import app
        from rekall.config import set_config
        from rekall.db import Database
        from rekall.models import Entry, generate_ulid

        # Setup
        db_path = temp_rekall_dir / "knowledge.db"
        set_config(make_config_with_db_path(db_path))
        db = Database(db_path)
        db.init()
        db.add(Entry(id=generate_ulid(), title="Archive test", type="pattern"))
        db.close()

        output_file = tmp_path / "backup.rekall.zip"
        result = runner.invoke(app, ["export", str(output_file)])
        assert result.exit_code == 0
        assert output_file.exists()
        assert zipfile.is_zipfile(output_file)
