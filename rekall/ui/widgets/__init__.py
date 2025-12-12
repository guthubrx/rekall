# rekall/ui/widgets/__init__.py
"""
TUI widgets package.

This package contains reusable Textual widgets for the Rekall TUI.

Current State (Facade Pattern):
    All widgets currently live in tui_main.py. This package provides
    the module structure for future extraction.

Widgets:
    - menu.py: MenuItem, MenuListView
    - detail_panel.py: EntryDetailPanel
    - search_bar.py: SearchBar
    - toast.py: ToastApp
    - overlays.py: DeleteConfirmOverlay, MigrationOverlayApp
"""

from __future__ import annotations

__all__: list[str] = []
