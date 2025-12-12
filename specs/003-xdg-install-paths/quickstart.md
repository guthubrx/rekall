# Quickstart: XDG-Compliant Installation Paths

**Feature**: 003-xdg-install-paths
**Date**: 2024-12-07

## Installation Standard (99% des cas)

```bash
# Rien à configurer - XDG par défaut
pip install rekall
rekall add bug "Mon premier bug"
# → DB créée dans ~/.local/share/rekall/knowledge.db
# → Config dans ~/.config/rekall/config.toml
```

**Vérifier la configuration:**

```bash
rekall config --show
```

**Output attendu:**

```
Configuration Rekall
────────────────────
Source: default

Chemins:
  Config:  ~/.config/rekall/
  Data:    ~/.local/share/rekall/
  Cache:   ~/.cache/rekall/
  DB:      ~/.local/share/rekall/knowledge.db

Variables d'environnement:
  REKALL_HOME:     (not set)
  XDG_CONFIG_HOME: (not set)
  XDG_DATA_HOME:   (not set)

Projet local: Non détecté
```

---

## Projet Local (équipe)

Pour partager une base de connaissances avec Git:

```bash
cd mon-projet/
rekall init --local
# → Crée .rekall/ dans le projet

git add .rekall/
git commit -m "Add Rekall knowledge base"
```

**Structure créée:**

```
mon-projet/
├── .rekall/
│   ├── config.toml      # Config projet (optionnel)
│   ├── knowledge.db     # Base de données
│   └── .gitignore       # Suggère d'ignorer ou non la DB
└── ...
```

**Utilisation automatique:**

```bash
cd mon-projet/
rekall add pattern "Pattern partagé"
# → Utilise automatiquement .rekall/knowledge.db
```

**Forcer global dans un projet local:**

```bash
rekall --global add bug "Bug global, pas projet"
```

---

## Chemin Personnalisé

### Via variable d'environnement

```bash
export REKALL_HOME=/mnt/nas/rekall
rekall add pattern "Pattern sur NAS"
# → Tout dans /mnt/nas/rekall/
```

### Via fichier de configuration

```bash
# ~/.config/rekall/config.toml
cat << 'EOF' > ~/.config/rekall/config.toml
data_dir = "/mnt/backup/rekall"
EOF

rekall add bug "Bug backupé"
# → DB dans /mnt/backup/rekall/knowledge.db
# → Config reste dans ~/.config/rekall/
```

---

## Migration depuis ~/.rekall/

Si vous avez une ancienne installation:

```bash
rekall
# → Prompt interactif:
# "Rekall a détecté une installation existante dans ~/.rekall/
#  Voulez-vous migrer vers le nouvel emplacement XDG?
#  [M]igrer  [C]onserver ancien  [Q]uitter"
```

**Forcer l'ancien chemin (temporaire):**

```bash
rekall --legacy add bug "Avec ancien chemin"
```

---

## Ordre de Priorité

Les chemins sont résolus dans cet ordre (premier trouvé gagne):

1. **CLI**: `--db-path`, `--config-path`
2. **Env**: `REKALL_HOME`, `REKALL_DB_PATH`
3. **Local**: `.rekall/` dans dossier courant
4. **Config**: `data_dir` dans config.toml
5. **XDG**: `$XDG_CONFIG_HOME`, `$XDG_DATA_HOME`
6. **Default**: platformdirs (ex: ~/.local/share/rekall/)

---

## Dépannage

### Voir les chemins actifs

```bash
rekall config --show
```

### Problème de permissions

```bash
# Si erreur "Permission denied"
ls -la ~/.local/share/rekall/
# Vérifier droits d'écriture

# Ou utiliser un chemin personnalisé
export REKALL_HOME=~/rekall-data
```

### Conflits projet/global

```bash
# Dans un projet avec .rekall/
rekall config --show
# → Doit afficher "Source: local"

# Pour utiliser global malgré tout
rekall --global config --show
# → Doit afficher "Source: default" ou "Source: xdg"
```
