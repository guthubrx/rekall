# Quickstart - Feature 018: Auto-Capture Contexte Enrichi

## Prérequis

- Python 3.11+
- Rekall v0.3.0+ installé
- Claude Code CLI (pour hook rappel proactif)
- Git (pour auto-détection fichiers)

## Installation Hook Rappel (Claude Code)

```bash
# Installer le hook de rappel proactif
rekall hooks install --cli claude

# Vérifier l'installation
ls ~/.claude/hooks/rekall-reminder.sh
```

## Utilisation Mode 1 - Agent Direct

L'agent fournit directement les échanges pertinents :

```python
# L'agent appelle directement avec conversation_excerpt
rekall_add(
    type="bug",
    title="Fix timeout API",
    context={
        "situation": "L'API timeout après 30s",
        "solution": "Augmenté timeout à 60s + retry logic",
        "trigger_keywords": ["timeout", "api", "retry"],
        "conversation_excerpt": """
User: L'API timeout souvent
Assistant: J'ai identifié le problème...
        """
    },
    auto_detect_files=True,  # Auto-détecte fichiers modifiés
    _cwd="/path/to/project"   # Répertoire git
)
```

## Utilisation Mode 2 - Système Assisté

Quand l'agent manque de contexte (conversation compactée) :

### Étape 1 : Demander les candidats

```python
response = rekall_add(
    type="bug",
    title="Fix timeout API",
    context={
        "situation": "L'API timeout après 30s",
        "solution": "Augmenté timeout à 60s + retry logic"
    },
    auto_capture_conversation=True,
    _transcript_path="~/.claude/projects/abc123/session.jsonl",
    _transcript_format="claude-jsonl"  # Optionnel, auto-détecté
)

# Réponse:
# {
#   "status": "candidates_ready",
#   "session_id": "01HXYZ...",
#   "candidates": [
#     {"index": 45, "role": "human", "content": "L'API timeout..."},
#     {"index": 46, "role": "assistant", "content": "J'ai identifié..."},
#     ...
#   ],
#   "instruction": "Reply with conversation_excerpt_indices..."
# }
```

### Étape 2 : Filtrer les pertinents

```python
rekall_add(
    type="bug",
    title="Fix timeout API",
    context={
        "situation": "L'API timeout après 30s",
        "solution": "Augmenté timeout à 60s + retry logic"
    },
    conversation_excerpt_indices=[45, 46, 47, 48, 49],  # 5 échanges pertinents
    _session_id="01HXYZ..."  # Session de l'étape 1
)

# Réponse:
# {
#   "status": "success",
#   "entry_id": "01HABC...",
#   "context_summary": {
#     "conversation_captured": true,
#     "files_detected": 3,
#     "temporal_markers": true,
#     "extraction_method": "auto_mode2"
#   }
# }
```

## Auto-Détection Git

```python
rekall_add(
    type="pattern",
    title="Pattern retry avec backoff",
    context={
        "situation": "Besoin de retry robuste",
        "solution": "Implémenté exponential backoff"
    },
    auto_detect_files=True,
    _cwd="/path/to/project"
)

# files_modified sera automatiquement rempli avec:
# - Fichiers staged (git diff --cached)
# - Fichiers unstaged (git diff)
# - Dédupliqués
```

## Marqueurs Temporels

Auto-générés si non fournis :

```python
# Créé à 14h30 un mercredi
rekall_add(
    type="bug",
    title="Bug du mercredi après-midi",
    context={...}
)
# → time_of_day: "afternoon"
# → day_of_week: "wednesday"

# Override manuel possible
rekall_add(
    type="bug",
    title="Bug critique",
    context={
        ...,
        "time_of_day": "night",  # Override
        "day_of_week": "friday"  # Override
    }
)
```

## Formats Transcript Supportés

| Format | CLI | Auto-détection |
|--------|-----|----------------|
| `claude-jsonl` | Claude Code | `.jsonl` |
| `cline-json` | Cline | `api_conversation_history.json` |
| `continue-json` | Continue.dev | `.continue/` path |
| `raw-json` | Generic | `.json` (fallback) |

## Troubleshooting

### Transcript non trouvé

```python
# Erreur:
{"status": "error", "error_code": "TRANSCRIPT_NOT_FOUND", ...}

# Solution: Utiliser Mode 1 (agent fournit conversation_excerpt)
```

### Git non disponible

```python
# Erreur:
{"status": "error", "error_code": "GIT_NOT_AVAILABLE", ...}

# Solution: files_modified sera vide, pas bloquant
```

### Format non supporté

```python
# Erreur:
{"status": "error", "error_code": "TRANSCRIPT_FORMAT_UNSUPPORTED", ...}

# Solution: Utiliser Mode 1 ou spécifier _transcript_format="raw-json"
```
