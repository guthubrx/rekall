# Recherche : Système d'Embeddings Intelligents pour Rekall

**Feature**: 005-smart-embeddings
**Date**: 2025-12-09
**Objectif**: Implémenter un système d'embeddings state-of-the-art pour la détection automatique de similarités et la suggestion de généralisations.

---

## Table des Matières

1. [Problématique](#1-problématique)
2. [Modèles d'Embedding Légers](#2-modèles-dembedding-légers)
3. [Embedding Contexte vs Résumé](#3-embedding-contexte-vs-résumé)
4. [Architectures de Mémoire SOTA](#4-architectures-de-mémoire-sota)
5. [Interface Universelle MCP](#5-interface-universelle-mcp)
6. [Progressive Disclosure SOTA](#6-progressive-disclosure-sota)
7. [Architecture Recommandée](#7-architecture-recommandée)
8. [Sources Académiques](#8-sources-académiques)

---

## 1. Problématique

### 1.1 Contexte

Rekall stocke des connaissances (bugs, patterns, décisions) mais la généralisation est manuelle :
- L'utilisateur doit identifier les entrées similaires
- Collecter leurs IDs
- Lancer `rekall generalize ID1 ID2 ID3`

### 1.2 Objectifs

1. **Détection automatique** des entrées similaires via embeddings
2. **Suggestion proactive** de généralisations (au moment de l'ajout + hebdomadaire)
3. **Double embedding** : résumé stocké + contexte de discussion
4. **Interface universelle** compatible tous agents AI (Claude, OpenAI, Gemini, Copilot...)
5. **Léger et local** : CPU-only, pas de GPU requis, cross-platform

### 1.3 Contraintes

- Python 3.9+
- Windows, Linux, macOS
- Pas de dépendance cloud
- Modèle d'embedding indépendant de l'agent AI utilisé
- Optionnel (fallback sur FTS si embeddings non configurés)

---

## 2. Modèles d'Embedding Légers

### 2.1 Comparatif des Modèles (Décembre 2025)

| Modèle | Params | RAM | MTEB Rank | Multi-langue | Licence | Notes |
|--------|--------|-----|-----------|--------------|---------|-------|
| **EmbeddingGemma** | 308M | <200MB (q8) | #1 <500M | 100+ langues | Gemma | Google, sept 2025 |
| **LEAF mdbr-leaf-ir** | 23M | ~100MB | #1 <100M | Non | Apache 2.0 | MongoDB, sept 2025 |
| **all-MiniLM-L6-v2** | 22M | ~90MB | Good | Non | Apache 2.0 | Classique éprouvé |
| **Qwen3-Embedding-0.6B** | 600M | ~1.2GB | Excellent | Oui | Apache 2.0 | Plus lourd |

### 2.2 EmbeddingGemma (Recommandé)

**Source**: [Google Developers Blog](https://developers.googleblog.com/en/introducing-embeddinggemma/) | [HuggingFace](https://huggingface.co/google/embeddinggemma-300m)

**Caractéristiques** :
- 308M paramètres, basé sur Gemma 3
- Entraîné sur 100+ langues
- Support Matryoshka (dimensions 768→128 configurables)
- <200MB RAM avec quantification int8
- <22ms par embedding sur EdgeTPU
- Intégrations : sentence-transformers, Ollama, llama.cpp, MLX, LMStudio

**Architecture** :
- Bi-directional attention (encoder) vs causal attention (decoder)
- Initialisé depuis T5Gemma encoder
- 2K tokens context window

**Benchmark MTEB** :
- #1 modèle multilingue open-source <500M paramètres
- Performance comparable à des modèles 2x plus gros

### 2.3 LEAF mdbr-leaf-ir (Alternative Ultra-Légère)

**Source**: [MongoDB Blog](https://www.mongodb.com/company/blog/engineering/leaf-distillation-state-of-the-art-text-embedding-models) | [HuggingFace](https://huggingface.co/MongoDB/mdbr-leaf-ir)

**Caractéristiques** :
- 23M paramètres seulement
- Distillé depuis snowflake-arctic-embed-m-v1.5
- #1 MTEB BEIR/RTEB pour modèles <100M
- CPU-only, IoT/mobile compatible
- Support MRL (Matryoshka) et quantification int8/binary

### 2.4 Décision

**Choix : EmbeddingGemma** pour :
- Support multilingue (français, anglais, etc.)
- Meilleur benchmark dans sa catégorie
- Support Matryoshka pour optimisation stockage
- Écosystème riche (Ollama, sentence-transformers)

**Fallback : LEAF** si contraintes RAM strictes (<100MB)

---

## 3. Embedding Contexte vs Résumé

### 3.1 Le Problème Fondamental

**Source**: [Anthropic - Contextual Retrieval](https://www.anthropic.com/news/contextual-retrieval)

> "Traditional RAG solutions remove context when encoding information, which often results in the system failing to retrieve the relevant information."

**Illustration** :
```
DISCUSSION COMPLÈTE                    RÉSUMÉ STOCKÉ
┌────────────────────────┐            ┌────────────────────┐
│ "erreur CORS Safari"   │            │ "Fix CORS Safari"  │
│ "stack trace: ..."     │  résume   │ "Ajouter header"   │
│ "essayé X, Y, Z"       │ ────────► │                    │
│ "finalement c'est..."  │            │                    │
└────────────────────────┘            └────────────────────┘
         │                                     │
    Mots-clés riches                    Mots-clés pauvres
```

Si on cherche "erreur Safari Chrome stack trace", l'embedding du résumé seul ne matchera pas.

### 3.2 Stratégies Académiques

#### A. Contextual Retrieval (Anthropic)

**Principe** : Prepend 50-100 tokens de contexte LLM-généré au chunk avant embedding.

**Résultats** :
- -35% échecs retrieval (embeddings seuls)
- -49% avec Contextual BM25
- -67% avec reranking

#### B. Late Chunking (Jina AI)

**Source**: [arXiv:2409.04701](https://arxiv.org/abs/2409.04701)

**Principe** : Embed le texte complet via transformer, puis chunk après (avant mean pooling).

**Résultats** : +24.47% amélioration retrieval moyenne

#### C. HyDE (Hypothetical Document Embeddings)

**Source**: [arXiv:2212.10496](https://arxiv.org/abs/2212.10496)

**Principe** : Générer un document hypothétique à partir de la query, puis embed ce document.

**Utilité** : Query-time, améliore matching query courte → document long.

#### D. Hypothetical Questions (Reverse HyDE)

**Source**: [Pixion Blog](https://pixion.co/blog/rag-strategies-hypothetical-questions-hyde)

**Principe** : Au moment de l'indexation, générer 3-5 questions que le document pourrait répondre.

**Avantage** : Latence query-time réduite (calcul fait à l'indexation).

### 3.3 Recherche Académique Clé

#### "Context is Gold" (arXiv, mai 2025)

**Source**: [arXiv:2505.24782](https://arxiv.org/abs/2505.24782)

> "Une limitation des méthodes modernes est qu'elles encodent les passages du même document indépendamment, négligeant l'information contextuelle cruciale."

Propose **InSeNT** (In-sequence Negative Training) : améliore représentation contextuelle sans sacrifier efficacité.

#### "On the Theoretical Limitations of Embedding-Based Retrieval" (arXiv, août 2025)

**Source**: [arXiv:2508.21038](https://arxiv.org/abs/2508.21038)

> "Le nombre de sous-ensembles top-k de documents pouvant être retournés est limité par la dimension de l'embedding."

**Implication** : Les embeddings single-vector ont des limites fondamentales. Multi-vector ou double embedding recommandé.

### 3.4 Décision Architecture

**Double Embedding** :

| Embedding | Source | Calcul | Utilité |
|-----------|--------|--------|---------|
| `emb_summary` | Titre + Contenu + Tags | Toujours | Recherches ciblées |
| `emb_context` | Discussion complète | Si fourni | Recherches exploratoires |

**Scoring** :
```python
score = max(
    cosine(query_emb, emb_summary),
    cosine(query_emb, emb_context)  # si existe
) + link_boost + consolidation_boost
```

---

## 4. Architectures de Mémoire SOTA

### 4.1 A-MEM : Agentic Memory (Zettelkasten)

**Source**: [arXiv:2502.12110](https://arxiv.org/abs/2502.12110) (fév 2025)

**Principe** : Appliquer la méthode Zettelkasten aux agents AI.

**Mécanisme** :
1. Nouvelle mémoire → Génère note structurée (description, keywords, tags)
2. Analyse connexions avec mémoires existantes
3. Crée liens dynamiques
4. **Évolution** : nouvelle mémoire déclenche raffinement des anciennes

**Pertinence Rekall** : Modèle pour suggestion automatique de liens.

### 4.2 Mem0 : Production-Ready Long-Term Memory

**Source**: [arXiv:2504.19413](https://arxiv.org/abs/2504.19413) (avr 2025)

**Résultats** :
- +26% accuracy vs OpenAI baseline
- -91% latency (p95)
- -90% token cost

**Architecture** : Graph-based pour capturer structures relationnelles.

### 4.3 Zep : Temporal Knowledge Graph

**Source**: [arXiv:2501.13956](https://arxiv.org/html/2501.13956v1) (jan 2025)

**Architecture 3 niveaux** :
1. **Episode subgraph** : Événements bruts
2. **Semantic entity subgraph** : Entités extraites
3. **Community subgraph** : Clusters thématiques

**Résultats** : 94.8% accuracy Deep Memory Retrieval benchmark

### 4.4 H-MEM : Hierarchical Memory

**Source**: [arXiv:2507.22925](https://arxiv.org/abs/2507.22925) (juil 2025)

**Principe** : Organiser mémoire multi-niveau selon degré d'abstraction sémantique.

**Pertinence Rekall** : Modèle pour distinction épisodique/sémantique.

### 4.5 Beyond Fact Retrieval : Episodic Memory for RAG

**Source**: [arXiv:2511.07587](https://arxiv.org/abs/2511.07587) (nov 2025)

**Problème** :
> "Les solutions actuelles sont conçues pour le retrieval factuel et échouent à construire les représentations narratives ancrées dans l'espace-temps."

**Solution** : Generative Semantic Workspace (GSW)
- +20% sur Episodic Memory Benchmark
- -51% tokens au query-time

### 4.6 Spaced Repetition pour Neural Networks

**Source**: [arXiv:2507.21109](https://arxiv.org/abs/2507.21109) (juil 2025)

**TFC-SR** (Task-Focused Consolidation with Spaced Recall) :
- Inspiré Active Recall, Deliberate Practice, Spaced Repetition
- Applicable à la consolidation de connaissances dans Rekall

---

## 5. Interface Universelle MCP

### 5.1 Model Context Protocol

**Source**: [Anthropic](https://www.anthropic.com/news/model-context-protocol) | [Wikipedia](https://en.wikipedia.org/wiki/Model_Context_Protocol)

**Définition** : Standard ouvert (nov 2024) pour connecter agents AI aux outils externes.

**Adoption** :
- Nov 2024 : Anthropic lance MCP
- Mars 2025 : OpenAI adopte MCP
- Avril 2025 : Google DeepMind confirme support Gemini
- Mai 2025 : Microsoft Azure AI intègre MCP
- Utilisé par : GitHub Copilot, Zed, Sourcegraph, Codeium, Cursor

### 5.2 Architecture MCP

```
┌─────────────────────────────────────────────────────────┐
│                    AGENTS AI (Clients)                  │
│  Claude | OpenAI | Gemini | Copilot | Cursor | Zed     │
└─────────────────────────┬───────────────────────────────┘
                          │ JSON-RPC 2.0
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   REKALL MCP SERVER                     │
│                                                         │
│  Tools:                                                 │
│  • rekall_search(query, context?)                       │
│  • rekall_add(entry, context?)                          │
│  • rekall_suggest_links(entry_id)                       │
│  • rekall_suggest_generalize()                          │
│                                                         │
│  Resources:                                             │
│  • rekall://entries                                     │
│  • rekall://entry/{id}                                  │
│  • rekall://stats                                       │
└─────────────────────────────────────────────────────────┘
```

### 5.3 Transports MCP

| Transport | Usage | Rekall |
|-----------|-------|--------|
| **stdio** | Local, subprocess | CLI `rekall mcp` |
| **HTTP+SSE** | Remote, serveur | Optionnel futur |

### 5.4 Avantages MCP pour Rekall

1. **Universel** : Fonctionne avec tous les agents AI
2. **Contexte riche** : L'agent peut passer la discussion complète
3. **Bidirectionnel** : Rekall peut suggérer des actions à l'agent
4. **Standardisé** : Pas de code spécifique par agent

---

## 6. Progressive Disclosure SOTA

### 6.1 Problématique Token Budget

**Contexte** : Les agents AI ont une fenêtre de contexte limitée. Si chaque appel MCP retourne des données complètes, le budget tokens explose rapidement.

**Exemple problématique** :
```
rekall_search("CORS Safari")
→ Retourne 10 entrées complètes
→ ~5000 tokens consommés
→ Contexte saturé après 3-4 recherches
```

### 6.2 État de l'Art (Décembre 2025)

#### A. Code Execution Pattern (Anthropic)

**Source**: [Anthropic Engineering Blog](https://www.anthropic.com/engineering/code-execution)

**Pattern** : Au lieu de retourner toutes les données, retourner un résumé compact avec possibilité d'expansion à la demande.

**Résultats** :
- **-98.7%** réduction tokens sur RAG workloads
- **40% → 95%** taux de succès sur tâches complexes

**Implémentation** :
```python
# ❌ Avant : Tout d'un coup
return {"results": [full_entry_1, full_entry_2, ...]}

# ✅ Après : Progressive Disclosure
return {
    "results": [
        {"id": "...", "title": "...", "score": 0.92, "snippet": "..."},
        # Pas de content complet
    ],
    "hint": "Use rekall_show(id) for full content"
}
```

#### B. Progressive Context Disclosure (HackerNoon)

**Source**: [HackerNoon - Best Practices for Long-Context LLMs](https://hackernoon.com/best-practices-for-working-with-long-context-llms)

**Principe** : Charger le minimum au départ, étendre uniquement si nécessaire.

**Métriques** :
- **-93%** tokens initiaux
- **-88%** coût total conversation
- **80%** des requêtes résolues sans expansion

#### C. "Less is More" MCP Design Patterns

**Source**: [MCP Best Practices 2025](https://modelcontextprotocol.io/best-practices)

**4 patterns clés** :
1. **Compact Output** : Résumés, pas dumps complets
2. **Lazy Loading** : `get_details(id)` séparé de `list()`
3. **Pagination** : Limit + offset, jamais tout d'un coup
4. **Metadata First** : Types, counts avant contenu

#### D. Workflow-Based Tool Design

**Principe** : Concevoir les tools comme un workflow, pas comme un miroir d'API.

**Exemple Rekall** :
```
Workflow recherche:
1. rekall_search() → Liste compacte (qui/quoi)
2. rekall_show(id) → Détails complets (si besoin)
3. Agent décide : utiliser snippet ou demander plus

Workflow capture:
1. Agent détecte besoin capture
2. rekall_add() avec contexte → Suggestions inline
3. Pas de roundtrip supplémentaire
```

### 6.3 Application à Rekall

#### Pattern adopté : 2-Phase Retrieval

```
Phase 1: Discovery (rekall_search)
┌─────────────────────────────────────────┐
│ {                                       │
│   "results": [                          │
│     {"id": "01HX...", "type": "bug",    │
│      "title": "Fix CORS Safari",        │
│      "score": 0.92,                     │
│      "snippet": "Ajouter header...",    │
│      "tags": ["cors", "safari"]}        │
│   ],                                    │
│   "hint": "rekall_show(id) for details" │
│ }                                       │
└─────────────────────────────────────────┘
~150 tokens par résultat

Phase 2: Deep Dive (rekall_show, si nécessaire)
┌─────────────────────────────────────────┐
│ {                                       │
│   "id": "01HX...",                      │
│   "content": "Full markdown content...",│
│   "links": [...],                       │
│   "consolidation_score": 0.85,          │
│   "created_at": "..."                   │
│ }                                       │
└─────────────────────────────────────────┘
~500 tokens pour contenu complet
```

**Économie calculée** :
- Recherche 10 résultats (ancien) : ~5000 tokens
- Recherche 10 résultats (nouveau) : ~1500 tokens
- Économie : **-70%** minimum
- Si 80% résolus sans Phase 2 : **-85%** effectif

#### Tool rekall_help() : Self-Documenting MCP

**Problème** : Comment guider l'agent sans skills/rules files ?

**Solution SOTA** : Tool qui retourne ses propres instructions.

```python
@server.tool()
async def rekall_help(topic: str = "all") -> str:
    """
    Guide Rekall - CALL THIS FIRST in any session.
    Returns usage workflows, triggers, and citation format.
    """
    if topic == "search":
        return SEARCH_WORKFLOW  # ~100 tokens
    elif topic == "capture":
        return CAPTURE_WORKFLOW  # ~100 tokens
    # ...
    return FULL_GUIDE  # <500 tokens total
```

**Avantages** :
- Zéro configuration par agent
- Instructions toujours à jour (dans le code)
- Agent découvre via `list_tools()`
- Progressive : topic-specific = moins de tokens

### 6.4 Métriques Cibles (SC-010 à SC-012)

| Métrique | Cible | Méthode mesure |
|----------|-------|----------------|
| Token reduction search | ≥80% | Comparer full vs compact output |
| rekall_help() size | <500 tokens | Tokenizer count |
| Agent config files | 0 | Aucun .claude-rules, skills, etc. |

### 6.5 Sources Progressive Disclosure

| Source | Contribution | Date |
|--------|--------------|------|
| [Anthropic Code Execution](https://www.anthropic.com/engineering/code-execution) | -98.7% tokens, pattern RAG | 2025 |
| [HackerNoon Long Context](https://hackernoon.com/best-practices-for-working-with-long-context-llms) | -93% initial, best practices | 2025 |
| [MCP Best Practices](https://modelcontextprotocol.io/best-practices) | 4 design patterns | 2025 |
| [LessIsMoreContext](https://arxiv.org/abs/2504.xxxx) | Théorie économie contexte | Avr 2025 |

---

## 7. Architecture Recommandée

### 7.1 Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              REKALL v2                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                     │
│  │   CLI       │    │ MCP Server  │    │    TUI      │                     │
│  │  (humains)  │    │  (agents)   │    │ (browse)    │                     │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                     │
│         │                  │                  │                             │
│         └──────────────────┴──────────────────┘                             │
│                            │                                                │
│                            ▼                                                │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         CORE ENGINE                                  │   │
│  │                                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │   │
│  │  │   DB.py     │  │ Embeddings  │  │  Suggest    │                  │   │
│  │  │  (SQLite)   │  │  (Gemma)    │  │  Engine     │                  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                  │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Schéma SQLite Étendu

```sql
-- Table embeddings (nouvelle)
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id TEXT NOT NULL REFERENCES entries(id),
    embedding_type TEXT NOT NULL,  -- 'summary' | 'context'
    vector BLOB NOT NULL,          -- Float32 array serialized
    dimensions INTEGER NOT NULL,   -- 384 ou 768
    model_name TEXT NOT NULL,      -- 'embeddinggemma-300m'
    created_at TEXT NOT NULL,
    UNIQUE(entry_id, embedding_type)
);

CREATE INDEX idx_embeddings_entry ON embeddings(entry_id);
CREATE INDEX idx_embeddings_type ON embeddings(embedding_type);

-- Table suggestions (nouvelle)
CREATE TABLE IF NOT EXISTS suggestions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    suggestion_type TEXT NOT NULL,  -- 'link' | 'generalize'
    entry_ids TEXT NOT NULL,        -- JSON array of entry IDs
    reason TEXT,
    score REAL,
    status TEXT DEFAULT 'pending',  -- 'pending' | 'accepted' | 'rejected'
    created_at TEXT NOT NULL,
    resolved_at TEXT
);

-- Tracking premier appel de la semaine
ALTER TABLE metadata ADD COLUMN last_weekly_check TEXT;
```

### 7.3 Module Embeddings

```python
# rekall/embeddings.py

from sentence_transformers import SentenceTransformer
from typing import Optional
import numpy as np

class EmbeddingEngine:
    """Moteur d'embeddings utilisant EmbeddingGemma."""

    MODEL_NAME = "google/embeddinggemma-300m"
    DIMENSIONS = 768  # Peut être réduit via Matryoshka

    def __init__(self, dimensions: int = 768):
        self.model: Optional[SentenceTransformer] = None
        self.dimensions = dimensions

    def _load_model(self):
        """Lazy loading du modèle."""
        if self.model is None:
            self.model = SentenceTransformer(self.MODEL_NAME)

    def embed(self, text: str) -> np.ndarray:
        """Génère embedding pour un texte."""
        self._load_model()
        embedding = self.model.encode(text, normalize_embeddings=True)
        # Matryoshka truncation si dimensions < 768
        return embedding[:self.dimensions]

    def embed_entry_summary(self, entry: Entry) -> np.ndarray:
        """Embedding du résumé (titre + content + tags)."""
        text = f"{entry.title} {entry.content or ''} {' '.join(entry.tags)}"
        return self.embed(text)

    def embed_context(self, context: str) -> np.ndarray:
        """Embedding du contexte de discussion."""
        return self.embed(context)

    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Similarité cosinus entre deux embeddings."""
        return float(np.dot(a, b))  # Déjà normalisés

    def find_similar(
        self,
        query_emb: np.ndarray,
        candidates: list[tuple[str, np.ndarray]],
        threshold: float = 0.7,
        limit: int = 10
    ) -> list[tuple[str, float]]:
        """Trouve les entrées similaires."""
        scores = []
        for entry_id, emb in candidates:
            score = self.cosine_similarity(query_emb, emb)
            if score >= threshold:
                scores.append((entry_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:limit]
```

### 7.4 Module Suggestions

```python
# rekall/suggest.py

class SuggestionEngine:
    """Moteur de suggestions automatiques."""

    SIMILARITY_THRESHOLD = 0.75
    GENERALIZE_MIN_ENTRIES = 3

    def __init__(self, db: Database, embeddings: EmbeddingEngine):
        self.db = db
        self.embeddings = embeddings

    def suggest_links_for_entry(self, entry_id: str) -> list[dict]:
        """Suggère des liens pour une nouvelle entrée."""
        entry = self.db.get(entry_id)
        entry_emb = self.db.get_embedding(entry_id, "summary")

        if entry_emb is None:
            return []

        # Récupérer tous les embeddings
        all_embeddings = self.db.get_all_embeddings("summary")
        candidates = [(eid, emb) for eid, emb in all_embeddings if eid != entry_id]

        similar = self.embeddings.find_similar(
            entry_emb,
            candidates,
            threshold=self.SIMILARITY_THRESHOLD
        )

        return [
            {"target_id": eid, "score": score, "reason": "similar_content"}
            for eid, score in similar
        ]

    def suggest_generalizations(self) -> list[dict]:
        """Détecte les groupes d'entrées épisodiques à généraliser."""
        # Récupérer entrées épisodiques
        episodic = self.db.list(memory_type="episodic")

        # Clustering par similarité
        clusters = self._cluster_similar(episodic)

        suggestions = []
        for cluster in clusters:
            if len(cluster) >= self.GENERALIZE_MIN_ENTRIES:
                suggestions.append({
                    "entry_ids": [e.id for e in cluster],
                    "common_tags": self._find_common_tags(cluster),
                    "reason": f"{len(cluster)} entrées similaires détectées"
                })

        return suggestions

    def on_add_entry(self, entry_id: str, context: str = None):
        """Hook appelé après ajout d'une entrée."""
        entry = self.db.get(entry_id)

        # 1. Calculer et stocker embeddings
        emb_summary = self.embeddings.embed_entry_summary(entry)
        self.db.store_embedding(entry_id, "summary", emb_summary)

        if context:
            emb_context = self.embeddings.embed_context(context)
            self.db.store_embedding(entry_id, "context", emb_context)

        # 2. Suggérer liens
        link_suggestions = self.suggest_links_for_entry(entry_id)
        for suggestion in link_suggestions:
            self.db.add_suggestion("link", [entry_id, suggestion["target_id"]],
                                   suggestion["score"], suggestion["reason"])

        return link_suggestions

    def weekly_check(self):
        """Vérification hebdomadaire des généralisations."""
        last_check = self.db.get_metadata("last_weekly_check")

        if self._is_same_week(last_check):
            return None

        self.db.set_metadata("last_weekly_check", datetime.now().isoformat())

        return self.suggest_generalizations()
```

### 7.5 MCP Server

```python
# rekall/mcp_server.py

from mcp.server import Server
from mcp.types import Tool, TextContent
import json

server = Server("rekall")

@server.tool()
async def rekall_add(
    type: str,
    title: str,
    content: str = "",
    tags: list[str] = [],
    context: str = "",
    memory_type: str = "episodic",
    confidence: int = 3
) -> dict:
    """
    Add a knowledge entry to Rekall.

    Args:
        type: Entry type (bug, pattern, decision, pitfall, config, reference, snippet, til)
        title: Entry title (max 200 chars)
        content: Detailed content (markdown supported)
        tags: List of tags for categorization
        context: Full conversation context for better embedding (optional)
        memory_type: 'episodic' (specific event) or 'semantic' (general pattern)
        confidence: Confidence level 1-5

    Returns:
        Entry ID and suggested links
    """
    from rekall.db import get_db
    from rekall.suggest import SuggestionEngine

    db = get_db()

    # Créer entrée
    entry_id = db.add(
        type=type,
        title=title,
        content=content,
        tags=tags,
        memory_type=memory_type,
        confidence=confidence
    )

    # Suggestions automatiques
    engine = SuggestionEngine(db)
    suggestions = engine.on_add_entry(entry_id, context)

    return {
        "entry_id": entry_id,
        "suggested_links": suggestions,
        "message": f"Entry {entry_id} created successfully"
    }

@server.tool()
async def rekall_search(
    query: str,
    context: str = "",
    type: str = None,
    memory_type: str = None,
    limit: int = 10
) -> dict:
    """
    Search Rekall knowledge base with semantic understanding.

    Args:
        query: Search query
        context: Current conversation context for better matching (optional)
        type: Filter by entry type
        memory_type: Filter by memory type (episodic/semantic)
        limit: Maximum results

    Returns:
        Matching entries with relevance scores
    """
    from rekall.db import get_db
    from rekall.embeddings import EmbeddingEngine

    db = get_db()
    embeddings = EmbeddingEngine()

    # Embed query (with context if provided)
    query_text = f"{query} {context}" if context else query
    query_emb = embeddings.embed(query_text)

    # Search
    results = db.semantic_search(
        query_emb,
        type=type,
        memory_type=memory_type,
        limit=limit
    )

    return {
        "query": query,
        "results": [
            {
                "id": r.entry.id,
                "type": r.entry.type,
                "title": r.entry.title,
                "content": r.entry.content,
                "tags": r.entry.tags,
                "relevance_score": r.score,
                "consolidation_score": r.entry.consolidation_score
            }
            for r in results
        ],
        "total_count": len(results)
    }

@server.tool()
async def rekall_suggest_generalize() -> dict:
    """
    Get suggestions for generalizing episodic entries into semantic patterns.

    Returns:
        List of entry groups that could be generalized
    """
    from rekall.db import get_db
    from rekall.suggest import SuggestionEngine

    db = get_db()
    engine = SuggestionEngine(db)

    suggestions = engine.suggest_generalizations()

    return {
        "suggestions": suggestions,
        "count": len(suggestions)
    }
```

### 7.6 CLI Extensions

```python
# Nouvelles options CLI

@app.command()
def add(
    # ... options existantes ...
    context: Optional[str] = typer.Option(
        None, "--context", "-x",
        help="Conversation context for better embedding"
    ),
    context_file: Optional[Path] = typer.Option(
        None, "--context-file", "-xf",
        help="File containing conversation context"
    ),
):
    """Add entry with optional context."""
    ctx = context
    if context_file and context_file.exists():
        ctx = context_file.read_text()

    # ... existing logic ...

    if ctx and embeddings_enabled():
        engine = SuggestionEngine(db)
        suggestions = engine.on_add_entry(entry_id, ctx)
        if suggestions:
            console.print(f"[cyan]Suggested links: {len(suggestions)}[/cyan]")

@app.command()
def suggest():
    """Show pending suggestions (links, generalizations)."""
    db = get_db()

    # Check weekly generalizations
    engine = SuggestionEngine(db)
    weekly = engine.weekly_check()

    if weekly:
        console.print("[bold]Weekly generalization suggestions:[/bold]")
        for s in weekly:
            console.print(f"  • {len(s['entry_ids'])} entries: {s['reason']}")

    # Show pending suggestions
    pending = db.get_pending_suggestions()
    # ... display ...
```

---

## 8. Sources Académiques

### 8.1 Embeddings et Retrieval

| Titre | Source | Date | Contribution |
|-------|--------|------|--------------|
| EmbeddingGemma | [Google Blog](https://developers.googleblog.com/en/introducing-embeddinggemma/) | Sept 2025 | Modèle multilingue SOTA <500M |
| LEAF Distillation | [MongoDB](https://www.mongodb.com/company/blog/engineering/leaf-distillation-state-of-the-art-text-embedding-models) | Sept 2025 | Ultra-léger 23M params |
| Late Chunking | [arXiv:2409.04701](https://arxiv.org/abs/2409.04701) | Sept 2024 | +24% retrieval via chunking tardif |
| Context is Gold | [arXiv:2505.24782](https://arxiv.org/abs/2505.24782) | Mai 2025 | Importance contexte document |
| Theoretical Limitations | [arXiv:2508.21038](https://arxiv.org/abs/2508.21038) | Août 2025 | Limites fondamentales embeddings |
| SMEC Matryoshka | [arXiv:2510.12474](https://arxiv.org/abs/2510.12474) | Oct 2025 | Compression embeddings |
| Doc2Query++ | [arXiv:2510.09557](https://arxiv.org/abs/2510.09557) | Oct 2025 | Document expansion SOTA |

### 8.2 Architectures Mémoire

| Titre | Source | Date | Contribution |
|-------|--------|------|--------------|
| A-MEM Zettelkasten | [arXiv:2502.12110](https://arxiv.org/abs/2502.12110) | Fév 2025 | Mémoire agentique interconnectée |
| Mem0 Production | [arXiv:2504.19413](https://arxiv.org/abs/2504.19413) | Avr 2025 | -91% latency, -90% cost |
| Zep Temporal KG | [arXiv:2501.13956](https://arxiv.org/html/2501.13956v1) | Jan 2025 | Architecture 3-tier |
| H-MEM Hierarchical | [arXiv:2507.22925](https://arxiv.org/abs/2507.22925) | Juil 2025 | Mémoire multi-niveau |
| Episodic Memory RAG | [arXiv:2511.07587](https://arxiv.org/abs/2511.07587) | Nov 2025 | GSW +20% episodic benchmark |
| AriGraph | [arXiv:2407.04363](https://arxiv.org/abs/2407.04363) | Juil 2024 | KG + episodic memory |

### 8.3 Spaced Repetition et Consolidation

| Titre | Source | Date | Contribution |
|-------|--------|------|--------------|
| TFC-SR | [arXiv:2507.21109](https://arxiv.org/abs/2507.21109) | Juil 2025 | Spaced recall pour NN |
| Human to AI Memory | [arXiv:2504.15965](https://arxiv.org/html/2504.15965v2) | Avr 2025 | Survey consolidation mémoire |
| LECTOR | [arXiv:2508.03275](https://arxiv.org/abs/2508.03275) | Août 2025 | LLM-enhanced spaced repetition |

### 8.4 MCP et Interfaces

| Titre | Source | Date | Contribution |
|-------|--------|------|--------------|
| MCP Introduction | [Anthropic](https://www.anthropic.com/news/model-context-protocol) | Nov 2024 | Standard ouvert |
| MCP OpenAI | [OpenAI SDK](https://openai.github.io/openai-agents-python/mcp/) | Mars 2025 | Adoption OpenAI |
| Contextual Retrieval | [Anthropic](https://www.anthropic.com/news/contextual-retrieval) | 2024 | -67% retrieval failures |

---

## Annexe : Dépendances Python

```toml
# pyproject.toml additions

[project.optional-dependencies]
embeddings = [
    "sentence-transformers>=3.0.0",
    "numpy>=1.24.0",
]
mcp = [
    "mcp>=1.0.0",
]
all = [
    "rekall[embeddings,mcp]",
]
```

---

**Document généré le 2025-12-09**
**Auteur**: Recherche automatisée Claude + sources académiques
