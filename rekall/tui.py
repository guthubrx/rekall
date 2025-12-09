"""Rekall TUI - Interactive Terminal User Interface using Textual."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.widgets import (
    DataTable,
    Footer,
    Input,
    ListItem,
    ListView,
    Markdown,
    SelectionList,
    Static,
)
from textual.widgets.selection_list import Selection

from rekall.config import get_config
from rekall.db import Database
from rekall.i18n import LANGUAGES, get_lang, load_lang_preference, set_lang, t
from rekall.models import VALID_TYPES, Entry, generate_ulid

console = Console()


# =============================================================================
# Textual-based Menu App (cross-platform, clean alternate screen)
# =============================================================================

# Banner ASCII art
BANNER_LINES = [
    "        ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗     ",
    "        ██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║     ",
    "        ██████╔╝█████╗  █████╔╝ ███████║██║     ██║     ",
    "        ██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║     ",
    "        ██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗",
    "        ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝",
]

BANNER_SUBTITLE = "Developer Knowledge Management System"
BANNER_QUOTE = "Get your ass to Mars. Quaid... crush those bugs"


def create_banner_container() -> Container:
    """Create the Rekall banner with gradient effect."""
    deep_blue = (67, 103, 205)
    light_blue = (147, 181, 247)

    gradient_lines = []
    for line in BANNER_LINES:
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
    indent = "        "

    return Container(
        Static(gradient_banner, id="banner-text", markup=True),
        Static(f"{indent}[bold white]{BANNER_SUBTITLE}[/]", id="subtitle", markup=True),
        Static(f'{indent}[dim]"{BANNER_QUOTE}"[/]', id="quote", markup=True),
        id="banner"
    )


# Theme colors (from banner gradient)
THEME_BLUE_DEEP = "#4367CD"    # rgb(67, 103, 205)
THEME_BLUE_LIGHT = "#93B5F7"   # rgb(147, 181, 247)

# Common CSS for banner and theme
BANNER_CSS = """
    #banner {
        height: auto;
        padding: 1 0;
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

    /* Theme: Use banner blue instead of yellow/warning */
    Footer {
        background: $surface-darken-1;
    }

    FooterKey {
        color: #93B5F7;
        background: transparent;
    }

    .footer-key--key {
        color: #4367CD;
        background: rgba(147, 181, 247, 0.2);
    }

    .footer-key--description {
        color: #93B5F7;
    }
"""


class MenuItem(ListItem):
    """A menu item with label and description."""

    def __init__(self, label: str, description: str, action_key: str, label_width: int = 15) -> None:
        super().__init__()
        self.label = label
        self.description = description
        self.action_key = action_key
        self.label_width = label_width

    def compose(self) -> ComposeResult:
        yield Static(f"{self.label:<{self.label_width}} [dim]{self.description}[/dim]")


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
                # Convert action_key to int for index-based results
                try:
                    self.app.exit(result=int(item.action_key))
                except ValueError:
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
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
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

    FooterKey {
        color: #93B5F7;
        background: transparent;
    }

    .footer-key--key {
        color: #4367CD;
        background: rgba(147, 181, 247, 0.2);
    }

    .footer-key--description {
        color: #93B5F7;
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

        # Calculate max label width for alignment
        max_label_width = max(len(label) for _, label, _ in self.menu_items) + 2

        yield MenuListView(
            *[MenuItem(label, desc, key, max_label_width) for key, label, desc in self.menu_items]
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
    """Simple menu app for sub-menus with banner."""

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
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
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
    """ + BANNER_CSS

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
        yield create_banner_container()

        if self.title_text:
            yield Static(self.title_text, id="title")

        # Build menu items, skipping separators
        menu_items = []
        valid_items = []
        for i, item in enumerate(self.items):
            if item.strip() and all(c in '─-═' for c in item.strip()):
                continue
            valid_items.append((i, item))

        # Calculate max label width for alignment
        max_label_width = max(len(item) for _, item in valid_items) + 2 if valid_items else 15

        for i, item in valid_items:
            menu_items.append(MenuItem(item, "", str(i), max_label_width))

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


class MultiSelectApp(App):
    """Multi-select menu app using SelectionList with banner."""

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
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
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

    #hint {
        text-align: center;
        padding: 0 1;
        color: $text-muted;
    }

    SelectionList {
        height: auto;
        max-height: 15;
        margin: 1 2;
        background: transparent;
        border: solid $primary;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "cancel", "Back", show=True),
        Binding("enter", "confirm", "Confirm", show=True),
    ]

    def __init__(self, title: str, items: List[tuple], hint: str = ""):
        """
        Args:
            title: Menu title
            items: List of (value, label) tuples
            hint: Optional hint text
        """
        super().__init__()
        self.title_text = title
        self.items = items  # [(value, label), ...]
        self.hint = hint
        self.result: Optional[List] = None

    def compose(self) -> ComposeResult:
        yield create_banner_container()

        if self.title_text:
            yield Static(self.title_text, id="title")

        if self.hint:
            yield Static(self.hint, id="hint")

        selections = [Selection(label, value, False) for value, label in self.items]
        yield SelectionList(*selections)

        yield Static("", id="left-notify")
        yield Footer()

    def show_left_notify(self, message: str, timeout: float = 3.0) -> None:
        """Show a notification on the left side."""
        notify_widget = self.query_one("#left-notify", Static)
        notify_widget.update(message)
        notify_widget.add_class("visible")
        self.set_timer(timeout, lambda: notify_widget.remove_class("visible"))

    def action_cancel(self) -> None:
        self.exit(result=None)

    def action_confirm(self) -> None:
        selection_list = self.query_one(SelectionList)
        selected = list(selection_list.selected)
        self.exit(result=selected if selected else None)


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
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
        text-style: bold;
        display: none;
        layer: notification;
    }

    #left-notify.visible {
        display: block;
    }

    #legend-modal {
        display: none;
        layer: modal;
        align: center middle;
        width: 70;
        height: auto;
        max-height: 85%;
        padding: 1 2;
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
    }

    #legend-modal.visible {
        display: block;
    }

    #legend-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    #legend-content {
        color: $text;
    }

    #legend-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    #graph-overlay {
        display: none;
        layer: modal;
        width: 100%;
        height: 100%;
        align: center middle;
        background: rgba(0, 0, 0, 0.5);
    }

    #graph-overlay.visible {
        display: block;
    }

    #graph-modal {
        width: 80;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
    }

    #graph-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    #graph-content {
        color: $text;
    }

    #graph-scroll {
        height: auto;
        max-height: 20;
    }

    #graph-hint {
        text-align: center;
        color: $text-muted;
        margin-top: 1;
    }

    #browse-container {
        height: 100%;
    }

    #section-title {
        padding: 0 2;
        margin-bottom: 1;
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
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "quit_or_close", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("enter", "select_entry", "View", show=True),
        Binding("e", "edit_entry", "Edit", show=True),
        Binding("d", "delete_entry", "Delete", show=True),
        Binding("slash", "search", "Search", show=True),
        Binding("question_mark", "toggle_legend", "?", show=True),
        Binding("space", "toggle_graph", "Graph", show=True),
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
        yield create_banner_container()
        yield Static(f"[dim]{t('menu.browse')} ({len(self.entries)} {t('browse.entries')})[/dim]", id="section-title")
        yield Container(
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
        # Legend modal (hidden by default)
        yield Container(
            Static(t("browse.legend_title"), id="legend-title"),
            Static(t("browse.legend_content"), id="legend-content"),
            Static("[dim]? ou Esc pour fermer[/dim]", id="legend-hint"),
            id="legend-modal",
        )
        # Graph modal with centered overlay
        yield Container(
            Container(
                Static(t("browse.graph_title"), id="graph-title"),
                VerticalScroll(
                    Static("", id="graph-content"),
                    id="graph-scroll",
                ),
                Static("[dim]Espace ou Esc pour fermer • Clic sur ID pour naviguer[/dim]", id="graph-hint"),
                id="graph-modal",
            ),
            id="graph-overlay",
        )

    def show_left_notify(self, message: str, timeout: float = 3.0) -> None:
        """Show a notification on the left side."""
        notify_widget = self.query_one("#left-notify", Static)
        notify_widget.update(message)
        notify_widget.add_class("visible")
        self.set_timer(timeout, lambda: notify_widget.remove_class("visible"))

    def action_help_quit(self) -> None:
        """Override Ctrl+C behavior to show left notification."""
        self.show_left_notify("Ctrl+Q pour quitter", 3.0)

    def action_toggle_legend(self) -> None:
        """Toggle the legend modal visibility."""
        legend = self.query_one("#legend-modal", Container)
        legend.toggle_class("visible")

    def action_toggle_graph(self) -> None:
        """Toggle the graph modal visibility for selected entry."""
        graph_overlay = self.query_one("#graph-overlay", Container)

        if graph_overlay.has_class("visible"):
            graph_overlay.remove_class("visible")
        else:
            # Generate graph for selected entry
            if self.selected_entry:
                graph_output = self.db.render_graph_ascii(
                    self.selected_entry.id,
                    max_depth=2,
                    show_incoming=True,
                    show_outgoing=True,
                    make_clickable=True,
                )
                graph_content = self.query_one("#graph-content", Static)
                graph_content.update(graph_output)
                graph_overlay.add_class("visible")
            else:
                self.show_left_notify("Aucune entrée sélectionnée", 2.0)

    def action_quit_or_close(self) -> None:
        """Close modals if open, otherwise quit."""
        legend = self.query_one("#legend-modal", Container)
        graph_overlay = self.query_one("#graph-overlay", Container)

        if legend.has_class("visible"):
            legend.remove_class("visible")
        elif graph_overlay.has_class("visible"):
            graph_overlay.remove_class("visible")
        else:
            self.app.exit()

    def on_mount(self) -> None:
        """Populate the DataTable with entries."""
        table = self.query_one("#entries-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_column(t("browse.type"), width=10, key="type")
        table.add_column(t("add.project"), width=12, key="project")
        table.add_column(t("add.title"), width=50, key="title")
        table.add_column(t("browse.created"), width=18, key="created")
        table.add_column(t("browse.updated"), width=18, key="updated")
        table.add_column(t("add.confidence"), width=4, key="confidence")
        table.add_column(t("browse.access"), width=6, key="access")
        table.add_column(t("browse.score"), width=5, key="score")
        table.add_column(t("browse.links_in"), width=3, key="links_in")
        table.add_column(t("browse.links_out"), width=3, key="links_out")

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
            title = entry.title[:48] + "…" if len(entry.title) > 48 else entry.title

            # Highlight search term in title
            title = self._highlight_text(title)

            # Get link counts
            links_in, links_out = self.db.count_links_by_direction(entry.id)

            table.add_row(
                entry.type,
                project[:10] + "…" if len(project) > 10 else project,
                Text.from_markup(title),
                entry.created_at.strftime("%Y-%m-%d %H:%M"),
                entry.updated_at.strftime("%Y-%m-%d %H:%M"),
                str(entry.confidence),
                str(entry.access_count),
                f"{entry.consolidation_score:.2f}",
                str(links_in),
                str(links_out),
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

        # Meta info - comprehensive
        tags_str = ", ".join(entry.tags) if entry.tags else "—"
        project_str = entry.project or "—"
        created_str = entry.created_at.strftime("%Y-%m-%d %H:%M")
        updated_str = entry.updated_at.strftime("%Y-%m-%d %H:%M")

        # Get link counts
        links_in, links_out = self.db.count_links_by_direction(entry.id)

        # Consolidation score color
        score = entry.consolidation_score
        if score >= 0.7:
            score_color = "green"
        elif score >= 0.4:
            score_color = "yellow"
        else:
            score_color = "red"

        meta_lines = [
            f"[dim]ID:[/dim] {entry.id}",
            f"[dim]{t('browse.type')}:[/dim] {entry.type}  "
            f"[dim]{t('browse.status')}:[/dim] {entry.status}  "
            f"[dim]{t('add.project')}:[/dim] {project_str}  "
            f"[dim]Memory:[/dim] {entry.memory_type}",
            f"[dim]{t('browse.created')}:[/dim] {created_str}  "
            f"[dim]{t('browse.updated')}:[/dim] {updated_str}",
            f"[dim]{t('browse.tags')}:[/dim] {tags_str}",
            f"[dim]{t('add.confidence')}:[/dim] {entry.confidence}/5  "
            f"[dim]{t('browse.access')}:[/dim] {entry.access_count}  "
            f"[dim]{t('browse.score')}:[/dim] [{score_color}]{score:.2f}[/{score_color}]  "
            f"[dim]Links:[/dim] ←{links_in} →{links_out}",
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
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
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

    #section-title {
        padding: 0 2;
        margin-bottom: 1;
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
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "quit", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self, files: list):
        super().__init__()
        self.files = files  # List of Path objects
        self.selected_file = files[0] if files else None

    def compose(self) -> ComposeResult:
        yield create_banner_container()
        yield Static(f"[dim]{t('menu.research')} ({len(self.files)} {t('research.files')})[/dim]", id="section-title")
        yield Container(
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


class IDEStatusApp(App):
    """Textual app for IDE integration - select in table, action panel below."""

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
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
        text-style: bold;
        display: none;
        layer: notification;
    }

    #left-notify.visible {
        display: block;
    }

    #ide-container {
        height: auto;
    }

    #status-table {
        height: auto;
        border: solid $primary;
        margin: 0 1;
    }

    DataTable {
        height: auto;
    }

    DataTable > .datatable--cursor {
        background: $primary 40%;
    }

    DataTable:focus > .datatable--cursor {
        background: $primary 60%;
    }

    #legend {
        height: auto;
        padding: 0 2;
        color: $text-muted;
    }

    #action-panel {
        height: auto;
        max-height: 8;
        border: solid #4367CD;
        margin: 0 1;
        padding: 0 1;
        background: $surface-darken-1;
        display: none;
    }

    #action-panel.visible {
        display: block;
    }

    #action-title {
        text-style: bold;
        color: #93B5F7;
        padding: 0 1;
    }

    #action-panel ListView {
        height: auto;
        background: transparent;
    }

    #action-panel ListItem {
        padding: 0 1;
    }

    #action-panel ListView:focus > ListItem.--highlight {
        background: #4367CD 30%;
    }

    Footer {
        background: $surface-darken-1;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "back_or_quit", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("enter", "select_ide", "Select", show=True),
        Binding("l", "install_all_local", "All Local", show=True),
        Binding("g", "install_all_global", "All Global", show=True),
    ]

    def __init__(self, ide_data: list, status: dict, stats: dict):
        super().__init__()
        self.ide_data = ide_data  # [(name, desc, local_target, global_target), ...]
        self.status = status
        self.stats = stats
        self.result = None
        self.selected_ide = None  # Currently selected IDE name
        self.action_panel_visible = False

    def compose(self) -> ComposeResult:
        yield create_banner_container()
        stats_text = f"Local: {self.stats['local_installed']} ✓ / {self.stats['local_not_installed']} ✗ | Global: {self.stats['global_installed']} ✓ / {self.stats['global_not_installed']} ✗"
        yield Container(
            DataTable(id="status-table"),
            Static(f"[dim]✓ {t('ide.installed')}  ✗ {t('ide.not_installed')}  — {t('ide.not_supported')}  |  {stats_text}[/dim]", id="legend"),
            Container(
                Static("", id="action-title"),
                ListView(id="action-list"),
                id="action-panel",
            ),
            Footer(),
            id="ide-container",
        )
        yield Static("", id="left-notify")

    def on_mount(self) -> None:
        """Populate the DataTable with IDE status."""
        table = self.query_one("#status-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_column("IDE/Agent", width=14)
        table.add_column(t("table.description"), width=30)
        table.add_column("Local", width=8, key="local")
        table.add_column("Global", width=8, key="global")

        # Add rows with IDE name as key
        for name, desc, local_target, global_target in self.ide_data:
            st = self.status.get(name, {})

            # Local status
            if st.get("local"):
                local_str = "[green]✓[/green]"
            else:
                local_str = "[red]✗[/red]"

            # Global status
            if st.get("supports_global"):
                if st.get("global"):
                    global_str = "[green]✓[/green]"
                else:
                    global_str = "[red]✗[/red]"
            else:
                global_str = "[dim]—[/dim]"

            table.add_row(name, desc, local_str, global_str, key=name)

        # Focus on the table
        table.focus()

    def _show_action_panel(self, ide_name: str) -> None:
        """Show action panel for selected IDE."""
        self.selected_ide = ide_name
        st = self.status.get(ide_name, {})
        has_local = st.get("local", False)
        has_global = st.get("global", False)
        can_global = st.get("supports_global", False)

        # Update title
        title = self.query_one("#action-title", Static)
        title.update(f"► {ide_name}")

        # Build action options
        action_list = self.query_one("#action-list", ListView)
        action_list.clear()

        # Install/Uninstall Local
        if has_local:
            action_list.append(ListItem(Static(f"[red]✗[/red] {t('ide.uninstall')} Local"), id="uninstall_local"))
        else:
            action_list.append(ListItem(Static(f"[green]✓[/green] {t('ide.install')} Local"), id="install_local"))

        # Install/Uninstall Global (if supported)
        if can_global:
            if has_global:
                action_list.append(ListItem(Static(f"[red]✗[/red] {t('ide.uninstall')} Global"), id="uninstall_global"))
            else:
                action_list.append(ListItem(Static(f"[green]✓[/green] {t('ide.install')} Global"), id="install_global"))

        action_list.append(ListItem(Static(f"[dim]← {t('common.cancel')}[/dim]"), id="cancel"))

        # Show panel and focus
        panel = self.query_one("#action-panel")
        panel.add_class("visible")
        self.action_panel_visible = True
        action_list.focus()

    def _hide_action_panel(self) -> None:
        """Hide action panel and return to table."""
        panel = self.query_one("#action-panel")
        panel.remove_class("visible")
        self.action_panel_visible = False
        self.selected_ide = None
        self.query_one("#status-table", DataTable).focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle Enter on a row - show action panel."""
        if event.row_key:
            ide_name = str(event.row_key.value)
            self._show_action_panel(ide_name)

    def action_select_ide(self) -> None:
        """Handle Enter key - show action panel for selected IDE."""
        if self.action_panel_visible:
            return  # Already in action panel
        table = self.query_one("#status-table", DataTable)
        if table.cursor_row is not None:
            ide_name = self.ide_data[table.cursor_row][0]
            self._show_action_panel(ide_name)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle action selection from panel."""
        if not self.action_panel_visible or not self.selected_ide:
            return

        item = event.item
        if item.id == "cancel":
            self._hide_action_panel()
        elif item.id == "install_local":
            self.result = ("install", self.selected_ide, False)
            self.exit(result=self.result)
        elif item.id == "install_global":
            self.result = ("install", self.selected_ide, True)
            self.exit(result=self.result)
        elif item.id == "uninstall_local":
            self.result = ("uninstall", self.selected_ide, False)
            self.exit(result=self.result)
        elif item.id == "uninstall_global":
            self.result = ("uninstall", self.selected_ide, True)
            self.exit(result=self.result)

    def action_back_or_quit(self) -> None:
        """Escape - hide panel or quit."""
        if self.action_panel_visible:
            self._hide_action_panel()
        else:
            self.exit(result=None)

    def action_install_all_local(self) -> None:
        """Install all IDEs locally."""
        if self.action_panel_visible:
            return
        if self.stats['local_not_installed'] > 0:
            self.result = ("install_all", False)
            self.exit(result=self.result)
        else:
            self.show_left_notify("Tous déjà installés en local")

    def action_install_all_global(self) -> None:
        """Install all IDEs globally."""
        if self.action_panel_visible:
            return
        if self.stats['global_not_installed'] > 0:
            self.result = ("install_all", True)
            self.exit(result=self.result)
        else:
            self.show_left_notify("Tous déjà installés en global")

    def show_left_notify(self, message: str, timeout: float = 3.0) -> None:
        """Show a notification on the left side."""
        notify_widget = self.query_one("#left-notify", Static)
        notify_widget.update(message)
        notify_widget.add_class("visible")
        self.set_timer(timeout, lambda: notify_widget.remove_class("visible"))

    def action_help_quit(self) -> None:
        """Override Ctrl+C behavior to show left notification."""
        self.show_left_notify("Ctrl+Q pour quitter", 3.0)

    def action_quit(self) -> None:
        self.exit(result=None)


class SpeckitApp(App):
    """Textual app for Speckit integration - select in table, action panel below."""

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
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
        text-style: bold;
        display: none;
        layer: notification;
    }

    #left-notify.visible {
        display: block;
    }

    #speckit-container {
        height: 1fr;
    }

    #status-table {
        height: auto;
        border: solid $primary;
        margin: 0 1;
    }

    DataTable {
        height: auto;
    }

    DataTable > .datatable--cursor {
        background: $primary 40%;
    }

    DataTable:focus > .datatable--cursor {
        background: $primary 60%;
    }

    #legend {
        height: auto;
        padding: 0 2;
        color: $text-muted;
    }

    #action-panel {
        height: 1fr;
        border: solid #4367CD;
        margin: 0 1;
        padding: 0 1;
        background: $surface-darken-1;
        display: none;
    }

    #action-panel.visible {
        display: block;
    }

    #action-title {
        text-style: bold;
        color: #93B5F7;
        padding: 0 1;
    }

    #preview-box {
        height: 1fr;
        border: solid $primary-darken-2;
        margin: 0 1;
        padding: 0 1;
        background: $surface-darken-2;
    }

    #preview-box Markdown {
        margin: 0;
        padding: 0;
    }

    #preview-box MarkdownH1 {
        color: rgb(147,181,247);
        text-style: bold;
        margin: 0;
        padding: 0;
    }

    #preview-box MarkdownH2 {
        color: rgb(127,161,227);
        text-style: bold;
        margin: 0;
        padding: 0;
    }

    #preview-box MarkdownH3 {
        color: rgb(107,141,207);
        text-style: bold;
        margin: 0;
        padding: 0;
    }

    #preview-box MarkdownFence {
        background: $surface-darken-3;
        margin: 1 0;
        padding: 1;
    }

    #preview-box MarkdownBlockQuote {
        border-left: thick $primary;
        padding-left: 1;
        color: $text-muted;
    }

    #preview-box MarkdownTable {
        margin: 1 0;
        background: $surface-darken-1;
    }

    #preview-box MarkdownTHead {
        background: $primary 30%;
    }

    #preview-box MarkdownTH {
        color: #93B5F7;
        text-style: bold;
        padding: 0 1;
    }

    #preview-box MarkdownTD {
        padding: 0 1;
    }

    #preview-box MarkdownTBody MarkdownTR:even {
        background: $surface-darken-2;
    }

    #action-panel ListView {
        height: auto;
        background: transparent;
    }

    #action-panel ListItem {
        padding: 0 1;
    }

    #action-panel ListView:focus > ListItem.--highlight {
        background: #4367CD 30%;
    }

    Footer {
        background: $surface-darken-1;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "back_or_quit", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("enter", "select_component", "Select", show=True),
        Binding("i", "install_all", "Install All", show=True),
        Binding("u", "uninstall_all", "Uninstall All", show=True),
    ]

    def __init__(self, status: dict, components: list, labels: dict):
        super().__init__()
        self.status = status
        self.components = components
        self.labels = labels
        self.result = None
        self.selected_component = None  # Currently selected component key
        self.action_panel_visible = False
        # Compute stats
        self.stats = {
            "installed": sum(1 for c in components if status.get(c) is True),
            "not_installed": sum(1 for c in components if status.get(c) is False),
        }

    def compose(self) -> ComposeResult:
        yield create_banner_container()
        stats_text = f"{t('ide.installed')}: {self.stats['installed']} ✓ | {t('ide.not_installed')}: {self.stats['not_installed']} ✗"
        yield Container(
            DataTable(id="status-table"),
            Static(f"[dim]✓ {t('ide.installed')}  ✗ {t('ide.not_installed')}  ⚠ {t('speckit.file_missing')}  |  {stats_text}[/dim]", id="legend"),
            Container(
                Static("", id="action-title"),
                VerticalScroll(
                    Markdown("", id="preview-content"),
                    id="preview-box",
                ),
                ListView(id="action-list"),
                id="action-panel",
            ),
            Footer(),
            id="speckit-container",
        )
        yield Static("", id="left-notify")

    def on_mount(self) -> None:
        """Populate the DataTable with component status."""
        table = self.query_one("#status-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_column(t("speckit.component"), width=35)
        table.add_column(t("ide.status"), width=20)

        # Add rows with component key
        for comp in self.components:
            label = self.labels.get(comp, comp)
            st = self.status.get(comp)
            if st is True:
                status_str = "[green]✓[/green]"
            elif st is False:
                status_str = "[red]✗[/red]"
            else:
                status_str = "[yellow]⚠[/yellow]"
            table.add_row(label, status_str, key=comp)

        # Focus on the table
        table.focus()

    def _format_preview_as_markdown(self, preview_text: str) -> str:
        """Convert preview text to markdown format."""
        lines = preview_text.split("\n")
        md_lines = []

        for line in lines:
            # Skip header lines (already shown in action-title)
            if line.startswith("[NEW FILE]"):
                md_lines.append("*📄 Nouveau fichier*")
            elif line.startswith("[APPEND TO]"):
                md_lines.append("*📝 Ajout au fichier*")
            elif line.startswith("[PATCH]"):
                md_lines.append("*🔧 Patch du fichier*")
            elif line.startswith("[DELETE]"):
                md_lines.append("*🗑️ Suppression*")
            elif line.startswith("[REMOVE FROM]"):
                md_lines.append("*➖ Retrait du fichier*")
            elif line.startswith("[SKIP]"):
                md_lines.append(f"*⏭️ {line[6:].strip()}*")
            elif line.startswith("─"):
                # Separator line -> skip (just visual separator)
                pass
            elif line.startswith("[+]"):
                md_lines.append(f"**➕** {line[3:].strip()}")
            elif line.startswith("[-]"):
                md_lines.append(f"**➖** {line[3:].strip()}")
            elif line.startswith("(truncated"):
                md_lines.append(f"*{line}*")
            else:
                md_lines.append(line)

        return "\n".join(md_lines)

    async def _show_action_panel(self, component: str) -> None:
        """Show action panel for selected component with preview."""
        from rekall.integrations import get_speckit_preview, get_speckit_uninstall_preview

        self.selected_component = component
        st = self.status.get(component)
        label = self.labels.get(component, component)

        # Update title
        title = self.query_one("#action-title", Static)
        title.update(f"► {label}")

        # Load and display preview
        preview_widget = self.query_one("#preview-content", Markdown)
        if st is True:
            # Installed -> show uninstall preview
            previews = get_speckit_uninstall_preview([component])
            preview_text = previews.get(component, f"*{t('speckit.preview')}...*")
        elif st is False:
            # Not installed -> show install preview
            previews = get_speckit_preview([component])
            preview_text = previews.get(component, f"*{t('speckit.preview')}...*")
        else:
            preview_text = f"⚠ {t('speckit.file_missing')}"
        # Convert preview to markdown format
        preview_md = self._format_preview_as_markdown(preview_text)
        preview_widget.update(preview_md)

        # Build action options
        action_list = self.query_one("#action-list", ListView)
        await action_list.clear()

        if st is True:
            # Installed -> offer uninstall
            action_list.append(ListItem(Static(f"[red]✗[/red] {t('ide.uninstall')}"), id="uninstall"))
        elif st is False:
            # Not installed -> offer install
            action_list.append(ListItem(Static(f"[green]✓[/green] {t('ide.install')}"), id="install"))
        else:
            # File missing -> can't do anything
            action_list.append(ListItem(Static(f"[yellow]⚠ {t('speckit.file_missing')}[/yellow]"), id="missing"))

        action_list.append(ListItem(Static(f"[dim]← {t('common.cancel')}[/dim]"), id="cancel"))

        # Show panel and focus
        panel = self.query_one("#action-panel")
        panel.add_class("visible")
        self.action_panel_visible = True
        action_list.focus()

    def _hide_action_panel(self) -> None:
        """Hide action panel and return to table."""
        panel = self.query_one("#action-panel")
        panel.remove_class("visible")
        self.action_panel_visible = False
        self.selected_component = None
        self.query_one("#status-table", DataTable).focus()

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle Enter on a row - show/update action panel."""
        if event.row_key:
            component = str(event.row_key.value)
            await self._show_action_panel(component)

    async def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight (arrow keys) - update preview if panel visible."""
        if self.action_panel_visible and event.row_key:
            component = str(event.row_key.value)
            # Update preview for highlighted row without changing focus
            await self._update_preview_only(component)

    async def _update_preview_only(self, component: str) -> None:
        """Update preview content without changing focus or actions."""
        from rekall.integrations import get_speckit_preview, get_speckit_uninstall_preview

        st = self.status.get(component)
        label = self.labels.get(component, component)

        # Update title
        title = self.query_one("#action-title", Static)
        title.update(f"► {label}")

        # Load and display preview
        preview_widget = self.query_one("#preview-content", Markdown)
        if st is True:
            previews = get_speckit_uninstall_preview([component])
            preview_text = previews.get(component, f"*{t('speckit.preview')}...*")
        elif st is False:
            previews = get_speckit_preview([component])
            preview_text = previews.get(component, f"*{t('speckit.preview')}...*")
        else:
            preview_text = f"⚠ {t('speckit.file_missing')}"
        preview_md = self._format_preview_as_markdown(preview_text)
        preview_widget.update(preview_md)

        # Update selected component and rebuild actions
        self.selected_component = component
        action_list = self.query_one("#action-list", ListView)
        await action_list.clear()

        if st is True:
            action_list.append(ListItem(Static(f"[red]✗[/red] {t('ide.uninstall')}"), id="uninstall"))
        elif st is False:
            action_list.append(ListItem(Static(f"[green]✓[/green] {t('ide.install')}"), id="install"))
        else:
            action_list.append(ListItem(Static(f"[yellow]⚠ {t('speckit.file_missing')}[/yellow]"), id="missing"))

        action_list.append(ListItem(Static(f"[dim]← {t('common.cancel')}[/dim]"), id="cancel"))

    async def action_select_component(self) -> None:
        """Handle Enter key - show action panel for selected component."""
        if self.action_panel_visible:
            # Panel visible - focus on action list
            self.query_one("#action-list", ListView).focus()
            return
        table = self.query_one("#status-table", DataTable)
        if table.cursor_row is not None:
            component = self.components[table.cursor_row]
            await self._show_action_panel(component)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle action selection from panel - execute directly."""
        if not self.action_panel_visible or not self.selected_component:
            return

        item = event.item
        if item.id == "cancel":
            self._hide_action_panel()
        elif item.id == "missing":
            self.show_left_notify(t("speckit.file_missing"))
            self._hide_action_panel()
        elif item.id == "install":
            self._execute_action("install", self.selected_component)
        elif item.id == "uninstall":
            self._execute_action("uninstall", self.selected_component)

    def _execute_action(self, action: str, component: str) -> None:
        """Execute install/uninstall action and refresh table."""
        from rekall.integrations import (
            get_speckit_status,
            install_speckit_partial,
            uninstall_speckit_partial,
        )

        label = self.labels.get(component, component)

        try:
            if action == "install":
                result = install_speckit_partial([component])
                if result["installed"]:
                    self.show_left_notify(f"✓ {label} {t('ide.installed').lower()}")
                elif result["errors"]:
                    self.show_left_notify(f"✗ {result['errors'][0]}")
            else:
                result = uninstall_speckit_partial([component])
                if result["removed"]:
                    self.show_left_notify(f"✓ {label} {t('speckit.removed').lower()}")
                elif result["errors"]:
                    self.show_left_notify(f"✗ {result['errors'][0]}")

            # Refresh status and table
            self.status = get_speckit_status()
            self.stats = {
                "installed": sum(1 for c in self.components if self.status.get(c) is True),
                "not_installed": sum(1 for c in self.components if self.status.get(c) is False),
            }
            self._refresh_table()

        except Exception as e:
            self.show_left_notify(f"✗ {t('common.error')}: {e}")

        self._hide_action_panel()

    def _refresh_table(self) -> None:
        """Refresh the table with updated status."""
        table = self.query_one("#status-table", DataTable)
        table.clear()

        for comp in self.components:
            label = self.labels.get(comp, comp)
            st = self.status.get(comp)
            if st is True:
                status_str = "[green]✓[/green]"
            elif st is False:
                status_str = "[red]✗[/red]"
            else:
                status_str = "[yellow]⚠[/yellow]"
            table.add_row(label, status_str, key=comp)

        # Update legend
        stats_text = f"{t('ide.installed')}: {self.stats['installed']} ✓ | {t('ide.not_installed')}: {self.stats['not_installed']} ✗"
        legend = self.query_one("#legend", Static)
        legend.update(f"[dim]✓ {t('ide.installed')}  ✗ {t('ide.not_installed')}  ⚠ {t('speckit.file_missing')}  |  {stats_text}[/dim]")

    def action_back_or_quit(self) -> None:
        """Escape - hide panel or quit."""
        if self.action_panel_visible:
            self._hide_action_panel()
        else:
            self.exit(result=None)

    def action_install_all(self) -> None:
        """Install all components."""
        if self.action_panel_visible:
            return
        if self.stats['not_installed'] > 0:
            self.result = ("install_all",)
            self.exit(result=self.result)
        else:
            self.show_left_notify(t("speckit.all_installed"))

    def action_uninstall_all(self) -> None:
        """Uninstall all components."""
        if self.action_panel_visible:
            return
        if self.stats['installed'] > 0:
            self.result = ("uninstall_all",)
            self.exit(result=self.result)
        else:
            self.show_left_notify(t("speckit.none_installed"))

    def show_left_notify(self, message: str, timeout: float = 3.0) -> None:
        """Show a notification on the left side."""
        notify_widget = self.query_one("#left-notify", Static)
        notify_widget.update(message)
        notify_widget.add_class("visible")
        self.set_timer(timeout, lambda: notify_widget.remove_class("visible"))

    def action_quit(self) -> None:
        self.exit(result=None)


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
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
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


class InfoDisplayApp(App):
    """Simple app to display info with Escape/Enter/Q to exit."""

    CSS = """
    Screen {
        background: $surface;
    }

    #content {
        height: 1fr;
        padding: 1 2;
    }

    #footer-hint {
        dock: bottom;
        height: 1;
        padding: 0 2;
        color: $text-muted;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "quit", "Back", show=False),
        Binding("enter", "quit", "Continue", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    def __init__(self, content: str, title: str = ""):
        super().__init__()
        self.content_text = content
        self.title_text = title

    def compose(self) -> ComposeResult:
        yield create_banner_container()
        yield Static(self.content_text, id="content", markup=True)
        yield Static("[dim]Press Escape, Enter or Q to continue...[/dim]", id="footer-hint")

    def action_quit(self) -> None:
        self.exit()


def show_info(content: str, title: str = ""):
    """Display info screen with Escape/Enter/Q to exit."""
    app = InfoDisplayApp(content, title)
    app.run()


class EscapePressed(Exception):
    """Raised when user presses Escape during input."""
    pass


def prompt_input(label: str, required: bool = True) -> Optional[str]:
    """Prompt user for text input. Returns None if Escape pressed."""
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.shortcuts import PromptSession

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
    """Change interface language using Textual menu."""
    lang_codes = list(LANGUAGES.keys())
    current_lang = get_lang()

    # Build menu items with checkmark for current
    lang_entries = []
    for code in lang_codes:
        name = LANGUAGES[code]
        marker = " ✓" if code == current_lang else ""
        lang_entries.append(f"{name}{marker}")

    lang_entries.append(f"← {t('common.back')}")

    # Use SimpleMenuApp (Textual)
    title = f"{t('language.title')} ({t('language.current')}: {LANGUAGES[current_lang]})"
    app = SimpleMenuApp(title, lang_entries)
    idx = app.run()

    if idx is None or idx >= len(lang_codes):
        return

    # Set new language
    new_lang = lang_codes[idx]
    set_lang(new_lang)
    show_toast(f"✓ {t('language.changed')} {LANGUAGES[new_lang]}")


def action_install_ide():
    """Configuration & Maintenance - unified menu for setup, backup, restore, IDE."""
    while True:
        # Build submenu (no separators - they break index mapping)
        submenu_options = [
            t('maintenance.db_info'),
            t('menu.setup'),
            t('maintenance.create_backup'),
            t('maintenance.restore_backup'),
            t('ide.integrations'),
            f"← {t('setup.back')}",
        ]
        actions = ["db_info", "setup", "backup", "restore", "ide", "back"]

        app = SimpleMenuApp(t("menu.config"), submenu_options)
        idx = app.run()

        # SimpleMenuApp returns str or int depending on selection method
        if idx is None:
            return
        idx = int(idx) if isinstance(idx, str) else idx

        if idx >= len(actions) or actions[idx] == "back":
            return

        action = actions[idx]

        if action == "db_info":
            _show_db_info()
        elif action == "setup":
            _database_setup_submenu()
        elif action == "backup":
            _create_backup_tui()
        elif action == "restore":
            _restore_backup_tui()
        elif action == "ide":
            _ide_integration_submenu()


def _database_setup_submenu():
    """Database setup submenu (moved from action_setup)."""
    from pathlib import Path

    from rekall.config import get_config
    from rekall.paths import PathResolver

    while True:
        config = get_config()

        # Detect current state
        local_rekall = Path.cwd() / ".rekall"
        local_db = local_rekall / "knowledge.db"
        has_local = local_rekall.exists()
        has_local_db = local_db.exists()

        resolver = PathResolver()
        global_paths = resolver._from_xdg()
        global_db = global_paths.db_path if global_paths else Path.home() / ".local" / "share" / "rekall" / "knowledge.db"
        has_global_db = global_db.exists()

        # Build status info
        global_status = "[green]✓[/green]" if has_global_db else "[dim]○[/dim]"
        local_status = "[green]✓[/green]" if has_local_db else ("[yellow]⚠[/yellow]" if has_local else "[dim]○[/dim]")

        # Build title with status
        title = f"{t('setup.title')} | {t('setup.current_source')}: {config.paths.source.value}"

        # Build dynamic menu
        submenu_options = []
        actions = []

        if has_global_db:
            submenu_options.append(f"{global_status} {t('setup.use_global')}")
            actions.append("use_global")
        else:
            submenu_options.append(f"{global_status} {t('setup.create_global')}")
            actions.append("create_global")

        if has_local_db:
            submenu_options.append(f"{local_status} {t('setup.use_local')}")
            actions.append("use_local")
        else:
            submenu_options.append(f"{local_status} {t('setup.create_local')}")
            actions.append("create_local")

        if has_global_db and not has_local_db:
            submenu_options.append(t("setup.copy_global_to_local"))
            actions.append("migrate_to_local")
        if has_local_db and not has_global_db:
            submenu_options.append(t("setup.copy_local_to_global"))
            actions.append("migrate_to_global")

        submenu_options.append(t("setup.show_config"))
        actions.append("show_config")

        submenu_options.append(f"← {t('setup.back')}")
        actions.append("back")

        # Show menu using Textual
        app = SimpleMenuApp(title, submenu_options)
        idx = app.run()

        if idx is None:
            return
        idx = int(idx) if isinstance(idx, str) else idx

        if idx >= len(actions) or actions[idx] == "back":
            return

        action = actions[idx]
        if action == "use_global":
            show_toast("✓ Base globale déjà active")
        elif action == "use_local":
            show_toast("✓ Base locale déjà active")
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


def _show_db_info():
    """Display database information in TUI."""
    from rekall import __release_date__, __version__
    from rekall.backup import get_database_stats
    from rekall.config import get_config
    from rekall.db import CURRENT_SCHEMA_VERSION

    config = get_config()
    stats = get_database_stats(config.db_path)

    if stats is None:
        show_info(f"[yellow]{t('info.no_db')}[/yellow]\n\n{t('info.run_init')}")
        return

    schema_status = f"[green]{t('info.schema_current')}[/green]" if stats.is_current else f"[yellow]{t('info.schema_outdated')}[/yellow]"

    info_text = f"""[bold]{t('info.title')}[/bold]

[cyan]Rekall:[/cyan]    v{__version__} ({__release_date__})
[cyan]Database:[/cyan]  {stats.path}
[cyan]{t('info.schema')}:[/cyan]    v{stats.schema_version}/{CURRENT_SCHEMA_VERSION} {schema_status}
[cyan]{t('info.entries')}:[/cyan]   {stats.total_entries} ({stats.active_entries} {t('info.active')}, {stats.obsolete_entries} {t('info.obsolete')})
[cyan]{t('info.links')}:[/cyan]     {stats.links_count}
[cyan]{t('info.size')}:[/cyan]      {stats.file_size_human}
"""
    show_info(info_text)


def _create_backup_tui():
    """Create backup via TUI."""
    from rekall.backup import create_backup
    from rekall.config import get_config

    config = get_config()

    if not config.db_path.exists():
        show_toast(f"⚠ {t('backup.no_db')}")
        return

    try:
        backup_info = create_backup(config.db_path)
        show_toast(f"✓ {t('backup.created')}: {backup_info.path.name}", 3.0)
    except Exception as e:
        show_toast(f"⚠ {t('backup.error')}: {e}", 3.0)


def _restore_backup_tui():
    """Restore from backup via TUI with selection."""
    from rekall.backup import get_database_stats, list_backups, restore_backup
    from rekall.config import get_config

    config = get_config()
    backups = list_backups()

    if not backups:
        show_toast(f"⚠ {t('maintenance.no_backups')}")
        return

    # Build backup list for selection
    backup_options = []
    for b in backups[:10]:  # Limit to 10 most recent
        date_str = b.timestamp.strftime("%Y-%m-%d %H:%M")
        backup_options.append(f"{date_str}  ({b.size_human})")

    backup_options.append(f"← {t('setup.back')}")

    app = SimpleMenuApp(t("maintenance.select_backup"), backup_options)
    idx = app.run()

    # SimpleMenuApp returns str or int depending on selection method
    if idx is None:
        return
    idx = int(idx) if isinstance(idx, str) else idx

    if idx >= len(backups):
        return

    selected_backup = backups[idx]

    # Show backup info
    backup_stats = get_database_stats(selected_backup.path)
    if backup_stats:
        info_text = f"""[bold]{t('maintenance.confirm_restore')}[/bold]

[cyan]File:[/cyan]     {selected_backup.path.name}
[cyan]Date:[/cyan]     {selected_backup.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
[cyan]Size:[/cyan]     {selected_backup.size_human}
[cyan]Entries:[/cyan]  {backup_stats.total_entries}
[cyan]Links:[/cyan]    {backup_stats.links_count}
"""
        show_info(info_text)

    # Confirm
    confirm_options = [t("common.yes"), t("common.cancel")]
    confirm_app = SimpleMenuApp(t("maintenance.confirm_restore"), confirm_options)
    confirm_result = confirm_app.run()
    if confirm_result is None:
        return
    confirm_idx = int(confirm_result) if isinstance(confirm_result, str) else confirm_result
    if confirm_idx != 0:
        return

    try:
        show_toast(f"⏳ {t('restore.safety_backup')}", 1.0)
        success, safety = restore_backup(selected_backup.path, config.db_path)
        if success:
            msg = f"✓ {t('restore.success')}"
            if safety:
                msg += f"\n   Safety: {safety.path.name}"
            show_toast(msg, 3.0)
    except Exception as e:
        show_toast(f"⚠ {e}", 3.0)


def _ide_integration_submenu():
    """IDE integration submenu (original action_install_ide logic)."""
    from pathlib import Path

    from rekall.integrations import (
        get_available,
        get_ide_status,
        install,
        install_all_ide,
        uninstall_ide,
    )

    while True:
        available = get_available()
        if not available:
            show_toast(f"⚠ {t('ide.not_supported')}")
            return

        # Get current status
        status = get_ide_status(Path.cwd())

        # Filter out speckit (has its own menu)
        filtered = [(n, d, lt, gt) for n, d, lt, gt in available if n != "speckit"]

        # Calculate stats
        local_installed = 0
        global_installed = 0
        local_not_installed = 0
        global_not_installed = 0

        for name, desc, local_target, global_target in filtered:
            st = status.get(name, {})
            if st.get("local"):
                local_installed += 1
            else:
                local_not_installed += 1
            if st.get("supports_global"):
                if st.get("global"):
                    global_installed += 1
                else:
                    global_not_installed += 1

        stats = {
            "local_installed": local_installed,
            "global_installed": global_installed,
            "local_not_installed": local_not_installed,
            "global_not_installed": global_not_installed,
        }

        # Show IDEStatusApp - table with action panel below
        app = IDEStatusApp(filtered, status, stats)
        result = app.run()

        if result is None:
            return

        action = result[0]

        if action == "install":
            # Single IDE install: ("install", ide_name, global_bool)
            _, ide_name, global_install = result
            loc = "GLOBAL" if global_install else "LOCAL"
            install(ide_name, Path.cwd(), global_install)
            show_toast(f"✓ {ide_name} installé ({loc})")
        elif action == "uninstall":
            # Single IDE uninstall: ("uninstall", ide_name, global_bool)
            _, ide_name, global_install = result
            loc = "GLOBAL" if global_install else "LOCAL"
            if uninstall_ide(ide_name, Path.cwd(), global_install):
                show_toast(f"✓ {ide_name} désinstallé ({loc})")
            else:
                show_toast(f"⚠ {ide_name} n'était pas installé ({loc})")
        elif action == "install_all":
            # Bulk install: ("install_all", global_bool)
            global_install = result[1]
            loc = "GLOBAL" if global_install else "LOCAL"
            res = install_all_ide(Path.cwd(), global_install)
            installed_count = len(res.get("installed", []))
            show_toast(f"✓ Installation {loc}: {installed_count} IDE(s)", 2.0)


def action_speckit_integration():
    """Manage Speckit integration with component selection using Textual."""
    from rekall.integrations import (
        SPECKIT_PATCHES,
        get_speckit_status,
    )

    # Component display names
    COMPONENT_LABELS = {
        "article": "Article XCIX (constitution)",
        "speckit.implement.md": "speckit.implement.md",
        "speckit.clarify.md": "speckit.clarify.md",
        "speckit.specify.md": "speckit.specify.md",
        "speckit.plan.md": "speckit.plan.md",
        "speckit.tasks.md": "speckit.tasks.md",
        "speckit.hotfix.md": "speckit.hotfix.md",
    }

    # All components in order (skill is now installed via Claude Code IDE integration)
    ALL_COMPONENTS = ["article"] + list(SPECKIT_PATCHES.keys())

    while True:
        # Get current status
        status = get_speckit_status()

        # Show SpeckitApp with status table, preview, and action panel
        # Individual install/uninstall are executed directly in the app
        # Only install_all/uninstall_all exit the app for bulk operations
        app = SpeckitApp(status, ALL_COMPONENTS, COMPONENT_LABELS)
        result = app.run()

        if result is None:
            return

        # Handle bulk actions (individual actions are handled in-app)
        action = result[0]
        if action == "install_all":
            _speckit_install_all(ALL_COMPONENTS)
        elif action == "uninstall_all":
            _speckit_uninstall_all(ALL_COMPONENTS)


def _speckit_install_all(all_components: list):
    """Install all components with preview using Textual."""
    from rekall.integrations import get_speckit_preview, install_speckit_partial

    # Build preview text
    previews = get_speckit_preview(all_components)
    preview_lines = [f"[bold]{t('speckit.preview')} - {t('speckit.install_all').upper()}[/bold]", ""]
    for comp, preview in previews.items():
        preview_lines.append(f"[cyan]{comp}:[/cyan] {preview.split(chr(10))[0]}")
    show_info("\n".join(preview_lines))

    # Confirm
    confirm_options = [t("speckit.yes_install_all"), t("common.cancel")]
    app = SimpleMenuApp(t("speckit.apply_changes"), confirm_options)
    if app.run() != 0:
        return

    # Execute
    try:
        result = install_speckit_partial(all_components)
        result_lines = [f"[green]✓[/green] {t('ide.installation_complete')}!"]
        if result["installed"]:
            result_lines.append(f"  {t('ide.installed')}: {', '.join(result['installed'])}")
        if result["skipped"]:
            result_lines.append(f"  [dim]{t('speckit.skipped')}: {', '.join(result['skipped'])}[/dim]")
        if result["errors"]:
            result_lines.append(f"  [red]{t('speckit.errors')}: {', '.join(result['errors'])}[/red]")
        show_info("\n".join(result_lines))
    except Exception as e:
        show_info(f"[red]✗ {t('common.error')}: {e}[/red]")


def _speckit_uninstall_all(all_components: list):
    """Uninstall all components with preview using Textual."""
    from rekall.integrations import get_speckit_uninstall_preview, uninstall_speckit_partial

    # Build preview text
    previews = get_speckit_uninstall_preview(all_components)
    preview_lines = [f"[bold]{t('speckit.preview')} - {t('speckit.uninstall_all').upper()}[/bold]", ""]
    for comp, preview in previews.items():
        preview_lines.append(f"[cyan]{comp}:[/cyan] {preview.split(chr(10))[0]}")
    preview_lines.append("")
    preview_lines.append(f"[dim]{t('speckit.note_regex')}[/dim]")
    show_info("\n".join(preview_lines))

    # Confirm
    confirm_options = [t("speckit.yes_uninstall_all"), t("common.cancel")]
    app = SimpleMenuApp(t("speckit.remove_integration"), confirm_options)
    if app.run() != 0:
        return

    # Execute
    try:
        result = uninstall_speckit_partial(all_components)
        result_lines = [f"[green]✓[/green] {t('ide.uninstallation_complete')}!"]
        if result["removed"]:
            result_lines.append(f"  {t('speckit.removed')}: {', '.join(result['removed'])}")
        if result["skipped"]:
            result_lines.append(f"  [dim]{t('speckit.skipped')}: {', '.join(result['skipped'])}[/dim]")
        if result["errors"]:
            result_lines.append(f"  [red]{t('speckit.errors')}: {', '.join(result['errors'])}[/red]")
        show_info("\n".join(result_lines))
    except Exception as e:
        show_info(f"[red]✗ {t('common.error')}: {e}[/red]")


def action_research():
    """Browse research sources with DataTable and detail panel."""
    from pathlib import Path
    research_dir = Path(__file__).parent / "research"

    if not research_dir.exists():
        show_toast(f"⚠ {t('research.no_files')}")
        return

    files = sorted(research_dir.glob("*.md"))
    if not files:
        show_toast(f"⚠ {t('research.no_files')}")
        return

    # Run the Research app (Textual)
    app = ResearchApp(files)
    app.run()


def action_add_entry():
    """Add a new knowledge entry."""
    # Select type using Textual menu
    type_options = list(VALID_TYPES) + [f"← {t('common.back')}"]
    app = SimpleMenuApp(t('add.type'), type_options)
    idx = app.run()

    if idx is None or idx == len(type_options) - 1:
        return

    entry_type = VALID_TYPES[idx]

    # Get title (still uses prompt_toolkit for now)
    title = prompt_input(t("add.title"))
    if not title:
        return

    # Get tags
    tags_input = prompt_input(t("add.tags"), required=False)
    tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []

    # Get project
    project = prompt_input(t("add.project"), required=False)

    # Get confidence using Textual menu
    conf_options = ["1 - Very Low", "2 - Low", "3 - Medium", "4 - High", "5 - Very High"]
    conf_app = SimpleMenuApp(t('add.confidence'), conf_options)
    conf_idx = conf_app.run()
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
    # Get search query (still uses prompt_toolkit for now)
    query = prompt_input(t("search.query"))
    if not query:
        return

    db = get_db()
    results = db.search(query, limit=20)

    if not results:
        show_toast(f"⚠ {t('search.no_results')}")
        return

    # Display results using BrowseApp (Textual)
    entries = [r.entry for r in results]
    app = BrowseApp(entries, db)
    app.run()


def action_browse():
    """Browse all entries with Textual DataTable and live detail preview."""
    db = get_db()
    entries = db.list_all(limit=100)

    if not entries:
        show_toast(f"⚠ {t('browse.no_entries')}")
        return

    while True:
        # Run the browse app (Textual)
        app = BrowseApp(entries, db)
        result = app.run()

        if result is None:
            return

        action, entry = result

        if action == "view":
            _show_entry_detail(entry)
            entries = db.list_all(limit=100)
            if not entries:
                show_toast(f"⚠ {t('browse.no_entries')}")
                return
        elif action == "edit":
            _edit_entry(entry)
            entries = db.list_all(limit=100)
            if not entries:
                return
        elif action == "delete":
            if _delete_entry(entry):
                entries = db.list_all(limit=100)
                if not entries:
                    show_toast(f"⚠ {t('browse.no_entries')}")
                    return


def _show_entry_detail(entry):
    """Display entry details with navigation options using Textual."""
    while True:
        # Build detail content
        stars = '★' * entry.confidence + '☆' * (5 - entry.confidence)
        lines = [
            f"[bold cyan]━━━ {entry.title} ━━━[/bold cyan]",
            "",
            f"[cyan]{t('browse.id')}:[/cyan]         {entry.id}",
            f"[cyan]{t('browse.type')}:[/cyan]       {entry.type}",
            f"[cyan]{t('browse.status')}:[/cyan]     {entry.status}",
            f"[cyan]{t('browse.confidence')}:[/cyan] {stars}",
        ]
        if entry.tags:
            lines.append(f"[cyan]{t('browse.tags')}:[/cyan]       {', '.join(entry.tags)}")
        if entry.project:
            lines.append(f"[cyan]{t('add.project')}:[/cyan]    {entry.project}")
        lines.append(f"[cyan]{t('browse.created')}:[/cyan]    {entry.created_at.strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"[cyan]{t('browse.updated')}:[/cyan]    {entry.updated_at.strftime('%Y-%m-%d %H:%M')}")

        if entry.content:
            lines.extend(["", f"[cyan]{t('browse.content')}:[/cyan]", entry.content])

        # Show details using Textual
        show_info("\n".join(lines))

        # Action menu using Textual
        action_options = [
            f"← {t('browse.back_to_list')}",
            t("browse.edit_entry"),
            t("browse.delete_entry"),
        ]
        app = SimpleMenuApp(t('action.actions'), action_options)
        action_idx = app.run()

        if action_idx is None or action_idx == 0:
            return
        elif action_idx == 1:
            _edit_entry(entry)
            return
        elif action_idx == 2:
            if _delete_entry(entry):
                return


def _edit_entry(entry):
    """Edit an existing entry (uses prompt_toolkit for inputs)."""
    # Edit title
    new_title = prompt_input(f"{t('add.title')} [{entry.title}]", required=False)
    if new_title:
        entry.title = new_title

    # Edit content
    content_preview = (entry.content[:50] + '...') if entry.content and len(entry.content) > 50 else (entry.content or '')
    new_content = prompt_input(f"{t('edit.new_content')} [{content_preview}]", required=False)
    if new_content:
        entry.content = new_content

    # Edit project
    new_project = prompt_input(f"{t('add.project')} [{entry.project or '-'}]", required=False)
    if new_project:
        entry.project = new_project if new_project != "-" else None

    # Edit tags
    current_tags = ", ".join(entry.tags) if entry.tags else "-"
    new_tags = prompt_input(f"{t('browse.tags')} [{current_tags}]", required=False)
    if new_tags:
        entry.tags = [tag.strip() for tag in new_tags.split(",") if tag.strip()]

    # Save
    db = get_db()
    db.update(entry)
    show_toast(f"✓ {t('browse.updated')}")


def _delete_entry(entry) -> bool:
    """Delete an entry with confirmation using Textual. Returns True if deleted."""
    title = f"{t('browse.confirm_delete', title=entry.title[:30])}"
    options = [t("common.no"), t("common.yes")]
    app = SimpleMenuApp(title, options)
    idx = app.run()

    if idx == 1:
        db = get_db()
        db.delete(entry.id)
        show_toast(f"✓ {t('browse.deleted')}")
        return True
    return False


def action_show():
    """Show entry details by ID using Textual."""
    entry_id = prompt_input(t("show.entry_id"))
    if not entry_id:
        return

    db = get_db()
    entry = db.get(entry_id)

    if not entry:
        show_toast(f"⚠ {t('show.not_found')}: {entry_id}")
        return

    # Build and display details using Textual
    stars = '★' * entry.confidence + '☆' * (5 - entry.confidence)
    lines = [
        f"[bold cyan]━━━ {entry.title} ━━━[/bold cyan]",
        "",
        f"[cyan]{t('browse.id')}:[/cyan] {entry.id}",
        f"[cyan]{t('browse.type')}:[/cyan] {entry.type}",
        f"[cyan]{t('browse.status')}:[/cyan] {entry.status}",
        f"[cyan]{t('browse.confidence')}:[/cyan] {stars}",
    ]
    if entry.tags:
        lines.append(f"[cyan]{t('browse.tags')}:[/cyan] {', '.join(entry.tags)}")
    if entry.project:
        lines.append(f"[cyan]{t('add.project')}:[/cyan] {entry.project}")
    if entry.content:
        lines.extend(["", f"[cyan]{t('browse.content')}:[/cyan]", entry.content])

    show_info("\n".join(lines))


def action_setup():
    """Setup / Configuration submenu using Textual."""
    from pathlib import Path

    from rekall.config import get_config
    from rekall.paths import PathResolver

    while True:
        config = get_config()

        # Detect current state
        local_rekall = Path.cwd() / ".rekall"
        local_db = local_rekall / "knowledge.db"
        has_local = local_rekall.exists()
        has_local_db = local_db.exists()

        resolver = PathResolver()
        global_paths = resolver._from_xdg()
        global_db = global_paths.db_path if global_paths else Path.home() / ".local" / "share" / "rekall" / "knowledge.db"
        has_global_db = global_db.exists()

        # Build status info
        global_status = "[green]✓[/green]" if has_global_db else "[dim]○[/dim]"
        local_status = "[green]✓[/green]" if has_local_db else ("[yellow]⚠[/yellow]" if has_local else "[dim]○[/dim]")

        # Build title with status
        title = f"{t('setup.title')} | {t('setup.current_source')}: {config.paths.source.value}"

        # Build dynamic menu
        submenu_options = []
        actions = []

        if has_global_db:
            submenu_options.append(f"{global_status} {t('setup.use_global')}")
            actions.append("use_global")
        else:
            submenu_options.append(f"{global_status} {t('setup.create_global')}")
            actions.append("create_global")

        if has_local_db:
            submenu_options.append(f"{local_status} {t('setup.use_local')}")
            actions.append("use_local")
        else:
            submenu_options.append(f"{local_status} {t('setup.create_local')}")
            actions.append("create_local")

        if has_global_db and not has_local_db:
            submenu_options.append(t("setup.copy_global_to_local"))
            actions.append("migrate_to_local")
        if has_local_db and not has_global_db:
            submenu_options.append(t("setup.copy_local_to_global"))
            actions.append("migrate_to_global")

        submenu_options.append(t("setup.show_config"))
        actions.append("show_config")

        submenu_options.append(f"← {t('setup.back')}")
        actions.append("back")

        # Show menu using Textual
        app = SimpleMenuApp(title, submenu_options)
        idx = app.run()

        if idx is None or actions[idx] == "back":
            return

        action = actions[idx]
        if action == "use_global":
            show_toast("✓ Base globale déjà active")
        elif action == "use_local":
            show_toast("✓ Base locale déjà active")
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
    """Copy database from source to destination using Textual."""
    import shutil

    # Show info about migration
    info = f"[bold]Migration {direction}[/bold]\n\n[cyan]Source:[/cyan] {source}\n[cyan]Destination:[/cyan] {dest}"
    show_info(info)

    # Confirm
    if dest.exists():
        title = "⚠ La destination existe déjà"
        options = ["Écraser la destination", "Annuler"]
    else:
        title = "Confirmer la copie ?"
        options = ["Oui, copier la base", "Annuler"]

    app = SimpleMenuApp(title, options)
    if app.run() != 0:
        return

    # Create destination directory if needed
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Copy database
    shutil.copy2(source, dest)

    # If migrating to local, also install commands
    if "LOCAL" in direction:
        _install_local_commands(dest.parent.parent)

    show_toast(f"✓ Base copiée: {dest}", 2.0)


def _setup_global():
    """Initialize global XDG database using Textual."""
    from rekall.db import Database
    from rekall.paths import PathResolver

    resolver = PathResolver()
    paths = resolver.resolve()

    # Show info
    info = f"[bold]Installation Globale (XDG)[/bold]\n\n[cyan]Config:[/cyan]  {paths.config_dir}\n[cyan]Data:[/cyan]    {paths.data_dir}\n[cyan]Cache:[/cyan]   {paths.cache_dir}\n[cyan]DB:[/cyan]      {paths.db_path}"
    show_info(info)

    if paths.db_path.exists():
        title = "⚠ La base de données existe déjà"
        options = ["Ouvrir la base existante", "Annuler"]
    else:
        title = "Créer la base de données ?"
        options = ["Oui, créer la base globale", "Annuler"]

    app = SimpleMenuApp(title, options)
    if app.run() != 0:
        return

    if not paths.db_path.exists():
        paths.config_dir.mkdir(parents=True, exist_ok=True)
        paths.data_dir.mkdir(parents=True, exist_ok=True)
        paths.cache_dir.mkdir(parents=True, exist_ok=True)

    db = Database(paths.db_path)
    db.init()
    db.close()

    show_toast("✓ Base globale initialisée", 2.0)


def _setup_local():
    """Initialize local project database using Textual."""
    from pathlib import Path

    from rekall.paths import init_local_project

    cwd = Path.cwd()
    local_dir = cwd / ".rekall"

    # Show info
    info = f"[bold]Installation Locale (Projet)[/bold]\n\n[cyan]Dossier:[/cyan]  {local_dir}\n[cyan]DB:[/cyan]       {local_dir / 'knowledge.db'}"
    show_info(info)

    if local_dir.exists():
        title = "⚠ Le dossier .rekall/ existe déjà"
        options = ["Ouvrir la base existante", "Annuler"]
        app = SimpleMenuApp(title, options)
        if app.run() != 0:
            return
    else:
        title = "Versionner la base dans Git ?"
        options = [
            "Versionner la DB (partage équipe)",
            "Exclure la DB du Git (données locales)",
            "Annuler",
        ]
        app = SimpleMenuApp(title, options)
        git_choice = app.run()

        if git_choice is None or git_choice == 2:
            return

        exclude_db = (git_choice == 1)
        init_local_project(cwd, exclude_db_from_git=exclude_db)
        _install_local_commands(cwd)

    show_toast("✓ Projet local initialisé", 2.0)


def _install_local_commands(project_path: Path):
    """Install rekall commands to project's .claude/commands/."""

    # Source: global command
    global_cmd = Path.home() / ".claude" / "commands" / "rekall.save.md"

    # Target: local project command
    local_cmd_dir = project_path / ".claude" / "commands"
    local_cmd = local_cmd_dir / "rekall.save.md"

    if not global_cmd.exists():
        show_toast("⚠ rekall.save.md global non trouvé, commande locale non installée.")
        return

    # Create directory if needed
    local_cmd_dir.mkdir(parents=True, exist_ok=True)

    # Copy command
    local_cmd.write_text(global_cmd.read_text())

    show_toast(f"✓ Commande /rekall.save installée: {local_cmd}")


def _show_config_details():
    """Show detailed configuration."""
    import os
    from io import StringIO

    from rich.console import Console as RichConsole

    from rekall.config import get_config

    config = get_config()

    # Build table content
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

    # Capture table as string
    string_io = StringIO()
    temp_console = RichConsole(file=string_io, force_terminal=True, width=100)
    temp_console.print("[bold]Configuration Détaillée[/bold]")
    temp_console.print()
    temp_console.print(table)
    content = string_io.getvalue()

    # Show in Textual app
    show_info(content)


def action_export_import():
    """Export / Import submenu using Textual."""
    while True:
        submenu_options = [
            t("export.archive"),
            t("export.markdown"),
            t("export.json"),
            "─" * 30,
            t("import.archive"),
            t("import.external_db"),
            "─" * 30,
            f"← {t('setup.back')}",
        ]
        app = SimpleMenuApp("Export / Import", submenu_options)
        idx = app.run()

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
    """Export to .rekall.zip archive using Textual."""
    from pathlib import Path

    from rekall.archive import RekallArchive

    filename = prompt_input(t("import.filename"))
    if not filename:
        return

    db = get_db()
    entries = db.list_all(limit=100000)

    if not entries:
        show_toast(f"⚠ {t('import.no_entries')}")
        return

    output_path = Path(f"{filename}.rekall.zip")
    RekallArchive.create(output_path, entries)
    show_toast(f"✓ {t('import.exported', count=len(entries), path=output_path)}", 2.0)


def _do_export_text(fmt: str):
    """Export to text format (md or json) using Textual."""
    from pathlib import Path

    from rekall import exporters

    filename = prompt_input(t("import.output_filename", fmt=fmt))
    if not filename:
        return

    db = get_db()
    entries = db.list_all(limit=100000)

    if not entries:
        show_toast(f"⚠ {t('import.no_entries')}")
        return

    output_path = Path(f"{filename}.{fmt}")

    if fmt == "json":
        content = exporters.export_json(entries)
    else:
        content = exporters.export_markdown(entries)

    output_path.write_text(content)
    show_toast(f"✓ {t('import.exported', count=len(entries), path=output_path)}", 2.0)


def _do_import_rekall():
    """Import from .rekall.zip archive using Textual."""
    from pathlib import Path

    from rekall.archive import RekallArchive
    from rekall.sync import ImportExecutor, build_import_plan

    filepath = prompt_input(t("import.archive_path"))
    if not filepath:
        return

    archive_path = Path(filepath)
    if not archive_path.exists():
        show_info(f"[red]{t('import.file_not_found')}: {filepath}[/red]")
        return

    # Open and validate
    archive = RekallArchive.open(archive_path)
    if archive is None:
        show_info(f"[red]{t('import.invalid_archive')}: {filepath}[/red]")
        return

    validation = archive.validate()
    if not validation.valid:
        error_lines = [f"[red]{t('import.validation_failed')}:[/red]"]
        for error in validation.errors:
            error_lines.append(f"  - {error}")
        show_info("\n".join(error_lines))
        return

    # Build info text
    manifest = archive.get_manifest()
    info_lines = [
        f"[cyan]{t('import.archive_info')}:[/cyan]",
        f"  {t('import.version')}: {manifest.format_version}",
        f"  {t('browse.created')}: {manifest.created_at.strftime('%Y-%m-%d %H:%M')}",
        f"  {t('import.entries')}: {manifest.stats.entries_count}",
        "",
    ]

    # Build plan
    db = get_db()
    imported_entries = archive.get_entries()
    plan = build_import_plan(db, imported_entries)

    # Add preview
    executor = ImportExecutor(db)
    preview = executor.preview(plan)
    info_lines.append(preview)

    show_info("\n".join(info_lines))

    if plan.total == 0:
        show_toast(f"⚠ {t('import.nothing_to_import')}")
        return

    # Choose strategy
    strategy_options = [
        t("import.skip_conflicts"),
        t("import.replace_conflicts"),
        t("import.merge_conflicts"),
        t("import.cancel"),
    ]
    strategy_app = SimpleMenuApp(t("import.conflict_strategy"), strategy_options)
    strategy_idx = strategy_app.run()

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
        result_lines = [f"[green]✓ {t('import.success')}[/green]"]
        result_lines.append(f"  {t('import.added')}: {result.added}")
        if result.replaced:
            result_lines.append(f"  {t('import.replaced')}: {result.replaced}")
        if result.merged:
            result_lines.append(f"  {t('import.merged')}: {result.merged}")
        result_lines.append(f"  {t('import.skipped')}: {result.skipped}")
        if result.backup_path:
            result_lines.append(f"  {t('import.backup')}: {result.backup_path}")
        show_info("\n".join(result_lines))
    else:
        error_lines = [f"[red]{t('import.failed')}:[/red]"]
        for error in result.errors:
            error_lines.append(f"  - {error}")
        show_info("\n".join(error_lines))


def _do_import_external_db():
    """Import from an external knowledge.db file using Textual."""
    from pathlib import Path

    from rekall.sync import ImportExecutor, build_import_plan, load_entries_from_external_db

    filepath = prompt_input(t("import.external_db_path"))
    if not filepath:
        return

    db_path = Path(filepath).expanduser()
    if not db_path.exists():
        show_info(f"[red]{t('import.file_not_found')}: {filepath}[/red]")
        return

    # Load entries from external DB
    try:
        imported_entries = load_entries_from_external_db(db_path)
    except ValueError as e:
        show_info(f"[red]{t('common.error')}: {e}[/red]")
        return

    if not imported_entries:
        show_toast(f"⚠ {t('import.no_entries_external')}")
        return

    # Build info text
    info_lines = [
        f"[cyan]{t('import.external_db')}:[/cyan]",
        f"  {t('import.file')}: {db_path}",
        f"  {t('import.entries')}: {len(imported_entries)}",
    ]

    # Group by type
    types_count = {}
    for entry in imported_entries:
        types_count[entry.type] = types_count.get(entry.type, 0) + 1
    info_lines.append(f"  {t('import.types')}: {', '.join(f'{tp}({c})' for tp, c in types_count.items())}")
    info_lines.append("")

    # Build plan
    db = get_db()
    plan = build_import_plan(db, imported_entries)

    # Add preview
    executor = ImportExecutor(db)
    preview = executor.preview(plan)
    info_lines.append(preview)

    show_info("\n".join(info_lines))

    if plan.total == 0:
        show_toast(f"⚠ {t('import.nothing_to_import')}")
        return

    # Choose strategy
    strategy_options = [
        t("import.skip_conflicts"),
        t("import.replace_conflicts"),
        t("import.merge_conflicts"),
        t("import.cancel"),
    ]
    strategy_app = SimpleMenuApp(t("import.conflict_strategy"), strategy_options)
    strategy_idx = strategy_app.run()

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
        result_lines = [f"[green]✓ {t('import.success')}[/green]"]
        result_lines.append(f"  {t('import.added')}: {result.added}")
        if result.replaced:
            result_lines.append(f"  {t('import.replaced')}: {result.replaced}")
        if result.merged:
            result_lines.append(f"  {t('import.merged')}: {result.merged}")
        result_lines.append(f"  {t('import.skipped')}: {result.skipped}")
        if result.backup_path:
            result_lines.append(f"  {t('import.backup')}: {result.backup_path}")
        show_info("\n".join(result_lines))
    else:
        error_lines = [f"[red]{t('import.failed')}:[/red]"]
        for error in result.errors:
            error_lines.append(f"  - {error}")
        show_info("\n".join(error_lines))


# =============================================================================
# Main TUI Loop
# =============================================================================


# Map action keys to functions
ACTION_MAP = {
    "language": None,  # Will be set to action_language
    "config": None,    # Unified config & maintenance
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
        ("config", t("menu.config"), t("menu.config.desc")),
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
        "config": action_install_ide,  # Unified config & maintenance menu
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
                show_info(f"[red]✗ {t('common.error')}: {e}[/red]")


if __name__ == "__main__":
    run_tui()
