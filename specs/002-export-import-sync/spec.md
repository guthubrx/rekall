# Feature: Export/Import Sync

## Overview

Transformer la fonctionnalité Export existante en une solution complète Export/Import permettant de synchroniser toutes les données Rekall entre plusieurs installations. L'objectif est de permettre aux utilisateurs de :
- Sauvegarder intégralement leur base de connaissances
- Restaurer sur une nouvelle machine ou après réinstallation
- Partager des connaissances entre équipes/projets

## Clarifications

### Session 2025-12-07
- Q: Comportement import en mode non-interactif ? → A: Option `--yes` pour skip confirmation en mode script
- Q: Gestion fichiers corrompus/incompatibles ? → A: Afficher erreur détaillée + avorter (pas d'import partiel)
- Q: Import sur installation existante ? → A: Non-destructif par défaut (SOTA rsync/git pattern)
  - `--dry-run` pour preview
  - Backup auto avant écrasement
  - Modes: skip / replace / merge / interactive

## Problem Statement

Actuellement, l'export Rekall ne produit que des fichiers Markdown ou JSON lisibles mais non réimportables. Un utilisateur qui change de machine ou veut partager sa base de connaissances n'a aucun moyen de la restaurer automatiquement.

**Impact** : Perte de connaissances accumulées lors de changement de machine, impossibilité de collaborer.

## User Scenarios

### Scenario 1: Migration vers nouvelle machine
**Persona** : Développeur qui change de MacBook

1. Sur l'ancienne machine : `rekall export --full backup.rekall`
2. Copier `backup.rekall` sur la nouvelle machine (USB, cloud, email)
3. Sur la nouvelle machine : `rekall import backup.rekall`
4. Vérifier que toutes les entrées sont restaurées

**Critère de succès** : 100% des entrées et métadonnées sont préservées

### Scenario 2: Partage de connaissances projet
**Persona** : Tech lead qui veut partager les décisions d'architecture

1. `rekall export --project mon-projet --full projet.rekall`
2. Partager `projet.rekall` avec l'équipe (Slack, Git, email)
3. Chaque membre : `rekall import projet.rekall --merge`
4. Les entrées sont ajoutées sans écraser les existantes

**Critère de succès** : Fusion sans perte de données locales

### Scenario 3: Backup régulier automatisé
**Persona** : Utilisateur soucieux de ses données

1. Configurer un cron/launchd : `rekall export --full ~/.rekall/backups/$(date +%Y%m%d).rekall`
2. Les backups s'accumulent avec date
3. En cas de problème : `rekall import ~/.rekall/backups/20251201.rekall`

**Critère de succès** : Restauration fidèle à n'importe quel point dans le temps

## Functional Requirements

### FR-001: Format d'export complet (.rekall)
Le système doit créer un fichier archive contenant :
- **Base de données** : Toutes les entrées avec métadonnées complètes (ID, timestamps, tags, project, confidence, status, superseded_by)
- **Fichiers research** : Copie des fichiers research/ personnalisés
- **Configuration** : Fichier config si présent
- **Manifeste** : Version du format, date d'export, statistiques

**Format** : Archive ZIP avec extension `.rekall`

### FR-002: Export sélectif
Le système doit permettre de filtrer l'export par :
- `--project <name>` : Uniquement les entrées d'un projet
- `--type <type>` : Uniquement un type d'entrée (bug, pattern, etc.)
- `--since <date>` : Entrées créées/modifiées après une date
- `--full` : Export complet (défaut si aucun filtre)

### FR-003: Import non-destructif par défaut (SOTA Pattern)
Le système adopte une approche **non-destructive par défaut** inspirée des bonnes pratiques rsync/git :

#### Mode Preview (dry-run)
- `rekall import backup.rekall --dry-run` : Affiche les changements sans les appliquer
- Affichage détaillé style rsync : `[NEW] entry_id`, `[UPDATE] entry_id`, `[SKIP] entry_id`

#### Détection des conflits
Pour chaque entrée importée, détecter :
- **Entrée identique (même ID, même contenu)** → Skip automatique
- **Entrée modifiée (même ID, contenu différent)** → Conflit à résoudre
- **Entrée nouvelle (ID inconnu)** → Ajout direct

#### Stratégies de résolution (choix utilisateur)
| Option | Comportement | Backup auto |
|--------|--------------|-------------|
| `--skip` | Ignorer les conflits (garder local) | Non |
| `--replace` | Écraser par la version importée | Oui (avant) |
| `--merge` | Créer nouvelles entrées avec nouveaux IDs | Non |
| `--interactive` | Demander pour chaque conflit | Selon choix |

#### Backup automatique avant modification
- Si `--replace` : Créer `~/.rekall/backups/pre-import-YYYYMMDD-HHMMSS.rekall`
- Option `--no-backup` pour désactiver (usage avancé)

#### Fichiers research : même logique
- **Fichier identique** → Skip
- **Fichier existant différent** → Demander : garder local / remplacer / renommer importé
- **Nouveau fichier** → Copier directement

### FR-004: Validation à l'import
Le système doit :
- Vérifier l'intégrité du fichier .rekall (checksum)
- Valider la compatibilité de version
- **En cas d'erreur** : Afficher diagnostic détaillé et avorter (pas d'import partiel)
- Afficher un aperçu : nombre d'entrées, projets, types
- Demander confirmation avant import (sauf si `--yes` spécifié pour mode script)

### FR-005: Interface TUI Export/Import
Le menu "Export" devient "Export / Import" avec sous-menu :
- Export complet
- Export filtré (projet/type)
- Import depuis fichier
- Historique des exports/imports

## Success Criteria

| Critère | Mesure | Cible |
|---------|--------|-------|
| Intégrité des données | Entrées identiques après export/import | 100% |
| Performance export | Temps pour 1000 entrées | < 5 secondes |
| Performance import | Temps pour 1000 entrées | < 10 secondes |
| Taille fichier | Ratio compression archive | > 50% |
| Compatibilité | Fichiers .rekall portables entre OS | macOS, Linux, Windows |

## Key Entities

### Archive .rekall (ZIP)
```
backup.rekall/
├── manifest.json       # Version, date, stats
├── entries.json        # Toutes les entrées DB
├── research/           # Fichiers research personnalisés
│   └── *.md
└── config.toml         # Configuration (si présente)
```

### Manifest
- `format_version` : Version du format (1.0)
- `created_at` : Timestamp ISO8601
- `rekall_version` : Version de Rekall utilisée
- `stats` : {entries_count, projects, types}
- `checksum` : SHA256 du contenu

## Assumptions

- Les fichiers research par défaut ne sont pas exportés (ils sont dans le package)
- Seuls les fichiers research ajoutés par l'utilisateur sont inclus
- L'import ne modifie jamais les fichiers research par défaut
- Un fichier .rekall est auto-suffisant (aucune dépendance externe)

## Out of Scope

- Synchronisation temps réel entre machines
- Serveur centralisé de partage
- Chiffrement des archives (le fichier est en clair)
- Import depuis autres formats (Notion, Obsidian, etc.)
- Versioning automatique des backups

## Dependencies

- Module `zipfile` (standard Python)
- Module `hashlib` pour checksums (standard Python)
- Aucune nouvelle dépendance externe requise

## Research Findings

Sources consultées pour les bonnes pratiques import/export :

- [rsync Best Practices - Dry Run](https://eduvola.com/blog/rsync-best-practices-always-test) : Pattern `--dry-run` pour preview
- [DigitalOcean rsync Tutorial](https://www.digitalocean.com/community/tutorials/how-to-use-rsync-to-sync-local-and-remote-directories) : `--itemize-changes` pour diff détaillé
- [SQLite UPSERT Documentation](https://www.sqlite.org/lang_UPSERT.html) : `ON CONFLICT DO UPDATE/NOTHING`
- [Blue Canvas Merge Conflicts](https://bluecanvas.io/blog/how-to-resolve-merge-conflicts-in-salesforce-ci-cd-pipeline-in-2025-blue-canvas) : Field-level merge, replay decisions

**Principes retenus** :
1. Non-destructif par défaut
2. Preview obligatoire avant modification
3. Backup automatique avant écrasement
4. Transaction atomique (tout ou rien)
