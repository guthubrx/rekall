"""
Modèles de données pour le module transcript.

Contient les dataclasses pour représenter les messages de transcript,
les formats supportés et les échanges candidats pour le Mode 2.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal, Optional


class TranscriptFormat(str, Enum):
    """Formats de transcript supportés par Rekall."""

    CLAUDE_JSONL = "claude-jsonl"  # Claude Code CLI - format JSONL
    CLINE_JSON = "cline-json"  # Cline VS Code extension - format JSON
    CONTINUE_JSON = "continue-json"  # Continue.dev - format JSON
    RAW_JSON = "raw-json"  # Format JSON générique (fallback)
    # Formats prévus pour v2
    SQLITE = "sqlite"  # Cursor, Amazon Q
    LMDB = "lmdb"  # Zed IDE


@dataclass
class TranscriptMessage:
    """
    Message normalisé depuis n'importe quel format de transcript.

    Représente un échange unique (question ou réponse) dans une conversation.
    Le format est unifié quel que soit le CLI/IDE source.
    """

    role: Literal["human", "assistant"]
    content: str
    timestamp: Optional[datetime] = None
    index: int = 0  # Position dans le transcript original

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour réponse MCP."""
        # Tronque le contenu si trop long pour l'affichage
        truncated_content = (
            self.content[:500] + "..." if len(self.content) > 500 else self.content
        )
        return {
            "role": self.role,
            "content": truncated_content,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "index": self.index,
        }

    def full_content(self) -> str:
        """Retourne le contenu complet sans troncature."""
        return self.content


@dataclass
class CandidateExchanges:
    """
    Réponse Mode 2 - Échanges candidats pour filtrage par l'agent.

    Quand l'agent demande une extraction assistée (auto_capture_conversation: true),
    le système retourne cette structure avec les N derniers échanges.
    L'agent peut ensuite sélectionner les indices pertinents.
    """

    session_id: str  # ULID pour corrélation Mode 2 Step 1 → Step 2
    total_exchanges: int  # Nombre total d'échanges dans le transcript
    candidates: list[TranscriptMessage] = field(default_factory=list)  # Max 20
    transcript_path: str = ""
    transcript_format: TranscriptFormat = TranscriptFormat.RAW_JSON

    def to_mcp_response(self) -> dict:
        """Convertit en réponse MCP pour le Mode 2 Step 1."""
        return {
            "status": "candidates_ready",
            "session_id": self.session_id,
            "total_exchanges": self.total_exchanges,
            "candidates": [c.to_dict() for c in self.candidates],
            "instruction": (
                "Reply with conversation_excerpt_indices to select pertinent exchanges. "
                f"Example: conversation_excerpt_indices: [0, 2, 5] to select exchanges at indices 0, 2, and 5."
            ),
        }

    def get_by_indices(self, indices: list[int]) -> list[TranscriptMessage]:
        """
        Retourne les messages correspondant aux indices donnés.

        Args:
            indices: Liste d'indices (0-based) des candidats à sélectionner

        Returns:
            Liste des TranscriptMessage correspondants
        """
        result = []
        for idx in indices:
            # Cherche le candidat avec cet index
            for candidate in self.candidates:
                if candidate.index == idx:
                    result.append(candidate)
                    break
        return result

    def format_as_excerpt(self, indices: list[int]) -> str:
        """
        Formate les messages sélectionnés en texte pour conversation_excerpt.

        Args:
            indices: Liste d'indices (0-based) des candidats à inclure

        Returns:
            Texte formaté avec les échanges sélectionnés
        """
        if not indices:
            return ""

        messages = self.get_by_indices(indices)
        lines = []
        for msg in messages:
            role_label = "Human" if msg.role == "human" else "Assistant"
            lines.append(f"{role_label}: {msg.full_content()}")
        return "\n\n".join(lines)
