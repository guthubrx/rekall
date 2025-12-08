# DevOps & Infrastructure - Sources de Recherche

**Dernière mise à jour:** 2025-12-05

---

## Scope (Ce que ce fichier couvre)

Ce fichier couvre tout ce qui touche au **DevOps**, à l'**infrastructure** et au **déploiement** :
- CI/CD pipelines et automation
- Infrastructure as Code (IaC) - Terraform, Pulumi, CDK
- Containerisation (Docker, Kubernetes)
- Cloud platforms (AWS, GCP, Azure)
- Observabilité (monitoring, logging, tracing)
- Site Reliability Engineering (SRE)

**Utiliser ce fichier quand** :
- Tu définis l'infrastructure pour un projet
- Tu conçois un pipeline CI/CD
- Tu évalues des options de déploiement
- Tu mets en place l'observabilité
- Tu estimes les coûts d'infrastructure

---

## Sources Primaires (CONSULTATION OBLIGATOIRE)

> **RÈGLE** : L'agent DOIT consulter au moins 2 de ces sources via WebSearch avant de proposer quoi que ce soit sur ce thème.

### Google SRE Books (Free)
- **URL** : https://sre.google/books/
- **Nature** : Documentation Google (référence mondiale)
- **Spécificité** : Les livres SRE de Google ont défini le domaine. Gratuits en ligne. Pratiques de fiabilité, on-call, incident management, SLOs/SLIs/SLAs. Référence absolue.
- **Ce qu'on y trouve** : SRE principles, SLOs, error budgets, toil reduction, incident management, monitoring.
- **Requêtes utiles** : `site:sre.google "[concept]"`, `"Google SRE" "[pratique]"`

### DORA (DevOps Research and Assessment)
- **URL** : https://dora.dev
- **Nature** : Research (Google Cloud)
- **Spécificité** : Recherche scientifique sur la performance DevOps. Métriques DORA (deployment frequency, lead time, MTTR, change failure rate) devenues standards de l'industrie.
- **Ce qu'on y trouve** : State of DevOps reports, DORA metrics, capabilities, benchmarks.
- **Requêtes utiles** : `site:dora.dev "[métrique]"`, `"DORA metrics" "[pratique]"`

### AWS Architecture Center
- **URL** : https://aws.amazon.com/architecture/
- **Nature** : Documentation vendor (AWS)
- **Spécificité** : Best practices et patterns d'architecture cloud AWS. Well-Architected Framework. Référence pour le cloud même hors AWS (concepts transposables).
- **Ce qu'on y trouve** : Well-Architected Framework, patterns d'architecture, reference architectures, best practices.
- **Requêtes utiles** : `site:aws.amazon.com/architecture "[pattern]"`, `"AWS Well-Architected" "[pillar]"`

### Kubernetes Documentation
- **URL** : https://kubernetes.io/docs/
- **Nature** : Documentation officielle (CNCF)
- **Spécificité** : Source de vérité pour Kubernetes. Concepts, patterns, best practices. Maintenu par la communauté cloud native.
- **Ce qu'on y trouve** : Concepts K8s, patterns de déploiement, best practices, troubleshooting.
- **Requêtes utiles** : `site:kubernetes.io "[concept]"`, `site:kubernetes.io "best practices"`

### HashiCorp Learn
- **URL** : https://developer.hashicorp.com
- **Nature** : Documentation vendor (Terraform, Vault)
- **Spécificité** : Terraform est le standard IaC. Vault pour les secrets. Tutorials bien structurés, patterns enterprise.
- **Ce qu'on y trouve** : Terraform patterns, modules, state management, Vault secrets, best practices.
- **Requêtes utiles** : `site:developer.hashicorp.com "terraform" "[pattern]"`, `site:developer.hashicorp.com "best practices"`

---

## Sources Secondaires (Recommandées)

### The New Stack
- **URL** : https://thenewstack.io
- **Nature** : Publication (cloud native)
- **Spécificité** : News et analyses sur l'écosystème cloud native. CNCF, Kubernetes, observabilité. Perspective industrie.
- **Ce qu'on y trouve** : News cloud native, analyses, interviews, tendances.

### CNCF Landscape
- **URL** : https://landscape.cncf.io
- **Nature** : Cartographie (Cloud Native Computing Foundation)
- **Spécificité** : Vue exhaustive de l'écosystème cloud native. Tous les projets catégorisés. Utile pour découvrir des alternatives.
- **Ce qu'on y trouve** : Projets cloud native par catégorie, maturité, adoption.

### DevOps Roadmap
- **URL** : https://roadmap.sh/devops
- **Nature** : Communauté (learning path)
- **Spécificité** : Roadmap visuel des compétences DevOps. Ressources associées pour chaque skill.
- **Ce qu'on y trouve** : Skills DevOps, learning path, ressources.

### Grafana Blog
- **URL** : https://grafana.com/blog/
- **Nature** : Vendor (observabilité)
- **Spécificité** : Grafana/Loki/Tempo/Mimir sont standards d'observabilité open source. Best practices monitoring.
- **Ce qu'on y trouve** : Observabilité patterns, dashboards, alerting, LGTM stack.

---

## Requêtes de Validation (Templates WebSearch)

> **RÈGLE** : L'agent DOIT exécuter au moins 1 de ces requêtes.

```
# Définir l'architecture d'infrastructure pour un use case
"[type: microservices|monolith|serverless]" + "infrastructure" + "best practices" + 2025

# Comparer des options cloud/tools
"[option A]" + "vs" + "[option B]" + "2025" + "comparison"

# Chercher les patterns de déploiement
"[pattern: blue-green|canary|rolling]" + "deployment" + "best practices"

# Estimer les coûts
"[cloud: AWS|GCP|Azure]" + "[service]" + "cost" + "optimization"

# Trouver les métriques DORA pour un contexte
"DORA metrics" + "[type d'organisation]" + "benchmark"
```

---

## Red Flags (Signaux d'Alerte)

Lors de la recherche, attention si :

- ❌ **Pas d'Infrastructure as Code** → Drift garanti, pas reproductible
- ❌ **Déploiement manuel en production** → Risque d'erreur humaine
- ❌ **Pas de monitoring/alerting** → Incidents découverts par les users
- ❌ **Secrets dans le code ou config non chiffrée** → Fuite garantie
- ❌ **Pas de backup/disaster recovery** → Perte de données possible
- ❌ **Single point of failure** → Disponibilité compromise

- ✅ **IaC versionné (Terraform, Pulumi, CDK)** → Reproductible
- ✅ **CI/CD automatisé** → Déploiements fiables
- ✅ **Observabilité (logs, metrics, traces)** → Debugging possible
- ✅ **SLOs définis** → Fiabilité mesurée
- ✅ **GitOps** → Source of truth dans Git
- ✅ **Secrets dans vault** → Sécurité correcte
