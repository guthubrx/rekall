# Contract: TUI Module Structure

**Feature**: 017-code-modularization
**Component**: rekall/ui/
**Date**: 2025-12-12

## Overview

Réorganisation de `tui.py` (7872 LOC, 14 classes + 100+ handlers) en screens et widgets Textual.

## Target Structure

```
rekall/ui/
├── __init__.py              # run_tui() + exports (~50 LOC)
├── app.py                   # RekallMenuApp principal (~400 LOC)
├── theme.py                 # BANNER, CSS, couleurs (~200 LOC)
├── helpers.py               # get_db, prompts, formatters (~250 LOC)
├── screens/
│   ├── __init__.py          # Exports screens (~20 LOC)
│   ├── main.py              # Écran principal menu (~300 LOC)
│   ├── browse.py            # BrowseApp, navigation (~500 LOC)
│   ├── research.py          # ResearchApp (~300 LOC)
│   ├── sources.py           # SourcesBrowseApp (~400 LOC)
│   ├── inbox.py             # InboxBrowseApp (~300 LOC)
│   ├── staging.py           # StagingBrowseApp (~300 LOC)
│   └── config.py            # MCPConfigApp, settings (~300 LOC)
└── widgets/
    ├── __init__.py          # Exports widgets (~20 LOC)
    ├── menu.py              # MenuItem, MenuListView (~200 LOC)
    ├── detail_panel.py      # EntryDetailPanel (~200 LOC)
    ├── search_bar.py        # SearchBar widget (~150 LOC)
    ├── toast.py             # ToastWidget, notifications (~100 LOC)
    └── overlays.py          # MigrationOverlay, etc. (~200 LOC)
```

**Total estimé**: ~3,900 LOC (vs 7,872 actuel - réduction via helpers et widgets partagés)

## Module Contracts

### __init__.py

```python
"""
TUI Rekall - Interface Textual.

Usage:
    from rekall.ui import run_tui
    run_tui()
"""

from rekall.ui.app import run_tui, RekallMenuApp
from rekall.ui.screens.browse import BrowseApp
from rekall.ui.screens.research import ResearchApp
from rekall.ui.screens.sources import SourcesBrowseApp
from rekall.ui.screens.inbox import InboxBrowseApp
from rekall.ui.screens.staging import StagingBrowseApp
from rekall.ui.screens.config import MCPConfigApp
from rekall.ui.widgets.menu import MenuItem, MenuListView
from rekall.ui.widgets.detail_panel import EntryDetailPanel
from rekall.ui.widgets.search_bar import SearchBar
from rekall.ui.widgets.toast import show_toast, ToastWidget
from rekall.ui.theme import BANNER, REKALL_CSS

__all__ = [
    "run_tui",
    "RekallMenuApp",
    "BrowseApp",
    "ResearchApp",
    "SourcesBrowseApp",
    "InboxBrowseApp",
    "StagingBrowseApp",
    "MCPConfigApp",
    "MenuItem",
    "MenuListView",
    "EntryDetailPanel",
    "SearchBar",
    "show_toast",
    "ToastWidget",
    "BANNER",
    "REKALL_CSS",
]
```

### app.py

```python
"""Application principale Rekall TUI."""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from rekall.ui.screens.main import MainScreen
from rekall.ui.theme import REKALL_CSS

__all__ = ["run_tui", "RekallMenuApp"]

class RekallMenuApp(App):
    """Application principale avec menu."""

    CSS = REKALL_CSS
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
        ("s", "search", "Search"),
        ("b", "browse", "Browse"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield MainScreen()
        yield Footer()

    def action_search(self) -> None:
        from rekall.ui.screens.research import ResearchApp
        self.push_screen(ResearchApp())

    def action_browse(self) -> None:
        from rekall.ui.screens.browse import BrowseApp
        self.push_screen(BrowseApp())


def run_tui() -> None:
    """Lance l'interface TUI."""
    app = RekallMenuApp()
    app.run()
```

### theme.py

```python
"""Thème et styles CSS pour le TUI."""

__all__ = ["BANNER", "REKALL_CSS", "COLORS"]

BANNER = r"""
██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗
██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║
██████╔╝█████╗  █████╔╝ ███████║██║     ██║
██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║
██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗
╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝
"""

COLORS = {
    "primary": "#7c3aed",    # violet
    "secondary": "#10b981",  # vert
    "warning": "#f59e0b",    # orange
    "error": "#ef4444",      # rouge
    "muted": "#6b7280",      # gris
}

REKALL_CSS = """
Screen {
    background: $surface;
}

Header {
    background: $primary;
}

#menu-list {
    width: 100%;
    height: auto;
}

.selected {
    background: $primary 30%;
}

EntryDetailPanel {
    border: round $primary;
    padding: 1;
}

SearchBar {
    dock: top;
    height: 3;
}
"""
```

### screens/browse.py

```python
"""Écran de navigation des entrées."""

from textual.app import App, ComposeResult
from textual.widgets import DataTable, Footer
from textual.screen import Screen
from rekall.ui.widgets.detail_panel import EntryDetailPanel
from rekall.ui.widgets.search_bar import SearchBar
from rekall.ui.helpers import get_db

__all__ = ["BrowseApp", "BrowseScreen"]

class BrowseScreen(Screen):
    """Écran de navigation."""

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("/", "search", "Search"),
        ("enter", "select", "View"),
        ("e", "edit", "Edit"),
        ("d", "delete", "Delete"),
    ]

    def compose(self) -> ComposeResult:
        yield SearchBar()
        yield DataTable(id="entries-table")
        yield EntryDetailPanel(id="detail-panel")
        yield Footer()

    def on_mount(self) -> None:
        self._load_entries()

    def _load_entries(self, query: str | None = None) -> None:
        db = get_db()
        if query:
            entries = db.entries.search(query)
        else:
            entries = db.entries.list_all(limit=100)
        self._populate_table(entries)

    def _populate_table(self, entries: list) -> None:
        table = self.query_one("#entries-table", DataTable)
        table.clear()
        table.add_columns("ID", "Title", "Tags", "Updated")
        for entry in entries:
            table.add_row(entry.id, entry.title, ", ".join(entry.tags), entry.updated_at)


class BrowseApp(App):
    """Application standalone de navigation."""

    def compose(self) -> ComposeResult:
        yield BrowseScreen()
```

### widgets/menu.py

```python
"""Widgets de menu réutilisables."""

from textual.widgets import ListItem, ListView
from textual.message import Message
from dataclasses import dataclass

__all__ = ["MenuItem", "MenuListView"]

@dataclass
class MenuItem:
    """Item de menu."""
    label: str
    action: str
    shortcut: str | None = None
    description: str | None = None


class MenuListView(ListView):
    """ListView spécialisé pour les menus."""

    class Selected(Message):
        """Message émis quand un item est sélectionné."""
        def __init__(self, item: MenuItem):
            self.item = item
            super().__init__()

    def __init__(self, items: list[MenuItem], **kwargs):
        super().__init__(**kwargs)
        self.menu_items = items

    def compose(self):
        for item in self.menu_items:
            yield ListItem(self._render_item(item))

    def _render_item(self, item: MenuItem) -> str:
        shortcut = f"[{item.shortcut}] " if item.shortcut else ""
        return f"{shortcut}{item.label}"

    def action_select_cursor(self) -> None:
        if self.highlighted is not None:
            item = self.menu_items[self.highlighted]
            self.post_message(self.Selected(item))
```

### widgets/detail_panel.py

```python
"""Panneau de détails d'une entrée."""

from textual.widgets import Static
from textual.reactive import reactive
from rekall.models import Entry

__all__ = ["EntryDetailPanel"]

class EntryDetailPanel(Static):
    """Affiche les détails d'une entrée."""

    entry: Entry | None = reactive(None)

    def watch_entry(self, entry: Entry | None) -> None:
        if entry is None:
            self.update("No entry selected")
        else:
            self.update(self._render_entry(entry))

    def _render_entry(self, entry: Entry) -> str:
        lines = [
            f"[bold]{entry.title}[/bold]",
            "",
            f"[dim]ID:[/dim] {entry.id}",
            f"[dim]URL:[/dim] {entry.url or 'N/A'}",
            f"[dim]Tags:[/dim] {', '.join(entry.tags) or 'None'}",
            "",
            entry.content[:500] if entry.content else "[dim]No content[/dim]",
        ]
        return "\n".join(lines)
```

## Class Mapping

| Classe actuelle | Fichier cible | Nouvelle classe |
|-----------------|---------------|-----------------|
| `RekallMenuApp` | app.py | `RekallMenuApp` |
| `SimpleMenuApp` | screens/main.py | `MainMenuScreen` |
| `BrowseApp` | screens/browse.py | `BrowseApp` |
| `ResearchApp` | screens/research.py | `ResearchApp` |
| `SourcesBrowseApp` | screens/sources.py | `SourcesBrowseApp` |
| `InboxBrowseApp` | screens/inbox.py | `InboxBrowseApp` |
| `StagingBrowseApp` | screens/staging.py | `StagingBrowseApp` |
| `MCPConfigApp` | screens/config.py | `MCPConfigApp` |
| `MenuItem` | widgets/menu.py | `MenuItem` |
| `MenuListView` | widgets/menu.py | `MenuListView` |
| `ToastApp` | widgets/toast.py | `ToastWidget` |
| `MigrationOverlayApp` | widgets/overlays.py | `MigrationOverlay` |

## Validation Criteria

- [ ] `from rekall.tui import run_tui` fonctionne (façade)
- [ ] `rekall browse` lance le TUI correctement
- [ ] Tous les raccourcis clavier fonctionnent
- [ ] `pytest tests/test_tui.py` passe
- [ ] Widgets réutilisables dans différents screens
- [ ] Aucun fichier > 500 LOC
- [ ] `ruff check rekall/ui/` sans erreur
