# Quickstart: Sources Integration

**Date** : 2025-12-11
**Feature** : 009-sources-integration

---

## Prérequis

- Python 3.9+
- Rekall installé (`pip install -e .`)
- Base de données Rekall existante (sera migrée v7→v8)

---

## Démarrage Rapide

### 1. Migration automatique

La migration v7→v8 s'exécute automatiquement au premier lancement après mise à jour :

```bash
rekall browse  # ou toute commande Rekall
# → Migration v7 → v8 appliquée automatiquement
```

### 2. Lier une source à un souvenir

**Via TUI** :
1. Créer ou éditer un souvenir
2. Dans le champ "Sources", taper :
   - Un thème : `05-knowledge` → autocomplete `05-knowledge-management.md`
   - Une URL : `https://pinecone.io/learn/rag/`
   - Un fichier : `./docs/architecture.md`
3. Ajouter une note optionnelle

**Via CLI** :
```bash
rekall add --source "https://pinecone.io/learn/rag/" --source-note "Section chunking"
```

### 3. Voir les backlinks d'une source

```bash
rekall sources show pinecone.io
# Affiche:
# - Score: 78/100
# - Cité par 5 souvenirs
# - Dernière utilisation: 2025-12-01
```

### 4. Dashboard sources

```bash
rekall sources
# ou dans TUI : Menu → Sources Documentaires
```

Affiche :
- Top 20 sources par score
- Sources dormantes (>6 mois)
- Sources émergentes (nouvelles)
- Sources inaccessibles (link rot)

---

## Commandes CLI

### Sources

| Commande | Description |
|----------|-------------|
| `rekall sources` | Dashboard sources |
| `rekall sources list` | Lister toutes les sources |
| `rekall sources show <domain>` | Détail d'une source |
| `rekall sources add <url>` | Ajouter une source manuellement |
| `rekall sources verify` | Vérifier link rot (toutes) |

### Liaison

| Commande | Description |
|----------|-------------|
| `rekall add --source <ref>` | Ajouter souvenir avec source |
| `rekall edit <id> --add-source <ref>` | Ajouter source à souvenir existant |
| `rekall show <id> --sources` | Voir sources d'un souvenir |

---

## Configuration

### Decay rates par défaut

Dans `~/.config/rekall/config.toml` :

```toml
[sources]
# Domaines avec decay rapide (AI/ML, news)
fast_decay_domains = ["openai.com", "anthropic.com", "huggingface.co"]

# Domaines avec decay lent (docs officielles)
slow_decay_domains = ["docs.python.org", "sqlite.org", "martinfowler.com"]

# Seuil source dormante (mois)
dormant_threshold_months = 6

# Seuil source émergente (citations en 30 jours)
emerging_threshold_citations = 3

# Nombre de sources dans le dashboard
dashboard_top_n = 20
```

### Vérification link rot

```toml
[sources.link_rot]
# Activer la vérification automatique
enabled = true

# Fréquence (quotidienne)
check_interval_hours = 24

# Timeout requête HTTP (secondes)
http_timeout = 10

# Nombre max de vérifications par run
max_checks_per_run = 50
```

---

## Algorithme de Scoring

Le score personnel (0-100) est calculé ainsi :

```
Score = min(100, usage_score + recency_score + reliability_bonus)

où:
- usage_score = min(60, sqrt(usage_count) × 10)
- recency_score = 30 × (0.5 ^ (days_since_last_use / half_life))
- reliability_bonus = {A: 10, B: 5, C: 0}

Demi-vies (half_life):
- fast: 90 jours (3 mois)
- medium: 180 jours (6 mois)
- slow: 365 jours (12 mois)
```

**Exemples** :

| Scenario | Usage | Jours | Decay | Reliability | Score |
|----------|-------|-------|-------|-------------|-------|
| Source très utilisée récemment | 25 | 7 | medium | A | ~89 |
| Source moyennement utilisée | 5 | 60 | medium | B | ~52 |
| Source peu utilisée ancienne | 2 | 180 | fast | C | ~19 |

---

## Workflow Recherche Priorisée

Lors d'une recherche Speckit, les sources sont automatiquement triées par score :

```
/speckit.plan "Implémenter RAG"

1. CHARGER sources du thème "RAG":
   → pinecone.io (score: 95) ✅ Top priority
   → langchain.com (score: 72)
   → medium.com (score: 18) ⚠️ Déprioritisé

2. GÉNÉRER requêtes WebSearch:
   → site:pinecone.io "RAG chunking" 2025
   → site:langchain.com "RAG best practices"

3. SUGGÉRER souvenirs liés:
   → "Bug: RAG hallucination fix" (01JERK...)
```

---

## Migration des Données Existantes

Si vous avez déjà des URLs dans vos souvenirs (dans `content` ou `context`), vous pouvez les extraire :

```bash
rekall sources migrate --extract-urls
# Extrait les URLs de tous les souvenirs existants
# Crée des liens entry_sources automatiquement
# Calcule les scores initiaux
```

---

## Troubleshooting

### La migration v8 échoue

```bash
# Vérifier la version actuelle
rekall db info

# Forcer une migration manuelle
rekall db migrate --to 8
```

### Score ne se met pas à jour

Le score est recalculé quand :
- Un nouveau lien entry_source est créé
- `rekall sources recalculate` est exécuté

```bash
rekall sources recalculate --all
```

### Link rot non détecté

```bash
# Vérification manuelle
rekall sources verify --domain pinecone.io

# Vérifier les logs
rekall sources verify --verbose
```
