"""
Module transcript - Parsing et extraction de conversations depuis différents IDE/CLI.

Ce module fournit les parsers pour extraire les conversations depuis les fichiers
de transcript de différents IDE supportant MCP (Claude Code, Cline, Continue.dev, etc.)

Exports publics:
- TranscriptFormat: Enum des formats supportés
- TranscriptMessage: Message normalisé depuis n'importe quel format
- CandidateExchanges: Réponse Mode 2 avec échanges candidats
- TranscriptParser: Interface abstraite pour les parsers
- ClaudeTranscriptParser: Parser JSONL Claude Code
- ClineTranscriptParser: Parser JSON Cline
- ContinueTranscriptParser: Parser JSON Continue.dev
- GenericJsonParser: Parser JSON générique (fallback)
- detect_format: Détection automatique du format
- get_parser: Factory pour obtenir le bon parser
"""

from rekall.transcript.models import (
    TranscriptFormat,
    TranscriptMessage,
    CandidateExchanges,
)
from rekall.transcript.parser_base import TranscriptParser
from rekall.transcript.parser_claude import ClaudeTranscriptParser
from rekall.transcript.parser_cline import ClineTranscriptParser
from rekall.transcript.parser_continue import ContinueTranscriptParser
from rekall.transcript.parser_generic import GenericJsonParser
from rekall.transcript.detector import detect_format, get_parser, get_parser_for_path
from rekall.transcript.session_manager import (
    SessionManager,
    SessionData,
    get_session_manager,
)

__all__ = [
    # Models
    "TranscriptFormat",
    "TranscriptMessage",
    "CandidateExchanges",
    # Parser interface
    "TranscriptParser",
    # Parser implementations
    "ClaudeTranscriptParser",
    "ClineTranscriptParser",
    "ContinueTranscriptParser",
    "GenericJsonParser",
    # Factory functions
    "detect_format",
    "get_parser",
    "get_parser_for_path",
    # Session management (Mode 2)
    "SessionManager",
    "SessionData",
    "get_session_manager",
]
