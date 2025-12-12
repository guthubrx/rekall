"""
Détection automatique du format de transcript et factory de parsers.

Ce module fournit les fonctions pour:
- Détecter automatiquement le format d'un fichier de transcript
- Obtenir le parser approprié pour un format donné
"""

from pathlib import Path
from typing import Optional

from rekall.transcript.models import TranscriptFormat
from rekall.transcript.parser_base import TranscriptParser
from rekall.transcript.parser_claude import ClaudeTranscriptParser
from rekall.transcript.parser_cline import ClineTranscriptParser
from rekall.transcript.parser_continue import ContinueTranscriptParser
from rekall.transcript.parser_generic import GenericJsonParser


# Mapping format → parser class
PARSER_REGISTRY: dict[TranscriptFormat, type[TranscriptParser]] = {
    TranscriptFormat.CLAUDE_JSONL: ClaudeTranscriptParser,
    TranscriptFormat.CLINE_JSON: ClineTranscriptParser,
    TranscriptFormat.CONTINUE_JSON: ContinueTranscriptParser,
    TranscriptFormat.RAW_JSON: GenericJsonParser,
}

# Patterns de chemin pour auto-détection (ordre important: plus spécifique d'abord)
PATH_PATTERNS: list[tuple[str, TranscriptFormat]] = [
    # Cline (doit être avant "claude" car le path contient "claude-dev")
    ("saoudrizwan.claude-dev", TranscriptFormat.CLINE_JSON),
    ("api_conversation_history", TranscriptFormat.CLINE_JSON),
    # Roo Code (même format que Cline)
    ("rooveterinaryinc.roo-cline", TranscriptFormat.CLINE_JSON),
    # Claude Code
    (".claude/projects", TranscriptFormat.CLAUDE_JSONL),
    # Continue.dev
    (".continue", TranscriptFormat.CONTINUE_JSON),
    ("dev_data", TranscriptFormat.CONTINUE_JSON),
]


def detect_format(
    path: Path,
    format_hint: Optional[str] = None,
) -> TranscriptFormat:
    """
    Détecte le format d'un fichier de transcript.

    Ordre de priorité:
    1. Format explicite fourni (format_hint)
    2. Patterns dans le chemin
    3. Extension du fichier
    4. Fallback: RAW_JSON

    Args:
        path: Chemin vers le fichier de transcript
        format_hint: Format explicite (ex: "claude-jsonl")

    Returns:
        TranscriptFormat détecté
    """
    # 1. Format explicite
    if format_hint:
        try:
            return TranscriptFormat(format_hint)
        except ValueError:
            pass  # Format invalide, continue avec auto-détection

    path_str = str(path).lower()

    # 2. Patterns dans le chemin (ordre important)
    for pattern, fmt in PATH_PATTERNS:
        if pattern.lower() in path_str:
            return fmt

    # 3. Extension du fichier
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        return TranscriptFormat.CLAUDE_JSONL
    elif suffix == ".json":
        # JSON peut être Cline, Continue ou Generic
        # On regarde le nom du fichier pour affiner
        name = path.name.lower()
        if "conversation" in name or "history" in name:
            return TranscriptFormat.CLINE_JSON
        return TranscriptFormat.RAW_JSON

    # 4. Fallback
    return TranscriptFormat.RAW_JSON


def get_parser(
    format: TranscriptFormat,
) -> TranscriptParser:
    """
    Factory pour obtenir un parser pour un format donné.

    Args:
        format: Format de transcript

    Returns:
        Instance du parser approprié

    Raises:
        ValueError: Si le format n'est pas supporté
    """
    parser_class = PARSER_REGISTRY.get(format)
    if not parser_class:
        raise ValueError(f"Unsupported transcript format: {format.value}")
    return parser_class()


def get_parser_for_path(
    path: Path,
    format_hint: Optional[str] = None,
) -> tuple[TranscriptParser, TranscriptFormat]:
    """
    Détecte le format et retourne le parser approprié.

    Combine detect_format() et get_parser() en une seule fonction.

    Args:
        path: Chemin vers le fichier de transcript
        format_hint: Format explicite optionnel

    Returns:
        Tuple (parser instance, format détecté)
    """
    format = detect_format(path, format_hint)
    parser = get_parser(format)
    return parser, format


def is_format_supported(format: str) -> bool:
    """
    Vérifie si un format est supporté.

    Args:
        format: Nom du format à vérifier

    Returns:
        True si le format est supporté
    """
    try:
        TranscriptFormat(format)
        return True
    except ValueError:
        return False


def get_supported_formats() -> list[str]:
    """
    Retourne la liste des formats supportés.

    Returns:
        Liste des noms de formats (ex: ["claude-jsonl", "cline-json", ...])
    """
    return [fmt.value for fmt in TranscriptFormat if fmt in PARSER_REGISTRY]
