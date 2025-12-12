"""Auto-scan module for periodic connector imports.

This module handles automatic periodic scanning of non-Claude connectors
(Cursor, etc.) based on configurable intervals.

Claude URLs are captured in real-time via PostToolUse hook, but other
CLIs require periodic scanning of their history files.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from rekall.db import Database


@dataclass
class ScanResult:
    """Result of a single connector scan."""

    connector: str
    success: bool
    imported: int = 0
    quarantined: int = 0
    skipped: bool = False  # True if scan was skipped (not due yet)
    error: Optional[str] = None
    last_marker: Optional[str] = None


@dataclass
class AutoscanResult:
    """Result of auto-scan operation."""

    scans_performed: int = 0
    scans_skipped: int = 0
    total_imported: int = 0
    total_quarantined: int = 0
    results: list[ScanResult] = None
    errors: list[str] = None

    def __post_init__(self):
        if self.results is None:
            self.results = []
        if self.errors is None:
            self.errors = []


def needs_scan(
    db: "Database",
    connector_name: str,
    interval_hours: float = 5.0,
    now: Optional[datetime] = None,
) -> bool:
    """Check if a connector needs to be scanned.

    Args:
        db: Database instance
        connector_name: Name of the connector to check
        interval_hours: Hours between scans
        now: Current time (uses datetime.now() if None)

    Returns:
        True if scan is needed (no previous scan or interval exceeded)
    """
    if now is None:
        now = datetime.now()

    # Get last import record
    import_record = db.get_connector_import(connector_name)

    if import_record is None or import_record.last_import is None:
        # Never scanned before
        return True

    # Check if interval has passed
    time_since_last = now - import_record.last_import
    interval = timedelta(hours=interval_hours)

    return time_since_last >= interval


def scan_connector(
    db: "Database",
    connector_name: str,
    force: bool = False,
    interval_hours: float = 5.0,
) -> ScanResult:
    """Scan a single connector for new URLs.

    Args:
        db: Database instance
        connector_name: Name of the connector to scan
        force: If True, scan even if interval hasn't passed
        interval_hours: Hours between scans (used if not forcing)

    Returns:
        ScanResult with import statistics
    """
    from rekall.connectors import get_connector
    from rekall.models import ConnectorImport, InboxEntry, generate_ulid

    # Check if scan needed
    if not force and not needs_scan(db, connector_name, interval_hours):
        return ScanResult(
            connector=connector_name,
            success=True,
            skipped=True,
        )

    # Get connector
    connector = get_connector(connector_name)
    if not connector:
        return ScanResult(
            connector=connector_name,
            success=False,
            error=f"Connector '{connector_name}' not found",
        )

    if not connector.is_available():
        return ScanResult(
            connector=connector_name,
            success=False,
            error=f"Connector '{connector_name}' not available (no history found)",
        )

    # Get last import marker for CDC
    import_record = db.get_connector_import(connector_name)
    since_marker = import_record.last_file_marker if import_record else None

    # Extract URLs
    try:
        extraction = connector.extract_urls(since_marker=since_marker)
    except Exception as e:
        return ScanResult(
            connector=connector_name,
            success=False,
            error=str(e),
        )

    # Import to inbox
    imported = 0
    quarantined = 0
    for extracted in extraction.urls:
        is_valid, error = connector.validate_url(extracted.url)

        entry = InboxEntry(
            id=generate_ulid(),
            url=extracted.url,
            domain=extracted.domain,
            cli_source=connector_name,
            project=extracted.project,
            conversation_id=extracted.conversation_id,
            user_query=extracted.user_query,
            assistant_snippet=extracted.assistant_snippet,
            surrounding_text=extracted.surrounding_text,
            captured_at=extracted.captured_at,
            import_source="autoscan",
            raw_json=extracted.raw_json,
            is_valid=is_valid,
            validation_error=error,
        )
        db.add_inbox_entry(entry)

        if is_valid:
            imported += 1
        else:
            quarantined += 1

    # Update CDC marker
    now = datetime.now()
    new_record = ConnectorImport(
        connector=connector_name,
        last_import=now,
        last_file_marker=extraction.last_file_marker or since_marker,
        entries_imported=(import_record.entries_imported if import_record else 0) + imported,
        errors_count=(import_record.errors_count if import_record else 0) + len(extraction.errors),
    )
    db.upsert_connector_import(new_record)

    return ScanResult(
        connector=connector_name,
        success=True,
        imported=imported,
        quarantined=quarantined,
        last_marker=extraction.last_file_marker,
    )


def autoscan(
    db: "Database",
    connectors: Optional[list[str]] = None,
    force: bool = False,
    interval_hours: Optional[float] = None,
) -> AutoscanResult:
    """Run auto-scan on configured connectors.

    Args:
        db: Database instance
        connectors: List of connector names to scan (uses config if None)
        force: If True, scan all connectors regardless of interval
        interval_hours: Override interval (uses config if None)

    Returns:
        AutoscanResult with aggregate statistics
    """
    from rekall.config import get_autoscan_config

    config = get_autoscan_config()

    # Use config values if not provided
    if connectors is None:
        connectors = config.connectors
    if interval_hours is None:
        interval_hours = config.interval_hours

    result = AutoscanResult()

    for connector_name in connectors:
        scan_result = scan_connector(
            db=db,
            connector_name=connector_name,
            force=force,
            interval_hours=interval_hours,
        )

        result.results.append(scan_result)

        if scan_result.skipped:
            result.scans_skipped += 1
        elif scan_result.success:
            result.scans_performed += 1
            result.total_imported += scan_result.imported
            result.total_quarantined += scan_result.quarantined
        else:
            result.errors.append(f"{connector_name}: {scan_result.error}")

    return result


def autoscan_if_needed(db: "Database") -> Optional[AutoscanResult]:
    """Run auto-scan if enabled and needed.

    This is the main entry point for automatic scanning.
    Call this from frequently-used commands to trigger periodic scans.

    Args:
        db: Database instance

    Returns:
        AutoscanResult if scan was performed, None if disabled or all skipped
    """
    from rekall.config import get_autoscan_config

    config = get_autoscan_config()

    if not config.enabled:
        return None

    # Check if any connector needs scanning
    any_needed = any(
        needs_scan(db, connector, config.interval_hours)
        for connector in config.connectors
    )

    if not any_needed:
        return None

    # Run autoscan (will skip connectors that don't need it)
    return autoscan(db)
