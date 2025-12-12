# Meilleures pratiques — Hooks Claude Code CLI (Anthropic)

Date: 2025‑12‑12  
Sources principales: documentation officielle Anthropic “Claude Code Hooks” et pages connexes (téléchargées le 2025‑12‑12).

## 1. Rappel du modèle de hooks Claude Code

### 1.1 Où configurer

Les hooks se déclarent dans les fichiers de settings Claude Code :
- `~/.claude/settings.json` : configuration utilisateur globale.  
- `.claude/settings.json` : configuration projet versionnée.  
- `.claude/settings.local.json` : configuration locale non commitée.  

Ces fichiers sont fusionnés par Claude Code au démarrage.

### 1.2 Structure de base

Un hook est attaché à un **événement** et optionnellement filtré par un **matcher** (nom d’outil ou regex).

Schéma conceptuel :
```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "ToolPattern",
        "hooks": [
          { "type": "command", "command": "your-command-here" }
        ]
      }
    ]
  }
}
```

- `matcher` est sensible à la casse et n’est applicable que pour `PreToolUse`, `PermissionRequest`, `PostToolUse`.  
  - chaîne simple = match exact (`Write`)  
  - regex = match multiple (`Edit|Write`, `Notebook.*`)  
  - `*` = tous les outils.  

### 1.3 Événements supportés (vue utile)

- **PreToolUse** : après génération des paramètres, avant exécution de l’outil. Idéal pour *contrôle d’accès/validation*.  
- **PermissionRequest** : quand l’UI demande une permission.  
- **PostToolUse** : juste après succès d’un outil. Idéal pour *capture/log/enrichissement*.  
- **Notification** : notifications internes (permission_prompt, idle_prompt, auth_success, etc.).  
- **UserPromptSubmit** : avant traitement d’un prompt utilisateur (permet injection de contexte).  
- **Stop / SubagentStop** : quand Claude veut s’arrêter / un subagent termine.  
- **SessionStart / SessionEnd** : début/fin de session.  
- **PreCompact** : avant compactage.  

## 2. Bonnes pratiques générales

### 2.1 Choisir le bon type de hook

Claude Code supporte deux types :
- **Bash/command hooks (`type: "command"`)**  
  - *Avantages*: rapides, déterministes, local‑first.  
  - *À utiliser pour*: règles simples, validation, transformations, capture d’artefacts.  
- **Prompt‑based hooks (`type: "prompt"`)**  
  - *Avantages*: décisions contextuelles riches.  
  - *Limites*: plus lents (appel LLM), non déterministes.  
  - *Actuellement restreints à*: `Stop` et `SubagentStop`.  
  - *À utiliser pour*: décider de continuer/stopper selon le contexte de session.  

Recommandation officielle : préférer bash pour règles simples; réserver prompt‑based aux décisions complexes.

### 2.2 Garder les hooks rapides et non bloquants

- Limite d’exécution par commande: **60s par défaut**, configurable par hook.  
- Tous les hooks qui matchent un événement **s’exécutent en parallèle**.  
- Les commandes identiques sont **dédupliquées automatiquement**.  

Conséquence pratique :  
1. éviter les tâches lourdes dans `PreToolUse`/`PostToolUse` (préférer un job async/background).  
2. mettre des timeouts serrés pour les actions réseau ou non critiques.  

### 2.3 Utiliser des chemins robustes et portables

Pour des scripts stockés dans le projet, Anthropic recommande :
- référencer le script via **`$CLAUDE_PROJECT_DIR`** (chemin absolu racine projet).  
- éviter de dépendre du `cwd` courant de Claude.  

Exemple conceptuel :
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/check-style.sh"
          }
        ]
      }
    ]
  }
}
```

### 2.4 Comprendre l’input et l’output

Tous les hooks reçoivent un JSON sur **stdin**.  
Pour `PostToolUse`, le payload contient notamment :
- `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`  
- `tool_name`  
- `tool_input` (schéma variable selon outil)  
- `tool_response` (résultat outil)  
- `tool_use_id`  

Les hooks contrôlent Claude Code via :
1. **exit codes**  
2. **stdout JSON** (si exit code 0) pour décision fine.  

### 2.5 Sécurité & hygiène (officiel)

Anthropic liste explicitement :
- **Valider/assainir les entrées** (`stdin` ≠ confiance).  
- **Toujours quoter les variables shell** (`"$VAR"` pas `$VAR`).  
- **Bloquer le path traversal** (refuser `..` dans les chemins).  
- **Utiliser des chemins absolus** et variables Claude (`$CLAUDE_PROJECT_DIR`).  
- **Ignorer les fichiers sensibles** (`.env`, `.git/`, clés, etc.).  

### 2.6 Sécurité de configuration

Claude Code protège contre la modification malveillante de hooks en cours de session :
- snapshot des hooks au démarrage;  
- avertit en cas de changement externe;  
- nécessite validation via la commande **`/hooks`** pour appliquer les changements.  

=> bon réflexe : redémarrer/valider via `/hooks` après changement.

## 3. Spécifique `PreToolUse`

### 3.1 Cas d’usage recommandés

- autoriser/refuser une action selon outil/fichier/projet.  
- ajouter du contexte avant exécution.  
- enforce policies (ex: pas d’écriture hors workspace).  

### 3.2 Decision control

Un hook peut renvoyer un JSON pour :
- `permissionDecision: "allow"|"deny"|"ask"` (contrôle de permission).  
- `updatedInput` pour modifier l’entrée de l’outil.  
- `hookSpecificOutput.additionalContext` pour donner du contexte à Claude.  

Utiliser `deny/ask` pour les règles de sécurité plutôt qu’un simple log.

## 4. Spécifique `PostToolUse`

### 4.1 Cas d’usage recommandés

PostToolUse se déclenche **après succès** d’un outil. Bon pour :
- capturer les artefacts (URLs WebFetch, fichiers écrits, commandes Bash).  
- indexer/enrichir sans bloquer Claude.  
- appliquer des règles post‑traitement (ex: auto‑format).  

### 4.2 Feedback à Claude (Decision Control)

Même si l’outil a déjà tourné, le hook peut renvoyer :
- `decision: "block"` + `reason` → Claude reçoit un feedback automatique.  
- `decision: undefined` → aucun effet.  

Différence importante :  
`continue: false` **arrête** Claude après les hooks; c’est plus fort que `decision: "block"`.

### 4.3 Exit code 2

Si le hook sort avec **exit code 2** :
- pour `PostToolUse`, l’outil est déjà exécuté; Claude voit l’erreur stderr comme feedback.  
=> utile pour signaler une non‑conformité sans rétro‑exécuter.

## 5. Prompt‑based hooks (`Stop`/`SubagentStop`)

### 5.1 Fonctionnement

Au lieu d’un bash, Claude Code envoie input + prompt à un LLM rapide (Haiku) et attend un JSON structuré avec la décision de stop/continue.

### 5.2 Best practices officielles

- **Prompts spécifiques** : exprimer clairement la décision attendue.  
- **Critères explicites** : lister ce que le LLM doit évaluer.  
- **Tester le prompt** sur plusieurs scénarios.  
- **Timeout adapté** (30s par défaut).  
- **Réserver aux décisions complexes**; sinon préférer bash.  

## 6. Debugging / Exploitation

Si un hook ne fonctionne pas :
1. vérifier l’enregistrement via **`/hooks`**.  
2. valider la syntaxe JSON des settings.  
3. exécuter la commande hook manuellement hors Claude Code.  
4. vérifier permissions/paths.  
5. activer `--debug` ou mode verbose pour voir l’exécution.

## 7. Application à Rekall (hook WebFetch)

Votre hook `rekall-webfetch.sh` est globalement aligné avec les bonnes pratiques :
- filtrage précoce sur `tool_name == WebFetch` (évite bruit).  
- variables correctement quotées.  
- exécution en background (`( … ) &`) pour ne pas bloquer Claude.  

Améliorations recommandées au regard des docs :
- référencer `rekall` et/ou le script via `"$CLAUDE_PROJECT_DIR"` si vous le rendez project‑local.  
- vérifier `CLAUDE_CODE_REMOTE` pour éviter certains comportements en contexte distant.  
- logger les erreurs dans un fichier local (ex: `~/.claude/hooks/logs/rekall.log`) pour debug, plutôt que `2>/dev/null`.  
- valider l’URL (schéma http/https, taille max) avant appel CLI.  

## Références

- Anthropic — Claude Code Hooks (configuration, events, prompt hooks, sécurité):  
  https://docs.anthropic.com/en/docs/claude-code/hooks  
- Anthropic — Claude Code Settings (structure & fichiers de config):  
  https://docs.anthropic.com/en/docs/claude-code/settings  

