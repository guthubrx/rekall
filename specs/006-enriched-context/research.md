# Recherche : Contexte Enrichi pour Mémoire IA

**Date** : 2025-12-10
**Objectif** : Explorer l'état de l'art sur la contextualisation des souvenirs et les systèmes de mémoire pour agents IA
**Motivation** : Le champ `context` de Rekall est sous-exploité - comment le rendre vraiment utile pour désambiguïser les embeddings similaires ?

---

## 1. Problématique

### Situation actuelle dans Rekall

```
Entry
├── title, content, type     → Bien exploité
├── embedding                → Recherche sémantique OK
└── context_compressed       → Sous-exploité, manuel, non structuré
```

### Le problème

- **Embeddings similaires** : 10 entrées sur "API timeout" ont des vecteurs proches
- **Contexte discriminant manquant** : Sans contexte, impossible de savoir laquelle est pertinente
- **Capture manuelle** : L'utilisateur oublie `--context`, donc rarement rempli

### L'objectif

```
Embeddings similaires + Contexte riche = Désambiguïsation précise
```

---

## 2. État de l'Art - Architectures de Mémoire

### 2.1 Zep / Graphiti : Architecture Temporelle à 3 Couches

**Source** : [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/html/2501.13956v1)

Architecture hiérarchique avec 3 sous-graphes :

```
┌─────────────────────────────────────────────────────────────┐
│ COUCHE COMMUNAUTÉ                                           │
│ Résumés de haut niveau, patterns généraux                   │
├─────────────────────────────────────────────────────────────┤
│ COUCHE SÉMANTIQUE                                           │
│ Entités extraites + relations + embeddings 1024D            │
├─────────────────────────────────────────────────────────────┤
│ COUCHE ÉPISODIQUE                                           │
│ Événements bruts, logs conversation, timestamps             │
└─────────────────────────────────────────────────────────────┘
```

**Points clés** :

- **Bi-temporel** : 4 timestamps par fait
  - `t_created` / `t_expired` : quand le fait est entré/sorti du système
  - `t_valid` / `t_invalid` : quand le fait était vrai dans le monde réel
- **Recherche hybride** : Combine BM25 + cosine similarity + graph traversal
- **Latence P95** : 300ms sans appel LLM pendant le retrieval

**Applicabilité Rekall** : Ajouter la couche épisodique (contexte conversation) et les timestamps temporels.

### 2.2 A-MEM : Mémoire Agentique inspirée Zettelkasten

**Source** : [A-MEM: Agentic Memory for LLM Agents (NeurIPS 2025)](https://arxiv.org/abs/2502.12110)

Principes du Zettelkasten appliqués aux LLM :

| Principe | Description | Implémentation |
|----------|-------------|----------------|
| Notes atomiques | Une mémoire = une seule idée | Entrées focalisées |
| Identifiants uniques | Chaque note a un ID | ULID dans Rekall |
| Liens bidirectionnels | Connexions entre mémoires | Links avec reason |
| Structure émergente | Organisation par connexions | Knowledge graph |
| Évolution continue | Mémoires se mettent à jour | À implémenter |

**Innovation clé** : Quand une nouvelle mémoire arrive, elle peut **déclencher la mise à jour des mémoires existantes**.

```python
# Pseudo-code A-MEM
def add_memory(new_memory):
    # 1. Générer note structurée
    note = generate_note(new_memory)  # title, keywords, tags, context

    # 2. Trouver mémoires similaires
    similar = find_similar(note.embedding)

    # 3. Créer liens
    for mem in similar:
        create_link(note, mem, reason=explain_relationship())

    # 4. ÉVOLUTION : Mettre à jour les mémoires existantes
    for mem in similar:
        if should_update(mem, note):
            update_context(mem, new_info=note)
```

**Applicabilité Rekall** : Implémenter l'évolution des mémoires et la génération automatique de métadonnées.

### 2.3 AriGraph : Mémoire Épisodique + Sémantique

**Source** : [AriGraph: Learning Knowledge Graph World Models with Episodic Memory for LLM Agents](https://arxiv.org/abs/2407.04363)

Combine deux types de mémoire dans un graphe :

```
┌─────────────────────────────────────────────────────────────┐
│ MÉMOIRE SÉMANTIQUE (triplets)                               │
│ (nginx, has_config, proxy_read_timeout)                     │
│ (timeout_504, caused_by, insufficient_proxy_timeout)        │
├─────────────────────────────────────────────────────────────┤
│ MÉMOIRE ÉPISODIQUE (événements)                             │
│ [2025-12-10 14:30] User asked about 504 error               │
│ [2025-12-10 14:35] Checked nginx logs                       │
│ [2025-12-10 14:40] Modified proxy_read_timeout              │
└─────────────────────────────────────────────────────────────┘
```

**Retrieval à deux étapes** :

1. **Recherche sémantique** : Triplets les plus pertinents
2. **Recherche épisodique** : Événements les plus pertinents

**Applicabilité Rekall** : Le champ `context` pourrait stocker les épisodes, les `entries` sont la mémoire sémantique.

---

## 3. État de l'Art - Consolidation Mémoire

### 3.1 Épisodique → Sémantique

**Source** : [Human-like Memory Recall and Consolidation in LLM-Based Agents (CHI 2024)](https://arxiv.org/html/2404.00573)

```
ÉPISODIQUE                         SÉMANTIQUE
────────────────────────────────────────────────────────────
"User X a fixé timeout nginx"  ──>  "Pattern: timeout nginx"
"User Y a eu même problème"    ──>  → vérifier proxy_read_timeout
"User Z timeout résolu nginx"  ──>  → valeur recommandée: 120s
```

**Résultats expérimentaux** :

- Agents avec mémoire **composite** (épisodique + sémantique) > agents mono-type
- La consolidation améliore le rappel et réduit le stockage

**Trade-offs** :

| Consolidation | Avantages | Inconvénients |
|---------------|-----------|---------------|
| Agressive | Moins de stockage, inférence rapide | Perte de nuances |
| Conservative | Préserve les détails | Memory bloat |

### 3.2 Modèle Hippocampe-Néocortex

**Source** : [Consolidation of Sequential Experience (bioRxiv 2024)](https://www.biorxiv.org/content/10.1101/2024.11.04.621950v2.full)

Inspiré des neurosciences :

```
┌─────────────────────────────────────────────────────────────┐
│ HIPPOCAMPE (Rekall: entries récentes)                       │
│ Encodage rapide des épisodes                                │
│                    │                                        │
│                    ▼ replay/consolidation                   │
│ NÉOCORTEX (Rekall: patterns généralisés)                    │
│ Modèle génératif du monde, patterns abstraits               │
└─────────────────────────────────────────────────────────────┘
```

**Applicabilité Rekall** : Implémenter une "phase de sommeil" où les entrées épisodiques sont consolidées en patterns sémantiques.

---

## 4. État de l'Art - Gestion du Contexte

### 4.1 Contexte Suffisant (Google ICLR 2025)

**Source** : [Deeper Insights into RAG: The Role of Sufficient Context](https://research.google/blog/deeper-insights-into-retrieval-augmented-generation-the-role-of-sufficient-context/)

**Découverte clé** : Les LLM excellent quand le contexte est **suffisant**, mais ne savent pas reconnaître quand il est **insuffisant**.

**Implication pour Rekall** : Il faut stocker assez de contexte pour permettre la désambiguïsation. Un embedding seul ne suffit pas.

### 4.2 Techniques de Résumé de Conversation

**Source** : [LLM Chat History Summarization Guide 2025](https://mem0.ai/blog/llm-chat-history-summarization-guide-2025)

| Technique | Description | Utilisation |
|-----------|-------------|-------------|
| Buffer | Stocke les N derniers messages | Court terme |
| Summary | Résume périodiquement | Long terme |
| Hybrid (Buffer + Summary) | Combine les deux | Optimal |
| Memory Formation | Extrait faits/préférences | Sélectif |

**ConversationSummaryBufferMemory** (LangChain) :

```python
# Pseudo-code
if token_count > max_token_limit:
    summary = llm.summarize(old_messages)
    memory = summary + recent_messages
```

**Problèmes** :

- Perte de détails rares lors du résumé
- Drift contextuel après plusieurs résumés

**Solution proposée** : Extraire les **faits clés** plutôt que résumer tout.

---

## 5. Synthèse : Architecture Proposée pour Rekall

### 5.1 Nouveau Modèle de Contexte

```python
@dataclass
class EnrichedContext:
    """Contexte structuré pour désambiguïsation."""

    # Épisodique (ce qui s'est passé)
    conversation_raw: str          # Derniers échanges compressés
    files_consulted: list[str]     # Fichiers ouverts/modifiés
    error_messages: list[str]      # Erreurs rencontrées

    # Sémantique (ce qu'on en retient)
    situation_summary: str         # Résumé de la situation initiale
    solution_path: str             # Comment on est arrivé à la solution
    alternatives_rejected: str     # Ce qui n'a pas marché et pourquoi

    # Retrieval (pour retrouver)
    trigger_keywords: list[str]    # Mots-clés déclencheurs
    temporal_markers: dict         # Quand, après quoi, avant quoi

    # Méta
    created_at: datetime
    updated_at: datetime
    consolidation_count: int       # Nombre de fois consolidé
```

### 5.2 Workflow de Capture

```
┌─────────────────────────────────────────────────────────────┐
│ 1. CAPTURE AUTOMATIQUE (MCP rekall_add)                     │
├─────────────────────────────────────────────────────────────┤
│ • Conversation: 10 derniers échanges (auto)                 │
│ • Fichiers: via context de l'agent (auto)                   │
│ • Erreurs: extraction des stack traces (auto)               │
│ • Timestamp: datetime.now() (auto)                          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. EXTRACTION STRUCTURÉE (LLM)                              │
├─────────────────────────────────────────────────────────────┤
│ Prompt: "Extrais de cette conversation:                     │
│ - La situation initiale                                     │
│ - Le chemin vers la solution                                │
│ - Les alternatives rejetées                                 │
│ - Les mots-clés pour retrouver ce souvenir"                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. LIENS AUTOMATIQUES                                       │
├─────────────────────────────────────────────────────────────┤
│ • Recherche entrées similaires par embedding                │
│ • Création liens avec reason générée                        │
│ • Mise à jour entrées existantes si pertinent               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. CONSOLIDATION PÉRIODIQUE (background)                    │
├─────────────────────────────────────────────────────────────┤
│ • Identifier clusters d'entrées similaires                  │
│ • Créer PATTERN sémantique si >= 3 entrées                  │
│ • Lier entrées épisodiques au pattern                       │
│ • Proposer en suggestion si incertain                       │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Recherche Hybride Améliorée

```python
def search_with_context(query: str) -> list[Entry]:
    # 1. Recherche sémantique (embedding)
    semantic_results = vector_search(query, top_k=20)

    # 2. Recherche BM25 (keywords)
    keyword_results = bm25_search(query, top_k=20)

    # 3. Fusion des résultats
    candidates = reciprocal_rank_fusion(semantic_results, keyword_results)

    # 4. Re-ranking avec contexte
    for entry in candidates:
        context = get_context(entry.id)
        if context:
            # Score bonus si contexte match la query
            entry.score += context_match_score(query, context)

    return sorted(candidates, key=lambda e: e.score, reverse=True)
```

---

## 6. Références Complètes

### Papers Académiques

1. **A-MEM** (NeurIPS 2025)
   [A-MEM: Agentic Memory for LLM Agents](https://arxiv.org/abs/2502.12110)
   Xu et al. - Rutgers, Ant Group, Salesforce

2. **Zep** (2025)
   [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/html/2501.13956v1)
   Rasmussen et al.

3. **AriGraph** (2024)
   [AriGraph: Learning Knowledge Graph World Models with Episodic Memory for LLM Agents](https://arxiv.org/abs/2407.04363)

4. **Human-like Memory** (CHI 2024)
   [My Agent Understands Me Better: Integrating Dynamic Human-like Memory Recall and Consolidation](https://arxiv.org/html/2404.00573)

5. **RAG Survey** (2024)
   [Retrieval-Augmented Generation for Large Language Models: A Survey](https://arxiv.org/abs/2312.10997)

6. **Sufficient Context** (ICLR 2025)
   [Deeper Insights into RAG: The Role of Sufficient Context](https://research.google/blog/deeper-insights-into-retrieval-augmented-generation-the-role-of-sufficient-context/)

7. **Memory Survey**
   [From Human Memory to AI Memory: A Survey](https://arxiv.org/html/2504.15965v2)

### Outils et Frameworks

- **Graphiti** : [github.com/getzep/graphiti](https://github.com/getzep/graphiti)
- **A-MEM Code** : [github.com/agiresearch/A-mem](https://github.com/agiresearch/A-mem)
- **Memory Survey Repo** : [github.com/Elvin-Yiming-Du/Survey_Memory_in_AI](https://github.com/Elvin-Yiming-Du/Survey_Memory_in_AI)
- **Memento (MCP)** : [mcpmarket.com/server/memento](https://mcpmarket.com/server/memento)

### Articles Techniques

- [LLM Chat History Summarization Guide 2025](https://mem0.ai/blog/llm-chat-history-summarization-guide-2025)
- [Building AI Agents with Knowledge Graph Memory](https://medium.com/@saeedhajebi/building-ai-agents-with-knowledge-graph-memory-a-comprehensive-guide-to-graphiti-3b77e6084dec)
- [AI Agent Memory Systems and Graph Database Integration](https://www.falkordb.com/blog/ai-agents-memory-systems/)
- [What Is AI Agent Memory? (IBM)](https://www.ibm.com/think/topics/ai-agent-memory)

---

## 7. Prochaines Étapes

### Phase 1 : Auto-capture du contexte (Quick Win)

- [ ] Modifier MCP `rekall_add` pour capturer automatiquement le contexte
- [ ] Stocker conversation brute compressée
- [ ] Extraire keywords automatiquement

### Phase 2 : Contexte structuré

- [ ] Nouveau modèle `EnrichedContext`
- [ ] Prompt d'extraction LLM
- [ ] Migration du champ `context_compressed`

### Phase 3 : Recherche hybride

- [ ] Ajouter re-ranking par contexte
- [ ] Combiner BM25 + embedding + context match

### Phase 4 : Consolidation automatique

- [ ] Détection de clusters
- [ ] Génération de patterns sémantiques
- [ ] Évolution des mémoires existantes

---

*Document généré le 2025-12-10 lors de la session de recherche sur l'amélioration du système de contexte Rekall.*
