"""
Module hooks - Configuration et gestion des hooks de rappel proactif.

Ce module fournit les structures de configuration pour les hooks
qui rappellent à l'agent de sauvegarder dans Rekall après résolution d'un problème.
"""

from rekall.hooks.models import HookConfig

__all__ = ["HookConfig"]
