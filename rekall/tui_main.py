"""Rekall TUI - Interactive Terminal User Interface using Textual."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text
from textual import events
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, VerticalScroll
from textual.message import Message
from textual.widgets import (
    Button,
    Collapsible,
    DataTable,
    Footer,
    Input,
    ListItem,
    ListView,
    Markdown,
    RadioButton,
    RadioSet,
    SelectionList,
    Static,
    TabbedContent,
    TabPane,
)
from textual.widgets.selection_list import Selection
from textual.suggester import Suggester, SuggestFromList

from rekall.config import get_config, save_config_to_toml


class MultiTagSuggester(Suggester):
    """Suggester for comma-separated tags - suggests for the last tag being typed."""

    def __init__(self, tags: list[str], case_sensitive: bool = False):
        super().__init__(use_cache=False, case_sensitive=case_sensitive)
        self.tags = tags
        self._case_sensitive = case_sensitive

    async def get_suggestion(self, value: str) -> Optional[str]:
        """Get suggestion for the last tag in a comma-separated list."""
        if not value:
            return None

        # Split by comma and get the last part being typed
        parts = value.split(",")
        current_tag = parts[-1].strip()

        if not current_tag:
            return None

        # Find matching tag
        for tag in self.tags:
            if self._case_sensitive:
                if tag.startswith(current_tag):
                    # Return full value with completed tag
                    prefix = ", ".join(p.strip() for p in parts[:-1])
                    if prefix:
                        return f"{prefix}, {tag}"
                    return tag
            else:
                if tag.lower().startswith(current_tag.lower()):
                    prefix = ", ".join(p.strip() for p in parts[:-1])
                    if prefix:
                        return f"{prefix}, {tag}"
                    return tag

        return None


from rekall.db import Database
from rekall.i18n import LANGUAGES, get_lang, load_lang_preference, set_lang, t
from rekall.models import VALID_TYPES, Entry, generate_ulid

console = Console()


# =============================================================================
# Sortable DataTable Mixin - Shared functionality for browse apps
# =============================================================================


class SortableTableMixin:
    """Mixin providing sortable column functionality for DataTable apps.

    Usage:
        class MyApp(SortableTableMixin, App):
            TABLE_ID = "my-table"

            def get_sort_key(self, column_key: str) -> Callable:
                return lambda item: getattr(item, column_key, "")

    Attributes:
        sort_column: Current sort column key (None = no sort)
        sort_reverse: True for descending, False for ascending
        entries: List of data items to display
    """

    TABLE_ID: str = "data-table"  # Override in subclass

    def init_sorting(self) -> None:
        """Initialize sorting state. Call in __init__."""
        self.sort_column: str | None = None
        self.sort_reverse: bool = False

    def get_sort_key(self, column_key: str):
        """Get sort key function for a column.

        Override in subclass to provide custom sort keys.

        Args:
            column_key: The column key to sort by

        Returns:
            Function that extracts sortable value from an item
        """
        return lambda item: getattr(item, column_key, "")

    def sort_entries(self) -> None:
        """Sort entries by current sort column."""
        if not self.sort_column or not hasattr(self, "entries"):
            return

        try:
            key_func = self.get_sort_key(self.sort_column)
            # Handle None values by converting to empty string for comparison
            safe_key = lambda x: (key_func(x) is None, key_func(x) if key_func(x) is not None else "")
            self.entries.sort(key=safe_key, reverse=self.sort_reverse)
        except (AttributeError, TypeError):
            # If sorting fails, don't crash
            pass

    def refresh_table(self) -> None:
        """Refresh the DataTable with current entries.

        Override in subclass to implement table refresh logic.
        """
        raise NotImplementedError("Subclass must implement refresh_table()")


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

    def __init__(
        self, label: str, description: str, action_key: str, label_width: int = 15
    ) -> None:
        super().__init__()
        self.label = label
        self.description = description
        self.action_key = action_key
        self.label_width = label_width

    def compose(self) -> ComposeResult:
        if self.action_key == "__section__":
            # Section header: ── TITRE ──
            yield Static(f"[bold cyan]{self.label}[/]")
        elif self.action_key == "__spacer__":
            # Empty line
            yield Static("")
        else:
            # Normal item
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
                # Skip non-selectable items (headers, spacers, box borders)
                if item.action_key.startswith("__"):
                    return
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

    def __init__(self, menu_items: list[tuple], banner_lines: list[str], subtitle: str, quote: str):
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

        # Calculate max label width for alignment (exclude special elements)
        selectable_items = [
            (key, label, desc) for key, label, desc in self.menu_items
            if not key.startswith("__")
        ]
        max_label_width = max(len(label) for _, label, _ in selectable_items) + 2

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

    def __init__(self, title: str, items: list[str], notification: str = ""):
        super().__init__()
        self.title_text = title
        self.items = items
        self.result = None
        self.initial_notification = notification

    def compose(self) -> ComposeResult:
        yield create_banner_container()

        if self.title_text:
            yield Static(self.title_text, id="title")

        # Build menu items with section headers support
        # Section headers start with "─" or "═" and are non-selectable
        menu_items = []
        self.index_mapping = {}  # Map ListView position to original index
        list_position = 0

        # Calculate max label width (excluding headers)
        selectable_items = [
            item for item in self.items
            if not (item.strip().startswith("─") or item.strip().startswith("═"))
        ]
        max_label_width = max((len(item) for item in selectable_items), default=15) + 2

        for i, item in enumerate(self.items):
            stripped = item.strip()
            # Empty line = visual spacer (non-selectable)
            if not stripped:
                menu_items.append(MenuItem(" ", "", "__spacer__", max_label_width))
                list_position += 1
                continue
            # Section header (non-selectable visual separator)
            if stripped.startswith("─") or stripped.startswith("═"):
                styled = f"[bold cyan]{stripped}[/bold cyan]"
                menu_items.append(MenuItem(styled, "", "__header__", max_label_width))
                list_position += 1
            else:
                menu_items.append(MenuItem(item, "", str(i), max_label_width))
                self.index_mapping[list_position] = i
                list_position += 1

        yield MenuListView(*menu_items)

        yield Static("", id="left-notify")
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted - show initial notification if any."""
        if self.initial_notification:
            self.show_left_notify(self.initial_notification, 3.0)

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
        """Handle item selection using action_key."""
        item = event.item
        if isinstance(item, MenuItem):
            # Skip non-selectable items (headers and spacers)
            if item.action_key in ("__header__", "__spacer__"):
                return
            try:
                self.exit(result=int(item.action_key))
            except ValueError:
                self.exit(result=item.action_key)


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

    def __init__(self, title: str, items: list[tuple], hint: str = ""):
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
        self.result: list | None = None

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


# =============================================================================
# Delete Confirmation Overlay Widget
# =============================================================================


class DeleteConfirmOverlay(Container):
    """Overlay for confirming entry deletion with link count warning."""

    DEFAULT_CSS = """
    DeleteConfirmOverlay {
        layer: modal;
        align: center middle;
        width: auto;
        height: auto;
        background: transparent;
    }

    DeleteConfirmOverlay #delete-confirm-box {
        background: $surface;
        border: thick $error;
        padding: 1 2;
        width: auto;
        max-width: 60;
        height: auto;
    }

    DeleteConfirmOverlay #delete-title {
        text-style: bold;
        color: $error;
        text-align: center;
        margin-bottom: 1;
    }

    DeleteConfirmOverlay #delete-links-warning {
        color: $warning;
        text-align: center;
        margin-bottom: 1;
    }

    DeleteConfirmOverlay #delete-buttons {
        align: center middle;
        height: auto;
        margin-top: 1;
    }

    DeleteConfirmOverlay .delete-button {
        margin: 0 1;
        min-width: 16;
    }

    DeleteConfirmOverlay .delete-button:focus {
        background: $primary;
    }
    """

    BINDINGS = [
        Binding("y", "confirm_delete", "Yes", show=False),
        Binding("n", "cancel_delete", "No", show=False),
        Binding("escape", "cancel_delete", "Cancel", show=False),
    ]

    def __init__(
        self,
        entry_title: str,
        entry_id: str,
        link_count: int = 0,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.entry_title = entry_title[:30] + "..." if len(entry_title) > 30 else entry_title
        self.entry_id = entry_id
        self.link_count = link_count

    def compose(self) -> ComposeResult:
        with Container(id="delete-confirm-box"):
            yield Static(
                t("browse.confirm_delete", title=self.entry_title),
                id="delete-title",
            )
            if self.link_count > 0:
                yield Static(
                    t("browse.links_warning", count=self.link_count),
                    id="delete-links-warning",
                )
            with Container(id="delete-buttons"):
                yield Static(
                    f"[bold red][ {t('browse.confirm_yes')} ][/]  [dim][ {t('browse.confirm_no')} ][/]",
                    id="delete-button-hint",
                )

    class DeleteConfirmed(Message):
        """Message sent when deletion is confirmed."""

        def __init__(self, entry_id: str) -> None:
            super().__init__()
            self.entry_id = entry_id

    class DeleteCancelled(Message):
        """Message sent when deletion is cancelled."""

        pass

    def action_confirm_delete(self) -> None:
        """Confirm deletion and notify parent."""
        self.post_message(self.DeleteConfirmed(self.entry_id))

    def action_cancel_delete(self) -> None:
        """Cancel deletion and remove overlay."""
        self.post_message(self.DeleteCancelled())


class BrowseApp(SortableTableMixin, App):
    """Textual app for browsing entries with DataTable and detail panel."""

    TABLE_ID = "entries-table"

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

    #graph-modal {
        display: none;
        layer: modal;
        width: 80;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        offset: 50% 4;
        background: #1e2a4a;
        border: thick #4367CD;
        color: #93B5F7;
    }

    #graph-modal.visible {
        display: block;
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
        Binding("a", "add_entry", "Add", show=True),
        Binding("e", "edit_entry", "Edit", show=True),
        Binding("d", "delete_entry", "Delete", show=True),
        Binding("slash", "search", "Search", show=True),
        Binding("question_mark", "toggle_legend", "?", show=True),
        Binding("space", "toggle_graph", "Graph", show=True),
        # Graph navigation keys
        Binding("1", "graph_nav(0)", "1", show=False),
        Binding("2", "graph_nav(1)", "2", show=False),
        Binding("3", "graph_nav(2)", "3", show=False),
        Binding("4", "graph_nav(3)", "4", show=False),
        Binding("5", "graph_nav(4)", "5", show=False),
        Binding("6", "graph_nav(5)", "6", show=False),
        Binding("7", "graph_nav(6)", "7", show=False),
        Binding("8", "graph_nav(7)", "8", show=False),
        Binding("9", "graph_nav(8)", "9", show=False),
        # Preview mode toggle
        Binding("less_than_sign", "preview_content", "<", show=False),
        Binding("greater_than_sign", "preview_context", ">", show=False),
        # Panel resize
        Binding("plus", "panel_grow", "+", show=False),
        Binding("minus", "panel_shrink", "-", show=False),
    ]

    def __init__(self, entries: list, db):
        super().__init__()
        self.init_sorting()  # Initialize sorting from SortableTableMixin
        self.all_entries = entries  # Keep original list
        self.entries = list(entries)  # Current filtered list (copy for sorting)
        self.graph_nav_ids: list[str] = []  # IDs navigable from graph modal
        self.context_sizes: dict[str, int] = {}  # Context compressed sizes
        self.preview_mode = "content"  # "content" or "context"
        self.config = get_config()
        self.detail_panel_fr = self.config.ui_detail_panel_ratio  # Load from config
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
        # Graph modal (hidden by default)
        yield Container(
            Static(t("browse.graph_title"), id="graph-title"),
            VerticalScroll(
                Static("", id="graph-content"),
                id="graph-scroll",
            ),
            Static("[dim]Espace/Esc: fermer • 1-9: naviguer[/dim]", id="graph-hint"),
            id="graph-modal",
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
        graph_modal = self.query_one("#graph-modal", Container)

        if graph_modal.has_class("visible"):
            graph_modal.remove_class("visible")
            self.graph_nav_ids = []
        # Generate graph for selected entry
        elif self.selected_entry:
            result = self.db.render_graph_ascii(
                self.selected_entry.id,
                max_depth=2,
                show_incoming=True,
                show_outgoing=True,
                make_clickable=True,
            )
            graph_output, self.graph_nav_ids = result
            graph_content = self.query_one("#graph-content", Static)
            graph_content.update(graph_output)
            graph_modal.add_class("visible")
        else:
            self.show_left_notify("Aucune entrée sélectionnée", 2.0)

    def action_graph_nav(self, index: int) -> None:
        """Navigate to entry by number key (1-9) when graph is visible."""
        graph_modal = self.query_one("#graph-modal", Container)
        if not graph_modal.has_class("visible"):
            return  # Only works when graph is open

        if 0 <= index < len(self.graph_nav_ids):
            entry_id = self.graph_nav_ids[index]
            self.action_navigate_to_entry(entry_id)

    def action_quit_or_close(self) -> None:
        """Close modals if open, otherwise quit."""
        legend = self.query_one("#legend-modal", Container)
        graph_modal = self.query_one("#graph-modal", Container)

        if legend.has_class("visible"):
            legend.remove_class("visible")
        elif graph_modal.has_class("visible"):
            graph_modal.remove_class("visible")
        else:
            self.app.exit()

    def action_navigate_to_entry(self, entry_id: str) -> None:
        """Navigate to a specific entry by ID (from graph click)."""
        # Close the graph modal
        graph_modal = self.query_one("#graph-modal", Container)
        graph_modal.remove_class("visible")

        # Find the entry in current list
        for idx, entry in enumerate(self.entries):
            if entry.id == entry_id:
                # Move cursor to that row
                table = self.query_one("#entries-table", DataTable)
                table.move_cursor(row=idx)
                # Update detail panel
                self.selected_entry = entry
                self._update_detail_panel(entry)
                self.show_left_notify(f"→ {entry.title[:40]}", 2.0)
                return

        # Entry not in current list - try to load it
        entry = self.db.get(entry_id, update_access=False)
        if entry:
            self.selected_entry = entry
            self._update_detail_panel(entry)
            self.show_left_notify(f"→ {entry.title[:40]} (hors liste)", 3.0)
        else:
            self.show_left_notify(f"Entrée non trouvée: {entry_id[:12]}...", 3.0)

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
        table.add_column("Ctx", width=6, key="context")

        # Load context sizes (single query)
        entry_ids = [e.id for e in self.entries]
        self.context_sizes = self.db.get_context_sizes(entry_ids)

        # Add rows
        self._populate_table()

        # Update detail panel for first entry
        if self.entries:
            self._update_detail_panel(self.entries[0])

        # Apply saved panel height ratio
        if self.detail_panel_fr != 1.0:
            self._apply_panel_height()

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

            # Format context size (bytes to human readable)
            ctx_size = self.context_sizes.get(entry.id, 0)
            if ctx_size == 0:
                ctx_str = "—"
            elif ctx_size < 1024:
                ctx_str = f"{ctx_size}B"
            else:
                ctx_str = f"{ctx_size // 1024}K"

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
                ctx_str,
                key=str(i),
            )

    # =========================================================================
    # Sortable table implementation (SortableTableMixin)
    # =========================================================================

    # Column definitions: (key, label_translation_key, width)
    COLUMNS = [
        ("type", "browse.type", 10),
        ("project", "add.project", 12),
        ("title", "add.title", 50),
        ("created", "browse.created", 18),
        ("updated", "browse.updated", 18),
        ("confidence", "add.confidence", 4),
        ("access", "browse.access", 6),
        ("score", "browse.score", 5),
        ("links_in", "browse.links_in", 3),
        ("links_out", "browse.links_out", 3),
        ("context", None, 6),  # "Ctx" label, no translation
    ]

    def get_sort_key(self, column_key: str):
        """Get sort key function for a column."""
        # Map column keys to entry attributes
        key_map = {
            "type": lambda e: e.type or "",
            "project": lambda e: (e.project or "").lower(),
            "title": lambda e: e.title.lower(),
            "created": lambda e: e.created_at,
            "updated": lambda e: e.updated_at,
            "confidence": lambda e: e.confidence,
            "access": lambda e: e.access_count,
            "score": lambda e: e.consolidation_score,
            "links_in": lambda e: self.db.count_links_by_direction(e.id)[0],
            "links_out": lambda e: self.db.count_links_by_direction(e.id)[1],
            "context": lambda e: self.context_sizes.get(e.id, 0),
        }
        return key_map.get(column_key, lambda e: "")

    def refresh_table(self) -> None:
        """Refresh the DataTable with current entries and sort state."""
        table = self.query_one("#entries-table", DataTable)
        table.clear(columns=True)

        # Add columns with sort indicators
        for key, label_key, width in self.COLUMNS:
            if label_key:
                base_label = t(label_key)
            else:
                base_label = "Ctx"  # Special case for context column

            # Add sort indicator if this column is sorted
            if self.sort_column == key:
                indicator = " ▼" if self.sort_reverse else " ▲"
                label = f"{base_label}{indicator}"
            else:
                label = base_label

            table.add_column(label, width=width, key=key)

        # Re-populate rows
        self._populate_table()

        # Update header
        self._update_header()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header click for sorting."""
        column_key = event.column_key.value

        # Toggle sort direction if same column, otherwise sort ascending
        if self.sort_column == column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_key
            self.sort_reverse = False

        # Sort entries
        self.sort_entries()

        # Refresh table
        self.refresh_table()

        # Notify user
        direction = "▼" if self.sort_reverse else "▲"
        self.show_left_notify(f"Trié par {column_key} {direction}", 1.5)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Update detail panel when row selection changes."""
        if event.row_key is not None:
            try:
                idx = int(event.row_key.value)
                if 0 <= idx < len(self.entries):
                    self.selected_entry = self.entries[idx]
                    self._update_detail_panel(self.selected_entry)
                    # Update graph modal if visible
                    self._update_graph_if_visible()
            except (ValueError, TypeError):
                pass

    def _update_graph_if_visible(self) -> None:
        """Update graph modal content if it's currently visible."""
        graph_modal = self.query_one("#graph-modal", Container)
        if graph_modal.has_class("visible") and self.selected_entry:
            result = self.db.render_graph_ascii(
                self.selected_entry.id,
                max_depth=2,
                show_incoming=True,
                show_outgoing=True,
                make_clickable=True,
            )
            graph_output, self.graph_nav_ids = result
            graph_content = self.query_one("#graph-content", Static)
            graph_content.update(graph_output)

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

        # Full content or context based on preview_mode
        if self.preview_mode == "context":
            # Try structured context first (new system)
            structured_ctx = self.db.get_structured_context(entry.id)
            if structured_ctx:
                # Format structured context nicely (Markdown format)
                lines = ["# CONTEXTE STRUCTURÉ\n"]
                lines.append(f"## 📍 Situation\n{structured_ctx.situation}\n")
                lines.append(f"## ✅ Solution\n{structured_ctx.solution}\n")
                if structured_ctx.trigger_keywords:
                    kw_str = ", ".join(f"`{kw}`" for kw in structured_ctx.trigger_keywords)
                    lines.append(f"## 🏷️ Keywords\n{kw_str}\n")
                if structured_ctx.what_failed:
                    lines.append(f"## ❌ Ce qui n'a pas marché\n{structured_ctx.what_failed}\n")
                if structured_ctx.conversation_excerpt:
                    lines.append(f"## 💬 Conversation\n{structured_ctx.conversation_excerpt}\n")
                if structured_ctx.files_modified:
                    files_str = ", ".join(f"`{f}`" for f in structured_ctx.files_modified)
                    lines.append(f"## 📁 Fichiers\n{files_str}\n")
                if structured_ctx.error_messages:
                    errors_str = "\n- ".join(structured_ctx.error_messages)
                    lines.append(f"## ⚠️ Erreurs\n- {errors_str}\n")
                content_widget.update("\n".join(lines))
            else:
                # Fallback to legacy compressed context
                context = self.db.get_context(entry.id)
                if context:
                    content_widget.update(f"**[CONTEXTE]**\n\n{context}")
                else:
                    content_widget.update("*Pas de contexte stocké pour cette entrée*")
        # Show normal content
        elif entry.content:
            content_widget.update(entry.content)
        else:
            content_widget.update(f"*{t('browse.no_content')}*")

    def action_preview_content(self) -> None:
        """Toggle preview mode (< or >)."""
        self._toggle_preview_mode()

    def action_preview_context(self) -> None:
        """Toggle preview mode (< or >)."""
        self._toggle_preview_mode()

    def _toggle_preview_mode(self) -> None:
        """Cycle between content and context preview modes."""
        if self.preview_mode == "content":
            self.preview_mode = "context"
            self.show_left_notify("◀ Contexte", 1.5)
        else:
            self.preview_mode = "content"
            self.show_left_notify("▶ Contenu", 1.5)

        if self.selected_entry:
            self._update_detail_panel(self.selected_entry)

    def action_panel_grow(self) -> None:
        """Increase detail panel height (+)."""
        self.detail_panel_fr = min(4.0, self.detail_panel_fr + 0.5)
        self._apply_panel_height()
        self._save_panel_ratio()

    def action_panel_shrink(self) -> None:
        """Decrease detail panel height (-)."""
        self.detail_panel_fr = max(0.5, self.detail_panel_fr - 0.5)
        self._apply_panel_height()
        self._save_panel_ratio()

    def _apply_panel_height(self) -> None:
        """Apply the current panel height fraction."""
        detail_panel = self.query_one("#detail-panel", VerticalScroll)
        detail_panel.styles.height = f"{self.detail_panel_fr}fr"

    def _save_panel_ratio(self) -> None:
        """Save panel ratio to config file."""
        save_config_to_toml(
            self.config.config_dir,
            {"ui": {"detail_panel_ratio": self.detail_panel_fr}}
        )

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
        """Delete selected entry with in-app confirmation overlay."""
        if not self.selected_entry:
            return

        # Count links for warning
        from rekall.db import get_db
        db = get_db()
        link_count = db.count_links(self.selected_entry.id)

        # Show confirmation overlay
        overlay = DeleteConfirmOverlay(
            entry_title=self.selected_entry.title,
            entry_id=self.selected_entry.id,
            link_count=link_count,
        )
        self.mount(overlay)
        overlay.focus()

    def action_add_entry(self) -> None:
        """Add a new entry (optionally pre-linked to selected entry)."""
        # Pass selected entry for potential pre-linking
        self.exit(result=("add", self.selected_entry))

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

    def on_delete_confirm_overlay_delete_confirmed(
        self, message: DeleteConfirmOverlay.DeleteConfirmed
    ) -> None:
        """Handle deletion confirmation from overlay."""
        from rekall.db import get_db

        # Remove overlay first
        overlay = self.query_one(DeleteConfirmOverlay)
        overlay.remove()

        # Delete entry
        db = get_db()
        try:
            db.delete(message.entry_id)
            show_toast(f"✓ {t('browse.deleted')}")

            # Refresh entries list
            self.all_entries = db.list_all(limit=100)
            self.entries = self.all_entries
            self._refresh_table(self.entries)

            # Handle empty list case
            if not self.entries:
                self._update_header(t('browse.no_entries'))
            else:
                self._update_header()

            # Focus table
            table = self.query_one("#entries-table", DataTable)
            table.focus()

        except Exception as e:
            show_toast(f"✗ {t('browse.delete_error')}: {e}")

    def on_delete_confirm_overlay_delete_cancelled(
        self, message: DeleteConfirmOverlay.DeleteCancelled
    ) -> None:
        """Handle deletion cancellation from overlay."""
        # Remove overlay
        overlay = self.query_one(DeleteConfirmOverlay)
        overlay.remove()

        # Focus table
        table = self.query_one("#entries-table", DataTable)
        table.focus()

    def _update_header(self, suffix: str = None) -> None:
        """Update header bar text."""
        header = self.query_one("#section-title", Static)
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


class SourcesBrowseApp(SortableTableMixin, App):
    """Textual app for browsing sources with DataTable and detail panel."""

    TABLE_ID = "sources-table"

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

    #browse-container {
        height: 100%;
    }

    #section-title {
        padding: 0 2;
        margin-bottom: 1;
    }

    #sources-table {
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

    Footer {
        background: $surface-darken-1;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "quit", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("enter", "select_source", "View", show=True),
        Binding("e", "edit_source", "Edit", show=True),
        Binding("d", "delete_source", "Delete", show=True),
        Binding("t", "edit_tags", "Tags", show=True),
        Binding("b", "bulk_mode", "Bulk", show=True),
        Binding("x", "demote_source", "Demote", show=True),
    ]

    def __init__(self, sources: list, db, title: str = None):
        super().__init__()
        self.init_sorting()  # Initialize sorting from SortableTableMixin
        self.sources = list(sources)  # Copy for sorting
        self.entries = self.sources  # Alias for mixin compatibility
        self.db = db
        self.title = title or t("sources.manage")
        self.selected_source = sources[0] if sources else None
        self.result_action = None  # ("view"|"edit"|"delete"|"tags"|"bulk"|"demote", source)
        self.source_tags: dict[str, list[str]] = {}  # Cache tags per source

    def compose(self) -> ComposeResult:
        yield create_banner_container()
        yield Static(f"[dim]{self.title} ({len(self.sources)} sources)[/dim]", id="section-title")
        yield Container(
            Container(
                DataTable(id="sources-table"),
            ),
            VerticalScroll(
                Static("", id="detail-title"),
                Static("", id="detail-meta"),
                Static("", id="detail-content"),
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

    def on_mount(self) -> None:
        """Populate the DataTable with sources."""
        table = self.query_one("#sources-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Add columns
        table.add_column(t("source.domain"), width=30, key="domain")
        table.add_column(t("source.score"), width=8, key="score")
        table.add_column(t("source.status"), width=12, key="status")
        table.add_column(t("source.role"), width=14, key="role")
        table.add_column(t("source.reliability"), width=5, key="reliability")
        table.add_column(t("source.usage_count"), width=6, key="usages")
        table.add_column(t("source.last_used"), width=12, key="last_used")
        table.add_column(t("tags.label"), width=25, key="tags")

        # Load tags for all sources
        for source in self.sources:
            self.source_tags[source.id] = self.db.get_source_themes(source.id)

        # Add rows
        self._populate_table()

        # Update detail panel for first source
        if self.sources:
            self._update_detail_panel(self.sources[0])

    def _populate_table(self) -> None:
        """Populate table rows with current sources."""
        table = self.query_one("#sources-table", DataTable)

        for i, source in enumerate(self.sources):
            # Format score with color indicator
            score = source.personal_score
            if score >= 70:
                score_str = f"[green]{score:.0f}[/green]"
            elif score >= 40:
                score_str = f"[yellow]{score:.0f}[/yellow]"
            else:
                score_str = f"[red]{score:.0f}[/red]"

            # Format status with icon
            status_icons = {
                "active": "✓",
                "inaccessible": "⚠️",
                "archived": "📦",
            }
            status_icon = status_icons.get(source.status, "?")
            status_str = f"{status_icon} {source.status}"

            # Format role with icon
            role_icons = {
                "hub": "🔗",
                "authority": "⭐",
                "unclassified": "·",
            }
            role_icon = role_icons.get(source.role, "·")
            role_str = f"{role_icon} {source.role}"

            # Format last used
            if source.last_used:
                last_used_str = source.last_used.strftime("%Y-%m-%d")
            else:
                last_used_str = "—"

            # Format tags (max 3 displayed)
            tags = self.source_tags.get(source.id, [])
            if tags:
                if len(tags) > 3:
                    tags_str = ", ".join(tags[:3]) + f" +{len(tags) - 3}"
                else:
                    tags_str = ", ".join(tags)
            else:
                tags_str = "[dim]—[/dim]"

            table.add_row(
                source.domain,
                Text.from_markup(score_str),
                Text.from_markup(status_str),
                Text.from_markup(role_str),
                source.reliability,
                str(source.usage_count),
                last_used_str,
                Text.from_markup(tags_str),
                key=str(i),
            )

    # =========================================================================
    # Sortable table implementation (SortableTableMixin)
    # =========================================================================

    # Column definitions: (key, label_translation_key, width)
    COLUMNS = [
        ("domain", "source.domain", 30),
        ("score", "source.score", 8),
        ("status", "source.status", 12),
        ("role", "source.role", 14),
        ("reliability", "source.reliability", 5),
        ("usages", "source.usage_count", 6),
        ("last_used", "source.last_used", 12),
        ("tags", "tags.label", 25),
    ]

    def get_sort_key(self, column_key: str):
        """Get sort key function for a column."""
        key_map = {
            "domain": lambda s: s.domain.lower(),
            "score": lambda s: s.personal_score,
            "status": lambda s: s.status or "",
            "role": lambda s: s.role or "",
            "reliability": lambda s: s.reliability or "",
            "usages": lambda s: s.usage_count,
            "last_used": lambda s: s.last_used or datetime.min,
            "tags": lambda s: ",".join(self.source_tags.get(s.id, [])),
        }
        return key_map.get(column_key, lambda s: "")

    def refresh_table(self) -> None:
        """Refresh the DataTable with current sources and sort state."""
        table = self.query_one("#sources-table", DataTable)
        table.clear(columns=True)

        # Add columns with sort indicators
        for key, label_key, width in self.COLUMNS:
            base_label = t(label_key)
            if self.sort_column == key:
                indicator = " ▼" if self.sort_reverse else " ▲"
                label = f"{base_label}{indicator}"
            else:
                label = base_label
            table.add_column(label, width=width, key=key)

        # Re-populate rows
        self._populate_table()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header click for sorting."""
        column_key = event.column_key.value

        if self.sort_column == column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_key
            self.sort_reverse = False

        self.sort_entries()
        self.refresh_table()

        direction = "▼" if self.sort_reverse else "▲"
        self.show_left_notify(f"Trié par {column_key} {direction}", 1.5)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Update detail panel when row selection changes."""
        if event.row_key is not None:
            try:
                idx = int(event.row_key.value)
                if 0 <= idx < len(self.sources):
                    self.selected_source = self.sources[idx]
                    self._update_detail_panel(self.selected_source)
            except (ValueError, TypeError):
                pass

    def _update_detail_panel(self, source) -> None:
        """Update the detail panel with source information."""
        title_widget = self.query_one("#detail-title", Static)
        meta_widget = self.query_one("#detail-meta", Static)
        content_widget = self.query_one("#detail-content", Static)

        title_widget.update(f"[bold cyan]{source.domain}[/bold cyan]")

        # Get backlinks count
        backlink_count = self.db.count_source_backlinks(source.id)

        # Get tags
        tags = self.source_tags.get(source.id, [])
        tags_str = ", ".join(tags) if tags else f"[dim]{t('tags.no_tags')}[/dim]"

        # Format dates
        created_str = source.created_at.strftime("%Y-%m-%d %H:%M")
        last_used_str = source.last_used.strftime("%Y-%m-%d %H:%M") if source.last_used else "—"
        last_verified_str = source.last_verified.strftime("%Y-%m-%d") if source.last_verified else "—"

        meta_lines = [
            f"[dim]ID:[/dim] {source.id}",
            f"[dim]{t('source.status')}:[/dim] {source.status}  "
            f"[dim]{t('source.role')}:[/dim] {source.role}  "
            f"[dim]{t('source.reliability')}:[/dim] {source.reliability}",
            f"[dim]{t('source.score')}:[/dim] {source.personal_score:.1f}/100  "
            f"[dim]{t('source.usage_count')}:[/dim] {source.usage_count}  "
            f"[dim]Backlinks:[/dim] {backlink_count}",
            f"[dim]{t('browse.created')}:[/dim] {created_str}  "
            f"[dim]{t('source.last_used')}:[/dim] {last_used_str}",
            f"[dim]Vérif.:[/dim] {last_verified_str}  "
            f"[dim]Decay:[/dim] {source.decay_rate}",
            f"[dim]{t('tags.label')}:[/dim] {tags_str}",
        ]

        # Add URL pattern if exists
        if source.url_pattern:
            meta_lines.append(f"[dim]URL:[/dim] {source.url_pattern}")

        # Add seed/promoted info
        if source.is_seed:
            meta_lines.append(f"[dim]Seed:[/dim] ✓ {source.seed_origin or ''}")
        if source.is_promoted:
            promoted_str = source.promoted_at.strftime("%Y-%m-%d") if source.promoted_at else "?"
            meta_lines.append(f"[dim]Promoted:[/dim] ✓ ({promoted_str})")

        meta_widget.update("\n".join(meta_lines))

        # Content area - show citation quality
        content_lines = []
        if source.citation_quality_factor > 0:
            cqf = source.citation_quality_factor
            if cqf >= 0.7:
                cqf_color = "green"
            elif cqf >= 0.4:
                cqf_color = "yellow"
            else:
                cqf_color = "red"
            content_lines.append(f"[dim]Citation Quality:[/dim] [{cqf_color}]{cqf:.2f}[/{cqf_color}]")

        content_widget.update("\n".join(content_lines) if content_lines else "")

    def action_quit(self) -> None:
        """Quit the app."""
        self.exit()

    def action_select_source(self) -> None:
        """Select source for viewing."""
        if self.selected_source:
            self.result_action = ("view", self.selected_source)
            self.exit()

    def action_edit_source(self) -> None:
        """Select source for editing."""
        if self.selected_source:
            self.result_action = ("edit", self.selected_source)
            self.exit()

    def action_delete_source(self) -> None:
        """Select source for deletion."""
        if self.selected_source:
            self.result_action = ("delete", self.selected_source)
            self.exit()

    def action_edit_tags(self) -> None:
        """Edit tags for selected source."""
        if self.selected_source:
            self.result_action = ("tags", self.selected_source)
            self.exit()

    def action_bulk_mode(self) -> None:
        """Enter bulk selection mode."""
        self.result_action = ("bulk", None)
        self.exit()

    def action_demote_source(self) -> None:
        """Demote selected source back to staging only."""
        if not self.selected_source:
            return

        # Check if source is promoted
        if not self.selected_source.is_promoted:
            self.show_left_notify("[yellow]Source is not promoted[/yellow]")
            return

        from rekall.promotion import demote_source

        result = demote_source(self.db, self.selected_source.id)
        if result.success:
            self.show_left_notify(t("promotion.demote.success"))
            # Remove from list and refresh table
            self.sources = [s for s in self.sources if s.id != self.selected_source.id]
            table = self.query_one("#sources-table", DataTable)
            table.clear()
            self._populate_table()
            if self.sources:
                self.selected_source = self.sources[0]
                self._update_detail_panel(self.selected_source)
        else:
            self.show_left_notify(f"[red]{result.error}[/red]")


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

    #preview-panel {
        height: 1fr;
        min-height: 10;
        border: solid #4367CD;
        margin: 1 1 0 1;
        padding: 0;
        background: $surface-darken-1;
    }

    #preview-title {
        text-style: bold;
        color: #93B5F7;
        padding: 0 1;
        height: auto;
    }

    #preview-scroll {
        height: 1fr;
        padding: 0 1;
    }

    #preview-panel Collapsible {
        padding: 0;
        margin: 0 0 1 0;
    }

    #preview-panel CollapsibleTitle {
        padding: 0 1;
        background: $surface-darken-2;
    }

    #preview-panel Collapsible > Contents {
        padding: 0 1;
    }

    .file-content {
        padding: 0;
        margin: 0;
    }

    .file-exists {
        color: green;
    }

    .file-new {
        color: yellow;
    }

    Footer {
        background: $surface-darken-1;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "back_or_quit", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("enter", "select_ide", "Select", show=True),
        Binding("l", "install_all_local", "Install Local", show=True),
        Binding("g", "install_all_global", "Install Global", show=True),
        Binding("L", "uninstall_all_local", "Uninstall Local", show=True),
        Binding("G", "uninstall_all_global", "Uninstall Global", show=True),
        Binding("c", "check_current", "Check", show=True),
        Binding("C", "check_all", "Check All", show=True),
    ]

    def __init__(self, ide_data: list, status: dict, stats: dict, base_path: Path):
        super().__init__()
        self.ide_data = ide_data  # [(name, desc, local_target, global_target), ...]
        self.status = status
        self.stats = stats
        self.base_path = base_path
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
            Container(
                Static("Files to install:", id="preview-title"),
                VerticalScroll(id="preview-scroll"),
                id="preview-panel",
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
        for name, desc, _local_target, _global_target in self.ide_data:
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

        # Focus on the table and show first IDE preview
        table.focus()
        if self.ide_data:
            self._update_preview(self.ide_data[0][0])

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Update preview when a different row is highlighted."""
        if event.row_key is not None:
            ide_name = str(event.row_key.value)
            self._update_preview(ide_name)

    def _update_preview(self, ide_name: str) -> None:
        """Update the preview panel with files for selected IDE."""
        from rekall.integrations import get_integration_files

        # Get files info - use global_install based on current status
        st = self.status.get(ide_name, {})
        # Show global files if integration supports global
        use_global = st.get("supports_global", False)

        files = get_integration_files(ide_name, self.base_path, global_install=use_global)

        # Update title
        title = self.query_one("#preview-title", Static)
        file_count = len(files)
        title.update(f"[bold #93B5F7]► {ide_name}[/] - {file_count} file{'s' if file_count != 1 else ''}")

        # Clear and rebuild preview scroll
        scroll = self.query_one("#preview-scroll", VerticalScroll)
        scroll.remove_children()

        if not files:
            scroll.mount(Static("[dim]No files to preview[/dim]"))
            return

        # Add collapsible for each file
        for i, file_info in enumerate(files):
            path = file_info["path"]
            content = file_info["content"]
            description = file_info["description"]
            exists = file_info["exists"]

            # Shorten path for display
            display_path = path.replace(str(Path.home()), "~")

            # Status indicator
            if exists:
                status = "[green]✓[/green]"
            else:
                status = "[yellow]NEW[/yellow]"

            # Create collapsible title
            coll_title = f"{status} {description}"

            # Truncate content for preview (first 50 lines max)
            lines = content.split('\n')
            if len(lines) > 50:
                preview_content = '\n'.join(lines[:50]) + f"\n... ({len(lines) - 50} more lines)"
            else:
                preview_content = content

            # Create collapsible (collapsed by default, first one expanded)
            collapsible = Collapsible(
                Static(f"[dim]{display_path}[/dim]\n\n{preview_content}", classes="file-content"),
                title=coll_title,
                collapsed=(i != 0),  # First one expanded
            )
            scroll.mount(collapsible)

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

    def action_uninstall_all_local(self) -> None:
        """Uninstall all IDEs locally."""
        if self.action_panel_visible:
            return
        if self.stats['local_installed'] > 0:
            self.result = ("uninstall_all", False)
            self.exit(result=self.result)
        else:
            self.show_left_notify("Aucun installé en local")

    def action_uninstall_all_global(self) -> None:
        """Uninstall all IDEs globally."""
        if self.action_panel_visible:
            return
        if self.stats['global_installed'] > 0:
            self.result = ("uninstall_all", True)
            self.exit(result=self.result)
        else:
            self.show_left_notify("Aucun installé en global")

    def action_check_current(self) -> None:
        """Check installation status of current IDE."""
        if self.action_panel_visible:
            return
        table = self.query_one("#status-table", DataTable)
        if table.cursor_row is None:
            return
        ide_name = self.ide_data[table.cursor_row][0]
        self._check_and_update_ide(ide_name)

    def action_check_all(self) -> None:
        """Check installation status of all IDEs."""
        if self.action_panel_visible:
            return
        for ide_name, _, _, _ in self.ide_data:
            self._check_and_update_ide(ide_name)
        self.show_left_notify(f"✓ {len(self.ide_data)} IDEs vérifiés")

    def _check_and_update_ide(self, ide_name: str) -> None:
        """Check and update status for a single IDE."""
        from rekall.integrations import get_ide_status

        # Get fresh status
        fresh_status = get_ide_status(self.base_path)
        st = fresh_status.get(ide_name, {})

        # Update internal status
        self.status[ide_name] = st

        # Update table row
        table = self.query_one("#status-table", DataTable)

        # Find row index
        row_idx = None
        for i, (name, _, _, _) in enumerate(self.ide_data):
            if name == ide_name:
                row_idx = i
                break

        if row_idx is None:
            return

        # Build new status strings
        if st.get("local"):
            local_str = "[green]✓[/green]"
        else:
            local_str = "[red]✗[/red]"

        if st.get("supports_global"):
            if st.get("global"):
                global_str = "[green]✓[/green]"
            else:
                global_str = "[red]✗[/red]"
        else:
            global_str = "[dim]—[/dim]"

        # Update cells
        row_key = table.get_row_at(row_idx)
        table.update_cell(row_key, "local", local_str)
        table.update_cell(row_key, "global", global_str)

        # Update stats
        self._recalculate_stats()

        # Update preview
        self._update_preview(ide_name)

    def _recalculate_stats(self) -> None:
        """Recalculate stats from current status."""
        local_installed = 0
        global_installed = 0
        local_not_installed = 0
        global_not_installed = 0

        for name, _, _, _ in self.ide_data:
            st = self.status.get(name, {})
            if st.get("local"):
                local_installed += 1
            else:
                local_not_installed += 1
            if st.get("supports_global"):
                if st.get("global"):
                    global_installed += 1
                else:
                    global_not_installed += 1

        self.stats = {
            "local_installed": local_installed,
            "global_installed": global_installed,
            "local_not_installed": local_not_installed,
            "global_not_installed": global_not_installed,
        }

        # Update legend
        stats_text = f"Local: {local_installed} ✓ / {local_not_installed} ✗ | Global: {global_installed} ✓ / {global_not_installed} ✗"
        legend = self.query_one("#legend", Static)
        legend.update(f"[dim]✓ {t('ide.installed')}  ✗ {t('ide.not_installed')}  — {t('ide.not_supported')}  |  {stats_text}[/dim]")

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

    #preview-panel {
        height: 1fr;
        min-height: 10;
        border: solid #4367CD;
        margin: 1 1 0 1;
        padding: 0;
        background: $surface-darken-1;
    }

    #preview-title {
        text-style: bold;
        color: #93B5F7;
        padding: 0 1;
        height: auto;
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
        Binding("i", "install_current", "Install", show=True),
        Binding("I", "install_all", "Install All", show=True),
        Binding("u", "uninstall_current", "Uninstall", show=True),
        Binding("U", "uninstall_all", "Uninstall All", show=True),
    ]

    def __init__(self, status: dict, components: list, labels: dict):
        super().__init__()
        self.status = status
        self.components = components
        self.labels = labels
        self.result = None
        self.selected_component = None  # Currently selected component key
        self.highlighted_component = None  # Currently highlighted component
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
            Static(f"[dim]✓ {t('ide.installed')}  ✗ {t('ide.not_installed')}  ⚠ {t('speckit.file_missing')}  |  i/I install  u/U uninstall  |  {stats_text}[/dim]", id="legend"),
            Container(
                Static("", id="action-title"),
                ListView(id="action-list"),
                id="action-panel",
            ),
            Container(
                Static("Preview", id="preview-title"),
                VerticalScroll(
                    Markdown("", id="preview-content"),
                    id="preview-box",
                ),
                id="preview-panel",
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

        # Initialize preview with first component
        if self.components:
            self.highlighted_component = self.components[0]
            self._update_preview(self.components[0])

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

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight (arrow keys) - always update preview."""
        if event.row_key:
            component = str(event.row_key.value)
            self.highlighted_component = component
            self._update_preview(component)

    def _update_preview(self, component: str) -> None:
        """Update preview panel for the given component."""
        from rekall.integrations import get_speckit_preview, get_speckit_uninstall_preview

        st = self.status.get(component)
        label = self.labels.get(component, component)

        # Update title
        title = self.query_one("#preview-title", Static)
        status_icon = "[green]✓[/green]" if st is True else "[red]✗[/red]" if st is False else "[yellow]⚠[/yellow]"
        title.update(f"{status_icon} {label}")

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

            # Update preview to reflect new state
            if self.highlighted_component:
                self._update_preview(self.highlighted_component)

        except Exception as e:
            self.show_left_notify(f"✗ {t('common.error')}: {e}")

        # Only hide action panel if it was visible (from Enter key flow)
        if self.action_panel_visible:
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
        legend.update(f"[dim]✓ {t('ide.installed')}  ✗ {t('ide.not_installed')}  ⚠ {t('speckit.file_missing')}  |  i/I install  u/U uninstall  |  {stats_text}[/dim]")

    def action_back_or_quit(self) -> None:
        """Escape - hide panel or quit."""
        if self.action_panel_visible:
            self._hide_action_panel()
        else:
            self.exit(result=None)

    def action_install_current(self) -> None:
        """Install the currently highlighted component."""
        if self.action_panel_visible:
            return
        if not self.highlighted_component:
            return
        st = self.status.get(self.highlighted_component)
        if st is False:
            self._execute_action("install", self.highlighted_component)
        elif st is True:
            self.show_left_notify(t("speckit.already_installed"))
        else:
            self.show_left_notify(t("speckit.file_missing"))

    def action_uninstall_current(self) -> None:
        """Uninstall the currently highlighted component."""
        if self.action_panel_visible:
            return
        if not self.highlighted_component:
            return
        st = self.status.get(self.highlighted_component)
        if st is True:
            self._execute_action("uninstall", self.highlighted_component)
        elif st is False:
            self.show_left_notify(t("speckit.not_installed"))
        else:
            self.show_left_notify(t("speckit.file_missing"))

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
_db: Database | None = None


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


class MCPConfigApp(App):
    """Textual app for MCP Server configuration with CLI selector."""

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

    #main-container {
        height: 1fr;
        padding: 0 2;
    }

    #status-section {
        height: auto;
        margin-bottom: 1;
    }

    #cli-selector {
        height: 3;
        border: solid $primary;
        padding: 0 2;
        margin: 1 0;
    }

    #cli-label {
        width: 100%;
        text-align: center;
    }

    #config-section {
        height: 1fr;
        border: solid $secondary;
        padding: 1 2;
        background: $surface-darken-1;
    }

    #config-scroll {
        height: 100%;
    }

    #footer-hint {
        dock: bottom;
        height: 1;
        padding: 0 2;
        color: $text-muted;
    }

    #info-overlay {
        display: none;
        layer: modal;
        width: 100%;
        height: 100%;
        align: center middle;
        color: $text;
    }

    #info-overlay.visible {
        display: block;
    }

    #info-content {
        text-align: center;
        width: 50;
        padding: 1 2;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "quit_or_close", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("left", "prev_cli", "←", show=True),
        Binding("right", "next_cli", "→", show=True),
        Binding("i", "install_config", "Install", show=True),
        Binding("r", "remove_config", "Remove", show=True),
        Binding("c", "copy_config", "Copy", show=True),
        Binding("question_mark", "toggle_info", "?", show=True),
    ]

    def __init__(self, cli_configs: dict, deps_ok: bool):
        super().__init__()
        self.cli_configs = cli_configs
        self.cli_keys = list(cli_configs.keys())
        self.selected_idx = 0
        self.deps_ok = deps_ok

    def compose(self) -> ComposeResult:
        yield create_banner_container()
        with Container(id="main-container"):
            # Status section
            yield Static(self._build_status(), id="status-section", markup=True)
            # CLI selector
            with Container(id="cli-selector"):
                yield Static(self._build_cli_selector(), id="cli-label", markup=True)
            # Config section
            with VerticalScroll(id="config-scroll"):
                yield Static(self._build_config(), id="config-section", markup=True)
        yield Static("[dim]←/→ change CLI • i install • r remove • c copy • ? info • Esc back[/dim]", id="footer-hint")
        yield Static("", id="left-notify")
        # Info overlay
        with Container(id="info-overlay"):
            yield Static(self._build_info_text(), id="info-content", markup=True)

    def _check_cli_installed(self) -> bool:
        """Check if Rekall is configured in the current CLI's config file."""
        import json
        from pathlib import Path

        cli_config = self.cli_configs[self.cli_keys[self.selected_idx]]
        file_path_str = cli_config["file"]

        if file_path_str.startswith("~"):
            file_path = Path(file_path_str).expanduser()
        elif file_path_str.startswith("."):
            file_path = Path.home() / file_path_str
        else:
            file_path = Path(file_path_str)

        if not file_path.exists():
            return False

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return False
                config = json.loads(content)

            # Check all possible formats
            if "mcpServers" in config:
                if isinstance(config["mcpServers"], dict):
                    return "rekall" in config["mcpServers"]
                elif isinstance(config["mcpServers"], list):
                    return any(e.get("name") == "rekall" for e in config["mcpServers"])
            if "context_servers" in config:
                return "rekall" in config["context_servers"]
            if "mcp" in config:
                return "rekall" in config["mcp"]
            return False
        except Exception:
            return False

    def _build_status(self) -> str:
        """Build status section content."""
        cli_name = self.cli_configs[self.cli_keys[self.selected_idx]]["name"]
        cli_installed = self._check_cli_installed()

        lines = ["[bold]MCP Server[/bold]"]

        # Package status
        if self.deps_ok:
            lines.append("[green]✓[/green] Package mcp installé")
        else:
            lines.append("[yellow]⚠[/yellow] Package manquant: [dim]pip install mcp[/dim]")

        # CLI config status
        if cli_installed:
            lines.append(f"[green]✓[/green] Configuré dans {cli_name}")
        else:
            lines.append(f"[dim]○[/dim] Non configuré dans {cli_name}")

        return "\n".join(lines)

    def _build_cli_selector(self) -> str:
        """Build CLI selector with arrows."""
        # Show all CLIs with current highlighted using reverse video
        parts = []
        for i, key in enumerate(self.cli_keys):
            name = self.cli_configs[key]["name"]
            if i == self.selected_idx:
                # Reverse video for selected CLI (text inverse)
                parts.append(f"[reverse] {name} [/reverse]")
            else:
                parts.append(f"[dim]{name}[/dim]")
        return "  ".join(parts)

    def _build_config(self) -> str:
        """Build config section content."""
        cli_config = self.cli_configs[self.cli_keys[self.selected_idx]]
        return f"""[cyan]File:[/cyan] {cli_config['file']}

[cyan]Configuration:[/cyan]
[dim]{cli_config['config']}[/dim]

[yellow]Add this to your config file to enable Rekall MCP server.[/yellow]"""

    def _build_info_text(self) -> str:
        """Build info overlay content."""
        return """[bold]MCP (Model Context Protocol)[/bold]

MCP permet aux agents IA (Claude, etc.)
d'accéder à vos souvenirs Rekall.

[cyan]Server ready[/cyan] = rekall mcp-server peut démarrer
[yellow]pip install mcp[/yellow] = dépendance manquante

[dim]? ou Esc pour fermer[/dim]"""

    def _update_display(self) -> None:
        """Update display after CLI change."""
        self.query_one("#status-section", Static).update(self._build_status())
        self.query_one("#cli-label", Static).update(self._build_cli_selector())
        self.query_one("#config-section", Static).update(self._build_config())

    def show_left_notify(self, message: str, timeout: float = 3.0) -> None:
        """Show a notification on the left side."""
        notify_widget = self.query_one("#left-notify", Static)
        notify_widget.update(message)
        notify_widget.add_class("visible")
        self.set_timer(timeout, lambda: notify_widget.remove_class("visible"))

    def action_prev_cli(self) -> None:
        """Select previous CLI."""
        self.selected_idx = (self.selected_idx - 1) % len(self.cli_keys)
        self._update_display()
        cli_name = self.cli_configs[self.cli_keys[self.selected_idx]]["name"]
        self.show_left_notify(f"→ {cli_name}", 1.5)

    def action_next_cli(self) -> None:
        """Select next CLI."""
        self.selected_idx = (self.selected_idx + 1) % len(self.cli_keys)
        self._update_display()
        cli_name = self.cli_configs[self.cli_keys[self.selected_idx]]["name"]
        self.show_left_notify(f"→ {cli_name}", 1.5)

    def action_copy_config(self) -> None:
        """Copy current config to clipboard."""
        try:
            import subprocess
            cli_config = self.cli_configs[self.cli_keys[self.selected_idx]]
            subprocess.run(["pbcopy"], input=cli_config["config"].encode(), check=True)
            self.show_left_notify("✓ Config copied", 2.0)
        except Exception:
            self.show_left_notify("⚠ Could not copy", 2.0)

    def action_install_config(self) -> None:
        """Install MCP config to the selected CLI's config file."""
        cli_key = self.cli_keys[self.selected_idx]
        cli_config = self.cli_configs[cli_key]
        result = _install_mcp_config(cli_config)
        self.show_left_notify(result, 4.0)
        self._update_display()  # Refresh status

    def action_remove_config(self) -> None:
        """Remove MCP config from the selected CLI's config file."""
        cli_key = self.cli_keys[self.selected_idx]
        cli_config = self.cli_configs[cli_key]
        result = _uninstall_mcp_config(cli_config)
        self.show_left_notify(result, 4.0)
        self._update_display()  # Refresh status

    def action_toggle_info(self) -> None:
        """Toggle info overlay visibility."""
        overlay = self.query_one("#info-overlay", Container)
        overlay.toggle_class("visible")

    def action_quit_or_close(self) -> None:
        """Close overlay if open, otherwise quit."""
        overlay = self.query_one("#info-overlay", Container)
        if overlay.has_class("visible"):
            overlay.remove_class("visible")
        else:
            self.exit()

    def action_quit(self) -> None:
        self.exit()


class InfoDisplayApp(App):
    """Simple app to display info with Escape/Enter/Q to exit."""

    CSS = """
    Screen {
        background: $surface;
    }

    #scroll-container {
        height: 1fr;
    }

    #content {
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
        Binding("up", "scroll_up", "Scroll up", show=False),
        Binding("down", "scroll_down", "Scroll down", show=False),
        Binding("pageup", "page_up", "Page up", show=False),
        Binding("pagedown", "page_down", "Page down", show=False),
    ]

    def __init__(self, content: str, title: str = ""):
        super().__init__()
        self.content_text = content
        self.title_text = title

    def compose(self) -> ComposeResult:
        yield create_banner_container()
        with VerticalScroll(id="scroll-container"):
            yield Static(self.content_text, id="content", markup=True)
        yield Static("[dim]↑↓ scroll • Escape/Enter/Q to continue[/dim]", id="footer-hint")

    def action_scroll_up(self) -> None:
        self.query_one("#scroll-container").scroll_up()

    def action_scroll_down(self) -> None:
        self.query_one("#scroll-container").scroll_down()

    def action_page_up(self) -> None:
        self.query_one("#scroll-container").scroll_page_up()

    def action_page_down(self) -> None:
        self.query_one("#scroll-container").scroll_page_down()

    def action_quit(self) -> None:
        self.exit()


def show_info(content: str, title: str = ""):
    """Display info screen with Escape/Enter/Q to exit."""
    app = InfoDisplayApp(content, title)
    app.run()


class EscapePressed(Exception):
    """Raised when user presses Escape during input."""
    pass


def prompt_input(label: str, required: bool = True) -> str | None:
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
    """Configuration & Maintenance - unified flat menu with visual groupings."""
    from pathlib import Path

    from rekall.config import get_config
    from rekall.paths import PathResolver

    pending_notification = ""

    while True:
        config = get_config()

        # Detect database state
        local_rekall = Path.cwd() / ".rekall"
        local_db = local_rekall / "knowledge.db"
        has_local = local_rekall.exists()
        has_local_db = local_db.exists()

        resolver = PathResolver()
        global_paths = resolver._from_xdg()
        global_db = global_paths.db_path if global_paths else Path.home() / ".local" / "share" / "rekall" / "knowledge.db"
        has_global_db = global_db.exists()

        # Status indicators
        global_icon = "[green]✓[/green]" if has_global_db else "[dim]○[/dim]"
        local_icon = "[green]✓[/green]" if has_local_db else ("[yellow]⚠[/yellow]" if has_local else "[dim]○[/dim]")
        emb_icon = "[green]✓[/green]" if config.smart_embeddings_enabled else "[dim]○[/dim]"

        # Build flat menu with section headers
        menu_options = []
        actions = []

        # ─── INTEGRATIONS ───
        menu_options.append("─── INTEGRATIONS ───")
        actions.append(None)

        menu_options.append("  ⚙ Intégration IDE")
        actions.append("ide")

        # MCP Server status
        mcp_icon = "[green]✓[/green]" if _check_mcp_deps() else "[dim]○[/dim]"
        menu_options.append(f"  {mcp_icon} Installation MCP")
        actions.append("configure_mcp")

        menu_options.append("  📦 Intégration Speckit")
        actions.append("speckit")

        # Spacer + SETTINGS section (Feature 007)
        menu_options.append("")
        actions.append(None)
        menu_options.append("─── SETTINGS ───")
        actions.append(None)

        # Smart Embeddings subsection
        menu_options.append(f"  {emb_icon} Smart Embeddings")
        actions.append("configure_embeddings")

        # Context mode display (indented under Smart Embeddings)
        mode_display = {
            "required": "[green]required[/green]",
            "recommended": "[yellow]recommended[/yellow]",
            "optional": "[dim]optional[/dim]",
        }
        current_mode = config.smart_embeddings_context_mode
        menu_options.append(f"      └─ Context: {mode_display.get(current_mode, current_mode)}")
        actions.append("settings_context_mode")

        # Max context size display (indented under Smart Embeddings)
        size_kb = config.max_context_size // 1024
        menu_options.append(f"      └─ Max size: {size_kb} KB")
        actions.append("settings_max_context_size")

        # Spacer + DATABASE section
        menu_options.append("")
        actions.append(None)
        menu_options.append("─── DATABASE ───")
        actions.append(None)

        menu_options.append(f"  ⓘ {t('maintenance.db_info')}")
        actions.append("db_info")

        if has_global_db:
            menu_options.append(f"  {global_icon} {t('setup.use_global')}")
            actions.append("use_global")
        else:
            menu_options.append(f"  {global_icon} {t('setup.create_global')}")
            actions.append("create_global")

        if has_local_db:
            menu_options.append(f"  {local_icon} {t('setup.use_local')}")
            actions.append("use_local")
        else:
            menu_options.append(f"  {local_icon} {t('setup.create_local')}")
            actions.append("create_local")

        if has_global_db and not has_local_db:
            menu_options.append(f"  → {t('setup.copy_global_to_local')}")
            actions.append("migrate_to_local")
        if has_local_db and not has_global_db:
            menu_options.append(f"  → {t('setup.copy_local_to_global')}")
            actions.append("migrate_to_global")

        # Spacer + ABOUT section
        menu_options.append("")
        actions.append(None)
        menu_options.append("─── ABOUT ───")
        actions.append(None)

        menu_options.append(f"  📋 {t('about.changelog')}")
        actions.append("changelog")

        menu_options.append(f"  ⓘ {t('about.version')}")
        actions.append("version_info")

        # Back
        menu_options.append("")
        actions.append(None)
        menu_options.append(f"← {t('setup.back')}")
        actions.append("back")

        # Show menu with pending notification
        title = f"{t('menu.config')} | {t('setup.current_source')}: {config.paths.source.value}"
        app = SimpleMenuApp(title, menu_options, pending_notification)
        pending_notification = ""  # Clear after use
        idx = app.run()

        if idx is None:
            return
        idx = int(idx) if isinstance(idx, str) else idx

        if idx >= len(actions):
            return

        action = actions[idx]
        if action is None or action == "back":
            return

        # Execute action
        if action == "db_info":
            _show_db_info()
        elif action == "use_global":
            pending_notification = "✓ Base globale déjà active"
        elif action == "use_local":
            pending_notification = "✓ Base locale déjà active"
        elif action == "create_global":
            _setup_global()
        elif action == "create_local":
            _setup_local()
        elif action == "migrate_to_local":
            _migrate_db(global_db, local_rekall / "knowledge.db", "GLOBAL → LOCAL")
        elif action == "migrate_to_global":
            _migrate_db(local_db, global_db, "LOCAL → GLOBAL")
        elif action == "configure_embeddings":
            _configure_embeddings()
        elif action == "configure_mcp":
            _configure_mcp()
        elif action == "ide":
            _ide_integration_submenu()
        elif action == "speckit":
            action_speckit_integration()
        elif action == "settings_context_mode":
            _configure_context_mode()
        elif action == "settings_max_context_size":
            _configure_max_context_size()
        elif action == "changelog":
            _show_changelog()
        elif action == "version_info":
            _show_version_info()


def _show_changelog():
    """Display changelog in TUI."""
    changelog = get_changelog_content()
    if changelog:
        show_info(changelog)
    else:
        show_info(f"[dim]{t('about.changelog_not_found')}[/dim]")


def _show_version_info():
    """Display version information in TUI."""
    from rekall import __release_date__, __version__
    from rekall.db import CURRENT_SCHEMA_VERSION

    info_text = f"""[bold]{t('about.version_title')}[/bold]

[cyan]Rekall:[/cyan]      v{__version__}
[cyan]{t('about.release_date')}:[/cyan]  {__release_date__}
[cyan]{t('info.schema')}:[/cyan]    v{CURRENT_SCHEMA_VERSION}
"""
    show_info(info_text)


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
        uninstall_all_ide,
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

        for name, _desc, _local_target, _global_target in filtered:
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
        app = IDEStatusApp(filtered, status, stats, Path.cwd())
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
        elif action == "uninstall_all":
            # Bulk uninstall: ("uninstall_all", global_bool)
            global_install = result[1]
            loc = "GLOBAL" if global_install else "LOCAL"
            res = uninstall_all_ide(Path.cwd(), global_install)
            removed_count = len(res.get("removed", []))
            show_toast(f"✓ Désinstallation {loc}: {removed_count} IDE(s)", 2.0)


def action_speckit_integration():
    """Manage Speckit integration with component selection using Textual."""
    from rekall.integrations import (
        SPECKIT_PATCHES,
        get_speckit_status,
    )

    # Component display names
    COMPONENT_LABELS = {
        "article_short": "Article XCIX - Court (~350 tokens) ★ recommandé",
        "article_extensive": "Article XCIX - Extensif (~1000 tokens)",
        "speckit.implement.md": "speckit.implement.md",
        "speckit.clarify.md": "speckit.clarify.md",
        "speckit.specify.md": "speckit.specify.md",
        "speckit.plan.md": "speckit.plan.md",
        "speckit.tasks.md": "speckit.tasks.md",
        "speckit.hotfix.md": "speckit.hotfix.md",
    }

    # All components in order (skill is now installed via Claude Code IDE integration)
    ALL_COMPONENTS = ["article_short", "article_extensive"] + list(SPECKIT_PATCHES.keys())

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


# =============================================================================
# Sources Dashboard (Feature 009)
# =============================================================================


def action_sources():
    """Unified Sources Manager - manage Sources, Inbox, and Staging."""
    db = get_db()

    result = run_unified_sources(db)

    # Handle result actions that need external processing
    if result:
        action_type, item = result
        if action_type == "tags":
            _edit_source_tags_standalone(db, item)
        elif action_type == "enrich":
            # Trigger enrichment for inbox entry
            from rekall.sources_inbox import enrich_inbox_entry
            enrich_inbox_entry(db, item.id)


def _edit_source_tags_standalone(db, source):
    """Edit tags for a source (standalone function for external call)."""
    while True:
        current_tags = db.get_source_themes(source.id)

        menu_options = []
        menu_options.append(f"[bold]{source.domain}[/bold]")
        menu_options.append("")
        menu_options.append(f"Tags: {', '.join(current_tags) if current_tags else '[dim]aucun[/dim]'}")
        menu_options.append("")

        if current_tags:
            for tag in current_tags:
                menu_options.append(f"  ❌ Retirer: {tag}")

        menu_options.append("")
        menu_options.append("  ➕ Ajouter un tag")
        menu_options.append(f"← {t('common.back')}")

        app = SimpleMenuApp("Éditer les tags", menu_options)
        idx = app.run()

        if idx is None:
            return

        # Calculate indices
        first_tag_idx = 4  # After header
        add_tag_idx = first_tag_idx + len(current_tags) + 1
        back_idx = add_tag_idx + 1

        if idx == back_idx or idx == back_idx - 1:  # Back
            return
        elif idx == add_tag_idx:  # Add tag
            all_tags = db.get_all_tags_with_counts()
            existing_tag_names = [t["theme"] for t in all_tags]

            tag_options = [f"{t['theme']} ({t['count']})" for t in all_tags]
            tag_options.append("")
            tag_options.append("✏️  Nouveau tag...")
            tag_options.append(f"← {t('common.cancel')}")

            tag_app = SimpleMenuApp("Choisir un tag", tag_options)
            tag_idx = tag_app.run()

            if tag_idx is None or tag_idx >= len(existing_tag_names) + 2:
                continue

            if tag_idx == len(existing_tag_names) + 1:  # New tag
                new_tag = show_input("Nom du nouveau tag:")
                if new_tag and new_tag.strip():
                    db.add_source_theme(source.id, new_tag.strip())
            elif tag_idx < len(existing_tag_names):
                selected_tag = existing_tag_names[tag_idx]
                if selected_tag not in current_tags:
                    db.add_source_theme(source.id, selected_tag)

        elif first_tag_idx <= idx < first_tag_idx + len(current_tags):
            # Remove tag
            tag_to_remove = current_tags[idx - first_tag_idx]
            db.remove_source_theme(source.id, tag_to_remove)


def _score_bar(score: float, width: int = 5) -> str:
    """Create a visual score bar."""
    filled = int((score / 100) * width)
    empty = width - filled
    return f"[green]{'█' * filled}[/green][dim]{'░' * empty}[/dim]"


def _role_icon(role: str) -> str:
    """Get icon for source role (Feature 010).

    Args:
        role: Source role (hub, authority, unclassified)

    Returns:
        Unicode icon representing the role
    """
    icons = {
        "authority": "📚",  # Official/canonical sources
        "hub": "🔗",        # Aggregators, indexes
        "unclassified": "📄",  # Default/unknown
    }
    return icons.get(role, "📄")


def _verify_source_links(db):
    """Verify accessibility of source links with progress display."""
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn

    from rekall.link_rot import verify_sources

    console = Console()

    # Count sources pending verification (not checked in last 24h)
    pending_normal = len(db.get_sources_to_verify(days_since_check=1, limit=1000))
    # Count all sources with domain
    total_sources = db.conn.execute(
        "SELECT COUNT(*) FROM sources WHERE domain IS NOT NULL AND domain != ''"
    ).fetchone()[0]

    # Build menu options
    menu_options = []

    if pending_normal == 0:
        menu_options.append("✓ Toutes les sources vérifiées (24h)")
        menu_options.append("")
        menu_options.append(f"🔄 {t('sources.verify_force')} ({total_sources} sources)")
        menu_options.append(f"← {t('common.cancel')}")
        force_indices = {2: True}  # Index 2 = force all
    else:
        menu_options.append(f"📊 À vérifier: {pending_normal}/{total_sources}")
        menu_options.append("")
        menu_options.append("ℹ️  Par défaut: sources non vérifiées depuis 24h")
        menu_options.append("    (max 50 par session)")
        menu_options.append("")
        menu_options.append(f"▶ Vérifier {min(pending_normal, 50)} sources")
        menu_options.append(f"🔄 {t('sources.verify_force')} ({total_sources} sources)")
        menu_options.append(f"← {t('common.cancel')}")
        force_indices = {5: False, 6: True}  # 5 = normal, 6 = force

    # Show menu
    app = SimpleMenuApp(t("sources.verify_title"), menu_options)
    idx = app.run()

    if idx is None:
        return

    # Determine action from selection
    if pending_normal == 0:
        if idx != 2:
            return
        force_all = True
    else:
        if idx not in force_indices:
            return
        force_all = force_indices[idx]

    # Determine parameters
    if force_all:
        days_since_check = 0
        limit = 1000  # All sources
    else:
        days_since_check = 1
        limit = 50

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            console=console,
            transient=False,
        ) as progress:
            task = progress.add_task("Vérification...", total=limit)

            def on_progress(current, total, domain):
                progress.update(task, total=total, completed=current)
                progress.update(task, description=f"🔍 {domain[:30]}")

            results = verify_sources(
                db,
                limit=limit,
                on_progress=on_progress,
                days_since_check=days_since_check,
            )

        msg = (
            f"✓ Vérification terminée:\n"
            f"  • Vérifiés: {results['verified']}\n"
            f"  • Accessibles: {results['accessible']}\n"
            f"  • Inaccessibles: {results['inaccessible']}"
        )
        show_info(msg)
    except Exception as e:
        show_toast(f"⚠ Erreur: {e}")


def _browse_by_tag(db):
    """Browse sources by tag - shows tag list with counts, then sources for selected tag."""
    while True:
        # Get all tags with counts
        tags = db.get_all_tags_with_counts()

        if not tags:
            show_toast(t("tags.no_tags"))
            return

        # Build menu options
        menu_options = []
        for tag_info in tags:
            menu_options.append(t("tags.count", tag=tag_info["theme"], count=tag_info["count"]))

        menu_options.append("")
        menu_options.append(f"← {t('common.back')}")

        app = SimpleMenuApp(t("tags.browse_by_tag"), menu_options)
        idx = app.run()

        if idx is None or idx >= len(tags):
            return

        # Show sources for selected tag
        selected_tag = tags[idx]["theme"]
        _show_sources_for_tag(db, selected_tag)


def _show_sources_for_tag(db, tag: str):
    """Show sources associated with a specific tag using DataTable view."""
    while True:
        sources = db.get_sources_by_tags([tag])

        if not sources:
            show_toast(t("filter.no_results"))
            return

        app = SourcesBrowseApp(sources, db, title=f"🏷️ {tag}")
        app.run()

        if app.result_action is None:
            return

        action, source = app.result_action

        if action == "view":
            _show_source_detail(db, source)
        elif action == "edit":
            _edit_source(db, source)
        elif action == "delete":
            _delete_source(db, source)
        elif action == "tags":
            _edit_source_tags(db, source)
        elif action == "bulk":
            _bulk_select_sources(db, sources)


def _advanced_search_sources(db):
    """Advanced search with multiple filter criteria."""
    # Current filter state
    filters = {
        "tags": [],
        "score_min": None,
        "score_max": None,
        "statuses": [],
        "roles": [],
        "last_used_days": None,
        "text_search": None,
    }

    while True:
        # Build filter summary
        filter_summary = []
        if filters["tags"]:
            filter_summary.append(f"Tags: {', '.join(filters['tags'])}")
        if filters["score_min"] is not None or filters["score_max"] is not None:
            smin = filters["score_min"] or 0
            smax = filters["score_max"] or 100
            filter_summary.append(f"Score: {smin}-{smax}")
        if filters["statuses"]:
            filter_summary.append(f"Statuts: {', '.join(filters['statuses'])}")
        if filters["roles"]:
            filter_summary.append(f"Rôles: {', '.join(filters['roles'])}")
        if filters["last_used_days"]:
            filter_summary.append(t("filter.freshness_days", days=filters["last_used_days"]))
        if filters["text_search"]:
            filter_summary.append(f"Texte: {filters['text_search']}")

        # Build menu
        menu_options = [
            f"🏷️ Tags: {', '.join(filters['tags']) or '-'}",
            f"📊 Score: {filters['score_min'] or 0}-{filters['score_max'] or 100}",
            f"📋 Statuts: {', '.join(filters['statuses']) or '-'}",
            f"👤 Rôles: {', '.join(filters['roles']) or '-'}",
            f"📅 Fraîcheur: {filters['last_used_days'] or '-'} jours",
            f"🔤 Texte: {filters['text_search'] or '-'}",
            "",
            f"▶️ {t('filter.apply')}",
            f"🗑️ {t('filter.clear')}",
            "",
            f"← {t('common.back')}",
        ]

        title = t("filter.title")
        if filter_summary:
            title += f" ({len(filter_summary)} filtre(s))"

        app = SimpleMenuApp(title, menu_options)
        idx = app.run()

        if idx is None or idx == 10:  # Back
            return

        if idx == 0:  # Tags
            _select_filter_tags(db, filters)
        elif idx == 1:  # Score
            _select_filter_score(filters)
        elif idx == 2:  # Statuts
            _select_filter_statuses(filters)
        elif idx == 3:  # Rôles
            _select_filter_roles(filters)
        elif idx == 4:  # Fraîcheur
            _select_filter_freshness(filters)
        elif idx == 5:  # Texte
            _select_filter_text(filters)
        elif idx == 7:  # Apply
            _apply_advanced_filter(db, filters)
        elif idx == 8:  # Clear
            filters = {
                "tags": [],
                "score_min": None,
                "score_max": None,
                "statuses": [],
                "roles": [],
                "last_used_days": None,
                "text_search": None,
            }
            show_toast("✓ Filtres effacés")


def _select_filter_tags(db, filters: dict):
    """Select tags for filtering."""
    all_tags = db.get_all_tags_with_counts()
    if not all_tags:
        show_toast(t("tags.no_tags"))
        return

    selected = set(filters["tags"])

    while True:
        menu_options = []
        for tag_info in all_tags:
            tag = tag_info["theme"]
            checkbox = "☑" if tag in selected else "☐"
            menu_options.append(f"{checkbox} {tag} ({tag_info['count']})")

        menu_options.append("")
        menu_options.append(f"✓ Confirmer ({len(selected)} sélectionné(s))")
        menu_options.append(f"← {t('common.back')}")

        app = SimpleMenuApp(f"{t('filter.by_score')} - Tags", menu_options)
        idx = app.run()

        if idx is None or idx >= len(all_tags) + 2:
            return
        elif idx == len(all_tags) + 1:
            filters["tags"] = list(selected)
            return
        elif idx < len(all_tags):
            tag = all_tags[idx]["theme"]
            if tag in selected:
                selected.remove(tag)
            else:
                selected.add(tag)


def _select_filter_score(filters: dict):
    """Select score range for filtering."""
    menu_options = [
        "0-25 (Bas)",
        "25-50 (Moyen-bas)",
        "50-75 (Moyen-haut)",
        "75-100 (Haut)",
        "30-100 (Utilisé)",
        "Personnalisé...",
        "",
        f"← {t('common.back')}",
    ]

    app = SimpleMenuApp(t("filter.by_score"), menu_options)
    idx = app.run()

    if idx == 0:
        filters["score_min"], filters["score_max"] = 0, 25
    elif idx == 1:
        filters["score_min"], filters["score_max"] = 25, 50
    elif idx == 2:
        filters["score_min"], filters["score_max"] = 50, 75
    elif idx == 3:
        filters["score_min"], filters["score_max"] = 75, 100
    elif idx == 4:
        filters["score_min"], filters["score_max"] = 30, 100
    elif idx == 5:
        min_input = prompt_input("Score minimum (0-100)")
        max_input = prompt_input("Score maximum (0-100)")
        try:
            filters["score_min"] = int(min_input) if min_input else None
            filters["score_max"] = int(max_input) if max_input else None
        except ValueError:
            show_toast("⚠ Valeurs invalides")


def _select_filter_statuses(filters: dict):
    """Select statuses for filtering."""
    all_statuses = ["active", "dormant", "inaccessible", "archived"]
    selected = set(filters["statuses"])

    while True:
        menu_options = []
        for status in all_statuses:
            checkbox = "☑" if status in selected else "☐"
            menu_options.append(f"{checkbox} {status}")

        menu_options.append("")
        menu_options.append(f"✓ Confirmer ({len(selected)} sélectionné(s))")
        menu_options.append(f"← {t('common.back')}")

        app = SimpleMenuApp(t("filter.by_status"), menu_options)
        idx = app.run()

        if idx is None or idx >= len(all_statuses) + 2:
            return
        elif idx == len(all_statuses) + 1:
            filters["statuses"] = list(selected)
            return
        elif idx < len(all_statuses):
            status = all_statuses[idx]
            if status in selected:
                selected.remove(status)
            else:
                selected.add(status)


def _select_filter_roles(filters: dict):
    """Select roles for filtering."""
    all_roles = ["hub", "authority", "unclassified"]
    selected = set(filters["roles"])

    while True:
        menu_options = []
        for role in all_roles:
            checkbox = "☑" if role in selected else "☐"
            menu_options.append(f"{checkbox} {role}")

        menu_options.append("")
        menu_options.append(f"✓ Confirmer ({len(selected)} sélectionné(s))")
        menu_options.append(f"← {t('common.back')}")

        app = SimpleMenuApp(t("filter.by_role"), menu_options)
        idx = app.run()

        if idx is None or idx >= len(all_roles) + 2:
            return
        elif idx == len(all_roles) + 1:
            filters["roles"] = list(selected)
            return
        elif idx < len(all_roles):
            role = all_roles[idx]
            if role in selected:
                selected.remove(role)
            else:
                selected.add(role)


def _select_filter_freshness(filters: dict):
    """Select freshness filter (last used within N days)."""
    menu_options = [
        "7 jours",
        "30 jours",
        "90 jours",
        "180 jours",
        "365 jours",
        "Personnalisé...",
        "Aucun filtre",
        "",
        f"← {t('common.back')}",
    ]

    app = SimpleMenuApp(t("filter.by_freshness"), menu_options)
    idx = app.run()

    if idx == 0:
        filters["last_used_days"] = 7
    elif idx == 1:
        filters["last_used_days"] = 30
    elif idx == 2:
        filters["last_used_days"] = 90
    elif idx == 3:
        filters["last_used_days"] = 180
    elif idx == 4:
        filters["last_used_days"] = 365
    elif idx == 5:
        days_input = prompt_input("Nombre de jours")
        try:
            filters["last_used_days"] = int(days_input) if days_input else None
        except ValueError:
            show_toast("⚠ Valeur invalide")
    elif idx == 6:
        filters["last_used_days"] = None


def _select_filter_text(filters: dict):
    """Select text search filter."""
    text_input = prompt_input(t("filter.by_text"))
    filters["text_search"] = text_input if text_input else None


def _apply_advanced_filter(db, filters: dict):
    """Apply filters and show results using DataTable view."""
    results = db.search_sources_advanced(
        tags=filters["tags"] or None,
        score_min=filters["score_min"],
        score_max=filters["score_max"],
        statuses=filters["statuses"] or None,
        roles=filters["roles"] or None,
        last_used_days=filters["last_used_days"],
        text_search=filters["text_search"],
    )

    if not results:
        show_toast(t("filter.no_results"))
        return

    while True:
        app = SourcesBrowseApp(results, db, title=t("filter.title"))
        app.run()

        if app.result_action is None:
            # Offer to save filter when exiting
            save_options = [
                f"← {t('common.back')}",
                f"💾 {t('filter.save')}",
            ]
            save_app = SimpleMenuApp(t("filter.title"), save_options)
            save_idx = save_app.run()
            if save_idx == 1:
                _save_current_filter(db, filters)
            return

        action, source = app.result_action

        if action == "view":
            _show_source_detail(db, source)
        elif action == "edit":
            _edit_source(db, source)
        elif action == "delete":
            if _delete_source(db, source):
                # Refresh results after deletion
                results = db.search_sources_advanced(
                    tags=filters["tags"] or None,
                    score_min=filters["score_min"],
                    score_max=filters["score_max"],
                    statuses=filters["statuses"] or None,
                    roles=filters["roles"] or None,
                    last_used_days=filters["last_used_days"],
                    text_search=filters["text_search"],
                )
                if not results:
                    show_toast(t("filter.no_results"))
                    return
        elif action == "tags":
            _edit_source_tags(db, source)
        elif action == "bulk":
            _bulk_select_sources(db, results)


def _save_current_filter(db, filters: dict):
    """Save current filter as a named view."""
    import json

    name = prompt_input(t("view.name"))
    if not name:
        return

    # Serialize filters to JSON
    filter_json = json.dumps(filters)

    try:
        db.conn.execute(
            "INSERT INTO saved_filters (name, filter_json) VALUES (?, ?)",
            (name, filter_json),
        )
        db.conn.commit()
        show_toast(t("view.saved", name=name))
    except Exception:
        show_toast("⚠ Une vue avec ce nom existe déjà")


def _manage_saved_views(db):
    """Manage saved filter views - list, apply, delete."""
    import json

    while True:
        saved_views = db.get_saved_filters()

        if not saved_views:
            show_toast(t("view.no_views"))
            return

        # Build menu
        menu_options = []
        for view in saved_views:
            # Parse filter to show summary
            filters = json.loads(view["filter_json"])
            summary_parts = []
            if filters.get("tags"):
                summary_parts.append(f"tags:{len(filters['tags'])}")
            if filters.get("score_min") or filters.get("score_max"):
                summary_parts.append("score")
            if filters.get("statuses"):
                summary_parts.append("status")
            if filters.get("roles"):
                summary_parts.append("role")

            summary = f" ({', '.join(summary_parts)})" if summary_parts else ""
            menu_options.append(f"📁 {view['name']}{summary}")

        menu_options.append("")
        menu_options.append(f"← {t('common.back')}")

        app = SimpleMenuApp(t("filter.saved_views"), menu_options)
        idx = app.run()

        if idx is None or idx >= len(saved_views):
            return

        # Show view actions
        selected_view = saved_views[idx]
        _show_view_actions(db, selected_view)


def _show_view_actions(db, view: dict):
    """Show actions for a saved view."""
    import json

    menu_options = [
        "▶️ Appliquer",
        "🗑️ Supprimer",
        "",
        f"← {t('common.back')}",
    ]

    app = SimpleMenuApp(f"📁 {view['name']}", menu_options)
    idx = app.run()

    if idx == 0:  # Apply
        filters = json.loads(view["filter_json"])
        show_toast(t("view.applied", name=view["name"]))
        _apply_advanced_filter(db, filters)
    elif idx == 1:  # Delete
        # Confirm delete
        confirm_options = [
            "✓ Oui, supprimer",
            "✗ Non, annuler",
        ]
        confirm_app = SimpleMenuApp(t("view.delete_confirm"), confirm_options)
        confirm_idx = confirm_app.run()

        if confirm_idx == 0:
            db.delete_saved_filter(view["id"])
            show_toast(t("view.deleted", name=view["name"]))


def _parse_tags_input(text: str) -> list[str]:
    """Parse comma-separated tags input into a clean list.

    Args:
        text: Raw input string with comma-separated tags

    Returns:
        List of normalized (lowercase, trimmed) non-empty tags
    """
    if not text:
        return []
    return [tag.strip().lower() for tag in text.split(",") if tag.strip()]


def _add_standalone_source(db):
    """Add a new source without linking to an entry."""
    from rekall.models import Source
    from rekall.utils import extract_domain, is_valid_url

    # Get domain/URL
    url_input = prompt_input(t("sources.enter_url"))
    if not url_input:
        return

    if not is_valid_url(url_input):
        show_toast("⚠ URL invalide")
        return

    domain = extract_domain(url_input)

    # Check if source exists
    existing = db.get_source_by_domain(domain)
    if existing:
        show_toast(f"⚠ Source existe déjà: {domain}")
        return

    # Get reliability
    rel_options = ["A - Très fiable", "B - Fiable", "C - À vérifier"]
    rel_app = SimpleMenuApp("Fiabilité", rel_options)
    rel_idx = rel_app.run()
    reliability = ["A", "B", "C"][rel_idx] if rel_idx is not None else "B"

    # Get tags (optional, with suggestions)
    existing_tags = db.get_all_tags_with_counts()
    if existing_tags:
        suggestions = ", ".join([tag_info["theme"] for tag_info in existing_tags[:5]])
        tags_prompt = f"{t('tags.enter_tags')} (ex: {suggestions})"
    else:
        tags_prompt = t("tags.enter_tags")

    tags_input = prompt_input(tags_prompt)
    tags = _parse_tags_input(tags_input)

    # Create source
    source = Source(domain=domain, reliability=reliability)
    added_source = db.add_source(source)

    # Add tags if any
    for tag in tags:
        db.add_source_theme(added_source.id, tag)

    if tags:
        show_toast(f"✓ Source ajoutée: {domain} (tags: {', '.join(tags)})")
    else:
        show_toast(f"✓ Source ajoutée: {domain}")


def _bulk_select_sources(db, sources):
    """Bulk selection mode for sources - select multiple and apply tag actions."""
    selected_ids = set()

    while True:
        # Build menu with checkboxes
        menu_options = []
        for source in sources:
            checkbox = "☑" if source.id in selected_ids else "☐"
            score_bar = _score_bar(source.personal_score)
            menu_options.append(f"{checkbox} {score_bar} {source.domain}")

        menu_options.append("")
        menu_options.append(f"[{len(selected_ids)}] {t('bulk.actions')}")
        menu_options.append(f"← {t('common.back')}")

        app = SimpleMenuApp(f"{t('bulk.select_mode')} - {t('bulk.selected', count=len(selected_ids))}", menu_options)
        idx = app.run()

        if idx is None:
            return

        # Check actions
        if idx == len(sources) + 1:
            if selected_ids:
                _bulk_tag_actions(db, list(selected_ids))
            else:
                show_toast("⚠ Sélectionnez au moins une source")
        elif idx >= len(sources) + 2:
            return
        elif idx < len(sources):
            # Toggle selection
            source_id = sources[idx].id
            if source_id in selected_ids:
                selected_ids.remove(source_id)
            else:
                selected_ids.add(source_id)


def _bulk_tag_actions(db, source_ids: list[str]):
    """Show bulk actions menu for selected sources."""
    menu_options = [
        f"➕ {t('tags.bulk_add')}",
        f"➖ {t('tags.bulk_remove')}",
        "",
        f"← {t('common.back')}",
    ]

    app = SimpleMenuApp(f"{t('bulk.actions')} ({len(source_ids)} sources)", menu_options)
    idx = app.run()

    if idx == 0:
        _bulk_add_tag(db, source_ids)
    elif idx == 1:
        _bulk_remove_tag(db, source_ids)


def _bulk_add_tag(db, source_ids: list[str]):
    """Add a tag to multiple sources."""
    # Get suggestions
    existing_tags = db.get_all_tags_with_counts()
    if existing_tags:
        suggestions = ", ".join([tag_info["theme"] for tag_info in existing_tags[:5]])
        tag_input = prompt_input(f"{t('tags.enter_tags')} (ex: {suggestions})")
    else:
        tag_input = prompt_input(t("tags.enter_tags"))

    tags = _parse_tags_input(tag_input)
    if not tags:
        return

    count = 0
    for source_id in source_ids:
        for tag in tags:
            db.add_source_theme(source_id, tag)
            count += 1

    show_toast(f"✓ {len(tags)} tag(s) ajouté(s) à {len(source_ids)} sources")


def _bulk_remove_tag(db, source_ids: list[str]):
    """Remove a tag from multiple sources."""
    # Get common tags across selected sources
    common_tags = set()
    for i, source_id in enumerate(source_ids):
        source_tags = set(db.get_source_themes(source_id))
        if i == 0:
            common_tags = source_tags
        else:
            common_tags &= source_tags

    if not common_tags:
        # Show all unique tags instead
        all_tags = set()
        for source_id in source_ids:
            all_tags.update(db.get_source_themes(source_id))
        if not all_tags:
            show_toast(t("tags.no_tags"))
            return
        tags_to_show = list(all_tags)
    else:
        tags_to_show = list(common_tags)

    # Build menu
    menu_options = tags_to_show + ["", f"← {t('common.back')}"]

    app = SimpleMenuApp(t("tags.remove"), menu_options)
    idx = app.run()

    if idx is None or idx >= len(tags_to_show):
        return

    tag_to_remove = tags_to_show[idx]
    removed_count = 0
    for source_id in source_ids:
        if tag_to_remove in db.get_source_themes(source_id):
            db.remove_source_theme(source_id, tag_to_remove)
            removed_count += 1

    show_toast(f"✓ Tag '{tag_to_remove}' retiré de {removed_count} sources")


def _list_all_sources(db):
    """List all sources with DataTable view."""
    sources = db.list_sources(limit=100)

    if not sources:
        show_toast(t("source.no_sources"))
        return

    while True:
        app = SourcesBrowseApp(sources, db)
        app.run()

        if app.result_action is None:
            return

        action, source = app.result_action

        if action == "view":
            _show_source_detail(db, source)
        elif action == "edit":
            _edit_source(db, source)
        elif action == "delete":
            _delete_source(db, source)
            # Refresh list after deletion
            sources = db.list_sources(limit=100)
            if not sources:
                show_toast(t("source.no_sources"))
                return
        elif action == "tags":
            _edit_source_tags(db, source)
        elif action == "bulk":
            _bulk_select_sources(db, sources)


def _show_source_detail(db, source):
    """Show source details with backlinks."""
    # Get backlinks count
    backlink_count = db.count_source_backlinks(source.id)

    # Get tags
    source_tags = db.get_source_themes(source.id)

    # Build detail
    lines = [
        f"[bold cyan]━━━ {source.domain} ━━━[/bold cyan]",
        "",
        f"[cyan]ID:[/cyan]          {source.id}",
        f"[cyan]Status:[/cyan]      {source.status}",
        f"[cyan]Fiabilité:[/cyan]   {source.reliability}",
        f"[cyan]Score:[/cyan]       {source.personal_score:.1f}/100",
        f"[cyan]Utilisations:[/cyan] {source.usage_count}",
    ]

    # Show tags
    if source_tags:
        tags_str = ", ".join(source_tags)
        lines.append(f"[cyan]Tags:[/cyan]        {tags_str}")
    else:
        lines.append(f"[cyan]Tags:[/cyan]        [dim]{t('tags.no_tags')}[/dim]")

    if source.url_pattern:
        lines.append(f"[cyan]Pattern:[/cyan]     {source.url_pattern}")

    if source.last_used:
        lines.append(f"[cyan]Dernière utilisation:[/cyan] {source.last_used.strftime('%Y-%m-%d')}")
    else:
        lines.append(f"[cyan]Dernière utilisation:[/cyan] {t('source_detail.never_used')}")

    if source.last_verified:
        lines.append(f"[cyan]Dernière vérification:[/cyan] {source.last_verified.strftime('%Y-%m-%d')}")

    # Backlinks
    lines.append("")
    if backlink_count == 1:
        lines.append(f"[yellow]{t('backlinks.cited_by_one')}[/yellow]")
    elif backlink_count > 1:
        lines.append(f"[yellow]{t('backlinks.cited_by', count=backlink_count)}[/yellow]")
    else:
        lines.append(f"[dim]{t('backlinks.no_backlinks')}[/dim]")

    show_info("\n".join(lines))

    # Action menu
    action_options = []

    if backlink_count > 0:
        action_options.append(f"📋 {t('backlinks.title')}")

    action_options.append(f"🏷️ {t('tags.edit')}")
    action_options.append("")
    action_options.append(f"← {t('common.back')}")

    app = SimpleMenuApp(t("source_detail.title"), action_options)
    action_idx = app.run()

    if action_idx is None:
        return

    # Handle actions
    if backlink_count > 0:
        if action_idx == 0:
            _show_source_backlinks(db, source)
        elif action_idx == 1:
            _edit_source_tags(db, source)
    else:
        if action_idx == 0:
            _edit_source_tags(db, source)


def _delete_source(db, source) -> bool:
    """Delete a source after confirmation."""
    # Check backlinks
    backlink_count = db.count_source_backlinks(source.id)

    # Build confirmation message
    msg = f"{t('browse.confirm_delete')}\n\n[bold]{source.domain}[/bold]"
    if backlink_count > 0:
        msg += f"\n\n[yellow]⚠️ Cette source est citée par {backlink_count} entrée(s)[/yellow]"

    confirm_options = [
        f"❌ {t('common.cancel')}",
        f"✓ {t('common.confirm')}",
    ]

    app = SimpleMenuApp(t("browse.delete"), confirm_options, subtitle=msg)
    idx = app.run()

    if idx == 1:  # Confirm
        if db.delete_source(source.id):
            show_toast(f"✓ Source '{source.domain}' supprimée")
            return True
        else:
            show_toast("❌ Erreur lors de la suppression")
    return False


def _edit_source(db, source):
    """Edit source properties - redirects to detail view."""
    _show_source_detail(db, source)


def _edit_source_tags(db, source):
    """Edit tags for a source - add or remove tags."""
    while True:
        current_tags = db.get_source_themes(source.id)

        # Build menu options
        menu_options = []

        # Show current tags with option to remove
        if current_tags:
            menu_options.append(f"[dim]── {t('tags.current')} ──[/dim]")
            for tag in current_tags:
                menu_options.append(f"  ❌ {tag}")
            menu_options.append("")

        # Add tag option
        menu_options.append(f"➕ {t('tags.add')}")
        menu_options.append("")
        menu_options.append(f"← {t('common.back')}")

        app = SimpleMenuApp(f"{t('tags.edit')} - {source.domain}", menu_options)
        idx = app.run()

        if idx is None:
            return

        # Find which action was selected
        option_text = menu_options[idx] if idx < len(menu_options) else ""

        if t("common.back") in option_text:
            return

        if t("tags.add") in option_text:
            # Show suggestions and prompt for new tags
            existing_tags = db.get_all_tags_with_counts()
            if existing_tags:
                suggestions = ", ".join([tag_info["theme"] for tag_info in existing_tags[:5]])
                new_tags_input = prompt_input(f"{t('tags.enter_tags')} (ex: {suggestions})")
            else:
                new_tags_input = prompt_input(t("tags.enter_tags"))

            new_tags = _parse_tags_input(new_tags_input)
            for tag in new_tags:
                if tag not in current_tags:
                    db.add_source_theme(source.id, tag)
                    show_toast(t("tags.added", tag=tag))

        elif "❌" in option_text:
            # Remove tag
            tag_to_remove = option_text.replace("❌", "").strip()
            db.remove_source_theme(source.id, tag_to_remove)
            show_toast(t("tags.removed", tag=tag_to_remove))


def _show_source_backlinks(db, source):
    """Show entries citing this source."""
    backlinks = db.get_source_backlinks(source.id, limit=20)

    if not backlinks:
        show_toast(t("backlinks.no_backlinks"))
        return

    menu_options = []
    for entry, _entry_source in backlinks:
        type_short = entry.type[:3].upper()
        menu_options.append(f"  [{type_short}] {entry.title[:40]}")

    menu_options.append("")
    menu_options.append(f"← {t('common.back')}")

    app = SimpleMenuApp(f"{t('backlinks.title')} - {source.domain}", menu_options)
    idx = app.run()

    if idx is not None and idx < len(backlinks):
        entry, _ = backlinks[idx]
        _show_entry_detail(entry)


def _add_source_to_entry(db, entry):
    """Add a source to an entry."""
    from rekall.models import Source
    from rekall.utils import extract_domain, extract_url_pattern, is_valid_url

    # Select source type
    type_options = [
        f"📚 {t('source.type.theme')} - Thème/Catégorie",
        f"🔗 {t('source.type.url')} - URL Web",
        f"📄 {t('source.type.file')} - Fichier local",
        f"← {t('common.back')}",
    ]
    type_app = SimpleMenuApp(t("sources.select_type"), type_options)
    type_idx = type_app.run()

    if type_idx is None or type_idx == 3:
        return

    source_types = ["theme", "url", "file"]
    source_type = source_types[type_idx]

    # Get source reference based on type
    if source_type == "theme":
        source_ref = prompt_input(t("sources.enter_theme"))
        if not source_ref:
            return
        # Link directly without curated source
        db.link_entry_to_source(entry.id, "theme", source_ref)
        show_toast(f"✓ {t('entry_source.added')}: {source_ref}")

    elif source_type == "url":
        url = prompt_input(t("sources.enter_url"))
        if not url:
            return

        if not is_valid_url(url):
            show_toast("⚠ URL invalide")
            return

        domain = extract_domain(url)
        url_pattern = extract_url_pattern(url)

        # Check if source exists or create it
        existing_source = db.get_source_by_domain(domain, url_pattern)
        if not existing_source:
            # Optionally ask about reliability for new source
            rel_options = ["A - Très fiable", "B - Fiable", "C - À vérifier", "Ne pas créer"]
            rel_app = SimpleMenuApp(f"Nouvelle source: {domain}", rel_options)
            rel_idx = rel_app.run()

            if rel_idx is None or rel_idx == 3:
                # Still link without curated source
                db.link_entry_to_source(entry.id, "url", url)
                show_toast(f"✓ {t('entry_source.added')}: {url[:30]}...")
                return

            reliability = ["A", "B", "C"][rel_idx]
            new_source = Source(
                domain=domain,
                url_pattern=url_pattern,
                reliability=reliability,
            )
            existing_source = db.add_source(new_source)

        # Link with curated source
        note = prompt_input(t("sources.optional_note"), required=False)
        db.link_entry_to_source(
            entry.id, "url", url,
            source_id=existing_source.id,
            note=note if note else None,
        )
        show_toast(f"✓ {t('entry_source.added')}: {domain}")

    elif source_type == "file":
        file_path = prompt_input(t("sources.enter_file"))
        if not file_path:
            return
        db.link_entry_to_source(entry.id, "file", file_path)
        show_toast(f"✓ {t('entry_source.added')}: {file_path[:30]}...")


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
        # Note: "delete" action is now handled in-app via DeleteConfirmOverlay
        # and no longer returns a result to this loop
        elif action == "add":
            # Add new entry, optionally pre-link to selected entry
            _add_entry_with_links(db, pre_link_entry=entry)
            entries = db.list_all(limit=100)


def _add_entry_with_links(db, pre_link_entry=None):
    """Add a new entry with optional linking to other entries.

    Args:
        db: Database instance
        pre_link_entry: Entry to suggest linking to (optional)
    """
    # 1. Select type
    type_options = list(VALID_TYPES) + [f"← {t('common.back')}"]
    app = SimpleMenuApp(t('add.type'), type_options)
    idx = app.run()

    if idx is None or idx == len(type_options) - 1:
        return

    entry_type = VALID_TYPES[idx]

    # 2. Get title
    title = prompt_input(t("add.title"))
    if not title:
        return

    # 3. Get content (optional)
    content = prompt_input(t("add.content"), required=False)

    # 4. Get tags
    tags_input = prompt_input(t("add.tags"), required=False)
    tags = [tag.strip() for tag in tags_input.split(",")] if tags_input else []

    # 5. Get project
    project = prompt_input(t("add.project"), required=False)

    # 6. Get confidence
    conf_options = ["1 - Very Low", "2 - Low", "3 - Medium", "4 - High", "5 - Very High"]
    conf_app = SimpleMenuApp(t('add.confidence'), conf_options)
    conf_idx = conf_app.run()
    confidence = (conf_idx + 1) if conf_idx is not None else 3

    # 7. Create entry
    entry = Entry(
        id=generate_ulid(),
        title=title,
        content=content,
        type=entry_type,
        tags=tags,
        project=project,
        confidence=confidence,
    )
    db.add(entry)

    show_toast(f"✓ {t('add.success')}: {entry.id[:8]}...", 2.0)

    # 8. Propose linking
    _propose_entry_links(db, entry, pre_link_entry)


def _propose_entry_links(db, new_entry, pre_link_entry=None):
    """Propose linking the new entry to other entries.

    Args:
        db: Database instance
        new_entry: The newly created entry
        pre_link_entry: Entry to suggest as first in the list (optional)
    """
    relation_types = ["related", "supersedes", "derived_from", "contradicts"]
    relation_labels = {
        "related": "↔ Related (lié à)",
        "supersedes": "→ Supersedes (remplace)",
        "derived_from": "← Derived from (dérivé de)",
        "contradicts": "⚡ Contradicts (contredit)",
    }

    while True:
        # Build link menu - always explicit choice
        menu_items = [
            f"✓ {t('common.done')} (Terminer)",
            "🔍 Rechercher une entrée",
            "📋 Choisir parmi les entrées",
        ]

        link_app = SimpleMenuApp("Ajouter des liens ?", menu_items)
        link_idx = link_app.run()

        if link_idx is None or link_idx == 0:
            # Done linking
            return

        target_entry = None

        if link_idx == 1:
            # Search for entry
            query = prompt_input("Recherche", required=False)
            if query:
                results = db.search(query, limit=15)
                if results:
                    # Filter out new_entry
                    filtered = [r for r in results if r.entry.id != new_entry.id]
                    if filtered:
                        target_entry = _select_entry_from_list(
                            [r.entry for r in filtered],
                            "Sélectionner l'entrée à lier"
                        )
                    else:
                        show_toast("Aucun résultat (hors entrée actuelle)", 2.0)
                else:
                    show_toast(f"⚠ {t('search.no_results')}", 2.0)
        elif link_idx == 2:
            # Show entry list with pre_link_entry first if provided
            recent = db.list_all(limit=20)
            recent_filtered = [e for e in recent if e.id != new_entry.id]

            # If pre_link_entry exists and is valid, put it first
            if pre_link_entry and pre_link_entry.id != new_entry.id:
                # Remove it if already in list to avoid duplicates
                recent_filtered = [e for e in recent_filtered if e.id != pre_link_entry.id]
                # Add it at the beginning with a marker
                recent_filtered.insert(0, pre_link_entry)

            if recent_filtered:
                target_entry = _select_entry_from_list(
                    recent_filtered,
                    "Sélectionner l'entrée à lier",
                    highlight_first=(pre_link_entry is not None)
                )
            else:
                show_toast("Aucune autre entrée disponible", 2.0)

        # If target selected, ask for relation type and create link
        if target_entry:
            _create_link_to_entry(db, new_entry, target_entry, relation_types, relation_labels)
            # Reset pre_link_entry after first link to avoid confusion
            pre_link_entry = None


def _select_entry_from_list(entries: list, title: str, highlight_first: bool = False):
    """Display a list of entries and let user select one.

    Args:
        entries: List of Entry objects
        title: Menu title
        highlight_first: If True, mark the first entry as suggested

    Returns:
        Selected Entry or None if cancelled
    """
    if not entries:
        return None

    # Build menu options with entry info
    menu_options = []
    for i, entry in enumerate(entries):
        type_short = entry.type[:3].upper()
        project = f"[{entry.project}]" if entry.project else ""
        title_text = entry.title[:40]

        # Mark first entry if highlight_first
        if i == 0 and highlight_first:
            menu_options.append(f"★ {type_short} {project} {title_text}")
        else:
            menu_options.append(f"  {type_short} {project} {title_text}")

    menu_options.append(f"← {t('common.back')}")

    app = SimpleMenuApp(title, menu_options)
    idx = app.run()

    if idx is None or idx >= len(entries):
        return None

    return entries[idx]


def _create_link_to_entry(db, source_entry, target_entry, relation_types, relation_labels):
    """Create a link between source and target entries.

    Args:
        db: Database instance
        source_entry: The source entry (new entry)
        target_entry: The target entry to link to
        relation_types: List of valid relation types
        relation_labels: Dict mapping types to display labels
    """
    # Select relation type
    rel_options = [relation_labels[rt] for rt in relation_types]
    rel_options.append(f"← {t('common.back')}")
    rel_app = SimpleMenuApp(f"Type de relation → {target_entry.title[:30]}", rel_options)
    rel_idx = rel_app.run()

    if rel_idx is None or rel_idx >= len(relation_types):
        return

    relation_type = relation_types[rel_idx]

    # Get optional reason
    reason = prompt_input("Raison du lien (optionnel)", required=False)

    # Create the link
    try:
        db.add_link(
            source_id=source_entry.id,
            target_id=target_entry.id,
            relation_type=relation_type,
            reason=reason if reason else None,
        )
        show_toast(f"✓ Lien créé: {source_entry.title[:20]}... → {target_entry.title[:20]}...", 2.0)
    except ValueError as e:
        show_toast(f"⚠ {str(e)[:50]}", 3.0)


def _show_entry_detail(entry):
    """Display entry details with navigation options using Textual."""
    db = get_db()

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

        # Show sources linked to this entry (Feature 009)
        entry_sources = db.get_entry_sources(entry.id)
        if entry_sources:
            lines.extend(["", f"[cyan]{t('source.linked_sources')}:[/cyan]"])
            for es in entry_sources:
                type_icon = {"theme": "📚", "url": "🔗", "file": "📄"}.get(es.source_type, "•")
                if es.source:
                    lines.append(f"  {type_icon} {es.source.domain} ({es.source_ref[:30]}...)")
                else:
                    lines.append(f"  {type_icon} {es.source_ref[:50]}")

        # Show details using Textual
        show_info("\n".join(lines))

        # Action menu using Textual
        action_options = [
            f"← {t('browse.back_to_list')}",
            t("browse.edit_entry"),
            f"📎 {t('sources.add_to_entry')}",
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
            _add_source_to_entry(db, entry)
            # Refresh entry data
            entry = db.get(entry.id, update_access=False) or entry
        elif action_idx == 3:
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
    table.add_row("", "")
    table.add_row("[bold]Smart Embeddings[/bold]", "")
    emb_status = "[green]✓ " + t("embeddings.status_enabled") + "[/green]" if config.smart_embeddings_enabled else "[dim]○ " + t("embeddings.status_disabled") + "[/dim]"
    table.add_row("  Status", emb_status)
    table.add_row("  Model", config.smart_embeddings_model)
    table.add_row("  Dimensions", str(config.smart_embeddings_dimensions))
    table.add_row("  Similarity threshold", str(config.smart_embeddings_similarity_threshold))
    table.add_row("", "")
    table.add_row("[bold]Interface (UI)[/bold]", "")
    table.add_row("  Detail panel ratio", f"{config.ui_detail_panel_ratio} (+/- pour ajuster)")

    # Capture table as string
    string_io = StringIO()
    temp_console = RichConsole(file=string_io, force_terminal=True, width=100)
    temp_console.print("[bold]Configuration Détaillée[/bold]")
    temp_console.print()
    temp_console.print(table)
    content = string_io.getvalue()

    # Show in Textual app
    show_info(content)


# Cache for embeddings dependency check (avoid slow reimport)
_embeddings_deps_cache: dict = {"checked": False, "available": False}


def _check_embeddings_deps() -> bool:
    """Check if embeddings dependencies are available (cached)."""
    if _embeddings_deps_cache["checked"]:
        return _embeddings_deps_cache["available"]

    # Show loading message (first time only)
    print("\r⏳ Checking dependencies...", end="", flush=True)

    try:
        import numpy  # noqa: F401
        import sentence_transformers  # noqa: F401
        _embeddings_deps_cache["available"] = True
    except ImportError:
        _embeddings_deps_cache["available"] = False

    _embeddings_deps_cache["checked"] = True
    print("\r" + " " * 30 + "\r", end="", flush=True)  # Clear message
    return _embeddings_deps_cache["available"]


# Cache for MCP dependency check
_mcp_deps_cache: dict = {"checked": False, "available": False}


def _check_mcp_deps() -> bool:
    """Check if MCP dependencies are available (cached)."""
    if _mcp_deps_cache["checked"]:
        return _mcp_deps_cache["available"]

    try:
        from mcp.server import Server  # noqa: F401
        _mcp_deps_cache["available"] = True
    except ImportError:
        _mcp_deps_cache["available"] = False

    _mcp_deps_cache["checked"] = True
    return _mcp_deps_cache["available"]


# MCP configuration per CLI
MCP_CLI_CONFIGS = {
    "claude-desktop": {
        "name": "Claude Desktop",
        "file": "~/Library/Application Support/Claude/claude_desktop_config.json",
        "config": '''{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp-server"]
    }
  }
}''',
    },
    "claude-code": {
        "name": "Claude Code",
        "file": "~/.claude/settings.json",
        "config": '''{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp-server"]
    }
  }
}''',
    },
    "cursor": {
        "name": "Cursor",
        "file": "~/.cursor/mcp.json",
        "config": '''{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp-server"]
    }
  }
}''',
    },
    "windsurf": {
        "name": "Windsurf",
        "file": "~/.codeium/windsurf/mcp_config.json",
        "config": '''{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp-server"]
    }
  }
}''',
    },
    "cline": {
        "name": "Cline",
        "file": "~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
        "config": '''{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp-server"]
    }
  }
}''',
    },
    "zed": {
        "name": "Zed",
        "file": "~/.config/zed/settings.json",
        "config": '''{
  "context_servers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp-server"]
    }
  }
}''',
    },
    "continue": {
        "name": "Continue.dev",
        "file": "~/.continue/config.json",
        "config": '''{
  "mcpServers": [
    {
      "name": "rekall",
      "command": "rekall",
      "args": ["mcp-server"]
    }
  ]
}''',
    },
    "copilot": {
        "name": "GitHub Copilot",
        "file": "~/.vscode/mcp.json",
        "config": '''{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp-server"]
    }
  }
}''',
    },
    "qwen": {
        "name": "Qwen Code",
        "file": "~/.qwen/settings.json",
        "config": '''{
  "mcpServers": {
    "rekall": {
      "command": "rekall",
      "args": ["mcp-server"]
    }
  }
}''',
    },
    "opencode": {
        "name": "OpenCode",
        "file": "~/.config/opencode/config.json",
        "config": '''{
  "mcp": {
    "rekall": {
      "type": "local",
      "command": ["rekall", "mcp-server"],
      "enabled": true
    }
  }
}''',
    },
}


def _install_mcp_config(cli_config: dict) -> str:
    """Install MCP config by merging into the CLI's config file.

    Strategy:
    1. Expand file path and create parent directories if needed
    2. Read existing config (or start with empty object)
    3. Create backup of existing file
    4. Merge mcpServers section (preserving other servers)
    5. Write merged config
    6. Validate JSON syntax
    7. If error: rollback from backup + create .error file

    Args:
        cli_config: Dict with 'name', 'file', 'config' keys

    Returns:
        Status message for notification
    """
    import json
    import shutil
    from datetime import datetime
    from pathlib import Path

    file_path_str = cli_config["file"]
    new_config = json.loads(cli_config["config"])

    # Expand path (handle ~ and relative paths)
    if file_path_str.startswith("~"):
        file_path = Path(file_path_str).expanduser()
    elif file_path_str.startswith("."):
        # Relative to home for safety
        file_path = Path.home() / file_path_str
    else:
        file_path = Path(file_path_str)

    backup_path = None
    error_path = file_path.with_suffix(".error.json")

    try:
        # Create parent directories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Read existing config or start fresh
        existing_config = {}
        if file_path.exists():
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        existing_config = json.loads(content)
            except json.JSONDecodeError:
                # Invalid JSON - we'll try to preserve it in error file
                pass

            # Create backup with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = file_path.with_suffix(f".backup_{timestamp}.json")
            shutil.copy2(file_path, backup_path)

        # Detect format and merge appropriately
        if "mcpServers" in new_config:
            new_servers = new_config["mcpServers"]
            if isinstance(new_servers, list):
                # Array format (Continue.dev)
                if "mcpServers" not in existing_config:
                    existing_config["mcpServers"] = []
                elif not isinstance(existing_config["mcpServers"], list):
                    # Convert existing dict to list if needed
                    existing_list = []
                    for name, cfg in existing_config["mcpServers"].items():
                        existing_list.append({"name": name, **cfg})
                    existing_config["mcpServers"] = existing_list

                # Find and replace rekall entry, or add new
                rekall_entry = new_servers[0]  # Our config has 1 entry
                found = False
                for i, entry in enumerate(existing_config["mcpServers"]):
                    if entry.get("name") == "rekall":
                        existing_config["mcpServers"][i] = rekall_entry
                        found = True
                        break
                if not found:
                    existing_config["mcpServers"].append(rekall_entry)
            else:
                # Dict format (standard - most CLIs)
                if "mcpServers" not in existing_config:
                    existing_config["mcpServers"] = {}
                existing_config["mcpServers"]["rekall"] = new_servers["rekall"]

        elif "context_servers" in new_config:
            # Zed format
            if "context_servers" not in existing_config:
                existing_config["context_servers"] = {}
            existing_config["context_servers"]["rekall"] = new_config["context_servers"]["rekall"]

        elif "mcp" in new_config:
            # OpenCode format
            if "mcp" not in existing_config:
                existing_config["mcp"] = {}
            existing_config["mcp"]["rekall"] = new_config["mcp"]["rekall"]

        else:
            return "⚠ Unknown config format"

        # Write merged config with nice formatting
        merged_json = json.dumps(existing_config, indent=2, ensure_ascii=False)

        # Validate before writing
        json.loads(merged_json)  # Will raise if invalid

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(merged_json + "\n")

        # Final validation - re-read and parse
        with open(file_path, encoding="utf-8") as f:
            json.loads(f.read())

        # Success - remove backup if it was just created and file was empty
        if backup_path and backup_path.exists():
            # Keep backup for safety, but could optionally remove small backups
            pass

        return f"✓ Installed to {file_path.name}"

    except json.JSONDecodeError as e:
        # JSON syntax error - rollback
        if backup_path and backup_path.exists():
            shutil.copy2(backup_path, file_path)
            # Write error file with the attempted merge
            try:
                with open(error_path, "w", encoding="utf-8") as f:
                    f.write(f"// JSON Error: {e}\n")
                    f.write("// Original file restored from backup\n")
                    f.write("// Attempted config below:\n")
                    f.write(json.dumps(existing_config, indent=2, ensure_ascii=False))
                return f"⚠ JSON error, restored backup. See {error_path.name}"
            except Exception:
                return f"⚠ JSON error: {e}"
        return f"⚠ JSON error: {e}"

    except PermissionError:
        return f"⚠ Permission denied: {file_path}"

    except Exception as e:
        # Other error - try to rollback
        if backup_path and backup_path.exists():
            try:
                shutil.copy2(backup_path, file_path)
                return f"⚠ Error, restored backup: {str(e)[:30]}"
            except Exception:
                pass
        return f"⚠ Error: {str(e)[:40]}"


def _uninstall_mcp_config(cli_config: dict) -> str:
    """Remove MCP config from the CLI's config file.

    Removes the 'rekall' entry from mcpServers, context_servers, or mcp section.

    Args:
        cli_config: Dict with 'name', 'file', 'config' keys

    Returns:
        Status message for notification
    """
    import json
    from pathlib import Path

    file_path_str = cli_config["file"]

    # Expand path
    if file_path_str.startswith("~"):
        file_path = Path(file_path_str).expanduser()
    elif file_path_str.startswith("."):
        file_path = Path.home() / file_path_str
    else:
        file_path = Path(file_path_str)

    if not file_path.exists():
        return "⚠ Config file not found"

    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return "⚠ Config file is empty"
            existing_config = json.loads(content)

        removed = False

        # Check mcpServers (dict format - most CLIs)
        if "mcpServers" in existing_config:
            if isinstance(existing_config["mcpServers"], dict):
                if "rekall" in existing_config["mcpServers"]:
                    del existing_config["mcpServers"]["rekall"]
                    removed = True
            elif isinstance(existing_config["mcpServers"], list):
                # Array format (Continue.dev)
                original_len = len(existing_config["mcpServers"])
                existing_config["mcpServers"] = [
                    entry for entry in existing_config["mcpServers"]
                    if entry.get("name") != "rekall"
                ]
                if len(existing_config["mcpServers"]) < original_len:
                    removed = True

        # Check context_servers (Zed format)
        if "context_servers" in existing_config:
            if "rekall" in existing_config["context_servers"]:
                del existing_config["context_servers"]["rekall"]
                removed = True

        # Check mcp (OpenCode format)
        if "mcp" in existing_config:
            if "rekall" in existing_config["mcp"]:
                del existing_config["mcp"]["rekall"]
                removed = True

        if not removed:
            return "⚠ Rekall not found in config"

        # Write updated config
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(existing_config, indent=2, ensure_ascii=False) + "\n")

        return f"✓ Removed from {file_path.name}"

    except json.JSONDecodeError:
        return "⚠ Invalid JSON in config file"
    except PermissionError:
        return f"⚠ Permission denied: {file_path}"
    except Exception as e:
        return f"⚠ Error: {str(e)[:40]}"


def _configure_mcp():
    """Configure MCP Server - single screen with CLI selector."""
    mcp_ok = _check_mcp_deps()
    app = MCPConfigApp(MCP_CLI_CONFIGS, mcp_ok)
    app.run()


def _configure_context_mode():
    """Configure context_mode setting (Feature 007).

    Shows menu to select between:
    - required: Reject entries without structured context
    - recommended: Warn but allow entries without context
    - optional: Accept all entries
    """
    from rekall.config import get_config, reset_config, save_config_to_toml

    config = get_config()
    current_mode = config.smart_embeddings_context_mode

    # Build menu with current selection highlighted
    menu_options = [
        "─── Context Mode ───",
        "",
        f"  {'→ ' if current_mode == 'required' else '  '}[green]required[/green] - Entrée refusée sans contexte structuré",
        f"  {'→ ' if current_mode == 'recommended' else '  '}[yellow]recommended[/yellow] - Avertissement sans contexte",
        f"  {'→ ' if current_mode == 'optional' else '  '}[dim]optional[/dim] - Tout accepter (permissif)",
        "",
        "← Retour",
    ]

    app = SimpleMenuApp("📋 Context Mode", menu_options)
    idx = app.run()

    if idx is None:
        return
    idx = int(idx) if isinstance(idx, str) else idx

    mode_map = {2: "required", 3: "recommended", 4: "optional"}
    new_mode = mode_map.get(idx)

    if new_mode and new_mode != current_mode:
        # Save to config
        success = save_config_to_toml(
            config.config_dir,
            {"smart_embeddings": {"context_mode": new_mode}}
        )
        if success:
            reset_config()  # Force reload
            show_toast(f"✓ Context mode: {new_mode}", 2.0)
        else:
            show_toast("⚠ Erreur sauvegarde config", 2.0)


def _configure_max_context_size():
    """Configure max_context_size setting (Feature 007).

    Shows menu to select context size limit in KB.
    """
    from rekall.config import get_config, reset_config, save_config_to_toml

    config = get_config()
    current_kb = config.max_context_size // 1024

    # Build menu with size options
    size_options = [5, 10, 20, 50, 100]

    menu_options = [
        "─── Max Context Size ───",
        "",
    ]

    for size in size_options:
        marker = "→ " if size == current_kb else "  "
        menu_options.append(f"  {marker}{size} KB")

    menu_options.append("")
    menu_options.append("← Retour")

    app = SimpleMenuApp("📏 Max Context Size", menu_options)
    idx = app.run()

    if idx is None:
        return
    idx = int(idx) if isinstance(idx, str) else idx

    # Map index to size (accounting for header and spacer)
    if 2 <= idx <= 2 + len(size_options) - 1:
        new_size = size_options[idx - 2]
        if new_size != current_kb:
            success = save_config_to_toml(
                config.config_dir,
                {"smart_embeddings": {"max_context_size": new_size * 1024}}
            )
            if success:
                reset_config()
                show_toast(f"✓ Max context size: {new_size} KB", 2.0)
            else:
                show_toast("⚠ Erreur sauvegarde config", 2.0)


def _configure_embeddings():
    """Configure Smart Embeddings - single flat menu with info and actions."""
    from rekall.config import get_config, reset_config, save_config_to_toml

    pending_notification = ""

    while True:
        config = get_config()

        # Check dependencies (cached after first call)
        deps_ok = _check_embeddings_deps()

        # Status indicators
        status_icon = "[green]✓[/green]" if config.smart_embeddings_enabled else "[dim]○[/dim]"
        deps_icon = "[green]✓[/green]" if deps_ok else "[yellow]⚠[/yellow]"

        # Build flat menu with info sections
        menu_options = []
        actions = []

        # ─── STATUS ───
        menu_options.append("─── STATUS ───")
        actions.append(None)

        status_text = t("embeddings.status_enabled") if config.smart_embeddings_enabled else t("embeddings.status_disabled")
        menu_options.append(f"  {status_icon} {status_text}")
        actions.append(None)

        deps_text = "Dependencies OK" if deps_ok else t('embeddings.deps_missing')
        menu_options.append(f"  {deps_icon} {deps_text}")
        actions.append(None)

        # ─── CONFIG ───
        menu_options.append("")
        actions.append(None)
        menu_options.append("─── CONFIG ───")
        actions.append(None)

        menu_options.append(f"  Model: {config.smart_embeddings_model}")
        actions.append(None)

        menu_options.append(f"  Dimensions: {config.smart_embeddings_dimensions}")
        actions.append(None)

        menu_options.append(f"  Threshold: {config.smart_embeddings_similarity_threshold}")
        actions.append(None)

        # ─── ACTIONS ───
        menu_options.append("")
        actions.append(None)
        menu_options.append("─── ACTIONS ───")
        actions.append(None)

        if config.smart_embeddings_enabled:
            menu_options.append(f"  ○ {t('embeddings.disable')}")
            actions.append("disable")
        else:
            menu_options.append(f"  ✓ {t('embeddings.enable')}")
            actions.append("enable")

        menu_options.append("")
        actions.append(None)
        menu_options.append(f"← {t('setup.back')}")
        actions.append("back")

        # Show menu with pending notification
        app = SimpleMenuApp(t("embeddings.title"), menu_options, pending_notification)
        pending_notification = ""  # Clear after use
        idx = app.run()

        if idx is None:
            return
        if idx >= len(actions):
            return

        action = actions[idx]
        if action is None or action == "back":
            return

        if action == "enable":
            success = save_config_to_toml(config.config_dir, {
                "smart_embeddings": {"enabled": True}
            })
            if success:
                reset_config()
                pending_notification = f"✓ {t('embeddings.saved')}"
            else:
                pending_notification = "⚠ Error saving config"
        elif action == "disable":
            success = save_config_to_toml(config.config_dir, {
                "smart_embeddings": {"enabled": False}
            })
            if success:
                reset_config()
                pending_notification = f"✓ {t('embeddings.saved')}"
            else:
                pending_notification = "⚠ Error saving config"


@dataclass
class ExportInfo:
    """Information about an export file."""

    path: Path
    timestamp: datetime
    size: int
    format: str  # rekall, md, json

    @property
    def size_human(self) -> str:
        """Human-readable size."""
        if self.size < 1024:
            return f"{self.size} B"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.1f} KB"
        else:
            return f"{self.size / (1024 * 1024):.1f} MB"


def _get_exports_dir() -> Path:
    """Get the exports directory (creates if needed)."""
    from rekall.config import get_config

    config = get_config()
    exports_dir = config.paths.data_dir / "exports"
    exports_dir.mkdir(parents=True, exist_ok=True)
    return exports_dir


def _list_exports(format_filter: str | None = None) -> list[ExportInfo]:
    """List existing exports.

    Args:
        format_filter: Filter by format (rekall, md, json) or None for all

    Returns:
        List of ExportInfo sorted by timestamp (newest first)
    """
    exports_dir = _get_exports_dir()
    exports = []

    patterns = {
        "rekall": "*.rekall.zip",
        "md": "*.md",
        "json": "*.json",
    }

    if format_filter:
        search_patterns = [patterns.get(format_filter, f"*.{format_filter}")]
    else:
        search_patterns = list(patterns.values())

    for pattern in search_patterns:
        for path in exports_dir.glob(pattern):
            if path.is_file():
                stat = path.stat()
                # Determine format from extension
                if path.suffix == ".zip":
                    fmt = "rekall"
                elif path.suffix == ".md":
                    fmt = "md"
                elif path.suffix == ".json":
                    fmt = "json"
                else:
                    fmt = path.suffix[1:]

                exports.append(
                    ExportInfo(
                        path=path,
                        timestamp=datetime.fromtimestamp(stat.st_mtime),
                        size=stat.st_size,
                        format=fmt,
                    )
                )

    exports.sort(key=lambda e: e.timestamp, reverse=True)
    return exports


def action_export_import():
    """Data management: backup, export, import submenu."""
    from rekall.backup import list_backups

    while True:
        # Get counts for display
        archives = _list_exports("rekall")
        backups = list_backups()

        # Build menu with sections
        menu_options = []
        actions = []

        # ─── BACKUP ───
        menu_options.append("─── BACKUP ───")
        actions.append(None)

        backup_label = f"  💾 {t('maintenance.create_backup')}"
        menu_options.append(backup_label)
        actions.append("backup")

        restore_label = f"  ↩ {t('maintenance.restore_backup')}"
        if backups:
            restore_label += f" [dim]({len(backups)})[/dim]"
        menu_options.append(restore_label)
        actions.append("restore")

        # ─── EXPORT ───
        menu_options.append("")
        actions.append(None)
        menu_options.append("─── EXPORT ───")
        actions.append(None)

        export_label = f"  📦 {t('export.archive')}"
        if archives:
            export_label += f" [dim]({len(archives)})[/dim]"
        menu_options.append(export_label)
        actions.append("export_archive")

        menu_options.append(f"  📄 {t('export.markdown')}")
        actions.append("export_md")

        menu_options.append(f"  📄 {t('export.json')}")
        actions.append("export_json")

        # ─── IMPORT ───
        menu_options.append("")
        actions.append(None)
        menu_options.append("─── IMPORT ───")
        actions.append(None)

        import_label = f"  📦 {t('import.archive')}"
        if archives:
            import_label += f" [dim]({len(archives)})[/dim]"
        menu_options.append(import_label)
        actions.append("import_archive")

        menu_options.append(f"  📄 {t('import.external_db')}")
        actions.append("import_db")

        # Back
        menu_options.append("")
        actions.append(None)
        menu_options.append(f"← {t('setup.back')}")
        actions.append("back")

        app = SimpleMenuApp(t("menu.data"), menu_options)
        idx = app.run()

        if idx is None:
            return
        if idx >= len(actions):
            return

        action = actions[idx]
        if action is None or action == "back":
            return

        if action == "backup":
            _create_backup_tui()
        elif action == "restore":
            _restore_backup_tui()
        elif action == "export_archive":
            _do_export_rekall()
        elif action == "export_md":
            _do_export_text("md")
        elif action == "export_json":
            _do_export_text("json")
        elif action == "import_archive":
            _do_import_rekall()
        elif action == "import_db":
            _do_import_external_db()


def _do_export_rekall():
    """Export to .rekall.zip archive using Textual with list of existing exports."""
    from rekall.archive import RekallArchive

    db = get_db()
    entries = db.list_all(limit=100000)

    if not entries:
        show_toast(f"⚠ {t('import.no_entries')}")
        return

    # List existing exports
    existing = _list_exports("rekall")
    exports_dir = _get_exports_dir()

    # Build selection menu
    options = [f"+ {t('export.new')}"]  # New export option
    for exp in existing[:10]:  # Limit to 10 most recent
        date_str = exp.timestamp.strftime("%Y-%m-%d %H:%M")
        options.append(f"{exp.path.name}  ({date_str}, {exp.size_human})")
    options.append(f"← {t('setup.back')}")

    app = SimpleMenuApp(t("export.select_or_new"), options)
    idx = app.run()

    if idx is None or idx == len(options) - 1:
        return

    if idx == 0:
        # New export - ask for filename
        filename = prompt_input(t("import.filename"))
        if not filename:
            return
        output_path = exports_dir / f"{filename}.rekall.zip"
    else:
        # Overwrite existing - confirm first
        selected = existing[idx - 1]
        confirm_options = [
            t("export.overwrite"),
            t("common.cancel"),
        ]
        confirm_app = SimpleMenuApp(
            f"{t('export.confirm_overwrite')}: {selected.path.name}",
            confirm_options
        )
        confirm_idx = confirm_app.run()
        if confirm_idx is None or confirm_idx != 0:
            return
        output_path = selected.path

    # Do the export
    RekallArchive.create(output_path, entries)
    show_toast(f"✓ {t('import.exported', count=len(entries), path=output_path.name)}", 2.0)


def _do_export_text(fmt: str):
    """Export to text format (md or json) using Textual with list of existing exports."""
    from rekall import exporters

    db = get_db()
    entries = db.list_all(limit=100000)

    if not entries:
        show_toast(f"⚠ {t('import.no_entries')}")
        return

    # List existing exports of this format
    existing = _list_exports(fmt)
    exports_dir = _get_exports_dir()

    # Build selection menu
    options = [f"+ {t('export.new')}"]
    for exp in existing[:10]:
        date_str = exp.timestamp.strftime("%Y-%m-%d %H:%M")
        options.append(f"{exp.path.name}  ({date_str}, {exp.size_human})")
    options.append(f"← {t('setup.back')}")

    app = SimpleMenuApp(t("export.select_or_new"), options)
    idx = app.run()

    if idx is None or idx == len(options) - 1:
        return

    if idx == 0:
        # New export
        filename = prompt_input(t("import.output_filename", fmt=fmt))
        if not filename:
            return
        output_path = exports_dir / f"{filename}.{fmt}"
    else:
        # Overwrite existing
        selected = existing[idx - 1]
        confirm_options = [t("export.overwrite"), t("common.cancel")]
        confirm_app = SimpleMenuApp(
            f"{t('export.confirm_overwrite')}: {selected.path.name}",
            confirm_options
        )
        confirm_idx = confirm_app.run()
        if confirm_idx is None or confirm_idx != 0:
            return
        output_path = selected.path

    # Generate content
    if fmt == "json":
        content = exporters.export_json(entries)
    else:
        content = exporters.export_markdown(entries)

    output_path.write_text(content)
    show_toast(f"✓ {t('import.exported', count=len(entries), path=output_path.name)}", 2.0)


def _do_import_rekall():
    """Import from .rekall.zip archive using Textual with list of available archives."""
    from pathlib import Path

    from rekall.archive import RekallArchive
    from rekall.sync import ImportExecutor, build_import_plan

    # List available archives
    archives = _list_exports("rekall")

    # Build selection menu
    options = []
    for arch in archives[:10]:
        date_str = arch.timestamp.strftime("%Y-%m-%d %H:%M")
        options.append(f"{arch.path.name}  ({date_str}, {arch.size_human})")

    options.append(f"📂 {t('import.other_file')}")  # Browse for other file
    options.append(f"← {t('setup.back')}")

    if archives:
        app = SimpleMenuApp(t("import.select_archive"), options)
    else:
        # No archives - show only "Other file" option
        options = [f"📂 {t('import.other_file')}", f"← {t('setup.back')}"]
        app = SimpleMenuApp(t("import.no_archives_found"), options)

    idx = app.run()

    if idx is None or idx == len(options) - 1:
        return

    # Determine archive path
    if archives and idx < len(archives):
        # Selected from list
        archive_path = archives[idx].path
    else:
        # "Other file" selected - ask for path
        filepath = prompt_input(t("import.archive_path"))
        if not filepath:
            return
        archive_path = Path(filepath).expanduser()
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
# Migration Overlay (Feature 007)
# =============================================================================


class MigrationOverlayApp(App):
    """Overlay app for migration prompts with changelog navigation."""

    CSS = """
    Screen {
        background: $surface;
        align: center middle;
    }

    #overlay-container {
        width: 70;
        height: auto;
        max-height: 30;
        padding: 1 2;
        background: $surface;
        border: thick #4367CD;
    }

    #overlay-title {
        text-align: center;
        padding: 1 0;
        color: #93B5F7;
        text-style: bold;
    }

    #overlay-content {
        height: auto;
        max-height: 18;
        padding: 1 2;
        background: $surface-darken-1;
        overflow: auto;
    }

    #overlay-nav {
        text-align: center;
        padding: 1 0;
        color: $text-muted;
    }

    #overlay-buttons {
        layout: horizontal;
        height: auto;
        align: center middle;
        padding: 1 0;
    }

    .overlay-button {
        width: auto;
        min-width: 15;
        margin: 0 1;
        padding: 0 2;
    }

    .overlay-button:focus {
        background: #4367CD;
        color: white;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "later", "Later", show=True),
        Binding("left", "prev_view", "◀", show=True),
        Binding("right", "next_view", "▶", show=True),
        Binding("m", "migrate", "Migrate", show=True),
    ]

    def __init__(
        self,
        current_version: int,
        target_version: int,
        legacy_count: int,
        changelog_content: str,
    ):
        super().__init__()
        self.current_version = current_version
        self.target_version = target_version
        self.legacy_count = legacy_count
        self.changelog_content = changelog_content
        self.current_view = 0  # 0 = migration, 1 = changelog
        self.result: str | None = None

    def compose(self) -> ComposeResult:
        from textual.widgets import Button

        with Container(id="overlay-container"):
            yield Static("", id="overlay-title")
            yield VerticalScroll(
                Markdown("", id="overlay-markdown"),
                id="overlay-content",
            )
            yield Static("◀ 1/2 ▶  (← →)", id="overlay-nav")
            with Container(id="overlay-buttons"):
                yield Button("Migrer", id="btn-migrate", variant="primary", classes="overlay-button")
                yield Button("Plus tard", id="btn-later", variant="default", classes="overlay-button")

    def on_mount(self) -> None:
        self._update_view()

    def _update_view(self) -> None:
        """Update display based on current view."""
        title_widget = self.query_one("#overlay-title", Static)
        content_widget = self.query_one("#overlay-markdown", Markdown)
        nav_widget = self.query_one("#overlay-nav", Static)

        if self.current_view == 0:
            # Migration view
            title_widget.update("🔄 Migration Disponible")
            nav_widget.update("◀ 1/2 ▶  (← →)")

            content = f"""## Mise à jour de schéma

**Version actuelle**: v{self.current_version}
**Nouvelle version**: v{self.target_version}

**Migrations en attente**: {self.target_version - self.current_version}
"""
            if self.legacy_count > 0:
                content += f"\n**Entrées sans contexte**: {self.legacy_count}\n"
                content += "\n*Ces entrées pourront être enrichies après migration.*"

            content += "\n\n---\n\nUne **sauvegarde automatique** sera créée avant la migration."

            content_widget.update(content)
        else:
            # Changelog view
            title_widget.update("📋 Changelog")
            nav_widget.update("◀ 2/2 ▶  (← →)")
            content_widget.update(self.changelog_content or "*Changelog non disponible*")

    def action_next_view(self) -> None:
        self.current_view = (self.current_view + 1) % 2
        self._update_view()

    def action_prev_view(self) -> None:
        self.current_view = (self.current_view - 1) % 2
        self._update_view()

    def action_migrate(self) -> None:
        self.result = "migrate"
        self.exit(result="migrate")

    def action_later(self) -> None:
        self.result = "later"
        self.exit(result="later")

    def on_button_pressed(self, event) -> None:

        button = event.button
        if button.id == "btn-migrate":
            self.action_migrate()
        elif button.id == "btn-later":
            self.action_later()


def check_migration_needed() -> tuple[bool, int, int, int]:
    """Check if database migration is needed.

    Returns:
        Tuple of (needs_migration, current_version, target_version, legacy_entries_count)
    """
    from rekall.db import CURRENT_SCHEMA_VERSION, Database

    config = get_config()

    if not config.db_path.exists():
        return (False, 0, CURRENT_SCHEMA_VERSION, 0)

    try:
        import sqlite3

        db = Database(config.db_path)
        db.conn = sqlite3.connect(str(config.db_path))
        current_version = db.get_schema_version()
        db.close()

        # Count legacy entries without structured context
        db = Database(config.db_path)
        db.init()
        entries = db.list_all(limit=10000)
        legacy_count = 0
        for entry in entries:
            ctx = db.get_structured_context(entry.id)
            if ctx is None:
                legacy_count += 1
        db.close()

        needs_migration = current_version < CURRENT_SCHEMA_VERSION
        return (needs_migration, current_version, CURRENT_SCHEMA_VERSION, legacy_count)
    except Exception:
        return (False, 0, CURRENT_SCHEMA_VERSION, 0)


def get_changelog_content() -> str:
    """Load changelog content for display."""
    changelog_paths = [
        Path(__file__).parent.parent / "CHANGELOG.md",
        Path(__file__).parent / "CHANGELOG.md",
    ]

    for path in changelog_paths:
        if path.exists():
            return path.read_text()

    return ""


def run_migration_overlay() -> str | None:
    """Run migration overlay only if schema migration is needed.

    Returns:
        "migrate" if user chose to migrate, "later" or None otherwise
    """
    needs_migration, current, target, legacy = check_migration_needed()

    # Only show popup for actual schema migrations, not for legacy entries
    if not needs_migration:
        return None

    changelog = get_changelog_content()

    app = MigrationOverlayApp(
        current_version=current,
        target_version=target,
        legacy_count=legacy,
        changelog_content=changelog,
    )

    return app.run()


def apply_migration_from_tui() -> bool:
    """Apply migrations from TUI context.

    Returns:
        True if migration successful, False otherwise
    """
    from rekall.backup import create_backup
    from rekall.db import Database

    config = get_config()

    try:
        # Create backup first
        create_backup(config.db_path)

        # Apply migrations
        db = Database(config.db_path)
        db.init()
        db.close()

        return True
    except Exception:
        return False


# =============================================================================
# Sources Inbox Browser (Feature 013 - US3)
# =============================================================================


def format_relative_time(dt: datetime) -> str:
    """Format datetime as relative time string (e.g., '2h ago').

    Args:
        dt: Datetime to format

    Returns:
        Relative time string
    """
    now = datetime.now()
    delta = now - dt

    minutes = int(delta.total_seconds() / 60)
    hours = int(delta.total_seconds() / 3600)
    days = int(delta.total_seconds() / 86400)

    if minutes < 60:
        time_str = t("inbox.time.minutes", n=max(1, minutes))
    elif hours < 24:
        time_str = t("inbox.time.hours", n=hours)
    else:
        time_str = t("inbox.time.days", n=days)

    return t("inbox.time_ago", time=time_str)


class InboxBrowseApp(SortableTableMixin, App):
    """Textual app for browsing inbox entries with DataTable and detail panel."""

    TABLE_ID = "inbox-table"

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

    #browse-container {
        height: 100%;
    }

    #section-title {
        padding: 0 2;
        margin-bottom: 1;
    }

    #inbox-table {
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

    Footer {
        background: $surface-darken-1;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "quit", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("i", "trigger_import", "Import", show=True),
        Binding("e", "trigger_enrich", "Enrich", show=True),
        Binding("v", "toggle_quarantine", "Quarantine", show=True),
        Binding("d", "delete_entry", "Delete", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def __init__(self, db, show_quarantine: bool = False):
        super().__init__()
        self.init_sorting()  # Initialize sorting from SortableTableMixin
        self.db = db
        self.show_quarantine = show_quarantine
        self.entries: list = []
        self.selected_entry = None
        self.result_action = None  # ("import"|"enrich"|"delete", entry)

    def compose(self) -> ComposeResult:
        yield create_banner_container()
        title = t("inbox.quarantine") if self.show_quarantine else t("inbox.title")
        yield Static(f"[dim]{title}[/dim]", id="section-title")
        yield Container(
            Container(
                DataTable(id="inbox-table"),
            ),
            VerticalScroll(
                Static("", id="detail-title"),
                Static("", id="detail-meta"),
                Static("", id="detail-content"),
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

    def on_mount(self) -> None:
        """Populate the DataTable with inbox entries."""
        self._load_entries()
        self._setup_table()

    def _load_entries(self) -> None:
        """Load entries from database."""
        if self.show_quarantine:
            self.entries = self.db.get_inbox_entries(quarantine_only=True, limit=500)
        else:
            self.entries = self.db.get_inbox_entries(valid_only=True, limit=500)

    def _setup_table(self) -> None:
        """Setup and populate the DataTable."""
        table = self.query_one("#inbox-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Clear existing
        table.clear(columns=True)

        # Add columns
        table.add_column(t("inbox.url"), width=50, key="url")
        table.add_column(t("inbox.domain"), width=20, key="domain")
        table.add_column(t("inbox.cli_source"), width=10, key="cli")
        table.add_column(t("inbox.project"), width=20, key="project")
        table.add_column(t("inbox.status"), width=12, key="status")
        table.add_column(t("inbox.captured_at"), width=12, key="captured")

        # Populate rows
        self._populate_table()

        # Update detail panel for first entry
        if self.entries:
            self.selected_entry = self.entries[0]
            self._update_detail_panel(self.entries[0])

    def _populate_table(self) -> None:
        """Populate table rows with current entries."""
        table = self.query_one("#inbox-table", DataTable)

        for entry in self.entries:
            # Format URL (truncate if too long)
            url = entry.url
            if len(url) > 48:
                url = url[:45] + "..."

            # Format domain
            domain = entry.domain or "—"
            if len(domain) > 18:
                domain = domain[:15] + "..."

            # Format CLI source
            cli = entry.cli_source or "—"

            # Format project
            project = entry.project or "—"
            if len(project) > 18:
                project = project[:15] + "..."

            # Format status with icon and color
            if not entry.is_valid:
                status = f"[red]⚠ {t('inbox.status.quarantine')}[/red]"
            elif entry.enriched_at:
                status = f"[green]✓ {t('inbox.status.enriched')}[/green]"
            else:
                status = f"[yellow]○ {t('inbox.status.pending')}[/yellow]"

            # Format captured time
            captured = format_relative_time(entry.captured_at)

            table.add_row(url, domain, cli, project, status, captured, key=entry.id)

    # =========================================================================
    # Sortable table implementation (SortableTableMixin)
    # =========================================================================

    COLUMNS = [
        ("url", "inbox.url", 50),
        ("domain", "inbox.domain", 20),
        ("cli", "inbox.cli_source", 10),
        ("project", "inbox.project", 20),
        ("status", "inbox.status", 12),
        ("captured", "inbox.captured_at", 12),
    ]

    def get_sort_key(self, column_key: str):
        """Get sort key function for a column."""
        key_map = {
            "url": lambda e: e.url.lower(),
            "domain": lambda e: (e.domain or "").lower(),
            "cli": lambda e: (e.cli_source or ""),
            "project": lambda e: (e.project or "").lower(),
            "status": lambda e: (0 if not e.is_valid else (1 if e.enriched_at else 2)),  # quarantine, enriched, pending
            "captured": lambda e: e.captured_at,
        }
        return key_map.get(column_key, lambda e: "")

    def refresh_table(self) -> None:
        """Refresh the DataTable with current entries and sort state."""
        table = self.query_one("#inbox-table", DataTable)
        table.clear(columns=True)

        # Add columns with sort indicators
        for key, label_key, width in self.COLUMNS:
            base_label = t(label_key)
            if self.sort_column == key:
                indicator = " ▼" if self.sort_reverse else " ▲"
                label = f"{base_label}{indicator}"
            else:
                label = base_label
            table.add_column(label, width=width, key=key)

        # Re-populate rows
        self._populate_table()

        # Update header
        title = t("inbox.quarantine") if self.show_quarantine else t("inbox.title")
        self.query_one("#section-title", Static).update(f"[dim]{title} ({len(self.entries)})[/dim]")

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header click for sorting."""
        column_key = event.column_key.value

        if self.sort_column == column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_key
            self.sort_reverse = False

        self.sort_entries()
        self.refresh_table()

        direction = "▼" if self.sort_reverse else "▲"
        self.show_left_notify(f"Trié par {column_key} {direction}", 1.5)

    def _update_detail_panel(self, entry) -> None:
        """Update detail panel with entry information."""
        title_widget = self.query_one("#detail-title", Static)
        meta_widget = self.query_one("#detail-meta", Static)
        content_widget = self.query_one("#detail-content", Static)

        # Title: Full URL
        title_widget.update(f"[bold]{entry.url}[/bold]")

        # Meta: CLI, Project, Date
        meta_parts = []
        meta_parts.append(f"[dim]CLI:[/dim] {entry.cli_source}")
        if entry.project:
            meta_parts.append(f"[dim]Project:[/dim] {entry.project}")
        meta_parts.append(f"[dim]Captured:[/dim] {entry.captured_at.strftime('%Y-%m-%d %H:%M')}")
        if entry.enriched_at:
            meta_parts.append(f"[dim]Enriched:[/dim] {entry.enriched_at.strftime('%Y-%m-%d %H:%M')}")
        if not entry.is_valid:
            meta_parts.append(f"[red]Error: {entry.validation_error}[/red]")
        meta_widget.update(" | ".join(meta_parts))

        # Content: Context from capture
        content_parts = []
        if entry.user_query:
            content_parts.append(f"[bold]User Query:[/bold]\n{entry.user_query}")
        if entry.assistant_snippet:
            snippet = entry.assistant_snippet[:500] + "..." if len(entry.assistant_snippet or "") > 500 else entry.assistant_snippet
            content_parts.append(f"\n[bold]Assistant Context:[/bold]\n{snippet}")
        if entry.surrounding_text:
            surrounding = entry.surrounding_text[:300] + "..." if len(entry.surrounding_text or "") > 300 else entry.surrounding_text
            content_parts.append(f"\n[bold]Surrounding Text:[/bold]\n{surrounding}")

        if content_parts:
            content_widget.update("\n".join(content_parts))
        else:
            content_widget.update("[dim]No context available[/dim]")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Update detail panel when row is highlighted."""
        if event.row_key is None:
            return

        # Find entry by ID
        entry_id = str(event.row_key.value)
        for entry in self.entries:
            if entry.id == entry_id:
                self.selected_entry = entry
                self._update_detail_panel(entry)
                break

    def action_quit(self) -> None:
        """Exit the app."""
        self.exit(result=None)

    def action_trigger_import(self) -> None:
        """Trigger import action."""
        self.result_action = ("import", None)
        self.exit(result="import")

    def action_trigger_enrich(self) -> None:
        """Trigger enrich action."""
        self.result_action = ("enrich", None)
        self.exit(result="enrich")

    def action_toggle_quarantine(self) -> None:
        """Toggle between quarantine and normal view."""
        self.show_quarantine = not self.show_quarantine
        self._load_entries()
        self._setup_table()
        # Update title
        title = t("inbox.quarantine") if self.show_quarantine else t("inbox.title")
        count = len(self.entries)
        self.query_one("#section-title", Static).update(f"[dim]{title} ({count})[/dim]")
        view_msg = t("inbox.view_quarantine") if not self.show_quarantine else t("inbox.view_all")
        self.show_left_notify(view_msg)

    def action_delete_entry(self) -> None:
        """Delete selected entry."""
        if not self.selected_entry:
            return

        entry = self.selected_entry

        # Delete from database
        if self.db.delete_inbox_entry(entry.id):
            # Remove from local list
            self.entries = [e for e in self.entries if e.id != entry.id]

            # Refresh table
            table = self.query_one("#inbox-table", DataTable)
            table.clear()
            self._populate_table()

            # Update selection
            if self.entries:
                self.selected_entry = self.entries[0]
                self._update_detail_panel(self.entries[0])
            else:
                self.selected_entry = None
                self.query_one("#detail-title", Static).update("")
                self.query_one("#detail-meta", Static).update("")
                self.query_one("#detail-content", Static).update(t("inbox.empty"))

            self.show_left_notify(t("inbox.delete.success"))

    def action_refresh(self) -> None:
        """Refresh the table."""
        self._load_entries()
        table = self.query_one("#inbox-table", DataTable)
        table.clear()
        self._populate_table()

        # Update title count
        title = t("inbox.quarantine") if self.show_quarantine else t("inbox.title")
        count = len(self.entries)
        self.query_one("#section-title", Static).update(f"[dim]{title} ({count})[/dim]")

        if self.entries:
            self.selected_entry = self.entries[0]
            self._update_detail_panel(self.entries[0])

        self.show_left_notify("Refreshed")


def run_inbox_browser(db, show_quarantine: bool = False) -> str | None:
    """Run the inbox browser TUI.

    Args:
        db: Database instance
        show_quarantine: Whether to show quarantine view initially

    Returns:
        Action string ("import", "enrich") or None
    """
    app = InboxBrowseApp(db, show_quarantine)
    return app.run()


# =============================================================================
# Sources Staging Browser (Feature 013 - US4)
# =============================================================================


class StagingBrowseApp(SortableTableMixin, App):
    """Textual app for browsing staging entries with DataTable, scores and detail panel."""

    TABLE_ID = "staging-table"

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

    #browse-container {
        height: 100%;
    }

    #section-title {
        padding: 0 2;
        margin-bottom: 1;
    }

    #staging-table {
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

    Footer {
        background: $surface-darken-1;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "quit", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("p", "promote_selected", "Promote", show=True),
        Binding("a", "auto_promote", "Auto-promote", show=True),
        Binding("r", "refresh_scores", "Refresh", show=True),
        Binding("enter", "view_details", "Details", show=True),
    ]

    def __init__(self, db, show_promoted: bool = False):
        super().__init__()
        self.init_sorting()  # Initialize sorting from SortableTableMixin
        self.db = db
        self.show_promoted = show_promoted
        self.entries: list = []
        self.selected_entry = None
        self.result_action = None

    def compose(self) -> ComposeResult:
        yield create_banner_container()
        title = t("staging.title")
        yield Static(f"[dim]{title}[/dim]", id="section-title")
        yield Container(
            Container(
                DataTable(id="staging-table"),
            ),
            VerticalScroll(
                Static("", id="detail-title"),
                Static("", id="detail-meta"),
                Static("", id="detail-content"),
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

    def on_mount(self) -> None:
        """Populate the DataTable with staging entries."""
        self._load_entries()
        self._setup_table()

    def _load_entries(self) -> None:
        """Load entries from database and calculate scores."""
        from rekall.promotion import calculate_promotion_score

        # Get all staging entries
        if self.show_promoted:
            self.entries = self.db.get_staging_entries(limit=500)
        else:
            # Get non-promoted entries
            all_entries = self.db.get_staging_entries(limit=500)
            self.entries = [e for e in all_entries if e.promoted_at is None]

        # Calculate and cache scores
        for entry in self.entries:
            entry.promotion_score = calculate_promotion_score(entry)

    def _setup_table(self) -> None:
        """Setup and populate the DataTable."""
        table = self.query_one("#staging-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        # Clear existing
        table.clear(columns=True)

        # Add columns
        table.add_column("", width=3, key="indicator")  # Promotion indicator
        table.add_column(t("staging.domain"), width=25, key="domain")
        table.add_column(t("staging.title.desc")[:20], width=35, key="title")
        table.add_column(t("staging.content_type"), width=14, key="type")
        table.add_column(t("staging.citations"), width=8, key="citations")
        table.add_column(t("staging.projects"), width=8, key="projects")
        table.add_column("Score", width=8, key="score")

        # Populate rows
        self._populate_table()

        # Update detail panel for first entry
        if self.entries:
            self.selected_entry = self.entries[0]
            self._update_detail_panel(self.entries[0])

    def _populate_table(self) -> None:
        """Populate table rows with current entries."""
        from rekall.promotion import get_promotion_indicator

        table = self.query_one("#staging-table", DataTable)

        for entry in self.entries:
            # Get promotion indicator
            indicator = get_promotion_indicator(entry, score=entry.promotion_score)
            if indicator == "⬆":
                indicator_str = f"[green]{indicator}[/green]"
            elif indicator == "→":
                indicator_str = f"[yellow]{indicator}[/yellow]"
            elif indicator == "✓":
                indicator_str = f"[blue]{indicator}[/blue]"
            elif indicator == "⚠":
                indicator_str = f"[red]{indicator}[/red]"
            else:
                indicator_str = " "

            # Format domain
            domain = entry.domain or "—"
            if len(domain) > 23:
                domain = domain[:20] + "..."

            # Format title
            title = entry.title or "—"
            if len(title) > 33:
                title = title[:30] + "..."

            # Format content type
            content_type = entry.content_type or "other"

            # Format counts
            citations = str(entry.citation_count)
            projects = str(entry.project_count)

            # Format score with color
            score = entry.promotion_score or 0.0
            if score >= 70:
                score_str = f"[green]{score:.0f}[/green]"
            elif score >= 56:  # Near threshold (80% of 70)
                score_str = f"[yellow]{score:.0f}[/yellow]"
            else:
                score_str = f"[dim]{score:.0f}[/dim]"

            table.add_row(
                indicator_str, domain, title, content_type,
                citations, projects, score_str, key=entry.id
            )

    # =========================================================================
    # Sortable table implementation (SortableTableMixin)
    # =========================================================================

    COLUMNS = [
        ("indicator", None, 3),  # No translation for indicator
        ("domain", "staging.domain", 25),
        ("title", "staging.title.desc", 35),
        ("type", "staging.content_type", 14),
        ("citations", "staging.citations", 8),
        ("projects", "staging.projects", 8),
        ("score", None, 8),  # "Score" label
    ]

    def get_sort_key(self, column_key: str):
        """Get sort key function for a column."""
        key_map = {
            "indicator": lambda e: e.promotion_score or 0,  # Sort by score for indicator
            "domain": lambda e: (e.domain or "").lower(),
            "title": lambda e: (e.title or "").lower(),
            "type": lambda e: e.content_type or "",
            "citations": lambda e: e.citation_count,
            "projects": lambda e: e.project_count,
            "score": lambda e: e.promotion_score or 0,
        }
        return key_map.get(column_key, lambda e: "")

    def refresh_table(self) -> None:
        """Refresh the DataTable with current entries and sort state."""
        table = self.query_one("#staging-table", DataTable)
        table.clear(columns=True)

        # Add columns with sort indicators
        for key, label_key, width in self.COLUMNS:
            if label_key:
                base_label = t(label_key)
                if len(base_label) > width - 2:
                    base_label = base_label[:width - 2]
            elif key == "score":
                base_label = "Score"
            else:
                base_label = ""  # indicator column

            if self.sort_column == key:
                indicator = " ▼" if self.sort_reverse else " ▲"
                label = f"{base_label}{indicator}"
            else:
                label = base_label
            table.add_column(label, width=width, key=key)

        # Re-populate rows
        self._populate_table()

        # Update header
        title = t("staging.title")
        self.query_one("#section-title", Static).update(f"[dim]{title} ({len(self.entries)})[/dim]")

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column header click for sorting."""
        column_key = event.column_key.value

        if self.sort_column == column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_key
            self.sort_reverse = False

        self.sort_entries()
        self.refresh_table()

        direction = "▼" if self.sort_reverse else "▲"
        self.show_left_notify(f"Trié par {column_key} {direction}", 1.5)

    def _update_detail_panel(self, entry) -> None:
        """Update detail panel with entry information."""
        title_widget = self.query_one("#detail-title", Static)
        meta_widget = self.query_one("#detail-meta", Static)
        content_widget = self.query_one("#detail-content", Static)

        # Title: Full URL
        title_widget.update(f"[bold]{entry.url}[/bold]")

        # Meta info
        meta_parts = []
        if entry.title:
            meta_parts.append(f"[bold]{entry.title}[/bold]")
        meta_parts.append(f"[dim]Type:[/dim] {entry.content_type or 'other'}")
        meta_parts.append(f"[dim]Lang:[/dim] {entry.language or '—'}")
        if entry.http_status:
            color = "green" if entry.http_status == 200 else "yellow"
            meta_parts.append(f"[dim]HTTP:[/dim] [{color}]{entry.http_status}[/{color}]")
        meta_widget.update(" | ".join(meta_parts))

        # Content: Description and stats
        content_parts = []
        if entry.description:
            content_parts.append(f"[bold]Description:[/bold]\n{entry.description}")

        content_parts.append("\n[bold]Statistics:[/bold]")
        content_parts.append(f"  Citations: {entry.citation_count}")
        content_parts.append(f"  Projects: {entry.project_count} ({entry.projects_list or '—'})")
        content_parts.append(f"  Score: {entry.promotion_score:.1f}/100")

        if entry.first_seen:
            content_parts.append(f"  First seen: {entry.first_seen.strftime('%Y-%m-%d')}")
        if entry.last_seen:
            content_parts.append(f"  Last seen: {entry.last_seen.strftime('%Y-%m-%d')}")

        if entry.promoted_at:
            content_parts.append(f"\n[green]✓ Promoted on {entry.promoted_at.strftime('%Y-%m-%d')}[/green]")

        content_widget.update("\n".join(content_parts))

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Update detail panel when row is highlighted."""
        if event.row_key is None:
            return

        entry_id = str(event.row_key.value)
        for entry in self.entries:
            if entry.id == entry_id:
                self.selected_entry = entry
                self._update_detail_panel(entry)
                break

    def action_quit(self) -> None:
        """Exit the app."""
        self.exit(result=None)

    def action_promote_selected(self) -> None:
        """Promote selected entry manually."""
        if not self.selected_entry:
            return

        if self.selected_entry.promoted_at:
            self.show_left_notify("Already promoted")
            return

        from rekall.promotion import promote_source

        result = promote_source(self.db, self.selected_entry)
        if result.success:
            self.show_left_notify(t("promotion.success"))
            self._load_entries()
            table = self.query_one("#staging-table", DataTable)
            table.clear()
            self._populate_table()
        else:
            self.show_left_notify(f"[red]{result.error}[/red]")

    def action_auto_promote(self) -> None:
        """Auto-promote all eligible entries."""
        from rekall.promotion import auto_promote_eligible

        result = auto_promote_eligible(self.db)

        if result.promoted > 0:
            self.show_left_notify(t("promotion.auto.success", count=result.promoted))
            self._load_entries()
            table = self.query_one("#staging-table", DataTable)
            table.clear()
            self._populate_table()
        else:
            self.show_left_notify(t("promotion.auto.none"))

    def action_refresh_scores(self) -> None:
        """Refresh scores for all entries."""
        self._load_entries()

        # Update scores in database
        for entry in self.entries:
            self.db.update_staging(entry)

        # Refresh table
        table = self.query_one("#staging-table", DataTable)
        table.clear()
        self._populate_table()

        # Update title count
        count = len(self.entries)
        title = t("staging.title")
        self.query_one("#section-title", Static).update(f"[dim]{title} ({count})[/dim]")

        if self.entries:
            self.selected_entry = self.entries[0]
            self._update_detail_panel(self.entries[0])

        self.show_left_notify("Scores refreshed")

    def action_view_details(self) -> None:
        """View details of selected entry (placeholder for future expansion)."""
        if self.selected_entry:
            self.show_left_notify(f"URL: {self.selected_entry.url[:50]}...")


def run_staging_browser(db, show_promoted: bool = False) -> str | None:
    """Run the staging browser TUI.

    Args:
        db: Database instance
        show_promoted: Whether to include promoted entries

    Returns:
        Action string or None
    """
    app = StagingBrowseApp(db, show_promoted)
    return app.run()


# =============================================================================
# Unified Sources Manager (Feature 018)
# =============================================================================


class UnifiedSourcesApp(SortableTableMixin, App):
    """Unified Sources Manager with tabs for Sources, Inbox, and Staging.

    Provides a single interface to manage the entire sources workflow:
    - Sources: Promoted/active sources in the knowledge base
    - Inbox: Captured URLs awaiting processing
    - Staging: Enriched sources awaiting promotion
    """

    CSS = """
    Screen {
        background: $surface;
        layers: base modal;
    }

    /* Tab styling */
    TabbedContent {
        height: 1fr;
    }

    TabPane {
        padding: 0;
    }

    /* Tables */
    .sources-table {
        height: 1fr;
        min-height: 10;
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

    /* Detail panel */
    #detail-panel {
        height: auto;
        max-height: 12;
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

    /* Left notification */
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

    /* Filter overlay */
    #filter-overlay {
        display: none;
        layer: modal;
        dock: top;
        width: 60;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        margin: 10 40;
        background: $surface;
        border: thick $primary;
    }

    #filter-overlay.visible {
        display: block;
    }

    #filter-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    /* Actions overlay */
    #actions-overlay {
        display: none;
        layer: modal;
        dock: top;
        width: 50;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        margin: 10 45;
        background: $surface;
        border: thick $secondary;
    }

    #actions-overlay.visible {
        display: block;
    }

    #actions-title {
        text-style: bold;
        text-align: center;
        margin-bottom: 1;
    }

    #actions-list {
        height: auto;
        max-height: 15;
    }

    /* Enrich overlay */
    #enrich-overlay {
        display: none;
        layer: modal;
        dock: top;
        width: 80;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        margin: 5 30;
        background: $surface;
        border: thick #4367CD;
    }

    #enrich-overlay.visible {
        display: block;
    }

    #enrich-type {
        layout: horizontal;
        height: auto;
        width: auto;
    }

    #enrich-type > RadioButton {
        width: auto;
        padding: 0 1;
    }

    #enrich-score {
        layout: horizontal;
        height: auto;
        width: auto;
    }

    #enrich-score > RadioButton {
        width: auto;
        padding: 0 1;
    }

    #enrich-title {
        text-style: bold;
        text-align: center;
        color: #93B5F7;
        margin-bottom: 0;
    }

    #enrich-url {
        color: #93B5F7;
        margin-bottom: 0;
    }

    #enrich-form {
        height: auto;
        padding: 0;
    }

    .enrich-label {
        color: #93B5F7;
        text-style: bold;
        margin-top: 0;
    }

    #enrich-buttons {
        layout: horizontal;
        margin-top: 1;
        align: center middle;
        height: 3;
    }

    #enrich-buttons Button {
        margin: 0 1;
        min-width: 12;
        background: #4367CD;
        color: #93B5F7;
    }

    #enrich-buttons Button:hover {
        background: #93B5F7;
        color: #4367CD;
    }

    Footer {
        background: $surface-darken-1;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "close_or_quit", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("s", "tab_sources", "Sources", show=True),
        Binding("i", "tab_inbox", "Inbox", show=True),
        Binding("g", "tab_staging", "Staging", show=True),
        Binding("f", "toggle_filter", "Filter", show=True),
        Binding("enter", "show_actions", "Actions", show=True),
        Binding("slash", "search", "Search", show=False),
        Binding("e", "quick_edit", "Edit", show=False),
        Binding("d", "quick_delete", "Delete", show=False),
        Binding("t", "quick_tags", "Tags", show=False),
        Binding("p", "quick_promote", "Promote", show=False),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def __init__(self, db):
        super().__init__()
        self.init_sorting()
        self.db = db
        self.current_tab = "sources"  # sources, inbox, staging

        # Data for each tab
        self.sources: list = []
        self.inbox_entries: list = []
        self.staging_entries: list = []

        # Selected items
        self.selected_source = None
        self.selected_inbox = None
        self.selected_staging = None

        # For mixin compatibility
        self.entries = self.sources

        # Cache
        self.source_tags: dict[str, list[str]] = {}

        # Tags suggester for auto-completion (supports comma-separated tags)
        all_tags = db.get_all_tags_with_counts()
        self.all_tag_names = [t["theme"] for t in all_tags]
        self.tags_suggester = MultiTagSuggester(self.all_tag_names, case_sensitive=False)

        # Result for caller
        self.result_action = None

    def compose(self) -> ComposeResult:
        yield create_banner_container()

        # Tabbed content with counts in labels
        with TabbedContent(id="tabs"):
            with TabPane("Sources (0)", id="tab-sources"):
                yield DataTable(id="sources-table", classes="sources-table")

            with TabPane("Inbox (0)", id="tab-inbox"):
                yield DataTable(id="inbox-table", classes="sources-table")

            with TabPane("Staging (0)", id="tab-staging"):
                yield DataTable(id="staging-table", classes="sources-table")

        # Detail panel (shared)
        yield Container(
            Static("", id="detail-title"),
            Static("", id="detail-meta"),
            id="detail-panel",
        )

        yield Footer()
        yield Static("", id="left-notify")

        # Filter overlay
        yield Container(
            Static("[bold]Filtrer les sources[/bold]", id="filter-title"),
            Static("[dim]f: fermer • Entrez critères de recherche[/dim]"),
            Input(placeholder="Recherche...", id="filter-input"),
            id="filter-overlay",
        )

        # Actions overlay
        yield Container(
            Static("[bold]Actions[/bold]", id="actions-title"),
            ListView(id="actions-list"),
            Static("[dim]Entrée: sélectionner • Esc: fermer[/dim]"),
            id="actions-overlay",
        )

        # Enrich overlay
        yield Container(
            Static("[bold]Enrichissement[/bold]", id="enrich-title"),
            Static("", id="enrich-url"),
            Container(
                Static("Titre", classes="enrich-label"),
                Input(placeholder="Titre de la source", id="enrich-input-title"),
                Static("Type", classes="enrich-label"),
                RadioSet(
                    RadioButton("documentation", id="type-doc"),
                    RadioButton("article", id="type-article"),
                    RadioButton("tutorial", id="type-tutorial"),
                    RadioButton("paper", id="type-paper"),
                    RadioButton("tool", id="type-tool"),
                    RadioButton("reference", id="type-ref"),
                    RadioButton("other", id="type-other"),
                    id="enrich-type",
                ),
                Static("Tags", classes="enrich-label"),
                Input(
                    placeholder="tag1, tag2, tag3",
                    id="enrich-input-tags",
                    suggester=self.tags_suggester,
                ),
                Static("Score (1-5)", classes="enrich-label"),
                RadioSet(
                    RadioButton("1", id="score-1"),
                    RadioButton("2", id="score-2"),
                    RadioButton("3", id="score-3", value=True),
                    RadioButton("4", id="score-4"),
                    RadioButton("5", id="score-5"),
                    id="enrich-score",
                ),
                id="enrich-form",
            ),
            Container(
                Button("Annuler", id="enrich-cancel"),
                Button("OK", id="enrich-submit"),
                id="enrich-buttons",
            ),
            id="enrich-overlay",
        )

    def on_mount(self) -> None:
        """Initialize all tables and load data."""
        self._load_all_data()
        self._setup_sources_table()
        self._setup_inbox_table()
        self._setup_staging_table()
        self._update_stats()

        # Focus first tab
        self._switch_to_tab("sources")

    def _load_all_data(self) -> None:
        """Load data for all tabs."""
        # Sources
        self.sources = list(self.db.list_sources(limit=500))
        for source in self.sources:
            self.source_tags[source.id] = self.db.get_source_themes(source.id)

        # Inbox
        self.inbox_entries = list(self.db.get_inbox_entries(valid_only=True, limit=500))

        # Staging
        self.staging_entries = list(self.db.get_staging_entries(promoted=False, limit=500))

    def _update_stats(self) -> None:
        """Update tab labels with counts."""
        tabs = self.query_one("#tabs", TabbedContent)
        # Update tab labels with counts
        for tab in tabs.query("Tab"):
            tab_id = str(tab.id)
            if "tab-sources" in tab_id:
                tab.label = f"Sources ({len(self.sources)})"
            elif "tab-inbox" in tab_id:
                tab.label = f"Inbox ({len(self.inbox_entries)})"
            elif "tab-staging" in tab_id:
                tab.label = f"Staging ({len(self.staging_entries)})"

    # =========================================================================
    # Sources Table
    # =========================================================================

    def _setup_sources_table(self) -> None:
        """Setup sources table columns and data."""
        table = self.query_one("#sources-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        table.add_column(t("source.domain"), width=25, key="domain")
        table.add_column(t("source.score"), width=8, key="score")
        table.add_column(t("source.status"), width=10, key="status")
        table.add_column(t("source.role"), width=12, key="role")
        table.add_column(t("source.reliability"), width=5, key="reliability")
        table.add_column(t("source.usage_count"), width=6, key="usages")
        table.add_column(t("tags.label"), width=20, key="tags")

        self._populate_sources_table()

    def _populate_sources_table(self) -> None:
        """Populate sources table rows."""
        table = self.query_one("#sources-table", DataTable)
        table.clear()

        for i, source in enumerate(self.sources):
            score = source.personal_score
            if score >= 70:
                score_str = f"[green]{score:.0f}[/green]"
            elif score >= 40:
                score_str = f"[yellow]{score:.0f}[/yellow]"
            else:
                score_str = f"[red]{score:.0f}[/red]"

            status_icons = {"active": "✓", "inaccessible": "⚠", "archived": "📦"}
            status_str = f"{status_icons.get(source.status, '?')} {source.status}"

            role_icons = {"hub": "🔗", "authority": "⭐", "unclassified": "·"}
            role_str = f"{role_icons.get(source.role, '·')} {source.role}"

            tags = self.source_tags.get(source.id, [])
            tags_str = ", ".join(tags[:2]) + (f" +{len(tags)-2}" if len(tags) > 2 else "") if tags else "—"

            table.add_row(
                source.domain[:23] + "…" if len(source.domain) > 23 else source.domain,
                Text.from_markup(score_str),
                Text.from_markup(status_str),
                Text.from_markup(role_str),
                source.reliability or "—",
                str(source.usage_count),
                tags_str,
                key=str(i),
            )

        if self.sources:
            self.selected_source = self.sources[0]

    # =========================================================================
    # Inbox Table
    # =========================================================================

    def _setup_inbox_table(self) -> None:
        """Setup inbox table columns and data."""
        table = self.query_one("#inbox-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        table.add_column(t("inbox.url"), width=40, key="url")
        table.add_column(t("inbox.domain"), width=18, key="domain")
        table.add_column(t("inbox.project"), width=15, key="project")
        table.add_column(t("inbox.status"), width=12, key="status")
        table.add_column(t("inbox.captured_at"), width=12, key="captured")

        self._populate_inbox_table()

    def _populate_inbox_table(self) -> None:
        """Populate inbox table rows."""
        table = self.query_one("#inbox-table", DataTable)
        table.clear()

        for entry in self.inbox_entries:
            url = entry.url[:38] + "…" if len(entry.url) > 38 else entry.url
            domain = (entry.domain or "—")[:16]
            project = (entry.project or "—")[:13]

            if not entry.is_valid:
                status = f"[red]⚠ quarantine[/red]"
            elif entry.enriched_at:
                status = f"[green]✓ enriched[/green]"
            else:
                status = f"[yellow]○ pending[/yellow]"

            captured = format_relative_time(entry.captured_at)

            table.add_row(url, domain, project, Text.from_markup(status), captured, key=entry.id)

        if self.inbox_entries:
            self.selected_inbox = self.inbox_entries[0]

    # =========================================================================
    # Staging Table
    # =========================================================================

    def _setup_staging_table(self) -> None:
        """Setup staging table columns and data."""
        table = self.query_one("#staging-table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = True

        table.add_column(t("staging.domain"), width=22, key="domain")
        table.add_column("Title", width=30, key="title")
        table.add_column(t("staging.content_type"), width=12, key="type")
        table.add_column(t("staging.citations"), width=8, key="citations")
        table.add_column("Score", width=8, key="score")
        table.add_column("", width=3, key="indicator")

        self._populate_staging_table()

    def _populate_staging_table(self) -> None:
        """Populate staging table rows."""
        from rekall.promotion import get_promotion_indicator

        table = self.query_one("#staging-table", DataTable)
        table.clear()

        for entry in self.staging_entries:
            domain = (entry.domain or "—")[:20]
            title = (entry.title or "—")[:28]
            content_type = entry.content_type or "other"

            score = entry.promotion_score or 0
            if score >= 70:
                score_str = f"[green]{score:.0f}[/green]"
            elif score >= 56:
                score_str = f"[yellow]{score:.0f}[/yellow]"
            else:
                score_str = f"[dim]{score:.0f}[/dim]"

            indicator = get_promotion_indicator(entry, score=score)
            ind_colors = {"⬆": "green", "→": "yellow", "✓": "blue", "⚠": "red"}
            ind_str = f"[{ind_colors.get(indicator, 'white')}]{indicator}[/]" if indicator else " "

            table.add_row(
                domain, title, content_type,
                str(entry.citation_count),
                Text.from_markup(score_str),
                Text.from_markup(ind_str),
                key=entry.id,
            )

        if self.staging_entries:
            self.selected_staging = self.staging_entries[0]

    # =========================================================================
    # Tab Navigation
    # =========================================================================

    def _switch_to_tab(self, tab: str) -> None:
        """Switch to a specific tab."""
        self.current_tab = tab
        tabs = self.query_one("#tabs", TabbedContent)

        tab_map = {"sources": "tab-sources", "inbox": "tab-inbox", "staging": "tab-staging"}
        tabs.active = tab_map[tab]

        # Update entries reference for sorting
        if tab == "sources":
            self.entries = self.sources
        elif tab == "inbox":
            self.entries = self.inbox_entries
        else:
            self.entries = self.staging_entries

        # Reset sort state on tab switch
        self.sort_column = None
        self.sort_reverse = False

        self._update_detail_panel()

    def action_tab_sources(self) -> None:
        """Switch to Sources tab."""
        self._switch_to_tab("sources")
        self.show_left_notify("Sources", 1.0)

    def action_tab_inbox(self) -> None:
        """Switch to Inbox tab."""
        self._switch_to_tab("inbox")
        self.show_left_notify("Inbox", 1.0)

    def action_tab_staging(self) -> None:
        """Switch to Staging tab."""
        self._switch_to_tab("staging")
        self.show_left_notify("Staging", 1.0)

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Handle tab activation via click."""
        tab_id = str(event.tab.id)
        if "sources" in tab_id:
            self.current_tab = "sources"
            self.entries = self.sources
            if self.sources and not self.selected_source:
                self.selected_source = self.sources[0]
        elif "inbox" in tab_id:
            self.current_tab = "inbox"
            self.entries = self.inbox_entries
            if self.inbox_entries and not self.selected_inbox:
                self.selected_inbox = self.inbox_entries[0]
        elif "staging" in tab_id:
            self.current_tab = "staging"
            self.entries = self.staging_entries
            if self.staging_entries and not self.selected_staging:
                self.selected_staging = self.staging_entries[0]

        self.sort_column = None
        self.sort_reverse = False
        self._update_detail_panel()

    # =========================================================================
    # Detail Panel
    # =========================================================================

    def _update_detail_panel(self) -> None:
        """Update detail panel based on current tab and selection."""
        title_widget = self.query_one("#detail-title", Static)
        meta_widget = self.query_one("#detail-meta", Static)

        if self.current_tab == "sources" and self.selected_source:
            src = self.selected_source
            title_widget.update(f"[bold cyan]{src.domain}[/bold cyan]")
            tags = self.source_tags.get(src.id, [])
            tags_str = ", ".join(tags) if tags else "[dim]no tags[/dim]"
            meta_widget.update(
                f"Score: {src.personal_score:.0f} | "
                f"Status: {src.status} | "
                f"Uses: {src.usage_count} | "
                f"Tags: {tags_str}"
            )

        elif self.current_tab == "inbox" and self.selected_inbox:
            entry = self.selected_inbox
            title_widget.update(f"[bold]{entry.url[:60]}{'…' if len(entry.url) > 60 else ''}[/bold]")
            meta_widget.update(
                f"Domain: {entry.domain or '—'} | "
                f"Project: {entry.project or '—'} | "
                f"CLI: {entry.cli_source or '—'}"
            )

        elif self.current_tab == "staging" and self.selected_staging:
            entry = self.selected_staging
            title_widget.update(f"[bold]{entry.title or entry.url[:50]}[/bold]")
            meta_widget.update(
                f"Domain: {entry.domain or '—'} | "
                f"Type: {entry.content_type or '—'} | "
                f"Score: {entry.promotion_score:.0f} | "
                f"Citations: {entry.citation_count}"
            )
        else:
            title_widget.update("[dim]No selection[/dim]")
            meta_widget.update("")

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row selection in any table."""
        if event.row_key is None:
            return

        table_id = event.data_table.id
        key = str(event.row_key.value) if event.row_key.value else None

        if not key:
            return

        if table_id == "sources-table":
            try:
                idx = int(key)
                if 0 <= idx < len(self.sources):
                    self.selected_source = self.sources[idx]
            except ValueError:
                pass
        elif table_id == "inbox-table":
            for entry in self.inbox_entries:
                if str(entry.id) == key:
                    self.selected_inbox = entry
                    break
        elif table_id == "staging-table":
            for entry in self.staging_entries:
                if str(entry.id) == key:
                    self.selected_staging = entry
                    break

        self._update_detail_panel()

    async def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle Enter key on DataTable row - show actions."""
        await self.action_show_actions()

    # =========================================================================
    # Filter Overlay
    # =========================================================================

    def action_toggle_filter(self) -> None:
        """Toggle filter overlay."""
        overlay = self.query_one("#filter-overlay", Container)
        overlay.toggle_class("visible")
        if overlay.has_class("visible"):
            self.query_one("#filter-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle filter input submission."""
        if event.input.id == "filter-input":
            query = event.value.strip().lower()
            self._apply_filter(query)
            self.query_one("#filter-overlay", Container).remove_class("visible")

    def _apply_filter(self, query: str) -> None:
        """Apply filter to current tab's data."""
        if not query:
            self._load_all_data()
            self._refresh_current_table()
            self.show_left_notify("Filtre effacé", 1.5)
            return

        if self.current_tab == "sources":
            self.sources = [
                s for s in self.db.list_sources(limit=500)
                if query in s.domain.lower() or
                   query in (s.status or "").lower() or
                   any(query in tag.lower() for tag in self.source_tags.get(s.id, []))
            ]
            self._populate_sources_table()
        elif self.current_tab == "inbox":
            self.inbox_entries = [
                e for e in self.db.get_inbox_entries(limit=1000)
                if query in e.url.lower() or query in (e.domain or "").lower()
            ]
            self._populate_inbox_table()
        elif self.current_tab == "staging":
            self.staging_entries = [
                e for e in self.db.get_staging_entries(promoted=False, limit=1000)
                if query in (e.domain or "").lower() or query in (e.title or "").lower()
            ]
            self._populate_staging_table()

        self._update_stats()
        self.show_left_notify(f"Filtré: {len(self.entries)} résultats", 1.5)

    def _refresh_current_table(self) -> None:
        """Refresh the current tab's table."""
        if self.current_tab == "sources":
            self._populate_sources_table()
        elif self.current_tab == "inbox":
            self._populate_inbox_table()
        else:
            self._populate_staging_table()
        self._update_stats()

    # =========================================================================
    # Actions Overlay
    # =========================================================================

    async def action_show_actions(self) -> None:
        """Show actions overlay for current selection."""
        overlay = self.query_one("#actions-overlay", Container)
        actions_list = self.query_one("#actions-list", ListView)
        # Remove all children properly and await completion
        await actions_list.remove_children()

        # Build action list based on current tab
        if self.current_tab == "sources" and self.selected_source:
            actions_list.append(ListItem(Static("📋 View details"), id="action-view"))
            actions_list.append(ListItem(Static("🏷️  Edit tags"), id="action-tags"))
            actions_list.append(ListItem(Static("🔗 View backlinks"), id="action-backlinks"))
            actions_list.append(ListItem(Static("⬇️  Demote to staging"), id="action-demote"))
            actions_list.append(ListItem(Static("🗑️  Delete"), id="action-delete"))

        elif self.current_tab == "inbox" and self.selected_inbox:
            actions_list.append(ListItem(Static("✨ Enrich & promote"), id="action-enrich"))
            actions_list.append(ListItem(Static("⬆️  Quick promote (no enrich)"), id="action-promote-staging"))
            actions_list.append(ListItem(Static("📋 View details"), id="action-view"))
            actions_list.append(ListItem(Static("⚠️  Quarantine"), id="action-quarantine"))
            actions_list.append(ListItem(Static("🗑️  Delete"), id="action-delete"))

        elif self.current_tab == "staging" and self.selected_staging:
            actions_list.append(ListItem(Static("📋 View details"), id="action-view"))
            actions_list.append(ListItem(Static("⬆️  Promote to sources"), id="action-promote"))
            actions_list.append(ListItem(Static("🔄 Refresh score"), id="action-refresh-score"))
            actions_list.append(ListItem(Static("🗑️  Delete"), id="action-delete"))

        else:
            actions_list.append(ListItem(Static("[dim]No selection[/dim]")))

        overlay.add_class("visible")
        actions_list.focus()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle action selection."""
        action_id = event.item.id
        self.query_one("#actions-overlay", Container).remove_class("visible")

        if action_id == "action-view":
            self._action_view_details()
        elif action_id == "action-tags":
            self._action_edit_tags()
        elif action_id == "action-backlinks":
            self._action_view_backlinks()
        elif action_id == "action-demote":
            self._action_demote()
        elif action_id == "action-delete":
            self._action_delete()
        elif action_id == "action-enrich":
            self._action_enrich()
        elif action_id == "action-quarantine":
            self._action_quarantine()
        elif action_id == "action-promote-staging":
            self._action_promote_to_staging()
        elif action_id == "action-promote":
            self._action_promote()
        elif action_id == "action-refresh-score":
            self._action_refresh_score()

    # =========================================================================
    # Action Implementations
    # =========================================================================

    def _action_view_details(self) -> None:
        """View full details of selected item."""
        if self.current_tab == "sources" and self.selected_source:
            src = self.selected_source
            self.show_left_notify(f"URL: {src.url_pattern or src.domain}", 3.0)
        elif self.current_tab == "inbox" and self.selected_inbox:
            self.show_left_notify(f"URL: {self.selected_inbox.url}", 3.0)
        elif self.current_tab == "staging" and self.selected_staging:
            self.show_left_notify(f"URL: {self.selected_staging.url}", 3.0)

    def _action_edit_tags(self) -> None:
        """Edit tags for selected source."""
        if self.selected_source:
            self.result_action = ("tags", self.selected_source)
            self.exit()

    def _action_view_backlinks(self) -> None:
        """View entries citing the selected source."""
        if self.selected_source:
            count = self.db.count_source_backlinks(self.selected_source.id)
            self.show_left_notify(f"Backlinks: {count} entries", 2.0)

    def _action_demote(self) -> None:
        """Demote source back to staging."""
        if self.selected_source:
            from rekall.promotion import demote_source
            result = demote_source(self.db, self.selected_source.id)
            if result:
                self.sources.remove(self.selected_source)
                self._populate_sources_table()
                self._update_stats()
                self.show_left_notify("Source demoted", 2.0)
            else:
                self.show_left_notify("[red]Demote failed[/red]", 2.0)

    def _action_delete(self) -> None:
        """Delete selected item."""
        if self.current_tab == "sources" and self.selected_source:
            self.db.delete_source(self.selected_source.id)
            self.sources.remove(self.selected_source)
            self._populate_sources_table()
            self.show_left_notify("Source deleted", 2.0)
        elif self.current_tab == "inbox" and self.selected_inbox:
            self.db.delete_inbox_entry(self.selected_inbox.id)
            self.inbox_entries.remove(self.selected_inbox)
            self._populate_inbox_table()
            self.show_left_notify("Entry deleted", 2.0)
        elif self.current_tab == "staging" and self.selected_staging:
            self.db.delete_staging_entry(self.selected_staging.id)
            self.staging_entries.remove(self.selected_staging)
            self._populate_staging_table()
            self.show_left_notify("Entry deleted", 2.0)
        self._update_stats()

    def _action_enrich(self) -> None:
        """Open enrich overlay for inbox entry."""
        if self.selected_inbox:
            self._show_enrich_overlay(self.selected_inbox)

    def _show_enrich_overlay(self, entry) -> None:
        """Show the enrichment overlay with entry data."""
        overlay = self.query_one("#enrich-overlay", Container)

        # Populate fields - InboxEntry has no title, use domain
        self.query_one("#enrich-url", Static).update(
            f"[cyan]{entry.url}[/cyan]"
        )
        self.query_one("#enrich-input-title", Input).value = entry.domain or ""
        self.query_one("#enrich-input-tags", Input).value = ""

        # Set default type - InboxEntry has no content_type
        content_type = "other"
        type_map = {
            "documentation": "type-doc",
            "article": "type-article",
            "tutorial": "type-tutorial",
            "paper": "type-paper",
            "tool": "type-tool",
            "reference": "type-ref",
            "other": "type-other",
        }
        radio_id = type_map.get(content_type, "type-other")
        try:
            self.query_one(f"#{radio_id}", RadioButton).value = True
        except Exception:
            pass

        # Show overlay
        overlay.add_class("visible")
        self.query_one("#enrich-input-title", Input).focus()

    def _close_enrich_overlay(self) -> None:
        """Close the enrichment overlay."""
        self.query_one("#enrich-overlay", Container).remove_class("visible")

    def _submit_enrichment(self) -> None:
        """Submit the enrichment form."""
        if not self.selected_inbox:
            return

        from rekall.enrichment import merge_into_staging

        entry = self.selected_inbox
        title = self.query_one("#enrich-input-title", Input).value or entry.domain or entry.url[:50]

        # Get content type
        content_type = "other"
        type_set = self.query_one("#enrich-type", RadioSet)
        if type_set.pressed_button:
            content_type = type_set.pressed_button.label.plain

        # Create staging entry
        staging, is_new = merge_into_staging(
            self.db,
            entry,
            title=title,
            description=None,
            content_type=content_type,
            language=None,
            is_accessible=True,
            http_status=200,
        )

        # Mark inbox as enriched
        self.db.mark_inbox_enriched(entry.id)

        # Update UI
        self.inbox_entries.remove(self.selected_inbox)
        self._populate_inbox_table()
        self._load_all_data()
        self._populate_staging_table()
        self._update_stats()

        # Close overlay and notify
        self._close_enrich_overlay()
        action = "Created" if is_new else "Merged into"
        self.show_left_notify(f"[green]{action} staging![/green]", 2.0)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in overlays."""
        if event.button.id == "enrich-cancel":
            self._close_enrich_overlay()
        elif event.button.id == "enrich-submit":
            self._submit_enrichment()

    def _action_quarantine(self) -> None:
        """Move inbox entry to quarantine."""
        if self.selected_inbox:
            self.db.quarantine_inbox_entry(self.selected_inbox.id, "Manual quarantine")
            self.inbox_entries.remove(self.selected_inbox)
            self._populate_inbox_table()
            self._update_stats()
            self.show_left_notify("Entry quarantined", 2.0)

    def _action_promote_to_staging(self) -> None:
        """Promote inbox entry to staging (without enrichment)."""
        if self.selected_inbox:
            from rekall.enrichment import merge_into_staging
            entry = self.selected_inbox
            # Create staging entry with basic info (no enrichment)
            # InboxEntry has no title/content_type - use domain as title
            staging, is_new = merge_into_staging(
                self.db,
                entry,
                title=entry.domain or entry.url[:50],
                description=None,
                content_type="other",
                language=None,
                is_accessible=True,
                http_status=200,
            )
            # Mark inbox as enriched
            self.db.mark_inbox_enriched(entry.id)
            self.inbox_entries.remove(self.selected_inbox)
            self._populate_inbox_table()
            self._load_all_data()  # Refresh staging
            self._populate_staging_table()
            self._update_stats()
            action = "Created" if is_new else "Merged into"
            self.show_left_notify(f"[green]{action} staging![/green]", 2.0)

    def _action_promote(self) -> None:
        """Promote staging entry to sources."""
        if self.selected_staging:
            from rekall.promotion import promote_source
            result = promote_source(self.db, self.selected_staging.id)
            if result:
                self.staging_entries.remove(self.selected_staging)
                self._populate_staging_table()
                self._load_all_data()  # Refresh sources
                self._populate_sources_table()
                self._update_stats()
                self.show_left_notify("[green]Promoted![/green]", 2.0)
            else:
                self.show_left_notify("[red]Promotion failed[/red]", 2.0)

    def _action_refresh_score(self) -> None:
        """Refresh promotion score for staging entry."""
        if self.selected_staging:
            from rekall.promotion import calculate_promotion_score
            new_score = calculate_promotion_score(self.db, self.selected_staging)
            self.db.update_staging_score(self.selected_staging.id, new_score)
            self.selected_staging.promotion_score = new_score
            self._populate_staging_table()
            self.show_left_notify(f"Score: {new_score:.0f}", 2.0)

    # =========================================================================
    # Quick Actions (keyboard shortcuts)
    # =========================================================================

    def action_quick_edit(self) -> None:
        """Quick edit via 'e' key."""
        self._action_view_details()

    def action_quick_delete(self) -> None:
        """Quick delete via 'd' key."""
        self._action_delete()

    def action_quick_tags(self) -> None:
        """Quick tags via 't' key."""
        if self.current_tab == "sources":
            self._action_edit_tags()

    def action_quick_promote(self) -> None:
        """Quick promote via 'p' key."""
        if self.current_tab == "staging":
            self._action_promote()

    def action_refresh(self) -> None:
        """Refresh current tab data."""
        self._load_all_data()
        self._refresh_current_table()
        self.show_left_notify("Refreshed", 1.5)

    def action_close_or_quit(self) -> None:
        """Close overlays or quit."""
        filter_overlay = self.query_one("#filter-overlay", Container)
        actions_overlay = self.query_one("#actions-overlay", Container)
        enrich_overlay = self.query_one("#enrich-overlay", Container)

        if enrich_overlay.has_class("visible"):
            enrich_overlay.remove_class("visible")
        elif filter_overlay.has_class("visible"):
            filter_overlay.remove_class("visible")
        elif actions_overlay.has_class("visible"):
            actions_overlay.remove_class("visible")
        else:
            self.exit()

    # =========================================================================
    # Sorting (SortableTableMixin implementation)
    # =========================================================================

    def get_sort_key(self, column_key: str):
        """Get sort key for current tab."""
        if self.current_tab == "sources":
            key_map = {
                "domain": lambda s: s.domain.lower(),
                "score": lambda s: s.personal_score,
                "status": lambda s: s.status or "",
                "role": lambda s: s.role or "",
                "reliability": lambda s: s.reliability or "",
                "usages": lambda s: s.usage_count,
                "tags": lambda s: ",".join(self.source_tags.get(s.id, [])),
            }
        elif self.current_tab == "inbox":
            key_map = {
                "url": lambda e: e.url.lower(),
                "domain": lambda e: (e.domain or "").lower(),
                "project": lambda e: (e.project or "").lower(),
                "status": lambda e: 0 if not e.is_valid else (1 if e.enriched_at else 2),
                "captured": lambda e: e.captured_at,
            }
        else:  # staging
            key_map = {
                "domain": lambda e: (e.domain or "").lower(),
                "title": lambda e: (e.title or "").lower(),
                "type": lambda e: e.content_type or "",
                "citations": lambda e: e.citation_count,
                "score": lambda e: e.promotion_score or 0,
                "indicator": lambda e: e.promotion_score or 0,
            }
        return key_map.get(column_key, lambda x: "")

    def refresh_table(self) -> None:
        """Refresh current table with sort state."""
        self._refresh_current_table()

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Handle column sort click."""
        column_key = event.column_key.value

        if self.sort_column == column_key:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column_key
            self.sort_reverse = False

        self.sort_entries()
        self._refresh_current_table()

        direction = "▼" if self.sort_reverse else "▲"
        self.show_left_notify(f"Sorted by {column_key} {direction}", 1.5)

    # =========================================================================
    # Notification
    # =========================================================================

    def show_left_notify(self, message: str, timeout: float = 2.0) -> None:
        """Show notification toast."""
        notify = self.query_one("#left-notify", Static)
        notify.update(message)
        notify.add_class("visible")
        self.set_timer(timeout, lambda: notify.remove_class("visible"))


def run_unified_sources(db) -> str | None:
    """Run the Unified Sources Manager.

    Args:
        db: Database instance

    Returns:
        Action tuple or None
    """
    app = UnifiedSourcesApp(db)
    app.run()
    return app.result_action


# =============================================================================
# Main TUI Loop
# =============================================================================


# Map action keys to functions
ACTION_MAP = {
    "language": None,  # Will be set to action_language
    "config": None,    # Unified config & maintenance
    "research": None,
    "search": None,
    "browse": None,
    "show": None,
    "export": None,
    "quit": None,
}


def get_menu_items():
    """Build menu items for RekallMenuApp."""
    return [
        # Section 1: Général
        ("__section__", "GÉNÉRAL", ""),
        ("language", t("menu.language"), t("menu.language.desc")),
        ("config", t("menu.config"), t("menu.config.desc")),
        ("__spacer__", "", ""),
        # Section 2: Base de connaissances (Feature 011)
        ("__section__", t("menu.knowledge_base"), ""),
        ("browse", t("menu.browse"), t("menu.browse.desc")),
        ("sources", t("menu.sources"), t("menu.sources.desc")),
        ("__spacer__", "", ""),
        # Section 3: Données
        ("__section__", "DONNÉES", ""),
        ("export", t("menu.export"), t("menu.export.desc")),
        ("__spacer__", "", ""),
        # Section 4: Quitter
        ("quit", t("menu.quit"), t("menu.quit.desc")),
    ]


# =============================================================================
# ConfigApp - Multi-IDE Configuration Screen (Feature 019)
# =============================================================================


class ConfigApp(App):
    """Textual app for IDE integrations configuration.

    Two sections:
    1. INTÉGRATIONS - All supported IDEs with Global/Local columns
    2. SPECKIT - Article 99 selection (visible if ~/.speckit/ exists)
    """

    CSS = """
    Screen {
        background: $surface;
    }

    #main-container {
        height: 1fr;
        padding: 0 2;
    }

    #detected-ide-header {
        height: auto;
        margin-bottom: 1;
        padding: 0 1;
        color: $success;
    }

    #integrations-section {
        height: auto;
        min-height: 10;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }

    #integrations-title {
        text-style: bold;
        color: $primary;
        margin-bottom: 1;
    }

    #column-headers {
        height: 1;
        margin-bottom: 1;
        color: $text-muted;
    }

    .ide-row {
        height: 1;
        padding: 0 1;
    }

    .ide-row:hover {
        background: $surface-lighten-1;
    }

    .ide-row.selected {
        background: $primary-darken-2;
    }

    .ide-name {
        width: 20;
    }

    .global-toggle {
        width: 12;
        text-align: center;
    }

    .local-toggle {
        width: 12;
        text-align: center;
    }

    .global-toggle.disabled {
        color: $text-muted;
    }

    #speckit-section {
        height: auto;
        min-height: 8;
        border: solid $secondary;
        padding: 1;
        display: none;
    }

    #speckit-section.visible {
        display: block;
    }

    #speckit-title {
        text-style: bold;
        color: $secondary;
        margin-bottom: 1;
    }

    #article99-selector {
        height: auto;
        padding: 0 1;
    }

    .article99-option {
        height: 1;
        padding: 0 1;
    }

    .article99-option.selected {
        background: $secondary-darken-2;
    }

    .article99-option .recommended {
        color: $warning;
    }

    #footer-hint {
        dock: bottom;
        height: 1;
        padding: 0 2;
        color: $text-muted;
    }

    #notification {
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

    #notification.visible {
        display: block;
    }
    """ + BANNER_CSS

    BINDINGS = [
        Binding("escape", "quit", "Quitter", show=True),
        Binding("q", "quit", "Quitter", show=False),
        Binding("up", "move_up", "↑", show=True),
        Binding("down", "move_down", "↓", show=True),
        Binding("space", "toggle", "Toggle", show=True),
        Binding("g", "install_global", "Global", show=True),
        Binding("l", "install_local", "Local", show=True),
        Binding("r", "remove", "Désinstaller", show=True),
        Binding("tab", "switch_section", "Section", show=True),
    ]

    def __init__(self, base_path: Path | None = None):
        super().__init__()
        self.base_path = base_path or Path.cwd()
        self._selected_ide_idx = 0
        self._selected_article99_idx = 0
        self._active_section = "integrations"  # or "speckit"
        self._notification_timer = None

        # Load data
        from rekall.integrations import (
            SUPPORTED_IDES,
            detect_ide,
            get_article99_recommendation,
            Article99Version,
        )
        self._ides = SUPPORTED_IDES
        self._detected = detect_ide(self.base_path)
        self._article99_versions = list(Article99Version)
        self._article99_recommendation = get_article99_recommendation(self.base_path)
        self._speckit_exists = (Path.home() / ".speckit").exists()

    def compose(self) -> ComposeResult:
        yield create_banner_container()

        with Container(id="main-container"):
            # Detected IDE header
            yield Static(self._build_detected_header(), id="detected-ide-header", markup=True)

            # Section 1: INTÉGRATIONS
            with Container(id="integrations-section"):
                yield Static("[bold]INTÉGRATIONS[/bold]", id="integrations-title")
                yield Static(self._build_column_headers(), id="column-headers", markup=True)
                yield Static(self._build_ide_list(), id="ide-list", markup=True)

            # Section 2: SPECKIT (conditional)
            with Container(id="speckit-section", classes="visible" if self._speckit_exists else ""):
                yield Static("[bold]SPECKIT[/bold]", id="speckit-title")
                yield Static(self._build_article99_selector(), id="article99-selector", markup=True)

        yield Static(
            "[dim]↑↓ naviguer • g global • l local • r désinstaller • Tab section • Esc quitter[/dim]",
            id="footer-hint"
        )
        yield Static("", id="notification")

    def _build_detected_header(self) -> str:
        """Build the detected IDE header."""
        if self._detected.ide:
            scope_str = "global" if self._detected.scope and self._detected.scope.value == "global" else "local"
            return f"[green]► IDE détecté: {self._detected.ide.name} ({scope_str})[/green]"
        return "[dim]Aucun IDE détecté[/dim]"

    def _build_column_headers(self) -> str:
        """Build column headers for IDE list."""
        return f"{'IDE':<20} {'Global':^12} {'Local':^12}"

    def _build_ide_list(self) -> str:
        """Build the IDE list with Global/Local columns."""
        from rekall.integrations import get_ide_status

        lines = []
        for idx, ide in enumerate(self._ides):
            # Check if this is the detected IDE
            is_detected = self._detected.ide and self._detected.ide.id == ide.id
            marker = "►" if is_detected else " "

            # Selection highlight
            selected = idx == self._selected_ide_idx and self._active_section == "integrations"
            prefix = "[reverse]" if selected else ""
            suffix = "[/reverse]" if selected else ""

            # Get installation status
            try:
                status = get_ide_status(ide.id, self.base_path)
                global_status = "✓" if status.get("global_installed") else "-"
                local_status = "✓" if status.get("local_installed") else "-"
            except Exception:
                global_status = "-"
                local_status = "-"

            # Global column (disabled if not supported)
            if ide.global_marker:
                global_col = f"{global_status:^12}"
            else:
                global_col = f"[dim]{'n/a':^12}[/dim]"

            local_col = f"{local_status:^12}"

            line = f"{prefix}{marker} {ide.name:<18} {global_col} {local_col}{suffix}"
            lines.append(line)

        return "\n".join(lines)

    def _build_article99_selector(self) -> str:
        """Build Article 99 version selector."""
        from rekall.integrations import Article99Version

        version_labels = {
            Article99Version.MICRO: ("Micro", "~50 tokens"),
            Article99Version.SHORT: ("Court", "~350 tokens"),
            Article99Version.EXTENSIVE: ("Extensif", "~1000 tokens"),
        }

        lines = []
        for idx, version in enumerate(self._article99_versions):
            label, tokens = version_labels[version]

            # Check if recommended
            is_recommended = version == self._article99_recommendation.recommended
            rec_marker = "★ recommandé" if is_recommended else ""

            # Selection highlight
            selected = idx == self._selected_article99_idx and self._active_section == "speckit"
            prefix = "[reverse]" if selected else ""
            suffix = "[/reverse]" if selected else ""

            # Radio button style
            checked = "◉" if idx == self._selected_article99_idx else "○"

            line = f"{prefix}{checked} {label} ({tokens}) {rec_marker}{suffix}"
            lines.append(line)

        # Add recommendation reason
        if self._article99_recommendation.reason:
            lines.append("")
            lines.append(f"[dim]{self._article99_recommendation.reason}[/dim]")

        return "\n".join(lines)

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()

    def action_move_up(self) -> None:
        """Move selection up."""
        if self._active_section == "integrations":
            self._selected_ide_idx = max(0, self._selected_ide_idx - 1)
            self._refresh_ide_list()
        else:
            self._selected_article99_idx = max(0, self._selected_article99_idx - 1)
            self._refresh_article99()

    def action_move_down(self) -> None:
        """Move selection down."""
        if self._active_section == "integrations":
            self._selected_ide_idx = min(len(self._ides) - 1, self._selected_ide_idx + 1)
            self._refresh_ide_list()
        else:
            self._selected_article99_idx = min(len(self._article99_versions) - 1, self._selected_article99_idx + 1)
            self._refresh_article99()

    def action_switch_section(self) -> None:
        """Switch between sections."""
        if not self._speckit_exists:
            return  # Can't switch if speckit doesn't exist

        if self._active_section == "integrations":
            self._active_section = "speckit"
        else:
            self._active_section = "integrations"

        self._refresh_ide_list()
        self._refresh_article99()

    def action_toggle(self) -> None:
        """Toggle current selection."""
        if self._active_section == "integrations":
            # Toggle would be handled by install/remove
            pass
        else:
            # Article 99 selection is already handled by navigation
            pass

    def action_install_global(self) -> None:
        """Install selected integration globally."""
        if self._active_section == "integrations":
            self._install_ide(global_install=True)
        else:
            self._install_article99()

    def action_install_local(self) -> None:
        """Install selected integration locally."""
        if self._active_section == "integrations":
            self._install_ide(global_install=False)
        else:
            self._install_article99()

    def action_remove(self) -> None:
        """Remove selected integration."""
        if self._active_section == "integrations":
            self._uninstall_ide()

    def _install_ide(self, global_install: bool = True) -> None:
        """Install the selected IDE integration.

        Args:
            global_install: If True, install globally; if False, install locally
        """
        from rekall.integrations import install

        ide = self._ides[self._selected_ide_idx]

        # Check if global is supported
        if global_install and not ide.global_marker:
            self._show_notification(f"✗ {ide.name} ne supporte pas l'installation globale")
            return

        try:
            install(ide.id, self.base_path, global_install=global_install)

            scope = "global" if global_install else "local"
            self._show_notification(f"✓ {ide.name} installé ({scope})")
            self._refresh_ide_list()
        except Exception as e:
            self._show_notification(f"✗ Erreur: {e}")

    def _uninstall_ide(self) -> None:
        """Uninstall the selected IDE integration."""
        from rekall.integrations import uninstall_ide

        ide = self._ides[self._selected_ide_idx]

        try:
            uninstall_ide(ide.id, self.base_path)
            self._show_notification(f"✓ {ide.name} désinstallé")
            self._refresh_ide_list()
        except Exception as e:
            self._show_notification(f"✗ Erreur: {e}")

    def _install_article99(self) -> None:
        """Install selected Article 99 version."""
        from rekall.integrations import install_article99

        version = self._article99_versions[self._selected_article99_idx]

        try:
            success = install_article99(version)
            if success:
                self._show_notification(f"✓ Article 99 ({version.value}) installé")
            else:
                self._show_notification("✗ ~/.speckit/ n'existe pas")
        except Exception as e:
            self._show_notification(f"✗ Erreur: {e}")

    def _refresh_ide_list(self) -> None:
        """Refresh the IDE list display."""
        try:
            ide_list = self.query_one("#ide-list", Static)
            ide_list.update(self._build_ide_list())
        except Exception:
            pass

    def _refresh_article99(self) -> None:
        """Refresh the Article 99 selector display."""
        try:
            selector = self.query_one("#article99-selector", Static)
            selector.update(self._build_article99_selector())
        except Exception:
            pass

    def _show_notification(self, message: str) -> None:
        """Show a notification message."""
        try:
            notif = self.query_one("#notification", Static)
            notif.update(message)
            notif.add_class("visible")

            # Auto-hide after 2 seconds
            if self._notification_timer:
                self._notification_timer.stop()

            self._notification_timer = self.set_timer(2.0, self._hide_notification)
        except Exception:
            pass

    def _hide_notification(self) -> None:
        """Hide the notification."""
        try:
            notif = self.query_one("#notification", Static)
            notif.remove_class("visible")
        except Exception:
            pass


def run_config_app(base_path: Path | None = None) -> None:
    """Run the ConfigApp TUI."""
    app = ConfigApp(base_path)
    app.run()


def run_tui():
    """Run the interactive TUI using Textual."""
    # Load saved language preference
    load_lang_preference()

    # Check for pending migrations at startup (Feature 007)
    migration_result = run_migration_overlay()
    if migration_result == "migrate":
        if apply_migration_from_tui():
            show_info("[green]✓ Migration réussie ![/green]")
        else:
            show_info("[red]✗ Échec de la migration. Vérifiez les logs.[/red]")

    # Action for unified ConfigApp
    def action_config():
        """Launch the unified ConfigApp for IDE integrations."""
        run_config_app(Path.cwd())

    # Map action keys to functions
    actions = {
        "language": action_language,
        "config": action_config,  # New unified ConfigApp (Feature 019)
        "research": action_research,
        "browse": action_browse,
        "sources": action_sources,  # Feature 009 - Sources Dashboard
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

        if result is None or result in {"__quit__", "quit"}:
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
