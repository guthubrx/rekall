"""
Gestionnaire de sessions temporaires pour le Mode 2 d'auto-capture.

Ce module gère les sessions éphémères utilisées lors du workflow en deux étapes:
- Step 1: L'agent demande les candidats → session créée avec CandidateExchanges
- Step 2: L'agent fournit les indices → session récupérée et finalisée

Les sessions expirent automatiquement après un délai configurable (défaut: 5 min).
"""

import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

from rekall.transcript.models import CandidateExchanges, TranscriptMessage


@dataclass
class SessionData:
    """Données stockées pour une session Mode 2."""

    session_id: str
    candidates: CandidateExchanges
    created_at: datetime = field(default_factory=datetime.now)
    # Métadonnées pour le Step 2
    entry_type: Optional[str] = None
    title: Optional[str] = None
    context: Optional[dict] = None
    tags: Optional[list[str]] = None
    project: Optional[str] = None
    confidence: int = 2

    def is_expired(self, ttl_seconds: int = 300) -> bool:
        """Vérifie si la session a expiré."""
        age = (datetime.now() - self.created_at).total_seconds()
        return age > ttl_seconds


class SessionManager:
    """
    Gestionnaire thread-safe des sessions temporaires Mode 2.

    Utilise un singleton pour maintenir les sessions entre les appels MCP.
    Les sessions sont nettoyées périodiquement via un thread de background.
    """

    _instance: Optional["SessionManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "SessionManager":
        """Singleton pattern pour partager les sessions."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self, ttl_seconds: int = 300, cleanup_interval: int = 60):
        """
        Initialise le gestionnaire.

        Args:
            ttl_seconds: Durée de vie des sessions (défaut: 5 min)
            cleanup_interval: Intervalle de nettoyage (défaut: 60s)
        """
        if self._initialized:
            return

        self._sessions: dict[str, SessionData] = {}
        self._sessions_lock = threading.Lock()
        self._ttl_seconds = ttl_seconds
        self._cleanup_interval = cleanup_interval
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        self._initialized = True

    def create_session(
        self,
        candidates: CandidateExchanges,
        entry_type: Optional[str] = None,
        title: Optional[str] = None,
        context: Optional[dict] = None,
        tags: Optional[list[str]] = None,
        project: Optional[str] = None,
        confidence: int = 2,
    ) -> str:
        """
        Crée une nouvelle session avec les candidats extraits.

        Args:
            candidates: CandidateExchanges extraits du transcript
            entry_type: Type de l'entrée (bug, pattern, etc.)
            title: Titre de l'entrée
            context: Contexte structuré
            tags: Tags de l'entrée
            project: Projet associé
            confidence: Niveau de confiance

        Returns:
            ID de session généré
        """
        session_id = str(uuid4())

        # Synchronise le session_id avec candidates
        candidates.session_id = session_id

        session = SessionData(
            session_id=session_id,
            candidates=candidates,
            entry_type=entry_type,
            title=title,
            context=context,
            tags=tags,
            project=project,
            confidence=confidence,
        )

        with self._sessions_lock:
            self._sessions[session_id] = session

        # Démarre le nettoyage si pas encore actif
        self._ensure_cleanup_running()

        return session_id

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Récupère une session par son ID.

        Args:
            session_id: ID de la session

        Returns:
            SessionData si trouvée et non expirée, None sinon
        """
        with self._sessions_lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if session.is_expired(self._ttl_seconds):
                del self._sessions[session_id]
                return None
            return session

    def delete_session(self, session_id: str) -> bool:
        """
        Supprime une session (après finalisation).

        Args:
            session_id: ID de la session

        Returns:
            True si supprimée, False si non trouvée
        """
        with self._sessions_lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False

    def get_selected_messages(
        self, session_id: str, indices: list[int]
    ) -> Optional[list[TranscriptMessage]]:
        """
        Récupère les messages sélectionnés par indices.

        Args:
            session_id: ID de la session
            indices: Liste des indices à récupérer

        Returns:
            Liste des messages sélectionnés, None si session non trouvée
        """
        session = self.get_session(session_id)
        if session is None:
            return None

        return session.candidates.get_by_indices(indices)

    def format_selected_as_excerpt(
        self, session_id: str, indices: list[int]
    ) -> Optional[str]:
        """
        Formate les messages sélectionnés en extrait de conversation.

        Args:
            session_id: ID de la session
            indices: Liste des indices à inclure

        Returns:
            Extrait formaté, None si session non trouvée
        """
        session = self.get_session(session_id)
        if session is None:
            return None

        return session.candidates.format_as_excerpt(indices)

    def _ensure_cleanup_running(self) -> None:
        """Démarre le thread de nettoyage si nécessaire."""
        if self._cleanup_thread is None or not self._cleanup_thread.is_alive():
            self._stop_cleanup.clear()
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_loop, daemon=True
            )
            self._cleanup_thread.start()

    def _cleanup_loop(self) -> None:
        """Boucle de nettoyage des sessions expirées."""
        while not self._stop_cleanup.is_set():
            self._cleanup_expired()
            time.sleep(self._cleanup_interval)

    def _cleanup_expired(self) -> None:
        """Supprime toutes les sessions expirées."""
        with self._sessions_lock:
            expired = [
                sid
                for sid, session in self._sessions.items()
                if session.is_expired(self._ttl_seconds)
            ]
            for sid in expired:
                del self._sessions[sid]

    def stop_cleanup(self) -> None:
        """Arrête le thread de nettoyage (pour les tests)."""
        self._stop_cleanup.set()
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=1)

    def clear_all(self) -> None:
        """Vide toutes les sessions (pour les tests)."""
        with self._sessions_lock:
            self._sessions.clear()

    @property
    def session_count(self) -> int:
        """Nombre de sessions actives."""
        with self._sessions_lock:
            return len(self._sessions)


# Singleton global pour accès facile
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Obtient l'instance singleton du SessionManager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
