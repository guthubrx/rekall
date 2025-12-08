# Data & Privacy - Sources de Recherche

**Dernière mise à jour:** 2025-12-05

---

## Scope (Ce que ce fichier couvre)

Ce fichier couvre tout ce qui touche aux **données** et à la **vie privée** :
- Modélisation de données et schémas
- GDPR et réglementations privacy (CCPA, LGPD)
- Data ethics et AI ethics
- Anonymisation et pseudonymisation
- Consentement et droits des utilisateurs
- Data governance et qualité des données

**Utiliser ce fichier quand** :
- Tu conçois un modèle de données avec des données personnelles
- Tu dois valider la conformité GDPR avant de spécifier
- Tu collectes ou traites des données utilisateur
- Tu intègres de l'analytics ou du tracking
- Tu dois définir une politique de rétention des données

---

## Sources Primaires (CONSULTATION OBLIGATOIRE)

> **RÈGLE** : L'agent DOIT consulter au moins 2 de ces sources via WebSearch avant de proposer quoi que ce soit sur ce thème.

### ICO (Information Commissioner's Office - UK)
- **URL** : https://ico.org.uk
- **Nature** : Autorité de régulation (UK)
- **Spécificité** : Guides pratiques GDPR parmi les plus clairs. Checklists, exemples concrets, décisions de justice. Référence même hors UK car très bien documenté.
- **Ce qu'on y trouve** : Guides GDPR par sujet, checklists, exemples, lawful basis, rights of individuals, breach reporting.
- **Requêtes utiles** : `site:ico.org.uk "[sujet GDPR]"`, `site:ico.org.uk "checklist"`, `site:ico.org.uk "lawful basis"`

### CNIL (Commission Nationale Informatique et Libertés - France)
- **URL** : https://www.cnil.fr
- **Nature** : Autorité de régulation (France)
- **Spécificité** : Guides en français, décisions récentes, focus sur les cookies/trackers. Référence pour le contexte français/européen.
- **Ce qu'on y trouve** : Guides RGPD, recommandations cookies, décisions sanctions, outils de conformité.
- **Requêtes utiles** : `site:cnil.fr "[sujet]"`, `site:cnil.fr "guide"`, `site:cnil.fr "cookies"`

### IAPP (International Association of Privacy Professionals)
- **URL** : https://iapp.org
- **Nature** : Association professionnelle
- **Spécificité** : LA communauté des professionnels de la privacy. Ressources, certifications (CIPP), news, analyses juridiques.
- **Ce qu'on y trouve** : Analyses réglementaires, comparaisons juridictions, news privacy, resources.
- **Requêtes utiles** : `site:iapp.org "[réglementation]"`, `site:iapp.org "GDPR" "[sujet]"`

### EDPB (European Data Protection Board)
- **URL** : https://edpb.europa.eu
- **Nature** : Institution EU (source officielle)
- **Spécificité** : Guidelines officielles GDPR au niveau européen. Interprétation officielle du règlement. Source de vérité légale.
- **Ce qu'on y trouve** : Guidelines officielles, opinions, recommendations, décisions contraignantes.
- **Requêtes utiles** : `site:edpb.europa.eu "guidelines" "[sujet]"`, `site:edpb.europa.eu "recommendations"`

### Future of Privacy Forum
- **URL** : https://fpf.org
- **Nature** : Think tank (privacy)
- **Spécificité** : Recherche sur la privacy, AI ethics, children's privacy. Publications influentes, perspective forward-looking.
- **Ce qu'on y trouve** : Research papers, AI privacy, children's data, emerging issues.
- **Requêtes utiles** : `site:fpf.org "AI" privacy`, `site:fpf.org "[sujet émergent]"`

---

## Sources Secondaires (Recommandées)

### GDPR.eu
- **URL** : https://gdpr.eu
- **Nature** : Guide (communautaire)
- **Spécificité** : Explications accessibles du GDPR, FAQ, checklists simples. Bon point d'entrée.
- **Ce qu'on y trouve** : FAQ GDPR, checklists, explications simplifiées.

### Data Protection Network
- **URL** : https://www.dpnetwork.org.uk
- **Nature** : Communauté (UK)
- **Spécificité** : Ressources pratiques pour DPOs, templates, guides opérationnels.
- **Ce qu'on y trouve** : Templates, guides pratiques, community Q&A.

### AI Ethics Guidelines (EU)
- **URL** : https://digital-strategy.ec.europa.eu/en/library/ethics-guidelines-trustworthy-ai
- **Nature** : Institution EU
- **Spécificité** : Guidelines officielles pour l'AI éthique en Europe. Base de l'AI Act.
- **Ce qu'on y trouve** : Principes AI éthique, checklist trustworthy AI, requirements.

### Privacy Patterns
- **URL** : https://privacypatterns.org
- **Nature** : Académique/Communautaire
- **Spécificité** : Design patterns pour la privacy. Privacy by design concret.
- **Ce qu'on y trouve** : Patterns de privacy, exemples d'implémentation.

---

## Requêtes de Validation (Templates WebSearch)

> **RÈGLE** : L'agent DOIT exécuter au moins 1 de ces requêtes.

```
# Vérifier les requirements GDPR pour un type de traitement
"GDPR" + "[type de données: health|financial|children]" + "requirements"

# Trouver le lawful basis approprié
"GDPR" + "lawful basis" + "[use case: marketing|analytics|personalization]"

# Vérifier les obligations de consentement
"GDPR" + "consent" + "[contexte: cookies|email|tracking]" + "requirements"

# Chercher les durées de rétention standards
"data retention" + "[type de données]" + "GDPR" + "recommended"

# Évaluer les risques privacy pour l'AI
"AI" + "privacy" + "[use case]" + "GDPR" OR "ethics"
```

---

## Red Flags (Signaux d'Alerte)

Lors de la recherche, attention si :

- ❌ **Pas de base légale identifiée pour le traitement** → Non-conforme GDPR
- ❌ **Consentement présumé ou pré-coché** → Invalide selon GDPR
- ❌ **Données collectées "au cas où"** → Violation minimisation
- ❌ **Pas de politique de rétention** → Données conservées indéfiniment
- ❌ **Transfert hors EU sans garanties** → Risque Schrems II
- ❌ **Pas de DPIA pour traitement à risque** → Obligation légale manquée

- ✅ **Base légale documentée pour chaque traitement** → Conformité de base
- ✅ **Privacy by design dès la conception** → Approche proactive
- ✅ **Registre des traitements à jour** → Accountability
- ✅ **Droits des personnes implémentés** → Accès, rectification, suppression
- ✅ **DPIA pour traitements sensibles** → Risques évalués
- ✅ **DPO désigné si requis** → Gouvernance en place
