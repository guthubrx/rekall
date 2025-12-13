# Feature Specification: Multi-IDE Rekall Integration

**Feature Branch**: `019-multi-ide-integration`
**Created**: 2025-12-13
**Status**: Draft
**Input**: Intégration optimisée de Rekall pour chaque IDE (Claude Code, Cursor, Copilot, Windsurf, Cline, Zed, Continue) avec détection automatique, instructions spécifiques par IDE, Article 99 adaptatif, et patches Speckit MCP/CLI selon les capacités de l'IDE

## Design Decisions

### Installation simplifiée et unifiée

L'écran `rekall config` est restructuré pour être plus simple et cohérent :

1. **Section INTÉGRATIONS unifiée** : Chaque IDE = un bundle complet (instructions + MCP + hooks). Plus de séparation artificielle entre "IDE" et "MCP Server".

2. **Section SPECKIT séparée** : Speckit est un framework, pas un IDE. Il a sa propre section avec :
   - Choix de la version Article 99 (MICRO/COURT/EXTENSIF) avec **recommandation dynamique**
   - Patches des commandes /speckit.*
   - Scope Global vs Local

3. **Gestion Global vs Local** : Chaque intégration peut être installée :
   - **Global** (`~/`) : Disponible dans tous les projets
   - **Local** (`./`) : Spécifique au projet courant

### Logique de recommandation Article 99

Le système recommande automatiquement la version optimale selon le contexte :

| Contexte détecté | Version recommandée | Raison |
|------------------|---------------------|--------|
| Skill Claude installée (global ou local) | MICRO (~50 tokens) | Documentation complète dans la skill |
| MCP configuré (sans skill Claude) | COURT (~350 tokens) | Outils MCP disponibles, juste workflow |
| CLI seulement (pas de MCP) | EXTENSIF (~1000 tokens) | Documentation complète nécessaire |

La recommandation prend en compte les installations **global ET local** pour afficher le conseil le plus pertinent.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Interface de configuration simplifiée (Priority: P1)

Un développeur lance `rekall config` et voit une interface unifiée avec deux sections principales : INTÉGRATIONS (tous les IDEs) et SPECKIT (framework séparé). Chaque IDE est présenté comme un bundle complet, pas comme des composants séparés.

**Why this priority**: L'UX simplifiée est la base de l'adoption. L'utilisateur ne devrait pas avoir à comprendre la différence entre skill, MCP, et rules.

**Independent Test**: Vérifier que l'interface affiche les deux sections distinctes avec tous les IDEs listés comme bundles.

**Acceptance Scenarios**:

1. **Given** un développeur qui lance `rekall config`, **When** l'écran s'affiche, **Then** il voit une section INTÉGRATIONS avec tous les IDEs (Claude, Cursor, Copilot, Windsurf, Cline, Zed, Continue) listés comme bundles complets.

2. **Given** un développeur dans la section INTÉGRATIONS, **When** il sélectionne "Claude Code", **Then** il voit que l'installation inclut "skill + MCP + hooks" (pas de choix séparé).

3. **Given** un développeur dans la section INTÉGRATIONS, **When** il regarde chaque IDE, **Then** il voit deux colonnes "Global" et "Local" pour choisir le scope d'installation.

4. **Given** Speckit installé sur le système, **When** le développeur navigue dans `rekall config`, **Then** il voit une section SPECKIT séparée des INTÉGRATIONS.

---

### User Story 2 - Installation automatique avec détection IDE (Priority: P1)

Le système détecte automatiquement l'IDE installé (local puis global) et pré-sélectionne les bonnes options.

**Why this priority**: L'expérience zero-config est cruciale pour l'adoption.

**Independent Test**: Peut être testé en vérifiant que `rekall config` détecte correctement l'IDE et propose les bonnes options d'installation.

**Acceptance Scenarios**:

1. **Given** un développeur avec Cursor installé (~/.cursor/ existe), **When** il lance `rekall config`, **Then** le système affiche "IDE détecté: Cursor" en haut de l'écran.

2. **Given** un développeur avec Claude Code installé (~/.claude/ existe), **When** il lance `rekall config`, **Then** le système affiche "IDE détecté: Claude Code" et la ligne Claude est mise en évidence.

3. **Given** un développeur avec plusieurs IDEs installés, **When** il lance `rekall config`, **Then** le système détecte l'IDE prioritaire (Claude > Cursor > Copilot > ...) et l'affiche.

4. **Given** un développeur sans IDE reconnu, **When** il lance `rekall config`, **Then** le système affiche "IDE: unknown".

---

### User Story 3 - Instructions optimisées par IDE (Priority: P1)

Chaque IDE reçoit des instructions Rekall adaptées à ses capacités : progressive disclosure pour Claude, .mdc rules pour Cursor, copilot-instructions.md pour Copilot, etc. L'installation bundle tout (instructions + MCP + hooks).

**Why this priority**: C'est l'objectif principal de la feature - optimiser l'expérience par IDE pour minimiser les tokens et maximiser l'efficacité.

**Independent Test**: Vérifier que chaque fichier d'instructions est installé au bon emplacement avec le bon contenu.

**Acceptance Scenarios**:

1. **Given** IDE = Claude Code et scope = Global, **When** l'utilisateur installe, **Then** la skill progressive disclosure est installée dans ~/.claude/commands/rekall.md + ~/.claude/commands/rekall/*.md + MCP config + hooks.

2. **Given** IDE = Claude Code et scope = Local, **When** l'utilisateur installe, **Then** la skill est installée dans .claude/commands/rekall.md + .claude/commands/rekall/*.md.

3. **Given** IDE = Cursor et scope = Global, **When** l'utilisateur installe, **Then** les rules + MCP sont installés dans ~/.cursor/.

4. **Given** IDE = GitHub Copilot et scope = Local, **When** l'utilisateur installe, **Then** une section Rekall est ajoutée dans .github/copilot-instructions.md + .vscode/mcp.json.

---

### User Story 4 - Article 99 avec recommandation dynamique (Priority: P2)

Dans la section SPECKIT, l'utilisateur choisit la version de l'Article 99 parmi MICRO/COURT/EXTENSIF. Le système affiche une **recommandation** basée sur les intégrations installées (global ET local).

**Why this priority**: Optimise le contexte Speckit mais dépend de la détection IDE (P1). Impact significatif sur les tokens de constitution.

**Independent Test**: Vérifier que la recommandation affichée correspond aux intégrations installées.

**Acceptance Scenarios**:

1. **Given** skill Claude installée en global, **When** l'utilisateur ouvre la section SPECKIT, **Then** il voit "★ recommandé: Micro (skill Claude installée en global)".

2. **Given** skill Claude installée en local seulement, **When** l'utilisateur ouvre la section SPECKIT, **Then** il voit "★ recommandé: Micro (skill Claude installée en local)".

3. **Given** MCP Cursor configuré mais pas de skill Claude, **When** l'utilisateur ouvre la section SPECKIT, **Then** il voit "★ recommandé: Court (MCP configuré)".

4. **Given** aucune intégration MCP installée, **When** l'utilisateur ouvre la section SPECKIT, **Then** il voit "★ recommandé: Extensif (CLI seulement)".

5. **Given** l'utilisateur ignore la recommandation et choisit une autre version, **When** il installe, **Then** la version choisie est installée (pas la recommandée).

6. **Given** Speckit NON installé (~/.speckit/ absent), **When** l'utilisateur navigue dans `rekall config`, **Then** la section SPECKIT n'est PAS affichée.

---

### User Story 5 - Patches Speckit adaptatifs MCP/CLI (Priority: P2)

Les patches des commandes Speckit (/speckit.implement, /speckit.plan, etc.) utilisent les outils MCP quand disponibles, sinon le CLI.

**Why this priority**: Complète l'intégration Speckit en adaptant les workflows. Dépend de la détection IDE.

**Independent Test**: Vérifier que les patches injectés dans les commandes Speckit utilisent MCP ou CLI selon l'IDE.

**Acceptance Scenarios**:

1. **Given** intégration MCP installée (n'importe quel IDE), **When** /speckit.implement est patché, **Then** le patch contient `rekall_search` (outil MCP).

2. **Given** aucune intégration MCP installée, **When** /speckit.implement est patché, **Then** le patch contient `rekall search "..."` (commande CLI).

3. **Given** intégration MCP installée, **When** /speckit.plan est patché, **Then** le patch recommande `rekall_search` avec types pattern,decision.

---

### User Story 6 - Installation multi-IDE et multi-scope (Priority: P3)

Un développeur peut installer plusieurs intégrations IDE simultanément, et choisir le scope (global/local) pour chacune indépendamment.

**Why this priority**: Cas d'usage avancé, la plupart des utilisateurs n'ont qu'un IDE principal.

**Independent Test**: Vérifier qu'on peut installer plusieurs intégrations IDE avec différents scopes.

**Acceptance Scenarios**:

1. **Given** un développeur avec Claude Code ET Cursor, **When** il accède à `rekall config`, **Then** il peut installer Claude en Global ET Cursor en Local.

2. **Given** intégrations Claude (global) + Cursor (local) actives, **When** l'utilisateur désinstalle Cursor local, **Then** seule l'intégration Cursor locale est supprimée, Claude global reste.

3. **Given** un IDE installé en Global ET en Local, **When** l'utilisateur regarde la section INTÉGRATIONS, **Then** les deux cases sont cochées.

---

### Edge Cases

- Que se passe-t-il si un fichier d'instructions IDE existe déjà avec du contenu custom ? Merger intelligemment ou avertir l'utilisateur.
- Comment gérer les mises à jour de version des instructions ? Versionner et proposer upgrade.
- Que se passe-t-il si la détection IDE est incorrecte ? Permettre override manuel dans `rekall config`.
- Comment gérer un IDE qui ajoute le support MCP après installation ? Proposer upgrade lors du prochain `rekall config`.
- Que faire si plusieurs IDEs sont détectés au niveau projet ET utilisateur ? Priorité : local > global, puis ordre de priorité IDE.
- Que se passe-t-il si la même intégration est installée en Global ET en Local ? Les deux coexistent, la recommandation Article 99 prend en compte les deux.
- Comment gérer la désinstallation partielle (Global uniquement ou Local uniquement) ? L'interface permet de décocher indépendamment.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST détecter automatiquement l'IDE installé en vérifiant les fichiers/dossiers locaux (projet) puis globaux (utilisateur).
- **FR-002**: System MUST supporter 7 IDEs : Claude Code, Cursor, GitHub Copilot, Windsurf, Cline, Zed, Continue.dev.
- **FR-003**: System MUST installer les instructions optimisées pour chaque IDE dans le format et emplacement approprié.
- **FR-004**: System MUST adapter la taille de l'Article 99 selon les capacités de l'IDE (MICRO/COURT/EXTENSIF).
- **FR-005**: System MUST ignorer l'intégration Speckit si Speckit n'est pas installé (~/.speckit/constitution.md absent).
- **FR-006**: System MUST permettre l'installation/désinstallation indépendante de chaque intégration IDE.
- **FR-007**: System MUST adapter les patches Speckit pour utiliser MCP ou CLI selon l'IDE.
- **FR-008**: System MUST afficher l'IDE détecté dans l'interface de configuration.
- **FR-009**: System MUST permettre un override manuel de l'IDE détecté.
- **FR-010**: System MUST prioriser la détection locale (projet) sur globale (utilisateur).
- **FR-011**: System MUST utiliser l'ordre de priorité : Claude > Cursor > Copilot > Windsurf > Cline > Zed > Continue > unknown.
- **FR-012**: System MUST permettre l'installation en scope Global (~/) ou Local (./) pour chaque intégration IDE.
- **FR-013**: System MUST afficher une recommandation dynamique pour la version Article 99 basée sur les intégrations installées (global ET local).
- **FR-014**: System MUST présenter les intégrations IDE comme des bundles complets (instructions + MCP + hooks) sans séparation.
- **FR-015**: System MUST afficher la section SPECKIT uniquement si Speckit est installé (~/.speckit/ présent).

### Key Entities

- **IDE**: Représente un environnement de développement supporté avec ses capacités (nom, supports_mcp, supports_progressive_disclosure, local_path, global_path, instructions_format).
- **Integration**: Configuration Rekall pour un IDE spécifique (ide, scope [global|local], instructions_content, mcp_config_path, installed).
- **Article99Version**: Version de l'article constitution (MICRO ~50 tokens, COURT ~350 tokens, EXTENSIF ~1000 tokens).
- **SpeckitPatch**: Modification d'une commande Speckit avec mode adaptatif (command_name, mcp_version, cli_version).
- **Scope**: Niveau d'installation (GLOBAL = ~/, LOCAL = ./) déterminant la portée de l'intégration.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% des 7 IDEs supportés ont une intégration fonctionnelle et testée.
- **SC-002**: La détection automatique identifie correctement l'IDE dans 95% des configurations standard.
- **SC-003**: Les instructions par IDE consomment au maximum les tokens spécifiés : Claude ~270 trigger, Cursor ~200, Copilot ~100, Windsurf ~250, Cline ~200, Zed ~200.
- **SC-004**: L'Article 99 MICRO ne dépasse pas 60 tokens, COURT 400 tokens, EXTENSIF 1100 tokens.
- **SC-005**: L'installation complète (détection + instructions + MCP + Speckit si présent) prend moins de 5 secondes.
- **SC-006**: L'expérience utilisateur est cohérente entre IDEs : même workflow "Consulter AVANT, Capturer APRÈS".

## Assumptions

- Les chemins de configuration des IDEs sont stables et documentés par leurs éditeurs.
- Les utilisateurs ont un seul IDE principal par projet (multi-IDE est un cas avancé).
- Le format MCP JSON est compatible entre les différents IDEs qui le supportent.
- Speckit utilise une constitution dans ~/.speckit/constitution.md.
- Les IDEs supportant MCP utilisent un format de configuration compatible Claude Desktop.

## Dependencies

- MCP Server Rekall existant (Feature 017+).
- Skill Claude Code progressive disclosure (déjà implémentée).
- TUI de configuration existant (`rekall config`).
- Écran d'installation MCP existant (pour Claude Code).
