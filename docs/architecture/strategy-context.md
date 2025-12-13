# Rekall Home : Contexte Stratégique & Décisions d'Architecture

**Date** : 2025-12-13
**Version** : 1.0
**Projet** : Rekall Home (16.devKMS)
**Type** : Documentation Stratégique (référence pour Speckit)

---

## Table des Matières

1. [Vision & Positionnement Rekall Home](#vision--positionnement-rekall-home)
2. [ADN Rekall : Features Uniques Déjà Implémentées](#adn-rekall--features-uniques-déjà-implémentées)
3. [Décision Stratégique : Format Unique CartaeItem](#décision-stratégique--format-unique-cartaeitem)
4. [Roadmap Home : Foundation pour Server](#roadmap-home--foundation-pour-server)
5. [Différenciateurs Compétitifs](#différenciateurs-compétitifs)
6. [Contexte Marché & Compétition](#contexte-marché--compétition)
7. [Décisions Techniques Majeures](#décisions-techniques-majeures)
8. [Synergies Home ↔ Server](#synergies-home--server)
9. [Next Steps & Priorités](#next-steps--priorités)

---

## Vision & Positionnement Rekall Home

### Mission

> **"Ton second cerveau dev solo avec structured context actionnable, 100% local, gratuit à vie"**

Rekall Home est un **outil de knowledge management personnel** optimisé pour développeurs solo. Contrairement aux solutions B2B (Notion, Confluence) qui visent la collaboration d'équipe, Rekall Home est conçu pour **capitaliser sur l'expérience individuelle**.

### Cas d'Usage Principal (Validé)

**Développeur solo qui veut** :
- ✅ Capturer bugs/patterns/décisions au fil de l'eau
- ✅ Ne JAMAIS résoudre le même bug deux fois
- ✅ Construire sa knowledge base personnelle sans cloud
- ✅ Utiliser CLI/TUI (terminal-first, pas GUI)
- ✅ Zero config, zero friction

**Workflow typique** :
```bash
# Day 1 : Debug bug CORS Safari (2h)
rekall add bug "Safari CORS credentials" --context-interactive
# → Capture situation/solution/what_failed

# Week 3 : Même bug réapparaît
rekall search "safari cors"
# → Trouve solution en 30s (vs 2h re-debug)

# Month 3 : Review connaissances
rekall review
# → Spaced repetition SM-2, consolidation mémoire
```

**Time saved** : 10-20h/mois (debugging évité + knowledge retrieval rapide)

---

## ADN Rekall : Features Uniques Déjà Implémentées

### 1. Structured Context (60% Valeur Précision Chatbot)

**Problème résolu** : Notes Markdown = flou, non-actionnable.

**Solution Rekall** :
```json
{
  "situation": "Safari 16+ bloque fetch même avec CORS headers corrects",
  "solution": "Ajouter credentials: 'include' + Access-Control-Allow-Credentials: true",
  "whatFailed": "Augmenter timeout n'a pas aidé. Retry logic inefficace.",
  "trigger_keywords": ["cors", "safari", "credentials", "fetch"],
  "error_messages": "TypeError: Failed to fetch",
  "files_modified": ["api/middleware/cors.js", "client/services/api.ts"]
}
```

**Impact** :
- ✅ **Réponses actionnables** : Copier-coller solution directement
- ✅ **Contexte préservé** : Pourquoi retry n'a pas marché → évite faux départs
- ✅ **Retrieval précis** : Keywords + error messages exacts → meilleur match search

**Analyse brutale de la valeur** :

Dans notre analyse comparative chatbot, structured context représente **60% de la précision chatbot** :

```
100% Précision chatbot =
├─ 60% : Qualité CONTENU capturé (situation/solution/whatFailed) ← Structured Context
├─ 20% : Retrieval (embeddings + reranking)
├─ 15% : Graph traversal + PageRank
└─ 5%  : OWL reasoning
```

**Pourquoi 60% ?**

Parce qu'un chatbot avec **mauvais contenu + meilleur algo** = mauvais chatbot.
Mais chatbot avec **bon contenu (structured) + algo basique** = bon chatbot.

**Exemple concret** :

Sans structured context :
```
User: "Comment fix timeout API ?"
Chatbot trouve doc "API Troubleshooting" (10 pages Markdown)
→ Retourne lien doc
→ User lit 30 min, extrait solution
→ Time-to-resolution : 45 min
```

Avec structured context :
```
User: "Comment fix timeout API ?"
Chatbot trouve entry structured :
  Situation: API timeout après deploy
  Solution: Augmenter connection pool à 50
  WhatFailed: Retry logic n'a pas aidé
  Files: config/database.yml
→ User copie-colle config
→ Time-to-resolution : 3 min

Time-to-resolution divisé par 15
```

**Différenciateur unique** : Aucun concurrent KMS (Notion, Confluence, Obsidian) n'impose structured context. Tous utilisent Markdown libre.

### 2. Spaced Repetition SM-2 (Cognitive Memory)

**Science cognitive** : Courbe d'oubli Ebbinghaus (1885) → Sans révision, on oublie 70% en 24h.

**Solution Rekall** : Algorithme SM-2 (SuperMemo 2) optimise timing révisions.

**Formule** :
```python
if rating >= 3:  # Easy, Good
    interval = interval * ease_factor
else:  # Hard, Again
    interval = 1 day
    ease_factor *= 0.8

next_review = today + interval
```

**Workflow** :
```bash
rekall review
# → 5 entries dues today
# → User rate chaque entry (Again, Hard, Good, Easy)
# → SM-2 calcule next review (3 days, 1 week, 1 month...)
```

**Impact** :
- ✅ **Consolidation mémoire** : Knowledge reste fresh
- ✅ **Priorise reviews** : Entries difficiles reviennent plus souvent
- ✅ **Long-term retention** : +6-9% retention vs pas de spaced repetition (research)

**Différenciateur unique** : Aucun KMS enterprise n'a spaced repetition. Seuls outils PKM (Personal Knowledge Management) comme Anki, RemNote.

### 3. Episodic vs Semantic Memory

**Science cognitive** : Tulving (1972) distingue :
- **Episodic** : Événements spécifiques ("J'ai fixé bug CORS mardi dernier")
- **Semantic** : Connaissances générales ("Toujours tester CORS sur Safari")

**Solution Rekall** :
- `bug` / `pitfall` / `config` → Episodic (événements uniques)
- `pattern` / `decision` → Semantic (principes réutilisables)

**Command generalize** :
```bash
# Après 3 bugs CORS similaires
rekall generalize 01HX7 01HY2 01HZ3
# → Crée pattern "CORS browser compatibility"
# → Extrait principe : "Toujours tester Safari/Chrome/Firefox"
```

**Impact** :
- ✅ **Transformation expérience → sagesse** : Episodes deviennent patterns
- ✅ **Knowledge compounds** : 3 bugs → 1 pattern réutilisable
- ✅ **Prévention** : Pattern rappelé AVANT de debug

**Différenciateur unique** : Notion/Confluence = pages statiques. Pas de distinction episodic/semantic, pas de généralisation automatique.

### 4. Knowledge Graph (Relations Typées)

**Problème** : Notes isolées = connections perdues.

**Solution Rekall** : Graph sémantique avec relations typées.

**Types relations** :
- `related` : Lié conceptuellement
- `supersedes` : Entry A remplace Entry B (nouvelle policy)
- `derived_from` : Pattern dérivé de bugs
- `contradicts` : Entry A contradicts Entry B (incohérence)

**Raison obligatoire** : Chaque link a justification explicite.

**Impact chatbot** :
- ✅ **Context enrichi** : Solution + patterns liés + warnings contradictions
- ✅ **Navigation conceptuelle** : User suit relations pour explorer
- ✅ **Détection incohérence** : Alert si 2 entries contradictoires

**Différenciateur vs concurrents** :
- **Notion** : Backlinks basiques (pas de types relations, pas de raison)
- **Obsidian** : Graph view mais communauté seulement, pas de types relations
- **Rekall** : Graph structuré + raison obligatoire → plus riche

### 5. Sources Reliability (Medallion Model)

**Problème** : Toutes sources pas égales (StackOverflow ≠ Official Docs).

**Solution Rekall** : Admiralty System (A/B/C) + Personal Score.

**Reliability ratings** :
- **A** : Highly reliable (official docs, peer-reviewed)
- **B** : Generally reliable (reputable blogs, SO accepted answers)
- **C** : Questionable (forum posts, unverified)

**Personal Score** :
```
Score = Usage × Recency × Reliability

- Usage: Combien de fois tu cites cette source
- Recency: Quand tu l'as utilisée dernièrement
- Reliability: A=1.0, B=0.8, C=0.6
```

**Impact chatbot** :
- ✅ **Tri par fiabilité** : Sources A prioritaires vs C
- ✅ **Tracking valuable sources** : Quelles sources tu utilises le plus ?
- ✅ **Link rot detection** : Alert si source URL devient inaccessible

**Différenciateur unique** : Aucun KMS n'a source reliability tracking intégré.

### 6. Local-First, Privacy-First (100% Local)

**Architecture** :
```
~/.local/share/rekall/
├── rekall.db           # SQLite (tout local)
├── embeddings.npz      # Vectors locaux (all-MiniLM-L6-v2)
└── config.toml         # Config zero cloud

Aucune donnée ne quitte ta machine. Jamais.
```

**Différenciateur vs cloud** :
- ❌ **Notion, Confluence, SharePoint** : Cloud-first (on-premise = enterprise plans $$$)
- ✅ **Rekall** : Local-first dès jour 1, gratuit

**Timing parfait** :
- **EU AI Act** (2024-2025) : Régulation systèmes IA
- **Data localization** : 80%+ population mondiale couverte par privacy laws
- **GDPR compliance** : Data portability obligatoire

**Argument de vente B2B** : "Vos données vous appartiennent, 100% local, zero vendor lock-in"

### 7. MCP Protocol (Model Context Protocol)

**Problème** : Intégrer AI assistants = APIs custom par outil.

**Solution Rekall** : MCP (standard Anthropic) = protocole universel.

**Compatible** :
- ✅ Claude Code, Claude Desktop
- ✅ Cursor, Windsurf
- ✅ Continue.dev
- ✅ N'importe quel MCP client

**Command** :
```bash
rekall mcp
# → Démarre serveur MCP
# → AI assistants consultent Rekall automatiquement
```

**Différenciateur unique** : Aucun concurrent KMS n'a MCP natif en 2025.

---

## Décision Stratégique : Format Unique CartaeItem

### Contexte de la Décision

**Question initiale** : Faut-il un format simple pour Home (gratuit) et un format avancé CartaeItem pour Server (payant) ?

**Hypothèse rejetée** : Plugin gratuit "format rekall" + plugin payant "format cartae"

**Problème identifié** : Rendre CartaeItem payant = erreur stratégique chicken-and-egg
- Petit userbase → Pas d'écosystème interopérable
- Pas d'écosystème → Valeur du format s'effondre
- **Analogie W3C** : JSON-LD/RDF/SKOS sont OUVERTS, d'où leur succès

### Décision Finale : Format Unique CartaeItem (Gratuit Partout)

**Architecture** :
```
┌─────────────────────────────────────────────────┐
│        REKALL HOME (Gratuit)                    │
├─────────────────────────────────────────────────┤
│ Format: CartaeItem (JSON-LD) ✅                 │
│                                                 │
│ Enrichissement BASIC (local) :                  │
│ ✅ @context + @type                             │
│ ✅ tags (folksonomy)                            │
│ ✅ categories SKOS (5-10 generic)               │
│ ✅ relationships (types basiques)               │
│ ✅ aiInsights (all-MiniLM, conf 0.6-0.8)        │
└─────────────────────────────────────────────────┘
                    ↕️ COMPATIBLE
┌─────────────────────────────────────────────────┐
│       REKALL SERVER (Payant)                    │
├─────────────────────────────────────────────────┤
│ Format: CartaeItem (JSON-LD) ✅                 │
│                                                 │
│ Enrichissement ADVANCED (cloud) :               │
│ 💰 categories SKOS (100+ industry)              │
│ 💰 aiInsights (Claude Opus, conf 0.85-0.95)     │
│ 💰 relationships ML (poids auto)                │
│ 💰 Graph analytics (PageRank)                   │
│ 💰 OWL reasoning distribué                      │
└─────────────────────────────────────────────────┘
```

### Rationale : Pourquoi Format Unique ?

#### 1. Compatibilité Totale
- Migration Home → Server = zero friction (même format)
- Export Home → Import dans Obsidian/Notion/Neo4j = seamless

#### 2. Encourage Adoption Écosystème
- CartaeItem **standard gratuit** → Autres outils peuvent l'adopter
- Plus d'adoption → **effet réseau** → plus de valeur pour tous
- Rekall devient **référentiel** du format, pas jardin fermé

#### 3. Value Proposition Claire

**Home (gratuit)** :
> "Capture en JSON-LD standard, enrichissement local basique (confiance 60-80%)"

**Server (payant)** :
> "Même format, enrichissement premium cloud (confiance 85-95%), taxonomies expertes, graph analytics"

#### 4. Différenciation TECHNIQUE, pas Artificielle

Les clients B2B **voient la différence de qualité** :

```json
// Home (gratuit) - Modèle local all-MiniLM
{
  "aiInsights": [{
    "model": "all-MiniLM-L6-v2",
    "confidence": 0.67,
    "insight": "Possible pattern related to browser compatibility"
  }]
}

// Server (payant) - Modèle cloud Claude Opus
{
  "aiInsights": [{
    "model": "claude-opus-4.5",
    "confidence": 0.93,
    "insight": "Pattern confirmed: Safari 16+ requires credentials: 'include' for CORS with cookies. See CVE-2023-XXXX. Affects 23% of mobile users. Mitigation: Update API headers + test Safari TestFlight."
  }]
}
```

**Lequel préfères-tu pour du debugging critique en prod ?** Évident : Server.

### Où est la MOAT si Format Gratuit ?

**Réponse** : La moat n'est PAS le format, c'est :

1. **Curation taxonomies SKOS** : 100+ schémas Legal/BFSI/Healthcare = 500+ heures experts
2. **Modèles IA fine-tunés** : Entraînement spécifique par industrie (patterns bugs fintech ≠ patterns bugs healthcare)
3. **Graph algorithms optimisés** : PageRank distribué sur 10M+ entries = non-trivial
4. **Infra scalable** : Multi-tenant, RBAC, analytics = expertise engineering
5. **Compliance** : SOC 2 + ISO 27001 = $100K+ barrière financière

**Analogie** : PostgreSQL est open-source (format SQL standard), mais **AWS RDS fait des milliards $** en vendant PostgreSQL **managé avec features premium**.

**Rekall = pareil** : Format CartaeItem (standard W3C), différenciateur = enrichissement premium.

### Schéma CartaeItem Complet (Home)

```typescript
interface CartaeItem {
  // JSON-LD Core
  "@context": "https://schema.org" | string;
  "@type": "TechArticle" | "HowTo" | "Article" | ...;

  // Identifiers
  identifier: string;  // ULID
  name: string;
  dateCreated: string;  // ISO 8601
  dateModified: string;

  // SKOS Categories (hiérarchique)
  about: {
    prefLabel: string;  // "web-security"
    broader?: string;   // "security"
    narrower?: string[];  // ["cors", "xss"]
    altLabel?: string[];  // Synonymes
  };

  // Tags (folksonomy, flat)
  keywords?: string[];

  // Structured Context (Rekall unique)
  situation?: string;
  solution?: string;
  whatFailed?: string;

  // Content
  articleBody?: string;

  // AI Insights
  aiInsights?: {
    model: string;
    confidence: number;  // 0.0-1.0
    insight: string;
  }[];

  // Relationships (typed, weighted)
  relationships?: {
    type: "relatedTo" | "supersedes" | "derivedFrom" | "contradicts";
    target: string;
    weight?: number;
    reason?: string;
  }[];
}
```

### Bénéfices CartaeItem pour Home

**1. Interopérabilité Native**
```bash
rekall export --format=jsonld obsidian/
# → 100 fichiers .json conformes JSON-LD
# → Import direct Obsidian/Notion/Neo4j
```

**2. SKOS Expansion Requêtes**
```python
# Recherche "security"
# → Expand via SKOS broader/narrower
# → Trouve entries "cors", "xss", "csrf"
# → +30-40% recall vs tags plats
```

**3. Standards W3C = Pérennité 20+ Ans**
- JSON-LD existe depuis 2014, stable
- SKOS depuis 2009
- Pas de risque format propriétaire obsolète

**4. Future-Proof**
- Dans 5 ans, tu veux migrer vers Neo4j ?
- Export JSON-LD → Import Neo4j, ZERO friction

---

## Roadmap Home : Foundation pour Server

### Priorités Home (Post-Migration CartaeItem)

**P0 - Foundation (Bloquant pour Server)** :
1. **024-cartae-format-migration** (4 semaines)
   - Migration Entry → CartaeItem
   - Export/Import JSON-LD
   - Validation schéma

**P1 - Enrichissement (Amélioration UX)** :
2. **025-skos-basic-taxonomy** (1-2 semaines)
   - 5-10 catégories SKOS generic
   - Expansion requêtes
3. **026-cognitive-memory-docs** (1 semaine)
   - Documentation Structured Context
   - Guide SM-2 Spaced Repetition

**P2 - Extensions (Nice-to-Have)** :
4. **027-export-import-advanced** (2 semaines)
   - Export Markdown, Obsidian, Notion
5. **028-plugin-system** (3-4 semaines)
   - Architecture plugins
6. **029-cli-tui-improvements** (2-3 semaines)
   - Review UI, graph viz, auto-completion

**Total effort Home** : ~13-16 semaines

### Synergies Home → Server

**Ce que Home fournit à Server** :

1. **Format CartaeItem** (déjà migré)
   - Server utilise MÊME format
   - Zero conversion Home → Server

2. **Structured Context** (déjà implémenté)
   - Server chatbot utilise situation/solution/whatFailed
   - 60% précision chatbot vient de Home

3. **SKOS taxonomy** (basic 5-10 catégories)
   - Server étend à 100+ catégories industry
   - Mais foundation = Home

4. **Embeddings pipeline** (all-MiniLM)
   - Server peut upgrader vers modèle cloud
   - Mais pipeline = validé sur Home

5. **MCP protocol** (déjà implémenté)
   - Server expose même MCP + features additionnelles

**Conclusion** : Home = 70% de la tech Server. Server = Home + multi-tenant + enrichissement premium.

---

## Différenciateurs Compétitifs

### Rekall Home vs Concurrents

| Feature | Rekall Home | Notion | Obsidian | Confluence |
|---------|-------------|--------|----------|------------|
| **Structured Context** | ✅ situation/solution/whatFailed | ❌ Markdown libre | ❌ Markdown libre | ❌ Markdown libre |
| **Spaced Repetition** | ✅ SM-2 algorithm | ❌ | ❌ | ❌ |
| **Knowledge Graph** | ✅ Relations typées + raison | ❌ Backlinks basiques | ✅ Graph view | ❌ Page tree |
| **SKOS Taxonomy** | ✅ Hiérarchique | ❌ Tags plats | ❌ Tags plats | ❌ Labels |
| **Sources Reliability** | ✅ A/B/C + Personal Score | ❌ | ❌ | ❌ |
| **Local-First** | ✅ 100% local | ❌ Cloud | ✅ Local | ❌ Cloud |
| **MCP Protocol** | ✅ Native | ❌ | ❌ | ❌ |
| **CLI/TUI** | ✅ Terminal-first | ❌ Web only | ❌ Desktop GUI | ❌ Web only |
| **Price** | ✅ **FREE** | $10-$20/user/mois | FREE (Sync $8/mois) | $5-$11/user/mois |

**Verdict** : Rekall Home a **7 features UNIQUES** que AUCUN concurrent n'a.

### Positionnement vs PKM Tools

**PKM (Personal Knowledge Management)** :
- Obsidian : Notes Markdown + graph view (communauté)
- Logseq : Outliner + graph (local-first)
- Notion : Workspace all-in-one (cloud)

**Rekall différence** :
- ✅ **Dev-focused** : Structured context pour bugs/patterns
- ✅ **Cognitive science** : Spaced repetition SM-2, episodic/semantic
- ✅ **Actionnable** : Pas juste notes, mais solutions copy-paste
- ✅ **AI-ready** : MCP protocol natif, embeddings, RAG-ready

**Positionnement** :
> "Obsidian pour devs qui veulent capitaliser sur debugging experience, avec science cognitive intégrée"

---

## Contexte Marché & Compétition

### Marché KMS (Knowledge Management Systems)

**Taille marché** :
- **2025** : $13.70 milliards USD
- **2030** : $32.15 milliards USD
- **CAGR** : 18.6%

**Segmentation** :
- Cloud : 62.66% (croissance 20.1% CAGR)
- On-premise : 37.34%
- Grandes entreprises : 56.52%
- PME : 43.48% (CAGR 19.60%, croissance plus rapide)

**Tendances 2025** :
1. **Privacy-first** : EU AI Act, data localization = top priorité
2. **AI-powered** : Gartner prédit AI-KM réduira resolution time 30% d'ici 2026
3. **Remote/hybrid work** : Demand accrue centralized knowledge repositories

**Opportunité Rekall** :
- Timing parfait privacy-first (Home = 100% local)
- Dev-focused niche sous-servie (Notion/Confluence = generalist)

### Compétition Principale (PKM/Dev Tools)

**Obsidian** :
- **Users** : 1M+ (community-driven)
- **Model** : Free + Sync $8/mois
- **Forces** : Graph view, plugins community, Markdown
- **Faiblesses** : Pas de structured context, pas de spaced repetition natif, pas de dev-specific features

**Logseq** :
- **Users** : 500K+
- **Model** : Free, local-first
- **Forces** : Outliner, graph, local-first
- **Faiblesses** : Même que Obsidian

**Notion** :
- **ARR** : $500M (2025 estimate)
- **Pricing** : $10-$20/user/mois
- **Forces** : All-in-one workspace, collaboration
- **Faiblesses** : Cloud-only (privacy), pas dev-focused, Markdown libre

**GitHub Issues/Projects** :
- **Users** : 100M+ devs
- **Model** : Inclus dans GitHub
- **Forces** : Intégré workflow dev, collaboration
- **Faiblesses** : Pas de knowledge management, pas de search sémantique, pas de spaced repetition

**Rekall positionnement** :
- Niche : Devs solo qui veulent **capitaliser expérience** (pas juste tracker issues)
- Différenciateur : **Structured context + cognitive memory** = unique
- Model : **Free forever** (Home), upsell vers Server (B2B teams)

---

## Décisions Techniques Majeures

### 1. Langage : Python 3.10+

**Pourquoi Python ?**
- ✅ Écosystème AI/ML riche (embeddings, NLP)
- ✅ Batteries included (SQLite, argparse, etc.)
- ✅ Rapid prototyping
- ✅ Large dev community

**Pourquoi 3.10+ ?**
- Match patterns (PEP 634)
- Union types (PEP 604)
- Better error messages

### 2. Database : SQLite

**Pourquoi SQLite ?**
- ✅ Local-first (fichier unique `~/.local/share/rekall/rekall.db`)
- ✅ Zero config (pas de serveur DB)
- ✅ FTS5 full-text search natif
- ✅ Performance OK jusqu'à 100K+ entries
- ✅ Portable (cross-platform)

**Limitations futures** :
- Server va probablement migrer PostgreSQL (multi-tenant scaling)
- Mais Home reste SQLite (simplicité > scaling)

### 3. Embeddings : all-MiniLM-L6-v2 (Local)

**Pourquoi ce modèle ?**
- ✅ 100% local (pas d'API, pas de cloud)
- ✅ Rapide : ~50ms par embedding (laptop CPU)
- ✅ Petit : ~100MB RAM
- ✅ Efficace : 384-dim vectors, bon recall

**Alternative considérée** : OpenAI text-embedding-3
- ❌ Rejetée : Requiert API key, cloud, coûts

**Configurable** : User peut switcher vers modèle multilingual si besoin

### 4. Interface : CLI/TUI (Terminal-First)

**Pourquoi terminal-first ?**
- ✅ Dev workflow = déjà dans terminal
- ✅ SSH-friendly (remote servers, containers)
- ✅ Keyboard-driven (efficacité)
- ✅ Pas de dépendances GUI (headless servers)

**Philosophie** :
> "Modern development happens everywhere: laptop, remote servers, containers, SSH. Terminal interface = accessible partout."

**Web UI** : Prévu pour Server (B2B), pas Home (dev solo).

### 5. MCP Protocol (Model Context Protocol)

**Pourquoi MCP ?**
- ✅ Standard Anthropic (Claude Code, Claude Desktop)
- ✅ Ecosystème grandissant (Cursor, Windsurf, Continue.dev)
- ✅ Protocole ouvert (pas vendor lock-in)

**Alternative considérée** : APIs custom par IDE
- ❌ Rejetée : Maintenance nightmare (VS Code API ≠ Cursor API ≠ etc.)

---

## Synergies Home ↔ Server

### Ce qui Bénéficie aux Deux

**1. Format CartaeItem** : Développé pour Home, utilisé par Server
- Home : Export ponctuel vers Obsidian
- Server : API CartaeItem pour intégrations B2B

**2. Structured Context** : Recherche validée sur Home → scales sur Server
- Home : Debugging personnel
- Server : Chatbot B2B (60% précision)

**3. Knowledge Graph** : Algorithmes développés sur Home → valeur B2B
- Home : Patterns personnels
- Server : Patterns équipe + analytics collective

**4. SKOS Taxonomy** : Foundation Home (5-10) → étendue Server (100+)
- Home : Catégories generic suffisantes
- Server : Industry-specific (Legal, BFSI, Healthcare)

**5. Plugin System** (futur) : Community peut créer plugins Home → Server adopte meilleurs
- Home : Plugins gratuits (exporters, enrichment)
- Server : Plugins premium (advanced analytics, OWL reasoning)

### Flux Innovation : Bottom-Up

```
Home (OSS, Community)
    ↓ Innovation
    ↓ Validation
    ↓ Adoption
Server (Commercial)
    ↓ Funding
    ↓ Development
    ↓ Backport
Home (OSS, Amélioré)
```

**Cycle vertueux** :
1. Community contribue features Home (gratuit)
2. Meilleurs features validés usage réel
3. Server adopte + améliore (payant)
4. Funding commercial finance développement Home
5. Nouvelles features backportées vers Home
6. Repeat

---

## Next Steps & Priorités

### Immédiat (Semaines 1-4) : Migration CartaeItem

**Spec** : 024-cartae-format-migration

**Objectif** : Foundation technique pour TOUT le reste.

**Tâches** :
1. Définir Pydantic model CartaeItem
2. Script migration Entry → CartaeItem
3. Export/Import JSON-LD
4. Tests migration 1,000 entries

**Critères succès** :
- Migration 10,000 entries < 30s
- Zero perte données
- Performance search identique

### Court-terme (Semaines 5-8) : SKOS + Documentation

**Specs** : 025-skos-basic-taxonomy + 026-cognitive-memory-docs

**Objectif** : Améliorer UX + onboarding.

**Tâches** :
1. Taxonomie SKOS 5-10 catégories
2. Query expansion broader/narrower
3. Documentation structured context
4. Guide spaced repetition

**Critères succès** :
- Recall +30% avec SKOS
- Nouveau user comprend structured context < 5 min

### Moyen-terme (Semaines 9-16) : Extensions

**Specs** : 027-export-import-advanced + 028-plugin-system + 029-cli-tui-improvements

**Objectif** : Polish UX, extensibilité.

**Tâches** :
1. Export Markdown/Obsidian/Notion
2. Plugin system architecture
3. TUI review interface améliorée
4. Auto-completion shell

**Critères succès** :
- Export Obsidian preserves 100% data
- 3+ plugins community dans 3 mois

### Long-terme : Maintenance + Community

**Focus** :
- Bug fixes
- Performance optimization
- Community support (GitHub issues, discussions)
- Documentation improvements

**Métriques** :
- GitHub stars growth
- Contributors actifs
- Issues resolution time < 7 days

---

## Conclusion : Home = Foundation Solide

Rekall Home n'est **PAS un side project**. C'est la **foundation technique ET philosophique** de tout l'écosystème Rekall.

**Home fournit** :
- ✅ 70% de la tech Server (format, structured context, embeddings)
- ✅ Validation product-market fit (devs solo = early adopters)
- ✅ Community OSS (contributors, feedback, plugins)
- ✅ Positioning anti-vendor-lock-in (argument B2B Server)

**Server serait impossible sans Home.**

Sans Home :
- Pas de validation structured context (60% précision chatbot)
- Pas de format CartaeItem testé en production
- Pas de community trust (OSS rassure enterprises)
- Pas de differentiation claire vs Notion/Confluence

**Analogie** : PostgreSQL (OSS) rend AWS RDS possible. Home (gratuit) rend Server (payant) possible.

---

**Ce document est la référence stratégique complète pour toute décision architecture/produit Rekall Home.**

*Dernière mise à jour : 2025-12-13*
