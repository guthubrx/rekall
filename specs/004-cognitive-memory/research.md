# Recherche Technique : Système de Mémoire Cognitive

**Date** : 2025-12-09
**Feature** : 004-cognitive-memory
**Prérequis** : [docs/research-memory-mechanisms.md](../../docs/research-memory-mechanisms.md)

---

## Synthèse

Ce document consolide les décisions techniques basées sur la recherche cognitive préalable. La recherche fondamentale (30+ sources académiques) est dans `docs/research-memory-mechanisms.md`.

---

## 1. Liens entre entrées (Knowledge Graph)

### Décision
Utiliser une **table SQLite `links`** avec relation many-to-many, pas une base graphe dédiée.

### Rationale
- **Impact prouvé** : +20% précision de récupération (source: Knowledge Graphs in RAG)
- **Simplicité** : SQLite suffisant pour ~1000 nœuds et ~5000 arêtes typiques
- **Pas de dépendance** : Neo4j/JanusGraph surdimensionné pour single-user CLI

### Alternatives considérées
| Alternative | Rejeté car |
|-------------|-----------|
| Neo4j | Dépendance serveur, overkill pour single-user |
| NetworkX en mémoire | Pas de persistence, perte au restart |
| JSON adjacency list | Pas de requêtes efficaces |

### Implémentation
```sql
CREATE TABLE links (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES entries(id),
    target_id TEXT NOT NULL REFERENCES entries(id),
    relation_type TEXT NOT NULL CHECK (relation_type IN ('related','supersedes','derived_from','contradicts')),
    created_at TEXT NOT NULL,
    UNIQUE(source_id, target_id, relation_type)
);
```

---

## 2. Tracking d'accès et consolidation

### Décision
Ajouter **3 colonnes à la table `entries`** : `last_accessed`, `access_count`, `consolidation_score`.

### Rationale
- **Courbe de l'oubli** : Entrées non accédées perdent 75% de "retrieval strength" après 1 semaine
- **Simplicité** : Mise à jour atomique lors de `get()` ou `search()`
- **Pas de table séparée** : Évite les JOINs pour l'affichage

### Alternatives considérées
| Alternative | Rejeté car |
|-------------|-----------|
| Table access_log | Historique complet inutile, surcharge disque |
| Score externe | Complexité synchronisation |

### Implémentation
```sql
ALTER TABLE entries ADD COLUMN last_accessed TEXT;
ALTER TABLE entries ADD COLUMN access_count INTEGER DEFAULT 0;
ALTER TABLE entries ADD COLUMN consolidation_score REAL DEFAULT 0.0;
```

**Score de consolidation** (0.0 - 1.0) :
```python
def calculate_consolidation(access_count: int, days_since_access: int) -> float:
    # Facteur fréquence (log pour éviter explosion)
    frequency_factor = min(1.0, math.log(access_count + 1) / 5)
    # Facteur fraîcheur (decay exponentiel sur 30 jours)
    freshness_factor = math.exp(-days_since_access / 30)
    return 0.6 * frequency_factor + 0.4 * freshness_factor
```

---

## 3. Distinction épisodique/sémantique

### Décision
Ajouter une **colonne `memory_type`** avec enum ('episodic', 'semantic').

### Rationale
- **Fondement cognitif** : Tulving (1972) - mémoires épisodiques (événements) vs sémantiques (concepts)
- **Impact agents LLM** : Papers récents (Fang et al.) montrent que cette distinction améliore la cohérence long-terme
- **Migration** : Entrées existantes = 'episodic' par défaut (clarification #2)

### Alternatives considérées
| Alternative | Rejeté car |
|-------------|-----------|
| Tags manuels | Inconsistant, oubli utilisateur |
| Classification auto | Complexité ML non justifiée pour V1 |

### Implémentation
```sql
ALTER TABLE entries ADD COLUMN memory_type TEXT DEFAULT 'episodic'
    CHECK (memory_type IN ('episodic', 'semantic'));
```

---

## 4. Répétition espacée

### Décision
Utiliser un **algorithme SM-2 simplifié** (pas FSRS).

### Rationale
- **Prouvé** : +6-9% rétention vs révision aléatoire
- **Simple** : SM-2 = 4 lignes de calcul, FSRS = algorithme complexe
- **Suffisant pour V1** : Optimisation FSRS différée

### Alternatives considérées
| Alternative | Rejeté car |
|-------------|-----------|
| FSRS | Out of scope V1, complexité |
| Leitner boxes | Moins flexible que intervalles |
| Anki-style | Dépendance externe |

### Implémentation
```python
def calculate_next_interval(current_interval: int, quality: int) -> int:
    """SM-2 simplifié. quality: 0-5 (0=échec, 5=parfait)"""
    if quality < 3:
        return 1  # Reset si échec
    ease_factor = max(1.3, 2.5 + 0.1 * (quality - 3))
    return int(current_interval * ease_factor)
```

Nouveaux champs (ou table `review_schedule`) :
```sql
ALTER TABLE entries ADD COLUMN next_review TEXT;  -- ISO date
ALTER TABLE entries ADD COLUMN review_interval INTEGER DEFAULT 1;  -- jours
ALTER TABLE entries ADD COLUMN ease_factor REAL DEFAULT 2.5;
```

---

## 5. Skill Claude Code

### Décision
Créer un **skill Claude Code** (fichier `.md` dans `.claude/skills/`) qui utilise les commandes `rekall` existantes.

### Rationale
- **Progressive disclosure** : Le skill charge les instructions seulement quand pertinent
- **Pas de modification Claude** : Utilise l'API Bash existante
- **Consultation + Capture** : Deux modes d'utilisation documentés dans le skill

### Alternatives considérées
| Alternative | Rejeté car |
|-------------|-----------|
| MCP Server | Overhead, pas nécessaire pour CLI simple |
| Slash command seul | Pas de contexte auto, activation manuelle |
| Hook Claude | Non supporté officiellement |

### Implémentation
Structure skill :
```markdown
---
name: rekall
description: Consultation automatique avant dev, capture après résolution
---

## Déclencheurs
- bug fix → `rekall search "bug $keywords"`
- feature → `rekall search "pattern $keywords"`
- decision → `rekall search "decision $keywords"`

## Actions post-résolution
- Bug résolu → proposer `rekall add --type bug`
- Décision prise → proposer `rekall add --type decision`
```

---

## 6. Migration des données existantes

### Décision
**Migration in-place** avec valeurs par défaut (pas de script séparé).

### Rationale
- Rekall détecte le schéma au démarrage et applique les `ALTER TABLE`
- Clarifications encodées : `memory_type='episodic'`, `access_count=1`, `last_accessed=created_at`
- Pas de perte de données

### Implémentation
Dans `db.py`, après création des tables :
```python
def _migrate_schema(self):
    """Apply schema migrations for cognitive memory."""
    # Check and add new columns if missing
    columns = {row[1] for row in self.conn.execute("PRAGMA table_info(entries)")}

    if 'memory_type' not in columns:
        self.conn.execute("ALTER TABLE entries ADD COLUMN memory_type TEXT DEFAULT 'episodic'")
    if 'last_accessed' not in columns:
        self.conn.execute("ALTER TABLE entries ADD COLUMN last_accessed TEXT")
        self.conn.execute("UPDATE entries SET last_accessed = created_at WHERE last_accessed IS NULL")
    # ... etc
```

---

## Résumé des décisions

| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| Links | Table SQLite | Simple, suffisant pour scale |
| Tracking | Colonnes entries | Atomique, pas de JOIN |
| Memory type | Enum colonne | Clair, migrable |
| Spaced rep | SM-2 simplifié | Prouvé, simple |
| Skill | .claude/skills/*.md | Standard Claude Code |
| Migration | ALTER TABLE in-place | Zero downtime |

---

## Sources techniques

- SQLite FTS5 : https://www.sqlite.org/fts5.html
- SM-2 Algorithm : https://super-memory.com/english/ol/sm2.htm
- Claude Code Skills : https://docs.anthropic.com/claude-code/skills
- Knowledge Graphs Survey : arXiv:2407.11511
