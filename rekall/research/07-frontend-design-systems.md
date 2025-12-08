# Frontend & Design Systems - Sources de Recherche

**Dernière mise à jour:** 2025-12-05

---

## Scope (Ce que ce fichier couvre)

Ce fichier couvre tout ce qui touche au **développement frontend** et aux **systèmes de design** :
- Design systems et component libraries
- Accessibilité (WCAG, European Accessibility Act 2025)
- UI/UX patterns et bonnes pratiques
- Frameworks frontend (React, Vue, Angular, Svelte)
- Performance frontend (Core Web Vitals)
- Responsive design et mobile-first

**Utiliser ce fichier quand** :
- Tu conçois une interface utilisateur
- Tu dois choisir un design system ou component library
- Tu valides les requirements d'accessibilité (obligatoire EAA juin 2025)
- Tu évalues l'UX d'une feature
- Tu choisis un framework frontend

---

## Sources Primaires (CONSULTATION OBLIGATOIRE)

> **RÈGLE** : L'agent DOIT consulter au moins 2 de ces sources via WebSearch avant de proposer quoi que ce soit sur ce thème.

### Nielsen Norman Group
- **URL** : https://www.nngroup.com/articles/
- **Nature** : Research UX (autorité mondiale)
- **Spécificité** : LA référence en UX research depuis 1998. Jakob Nielsen est le père de l'utilisabilité. Articles basés sur études utilisateurs rigoureuses. Standards de l'industrie.
- **Ce qu'on y trouve** : Guidelines UX, études utilisateurs, patterns d'interaction, évaluation d'interfaces, accessibilité.
- **Requêtes utiles** : `site:nngroup.com "[pattern UX]"`, `site:nngroup.com "accessibility"`, `site:nngroup.com "mobile"`

### W3C WAI (Web Accessibility Initiative)
- **URL** : https://www.w3.org/WAI/
- **Nature** : Standards officiels (W3C)
- **Spécificité** : Source officielle des standards WCAG (Web Content Accessibility Guidelines). Obligatoire pour conformité légale (EAA 2025). Techniques et critères de succès.
- **Ce qu'on y trouve** : WCAG 2.1/2.2, techniques d'implémentation, critères de succès, tutoriels accessibilité.
- **Requêtes utiles** : `site:w3.org/WAI "[composant]" accessibility`, `site:w3.org "WCAG" "[critère]"`

### web.dev (Google)
- **URL** : https://web.dev
- **Nature** : Documentation Google (Chrome/Web)
- **Spécificité** : Best practices officielles Google pour le web. Core Web Vitals, performance, PWA, accessibilité. Impact direct sur le SEO.
- **Ce qu'on y trouve** : Core Web Vitals, guides performance, patterns modernes, lighthouse audits, métriques.
- **Requêtes utiles** : `site:web.dev "performance"`, `site:web.dev "accessibility"`, `site:web.dev "[framework]"`

### Smashing Magazine
- **URL** : https://www.smashingmagazine.com
- **Nature** : Publication technique (communauté)
- **Spécificité** : Articles techniques approfondis par des praticiens. CSS, JavaScript, design systems, accessibilité. Très respecté dans la communauté frontend.
- **Ce qu'on y trouve** : Tutoriels avancés, case studies, design patterns, nouvelles techniques CSS/JS.
- **Requêtes utiles** : `site:smashingmagazine.com "[sujet technique]"`, `site:smashingmagazine.com "design system"`

### Storybook Blog
- **URL** : https://storybook.js.org/blog/
- **Nature** : Outil/Communauté (standard de facto)
- **Spécificité** : Storybook est l'outil standard pour documenter les design systems. Blog avec best practices, patterns de component libraries, cas d'usage enterprise.
- **Ce qu'on y trouve** : Design system patterns, component documentation, testing visuel, adoption enterprise.
- **Requêtes utiles** : `site:storybook.js.org "design system"`, `site:storybook.js.org "[framework]"`

---

## Sources Secondaires (Recommandées)

### A List Apart
- **URL** : https://alistapart.com
- **Nature** : Publication (pionnière du web)
- **Spécificité** : Publication historique du web design (depuis 1998). Articles fondateurs sur le responsive design, accessibility, standards web.
- **Ce qu'on y trouve** : Articles de fond, réflexions sur les standards, histoire du web design.

### CSS-Tricks (DigitalOcean)
- **URL** : https://css-tricks.com
- **Nature** : Tutoriels (communauté)
- **Spécificité** : Ressource pratique pour CSS et frontend. Almanac CSS complet, guides Flexbox/Grid, snippets.
- **Ce qu'on y trouve** : Tutoriels CSS, snippets, guides techniques, astuces.

### Component Libraries Docs
- **URLs** : mui.com, chakra-ui.com, radix-ui.com, ui.shadcn.com
- **Nature** : Documentation vendors
- **Spécificité** : Documentation des principales component libraries. Patterns, API, accessibilité intégrée.
- **Ce qu'on y trouve** : Composants, guidelines, patterns d'usage, accessibilité.

### Deque University
- **URL** : https://dequeuniversity.com
- **Nature** : Formation accessibilité
- **Spécificité** : Formation professionnelle en accessibilité. Créateurs de axe (outil de test). Certifications.
- **Ce qu'on y trouve** : Cours accessibilité, patterns ARIA, testing, certifications.

---

## Requêtes de Validation (Templates WebSearch)

> **RÈGLE** : L'agent DOIT exécuter au moins 1 de ces requêtes.

```
# Vérifier les requirements d'accessibilité pour un composant
"[composant: modal|form|navigation]" + "accessibility" + "WCAG" + "best practices"

# Comparer des component libraries
"[library A]" + "vs" + "[library B]" + "2025" + "comparison"

# Vérifier les patterns UX pour un use case
site:nngroup.com "[use case: checkout|onboarding|search]"

# Chercher les Core Web Vitals pour une technique
"[technique: lazy loading|code splitting]" + "Core Web Vitals" + "performance"

# Vérifier la conformité EAA 2025
"European Accessibility Act" + "[secteur/type d'application]" + "requirements"
```

---

## Red Flags (Signaux d'Alerte)

Lors de la recherche, attention si :

- ❌ **Aucune mention d'accessibilité** → Non-conforme EAA juin 2025, risque légal
- ❌ **Component library sans ARIA support** → Accessibilité à implémenter from scratch
- ❌ **Pas de responsive design** → Expérience mobile dégradée
- ❌ **Core Web Vitals ignorés** → Impact SEO et UX
- ❌ **Design system "from scratch" sans justification** → Réinventer la roue
- ❌ **Animations sans prefers-reduced-motion** → Problème accessibilité

- ✅ **WCAG 2.1 AA mentionné** → Baseline accessibilité respectée
- ✅ **Component library avec accessibilité intégrée** → Moins de travail
- ✅ **Design tokens documentés** → Système scalable
- ✅ **Storybook ou équivalent** → Documentation vivante
- ✅ **Tests visuels automatisés** → Régression UI détectée
