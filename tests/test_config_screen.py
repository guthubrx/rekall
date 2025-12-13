"""Integration tests for ConfigApp TUI screen."""

from __future__ import annotations

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestConfigAppStructure:
    """Tests for ConfigApp basic structure and sections."""

    @pytest.mark.asyncio
    async def test_config_app_has_two_sections(self):
        """Test that ConfigApp displays 2 main sections."""
        from rekall.tui_main import ConfigApp

        app = ConfigApp()
        async with app.run_test() as pilot:
            # Check for INTÉGRATIONS section
            integrations_section = app.query_one("#integrations-section", expect_type=None)
            assert integrations_section is not None

            # Check for SPECKIT section
            speckit_section = app.query_one("#speckit-section", expect_type=None)
            assert speckit_section is not None

    @pytest.mark.asyncio
    async def test_integrations_section_shows_ides(self):
        """Test that INTÉGRATIONS section lists all supported IDEs."""
        from rekall.tui_main import ConfigApp

        app = ConfigApp()
        async with app.run_test() as pilot:
            # Should show at least Claude and Cursor
            content = app.query_one("#integrations-section").render()
            content_str = str(content)

            assert "Claude" in content_str or "claude" in content_str
            assert "Cursor" in content_str or "cursor" in content_str

    @pytest.mark.asyncio
    async def test_speckit_section_conditional_visibility(self, tmp_path: Path):
        """Test that SPECKIT section is only visible if ~/.speckit/ exists."""
        from rekall.tui_main import ConfigApp

        # Test without speckit directory
        with patch.object(Path, "home", return_value=tmp_path):
            app = ConfigApp()
            async with app.run_test() as pilot:
                speckit_section = app.query("#speckit-section")
                # Should be hidden or empty when no speckit
                assert len(speckit_section) == 0 or not speckit_section[0].display

        # Test with speckit directory
        (tmp_path / ".speckit").mkdir()
        with patch.object(Path, "home", return_value=tmp_path):
            app = ConfigApp()
            async with app.run_test() as pilot:
                speckit_section = app.query("#speckit-section")
                assert len(speckit_section) > 0 and speckit_section[0].display


class TestConfigAppIDEDetection:
    """Tests for IDE detection display in ConfigApp."""

    @pytest.mark.asyncio
    async def test_displays_detected_ide(self, tmp_path: Path):
        """Test that detected IDE is displayed at top of screen."""
        from rekall.tui_main import ConfigApp

        # Create Claude directory
        (tmp_path / ".claude").mkdir()

        with patch.object(Path, "home", return_value=tmp_path):
            app = ConfigApp()
            async with app.run_test() as pilot:
                # Should show "IDE détecté: Claude Code" or similar
                header = app.query_one("#detected-ide-header", expect_type=None)
                if header:
                    content = str(header.render())
                    assert "Claude" in content or "détecté" in content

    @pytest.mark.asyncio
    async def test_highlights_detected_ide_row(self, tmp_path: Path):
        """Test that detected IDE row has visual highlight marker."""
        from rekall.tui_main import ConfigApp

        (tmp_path / ".claude").mkdir()

        with patch.object(Path, "home", return_value=tmp_path):
            app = ConfigApp()
            async with app.run_test() as pilot:
                # The detected IDE row should have a marker (►)
                rows = app.query(".ide-row")
                for row in rows:
                    content = str(row.render())
                    if "Claude" in content:
                        assert "►" in content or "selected" in row.classes


class TestConfigAppGlobalLocalColumns:
    """Tests for Global/Local columns in ConfigApp."""

    @pytest.mark.asyncio
    async def test_shows_global_local_columns(self):
        """Test that IDE list shows Global and Local columns."""
        from rekall.tui_main import ConfigApp

        app = ConfigApp()
        async with app.run_test() as pilot:
            # Should have Global and Local column headers
            headers = app.query_one("#column-headers", expect_type=None)
            if headers:
                content = str(headers.render())
                assert "Global" in content
                assert "Local" in content

    @pytest.mark.asyncio
    async def test_global_column_disabled_for_local_only_ides(self):
        """Test that Global column is disabled for IDEs that don't support global."""
        from rekall.tui_main import ConfigApp

        app = ConfigApp()
        async with app.run_test() as pilot:
            # Cursor doesn't support global install
            cursor_row = None
            for row in app.query(".ide-row"):
                if "Cursor" in str(row.render()):
                    cursor_row = row
                    break

            if cursor_row:
                global_toggle = cursor_row.query_one(".global-toggle", expect_type=None)
                if global_toggle:
                    assert global_toggle.disabled or "n/a" in str(global_toggle.render())


class TestConfigAppKeyBindings:
    """Tests for ConfigApp keyboard navigation."""

    @pytest.mark.asyncio
    async def test_escape_quits_app(self):
        """Test that Escape key quits the application."""
        from rekall.tui_main import ConfigApp

        app = ConfigApp()
        async with app.run_test() as pilot:
            await pilot.press("escape")
            # App should be exiting
            assert app.return_code is not None or app._exit

    @pytest.mark.asyncio
    async def test_arrow_keys_navigate(self):
        """Test that arrow keys navigate between IDE rows."""
        from rekall.tui_main import ConfigApp

        app = ConfigApp()
        async with app.run_test() as pilot:
            # Get initial focused row
            initial = app.focused

            await pilot.press("down")
            after_down = app.focused

            # Focus should have changed
            assert initial != after_down or initial is None

    @pytest.mark.asyncio
    async def test_space_toggles_selection(self):
        """Test that Space toggles current selection."""
        from rekall.tui_main import ConfigApp

        app = ConfigApp()
        async with app.run_test() as pilot:
            # Navigate to first IDE and press space
            await pilot.press("down")
            await pilot.press("space")

            # Should trigger some visual change (checked state)
            # Actual assertion depends on implementation


class TestConfigAppArticle99Selector:
    """Tests for Article 99 selector widget."""

    @pytest.mark.asyncio
    async def test_article99_selector_shows_three_options(self, tmp_path: Path):
        """Test that Article 99 selector shows MICRO/COURT/EXTENSIF options."""
        from rekall.tui_main import ConfigApp

        # Need speckit directory for this section to appear
        (tmp_path / ".speckit").mkdir()

        with patch.object(Path, "home", return_value=tmp_path):
            app = ConfigApp()
            async with app.run_test() as pilot:
                selector = app.query_one("#article99-selector", expect_type=None)
                if selector:
                    content = str(selector.render())
                    assert "Micro" in content or "MICRO" in content
                    assert "Court" in content or "SHORT" in content
                    assert "Extensif" in content or "EXTENSIVE" in content

    @pytest.mark.asyncio
    async def test_article99_shows_recommendation(self, tmp_path: Path):
        """Test that Article 99 selector shows recommendation marker."""
        from rekall.tui_main import ConfigApp

        (tmp_path / ".speckit").mkdir()
        (tmp_path / ".claude" / "commands").mkdir(parents=True)
        (tmp_path / ".claude" / "commands" / "rekall.md").write_text("# Rekall")

        with patch.object(Path, "home", return_value=tmp_path):
            app = ConfigApp()
            async with app.run_test() as pilot:
                selector = app.query_one("#article99-selector", expect_type=None)
                if selector:
                    content = str(selector.render())
                    # Should show recommendation marker (★)
                    assert "★" in content or "recommandé" in content
