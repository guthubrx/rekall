# Quickstart: Multi-IDE Rekall Integration

**Feature**: 019-multi-ide-integration
**Date**: 2025-12-13

---

## Objectif

Intégrer Rekall dans n'importe quel IDE supporté en une seule commande.

---

## Installation Rapide

### Via TUI (recommandé)

```bash
rekall config
```

L'écran de configuration détecte automatiquement votre IDE et propose les options appropriées.

### Via CLI

```bash
# Installer pour Claude Code (global)
rekall integrate claude --global

# Installer pour Cursor (local au projet)
rekall integrate cursor --local

# Voir le statut de toutes les intégrations
rekall integrate --status
```

---

## IDEs Supportés

| IDE | Global | Local | MCP | Notes |
|-----|--------|-------|-----|-------|
| Claude Code | ✅ | ✅ | ✅ | Skill /rekall + hooks |
| Cursor | ❌ | ✅ | ✅ | .mdc rules |
| GitHub Copilot | ❌ | ✅ | ✅ | copilot-instructions.md |
| Windsurf | ❌ | ✅ | ❌ | .windsurfrules |
| Cline | ❌ | ✅ | ✅ | .clinerules |
| Zed | ✅ | ✅ | ✅ | settings.json |
| Continue.dev | ✅ | ✅ | ✅ | config.json |

---

## Intégration Speckit

Si Speckit est installé (`~/.speckit/`), l'écran affiche une section supplémentaire :

### Article 99 (Constitution)

Choisir la version selon votre setup :

| Version | Tokens | Quand l'utiliser |
|---------|--------|------------------|
| **Micro** | ~50 | Skill Claude installée |
| **Court** | ~350 | MCP configuré (sans skill) |
| **Extensif** | ~1000 | CLI seulement |

### Patches Speckit

Les commandes `/speckit.*` sont automatiquement patchées pour inclure une consultation Rekall.

---

## Fichiers Installés

### Claude Code (Global)

```
~/.claude/
├── commands/
│   ├── rekall.md              # Skill principale
│   └── rekall/
│       ├── consultation.md    # Workflow recherche
│       ├── capture.md         # Workflow capture
│       ├── linking.md         # Knowledge graph
│       └── commands.md        # Référence CLI
├── hooks/
│   ├── rekall-webfetch.sh     # Capture URLs automatique
│   └── rekall-reminder.sh     # Rappel sauvegarde
└── settings.json              # Config hooks (modifié)
```

### Cursor (Local)

```
.cursor/
├── rules/
│   └── rekall.mdc             # Rules Rekall
└── mcp.json                   # Config MCP (modifié)
```

### Speckit

```
~/.speckit/
└── constitution.md            # Article 99 ajouté

~/.claude/commands/
├── speckit.implement.md       # Patché
├── speckit.plan.md            # Patché
└── ...
```

---

## Vérification

```bash
# Vérifier le statut
rekall integrate --status

# Sortie attendue:
# IDE détecté: Claude Code (global)
#
# INTÉGRATIONS:
#   Claude Code    global: ✓    local: -
#   Cursor         global: n/a  local: -
#   ...
#
# SPECKIT:
#   Article 99: Court (★ recommandé: Micro)
#   Patches: 3/6 installés
```

---

## Désinstallation

```bash
# Désinstaller une intégration
rekall integrate claude --global --uninstall

# Ou via TUI: sélectionner et appuyer sur 'r'
```

---

## Troubleshooting

### L'IDE n'est pas détecté

Vérifier que le dossier de configuration existe :
- Claude Code : `~/.claude/` ou `.claude/`
- Cursor : `.cursor/`
- etc.

### MCP ne fonctionne pas

1. Vérifier le package : `pip show mcp`
2. Tester le serveur : `rekall mcp`
3. Debug : `claude --mcp-debug`

### Skill /rekall ne se charge pas

1. Vérifier le fichier : `cat ~/.claude/commands/rekall.md`
2. Vérifier les permissions : `ls -la ~/.claude/commands/`
3. Redémarrer Claude Code

---

## Prochaines étapes

1. Lancer `rekall config` pour configurer votre IDE
2. Tester avec `/rekall` (Claude) ou `rekall search "test"`
3. Consulter `rekall --help` pour toutes les commandes
