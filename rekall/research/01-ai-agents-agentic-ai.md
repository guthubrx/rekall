# AI Agents & Agentic AI - Sources de Recherche

**Dernière mise à jour:** 2025-12-05

---

## Scope (Ce que ce fichier couvre)

Ce fichier couvre tout ce qui touche aux **agents IA autonomes** et aux **systèmes multi-agents** :
- Taxonomie et définitions (AI Agent vs Agentic AI)
- Niveaux d'autonomie et types d'agents
- Frameworks et outils pour construire des agents
- Protocoles de communication inter-agents (MCP, A2A)
- Prédictions marché et adoption enterprise
- Risques et échecs documentés ("Agent Washing")

**Utiliser ce fichier quand** :
- Tu proposes une feature impliquant automatisation ou agents
- Tu dois choisir un framework pour orchestrer des agents
- Tu évalues la maturité d'une approche agentic
- Tu veux éviter les pièges classiques (40% projets annulés)

---

## Sources Primaires (CONSULTATION OBLIGATOIRE)

> **RÈGLE** : L'agent DOIT consulter au moins 2 de ces sources via WebSearch avant de proposer quoi que ce soit sur ce thème.

### Gartner Newsroom
- **URL** : https://www.gartner.com/en/newsroom
- **Nature** : Analyste marché (référence enterprise)
- **Spécificité** : Prédictions à 3-5 ans avec méthodologie rigoureuse, Hype Cycles, alertes sur les risques marché. Gartner est souvent le premier à quantifier les échecs (ex: "40% projets annulés").
- **Ce qu'on y trouve** : Prédictions adoption agentic AI, pourcentages marché, alertes sur "Agent Washing", Guardian Agents, timeline réaliste d'adoption enterprise.
- **Requêtes utiles** : `site:gartner.com "agentic AI" 2025`, `site:gartner.com "AI agents" predictions`

### arXiv CS.AI
- **URL** : https://arxiv.org/list/cs.AI/recent
- **Nature** : Académique (papers de recherche)
- **Spécificité** : Papers pré-publication des labos de recherche (Google, OpenAI, universités). Définitions rigoureuses, taxonomies, benchmarks académiques. Souvent 6-12 mois d'avance sur l'industrie.
- **Ce qu'on y trouve** : Taxonomies formelles (AI Agent vs Agentic AI), architectures multi-agents, benchmarks de performance, études sur les limitations.
- **Requêtes utiles** : `site:arxiv.org "AI agents" taxonomy`, `site:arxiv.org "agentic AI" framework`

### Anthropic Research Blog
- **URL** : https://www.anthropic.com/research
- **Nature** : Vendor (éditeur de Claude)
- **Spécificité** : Insights directs du créateur de Claude. Focus sur la sécurité, l'alignement, les capacités réelles vs marketing. MCP protocol officiel.
- **Ce qu'on y trouve** : Capabilities réelles des LLMs, limitations documentées, MCP specification, patterns de tool use, safety considerations.
- **Requêtes utiles** : `site:anthropic.com "AI agents"`, `site:anthropic.com "MCP" protocol`

### OpenAI Blog
- **URL** : https://openai.com/blog
- **Nature** : Vendor (éditeur de GPT)
- **Spécificité** : Announcements officiels, nouveaux modèles, function calling, assistants API. Référence pour les capabilities mainstream.
- **Ce qu'on y trouve** : Nouveaux modèles et capabilities, function calling patterns, assistants API, best practices officielles.
- **Requêtes utiles** : `site:openai.com "agents"`, `site:openai.com "function calling"`

### Google AI Blog
- **URL** : https://ai.googleblog.com
- **Nature** : Vendor (éditeur de Gemini)
- **Spécificité** : Recherche appliquée Google, protocole A2A (Agent-to-Agent), Gemini agents. Scale enterprise.
- **Ce qu'on y trouve** : Protocole A2A, architectures Google, Gemini capabilities, patterns multi-agents à grande échelle.
- **Requêtes utiles** : `site:ai.googleblog.com "agents"`, `site:google.com "A2A protocol"`

---

## Sources Secondaires (Recommandées)

### LangChain Blog
- **URL** : https://blog.langchain.dev
- **Nature** : Vendor/Communauté (framework leader)
- **Spécificité** : LangGraph patterns, retours terrain de la communauté, breaking changes, migrations.
- **Ce qu'on y trouve** : Patterns LangGraph, cas d'usage production, évolutions framework.

### Hacker News
- **URL** : https://news.ycombinator.com
- **Nature** : Communauté développeurs
- **Spécificité** : Retours terrain non filtrés, critiques, échecs documentés, discussions techniques pointues.
- **Ce qu'on y trouve** : Retours d'expérience bruts, problèmes rencontrés en prod, discussions sur les limitations.

### AI Snake Oil
- **URL** : https://www.aisnakeoil.com
- **Nature** : Critique/Académique
- **Spécificité** : Détection du hype et du "AI Washing". Professeurs Princeton qui décortiquent les claims marketing.
- **Ce qu'on y trouve** : Analyses critiques des claims vendors, détection d'exagérations, perspective académique sobre.

### The Batch (DeepLearning.AI)
- **URL** : https://www.deeplearning.ai/the-batch/
- **Nature** : Newsletter (Andrew Ng)
- **Spécificité** : Synthèse hebdomadaire de l'actualité AI par une autorité du domaine.
- **Ce qu'on y trouve** : Résumé des avancées de la semaine, perspective équilibrée, signaux importants.

---

## Requêtes de Validation (Templates WebSearch)

> **RÈGLE** : L'agent DOIT exécuter au moins 1 de ces requêtes.

```
# Valider qu'une approche agentic n'est pas du hype
"agentic AI" + [use case] + "ROI" OR "failure" OR "lessons learned" 2025

# Vérifier la maturité d'un framework en production
"[framework: LangGraph|CrewAI|AutoGen]" + "production" + "issues" OR "problems" 2025

# Chercher des cas d'échecs documentés
"AI agent" + "failed" OR "cancelled" OR "abandoned" + [secteur] 2025

# Vérifier l'état du marché multi-agents
"multi-agent" + "enterprise" + "adoption" + 2025

# Détecter le "Agent Washing" (vendors qui exagèrent)
"agentic AI" + "hype" OR "overpromise" OR "marketing" 2025
```

---

## Red Flags (Signaux d'Alerte)

Lors de la recherche, attention si :

- ❌ **Aucun case study production trouvé** → Technologie probablement immature
- ❌ **Que des articles marketing vendor** → "Agent Washing" probable, manque de validation indépendante
- ❌ **Pas de mention de coûts/limites** → Source biaisée, vision incomplète
- ❌ **Paper arXiv sans citation après 6 mois** → Approche non validée par la communauté
- ❌ **Framework < 6 mois sans release stable** → Risque d'instabilité, breaking changes
- ❌ **Claims de "full autonomy" ou "human-level"** → Red flag majeur, probablement exagéré

- ✅ **Retours d'expérience avec métriques before/after** → Signal fiable
- ✅ **Mention explicite des limitations** → Source honnête
- ✅ **Utilisé par grandes entreprises nommées** → Validation production
- ✅ **Discussion des échecs aussi** → Recherche mature
