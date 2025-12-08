# ROI & Business Value - Sources de Recherche

**Dernière mise à jour:** 2025-12-05

---

## Scope (Ce que ce fichier couvre)

Ce fichier couvre tout ce qui touche à la **justification économique** de l'AI :
- Mesure du ROI (Return on Investment) des projets AI
- Business cases et études TEI (Total Economic Impact)
- Benchmarks de productivité par secteur
- Coûts cachés et TCO (Total Cost of Ownership)
- Facteurs de succès et anti-patterns économiques
- Payback periods et horizons de rentabilité

**Utiliser ce fichier quand** :
- Tu dois justifier économiquement un investissement AI
- Tu cherches des benchmarks sectoriels de ROI
- Tu veux identifier les coûts cachés d'un projet
- Tu construis un business case pour stakeholders
- Tu évalues si une approche AI est économiquement viable

---

## Sources Primaires (CONSULTATION OBLIGATOIRE)

> **RÈGLE** : L'agent DOIT consulter au moins 2 de ces sources via WebSearch avant de proposer quoi que ce soit sur ce thème.

### Forrester Research
- **URL** : https://www.forrester.com/research/
- **Nature** : Analyste marché (spécialiste ROI)
- **Spécificité** : Études TEI (Total Economic Impact) - méthodologie rigoureuse de calcul ROI. Forrester est LA référence pour quantifier la valeur business de l'IT. Études sponsorisées mais avec méthodologie publique.
- **Ce qu'on y trouve** : ROI chiffrés par use case (customer service, code assistance, document processing), payback periods, TCO détaillés, facteurs de risque quantifiés.
- **Requêtes utiles** : `site:forrester.com "AI" "TEI"`, `site:forrester.com "ROI" "generative AI" 2025`

### McKinsey Insights
- **URL** : https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights
- **Nature** : Cabinet conseil (stratégie)
- **Spécificité** : Vision stratégique C-level, études globales sur l'impact économique de l'AI. Focus sur la création de valeur business, pas technique.
- **Ce qu'on y trouve** : Potentiel économique de l'AI par secteur, stratégies d'adoption, value creation frameworks, études de productivité.
- **Requêtes utiles** : `site:mckinsey.com "generative AI" "economic impact"`, `site:mckinsey.com "AI productivity" 2025`

### Gartner
- **URL** : https://www.gartner.com/en/research
- **Nature** : Analyste marché (prédictions)
- **Spécificité** : Prédictions marché, TCO analysis, business value frameworks. Focus sur la réalisation de valeur (pas juste les promesses).
- **Ce qu'on y trouve** : Prédictions ROI réalistes, alertes sur les projets qui échouent, frameworks de mesure de valeur, TCO par technologie.
- **Requêtes utiles** : `site:gartner.com "AI" "business value"`, `site:gartner.com "AI ROI" 2025`

### Harvard Business Review
- **URL** : https://hbr.org/topic/subject/artificial-intelligence
- **Nature** : Publication business (académique-pratique)
- **Spécificité** : Articles équilibrés entre théorie et pratique. Cas d'échecs documentés, analyses post-mortem, perspective managériale.
- **Ce qu'on y trouve** : Case studies réels avec résultats, analyses d'échecs, perspectives de dirigeants, leçons apprises.
- **Requêtes utiles** : `site:hbr.org "AI" "ROI"`, `site:hbr.org "AI investment" "failure"`

### MIT Sloan Management Review
- **URL** : https://sloanreview.mit.edu/tag/artificial-intelligence/
- **Nature** : Publication académique-business
- **Spécificité** : Recherche appliquée MIT, études empiriques avec données, focus sur les résultats mesurables.
- **Ce qu'on y trouve** : Études de productivité avec méthodologie, analyses coûts-bénéfices, research-backed ROI analysis.
- **Requêtes utiles** : `site:sloanreview.mit.edu "AI" "productivity"`, `site:sloanreview.mit.edu "AI" "value"`

---

## Sources Secondaires (Recommandées)

### CB Insights
- **URL** : https://www.cbinsights.com/research/
- **Nature** : Analyse startup/VC
- **Spécificité** : Tendances d'investissement, échecs de startups AI, analyse de marché venture capital.
- **Ce qu'on y trouve** : Pourquoi les startups AI échouent, tendances d'investissement, valorisations.

### a16z (Andreessen Horowitz)
- **URL** : https://a16z.com/ai/
- **Nature** : VC/Thought leadership
- **Spécificité** : Perspective VC sur l'économie de l'AI, coûts infrastructure, marges des applications AI.
- **Ce qu'on y trouve** : Économie des modèles AI, coûts infrastructure GPU, analyse de rentabilité.

### Deloitte AI Institute
- **URL** : https://www2.deloitte.com/us/en/pages/consulting/solutions/ai-institute.html
- **Nature** : Cabinet conseil (études terrain)
- **Spécificité** : Études d'adoption enterprise, enquêtes terrain, ROI par industrie.
- **Ce qu'on y trouve** : State of AI reports, études d'adoption, benchmarks sectoriels.

### OpenAI / Anthropic / Cloud Pricing
- **URLs** : openai.com/pricing, anthropic.com/pricing, cloud providers
- **Nature** : Vendors (pricing officiel)
- **Spécificité** : Coûts réels des APIs, évolution des prix, comparaisons.
- **Ce qu'on y trouve** : Coûts API actuels, pricing tiers, calculateurs de coûts.

---

## Requêtes de Validation (Templates WebSearch)

> **RÈGLE** : L'agent DOIT exécuter au moins 1 de ces requêtes.

```
# Trouver des études de ROI pour un use case spécifique
"AI ROI" + [use case: customer service|code assistance|document processing] + "case study" 2025

# Identifier les coûts cachés
"AI implementation" + "hidden costs" OR "unexpected costs" OR "TCO" 2025

# Chercher des échecs documentés (crucial pour éviter les pièges)
"AI project" + "failed" OR "abandoned" OR "lessons learned" + [secteur] 2025

# Vérifier les benchmarks de productivité actuels
"AI productivity" + "study" OR "research" + "developers" OR "customer service" 2025

# Évaluer le payback period réaliste
"AI" + "payback period" OR "time to value" + [use case] 2025
```

---

## Red Flags (Signaux d'Alerte)

Lors de la recherche, attention si :

- ❌ **ROI promis > 500% sans case study détaillé** → Probablement exagéré
- ❌ **Payback < 6 mois sans contexte** → Conditions très spécifiques, non généralisable
- ❌ **Aucune mention de coûts cachés** → Analyse incomplète, TCO sous-estimé
- ❌ **"Savings" sans baseline mesurée** → Chiffres probablement inventés
- ❌ **Étude sponsorisée sans méthodologie publique** → Biais probable
- ❌ **Que des success stories, aucun échec** → Sélection biaisée

- ✅ **Case study avec métriques before/after vérifiables** → Signal fiable
- ✅ **Mention explicite des échecs/ajustements** → Source honnête
- ✅ **TCO détaillé incluant maintenance et formation** → Analyse complète
- ✅ **Étude longitudinale (> 6 mois)** → Effets durables mesurés
- ✅ **Méthodologie de calcul ROI explicitée** → Reproductible
