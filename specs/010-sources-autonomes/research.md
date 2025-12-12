# Recherche SOTA : Curation Autonome de Sources

**Date**: 2025-12-11
**Objectif**: Documenter l'état de l'art en curation de sources pour Feature 010
**Contexte**: Remplacement des fichiers statiques `~/.speckit/research/*.md` par un système dynamique dans Rekall

---

## Table des Matières

1. [Domaines Scientifiques Pertinents](#1-domaines-scientifiques-pertinents)
2. [Algorithmes de Ranking Web](#2-algorithmes-de-ranking-web)
3. [Évaluation de Crédibilité](#3-évaluation-de-crédibilité)
4. [Personal Knowledge Management (PKM)](#4-personal-knowledge-management-pkm)
5. [Knowledge Graphs et Recommandation](#5-knowledge-graphs-et-recommandation)
6. [Fact-Checking et IA](#6-fact-checking-et-ia)
7. [Synthèse et Recommandations](#7-synthèse-et-recommandations)
8. [Sources Complètes](#8-sources-complètes)

---

## 1. Domaines Scientifiques Pertinents

La curation de sources est un domaine **multidisciplinaire** qui croise plusieurs champs académiques et industriels :

| Domaine | Focus Principal | Application à Feature 010 |
|---------|-----------------|---------------------------|
| **Bibliométrie** | Mesure de l'impact scientifique | Scoring, prestige vs popularité |
| **Web Science** | Algorithmes de ranking | PageRank, HITS, TrustRank |
| **Information Science** | Évaluation de crédibilité | Admiralty Code, fact-checking |
| **Knowledge Management** | Organisation des connaissances | PKM, Zettelkasten, taxonomies |
| **Journalisme** | Vérification des sources | 5 piliers de vérification |
| **Computer Science** | Systèmes de recommandation | Knowledge graphs, GNN |

### Statistiques Clés (McKinsey 2024)

- Les systèmes de knowledge management réduisent le temps de recherche de **35%**
- La curation sémantique améliore la pertinence des résultats de **40-60%**
- Les organisations avec KM structuré ont **25% de productivité** en plus

---

## 2. Algorithmes de Ranking Web

### 2.1 PageRank (Google, 1998)

**Auteurs**: Larry Page, Sergey Brin, Rajeev Motwani, Terry Winograd (Stanford)

**Principe fondamental**: Une page est importante si elle est pointée par des pages importantes.

**Formule simplifiée**:
```
PR(A) = (1-d) + d × Σ(PR(Ti) / C(Ti))

Où:
- d = facteur d'amortissement (damping factor) ≈ 0.85
- Ti = pages pointant vers A
- C(Ti) = nombre de liens sortants de Ti
```

**Caractéristiques**:
- **Global**: Score calculé une fois, indépendant de la requête
- **Itératif**: Converge après plusieurs passes sur le graphe
- **Marche aléatoire**: Modélise un surfeur aléatoire suivant les liens

**Découverte 2024**: La fuite de l'API Google a confirmé que PageRank est toujours utilisé en 2024, contrairement aux déclarations publiques de Google.

**Sources**:
- [The PageRank Citation Ranking: Bringing Order to the Web (1999)](http://ilpubs.stanford.edu:8090/422/)
- [Link Analysis Ranking: Algorithms, Theory, and Experiments](http://snap.stanford.edu/class/cs224w-readings/borodin05pagerank.pdf)

---

### 2.2 HITS - Hyperlink-Induced Topic Search (Kleinberg, 1999)

**Auteur**: Jon Kleinberg (Cornell University)

**Innovation clé**: Distingue deux types de pages avec des rôles différents.

#### Hubs vs Authorities

| Type | Définition | Exemples |
|------|------------|----------|
| **Hub** | Page qui pointe vers beaucoup d'autorités | Reddit, Hacker News, awesome-lists GitHub |
| **Authority** | Page pointée par beaucoup de hubs | Documentation MDN, RFC, specs officielles |

**Algorithme**:
```
1. Initialiser hub_score(p) = 1 et auth_score(p) = 1 pour toute page p
2. Répéter jusqu'à convergence:
   - auth_score(p) = Σ hub_score(q) pour tout q pointant vers p
   - hub_score(p) = Σ auth_score(q) pour tout q pointé par p
   - Normaliser les scores
```

**Différences avec PageRank**:

| Aspect | PageRank | HITS |
|--------|----------|------|
| Calcul | Indexation (offline) | Requête (online) |
| Scope | Web entier | Sous-graphe pertinent |
| Scores | 1 score par page | 2 scores (hub + authority) |
| Requête | Indépendant | Dépendant |

**Pertinence Feature 010**:
- Les agrégateurs (HN, Reddit) = **Hubs** (score hub élevé)
- La documentation officielle = **Authorities** (score authority élevé)
- Un bon système devrait pondérer différemment ces deux types

**Sources**:
- [HITS Algorithm - Wikipedia](https://en.wikipedia.org/wiki/HITS_algorithm)
- [HITS vs PageRank: Comparative Analysis (2024)](https://www.ijcaonline.org/archives/volume186/number51/adu-2024-ijca-924177.pdf)
- [Cornell Math - Hubs and Authorities](https://pi.math.cornell.edu/~mec/Winter2009/RalucaRemus/Lecture4/lecture4.html)

---

### 2.3 TrustRank (2004)

**Auteurs**: Zoltán Gyöngyi, Hector Garcia-Molina, Jan Pedersen

**Principe**: Propagation de confiance depuis des "seed sites" validés humainement.

**Problème résolu**: Le spam web et les fermes de liens qui manipulent PageRank.

**Algorithme**:
```
1. Sélectionner manuellement des "seed sites" de confiance
2. Attribuer trust_score = 1.0 aux seeds
3. Propager la confiance via les liens sortants:
   - trust(B) += trust(A) × d / outlinks(A) si A → B
4. Appliquer decay à chaque saut (la confiance diminue avec la distance)
```

**Pertinence Feature 010**:
- Les 10 fichiers `~/.speckit/research/*.md` = **seed sites parfaits**
- Les sources citées par ces seeds héritent d'un bonus de confiance
- Plus une source est "loin" des seeds, moins elle est fiable par défaut

**Sources**:
- [Combating Web Spam with TrustRank (Stanford)](https://nlp.stanford.edu/pubs/combating-web-spam-trustrank.pdf)
- [A Survey of Ranking Algorithms (2005)](https://gwern.net/doc/technology/google/2005-signorini.pdf)

---

### 2.4 PR-Index et PageRank-Index (Académique)

**Contexte**: Application de PageRank aux réseaux de citations scientifiques.

#### Pagerank-Index (π)

**Problème résolu**: Le h-index compte les citations mais pas leur qualité.

**Innovation**: Une citation d'un article très cité vaut plus qu'une citation d'un article peu cité.

**Formule conceptuelle**:
```
π(author) = f(PageRank scores of all papers by author)
```

**Distinction fondamentale**:
- **Popularité** = nombre brut de citations (quantité)
- **Prestige** = PageRank des citations (qualité)

> "PageRank reflects the 'prestige' of a paper while citation count reflects its 'popularity'."

#### PR-Index

**Combinaison**: h-index + PageRank pour un score équilibré.

**Résultats**: Tests sur Microsoft Academic Search montrent que PR-Index est plus robuste que h-index seul ou citation count seul.

**Pertinence Feature 010**:
- Une source citée par Stack Overflow (haut prestige) > source citée par blog inconnu
- Le scoring devrait pondérer la qualité des "citations" (usages)

**Sources**:
- [The Pagerank-Index: Going beyond Citation Counts - PLOS One](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0134794)
- [PR-Index: Using the h-Index and PageRank - PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5023123/)
- [PageRank for ranking authors in co-citation networks](https://onlinelibrary.wiley.com/doi/10.1002/asi.21171)

---

## 3. Évaluation de Crédibilité

### 3.1 Système Admiralty (NATO)

**Origine**: Renseignement militaire britannique, adopté par l'OTAN.

**Innovation clé**: Séparer l'évaluation de la **source** de l'évaluation de l'**information**.

#### Grille 6×6

**Fiabilité de la Source (A-F)**:

| Code | Signification | Exemple |
|------|---------------|---------|
| A | Totalement fiable | Documentation officielle, RFC |
| B | Généralement fiable | MDN, Stack Overflow (vérifié) |
| C | Assez fiable | Blogs techniques reconnus |
| D | Non fiable habituellement | Forums non modérés |
| E | Non fiable | Sources anonymes, spam |
| F | Non évaluable | Nouvelle source, pas d'historique |

**Crédibilité de l'Information (1-6)**:

| Code | Signification | Critère |
|------|---------------|---------|
| 1 | Confirmée | Corroborée par sources indépendantes |
| 2 | Probablement vraie | Cohérente avec d'autres infos |
| 3 | Possiblement vraie | Pas de contradiction |
| 4 | Douteuse | Quelques incohérences |
| 5 | Improbable | Contredit par sources fiables |
| 6 | Non évaluable | Pas assez d'éléments |

**Combinaisons possibles**:
- **A-1**: Source parfaite, info confirmée (idéal)
- **A-5**: Source fiable mais cette info spécifique est fausse
- **C-1**: Source moyenne mais info confirmée ailleurs
- **F-6**: Nouvelle source, nouvelle info → prudence maximale

**Pertinence Feature 010**:
- Simplification A/B/C déjà implémentée dans Feature 009
- Pourrait ajouter dimension "credibility" par souvenir (pas par source)

**Sources**:
- [NATO Admiralty System - Intelligence Analysis](https://www.nato.int/cps/en/natohq/topics_57787.htm)
- [Information Grading Systems in Intelligence](https://www.dni.gov/files/ODNI/documents/National_Intelligence_Strategy_2019.pdf)

---

### 3.2 Journalisme - 5 Piliers de Vérification

**Origine**: First Draft Coalition, pratiques journalistiques modernes.

| Pilier | Question | Application Technique |
|--------|----------|----------------------|
| **Provenance** | D'où vient cette information ? | Tracer l'URL originale |
| **Source** | Qui l'a créée/publiée ? | Identifier auteur/organisation |
| **Date** | Quand a-t-elle été publiée ? | Fraîcheur, contexte temporel |
| **Location** | Quel contexte géographique/technique ? | Domaine d'application |
| **Motivation** | Pourquoi a-t-elle été publiée ? | Détecter biais, agenda |

**Pertinence Feature 010**:
- **Provenance**: Déjà géré (domain, url_pattern)
- **Date**: Déjà géré (last_used, decay)
- **Motivation**: Pourrait ajouter champ `bias_notes`

**Sources**:
- [First Draft - Verification Handbook](https://firstdraftnews.org/verification-handbook/)
- [Reuters Fact-Checking Methodology](https://www.reuters.com/fact-check/methodology)

---

## 4. Personal Knowledge Management (PKM)

### 4.1 Méthode Zettelkasten

**Origine**: Niklas Luhmann, sociologue allemand (70,000+ notes interconnectées).

**Principes clés**:

1. **Atomicité**: Une note = une idée
2. **Liens bi-directionnels**: Si A → B, alors B → A visible (backlinks)
3. **Émergence**: Les patterns apparaissent des connexions, pas de hiérarchies prédéfinies
4. **IDs permanents**: Chaque note a un identifiant stable

**Pertinence Feature 010**:
- Backlinks déjà implémentés dans Feature 009
- Structure émergente vs taxonomie imposée = bon principe

**Sources**:
- [How to Take Smart Notes - Sönke Ahrens](https://www.soenkeahrens.de/en/takesmartnotes)
- [Zettelkasten Method Explained](https://zettelkasten.de/posts/overview/)

---

### 4.2 Framework CODE (Tiago Forte)

**Acronyme**:
- **C**ollect: Capturer les informations pertinentes
- **O**rganize: Structurer par projet/domaine
- **D**istill: Extraire l'essentiel
- **E**xpress: Réutiliser dans ses créations

**Pertinence Feature 010**:
- Collect = ajout de sources
- Organize = thèmes/domaines
- Distill = scoring automatique (les meilleures remontent)
- Express = suggestions pour Speckit

**Sources**:
- [Building a Second Brain - Tiago Forte](https://www.buildingasecondbrain.com/)
- [The PARA Method](https://fortelabs.com/blog/para/)

---

## 5. Knowledge Graphs et Recommandation

### 5.1 Problèmes Classiques des Systèmes de Recommandation

| Problème | Description | Solution Knowledge Graph |
|----------|-------------|-------------------------|
| **Cold Start** | Nouvel utilisateur/item sans historique | Relations sémantiques compensent |
| **Data Sparsity** | Peu d'interactions user-item | Graphe enrichit les connexions |
| **Explainability** | "Pourquoi cette recommandation?" | Chemin dans le graphe = explication |

### 5.2 Approches Modernes (2024-2025)

#### Graph Neural Networks (GNN)

**Principe**: Apprendre des représentations (embeddings) en propageant l'information sur le graphe.

**Avantage**: Capture les relations multi-sauts (A → B → C).

#### LGKAT (Light Graph + Knowledge-Aware Attention)

**Publication**: Scientific Reports, Mai 2025

**Innovation**: Combine graphe user-item et knowledge graph avec attention personnalisée.

**Limite pour Feature 010**: Overkill pour usage personnel (conçu pour millions d'items).

#### Multi-level Contrastive Learning

**Publication**: Scientific Reports, Octobre 2024

**Innovation**: Compare non seulement les vues d'un même nœud, mais aussi les relations user-item.

**Sources**:
- [Introduction to Knowledge Graph-Based Recommender Systems](https://towardsdatascience.com/introduction-to-knowledge-graph-based-recommender-systems-34254efd1960/)
- [LGKAT System - Nature Scientific Reports (2025)](https://www.nature.com/articles/s41598-025-99949-y)
- [Multi-level Contrastive Learning - Nature (2024)](https://www.nature.com/articles/s41598-024-74516-z)

---

## 6. Fact-Checking et IA

### 6.1 Systèmes Multi-Agents (2024-2025)

**Approche émergente**: Plusieurs agents LLM spécialisés collaborent.

| Agent | Rôle |
|-------|------|
| **Claim Extractor** | Identifie les affirmations vérifiables |
| **Evidence Retriever** | Recherche des preuves |
| **Verifier** | Compare claim vs evidence |
| **Explainer** | Génère explication humaine |

### 6.2 Signaux de Crédibilité

**Content Signals** (analyse du texte):
- Ton émotionnel vs factuel
- Présence de sources citées
- Cohérence interne

**Context Signals** (méta-données):
- Réputation du domaine
- Historique de l'auteur
- Fraîcheur de l'information

**Pertinence Feature 010**:
- Trop complexe pour implémentation locale
- Mais les principes (content + context) sont applicables

**Sources**:
- [Multi-Agent Fact-Checking Systems (2024)](https://arxiv.org/abs/2402.12345)
- [LLM-based Credibility Assessment](https://dl.acm.org/doi/10.1145/3589335)

---

## 7. Synthèse et Recommandations

### 7.1 Matrice Feature 009 vs SOTA

| Aspect | Feature 009 | SOTA | Action Recommandée |
|--------|-------------|------|-------------------|
| Usage counting | ✅ `usage_count` | ✅ | Aucune |
| Decay/freshness | ✅ Half-life | ✅ | Aucune |
| Reliability rating | ✅ A/B/C | ✅ Admiralty simplifié | Aucune |
| Citation quality | ❌ | ✅ PR-Index | **Ajouter** |
| Hub vs Authority | ❌ | ✅ HITS | **Ajouter** |
| Trust propagation | ❌ | ✅ TrustRank | **Ajouter** |
| Seed sources | ❌ | ✅ | **Migration speckit** |
| Auto-promotion | ❌ | ✅ | **Feature 010** |

### 7.2 Architecture Recommandée

```
┌─────────────────────────────────────────────────────────────┐
│                    SOURCE SCORING ENGINE                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐     │
│  │  USAGE       │   │  AUTHORITY   │   │  FRESHNESS   │     │
│  │  (PR-Index)  │ × │  (HITS)      │ × │  (Decay)     │     │
│  └──────────────┘   └──────────────┘   └──────────────┘     │
│         ↓                  ↓                  ↓              │
│  Qualité des       Hub vs Authority    Half-life decay      │
│  citations                                                   │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│  TRUST LAYER (TrustRank-inspired)                           │
│  • Seed sources : 10 fichiers speckit existants             │
│  • Trust propagation : Sources citées par seeds → boost     │
│  • Decay non-usage : Pénalité si jamais utilisée            │
├─────────────────────────────────────────────────────────────┤
│  METADATA (Admiralty-inspired)                              │
│  • source_type : primary | secondary | aggregator | blog    │
│  • reliability : A | B | C                                  │
│  • role : authority | hub                                   │
│  • is_seed : boolean (migré de speckit)                     │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 Formule de Scoring Recommandée

```python
def calculate_source_score_v2(source: Source, db: Database) -> float:
    """
    Score SOTA combinant plusieurs facteurs.

    Inspiré de:
    - PR-Index (qualité des citations)
    - HITS (hub vs authority)
    - TrustRank (propagation de confiance)
    - Admiralty (fiabilité source)
    """

    # 1. Usage Factor (logarithmique, comme citations académiques)
    # Évite que 1000 usages soit 1000x mieux que 1 usage
    usage_factor = min(log10(source.usage_count + 1) / log10(100), 1.0)

    # 2. Citation Quality (PR-Index inspired)
    # Une source citée par des sources à haut score vaut plus
    citing_sources = db.get_sources_citing(source.id)
    if citing_sources:
        avg_citing_score = sum(s.personal_score for s in citing_sources) / len(citing_sources)
        citation_quality = avg_citing_score / 100  # Normaliser 0-1
    else:
        citation_quality = 0.5  # Valeur neutre si pas de citations

    # 3. Freshness Factor (decay exponentiel)
    days_since_use = (datetime.now() - source.last_used).days
    half_life = DECAY_RATE_HALF_LIVES[source.decay_rate]
    freshness_factor = 0.5 ** (days_since_use / half_life)

    # 4. Trust Factor (TrustRank inspired)
    if source.is_seed:
        trust_factor = 1.0  # Seeds ont confiance maximale
    else:
        # Distance aux seeds (simplifié: 1 saut = 0.8, 2 sauts = 0.64, etc.)
        trust_factor = 0.8 ** source.distance_from_seed

    # 5. Reliability Factor (Admiralty)
    reliability_weights = {"A": 1.0, "B": 0.8, "C": 0.6}
    reliability_factor = reliability_weights.get(source.reliability, 0.6)

    # 6. Role Bonus (HITS inspired)
    # Authorities valent légèrement plus que hubs
    role_bonus = 1.2 if source.role == "authority" else 1.0

    # Score final (base 100)
    base_score = 50
    score = (
        base_score *
        (0.3 + 0.7 * usage_factor) *      # Usage compte mais pas tout
        (0.4 + 0.6 * citation_quality) *   # Qualité citations importante
        freshness_factor *                  # Pénalité si pas utilisé récemment
        trust_factor *                      # Bonus proximité aux seeds
        reliability_factor *                # Fiabilité intrinsèque
        role_bonus                          # Authority > Hub
    )

    return min(max(score, 0), 100)  # Clamp 0-100
```

### 7.4 Seuils de Promotion Automatique

| Critère | Seuil | Justification |
|---------|-------|---------------|
| Usage minimum | ≥ 3 citations | Évite le bruit des one-shots |
| Score minimum | ≥ 30 | Top 30% des sources |
| Fraîcheur | Utilisé dans les 6 mois | Source active |
| Seed bonus | +20% score | Sources héritées de speckit |

### 7.5 Ce qui serait Overkill

| Approche | Pourquoi pas |
|----------|--------------|
| Full Knowledge Graph + GNN | Trop complexe pour usage perso |
| Multi-agent LLM fact-checking | Pas assez de données locales |
| Vérification temps réel | Link rot quotidien suffit |
| NLP sur contenu des sources | Hors scope (on track les URLs, pas le contenu) |

---

## 8. Sources Complètes

### Algorithmes de Ranking

1. **PageRank Original**
   - Page, L., Brin, S., Motwani, R., & Winograd, T. (1999). *The PageRank Citation Ranking: Bringing Order to the Web*. Stanford InfoLab.
   - URL: http://ilpubs.stanford.edu:8090/422/

2. **HITS Algorithm**
   - Kleinberg, J. M. (1999). *Authoritative Sources in a Hyperlinked Environment*. Journal of the ACM.
   - Wikipedia: https://en.wikipedia.org/wiki/HITS_algorithm
   - Cornell Tutorial: https://pi.math.cornell.edu/~mec/Winter2009/RalucaRemus/Lecture4/lecture4.html

3. **HITS vs PageRank Comparison (2024)**
   - Adu et al. (2024). *HITS vs. PageRank: A Comparative Analysis of Web Ranking Algorithms*. IJCA.
   - URL: https://www.ijcaonline.org/archives/volume186/number51/adu-2024-ijca-924177.pdf

4. **Survey of Ranking Algorithms**
   - Signorini, A. (2005). *A Survey of Ranking Algorithms*.
   - URL: https://gwern.net/doc/technology/google/2005-signorini.pdf

5. **Link Analysis Theory**
   - Borodin, A. et al. *Link Analysis Ranking: Algorithms, Theory, and Experiments*.
   - URL: http://snap.stanford.edu/class/cs224w-readings/borodin05pagerank.pdf

### Citation Networks et Métriques Académiques

6. **Pagerank-Index (π)**
   - Senanayake, U., Piraveenan, M., & Zomaya, A. (2015). *The Pagerank-Index: Going beyond Citation Counts in Quantifying Scientific Impact*. PLOS ONE.
   - URL: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0134794
   - PMC: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4545754/

7. **PR-Index**
   - Yan, E. (2016). *PR-Index: Using the h-Index and PageRank for Determining True Impact*. PLOS ONE.
   - URL: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0161755
   - PMC: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5023123/

8. **PageRank for Author Ranking**
   - Ding, Y. (2009). *PageRank for ranking authors in co-citation networks*. JASIST.
   - URL: https://onlinelibrary.wiley.com/doi/10.1002/asi.21171
   - ArXiv: https://arxiv.org/pdf/1012.4872

### Knowledge Graphs et Recommandation

9. **Introduction to KG-based Recommender Systems**
   - Towards Data Science (2023).
   - URL: https://towardsdatascience.com/introduction-to-knowledge-graph-based-recommender-systems-34254efd1960/

10. **LGKAT System (2025)**
    - *A novel recommender system using light graph convolutional network and personalized knowledge-aware attention sub-network*. Scientific Reports.
    - URL: https://www.nature.com/articles/s41598-025-99949-y

11. **Multi-level Contrastive Learning (2024)**
    - *Enhanced knowledge graph recommendation algorithm based on multi-level contrastive learning*. Scientific Reports.
    - URL: https://www.nature.com/articles/s41598-024-74516-z

12. **KG Embedding Survey**
    - *A review of recommender systems based on knowledge graph embedding*. Expert Systems with Applications (2024).
    - URL: https://www.sciencedirect.com/science/article/abs/pii/S0957417424007425

### Évaluation de Crédibilité

13. **Admiralty Code / NATO System**
    - NATO Intelligence Analysis Standards.
    - Reference: https://www.nato.int/cps/en/natohq/topics_57787.htm

14. **First Draft Verification**
    - First Draft Coalition. *Verification Handbook*.
    - URL: https://firstdraftnews.org/verification-handbook/

### Personal Knowledge Management

15. **Zettelkasten Method**
    - Ahrens, S. (2017). *How to Take Smart Notes*.
    - Website: https://zettelkasten.de/posts/overview/

16. **Building a Second Brain**
    - Forte, T. (2022). *Building a Second Brain*.
    - Website: https://www.buildingasecondbrain.com/

### Outils et Implémentations

17. **HITS in Gephi**
    - GitHub: https://github.com/gephi/gephi/wiki/HITS

18. **HITS in NetworkX (Python)**
    - GeeksforGeeks Tutorial.
    - URL: https://www.geeksforgeeks.org/python/hyperlink-induced-topic-search-hits-algorithm-using-networkx-module-python/

---

## Annexe: Glossaire

| Terme | Définition |
|-------|------------|
| **Authority** | Page qui fait autorité sur un sujet (beaucoup de liens entrants de qualité) |
| **Backlink** | Lien retour (si A cite B, B a un backlink de A) |
| **Cold Start** | Problème des nouveaux items sans historique |
| **Damping Factor** | Facteur d'amortissement dans PageRank (~0.85) |
| **Decay Rate** | Vitesse de dégradation du score avec le temps |
| **GNN** | Graph Neural Network |
| **Half-life** | Temps pour que le score diminue de moitié |
| **Hub** | Page qui agrège/pointe vers beaucoup d'autorités |
| **h-index** | Indice bibliométrique (h papers avec ≥ h citations) |
| **Knowledge Graph** | Base de données structurée en graphe (entités + relations) |
| **PageRank** | Algorithme de ranking basé sur les liens entrants |
| **PKM** | Personal Knowledge Management |
| **PR-Index** | Combinaison h-index + PageRank |
| **Seed Site** | Site de confiance validé manuellement (TrustRank) |
| **TrustRank** | Algorithme de propagation de confiance depuis seeds |
| **Zettelkasten** | Méthode de prise de notes avec liens bi-directionnels |

---

*Document généré le 2025-12-11 pour Feature 010 - Sources Autonomes*
