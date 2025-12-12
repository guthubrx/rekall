# Plan Phase 2 : Auto-Capture Contexte Enrichi

**Date** : 2025-12-12
**Spec** : [006-enriched-context](./spec.md)
**Statut** : En attente de validation

---

## Résumé Exécutif

Implémenter les fonctionnalités manquantes de la spec 006 :
1. **Auto-capture conversation** : Extraire automatiquement les 10 derniers messages
2. **Auto-détection fichiers** : Détecter les fichiers modifiés via git
3. **Temporal markers** : Ajouter contexte temporel (quand, durée)
4. **Hook de rappel proactif** : Rappeler à l'agent de sauvegarder après résolution

---

## Écarts Identifiés (Spec vs Implémentation)

| Fonctionnalité | Prévu | Actuel | Priorité |
|----------------|-------|--------|----------|
| conversation_excerpt auto | 10 derniers messages | Manuel | P0 |
| files_modified auto | git diff | Manuel | P1 |
| temporal_markers | quand/durée/après | Non implémenté | P2 |
| Hook rappel proactif | Détection "résolu" | Non implémenté | P1 |

---

## Architecture Technique

### 1. Auto-Capture Conversation (P0)

**Problème** : L'agent doit manuellement copier la conversation dans `conversation_excerpt`.

**Solution** : Utiliser `transcript_path` disponible dans les hooks Claude Code.

#### Approche A : Enrichissement côté MCP (RECOMMANDÉ)

Le MCP `rekall_add` accepte un nouveau champ `auto_capture` :

```python
# mcp_server.py - _handle_add()
if context_arg.get("auto_capture_conversation"):
    transcript_path = args.get("_transcript_path")  # Passé par l'agent
    if transcript_path:
        conversation = extract_last_n_messages(transcript_path, n=10)
        context_arg["conversation_excerpt"] = conversation
```

L'agent Claude a accès au transcript et peut le passer :

```python
# Appel MCP par l'agent
rekall_add(
    type="bug",
    title="Fix 504 timeout",
    context={
        "situation": "...",
        "solution": "...",
        "trigger_keywords": [...],
        "auto_capture_conversation": True,
        "_transcript_path": "/path/to/transcript.jsonl"
    }
)
```

#### Approche B : Hook PostToolUse sur rekall_add

Un hook qui enrichit automatiquement après l'appel :

```bash
# ~/.claude/hooks/rekall-enrich.sh
# Déclenché par PostToolUse sur mcp__rekall__rekall_add
```

**Choix** : Approche A (plus simple, pas de hook supplémentaire)

#### Fichiers à modifier

| Fichier | Modification |
|---------|--------------|
| `rekall/mcp_server.py` | Ajouter extraction transcript dans `_handle_add` |
| `rekall/context_extractor.py` | Nouvelle fonction `extract_last_n_messages(path, n)` |
| `rekall/models.py` | Documenter le flux auto-capture |

#### Code : extract_last_n_messages

```python
# rekall/context_extractor.py

def extract_last_n_messages(transcript_path: str, n: int = 10) -> str:
    """Extrait les N derniers échanges user/assistant du transcript Claude.

    Args:
        transcript_path: Chemin vers le fichier JSONL du transcript
        n: Nombre d'échanges à extraire (défaut: 10)

    Returns:
        String formaté des derniers échanges
    """
    import json
    from pathlib import Path

    messages = []
    path = Path(transcript_path)

    if not path.exists():
        return ""

    with open(path, 'r') as f:
        for line in f:
            try:
                event = json.loads(line)
                # Filtrer les messages user et assistant
                if event.get("type") in ("human", "assistant"):
                    role = "User" if event["type"] == "human" else "Assistant"
                    content = event.get("content", "")
                    # Tronquer les messages longs
                    if len(content) > 500:
                        content = content[:500] + "..."
                    messages.append(f"{role}: {content}")
            except json.JSONDecodeError:
                continue

    # Garder les N derniers
    recent = messages[-n*2:] if len(messages) > n*2 else messages
    return "\n".join(recent)
```

---

### 2. Auto-Détection Fichiers Modifiés (P1)

**Problème** : L'agent doit manuellement lister les fichiers dans `files_modified`.

**Solution** : Utiliser `git diff --name-only` automatiquement.

#### Approche

Dans le MCP `rekall_add`, si `auto_detect_files: true` :

```python
# mcp_server.py - _handle_add()
if context_arg.get("auto_detect_files"):
    cwd = args.get("_cwd", os.getcwd())
    files = detect_modified_files(cwd)
    context_arg["files_modified"] = files
```

#### Code : detect_modified_files

```python
# rekall/context_extractor.py

def detect_modified_files(cwd: str) -> list[str]:
    """Détecte les fichiers modifiés via git dans le répertoire.

    Args:
        cwd: Répertoire de travail

    Returns:
        Liste des fichiers modifiés (staged + unstaged)
    """
    import subprocess

    try:
        # Fichiers modifiés non staged
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5
        )
        unstaged = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Fichiers staged
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=5
        )
        staged = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Combiner et dédupliquer
        all_files = list(set(unstaged + staged))
        return [f for f in all_files if f]  # Filtrer les vides

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []
```

---

### 3. Temporal Markers (P2)

**Problème** : Pas de contexte temporel pour situer le souvenir.

**Solution** : Ajouter des champs temporels au `StructuredContext`.

#### Modifications au modèle

```python
# rekall/models.py - StructuredContext

@dataclass
class StructuredContext:
    # ... champs existants ...

    # Temporal markers (optionnels, auto-générés si non fournis)
    session_duration_minutes: int | None = None  # Durée de la session
    time_of_day: str | None = None  # "morning", "afternoon", "evening", "night"
    day_of_week: str | None = None  # "monday", "tuesday", etc.
    preceded_by: str | None = None  # Ce qui s'est passé avant (optionnel)
```

#### Auto-génération

```python
# rekall/context_extractor.py

def generate_temporal_markers() -> dict:
    """Génère les marqueurs temporels automatiquement."""
    from datetime import datetime

    now = datetime.now()
    hour = now.hour

    if 5 <= hour < 12:
        time_of_day = "morning"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 21:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    return {
        "time_of_day": time_of_day,
        "day_of_week": now.strftime("%A").lower(),
    }
```

---

### 4. Hook de Rappel Proactif (P1)

**Problème** : L'agent oublie de sauvegarder après avoir résolu un problème.

**Solution** : Hook `Stop` qui détecte les patterns de résolution et injecte un rappel.

#### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Claude termine sa réponse                                    │
│                    │                                         │
│                    ▼                                         │
│           ┌───────────────┐                                  │
│           │  Hook "Stop"  │                                  │
│           └───────┬───────┘                                  │
│                   │                                          │
│                   ▼                                          │
│     ┌─────────────────────────────┐                          │
│     │ Analyse dernière réponse    │                          │
│     │ • Contient "résolu/fixed" ? │                          │
│     │ • Fichiers modifiés ?       │                          │
│     │ • Erreur corrigée ?         │                          │
│     └─────────────┬───────────────┘                          │
│                   │                                          │
│        ┌──────────┴──────────┐                               │
│        │                     │                               │
│    Pattern détecté      Pas de pattern                       │
│        │                     │                               │
│        ▼                     ▼                               │
│  ┌───────────────┐    (pas d'action)                         │
│  │ Injecter      │                                           │
│  │ rappel Rekall │                                           │
│  └───────────────┘                                           │
└─────────────────────────────────────────────────────────────┘
```

#### Hook Script

```bash
#!/bin/bash
# ~/.claude/hooks/rekall-reminder.sh
# Hook Stop pour rappeler de sauvegarder dans Rekall

INPUT=$(cat)

# Lire le transcript pour analyser la dernière réponse
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty')

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# Extraire la dernière réponse assistant
LAST_RESPONSE=$(tail -20 "$TRANSCRIPT_PATH" | grep '"type":"assistant"' | tail -1 | jq -r '.content // empty')

# Patterns indiquant une résolution
RESOLUTION_PATTERNS="résolu|fixed|corrigé|fonctionne|marche|succès|réussi|terminé|done|working"

if echo "$LAST_RESPONSE" | grep -qiE "$RESOLUTION_PATTERNS"; then
    # Vérifier si déjà sauvegardé récemment (éviter spam)
    if echo "$LAST_RESPONSE" | grep -qi "rekall"; then
        exit 0
    fi

    # Injecter un rappel
    cat << 'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "Stop",
    "additionalContext": "<system-reminder>\n💡 **Rappel Rekall** : Tu viens de résoudre un problème. Pense à sauvegarder cette solution avec `rekall_add` pour pouvoir la retrouver plus tard.\n\nContexte structuré requis :\n- situation: Quel était le problème ?\n- solution: Comment l'as-tu résolu ?\n- trigger_keywords: Mots-clés pour retrouver\n- what_failed: Ce qui n'a pas marché (optionnel)\n</system-reminder>"
  },
  "continue": false
}
EOF
fi

exit 0
```

#### Configuration settings.json

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/rekall-reminder.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Plan d'Implémentation

### Phase 2.1 : Auto-Capture Conversation (P0) - ~2h

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T001 | `rekall/context_extractor.py` | Ajouter `extract_last_n_messages()` |
| T002 | `rekall/mcp_server.py` | Modifier `_handle_add` pour accepter `_transcript_path` |
| T003 | `rekall/mcp_server.py` | Appeler extraction si `auto_capture_conversation: true` |
| T004 | Tests | Tester extraction JSONL |

### Phase 2.2 : Auto-Détection Fichiers (P1) - ~1h

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T005 | `rekall/context_extractor.py` | Ajouter `detect_modified_files()` |
| T006 | `rekall/mcp_server.py` | Modifier `_handle_add` pour accepter `_cwd` |
| T007 | `rekall/mcp_server.py` | Appeler détection si `auto_detect_files: true` |
| T008 | Tests | Tester détection git |

### Phase 2.3 : Hook Rappel Proactif (P1) - ~1h

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T009 | `~/.claude/hooks/rekall-reminder.sh` | Créer le hook |
| T010 | `rekall/cli_main.py` | Commande `rekall hooks install-reminder` |
| T011 | Documentation | Documenter le hook |

### Phase 2.4 : Temporal Markers (P2) - ~1h

| Tâche | Fichier | Description |
|-------|---------|-------------|
| T012 | `rekall/models.py` | Ajouter champs temporels à StructuredContext |
| T013 | `rekall/context_extractor.py` | Ajouter `generate_temporal_markers()` |
| T014 | `rekall/mcp_server.py` | Auto-générer si non fournis |
| T015 | `rekall/db.py` | Migration schéma si nécessaire |

---

## Estimation Totale

| Phase | Effort | Priorité |
|-------|--------|----------|
| 2.1 Auto-Capture Conversation | ~2h | P0 |
| 2.2 Auto-Détection Fichiers | ~1h | P1 |
| 2.3 Hook Rappel Proactif | ~1h | P1 |
| 2.4 Temporal Markers | ~1h | P2 |
| **Total** | **~5h** | |

---

## Risques et Mitigations

| Risque | Mitigation |
|--------|------------|
| Transcript trop gros | Limiter à 10 messages, tronquer à 500 chars |
| Git non disponible | Fallback gracieux (liste vide) |
| Hook trop intrusif | Pattern matching strict, cooldown |
| Performance | Extraction lazy, cache |

---

## Métriques de Succès

- [ ] 80%+ des nouveaux souvenirs ont `conversation_excerpt` rempli
- [ ] 60%+ ont `files_modified` auto-détecté
- [ ] Hook rappel déclenché dans 50%+ des résolutions
- [ ] Pas de régression sur les tests existants

---

*Plan créé le 2025-12-12 - Phase 2 de Feature 006*
