# Testing & Quality - Sources de Recherche

**Dernière mise à jour:** 2025-12-05

---

## Scope (Ce que ce fichier couvre)

Ce fichier couvre tout ce qui touche aux **stratégies de test** et à la **qualité logicielle** :
- Test-Driven Development (TDD) et Behavior-Driven Development (BDD)
- Pyramide de tests (unit, integration, e2e)
- Testing strategies par type d'application
- Qualité de code et dette technique
- Code review et pair programming
- Métriques de qualité et coverage

**Utiliser ce fichier quand** :
- Tu définis la stratégie de test pour une feature
- Tu évalues la couverture de tests nécessaire
- Tu dois justifier l'investissement en tests
- Tu choisis un framework de test
- Tu mets en place des quality gates

---

## Sources Primaires (CONSULTATION OBLIGATOIRE)

> **RÈGLE** : L'agent DOIT consulter au moins 2 de ces sources via WebSearch avant de proposer quoi que ce soit sur ce thème.

### Martin Fowler Blog
- **URL** : https://martinfowler.com
- **Nature** : Thought leader (référence mondiale)
- **Spécificité** : Martin Fowler est l'autorité en architecture et qualité logicielle. Créateur du concept de pyramide de tests, refactoring, patterns. Articles fondateurs lus par toute l'industrie.
- **Ce qu'on y trouve** : Test pyramid, TDD, refactoring, patterns de test, architecture, continuous integration.
- **Requêtes utiles** : `site:martinfowler.com "testing"`, `site:martinfowler.com "TDD"`, `site:martinfowler.com "[pattern]"`

### Testing Library Docs
- **URL** : https://testing-library.com
- **Nature** : Documentation outil (standard de facto)
- **Spécificité** : Testing Library est devenu le standard pour tester les interfaces (React, Vue, Angular). Philosophie "test comme l'utilisateur" qui a changé l'industrie.
- **Ce qu'on y trouve** : Best practices testing UI, queries accessibles, patterns de test, guides par framework.
- **Requêtes utiles** : `site:testing-library.com "[framework]"`, `site:testing-library.com "best practices"`

### Google Testing Blog
- **URL** : https://testing.googleblog.com
- **Nature** : Blog corporate (Google)
- **Spécificité** : Insights de l'équipe testing de Google. Pratiques à grande échelle, philosophie de test, outils internes rendus publics.
- **Ce qu'on y trouve** : Testing at scale, flaky tests, test automation, testing culture, métriques.
- **Requêtes utiles** : `site:testing.googleblog.com "[sujet]"`, `"Google testing" "[pratique]"`

### Ministry of Testing
- **URL** : https://www.ministryoftesting.com
- **Nature** : Communauté (QA/Testing)
- **Spécificité** : Plus grande communauté de testeurs. Articles, formations, conférences. Perspective QA professionnelle.
- **Ce qu'on y trouve** : Stratégies de test, automation, exploratory testing, career QA, outils.
- **Requêtes utiles** : `site:ministryoftesting.com "[sujet]"`, `site:ministryoftesting.com "automation"`

### Playwright / Cypress Docs
- **URLs** : https://playwright.dev, https://docs.cypress.io
- **Nature** : Documentation outils (e2e leaders)
- **Spécificité** : Les deux leaders du testing e2e. Best practices, patterns, debugging. Playwright (Microsoft) vs Cypress (communauté).
- **Ce qu'on y trouve** : E2E best practices, patterns, fixtures, parallel testing, debugging.
- **Requêtes utiles** : `site:playwright.dev "best practices"`, `site:docs.cypress.io "[pattern]"`

---

## Sources Secondaires (Recommandées)

### Kent C. Dodds Blog
- **URL** : https://kentcdodds.com/blog
- **Nature** : Thought leader (Testing Library creator)
- **Spécificité** : Créateur de Testing Library. Articles influents sur les pratiques de test modernes. "Write tests. Not too many. Mostly integration."
- **Ce qu'on y trouve** : Philosophie de test, Testing Library patterns, React testing.

### Cucumber Blog
- **URL** : https://cucumber.io/blog/
- **Nature** : Vendor (BDD)
- **Spécificité** : Référence pour Behavior-Driven Development. Gherkin, living documentation, collaboration dev-business.
- **Ce qu'on y trouve** : BDD patterns, Gherkin, collaboration, living documentation.

### SonarSource Blog
- **URL** : https://www.sonarsource.com/blog/
- **Nature** : Vendor (qualité de code)
- **Spécificité** : SonarQube/SonarCloud sont les standards pour la qualité de code. Métriques, debt technique, coverage.
- **Ce qu'on y trouve** : Code quality, technical debt, coverage, security hotspots.

### Test Automation University
- **URL** : https://testautomationu.applitools.com
- **Nature** : Formation gratuite (Applitools)
- **Spécificité** : Cours gratuits sur l'automation par des experts. Large catalogue, certifications.
- **Ce qu'on y trouve** : Cours automation, frameworks, patterns, certifications.

---

## Requêtes de Validation (Templates WebSearch)

> **RÈGLE** : L'agent DOIT exécuter au moins 1 de ces requêtes.

```
# Définir la stratégie de test pour un type d'application
"[type: API|frontend|mobile]" + "testing strategy" + "best practices" + 2025

# Comparer des frameworks de test
"[framework A]" + "vs" + "[framework B]" + "2025" + "comparison"

# Chercher le bon ratio de couverture
"test coverage" + "[type d'application]" + "recommended" OR "best practices"

# Trouver des patterns pour un type de test
"[type: unit|integration|e2e]" + "testing" + "patterns" + "[technologie]"

# Évaluer le ROI des tests
"testing ROI" + "cost of bugs" + "shift left"
```

---

## Red Flags (Signaux d'Alerte)

Lors de la recherche, attention si :

- ❌ **Aucune stratégie de test définie** → Bugs garantis en production
- ❌ **Que des tests e2e, pas d'unit tests** → Pyramide inversée, feedback lent
- ❌ **Coverage comme seule métrique** → Faux sentiment de sécurité
- ❌ **Tests flaky ignorés** → Confiance dans la suite détruite
- ❌ **Pas de tests pour les cas d'erreur** → Happy path seulement
- ❌ **Mocks partout sans tests d'intégration** → Tests qui ne testent rien

- ✅ **Pyramide de tests respectée** → Feedback rapide + confiance
- ✅ **TDD ou tests écrits avec le code** → Design guidé par les tests
- ✅ **Tests d'accessibilité inclus** → Conformité validée
- ✅ **Tests de performance** → Régressions détectées
- ✅ **Living documentation (BDD)** → Specs toujours à jour
