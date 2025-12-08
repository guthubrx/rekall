# Architectures & Patterns AI - Sources de Recherche

**Dernière mise à jour:** 2025-12-05

---

## Scope (Ce que ce fichier couvre)

Ce fichier couvre tout ce qui touche à l'**architecture technique** des systèmes AI :
- Topologies de coordination multi-agents (star, tree, graph, swarm)
- Protocoles de communication (MCP, A2A, function calling)
- Design patterns (ReAct, Plan-and-Execute, Reflection, Supervisor)
- Architectures RAG (Retrieval-Augmented Generation)
- Infrastructure et observabilité (monitoring, métriques LLM)
- Memory systems (working, episodic, semantic)

**Utiliser ce fichier quand** :
- Tu dois choisir une architecture pour un système AI
- Tu évalues un protocole de communication (MCP vs A2A)
- Tu implémentes du RAG et cherches les best practices
- Tu conçois un système multi-agents
- Tu définis l'infrastructure de monitoring pour LLMs

---

## Sources Primaires (CONSULTATION OBLIGATOIRE)

> **RÈGLE** : L'agent DOIT consulter au moins 2 de ces sources via WebSearch avant de proposer quoi que ce soit sur ce thème.

### MCP Specification (Model Context Protocol)
- **URL** : https://modelcontextprotocol.io
- **Nature** : Specification officielle (Anthropic)
- **Spécificité** : Documentation officielle du protocole MCP. Seule source de vérité pour l'implémentation. Évolutions du protocol, breaking changes.
- **Ce qu'on y trouve** : Spec complète JSON-RPC, transport options, tools/resources/prompts/sampling, exemples d'implémentation.
- **Requêtes utiles** : `site:modelcontextprotocol.io`, `"MCP" "model context protocol" specification`

### LangChain / LangGraph Documentation
- **URL** : https://python.langchain.com/docs/
- **Nature** : Documentation framework (leader marché)
- **Spécificité** : Framework le plus utilisé pour construire des applications LLM. LangGraph pour les workflows stateful. Documentation extensive avec exemples.
- **Ce qu'on y trouve** : Patterns officiels, breaking changes, architectures recommandées, intégrations.
- **Requêtes utiles** : `site:langchain.com "LangGraph"`, `site:langchain.com "RAG" best practices`

### Anthropic Documentation
- **URL** : https://docs.anthropic.com
- **Nature** : Documentation vendor (Claude)
- **Spécificité** : Best practices officielles pour Claude. Tool use patterns, prompt engineering, limites et capabilities réelles.
- **Ce qu'on y trouve** : Tool use documentation, context window management, best practices prompting, Claude-specific patterns.
- **Requêtes utiles** : `site:docs.anthropic.com "tool use"`, `site:anthropic.com "agents" patterns`

### arXiv CS.SE (Software Engineering)
- **URL** : https://arxiv.org/list/cs.SE/recent
- **Nature** : Académique (papers de recherche)
- **Spécificité** : Papers sur l'ingénierie des systèmes AI, architectures, patterns émergents. Recherche académique rigoureuse.
- **Ce qu'on y trouve** : Études architectures multi-agents, benchmarks patterns, analyses comparatives.
- **Requêtes utiles** : `site:arxiv.org "LLM architecture"`, `site:arxiv.org "RAG" benchmark`

### Chip Huyen Blog / MLOps Community
- **URL** : https://huyenchip.com/blog/
- **Nature** : Thought leadership (ML Engineering)
- **Spécificité** : Chip Huyen est LA référence pour MLOps et LLMOps. Articles techniques profonds basés sur expérience terrain. Livre "Designing ML Systems".
- **Ce qu'on y trouve** : LLMOps best practices, production patterns, analyses techniques profondes.
- **Requêtes utiles** : `site:huyenchip.com "LLM"`, `"Chip Huyen" "RAG" OR "agents"`

---

## Sources Secondaires (Recommandées)

### Simon Willison Blog
- **URL** : https://simonwillison.net
- **Nature** : Practitioner/Thought leader
- **Spécificité** : Développeur expérimenté qui teste et documente tous les outils LLM. Perspective pratique, tutorials, retours terrain.
- **Ce qu'on y trouve** : Reviews outils, tutorials pratiques, expérimentations.

### LangChain GitHub Issues/Discussions
- **URL** : https://github.com/langchain-ai/langchain
- **Nature** : Communauté open source
- **Spécificité** : Problèmes réels rencontrés en production, discussions techniques, workarounds.
- **Ce qu'on y trouve** : Issues production, breaking changes, solutions communauté.

### Pinecone / Weaviate Blogs
- **URLs** : https://www.pinecone.io/learn/, https://weaviate.io/blog
- **Nature** : Vendors vector DB
- **Spécificité** : Deep dives sur RAG, embeddings, chunking strategies. Expertise vector search.
- **Ce qu'on y trouve** : RAG patterns, chunking strategies, retrieval optimization.

### InfoQ AI/ML
- **URL** : https://www.infoq.com/ai-ml-data-eng/
- **Nature** : Publication technique
- **Spécificité** : Articles d'architecture, case studies techniques, présentations de conférences.
- **Ce qu'on y trouve** : Architectures enterprise, case studies, patterns avancés.

---

## Requêtes de Validation (Templates WebSearch)

> **RÈGLE** : L'agent DOIT exécuter au moins 1 de ces requêtes.

```
# Vérifier la maturité d'un framework avant de l'adopter
"[framework: LangGraph|CrewAI|AutoGen]" + "production" + "issues" OR "problems" 2025

# Comparer des approches architecturales
"[pattern A]" + "vs" + "[pattern B]" + "trade-offs" OR "comparison"

# Chercher les problèmes courants de RAG en production
"RAG" + "production" + "problems" OR "lessons learned" OR "challenges" 2025

# Vérifier l'état d'un protocole
"MCP" OR "A2A" + "adoption" + "enterprise" 2025

# Trouver des retours sur des architectures multi-agents
"multi-agent" + "architecture" + "failure modes" OR "debugging" 2025
```

---

## Red Flags (Signaux d'Alerte)

Lors de la recherche, attention si :

- ❌ **Framework < 6 mois sans major release stable** → Instable, risque breaking changes
- ❌ **Beaucoup d'issues GitHub "breaking" ouvertes** → Migration risquée
- ❌ **Pattern uniquement dans POC/demos** → Pas validé en production
- ❌ **Documentation sparse ou outdated** → Maintenance douteuse
- ❌ **Vendor lock-in fort sans exit strategy** → Risque long-terme
- ❌ **Pas de mention de debugging/observability** → Architecture aveugle

- ✅ **Utilisé par grandes entreprises en production** → Signal positif
- ✅ **Active community (Discord, GitHub)** → Support disponible
- ✅ **Clear migration path entre versions** → Maturité
- ✅ **Documentation des failure modes** → Engineering mature
- ✅ **Exemples de monitoring/observability** → Production-ready
