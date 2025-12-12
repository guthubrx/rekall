# Meilleurs hooks Claude Code — exemples référencés et prêts à l’emploi

Date: 2025‑12‑12  
Synthèse à partir de sources officielles + guides communautaires (jusqu’à 2025‑08).

## Sources utilisées

- Docs officielles Anthropic — Hooks Claude Code: https://docs.anthropic.com/en/docs/claude-code/hooks  
- SmartScope — “Claude Code Hooks guide” (exemples pratiques): https://smartscope.blog/en/generative-ai/claude/claude-code-hooks-guide/  
- Apidog — “Claude Code Hooks” (format/lint/tests/commit gate): https://apidog.com/blog/claude-code-hooks/  
- SuiteInsider — guide complet hooks Claude Code: https://suiteinsider.com/complete-guide-creating-claude-code-hooks/  
- Disler — “claude-code-hooks-mastery” (sécurité + UserPromptSubmit): https://github.com/disler/claude-code-hooks-mastery  
- John Lindquist — framework TypeScript “claude-hooks” (plugins type‑safe): https://github.com/johnlindquist/claude-hooks  
- GitButler — hooks Stop pour notifications: https://blog.gitbutler.com/automate-your-ai-workflows-with-claude-code-hooks  

## Notes sur le format

Le format **officiel** est JSON dans `~/.claude/settings.json` et `.claude/settings.json`.  
Certains blogs utilisent une syntaxe TOML `[[hooks]]`; elle n’est pas décrite dans les docs officielles.  
Les exemples ci‑dessous sont donnés en JSON (adaptables en TOML si besoin).

---

## 1) Bloquer les commandes dangereuses (PreToolUse)

**Pourquoi c’est “top”**: cité dans plusieurs guides car c’est le garde‑fou principal contre erreurs/sabotage local.  
**Sources**: SmartScope (PreToolUse Bash blocker), Disler (dangerous patterns).  

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/block_dangerous_bash.py"
          }
        ]
      }
    ]
  }
}
```

Exemple de logique `block_dangerous_bash.py` (SmartScope/Disler):
- refuser `rm -rf`, `sudo rm`, `chmod 777`, écritures vers `/etc/`, etc.  
- sortir avec **exit code 2** pour bloquer l’appel outil.

---

## 2) Auto‑format / auto‑lint après édition (PostToolUse)

**Pourquoi c’est “top”**: gain immédiat de qualité; l’exemple le plus répandu.  
**Sources**: SmartScope (Black/Prettier/Rustfmt), Apidog (ruff+black), SuiteInsider (prettier).  

### Python (Black + Ruff)
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "ruff check --fix \"$CLAUDE_FILE_PATHS\" && black \"$CLAUDE_FILE_PATHS\""
          }
        ]
      }
    ]
  }
}
```

### JS/TS (Prettier)
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write \"$CLAUDE_FILE_PATHS\""
          }
        ]
      }
    ]
  }
}
```

### Rust (rustfmt)
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "rustfmt \"$CLAUDE_FILE_PATHS\""
          }
        ]
      }
    ]
  }
}
```

---

## 3) Lancer les tests automatiquement (PostToolUse, souvent en background)

**Pourquoi c’est “top”**: transforme Claude Code en CI locale continue; très cité.  
**Sources**: SmartScope (pytest background), Apidog (pytest background), SuiteInsider (npm test).  

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "pytest -q",
            "timeout": 300,
            "run_in_background": true
          }
        ]
      }
    ]
  }
}
```

Variante JS:
`"command": "npm test"` (SuiteInsider).

---

## 4) Gate “pré‑commit” ou “pré‑push” (PreToolUse)

**Pourquoi c’est “top”**: permet de refuser un commit si les règles qualité ne passent pas.  
**Source**: Apidog.  

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git commit:*)",
        "hooks": [
          {
            "type": "command",
            "command": "sh \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre_commit_checks.sh"
          }
        ]
      }
    ]
  }
}
```

Le script doit sortir non‑zéro / code 2 pour bloquer.

---

## 5) Valider le résultat d’un outil et renvoyer du feedback (PostToolUse)

**Pourquoi c’est “top”**: corrige les “faux succès” et force Claude à réparer.  
**Sources**: Disler (Result Validation), docs officielles (PostToolUse decision control).  

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/validate_tool_result.py"
          }
        ]
      }
    ]
  }
}
```

Idée de `validate_tool_result.py` (Disler):
- si `tool_name == \"Write\"` et `success == false`, renvoyer:
```json
{"decision":"block","reason":"Write failed; check permissions and retry"}
```

---

## 6) Logger/valider les prompts utilisateur (UserPromptSubmit)

**Pourquoi c’est “top”**: audit trail + enforcement de templates; très utile en équipe.  
**Source**: Disler (UserPromptSubmit deep dive).  

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/user_prompt_submit.py"
          }
        ]
      }
    ]
  }
}
```

Use cases cités:
- log JSONL des prompts + session_id  
- refuser prompts non conformes (ex: “supprime /etc”)  
- injecter du contexte standard (guidelines, conventions projet).

---

## 7) Hook Stop “completion guard” + notifications

**Pourquoi c’est “top”**: évite les sessions “terminées trop tôt” et améliore le feedback utilisateur.  
**Sources**: Disler (Completion Validation Stop), GitButler/SuiteInsider (notifications), SmartScope (auto‑commit).  

### a) Empêcher Claude de “stop” si tests KO
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/stop_guard.py"
          }
        ]
      }
    ]
  }
}
```

`stop_guard.py` (Disler):
- lancer un check rapide (ou relire un flag de test)  
- renvoyer `{ "decision":"block", "reason":"Tests failing; fix before stopping." }`.

### b) Notification locale fin de session
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "osascript -e 'display notification \"Claude finished\" with title \"Session Complete\"'"
          }
        ]
      }
    ]
  }
}
```

### c) Auto‑commit (à utiliser avec prudence)
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "git add . && git commit -m \"Auto‑commit via Claude Code\"" }
        ]
      }
    ]
  }
}
```
**Risque**: peut committer du code cassé ou non désiré; mieux si combiné au Stop guard.

---

## 8) Plugins TypeScript type‑safe (hook avancé)

**Pourquoi c’est “top”**: pour des hooks complexes, un framework type‑safe limite les erreurs et facilite le partage.  
**Source**: John Lindquist `claude-hooks`.  

Approche:
- scaffolding `claude-hooks init` crée `.claude/hooks/*.ts`  
- fonctions `preToolUse(payload)` et `postToolUse(payload)` typées.  
- utile pour pipelines internes (webhooks, dashboards, rules multiples).

---

## Recommandation d’ensemble

Si tu dois n’en garder que 3 au départ:
1. **PreToolUse Bash blocker** (sécurité).  
2. **PostToolUse auto‑format/lint** (qualité).  
3. **PostToolUse tests en background + Stop guard** (fiabilité).  

Ils sont les plus cités, les plus “ROI”, et se combinent bien entre eux.

