# Cognitive Load & Productivity - Sources de Recherche

**Dernière mise à jour:** 2025-12-05

---

## Scope (Ce que ce fichier couvre)

Ce fichier couvre tout ce qui touche à l'**interaction humain-AI** et ses effets :
- Théorie de la charge cognitive (Sweller, Miller)
- Impact de l'AI sur la productivité des développeurs et knowledge workers
- Cognitive offloading (délégation cognitive à l'AI)
- Attention economy et fragmentation
- Paradoxe de la délégation (supervision vs autonomie)
- Mesure de productivité (framework SPACE, métriques cognitives)

**Utiliser ce fichier quand** :
- Tu conçois une interface ou UX impliquant l'AI
- Tu évalues l'impact d'un outil AI sur la productivité
- Tu veux éviter la surcharge cognitive des utilisateurs
- Tu mesures l'efficacité d'une feature d'assistance AI
- Tu analyses les effets à long terme de l'AI sur les compétences

---

## Sources Primaires (CONSULTATION OBLIGATOIRE)

> **RÈGLE** : L'agent DOIT consulter au moins 2 de ces sources via WebSearch avant de proposer quoi que ce soit sur ce thème.

### arXiv CS.HC (Human-Computer Interaction)
- **URL** : https://arxiv.org/list/cs.HC/recent
- **Nature** : Académique (papers de recherche)
- **Spécificité** : Papers HCI récents sur l'interaction humain-AI, études cognitives, expérimentations UX. Recherche académique rigoureuse avec méthodologie.
- **Ce qu'on y trouve** : Études empiriques sur cognitive offloading, impact LLMs sur cognition, human-AI collaboration patterns, expériences contrôlées.
- **Requêtes utiles** : `site:arxiv.org "cognitive load" "AI"`, `site:arxiv.org "human-AI collaboration" productivity`

### GitHub Engineering Blog
- **URL** : https://github.blog/category/engineering/
- **Nature** : Vendor/Research (éditeur Copilot)
- **Spécificité** : Données terrain massives sur la productivité développeur avec Copilot. Études internes avec millions de datapoints. Créateur du framework SPACE.
- **Ce qu'on y trouve** : Études Copilot impact, framework SPACE, métriques de productivité développeur, données réelles d'utilisation.
- **Requêtes utiles** : `site:github.blog "Copilot" productivity`, `site:github.blog "developer productivity" "AI"`

### Nielsen Norman Group
- **URL** : https://www.nngroup.com/articles/
- **Nature** : Research UX (autorité du domaine)
- **Spécificité** : LA référence mondiale en UX research. Articles basés sur études utilisateurs. Focus sur l'utilisabilité et la charge cognitive des interfaces AI.
- **Ce qu'on y trouve** : Guidelines UX pour AI interfaces, études utilisateurs, patterns d'interaction AI, cognitive load dans les interfaces.
- **Requêtes utiles** : `site:nngroup.com "AI"`, `site:nngroup.com "cognitive load"`

### ACM Digital Library
- **URL** : https://dl.acm.org
- **Nature** : Académique (peer-reviewed)
- **Spécificité** : Papers CHI (Conference on Human Factors), CSCW. Recherche HCI peer-reviewed la plus rigoureuse. Études longitudinales sur productivité.
- **Ce qu'on y trouve** : Études longitudinales human-AI, CHI papers sur cognitive load, recherche CSCW sur collaboration.
- **Requêtes utiles** : `site:dl.acm.org "AI" "cognitive load"`, `site:dl.acm.org "developer productivity" "LLM"`

### Microsoft Research
- **URL** : https://www.microsoft.com/en-us/research/
- **Nature** : Vendor/Research
- **Spécificité** : Recherche appliquée sur les outils de productivité (VS Code, Copilot, Teams). Études internes avec données massives.
- **Ce qu'on y trouve** : Études workplace productivity, AI collaboration research, données d'usage outils Microsoft.
- **Requêtes utiles** : `site:microsoft.com/research "AI" "productivity"`, `site:microsoft.com/research "cognitive"`

---

## Sources Secondaires (Recommandées)

### JetBrains Blog
- **URL** : https://blog.jetbrains.com
- **Nature** : Vendor (IDEs)
- **Spécificité** : Developer surveys annuels, données d'usage IDE, impact des outils AI sur le développement.
- **Ce qu'on y trouve** : State of Developer Ecosystem, tendances développeurs, adoption outils AI.

### Cal Newport Blog
- **URL** : https://calnewport.com/blog/
- **Nature** : Thought leadership (productivité)
- **Spécificité** : Deep work, attention management, critique des technologies distrayantes. Perspective académique sur la productivité.
- **Ce qu'on y trouve** : Principes deep work, gestion de l'attention, critique éclairée des outils AI.

### Harvard Business Review - Productivity
- **URL** : https://hbr.org/topic/subject/productivity
- **Nature** : Publication business
- **Spécificité** : Articles managériaux sur la productivité, burnout, focus. Perspective organisationnelle.
- **Ce qu'on y trouve** : Études workplace, burnout, productivité des équipes.

### NBER Working Papers
- **URL** : https://www.nber.org/papers
- **Nature** : Académique économie
- **Spécificité** : Papers économiques sur l'impact AI sur le travail (Brynjolfsson et al.). Études macro-économiques rigoureuses.
- **Ce qu'on y trouve** : Impact économique AI sur productivité, études Brynjolfsson, analyses macro.

---

## Requêtes de Validation (Templates WebSearch)

> **RÈGLE** : L'agent DOIT exécuter au moins 1 de ces requêtes.

```
# Vérifier l'impact réel sur la productivité développeur
"AI" + "developer productivity" + "study" OR "research" + 2025

# Chercher les effets négatifs (crucial pour une vue équilibrée)
"AI" + "cognitive load" + "negative" OR "fatigue" OR "burnout" 2025

# Évaluer l'impact sur les compétences à long terme
"AI assistance" + "skill degradation" OR "deskilling" OR "dependency" 2025

# Trouver des études UX sur les interfaces AI
"AI interface" + "user experience" + "study" 2025

# Vérifier les métriques de productivité utilisées
"developer productivity" + "metrics" OR "SPACE framework" + 2025
```

---

## Red Flags (Signaux d'Alerte)

Lors de la recherche, attention si :

- ❌ **Étude avec N < 50 participants** → Pas généralisable statistiquement
- ❌ **Pas de groupe contrôle** → Biais de sélection probable
- ❌ **Sponsorisée par vendor AI sans peer review** → Conflit d'intérêt
- ❌ **"Productivity +X%" sans définition de productivité** → Métrique vague, manipulable
- ❌ **Pas de mention de fatigue/burnout** → Vision incomplète, biais positif
- ❌ **Étude < 1 semaine** → Effet nouveauté, pas représentatif long terme

- ✅ **Étude longitudinale (> 3 mois)** → Effets durables mesurés
- ✅ **Réplication indépendante** → Résultats fiables
- ✅ **Mention des effets négatifs aussi** → Recherche honnête
- ✅ **Méthodologie détaillée et reproductible** → Science solide
- ✅ **Plusieurs métriques (pas juste vitesse)** → Vue holistique
