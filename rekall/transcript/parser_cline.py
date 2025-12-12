"""
Parser pour les transcripts Cline (format JSON).

Cline stocke l'historique des conversations dans un fichier JSON
api_conversation_history.json dans le dossier de la tâche.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from rekall.transcript.models import TranscriptFormat, TranscriptMessage
from rekall.transcript.parser_base import ParserError, TranscriptParser


class ClineTranscriptParser(TranscriptParser):
    """
    Parser pour le format JSON de Cline VS Code extension.

    Format attendu (api_conversation_history.json):
    [
        {
            "role": "user" | "assistant",
            "content": "..." | [{"type": "text", "text": "..."}],
            "ts": timestamp_ms (optionnel)
        },
        ...
    ]

    Ou structure avec wrapper:
    {
        "messages": [...],
        "metadata": {...}
    }
    """

    @property
    def format(self) -> TranscriptFormat:
        return TranscriptFormat.CLINE_JSON

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

        # Extrait la liste des messages
        messages_data = self._extract_messages_list(data)
        if messages_data is None:
            raise ParserError(
                "Could not find messages in transcript",
                path=path,
                format=self.format,
            )

        messages = []
        for index, msg_data in enumerate(messages_data):
            msg = self._parse_message(msg_data, index)
            if msg:
                messages.append(msg)

        return messages

    def parse_last_n(
        self, path: Path, n: int = 20
    ) -> tuple[list[TranscriptMessage], int]:
        """
        Parse les N derniers messages.

        Note: Pour JSON, on doit charger tout le fichier en mémoire,
        mais on ne retourne que les N derniers messages.
        """
        all_messages = self.parse(path)
        total = len(all_messages)

        # Retourne les N derniers
        last_n = all_messages[-n:] if len(all_messages) > n else all_messages

        return last_n, total

    def _extract_messages_list(self, data) -> Optional[list]:
        """Extrait la liste des messages depuis différentes structures possibles."""
        # Direct array
        if isinstance(data, list):
            return data

        # Wrapper object
        if isinstance(data, dict):
            if "messages" in data:
                return data["messages"]
            if "conversation" in data:
                return data["conversation"]
            if "history" in data:
                return data["history"]

        return None

    def _parse_message(self, data: dict, index: int) -> Optional[TranscriptMessage]:
        """Parse un objet message en TranscriptMessage."""
        if not isinstance(data, dict):
            return None

        # Extraction du rôle
        role = data.get("role")
        if not role:
            return None

        # Normalise le rôle
        try:
            normalized_role = self.normalize_role(role)
        except ValueError:
            return None

        # Extraction du contenu
        content = self._extract_content(data)
        if not content:
            return None

        # Extraction du timestamp (optionnel)
        timestamp = self._extract_timestamp(data)

        return TranscriptMessage(
            role=normalized_role,  # type: ignore
            content=content,
            timestamp=timestamp,
            index=index,
        )

    def _extract_content(self, data: dict) -> Optional[str]:
        """Extrait le contenu textuel."""
        content = data.get("content")

        if isinstance(content, str):
            return content

        if isinstance(content, list):
            # Format: [{"type": "text", "text": "..."}, ...]
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if "text" in item:
                        parts.append(item["text"])
                    elif "content" in item:
                        parts.append(str(item["content"]))
                elif isinstance(item, str):
                    parts.append(item)
            return "\n".join(parts) if parts else None

        return None

    def _extract_timestamp(self, data: dict) -> Optional[datetime]:
        """Extrait le timestamp si présent."""
        # Timestamp en millisecondes
        ts = data.get("ts") or data.get("timestamp")
        if ts:
            try:
                if isinstance(ts, (int, float)):
                    # Millisecondes vers datetime
                    return datetime.fromtimestamp(ts / 1000)
                elif isinstance(ts, str):
                    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, OSError):
                pass
        return None
