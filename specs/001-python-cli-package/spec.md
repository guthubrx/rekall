# Feature Specification: DevKMS - Developer Knowledge Management CLI

**Feature Branch**: `001-python-cli-package`
**Created**: 2025-12-07
**Status**: Draft
**Input**: User description: "DevKMS - Developer Knowledge Management System. CLI Python cross-platform pour capturer et retrouver bugs, patterns, decisions. Distribution PyPI. Intégrations multi-IDE (Claude Code, Cursor, Copilot, etc.)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Search Existing Knowledge (Priority: P1)

Un développeur rencontre un bug ou commence une nouvelle feature. Avant de chercher sur internet, il veut vérifier s'il a déjà résolu un problème similaire.

**Why this priority**: C'est le cas d'usage principal - retrouver des connaissances existantes pour éviter de résoudre deux fois le même problème. Sans recherche efficace, le système n'a aucune valeur.

**Independent Test**: Peut être testé en ajoutant manuellement quelques entrées dans la base puis en effectuant des recherches.

**Acceptance Scenarios**:

1. **Given** une base contenant des entrées sur "import circulaire React", **When** l'utilisateur tape `mem search "circular import"`, **Then** les entrées pertinentes s'affichent avec titre, type et niveau de confiance
2. **Given** une base vide, **When** l'utilisateur effectue une recherche, **Then** un message clair indique qu'aucun résultat n'a été trouvé
3. **Given** une requête avec des mots-clés multiples, **When** l'utilisateur tape `mem search "cache react query"`, **Then** la recherche retourne les entrées contenant un ou plusieurs de ces termes, triées par pertinence

---

### User Story 2 - Capture New Knowledge (Priority: P1)

Après avoir résolu un bug ou découvert un pattern utile, le développeur veut le sauvegarder pour le retrouver plus tard.

**Why this priority**: Égale à P1 car sans capture, pas de base de connaissances. Indissociable de la recherche.

**Independent Test**: Peut être testé en créant une entrée puis en vérifiant qu'elle apparaît dans les recherches.

**Acceptance Scenarios**:

1. **Given** un bug résolu, **When** l'utilisateur tape `mem add bug "Fix import circulaire" -t react,import`, **Then** une nouvelle entrée est créée avec un ID unique, le type "bug" et les tags spécifiés
2. **Given** une commande `mem add` sans contenu, **When** l'utilisateur valide, **Then** un éditeur s'ouvre pour saisir le contenu détaillé
3. **Given** un type invalide, **When** l'utilisateur tape `mem add invalid "titre"`, **Then** un message d'erreur liste les types valides (bug, pattern, decision, pitfall, config, reference)

---

### User Story 3 - Installation Simple (Priority: P1)

Un développeur veut installer DevKMS rapidement, quelle que soit sa plateforme (Windows, macOS, Linux).

**Why this priority**: P1 car sans installation facile, pas d'adoption. C'est le premier contact avec l'outil.

**Independent Test**: Peut être testé sur une machine vierge avec uniquement Python installé.

**Acceptance Scenarios**:

1. **Given** Python 3.11+ installé, **When** l'utilisateur tape `pip install devkms`, **Then** la commande `mem` devient disponible dans le PATH
2. **Given** une installation fraîche, **When** l'utilisateur tape `mem init`, **Then** la base de données est créée dans `~/.devkms/` avec le schéma correct
3. **Given** une base existante, **When** l'utilisateur réinstalle le package, **Then** les données existantes sont préservées

---

### User Story 4 - Intégration IDE/Agent (Priority: P2)

Un développeur veut que son assistant IA (Claude Code, Cursor, Copilot, etc.) utilise automatiquement DevKMS sans action manuelle.

**Why this priority**: P2 car c'est un "turbo" qui améliore l'expérience mais le CLI seul est déjà fonctionnel.

**Independent Test**: Peut être testé en installant l'intégration puis en vérifiant que le fichier de règles est créé.

**Acceptance Scenarios**:

1. **Given** Cursor installé, **When** l'utilisateur tape `mem install cursor`, **Then** le fichier `.cursorrules` (ou global) contient les instructions pour utiliser `mem`
2. **Given** Claude Code utilisé, **When** DevKMS est installé comme plugin, **Then** les skills sont disponibles et s'activent automatiquement avant debug/après résolution
3. **Given** un IDE non supporté, **When** l'utilisateur tape `mem install unknown`, **Then** un message liste les intégrations disponibles

---

### User Story 5 - Consultation des Sources de Recherche (Priority: P2)

Avant de faire des recherches web, le développeur veut consulter les sources curées pertinentes pour son domaine.

**Why this priority**: P2 car améliore la qualité des recherches mais n'est pas bloquant pour l'usage basique.

**Independent Test**: Peut être testé en consultant un fichier research et en vérifiant que les URLs sont valides.

**Acceptance Scenarios**:

1. **Given** un projet impliquant de l'IA, **When** l'utilisateur tape `mem research ai-agents`, **Then** les sources primaires et requêtes suggérées s'affichent
2. **Given** un thème inexistant, **When** l'utilisateur tape `mem research unknown`, **Then** la liste des thèmes disponibles s'affiche

---

### User Story 6 - Recherche Sémantique (Priority: P3)

Le développeur veut trouver des entrées sémantiquement similaires même sans mots-clés exacts.

**Why this priority**: P3 car nécessite une dépendance externe (Ollama/OpenAI) et la recherche full-text couvre la majorité des cas.

**Independent Test**: Peut être testé avec Ollama installé localement.

**Acceptance Scenarios**:

1. **Given** Ollama installé avec `nomic-embed-text`, **When** l'utilisateur tape `mem similar "optimisation de cache"`, **Then** les entrées sémantiquement proches s'affichent même sans le mot "cache" exact
2. **Given** aucun provider d'embeddings configuré, **When** l'utilisateur tape `mem similar "query"`, **Then** un fallback sur la recherche full-text est utilisé avec un message informatif

---

### Edge Cases

- Que se passe-t-il si la base de données est corrompue ? Message d'erreur clair avec suggestion de restauration depuis backup
- Comment gérer les caractères spéciaux dans les recherches ? Échappement automatique pour SQLite FTS5
- Que faire si `~/.devkms/` n'est pas accessible en écriture ? Message d'erreur avec suggestion de chemin alternatif via variable d'environnement
- Comment gérer les conflits si plusieurs processus écrivent simultanément ? SQLite WAL mode (Write-Ahead Logging) activé par défaut

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a `mem` command accessible depuis le terminal après installation
- **FR-002**: System MUST supporter les commandes: `init`, `add`, `search`, `similar`, `show`, `browse`, `export`, `install`, `deprecate`
- **FR-003**: System MUST stocker les données dans une base SQLite avec Full-Text Search (FTS5)
- **FR-004**: System MUST fonctionner sur Windows, macOS et Linux sans modification
- **FR-005**: System MUST être installable via `pip install devkms` ou `uv tool install devkms`
- **FR-006**: System MUST supporter 6 types d'entrées: bug, pattern, decision, pitfall, config, reference
- **FR-007**: System MUST permettre de taguer les entrées pour faciliter le filtrage
- **FR-008**: System MUST attribuer un niveau de confiance (0-5) à chaque entrée
- **FR-009**: System MUST fournir des templates d'intégration pour au moins 8 IDE/agents IA
- **FR-010**: System MUST inclure des fichiers de sources de recherche curées (research/)
- **FR-011**: System MUST initialiser automatiquement la base de données lors du premier usage
- **FR-012**: System MUST préserver les données existantes lors des mises à jour du package
- **FR-013**: System MUST afficher un avertissement lors de `mem export` si du contenu potentiellement sensible est détecté (patterns: API keys, passwords, tokens)
- **FR-014**: System MUST permettre de marquer une entrée comme obsolète avec référence optionnelle vers l'entrée qui la remplace

### Key Entities

- **Entry**: Une connaissance capturée (bug résolu, pattern, décision, etc.) avec titre, contenu, type, projet, tags, niveau de confiance, statut (active/obsolete), référence vers entrée remplaçante, dates de création/modification
- **Tag**: Mot-clé associé à une entrée pour faciliter le filtrage et la catégorisation
- **Research Source**: Fichier markdown contenant des URLs curées et requêtes suggérées pour un domaine thématique

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un utilisateur peut installer et effectuer sa première recherche en moins de 2 minutes
- **SC-002**: Une recherche full-text retourne des résultats en moins de 100ms pour une base de 10 000 entrées
- **SC-003**: L'installation fonctionne sur les 3 OS majeurs sans configuration supplémentaire
- **SC-004**: 100% des commandes principales disposent d'une aide accessible via `--help`
- **SC-005**: Les intégrations IDE sont installables en une seule commande (`mem install <ide>`)
- **SC-006**: Les fichiers de recherche couvrent au moins 10 domaines thématiques

## Scope & Boundaries

### In Scope

- CLI Python avec commandes de base (add, search, show, browse, export)
- Base de données SQLite locale avec FTS5
- Recherche sémantique optionnelle (Ollama/OpenAI)
- Templates d'intégration pour 8 IDE/agents
- Distribution via PyPI
- Fichiers de sources de recherche curées
- Skills pour Claude Code (plugin)

### Out of Scope

- Interface graphique (GUI)
- Synchronisation cloud entre machines
- Collaboration multi-utilisateurs
- API REST/HTTP
- Application mobile

## Assumptions

- Python 3.11+ est disponible sur la machine de l'utilisateur
- L'utilisateur a les droits d'écriture dans son répertoire home (`~/.devkms/`)
- SQLite 3.9+ est disponible (inclus dans Python standard library)
- Pour la recherche sémantique : Ollama ou clé API OpenAI disponible (optionnel)

## Dependencies

- **typer** : Framework CLI moderne avec auto-complétion
- **rich** : Affichage coloré et formaté dans le terminal
- **Bibliothèque standard Python** : sqlite3, pathlib, json, urllib

## Constraints

- Dépendances minimales (2 packages externes maximum)
- Pas de base de données externe requise (SQLite embarqué)
- Taille du package inférieure à 500KB (hors données research)
- Compatible Python 3.11+

## Clarifications

### Session 2025-12-07

- Q: Protection des données sensibles lors de l'export ? → A: Avertissement lors de `mem export` si contenu potentiellement sensible détecté
