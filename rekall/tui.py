"""Rekall TUI - Interactive Terminal User Interface using Textual."""

from __future__ import annotations

from typing import Optional, List, Callable
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.text import Text

from textual.app import App, ComposeResult
from textual.widgets import Static, ListItem, ListView, Footer, Header, DataTable, RichLog, Input, Markdown
from textual.containers import Container, Vertical, Horizontal, VerticalScroll
from textual.binding import Binding
from textual.reactive import reactive
from textual import events

from rekall import __version__
from rekall.config import get_config, set_config, Config
from rekall.db import Database
from rekall.models import Entry, VALID_TYPES, generate_ulid
from rekall.i18n import t, get_lang, set_lang, LANGUAGES, load_lang_preference

console = Console()


# =============================================================================
# Textual-based Menu App (cross-platform, clean alternate screen)
# =============================================================================


class MenuItem(ListItem):
    """A menu item with label and description."""

    def __init__(self, label: str, description: str, action_key: str) -> None:
        super().__init__()
        self.label = label
        self.description = description
        self.action_key = action_key

    def compose(self) -> ComposeResult:
        yield Static(f"{self.label:<15} [dim]{self.description}[/dim]")


class MenuListView(ListView):
    """Custom ListView that handles Enter and Escape."""

    BINDINGS = [
        Binding("enter", "select_item", "Select", show=False),
        Binding("escape", "cancel", "Back", show=True),
        Binding("q", "quit_app", "Quit", show=True),
    ]

    def action_cancel(self) -> None:
        """Handle Escape - go back or quit."""
        self.app.exit(result=None)

    def action_quit_app(self) -> None:
        """Handle Q - quit."""
        self.app.exit(result="__quit__")

    def action_select_item(self) -> None:
        """Handle Enter - select current item."""
        if self.highlighted_child is not None:
            item = self.highlighted_child
            if isinstance(item, MenuItem):
                self.app.exit(result=item.action_key)


class RekallMenuApp(App):
    """Textual app for Rekall main menu."""

    CSS = """
    Screen {
        background: $surface;
    }

    #left-notify {
        dock: bottom;
        width: auto;
        max-width: 60;
        height: auto;
        padding: 1 2;
        margin: 1 2;
        background: #2d4a3e;
        border: thick #3d6a5e;
        color: #7fcea0;
        text-style: bold;
        display: none;
        layer: notification;
    }

    #left-notify.visible {
        display: block;
    }

    #banner {
        height: auto;
        padding: 1 0;
        text-align: center;
    }

    #banner-text {
        text-align: left;
        width: 100%;
    }

    #subtitle {
        text-align: left;
        color: $text;
        margin-top: 0;
    }

    #quote {
        text-align: left;
        color: $text-muted;
        margin-bottom: 0;
    }

    ListView {
        height: auto;
        margin: 0 2;
        background: transparent;
    }

    ListItem {
        padding: 0 1;
    }

    ListItem:hover {
        background: $primary 20%;
    }

    ListView:focus > ListItem.--highlight {
        background: $primary 40%;
    }

    Footer {
        background: $surface-darken-1;
    }
    """

    BINDINGS = [
        Binding("q", "quit_app", "Quit"),
        Binding("escape", "cancel", "Back"),
    ]

    def __init__(self, menu_items: List[tuple], banner_lines: List[str], subtitle: str, quote: str):
        super().__init__()
        self.menu_items = menu_items
        self.banner_lines = banner_lines
        self.subtitle = subtitle
        self.quote = quote
        self.result = None

    def compose(self) -> ComposeResult:
        # Use Rich markup for gradient banner (get_banner() returns Rich markup)
        # We need to generate it inline since get_banner() is defined later
        deep_blue = (67, 103, 205)
        light_blue = (147, 181, 247)

        gradient_lines = []
        for line in self.banner_lines:
            content_start = len(line) - len(line.lstrip())
            content = line[content_start:]
            if not content:
                gradient_lines.append(line)
                continue

            result = line[:content_start]
            n = len(content)

            for i, char in enumerate(content):
                if char == ' ':
                    result += char
                    continue
                t_val = i / max(n - 1, 1)
                r = int(deep_blue[0] + (light_blue[0] - deep_blue[0]) * t_val)
                g = int(deep_blue[1] + (light_blue[1] - deep_blue[1]) * t_val)
                b = int(deep_blue[2] + (light_blue[2] - deep_blue[2]) * t_val)
                result += f"[bold rgb({r},{g},{b})]{char}[/]"

            gradient_lines.append(result)

        gradient_banner = "\n".join(gradient_lines)

        # Use same indentation as banner (8 spaces)
        indent = "        "
        yield Container(
            Static(gradient_banner, id="banner-text", markup=True),
            Static(f"{indent}[bold white]{self.subtitle}[/]", id="subtitle", markup=True),
            Static(f'{indent}[dim]"{self.quote}"[/]', id="quote", markup=True),
            id="banner"
        )

        yield MenuListView(
            *[MenuItem(label, desc, key) for key, label, desc in self.menu_items]
        )

        yield Static("", id="left-notify")
        yield Footer()

    def show_left_notify(self, message: str, timeout: float = 3.0) -> None:
        """Show a notification on the left side."""
        notify_widget = self.query_one("#left-notify", Static)
        notify_widget.update(message)
        notify_widget.add_class("visible")
        self.set_timer(timeout, lambda: notify_widget.remove_class("visible"))

    def action_help_quit(self) -> None:
        """Override Ctrl+C behavior to show left notification."""
        self.show_left_notify("Ctrl+Q pour quitter", 3.0)

    def action_quit_app(self) -> None:
        self.exit(result="__quit__")

    def action_cancel(self) -> None:
        self.exit(result=None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle item selection."""
        item = event.item
        if isinstance(item, MenuItem):
            self.exit(result=item.action_key)


class SimpleMenuApp(App):
    """Simple menu app for sub-menus (without banner)."""

    CSS = """
    Screen {
        background: $surface;
    }

    #left-notify {
        dock: bottom;
        width: auto;
        max-width: 60;
        height: auto;
        padding: 1 2;
        margin: 1 2;
        background: #2d4a3e;
        border: thick #3d6a5e;
        color: #7fcea0;
        text-style: bold;
        display: none;
        layer: notification;
    }

    #left-notify.visible {
        display: block;
    }

    #title {
        text-align: center;
        padding: 1;
        color: $primary;
        text-style: bold;
    }

    ListView {
        height: auto;
        margin: 1 2;
        background: transparent;
    }

    ListItem {
        padding: 0 1;
    }

    ListView:focus > ListItem.--highlight {
        background: $primary 40%;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Back", show=True),
        Binding("q", "cancel", "Back", show=False),
    ]

    def __init__(self, title: str, items: List[str]):
        super().__init__()
        self.title_text = title
        self.items = items
        self.result = None

    def compose(self) -> ComposeResult:
        if self.title_text:
            yield Static(self.title_text, id="title")

        # Build menu items, skipping separators
        menu_items = []
        for i, item in enumerate(self.items):
            if item.strip() and all(c in '─-═' for c in item.strip()):
                continue
            menu_items.append(MenuItem(item, "", str(i)))

        yield MenuListView(*menu_items)

        yield Static("", id="left-notify")
        yield Footer()

    def show_left_notify(self, message: str, timeout: float = 3.0) -> None:
        """Show a notification on the left side."""
        notify_widget = self.query_one("#left-notify", Static)
        notify_widget.update(message)
        notify_widget.add_class("visible")
        self.set_timer(timeout, lambda: notify_widget.remove_class("visible"))

    def action_help_quit(self) -> None:
        """Override Ctrl+C behavior to show left notification."""
        self.show_left_notify("Ctrl+Q pour quitter", 3.0)

    def action_cancel(self) -> None:
        self.exit(result=None)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        # Get the index directly from the ListView
        list_view = event.list_view
        idx = list_view.index
        if idx is not None:
            self.exit(result=int(idx) if not isinstance(idx, int) else idx)
        else:
            self.exit(result=None)


class BrowseApp(App):
    """Textual app for browsing entries with DataTable and detail panel."""

    CSS = """
    Screen {
        background: $surface;
    }

    #left-notify {
        dock: bottom;
        width: auto;
        max-width: 60;
        height: auto;
        padding: 1 2;
        margin: 1 2;
        background: #2d4a3e;
        border: thick #3d6a5e;
        color: #7fcea0;
        text-style: bold;
        display: none;
        layer: notification;
    }

    #left-notify.visible {
        display: block;
    }

    #browse-container {
        height: 100%;
    }

    #header-bar {
        height: 3;
        padding: 1 2;
        background: $primary-darken-2;
        text-align: center;
    }

    #entries-table {
        height: 1fr;
        min-height: 8;
        border: solid $primary;
        margin: 0 1;
    }

    DataTable {
        height: 100%;
    }

    DataTable > .datatable--cursor {
        background: $primary 40%;
    }

    DataTable:focus > .datatable--cursor {
        background: $primary 60%;
    }

    #search-bar {
        height: 3;
        margin: 0 1;
        display: none;
    }

    #search-bar.visible {
        display: block;
    }

    #search-input {
        width: 100%;
    }

    #detail-panel {
        height: 1fr;
        min-height: 10;
        border: solid $secondary;
        margin: 0 1 1 1;
        padding: 1 2;
        background: $surface-darken-1;
    }

    #detail-title {
        text-style: bold;
        color: $text;
    }

    #detail-meta {
        color: $text-muted;
        margin-top: 1;
    }

    #detail-content {
        color: $text;
        margin-top: 1;
        height: auto;
        overflow-y: auto;
    }

    Markdown {
        margin: 0;
        padding: 0;
    }

    MarkdownH1 {
        color: rgb(147,181,247);
        text-style: bold;
        margin: 0;
        padding: 0;
    }

    MarkdownH2 {
        color: rgb(127,161,227);
        text-style: bold;
        margin: 0;
        padding: 0;
    }

    MarkdownH3 {
        color: rgb(107,141,207);
        text-style: bold;
        margin: 0;
        padding: 0;
    }

    MarkdownFence {
        background: $surface-darken-2;
        margin: 1 0;
        padding: 1;
    }

    MarkdownBlockQuote {
        border-left: thick $primary;
        padding-left: 1;
        color: $text-muted;
    }

    Footer {
        background: $surface-darken-1;
    }
    """

    BINDINGS = [
        Binding("escape", "quit", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("enter", "select_entry", "View", show=True),
        Binding("e", "edit_entry", "Edit", show=True),
        Binding("d", "delete_entry", "Delete", show=True),
        Binding("slash", "search", "Search", show=True),
    ]

    def __init__(self, entries: list, db):
        super().__init__()
        self.all_entries = entries  # Keep original list
        self.entries = entries  # Current filtered list
        self.db = db
        self.selected_entry = entries[0] if entries else None
        self.result_action = None  # ("view"|"edit"|"delete", entry)
        self.search_mode = False
        self.current_query = ""

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"[bold]REKALL[/bold] - {t('menu.browse')} ({len(self.entries)} {t('browse.entries')})", id="header-bar"),
            Container(
                DataTable(id="entries-table"),
            ),
            Container(
                Input(placeholder=t("search.query"), id="search-input"),
                id="search-bar",
            ),
            VerticalScroll(
                Static("", id="detail-title"),
                Static("", id="detail-meta"),
                Markdown("", id="detail-content"),
                id="detail-panel",
            ),
            Footer(),
            id="browse-container",
        )
        yield Static("", id="left-notify")

    def show_left_notify(self, message: str, timeout: float = 3.0) -> None:
        """Show a notification on the left side."""
        notify_widget = self.query_one("#left-notify", Static)
        notify_widget.update(message)
        notify_widget.add_class("visible")
        self.set_timer(timeout, lambda: notify_widget.remove_class("visible"))

    def action_help_quit(self) -> None:
        """Override Ctrl+C behavior to show left notification."""
        self.show_left_notify("Ctrl+Q pour quitter", 3.0)

    def on_mount(self) -> None:
        """Populate the DataTable with entries."""
        table = self.query_one("#entries-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_column(t("browse.type"), width=10, key="type")
        table.add_column(t("add.project"), width=12, key="project")
        table.add_column(t("add.title"), width=40, key="title")
        table.add_column(t("browse.preview"), key="preview")

        # Add rows
        self._populate_table()

        # Update detail panel for first entry
        if self.entries:
            self._update_detail_panel(self.entries[0])

    def _get_content_preview(self, entry, max_len: int = 60) -> str:
        """Get content preview - shows context around search term if searching."""
        if not entry.content:
            return "—"

        content = entry.content.replace("\n", " ").strip()

        if self.current_query:
            # Find the search term and show context around it
            query_lower = self.current_query.lower()
            content_lower = content.lower()
            pos = content_lower.find(query_lower)

            if pos != -1:
                # Calculate window around the match
                start = max(0, pos - 20)
                end = min(len(content), pos + len(self.current_query) + 40)

                preview = content[start:end]
                if start > 0:
                    preview = "…" + preview
                if end < len(content):
                    preview = preview + "…"

                return preview

        # Default: show beginning of content
        if len(content) > max_len:
            return content[:max_len] + "…"
        return content

    def _populate_table(self) -> None:
        """Populate table rows with current entries."""
        table = self.query_one("#entries-table", DataTable)

        for i, entry in enumerate(self.entries):
            project = entry.project or "—"
            title = entry.title[:38] + "…" if len(entry.title) > 38 else entry.title
            preview = self._get_content_preview(entry)

            # Highlight search term in title and preview
            title = self._highlight_text(title)
            preview = self._highlight_text(preview)

            table.add_row(
                entry.type,
                project[:10] + "…" if len(project) > 10 else project,
                Text.from_markup(title),
                Text.from_markup(preview),
                key=str(i),
            )

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Update detail panel when row selection changes."""
        if event.row_key is not None:
            try:
                idx = int(event.row_key.value)
                if 0 <= idx < len(self.entries):
                    self.selected_entry = self.entries[idx]
                    self._update_detail_panel(self.selected_entry)
            except (ValueError, TypeError):
                pass

    def _update_detail_panel(self, entry) -> None:
        """Update the detail panel with entry information."""
        title_widget = self.query_one("#detail-title", Static)
        meta_widget = self.query_one("#detail-meta", Static)
        content_widget = self.query_one("#detail-content", Markdown)

        # Title with highlighting
        highlighted_title = self._highlight_text(entry.title)
        title_widget.update(f"[bold cyan]{highlighted_title}[/bold cyan]")

        # Meta info
        tags_str = ", ".join(entry.tags) if entry.tags else "—"
        meta_lines = [
            f"[dim]ID:[/dim] {entry.id}  "
            f"[dim]{t('browse.type')}:[/dim] {entry.type}  "
            f"[dim]{t('browse.status')}:[/dim] {entry.status}  "
            f"[dim]{t('browse.tags')}:[/dim] {tags_str}",
        ]
        meta_widget.update("\n".join(meta_lines))

        # Full content with markdown rendering and highlighting
        if entry.content:
            # For markdown, we highlight after render isn't possible
            # So we show raw content with markdown rendering
            content_widget.update(entry.content)
        else:
            content_widget.update(f"*{t('browse.no_content')}*")

    def action_quit(self) -> None:
        self.exit(result=None)

    def action_select_entry(self) -> None:
        """View selected entry details."""
        if self.selected_entry:
            self.exit(result=("view", self.selected_entry))

    def action_edit_entry(self) -> None:
        """Edit selected entry."""
        if self.selected_entry:
            self.exit(result=("edit", self.selected_entry))

    def action_delete_entry(self) -> None:
        """Delete selected entry."""
        if self.selected_entry:
            self.exit(result=("delete", self.selected_entry))

    def action_search(self) -> None:
        """Toggle search bar."""
        search_bar = self.query_one("#search-bar")
        search_input = self.query_one("#search-input", Input)

        if self.search_mode:
            # Hide search bar and reset
            search_bar.remove_class("visible")
            self.search_mode = False
            search_input.value = ""
            # Reset to all entries
            if self.current_query:
                self.current_query = ""
                self._refresh_table(self.all_entries)
            self.query_one("#entries-table", DataTable).focus()
        else:
            # Show search bar
            search_bar.add_class("visible")
            self.search_mode = True
            search_input.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search submission - close search bar."""
        self._close_search_bar()

    def _close_search_bar(self) -> None:
        """Close search bar and focus table."""
        search_bar = self.query_one("#search-bar")
        search_bar.remove_class("visible")
        self.search_mode = False
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        table = self.query_one("#entries-table", DataTable)
        table.focus()

    def on_key(self, event: events.Key) -> None:
        """Handle key events - arrow keys navigate table while keeping search open."""
        if self.search_mode and event.key in ("up", "down"):
            # Focus table for navigation but keep search bar visible
            table = self.query_one("#entries-table", DataTable)
            table.focus()
            if event.key == "up":
                table.action_cursor_up()
            else:
                table.action_cursor_down()
            event.prevent_default()
            event.stop()
        elif event.key == "escape":
            # First Escape: if search active, clear it and reset results
            if self.current_query:
                self.current_query = ""
                self._refresh_table(self.all_entries)
                self._update_header()
                self._close_search_bar()
                event.prevent_default()
                event.stop()
            # Second Escape (no search): quit handled by default action_quit

    def on_input_changed(self, event: Input.Changed) -> None:
        """Live search as user types."""
        query = event.value.strip()

        if not query:
            # Reset to all entries
            self.current_query = ""
            self.entries = self.all_entries
            self._refresh_table(self.entries)
            self._update_header()
            return

        # Update current query for highlighting
        self.current_query = query

        # Filter entries locally for instant feedback
        query_lower = query.lower()
        filtered = [
            e for e in self.all_entries
            if query_lower in e.title.lower() or (e.content and query_lower in e.content.lower())
        ]
        self.entries = filtered if filtered else self.all_entries
        self._refresh_table(self.entries)
        self._update_header(f"{len(filtered)} {t('search.results_found')}" if filtered else t('search.no_results'))

    def _update_header(self, suffix: str = None) -> None:
        """Update header bar text."""
        header = self.query_one("#header-bar", Static)
        base = f"[bold]REKALL[/bold] - {t('menu.browse')} ({len(self.entries)} {t('browse.entries')})"
        if suffix:
            header.update(f"{base} - {suffix}")
        else:
            header.update(base)

    def _refresh_table(self, entries: list) -> None:
        """Refresh the DataTable with new entries."""
        self.entries = entries
        table = self.query_one("#entries-table", DataTable)
        table.clear()

        # Re-populate with current entries and search context
        self._populate_table()

        # Update selected entry
        if entries:
            self.selected_entry = entries[0]
            self._update_detail_panel(entries[0])
        else:
            self.selected_entry = None

    def _highlight_text(self, text: str) -> str:
        """Highlight search query in text using Rich markup."""
        if not self.current_query or not text:
            return text

        import re
        query = self.current_query
        # Case-insensitive replacement with highlight
        pattern = re.compile(re.escape(query), re.IGNORECASE)

        def replacer(match):
            return f"[bold rgb(147,181,247)]{match.group(0)}[/]"

        return pattern.sub(replacer, text)


class ResearchApp(App):
    """Textual app for browsing research files with DataTable and detail panel."""

    CSS = """
    Screen {
        background: $surface;
    }

    #left-notify {
        dock: bottom;
        width: auto;
        max-width: 60;
        height: auto;
        padding: 1 2;
        margin: 1 2;
        background: #2d4a3e;
        border: thick #3d6a5e;
        color: #7fcea0;
        text-style: bold;
        display: none;
        layer: notification;
    }

    #left-notify.visible {
        display: block;
    }

    #research-container {
        height: 100%;
    }

    #header-bar {
        height: 3;
        padding: 1 2;
        background: $primary-darken-2;
        text-align: center;
    }

    #files-table {
        height: auto;
        max-height: 50%;
        border: solid $primary;
        margin: 0 1;
    }

    DataTable > .datatable--cursor {
        background: $primary 40%;
    }

    DataTable:focus > .datatable--cursor {
        background: $primary 60%;
    }

    VerticalScroll {
        height: 1fr;
        border: solid $secondary;
        margin: 0 1 1 1;
        padding: 1 2;
        background: $surface-darken-1;
    }

    #content-panel {
        height: auto;
    }

    Markdown {
        margin: 0;
        padding: 0;
    }

    MarkdownH1 {
        color: rgb(147,181,247);
        text-style: bold;
        margin: 0;
        padding: 0;
    }

    MarkdownH2 {
        color: rgb(127,161,227);
        text-style: bold;
        margin: 0;
        padding: 0;
    }

    MarkdownH3 {
        color: rgb(107,141,207);
        text-style: bold;
        margin: 0;
        padding: 0;
    }

    MarkdownFence {
        background: $surface-darken-2;
        margin: 1 0;
        padding: 1;
    }

    MarkdownBlockQuote {
        border-left: thick $primary;
        padding-left: 1;
        color: $text-muted;
    }

    Footer {
        background: $surface-darken-1;
    }
    """

    BINDINGS = [
        Binding("escape", "quit", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, files: list):
        super().__init__()
        self.files = files  # List of Path objects
        self.selected_file = files[0] if files else None

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"[bold]REKALL[/bold] - {t('menu.research')} ({len(self.files)} {t('research.files')})", id="header-bar"),
            DataTable(id="files-table"),
            VerticalScroll(
                Markdown("", id="content-panel"),
            ),
            Footer(),
            id="research-container",
        )
        yield Static("", id="left-notify")

    def show_left_notify(self, message: str, timeout: float = 3.0) -> None:
        """Show a notification on the left side."""
        notify_widget = self.query_one("#left-notify", Static)
        notify_widget.update(message)
        notify_widget.add_class("visible")
        self.set_timer(timeout, lambda: notify_widget.remove_class("visible"))

    def action_help_quit(self) -> None:
        """Override Ctrl+C behavior to show left notification."""
        self.show_left_notify("Ctrl+Q pour quitter", 3.0)

    def on_mount(self) -> None:
        """Populate the DataTable with files."""
        table = self.query_one("#files-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_column(t("research.topic"), key="topic")

        # Add rows
        for i, file_path in enumerate(self.files):
            table.add_row(file_path.stem, key=str(i))

        # Show first file content
        if self.files:
            self._update_content_panel(self.files[0])

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Update content panel when row selection changes."""
        if event.row_key is not None:
            try:
                idx = int(event.row_key.value)
                if 0 <= idx < len(self.files):
                    self.selected_file = self.files[idx]
                    self._update_content_panel(self.selected_file)
            except (ValueError, TypeError):
                pass

    def _update_content_panel(self, file_path) -> None:
        """Update the content panel with file content (markdown rendered)."""
        content_widget = self.query_one("#content-panel", Markdown)
        try:
            content = file_path.read_text()
            content_widget.update(content)
        except Exception as e:
            content_widget.update(f"**Error:** {e}")

    def action_quit(self) -> None:
        self.exit(result=None)


class TerminalMenu:
    """Cross-platform terminal menu using Textual.

    Drop-in replacement for simple-term-menu's TerminalMenu.
    Uses Textual's alternate screen for clean exit (no scrollback pollution).
    Works on Windows, macOS, and Linux.
    """

    def __init__(
        self,
        entries: List[str],
        title: str = "",
        menu_cursor: str = "► ",
        menu_cursor_style: tuple = None,
        menu_highlight_style: tuple = None,
        **kwargs
    ):
        self.entries = entries
        self.title = title

    def show(self) -> Optional[int]:
        """Show the menu and return selected index, or None if cancelled."""
        if not self.entries:
            return None

        app = SimpleMenuApp(self.title, self.entries)
        result = app.run()

        # Ensure result is an int (or None)
        if result is not None and not isinstance(result, int):
            try:
                result = int(result)
            except (ValueError, TypeError):
                result = None
        return result


# ASCII Banner for Textual (plain text, colored by CSS)
# Each line colored with horizontal gradient
BANNER_LINES = [
    "        ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗",
    "        ██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║",
    "        ██████╔╝█████╗  █████╔╝ ███████║██║     ██║",
    "        ██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║",
    "        ██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗",
    "        ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝",
]


def _gradient_line(line: str, start_rgb: tuple, end_rgb: tuple) -> str:
    """Apply horizontal gradient to a line of text."""
    # Find content bounds (skip leading spaces)
    content_start = len(line) - len(line.lstrip())
    content = line[content_start:]
    if not content:
        return line

    result = line[:content_start]  # Keep leading spaces
    n = len(content)

    for i, char in enumerate(content):
        if char == ' ':
            result += char
            continue
        # Interpolate color
        t = i / max(n - 1, 1)
        r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * t)
        g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * t)
        b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * t)
        result += f"[bold rgb({r},{g},{b})]{char}[/]"

    return result


def get_banner() -> str:
    """Generate banner with gradient effect."""
    # Blue gradient: deep blue -> light blue
    deep_blue = (67, 103, 205)   # Similar to Gemini's left blue
    light_blue = (147, 181, 247) # Lighter blue (not white)

    lines = [_gradient_line(line, deep_blue, light_blue) for line in BANNER_LINES]
    banner = "\n".join(lines)

    subtitle = t("banner.subtitle")
    quote = t("banner.quote")
    return f"""
{banner}

[bold white]            {subtitle}[/bold white]
[dim]        {quote}[/dim]
"""

# Database instance
_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create database connection."""
    global _db
    if _db is None:
        config = get_config()
        _db = Database(config.db_path)
        _db.init()
    return _db


def clear_screen():
    """Clear terminal screen."""
    console.clear()


def show_banner():
    """Display the REKALL banner with gradient."""
    console.print(get_banner())
    console.print()


class ToastApp(App):
    """Mini app to display a toast notification and auto-close."""

    CSS = """
    Screen {
        background: transparent;
    }

    #toast-message {
        dock: bottom;
        width: auto;
        max-width: 80;
        height: auto;
        padding: 1 2;
        margin: 1 2;
        background: #2d4a3e;
        border: thick #3d6a5e;
        color: #7fcea0;
        text-style: bold;
    }
    """

    def __init__(self, message: str, duration: float = 1.5):
        super().__init__()
        self.message = message
        self.duration = duration

    def compose(self) -> ComposeResult:
        yield Static(self.message, id="toast-message")

    def on_mount(self) -> None:
        self.set_timer(self.duration, self.exit)


def show_toast(message: str, duration: float = 1.5):
    """Display a toast notification and auto-close."""
    app = ToastApp(message, duration)
    app.run()


def brief_pause(duration: float = 0.8):
    """Brief pause for auto-dismissing messages."""
    import time
    time.sleep(duration)


def press_enter_to_continue():
    """Wait for user to press Enter."""
    console.print()
    console.print(f"[dim]{t('common.press_enter')}[/dim]", end="")
    input()


class EscapePressed(Exception):
    """Raised when user presses Escape during input."""
    pass


def prompt_input(label: str, required: bool = True) -> Optional[str]:
    """Prompt user for text input. Returns None if Escape pressed."""
    from prompt_toolkit.shortcuts import PromptSession
    from prompt_toolkit.key_binding import KeyBindings

    bindings = KeyBindings()

    @bindings.add('escape', eager=True)
    def _(event):
        """Handle Escape key - eager=True for instant response."""
        event.app.exit(exception=EscapePressed())

    suffix = " (Esc=cancel)" if not required else ""
    try:
        session = PromptSession(key_bindings=bindings)
        # Set escape delay to 0 for instant response
        session.app.ttimeoutlen = 0.0
        session.app.timeoutlen = 0.0
        value = session.prompt(f"{label}{suffix}: ").strip()
        if required and not value:
            console.print("[red]This field is required.[/red]")
            return prompt_input(label, required)
        return value if value else None
    except EscapePressed:
        return None


# =============================================================================
# Menu Actions
# =============================================================================


def action_language():
    """Change interface language."""
    clear_screen()
    show_banner()

    console.print(f"[bold cyan]{t('language.title')}[/bold cyan]")
    console.print()
    console.print(f"[dim]{t('language.current')}: {LANGUAGES[get_lang()]}[/dim]")
    console.print()

    # Build language menu
    lang_entries = []
    lang_codes = list(LANGUAGES.keys())
    current_lang = get_lang()

    for code in lang_codes:
        name = LANGUAGES[code]
        marker = " ✓" if code == current_lang else ""
        lang_entries.append(f"{name}{marker}")

    lang_entries.append(f"← {t('common.back')}")

    menu = TerminalMenu(
        lang_entries,
        menu_cursor="► ",
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("fg_cyan",),
    )

    idx = menu.show()

    if idx is None or idx == len(lang_codes):
        # Back or Escape
        return

    # Set new language
    new_lang = lang_codes[idx]
    set_lang(new_lang)

    # Toast notification
    show_toast(f"✓ {t('language.changed')} {LANGUAGES[new_lang]}")


def action_install_ide():
    """Install IDE integration with status display and local/global choice."""
    from pathlib import Path
    from rekall.integrations import (
        get_available, get_ide_status, install, uninstall_ide,
        install_all_ide, uninstall_all_ide, supports_global
    )

    while True:
        clear_screen()
        show_banner()

        available = get_available()
        if not available:
            console.print(f"[yellow]{t('ide.not_supported')}[/yellow]")
            press_enter_to_continue()
            return

        # Get current status
        status = get_ide_status(Path.cwd())

        # Display status table
        console.print(f"[bold cyan]{t('ide.title')}[/bold cyan]")
        console.print()

        table = Table(box=box.ROUNDED, show_header=True)
        table.add_column("IDE/Agent", style="white", min_width=12)
        table.add_column(t("table.description"), min_width=20)
        table.add_column(t("table.local"), no_wrap=True, justify="center")
        table.add_column(t("table.global"), no_wrap=True, justify="center")

        # Filter out speckit (has its own menu)
        filtered = [(n, d, lt, gt) for n, d, lt, gt in available if n != "speckit"]

        local_installed = 0
        global_installed = 0
        local_not_installed = 0
        global_not_installed = 0

        for name, desc, local_target, global_target in filtered:
            st = status.get(name, {})

            # Local status
            if st.get("local"):
                local_str = "[green]✓[/green]"
                local_installed += 1
            else:
                local_str = "[red]✗[/red]"
                local_not_installed += 1

            # Global status
            if st.get("supports_global"):
                if st.get("global"):
                    global_str = "[green]✓[/green]"
                    global_installed += 1
                else:
                    global_str = "[red]✗[/red]"
                    global_not_installed += 1
            else:
                global_str = "[dim]—[/dim]"  # Not supported

            table.add_row(name, desc, local_str, global_str)

        console.print(table)
        console.print()
        console.print(f"[dim]✓ {t('ide.installed')}  ✗ {t('ide.not_installed')}  — {t('ide.not_supported')}[/dim]")
        console.print()
        console.print(f"[dim]{t('action.project')}: {Path.cwd()}[/dim]")
        console.print(f"[dim]Local: {local_installed} {t('ide.installed')} | Global: {global_installed} {t('ide.installed')}[/dim]")
        console.print()

        # Build menu options
        options = []
        actions = []

        # Bulk actions first
        if local_not_installed > 0:
            options.append(f"{t('ide.install_all_local')} ({local_not_installed} {t('ide.remaining')})")
            actions.append(("install_all", False))

        if global_not_installed > 0:
            options.append(f"{t('ide.install_all_global')} ({global_not_installed} {t('ide.remaining')})")
            actions.append(("install_all", True))

        if local_installed > 0:
            options.append(f"{t('ide.uninstall_all_local')} ({local_installed} {t('ide.installed')})")
            actions.append(("uninstall_all", False))

        if global_installed > 0:
            options.append(f"{t('ide.uninstall_all_global')} ({global_installed} {t('ide.installed')})")
            actions.append(("uninstall_all", True))

        options.append("─" * 40)
        actions.append((None, None))

        # Individual actions - one entry per integration
        for name, desc, local_target, global_target in filtered:
            st = status.get(name, {})
            has_local = st.get("local", False)
            has_global = st.get("global", False)
            can_global = st.get("supports_global", False)

            # Build status indicator (plain text - TerminalMenu doesn't support Rich tags)
            if has_local and has_global:
                status_indicator = "✓ L+G"
            elif has_local:
                status_indicator = "✓ L"
            elif has_global:
                status_indicator = "✓ G"
            else:
                status_indicator = "○"

            options.append(f"{name:<14} {status_indicator}")
            actions.append(("manage", name))

        options.append("─" * 40)
        actions.append((None, None))

        options.append(t("setup.back"))
        actions.append(("back", None))

        menu = TerminalMenu(
            options,
            title=f"{t('action.actions')}:",
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
            skip_empty_entries=True,
        )

        idx = menu.show()
        if idx is None:
            return

        action, param = actions[idx]

        if action == "back":
            return
        elif action == "manage":
            _manage_single_ide(param, status.get(param, {}))
        elif action == "install_all":
            global_install = param
            result = install_all_ide(Path.cwd(), global_install)
            loc = "GLOBAL" if global_install else "LOCAL"
            console.print(f"\n[green]✓[/green] Installation {loc} terminée:")
            if result["installed"]:
                console.print(f"  {t('ide.installed')}: {', '.join(result['installed'])}")
            if result.get("skipped_no_global"):
                console.print(f"  [dim]{t('ide.not_supported')}: {', '.join(result['skipped_no_global'])}[/dim]")
            if result["failed"]:
                console.print(f"  [red]{t('speckit.errors')}: {', '.join(result['failed'])}[/red]")
            press_enter_to_continue()
        elif action == "uninstall_all":
            global_install = param
            loc = "GLOBAL" if global_install else "LOCAL"
            confirm_menu = TerminalMenu(
                [t("ide.yes_uninstall", loc=loc), t("common.cancel")],
                title=t("ide.confirm_uninstall", loc=loc),
                menu_cursor="► ",
                menu_cursor_style=("fg_cyan", "bold"),
            )
            if confirm_menu.show() == 0:
                result = uninstall_all_ide(Path.cwd(), global_install)
                console.print(f"\n[green]✓[/green] {t('ide.uninstallation_complete')} {loc}:")
                if result["removed"]:
                    console.print(f"  {t('speckit.removed')}: {', '.join(result['removed'])}")
                if result["skipped"]:
                    console.print(f"  [dim]{t('ide.not_installed')}: {', '.join(result['skipped'])}[/dim]")
                press_enter_to_continue()


def _manage_single_ide(name: str, current_status: dict):
    """Manage a single IDE integration - install/uninstall local/global."""
    from pathlib import Path
    from rekall.integrations import (
        install, uninstall_ide, supports_global, get_ide_target_path
    )

    clear_screen()
    show_banner()

    has_local = current_status.get("local", False)
    has_global = current_status.get("global", False)
    can_global = current_status.get("supports_global", False)

    console.print(f"[bold cyan]{t('ide.manage')}: {name}[/bold cyan]")
    console.print()

    # Show current status
    table = Table(box=box.ROUNDED, show_header=True)
    table.add_column(t("ide.location"), min_width=10)
    table.add_column(t("ide.status"), min_width=15)
    table.add_column(t("ide.path"), style="dim")

    # Local row
    local_path = get_ide_target_path(name, Path.cwd(), False)
    if has_local:
        table.add_row("LOCAL", f"[green]✓ {t('ide.installed')}[/green]", str(local_path))
    else:
        table.add_row("LOCAL", f"[dim]○ {t('ide.not_installed')}[/dim]", str(local_path))

    # Global row (if supported)
    if can_global:
        global_path = get_ide_target_path(name, Path.cwd(), True)
        if has_global:
            table.add_row("GLOBAL", f"[green]✓ {t('ide.installed')}[/green]", str(global_path))
        else:
            table.add_row("GLOBAL", f"[dim]○ {t('ide.not_installed')}[/dim]", str(global_path))
    else:
        table.add_row("GLOBAL", f"[dim]— {t('ide.not_supported')}[/dim]", "")

    console.print(table)
    console.print()

    # Build action menu
    options = []
    actions = []

    # Install options
    if not has_local:
        options.append(t("ide.install_local"))
        actions.append(("install", False))

    if can_global and not has_global:
        options.append(t("ide.install_global"))
        actions.append(("install", True))

    # Uninstall options
    if has_local:
        options.append(t("ide.uninstall_local"))
        actions.append(("uninstall", False))

    if can_global and has_global:
        options.append(t("ide.uninstall_global"))
        actions.append(("uninstall", True))

    options.append("─" * 30)
    actions.append((None, None))

    options.append(t("action.back"))
    actions.append(("back", None))

    menu = TerminalMenu(
        options,
        title=f"{t('action.actions')}:",
        menu_cursor="► ",
        menu_cursor_style=("fg_cyan", "bold"),
        skip_empty_entries=True,
    )

    idx = menu.show()
    if idx is None:
        return

    action, global_install = actions[idx]

    if action == "back":
        return
    elif action == "install":
        target = install(name, Path.cwd(), global_install)
        loc = "GLOBAL" if global_install else "LOCAL"
        show_toast(f"✓ {name} installé ({loc})")
    elif action == "uninstall":
        loc = "GLOBAL" if global_install else "LOCAL"
        if uninstall_ide(name, Path.cwd(), global_install):
            show_toast(f"✓ {name} désinstallé ({loc})")
        else:
            show_toast(f"⚠ {name} n'était pas installé ({loc})")


def action_speckit_integration():
    """Manage Speckit integration with component selection."""
    from rekall.integrations import (
        get_speckit_status,
        get_speckit_preview,
        get_speckit_uninstall_preview,
        install_speckit_partial,
        uninstall_speckit_partial,
        SPECKIT_PATCHES,
    )

    # Component display names
    COMPONENT_LABELS = {
        "skill": "Skill rekall.speckit.md",
        "article": "Article XCIX (constitution)",
        "speckit.implement.md": "speckit.implement.md",
        "speckit.clarify.md": "speckit.clarify.md",
        "speckit.specify.md": "speckit.specify.md",
        "speckit.plan.md": "speckit.plan.md",
        "speckit.tasks.md": "speckit.tasks.md",
        "speckit.hotfix.md": "speckit.hotfix.md",
    }

    # All components in order
    ALL_COMPONENTS = ["skill", "article"] + list(SPECKIT_PATCHES.keys())

    while True:
        clear_screen()
        show_banner()

        # Get current status
        status = get_speckit_status()

        # Build status display
        console.print(f"[bold cyan]{t('speckit.title')}[/bold cyan]")
        console.print()

        # Status table
        table = Table(box=box.ROUNDED, show_header=True)
        table.add_column(t("speckit.component"), style="white", min_width=30)
        table.add_column(t("ide.status"), no_wrap=True)

        for comp in ALL_COMPONENTS:
            label = COMPONENT_LABELS.get(comp, comp)
            st = status.get(comp)
            if st is True:
                status_str = f"[green]✓ {t('ide.installed')}[/green]"
            elif st is False:
                status_str = f"[dim]○ {t('ide.not_installed')}[/dim]"
            else:  # None = file doesn't exist
                status_str = f"[yellow]⚠ {t('speckit.file_missing')}[/yellow]"
            table.add_row(label, status_str)

        console.print(table)
        console.print()

        # Main menu
        menu_options = [
            t("speckit.select_install"),
            t("speckit.select_uninstall"),
            t("speckit.install_all"),
            t("speckit.uninstall_all"),
            "─" * 35,
            t("setup.back"),
        ]

        menu = TerminalMenu(
            menu_options,
            title=f"{t('action.actions')}:",
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
            skip_empty_entries=True,
        )

        choice = menu.show()
        if choice is None or choice == 5:
            return

        if choice == 0:  # Select to install
            _speckit_select_and_action(status, ALL_COMPONENTS, COMPONENT_LABELS, "install")
        elif choice == 1:  # Select to uninstall
            _speckit_select_and_action(status, ALL_COMPONENTS, COMPONENT_LABELS, "uninstall")
        elif choice == 2:  # Install all
            _speckit_install_all(ALL_COMPONENTS)
        elif choice == 3:  # Uninstall all
            _speckit_uninstall_all(ALL_COMPONENTS)


def _speckit_select_and_action(status: dict, all_components: list, labels: dict, action: str):
    """Show multi-select menu for components, then preview and execute action."""
    from rekall.integrations import (
        get_speckit_preview,
        get_speckit_uninstall_preview,
        install_speckit_partial,
        uninstall_speckit_partial,
    )

    clear_screen()
    show_banner()

    # Filter available components based on action
    if action == "install":
        available = [c for c in all_components if status.get(c) is False]
        if not available:
            console.print(f"[yellow]{t('speckit.all_installed')}[/yellow]")
            brief_pause()
            return
        title_text = t("speckit.select_install").rstrip(".")
    else:  # uninstall
        available = [c for c in all_components if status.get(c) is True]
        if not available:
            console.print(f"[yellow]{t('speckit.none_installed')}[/yellow]")
            brief_pause()
            return
        title_text = t("speckit.select_uninstall").rstrip(".")

    # Build multi-select menu
    menu_entries = [t("speckit.all_select")] + [labels.get(c, c) for c in available]

    menu = TerminalMenu(
        menu_entries,
        title=f"{title_text} ({t('speckit.select_toggle')}):",
        menu_cursor="► ",
        menu_cursor_style=("fg_cyan", "bold"),
        multi_select=True,
        show_multi_select_hint=True,
        multi_select_select_on_accept=False,
        multi_select_empty_ok=False,
    )

    selected_indices = menu.show()
    if selected_indices is None:
        return

    # Handle "All" selection
    if isinstance(selected_indices, tuple):
        selected_indices = list(selected_indices)
    elif isinstance(selected_indices, int):
        selected_indices = [selected_indices]

    # Map indices to components (accounting for "All" at index 0)
    if 0 in selected_indices:
        selected_components = available  # All selected
    else:
        selected_components = [available[i - 1] for i in selected_indices if i > 0]

    if not selected_components:
        console.print(f"[yellow]{t('speckit.none_selected')}[/yellow]")
        brief_pause()
        return

    # Show preview
    clear_screen()
    show_banner()

    console.print(f"[bold]{t('speckit.preview')} - {action.upper()}[/bold]")
    console.print()

    if action == "install":
        previews = get_speckit_preview(selected_components)
    else:
        previews = get_speckit_uninstall_preview(selected_components)

    for comp in selected_components:
        preview = previews.get(comp, f"[?] {comp}")
        console.print(Panel(preview, title=labels.get(comp, comp), border_style="cyan"))
        console.print()

    # Confirm
    confirm_menu = TerminalMenu(
        [t("speckit.yes_action", action=action, count=len(selected_components)), t("common.cancel")],
        title=t("speckit.apply_changes"),
        menu_cursor="► ",
        menu_cursor_style=("fg_cyan", "bold"),
    )

    if confirm_menu.show() != 0:
        return

    # Execute
    try:
        if action == "install":
            result = install_speckit_partial(selected_components)
            console.print(f"\n[green]✓[/green] {t('ide.installation_complete')}!")
            if result["installed"]:
                console.print(f"  {t('ide.installed')}: {', '.join(result['installed'])}")
            if result["skipped"]:
                console.print(f"  [dim]{t('speckit.skipped')}: {', '.join(result['skipped'])}[/dim]")
        else:
            result = uninstall_speckit_partial(selected_components)
            console.print(f"\n[green]✓[/green] {t('ide.uninstallation_complete')}!")
            if result["removed"]:
                console.print(f"  {t('speckit.removed')}: {', '.join(result['removed'])}")
            if result["skipped"]:
                console.print(f"  [dim]{t('speckit.skipped')}: {', '.join(result['skipped'])}[/dim]")

        if result.get("errors"):
            console.print(f"  [red]{t('speckit.errors')}: {', '.join(result['errors'])}[/red]")

    except Exception as e:
        console.print(f"\n[red]✗ Error: {e}[/red]")

    press_enter_to_continue()


def _speckit_install_all(all_components: list):
    """Install all components with preview."""
    from rekall.integrations import get_speckit_preview, install_speckit_partial

    clear_screen()
    show_banner()

    console.print(f"[bold]{t('speckit.preview')} - {t('speckit.install_all').upper()}[/bold]")
    console.print()

    previews = get_speckit_preview(all_components)
    for comp, preview in previews.items():
        console.print(f"[cyan]{comp}:[/cyan] {preview.split(chr(10))[0]}")  # First line only

    console.print()

    confirm_menu = TerminalMenu(
        [t("speckit.yes_install_all"), t("common.cancel")],
        title=t("speckit.apply_changes"),
        menu_cursor="► ",
        menu_cursor_style=("fg_cyan", "bold"),
    )

    if confirm_menu.show() != 0:
        return

    try:
        result = install_speckit_partial(all_components)
        console.print(f"\n[green]✓[/green] {t('ide.installation_complete')}!")
        if result["installed"]:
            console.print(f"  {t('ide.installed')}: {', '.join(result['installed'])}")
        if result["skipped"]:
            console.print(f"  [dim]{t('speckit.skipped')}: {', '.join(result['skipped'])}[/dim]")
        if result["errors"]:
            console.print(f"  [red]{t('speckit.errors')}: {', '.join(result['errors'])}[/red]")
    except Exception as e:
        console.print(f"\n[red]✗ {t('common.error')}: {e}[/red]")

    press_enter_to_continue()


def _speckit_uninstall_all(all_components: list):
    """Uninstall all components with preview."""
    from rekall.integrations import get_speckit_uninstall_preview, uninstall_speckit_partial

    clear_screen()
    show_banner()

    console.print(f"[bold]{t('speckit.preview')} - {t('speckit.uninstall_all').upper()}[/bold]")
    console.print()

    previews = get_speckit_uninstall_preview(all_components)
    for comp, preview in previews.items():
        console.print(f"[cyan]{comp}:[/cyan] {preview.split(chr(10))[0]}")  # First line only

    console.print()
    console.print(f"[dim]{t('speckit.note_regex')}[/dim]")
    console.print()

    confirm_menu = TerminalMenu(
        [t("speckit.yes_uninstall_all"), t("common.cancel")],
        title=t("speckit.remove_integration"),
        menu_cursor="► ",
        menu_cursor_style=("fg_cyan", "bold"),
    )

    if confirm_menu.show() != 0:
        return

    try:
        result = uninstall_speckit_partial(all_components)
        console.print(f"\n[green]✓[/green] {t('ide.uninstallation_complete')}!")
        if result["removed"]:
            console.print(f"  {t('speckit.removed')}: {', '.join(result['removed'])}")
        if result["skipped"]:
            console.print(f"  [dim]{t('speckit.skipped')}: {', '.join(result['skipped'])}[/dim]")
        if result["errors"]:
            console.print(f"  [red]{t('speckit.errors')}: {', '.join(result['errors'])}[/red]")
    except Exception as e:
        console.print(f"\n[red]✗ {t('common.error')}: {e}[/red]")

    press_enter_to_continue()


def action_research():
    """Browse research sources with DataTable and detail panel."""
    from pathlib import Path
    research_dir = Path(__file__).parent / "research"

    if not research_dir.exists():
        clear_screen()
        show_banner()
        console.print(f"[yellow]{t('research.no_files')}[/yellow]")
        brief_pause()
        return

    files = sorted(research_dir.glob("*.md"))
    if not files:
        clear_screen()
        show_banner()
        console.print(f"[yellow]{t('research.no_files')}[/yellow]")
        brief_pause()
        return

    # Run the Research app
    app = ResearchApp(files)
    app.run()


def action_add_entry():
    """Add a new knowledge entry."""
    clear_screen()
    show_banner()

    # Select type
    type_options = list(VALID_TYPES) + [t("setup.back")]
    menu = TerminalMenu(
        type_options,
        title=f"{t('add.type')}:",
        menu_cursor="► ",
        menu_cursor_style=("fg_cyan", "bold"),
    )

    idx = menu.show()
    if idx is None or idx == len(type_options) - 1:
        return

    entry_type = type_options[idx]
    console.print(f"[cyan]{t('add.type')}:[/cyan] {entry_type}\n")

    # Get title
    title = prompt_input(t("add.title"))
    if not title:
        return

    # Get tags
    tags_input = prompt_input(t("add.tags"), required=False)
    tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []

    # Get project
    project = prompt_input(t("add.project"), required=False)

    # Get confidence
    conf_options = ["1 - Very Low", "2 - Low", "3 - Medium", "4 - High", "5 - Very High"]
    conf_menu = TerminalMenu(
        conf_options,
        title=f"{t('add.confidence')}:",
        menu_cursor="► ",
        menu_cursor_style=("fg_cyan", "bold"),
    )
    conf_idx = conf_menu.show()
    confidence = (conf_idx + 1) if conf_idx is not None else 3

    # Create entry
    db = get_db()
    entry = Entry(
        id=generate_ulid(),
        title=title,
        type=entry_type,
        tags=tags,
        project=project,
        confidence=confidence,
    )
    db.add(entry)

    show_toast(f"✓ {t('add.success')}: {entry.id[:8]}... \"{title[:30]}{'...' if len(title) > 30 else ''}\"", 2.0)


def action_search():
    """Search knowledge base."""
    clear_screen()
    show_banner()

    query = prompt_input(t("search.query"))
    if not query:
        return

    db = get_db()
    results = db.search(query, limit=20)

    if not results:
        console.print(f"[yellow]{t('search.no_results')}[/yellow]")
        brief_pause()
        return

    # Display results
    table = Table(title=f"{t('search.results_for')}: {query}", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column(t("browse.type"), width=10)
    table.add_column(t("add.title"), min_width=30)

    for result in results:
        entry = result.entry
        table.add_row(entry.id[:12] + "...", entry.type, entry.title)

    console.print(table)
    press_enter_to_continue()


def action_browse():
    """Browse all entries with Textual DataTable and live detail preview."""
    db = get_db()
    entries = db.list_all(limit=100)

    if not entries:
        clear_screen()
        show_banner()
        console.print(f"[yellow]{t('browse.no_entries')}[/yellow]")
        brief_pause()
        return

    while True:
        # Run the browse app
        app = BrowseApp(entries, db)
        result = app.run()

        if result is None:
            # User pressed Escape or Q - exit browse
            return

        action, entry = result

        if action == "view":
            _show_entry_detail(entry)
            # Refresh entries after viewing (might have been edited)
            entries = db.list_all(limit=100)
            if not entries:
                clear_screen()
                show_banner()
                console.print(f"[yellow]{t('browse.no_entries')}[/yellow]")
                brief_pause()
                return
        elif action == "edit":
            clear_screen()
            show_banner()
            _edit_entry(entry)
            entries = db.list_all(limit=100)
            if not entries:
                return
        elif action == "delete":
            clear_screen()
            show_banner()
            if _delete_entry(entry):
                entries = db.list_all(limit=100)
                if not entries:
                    clear_screen()
                    show_banner()
                    console.print(f"[yellow]{t('browse.no_entries')}[/yellow]")
                    brief_pause()
                    return


def _show_entry_detail(entry):
    """Display entry details with navigation options."""
    while True:
        clear_screen()
        show_banner()

        # Display details
        console.print(Panel(f"[bold]{entry.title}[/bold]", border_style="cyan"))
        console.print()
        console.print(f"[cyan]{t('browse.id')}:[/cyan]         {entry.id}")
        console.print(f"[cyan]{t('browse.type')}:[/cyan]       {entry.type}")
        console.print(f"[cyan]{t('browse.status')}:[/cyan]     {entry.status}")
        console.print(f"[cyan]{t('browse.confidence')}:[/cyan] {'★' * entry.confidence}{'☆' * (5 - entry.confidence)}")
        if entry.tags:
            console.print(f"[cyan]{t('browse.tags')}:[/cyan]       {', '.join(entry.tags)}")
        if entry.project:
            console.print(f"[cyan]{t('add.project')}:[/cyan]    {entry.project}")
        console.print(f"[cyan]{t('browse.created')}:[/cyan]    {entry.created_at.strftime('%Y-%m-%d %H:%M')}")
        console.print(f"[cyan]{t('browse.updated')}:[/cyan]    {entry.updated_at.strftime('%Y-%m-%d %H:%M')}")

        if entry.content:
            console.print()
            console.print(f"[cyan]{t('browse.content')}:[/cyan]")
            console.print(Panel(entry.content, border_style="dim"))

        console.print()

        # Action menu
        action_options = [
            t("browse.back_to_list"),
            "─" * 20,
            t("browse.edit_entry"),
            t("browse.delete_entry"),
        ]
        action_menu = TerminalMenu(
            action_options,
            title=f"{t('action.actions')}:",
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
            skip_empty_entries=True,
        )

        action_idx = action_menu.show()

        if action_idx is None or action_idx == 0:
            return  # Back to list
        elif action_idx == 2:
            _edit_entry(entry)
            return  # Return to list after edit
        elif action_idx == 3:
            if _delete_entry(entry):
                return  # Return to list after delete


def _edit_entry(entry):
    """Edit an existing entry."""
    console.print(f"\n[cyan]{t('edit.title')}[/cyan]")
    console.print(f"[dim]({t('edit.keep_current')})[/dim]\n")

    # Edit title
    new_title = prompt_input(f"{t('add.title')} [{entry.title}]")
    if new_title:
        entry.title = new_title

    # Edit content
    console.print(f"[dim]{t('edit.current_content')}: {entry.content[:100]}{'...' if len(entry.content or '') > 100 else ''}[/dim]")
    new_content = prompt_input(t("edit.new_content"))
    if new_content:
        entry.content = new_content

    # Edit project
    new_project = prompt_input(f"{t('add.project')} [{entry.project or t('edit.none')}]")
    if new_project:
        entry.project = new_project if new_project != "-" else None

    # Edit tags
    current_tags = ", ".join(entry.tags) if entry.tags else t("edit.none")
    new_tags = prompt_input(f"{t('browse.tags')} [{current_tags}]")
    if new_tags:
        entry.tags = [t.strip() for t in new_tags.split(",") if t.strip()]

    # Save
    db = get_db()
    db.update(entry)
    show_toast(f"✓ {t('browse.updated')}")


def _delete_entry(entry) -> bool:
    """Delete an entry with confirmation. Returns True if deleted."""
    confirm_menu = TerminalMenu(
        [t("common.no"), t("common.yes")],
        title=t("browse.confirm_delete", title=entry.title),
        menu_cursor="► ",
        menu_cursor_style=("fg_red", "bold"),
    )

    if confirm_menu.show() == 1:
        db = get_db()
        db.delete(entry.id)
        show_toast(f"✓ {t('browse.deleted')}")
        return True
    return False


def action_show():
    """Show entry details by ID."""
    clear_screen()
    show_banner()

    entry_id = prompt_input(t("show.entry_id"))
    if not entry_id:
        return

    db = get_db()
    entry = db.get(entry_id)

    if not entry:
        console.print(f"[red]{t('show.not_found')}: {entry_id}[/red]")
        press_enter_to_continue()
        return

    # Display details
    console.print(Panel(f"[bold]{entry.title}[/bold]", border_style="cyan"))
    console.print(f"[cyan]{t('browse.id')}:[/cyan] {entry.id}")
    console.print(f"[cyan]{t('browse.type')}:[/cyan] {entry.type}")
    console.print(f"[cyan]{t('browse.status')}:[/cyan] {entry.status}")
    console.print(f"[cyan]{t('browse.confidence')}:[/cyan] {'★' * entry.confidence}{'☆' * (5 - entry.confidence)}")
    if entry.tags:
        console.print(f"[cyan]{t('browse.tags')}:[/cyan] {', '.join(entry.tags)}")
    if entry.project:
        console.print(f"[cyan]{t('add.project')}:[/cyan] {entry.project}")
    if entry.content:
        console.print(f"\n[cyan]{t('browse.content')}:[/cyan]\n{entry.content}")

    press_enter_to_continue()


def action_setup():
    """Setup / Configuration submenu - choose installation location."""
    from pathlib import Path
    from rekall.config import get_config
    from rekall.paths import PathResolver, PathSource, init_local_project

    while True:
        clear_screen()
        show_banner()

        config = get_config()

        # Detect current state
        local_rekall = Path.cwd() / ".rekall"
        local_db = local_rekall / "knowledge.db"
        has_local = local_rekall.exists()
        has_local_db = local_db.exists()

        resolver = PathResolver()
        global_paths = resolver._from_xdg()  # Get XDG paths directly
        global_db = global_paths.db_path if global_paths else Path.home() / ".local" / "share" / "rekall" / "knowledge.db"
        has_global_db = global_db.exists()

        # Show current config
        console.print(f"[bold cyan]{t('setup.title')}[/bold cyan]")
        console.print()
        console.print(f"[cyan]{t('setup.current_source')}:[/cyan] {config.paths.source.value}")
        console.print(f"[cyan]{t('setup.active_db')}:[/cyan] {config.db_path}")
        console.print()

        # Show status of both locations
        if has_global_db:
            console.print(f"[green]✓[/green] {t('setup.global_db')}: {global_db}")
        else:
            console.print(f"[dim]○ {t('setup.global_db')}: {global_db} ({t('setup.not_created')})[/dim]")

        if has_local_db:
            console.print(f"[green]✓[/green] {t('setup.local_db')}: {local_db}")
        elif has_local:
            console.print(f"[yellow]⚠[/yellow] .rekall/ exists but no DB: {local_rekall}")
        else:
            console.print(f"[dim]○ {t('setup.local_db')}: {local_rekall} ({t('setup.not_created')})[/dim]")
        console.print()

        # Build dynamic menu based on state
        submenu_options = []
        actions = []

        # Option 1: Global
        if has_global_db:
            submenu_options.append(t("setup.use_global"))
            actions.append(("use_global", None))
        else:
            submenu_options.append(t("setup.create_global"))
            actions.append(("create_global", None))

        # Option 2: Local
        if has_local_db:
            submenu_options.append(t("setup.use_local"))
            actions.append(("use_local", None))
        else:
            submenu_options.append(t("setup.create_local"))
            actions.append(("create_local", None))

        # Option 3: Migration (if both exist or one exists)
        if has_global_db and not has_local_db:
            submenu_options.append(t("setup.copy_global_to_local"))
            actions.append(("migrate_to_local", None))
        if has_local_db and not has_global_db:
            submenu_options.append(t("setup.copy_local_to_global"))
            actions.append(("migrate_to_global", None))

        submenu_options.append("─" * 35)
        actions.append((None, None))

        submenu_options.append(t("setup.show_config"))
        actions.append(("show_config", None))

        submenu_options.append("─" * 35)
        actions.append((None, None))

        submenu_options.append(t("setup.back"))
        actions.append(("back", None))

        menu = TerminalMenu(
            submenu_options,
            title="Actions:",
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
            skip_empty_entries=True,
        )

        idx = menu.show()
        if idx is None:
            return

        action, _ = actions[idx]

        if action == "back":
            return
        elif action == "use_global":
            show_toast(f"✓ Base globale déjà active")
        elif action == "use_local":
            show_toast(f"✓ Base locale déjà active")
        elif action == "create_global":
            _setup_global()
        elif action == "create_local":
            _setup_local()
        elif action == "migrate_to_local":
            _migrate_db(global_db, local_rekall / "knowledge.db", "GLOBAL → LOCAL")
        elif action == "migrate_to_global":
            _migrate_db(local_db, global_db, "LOCAL → GLOBAL")
        elif action == "show_config":
            _show_config_details()


def _migrate_db(source: Path, dest: Path, direction: str):
    """Copy database from source to destination."""
    import shutil

    clear_screen()
    show_banner()

    console.print(f"[bold]Migration {direction}[/bold]")
    console.print()
    console.print(f"[cyan]Source:[/cyan] {source}")
    console.print(f"[cyan]Destination:[/cyan] {dest}")
    console.print()

    if dest.exists():
        console.print("[yellow]⚠ La destination existe déjà ![/yellow]")
        confirm_menu = TerminalMenu(
            ["Écraser la destination", "Annuler"],
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
        )
        if confirm_menu.show() != 0:
            return
    else:
        confirm_menu = TerminalMenu(
            [f"Oui, copier la base", "Annuler"],
            title="Confirmer la copie ?",
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
        )
        if confirm_menu.show() != 0:
            return

    # Create destination directory if needed
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy database
    shutil.copy2(source, dest)

    console.print(f"\n[green]✓[/green] Base copiée: {dest}")

    # If migrating to local, also install commands
    if "LOCAL" in direction:
        _install_local_commands(dest.parent.parent)  # .rekall -> project root

    press_enter_to_continue()


def _setup_global():
    """Initialize global XDG database."""
    from rekall.paths import PathResolver
    from rekall.db import Database

    clear_screen()
    show_banner()

    # Resolve XDG paths
    resolver = PathResolver()
    paths = resolver.resolve()

    console.print("[bold]Installation Globale (XDG)[/bold]")
    console.print()
    console.print(f"[cyan]Config:[/cyan]  {paths.config_dir}")
    console.print(f"[cyan]Data:[/cyan]    {paths.data_dir}")
    console.print(f"[cyan]Cache:[/cyan]   {paths.cache_dir}")
    console.print(f"[cyan]DB:[/cyan]      {paths.db_path}")
    console.print()

    if paths.db_path.exists():
        console.print("[yellow]⚠ La base de données existe déjà.[/yellow]")
        console.print()

        confirm_menu = TerminalMenu(
            ["Ouvrir la base existante", "Annuler"],
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
        )
        if confirm_menu.show() != 0:
            return
    else:
        # Confirm creation
        confirm_menu = TerminalMenu(
            ["Oui, créer la base globale", "Annuler"],
            title="Créer la base de données ?",
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
        )
        if confirm_menu.show() != 0:
            return

        # Create directories
        paths.config_dir.mkdir(parents=True, exist_ok=True)
        paths.data_dir.mkdir(parents=True, exist_ok=True)
        paths.cache_dir.mkdir(parents=True, exist_ok=True)

    # Initialize DB
    db = Database(paths.db_path)
    db.init()
    db.close()

    show_toast(f"✓ Base globale initialisée", 2.0)


def _setup_local():
    """Initialize local project database."""
    from pathlib import Path
    from rekall.paths import init_local_project

    clear_screen()
    show_banner()

    cwd = Path.cwd()
    local_dir = cwd / ".rekall"

    console.print("[bold]Installation Locale (Projet)[/bold]")
    console.print()
    console.print(f"[cyan]Dossier:[/cyan]  {local_dir}")
    console.print(f"[cyan]DB:[/cyan]       {local_dir / 'knowledge.db'}")
    console.print()

    if local_dir.exists():
        console.print("[yellow]⚠ Le dossier .rekall/ existe déjà.[/yellow]")
        console.print()

        confirm_menu = TerminalMenu(
            ["Ouvrir la base existante", "Annuler"],
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
        )
        if confirm_menu.show() != 0:
            return
    else:
        console.print("[dim]Un fichier .gitignore sera créé avec des suggestions.[/dim]")
        console.print()

        # Ask about git versioning
        git_menu = TerminalMenu(
            [
                "Versionner la DB (partage équipe)",
                "Exclure la DB du Git (données locales)",
                "Annuler",
            ],
            title="Versionner la base dans Git ?",
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
        )

        git_choice = git_menu.show()
        if git_choice is None or git_choice == 2:
            return

        exclude_db = (git_choice == 1)

        # Create local project
        init_local_project(cwd, exclude_db_from_git=exclude_db)

        # Copy rekall.save.md command to local .claude/commands/
        _install_local_commands(cwd)

    show_toast(f"✓ Projet local initialisé", 2.0)


def _install_local_commands(project_path: Path):
    """Install rekall commands to project's .claude/commands/."""
    from pathlib import Path

    # Source: global command
    global_cmd = Path.home() / ".claude" / "commands" / "rekall.save.md"

    # Target: local project command
    local_cmd_dir = project_path / ".claude" / "commands"
    local_cmd = local_cmd_dir / "rekall.save.md"

    if not global_cmd.exists():
        console.print("[yellow]⚠ rekall.save.md global non trouvé, commande locale non installée.[/yellow]")
        return

    # Create directory if needed
    local_cmd_dir.mkdir(parents=True, exist_ok=True)

    # Copy command
    local_cmd.write_text(global_cmd.read_text())

    console.print(f"[green]✓[/green] Commande /rekall.save installée: {local_cmd}")


def _show_config_details():
    """Show detailed configuration."""
    from rekall.config import get_config
    import os

    clear_screen()
    show_banner()

    config = get_config()

    console.print("[bold]Configuration Détaillée[/bold]")
    console.print()

    table = Table(box=box.ROUNDED)
    table.add_column("Paramètre", style="cyan")
    table.add_column("Valeur")

    table.add_row("Source", config.paths.source.value)
    table.add_row("Config dir", str(config.paths.config_dir))
    table.add_row("Data dir", str(config.paths.data_dir))
    table.add_row("Cache dir", str(config.paths.cache_dir))
    table.add_row("DB path", str(config.paths.db_path))
    table.add_row("DB existe", "✓" if config.db_path.exists() else "✗")
    table.add_row("", "")
    table.add_row("REKALL_HOME", os.environ.get("REKALL_HOME", "(non défini)"))
    table.add_row("XDG_CONFIG_HOME", os.environ.get("XDG_CONFIG_HOME", "(non défini)"))
    table.add_row("XDG_DATA_HOME", os.environ.get("XDG_DATA_HOME", "(non défini)"))

    console.print(table)
    press_enter_to_continue()


def action_export_import():
    """Export / Import submenu."""
    while True:
        clear_screen()
        show_banner()

        submenu_options = [
            t("export.archive"),
            t("export.markdown"),
            t("export.json"),
            "─" * 30,
            t("import.archive"),
            t("import.external_db"),
            "─" * 30,
            t("setup.back"),
        ]
        menu = TerminalMenu(
            submenu_options,
            title="Export / Import:",
            menu_cursor="► ",
            menu_cursor_style=("fg_cyan", "bold"),
            skip_empty_entries=True,
        )

        idx = menu.show()
        if idx is None or idx == 7:  # Back or Escape
            return

        if idx == 0:
            _do_export_rekall()
        elif idx == 1:
            _do_export_text("md")
        elif idx == 2:
            _do_export_text("json")
        elif idx == 4:
            _do_import_rekall()
        elif idx == 5:
            _do_import_external_db()


def _do_export_rekall():
    """Export to .rekall.zip archive."""
    from pathlib import Path
    from rekall.archive import RekallArchive

    filename = prompt_input(t("import.filename"))
    if not filename:
        return

    db = get_db()
    entries = db.list_all(limit=100000)

    if not entries:
        console.print(f"[yellow]{t('import.no_entries')}[/yellow]")
        brief_pause()
        return

    output_path = Path(f"{filename}.rekall.zip")
    RekallArchive.create(output_path, entries)
    show_toast(f"✓ {t('import.exported', count=len(entries), path=output_path)}", 2.0)


def _do_export_text(fmt: str):
    """Export to text format (md or json)."""
    from pathlib import Path
    from rekall import exporters

    filename = prompt_input(t("import.output_filename", fmt=fmt))
    if not filename:
        return

    db = get_db()
    entries = db.list_all(limit=100000)

    if not entries:
        console.print(f"[yellow]{t('import.no_entries')}[/yellow]")
        brief_pause()
        return

    output_path = Path(f"{filename}.{fmt}")

    if fmt == "json":
        content = exporters.export_json(entries)
    else:
        content = exporters.export_markdown(entries)

    output_path.write_text(content)
    show_toast(f"✓ {t('import.exported', count=len(entries), path=output_path)}", 2.0)


def _do_import_rekall():
    """Import from .rekall.zip archive."""
    from pathlib import Path
    from rekall.archive import RekallArchive
    from rekall.sync import ImportExecutor, build_import_plan

    filepath = prompt_input(t("import.archive_path"))
    if not filepath:
        return

    archive_path = Path(filepath)
    if not archive_path.exists():
        console.print(f"[red]{t('import.file_not_found')}: {filepath}[/red]")
        press_enter_to_continue()
        return

    # Open and validate
    archive = RekallArchive.open(archive_path)
    if archive is None:
        console.print(f"[red]{t('import.invalid_archive')}: {filepath}[/red]")
        press_enter_to_continue()
        return

    validation = archive.validate()
    if not validation.valid:
        console.print(f"[red]{t('import.validation_failed')}:[/red]")
        for error in validation.errors:
            console.print(f"  - {error}")
        press_enter_to_continue()
        return

    # Show info
    manifest = archive.get_manifest()
    console.print(f"\n[cyan]{t('import.archive_info')}:[/cyan]")
    console.print(f"  {t('import.version')}: {manifest.format_version}")
    console.print(f"  {t('browse.created')}: {manifest.created_at.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"  {t('import.entries')}: {manifest.stats.entries_count}")
    console.print()

    # Build plan
    db = get_db()
    imported_entries = archive.get_entries()
    plan = build_import_plan(db, imported_entries)

    # Show preview
    executor = ImportExecutor(db)
    preview = executor.preview(plan)
    console.print(preview)
    console.print()

    if plan.total == 0:
        console.print(f"[yellow]{t('import.nothing_to_import')}[/yellow]")
        brief_pause()
        return

    # Choose strategy
    strategy_options = [
        t("import.skip_conflicts"),
        t("import.replace_conflicts"),
        t("import.merge_conflicts"),
        t("import.cancel"),
    ]
    strategy_menu = TerminalMenu(
        strategy_options,
        title=f"{t('import.conflict_strategy')}:",
        menu_cursor="► ",
        menu_cursor_style=("fg_cyan", "bold"),
    )

    strategy_idx = strategy_menu.show()
    if strategy_idx is None or strategy_idx == 3:
        return

    strategies = ["skip", "replace", "merge"]
    strategy = strategies[strategy_idx]

    # Configure backup
    backup_dir = db.db_path.parent / "backups"
    executor = ImportExecutor(db, backup_dir=backup_dir)

    # Execute
    result = executor.execute(plan, strategy=strategy)

    if result.success:
        console.print()
        console.print(f"[green]✓ {t('import.success')}[/green]")
        console.print(f"  {t('import.added')}: {result.added}")
        if result.replaced:
            console.print(f"  {t('import.replaced')}: {result.replaced}")
        if result.merged:
            console.print(f"  {t('import.merged')}: {result.merged}")
        console.print(f"  {t('import.skipped')}: {result.skipped}")
        if result.backup_path:
            console.print(f"  {t('import.backup')}: {result.backup_path}")
    else:
        console.print(f"[red]{t('import.failed')}:[/red]")
        for error in result.errors:
            console.print(f"  - {error}")

    press_enter_to_continue()


def _do_import_external_db():
    """Import from an external knowledge.db file."""
    from pathlib import Path
    from rekall.sync import (
        ImportExecutor, build_import_plan, load_entries_from_external_db
    )

    filepath = prompt_input(t("import.external_db_path"))
    if not filepath:
        return

    db_path = Path(filepath).expanduser()
    if not db_path.exists():
        console.print(f"[red]{t('import.file_not_found')}: {filepath}[/red]")
        press_enter_to_continue()
        return

    # Load entries from external DB
    try:
        imported_entries = load_entries_from_external_db(db_path)
    except ValueError as e:
        console.print(f"[red]{t('common.error')}: {e}[/red]")
        press_enter_to_continue()
        return

    if not imported_entries:
        console.print(f"[yellow]{t('import.no_entries_external')}[/yellow]")
        brief_pause()
        return

    # Show info
    console.print(f"\n[cyan]{t('import.external_db')}:[/cyan]")
    console.print(f"  {t('import.file')}: {db_path}")
    console.print(f"  {t('import.entries')}: {len(imported_entries)}")

    # Group by type
    types_count = {}
    for entry in imported_entries:
        types_count[entry.type] = types_count.get(entry.type, 0) + 1
    console.print(f"  {t('import.types')}: {', '.join(f'{tp}({c})' for tp, c in types_count.items())}")
    console.print()

    # Build plan
    db = get_db()
    plan = build_import_plan(db, imported_entries)

    # Show preview
    executor = ImportExecutor(db)
    preview = executor.preview(plan)
    console.print(preview)
    console.print()

    if plan.total == 0:
        console.print(f"[yellow]{t('import.nothing_to_import')}[/yellow]")
        brief_pause()
        return

    # Choose strategy
    strategy_options = [
        t("import.skip_conflicts"),
        t("import.replace_conflicts"),
        t("import.merge_conflicts"),
        t("import.cancel"),
    ]
    strategy_menu = TerminalMenu(
        strategy_options,
        title=f"{t('import.conflict_strategy')}:",
        menu_cursor="► ",
        menu_cursor_style=("fg_cyan", "bold"),
    )

    strategy_idx = strategy_menu.show()
    if strategy_idx is None or strategy_idx == 3:
        return

    strategies = ["skip", "replace", "merge"]
    strategy = strategies[strategy_idx]

    # Configure backup
    backup_dir = db.db_path.parent / "backups"
    executor = ImportExecutor(db, backup_dir=backup_dir)

    # Execute
    result = executor.execute(plan, strategy=strategy)

    if result.success:
        console.print()
        console.print(f"[green]✓ {t('import.success')}[/green]")
        console.print(f"  {t('import.added')}: {result.added}")
        if result.replaced:
            console.print(f"  {t('import.replaced')}: {result.replaced}")
        if result.merged:
            console.print(f"  {t('import.merged')}: {result.merged}")
        console.print(f"  {t('import.skipped')}: {result.skipped}")
        if result.backup_path:
            console.print(f"  {t('import.backup')}: {result.backup_path}")
    else:
        console.print(f"[red]{t('import.failed')}:[/red]")
        for error in result.errors:
            console.print(f"  - {error}")

    press_enter_to_continue()


# =============================================================================
# Main TUI Loop
# =============================================================================


# Map action keys to functions
ACTION_MAP = {
    "language": None,  # Will be set to action_language
    "setup": None,
    "install_ide": None,
    "speckit": None,
    "research": None,
    "add": None,
    "search": None,
    "browse": None,
    "show": None,
    "export": None,
    "quit": None,
}


def get_menu_items():
    """Build menu items for RekallMenuApp."""
    return [
        ("language", t("menu.language"), t("menu.language.desc")),
        ("setup", t("menu.setup"), t("menu.setup.desc")),
        ("install_ide", t("menu.install_ide"), t("menu.install_ide.desc")),
        ("speckit", t("menu.speckit"), t("menu.speckit.desc")),
        ("research", t("menu.research"), t("menu.research.desc")),
        ("add", t("menu.add"), t("menu.add.desc")),
        ("browse", t("menu.browse"), t("menu.browse.desc")),
        ("show", t("menu.show"), t("menu.show.desc")),
        ("export", t("menu.export"), t("menu.export.desc")),
        ("quit", t("menu.quit"), t("menu.quit.desc")),
    ]


def run_tui():
    """Run the interactive TUI using Textual."""
    # Load saved language preference
    load_lang_preference()

    # Map action keys to functions
    actions = {
        "language": action_language,
        "setup": action_setup,
        "install_ide": action_install_ide,
        "speckit": action_speckit_integration,
        "research": action_research,
        "add": action_add_entry,
        "browse": action_browse,
        "show": action_show,
        "export": action_export_import,
        "quit": None,
    }

    while True:
        # Build menu items fresh each loop (for language changes)
        menu_items = get_menu_items()

        # Create and run the Textual app
        app = RekallMenuApp(
            menu_items=menu_items,
            banner_lines=BANNER_LINES,
            subtitle=t("banner.subtitle"),
            quote=t("banner.quote"),
        )

        result = app.run()

        if result is None or result == "__quit__" or result == "quit":
            # Escape, Q, or Quit selected
            break

        # Execute the action
        action = actions.get(result)
        if action is not None:
            try:
                action()
            except KeyboardInterrupt:
                continue
            except Exception as e:
                console.print(f"\n[red]✗ {t('common.error')}: {e}[/red]")
                input("\nPress Enter to continue...")

    console.print(f"[dim]{t('common.goodbye')}[/dim]")


if __name__ == "__main__":
    run_tui()
