# Knowledge Management & AI - Sources de Recherche

**Dernière mise à jour:** 2025-12-05

---

## Scope (Ce que ce fichier couvre)

Ce fichier couvre tout ce qui touche à la **gestion des connaissances** augmentée par l'AI :
- Évolution du Knowledge Management (document-centric → AI-augmented)
- Architectures RAG pour la recherche d'information
- Documentation AI-assisted (auto-documentation, freshness)
- Knowledge graphs et semantic search
- Enterprise search et retrieval
- Capture de connaissances tacites vs explicites

**Utiliser ce fichier quand** :
- Tu conçois un système de documentation AI-augmented
- Tu implémentes du RAG pour la recherche interne
- Tu évalues une plateforme de knowledge management
- Tu veux mesurer l'efficacité d'un système KM
- Tu analyses le build vs buy pour l'enterprise search

---

## Sources Primaires (CONSULTATION OBLIGATOIRE)

> **RÈGLE** : L'agent DOIT consulter au moins 2 de ces sources via WebSearch avant de proposer quoi que ce soit sur ce thème.

### APQC (American Productivity & Quality Center)
- **URL** : https://www.apqc.org/knowledge-management
- **Nature** : Organisation de recherche (KM spécialisé)
- **Spécificité** : LA référence mondiale en Knowledge Management. Benchmarks, best practices, standards de l'industrie. Recherche indépendante depuis 30+ ans.
- **Ce qu'on y trouve** : Benchmarks KM, frameworks, études de cas enterprise, métriques standards KM.
- **Requêtes utiles** : `site:apqc.org "knowledge management" "AI"`, `site:apqc.org "KM" benchmarks`

### arXiv CS.IR (Information Retrieval)
- **URL** : https://arxiv.org/list/cs.IR/recent
- **Nature** : Académique (papers de recherche)
- **Spécificité** : Papers sur RAG, retrieval, semantic search. Recherche de pointe sur les algorithmes de recherche d'information.
- **Ce qu'on y trouve** : Papers RAG récents, benchmarks retrieval, études hallucination mitigation, nouvelles architectures.
- **Requêtes utiles** : `site:arxiv.org "RAG" evaluation`, `site:arxiv.org "retrieval augmented generation" benchmark`

### Pinecone Learning Center
- **URL** : https://www.pinecone.io/learn/
- **Nature** : Vendor (vector DB) / Education
- **Spécificité** : Tutorials très détaillés sur RAG, embeddings, chunking. Pinecone est leader du marché vector DB, leur contenu éducatif est de haute qualité.
- **Ce qu'on y trouve** : Guides RAG complets, chunking strategies, embedding models comparisons, best practices production.
- **Requêtes utiles** : `site:pinecone.io "RAG"`, `site:pinecone.io "chunking"`

### LlamaIndex Documentation
- **URL** : https://docs.llamaindex.ai
- **Nature** : Documentation framework (RAG spécialisé)
- **Spécificité** : Framework dédié au RAG et knowledge retrieval. Documentation extensive sur les patterns de retrieval avancés.
- **Ce qu'on y trouve** : Patterns RAG avancés, query engines, indexing strategies, integrations.
- **Requêtes utiles** : `site:llamaindex.ai "RAG"`, `site:llamaindex.ai "query engine"`

### KMWorld
- **URL** : https://www.kmworld.com
- **Nature** : Publication KM (industrie)
- **Spécificité** : News et tendances du knowledge management. Perspective industrie, case studies, vendors reviews.
- **Ce qu'on y trouve** : Tendances KM, case studies enterprise, comparatifs outils, interviews experts.
- **Requêtes utiles** : `site:kmworld.com "AI"`, `site:kmworld.com "enterprise search"`

---

## Sources Secondaires (Recommandées)

### Weaviate Blog
- **URL** : https://weaviate.io/blog
- **Nature** : Vendor (vector DB)
- **Spécificité** : Focus sur hybrid search (vector + keyword), retrieval optimization. Alternative open source à Pinecone.
- **Ce qu'on y trouve** : Hybrid search patterns, benchmark comparisons, production tips.

### Notion / Confluence / Glean Blogs
- **URLs** : notion.so/blog, atlassian.com/blog/confluence, glean.com/blog
- **Nature** : Vendors (KM platforms)
- **Spécificité** : Fonctionnalités AI de leurs plateformes, tendances KM enterprise.
- **Ce qu'on y trouve** : Features AI, use cases, tendances documentation enterprise.

### Semantic Scholar
- **URL** : https://www.semanticscholar.org
- **Nature** : Moteur de recherche académique (AI-powered)
- **Spécificité** : Exemple réel de semantic search sur papers académiques. Utile pour chercher des papers.
- **Ce qu'on y trouve** : Papers académiques avec ranking AI, citations, related papers.

### ACM SIGIR
- **URL** : https://sigir.org
- **Nature** : Conférence académique (Information Retrieval)
- **Spécificité** : Conférence principale sur l'Information Retrieval. Papers peer-reviewed les plus rigoureux.
- **Ce qu'on y trouve** : Papers SIGIR, état de l'art retrieval, benchmarks officiels.

---

## Requêtes de Validation (Templates WebSearch)

> **RÈGLE** : L'agent DOIT exécuter au moins 1 de ces requêtes.

```
# Vérifier les meilleures pratiques RAG actuelles
"RAG" + "best practices" + "production" + 2025

# Chercher les problèmes courants de RAG
"RAG" + "hallucination" OR "problems" OR "limitations" + 2025

# Évaluer une plateforme KM
"[platform: Notion|Confluence|Glean]" + "AI" + "review" OR "comparison" + 2025

# Trouver des métriques de KM standard
"knowledge management" + "metrics" OR "KPIs" + "AI" + 2025

# Comparer build vs buy pour enterprise search
"enterprise search" + "build vs buy" + "AI" + 2025
```

---

## Red Flags (Signaux d'Alerte)

Lors de la recherche, attention si :

- ❌ **Claims "100% accuracy" pour RAG** → Irréaliste (hallucinations existent toujours)
- ❌ **Solution KM sans plan de maintenance contenu** → Docs obsolètes inévitables
- ❌ **Pas de mention de chunking strategy** → Implémentation naive
- ❌ **Enterprise search sans hybrid (vector + keyword)** → Recall limité
- ❌ **Pas de feedback loop utilisateurs** → Pas d'amélioration continue
- ❌ **Pas de mention de hallucination mitigation** → Risque fiabilité

- ✅ **Métriques de retrieval (Recall@K, MRR) documentées** → Approche sérieuse
- ✅ **Plan de freshness/update automatique** → Maintenance pensée
- ✅ **Human-in-the-loop pour validation** → Safety intégrée
- ✅ **Chunking strategy explicite** → Engineering mature
- ✅ **Benchmarks sur données réelles** → Validation empirique
