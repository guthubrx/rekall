# Design: Progressive Disclosure pour Rekall Skill

**Date**: 2025-12-09
**Feature**: 004-cognitive-memory
**User Story**: US2 (Consultation automatique)

---

## Contexte et Problème

Le skill Claude doit présenter les résultats Rekall de manière efficace. Le design initial "tout ou rien" ne prenait pas en compte:
- Les deux audiences distinctes (Agent AI vs Humain)
- La charge cognitive variable selon le volume de résultats
- Le besoin de traçabilité des sources

## Recherche UX

### Sources consultées
- Nielsen Norman Group (NN/g): Progressive Disclosure
- clig.dev: Command Line Interface Guidelines
- MIT Media Lab: AI-assisted decision making

### Principes clés retenus

1. **Maximum 2 niveaux de disclosure** (NN/g)
2. **Information scent** - Labels et résumés guidant l'exploration
3. **"If everything is a highlight, nothing is a highlight"** (clig.dev)
4. **Trade-off cognitive load vs depth** - L'IA réduit la charge mais peut réduire la qualité du raisonnement

---

## Architecture Décidée

### Séparation des responsabilités

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Rekall CLI    │ ───▶ │   Skill Claude  │ ───▶ │     Humain      │
│   (--json)      │      │   (présentation)│      │   (lecture)     │
└─────────────────┘      └─────────────────┘      └─────────────────┘
     Données              Logique format           Consommation
     complètes            adapté audience          finale
```

**Rationale**: L'agent AI a besoin de toutes les données pour raisonner. L'humain a besoin d'un résumé digestible. La logique de présentation est dans le skill, pas dans Rekall.

---

## Format JSON (Agent AI)

### Structure complète

```json
{
  "query": "auth timeout",
  "results": [
    {
      "id": "01HXYZ...",
      "type": "bug",
      "title": "Timeout auth API - augmenter à 30s",
      "content": "## Problème\nTimeout de 5s insuffisant...",
      "tags": ["auth", "api", "timeout"],
      "project": "backend-api",
      "confidence": 4,
      "consolidation_score": 0.89,
      "access_count": 12,
      "last_accessed": "2025-12-07",
      "relevance_score": 0.85,
      "links": {
        "outgoing": [
          {"target_id": "01HABC...", "type": "related"}
        ],
        "incoming": [
          {"source_id": "01HDEF...", "type": "derived_from"}
        ]
      }
    }
  ],
  "total_count": 4,
  "context_matches": {
    "project": true,
    "tags": ["auth", "api"]
  }
}
```

### Champs et utilisation

| Champ | Usage Agent |
|-------|-------------|
| `id` | Référence pour citations |
| `content` | Analyse complète du contexte |
| `relevance_score` | Priorisation des sources |
| `consolidation_score` | Fiabilité de la source |
| `links` | Découverte connaissances connexes |
| `context_matches` | Pertinence projet/tags |

---

## Format Humain (Affichage)

### Structure de présentation

```
🧠 Rekall: 3 connaissances pertinentes

D'après « Timeout auth API » [1], le timeout par défaut de 5s est
insuffisant en production. La solution recommandée selon
« Pattern retry backoff » [2] est d'implémenter un retry exponentiel.

---
Références:
[1] 01HXYZ - bug - Timeout auth API
[2] 01HABC - pattern - Pattern retry backoff
[3] 01HDEF - config - Config timeout services
```

### Éléments clés

1. **Header résumé** - Nombre et titres des entrées pertinentes
2. **Citations inline** - Format: `D'après « Titre » [N], ...`
3. **Section références** - IDs complets pour traçabilité
4. **Séparation claire** - Contenu Rekall vs réponse agent

---

## Score de Pertinence

### Formule combinée

```
relevance_score = (FTS × 0.4) + (context_match × 0.35) + (meta_quality × 0.25)
```

| Composant | Poids | Description |
|-----------|-------|-------------|
| FTS | 40% | Score de recherche full-text SQLite |
| context_match | 35% | Correspondance projet/tags courant |
| meta_quality | 25% | confidence × consolidation_score |

### Seuils d'affichage (hybride)

**Par score:**
- `> 0.7` : Résultats prioritaires (détail complet)
- `0.4 - 0.7` : Résultats secondaires (résumé)
- `< 0.4` : Non affiché

**Par volume:**
- `1-2` résultats : Détail complet pour tous
- `3-5` résultats : Prioritaires détaillés, autres résumés
- `6+` résultats : Top 3 détaillés, reste en liste

---

## Comportement "Aucun résultat"

### Format

```
🧠 Rekall: Aucune connaissance trouvée pour "nouveau-sujet"

Je procède sans contexte historique.
💡 Si cette tâche produit des connaissances utiles, je proposerai
   de les capturer à la fin.
```

### Rationale

- **Mention explicite** - L'humain sait que Rekall a été consulté
- **Annonce capture future** - Prépare l'utilisateur à la proposition US3
- **Pas de faux positifs** - Pas d'inventions ou suggestions non pertinentes

---

## Implémentation

### Option CLI `--json`

```bash
# Agent utilise
rekall search "auth timeout" --json

# Humain utilise (par défaut)
rekall search "auth timeout"
```

### Détection d'audience dans le skill

Le skill Claude détecte automatiquement:
- Si appelé programmatiquement → JSON complet
- Si présenté à l'humain → Format lisible

---

## Décisions Clés

| # | Décision | Rationale |
|---|----------|-----------|
| D1 | Deux audiences séparées | Agent AI ≠ besoins humains |
| D2 | JSON complet pour agent | L'agent raisonne sur données complètes |
| D3 | Citations inline | Traçabilité sans surcharge visuelle |
| D4 | Score combiné 3 facteurs | FTS seul insuffisant |
| D5 | Annonce capture si vide | Prépare flow US3 |

---

## Références

- [Nielsen Norman Group - Progressive Disclosure](https://www.nngroup.com/articles/progressive-disclosure/)
- [Command Line Interface Guidelines](https://clig.dev/)
- MIT Media Lab - AI-assisted cognition research
