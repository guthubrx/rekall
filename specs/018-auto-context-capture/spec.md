# Feature Specification: Auto-Capture Contexte Enrichi

**Feature Branch**: `018-auto-context-capture`
**Created**: 2025-12-12
**Status**: Draft
**Input**: Phase 2 de Feature 006 - Auto-capture contexte enrichi avec extraction automatique des 5 dernières conversations pertinentes, détection fichiers modifiés via git, marqueurs temporels, et hooks de rappel proactif multi-CLI
**Parent Spec**: [006-enriched-context](../006-enriched-context/spec.md)

## Clarifications

### Session 2025-12-12
- Q: Comment déterminer la "pertinence" des échanges à capturer ? → A: L'agent décide lui-même via un mode hybride : soit il fournit directement `conversation_excerpt`, soit il demande au système de proposer des candidats depuis le transcript et filtre ensuite.
- Q: Comment gérer les différents emplacements de transcript selon les IDE/CLI ? → A: Support multi-format avec parsers dédiés (JSONL, JSON, SQLite) et paramètre `_transcript_format` explicite.

## Contexte et Motivation

Cette feature complète la spec 006 (Contexte Enrichi) en automatisant ce qui était prévu mais non implémenté :

| Fonctionnalité | Spec 006 | État Actuel | Cette Feature |
|----------------|----------|-------------|---------------|
| `conversation_excerpt` | Auto-capture 10 messages | Manuel | Auto-capture 5 conversations pertinentes |
| `files_modified` | Auto via git diff | Manuel | Auto-détection git staged+unstaged |
| Temporal markers | Prévu | Non implémenté | Auto-génération time_of_day, day_of_week |
| Hook rappel proactif | Prévu | Non implémenté | Multi-CLI (Claude, Cursor, Continue.dev) |

## Research Findings

### Claude Code Hooks (Source: [Hooks Reference](https://docs.claude.com/en/docs/claude-code/hooks))
- Le payload des hooks inclut `transcript_path` pointant vers un fichier JSONL
- Le hook `Stop` permet d'injecter du contexte après la réponse de l'agent
- Le hook `PreCompact` permet de sauvegarder le transcript avant compaction

### Autres CLIs (Sources: [Windsurf vs Cursor](https://www.qodo.ai/blog/windsurf-vs-cursor/), [Continue.dev](https://docs.continue.dev/cli/quick-start))
- **Windsurf/Cursor** : Pas de système de hooks documenté pour accès au transcript
- **Continue.dev** : Supporte les git hooks mais pas d'accès programmatique au transcript
- **Conclusion** : L'auto-capture de conversation sera Claude Code-only initialement, les autres CLIs devront utiliser la capture manuelle ou l'option `auto_detect_files` uniquement

### Emplacements Transcript par IDE/CLI (Source: Recherche 2025-12-12)

| IDE/CLI | Support MCP | Format | Emplacement par défaut |
|---------|-------------|--------|------------------------|
| **Claude Code** | ✅ Oui | JSONL | `~/.claude/projects/[hash]/[session].jsonl` |
| **Cline** | ✅ Oui | JSON | `~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/tasks/` |
| **Roo Code** | ✅ Oui | JSON | `~/.config/Code/User/globalStorage/rooveterinaryinc.roo-cline/` |
| **Continue.dev** | ✅ Oui | JSON | `.continue/dev_data/` (projet local) |
| **Zed** | ✅ Oui | LMDB | `~/.local/share/zed/threads/` |
| **Windsurf** | ✅ Oui | ? | Non documenté publiquement |
| **Cursor** | ⚠️ Partiel | SQLite | `workspaceStorage/[hash]/state.vscdb` |
| **GitHub Copilot** | ⚠️ Partiel | JSON | `workspaceStorage/[hash]/chatSessions/` |
| **Amazon Q** | ⚠️ Partiel | SQLite | `~/Library/.../amazon-q/data.sqlite3` |

### Stratégie Multi-Format Transcript

**Formats supportés (v1) :**
- `claude-jsonl` : Format JSONL Claude Code (type: human|assistant, content, timestamp)
- `cline-json` : Format JSON Cline (api_conversation_history.json)
- `continue-json` : Format JSON Continue.dev
- `raw-json` : Format JSON générique (array de {role, content})

**Formats prévus (v2) :**
- `sqlite` : Pour Cursor, Amazon Q (requête SQL sur tables de messages)
- `lmdb` : Pour Zed (lecture binaire LMDB)

**Principe de portabilité MCP :**
- Le paramètre `_transcript_path` est toujours explicite (jamais deviné)
- Le paramètre `_transcript_format` indique le parser à utiliser
- Auto-détection du format basée sur l'extension si format non spécifié (.jsonl → claude-jsonl, .json → raw-json)

### Red Flags Identifiés
- Risque de dépendance Claude Code : Atténué par support multi-format et fallback gracieux
- Taille des conversations : Atténué par compression zlib (déjà en place)
- Formats propriétaires non documentés (Windsurf) : Fallback sur Mode 1 (agent fournit directement)

## User Scenarios & Testing

### User Story 1 - Auto-Capture Conversation (Priority: P0)

L'agent IA sauvegarde automatiquement le contexte de conversation pertinent lors de la création d'un souvenir, sans devoir copier/coller manuellement les échanges.

**Why this priority**: Core feature - réduit de 80% la friction de capture contextuelle. Sans cela, les souvenirs manquent du contexte crucial pour les retrouver.

**Mode Hybride de Capture** (décision de clarification 2025-12-12) :
- **Mode 1 - Agent Direct** : L'agent fournit directement `conversation_excerpt` avec les échanges qu'il juge pertinents (1 appel MCP, portable)
- **Mode 2 - Système Assisté** : Si l'agent manque de contexte (conversation compactée), il active `auto_capture_conversation: true` avec `_transcript_path`. Le système lit le transcript, retourne les N derniers échanges candidats, et l'agent filtre ceux pertinents (2 appels MCP, utilise le transcript complet)

**Independent Test**: Créer un souvenir via MCP en Mode 1 (agent fournit `conversation_excerpt`) et en Mode 2 (système propose depuis transcript).

**Acceptance Scenarios**:

1. **Given** l'agent a le contexte complet en mémoire, **When** il appelle `rekall_add` avec `conversation_excerpt` rempli directement, **Then** le système stocke les échanges fournis sans traitement supplémentaire (Mode 1)
2. **Given** l'agent manque de contexte et veut assistance, **When** il appelle `rekall_add` avec `auto_capture_conversation: true`, `_transcript_path` et `_transcript_format`, **Then** le système retourne les 20 derniers échanges candidats pour filtrage
3. **Given** l'agent reçoit les candidats, **When** il rappelle avec `conversation_excerpt_indices: [3, 7, 12, 15, 18]`, **Then** le système stocke uniquement ces 5 échanges
4. **Given** le transcript n'est pas accessible (CLI non supporté ou format inconnu), **When** l'agent appelle en Mode 2, **Then** le système retourne une erreur explicite invitant à utiliser Mode 1
5. **Given** le transcript existe mais contient moins de 20 échanges, **When** l'extraction est déclenchée, **Then** le système retourne tous les échanges disponibles

---

### User Story 2 - Auto-Détection Fichiers Modifiés (Priority: P1)

Le système détecte automatiquement les fichiers modifiés via git lors de la création d'un souvenir, enrichissant le contexte sans effort manuel.

**Why this priority**: Complète le contexte avec les fichiers touchés, crucial pour retrouver des bugs liés à des fichiers spécifiques.

**Independent Test**: Créer un souvenir avec `auto_detect_files: true` dans un repo git avec des fichiers modifiés et vérifier que `files_modified` les liste.

**Acceptance Scenarios**:

1. **Given** l'utilisateur a modifié 3 fichiers (2 staged, 1 unstaged), **When** l'agent appelle `rekall_add` avec `auto_detect_files: true` et `_cwd`, **Then** `files_modified` contient les 3 fichiers uniques
2. **Given** le répertoire n'est pas un repo git, **When** l'auto-détection est activée, **Then** le système accepte l'entrée avec `files_modified` vide (fallback gracieux)
3. **Given** aucun fichier n'est modifié, **When** l'auto-détection est activée, **Then** `files_modified` est une liste vide

---

### User Story 3 - Temporal Markers Auto-Générés (Priority: P2)

Le système ajoute automatiquement des marqueurs temporels pour situer le souvenir dans le temps (moment de la journée, jour de la semaine).

**Why this priority**: Aide à retrouver des souvenirs par contexte temporel ("le bug du vendredi soir", "le fix du matin").

**Independent Test**: Créer un souvenir à 14h30 un mercredi et vérifier que `time_of_day: afternoon` et `day_of_week: wednesday` sont auto-générés.

**Acceptance Scenarios**:

1. **Given** un souvenir est créé à 10h00, **When** `auto_temporal_markers` est activé ou non spécifié, **Then** `time_of_day: morning` et `day_of_week` corrects sont ajoutés
2. **Given** l'utilisateur fournit explicitement `time_of_day: custom`, **When** le souvenir est créé, **Then** la valeur manuelle prévaut sur l'auto-génération
3. **Given** le souvenir est créé à 23h45, **When** les marqueurs sont générés, **Then** `time_of_day: night`

---

### User Story 4 - Hook de Rappel Proactif (Priority: P1)

Le système rappelle à l'agent de sauvegarder dans Rekall quand il détecte qu'un problème vient d'être résolu.

**Why this priority**: Élimine l'oubli de sauvegarde - principal problème de capture actuel.

**Independent Test**: Configurer le hook Stop, résoudre un bug (message contenant "fixed"), et vérifier que le rappel Rekall est injecté.

**Acceptance Scenarios**:

1. **Given** l'agent vient de dire "le bug est résolu", **When** le hook Stop s'exécute, **Then** un rappel Rekall est injecté dans le contexte
2. **Given** l'agent a déjà mentionné "rekall" dans sa réponse, **When** le hook détecte "résolu", **Then** aucun rappel n'est injecté (évite le spam)
3. **Given** la réponse ne contient pas de pattern de résolution, **When** le hook s'exécute, **Then** aucune action n'est prise

---

### User Story 5 - Installation Multi-CLI (Priority: P3)

L'utilisateur peut installer les hooks et configurations spécifiques à son CLI via une commande dédiée.

**Why this priority**: Permet l'adoption de la feature sur différents environnements de développement.

**Independent Test**: Exécuter `rekall hooks install --cli claude` et vérifier que le hook est installé dans `~/.claude/hooks/`.

**Acceptance Scenarios**:

1. **Given** l'utilisateur utilise Claude Code, **When** `rekall hooks install --cli claude` est exécuté, **Then** le hook `rekall-reminder.sh` est créé dans `~/.claude/hooks/` avec les permissions correctes
2. **Given** l'utilisateur utilise un CLI non supporté, **When** l'installation est tentée, **Then** un message explique que seules les fonctionnalités git (`auto_detect_files`) sont disponibles

---

### Edge Cases

- Que se passe-t-il si le transcript JSONL est corrompu ? → Retourner `conversation_excerpt` vide avec warning
- Comment gérer les transcripts très longs (>1000 échanges) ? → Lire le fichier en streaming depuis la fin
- Que se passe-t-il si git timeout (>5 secondes) ? → Retourner liste vide, log warning
- Comment gérer les fichiers binaires dans git diff ? → Filtrer par extension (exclure images, binaires)

## Requirements

### Functional Requirements

**Mode 1 - Agent Direct :**
- **FR-001**: Le système DOIT accepter `conversation_excerpt` directement fourni par l'agent sans traitement

**Mode 2 - Système Assisté :**
- **FR-002**: Le système DOIT accepter les paramètres `auto_capture_conversation`, `_transcript_path` et `_transcript_format` dans `rekall_add`
- **FR-003**: Le système DOIT supporter les formats de transcript : `claude-jsonl`, `cline-json`, `continue-json`, `raw-json`
- **FR-004**: Le système DOIT retourner les 20 derniers échanges candidats quand `auto_capture_conversation: true`
- **FR-005**: Le système DOIT accepter `conversation_excerpt_indices` pour finaliser la sélection des échanges pertinents
- **FR-006**: Le système DOIT auto-détecter le format basé sur l'extension si `_transcript_format` non fourni

**Auto-détection fichiers :**
- **FR-007**: Le système DOIT accepter les paramètres `auto_detect_files` et `_cwd` dans le contexte de `rekall_add`
- **FR-008**: Le système DOIT combiner les fichiers staged et unstaged de git en liste dédupliquée

**Marqueurs temporels :**
- **FR-009**: Le système DOIT auto-générer `time_of_day` et `day_of_week` si non fournis

**Hooks de rappel :**
- **FR-010**: Le système DOIT fournir un script de hook Stop pour Claude Code détectant les patterns de résolution
- **FR-011**: Le système DOIT fournir une commande CLI `rekall hooks install` pour installer les hooks

### Key Entities

- **TranscriptMessage**: Un échange dans le transcript (type: human|assistant, content: string, timestamp)
- **TranscriptFormat**: Enum des formats supportés (claude-jsonl, cline-json, continue-json, raw-json)
- **TranscriptParser**: Interface pour parser les différents formats de transcript vers TranscriptMessage[]
- **CandidateExchanges**: Réponse du Mode 2 contenant les échanges candidats avec leurs indices
- **TemporalMarkers**: Contexte temporel (time_of_day: morning|afternoon|evening|night, day_of_week: monday..sunday)
- **HookConfig**: Configuration du hook de rappel (patterns de résolution, cooldown, CLI cible)

## Success Criteria

### Measurable Outcomes

- **SC-001**: 80%+ des nouveaux souvenirs créés via MCP avec `auto_capture_conversation: true` ont un `conversation_excerpt` non vide (quand transcript disponible)
- **SC-002**: 70%+ des souvenirs créés dans un repo git avec `auto_detect_files: true` ont `files_modified` non vide
- **SC-003**: 100% des souvenirs ont `time_of_day` et `day_of_week` remplis (auto ou manuel)
- **SC-004**: Le hook de rappel se déclenche dans 50%+ des cas où un pattern de résolution est détecté
- **SC-005**: Le temps d'extraction du transcript reste inférieur à 500ms pour des transcripts de moins de 1000 échanges
- **SC-006**: Aucune régression sur les tests existants de la feature 006

## Assumptions

- Les formats de transcript des IDE majeurs (Claude Code JSONL, Cline JSON, Continue.dev JSON) restent stables
- Git est disponible dans le PATH sur les systèmes où `auto_detect_files` est utilisé
- Les hooks Claude Code supportent le format de sortie JSON documenté
- La compression zlib existante gère efficacement les conversations longues sans troncature
- L'agent est capable de déterminer s'il a assez de contexte pour fournir `conversation_excerpt` directement (Mode 1) ou s'il a besoin d'assistance (Mode 2)
- Les IDE avec formats non documentés (Windsurf) ou propriétaires (Cursor SQLite) utiliseront Mode 1 exclusivement en v1
