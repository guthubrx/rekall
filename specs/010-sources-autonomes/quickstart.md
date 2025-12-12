# Quickstart: Sources Autonomes

**Feature**: 010-sources-autonomes
**Date**: 2025-12-11

---

## Prérequis

- Rekall installé (`pip install -e .` ou `rekall --version`)
- Feature 009 (Sources Integration) déployée (schema v8)
- Fichiers speckit research dans `~/.speckit/research/` (optionnel)

---

## 1. Migration des Sources Speckit

### Vérifier les fichiers existants

```bash
ls ~/.speckit/research/
# Devrait afficher : 01-ai-agents.md, 02-security.md, etc.
```

### Lancer la migration

```bash
# Mode dry-run pour voir ce qui sera importé
rekall sources migrate --dry-run

# Migration réelle
rekall sources migrate
```

**Résultat attendu** :
```json
{
  "status": "success",
  "imported": 45,
  "updated": 0,
  "themes": ["ai-agents", "roi-business", "security", ...]
}
```

---

## 2. Vérifier les Sources Importées

### Lister les thèmes

```bash
rekall sources list-themes
```

### Voir les sources d'un thème

```bash
rekall sources suggest --theme security --limit 5
```

### Statistiques globales

```bash
rekall sources stats
```

---

## 3. Utilisation Quotidienne

### Ajouter une source manuellement

```bash
# Via la commande existante (Feature 009)
rekall sources add "https://example.com/docs"

# Ajouter un thème
rekall sources add-theme <SOURCE_ID> security
```

### Classifier une source

```bash
# Si une source n'est pas automatiquement classifiée
rekall sources classify <SOURCE_ID> authority
```

### Recalculer les scores

```bash
# Manuellement
rekall sources recalculate

# Voir les sources promues
rekall sources suggest --promoted-only
```

---

## 4. Intégration Speckit

### Configurer l'appel depuis Speckit

Dans vos procédures speckit, remplacez la lecture des fichiers statiques par :

```bash
# Avant (fichiers statiques)
cat ~/.speckit/research/06-security.md | grep "^- https://"

# Après (API Rekall)
rekall sources suggest --theme security | jq -r '.sources[].domain'
```

### Exemple de script d'intégration

```bash
#!/bin/bash
# get-research-sources.sh

THEME="${1:-ai-agents}"
FORMAT="${2:-domains}"

case $FORMAT in
  domains)
    rekall sources suggest --theme "$THEME" | jq -r '.sources[].domain'
    ;;
  site-queries)
    rekall sources suggest --theme "$THEME" | \
      jq -r '.sources[] | "site:\(.domain)"'
    ;;
  full)
    rekall sources suggest --theme "$THEME"
    ;;
esac
```

---

## 5. Dashboard TUI

### Voir les sources dans l'interface

```bash
rekall tui
# Naviguer vers "Sources Documentaires"
```

**Sections disponibles** :
- Sources Seeds (migrées de speckit)
- Sources Promues (automatiquement)
- Top Sources par Score
- Sources Dormantes (>6 mois)
- Sources Inaccessibles (link rot)

---

## 6. Maintenance

### Recalcul automatique (cron)

```bash
# Ajouter au crontab
crontab -e

# Ligne à ajouter (recalcul quotidien à 3h)
0 3 * * * /usr/local/bin/rekall sources recalculate >> ~/.rekall/logs/scores.log 2>&1
```

### Vérification link rot

```bash
# Vérifier les URLs (Feature 009)
rekall sources verify

# Voir les sources inaccessibles
rekall sources suggest --theme all | jq '.sources[] | select(.status == "inaccessible")'
```

### Nettoyage des sources obsolètes

```bash
# Voir les sources dormantes (>6 mois sans usage)
rekall sources stats | jq '.dormant'

# Supprimer manuellement si nécessaire
rekall sources delete <SOURCE_ID>
```

---

## Troubleshooting

### Migration échoue

```bash
# Vérifier le format des fichiers
cat ~/.speckit/research/01-ai-agents.md | head -50

# Relancer avec verbose
rekall sources migrate --verbose
```

### Scores incohérents

```bash
# Forcer recalcul complet
rekall sources recalculate --verbose

# Vérifier citation quality
rekall show <SOURCE_ID>
```

### Speckit ne trouve pas de sources

```bash
# Vérifier que le thème existe
rekall sources list-themes

# Vérifier le format de sortie
rekall sources suggest --theme security 2>&1 | head
```

---

## Ressources

- **Spec** : `specs/010-sources-autonomes/spec.md`
- **Data Model** : `specs/010-sources-autonomes/data-model.md`
- **API CLI** : `specs/010-sources-autonomes/contracts/cli-api.md`
- **Research SOTA** : `specs/010-sources-autonomes/research.md`
