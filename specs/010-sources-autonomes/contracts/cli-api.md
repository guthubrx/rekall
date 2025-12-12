# CLI API Contracts: Sources Autonomes

**Feature**: 010-sources-autonomes
**Date**: 2025-12-11

---

## Overview

Extension de la CLI `rekall` avec nouvelles commandes pour la gestion autonome des sources.

**Groupe de commandes** : `rekall sources`

---

## Commands

### 1. `rekall sources migrate`

Importe les fichiers speckit research dans la base de données comme sources seed.

**Usage**:
```bash
rekall sources migrate [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--path` | PATH | `~/.speckit/research/` | Chemin vers fichiers research |
| `--dry-run` | FLAG | false | Afficher ce qui serait importé sans modifier |
| `--force` | FLAG | false | Réimporter même si déjà migré |

**Output** (JSON):
```json
{
  "status": "success",
  "imported": 45,
  "updated": 3,
  "skipped": 2,
  "errors": [],
  "themes": ["ai-agents", "security", "testing", ...]
}
```

**Exit Codes**:
- `0` : Succès
- `1` : Erreur de parsing fichiers
- `2` : Chemin invalide

---

### 2. `rekall sources suggest`

Retourne les sources triées par score pour un thème donné. API principale pour intégration Speckit.

**Usage**:
```bash
rekall sources suggest --theme <THEME> [OPTIONS]
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `--theme` | TEXT | Yes | Thème à filtrer (ex: "security") |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--limit` | INT | 20 | Nombre max de sources |
| `--min-score` | FLOAT | 0 | Score minimum |
| `--include-unclassified` | FLAG | true | Inclure sources non classifiées |
| `--seeds-only` | FLAG | false | Uniquement les sources seed |
| `--promoted-only` | FLAG | false | Uniquement les sources promues |

**Output** (JSON):
```json
{
  "theme": "security",
  "count": 15,
  "sources": [
    {
      "id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
      "domain": "owasp.org",
      "url_pattern": "/www-project-*",
      "score": 87.5,
      "role": "authority",
      "reliability": "A",
      "is_seed": true,
      "is_promoted": false,
      "usage_count": 12,
      "last_used": "2025-12-10T14:30:00Z"
    },
    {
      "id": "01ARZ3NDEKTSV4RRFFQ69G5FAW",
      "domain": "security.stackexchange.com",
      "url_pattern": null,
      "score": 65.2,
      "role": "hub",
      "reliability": "B",
      "is_seed": false,
      "is_promoted": true,
      "usage_count": 8,
      "last_used": "2025-12-05T09:15:00Z"
    }
  ]
}
```

**Exit Codes**:
- `0` : Succès (même si liste vide)
- `1` : Thème invalide

---

### 3. `rekall sources recalculate`

Recalcule les scores de toutes les sources et met à jour les statuts de promotion.

**Usage**:
```bash
rekall sources recalculate [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--source-id` | TEXT | null | Recalculer une seule source |
| `--update-promotions` | FLAG | true | Mettre à jour is_promoted |
| `--verbose` | FLAG | false | Afficher détails par source |

**Output** (JSON):
```json
{
  "status": "success",
  "recalculated": 127,
  "promoted": 12,
  "demoted": 3,
  "unchanged": 112,
  "duration_ms": 234
}
```

**Exit Codes**:
- `0` : Succès
- `1` : Erreur base de données

---

### 4. `rekall sources classify`

Classifie manuellement une source comme hub ou authority.

**Usage**:
```bash
rekall sources classify <SOURCE_ID> <ROLE>
```

**Arguments**:
| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `SOURCE_ID` | TEXT | Yes | ID de la source |
| `ROLE` | TEXT | Yes | hub / authority / unclassified |

**Output** (JSON):
```json
{
  "status": "success",
  "source_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  "previous_role": "unclassified",
  "new_role": "authority",
  "score_before": 45.2,
  "score_after": 54.2
}
```

**Exit Codes**:
- `0` : Succès
- `1` : Source non trouvée
- `2` : Rôle invalide

---

### 5. `rekall sources list-themes`

Liste tous les thèmes disponibles avec statistiques.

**Usage**:
```bash
rekall sources list-themes [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--min-sources` | INT | 1 | Nombre min de sources par thème |

**Output** (JSON):
```json
{
  "themes": [
    {"theme": "ai-agents", "count": 23, "avg_score": 67.5},
    {"theme": "security", "count": 18, "avg_score": 72.1},
    {"theme": "testing", "count": 12, "avg_score": 58.3}
  ]
}
```

---

### 6. `rekall sources add-theme`

Ajoute un thème à une source existante.

**Usage**:
```bash
rekall sources add-theme <SOURCE_ID> <THEME>
```

**Output** (JSON):
```json
{
  "status": "success",
  "source_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  "theme": "devops",
  "themes": ["security", "devops"]
}
```

---

### 7. `rekall sources stats`

Affiche statistiques globales des sources.

**Usage**:
```bash
rekall sources stats
```

**Output** (JSON):
```json
{
  "total_sources": 127,
  "seeds": 45,
  "promoted": 23,
  "by_role": {
    "authority": 34,
    "hub": 56,
    "unclassified": 37
  },
  "by_reliability": {
    "A": 28,
    "B": 67,
    "C": 32
  },
  "avg_score": 45.7,
  "themes_count": 10,
  "inaccessible": 5
}
```

---

## Error Response Format

Toutes les erreurs suivent ce format JSON :

```json
{
  "status": "error",
  "code": "SOURCE_NOT_FOUND",
  "message": "Source with ID '01ARZ...' not found",
  "details": {}
}
```

**Error Codes**:
| Code | Description |
|------|-------------|
| `SOURCE_NOT_FOUND` | Source ID invalide |
| `INVALID_ROLE` | Rôle non reconnu |
| `INVALID_THEME` | Thème format invalide |
| `PARSE_ERROR` | Erreur parsing fichier speckit |
| `DATABASE_ERROR` | Erreur SQLite |

---

## Integration Example (Speckit)

```bash
#!/bin/bash
# speckit-research-lookup.sh

THEME="$1"

# Appel Rekall pour obtenir sources
SOURCES=$(rekall sources suggest --theme "$THEME" --limit 10)

# Parser JSON pour générer requêtes
echo "$SOURCES" | jq -r '.sources[] | "site:\(.domain) \(.url_pattern // "")"' \
  | head -5
```

---

## Batch Processing

Pour le recalcul quotidien (cron) :

```bash
# Crontab entry (daily at 3am)
0 3 * * * /usr/local/bin/rekall sources recalculate --update-promotions >> /var/log/rekall-scores.log 2>&1
```
