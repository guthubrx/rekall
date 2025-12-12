# CLI Contract: Sources Medallion

**Feature**: 013-sources-medallion
**Date**: 2025-12-11

Ce document définit le contrat de l'interface CLI pour les commandes sources inbox/staging.

---

## Commandes Inbox (Bronze)

### `rekall sources inbox`

**Description**: Lance le TUI DataTable pour visualiser l'inbox des sources capturées.

**Usage**:
```bash
rekall sources inbox
```

**Output**: Interface TUI interactive avec les colonnes:
- URL (tronquée à 50 chars)
- CLI Source
- Projet
- Date de capture (format relatif: "il y a 2h")

**Bindings TUI**:
| Touche | Action |
|--------|--------|
| `i` | Import (lance import tous connecteurs) |
| `e` | Enrichir maintenant |
| `q` | Vue quarantine |
| `d` | Supprimer entrée sélectionnée |
| `Esc` | Retour menu sources |

---

### `rekall sources inbox import`

**Description**: Importe les URLs depuis les historiques des CLIs IA configurés.

**Usage**:
```bash
rekall sources inbox import [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--cli` | Choice | all | Connecteur spécifique: `claude`, `cursor`, `all` |
| `--since` | str | None | Période: `7d`, `30d`, `3m` (jours/mois) |
| `--dry-run` | bool | False | Affiche ce qui serait importé sans modifier |

**Exemples**:
```bash
# Import tous les CLIs
rekall sources inbox import

# Import Claude uniquement, derniers 7 jours
rekall sources inbox import --cli claude --since 7d

# Preview sans modification
rekall sources inbox import --dry-run
```

**Output Format**:
```
📥 Import sources depuis historiques CLI...

Connecteur: claude_cli
  ✓ 45 URLs extraites
  ✓ 42 valides, 3 en quarantine
  ⏱ 2.3s

Connecteur: cursor
  ✓ 23 URLs extraites
  ✓ 21 valides, 2 en quarantine
  ⏱ 1.1s

───────────────────────────────
Total: 68 nouvelles sources dans l'inbox
       5 sources en quarantine
```

**Exit Codes**:
| Code | Signification |
|------|---------------|
| 0 | Succès |
| 1 | Erreur générale |
| 2 | Connecteur non disponible |

---

### `rekall sources inbox stats`

**Description**: Affiche les statistiques de l'inbox.

**Usage**:
```bash
rekall sources inbox stats
```

**Output Format**:
```
📊 Statistiques Inbox

Par CLI Source:
  claude_cli    │ 156 URLs │ 4 en quarantine
  cursor        │  89 URLs │ 2 en quarantine

Par Projet (top 5):
  rekall        │  78 URLs
  bigmind-web   │  45 URLs
  speckit       │  34 URLs
  ...

État:
  En attente d'enrichissement: 23
  Déjà enrichies:            222
```

---

### `rekall sources inbox quarantine`

**Description**: Affiche les entrées en quarantine (URLs invalides).

**Usage**:
```bash
rekall sources inbox quarantine
```

**Output Format**:
```
⚠️ Sources en quarantine (6)

URL                              │ Raison                  │ Capturé
───────────────────────────────────────────────────────────────────────
localhost:3000/api/test          │ Skipped: localhost      │ il y a 2h
file:///Users/moi/doc.pdf        │ Invalid URL scheme      │ hier
192.168.1.1/admin                │ Skipped: 192.168.       │ il y a 3j

[d] Supprimer  [r] Réessayer validation  [Esc] Retour
```

---

### `rekall sources inbox clear`

**Description**: Supprime les entrées inbox déjà enrichies.

**Usage**:
```bash
rekall sources inbox clear [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--all` | bool | False | Supprime TOUT (y compris non enrichies) |
| `--force` | bool | False | Pas de confirmation |

**Confirmation**:
```
⚠️ Cette action va supprimer 156 entrées enrichies de l'inbox.
   Les données sont déjà consolidées dans le staging.

Continuer? [y/N]
```

---

## Commandes Staging (Silver)

### `rekall sources staging`

**Description**: Lance le TUI DataTable pour le staging avec scores de promotion.

**Usage**:
```bash
rekall sources staging
```

**Output**: Interface TUI interactive avec les colonnes:
- Domaine
- Titre (tronqué)
- Type
- Citations
- Projets
- Score
- Indicateur (⬆ éligible, → proche)

**Bindings TUI**:
| Touche | Action |
|--------|--------|
| `p` | Promouvoir manuellement |
| `a` | Auto-promote tous éligibles |
| `d` | Supprimer du staging |
| `r` | Rafraîchir scores |
| `Enter` | Détails source |
| `Esc` | Retour menu sources |

---

### `rekall sources staging enrich`

**Description**: Force l'enrichissement des entrées Bronze en attente.

**Usage**:
```bash
rekall sources staging enrich [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--batch` | int | 50 | Nombre d'URLs par batch |
| `--timeout` | float | 5.0 | Timeout fetch par URL (secondes) |

**Output Format**:
```
🔄 Enrichissement Bronze → Silver...

Batch 1/3:
  ✓ 48/50 enrichies
  ✗ 2 timeouts (marquées pour retry)
  ⏱ 45.2s

───────────────────────────────
Total: 144 sources enrichies
       4 en attente de retry
```

---

### `rekall sources staging promote`

**Description**: Promeut une source Silver vers Gold.

**Usage**:
```bash
rekall sources staging promote <URL_OR_ID> [OPTIONS]
```

**Arguments**:
| Argument | Type | Description |
|----------|------|-------------|
| `URL_OR_ID` | str | URL complète ou ID staging |

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--auto` | bool | False | Promeut TOUTES les sources éligibles |

**Exemples**:
```bash
# Promotion manuelle par URL
rekall sources staging promote "https://docs.python.org/3/library/"

# Promotion manuelle par ID
rekall sources staging promote 01HGXK3M7Q2N5P8R9T0V1W2X3Y

# Auto-promotion de tous les éligibles
rekall sources staging promote --auto
```

**Output Format (manuel)**:
```
✅ Source promue vers Gold

URL:    https://docs.python.org/3/library/
Score:  8.5 (seuil: 5.0)
ID:     01HGXK3M7Q2N5P8R9T0V1W2X3Y
```

**Output Format (auto)**:
```
🚀 Auto-promotion des sources éligibles...

  ✓ docs.python.org/3/library/     (score: 8.5)
  ✓ github.com/anthropics/sdk      (score: 6.2)
  ✓ react.dev/reference/hooks      (score: 5.5)

───────────────────────────────
3 sources promues vers Gold
```

---

### `rekall sources staging drop`

**Description**: Supprime une source du staging.

**Usage**:
```bash
rekall sources staging drop <URL_OR_ID> [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force` | bool | False | Pas de confirmation |

**Confirmation**:
```
⚠️ Supprimer cette source du staging?

URL:       https://example.com/doc
Citations: 3
Score:     4.2

Cette action ne supprime pas les entrées inbox associées.

Continuer? [y/N]
```

---

## Commandes Gold (Extension)

### `rekall sources demote`

**Description**: Dépromeut une source Gold vers Silver.

**Usage**:
```bash
rekall sources demote <SOURCE_ID> [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--force` | bool | False | Pas de confirmation |

**Contrainte**: Seules les sources avec `is_promoted=TRUE` peuvent être dépromotues.

**Output Format**:
```
⬇️ Source dépromotue vers Silver

URL:    https://docs.python.org/3/library/
Ancien score Gold: 65.0
Retour au staging avec score: 8.5
```

**Erreur si non-promue**:
```
❌ Erreur: Cette source n'a pas été promue automatiquement.
   Seules les sources promues peuvent être dépromotues.

   Pour supprimer une source manuellement ajoutée,
   utilisez: rekall sources delete <ID>
```

---

## Configuration

### `rekall config promotion-threshold`

**Description**: Configure le seuil de promotion.

**Usage**:
```bash
rekall config promotion-threshold [VALUE]
```

**Exemples**:
```bash
# Afficher valeur actuelle
rekall config promotion-threshold
# → Seuil de promotion: 5.0

# Modifier
rekall config promotion-threshold 3.0
# → Seuil de promotion modifié: 5.0 → 3.0
```

---

### `rekall config promotion-weights`

**Description**: Configure les poids du scoring.

**Usage**:
```bash
rekall config promotion-weights [OPTIONS]
```

**Options**:
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--citation` | float | 1.0 | Poids par citation |
| `--project` | float | 2.0 | Poids par projet distinct |
| `--recency` | float | 0.5 | Boost récence |
| `--decay-days` | int | 30 | Jours avant decay complet |

**Exemples**:
```bash
# Afficher valeurs actuelles
rekall config promotion-weights
# → citation: 1.0, project: 2.0, recency: 0.5, decay: 30 jours

# Augmenter importance multi-projet
rekall config promotion-weights --project 4.0
# → project: 2.0 → 4.0
```

---

## Codes de Sortie Globaux

| Code | Signification |
|------|---------------|
| 0 | Succès |
| 1 | Erreur générale (exception non gérée) |
| 2 | Ressource non trouvée (URL, ID) |
| 3 | Validation échouée (URL invalide, etc.) |
| 4 | Opération annulée par l'utilisateur |
