# Feature Specification: Auto-Capture Contexte Enrichi

**Feature Branch**: `018-auto-context-capture`
**Created**: 2025-12-12
**Status**: Draft
**Input**: Phase 2 de Feature 006 - Auto-capture contexte enrichi avec extraction automatique des 5 dernières conversations pertinentes, détection fichiers modifiés via git, marqueurs temporels, et hooks de rappel proactif multi-CLI
**Parent Spec**: [006-enriched-context](../006-enriched-context/spec.md)

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

### Red Flags Identifiés
- Risque de dépendance Claude Code : Atténué par fallback gracieux (conversation manuelle si pas de transcript)
- Taille des conversations : Atténué par compression zlib (déjà en place)

## User Scenarios & Testing

### User Story 1 - Auto-Capture Conversation (Priority: P0)

L'agent IA sauvegarde automatiquement le contexte de conversation pertinent lors de la création d'un souvenir, sans devoir copier/coller manuellement les échanges.

**Why this priority**: Core feature - réduit de 80% la friction de capture contextuelle. Sans cela, les souvenirs manquent du contexte crucial pour les retrouver.

**Independent Test**: Créer un souvenir via MCP avec `auto_capture_conversation: true` et vérifier que `conversation_excerpt` contient les 5 derniers échanges pertinents.

**Acceptance Scenarios**:

1. **Given** l'agent a résolu un bug et veut sauvegarder, **When** il appelle `rekall_add` avec `auto_capture_conversation: true` et `_transcript_path`, **Then** le système extrait les 5 dernières paires question/réponse et les stocke dans `conversation_excerpt`
2. **Given** le transcript n'est pas accessible (CLI non-Claude), **When** l'agent appelle `rekall_add` avec `auto_capture_conversation: true` sans `_transcript_path`, **Then** le système accepte l'entrée avec `conversation_excerpt` vide et log un warning
3. **Given** le transcript existe mais contient moins de 5 conversations, **When** l'extraction est déclenchée, **Then** le système extrait toutes les conversations disponibles sans erreur

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

- **FR-001**: Le système DOIT accepter les paramètres `auto_capture_conversation` et `_transcript_path` dans le contexte de `rekall_add`
- **FR-002**: Le système DOIT extraire les 5 dernières paires question/réponse pertinentes du transcript JSONL
- **FR-003**: Le système DOIT accepter les paramètres `auto_detect_files` et `_cwd` dans le contexte de `rekall_add`
- **FR-004**: Le système DOIT combiner les fichiers staged et unstaged de git en liste dédupliquée
- **FR-005**: Le système DOIT auto-générer `time_of_day` et `day_of_week` si non fournis
- **FR-006**: Le système DOIT fournir un script de hook Stop pour Claude Code détectant les patterns de résolution
- **FR-007**: Le système DOIT fournir une commande CLI `rekall hooks install` pour installer les hooks

### Key Entities

- **TranscriptMessage**: Un échange dans le transcript (type: human|assistant, content: string, timestamp)
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

- Le format JSONL du transcript Claude Code reste stable (type: "human"|"assistant", content: string)
- Git est disponible dans le PATH sur les systèmes où `auto_detect_files` est utilisé
- Les hooks Claude Code supportent le format de sortie JSON documenté
- La compression zlib existante gère efficacement les conversations longues sans troncature
