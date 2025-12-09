"""Export functionality for Rekall."""

from __future__ import annotations

import json
import re
from datetime import datetime

from rekall.models import Entry

# Patterns for detecting sensitive data
SENSITIVE_PATTERNS = [
    (r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[\w-]{20,}", "API Key"),
    (r"(?i)(secret|token|password|passwd|pwd)\s*[:=]\s*['\"]?[\w-]{8,}", "Secret/Token"),
    (r"(?i)sk-[a-zA-Z0-9]{20,}", "OpenAI API Key"),
    (r"(?i)ghp_[a-zA-Z0-9]{36}", "GitHub Token"),
    (r"(?i)xox[baprs]-[a-zA-Z0-9-]{10,}", "Slack Token"),
    (r"(?i)Bearer\s+[a-zA-Z0-9._-]{20,}", "Bearer Token"),
    (r"(?i)aws[_-]?(access[_-]?key|secret)", "AWS Credentials"),
]


def detect_sensitive_data(entries: list[Entry]) -> list[tuple[str, str, str]]:
    """Detect potential sensitive data in entries.

    Returns list of (entry_id, entry_title, pattern_name) tuples.
    """
    findings = []

    for entry in entries:
        text = f"{entry.title} {entry.content}"
        for pattern, name in SENSITIVE_PATTERNS:
            if re.search(pattern, text):
                findings.append((entry.id, entry.title, name))
                break  # One finding per entry is enough

    return findings


def export_markdown(entries: list[Entry]) -> str:
    """Export entries to markdown format."""
    lines = [
        "# Rekall Knowledge Export",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total entries: {len(entries)}",
        "",
        "---",
        "",
    ]

    # Group by type
    by_type: dict[str, list[Entry]] = {}
    for entry in entries:
        if entry.type not in by_type:
            by_type[entry.type] = []
        by_type[entry.type].append(entry)

    for entry_type, type_entries in sorted(by_type.items()):
        lines.append(f"## {entry_type.title()}s ({len(type_entries)})")
        lines.append("")

        for entry in type_entries:
            confidence_stars = "★" * entry.confidence + "☆" * (5 - entry.confidence)
            lines.append(f"### {entry.title}")
            lines.append("")
            lines.append(f"- **ID**: `{entry.id}`")
            lines.append(f"- **Confidence**: {confidence_stars}")
            if entry.project:
                lines.append(f"- **Project**: {entry.project}")
            if entry.tags:
                lines.append(f"- **Tags**: {', '.join(entry.tags)}")
            lines.append(f"- **Created**: {entry.created_at.strftime('%Y-%m-%d')}")
            if entry.status == "obsolete":
                lines.append("- **Status**: OBSOLETE")
                if entry.superseded_by:
                    lines.append(f"- **Replaced by**: {entry.superseded_by}")
            lines.append("")

            if entry.content:
                lines.append(entry.content)
                lines.append("")

            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def export_json(entries: list[Entry]) -> str:
    """Export entries to JSON format."""
    data = []
    for entry in entries:
        entry_dict = {
            "id": entry.id,
            "title": entry.title,
            "type": entry.type,
            "content": entry.content,
            "project": entry.project,
            "tags": entry.tags,
            "confidence": entry.confidence,
            "status": entry.status,
            "superseded_by": entry.superseded_by,
            "created_at": entry.created_at.isoformat(),
            "updated_at": entry.updated_at.isoformat(),
        }
        data.append(entry_dict)

    return json.dumps(data, indent=2, ensure_ascii=False)
