# Feature Specification: XDG-Compliant Installation Paths

**Feature Branch**: `003-xdg-install-paths`
**Created**: 2024-12-07
**Status**: Draft
**Input**: User description: "Je veux que l'utilisateur puisse choisir entre installation globale ou projet. Respecter la spécification XDG pour $HOME/.config/rekall (config), $HOME/.local/share/rekall (data), ou permettre un chemin personnalisé."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Default Installation Experience (Priority: P1)

Un nouvel utilisateur installe Rekall pour la première fois. Sans configuration préalable, le système utilise automatiquement les chemins XDG standard sur Linux/macOS, offrant une expérience "ça marche tout seul" conforme aux bonnes pratiques.

**Why this priority**: L'expérience par défaut doit être excellente pour 90% des utilisateurs qui n'ont pas besoin de personnalisation.

**Independent Test**: Installer Rekall sur une machine vierge et vérifier que les fichiers sont créés aux bons emplacements XDG sans aucune configuration manuelle.

**Acceptance Scenarios**:

1. **Given** une machine Linux sans configuration Rekall, **When** l'utilisateur exécute `rekall` pour la première fois, **Then** la config est créée dans `$XDG_CONFIG_HOME/rekall/` (ou `~/.config/rekall/` par défaut) et la DB dans `$XDG_DATA_HOME/rekall/` (ou `~/.local/share/rekall/`)

2. **Given** une machine macOS sans configuration Rekall, **When** l'utilisateur exécute `rekall` pour la première fois, **Then** la config est créée dans `~/.config/rekall/` et la DB dans `~/.local/share/rekall/` (XDG, identique à Linux)

3. **Given** les variables d'environnement XDG définies (`$XDG_CONFIG_HOME=/custom/config`), **When** l'utilisateur exécute `rekall`, **Then** le système respecte ces variables

---

### User Story 2 - Installation Projet Local (Priority: P2)

Une équipe veut partager une base de connaissances Rekall spécifique à leur projet. Ils configurent Rekall pour stocker les données dans le dossier du projet, versionnable avec Git.

**Why this priority**: Le travail en équipe est un cas d'usage majeur où une DB partagée par projet est essentielle.

**Independent Test**: Initialiser Rekall dans un projet Git et vérifier que les données sont dans `.rekall/` du projet.

**Acceptance Scenarios**:

1. **Given** un projet Git, **When** l'utilisateur exécute `rekall init --local`, **Then** un dossier `.rekall/` est créé à la racine du projet avec config et DB

2. **Given** un projet avec `.rekall/` existant, **When** l'utilisateur exécute `rekall` dans ce projet, **Then** Rekall utilise automatiquement la DB locale du projet (priorité sur global)

3. **Given** un projet avec `.rekall/`, **When** un autre membre de l'équipe clone le repo, **Then** il peut immédiatement utiliser la base de connaissances partagée

---

### User Story 3 - Chemin Personnalisé (Priority: P3)

Un utilisateur avancé veut stocker sa base Rekall sur un NAS, un disque externe, ou un emplacement spécifique. Il configure un chemin personnalisé via variable d'environnement ou fichier de config.

**Why this priority**: Cas avancé pour utilisateurs avec besoins spécifiques (stockage réseau, backup, etc.)

**Independent Test**: Configurer `REKALL_HOME=/mnt/nas/rekall` et vérifier que toutes les données y sont stockées.

**Acceptance Scenarios**:

1. **Given** la variable `REKALL_HOME=/custom/path`, **When** l'utilisateur exécute `rekall`, **Then** config et DB sont dans `/custom/path/`

2. **Given** un fichier `~/.config/rekall/config.toml` avec `data_dir = "/mnt/backup/rekall"`, **When** l'utilisateur exécute `rekall`, **Then** la DB est dans `/mnt/backup/rekall/` mais la config reste en place

3. **Given** à la fois `REKALL_HOME` défini et un projet local `.rekall/`, **When** l'utilisateur exécute `rekall` dans le projet, **Then** le projet local a priorité (avec option `--global` pour forcer global)

---

### User Story 4 - Migration Depuis Installation Existante (Priority: P3)

Un utilisateur existant met à jour Rekall vers la nouvelle version avec chemins XDG. Ses données existantes sont préservées et migrées automatiquement si nécessaire.

**Why this priority**: Ne pas perdre les données des utilisateurs existants est critique mais concerne une transition unique.

**Independent Test**: Installer nouvelle version sur machine avec ancienne installation et vérifier migration transparente.

**Acceptance Scenarios**:

1. **Given** une installation existante avec `~/.rekall/` (ancien format), **When** l'utilisateur met à jour et exécute `rekall`, **Then** les données sont migrées vers le nouvel emplacement XDG avec message explicatif

2. **Given** une migration en cours, **When** l'utilisateur refuse la migration, **Then** l'ancien emplacement continue de fonctionner (mode compatibilité)

---

### Edge Cases

- Si `$XDG_CONFIG_HOME` pointe vers un emplacement sans droits d'écriture → Échouer avec message d'erreur clair (pas de fallback silencieux)
- Comment gérer un projet local `.rekall/` corrompu (fallback sur global) ?
- Comment gérer les permissions sur la DB en mode équipe (plusieurs utilisateurs) ?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST détecter automatiquement la plateforme (Linux, macOS, Windows) et appliquer les conventions de chemins appropriées
- **FR-002**: System MUST respecter les variables d'environnement XDG (`$XDG_CONFIG_HOME`, `$XDG_DATA_HOME`, `$XDG_CACHE_HOME`) quand définies
- **FR-003**: System MUST supporter l'initialisation locale via `rekall init --local` créant `.rekall/` dans le dossier courant
- **FR-004**: System MUST détecter un dossier `.rekall/` dans le dossier courant uniquement (pas de recherche ancêtres) et l'utiliser en priorité
- **FR-005**: System MUST supporter la variable d'environnement `REKALL_HOME` pour chemin personnalisé global
- **FR-006**: System MUST permettre de configurer `data_dir` dans le fichier de configuration pour séparer config et données
- **FR-007**: System MUST fournir une commande `rekall config --show` affichant tous les chemins actifs et leur source (défaut, env, config, local)
- **FR-008**: System MUST migrer automatiquement les anciennes installations (`~/.rekall/`) vers le nouveau format avec confirmation utilisateur
- **FR-009**: System MUST supporter l'option `--global` pour forcer l'utilisation de la DB globale même dans un projet local

### Ordre de Priorité des Sources

Le système résout les chemins selon cet ordre (premier trouvé gagne) :

1. Option CLI (`--db-path`, `--config-path`)
2. Variables d'environnement (`REKALL_HOME`, `REKALL_DB_PATH`)
3. Projet local (`.rekall/` dans le dossier courant uniquement)
4. Fichier de configuration utilisateur
5. Variables XDG (`$XDG_CONFIG_HOME`, `$XDG_DATA_HOME`)
6. Défauts plateforme :
   - Linux/macOS: `~/.config/rekall/` (config) + `~/.local/share/rekall/` (data)
   - Windows: `%APPDATA%\rekall\` (ex: `C:\Users\nom\AppData\Roaming\rekall`)

### Key Entities

- **Configuration**: Paramètres utilisateur (préférences, intégrations IDE actives)
- **Database**: Base SQLite contenant les entrées de connaissances
- **Cache**: Données temporaires (index de recherche, etc.)
- **Project Config**: Configuration spécifique au projet local (`.rekall/config.toml`)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un nouvel utilisateur peut utiliser Rekall sans aucune configuration manuelle en moins de 30 secondes après installation
- **SC-002**: Une équipe peut partager une base Rekall via Git en ajoutant simplement `.rekall/` au repo
- **SC-003**: 100% des chemins utilisés sont visibles via `rekall config --show`
- **SC-004**: Les utilisateurs existants ne perdent aucune donnée lors de la mise à jour
- **SC-005**: Le système fonctionne sur Linux, macOS et Windows avec les conventions natives de chaque plateforme

## Clarifications

### Session 2024-12-07

- Q: Jusqu'où remonter pour détecter `.rekall/` dans la hiérarchie ? → A: Dossier courant uniquement, pas de recherche ancêtres. Fallback sur emplacements globaux.
- Q: Priorité des chemins sur macOS (XDG vs ~/Library/) ? → A: XDG uniquement sur Mac, identique à Linux (~/.config/ + ~/.local/share/).
- Q: Comportement si emplacement sans droits d'écriture ? → A: Échouer avec message d'erreur clair (pas de fallback silencieux).

## Assumptions

- Les utilisateurs Linux/macOS sont familiers avec le concept XDG ou n'ont pas besoin de le connaître (défauts intelligents)
- Le mode projet local `.rekall/` est destiné à être versionné avec Git
- La migration depuis l'ancien format est une opération unique par utilisateur
- Les permissions fichiers sont gérées par le système d'exploitation (pas de gestion de droits utilisateur dans Rekall)
