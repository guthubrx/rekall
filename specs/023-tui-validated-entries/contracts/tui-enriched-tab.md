# Contract: TUI Enriched Tab Interface

**Date**: 2025-12-13
**Feature**: 023-tui-validated-entries

## Overview

Ce contrat definit l'interface du nouvel onglet "Enrichies" dans la TUI UnifiedSourcesApp.

## Components

### 1. Tab Definition

```python
# Dans UnifiedSourcesApp.compose()
with TabbedContent(id="tabs"):
    with TabPane("Sources (0)", id="tab-sources"):
        yield DataTable(id="sources-table", classes="sources-table")
    with TabPane("Enrichies (0)", id="tab-enriched"):  # NOUVEAU
        yield DataTable(id="enriched-table", classes="sources-table")
    with TabPane("Inbox (0)", id="tab-inbox"):
        yield DataTable(id="inbox-table", classes="sources-table")
    with TabPane("Staging (0)", id="tab-staging"):
        yield DataTable(id="staging-table", classes="sources-table")
```

### 2. Keyboard Bindings

```python
BINDINGS = [
    # Navigation onglets
    Binding("s", "tab_sources", "Sources", show=True),
    Binding("n", "tab_enriched", "Enrichies", show=True),  # NOUVEAU
    Binding("i", "tab_inbox", "Inbox", show=True),
    Binding("g", "tab_staging", "Staging", show=True),

    # Actions globales (existantes)
    Binding("escape", "close_or_quit", "Back", show=True),
    Binding("q", "quit", "Quit", show=True),
    Binding("f", "toggle_filter", "Filter", show=True),
    Binding("r", "refresh", "Refresh", show=True),
    Binding("/", "search", "Search", show=False),
    Binding("enter", "show_actions", "Actions", show=True),

    # Quick actions existantes
    Binding("e", "quick_edit", "Edit", show=False),
    Binding("d", "quick_delete", "Delete", show=False),
    Binding("t", "quick_tags", "Tags", show=False),
    Binding("p", "quick_promote", "Promote", show=False),

    # Quick actions NOUVELLES pour Enrichies
    Binding("v", "quick_validate", "Validate", show=False),  # NOUVEAU
]
```

### 3. Table Columns

```python
def _setup_enriched_table(self) -> None:
    """Configure les colonnes de la table Enrichies."""
    table = self.query_one("#enriched-table", DataTable)
    table.cursor_type = "row"
    table.zebra_stripes = True

    # Colonnes
    table.add_column("Domain", width=22, key="domain")
    table.add_column("Type", width=12, key="ai_type")
    table.add_column("Conf.", width=6, key="confidence")
    table.add_column("Status", width=10, key="status")
    table.add_column("Tags", width=25, key="tags")
    table.add_column("Validated", width=12, key="validated_at")
```

### 4. Row Formatting

```python
def _format_enriched_row(self, source: Source) -> tuple:
    """Formate une ligne pour la table Enrichies."""

    # Confidence avec couleur
    conf_pct = int(source.ai_confidence * 100) if source.ai_confidence else 0
    if conf_pct >= 90:
        conf_display = f"[green]{conf_pct}%[/green]"
    elif conf_pct >= 70:
        conf_display = f"[yellow]{conf_pct}%[/yellow]"
    else:
        conf_display = f"[red]{conf_pct}%[/red]"

    # Status avec icone
    if source.enrichment_status == "proposed":
        status_display = "[orange1]⏳ proposed[/orange1]"
    else:  # validated
        status_display = "[green]✓ validated[/green]"

    # Tags tronques
    tags = source.ai_tags[:3] if source.ai_tags else []
    extra = len(source.ai_tags) - 3 if source.ai_tags and len(source.ai_tags) > 3 else 0
    tags_display = ", ".join(tags)
    if extra > 0:
        tags_display += f" +{extra}"

    # Date validation
    validated = source.enrichment_validated_at[:10] if source.enrichment_validated_at else "-"

    return (
        source.domain,
        source.ai_type or "-",
        conf_display,
        status_display,
        tags_display,
        validated,
    )
```

### 5. Detail Panel Content

```python
def _update_enriched_detail(self, source: Source) -> None:
    """Met a jour le panneau de detail pour une source enrichie."""

    title_widget = self.query_one("#detail-title", Static)
    meta_widget = self.query_one("#detail-meta", Static)

    # Titre
    title_widget.update(f"[bold]{source.domain}[/bold]")

    # Metadonnees
    lines = [
        f"[cyan]ID:[/cyan] {source.id[:8]}...",
        f"[cyan]Type:[/cyan] {source.ai_type or 'N/A'}",
        f"[cyan]Confidence:[/cyan] {int(source.ai_confidence * 100)}%",
        f"[cyan]Status:[/cyan] {source.enrichment_status}",
        "",
        f"[cyan]Tags:[/cyan]",
    ]

    if source.ai_tags:
        for tag in source.ai_tags:
            lines.append(f"  • {tag}")
    else:
        lines.append("  (aucun)")

    lines.extend([
        "",
        f"[cyan]Summary:[/cyan]",
        source.ai_summary or "(aucun)",
    ])

    meta_widget.update("\n".join(lines))
```

### 6. Actions Menu

```python
def _get_enriched_actions(self) -> list[tuple[str, str, str]]:
    """Retourne les actions disponibles pour l'onglet Enrichies."""
    source = self.selected_enriched
    actions = [
        ("view", "📋 View full details", "View source details"),
    ]

    if source.enrichment_status == "proposed":
        actions.extend([
            ("validate", "✓ Validate enrichment", "Accept AI enrichment"),
            ("reject", "✗ Reject enrichment", "Reset to none"),
            ("modify", "✏️ Modify enrichment", "Edit before validating"),
        ])

    actions.extend([
        ("tags", "🏷️ Edit tags", "Manage source tags"),
        ("backlinks", "🔗 View backlinks", "Show linked entries"),
    ])

    return actions
```

## Data Interface

### DB Methods Required

```python
class RekallDB:
    def get_enriched_sources(
        self,
        status: str | None = None,  # 'proposed' | 'validated' | None (both)
        limit: int = 500,
    ) -> list[Source]:
        """Recupere les sources avec enrichissement IA."""
        ...

    def validate_enrichment(self, source_id: str) -> bool:
        """Valide une source proposed -> validated."""
        ...

    def reject_enrichment(self, source_id: str) -> bool:
        """Rejette une source proposed -> none."""
        ...

    def count_enriched_sources(self) -> dict:
        """Retourne {'total': N, 'proposed': N, 'validated': N}."""
        ...
```

## Events Flow

```
User presse 'n'
      │
      ▼
action_tab_enriched()
      │
      ▼
_switch_to_tab("enriched")
      │
      ├─► current_tab = "enriched"
      ├─► entries = enriched_entries
      ├─► tabs.active = "tab-enriched"
      └─► _update_detail_panel()

User selectionne ligne
      │
      ▼
on_data_table_row_highlighted()
      │
      ▼
selected_enriched = enriched_entries[idx]
      │
      ▼
_update_detail_panel()

User presse 'v' (sur proposed)
      │
      ▼
action_quick_validate()
      │
      ▼
db.validate_enrichment(source_id)
      │
      ├─► Refresh enriched_entries
      ├─► _populate_enriched_table()
      └─► show_left_notify("✓ Enrichment validated")
```

## Styling

```css
/* Pas de nouveau CSS necessaire */
/* Reutilise les styles .sources-table existants */

#enriched-table {
    /* Herite de .sources-table */
}

/* Les indicateurs de status utilisent Rich markup inline */
/* [green]✓[/green], [orange1]⏳[/orange1] */
```

## Empty State

```python
def _show_enriched_empty_state(self) -> None:
    """Affiche message si aucune source enrichie."""
    table = self.query_one("#enriched-table", DataTable)
    table.clear()

    # Message dans le panneau de detail
    title_widget = self.query_one("#detail-title", Static)
    meta_widget = self.query_one("#detail-meta", Static)

    title_widget.update("[dim]Aucune source enrichie[/dim]")
    meta_widget.update(
        "[dim]Utilisez rekall_enrich_source pour enrichir\n"
        "des sources avec des metadonnees IA.[/dim]"
    )
```

## Testing Contract

```python
# Tests d'acceptance
def test_enriched_tab_visible():
    """L'onglet Enrichies est visible dans la TUI."""
    ...

def test_enriched_keyboard_navigation():
    """Le raccourci 'n' active l'onglet Enrichies."""
    ...

def test_enriched_shows_proposed_first():
    """Les entrees proposed apparaissent avant validated."""
    ...

def test_validate_action():
    """L'action validate change le status proposed -> validated."""
    ...

def test_reject_action():
    """L'action reject remet le status a none."""
    ...

def test_enriched_detail_panel():
    """Le panneau de detail affiche ai_summary et ai_tags."""
    ...
```
