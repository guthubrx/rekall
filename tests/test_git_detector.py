"""
Tests pour le module git_detector.

Tests couvrant:
- Détection repo Git (is_git_repo)
- Récupération fichiers modifiés (staged/unstaged)
- Récupération fichiers non trackés
- Filtrage fichiers binaires
- Filtrage chemins ignorés
- Gestion erreurs et timeouts
"""

import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rekall.git_detector import (
    BINARY_EXTENSIONS,
    IGNORE_PATTERNS,
    GitError,
    GitNotAvailable,
    GitTimeout,
    filter_binary_files,
    filter_ignored_paths,
    get_all_changes,
    get_modified_files,
    get_untracked_files,
    is_git_repo,
)


# ============================================================
# Tests: is_git_repo
# ============================================================


class TestIsGitRepo:
    """Tests pour la fonction is_git_repo."""

    def test_returns_true_for_git_repo(self, tmp_path: Path) -> None:
        """Retourne True pour un vrai repo Git."""
        # Créer un repo git
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

        assert is_git_repo(tmp_path) is True

    def test_returns_false_for_non_git_directory(self, tmp_path: Path) -> None:
        """Retourne False pour un dossier non-Git."""
        assert is_git_repo(tmp_path) is False

    def test_returns_false_for_nonexistent_directory(self) -> None:
        """Retourne False pour un dossier inexistant."""
        assert is_git_repo(Path("/nonexistent/path/12345")) is False

    def test_handles_timeout(self, tmp_path: Path) -> None:
        """Gère le timeout gracieusement."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 5)
            assert is_git_repo(tmp_path) is False

    def test_handles_git_not_found(self, tmp_path: Path) -> None:
        """Gère l'absence de git gracieusement."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            assert is_git_repo(tmp_path) is False

    def test_uses_cwd_by_default(self) -> None:
        """Utilise le répertoire courant par défaut."""
        # Le répertoire du projet devrait être un repo Git
        # On ne peut pas garantir ça dans tous les environnements
        # Donc on mocke pour tester le comportement
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            is_git_repo()
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            assert call_args[1]["cwd"] is None


# ============================================================
# Tests: get_modified_files
# ============================================================


class TestGetModifiedFiles:
    """Tests pour la fonction get_modified_files."""

    @pytest.fixture
    def git_repo(self, tmp_path: Path) -> Path:
        """Crée un repo Git avec quelques fichiers."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        # Créer et committer un fichier initial
        (tmp_path / "initial.txt").write_text("initial content")
        subprocess.run(["git", "add", "initial.txt"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=tmp_path,
            capture_output=True,
        )

        return tmp_path

    def test_returns_empty_for_clean_repo(self, git_repo: Path) -> None:
        """Retourne liste vide pour un repo propre."""
        files = get_modified_files(cwd=git_repo)
        assert files == []

    def test_detects_staged_files(self, git_repo: Path) -> None:
        """Détecte les fichiers staged."""
        # Modifier et stager un fichier
        (git_repo / "initial.txt").write_text("modified content")
        subprocess.run(["git", "add", "initial.txt"], cwd=git_repo, capture_output=True)

        files = get_modified_files(cwd=git_repo, include_staged=True, include_unstaged=False)
        assert "initial.txt" in files

    def test_detects_unstaged_files(self, git_repo: Path) -> None:
        """Détecte les fichiers modifiés non staged."""
        # Modifier sans stager
        (git_repo / "initial.txt").write_text("modified content")

        files = get_modified_files(cwd=git_repo, include_staged=False, include_unstaged=True)
        assert "initial.txt" in files

    def test_combines_staged_and_unstaged(self, git_repo: Path) -> None:
        """Combine staged et unstaged sans doublons."""
        # Créer deux fichiers
        (git_repo / "file1.txt").write_text("file1")
        (git_repo / "file2.txt").write_text("file2")
        subprocess.run(["git", "add", "file1.txt", "file2.txt"], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add files"], cwd=git_repo, capture_output=True)

        # Modifier les deux fichiers
        (git_repo / "file1.txt").write_text("file1 modified")
        (git_repo / "file2.txt").write_text("file2 modified")

        # Stager seulement file1
        subprocess.run(["git", "add", "file1.txt"], cwd=git_repo, capture_output=True)

        files = get_modified_files(cwd=git_repo)
        assert "file1.txt" in files
        assert "file2.txt" in files
        # Pas de doublons
        assert len(files) == len(set(files))

    def test_filters_binary_files_by_default(self, git_repo: Path) -> None:
        """Filtre les fichiers binaires par défaut."""
        # Créer un fichier PNG (binaire)
        (git_repo / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        subprocess.run(["git", "add", "image.png"], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add image"], cwd=git_repo, capture_output=True)

        # Modifier le fichier binaire
        (git_repo / "image.png").write_bytes(b"\x89PNG modified")

        files = get_modified_files(cwd=git_repo, filter_binary=True)
        assert "image.png" not in files

    def test_includes_binary_when_disabled(self, git_repo: Path) -> None:
        """Inclut les binaires si filtrage désactivé."""
        (git_repo / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        subprocess.run(["git", "add", "image.png"], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add image"], cwd=git_repo, capture_output=True)

        (git_repo / "image.png").write_bytes(b"\x89PNG modified")

        files = get_modified_files(cwd=git_repo, filter_binary=False)
        assert "image.png" in files

    def test_returns_sorted_list(self, git_repo: Path) -> None:
        """Retourne une liste triée alphabétiquement."""
        # Créer plusieurs fichiers
        for name in ["zebra.txt", "alpha.txt", "middle.txt"]:
            (git_repo / name).write_text(name)
        subprocess.run(["git", "add", "."], cwd=git_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add files"], cwd=git_repo, capture_output=True)

        # Modifier
        for name in ["zebra.txt", "alpha.txt", "middle.txt"]:
            (git_repo / name).write_text(f"{name} modified")

        files = get_modified_files(cwd=git_repo)
        assert files == sorted(files)

    def test_raises_for_non_git_repo(self, tmp_path: Path) -> None:
        """Lève GitNotAvailable pour un non-repo."""
        with pytest.raises(GitNotAvailable):
            get_modified_files(cwd=tmp_path)

    def test_raises_on_timeout(self, git_repo: Path) -> None:
        """Lève GitTimeout si l'opération dépasse le timeout."""
        with patch("rekall.git_detector._get_staged_files") as mock_staged:
            mock_staged.side_effect = subprocess.TimeoutExpired("git", 5)

            with pytest.raises(GitTimeout):
                get_modified_files(cwd=git_repo, timeout=5.0)

    def test_raises_if_git_not_found(self, git_repo: Path) -> None:
        """Lève GitNotAvailable si git n'est pas installé."""
        with patch("rekall.git_detector._get_staged_files") as mock_staged:
            mock_staged.side_effect = FileNotFoundError()

            with pytest.raises(GitNotAvailable):
                get_modified_files(cwd=git_repo)

    def test_accepts_string_path(self, git_repo: Path) -> None:
        """Accepte un chemin string en plus de Path."""
        (git_repo / "initial.txt").write_text("modified")

        files = get_modified_files(cwd=str(git_repo))
        assert "initial.txt" in files


# ============================================================
# Tests: get_untracked_files
# ============================================================


class TestGetUntrackedFiles:
    """Tests pour la fonction get_untracked_files."""

    @pytest.fixture
    def git_repo(self, tmp_path: Path) -> Path:
        """Crée un repo Git vide."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )
        # Commit initial pour avoir un repo valide
        (tmp_path / ".gitkeep").write_text("")
        subprocess.run(["git", "add", ".gitkeep"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=tmp_path,
            capture_output=True,
        )
        return tmp_path

    def test_detects_new_files(self, git_repo: Path) -> None:
        """Détecte les nouveaux fichiers non trackés."""
        (git_repo / "newfile.txt").write_text("new content")

        files = get_untracked_files(cwd=git_repo)
        assert "newfile.txt" in files

    def test_filters_binary_by_default(self, git_repo: Path) -> None:
        """Filtre les fichiers binaires par défaut."""
        (git_repo / "newimage.jpg").write_bytes(b"\xff\xd8\xff")

        files = get_untracked_files(cwd=git_repo, filter_binary=True)
        assert "newimage.jpg" not in files

    def test_returns_sorted(self, git_repo: Path) -> None:
        """Retourne une liste triée."""
        for name in ["z.txt", "a.txt", "m.txt"]:
            (git_repo / name).write_text("")

        files = get_untracked_files(cwd=git_repo)
        assert files == sorted(files)

    def test_respects_gitignore(self, git_repo: Path) -> None:
        """Respecte le .gitignore."""
        (git_repo / ".gitignore").write_text("*.log\n")
        subprocess.run(["git", "add", ".gitignore"], cwd=git_repo, capture_output=True)

        (git_repo / "debug.log").write_text("log content")
        (git_repo / "source.py").write_text("code")

        files = get_untracked_files(cwd=git_repo)
        assert "debug.log" not in files
        assert "source.py" in files

    def test_raises_for_non_repo(self, tmp_path: Path) -> None:
        """Lève GitNotAvailable pour non-repo."""
        with pytest.raises(GitNotAvailable):
            get_untracked_files(cwd=tmp_path)


# ============================================================
# Tests: filter_binary_files
# ============================================================


class TestFilterBinaryFiles:
    """Tests pour la fonction filter_binary_files."""

    def test_filters_image_extensions(self) -> None:
        """Filtre les extensions d'images."""
        files = ["code.py", "photo.png", "icon.jpg", "logo.gif", "style.css"]
        result = filter_binary_files(files)

        assert "code.py" in result
        assert "style.css" in result
        assert "photo.png" not in result
        assert "icon.jpg" not in result
        assert "logo.gif" not in result

    def test_filters_compiled_extensions(self) -> None:
        """Filtre les fichiers compilés."""
        files = ["main.py", "main.pyc", "lib.so", "app.exe"]
        result = filter_binary_files(files)

        assert "main.py" in result
        assert "main.pyc" not in result
        assert "lib.so" not in result
        assert "app.exe" not in result

    def test_filters_archives(self) -> None:
        """Filtre les archives."""
        files = ["data.json", "backup.zip", "package.tar.gz"]
        result = filter_binary_files(files)

        assert "data.json" in result
        assert "backup.zip" not in result
        # Note: .gz est filtré mais tar.gz a l'extension .gz
        assert "package.tar.gz" not in result

    def test_case_insensitive(self) -> None:
        """Filtrage insensible à la casse."""
        files = ["Photo.PNG", "ICON.JPG", "code.PY"]
        result = filter_binary_files(files)

        assert "code.PY" in result
        assert "Photo.PNG" not in result
        assert "ICON.JPG" not in result

    def test_handles_paths_with_directories(self) -> None:
        """Gère les chemins avec répertoires."""
        files = ["src/main.py", "assets/logo.png", "dist/bundle.js"]
        result = filter_binary_files(files)

        assert "src/main.py" in result
        assert "dist/bundle.js" in result
        assert "assets/logo.png" not in result

    def test_handles_empty_list(self) -> None:
        """Gère une liste vide."""
        assert filter_binary_files([]) == []

    def test_handles_no_extension(self) -> None:
        """Gère les fichiers sans extension."""
        files = ["Makefile", "Dockerfile", "README"]
        result = filter_binary_files(files)

        # Fichiers sans extension sont gardés
        assert "Makefile" in result
        assert "Dockerfile" in result
        assert "README" in result


# ============================================================
# Tests: filter_ignored_paths
# ============================================================


class TestFilterIgnoredPaths:
    """Tests pour la fonction filter_ignored_paths."""

    def test_filters_node_modules(self) -> None:
        """Filtre node_modules."""
        files = ["src/app.js", "node_modules/lodash/index.js"]
        result = filter_ignored_paths(files)

        assert "src/app.js" in result
        assert "node_modules/lodash/index.js" not in result

    def test_filters_pycache(self) -> None:
        """Filtre __pycache__."""
        files = ["main.py", "__pycache__/main.cpython-311.pyc"]
        result = filter_ignored_paths(files)

        assert "main.py" in result
        assert "__pycache__/main.cpython-311.pyc" not in result

    def test_filters_venv(self) -> None:
        """Filtre les environnements virtuels."""
        files = [
            "app.py",
            ".venv/lib/python3.11/site-packages/pip/__init__.py",
            "venv/bin/activate",
        ]
        result = filter_ignored_paths(files)

        assert "app.py" in result
        assert len(result) == 1

    def test_filters_git_directory(self) -> None:
        """Filtre le répertoire .git."""
        files = ["README.md", ".git/config", ".git/HEAD"]
        result = filter_ignored_paths(files)

        assert "README.md" in result
        assert len(result) == 1

    def test_filters_build_directories(self) -> None:
        """Filtre les répertoires de build."""
        files = [
            "src/index.ts",
            "dist/index.js",
            "build/app.js",
            ".next/static/chunks/main.js",
        ]
        result = filter_ignored_paths(files)

        assert "src/index.ts" in result
        assert len(result) == 1

    def test_handles_empty_list(self) -> None:
        """Gère une liste vide."""
        assert filter_ignored_paths([]) == []

    def test_keeps_similar_named_files(self) -> None:
        """Garde les fichiers avec des noms similaires mais pas dans des dossiers ignorés."""
        files = ["my_venv_config.txt", "node_modules_readme.md"]
        result = filter_ignored_paths(files)

        # Ces fichiers ne sont pas DANS les dossiers ignorés
        assert "my_venv_config.txt" in result
        assert "node_modules_readme.md" in result


# ============================================================
# Tests: get_all_changes
# ============================================================


class TestGetAllChanges:
    """Tests pour la fonction get_all_changes."""

    @pytest.fixture
    def git_repo(self, tmp_path: Path) -> Path:
        """Crée un repo Git avec fichiers."""
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
        )

        (tmp_path / "tracked.txt").write_text("tracked")
        subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=tmp_path,
            capture_output=True,
        )
        return tmp_path

    def test_returns_categorized_changes(self, git_repo: Path) -> None:
        """Retourne les changements catégorisés."""
        # Créer différents types de changements
        (git_repo / "tracked.txt").write_text("modified")  # unstaged
        (git_repo / "staged.txt").write_text("new staged")
        subprocess.run(["git", "add", "staged.txt"], cwd=git_repo, capture_output=True)
        (git_repo / "untracked.txt").write_text("new")  # untracked

        changes = get_all_changes(cwd=git_repo)

        assert "staged" in changes
        assert "unstaged" in changes
        assert "untracked" in changes

        assert "staged.txt" in changes["staged"]
        assert "tracked.txt" in changes["unstaged"]
        assert "untracked.txt" in changes["untracked"]

    def test_all_lists_sorted(self, git_repo: Path) -> None:
        """Toutes les listes sont triées."""
        for name in ["z.txt", "a.txt", "m.txt"]:
            (git_repo / name).write_text(name)

        changes = get_all_changes(cwd=git_repo)

        for key in ["staged", "unstaged", "untracked"]:
            assert changes[key] == sorted(changes[key])

    def test_filters_binary_by_default(self, git_repo: Path) -> None:
        """Filtre les binaires par défaut dans toutes les catégories."""
        (git_repo / "image.png").write_bytes(b"PNG")

        changes = get_all_changes(cwd=git_repo, filter_binary=True)

        assert "image.png" not in changes["untracked"]

    def test_raises_for_non_repo(self, tmp_path: Path) -> None:
        """Lève GitNotAvailable pour non-repo."""
        with pytest.raises(GitNotAvailable):
            get_all_changes(cwd=tmp_path)


# ============================================================
# Tests: Constantes
# ============================================================


class TestConstants:
    """Tests pour les constantes du module."""

    def test_binary_extensions_is_frozenset(self) -> None:
        """BINARY_EXTENSIONS est un frozenset immuable."""
        assert isinstance(BINARY_EXTENSIONS, frozenset)

    def test_binary_extensions_has_common_types(self) -> None:
        """BINARY_EXTENSIONS contient les types courants."""
        expected = {".png", ".jpg", ".pdf", ".zip", ".exe", ".pyc"}
        assert expected.issubset(BINARY_EXTENSIONS)

    def test_ignore_patterns_is_frozenset(self) -> None:
        """IGNORE_PATTERNS est un frozenset immuable."""
        assert isinstance(IGNORE_PATTERNS, frozenset)

    def test_ignore_patterns_has_common_dirs(self) -> None:
        """IGNORE_PATTERNS contient les dossiers courants."""
        expected = {"node_modules", ".git", "__pycache__", ".venv", "dist"}
        assert expected.issubset(IGNORE_PATTERNS)


# ============================================================
# Tests: Exceptions
# ============================================================


class TestExceptions:
    """Tests pour les exceptions du module."""

    def test_git_error_is_base(self) -> None:
        """GitError est l'exception de base."""
        assert issubclass(GitNotAvailable, GitError)
        assert issubclass(GitTimeout, GitError)

    def test_exceptions_can_have_message(self) -> None:
        """Les exceptions acceptent un message."""
        err1 = GitNotAvailable("Not a repo")
        err2 = GitTimeout("Timed out")

        assert str(err1) == "Not a repo"
        assert str(err2) == "Timed out"
