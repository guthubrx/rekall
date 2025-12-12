"""Claude Code CLI connector for URL extraction.

This module extracts URLs from Claude Code (claude.ai CLI) conversation history,
specifically targeting WebFetch tool calls which contain documentation URLs.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from rekall.connectors.base import BaseConnector, ExtractedURL, ExtractionResult


class ClaudeCLIConnector(BaseConnector):
    """Connector for Claude Code CLI history.

    Claude Code stores conversation history in JSONL files under:
    ~/.claude/projects/{project_hash}/conversations/

    Each conversation is a JSONL file where each line is a JSON object
    representing a message or tool call.
    """

    # Default paths
    CLAUDE_DIR = Path.home() / ".claude"
    PROJECTS_DIR = CLAUDE_DIR / "projects"

    # URL extraction patterns
    URL_PATTERN = re.compile(
        r'https?://[^\s<>"\'`\]\)]+',
        re.IGNORECASE,
    )

    @property
    def cli_source(self) -> str:
        """Identifier for Claude Code CLI."""
        return "claude"

    def is_available(self) -> bool:
        """Check if Claude Code is installed and has history.

        Returns:
            True if ~/.claude/projects/ exists and has content
        """
        return self.PROJECTS_DIR.exists() and any(self.PROJECTS_DIR.iterdir())

    def get_history_paths(self) -> list[Path]:
        """Get paths to all Claude Code JSONL history files.

        Returns:
            List of paths to JSONL conversation files, sorted by modification time
        """
        if not self.is_available():
            return []

        jsonl_files = []
        for project_dir in self.PROJECTS_DIR.iterdir():
            if not project_dir.is_dir():
                continue
            conversations_dir = project_dir / "conversations"
            if conversations_dir.exists():
                jsonl_files.extend(conversations_dir.glob("*.jsonl"))

        # Sort by modification time (oldest first for incremental processing)
        return sorted(jsonl_files, key=lambda p: p.stat().st_mtime)

    def extract_urls(
        self,
        since_marker: Optional[str] = None,
        project_filter: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract URLs from Claude Code history.

        Targets WebFetch tool calls which contain documentation URLs.
        Also extracts URLs from assistant responses when relevant.

        Args:
            since_marker: Optional file path marker for CDC (skip files before this)
            project_filter: Optional project name to filter by

        Returns:
            ExtractionResult with extracted URLs
        """
        result = ExtractionResult()

        if not self.is_available():
            result.errors.append("Claude Code not available or no history found")
            return result

        history_files = self.get_history_paths()
        if not history_files:
            return result

        # Find starting point for incremental import
        start_idx = 0
        if since_marker:
            try:
                marker_path = Path(since_marker)
                for idx, path in enumerate(history_files):
                    if path == marker_path or str(path) == since_marker:
                        start_idx = idx + 1  # Start after the marker
                        break
            except Exception:
                pass  # Invalid marker, start from beginning

        # Process files
        seen_urls: set[str] = set()  # Dedup within this extraction

        for file_path in history_files[start_idx:]:
            result.files_processed += 1
            result.last_file_marker = str(file_path)

            # Determine project from path
            project = self._extract_project_from_path(file_path)
            if project_filter and project != project_filter:
                continue

            # Extract conversation ID from filename
            conversation_id = file_path.stem

            try:
                urls = self._extract_urls_from_file(
                    file_path, project, conversation_id, seen_urls
                )
                result.urls.extend(urls)
            except Exception as e:
                result.errors.append(f"Error processing {file_path}: {e}")

        return result

    def _extract_project_from_path(self, file_path: Path) -> Optional[str]:
        """Extract project identifier from file path.

        The path structure is: ~/.claude/projects/{project_hash}/conversations/{id}.jsonl
        We try to find a more human-readable project name from project metadata.
        """
        try:
            # Navigate up to project directory
            project_dir = file_path.parent.parent

            # Try to read project metadata
            metadata_file = project_dir / "project.json"
            if metadata_file.exists():
                with open(metadata_file, encoding="utf-8") as f:
                    metadata = json.load(f)
                    return metadata.get("name") or metadata.get("path") or project_dir.name

            # Fall back to directory name (hash)
            return project_dir.name
        except Exception:
            return None

    def _extract_urls_from_file(
        self,
        file_path: Path,
        project: Optional[str],
        conversation_id: str,
        seen_urls: set[str],
    ) -> list[ExtractedURL]:
        """Extract URLs from a single JSONL conversation file.

        Args:
            file_path: Path to the JSONL file
            project: Project identifier
            conversation_id: Conversation ID
            seen_urls: Set of already-seen URLs for deduplication

        Returns:
            List of ExtractedURL objects
        """
        urls: list[ExtractedURL] = []

        with open(file_path, encoding="utf-8") as f:
            last_user_query: Optional[str] = None

            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Track user queries for context
                if self._is_user_message(entry):
                    last_user_query = self._extract_text(entry)
                    continue

                # Look for WebFetch tool calls (primary source)
                webfetch_urls = self._extract_webfetch_urls(entry)
                for url, snippet in webfetch_urls:
                    if url in seen_urls:
                        continue

                    is_valid, error = self.validate_url(url)
                    extracted = ExtractedURL(
                        url=url,
                        domain=self.extract_domain(url),
                        project=project,
                        conversation_id=conversation_id,
                        user_query=last_user_query[:500] if last_user_query else None,
                        assistant_snippet=snippet[:500] if snippet else None,
                        captured_at=self._get_timestamp(entry) or datetime.now(),
                        raw_json=line if not is_valid else None,  # Keep raw for debugging quarantined
                        source_file=str(file_path),
                    )

                    # Mark invalid URLs
                    if not is_valid:
                        extracted.raw_json = json.dumps({
                            "validation_error": error,
                            "original_line": line_num,
                        })

                    urls.append(extracted)
                    seen_urls.add(url)

                # Also extract URLs from assistant responses (secondary)
                if self._is_assistant_message(entry):
                    text = self._extract_text(entry)
                    if text:
                        inline_urls = self._extract_inline_urls(text)
                        for url in inline_urls:
                            if url in seen_urls:
                                continue

                            is_valid, error = self.validate_url(url)
                            extracted = ExtractedURL(
                                url=url,
                                domain=self.extract_domain(url),
                                project=project,
                                conversation_id=conversation_id,
                                user_query=last_user_query[:500] if last_user_query else None,
                                surrounding_text=text[:200] if text else None,
                                captured_at=self._get_timestamp(entry) or datetime.now(),
                                source_file=str(file_path),
                            )

                            if not is_valid:
                                extracted.raw_json = json.dumps({
                                    "validation_error": error,
                                })

                            urls.append(extracted)
                            seen_urls.add(url)

        return urls

    def _is_user_message(self, entry: dict) -> bool:
        """Check if entry is a user message."""
        return entry.get("role") == "user" or entry.get("type") == "human"

    def _is_assistant_message(self, entry: dict) -> bool:
        """Check if entry is an assistant message."""
        return entry.get("role") == "assistant" or entry.get("type") == "assistant"

    def _extract_text(self, entry: dict) -> Optional[str]:
        """Extract text content from an entry."""
        # Direct content
        if isinstance(entry.get("content"), str):
            return entry["content"]

        # Content array (Claude format)
        if isinstance(entry.get("content"), list):
            texts = []
            for item in entry["content"]:
                if isinstance(item, str):
                    texts.append(item)
                elif isinstance(item, dict) and item.get("type") == "text":
                    texts.append(item.get("text", ""))
            return "\n".join(texts) if texts else None

        # Message field
        if entry.get("message"):
            return self._extract_text({"content": entry["message"]})

        return None

    def _extract_webfetch_urls(self, entry: dict) -> list[tuple[str, Optional[str]]]:
        """Extract URLs from WebFetch tool calls.

        Returns:
            List of (url, snippet) tuples
        """
        urls = []

        # Tool use format
        if entry.get("type") == "tool_use" and entry.get("name") == "WebFetch":
            input_data = entry.get("input", {})
            url = input_data.get("url")
            if url:
                urls.append((url, None))

        # Tool calls array format
        for tool_call in entry.get("tool_calls", []):
            if tool_call.get("name") == "WebFetch":
                input_data = tool_call.get("input", {})
                url = input_data.get("url")
                if url:
                    urls.append((url, None))

        # Content array with tool_use
        if isinstance(entry.get("content"), list):
            for item in entry["content"]:
                if isinstance(item, dict):
                    if item.get("type") == "tool_use" and item.get("name") == "WebFetch":
                        input_data = item.get("input", {})
                        url = input_data.get("url")
                        if url:
                            urls.append((url, None))

        # Tool result format (contains the fetched content)
        if entry.get("type") == "tool_result":
            # Get URL from tool_use_id reference or content
            content = entry.get("content", "")
            if isinstance(content, str) and "http" in content.lower():
                # Try to extract URL from result
                found = self.URL_PATTERN.findall(content)
                for url in found[:1]:  # Only first URL from result
                    snippet = content[:200] if content else None
                    urls.append((url, snippet))

        return urls

    def _extract_inline_urls(self, text: str) -> list[str]:
        """Extract HTTP/HTTPS URLs from text.

        Args:
            text: Text to search for URLs

        Returns:
            List of unique URLs found
        """
        if not text:
            return []

        # Find all URLs
        matches = self.URL_PATTERN.findall(text)

        # Clean up URLs (remove trailing punctuation that might be captured)
        cleaned = []
        for url in matches:
            # Remove common trailing chars that shouldn't be part of URL
            url = url.rstrip(".,;:!?)]}>\"'")
            if url and len(url) > 10:  # Minimum reasonable URL length
                cleaned.append(url)

        return list(dict.fromkeys(cleaned))  # Preserve order, remove dupes

    def _get_timestamp(self, entry: dict) -> Optional[datetime]:
        """Extract timestamp from entry if available."""
        for key in ("timestamp", "created_at", "time"):
            if key in entry:
                try:
                    ts = entry[key]
                    if isinstance(ts, (int, float)):
                        return datetime.fromtimestamp(ts)
                    if isinstance(ts, str):
                        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                except Exception:
                    continue
        return None
