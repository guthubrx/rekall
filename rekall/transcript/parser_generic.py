"""
Parser générique pour les transcripts JSON.

Ce parser est utilisé comme fallback quand le format spécifique
n'est pas reconnu. Il tente de parser différentes structures JSON courantes.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from rekall.transcript.models import TranscriptFormat, TranscriptMessage
from rekall.transcript.parser_base import ParserError, TranscriptParser


class GenericJsonParser(TranscriptParser):
    """
    Parser générique pour formats JSON non reconnus.

    Supporte plusieurs structures courantes:
    - Array direct: [{role, content}, ...]
    - Object avec messages: {messages: [...]}
    - Object avec conversation: {conversation: [...]}
    - Object avec history: {history: [...]}
    """

    @property
    def format(self) -> TranscriptFormat:
        return TranscriptFormat.RAW_JSON

    def parse(self, path: Path) -> list[TranscriptMessage]:
        """Parse le fichier JSON en essayant différentes structures."""
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

        # Tente d'extraire les messages
        messages_data = self._find_messages(data)
        if not messages_data:
            raise ParserError(
                "Could not find messages array in JSON",
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
        """Parse les N derniers messages."""
        all_messages = self.parse(path)
        total = len(all_messages)
        last_n = all_messages[-n:] if len(all_messages) > n else all_messages
        return last_n, total

    def _find_messages(self, data) -> Optional[list]:
        """
        Cherche la liste des messages dans différentes structures possibles.

        Explore récursivement si nécessaire.
        """
        # Direct array
        if isinstance(data, list):
            # Vérifie que ça ressemble à des messages
            if data and isinstance(data[0], dict):
                if any(
                    key in data[0] for key in ("role", "type", "sender", "from")
                ):
                    return data

        # Object avec clé connue
        if isinstance(data, dict):
            # Clés prioritaires
            for key in ("messages", "conversation", "history", "chat", "data"):
                if key in data:
                    found = self._find_messages(data[key])
                    if found:
                        return found

            # Cherche dans les sous-objets
            for value in data.values():
                if isinstance(value, (list, dict)):
                    found = self._find_messages(value)
                    if found:
                        return found

        return None

    def _parse_message(self, data: dict, index: int) -> Optional[TranscriptMessage]:
        """
        Parse un message avec support pour différents formats de rôle et contenu.
        """
        if not isinstance(data, dict):
            return None

        # Extraction du rôle (plusieurs conventions possibles)
        role = (
            data.get("role")
            or data.get("type")
            or data.get("sender")
            or data.get("from")
            or data.get("author")
        )

        if not role:
            return None

        try:
            normalized_role = self.normalize_role(role)
        except ValueError:
            return None

        # Extraction du contenu (plusieurs conventions possibles)
        content = self._extract_content(data)
        if not content:
            return None

        # Extraction du timestamp
        timestamp = self._extract_timestamp(data)

        return TranscriptMessage(
            role=normalized_role,  # type: ignore
            content=content,
            timestamp=timestamp,
            index=index,
        )

    def _extract_content(self, data: dict) -> Optional[str]:
        """Extrait le contenu depuis différentes structures."""
        # Clés possibles pour le contenu
        for key in ("content", "text", "message", "body", "value"):
            if key in data:
                value = data[key]
                if isinstance(value, str):
                    return value
                if isinstance(value, list):
                    parts = []
                    for item in value:
                        if isinstance(item, str):
                            parts.append(item)
                        elif isinstance(item, dict):
                            text = item.get("text") or item.get("content")
                            if text:
                                parts.append(str(text))
                    return "\n".join(parts) if parts else None

        return None

    def _extract_timestamp(self, data: dict) -> Optional[datetime]:
        """Extrait le timestamp depuis différentes structures."""
        for key in ("timestamp", "ts", "time", "created_at", "date"):
            if key in data:
                ts = data[key]
                try:
                    if isinstance(ts, str):
                        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    elif isinstance(ts, (int, float)):
                        # Assume millisecondes si > 1e10
                        if ts > 1e10:
                            return datetime.fromtimestamp(ts / 1000)
                        return datetime.fromtimestamp(ts)
                except (ValueError, OSError):
                    continue
        return None
