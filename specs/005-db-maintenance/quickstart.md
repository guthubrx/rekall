# Quickstart: Database Maintenance

**Feature**: 005-db-maintenance

## Vue d'ensemble

Rekall inclut des outils de maintenance pour gérer votre base de connaissances : visualiser les informations, créer des sauvegardes et restaurer en cas de besoin.

## Commandes CLI

### Voir les informations de la base

```bash
rekall info
```

Affiche :
- Chemin de la base de données
- Version du schéma
- Nombre d'entrées (actives/obsolètes)
- Nombre de liens
- Taille du fichier

### Créer une sauvegarde

```bash
# Sauvegarde automatique (dans ~/.rekall/backups/)
rekall backup

# Sauvegarde vers un chemin personnalisé
rekall backup --output ~/mes-backups/rekall-backup.db
```

Les backups sont nommés automatiquement avec la date : `knowledge_2025-12-09_143022.db`

### Restaurer depuis une sauvegarde

```bash
rekall restore ~/.rekall/backups/knowledge_2025-12-09_143022.db
```

**Important** : Un backup de sécurité est créé automatiquement avant chaque restauration. Vous ne perdrez jamais vos données !

## Interface TUI

Dans le TUI (`rekall browse`), accédez au menu **Installation & Maintenance** :

1. **Database Info** - Voir les statistiques
2. **Create Backup** - Sauvegarder en un clic
3. **Restore from Backup** - Sélectionner un backup à restaurer

## Bonnes pratiques

1. **Avant une mise à jour** : `rekall backup`
2. **Régulièrement** : Planifiez des backups automatiques
3. **Avant un restore** : Pas besoin, le safety backup est automatique

## Emplacement des fichiers

| Fichier | Emplacement |
|---------|-------------|
| Base de données | `~/.local/share/rekall/knowledge.db` |
| Backups | `~/.rekall/backups/` |
| Safety backups | `~/.rekall/backups/*_pre-restore.db` |
