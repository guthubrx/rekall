"""
Détection automatique des fichiers modifiés via Git.

Ce module fournit les fonctions pour détecter les fichiers modifiés
dans un répertoire Git, avec support pour:
- Fichiers staged (git add)
- Fichiers unstaged (modifiés mais pas ajoutés)
- Filtrage des fichiers binaires
- Timeout pour éviter les blocages
"""

import subprocess
from pathlib import Path
from typing import Optional


class GitError(Exception):
    """Erreur lors d'une opération Git."""

    pass


class GitNotAvailable(GitError):
    """Git n'est pas disponible ou le répertoire n'est pas un repo."""

    pass


class GitTimeout(GitError):
    """Timeout lors d'une opération Git."""

    pass


# Extensions de fichiers binaires courants à filtrer
BINARY_EXTENSIONS = frozenset({
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".tiff", ".tif", ".psd", ".ai", ".eps",
    # Audio/Video
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv", ".flac", ".ogg",
    ".webm", ".m4a", ".m4v",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".7z", ".rar", ".xz",
    # Documents binaires
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    # Compilés
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".o", ".a", ".lib",
    ".class", ".jar", ".war",
    # Fonts
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
    # Databases
    ".db", ".sqlite", ".sqlite3", ".lmdb",
    # Autres
    ".bin", ".dat", ".lock", ".DS_Store",
})

# Patterns de fichiers/dossiers à ignorer
IGNORE_PATTERNS = frozenset({
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".env",
    "dist",
    "build",
    ".next",
    ".nuxt",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
})


def is_git_repo(cwd: Optional[Path] = None) -> bool:
    """
    Vérifie si le répertoire est un dépôt Git.

    Args:
        cwd: Répertoire à vérifier (défaut: répertoire courant)

    Returns:
        True si c'est un repo Git, False sinon
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            cwd=cwd,
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def get_modified_files(
    cwd: Optional[Path] = None,
    timeout: float = 5.0,
    include_staged: bool = True,
    include_unstaged: bool = True,
    filter_binary: bool = True,
) -> list[str]:
    """
    Récupère la liste des fichiers modifiés dans le repo Git.

    Combine les fichiers staged (git add) et unstaged pour donner
    une vue complète des modifications en cours.

    Args:
        cwd: Répertoire de travail (défaut: répertoire courant)
        timeout: Timeout en secondes (défaut: 5s)
        include_staged: Inclure les fichiers staged
        include_unstaged: Inclure les fichiers non staged
        filter_binary: Filtrer les fichiers binaires

    Returns:
        Liste dédupliquée des chemins relatifs des fichiers modifiés

    Raises:
        GitNotAvailable: Si git n'est pas disponible ou pas un repo
        GitTimeout: Si l'opération dépasse le timeout
    """
    if cwd is None:
        cwd = Path.cwd()
    elif isinstance(cwd, str):
        cwd = Path(cwd)

    # Vérifie que c'est un repo Git
    if not is_git_repo(cwd):
        raise GitNotAvailable(f"Not a git repository: {cwd}")

    modified_files: set[str] = set()

    try:
        # Fichiers staged (dans l'index, prêts à être committés)
        if include_staged:
            staged = _get_staged_files(cwd, timeout)
            modified_files.update(staged)

        # Fichiers unstaged (modifiés mais pas ajoutés)
        if include_unstaged:
            unstaged = _get_unstaged_files(cwd, timeout)
            modified_files.update(unstaged)

    except subprocess.TimeoutExpired:
        raise GitTimeout(f"Git operation timed out after {timeout}s")
    except FileNotFoundError:
        raise GitNotAvailable("Git command not found")

    # Filtrage
    result = list(modified_files)

    if filter_binary:
        result = filter_binary_files(result)

    result = filter_ignored_paths(result)

    # Tri alphabétique pour consistance
    result.sort()

    return result


def _get_staged_files(cwd: Path, timeout: float) -> list[str]:
    """Récupère les fichiers staged (git diff --cached --name-only)."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        return []

    return [f.strip() for f in result.stdout.splitlines() if f.strip()]


def _get_unstaged_files(cwd: Path, timeout: float) -> list[str]:
    """Récupère les fichiers modifiés non staged (git diff --name-only)."""
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        return []

    return [f.strip() for f in result.stdout.splitlines() if f.strip()]


def get_untracked_files(
    cwd: Optional[Path] = None,
    timeout: float = 5.0,
    filter_binary: bool = True,
) -> list[str]:
    """
    Récupère les fichiers non trackés (nouveaux fichiers).

    Args:
        cwd: Répertoire de travail
        timeout: Timeout en secondes
        filter_binary: Filtrer les fichiers binaires

    Returns:
        Liste des fichiers non trackés
    """
    if cwd is None:
        cwd = Path.cwd()
    elif isinstance(cwd, str):
        cwd = Path(cwd)

    if not is_git_repo(cwd):
        raise GitNotAvailable(f"Not a git repository: {cwd}")

    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode != 0:
            return []

        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]

        if filter_binary:
            files = filter_binary_files(files)

        files = filter_ignored_paths(files)
        files.sort()

        return files

    except subprocess.TimeoutExpired:
        raise GitTimeout(f"Git operation timed out after {timeout}s")
    except FileNotFoundError:
        raise GitNotAvailable("Git command not found")


def filter_binary_files(files: list[str]) -> list[str]:
    """
    Filtre les fichiers binaires basé sur l'extension.

    Args:
        files: Liste de chemins de fichiers

    Returns:
        Liste filtrée sans les fichiers binaires
    """
    result = []
    for f in files:
        ext = Path(f).suffix.lower()
        if ext not in BINARY_EXTENSIONS:
            result.append(f)
    return result


def filter_ignored_paths(files: list[str]) -> list[str]:
    """
    Filtre les fichiers dans des répertoires ignorés.

    Args:
        files: Liste de chemins de fichiers

    Returns:
        Liste filtrée sans les fichiers dans des dossiers ignorés
    """
    result = []
    for f in files:
        parts = Path(f).parts
        # Vérifie si un des composants du chemin est dans IGNORE_PATTERNS
        if not any(part in IGNORE_PATTERNS for part in parts):
            result.append(f)
    return result


def get_all_changes(
    cwd: Optional[Path] = None,
    timeout: float = 5.0,
    filter_binary: bool = True,
) -> dict[str, list[str]]:
    """
    Récupère tous les changements catégorisés.

    Args:
        cwd: Répertoire de travail
        timeout: Timeout en secondes
        filter_binary: Filtrer les fichiers binaires

    Returns:
        Dict avec clés 'staged', 'unstaged', 'untracked'
    """
    if cwd is None:
        cwd = Path.cwd()
    elif isinstance(cwd, str):
        cwd = Path(cwd)

    if not is_git_repo(cwd):
        raise GitNotAvailable(f"Not a git repository: {cwd}")

    staged = _get_staged_files(cwd, timeout)
    unstaged = _get_unstaged_files(cwd, timeout)

    try:
        untracked = get_untracked_files(cwd, timeout, filter_binary=False)
    except GitError:
        untracked = []

    if filter_binary:
        staged = filter_binary_files(staged)
        unstaged = filter_binary_files(unstaged)
        untracked = filter_binary_files(untracked)

    staged = filter_ignored_paths(staged)
    unstaged = filter_ignored_paths(unstaged)
    untracked = filter_ignored_paths(untracked)

    return {
        "staged": sorted(staged),
        "unstaged": sorted(unstaged),
        "untracked": sorted(untracked),
    }
