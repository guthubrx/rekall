"""
Interface abstraite pour les parsers de transcript.

Définit le contrat que tous les parsers doivent implémenter
pour extraire les messages depuis différents formats de transcript.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from rekall.transcript.models import TranscriptFormat, TranscriptMessage


class TranscriptParser(ABC):
    """
    Interface abstraite pour parser les fichiers de transcript.

    Chaque implémentation gère un format spécifique (JSONL, JSON, etc.)
    et produit une liste normalisée de TranscriptMessage.
    """

    @property
    @abstractmethod
    def format(self) -> TranscriptFormat:
        """Retourne le format géré par ce parser."""
        ...

    @abstractmethod
    def parse(self, path: Path) -> list[TranscriptMessage]:
        """
        Parse un fichier de transcript complet.

        Args:
            path: Chemin vers le fichier de transcript

        Returns:
            Liste de tous les messages dans l'ordre chronologique

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si le format est invalide ou corrompu
        """
        ...

    @abstractmethod
    def parse_last_n(
        self, path: Path, n: int = 20
    ) -> tuple[list[TranscriptMessage], int]:
        """
        Parse uniquement les N derniers échanges d'un transcript.

        Optimisé pour les gros fichiers - ne charge pas tout en mémoire.

        Args:
            path: Chemin vers le fichier de transcript
            n: Nombre d'échanges à extraire (défaut: 20)

        Returns:
            Tuple (liste des N derniers messages, nombre total d'échanges)

        Raises:
            FileNotFoundError: Si le fichier n'existe pas
            ValueError: Si le format est invalide ou corrompu
        """
        ...

    def validate(self, path: Path) -> bool:
        """
        Vérifie si le fichier est un transcript valide pour ce parser.

        Args:
            path: Chemin vers le fichier à valider

        Returns:
            True si le fichier semble valide pour ce parser
        """
        if not path.exists():
            return False
        try:
            # Essaie de parser les premiers éléments
            messages = self.parse_last_n(path, n=1)
            return len(messages[0]) >= 0  # Peut être vide mais valide
        except (ValueError, OSError):
            return False

    @staticmethod
    def normalize_role(role: str) -> str:
        """
        Normalise le rôle vers 'human' ou 'assistant'.

        Gère les variations: user, human, User → human
                            assistant, Assistant, bot → assistant

        Args:
            role: Rôle brut depuis le transcript

        Returns:
            'human' ou 'assistant'

        Raises:
            ValueError: Si le rôle n'est pas reconnu
        """
        role_lower = role.lower().strip()
        if role_lower in ("human", "user", "utilisateur"):
            return "human"
        elif role_lower in ("assistant", "bot", "ai", "claude"):
            return "assistant"
        else:
            raise ValueError(f"Unknown role: {role}")


class ParserError(Exception):
    """Exception levée lors d'erreurs de parsing."""

    def __init__(
        self,
        message: str,
        path: Optional[Path] = None,
        format: Optional[TranscriptFormat] = None,
    ):
        self.path = path
        self.format = format
        super().__init__(message)

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.path:
            parts.append(f"Path: {self.path}")
        if self.format:
            parts.append(f"Format: {self.format.value}")
        return " | ".join(parts)
