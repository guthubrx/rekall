"""
Parser pour les transcripts Claude Code (format JSONL).

Le format Claude Code stocke les conversations dans des fichiers JSONL
où chaque ligne est un objet JSON représentant un message.
"""

import json
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

from rekall.transcript.models import TranscriptFormat, TranscriptMessage
from rekall.transcript.parser_base import ParserError, TranscriptParser


class ClaudeTranscriptParser(TranscriptParser):
    """
    Parser pour le format JSONL de Claude Code CLI.

    Format attendu (une ligne JSON par message):
    {
        "type": "human" | "assistant",
        "message": {
            "content": [{"type": "text", "text": "..."}] | string,
            ...
        },
        "timestamp": "ISO8601" (optionnel)
    }

    Variante possible:
    {
        "role": "user" | "assistant",
        "content": "..." | [{"type": "text", "text": "..."}]
    }
    """

    @property
    def format(self) -> TranscriptFormat:
        return TranscriptFormat.CLAUDE_JSONL

    def parse(self, path: Path) -> list[TranscriptMessage]:
        """Parse le fichier JSONL complet."""
        if not path.exists():
            raise FileNotFoundError(f"Transcript not found: {path}")

        messages = []
        index = 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        msg = self._parse_message(data, index)
                        if msg:
                            messages.append(msg)
                            index += 1
                    except json.JSONDecodeError as e:
                        # Log warning mais continue le parsing
                        continue
                    except ValueError:
                        # Message invalide, skip
                        continue

        except IOError as e:
            raise ParserError(
                f"Failed to read transcript: {e}",
                path=path,
                format=self.format,
            )

        return messages

    def parse_last_n(
        self, path: Path, n: int = 20
    ) -> tuple[list[TranscriptMessage], int]:
        """
        Parse les N derniers messages en utilisant une deque pour limiter la mémoire.

        Pour les gros fichiers, cette méthode est plus efficace que parse()
        car elle ne garde que les N derniers éléments en mémoire.
        """
        if not path.exists():
            raise FileNotFoundError(f"Transcript not found: {path}")

        # Utilise une deque pour garder seulement les N derniers
        recent: deque[TranscriptMessage] = deque(maxlen=n)
        total_count = 0
        index = 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        msg = self._parse_message(data, index)
                        if msg:
                            recent.append(msg)
                            total_count += 1
                            index += 1
                    except (json.JSONDecodeError, ValueError):
                        continue

        except IOError as e:
            raise ParserError(
                f"Failed to read transcript: {e}",
                path=path,
                format=self.format,
            )

        return list(recent), total_count

    def _parse_message(self, data: dict, index: int) -> Optional[TranscriptMessage]:
        """
        Parse un objet JSON en TranscriptMessage.

        Gère les différentes variantes du format Claude.
        """
        # Extraction du rôle
        role = None
        if "type" in data:
            role = data["type"]
        elif "role" in data:
            role = data["role"]

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
        """Extrait le contenu textuel depuis différentes structures possibles."""
        # Structure: {"message": {"content": ...}}
        if "message" in data:
            msg = data["message"]
            if isinstance(msg, dict) and "content" in msg:
                return self._content_to_string(msg["content"])

        # Structure directe: {"content": ...}
        if "content" in data:
            return self._content_to_string(data["content"])

        # Structure: {"text": ...}
        if "text" in data:
            return str(data["text"])

        return None

    def _content_to_string(self, content) -> Optional[str]:
        """Convertit le contenu (string ou array) en string."""
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            # Format: [{"type": "text", "text": "..."}, ...]
            parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text" and "text" in item:
                        parts.append(item["text"])
                    elif "content" in item:
                        parts.append(str(item["content"]))
                elif isinstance(item, str):
                    parts.append(item)
            return "\n".join(parts) if parts else None

        return None

    def _extract_timestamp(self, data: dict) -> Optional[datetime]:
        """Extrait le timestamp si présent."""
        ts = data.get("timestamp") or data.get("created_at")
        if ts:
            try:
                return datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass
        return None
