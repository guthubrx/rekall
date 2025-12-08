"""Tests for IDE/Agent integrations (TDD - written before implementation)."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

runner = CliRunner()


# ============================================================================
# US4: IDE Integration Tests (T050-T053)
# ============================================================================


class TestInstallCommand:
    """Tests for `mem install` command."""

    def test_install_cursor_creates_cursorrules(self, temp_rekall_dir: Path, tmp_path: Path, monkeypatch):
        """T050: mem install cursor should create .cursorrules file."""
        from rekall.cli import app

        # Change to temp directory to avoid modifying real files
        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["install", "cursor"])
        assert result.exit_code == 0

        # Check file was created
        cursorrules = tmp_path / ".cursorrules"
        assert cursorrules.exists()
        content = cursorrules.read_text()
        assert "rekall" in content.lower()

    def test_install_list_shows_available_ides(self, temp_rekall_dir: Path):
        """T051: mem install --list should show available IDEs."""
        from rekall.cli import app

        result = runner.invoke(app, ["install", "--list"])
        assert result.exit_code == 0
        assert "cursor" in result.stdout.lower()
        assert "claude" in result.stdout.lower()
        assert "copilot" in result.stdout.lower()

    def test_install_unknown_shows_error(self, temp_rekall_dir: Path):
        """T052: mem install unknown should show error and list valid options."""
        from rekall.cli import app

        result = runner.invoke(app, ["install", "unknown-ide"])
        assert result.exit_code != 0 or "error" in result.stdout.lower() or "unknown" in result.stdout.lower()
        # Should suggest valid options
        assert "cursor" in result.stdout.lower() or "available" in result.stdout.lower()

    def test_template_contains_mem_instructions(self, temp_rekall_dir: Path, tmp_path: Path, monkeypatch):
        """T053: Generated template should contain mem usage instructions."""
        from rekall.cli import app

        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["install", "cursor"])
        assert result.exit_code == 0

        cursorrules = tmp_path / ".cursorrules"
        content = cursorrules.read_text()

        # Should contain key rekall commands
        assert "rekall search" in content or "rekall add" in content
        # Should explain the purpose
        assert "knowledge" in content.lower() or "rekall" in content.lower()


class TestIntegrationTemplates:
    """Tests for individual integration templates."""

    def test_claude_template_creates_skill(self, temp_rekall_dir: Path, tmp_path: Path, monkeypatch):
        """Claude integration should create a skill file."""
        from rekall.cli import app

        # Use tmp_path as fake home
        fake_claude_dir = tmp_path / ".claude" / "commands"
        monkeypatch.setenv("HOME", str(tmp_path))

        result = runner.invoke(app, ["install", "claude"])
        assert result.exit_code == 0

        # Check skill was created
        skill_file = fake_claude_dir / "mem.md"
        assert skill_file.exists() or "created" in result.stdout.lower()

    def test_copilot_template_creates_instructions(self, temp_rekall_dir: Path, tmp_path: Path, monkeypatch):
        """Copilot integration should create instructions file."""
        from rekall.cli import app

        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["install", "copilot"])
        assert result.exit_code == 0

        # Check file was created (GitHub Copilot uses .github/copilot-instructions.md)
        copilot_file = tmp_path / ".github" / "copilot-instructions.md"
        assert copilot_file.exists()

    def test_windsurf_template_creates_rules(self, temp_rekall_dir: Path, tmp_path: Path, monkeypatch):
        """Windsurf integration should create rules file."""
        from rekall.cli import app

        monkeypatch.chdir(tmp_path)

        result = runner.invoke(app, ["install", "windsurf"])
        assert result.exit_code == 0

        # Windsurf uses .windsurfrules
        windsurf_file = tmp_path / ".windsurfrules"
        assert windsurf_file.exists()
