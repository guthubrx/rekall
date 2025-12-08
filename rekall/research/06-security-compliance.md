# Security & Compliance - Sources de Recherche

**Dernière mise à jour:** 2025-12-05

---

## Scope (Ce que ce fichier couvre)

Ce fichier couvre tout ce qui touche à la **sécurité applicative** et à la **conformité** :
- Shift Left Security (sécurité dès la conception)
- OWASP Top 10 et secure coding standards
- Threat modeling et analyse de risques
- Conformité réglementaire (GDPR, SOC2, ISO 27001)
- Gestion des dépendances et vulnérabilités (SCA)
- Authentification, autorisation, gestion des secrets

**Utiliser ce fichier quand** :
- Tu conçois une feature qui manipule des données sensibles
- Tu dois valider les contraintes de sécurité avant de spécifier
- Tu évalues les risques d'une nouvelle architecture
- Tu intègres une dépendance tierce (library, API)
- Tu dois respecter des normes de conformité (GDPR, SOC2, etc.)

---

## Sources Primaires (CONSULTATION OBLIGATOIRE)

> **RÈGLE** : L'agent DOIT consulter au moins 2 de ces sources via WebSearch avant de proposer quoi que ce soit sur ce thème.

### OWASP (Open Web Application Security Project)
- **URL** : https://owasp.org
- **Nature** : Organisation à but non lucratif (référence mondiale)
- **Spécificité** : LA référence en sécurité applicative. Standards utilisés par toute l'industrie. OWASP Top 10 mis à jour régulièrement. Checklists, guides, outils gratuits.
- **Ce qu'on y trouve** : OWASP Top 10 (2025 RC sorti), ASVS (Application Security Verification Standard), cheat sheets, testing guides, outils (ZAP, Dependency-Check).
- **Requêtes utiles** : `site:owasp.org "top 10" 2025`, `site:owasp.org "cheat sheet" [sujet]`

### NIST Cybersecurity
- **URL** : https://www.nist.gov/cybersecurity
- **Nature** : Agence gouvernementale US (standards)
- **Spécificité** : Standards de référence enterprise (NIST CSF, SP 800 series). Utilisés pour la conformité, les audits, les certifications. Très détaillés et rigoureux.
- **Ce qu'on y trouve** : NIST Cybersecurity Framework, guides de secure development, standards cryptographie, best practices.
- **Requêtes utiles** : `site:nist.gov "secure software development"`, `site:nist.gov "SDLC" security`

### Snyk Blog & Learn
- **URL** : https://snyk.io/blog/ et https://learn.snyk.io
- **Nature** : Vendor (SCA/SAST) + Education
- **Spécificité** : Leader en Software Composition Analysis. Contenu éducatif très riche sur les vulnérabilités, secure coding, shift left. Base de données de vulnérabilités.
- **Ce qu'on y trouve** : Guides secure coding par langage, vulnérabilités expliquées, shift left practices, state of open source security reports.
- **Requêtes utiles** : `site:snyk.io "secure coding"`, `site:snyk.io "[langage]" security`

### PortSwigger Web Security Academy
- **URL** : https://portswigger.net/web-security
- **Nature** : Vendor (Burp Suite) + Education
- **Spécificité** : Formation gratuite et complète sur la sécurité web. Labs pratiques. Créateurs de Burp Suite (outil de référence pentest).
- **Ce qu'on y trouve** : Cours sur chaque type de vulnérabilité (XSS, SQLi, CSRF...), labs interactifs, explications détaillées.
- **Requêtes utiles** : `site:portswigger.net "[type de vulnérabilité]"`, `site:portswigger.net "authentication"`

### CISA (Cybersecurity & Infrastructure Security Agency)
- **URL** : https://www.cisa.gov
- **Nature** : Agence gouvernementale US (alertes)
- **Spécificité** : Alertes de sécurité officielles, KEV (Known Exploited Vulnerabilities), advisories. Source de vérité pour les vulnérabilités critiques.
- **Ce qu'on y trouve** : Alertes CVE critiques, advisories, best practices, secure by design guides.
- **Requêtes utiles** : `site:cisa.gov "secure by design"`, `site:cisa.gov "[technologie]" advisory`

---

## Sources Secondaires (Recommandées)

### GitGuardian Blog
- **URL** : https://blog.gitguardian.com
- **Nature** : Vendor (secrets detection)
- **Spécificité** : Spécialisé dans la détection de secrets dans le code. State of Secrets Sprawl reports. Bonnes pratiques gestion des secrets.
- **Ce qu'on y trouve** : Gestion des secrets, shift left, statistiques sur les fuites.

### Trail of Bits Blog
- **URL** : https://blog.trailofbits.com
- **Nature** : Entreprise de sécurité (audits)
- **Spécificité** : Audits de sécurité de haut niveau, recherche avancée, outils open source (Slither, Echidna).
- **Ce qu'on y trouve** : Analyses de vulnérabilités, secure development guides, outils.

### GDPR.eu
- **URL** : https://gdpr.eu
- **Nature** : Guide GDPR (référence)
- **Spécificité** : Explications claires du GDPR, checklists, requirements par type de traitement.
- **Ce qu'on y trouve** : Requirements GDPR, checklists conformité, FAQ.

### CWE (Common Weakness Enumeration)
- **URL** : https://cwe.mitre.org
- **Nature** : Base de données (MITRE)
- **Spécificité** : Catalogue exhaustif des types de faiblesses logicielles. Référence pour classifier les vulnérabilités.
- **Ce qu'on y trouve** : Classification des vulnérabilités, CWE Top 25, descriptions détaillées.

---

## Requêtes de Validation (Templates WebSearch)

> **RÈGLE** : L'agent DOIT exécuter au moins 1 de ces requêtes.

```
# Vérifier les vulnérabilités connues d'une technologie
"[technologie/framework]" + "vulnerability" OR "CVE" + 2025

# Chercher les best practices de sécurité pour un use case
"secure" + "[use case: authentication|file upload|API]" + "best practices" + 2025

# Vérifier la conformité GDPR pour un traitement
"GDPR" + "[type de données/traitement]" + "requirements" OR "compliance"

# Trouver les patterns de threat modeling
"threat modeling" + "[type d'application]" + "STRIDE" OR "PASTA"

# Vérifier les recommandations OWASP actuelles
site:owasp.org "[sujet]" + "cheat sheet" OR "guide"
```

---

## Red Flags (Signaux d'Alerte)

Lors de la recherche, attention si :

- ❌ **Aucune mention de sécurité dans la spec** → Red flag majeur, ajouter
- ❌ **Dépendance avec CVE critique non patché** → Blocker, chercher alternative
- ❌ **"Security through obscurity"** → Anti-pattern, ne pas valider
- ❌ **Pas de threat model pour données sensibles** → Risque non évalué
- ❌ **Secrets hardcodés ou en config non chiffrée** → Fuite garantie
- ❌ **Auth custom au lieu de standards (OAuth2, OIDC)** → Risque élevé

- ✅ **OWASP Top 10 adressé explicitement** → Baseline sécurité respectée
- ✅ **Threat model documenté** → Risques identifiés
- ✅ **Dépendances scannées (SCA)** → Supply chain sécurisée
- ✅ **Secrets dans vault/env sécurisé** → Gestion correcte
- ✅ **Conformité mentionnée avec preuves** → Compliance sérieuse
