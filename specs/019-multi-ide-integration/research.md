# Research: Multi-IDE Rekall Integration

**Feature**: 019-multi-ide-integration
**Date**: 2025-12-13
**Sources**: Baseline (04-architectures-patterns.md) + WebSearch live

---

## 1. Configuration MCP par IDE

### Decision: Format de configuration MCP unifié

**Choix**: Utiliser le format JSON standard MCP compatible avec tous les IDEs supportant MCP.

**Rationale**:
- MCP est un protocole standard avec format JSON-RPC défini par Anthropic
- La plupart des IDEs supportant MCP utilisent un format compatible `mcpServers` ou `context_servers`
- Configuration dans `~/.claude.json` ou équivalent par IDE

**Alternatives considérées**:
- Format custom par IDE → Rejeté (maintenance impossible, pas de réutilisation)
- YAML unifié → Rejeté (les IDEs attendent du JSON)

**Sources**:
- [Claude Code MCP Documentation](https://docs.claude.com/en/docs/claude-code/mcp)
- [Scott Spence - Configuring MCP Tools](https://scottspence.com/posts/configuring-mcp-tools-in-claude-code)
- [MCP Server Setup Guide](https://claudepro.directory/guides/claude-mcp-server-setup-guide)

---

## 2. Format des Instructions IDE

### Decision: Cursor utilise .mdc au lieu de .cursorrules

**Choix**: Utiliser `.cursor/rules/rekall.mdc` pour Cursor (format moderne).

**Rationale**:
- `.cursorrules` est déprécié depuis Cursor 0.45
- `.mdc` permet globs, triggers, et inclusion sélective
- Réduction du token usage en n'activant que les règles pertinentes
- Versioning propre dans `.cursor/rules/`

**Alternatives considérées**:
- `.cursorrules` legacy → Rejeté (déprécié, sera supprimé)
- Fichier unique `.cursor/index.mdc` → Rejeté (préférer fichiers séparés pour modularité)

**Sources**:
- [Cursor Rules Documentation](https://docs.cursor.com/context/rules)
- [Cursor Forum - MDC Best Practices](https://forum.cursor.com/t/my-best-practices-for-mdc-rules-and-troubleshooting/50526)
- [Cursor Rules Configuration](https://cursorrules.org/)

---

## 3. Architecture Bundles IDE

### Decision: Bundle = Instructions + MCP + Hooks

**Choix**: Chaque IDE est un bundle complet installé atomiquement.

**Rationale**:
- Simplifie l'UX : un seul clic pour tout installer
- Évite les états incohérents (MCP sans instructions, etc.)
- Permet la détection de statut global par IDE

**Composants du bundle**:

| IDE | Instructions | MCP Config | Hooks |
|-----|-------------|------------|-------|
| Claude Code | `~/.claude/commands/rekall.md` + rekall/*.md | `~/.claude.json` | rekall-webfetch.sh, rekall-reminder.sh |
| Cursor | `.cursor/rules/rekall.mdc` | `.cursor/mcp.json` | N/A (pas de hooks natifs) |
| Copilot | `.github/copilot-instructions.md` | `.vscode/mcp.json` | N/A |
| Windsurf | `.windsurfrules` | N/A (pas de MCP) | N/A |
| Cline | `.clinerules` | `.vscode/mcp.json` | N/A |
| Zed | `.zed/settings.json` | Dans settings.json | N/A |
| Continue | `.continue/config.json` | Dans config.json | N/A |

---

## 4. Détection IDE

### Decision: Vérification paths locaux puis globaux

**Choix**: Détecter l'IDE en vérifiant l'existence de fichiers/dossiers caractéristiques.

**Algorithme**:
1. Vérifier paths locaux (projet courant) d'abord
2. Puis vérifier paths globaux (home directory)
3. Ordre de priorité : Claude > Cursor > Copilot > Windsurf > Cline > Zed > Continue

**Paths de détection**:

| IDE | Local Check | Global Check |
|-----|-------------|--------------|
| Claude Code | `.claude/` | `~/.claude/` |
| Cursor | `.cursor/` | `~/.cursor/` |
| Copilot | `.github/` + `.vscode/` | N/A |
| Windsurf | `.windsurf/` | `~/.windsurf/` |
| Cline | `.cline/` | `~/.cline/` |
| Zed | `.zed/` | `~/.config/zed/` |
| Continue | `.continue/` | `~/.continue/` |

**Rationale**:
- Local first : le contexte projet est plus pertinent
- Priorité Claude : IDE principal pour Rekall (skill native)

---

## 5. Article 99 - Versions et Recommandation

### Decision: 3 versions avec recommandation dynamique

**Choix**: MICRO (~50 tokens), COURT (~350 tokens), EXTENSIF (~1000 tokens).

**Logique de recommandation**:

| Contexte détecté | Version | Raison |
|------------------|---------|--------|
| Skill Claude installée (global OU local) | MICRO | Documentation dans skill, juste rappel |
| MCP configuré (sans skill Claude) | COURT | Outils MCP disponibles, workflow compact |
| CLI seulement | EXTENSIF | Documentation complète nécessaire |

**Contenu par version**:

- **MICRO**: Principe (2 lignes) + types + 3 commandes essentielles
- **COURT**: + workflow détaillé + intégration Claude Code
- **EXTENSIF**: + serveur MCP + liens + généralisation + hooks

**Rationale**:
- Optimisation tokens dans constitution Speckit
- La skill Claude contient déjà toute la doc → MICRO suffit
- MCP fournit les outils → COURT suffit pour le workflow
- CLI seul → besoin de tout documenter

---

## 6. Gestion Scope Global vs Local

### Decision: Colonnes séparées avec installation indépendante

**Choix**: Interface avec 2 colonnes (Global / Local) par IDE.

**Comportement**:
- Chaque scope est indépendant (peut installer Global sans Local et vice-versa)
- La recommandation Article 99 tient compte des DEUX scopes
- Désinstallation partielle possible

**Paths**:

| IDE | Local | Global |
|-----|-------|--------|
| Claude Code | `.claude/commands/rekall.md` | `~/.claude/commands/rekall.md` |
| Cursor | `.cursor/rules/rekall.mdc` | N/A (pas de global) |
| Copilot | `.github/copilot-instructions.md` | N/A |
| Zed | `.zed/settings.json` | `~/.config/zed/settings.json` |

**Rationale**:
- Global = disponible partout, moins de duplication
- Local = spécifique projet, versionné avec le code
- Flexibilité maximale pour l'utilisateur

---

## 7. Performance & Context Window

### Best Practices MCP (sources live)

**Recommandations appliquées**:
1. **Désactiver MCP non utilisé** : Chaque serveur MCP consomme du context window
2. **Nettoyage régulier** : `claude mcp remove <name>` pour serveurs inutilisés
3. **Debug** : Flag `--mcp-debug` pour diagnostics
4. **Sécurité** : Variables d'environnement pour credentials, pas de hardcode

**Impact sur design**:
- L'installation doit être réversible proprement
- Afficher clairement le statut de chaque intégration
- Permettre désinstallation granulaire

---

## 8. Migration et Edge Cases

### Gestion des fichiers existants

**Stratégie**:
- Vérifier existence avant écriture
- Si fichier existe avec contenu custom → proposer merge ou avertir
- Si déjà patché → skip silencieux

### Upgrade de version

**Stratégie**:
- Stocker version dans commentaire du fichier
- Proposer upgrade lors de `rekall config`
- Backup avant upgrade

---

## Résumé des Décisions Techniques

| Aspect | Décision | Source |
|--------|----------|--------|
| Format MCP | JSON standard mcpServers | Claude Docs |
| Cursor format | .mdc (pas .cursorrules) | Cursor Forum |
| Bundle | Instructions + MCP + Hooks atomiques | Design interne |
| Détection | Local first, puis global | Design interne |
| Article 99 | 3 versions, recommandation dynamique | Brainstorming |
| Scope | Colonnes Global/Local indépendantes | Spec requirement |

---

## Sources Consultées

### Baseline (speckit/research/)
- `04-architectures-patterns.md` : Patterns MCP, architectures

### Live (WebSearch)
- [Claude Code MCP Documentation](https://docs.claude.com/en/docs/claude-code/mcp)
- [Scott Spence - Configuring MCP Tools](https://scottspence.com/posts/configuring-mcp-tools-in-claude-code)
- [Cursor Rules Documentation](https://docs.cursor.com/context/rules)
- [Cursor Forum - MDC Best Practices](https://forum.cursor.com/t/my-best-practices-for-mdc-rules-and-troubleshooting/50526)
- [Anthropic Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
