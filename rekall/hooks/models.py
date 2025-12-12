"""
Modèles de configuration pour les hooks Rekall.

Contient la dataclass HookConfig pour configurer les hooks
de rappel proactif sur différents CLI/IDE.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


# CLI supportés pour l'installation des hooks
SupportedCLI = Literal["claude", "cline", "continue", "generic"]

# Types de hooks disponibles
HookType = Literal["stop", "post_tool_use"]


@dataclass
class HookConfig:
    """
    Configuration du hook de rappel proactif.

    Définit les paramètres pour installer et configurer un hook
    qui détecte les patterns de résolution et rappelle l'agent
    de sauvegarder dans Rekall.
    """

    cli: SupportedCLI
    hook_type: HookType = "stop"
    patterns: list[str] = field(default_factory=lambda: [
        r"bug.*résolu",
        r"fixed",
        r"corrigé",
        r"problème.*réglé",
        r"fonctionne.*maintenant",
        r"✅",
        r"resolved",
        r"issue.*fixed",
    ])
    cooldown_seconds: int = 300  # 5 min entre rappels
    enabled: bool = True

    # Chemins d'installation par CLI
    INSTALL_PATHS: dict[str, str] = field(default_factory=lambda: {
        "claude": "~/.claude/hooks/",
        "cline": "~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/hooks/",
        "continue": ".continue/hooks/",
        "generic": "~/.config/rekall/hooks/",
    })

    def get_install_path(self) -> Path:
        """Retourne le chemin d'installation pour le CLI configuré."""
        path_str = self.INSTALL_PATHS.get(self.cli, self.INSTALL_PATHS["generic"])
        return Path(path_str).expanduser()

    def get_hook_filename(self) -> str:
        """Retourne le nom du fichier hook selon le type."""
        if self.hook_type == "stop":
            return "rekall-reminder.sh"
        elif self.hook_type == "post_tool_use":
            return "rekall-post-tool.sh"
        return "rekall-hook.sh"

    def get_full_hook_path(self) -> Path:
        """Retourne le chemin complet du fichier hook."""
        return self.get_install_path() / self.get_hook_filename()

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour sérialisation."""
        return {
            "cli": self.cli,
            "hook_type": self.hook_type,
            "patterns": self.patterns,
            "cooldown_seconds": self.cooldown_seconds,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HookConfig":
        """Reconstruit depuis un dictionnaire."""
        return cls(
            cli=data["cli"],
            hook_type=data.get("hook_type", "stop"),
            patterns=data.get("patterns", []),
            cooldown_seconds=data.get("cooldown_seconds", 300),
            enabled=data.get("enabled", True),
        )

    @classmethod
    def for_claude(cls) -> "HookConfig":
        """Crée une configuration pour Claude Code."""
        return cls(cli="claude", hook_type="stop")

    @classmethod
    def for_cline(cls) -> "HookConfig":
        """Crée une configuration pour Cline."""
        return cls(cli="cline", hook_type="stop")

    @classmethod
    def for_continue(cls) -> "HookConfig":
        """Crée une configuration pour Continue.dev."""
        return cls(cli="continue", hook_type="stop")
