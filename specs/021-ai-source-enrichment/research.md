# Research: AI-Assisted Source Enrichment

**Date**: 2025-12-13
**Status**: Completed

---

## Questions de Recherche

1. Comment évaluer la qualité d'une source d'information ?
2. Quelles sont les meilleures pratiques pour la curation AI-assisted ?
3. Comment trouver des sources de qualité à consulter régulièrement ?

---

## Sources Consultées

### Frameworks d'Évaluation Qualité

| Source | Type | Findings |
|--------|------|----------|
| [Wang & Strong IQ Framework](https://www.researchgate.net/publication/2817324_Assessment_Methods_for_Information_Quality_Criteria) | Académique | 118 dimensions → 4 catégories : Intrinsèque, Contextuelle, Représentationnelle, Accessibilité |
| [University of Exeter Criteria](https://libguides.exeter.ac.uk/evaluatinginformation/criteria) | Académique | CRAAP Test : Currency, Relevance, Authority, Accuracy, Purpose |
| [FCSM Data Quality Framework](https://nces.ed.gov/fcsm/pdf/FCSM.20.04_A_Framework_for_Data_Quality.pdf) | Gouvernemental | 6 dimensions : Relevance, Accuracy, Timeliness, Accessibility, Interpretability, Coherence |

### AI Knowledge Curation

| Source | Type | Findings |
|--------|------|----------|
| [DataFuel AI Curation](https://www.datafuel.dev/blog/leveraging_ai_to_automate_knowledge_base_curation_and_maintenance) | Industry | NLP pour extraction, standardisation auto, scheduled updates |
| [Ipsos AI Knowledge Libraries](https://www.ipsos.com/en-us/conversations-ai-part-iv-ai-assisted-knowledge-libraries-and-curation) | Research | Pilotes : AI trouve info, mais validation humaine critique pour accuracy |
| [Xyonix Knowledge Curation](https://www.xyonix.com/solutions/knowledge-curation) | Industry | Human-centric benchmarking, gap identification, continuous improvement |
| [Shelf AI in KM](https://shelf.io/blog/role-of-artificial-intelligence-knowledge-management/) | Industry | Intelligent search, auto-categorization, content recommendations |

### Citation Management AI

| Source | Type | Findings |
|--------|------|----------|
| [INRA Citation Management](https://www.inra.ai/blog/citation-management) | Industry | Workflow 5 étapes : AI Discovery → Smart Export → Human Verification → Enhanced Organization → Writing Integration |
| [Sourcely AI Citations](https://www.sourcely.net/resources/top-10-ai-tools-for-citations-in-2025) | Review | Outils : Zotero AI, Mendeley, EndNote, Semantic Scholar |

---

## Findings Clés

### 1. Critères de Qualité des Sources (Consensus)

**Wang & Strong + CRAAP = 6 dimensions pratiques :**

```
1. AUTHORITY (Autorité)
   - Qui est l'auteur/éditeur ?
   - Qualifications ? Affiliations ?
   - Domaine connu (arxiv=haute, blog perso=basse)

2. ACCURACY (Exactitude)
   - Contenu vérifiable ?
   - Références/citations présentes ?
   - Peer-reviewed ?

3. CURRENCY (Fraîcheur)
   - Date de publication ?
   - Dernière mise à jour ?
   - Domaine sensible au temps ? (tech=oui, histoire=non)

4. RELEVANCE (Pertinence)
   - Match avec le besoin utilisateur ?
   - Niveau approprié (débutant/expert) ?

5. PURPOSE (Objectif)
   - Informer, persuader, vendre ?
   - Biais identifiables ?

6. ACCESSIBILITY (Accessibilité)
   - URL fonctionnelle ?
   - Paywall ? Login requis ?
   - Format lisible ?
```

### 2. Balance Human-AI (Consensus fort)

> "AI assists, but humans decide" - INRA

**Pattern recommandé :**
1. **AI** : Collecte, extraction, scoring initial
2. **Humain** : Validation, correction, décision finale
3. **AI** : Apprentissage des corrections pour améliorer

**Red flags :**
- ❌ Application automatique sans validation
- ❌ Score unique sans explication
- ❌ Pas de possibilité de correction

### 3. Sources de Qualité par Thème

**Pattern identifié dans rekall/research/*.md :**

```
Sources Primaires (OBLIGATOIRES)
├── Académiques (arxiv, ACM, IEEE)
├── Officielles (docs framework, specs W3C)
└── Analystes (Gartner, Forrester, APQC)

Sources Secondaires (RECOMMANDÉES)
├── Communautaires (Stack Overflow, GitHub)
├── Blogs experts (Martin Fowler, Kent Beck)
└── Vendors (Pinecone, Weaviate - pour leur domaine)

Red Flags
├── Claims sans preuves
├── Pas de date
├── Auteur anonyme
└── Contenu sponsorisé non déclaré
```

### 4. Métriques de Curation Efficace

| Métrique | Cible | Source |
|----------|-------|--------|
| Precision classification AI | > 80% | Ipsos pilots |
| Réduction temps curation | 70% | DataFuel claims |
| Coût API par source | < $0.002 | Claude Haiku pricing |
| Taux de validation humaine | > 90% | Best practice |

---

## Recommandations pour Rekall

### Quick Wins (Phase 1)

1. **Afficher URLs individuelles** - Déjà stockées dans `entry_sources.source_ref`, juste pas affichées
2. **Compteur URLs par domaine** - Ajouter `unique_urls_count` calculé

### Medium Term (Phase 2)

3. **Enrichissement AI batch** - Prompt structuré, résultats en JSON
4. **Scoring multi-dimensions** - Pas juste A/B/C mais 6 critères
5. **Review UI** - Validation/rejet des suggestions

### Long Term (Phase 3)

6. **Integration research/*.md** - Suggérer sources de qualité connues
7. **Clustering embeddings** - Regroupement auto par similarité
8. **Feedback loop** - Apprendre des validations/rejets

---

## Existant dans Rekall

### Déjà implémenté

- [x] Stockage URLs individuelles (`entry_sources.source_ref`)
- [x] Fichiers research/*.md avec sources curées
- [x] Embeddings pour similarité (Feature 020)
- [x] Score personnel (`personal_score`)
- [x] Fiabilité (`reliability` A/B/C)
- [x] `rekall_sources_suggest` MCP tool
- [x] Auto-classification via `known_domains`

### À ajouter

- [ ] Affichage URLs individuelles dans TUI
- [ ] Enrichissement LLM
- [ ] Résumé automatique
- [ ] Scoring multi-critères AI
- [ ] Suggestions depuis research/*.md
- [ ] Clustering thématique

---

## Conclusion

Le système Rekall a déjà une excellente base :
- **Modèle de données** : Complet (domain + URLs individuelles)
- **Infrastructure** : Embeddings, scoring, known domains
- **Sources de référence** : research/*.md curés manuellement

**Gap principal** : Affichage + automation AI

**Effort estimé** :
- Phase 1 (affichage) : 2-3h
- Phase 2 (AI) : 8-12h
- Phase 3 (avancé) : 12-16h
