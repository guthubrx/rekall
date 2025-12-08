# Research Hub - Sources Fiables pour la Recherche

**Version:** 3.0.0
**Dernière mise à jour:** 2025-12-05

---

## Philosophie

Ce répertoire ne contient **PAS** de données pré-compilées (métriques, benchmarks, prédictions).

**Pourquoi ?** Les données chiffrées deviennent obsolètes en quelques mois. Au lieu de maintenir des tableaux qui vieillissent mal, ce hub pointe vers des **sources fiables** que l'agent DOIT consulter en temps réel.

**Principe** : Forcer la recherche live → données toujours fraîches → recommandations mieux fondées.

---

## Règle Obligatoire (Article IX - Constitution)

Avant de proposer toute feature touchant à l'AI, l'architecture, la productivité ou le KM, l'agent **DOIT** :

1. **Identifier** le(s) thème(s) pertinent(s) ci-dessous
2. **Lire** le fichier correspondant pour extraire les sources
3. **Exécuter WebSearch** sur :
   - Minimum **2 sources primaires**
   - Minimum **1 requête de validation**
4. **Documenter** les findings dans `research.md`

**INTERDIT** : Proposer sans avoir exécuté ce workflow.

---

## Thèmes Disponibles

| # | Thème | Fichier | Quand l'utiliser |
|---|-------|---------|------------------|
| 01 | AI Agents & Agentic AI | `01-ai-agents-agentic-ai.md` | Agents, automatisation, orchestration, multi-agents |
| 02 | ROI & Business Value | `02-roi-business-value.md` | Justification économique, business case, coûts |
| 03 | Cognitive Load & Productivity | `03-cognitive-load-productivity.md` | UX, productivité, attention, charge cognitive |
| 04 | Architectures & Patterns | `04-architectures-patterns.md` | Patterns techniques, protocoles, RAG, infrastructure |
| 05 | Knowledge Management | `05-knowledge-management.md` | Documentation, KM, recherche d'info, RAG |
| 06 | Security & Compliance | `06-security-compliance.md` | OWASP, Shift Left, GDPR, threat modeling |
| 07 | Frontend & Design Systems | `07-frontend-design-systems.md` | UI/UX, accessibilité, component libraries, EAA 2025 |
| 08 | Testing & Quality | `08-testing-quality.md` | TDD, pyramide de tests, quality gates, coverage |
| 09 | DevOps & Infrastructure | `09-devops-infrastructure.md` | CI/CD, IaC, Kubernetes, observabilité, SRE |
| 10 | Data & Privacy | `10-data-privacy.md` | GDPR, consentement, data ethics, rétention |

---

## Structure de Chaque Fichier

Chaque fichier thématique contient :

```
## Scope
   └─ Ce que le thème couvre, quand l'utiliser

## Sources Primaires (OBLIGATOIRE)
   └─ 4-6 sources haute autorité avec :
      • URL
      • Nature (analyste, académique, vendor, communauté)
      • Spécificité (ce qui rend cette source unique)
      • Ce qu'on y trouve
      • Requêtes utiles

## Sources Secondaires (Recommandées)
   └─ Sources complémentaires pour approfondir

## Requêtes de Validation
   └─ Templates WebSearch prêts à l'emploi

## Red Flags
   └─ Signaux d'alerte à surveiller dans les résultats
```

---

## Workflow Intégré

```
┌─────────────────────────────────────────────────────────────┐
│  /speckit.plan déclenche Phase 0.1 (Article IX)            │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  1. IDENTIFIER thème(s) pertinent(s)                       │
│     → Lire fichier ~/.speckit/research/XX-xxx.md           │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. EXTRAIRE sources primaires + requêtes                  │
│     → URLs, nature, spécificité, red flags                 │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. EXÉCUTER WebSearch OBLIGATOIRE                         │
│     → 2 sources primaires minimum                          │
│     → 1 requête de validation minimum                      │
│     → Recherche échecs/lessons learned                     │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  4. DOCUMENTER dans research.md                            │
│     → Sources consultées (URL + date)                      │
│     → Findings clés                                        │
│     → Red flags identifiés                                 │
│     → Recommandation argumentée                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Maintenance

### Mise à Jour des Sources

- Vérifier **trimestriellement** que les URLs sont toujours valides
- Ajouter de nouvelles sources pertinentes identifiées pendant les recherches
- Mettre à jour la date "Dernière mise à jour" de chaque fichier modifié

### Ajout d'un Nouveau Thème

1. Créer fichier `XX-nom-theme.md` suivant la structure standard
2. Remplir : Scope, Sources Primaires (4-6), Sources Secondaires, Requêtes, Red Flags
3. Mettre à jour ce README (table des thèmes)
4. Mettre à jour `/speckit.plan` (table Phase 0.1)
