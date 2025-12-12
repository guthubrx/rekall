"""
Parser pour les transcripts Continue.dev (format JSON).

Continue.dev stocke les données de développement dans .continue/dev_data/
avec un format JSON spécifique.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from rekall.transcript.models import TranscriptFormat, TranscriptMessage
from rekall.transcript.parser_base import ParserError, TranscriptParser


class ContinueTranscriptParser(TranscriptParser):
    """
    Parser pour le format JSON de Continue.dev.

    Format attendu:
    {
        "sessions": [
            {
                "messages": [
                    {"role": "user", "content": "..."},
                    {"role": "assistant", "content": "..."}
                ]
            }
        ]
    }

    Ou format simplifié:
    {
        "messages": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """

    @property
    def format(self) -> TranscriptFormat:
        return TranscriptFormat.CONTINUE_JSON

    def parse(self, path: Path) -> list[TranscriptMessage]:
        """Parse le fichier JSON complet."""
        if not path.exists():
            raise FileNotFoundError(f"Transcript not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ParserError(
                f"Invalid JSON format: {e}",
                path=path,
                format=self.format,
            )
        except IOError as e:
            raise ParserError(
                f"Failed to read transcript: {e}",
                path=path,
                format=self.format,
            )

        # Extrait tous les messages de toutes les sessions
        all_messages = self._extract_all_messages(data)

        messages = []
        for index, msg_data in enumerate(all_messages):
            msg = self._parse_message(msg_data, index)
            if msg:
                messages.append(msg)

        return messages

    def parse_last_n(
        self, path: Path, n: int = 20
    ) -> tuple[list[TranscriptMessage], int]:
        """Parse les N derniers messages."""
        all_messages = self.parse(path)
        total = len(all_messages)
        last_n = all_messages[-n:] if len(all_messages) > n else all_messages
        return last_n, total

    def _extract_all_messages(self, data) -> list:
        """Extrait tous les messages depuis la structure Continue.dev."""
        messages = []

        if isinstance(data, dict):
            # Format avec sessions
            if "sessions" in data:
                for session in data["sessions"]:
                    if isinstance(session, dict) and "messages" in session:
                        messages.extend(session["messages"])
            # Format direct avec messages
            elif "messages" in data:
                messages.extend(data["messages"])
            # Format avec history
            elif "history" in data:
                messages.extend(data["history"])

        elif isinstance(data, list):
            messages = data

        return messages

    def _parse_message(self, data: dict, index: int) -> Optional[TranscriptMessage]:
        """Parse un objet message en TranscriptMessage."""
        if not isinstance(data, dict):
            return None

        role = data.get("role")
        if not role:
            return None

        try:
            normalized_role = self.normalize_role(role)
        except ValueError:
            return None

        content = data.get("content", "")
        if isinstance(content, list):
            # Format array de content blocks
            parts = []
            for item in content:
                if isinstance(item, dict) and "text" in item:
                    parts.append(item["text"])
                elif isinstance(item, str):
                    parts.append(item)
            content = "\n".join(parts)

        if not content:
            return None

        timestamp = None
        if "timestamp" in data:
            try:
                ts = data["timestamp"]
                if isinstance(ts, str):
                    timestamp = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                elif isinstance(ts, (int, float)):
                    timestamp = datetime.fromtimestamp(ts / 1000)
            except (ValueError, OSError):
                pass

        return TranscriptMessage(
            role=normalized_role,  # type: ignore
            content=content,
            timestamp=timestamp,
            index=index,
        )
