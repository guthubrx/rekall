"""IDE/Agent integration templates for Rekall."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable


# =============================================================================
# Data Models for Multi-IDE Integration (Feature 019)
# =============================================================================


class Scope(Enum):
    """Installation scope for IDE integrations."""

    GLOBAL = "global"  # ~/.{ide}/
    LOCAL = "local"  # ./{ide}/ (project-local)


class Article99Version(Enum):
    """Article 99 version levels for Speckit constitution."""

    MICRO = "micro"  # ~50 tokens - when skill is installed
    SHORT = "short"  # ~350 tokens - when MCP is configured
    EXTENSIVE = "extensive"  # ~1000 tokens - CLI only


@dataclass
class IDE:
    """Represents a supported IDE with its configuration."""

    id: str  # e.g., "claude", "cursor"
    name: str  # e.g., "Claude Code", "Cursor"
    priority: int  # Lower = higher priority (1=Claude, 2=Cursor, etc.)
    local_marker: str  # e.g., ".claude", ".cursor"
    global_marker: str | None  # e.g., ".claude" or None if no global support
    supports_mcp: bool = True
    supports_hooks: bool = False  # Only Claude has hooks


@dataclass
class DetectedIDE:
    """Result of IDE detection."""

    ide: IDE | None  # None if no IDE detected
    scope: Scope | None = None  # Where it was detected
    path: Path | None = None  # Path where marker was found


@dataclass
class Article99Config:
    """Configuration for Article 99 recommendation."""

    recommended: Article99Version
    reason: str  # Human-readable reason for recommendation
    current: Article99Version | None = None  # Currently installed version


@dataclass
class IntegrationStatus:
    """Status of an IDE integration."""

    ide: IDE
    global_installed: bool = False
    local_installed: bool = False
    mcp_configured: bool = False
    hooks_configured: bool = False


# =============================================================================
# Supported IDEs Configuration
# =============================================================================

SUPPORTED_IDES: list[IDE] = [
    IDE(
        id="claude",
        name="Claude Code",
        priority=1,
        local_marker=".claude",
        global_marker=".claude",
        supports_mcp=True,
        supports_hooks=True,
    ),
    IDE(
        id="cursor",
        name="Cursor",
        priority=2,
        local_marker=".cursor",
        global_marker=None,  # Cursor is local-only
        supports_mcp=True,
        supports_hooks=False,
    ),
    IDE(
        id="copilot",
        name="GitHub Copilot",
        priority=3,
        local_marker=".github",
        global_marker=None,
        supports_mcp=True,
        supports_hooks=False,
    ),
    IDE(
        id="windsurf",
        name="Windsurf",
        priority=4,
        local_marker=".windsurf",
        global_marker=None,
        supports_mcp=False,  # Uses .windsurfrules only
        supports_hooks=False,
    ),
    IDE(
        id="cline",
        name="Cline",
        priority=5,
        local_marker=".cline",
        global_marker=None,
        supports_mcp=True,
        supports_hooks=False,
    ),
    IDE(
        id="zed",
        name="Zed",
        priority=6,
        local_marker=".zed",
        global_marker=".config/zed",
        supports_mcp=True,
        supports_hooks=False,
    ),
    IDE(
        id="continue",
        name="Continue.dev",
        priority=7,
        local_marker=".continue",
        global_marker=".continue",
        supports_mcp=True,
        supports_hooks=False,
    ),
]

# Quick lookup by ID
_IDE_BY_ID: dict[str, IDE] = {ide.id: ide for ide in SUPPORTED_IDES}


def get_ide_by_id(ide_id: str) -> IDE | None:
    """Get IDE by its ID."""
    return _IDE_BY_ID.get(ide_id)


# =============================================================================
# IDE Detection
# =============================================================================


def detect_ide(base_path: Path) -> DetectedIDE:
    """Detect the primary IDE for a project.

    Detection priority:
    1. Local markers (in base_path) - sorted by IDE priority
    2. Global markers (in home) - sorted by IDE priority

    Args:
        base_path: Project directory to check for local markers

    Returns:
        DetectedIDE with the highest-priority detected IDE, or ide=None if none found
    """
    # Check local first (higher priority than global)
    for ide in sorted(SUPPORTED_IDES, key=lambda x: x.priority):
        local_path = base_path / ide.local_marker
        if local_path.exists():
            return DetectedIDE(ide=ide, scope=Scope.LOCAL, path=local_path)

    # Then check global
    home = Path.home()
    for ide in sorted(SUPPORTED_IDES, key=lambda x: x.priority):
        if ide.global_marker:
            global_path = home / ide.global_marker
            if global_path.exists():
                return DetectedIDE(ide=ide, scope=Scope.GLOBAL, path=global_path)

    return DetectedIDE(ide=None)


def get_all_detected_ides(base_path: Path) -> list[tuple[IDE, Scope]]:
    """Get all detected IDEs with their scopes.

    Args:
        base_path: Project directory to check

    Returns:
        List of (IDE, Scope) tuples, sorted by IDE priority
    """
    detected: list[tuple[IDE, Scope]] = []
    home = Path.home()

    for ide in sorted(SUPPORTED_IDES, key=lambda x: x.priority):
        # Check local
        local_path = base_path / ide.local_marker
        if local_path.exists():
            detected.append((ide, Scope.LOCAL))

        # Check global
        if ide.global_marker:
            global_path = home / ide.global_marker
            if global_path.exists():
                detected.append((ide, Scope.GLOBAL))

    return detected


# =============================================================================
# Registry of available integrations (legacy format)
# =============================================================================

# Registry of available integrations
# Format: name -> (installer_function, description, local_target, global_target or None)
INTEGRATIONS: dict[str, tuple[Callable[[Path, bool], Path], str, str, str | None]] = {}


def register(name: str, description: str, local_target: str, global_target: str | None = None):
    """Decorator to register an integration.

    Args:
        name: Integration name
        description: Human-readable description
        local_target: Path for local (project) installation
        global_target: Path for global (home) installation, or None if not supported
    """
    def decorator(func: Callable[[Path, bool], Path]):
        INTEGRATIONS[name] = (func, description, local_target, global_target)
        return func
    return decorator


def get_available() -> list[tuple[str, str, str, str | None]]:
    """Get list of available integrations.

    Returns:
        List of (name, description, local_target, global_target) tuples.
        Local paths are prefixed with './' to indicate project-local installation.
        global_target is None if global installation not supported.
    """
    result = []
    for name, (_, desc, local_target, global_target) in INTEGRATIONS.items():
        # Add ./ prefix for local paths
        local_display = f"./{local_target}" if not local_target.startswith("~") else local_target
        result.append((name, desc, local_display, global_target))
    return result


def supports_global(name: str) -> bool:
    """Check if an integration supports global installation."""
    if name not in INTEGRATIONS:
        return False
    _, _, _, global_target = INTEGRATIONS[name]
    return global_target is not None


def get_integration_files(name: str, base_path: Path, global_install: bool = False) -> list[dict]:
    """Get list of files that would be installed for an integration.

    Returns a list of dicts with:
    - path: Target file path (str)
    - content: File content (str)
    - description: Short description of the file
    - exists: Whether file already exists

    Args:
        name: Integration name
        base_path: Base path for local installation
        global_install: If True, return global paths

    Returns:
        List of file info dicts
    """
    if name not in INTEGRATIONS:
        return []

    files = []

    if name == "claude":
        # Claude has progressive disclosure structure + hooks + settings.json
        if global_install:
            commands_dir = Path.home() / ".claude" / "commands"
            hooks_dir = Path.home() / ".claude" / "hooks"
            settings_path = Path.home() / ".claude" / "settings.json"
        else:
            commands_dir = base_path / ".claude" / "commands"
            hooks_dir = base_path / ".claude" / "hooks"
            settings_path = base_path / ".claude" / "settings.json"

        rekall_dir = commands_dir / "rekall"

        # Main skill file (~200 tokens, loaded when triggered)
        rekall_path = commands_dir / "rekall.md"
        files.append({
            "path": str(rekall_path),
            "content": REKALL_SKILL_MAIN,
            "description": "/rekall - Main skill (~200 tokens)",
            "exists": rekall_path.exists(),
        })

        # Progressive disclosure reference files (loaded on demand)
        files.append({
            "path": str(rekall_dir / "consultation.md"),
            "content": REKALL_SKILL_CONSULTATION,
            "description": "rekall/ - Search workflow (on demand)",
            "exists": (rekall_dir / "consultation.md").exists(),
        })
        files.append({
            "path": str(rekall_dir / "capture.md"),
            "content": REKALL_SKILL_CAPTURE,
            "description": "rekall/ - Capture workflow (on demand)",
            "exists": (rekall_dir / "capture.md").exists(),
        })
        files.append({
            "path": str(rekall_dir / "linking.md"),
            "content": REKALL_SKILL_LINKING,
            "description": "rekall/ - Knowledge graph (on demand)",
            "exists": (rekall_dir / "linking.md").exists(),
        })
        files.append({
            "path": str(rekall_dir / "commands.md"),
            "content": REKALL_SKILL_COMMANDS,
            "description": "rekall/ - CLI reference (on demand)",
            "exists": (rekall_dir / "commands.md").exists(),
        })

        # Hook 1: rekall-webfetch.sh (PostToolUse)
        hook_path = hooks_dir / "rekall-webfetch.sh"
        hook_content = _get_webfetch_hook_content()
        files.append({
            "path": str(hook_path),
            "content": hook_content,
            "description": "WebFetch hook - Auto-capture URLs",
            "exists": hook_path.exists(),
        })

        # Hook 2: rekall-reminder.sh (Stop)
        reminder_hook_path = hooks_dir / "rekall-reminder.sh"
        reminder_hook_content = _get_reminder_hook_content()
        files.append({
            "path": str(reminder_hook_path),
            "content": reminder_hook_content,
            "description": "Stop hook - Rappel sauvegarde Rekall",
            "exists": reminder_hook_path.exists(),
        })

        # Settings.json hook config (show what will be added)
        hook_config = '''{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "WebFetch",
        "hooks": [{"type": "command", "command": "<hooks_dir>/rekall-webfetch.sh"}]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [{"type": "command", "command": "<hooks_dir>/rekall-reminder.sh"}]
      }
    ]
  }
}'''
        files.append({
            "path": str(settings_path),
            "content": hook_config.replace("<hooks_dir>", str(hooks_dir)),
            "description": "settings.json - Hook configuration (merged)",
            "exists": settings_path.exists(),
        })

    elif name == "speckit":
        # Speckit: article + patches
        constitution_path = Path.home() / ".speckit" / "constitution.md"
        files.append({
            "path": str(constitution_path),
            "content": ARTICLE_99_CONTENT,
            "description": "Article XCIX - Rekall integration",
            "exists": constitution_path.exists() and "XCIX. Rekall" in constitution_path.read_text() if constitution_path.exists() else False,
        })

        # Show which files would be patched
        claude_dir = Path.home() / ".claude" / "commands"
        for filename, (search_term, types, _) in SPECKIT_PATCHES.items():
            filepath = claude_dir / filename
            if filepath.exists():
                section = _make_rekall_section(search_term, types)
                files.append({
                    "path": str(filepath),
                    "content": section,
                    "description": f"Patch: {filename}",
                    "exists": "Consultation Rekall" in filepath.read_text() if filepath.exists() else False,
                })

    else:
        # Standard single-file integrations
        _, _, local_target, global_target = INTEGRATIONS[name]

        if global_install and global_target:
            target_path = Path.home() / global_target[2:]  # Remove ~/
        else:
            target_path = base_path / local_target

        # Generate content by calling the installer in dry-run mode
        # For now, we'll generate a preview based on the template
        content = _generate_integration_preview(name)

        files.append({
            "path": str(target_path),
            "content": content,
            "description": INTEGRATIONS[name][1],  # Use the description
            "exists": target_path.exists(),
        })

    return files


def _get_webfetch_hook_content() -> str:
    """Return the content of rekall-webfetch.sh hook."""
    # Try to read from package data
    try:
        from importlib.resources import files
        hook_source = files("rekall.data.hooks").joinpath("rekall-webfetch.sh")
        return hook_source.read_text()
    except Exception:
        pass

    # Fallback: read from source tree
    dev_path = Path(__file__).parent.parent / "data" / "hooks" / "rekall-webfetch.sh"
    if dev_path.exists():
        return dev_path.read_text()

    # Ultimate fallback: return a placeholder
    return '''#!/bin/bash
# Rekall WebFetch Hook - Captures URLs from WebFetch tool calls
# Adds URLs to Rekall inbox for later processing

URL="$TOOL_INPUT_URL"
if [ -n "$URL" ]; then
    rekall inbox add "$URL" --source webfetch 2>/dev/null || true
fi
'''


def _get_reminder_hook_content() -> str:
    """Return the content of rekall-reminder.sh hook."""
    # Try to read from package data
    try:
        from importlib.resources import files
        hook_source = files("rekall.data.hooks").joinpath("rekall-reminder.sh")
        return hook_source.read_text()
    except Exception:
        pass

    # Fallback: read from source tree
    dev_path = Path(__file__).parent.parent / "data" / "hooks" / "rekall-reminder.sh"
    if dev_path.exists():
        return dev_path.read_text()

    # Ultimate fallback: return a placeholder
    return '''#!/bin/bash
# Rekall Reminder Hook - Detects resolution patterns and reminds to save
# Triggered on Stop event in Claude Code

PAYLOAD=$(cat)
TRANSCRIPT_PATH=$(echo "$PAYLOAD" | jq -r '.transcript_path // empty')

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# Check for resolution patterns in last response
LAST_RESPONSE=$(tail -20 "$TRANSCRIPT_PATH" | jq -s '[.[] | select(.type == "assistant")] | last | .content // empty')

if echo "$LAST_RESPONSE" | grep -qiE "(fixed|resolu|corrected|working now)"; then
    if ! echo "$LAST_RESPONSE" | grep -qi "rekall"; then
        echo "---"
        echo "**Rekall Reminder**: Pense a sauvegarder avec /rekall"
    fi
fi
'''


def _generate_integration_preview(name: str) -> str:
    """Generate preview content for a standard integration."""
    if name == "cursor":
        return f"# Cursor Rules - Rekall Integration\\n{REKALL_INSTRUCTIONS[:500]}..."
    elif name == "copilot":
        return f"# GitHub Copilot Instructions\\n{REKALL_INSTRUCTIONS[:500]}..."
    elif name == "windsurf":
        return f"# Windsurf Rules\\n{REKALL_INSTRUCTIONS[:500]}..."
    elif name == "cline":
        return f"# Cline Rules\\n{REKALL_INSTRUCTIONS[:500]}..."
    elif name == "aider":
        return "# Aider Configuration\\nauto-commits: true\\n..."
    elif name == "continue":
        return '{"customCommands": [...], "docs": [...]}'
    elif name == "zed":
        return '{"assistant": {"context": "Rekall instructions..."}}'
    elif name == "gemini":
        return f"# Gemini CLI\\n{REKALL_INSTRUCTIONS[:500]}..."
    elif name == "cursor-agent":
        return "---\\ndescription: Rekall integration\\nglobs: [\"**/*\"]\\n---\\n..."
    elif name == "qwen":
        return f"# Qwen Code\\n{REKALL_INSTRUCTIONS[:500]}..."
    elif name == "opencode":
        return f"# OpenCode\\n{REKALL_INSTRUCTIONS[:500]}..."
    else:
        return f"# {name.title()} Integration\\nRekall knowledge management..."


def install(name: str, base_path: Path, global_install: bool = False) -> Path:
    """Install an integration.

    Args:
        name: Integration name
        base_path: Base path for installation (usually cwd)
        global_install: If True and supported, install globally

    Returns:
        Path to created file

    Raises:
        ValueError: If integration not found or global not supported
    """
    if name not in INTEGRATIONS:
        available = ", ".join(INTEGRATIONS.keys())
        raise ValueError(f"Unknown integration '{name}'. Available: {available}")

    installer, _, _, global_target = INTEGRATIONS[name]

    if global_install and global_target is None:
        raise ValueError(f"Integration '{name}' does not support global installation")

    return installer(base_path, global_install)


def get_ide_status(base_path: Path) -> dict[str, dict]:
    """Get installation status of each IDE integration.

    Args:
        base_path: Base path to check (usually cwd)

    Returns:
        Dict mapping integration name to status dict:
        {
            "local": True/False (installed locally),
            "global": True/False/None (installed globally, None if not supported),
            "supports_global": bool
        }
    """
    status = {}

    for name, (_, _, local_target, global_target) in INTEGRATIONS.items():
        # Skip speckit - it has its own detailed status
        if name == "speckit":
            continue

        # Check local installation
        local_path = base_path / local_target
        local_installed = local_path.exists()

        # Check global installation (if supported)
        if global_target:
            global_path = Path.home() / global_target[2:]  # Remove ~/
            global_installed = global_path.exists()
        else:
            global_installed = None

        status[name] = {
            "local": local_installed,
            "global": global_installed,
            "supports_global": global_target is not None
        }

    return status


def get_ide_target_path(name: str, base_path: Path, global_install: bool = False) -> Path:
    """Get the target file path for an IDE integration.

    Args:
        name: Integration name
        base_path: Base path (usually cwd)
        global_install: If True, return global path

    Returns:
        Path to the integration file
    """
    if name not in INTEGRATIONS:
        raise ValueError(f"Unknown integration: {name}")

    _, _, local_target, global_target = INTEGRATIONS[name]

    if global_install:
        if global_target is None:
            raise ValueError(f"Integration '{name}' does not support global installation")
        return Path.home() / global_target[2:]  # Remove ~/
    else:
        return base_path / local_target


def uninstall_ide(name: str, base_path: Path, global_install: bool = False) -> bool:
    """Uninstall an IDE integration by removing its file(s).

    Args:
        name: Integration name
        base_path: Base path (usually cwd)
        global_install: If True and supported, uninstall from global location

    Returns:
        True if file(s) were removed, False if nothing existed
    """
    # Special handling for Claude - has multiple files
    if name == "claude":
        return _uninstall_claude(base_path, global_install)

    target = get_ide_target_path(name, base_path, global_install)

    if target.exists():
        target.unlink()
        # Clean up empty parent directories (but not .cursor, .github, etc.)
        parent = target.parent
        if parent.name in ("rules", "commands") and not any(parent.iterdir()):
            parent.rmdir()
        return True
    return False


def _uninstall_claude(base_path: Path, global_install: bool = False) -> bool:
    """Uninstall Claude Code integration completely.

    Removes:
    - ~/.claude/commands/rekall.md (or rekall*.md)
    - ~/.claude/commands/rekall/ directory (progressive disclosure files)
    - ~/.claude/hooks/rekall-*.sh
    - Hook entries from ~/.claude/settings.json

    Args:
        base_path: Base path (usually cwd)
        global_install: If True, uninstall from global location

    Returns:
        True if any files were removed
    """
    import json
    import shutil

    removed_any = False

    if global_install:
        commands_dir = Path.home() / ".claude" / "commands"
        hooks_dir = Path.home() / ".claude" / "hooks"
        settings_path = Path.home() / ".claude" / "settings.json"
    else:
        commands_dir = base_path / ".claude" / "commands"
        hooks_dir = base_path / ".claude" / "hooks"
        settings_path = base_path / ".claude" / "settings.json"

    # Remove rekall*.md commands (rekall.md, rekall.save.md, rekall.enrich.md)
    if commands_dir.exists():
        for f in commands_dir.glob("rekall*.md"):
            f.unlink()
            removed_any = True

        # Remove rekall/ directory (progressive disclosure reference files)
        rekall_dir = commands_dir / "rekall"
        if rekall_dir.exists() and rekall_dir.is_dir():
            shutil.rmtree(rekall_dir)
            removed_any = True

    # Remove rekall-*.sh hooks
    if hooks_dir.exists():
        for f in hooks_dir.glob("rekall-*.sh"):
            f.unlink()
            removed_any = True

    # Remove hook entries from settings.json
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
            modified = False

            if "hooks" in settings:
                # Remove PostToolUse WebFetch hook
                if "PostToolUse" in settings["hooks"]:
                    original_len = len(settings["hooks"]["PostToolUse"])
                    settings["hooks"]["PostToolUse"] = [
                        h for h in settings["hooks"]["PostToolUse"]
                        if "rekall" not in str(h.get("hooks", [])).lower()
                    ]
                    if len(settings["hooks"]["PostToolUse"]) < original_len:
                        modified = True
                    if not settings["hooks"]["PostToolUse"]:
                        del settings["hooks"]["PostToolUse"]

                # Remove Stop hook
                if "Stop" in settings["hooks"]:
                    original_len = len(settings["hooks"]["Stop"])
                    settings["hooks"]["Stop"] = [
                        h for h in settings["hooks"]["Stop"]
                        if "rekall" not in str(h.get("hooks", [])).lower()
                    ]
                    if len(settings["hooks"]["Stop"]) < original_len:
                        modified = True
                    if not settings["hooks"]["Stop"]:
                        del settings["hooks"]["Stop"]

                # Clean up empty hooks object
                if not settings["hooks"]:
                    del settings["hooks"]

            if modified:
                settings_path.write_text(json.dumps(settings, indent=2))
                removed_any = True

        except (json.JSONDecodeError, KeyError):
            pass  # Ignore malformed settings.json

    return removed_any


def install_all_ide(base_path: Path, global_install: bool = False) -> dict:
    """Install all IDE integrations (except speckit).

    Args:
        base_path: Base path for installation
        global_install: If True, install globally where supported

    Returns:
        Dict with installed and failed lists
    """
    results = {"installed": [], "failed": [], "skipped_no_global": []}

    for name in INTEGRATIONS.keys():
        if name == "speckit":
            continue

        # Skip if requesting global but integration doesn't support it
        if global_install and not supports_global(name):
            results["skipped_no_global"].append(name)
            continue

        try:
            install(name, base_path, global_install)
            results["installed"].append(name)
        except Exception as e:
            results["failed"].append(f"{name}: {e}")

    return results


def uninstall_all_ide(base_path: Path, global_install: bool = False) -> dict:
    """Uninstall all IDE integrations (except speckit).

    Args:
        base_path: Base path
        global_install: If True, uninstall from global location where supported

    Returns:
        Dict with removed and skipped lists
    """
    results = {"removed": [], "skipped": []}

    for name in INTEGRATIONS.keys():
        if name == "speckit":
            continue

        # Skip if requesting global but integration doesn't support it
        if global_install and not supports_global(name):
            continue

        if uninstall_ide(name, base_path, global_install):
            results["removed"].append(name)
        else:
            results["skipped"].append(name)

    return results


# =============================================================================
# Shared Content - Rekall Instructions
# =============================================================================

REKALL_INSTRUCTIONS = """
## Rekall - Developer Knowledge Management

This project uses Rekall for capturing and retrieving development knowledge.

### Available Commands

- `rekall search "query"` - Search for bugs, patterns, decisions
- `rekall add <type> "title"` - Add new knowledge entry
- `rekall show <id>` - Show entry details
- `rekall browse` - List all entries
- `rekall export backup.rekall.zip` - Export knowledge base
- `rekall import backup.rekall.zip` - Import from archive

### Entry Types

| Type | When to use |
|------|-------------|
| `bug` | Bug fixed, error resolved |
| `pattern` | Reusable code, best practice |
| `decision` | Architecture choice, trade-off |
| `pitfall` | Mistake to avoid, anti-pattern |
| `config` | Configuration snippet, setup |
| `reference` | External doc, useful link |

### Workflow

**Before solving a problem**, search existing knowledge:
```bash
rekall search "error message or topic"
```

**After solving a problem**, capture the knowledge:
```bash
echo "## Problem
Description of the issue...

## Solution
How it was fixed...

## Why
Explanation of root cause..." | rekall add bug "Fix: description" -t tag1,tag2 -p project-name -c 3
```
"""


# =============================================================================
# WebFetch Hook Installation Helper
# =============================================================================


def _install_webfetch_hook() -> bool:
    """Install WebFetch hook for automatic URL capture in Claude Code.

    This hook captures URLs from WebFetch tool calls and adds them to the
    Rekall inbox for later processing.

    Returns:
        True if hook was installed/updated, False if already configured
    """
    import json

    # Step 1: Install hook script
    hook_dest = Path.home() / ".claude" / "hooks" / "rekall-webfetch.sh"

    try:
        # Try to get hook from package resources
        try:
            from importlib.resources import files
            hook_source = files("rekall.data.hooks").joinpath("rekall-webfetch.sh")
            hook_content = hook_source.read_text()
        except Exception:
            # Fallback for development: read from source tree
            dev_path = Path(__file__).parent.parent / "data" / "hooks" / "rekall-webfetch.sh"
            if dev_path.exists():
                hook_content = dev_path.read_text()
            else:
                # Hook script not found - skip installation
                return False

        # Create hooks directory and write script
        hook_dest.parent.mkdir(parents=True, exist_ok=True)
        hook_dest.write_text(hook_content)
        hook_dest.chmod(0o755)

    except Exception:
        return False

    # Step 2: Configure Claude settings.json
    settings_path = Path.home() / ".claude" / "settings.json"

    try:
        if settings_path.exists():
            settings = json.loads(settings_path.read_text())
        else:
            settings = {}

        # Check if hook already configured
        hooks = settings.get("hooks", {})
        post_tool_use = hooks.get("PostToolUse", [])

        # Check if our hook is already there
        hook_already_exists = any(
            h.get("matcher") == "WebFetch" and
            any("rekall-webfetch" in hh.get("command", "") for hh in h.get("hooks", []))
            for h in post_tool_use
        )

        if hook_already_exists:
            return False

        # Add our hook configuration
        new_hook = {
            "matcher": "WebFetch",
            "hooks": [
                {
                    "type": "command",
                    "command": str(hook_dest)
                }
            ]
        }
        post_tool_use.append(new_hook)
        hooks["PostToolUse"] = post_tool_use
        settings["hooks"] = hooks

        # Write back settings
        settings_path.write_text(json.dumps(settings, indent=2))
        return True

    except Exception:
        return False


# =============================================================================
# Integration Installers
# =============================================================================

@register("cursor", "Cursor AI rules", ".cursorrules", None)
def install_cursor(base_path: Path, global_install: bool = False) -> Path:
    """Install Cursor integration (.cursorrules)."""
    content = f"""# Cursor Rules - Rekall Integration

## Knowledge Management
{REKALL_INSTRUCTIONS}

### Cursor-Specific Instructions

When helping with code:
1. First search for existing solutions: `rekall search "topic"`
2. After solving issues, suggest capturing with `rekall add`
3. Reference relevant entries by ID when applicable
"""

    target = base_path / ".cursorrules"
    target.write_text(content)
    return target


@register("claude", "Claude Code skill + hooks", ".claude/commands/rekall.md", "~/.claude/commands/rekall.md")
def install_claude(base_path: Path, global_install: bool = False) -> Path:
    """Install Claude Code integration (skill /rekall + WebFetch & Stop hooks).

    Installs progressive disclosure structure:
    - rekall.md (main skill ~200 tokens, loaded when triggered)
    - rekall/consultation.md (search workflow, loaded on demand)
    - rekall/capture.md (save workflow, loaded on demand)
    - rekall/linking.md (knowledge graph, loaded on demand)
    - rekall/commands.md (CLI reference, loaded on demand)
    """

    # Install /rekall skill with progressive disclosure
    if global_install:
        claude_dir = Path.home() / ".claude" / "commands"
    else:
        claude_dir = base_path / ".claude" / "commands"

    claude_dir.mkdir(parents=True, exist_ok=True)

    # Create rekall subdirectory for reference files
    rekall_dir = claude_dir / "rekall"
    rekall_dir.mkdir(parents=True, exist_ok=True)

    # Install main skill file (loaded when triggered, ~200 tokens)
    rekall_skill_path = claude_dir / "rekall.md"
    rekall_skill_path.write_text(REKALL_SKILL_MAIN)

    # Install reference files (loaded on demand via progressive disclosure)
    (rekall_dir / "consultation.md").write_text(REKALL_SKILL_CONSULTATION)
    (rekall_dir / "capture.md").write_text(REKALL_SKILL_CAPTURE)
    (rekall_dir / "linking.md").write_text(REKALL_SKILL_LINKING)
    (rekall_dir / "commands.md").write_text(REKALL_SKILL_COMMANDS)

    # Install WebFetch hook for automatic URL capture (Feature 013)
    _install_webfetch_hook()

    # Install Claude hooks (Feature 018)
    _install_claude_hooks(base_path, global_install)

    return rekall_skill_path


def _install_claude_hooks(base_path: Path, global_install: bool) -> None:
    """Install Rekall hooks for Claude Code.

    Installs:
    - rekall-webfetch.sh (PostToolUse hook for URL capture)
    - rekall-reminder.sh (Stop hook for save reminder)

    Also updates settings.json with hook configuration.

    Args:
        base_path: Project base path for local install
        global_install: If True, install to ~/.claude/, else to .claude/
    """
    import json
    import shutil

    # Determine paths based on install type
    if global_install:
        hooks_dir = Path.home() / ".claude" / "hooks"
        settings_path = Path.home() / ".claude" / "settings.json"
    else:
        hooks_dir = base_path / ".claude" / "hooks"
        settings_path = base_path / ".claude" / "settings.json"

    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Source hooks from package
    source_dir = Path(__file__).parent.parent / "data" / "hooks"

    # Install webfetch hook
    webfetch_source = source_dir / "rekall-webfetch.sh"
    webfetch_dest = hooks_dir / "rekall-webfetch.sh"

    if webfetch_source.exists():
        shutil.copy2(webfetch_source, webfetch_dest)
        webfetch_dest.chmod(0o755)

    # Install reminder hook (Stop hook)
    reminder_source = source_dir / "rekall-reminder.sh"
    reminder_dest = hooks_dir / "rekall-reminder.sh"

    if reminder_source.exists():
        shutil.copy2(reminder_source, reminder_dest)
        reminder_dest.chmod(0o755)

    # Update settings.json with hook configuration
    settings = {}

    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text())
        except json.JSONDecodeError:
            settings = {}

    hooks_config = settings.get("hooks", {})

    # Configure PostToolUse hook (WebFetch capture)
    post_tool_use = hooks_config.get("PostToolUse", [])
    webfetch_hook_exists = any(
        h.get("matcher") == "WebFetch" and
        any("rekall-webfetch" in hh.get("command", "") for hh in h.get("hooks", []))
        for h in post_tool_use
    )
    if not webfetch_hook_exists:
        post_tool_use.append({
            "matcher": "WebFetch",
            "hooks": [{"type": "command", "command": str(webfetch_dest)}]
        })
        hooks_config["PostToolUse"] = post_tool_use

    # Configure Stop hook (reminder)
    stop_hooks = hooks_config.get("Stop", [])
    reminder_hook_exists = any(
        any("rekall-reminder" in hh.get("command", "") for hh in h.get("hooks", []))
        for h in stop_hooks
    )
    if not reminder_hook_exists:
        stop_hooks.append({
            "matcher": "",
            "hooks": [{"type": "command", "command": str(reminder_dest)}]
        })
        hooks_config["Stop"] = stop_hooks

    settings["hooks"] = hooks_config

    # Write updated settings
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2))


@register("copilot", "GitHub Copilot instructions", ".github/copilot-instructions.md", None)
def install_copilot(base_path: Path, global_install: bool = False) -> Path:
    """Install GitHub Copilot integration."""
    content = f"""# GitHub Copilot Instructions - Rekall Integration
{REKALL_INSTRUCTIONS}

### Copilot Guidelines

When generating code suggestions:
- Consider searching Rekall for existing patterns: `rekall search "topic"`
- Suggest capturing new patterns discovered during development
- Reference entry IDs when applicable
"""

    github_dir = base_path / ".github"
    github_dir.mkdir(parents=True, exist_ok=True)

    target = github_dir / "copilot-instructions.md"
    target.write_text(content)
    return target


@register("windsurf", "Windsurf AI rules", ".windsurfrules", None)
def install_windsurf(base_path: Path, global_install: bool = False) -> Path:
    """Install Windsurf integration."""
    content = f"""# Windsurf Rules - Rekall Integration
{REKALL_INSTRUCTIONS}

### Windsurf Guidelines

- Search before solving: `rekall search "error or topic"`
- Capture after fixing: `rekall add bug "Fix description"`
"""

    target = base_path / ".windsurfrules"
    target.write_text(content)
    return target


@register("cline", "Cline AI rules", ".clinerules", None)
def install_cline(base_path: Path, global_install: bool = False) -> Path:
    """Install Cline integration."""
    content = f"""# Cline Rules - Rekall Integration
{REKALL_INSTRUCTIONS}

### Cline Guidelines

- Search before solving: `rekall search "error or topic"`
- Capture after fixing: `rekall add bug "Fix description"`
"""

    target = base_path / ".clinerules"
    target.write_text(content)
    return target


@register("aider", "Aider conventions", ".aider.conf.yml", None)
def install_aider(base_path: Path, global_install: bool = False) -> Path:
    """Install Aider integration."""
    content = """# Aider Configuration - Rekall Integration
#
# Rekall Commands:
# - rekall search "query" - Search knowledge base
# - rekall add <type> "title" - Add entry
# - rekall browse - List all entries
#
# Before working on issues, search: rekall search "topic"
# After fixing bugs, capture: rekall add bug "description"

# Aider settings
auto-commits: true
"""

    target = base_path / ".aider.conf.yml"
    target.write_text(content)
    return target


@register("continue", "Continue.dev config", ".continue/config.json", None)
def install_continue(base_path: Path, global_install: bool = False) -> Path:
    """Install Continue.dev integration."""
    import json

    config = {
        "customCommands": [
            {
                "name": "rekall-search",
                "description": "Search Rekall knowledge base",
                "prompt": "Search Rekall with: rekall search \"{{{input}}}\""
            },
            {
                "name": "rekall-save",
                "description": "Save knowledge to Rekall",
                "prompt": "Capture this knowledge with rekall add"
            }
        ],
        "docs": [
            {
                "title": "Rekall",
                "description": "Developer knowledge management",
                "content": REKALL_INSTRUCTIONS
            }
        ]
    }

    continue_dir = base_path / ".continue"
    continue_dir.mkdir(parents=True, exist_ok=True)

    target = continue_dir / "config.json"
    target.write_text(json.dumps(config, indent=2))
    return target


@register("zed", "Zed AI assistant context", ".zed/settings.json", None)
def install_zed(base_path: Path, global_install: bool = False) -> Path:
    """Install Zed integration."""
    import json

    config = {
        "assistant": {
            "default_model": {
                "provider": "anthropic",
                "model": "claude-sonnet-4-20250514"
            },
            "context": f"""
Rekall - Developer Knowledge Management:
{REKALL_INSTRUCTIONS}
"""
        }
    }

    zed_dir = base_path / ".zed"
    zed_dir.mkdir(parents=True, exist_ok=True)

    target = zed_dir / "settings.json"
    target.write_text(json.dumps(config, indent=2))
    return target


@register("gemini", "Gemini CLI context", "GEMINI.md", "~/.gemini/GEMINI.md")
def install_gemini(base_path: Path, global_install: bool = False) -> Path:
    """Install Gemini CLI integration (GEMINI.md)."""
    content = f"""# Gemini CLI - Rekall Integration
{REKALL_INSTRUCTIONS}

## Gemini-Specific Instructions

When helping with code in this project:
1. First search for existing solutions: `rekall search "topic"`
2. After solving issues, suggest capturing with `rekall add`
3. Reference relevant entries by ID when applicable

Use `/memory add` to save important context to your global memory.
"""

    if global_install:
        gemini_dir = Path.home() / ".gemini"
        gemini_dir.mkdir(parents=True, exist_ok=True)
        target = gemini_dir / "GEMINI.md"
    else:
        target = base_path / "GEMINI.md"

    target.write_text(content)
    return target


@register("cursor-agent", "Cursor Agent rules (.mdc)", ".cursor/rules/rekall.mdc", None)
def install_cursor_agent(base_path: Path, global_install: bool = False) -> Path:
    """Install Cursor Agent integration (.cursor/rules/rekall.mdc)."""
    content = f"""---
description: Rekall knowledge management integration
globs: ["**/*"]
alwaysApply: true
---

# Rekall - Developer Knowledge Management
{REKALL_INSTRUCTIONS}

## Cursor Agent Instructions

When working on this project:
1. Search existing knowledge before implementing: `rekall search "topic"`
2. After fixing bugs or discovering patterns, suggest capturing with `rekall add`
3. Reference entry IDs when applicable
"""

    cursor_rules_dir = base_path / ".cursor" / "rules"
    cursor_rules_dir.mkdir(parents=True, exist_ok=True)

    target = cursor_rules_dir / "rekall.mdc"
    target.write_text(content)
    return target


@register("qwen", "Qwen Code context", "QWEN.md", "~/.qwen/QWEN.md")
def install_qwen(base_path: Path, global_install: bool = False) -> Path:
    """Install Qwen Code integration (QWEN.md)."""
    content = f"""# Qwen Code - Rekall Integration
{REKALL_INSTRUCTIONS}

## Qwen-Specific Instructions

When helping with code in this project:
1. First search for existing solutions: `rekall search "topic"`
2. After solving issues, suggest capturing with `rekall add`
3. Reference relevant entries by ID when applicable
"""

    if global_install:
        qwen_dir = Path.home() / ".qwen"
        qwen_dir.mkdir(parents=True, exist_ok=True)
        target = qwen_dir / "QWEN.md"
    else:
        target = base_path / "QWEN.md"

    target.write_text(content)
    return target


@register("opencode", "opencode AGENTS.md", "AGENTS.md", "~/.config/opencode/AGENTS.md")
def install_opencode(base_path: Path, global_install: bool = False) -> Path:
    """Install opencode integration (AGENTS.md)."""
    content = f"""# OpenCode - Rekall Integration
{REKALL_INSTRUCTIONS}

## OpenCode Instructions

When working on this project:
1. Search existing knowledge before implementing: `rekall search "topic"`
2. After fixing bugs or discovering patterns, suggest capturing with `rekall add`
3. Use `@general` for complex searches across the codebase
4. Reference entry IDs when applicable
"""

    if global_install:
        opencode_dir = Path.home() / ".config" / "opencode"
        opencode_dir.mkdir(parents=True, exist_ok=True)
        target = opencode_dir / "AGENTS.md"
    else:
        target = base_path / "AGENTS.md"

    target.write_text(content)
    return target


# =============================================================================
# Speckit Integration (Complex - multiple files)
# =============================================================================

# =============================================================================
# Rekall Skill - Progressive Disclosure Structure (SOTA)
# =============================================================================
# Main skill file (~200 tokens) + reference files loaded on demand
# Structure:
#   rekall.md           - Main routing + principles (loaded when triggered)
#   rekall/
#     consultation.md   - Search workflow details
#     capture.md        - Save workflow details
#     linking.md        - Knowledge graph features
#     commands.md       - Full CLI reference

REKALL_SKILL_MAIN = '''---
name: rekall
description: Searches and captures developer knowledge (bugs, patterns, decisions). Use when starting tasks to find existing solutions, or after solving problems to save knowledge. Triggers on bug fixes, debugging, architecture decisions, and pattern discovery.
---

# Rekall - Developer Knowledge Memory

## Routing: $ARGUMENTS

| Argument | Action |
|----------|--------|
| _(empty)_ | Extract keywords from conversation → search |
| `help` | Show quick reference below, then STOP |
| `save` | Go to capture workflow → See [capture.md](rekall/capture.md) |
| `search <query>` | Search with provided query |

---

## Core Principle

1. **Search BEFORE** acting → find existing solutions
2. **Capture AFTER** solving → document for future

---

## Quick Reference (`/rekall help`)

**Commands:** `/rekall` (search) | `/rekall save` (capture) | `/rekall search <query>`

**Types:** `bug` | `pattern` | `decision` | `pitfall` | `config` | `reference`

```bash
rekall search "query"      # Search knowledge base
rekall add bug "title"     # Add entry
rekall show <id>           # Show details
```

---

## Workflows

**Searching knowledge:** See [consultation.md](rekall/consultation.md)
- Keyword extraction, JSON format, presentation to user

**Capturing knowledge:** See [capture.md](rekall/capture.md)
- Auto-generation of title/tags/type, proposal format, execution

**Knowledge graph:** See [linking.md](rekall/linking.md)
- Link types, generalization, memory types

**Full CLI reference:** See [commands.md](rekall/commands.md)
'''

REKALL_SKILL_CONSULTATION = '''# Consultation Workflow

## When to Search

**BEFORE** starting any bug fix, feature, or refactor, search Rekall:

| Context | Command |
|---------|---------|
| Bug fix | `rekall search "bug KEYWORDS" --json --limit 5` |
| Feature | `rekall search "pattern KEYWORDS" --json --limit 5` |
| Decision | `rekall search "decision KEYWORDS" --json --limit 5` |

## Keyword Extraction

Extract from user request:
- Technologies (Python, React, SQLite...)
- File/module names
- Error messages
- Technical concepts

## JSON Response Format

```json
{
  "results": [{
    "id": "01HXYZ...",
    "type": "bug",
    "title": "Timeout auth API",
    "relevance_score": 0.85,
    "tags": ["auth", "api"],
    "links": {"outgoing": [...], "incoming": [...]}
  }],
  "total_count": 3
}
```

## Presentation to User

**With results** - Use inline citations:

```
🧠 Rekall: 3 relevant entries

Based on "Timeout auth API" [1], the 5s default timeout is
insufficient. Recommended solution from "Retry backoff pattern" [2]
is exponential retry.

---
[1] 01HXYZ - bug - Timeout auth API
[2] 01HABC - pattern - Retry backoff pattern
```

**No results:**

```
🧠 Rekall: No knowledge found for "new-topic"

Proceeding without historical context.
💡 Will propose capture if useful knowledge emerges.
```

## Relevance Scoring

- `> 0.7` : Full detail in response
- `0.4 - 0.7` : Summary only
- `< 0.4` : Don\'t mention
'''

REKALL_SKILL_CAPTURE = '''# Capture Workflow

## When to Capture

**AFTER** solving a problem, propose capture:

| Event | Suggested Type |
|-------|----------------|
| Bug fixed | `bug` |
| Technical decision | `decision` |
| Pattern discovered | `pattern` |
| Pitfall avoided | `pitfall` |
| Config found | `config` |
| Useful web reference | `reference` |

## Auto-Generation

**Title** (max 60 chars): "Verb + Object + Context"
- Examples: "Fix timeout auth API Python", "Pattern retry with backoff"

**Tags** (2-5, kebab-case): technologies, concepts, module names

**Memory Type:**
- `episodic` (default): Specific event, particular bug
- `semantic`: Reusable pattern, general best practice

## Proposal Format

```
💾 Knowledge detected

Proposing to save:

**Title**: Fix auth API timeout - increase to 30s
**Type**: bug
**Tags**: auth, api, timeout, python
**Confidence**: 4/5

Content:
---
## Problem
5s timeout insufficient for auth API in production.

## Solution
Increase timeout to 30s in config.py line 42.
---

Options:
1. ✅ Save as-is
2. ✏️ Modify before saving
3. ❌ Don\'t save
```

## Execution

```bash
echo "MARKDOWN_CONTENT" | rekall add TYPE "TITLE" \\
  -p PROJECT -t TAGS --memory-type episodic -c CONFIDENCE
```

## Rules

1. **Propose ONCE only** - If refused, don\'t re-propose in same session
2. **Check first** - Search for similar existing entries
3. **Skip trivial** - Simple questions, typos, basic commands
4. **Default confidence**: 3/5
'''

REKALL_SKILL_LINKING = '''# Knowledge Graph & Linking

## After Creating an Entry

Propose linking if similar entries exist:

```
🔗 Related entries detected

Your new entry could link to:

1. [type] "Title" (SHORT_ID)
   → Similarity: X% (reason)

Create links?
- [1] Link as "related"
- [2] Link as "derived_from"
- [3] Skip
```

## Link Types

| Type | Usage |
|------|-------|
| `related` | Thematic connection |
| `supersedes` | Replaces obsolete entry |
| `derived_from` | Generalized from episodics |
| `contradicts` | Conflicting information |

```bash
rekall link SOURCE_ID TARGET_ID --type related
rekall related ENTRY_ID  # View links
```

## Memory Types

| Type | Usage |
|------|-------|
| `episodic` | Specific event (bug, incident) - default |
| `semantic` | General concept (pattern, best practice) |

## Generalization

When 3+ similar episodic entries exist:

```
💡 Generalization opportunity

3 similar episodic entries on "TOPIC":
- ID1 "Title 1"
- ID2 "Title 2"
- ID3 "Title 3"

Generalize to semantic pattern?
→ `rekall generalize ID1 ID2 ID3`
```
'''

REKALL_SKILL_COMMANDS = '''# Rekall CLI Reference

## Search

```bash
rekall search "query"                    # Full-text search
rekall search "q" --type bug             # Filter by type
rekall search "q" --memory-type semantic # Filter by memory type
rekall search "q" --json --limit 5       # JSON output for processing
```

## Add Entries

```bash
rekall add <type> "title"                         # Interactive add
rekall add bug "title" -t tag1,tag2 -p project   # With tags/project
rekall add pattern "title" --memory-type semantic # Semantic memory

# Pipe content
echo "## Problem\\n..." | rekall add bug "title" -c 4
```

## Entry Types

`bug` | `pattern` | `decision` | `pitfall` | `config` | `reference`

## Links

```bash
rekall link ID1 ID2 --type related    # Create link
rekall unlink ID1 ID2                 # Remove link
rekall related ID                     # View connections
rekall similar ID                     # Find similar entries
```

## Knowledge Graph

```bash
rekall generalize ID1 ID2 ID3         # Create semantic from episodics
rekall stale                          # Entries not accessed recently
rekall info                           # Database statistics
```

## Browse & Export

```bash
rekall show <id>                      # Entry details
rekall browse                         # Interactive TUI
rekall export backup.rekall.zip       # Export database
rekall import backup.rekall.zip       # Import database
```

## MCP Server

```bash
rekall mcp                            # Start MCP server (stdio)
rekall config                         # Open configuration TUI
```

MCP tools: `rekall_search` | `rekall_add` | `rekall_show` | `rekall_link` | `rekall_related` | `rekall_similar` | `rekall_info` | `rekall_stale` | `rekall_generalize`
'''

# Legacy alias for backward compatibility (will be removed)
REKALL_SKILL = REKALL_SKILL_MAIN


# =============================================================================
# Article 99 Versions (Feature 019)
# =============================================================================

# Version micro de l'article 99 (~50 tokens) - quand skill installée
ARTICLE_99_MICRO = '''---

## XCIX. Rekall

**Mémoire cognitive persistante.** Utilise `/rekall` pour consulter et `/rekall save` pour capturer.
'''

# Version courte de l'article 99 (~350 tokens) - RECOMMANDEE
ARTICLE_99_SHORT = '''
---

## Memoire Developpeur Persistante

### XCIX. Rekall - Memoire Cognitive (OPTIONNEL)

**Rekall** = memoire cognitive persistante cross-projets. Utiliser `/rekall help` pour aide complete.

#### Principe
- **Consulter AVANT** → `/rekall` ou `rekall search "query"`
- **Capturer APRES** → `/rekall save` ou `rekall add <type> "titre"`

#### Types d'Entrees
`bug` | `pattern` | `decision` | `pitfall` | `config` | `reference`

#### Commandes Essentielles
```bash
rekall search "query"       # Rechercher
rekall add bug "titre"      # Ajouter
rekall show <id>            # Details
rekall browse               # TUI interactive
```

#### Integration Claude Code
- `/rekall` : Recherche contextuelle
- `/rekall save` : Capture immediate
- `/rekall help` : Aide complete

'''

# Version extensive de l'article 99 (~1000 tokens)
ARTICLE_99_EXTENSIVE = '''
---

## Memoire Developpeur Persistante

### XCIX. Rekall - Memoire Cognitive (OPTIONNEL)

**Rekall** est un systeme de memoire cognitive persistante cross-projets avec knowledge graph et serveur MCP.

#### 1. Principe

- **Consulter AVANT** d'agir - chercher les connaissances existantes
- **Capturer APRES** avoir resolu - documenter les solutions
- **Lier** les connaissances - construire un graphe de savoir
- **Generaliser** les patterns - transformer l'episodique en semantique

#### 2. Types d'Entrees

| Type | Usage |
|------|-------|
| `bug` | Bug resolu, erreur corrigee |
| `pattern` | Code reutilisable, best practice |
| `decision` | Choix technique, trade-off |
| `pitfall` | Piege a eviter, anti-pattern |
| `config` | Configuration, setup |
| `reference` | Doc externe, lien utile |

#### 3. Types de Memoire

| Type | Usage |
|------|-------|
| `episodic` | Evenement specifique (bug, incident) - defaut |
| `semantic` | Concept general (pattern, best practice) |

#### 4. Commandes CLI

**Recherche:** `rekall search "query"` | `--type bug` | `--memory-type semantic`

**Ajout:** `rekall add <type> "titre"` | `rekall link ID1 ID2` | `rekall generalize ID1 ID2 ID3`

**Exploration:** `rekall show <id>` | `rekall related <id>` | `rekall browse`

**Maintenance:** `rekall stale` | `rekall info` | `rekall export backup.zip`

#### 5. Types de Liens

`related` (thematique) | `supersedes` (remplace) | `derived_from` (generalise) | `contradicts` (conflit)

#### 6. Serveur MCP

Outils MCP: `rekall_help` | `rekall_search` | `rekall_add` | `rekall_show` | `rekall_link` | `rekall_related` | `rekall_similar` | `rekall_info` | `rekall_stale` | `rekall_generalize`

Config: `rekall` → Configuration → Installation MCP

#### 7. Integration Claude Code

**Skill `/rekall`:** `/rekall` (recherche) | `/rekall save` (capture) | `/rekall help` (aide)

**Hooks:** WebFetch (capture URLs) | Stop (rappel sauvegarde)

#### 8. Workflow

1. Debut → `/rekall` consulter
2. Travail → URLs capturees auto
3. Fin → `/rekall save` documenter
4. Consolider → `rekall generalize`

'''

# Alias par defaut (version courte recommandee)
ARTICLE_99_CONTENT = ARTICLE_99_SHORT

# Map version enum to content
_ARTICLE_99_VERSIONS: dict[Article99Version, str] = {
    Article99Version.MICRO: ARTICLE_99_MICRO,
    Article99Version.SHORT: ARTICLE_99_SHORT,
    Article99Version.EXTENSIVE: ARTICLE_99_EXTENSIVE,
}


def get_article99_recommendation(base_path: Path) -> Article99Config:
    """Get recommended Article 99 version based on installed integrations.

    Recommendation logic:
    - MICRO (~50 tokens): Claude skill is installed (full /rekall access)
    - SHORT (~350 tokens): MCP is configured but no skill
    - EXTENSIVE (~1000 tokens): CLI only, no IDE integration

    Args:
        base_path: Project directory for context

    Returns:
        Article99Config with recommended version and reason
    """
    home = Path.home()

    # Check for Claude skill (highest integration level)
    skill_path = home / ".claude" / "commands" / "rekall.md"
    if skill_path.exists():
        return Article99Config(
            recommended=Article99Version.MICRO,
            reason="Skill /rekall installée - instructions complètes disponibles via skill",
        )

    # Check for MCP configuration
    # Claude MCP
    claude_mcp = home / ".claude" / "settings.json"
    # Cursor MCP
    cursor_mcp = base_path / ".cursor" / "mcp.json"

    if claude_mcp.exists() or cursor_mcp.exists():
        return Article99Config(
            recommended=Article99Version.SHORT,
            reason="MCP configuré - accès aux outils rekall_*",
        )

    # Fallback: CLI only
    return Article99Config(
        recommended=Article99Version.EXTENSIVE,
        reason="CLI seulement - instructions complètes nécessaires",
    )


def install_article99(version: Article99Version) -> bool:
    """Install or update Article 99 in Speckit constitution.

    Args:
        version: Article99Version to install (MICRO, SHORT, or EXTENSIVE)

    Returns:
        True if installation succeeded, False if speckit directory doesn't exist
    """
    import re

    constitution_path = Path.home() / ".speckit" / "constitution.md"

    if not constitution_path.parent.exists():
        return False

    content = _ARTICLE_99_VERSIONS[version]

    if not constitution_path.exists():
        # Create new constitution with just Article 99
        constitution_path.write_text(f"# Constitution\n\n{content}")
        return True

    existing = constitution_path.read_text()

    # Remove existing Article 99 if present (various formats)
    patterns = [
        r"---\s*\n+##\s*(?:XCIX\.?|Article\s*99)\s*[-:.]?\s*Rekall.*?(?=\n---|\n##\s*(?!XCIX|Article\s*99)|\Z)",  # With separator
        r"##\s*(?:XCIX\.?|Article\s*99)\s*[-:.]?\s*Rekall.*?(?=\n##\s*(?!XCIX|Article\s*99)|\Z)",  # Without separator
        r"##\s*Memoire Developpeur Persistante.*?(?=\n---|\n##\s*(?!XCIX|Article\s*99)|\Z)",  # Old header
    ]

    cleaned = existing
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.DOTALL | re.IGNORECASE)

    # Clean up multiple blank lines
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    # Append new Article 99
    new_content = cleaned.rstrip() + "\n\n" + content.strip() + "\n"
    constitution_path.write_text(new_content)

    return True


# Patches for Speckit command files
# Format: filename -> (search_term, types, insert_after)
# Note: speckit.hotfix.md may not exist in standard installations - handled gracefully
SPECKIT_PATCHES = {
    "speckit.implement.md": ("NOM_PROJET", "pitfall,bug", "## Outline\n"),
    "speckit.hotfix.md": ("DESCRIPTION_BUG", "bug,pitfall", "Tu exécutes le workflow de hotfix pour SpecKit.\n"),
    "speckit.clarify.md": ("SUJET_DE_LA_SPEC", "decision", "## Outline\n"),
    "speckit.specify.md": ("MOTS_CLES_DE_LA_FEATURE", "decision,pattern", "Given that feature description, do this:\n"),
    "speckit.plan.md": ("architecture pattern", "pattern,decision", "## Outline\n"),
    "speckit.tasks.md": ("TECHNOS_UTILISEES", "pattern,bug", "## Outline\n"),
}


def _make_rekall_section(search_term: str, types: str, use_mcp: bool = False) -> str:
    """Generate a Rekall consultation section.

    Args:
        search_term: Search query placeholder
        types: Comma-separated entry types
        use_mcp: If True, generate MCP tool calls; if False, generate CLI commands
    """
    if use_mcp:
        # MCP version - uses rekall_search tool
        return f'''### 0. Consultation Rekall (OPTIONNEL)

**Voir `/rekall` pour les instructions completes.**

Utilise l'outil MCP `rekall_search` :
- `rekall_search(query="{search_term}", type="{types}", limit=5)`
- `rekall_search(query="{search_term}", memory_type="semantic", limit=3)`

'''
    else:
        # CLI version - uses bash commands
        return f'''### 0. Consultation Rekall (OPTIONNEL)

**Voir `/rekall` pour les instructions completes.**

```bash
# Recherche par type
rekall search "{search_term}" --type {types} --limit 5

# Recherche par memoire (patterns consolides)
rekall search "{search_term}" --memory-type semantic --limit 3
```

'''


def has_mcp_configured(base_path: Path) -> bool:
    """Check if MCP is configured for any IDE.

    Returns True if Claude or Cursor has MCP configured.
    """
    home = Path.home()

    # Check Claude MCP (settings.json with mcpServers)
    claude_settings = home / ".claude" / "settings.json"
    if claude_settings.exists():
        try:
            import json
            content = claude_settings.read_text()
            data = json.loads(content)
            if "mcpServers" in data and data["mcpServers"]:
                return True
        except Exception:
            pass

    # Check Cursor MCP (mcp.json)
    cursor_mcp = base_path / ".cursor" / "mcp.json"
    if cursor_mcp.exists():
        return True

    return False


@register("speckit", "Speckit workflow integration", "~/.claude/commands/ + ~/.speckit/constitution.md", None)
def install_speckit(base_path: Path, global_install: bool = False) -> Path:
    """Install Speckit integration (article + patches).

    This integration:
    1. Adds Article XCIX (99) to ~/.speckit/constitution.md
    2. Patches Speckit command files with Rekall consultation sections

    Note: The /rekall skill is installed via the Claude Code IDE integration.

    Returns:
        Path to the constitution file (or commands dir if no constitution)
    """
    results = {"article": False, "patched": [], "skipped": []}
    claude_dir = Path.home() / ".claude" / "commands"
    claude_dir.mkdir(parents=True, exist_ok=True)

    # 1. Add Article 99 to constitution
    constitution_path = Path.home() / ".speckit" / "constitution.md"
    if constitution_path.exists():
        content = constitution_path.read_text()
        if "XCIX. Rekall" not in content:
            new_content = content.rstrip() + "\n" + ARTICLE_99_CONTENT
            constitution_path.write_text(new_content)
            results["article"] = True

    # 2. Patch Speckit command files
    for filename, (search_term, types, insert_after) in SPECKIT_PATCHES.items():
        filepath = claude_dir / filename
        if not filepath.exists():
            results["skipped"].append(filename)
            continue

        content = filepath.read_text()

        # Skip if already patched
        if "Consultation Rekall" in content or "rekall search" in content:
            results["skipped"].append(filename)
            continue

        # Find insertion point and insert section
        if insert_after in content:
            section = _make_rekall_section(search_term, types)
            new_content = content.replace(insert_after, insert_after + section)
            filepath.write_text(new_content)
            results["patched"].append(filename)
        else:
            results["skipped"].append(filename)

    # Print summary
    print("Rekall-Speckit integration installed:")
    print(f"  - Article 99: {'Added' if results['article'] else 'Skipped (exists or no constitution)'}")
    print(f"  - Patched: {', '.join(results['patched']) or 'None'}")
    if results["skipped"]:
        print(f"  - Skipped: {', '.join(results['skipped'])}")

    return constitution_path if constitution_path.exists() else claude_dir


def is_speckit_installed() -> bool:
    """Check if Speckit integration is installed.

    Returns:
        True if any part of the integration is present
    """
    status = get_speckit_status()
    return any(status.values())


def get_speckit_status() -> dict:
    """Get detailed installation status of each Speckit component.

    Returns:
        Dict mapping component names to their installation status (bool or str)
        For article: "short", "extensive", or False
    """
    claude_dir = Path.home() / ".claude" / "commands"
    status = {}

    # Check constitution article (detect which version is installed)
    constitution_path = Path.home() / ".speckit" / "constitution.md"
    if constitution_path.exists():
        content = constitution_path.read_text()
        if "XCIX. Rekall" in content:
            # Detect version by checking for extensive-only content
            if "#### 6. Serveur MCP" in content or "Outils MCP:" in content:
                status["article_short"] = False
                status["article_extensive"] = True
            else:
                status["article_short"] = True
                status["article_extensive"] = False
        else:
            status["article_short"] = False
            status["article_extensive"] = False
    else:
        status["article_short"] = False
        status["article_extensive"] = False

    # Check each Speckit command file
    for filename in SPECKIT_PATCHES.keys():
        filepath = claude_dir / filename
        if filepath.exists():
            content = filepath.read_text()
            status[filename] = "Consultation Rekall" in content
        else:
            status[filename] = None  # File doesn't exist

    return status


def get_speckit_preview(components: list[str]) -> dict[str, str]:
    """Generate preview of changes for selected components.

    Args:
        components: List of component names to preview

    Returns:
        Dict mapping component names to their preview text (diff or content)
    """
    previews = {}
    claude_dir = Path.home() / ".claude" / "commands"

    for component in components:
        if component == "article_short":
            # Show the short article content
            previews["article_short"] = f"[APPEND TO] ~/.speckit/constitution.md\n{'─' * 50}\n{ARTICLE_99_SHORT}"
        elif component == "article_extensive":
            # Show the extensive article content
            previews["article_extensive"] = f"[APPEND TO] ~/.speckit/constitution.md\n{'─' * 50}\n{ARTICLE_99_EXTENSIVE}"

        elif component in SPECKIT_PATCHES:
            filepath = claude_dir / component
            if not filepath.exists():
                previews[component] = f"[SKIP] {component} - file not found"
                continue

            content = filepath.read_text()
            if "Consultation Rekall" in content:
                previews[component] = f"[SKIP] {component} - already patched"
                continue

            search_term, types, insert_after = SPECKIT_PATCHES[component]
            section = _make_rekall_section(search_term, types)

            # Find context around insertion point
            if insert_after in content:
                idx = content.find(insert_after)
                before = content[max(0, idx-50):idx + len(insert_after)]
                previews[component] = f"[PATCH] {component}\n{'─' * 50}\n...{before}\n[+] {section.strip()}\n..."
            else:
                previews[component] = f"[SKIP] {component} - insertion point not found"

    return previews


def get_speckit_uninstall_preview(components: list[str]) -> dict[str, str]:
    """Generate preview of uninstall changes for selected components.

    Args:
        components: List of component names to preview

    Returns:
        Dict mapping component names to their preview text
    """
    import re
    previews = {}
    claude_dir = Path.home() / ".claude" / "commands"

    for component in components:
        if component in ("article_short", "article_extensive"):
            constitution_path = Path.home() / ".speckit" / "constitution.md"
            if constitution_path.exists():
                content = constitution_path.read_text()
                if "XCIX. Rekall" in content:
                    version = "extensive" if "Outils MCP:" in content else "short"
                    previews[component] = f"[REMOVE FROM] ~/.speckit/constitution.md\n{'─' * 50}\n[-] Article XCIX ({version} version)"
                else:
                    previews[component] = f"[SKIP] {component} - not in constitution"
            else:
                previews[component] = f"[SKIP] {component} - constitution not found"

        elif component in SPECKIT_PATCHES:
            filepath = claude_dir / component
            if not filepath.exists():
                previews[component] = f"[SKIP] {component} - file not found"
                continue

            content = filepath.read_text()
            if "Consultation Rekall" not in content:
                previews[component] = f"[SKIP] {component} - not patched"
                continue

            # Find the section that will be removed
            pattern = r'### \d+[ab]?\. Consultation Rekall[^\n]*\n+(?:\*\*[^\n]*\n+)?```bash\n[^`]*```\n+'
            match = re.search(pattern, content)
            if match:
                previews[component] = f"[CLEAN] {component}\n{'─' * 50}\n[-] {match.group(0).strip()[:200]}..."
            else:
                previews[component] = f"[CLEAN] {component} - Rekall section will be removed"

    return previews


def install_speckit_partial(components: list[str]) -> dict:
    """Install selected Speckit components.

    Args:
        components: List of component names to install

    Returns:
        Dict with installation results
    """
    results = {"installed": [], "skipped": [], "errors": []}
    claude_dir = Path.home() / ".claude" / "commands"
    claude_dir.mkdir(parents=True, exist_ok=True)

    for component in components:
        try:
            if component in ("article_short", "article_extensive"):
                constitution_path = Path.home() / ".speckit" / "constitution.md"
                if constitution_path.exists():
                    content = constitution_path.read_text()
                    article_content = ARTICLE_99_SHORT if component == "article_short" else ARTICLE_99_EXTENSIVE

                    if "XCIX. Rekall" not in content:
                        # No article yet - add it
                        new_content = content.rstrip() + "\n" + article_content
                        constitution_path.write_text(new_content)
                        results["installed"].append(component)
                    else:
                        # Article exists - check if it's the same version
                        is_extensive = "Outils MCP:" in content
                        if (component == "article_extensive" and is_extensive) or \
                           (component == "article_short" and not is_extensive):
                            results["skipped"].append(f"{component} (already installed)")
                        else:
                            # Different version - replace it
                            # Remove old article first
                            import re
                            pattern = r'\n---\n\n## Memoire Developpeur Persistante\n### XCIX\. Rekall.*?(?=\n---\n|\n## [A-Z]|\Z)'
                            new_content = re.sub(pattern, '', content, flags=re.DOTALL)
                            new_content = new_content.rstrip() + "\n" + article_content
                            constitution_path.write_text(new_content)
                            results["installed"].append(component)
                else:
                    results["skipped"].append(f"{component} (no constitution)")

            elif component in SPECKIT_PATCHES:
                filepath = claude_dir / component
                if not filepath.exists():
                    results["skipped"].append(f"{component} (not found)")
                    continue

                content = filepath.read_text()
                if "Consultation Rekall" in content:
                    results["skipped"].append(f"{component} (exists)")
                    continue

                search_term, types, insert_after = SPECKIT_PATCHES[component]
                if insert_after in content:
                    section = _make_rekall_section(search_term, types)
                    new_content = content.replace(insert_after, insert_after + section)
                    filepath.write_text(new_content)
                    results["installed"].append(component)
                else:
                    results["skipped"].append(f"{component} (no insertion point)")

        except Exception as e:
            results["errors"].append(f"{component}: {e}")

    return results


def uninstall_speckit_partial(components: list[str]) -> dict:
    """Uninstall selected Speckit components.

    Args:
        components: List of component names to uninstall

    Returns:
        Dict with uninstallation results
    """
    import re

    results = {"removed": [], "skipped": [], "errors": []}
    claude_dir = Path.home() / ".claude" / "commands"

    for component in components:
        try:
            if component in ("article_short", "article_extensive"):
                constitution_path = Path.home() / ".speckit" / "constitution.md"
                if constitution_path.exists():
                    content = constitution_path.read_text()
                    if "XCIX. Rekall" in content:
                        patterns = [
                            r'\n---\n+## Memoire Developpeur Persistante\n+### XCIX\. Rekall[^\n]*\n.*?(?=\n---\n|\Z)',
                            r'\n### XCIX\. Rekall[^\n]*\n.*?(?=\n### [A-Z]|\n---\n|\Z)',
                        ]
                        new_content = content
                        for pattern in patterns:
                            new_content = re.sub(pattern, '', new_content, flags=re.DOTALL)
                        new_content = re.sub(r'\n{3,}$', '\n', new_content)

                        if new_content != content:
                            constitution_path.write_text(new_content)
                            results["removed"].append(component)
                        else:
                            results["skipped"].append(f"{component} (no change)")
                    else:
                        results["skipped"].append(f"{component} (not in constitution)")
                else:
                    results["skipped"].append(f"{component} (no constitution)")

            elif component in SPECKIT_PATCHES:
                filepath = claude_dir / component
                if not filepath.exists():
                    results["skipped"].append(f"{component} (not found)")
                    continue

                content = filepath.read_text()
                if "Consultation Rekall" not in content:
                    results["skipped"].append(f"{component} (not patched)")
                    continue

                original_content = content
                pattern1 = r'### \d+[ab]?\. Consultation Rekall[^\n]*\n+(?:\*\*[^\n]*\n+)?```bash\n[^`]*```\n+'
                content = re.sub(pattern1, '', content)
                pattern2 = r'```bash\nrekall search "[^"]*" --type [^\n]+ --limit \d+\n```\n+'
                content = re.sub(pattern2, '', content)

                if content != original_content:
                    filepath.write_text(content)
                    results["removed"].append(component)
                else:
                    results["skipped"].append(f"{component} (no change)")

        except Exception as e:
            results["errors"].append(f"{component}: {e}")

    return results


def uninstall_speckit() -> dict:
    """Remove Speckit integration.

    Uses regex patterns to cleanly remove added sections without needing backups.
    This allows the user to modify their files between install/uninstall.

    Returns:
        Dict with uninstallation results
    """
    import re

    results = {"article_removed": False, "cleaned": []}

    claude_dir = Path.home() / ".claude" / "commands"

    # 1. Remove Article XCIX from constitution
    constitution_path = Path.home() / ".speckit" / "constitution.md"
    if constitution_path.exists():
        content = constitution_path.read_text()
        if "XCIX. Rekall" in content or "Rekall - Capture de Connaissances" in content:
            # Pattern: Match from "---" before article to end of article
            # Handles variations in whitespace and content
            patterns = [
                # Full section with header
                r'\n---\n+## Memoire Developpeur Persistante\n+### XCIX\. Rekall[^\n]*\n.*?(?=\n---\n|\Z)',
                # Just the article without header (if header was modified)
                r'\n### XCIX\. Rekall[^\n]*\n.*?(?=\n### [A-Z]|\n---\n|\Z)',
            ]
            new_content = content
            for pattern in patterns:
                new_content = re.sub(pattern, '', new_content, flags=re.DOTALL)

            # Clean up any double newlines at end
            new_content = re.sub(r'\n{3,}$', '\n', new_content)

            if new_content != content:
                constitution_path.write_text(new_content)
                results["article_removed"] = True

    # 3. Clean Speckit command files - remove Rekall consultation sections
    for filename in SPECKIT_PATCHES.keys():
        filepath = claude_dir / filename
        if not filepath.exists():
            continue

        content = filepath.read_text()
        original_content = content

        # Pattern 1: Standard "### 0. Consultation Rekall" section
        # Matches: ### 0. Consultation Rekall (OPTIONNEL)\n...\n```\n\n
        pattern1 = r'### \d+[ab]?\. Consultation Rekall[^\n]*\n+(?:\*\*[^\n]*\n+)?```bash\n[^`]*```\n+'
        content = re.sub(pattern1, '', content)

        # Pattern 2: Any remaining "rekall search" in code blocks we added
        # Only remove if it's our generated pattern (with --type and --limit)
        # Don't remove user-added rekall commands
        pattern2 = r'```bash\nrekall search "[^"]*" --type [^\n]+ --limit \d+\n```\n+'
        content = re.sub(pattern2, '', content)

        if content != original_content:
            filepath.write_text(content)
            results["cleaned"].append(filename)

    return results
