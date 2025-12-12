# Research: Sources Medallion Architecture

**Feature**: 013-sources-medallion
**Date**: 2025-12-11
**Status**: Complete

---

## Résumé des Recherches

Cette feature implémente une architecture Medallion pour capturer et promouvoir les sources documentaires. La recherche a été effectuée pendant la phase de spécification et consolidée ici.

---

## 1. Medallion Architecture (Databricks Pattern)

### Source Baseline
- **Fichier**: `~/.speckit/research/04-architectures-patterns.md`
- **Sources consultées**:
  - [Databricks Medallion Architecture](https://www.databricks.com/glossary/medallion-architecture)
  - [Azure Databricks Medallion Guide](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion)
  - [Piethein Strengholt Best Practices](https://piethein.medium.com/medallion-architecture-best-practices-for-managing-bronze-silver-and-gold-486de7c90055)

### Décision
**Choix**: Architecture 3-tier Bronze/Silver/Gold conforme au pattern Databricks.

### Rationale
- **Bronze (Inbox)**: Données brutes avec contexte de capture, aucune transformation
- **Silver (Staging)**: Données enrichies, dédupliquées, validées
- **Gold (Sources curées)**: Table existante, seule extension = flags promotion

### Alternatives Rejetées
| Alternative | Pourquoi Rejetée |
|-------------|------------------|
| Pipeline flat (Bronze → Gold direct) | Perte de traçabilité, pas d'états intermédiaires pour debug |
| 4-tier avec Platinum | Over-engineering pour le volume prévu (~1000 sources) |
| Stream processing (Kafka-like) | Overkill pour batch import CLI |

### Best Practice Appliquée: Quarantine
Les URLs invalides sont marquées `is_valid=FALSE` avec `validation_error` plutôt que supprimées. Permet:
- Audit des faux positifs
- Récupération manuelle si nécessaire
- Métriques de qualité des imports

---

## 2. CLI History Extraction

### 2.1 Claude Code CLI

#### Source Baseline
- [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor)
- [claude-history](https://github.com/thejud/claude-history)
- [Kent Gigger - Hidden Conversation History](https://kentgigger.com/posts/claude-code-conversation-history)

#### Format Documenté
```text
~/.claude/projects/{project-path-encoded}/
├── {conversation-id-1}.jsonl
├── {conversation-id-2}.jsonl
└── ...
```

**Encodage chemin projet**: Les `/` sont remplacés par `-`.
Exemple: `/Users/moi/Projects/foo` → `-Users-moi-Projects-foo`

#### Structure JSONL
```json
{"type": "user", "message": {"content": "..."}, "timestamp": 1733900000000}
{"type": "assistant", "message": {"content": [{"type": "text", "text": "..."}, {"type": "tool_use", "name": "WebFetch", "input": {"url": "https://..."}}]}, "timestamp": 1733900001000}
```

#### Extraction URLs
- Chercher `type: "tool_use"` avec `name: "WebFetch"`
- L'URL est dans `input.url`
- Le contexte utilisateur est dans le message `type: "user"` précédent

#### Limitation Connue
⚠️ **Rétention 30 jours par défaut** - Configurable dans `~/.claude/settings.json`

### 2.2 Cursor IDE

#### Source Baseline
- [cursor-chat-export](https://github.com/somogyijanos/cursor-chat-export)
- [Cursor Forum - Chat History](https://forum.cursor.com/t/chat-history-folder/7653)

#### Format Documenté
```text
~/Library/Application Support/Cursor/User/workspaceStorage/{workspace-hash}/
└── state.vscdb (SQLite)
```

#### Structure SQLite
```sql
SELECT value FROM ItemTable
WHERE [key] IN ('aiService.prompts', 'workbench.panel.aichat.view.aichat.chatdata')
```

La colonne `value` contient du JSON avec les messages de chat.

#### Extraction URLs
- Parser le JSON des messages
- Extraire les URLs via regex depuis le contenu texte
- Pattern: `https?://[^\s<>"')\]]+[^\s<>"')\].,;!?]`

#### Limitation Connue
⚠️ **Format instable** - Cursor change régulièrement sa structure interne

---

## 3. Scoring & Recommendation

### Source Baseline
- **Fichier**: `~/.speckit/research/04-architectures-patterns.md`
- [Google ML - Recommendation Scoring](https://developers.google.com/machine-learning/recommendation/dnn/scoring)
- [Evidently AI - Ranking Metrics](https://www.evidentlyai.com/ranking-metrics/evaluating-recommender-systems)

### Décision
**Formule de scoring**:
```python
score = (citation_count × W_citation) + (project_count × W_project) + (recency_boost × W_recency)

# Où recency_boost = max(0, 1.0 - (days_since_last_seen / decay_days))
```

### Poids par Défaut
| Facteur | Poids | Justification |
|---------|-------|---------------|
| citation | 1.0 | Baseline - chaque citation compte |
| project | 2.0 | Multi-projet = source transversale, plus valuable |
| recency | 0.5 | Boost léger pour sources récentes |

### Seuil de Promotion
**Défaut**: 5.0

Avec les poids par défaut:
- 3 citations = 3.0 + 0.5 récence = 3.5 (pas promu)
- 5 citations = 5.0 + 0.5 récence = 5.5 (promu)
- 2 citations + 2 projets = 2.0 + 4.0 + 0.5 = 6.5 (promu)

### Alternatives Rejetées
| Alternative | Pourquoi Rejetée |
|-------------|------------------|
| Score binaire (promote/not) | Pas de visibilité sur la progression |
| ML-based scoring | Over-engineering, pas assez de données pour entraîner |
| Decay exponentiel | Trop agressif, pénalise les sources stables |

---

## 4. Content Classification

### Décision
Classification basée sur domaine et patterns URL (heuristique simple).

### Mapping Types
| Pattern | Type |
|---------|------|
| github.com, gitlab.com | repository |
| /docs/, .readthedocs., documentation | documentation |
| /api/, swagger, openapi | api |
| stackoverflow.com, stackexchange.com | forum |
| /blog/, medium.com, dev.to | blog |
| arxiv.org, paper | paper |
| (autre) | other |

### Rationale
- Pas besoin de ML pour ~80% des cas d'usage
- Les domaines connus couvrent la majorité des sources dev
- Fallback `other` pour le reste

---

## 5. Web Metadata Extraction

### Décision
Utiliser httpx + BeautifulSoup4 pour extraction synchrone avec timeout.

### Stratégie d'Extraction
1. **Title**: `<title>` ou `og:title`
2. **Description**: `<meta name="description">` ou `og:description`
3. **Language**: `<html lang="...">`

### Timeout & Retry
- Timeout: 5 secondes par défaut
- Retry: Non (marquer pour retry ultérieur si échec)
- Fallback: Source créée sans métadonnées, marquée `is_accessible=FALSE`

### Alternatives Rejetées
| Alternative | Pourquoi Rejetée |
|-------------|------------------|
| requests | httpx a meilleure API et support async natif |
| Playwright/Selenium | Overkill pour metadata, trop lent |
| API tierce (Diffbot, etc.) | Dépendance externe, coût |

---

## 6. Plugin Architecture (Connecteurs)

### Décision
Architecture plugin avec BaseConnector abstract class et registry.

### Interface
```python
class BaseConnector(ABC):
    name: str              # 'claude_cli', 'cursor'
    description: str

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def get_history_paths(self) -> list[Path]: ...

    @abstractmethod
    def extract_urls(self, path: Path, since: datetime | None) -> Iterator[InboxEntry]: ...
```

### Rationale
- Nouveaux CLIs (Windsurf, Aider, Cody) facilement ajoutables
- Chaque connecteur isolé, testable indépendamment
- Registry pour discovery automatique

---

## Points Résolus (ex-NEEDS CLARIFICATION)

| Question | Résolution |
|----------|------------|
| Format exact JSONL Claude? | Documenté via claude-conversation-extractor |
| Tables SQLite Cursor? | Documenté via cursor-chat-export |
| Formule scoring? | Linéaire avec 3 facteurs + decay |
| Seuil promotion? | 5.0 par défaut, configurable |
| Classification contenu? | Heuristique domaine/URL pattern |

---

## Sources Consultées

### Medallion Architecture
1. [Databricks Glossary](https://www.databricks.com/glossary/medallion-architecture) - Pattern canonique
2. [Azure Databricks Guide](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/medallion) - Best practices
3. [Piethein Strengholt](https://piethein.medium.com/medallion-architecture-best-practices-for-managing-bronze-silver-and-gold-486de7c90055) - Production tips

### CLI History
4. [claude-conversation-extractor](https://github.com/ZeroSumQuant/claude-conversation-extractor) - Format JSONL
5. [claude-history](https://github.com/thejud/claude-history) - Parsing Python
6. [cursor-chat-export](https://github.com/somogyijanos/cursor-chat-export) - Format SQLite

### Scoring
7. [Google ML Recommendation](https://developers.google.com/machine-learning/recommendation/dnn/scoring) - Multi-stage scoring
8. [Evidently AI Ranking](https://www.evidentlyai.com/ranking-metrics/evaluating-recommender-systems) - Métriques

### Enrichment
9. [Firecrawl Guide](https://www.firecrawl.dev/blog/complete-guide-to-data-enrichment) - Patterns enrichissement
10. [Haystack Metadata](https://haystack.deepset.ai/blog/extracting-metadata-filter) - Extraction techniques
