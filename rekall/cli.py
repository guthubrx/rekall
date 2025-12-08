"""Rekall CLI - Developer Knowledge Management System."""

from __future__ import annotations

import platform
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from rekall import __version__
from rekall.config import Config, get_config, set_config
from rekall.db import Database
from rekall.models import Entry, VALID_TYPES, generate_ulid

console = Console()

# ASCII Banner - REKALL (Total Recall reference)
BANNER = """\
[bold cyan]        ██████╗ ███████╗██╗  ██╗ █████╗ ██╗     ██╗
        ██╔══██╗██╔════╝██║ ██╔╝██╔══██╗██║     ██║
        ██████╔╝█████╗  █████╔╝ ███████║██║     ██║
        ██╔══██╗██╔══╝  ██╔═██╗ ██╔══██║██║     ██║
        ██║  ██║███████╗██║  ██╗██║  ██║███████╗███████╗
        ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚══════╝[/bold cyan]

[bold white]            Developer Knowledge Management System[/bold white]
[dim]        "Get your ass to Mars. Quaid... crush those bugs"[/dim]
"""


def show_banner():
    """Display the REKALL banner."""
    console.print(BANNER)


# Create Typer app with Rich markup
app = typer.Typer(
    name="rekall",
    help="Capture and retrieve bugs, patterns, and decisions.",
    add_completion=False,
    rich_markup_mode="rich",
    pretty_exceptions_show_locals=False,
)

# Database instance (lazy loaded)
_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create database connection."""
    global _db
    if _db is None:
        config = get_config()
        _db = Database(config.db_path)
        _db.init()
    return _db


# Global CLI options stored in context
_cli_global: bool = False
_cli_legacy: bool = False


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    use_global: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Force global configuration (ignore local .rekall/)",
    ),
    use_legacy: bool = typer.Option(
        False,
        "--legacy",
        help="Use legacy ~/.rekall/ path (compatibility mode)",
    ),
):
    """Rekall - Developer Knowledge Management System."""
    global _cli_global, _cli_legacy
    _cli_global = use_global
    _cli_legacy = use_legacy

    # Only reset config if CLI flags are used (allows test injection)
    if use_legacy or use_global:
        from rekall.config import reset_config
        reset_config()

    # Apply legacy mode if requested
    if use_legacy:
        from rekall.paths import ResolvedPaths, PathSource
        from pathlib import Path

        legacy_path = Path.home() / ".rekall"
        paths = ResolvedPaths(
            config_dir=legacy_path,
            data_dir=legacy_path,
            cache_dir=legacy_path / "cache",
            db_path=legacy_path / "knowledge.db",
            source=PathSource.CLI,
        )
        from rekall.config import Config, set_config
        set_config(Config(paths=paths))
    elif use_global:
        # Force global config (skip local project detection)
        from rekall.paths import PathResolver
        from rekall.config import Config, set_config
        paths = PathResolver.resolve(force_global=True)
        set_config(Config(paths=paths))

    if ctx.invoked_subcommand is None:
        # Launch interactive TUI
        from rekall.tui import run_tui
        run_tui()


# ============================================================================
# Version Command (like specify)
# ============================================================================


@app.command()
def version():
    """Display version and system information."""
    show_banner()

    # Build info table
    info_table = Table(show_header=False, box=None, padding=(0, 4))
    info_table.add_column("Label", style="dim", justify="right", width=20)
    info_table.add_column("Value", style="bold")

    info_table.add_row("CLI Version", __version__)
    info_table.add_row("Python", platform.python_version())
    info_table.add_row("Platform", platform.system())
    info_table.add_row("Architecture", platform.machine())

    # Get OS version
    if platform.system() == "Darwin":
        os_version = platform.mac_ver()[0]
    elif platform.system() == "Windows":
        os_version = platform.win32_ver()[0]
    else:
        os_version = platform.release()
    info_table.add_row("OS Version", os_version)

    # Database info
    config = get_config()
    db_exists = config.db_path.exists()
    info_table.add_row("Database", str(config.db_path))
    info_table.add_row("DB Status", "[green]initialized[/green]" if db_exists else "[yellow]not initialized[/yellow]")

    console.print(Panel(
        info_table,
        title="REKALL CLI Information",
        border_style="cyan",
        padding=(1, 2),
    ))


# ============================================================================
# Config Command (FR-007)
# ============================================================================


@app.command()
def config(
    show: bool = typer.Option(
        False,
        "--show",
        "-s",
        help="Display current configuration paths and sources",
    ),
):
    """Manage Rekall configuration.

    Display or modify configuration settings.

    Examples:
        rekall config --show    # Show all paths and their sources
    """
    import os

    if show:
        cfg = get_config()
        paths = cfg.paths

        console.print("[bold cyan]Configuration Rekall[/bold cyan]")
        console.print("─" * 40)
        console.print(f"[bold]Source:[/bold] {paths.source.value}")
        console.print()

        console.print("[bold]Chemins:[/bold]")
        console.print(f"  Config:  {paths.config_dir}")
        console.print(f"  Data:    {paths.data_dir}")
        console.print(f"  Cache:   {paths.cache_dir}")
        console.print(f"  DB:      {paths.db_path}")
        console.print()

        console.print("[bold]Variables d'environnement:[/bold]")
        rekall_home = os.environ.get("REKALL_HOME")
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        xdg_data = os.environ.get("XDG_DATA_HOME")

        console.print(f"  REKALL_HOME:     {rekall_home or '[dim](not set)[/dim]'}")
        console.print(f"  XDG_CONFIG_HOME: {xdg_config or '[dim](not set)[/dim]'}")
        console.print(f"  XDG_DATA_HOME:   {xdg_data or '[dim](not set)[/dim]'}")
        console.print()

        if paths.is_local_project:
            console.print("[bold]Projet local:[/bold] [green]Détecté (.rekall/)[/green]")
        else:
            console.print("[bold]Projet local:[/bold] [dim]Non détecté[/dim]")
    else:
        console.print("Use [cyan]rekall config --show[/cyan] to display configuration.")
        console.print("Use [cyan]rekall config --help[/cyan] for more options.")


# ============================================================================
# Init Command
# ============================================================================


@app.command()
def init(
    local: bool = typer.Option(
        False,
        "--local",
        "-l",
        help="Initialize in current directory as local project",
    ),
):
    """Initialize Rekall database.

    Creates the database file. By default uses XDG paths.
    Use --local to create .rekall/ in current directory for team sharing.

    Examples:
        rekall init           # Initialize with XDG paths
        rekall init --local   # Initialize .rekall/ in current directory
    """
    from rekall.paths import init_local_project

    if local:
        # Initialize local project
        local_dir = init_local_project()
        db_path = local_dir / "knowledge.db"
        db = Database(db_path)
        db.init()
        db.close()

        console.print(f"[green]✓[/green] Local project initialized: {local_dir}")
        console.print(f"  Database: {db_path}")
        console.print(f"  [dim]Add .rekall/ to Git to share with your team[/dim]")
    else:
        cfg = get_config()
        cfg.paths.ensure_dirs()
        db = Database(cfg.db_path)
        db.init()
        db.close()

        console.print(f"[green]✓[/green] Database initialized: {cfg.db_path}")


# ============================================================================
# Search Command (US1)
# ============================================================================


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    entry_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help=f"Filter by type: {', '.join(VALID_TYPES)}",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project",
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum results"),
):
    """Search knowledge base.

    Examples:
        rekall search "circular import"
        rekall search "cache" --type pattern
        rekall search "react" --project frontend
    """
    db = get_db()
    results = db.search(query, entry_type=entry_type, project=project, limit=limit)

    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return

    # Display results in a table
    table = Table(title=f"Search: {query}", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Type", width=10)
    table.add_column("Title", min_width=30)
    table.add_column("Confidence", justify="center", width=10)
    table.add_column("Project", width=15)

    for result in results:
        entry = result.entry
        confidence_stars = "★" * entry.confidence + "☆" * (5 - entry.confidence)
        table.add_row(
            entry.id[:12] + "...",
            entry.type,
            entry.title,
            confidence_stars,
            entry.project or "-",
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} result(s)[/dim]")


# ============================================================================
# Add Command (US2)
# ============================================================================


@app.command()
def add(
    entry_type: str = typer.Argument(
        ...,
        help=f"Entry type: {', '.join(VALID_TYPES)}",
    ),
    title: str = typer.Argument(..., help="Entry title"),
    tags: Optional[str] = typer.Option(
        None,
        "--tags",
        "-t",
        help="Comma-separated tags",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Project name",
    ),
    confidence: int = typer.Option(
        2,
        "--confidence",
        "-c",
        min=0,
        max=5,
        help="Confidence level (0-5)",
    ),
    content: Optional[str] = typer.Option(
        None,
        "--content",
        "-m",
        help="Entry content (markdown)",
    ),
):
    """Add a new knowledge entry.

    Types: bug, pattern, decision, pitfall, config, reference

    Examples:
        rekall add bug "Fix circular import" -t react,import -p my-project
        rekall add pattern "API error handling" -c 4
        rekall add decision "Use TypeScript" -m "Better type safety..."
    """
    # Validate type
    if entry_type not in VALID_TYPES:
        console.print(
            f"[red]Error: Invalid type '{entry_type}'[/red]\n"
            f"Valid types: {', '.join(VALID_TYPES)}"
        )
        raise typer.Exit(1)

    # Parse tags
    tag_list = []
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    # Read content from stdin if not provided and stdin is not a tty
    entry_content = content or ""
    if not entry_content and not sys.stdin.isatty():
        entry_content = sys.stdin.read()

    # Create entry
    entry = Entry(
        id=generate_ulid(),
        title=title,
        type=entry_type,
        content=entry_content,
        project=project,
        tags=tag_list,
        confidence=confidence,
    )

    # Save to database
    db = get_db()
    db.add(entry)

    console.print(f"[green]✓[/green] Entry created: {entry.id}")
    console.print(f"  Type: {entry.type}")
    console.print(f"  Title: {entry.title}")
    if tag_list:
        console.print(f"  Tags: {', '.join(tag_list)}")
    if project:
        console.print(f"  Project: {project}")


# ============================================================================
# Show Command
# ============================================================================


@app.command()
def show(
    entry_id: str = typer.Argument(..., help="Entry ID (or prefix)"),
):
    """Show entry details.

    Example:
        rekall show 01ARZ3NDEK
    """
    db = get_db()

    # Try exact match first, then prefix match
    entry = db.get(entry_id)
    if entry is None:
        # Try prefix match
        all_entries = db.list_all(limit=1000)
        matches = [e for e in all_entries if e.id.startswith(entry_id)]
        if len(matches) == 1:
            entry = matches[0]
        elif len(matches) > 1:
            console.print(f"[yellow]Multiple entries match '{entry_id}':[/yellow]")
            for e in matches[:5]:
                console.print(f"  {e.id}: {e.title}")
            return
        else:
            console.print(f"[red]Entry not found: {entry_id}[/red]")
            raise typer.Exit(1)

    # Display entry
    confidence_stars = "★" * entry.confidence + "☆" * (5 - entry.confidence)

    panel_content = Text()
    panel_content.append(f"ID: ", style="bold")
    panel_content.append(f"{entry.id}\n")
    panel_content.append(f"Type: ", style="bold")
    panel_content.append(f"{entry.type}\n")
    panel_content.append(f"Confidence: ", style="bold")
    panel_content.append(f"{confidence_stars}\n")
    if entry.project:
        panel_content.append(f"Project: ", style="bold")
        panel_content.append(f"{entry.project}\n")
    if entry.tags:
        panel_content.append(f"Tags: ", style="bold")
        panel_content.append(f"{', '.join(entry.tags)}\n")
    panel_content.append(f"Created: ", style="bold")
    panel_content.append(f"{entry.created_at.strftime('%Y-%m-%d %H:%M')}\n")
    if entry.status == "obsolete":
        panel_content.append(f"Status: ", style="bold")
        panel_content.append(f"OBSOLETE", style="red")
        if entry.superseded_by:
            panel_content.append(f" (replaced by {entry.superseded_by})")
        panel_content.append("\n")

    console.print(Panel(panel_content, title=entry.title, border_style="cyan"))

    if entry.content:
        console.print("\n[bold]Content:[/bold]")
        console.print(entry.content)


# ============================================================================
# Browse Command
# ============================================================================


@app.command()
def browse(
    entry_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help=f"Filter by type: {', '.join(VALID_TYPES)}",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project",
    ),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum entries"),
):
    """Browse all entries.

    Examples:
        rekall browse
        rekall browse --type bug
        rekall browse --project my-project
    """
    db = get_db()
    entries = db.list_all(entry_type=entry_type, project=project, limit=limit)

    if not entries:
        console.print("[yellow]No entries found.[/yellow]")
        return

    table = Table(title="Knowledge Base", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Type", width=10)
    table.add_column("Title", min_width=30)
    table.add_column("Confidence", justify="center", width=10)
    table.add_column("Created", width=12)

    for entry in entries:
        confidence_stars = "★" * entry.confidence + "☆" * (5 - entry.confidence)
        table.add_row(
            entry.id[:12] + "...",
            entry.type,
            entry.title,
            confidence_stars,
            entry.created_at.strftime("%Y-%m-%d"),
        )

    console.print(table)
    console.print(f"\n[dim]Showing {len(entries)} entries[/dim]")


# ============================================================================
# Deprecate Command
# ============================================================================


@app.command()
def deprecate(
    entry_id: str = typer.Argument(..., help="Entry ID to deprecate"),
    replaced_by: Optional[str] = typer.Option(
        None,
        "--replaced-by",
        "-r",
        help="ID of the replacing entry",
    ),
):
    """Mark an entry as obsolete.

    Example:
        rekall deprecate 01ARZ3NDEK --replaced-by 01BRZ4NEFL
    """
    db = get_db()
    entry = db.get(entry_id)

    if entry is None:
        console.print(f"[red]Entry not found: {entry_id}[/red]")
        raise typer.Exit(1)

    entry.status = "obsolete"
    entry.superseded_by = replaced_by
    db.update(entry)

    console.print(f"[green]✓[/green] Entry marked as obsolete: {entry_id}")
    if replaced_by:
        console.print(f"  Replaced by: {replaced_by}")


# ============================================================================
# Install Command (US4 - IDE Integration)
# ============================================================================


@app.command()
def install(
    ide: Optional[str] = typer.Argument(
        None,
        help="IDE/Agent to install integration for",
    ),
    list_available: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List available integrations",
    ),
):
    """Install IDE/Agent integration.

    Creates configuration files for your AI coding assistant.

    Examples:
        rekall install --list          # Show available integrations
        rekall install cursor          # Create .cursorrules
        rekall install claude          # Create Claude Code skill
        rekall install copilot         # Create Copilot instructions
    """
    from rekall import integrations

    # List mode
    if list_available or ide is None:
        available = integrations.get_available()

        table = Table(title="Available Integrations", show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Name", style="cyan", width=12)
        table.add_column("Description", min_width=25)
        table.add_column("Local", style="dim")
        table.add_column("Global", style="dim")

        for name, desc, local_target, global_target in available:
            table.add_row(name, desc, local_target, global_target or "—")

        console.print(table)
        console.print(f"\n[dim]Usage: rekall install <name> [--global][/dim]")
        return

    # Install mode
    try:
        target_path = integrations.install(ide, Path.cwd())
        console.print(f"[green]✓[/green] Integration installed: {ide}")
        console.print(f"  Created: {target_path}")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")

        # Show available options
        console.print("\n[yellow]Available integrations:[/yellow]")
        for name, desc, local_target, global_target in integrations.get_available():
            console.print(f"  [cyan]{name}[/cyan] - {desc}")

        raise typer.Exit(1)


# ============================================================================
# Research Command (US5 - Curated Research Sources)
# ============================================================================


def get_research_topics() -> dict[str, Path]:
    """Get available research topics from bundled files."""
    import importlib.resources

    topics = {}

    # Try to find research files in package
    try:
        # Python 3.9+ way
        research_dir = Path(__file__).parent / "research"
        if research_dir.exists():
            for f in research_dir.glob("*.md"):
                if f.name == "README.md":
                    continue
                # Extract topic name from filename (e.g., "01-ai-agents-agentic-ai.md" -> "ai-agents")
                name = f.stem
                # Remove number prefix if present
                if name[:2].isdigit() and name[2] == "-":
                    name = name[3:]
                # Take first part as topic name
                topic = name.split("-")[0] if "-" in name else name
                # Use full name for better matching
                full_topic = "-".join(name.split("-")[:2]) if "-" in name else name
                topics[full_topic] = f
    except Exception:
        pass

    return topics


@app.command()
def research(
    topic: Optional[str] = typer.Argument(
        None,
        help="Research topic to display",
    ),
    list_topics: bool = typer.Option(
        False,
        "--list",
        "-l",
        help="List available research topics",
    ),
):
    """Browse curated research sources.

    Access curated research documents on various development topics.

    Examples:
        rekall research --list           # Show available topics
        rekall research ai-agents        # Show AI agents research
        rekall research security         # Show security research
    """
    topics = get_research_topics()

    # List mode or no topic
    if list_topics or topic is None:
        table = Table(title="Available Research Topics", show_header=True, header_style="bold", box=box.ROUNDED)
        table.add_column("Topic", style="cyan", width=25)
        table.add_column("File", style="dim")

        for name, path in sorted(topics.items()):
            table.add_row(name, path.name)

        console.print(table)
        console.print(f"\n[dim]Usage: rekall research <topic>[/dim]")
        return

    # Find matching topic
    matching = None
    for name, path in topics.items():
        if topic.lower() in name.lower() or name.lower() in topic.lower():
            matching = (name, path)
            break

    if matching is None:
        console.print(f"[red]Error: Unknown topic '{topic}'[/red]")
        console.print("\n[yellow]Available topics:[/yellow]")
        for name in sorted(topics.keys()):
            console.print(f"  [cyan]{name}[/cyan]")
        raise typer.Exit(1)

    # Display content
    name, path = matching
    content = path.read_text()

    console.print(Panel(
        f"[bold]{name}[/bold]\n[dim]{path.name}[/dim]",
        border_style="cyan",
    ))
    console.print()
    console.print(content)


# ============================================================================
# Similar Command (US6 - Semantic Search with FTS Fallback)
# ============================================================================


@app.command()
def similar(
    query: str = typer.Argument(..., help="Query to find similar entries"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results"),
):
    """Find semantically similar entries.

    Uses embeddings when configured, falls back to FTS otherwise.

    Examples:
        rekall similar "error handling patterns"
        rekall similar "authentication flow" -l 5
    """
    config = get_config()
    db = get_db()

    # Check if embeddings provider is configured
    has_embeddings = config.embeddings_provider is not None

    if has_embeddings:
        # TODO: Implement actual embedding-based search
        # For now, just note that it would use embeddings
        console.print("[dim]Using embeddings provider: {config.embeddings_provider}[/dim]")
    else:
        console.print("[dim]No embeddings provider configured, using FTS fallback[/dim]")

    # Fallback to FTS search
    results = db.search(query, limit=limit)

    if not results:
        console.print("[yellow]No similar entries found.[/yellow]")
        return

    # Display results
    table = Table(title=f"Similar to: {query}", show_header=True, header_style="bold", box=box.ROUNDED)
    table.add_column("ID", style="dim", width=12)
    table.add_column("Type", width=10)
    table.add_column("Title", min_width=30)
    table.add_column("Confidence", justify="center", width=10)

    for result in results:
        entry = result.entry
        confidence_stars = "★" * entry.confidence + "☆" * (5 - entry.confidence)
        table.add_row(
            entry.id[:12] + "...",
            entry.type,
            entry.title,
            confidence_stars,
        )

    console.print(table)
    console.print(f"\n[dim]Found {len(results)} similar entries (FTS fallback)[/dim]")


# ============================================================================
# Export/Import Commands (Phase 9 + Export/Import Sync)
# ============================================================================


@app.command()
def export(
    output: str = typer.Argument(
        ...,
        help="Output file path (.rekall.zip for archive, .md or .json for text)",
    ),
    format: Optional[str] = typer.Option(
        None,
        "--format",
        "-f",
        help="Export format: rekall (default), md, or json",
    ),
    entry_type: Optional[str] = typer.Option(
        None,
        "--type",
        "-t",
        help="Filter by entry type",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        "-p",
        help="Filter by project",
    ),
):
    """Export knowledge base.

    Export all entries to .rekall.zip archive (portable backup) or text formats.

    Examples:
        rekall export backup.rekall.zip
        rekall export backup.rekall.zip --project myproject
        rekall export --format md knowledge.md
        rekall export --format json backup.json
    """
    from rekall import exporters
    from rekall.archive import RekallArchive

    db = get_db()
    entries = db.list_all(entry_type=entry_type, project=project, limit=100000)

    if not entries:
        console.print("[yellow]No entries to export.[/yellow]")
        return

    # Determine format from output extension or explicit option
    output_path = Path(output)
    if format is None:
        if output_path.name.endswith(".rekall.zip"):
            format = "rekall"
        elif output_path.suffix == ".json":
            format = "json"
        else:
            format = "md"

    # Check for sensitive data
    sensitive = exporters.detect_sensitive_data(entries)
    if sensitive:
        console.print(f"[yellow]Warning: {len(sensitive)} entries may contain sensitive data:[/yellow]")
        for entry_id, title, pattern in sensitive[:5]:
            console.print(f"  [dim]{entry_id[:12]}[/dim] {title} ({pattern})")
        if len(sensitive) > 5:
            console.print(f"  [dim]... and {len(sensitive) - 5} more[/dim]")
        console.print()

    # Export
    if format == "rekall":
        RekallArchive.create(output_path, entries)
        console.print(f"[green]✓[/green] Exported {len(entries)} entries to {output}")
    elif format == "json":
        content = exporters.export_json(entries)
        output_path.write_text(content)
        console.print(f"[green]✓[/green] Exported {len(entries)} entries to {output}")
    else:
        content = exporters.export_markdown(entries)
        output_path.write_text(content)
        console.print(f"[green]✓[/green] Exported {len(entries)} entries to {output}")


@app.command("import")
def import_archive(
    archive: str = typer.Argument(..., help="Path to .rekall.zip archive file"),
    strategy: str = typer.Option(
        "skip",
        "--strategy",
        "-s",
        help="Conflict resolution: skip (default), replace, merge",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Preview changes without importing",
    ),
    yes: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
    no_backup: bool = typer.Option(
        False,
        "--no-backup",
        help="Skip automatic backup before replace",
    ),
):
    """Import knowledge base from .rekall.zip archive.

    Import entries from a portable .rekall.zip archive with conflict resolution.

    Strategies:
        skip    - Keep local entries on conflict (default)
        replace - Overwrite local with imported (creates backup)
        merge   - Create new entries with new IDs

    Examples:
        rekall import backup.rekall.zip
        rekall import backup.rekall.zip --dry-run
        rekall import backup.rekall.zip --strategy replace --yes
    """
    from rekall.archive import RekallArchive
    from rekall.sync import ImportExecutor, build_import_plan

    archive_path = Path(archive)

    # Check file exists
    if not archive_path.exists():
        console.print(f"[red]Error: File not found: {archive}[/red]")
        raise typer.Exit(1)

    # Open and validate archive
    rekall_archive = RekallArchive.open(archive_path)
    if rekall_archive is None:
        console.print(f"[red]Error: Invalid or corrupted archive: {archive}[/red]")
        raise typer.Exit(1)

    validation = rekall_archive.validate()
    if not validation.valid:
        console.print("[red]Error: Archive validation failed:[/red]")
        for error in validation.errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)

    # Get manifest and entries
    manifest = rekall_archive.get_manifest()
    imported_entries = rekall_archive.get_entries()

    console.print(f"[cyan]Archive info:[/cyan]")
    console.print(f"  Version: {manifest.format_version}")
    console.print(f"  Created: {manifest.created_at.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"  Entries: {manifest.stats.entries_count}")
    console.print()

    # Build import plan
    db = get_db()
    plan = build_import_plan(db, imported_entries)

    # Show preview
    executor = ImportExecutor(db)
    preview = executor.preview(plan)
    console.print(preview)
    console.print()

    # Dry run mode
    if dry_run:
        console.print("[yellow]Dry run - no changes made.[/yellow]")
        return

    # Confirmation
    if not yes:
        if plan.total == 0:
            console.print("[yellow]Nothing to import.[/yellow]")
            return

        confirm = typer.confirm("Continue with import?")
        if not confirm:
            console.print("[yellow]Import cancelled.[/yellow]")
            return

    # Validate strategy
    if strategy not in ("skip", "replace", "merge"):
        console.print(f"[red]Error: Invalid strategy '{strategy}'. Use: skip, replace, merge[/red]")
        raise typer.Exit(1)

    # Configure backup
    backup_dir = None if no_backup else db.db_path.parent / "backups"
    executor = ImportExecutor(db, backup_dir=backup_dir)

    # Execute import
    result = executor.execute(plan, strategy=strategy)

    if result.success:
        console.print()
        console.print("[green]✓ Import completed successfully![/green]")
        console.print(f"  Added: {result.added}")
        if result.replaced:
            console.print(f"  Replaced: {result.replaced}")
        if result.merged:
            console.print(f"  Merged: {result.merged}")
        console.print(f"  Skipped: {result.skipped}")
        if result.backup_path:
            console.print(f"  Backup: {result.backup_path}")
    else:
        console.print("[red]Error: Import failed[/red]")
        for error in result.errors:
            console.print(f"  - {error}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
