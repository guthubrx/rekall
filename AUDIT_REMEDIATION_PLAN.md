# 📋 Plan de Remédiation Audit Sécurité - Rekall

**Date:** 2025-12-11
**Score initial:** B- (Sécurité C, Qualité B, Architecture B, Tests B-, Performance B)
**Objectif:** Atteindre un niveau SOTA (State of the Art) sur chaque dimension

---

## 📚 Table des Matières

### Sécurité et Qualité
1. [CI/CD et Scans de Sécurité](#1-cicd-et-scans-de-sécurité)
2. [Chiffrement des Données SQLite](#2-chiffrement-des-données-sqlite)
3. [Authentification et Autorisation](#3-authentification-et-autorisation)
4. [Gestion des PII et Conformité RGPD](#4-gestion-des-pii-et-conformité-rgpd)
5. [Validation des Entrées Utilisateur](#5-validation-des-entrées-utilisateur)
6. [Verrouillage des Dépendances](#6-verrouillage-des-dépendances)
7. [Qualité de Code et Linting](#7-qualité-de-code-et-linting)
8. [Architecture et Séparation des Couches](#8-architecture-et-séparation-des-couches)

### Cohérence et Maintenabilité
9. [Duplication de Code et Principe DRY](#9-duplication-de-code-et-principe-dry)
10. [CLI Monolithique et Modularisation](#10-cli-monolithique-et-modularisation)
11. [Code Mort et Intégrations Non Raccordées](#11-code-mort-et-intégrations-non-raccordées)

### Robustesse et Observabilité
12. [Observabilité et Gestion d'Erreurs](#12-observabilité-et-gestion-derreurs)
13. [Persistance de Configuration](#13-persistance-de-configuration)
14. [Durcissement des Archives et Imports](#14-durcissement-des-archives-et-imports)

### Hygiène du Code Généré par IA (Nouveau)
15. [Détection et Correction des Contributions IA](#15-détection-et-correction-des-contributions-ia)

### Synthèse
16. [Roadmap de Mise en Œuvre](#16-roadmap-de-mise-en-œuvre)

---

## 🎯 Analyse de Pertinence par Niveau

### Contexte Rekall

Avant d'évaluer chaque niveau, rappelons le contexte spécifique de Rekall :

| Caractéristique | Impact sur les choix |
|-----------------|---------------------|
| **CLI Python locale** | Pas d'exposition réseau → moins de surface d'attaque |
| **Usage personnel** | Pas de multi-utilisateurs → authentification moins critique |
| **Base de connaissances** | Données potentiellement sensibles mais pas critiques (pas de secrets bancaires) |
| **Projet open-source** | Qualité de code importante pour contributions |
| **< 500 LOC** | Architecture simple suffisante |

### Légende des Évaluations

| Badge | Signification |
|-------|---------------|
| ✅ **ESSENTIEL** | ROI excellent, effort minimal, impact maximal. À faire absolument. |
| 👍 **RECOMMANDÉ** | Bon rapport effort/bénéfice. Améliore significativement le projet. |
| 🟡 **OPTIONNEL** | Utile dans certains contextes. À considérer selon les besoins réels. |
| ⚠️ **OVERKILL** | Over-engineering pour ce contexte. Complexité injustifiée. |

---

### 📊 Tableau Récapitulatif

#### Sécurité et Qualité (Sections 1-8)

| Section | Niveau 1 | Niveau 2 | Niveau 3 | Recommandation |
|---------|----------|----------|----------|----------------|
| **1. CI/CD & Sécurité** | ✅ ESSENTIEL | 👍 RECOMMANDÉ | ⚠️ OVERKILL | Niveaux 1-2 |
| **2. Chiffrement SQLite** | ✅ ESSENTIEL | 🟡 OPTIONNEL | ⚠️ OVERKILL | Niveau 1 obligatoire |
| **3. Authentification** | 🟡 OPTIONNEL | ⚠️ OVERKILL | ⚠️ OVERKILL | Si chiffrement activé |
| **4. RGPD/PII** | 👍 RECOMMANDÉ | 🟡 OPTIONNEL | ⚠️ OVERKILL | Niveau 1 suffit |
| **5. Validation entrées** | ✅ ESSENTIEL | 👍 RECOMMANDÉ | ⚠️ OVERKILL | Niveaux 1-2 |
| **6. Verrouillage deps** | ✅ ESSENTIEL | 👍 RECOMMANDÉ | 🟡 OPTIONNEL | Niveaux 1-2 |
| **7. Linting** | ✅ ESSENTIEL | 👍 RECOMMANDÉ | 🟡 OPTIONNEL | Niveaux 1-2 |
| **8. Architecture** | 👍 RECOMMANDÉ | ⚠️ OVERKILL | ⚠️ OVERKILL | Niveau 1 max |

#### Cohérence et Maintenabilité (Sections 9-11)

| Section | Niveau 1 | Niveau 2 | Niveau 3 | Recommandation |
|---------|----------|----------|----------|----------------|
| **9. Duplication (DRY)** | ✅ ESSENTIEL | 👍 RECOMMANDÉ | ⚠️ OVERKILL | Niveaux 1-2 |
| **10. CLI Modulaire** | 👍 RECOMMANDÉ | 🟡 OPTIONNEL | ⚠️ OVERKILL | Niveau 1 suffit |
| **11. Code Mort** | ✅ ESSENTIEL | 👍 RECOMMANDÉ | 🟡 OPTIONNEL | Niveaux 1-2 |

#### Robustesse et Observabilité (Sections 12-14)

| Section | Niveau 1 | Niveau 2 | Niveau 3 | Recommandation |
|---------|----------|----------|----------|----------------|
| **12. Gestion Erreurs** | ✅ ESSENTIEL | 👍 RECOMMANDÉ | 🟡 OPTIONNEL | Niveaux 1-2 |
| **13. Config Atomique** | ✅ ESSENTIEL | 👍 RECOMMANDÉ | ⚠️ OVERKILL | Niveau 1-2 |
| **14. Sécurité Archives** | ✅ ESSENTIEL | 👍 RECOMMANDÉ | 🟡 OPTIONNEL | Niveaux 1-2 |

#### Hygiène du Code IA (Section 15 - Nouveau)

| Section | Niveau 1 | Niveau 2 | Niveau 3 | Recommandation |
|---------|----------|----------|----------|----------------|
| **15. Contributions IA** | ✅ ESSENTIEL | 👍 RECOMMANDÉ | 🟡 OPTIONNEL | Niveaux 1-2 |

---

### 🔍 Analyse Détaillée par Section

#### 1. CI/CD et Scans de Sécurité

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (pip-audit + Bandit) | ✅ ESSENTIEL | Effort minimal (~30 min), détecte les CVE dans les dépendances. Indispensable pour tout projet Python moderne. |
| **Niveau 2** (Safety + TruffleHog) | 👍 RECOMMANDÉ | Safety ajoute une couverture CVE complémentaire. TruffleHog utile si tu commites des configs avec secrets potentiels. |
| **Niveau 3** (Semgrep + SARIF) | ⚠️ OVERKILL | Semgrep et l'intégration GitHub Security Tab sont des outils enterprise. Pour une CLI personnelle de <500 LOC, c'est de l'artillerie lourde. Bandit suffit largement. |

**💡 Verdict:** Implémenter Niveaux 1-2. Le Niveau 3 n'apporte rien de tangible.

---

#### 2. Chiffrement des Données SQLite

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Permissions 600) | ✅ ESSENTIEL | 3 lignes de code, zéro dépendance, protection immédiate contre les lectures accidentelles. Aucune raison de ne pas le faire. |
| **Niveau 2** (SQLCipher optionnel) | 🟡 OPTIONNEL | Ajoute une dépendance native (compilation possible), complexifie le setup. Utile **uniquement si** tu stockes des données vraiment sensibles (mots de passe, secrets API). Pour des notes de dev classiques ? Pas nécessaire. |
| **Niveau 3** (Migration auto) | ⚠️ OVERKILL | Mécanisme de migration automatique chiffré→non-chiffré avec backup sécurisé ? C'est de l'over-engineering. Si tu veux chiffrer, tu chiffres dès le départ. |

**💡 Verdict:** Niveau 1 obligatoire. Niveau 2 seulement si tu stockes des secrets réels.

---

#### 3. Authentification et Autorisation

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Keyring passphrase) | 🟡 OPTIONNEL | Utile **uniquement si** le chiffrement SQLCipher est activé (pour stocker la passphrase). Sinon, aucune valeur ajoutée - c'est déjà TON shell, TES fichiers, TON user Unix. |
| **Niveau 2** (Sessions avec timeout) | ⚠️ OVERKILL | Des sessions avec timeout d'inactivité pour une CLI ? Tu tapes une commande, elle s'exécute, fin. Il n'y a pas de "session" persistante à protéger. Pattern copié des apps web, non applicable ici. |
| **Niveau 3** (Audit logs) | ⚠️ OVERKILL | Logger chaque accès à tes propres notes ? C'est du paranoia-driven development. Les logs système (`.bash_history`) suffisent pour l'audit personnel. |

**💡 Verdict:** Implémenter Niveau 1 **seulement si** SQLCipher activé. Sinon, skip complet.

---

#### 4. Gestion des PII et Conformité RGPD

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Classification + doc) | 👍 RECOMMANDÉ | Ajouter un champ `classification` et documenter la politique de données prend 30 min et montre une maturité du projet. Utile pour les contributeurs. |
| **Niveau 2** (Détection PII regex) | 🟡 OPTIONNEL | Les regex basiques (email, téléphone) sont faciles à ajouter. Mais utiliser un modèle ML (DeBERTa-v3) pour détecter les PII dans une CLI locale ? Overkill absolu. Reste sur les regex simples si tu le fais. |
| **Niveau 3** (Purge automatique) | ⚠️ OVERKILL | `secure_delete` avec écrasement mémoire et `VACUUM` ? Tu n'es pas une banque. Un simple `DELETE` SQLite suffit. La "récupération forensique" de notes personnelles n'est pas un threat model réaliste. |

**💡 Verdict:** Niveau 1 pour la doc et la structure. Niveau 2 regex seulement si besoin réel.

---

#### 5. Validation des Entrées Utilisateur

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Pydantic validators) | ✅ ESSENTIEL | Pydantic est déjà quasi-standard en Python moderne. Validation propre, messages d'erreur clairs, typage fort. Excellent ROI. |
| **Niveau 2** (Requêtes paramétrées strictes) | 👍 RECOMMANDÉ | Tu utilises probablement déjà des `?` placeholders. Formaliser ça avec une couche de validation FTS est une bonne pratique défensive. |
| **Niveau 3** (Triggers SQL audit) | ⚠️ OVERKILL | Des triggers SQLite pour logger chaque INSERT/UPDATE dans une table d'audit ? Pour une CLI personnelle ? C'est du pattern enterprise copié sans réflexion. Complexité inutile, performance dégradée, maintenance accrue. |

**💡 Verdict:** Niveaux 1-2 recommandés. Niveau 3 à éviter.

---

#### 6. Verrouillage des Dépendances

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (uv lock) | ✅ ESSENTIEL | `uv lock` prend 5 secondes, garantit la reproductibilité. Aucune raison de ne pas le faire. C'est le standard 2025. |
| **Niveau 2** (CI avec --frozen) | 👍 RECOMMANDÉ | Vérifier en CI que le lockfile est synchronisé évite les "ça marche sur ma machine". Bonne pratique à faible coût. |
| **Niveau 3** (Hash verification) | 🟡 OPTIONNEL | `--require-hashes` et `no-binary` pour compiler les packages ? Pour un projet open-source personnel, c'est excessif. Réserve ça aux environnements haute sécurité (banque, santé). |

**💡 Verdict:** Niveaux 1-2 obligatoires. Niveau 3 optionnel.

---

#### 7. Qualité de Code et Linting

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Ruff E, F, W) | ✅ ESSENTIEL | Configuration de base en 2 min. Détecte les erreurs évidentes. Aucune raison de s'en passer. |
| **Niveau 2** (Règles étendues + S) | 👍 RECOMMANDÉ | Ajouter isort, bugbear, et les règles Bandit dans Ruff (S) améliore la qualité sans friction. |
| **Niveau 3** (Pre-commit hooks) | 🟡 OPTIONNEL | Les pre-commit hooks sont nice-to-have mais pas critiques pour un développeur solo. La CI fait le même travail. Utile si plusieurs contributeurs. |

**💡 Verdict:** Niveaux 1-2 recommandés. Niveau 3 si contributions externes.

---

#### 8. Architecture et Séparation des Couches

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Entités extraites) | 👍 RECOMMANDÉ | Séparer les dataclasses métier dans `entities.py` améliore la lisibilité et la testabilité. Effort minimal, gain de clarté. |
| **Niveau 2** (Repository Pattern) | ⚠️ OVERKILL | Pour un projet de <500 LOC avec un seul backend (SQLite), créer des interfaces abstraites `NoteRepository` + implémentation concrète est de l'over-abstraction. Tu n'auras jamais de backend PostgreSQL ou MongoDB. YAGNI (You Ain't Gonna Need It). |
| **Niveau 3** (Use Cases + DI) | ⚠️ OVERKILL | Un conteneur d'injection de dépendances et des Use Cases formels pour une CLI de notes ? C'est de l'architecture enterprise plaquée sur un projet simple. Tu vas passer plus de temps sur la plomberie que sur les features. |

**💡 Verdict:** Niveau 1 uniquement. Les niveaux 2-3 sont du cargo cult architecture.

---

#### 9. Duplication de Code et Principe DRY

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Fonction partagée basique) | ✅ ESSENTIEL | Extraire `entry_to_dict()` et `dict_to_entry()` prend 30 min et élimine 40+ lignes dupliquées. ROI immédiat. |
| **Niveau 2** (Module serializers dédié) | 👍 RECOMMANDÉ | Créer `rekall/serializers.py` centralise toute la logique de conversion. Facilite les évolutions de schéma. |
| **Niveau 3** (Pydantic/dataclass avec serdes) | ⚠️ OVERKILL | Remplacer par des modèles Pydantic avec `model_dump()`/`model_validate()` est élégant mais nécessite un refactoring majeur pour peu de gain sur un schéma stable. |

**💡 Verdict:** Niveaux 1-2 recommandés. Niveau 3 si refonte majeure prévue.

---

#### 10. CLI Monolithique et Modularisation

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Extraction helpers) | 👍 RECOMMANDÉ | Déplacer l'init DB/config dans `rekall/config.py` réduit le bruit sans restructuration majeure. ~1h de travail. |
| **Niveau 2** (Sous-commandes modulaires) | 🟡 OPTIONNEL | Créer `commands/export.py`, `commands/integrations.py` améliore la navigation mais nécessite de toucher tous les imports. Utile si le fichier dépasse 3000 LOC. |
| **Niveau 3** (Architecture plugins Typer) | ⚠️ OVERKILL | Système de découverte automatique de commandes avec entry points ? Pour une CLI locale de ~15 commandes, c'est de la sur-architecture. |

**💡 Verdict:** Niveau 1 suffit. Niveau 2 si le fichier continue de grossir.

---

#### 11. Code Mort et Intégrations Non Raccordées

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Vulture basique) | ✅ ESSENTIEL | Exécuter `vulture rekall/` identifie le code mort en 10 secondes. Intégration CI triviale. |
| **Niveau 2** (Raccorder ou documenter) | 👍 RECOMMANDÉ | Les installateurs IDE (Copilot, Windsurf, etc.) sont du code valide mais inaccessible. Soit ajouter des commandes CLI `rekall install-integration`, soit les marquer comme "expérimental". |
| **Niveau 3** (Système de plugins dynamique) | 🟡 OPTIONNEL | Utiliser stevedore/pluggy pour charger les intégrations dynamiquement est élégant mais complexe. Réserver aux cas où tu veux des plugins tiers. |

**💡 Verdict:** Niveaux 1-2 recommandés. Niveau 3 si écosystème de plugins envisagé.

---

#### 12. Observabilité et Gestion d'Erreurs

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Exceptions ciblées + logging) | ✅ ESSENTIEL | Remplacer `except Exception` par des exceptions spécifiques avec `logging.exception()`. Coût minimal, débuggabilité maximale. |
| **Niveau 2** (Rich/Typer feedback) | 👍 RECOMMANDÉ | Utiliser `typer.echo()` avec codes couleur Rich pour les erreurs utilisateur. Messages explicites avec suggestions de remédiation. |
| **Niveau 3** (Structured logging avec Loguru/structlog) | 🟡 OPTIONNEL | JSON logs, contexte enrichi, agrégation. Utile pour debug complexe mais overkill pour une CLI locale. |

**💡 Verdict:** Niveaux 1-2 obligatoires. Niveau 3 si besoin d'agrégation de logs.

---

#### 13. Persistance de Configuration (Intégrité)

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Lib TOML + atomicité basique) | ✅ ESSENTIEL | Utiliser `tomli`/`tomli-w` au lieu de manipulation manuelle. Écriture atomique : `tempfile` + `os.replace()`. |
| **Niveau 2** (fsync + feedback utilisateur) | 👍 RECOMMANDÉ | Appeler `fsync()` avant rename pour garantir la persistance. Logger/afficher les erreurs d'écriture. |
| **Niveau 3** (File locking avec fcntl/portalocker) | ⚠️ OVERKILL | Verrous de fichiers pour CLI mono-utilisateur ? Complexité inutile. Le pattern atomic write suffit. |

**💡 Verdict:** Niveaux 1-2 couvrent 99% des cas. Niveau 3 seulement si accès concurrents réels.

---

#### 14. Durcissement des Archives et Imports

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Limites de taille basiques) | ✅ ESSENTIEL | Vérifier `file_size` avant extraction. Rejeter archives > N Mo. Coût nul, protection DoS immédiate. |
| **Niveau 2** (Validation champs + ratio compression) | 👍 RECOMMANDÉ | Valider chaque champ JSON (taille contenu, nombre tags). Calculer ratio décompression pour détecter zip bombs. |
| **Niveau 3** (Sandbox + quotas ressources) | 🟡 OPTIONNEL | Limiter mémoire/CPU du processus d'extraction avec `resource.setrlimit()`. Utile si archives proviennent de sources non fiables. |

**💡 Verdict:** Niveaux 1-2 couvrent les attaques courantes. Niveau 3 pour paranoïa justifiée.

---

#### 15. Détection et Correction des Contributions IA

| Niveau | Évaluation | Justification |
|--------|------------|---------------|
| **Niveau 1** (Ruff élargi + fix f-strings) | ✅ ESSENTIEL | Activer règles ANN, B, N, PL. Corriger les f-strings manquantes. Coût minimal, détecte 90% des problèmes IA. |
| **Niveau 2** (Audit TODO + conventions) | 👍 RECOMMANDÉ | Scanner les TODO/placeholders, établir guide de style, vérifier cohérence fonctionnalités/docs. |
| **Niveau 3** (Sloppylint + revue narrative) | 🟡 OPTIONNEL | Outils spécialisés détection IA, revue manuelle des promesses de fonctionnalités. Pour projets collaboratifs. |

**💡 Verdict:** Niveaux 1-2 obligatoires pour tout projet avec contributions IA. Niveau 3 si équipe multi-agents.

---

### 🏆 Synthèse des Recommandations

#### ✅ À implémenter absolument (Semaine 1-2)

1. **CI/CD Niveau 1** : pip-audit + Bandit
2. **Permissions SQLite** : chmod 600
3. **uv lock** : Verrouillage des dépendances
4. **Ruff basique** : Règles E, F, W
5. **Validation Pydantic** : Pour les entrées utilisateur
6. **DRY serializers** : Extraire `entry_to_dict()` partagée
7. **Vulture** : Détection code mort en CI
8. **Exceptions ciblées** : Remplacer `except Exception` silencieux
9. **TOML lib** : `tomli-w` au lieu de manipulation manuelle
10. **Limite taille archives** : Rejeter fichiers > N Mo
11. **Ruff élargi IA** : Activer règles ANN, B, N, PL *(Nouveau)*
12. **Fix f-strings** : Corriger interpolations manquantes (`{var}` → f-string) *(Nouveau)*

#### 👍 Recommandé (Semaine 3-4)

1. **CI/CD Niveau 2** : Safety + TruffleHog
2. **Ruff étendu** : Ajouter I, B, S, UP
3. **CI avec lockfile** : uv sync --frozen
4. **Documentation RGPD** : Classification des données
5. **Requêtes paramétrées** : Validation FTS
6. **Module serializers** : Créer `rekall/serializers.py`
7. **Raccorder intégrations** : Commandes CLI pour installateurs IDE
8. **Rich error feedback** : Messages utilisateur avec suggestions
9. **Atomic write + fsync** : Écriture sécurisée config.toml
10. **Validation ZIP ratio** : Détection zip bombs
11. **Audit TODO/placeholders** : Scanner et corriger les TODO non résolus *(Nouveau)*
12. **Guide de style** : Documenter conventions PEP 8 + patterns maison *(Nouveau)*

#### 🟡 Optionnel (selon besoins)

1. **SQLCipher** : Si données vraiment sensibles
2. **Keyring** : Si SQLCipher activé
3. **Détection PII regex** : Si exports fréquents
4. **Pre-commit hooks** : Si contributeurs externes
5. **CLI modulaire** : Sous-commandes si >3000 LOC
6. **Plugins dynamiques** : Stevedore si écosystème tiers
7. **Structured logging** : Loguru/structlog si debug complexe
8. **Sandbox extraction** : `resource.setrlimit()` si sources non fiables
9. **Sloppylint** : Détection patterns IA si contributions multi-agents *(Nouveau)*
10. **Revue narrative** : Audit cohérence docs/fonctionnalités si équipe *(Nouveau)*

#### ⚠️ À éviter (over-engineering)

1. ~~Semgrep + SARIF~~ → Bandit suffit
2. ~~Migration SQLCipher auto~~ → Chiffrer dès le départ
3. ~~Sessions avec timeout~~ → Pas de session en CLI
4. ~~Audit logs~~ → Pas de valeur pour usage perso
5. ~~Triggers SQL audit~~ → Complexité inutile
6. ~~Repository Pattern~~ → Un seul backend
7. ~~Use Cases + DI~~ → <500 LOC, pas besoin
8. ~~Pydantic serdes complet~~ → Schéma stable, pas de valeur
9. ~~Architecture plugins Typer~~ → ~15 commandes seulement
10. ~~File locking fcntl~~ → CLI mono-utilisateur, atomic write suffit
11. ~~AI code detection ML~~ → Overkill pour projet personnel *(Nouveau)*

---

## 1. CI/CD et Scans de Sécurité

### 🔴 Problématique Identifiée

> **[HAUTE] Absence totale de pipeline CI/CD et de scans de vulnérabilités**
> - Aucune automatisation pour tests, lint, ou audits (SAST/dep)
> - Risque d'introduire des CVE ou régressions
> - Référence: OWASP A03:2025 (Software Supply Chain Failures)

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [pip-audit (GitHub PyPA)](https://github.com/pypa/pip-audit) | **Outil officiel PyPA**, maintenu activement, utilise la base PyPI Advisory Database. Standard de facto pour l'audit des dépendances Python. |
| [Safety (GitHub pyupio)](https://github.com/pyupio/safety) | **Alternative mature** avec base de données propriétaire plus exhaustive. Offre GitHub Action dédiée. Complémentaire à pip-audit. |
| [Wiz - CI/CD Security Best Practices](https://www.wiz.io/academy/ci-cd-security-best-practices) | **Guide enterprise-grade** avec métriques 2025 (35% des entreprises utilisent des runners mal configurés). Approche "shift-left" bien documentée. |
| [Atmosly - Python CI/CD Pipeline 2025](https://atmosly.com/blog/python-ci-cd-pipeline-mastery-a-complete-guide-for-2025) | **Guide complet 2025** avec exemples GitHub Actions, matrix builds, et bonnes pratiques de sécurité intégrées. |
| [Bandit (GitHub PyCQA)](https://github.com/PyCQA/bandit) | **SAST officiel Python** par PyCQA. 88% de détection des failles d'injection selon benchmarks OWASP 2024. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [Medium - EDTS Automated Security Testing](https://medium.com/edts/automated-security-testing-in-ci-cd-pipelines-using-github-actions-7e974804a92c) | Article généraliste sans focus Python, exemples trop simplistes pour une implémentation SOTA. |
| [DevOps Training Institute - 15 GitHub Actions Plugins](https://www.devopstraininginstitute.com/blog/15-most-used-plugins-in-github-actions) | Liste sans profondeur technique, pas de contexte sécurité Python spécifique. |
| [CyberSecurityNews - Building Secure DevOps Pipeline](https://cybersecuritynews.com/ci-cd-security/) | Contenu orienté marketing, manque d'exemples concrets et de code. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Approche "Shift-Left"** : Intégrer les tests de sécurité le plus tôt possible dans le cycle
2. **Multi-couches de sécurité** :
   - SAST (Static Application Security Testing) : Bandit, Semgrep
   - SCA (Software Composition Analysis) : pip-audit, Safety
   - Secret Scanning : detect-secrets, gitleaks
3. **Épinglage des Actions** : Utiliser le SHA complet (pas juste `@v4`) pour les actions GitHub
4. **Fail-fast** : Bloquer les merges si vulnérabilités critiques détectées

### 📈 Remédiation Graduelle

#### Niveau 1 - Fondations (Semaine 1)
```yaml
# .github/workflows/security.yml
name: Security Checks
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pip-audit bandit[toml]

      - name: Run pip-audit
        run: pip-audit --require-hashes --strict

      - name: Run Bandit
        run: bandit -r rekall/ -c pyproject.toml
```

#### Niveau 2 - Intermédiaire (Semaine 2-3)
```yaml
# Ajouter Safety pour couverture complémentaire
- name: Run Safety
  run: |
    pip install safety
    safety check --full-report

# Ajouter secret scanning
- name: Detect Secrets
  uses: trufflesecurity/trufflehog@main
  with:
    path: ./
    base: ${{ github.event.repository.default_branch }}
```

#### Niveau 3 - Avancé (Mois 1)
```yaml
# Configuration complète avec Semgrep
- name: Semgrep SAST
  uses: returntocorp/semgrep-action@v1
  with:
    config: >-
      p/python
      p/security-audit
      p/owasp-top-ten

# Rapport SARIF pour GitHub Security tab
- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: results.sarif
```

#### Configuration pyproject.toml
```toml
[tool.bandit]
exclude_dirs = ["tests", ".venv", "__pycache__"]
skips = ["B101"]  # skip assert warnings in tests
targets = ["rekall"]

[tool.bandit.assert_used]
skips = ["*_test.py", "*test_*.py"]
```

---

## 2. Chiffrement des Données SQLite

### 🔴 Problématique Identifiée

> **[HAUTE] Données stockées en clair dans SQLite sans protection**
> - La base locale n'emploie ni chiffrement au repos ni contrôle d'accès
> - Compromission machine ⇒ fuite de notes potentiellement sensibles
> - Références: OWASP A04:2025 (Cryptographic Failures), CWE-311

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [Charles Leifer - Encrypted SQLite with SQLCipher](https://charlesleifer.com/blog/encrypted-sqlite-databases-with-python-and-sqlcipher/) | **Auteur de Peewee ORM**, expert reconnu. Guide pratique avec exemples Python fonctionnels. Recommande sqlcipher3-binary. |
| [sqlcipher3 (GitHub coleifer)](https://github.com/coleifer/sqlcipher3) | **Bindings Python maintenus** (contrairement à pysqlcipher3). Package wheel autonome disponible (sqlcipher3-binary). |
| [Blackhawk - Best Practices for Securing SQLite](https://blackhawk.sh/en/blog/best-practices-for-securing-sqlite/) | **Guide complet** couvrant permissions fichiers, WAL, et chiffrement. Approche défense en profondeur. |
| [Tencent Cloud - SQLite Encryption](https://www.tencentcloud.com/techpedia/102689) | **Perspective enterprise** avec comparaison des options (SQLCipher, SEE, wxSQLite3). Métriques de performance incluses. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [pysqlcipher3 (rigglemania)](https://github.com/rigglemania/pysqlcipher3) | **Projet abandonné** - dernier commit 2019. Documentation SQLAlchemy confirme qu'il n'est plus maintenu. |
| [pysqlcipher (PyPI)](https://pypi.org/project/pysqlcipher/) | **Obsolète** - Python 2 uniquement, incompatible Python 3.9+. |
| [privacee/pysqlcipher3](https://github.com/privacee/pysqlcipher3) | **Fork non officiel** sans activité significative. Risque de sécurité à utiliser un fork non audité. |
| [Devart Python Connector](https://docs.devart.com/python/sqlite/database-encryption.htm) | **Solution propriétaire payante**, non adapté à un projet open-source. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **SQLCipher** : Standard de facto pour le chiffrement SQLite (AES-256-CBC)
2. **Gestion des clés** : Utiliser le keyring système (voir section 3)
3. **Protection des fichiers** :
   - Permissions `chmod 600` sur le fichier .db
   - Protéger aussi les fichiers `-wal` et `-shm`
4. **Migration transparente** : Supporter les bases existantes non chiffrées

### 📈 Remédiation Graduelle

#### Niveau 1 - Permissions Fichiers (Immédiat)
```python
# rekall/db.py - Ajout après création de la base
import os
import stat

def secure_db_permissions(db_path: Path) -> None:
    """Restreint les permissions du fichier DB à l'utilisateur seul."""
    os.chmod(db_path, stat.S_IRUSR | stat.S_IWUSR)  # 600

    # Protéger aussi les fichiers WAL si présents
    for suffix in ['-wal', '-shm']:
        wal_path = db_path.parent / f"{db_path.name}{suffix}"
        if wal_path.exists():
            os.chmod(wal_path, stat.S_IRUSR | stat.S_IWUSR)
```

#### Niveau 2 - Chiffrement Optionnel (Semaine 2-4)
```python
# rekall/crypto.py
from typing import Optional
import sqlcipher3

def get_encrypted_connection(
    db_path: str,
    passphrase: Optional[str] = None
) -> sqlcipher3.Connection:
    """
    Ouvre une connexion SQLite chiffrée avec SQLCipher.

    Args:
        db_path: Chemin vers la base de données
        passphrase: Phrase de passe pour le chiffrement
    """
    conn = sqlcipher3.connect(db_path)

    if passphrase:
        # Configuration SQLCipher optimale
        conn.execute(f"PRAGMA key = '{passphrase}'")
        conn.execute("PRAGMA cipher_page_size = 4096")
        conn.execute("PRAGMA kdf_iter = 256000")  # PBKDF2 iterations
        conn.execute("PRAGMA cipher_hmac_algorithm = HMAC_SHA512")
        conn.execute("PRAGMA cipher_kdf_algorithm = PBKDF2_HMAC_SHA512")

    return conn
```

#### Niveau 3 - Migration Automatique (Mois 1-2)
```python
# rekall/migration.py
def migrate_to_encrypted(
    plain_db: Path,
    encrypted_db: Path,
    passphrase: str
) -> None:
    """
    Migre une base non chiffrée vers une base chiffrée.

    Utilise sqlcipher_export pour une migration atomique.
    """
    import sqlite3
    import sqlcipher3

    # Ouvrir la base source en lecture seule
    src = sqlite3.connect(f"file:{plain_db}?mode=ro", uri=True)

    # Créer la base chiffrée
    dst = sqlcipher3.connect(str(encrypted_db))
    dst.execute(f"PRAGMA key = '{passphrase}'")

    # Export atomique
    src.backup(dst)

    src.close()
    dst.close()

    # Supprimer l'ancienne base de façon sécurisée
    secure_delete(plain_db)
```

#### Dépendances à ajouter
```toml
# pyproject.toml
[project.optional-dependencies]
encryption = [
    "sqlcipher3-binary>=0.5.0",
]
```

---

## 3. Authentification et Autorisation

### 🔴 Problématique Identifiée

> **[MOYENNE] Absence d'authentification/autorisation**
> - Toute personne ayant accès au shell peut lire/écrire la base
> - Fuite ou corruption si poste partagé/compromis
> - Référence: OWASP A01:2025 (Broken Access Control)

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [keyring (PyPI)](https://pypi.org/project/keyring/) | **Bibliothèque standard de facto** pour le stockage sécurisé de credentials. Cross-platform (macOS Keychain, Windows Credential Locker, Linux Secret Service). |
| [keyring Documentation](https://keyring.readthedocs.io/) | **Documentation officielle** avec exemples d'utilisation, backends supportés, et configuration avancée. |
| [Martin Heinz - Secure Password Handling](https://martinheinz.dev/blog/59) | **Article technique approfondi** comparant les approches (keyring, getpass, environment). Recommandations claires avec justifications. |
| [CLIMB - 10 Python Keyring Best Practices](https://climbtheladder.com/10-python-keyring-best-practices/) | **Checklist pratique** : least privilege, rotation, backup sécurisé. Orienté production. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [GeeksforGeeks - Storing passwords with keyring](https://www.geeksforgeeks.org/python/storing-passwords-with-python-keyring/) | **Contenu trop basique**, exemples sans considérations de sécurité avancées. Pas de gestion d'erreurs. |
| [alexwlchan - Use keyring](https://alexwlchan.net/2016/you-should-use-keyring/) | **Article de 2016**, informations potentiellement obsolètes concernant les backends Linux modernes. |
| [pythonmana - Secure password processing](https://pythonmana.com/2022/01/202201050416151089.html) | **Qualité douteuse**, traduction automatique visible, code non testé. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Keyring système** : Déléguer le stockage des secrets au système d'exploitation
2. **Principe du moindre privilège** : Ne stocker que les secrets strictement nécessaires
3. **Verrouillage automatique** : Timeout d'inactivité configurable
4. **Journalisation d'accès** : Logger les accès pour audit (sans logger les secrets !)
5. **Fallback sécurisé** : Demander le mot de passe si keyring indisponible

### 📈 Remédiation Graduelle

#### Niveau 1 - Protection par Passphrase (Semaine 1-2)
```python
# rekall/auth.py
import getpass
import keyring
from typing import Optional

SERVICE_NAME = "rekall"
USERNAME = "db_passphrase"

def get_passphrase(prompt: bool = True) -> Optional[str]:
    """
    Récupère la passphrase depuis le keyring système.

    Args:
        prompt: Si True, demande à l'utilisateur si non trouvée

    Returns:
        La passphrase ou None si non disponible
    """
    # Essayer le keyring système
    passphrase = keyring.get_password(SERVICE_NAME, USERNAME)

    if passphrase is None and prompt:
        passphrase = getpass.getpass("Passphrase Rekall: ")

        # Proposer de sauvegarder
        if input("Sauvegarder dans le keyring? [o/N] ").lower() == 'o':
            set_passphrase(passphrase)

    return passphrase


def set_passphrase(passphrase: str) -> None:
    """Stocke la passphrase dans le keyring système."""
    keyring.set_password(SERVICE_NAME, USERNAME, passphrase)


def delete_passphrase() -> None:
    """Supprime la passphrase du keyring."""
    try:
        keyring.delete_password(SERVICE_NAME, USERNAME)
    except keyring.errors.PasswordDeleteError:
        pass  # Déjà supprimée
```

#### Niveau 2 - Mode Protégé avec Verrouillage (Semaine 3-4)
```python
# rekall/session.py
import time
from dataclasses import dataclass
from typing import Optional

@dataclass
class Session:
    """Session authentifiée avec timeout."""

    passphrase: str
    created_at: float
    last_activity: float
    timeout_seconds: int = 300  # 5 minutes par défaut

    def is_valid(self) -> bool:
        """Vérifie si la session est encore valide."""
        return (time.time() - self.last_activity) < self.timeout_seconds

    def touch(self) -> None:
        """Met à jour le timestamp d'activité."""
        self.last_activity = time.time()

    def lock(self) -> None:
        """Verrouille la session (efface la passphrase de la mémoire)."""
        # Écraser la passphrase en mémoire
        self.passphrase = "x" * len(self.passphrase)
        self.passphrase = None


_current_session: Optional[Session] = None

def require_auth(func):
    """Décorateur exigeant une session authentifiée."""
    def wrapper(*args, **kwargs):
        global _current_session

        if _current_session is None or not _current_session.is_valid():
            passphrase = get_passphrase(prompt=True)
            if not passphrase:
                raise AuthenticationError("Authentification requise")
            _current_session = Session(
                passphrase=passphrase,
                created_at=time.time(),
                last_activity=time.time()
            )

        _current_session.touch()
        return func(*args, **kwargs)

    return wrapper
```

#### Niveau 3 - Journalisation d'Accès (Mois 1)
```python
# rekall/audit.py
import logging
from datetime import datetime
from pathlib import Path

def setup_audit_log(log_path: Path) -> logging.Logger:
    """Configure un logger d'audit sécurisé."""

    logger = logging.getLogger("rekall.audit")
    logger.setLevel(logging.INFO)

    # Handler fichier avec rotation
    handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,  # 1 MB
        backupCount=5
    )

    # Format d'audit
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def log_access(action: str, resource: str, success: bool) -> None:
    """
    Journalise un accès.

    IMPORTANT: Ne JAMAIS logger de secrets ou données sensibles !
    """
    logger = logging.getLogger("rekall.audit")
    status = "SUCCESS" if success else "FAILURE"
    logger.info(f"{status} | {action} | {resource}")
```

---

## 4. Gestion des PII et Conformité RGPD

### 🔴 Problématique Identifiée

> **[MOYENNE] Politique de rétention et masquage non définie**
> - Les captures peuvent inclure PII/secrets
> - Pas de mécanisme de purge/masquage
> - Non-conformité RGPD potentielle

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [Alation - GDPR Data Compliance 2025](https://www.alation.com/blog/gdpr-data-compliance-best-practices-2025/) | **Guide enterprise 2025** avec focus sur les amendes récentes (8-22M€) et les articles RGPD concernés. Approche lifecycle management. |
| [Accutive Security - GDPR Data Masking Guide 2025](https://accutivesecurity.com/how-to-implement-gdpr-data-masking-without-sacrificing-usability/) | **Guide technique** comparant anonymisation vs pseudonymisation. Exemples de techniques de masquage préservant l'utilité. |
| [Sentra - PII Compliance Checklist 2025](https://www.sentra.io/learn/pii-compliance-checklist) | **Checklist actionnable** avec 17 types de PII à considérer. Framework de classification des données. |
| [HydroXai - pii-masker (GitHub)](https://github.com/HydroXai/pii-masker) | **Outil open-source** basé sur DeBERTa-v3 pour détection/masquage automatique de PII. API Python simple. |
| [MSTICPy - Data Masking](https://msticpy.readthedocs.io/en/latest/data_acquisition/DataMasking.html) | **Bibliothèque Microsoft** pour l'obfuscation de données. Fonctions de hachage et mapping aléatoire. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [Ground Labs - PII and Data Retention](https://www.groundlabs.com/blog/what-is-pii-for-gdpr) | **Contenu orienté produit** (promotion de leur solution), peu de valeur technique pour l'implémentation. |
| [pii.ai - GDPR Compliant Guide](https://www.pii.ai/blog/gdpr-compliant-the-complete-2025-guide) | **Site commercial** avec contenu générique, pas d'exemples de code ou d'architecture. |
| [ByteTools - AI Privacy Guide](https://bytetools.io/guides/ai-privacy-best-practices) | **Hors scope** - focalisé sur l'IA/LLM, pas sur les applications de gestion de données locales. |
| [Nightfall AI - PII Management](https://www.nightfall.ai/blog/storing-pii-in-the-cloud-best-practices-and-regulatory-considerations) | **Orienté cloud/SaaS**, recommandations non applicables à une CLI locale. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Classification des données** : Identifier et taguer les champs contenant potentiellement des PII
2. **Minimisation** : Ne collecter que les données strictement nécessaires
3. **Rétention définie** : Politique de durée de conservation documentée
4. **Droit à l'effacement** : Commande de purge sécurisée (Article 17 RGPD)
5. **Masquage à l'export** : Options d'anonymisation pour les exports

### 📈 Remédiation Graduelle

#### Niveau 1 - Classification et Documentation (Semaine 1)
```python
# rekall/models.py
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

class DataClassification(Enum):
    """Classification RGPD des données."""
    PUBLIC = "public"           # Données non sensibles
    INTERNAL = "internal"       # Données internes
    CONFIDENTIAL = "confidential"  # Données personnelles
    RESTRICTED = "restricted"   # Données sensibles (santé, opinions, etc.)


@dataclass
class Note:
    """Modèle de note avec métadonnées de classification."""

    id: int
    content: str
    created_at: datetime
    updated_at: datetime

    # Métadonnées RGPD
    classification: DataClassification = DataClassification.INTERNAL
    contains_pii: bool = False
    retention_days: Optional[int] = None  # None = rétention indéfinie

    def is_expired(self) -> bool:
        """Vérifie si la note a dépassé sa période de rétention."""
        if self.retention_days is None:
            return False
        age = (datetime.now() - self.created_at).days
        return age > self.retention_days
```

#### Niveau 2 - Détection Automatique de PII (Semaine 2-4)
```python
# rekall/pii.py
import re
from typing import List, Tuple

# Patterns de détection de PII (regex simples pour v1)
PII_PATTERNS = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone_fr": r'\b(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}\b',
    "iban": r'\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b',
    "credit_card": r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
    "ssn_fr": r'\b[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}\s?\d{2}\b',
}


def detect_pii(text: str) -> List[Tuple[str, str, int, int]]:
    """
    Détecte les PII dans un texte.

    Returns:
        Liste de tuples (type, valeur, début, fin)
    """
    findings = []

    for pii_type, pattern in PII_PATTERNS.items():
        for match in re.finditer(pattern, text, re.IGNORECASE):
            findings.append((
                pii_type,
                match.group(),
                match.start(),
                match.end()
            ))

    return findings


def mask_pii(text: str, mask_char: str = "*") -> str:
    """
    Masque les PII détectés dans un texte.

    Préserve les premiers et derniers caractères pour l'identification.
    """
    result = text

    for pii_type, value, start, end in sorted(
        detect_pii(text),
        key=lambda x: x[2],
        reverse=True  # Traiter de la fin au début
    ):
        if len(value) > 4:
            masked = value[0] + mask_char * (len(value) - 2) + value[-1]
        else:
            masked = mask_char * len(value)

        result = result[:start] + masked + result[end:]

    return result
```

#### Niveau 3 - Commandes de Purge et Rétention (Mois 1-2)
```python
# rekall/retention.py
from datetime import datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def purge_expired_notes(db, dry_run: bool = True) -> int:
    """
    Purge les notes ayant dépassé leur période de rétention.

    Args:
        db: Connexion à la base de données
        dry_run: Si True, simule sans supprimer

    Returns:
        Nombre de notes purgées (ou à purger si dry_run)
    """
    cursor = db.execute("""
        SELECT id, created_at, retention_days
        FROM notes
        WHERE retention_days IS NOT NULL
    """)

    expired_ids = []
    now = datetime.now()

    for row in cursor:
        note_id, created_at, retention_days = row
        expiry = created_at + timedelta(days=retention_days)
        if now > expiry:
            expired_ids.append(note_id)

    if not dry_run and expired_ids:
        placeholders = ','.join('?' * len(expired_ids))
        db.execute(
            f"DELETE FROM notes WHERE id IN ({placeholders})",
            expired_ids
        )
        db.commit()
        logger.info(f"Purgé {len(expired_ids)} notes expirées")

    return len(expired_ids)


def secure_delete_note(db, note_id: int) -> None:
    """
    Suppression sécurisée d'une note (droit à l'oubli RGPD).

    Écrase le contenu avant suppression pour éviter la récupération.
    """
    # Écraser le contenu
    db.execute(
        "UPDATE notes SET content = ?, updated_at = ? WHERE id = ?",
        ("[DELETED]", datetime.now(), note_id)
    )

    # Puis supprimer
    db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    db.commit()

    # VACUUM pour libérer l'espace et éviter récupération
    db.execute("VACUUM")
```

#### Documentation à ajouter au README
```markdown
## Politique de Confidentialité et Rétention

### Classification des Données
- **PUBLIC**: Informations non sensibles
- **INTERNAL**: Notes personnelles standard
- **CONFIDENTIAL**: Contient des données personnelles (PII)
- **RESTRICTED**: Données sensibles (santé, finances)

### Rétention
Par défaut, les notes sont conservées indéfiniment. Vous pouvez définir
une période de rétention par note avec `--retention-days`.

### Droit à l'Effacement
Utilisez `rekall delete --secure <id>` pour une suppression conforme RGPD.
```

---

## 5. Validation des Entrées Utilisateur

### 🔴 Problématique Identifiée

> **[MOYENNE] Vérification limitée des entrées utilisateur**
> - Peu de validation/sanitation des contenus stockés
> - Risque d'injection FTS ou de corruption logique
> - Références: OWASP A05:2025 (Injection)

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html) | **Source autoritaire** OWASP. Principes fondamentaux : whitelist > blacklist, validation + encodage contextuels. |
| [Pydantic Documentation](https://docs.pydantic.dev/latest/) | **Standard Python** pour la validation de données. Type hints natifs, validation automatique, excellent écosystème. |
| [Real Python - Prevent SQL Injection](https://realpython.com/prevent-python-sql-injection/) | **Tutoriel pratique** avec exemples sqlite3, parameterized queries, et pièges courants. Qualité éditoriale Real Python. |
| [johal.in - Pydantic Validation Layers 2025](https://johal.in/pydantic-validation-layers-secure-python-ml-input-sanitization-2025/) | **Article récent** sur les couches de validation, applicable au-delà du ML. Patterns défensifs modernes. |
| [SQLite FTS3/FTS4 Documentation](https://www.sqlite.org/fts3.html) | **Documentation officielle** SQLite. Essentiel pour comprendre le MATCH operator et ses particularités. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [freedium.cfd - Input Validation Best Practices](https://freedium.cfd/a2c255b858e0) | **Mirror non officiel** de Medium, potentiellement modifié. Préférer la source originale. |
| [spsanderson.com - Python Input Validation Beginner's Guide](https://www.spsanderson.com/steveondata/posts/2025-07-16/) | **Niveau trop basique**, destiné aux débutants absolus. Pas de considérations sécurité avancées. |
| [toxigon.com - FastAPI Security](https://toxigon.com/python-fastapi-security-best-practices-2025) | **Hors scope** - spécifique FastAPI/web, non applicable à une CLI. |
| [moldstud.com - Backend Validation Tips](https://moldstud.com/articles/p-essential-data-validation-sanitization-practices-for-backend-developers-best-backend-development-tips-2025) | **Contenu générique** sans focus Python, exemples dans d'autres langages. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Validation en couches** : Valider à l'entrée ET avant le stockage
2. **Whitelist > Blacklist** : 30% plus efficace selon OWASP
3. **Requêtes paramétrées** : TOUJOURS utiliser les placeholders `?`
4. **Limites explicites** : Longueurs max, formats attendus
5. **Encodage contextuel** : Échapper selon le contexte de sortie

### 📈 Remédiation Graduelle

#### Niveau 1 - Validation Pydantic (Semaine 1)
```python
# rekall/validators.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re

class NoteInput(BaseModel):
    """Validation des entrées pour la création de notes."""

    content: str = Field(
        min_length=1,
        max_length=100_000,  # 100 KB max
        description="Contenu de la note"
    )

    tags: Optional[list[str]] = Field(
        default=None,
        max_length=20,  # Max 20 tags
        description="Tags associés"
    )

    classification: str = Field(
        default="internal",
        pattern=r"^(public|internal|confidential|restricted)$"
    )

    @field_validator('content')
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Nettoie le contenu tout en préservant le formatage."""
        # Supprimer les caractères de contrôle (sauf newline, tab)
        v = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', v)

        # Normaliser les fins de ligne
        v = v.replace('\r\n', '\n').replace('\r', '\n')

        return v.strip()

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Valide et nettoie les tags."""
        if v is None:
            return None

        cleaned = []
        for tag in v:
            # Tags alphanumériques + tirets uniquement
            tag = re.sub(r'[^a-zA-Z0-9\-_]', '', tag.strip().lower())
            if tag and len(tag) <= 50:
                cleaned.append(tag)

        return cleaned[:20] if cleaned else None


class SearchQuery(BaseModel):
    """Validation des requêtes de recherche."""

    query: str = Field(
        min_length=1,
        max_length=500,
        description="Requête de recherche"
    )

    limit: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="Nombre max de résultats"
    )

    @field_validator('query')
    @classmethod
    def sanitize_fts_query(cls, v: str) -> str:
        """
        Nettoie la requête pour SQLite FTS.

        Échappe les caractères spéciaux FTS pour éviter les injections.
        """
        # Caractères spéciaux FTS à échapper
        fts_special = ['*', '"', '(', ')', 'OR', 'AND', 'NOT', 'NEAR']

        result = v
        for char in ['"', '*', '(', ')']:
            result = result.replace(char, f'"{char}"')

        # Limiter la longueur des termes individuels
        terms = result.split()
        terms = [t[:100] for t in terms]  # Max 100 chars par terme

        return ' '.join(terms)
```

#### Niveau 2 - Requêtes Paramétrées Strictes (Semaine 2)
```python
# rekall/db.py - Amélioration des requêtes existantes

def search_notes(db, query: str, limit: int = 50) -> list:
    """
    Recherche full-text avec requêtes paramétrées.

    IMPORTANT: Toujours utiliser des paramètres, jamais de f-strings !
    """
    # Valider l'entrée
    validated = SearchQuery(query=query, limit=limit)

    # Requête paramétrée - le ? est OBLIGATOIRE
    cursor = db.execute(
        """
        SELECT id, content, snippet(notes_fts, 1, '<mark>', '</mark>', '...', 32)
        FROM notes_fts
        WHERE notes_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        (validated.query, validated.limit)
    )

    return cursor.fetchall()


def insert_note(db, content: str, **kwargs) -> int:
    """
    Insère une note avec validation stricte.
    """
    # Validation via Pydantic
    validated = NoteInput(content=content, **kwargs)

    cursor = db.execute(
        """
        INSERT INTO notes (content, classification, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        """,
        (
            validated.content,
            validated.classification,
            datetime.now(),
            datetime.now()
        )
    )

    db.commit()
    return cursor.lastrowid
```

#### Niveau 3 - Contraintes Base de Données (Mois 1)
```python
# rekall/migrations/003_add_constraints.py
"""
Migration: Ajouter des contraintes CHECK à la base de données.

Ces contraintes servent de dernière ligne de défense.
"""

MIGRATION_SQL = """
-- Contraintes sur la table notes
ALTER TABLE notes ADD CONSTRAINT chk_content_length
    CHECK (length(content) <= 100000);

ALTER TABLE notes ADD CONSTRAINT chk_classification
    CHECK (classification IN ('public', 'internal', 'confidential', 'restricted'));

-- Index pour améliorer les performances de validation
CREATE INDEX IF NOT EXISTS idx_notes_classification
    ON notes(classification);

-- Table d'audit des modifications
CREATE TABLE IF NOT EXISTS notes_audit (
    id INTEGER PRIMARY KEY,
    note_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')),
    old_content TEXT,
    new_content TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT
);

-- Trigger d'audit
CREATE TRIGGER IF NOT EXISTS audit_notes_update
AFTER UPDATE ON notes
BEGIN
    INSERT INTO notes_audit (note_id, action, old_content, new_content)
    VALUES (OLD.id, 'UPDATE', OLD.content, NEW.content);
END;
"""
```

---

## 6. Verrouillage des Dépendances

### 🔴 Problématique Identifiée

> **[BASSE] Absence de verrouillage des versions**
> - Contraintes larges `>=` exposent aux changements non maîtrisés
> - Builds non reproductibles
> - Référence: OWASP A03:2025 (Software Supply Chain Failures)

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [uv Documentation - Locking](https://docs.astral.sh/uv/pip/compile/) | **Documentation officielle** du gestionnaire moderne d'Astral. Lockfiles universels cross-platform, intégration native pyproject.toml. |
| [PEP 751](https://peps.python.org/pep-0751/) | **Standard en cours** pour le format de lockfile Python. Contexte important pour comprendre l'évolution de l'écosystème. |
| [Lincoln Loop - pip-tools](https://lincolnloop.com/blog/python-dependency-locking-pip-tools/) | **Guide pratique pip-tools** par une agence Django reconnue. Workflow requirements.in → requirements.txt bien expliqué. |
| [Syntal - Poetry/uv Lockfile Strategies](https://medium.com/@sparknp1/8-poetry-uv-lockfile-strategies-that-tame-dependency-hell-4bbf63fee566) | **Article 2025** comparant 8 stratégies de lockfiles. Cas d'usage enterprise avec multi-environnements. |
| [Loopwerk - Poetry vs uv](https://www.loopwerk.io/articles/2024/python-poetry-vs-uv/) | **Comparaison objective** avec benchmarks. Aide au choix d'outil selon le contexte projet. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [Envelope - Poetry vs Uv vs Pip](https://envelope.dev/blog/poetry-vs-uv-vs-pip-choosing-the-right-package-installer) | **Contenu superficiel**, pas de recommandations concrètes pour la sécurité supply chain. |
| [dimasyotama - Python Packaging Landscape](https://dimasyotama.medium.com/navigating-the-python-packaging-landscape-pip-vs-poetry-vs-uv-a-developers-guide-49a9c93caf9c) | **Article généraliste** sans focus sur le verrouillage et la reproductibilité. |
| [pydevtools handbook](https://pydevtools.com/handbook/how-to-use-a-uv-lockfile-for-reproducible-python-environments/) | **Site peu connu**, contenu non vérifié, risque de recommandations obsolètes. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Outil moderne** : Préférer `uv` (2025) ou Poetry pour le verrouillage automatique
2. **Lockfile universel** : uv.lock capture toutes les plateformes dans un seul fichier
3. **Hash-pinning** : Vérifier l'intégrité des packages avec les hashes
4. **CI reproductible** : Utiliser `--frozen` ou `sync` au lieu de `install`
5. **Séparation dev/prod** : Groupes de dépendances distincts

### 📈 Remédiation Graduelle

#### Niveau 1 - Migration vers uv (Semaine 1)
```bash
# Installation de uv (recommandé 2025)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialiser le lockfile depuis pyproject.toml existant
cd rekall
uv lock

# Le fichier uv.lock est créé automatiquement
```

```toml
# pyproject.toml - Mise à jour
[project]
name = "rekall"
version = "0.1.0"
requires-python = ">=3.9"

dependencies = [
    "typer>=0.9.0",
    "rich>=13.0.0",
    "sqlite-utils>=3.35",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "bandit[toml]>=1.7.0",
]

encryption = [
    "sqlcipher3-binary>=0.5.0",
]

[tool.uv]
# Exiger un lockfile à jour
locked = true
```

#### Niveau 2 - CI avec Lockfile (Semaine 2)
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: "latest"

      - name: Set up Python ${{ matrix.python-version }}
        run: uv python install ${{ matrix.python-version }}

      - name: Install dependencies (locked)
        run: uv sync --frozen  # Échoue si lockfile désynchronisé

      - name: Run tests
        run: uv run pytest tests/ -v --cov=rekall

      - name: Verify lockfile is up to date
        run: |
          uv lock --check
          if [ $? -ne 0 ]; then
            echo "::error::Lockfile out of sync. Run 'uv lock' locally."
            exit 1
          fi
```

#### Niveau 3 - Audit et Hash Verification (Mois 1)
```yaml
# .github/workflows/security.yml (extension)
jobs:
  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Export requirements with hashes
        run: uv export --format requirements-txt --hashes > requirements.txt

      - name: Audit dependencies
        run: |
          uv pip install pip-audit
          pip-audit -r requirements.txt --require-hashes --strict

      - name: Check for yanked packages
        run: uv pip check
```

```toml
# pyproject.toml - Configuration uv avancée
[tool.uv]
locked = true

[tool.uv.sources]
# Forcer les sources officielles uniquement
rekall = { index = "pypi" }

[tool.uv.pip]
# Options de sécurité
require-hashes = true
no-binary = ["pyyaml"]  # Compiler depuis les sources pour audit
```

---

## 7. Qualité de Code et Linting

### 🔴 Problématique Identifiée

> **[BASSE] Style lint partiel**
> - Ruff configuré uniquement sur règles basiques
> - Pas d'exécution CI

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [Ruff Documentation](https://docs.astral.sh/ruff/) | **Source officielle** Astral. Configuration exhaustive, 800+ règles documentées, exemples pyproject.toml. |
| [Ruff Configuration Guide](https://docs.astral.sh/ruff/configuration/) | **Guide officiel** pour la configuration. Explique preview mode, version pinning, et intégration CI. |
| [Real Python - Ruff Python Linter](https://realpython.com/ruff-python/) | **Tutoriel approfondi** par Real Python. Progression pédagogique, exemples concrets, bonnes pratiques d'adoption. |
| [Better Stack - Linting with Ruff](https://betterstack.com/community/guides/scaling-python/ruff-explained/) | **Guide pratique** avec comparaisons de performance (10-100x plus rapide). Workflow pre-commit inclus. |
| [GPXZ - How to configure ruff](https://www.gpxz.io/blog/ruff) | **Article technique** avec configuration progressive. Stratégie d'adoption graduelle bien expliquée. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [Medium - Configure Ruff with pyproject.toml](https://medium.com/@gema.correa/configure-ruff-easily-with-pyproject-toml-f75914fab055) | **Article basique** sans valeur ajoutée par rapport à la documentation officielle. |
| [Red And Green - Ruff Python Linter](https://redandgreen.co.uk/ruff-python-linter-written-in-rust/python-code/) | **Contenu superficiel**, présentation sans profondeur technique. |
| [glukhov.org - Python Linters Guide](https://www.glukhov.org/post/2025/11/linters-for-python/) | **Guide multi-linters** moins pertinent quand Ruff remplace la plupart des outils. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Ruff all-in-one** : Remplace Flake8, isort, pyupgrade, Black en un seul outil
2. **Épinglage de version** : Éviter les faux positifs lors des mises à jour
3. **Règles progressives** : Commencer par E, F, puis ajouter B, UP, S
4. **Pre-commit hooks** : Feedback immédiat avant commit
5. **CI stricte** : Bloquer les merges sur violations

### 📈 Remédiation Graduelle

#### Niveau 1 - Configuration de Base (Semaine 1)
```toml
# pyproject.toml

[tool.ruff]
# Version épinglée pour reproductibilité
required-version = ">=0.8.0"

# Paramètres généraux
line-length = 88
target-version = "py39"
src = ["rekall", "tests"]

# Exclusions
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
]

[tool.ruff.lint]
# Niveau 1: Règles essentielles
select = [
    "E",    # pycodestyle errors
    "F",    # Pyflakes
    "W",    # pycodestyle warnings
]

# Ignorer les règles problématiques
ignore = [
    "E501",  # Line too long (géré par formatter)
]

# Corrections automatiques autorisées
fixable = ["ALL"]
unfixable = []

[tool.ruff.format]
# Paramètres de formatage
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

#### Niveau 2 - Règles Étendues (Semaine 2-3)
```toml
# pyproject.toml - Extension

[tool.ruff.lint]
select = [
    # Niveau 1
    "E", "F", "W",

    # Niveau 2 - Qualité
    "I",    # isort (imports)
    "N",    # pep8-naming
    "UP",   # pyupgrade
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "SIM",  # flake8-simplify

    # Sécurité
    "S",    # flake8-bandit (règles de sécurité)
]

ignore = [
    "E501",   # Line too long
    "S101",   # assert used (OK dans tests)
    "B008",   # Function call in default argument (OK avec Typer)
]

[tool.ruff.lint.per-file-ignores]
# Règles spécifiques par fichier
"tests/**/*.py" = [
    "S101",  # assert OK dans tests
    "S105",  # Hardcoded password OK dans tests
    "S106",  # Hardcoded password OK dans tests
]
"rekall/cli.py" = [
    "B008",  # Typer utilise des defaults callable
]

[tool.ruff.lint.isort]
# Configuration isort
known-first-party = ["rekall"]
force-single-line = false
lines-after-imports = 2

[tool.ruff.lint.flake8-bandit]
# Configuration sécurité
check-typed-exception = true
hardcoded-tmp-directory = ["/tmp", "/var/tmp"]
```

#### Niveau 3 - Pre-commit et CI (Mois 1)
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0  # Épingler la version !
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

```yaml
# .github/workflows/lint.yml
name: Lint

on: [push, pull_request]

jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Ruff
        run: pip install ruff==0.8.0  # Version épinglée

      - name: Run Ruff Linter
        run: ruff check --output-format=github .

      - name: Run Ruff Formatter
        run: ruff format --check .
```

---

## 8. Architecture et Séparation des Couches

### 🔴 Problématique Identifiée

> **[MOYENNE] Couche data et logique mêlées**
> - `rekall/db.py` combine schéma, migrations et logique
> - Difficile à tester/étendre
> - Dépendance forte à SQLite

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [Cosmic Python - Repository Pattern](https://www.cosmicpython.com/book/chapter_02_repository.html) | **Livre de référence** "Architecture Patterns with Python" par Harry Percival et Bob Gregory. Repository pattern expliqué avec exemples concrets. |
| [glukhov.org - Clean Architecture Python 2025](https://www.glukhov.org/post/2025/11/python-design-patterns-for-clean-architecture/) | **Article récent** (Nov 2025) avec patterns modernes : Unit of Work, DI, séparation stricte des couches. |
| [py-clean-arch (GitHub)](https://github.com/cdddg/py-clean-arch) | **Implémentation de référence** avec SQLAlchemy 2.0 async. Structure de projet exemplaire à adapter. |
| [Krython - Clean Architecture Tutorial](https://www.krython.com/tutorial/python/architectural-patterns-clean-architecture) | **Tutoriel structuré** avec diagrammes et progression pédagogique. Bon point d'entrée pour comprendre les concepts. |
| [Dev3lop - Repository Pattern](https://dev3lop.com/repository-pattern-clean-data-access-layers/) | **Focus repository** avec justifications du pattern (testabilité, abstraction, maintenance). |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [python-clean-architecture (PyPI)](https://pypi.org/project/python-clean-architecture/) | **Package peu maintenu** (dernière release 2021), dépendances obsolètes. |
| [pcah/python-clean-architecture (GitHub)](https://github.com/pcah/python-clean-architecture) | **Projet inactif** (pas de commits récents), approche trop complexe pour une CLI simple. |
| [fast-clean-architecture (PyPI)](https://pypi.org/project/fast-clean-architecture/) | **Scaffolding tool**, pas de documentation sur les patterns, génère du boilerplate non adapté. |
| [LinkedIn - Clean Architecture Implementation](https://www.linkedin.com/pulse/implementation-clean-architecture-python-part-1-cli-watanabe) | **Article LinkedIn** sans profondeur technique suffisante, exemples incomplets. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Couches distinctes** :
   - Domain (entités pures, sans dépendances)
   - Application (use cases, orchestration)
   - Infrastructure (DB, fichiers, APIs externes)
   - Interface (CLI, API)

2. **Repository Pattern** : Abstraction du stockage pour testabilité
3. **Dependency Injection** : Inversion des dépendances
4. **Unit of Work** : Gestion transactionnelle cohérente

### 📈 Remédiation Graduelle

#### Niveau 1 - Extraction des Entités (Semaine 1-2)
```python
# rekall/domain/entities.py
"""
Entités du domaine - AUCUNE dépendance externe.

Ces classes représentent les concepts métier purs.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class Classification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


@dataclass
class Note:
    """Entité Note - objet métier pur."""

    id: Optional[int] = None
    content: str = ""
    tags: List[str] = field(default_factory=list)
    classification: Classification = Classification.INTERNAL
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    retention_days: Optional[int] = None

    def is_expired(self) -> bool:
        """Logique métier : la note est-elle expirée ?"""
        if self.retention_days is None:
            return False
        from datetime import timedelta
        expiry = self.created_at + timedelta(days=self.retention_days)
        return datetime.now() > expiry

    def contains_sensitive_data(self) -> bool:
        """Logique métier : données sensibles ?"""
        return self.classification in (
            Classification.CONFIDENTIAL,
            Classification.RESTRICTED
        )
```

#### Niveau 2 - Repository Pattern (Semaine 3-4)
```python
# rekall/domain/repositories.py
"""
Interfaces des repositories - contrats abstraits.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from .entities import Note


class NoteRepository(ABC):
    """Interface abstraite pour le stockage des notes."""

    @abstractmethod
    def add(self, note: Note) -> Note:
        """Ajoute une note et retourne la note avec son ID."""
        pass

    @abstractmethod
    def get(self, note_id: int) -> Optional[Note]:
        """Récupère une note par son ID."""
        pass

    @abstractmethod
    def get_all(self, limit: int = 100) -> List[Note]:
        """Récupère toutes les notes."""
        pass

    @abstractmethod
    def search(self, query: str, limit: int = 50) -> List[Note]:
        """Recherche full-text dans les notes."""
        pass

    @abstractmethod
    def update(self, note: Note) -> Note:
        """Met à jour une note existante."""
        pass

    @abstractmethod
    def delete(self, note_id: int) -> bool:
        """Supprime une note. Retourne True si supprimée."""
        pass

    @abstractmethod
    def purge_expired(self) -> int:
        """Purge les notes expirées. Retourne le nombre purgé."""
        pass


# rekall/infrastructure/sqlite_repository.py
"""
Implémentation SQLite du repository.
"""
import sqlite3
from typing import List, Optional
from datetime import datetime

from rekall.domain.entities import Note, Classification
from rekall.domain.repositories import NoteRepository


class SQLiteNoteRepository(NoteRepository):
    """Implémentation SQLite du NoteRepository."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[sqlite3.Connection] = None

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    def _row_to_note(self, row: sqlite3.Row) -> Note:
        """Convertit une ligne DB en entité Note."""
        return Note(
            id=row["id"],
            content=row["content"],
            tags=row["tags"].split(",") if row["tags"] else [],
            classification=Classification(row["classification"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            retention_days=row["retention_days"],
        )

    def add(self, note: Note) -> Note:
        cursor = self.connection.execute(
            """
            INSERT INTO notes (content, tags, classification, created_at, updated_at, retention_days)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                note.content,
                ",".join(note.tags),
                note.classification.value,
                note.created_at.isoformat(),
                note.updated_at.isoformat(),
                note.retention_days,
            )
        )
        self.connection.commit()
        note.id = cursor.lastrowid
        return note

    def get(self, note_id: int) -> Optional[Note]:
        cursor = self.connection.execute(
            "SELECT * FROM notes WHERE id = ?",
            (note_id,)
        )
        row = cursor.fetchone()
        return self._row_to_note(row) if row else None

    def search(self, query: str, limit: int = 50) -> List[Note]:
        cursor = self.connection.execute(
            """
            SELECT n.* FROM notes n
            JOIN notes_fts ON n.id = notes_fts.rowid
            WHERE notes_fts MATCH ?
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit)
        )
        return [self._row_to_note(row) for row in cursor.fetchall()]

    # ... autres méthodes ...
```

#### Niveau 3 - Use Cases et DI (Mois 1-2)
```python
# rekall/application/use_cases.py
"""
Use cases - orchestration de la logique métier.
"""
from dataclasses import dataclass
from typing import List, Optional

from rekall.domain.entities import Note
from rekall.domain.repositories import NoteRepository
from rekall.application.validators import NoteValidator


@dataclass
class CreateNoteUseCase:
    """Use case : Création d'une note."""

    repository: NoteRepository
    validator: NoteValidator

    def execute(self, content: str, **kwargs) -> Note:
        """
        Crée une nouvelle note après validation.

        Raises:
            ValidationError: Si le contenu est invalide
        """
        # Validation
        validated = self.validator.validate_content(content)

        # Création de l'entité
        note = Note(
            content=validated,
            **kwargs
        )

        # Persistance
        return self.repository.add(note)


@dataclass
class SearchNotesUseCase:
    """Use case : Recherche de notes."""

    repository: NoteRepository
    validator: NoteValidator

    def execute(self, query: str, limit: int = 50) -> List[Note]:
        """
        Recherche des notes correspondant à la requête.
        """
        # Validation et sanitization
        safe_query = self.validator.sanitize_search_query(query)

        # Recherche
        return self.repository.search(safe_query, limit)


# rekall/infrastructure/container.py
"""
Conteneur d'injection de dépendances.
"""
from dataclasses import dataclass
from pathlib import Path

from rekall.domain.repositories import NoteRepository
from rekall.infrastructure.sqlite_repository import SQLiteNoteRepository
from rekall.application.use_cases import CreateNoteUseCase, SearchNotesUseCase
from rekall.application.validators import NoteValidator


@dataclass
class Container:
    """Conteneur DI simple."""

    db_path: Path

    @property
    def note_repository(self) -> NoteRepository:
        return SQLiteNoteRepository(str(self.db_path))

    @property
    def note_validator(self) -> NoteValidator:
        return NoteValidator()

    @property
    def create_note(self) -> CreateNoteUseCase:
        return CreateNoteUseCase(
            repository=self.note_repository,
            validator=self.note_validator,
        )

    @property
    def search_notes(self) -> SearchNotesUseCase:
        return SearchNotesUseCase(
            repository=self.note_repository,
            validator=self.note_validator,
        )
```

#### Structure de Projet Cible
```
rekall/
├── domain/                 # Couche Domaine (0 dépendances)
│   ├── __init__.py
│   ├── entities.py         # Entités métier
│   └── repositories.py     # Interfaces abstraites
│
├── application/            # Couche Application
│   ├── __init__.py
│   ├── use_cases.py        # Cas d'utilisation
│   └── validators.py       # Validation métier
│
├── infrastructure/         # Couche Infrastructure
│   ├── __init__.py
│   ├── sqlite_repository.py
│   ├── crypto.py           # Chiffrement
│   └── container.py        # DI
│
├── interface/              # Couche Interface
│   ├── __init__.py
│   └── cli.py              # Commandes Typer
│
└── migrations/             # Migrations DB
    ├── __init__.py
    └── versions/
```

---

## 9. Duplication de Code et Principe DRY

### 🔴 Problématique Identifiée

> **[MOYENNE] Duplication de la sérialisation JSON**
> - Les exports JSON sont implémentés deux fois (`exporters.py` L90-109 et `archive.py` L91-145)
> - Même mapping champ-par-champ dupliqué
> - Risque d'écarts de format entre export simple et archive compressée
> - Fichiers concernés: `rekall/exporters.py`, `rekall/archive.py`

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [CodeSignal - Applying DRY Principle in Python](https://codesignal.com/learn/courses/applying-clean-code-principles-in-python/lessons/applying-the-dry-principle-in-python) | **Cours structuré** avec exemples concrets d'extraction de fonctions. Techniques directement applicables. |
| [Earth Lab - DRY Code and Modularity](https://earthdatascience.org/courses/intro-to-earth-data-science/write-efficient-python-code/intro-to-clean-code/dry-modular-code/) | **Guide académique** avec 3 stratégies clés : fonctions, boucles, conditionnels. Approche pédagogique claire. |
| [Pydantic Serialization Docs](https://docs.pydantic.dev/latest/concepts/serialization/) | **Documentation officielle** pour les patterns `model_dump()` et sérialisation JSON. Référence authoritative. |
| [Tom Augspurger - Serializing Dataclasses](https://tomaugspurger.net/posts/serializing-dataclasses/) | **Article technique** comparant `asdict()` vs custom serializers. Recommandations pratiques pour dataclasses. |
| [Hrekov - Python Data Serialization 2025](https://hrekov.com/blog/python-data-serialization-2025) | **Panorama 2025** des alternatives (msgspec, cattrs, pyserde). Contexte sur l'évolution de l'écosystème. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [Wikipedia - DRY Principle](https://en.wikipedia.org/wiki/Don't_repeat_yourself) | **Trop généraliste**, définition sans exemples de code Python. |
| [Gazar - Embracing DRY Principle](https://gazar.dev/clean-code/embracing-the-dry-principle-in-programming) | **Exemples multi-langages**, pas de focus Python spécifique. |
| [leehanchung - Pydantic Performance Spaghetti](https://leehanchung.github.io/blogs/2025/07/03/pydantic-is-all-you-need-for-performance-spaghetti/) | **Article critique** utile pour le contexte mais anti-Pydantic extrême. Bias visible. |
| [PixelFreeStudio - DRY Best Practices](https://blog.pixelfreestudio.com/best-practices-for-writing-dry-dont-repeat-yourself-code/) | **Contenu générique**, pas d'exemples Python concrets. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Single Source of Truth** : Une seule fonction de sérialisation pour un type de données
2. **Séparer validation et sérialisation** : Pydantic aux frontières, dataclass en interne
3. **Module utilitaire dédié** : Centraliser les conversions dans un fichier `serializers.py`
4. **Tests unitaires** : Chaque fonction de conversion doit avoir ses tests
5. **Documentation du schéma** : Documenter le format JSON attendu

### 📈 Remédiation Graduelle

#### Niveau 1 - Fonction Partagée Basique (30 min) ✅ ESSENTIEL
```python
# rekall/utils.py (ou ajouter à un fichier existant)
from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

def entry_to_dict(entry) -> Dict[str, Any]:
    """
    Convertit une Entry en dictionnaire sérialisable JSON.

    Source unique de vérité pour la sérialisation des entrées.
    Utilisée par exporters.py ET archive.py.
    """
    data = asdict(entry)

    # Conversion des types non-JSON
    for key, value in data.items():
        if isinstance(value, datetime):
            data[key] = value.isoformat()

    return data


def dict_to_entry(data: Dict[str, Any], entry_class):
    """
    Reconstruit une Entry depuis un dictionnaire JSON.

    Source unique de vérité pour la désérialisation.
    """
    # Conversion des dates ISO -> datetime
    for key in ['created_at', 'updated_at', 'recalled_at']:
        if key in data and isinstance(data[key], str):
            data[key] = datetime.fromisoformat(data[key])

    return entry_class(**data)
```

```python
# rekall/exporters.py - Modification
from rekall.utils import entry_to_dict

def export_to_json(entries, output_path):
    data = [entry_to_dict(e) for e in entries]
    # ... reste du code
```

```python
# rekall/archive.py - Modification
from rekall.utils import entry_to_dict, dict_to_entry

def create_archive(entries, output_path):
    data = [entry_to_dict(e) for e in entries]
    # ... reste du code
```

#### Niveau 2 - Module Serializers Dédié (1h) 👍 RECOMMANDÉ
```python
# rekall/serializers.py
"""
Module de sérialisation centralisé.

Toute conversion Entry <-> dict/JSON passe par ce module.
Évite la duplication et garantit la cohérence des formats.
"""
from dataclasses import asdict, fields
from datetime import datetime
from typing import Any, Dict, List, Type, TypeVar
import json

T = TypeVar('T')

class EntrySerializer:
    """Serializer pour les objets Entry."""

    # Champs à traiter comme des dates
    DATE_FIELDS = {'created_at', 'updated_at', 'recalled_at'}

    # Champs sensibles à masquer dans certains exports
    SENSITIVE_FIELDS = {'api_key', 'password', 'token'}

    @classmethod
    def to_dict(cls, entry, mask_sensitive: bool = False) -> Dict[str, Any]:
        """Convertit une Entry en dict."""
        data = asdict(entry)

        for key, value in list(data.items()):
            # Dates -> ISO string
            if isinstance(value, datetime):
                data[key] = value.isoformat()

            # Masquage optionnel des champs sensibles
            if mask_sensitive and key in cls.SENSITIVE_FIELDS:
                data[key] = "***MASKED***"

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], entry_class: Type[T]) -> T:
        """Reconstruit une Entry depuis un dict."""
        # Copie pour ne pas modifier l'original
        data = data.copy()

        # Conversion des dates
        for key in cls.DATE_FIELDS:
            if key in data and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])

        # Ne garder que les champs valides pour la dataclass
        valid_fields = {f.name for f in fields(entry_class)}
        data = {k: v for k, v in data.items() if k in valid_fields}

        return entry_class(**data)

    @classmethod
    def to_json(cls, entries: List, indent: int = 2) -> str:
        """Sérialise une liste d'entries en JSON."""
        data = [cls.to_dict(e) for e in entries]
        return json.dumps(data, indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str, entry_class: Type[T]) -> List[T]:
        """Désérialise du JSON en liste d'entries."""
        data = json.loads(json_str)
        return [cls.from_dict(d, entry_class) for d in data]
```

#### Niveau 3 - Pydantic Models avec Serdes (Refactoring majeur) ⚠️ OVERKILL
```python
# rekall/models.py - Remplacement complet par Pydantic
# ⚠️ Nécessite de modifier TOUS les usages de Entry
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Entry(BaseModel):
    """Entry avec sérialisation Pydantic native."""

    id: Optional[int] = None
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat()
        }
    }

# Usage:
# entry.model_dump()  # -> dict
# entry.model_dump_json()  # -> JSON string
# Entry.model_validate(data)  # -> Entry from dict
```

**Pourquoi c'est overkill :** Le schéma `Entry` est stable depuis longtemps. Migrer vers Pydantic nécessite de modifier tous les fichiers qui créent/manipulent des Entry. Pour un gain minime sur un schéma qui ne change pas, c'est du refactoring pour le plaisir du refactoring.

---

## 10. CLI Monolithique et Modularisation

### 🔴 Problématique Identifiée

> **[MOYENNE] CLI concentrant ~2.7k lignes**
> - Configuration, accès base, TUI, intégrations et commandes métier mélangés
> - Navigation et découplage difficiles
> - Fichier concerné: `rekall/cli.py`

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [PyTutorial - Typer Subcommands and Modular CLI](https://pytutorial.com/python-typer-subcommands-and-modular-cli/) | **Guide pratique Typer** avec structure de projet recommandée et `add_typer()` pour grouper les commandes. |
| [Real Python - Click Extensible CLI](https://realpython.com/python-click/) | **Tutoriel approfondi** sur les nested commands et l'architecture modulaire Click (base de Typer). |
| [Better Stack - Click Explained](https://betterstack.com/community/guides/scaling-python/click-explained/) | **Guide complet** avec patterns de composition et lazy loading pour grandes CLIs. |
| [Hitchhiker's Guide - Project Structure](https://docs.python-guide.org/writing/structure/) | **Référence Python** sur la structuration de projets. Principes applicables aux CLIs. |
| [Qodo - 8 Python Refactoring Techniques](https://www.qodo.ai/blog/8-python-code-refactoring-techniques-tools-practices/) | **Guide refactoring** avec outils (Rope, PyCharm) et best practices pour extraire du code. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [CodeRivers - Mastering Typer](https://coderivers.org/blog/typer-python/) | **Contenu basique** répétant la documentation officielle sans valeur ajoutée. |
| [djamware - Build CLI with Typer](https://www.djamware.com/post/692d8641e6e2a42c2b84c3c1/build-powerful-commandline-tools-in-python-using-typer) | **Tutoriel débutant**, pas de patterns avancés pour grandes CLIs. |
| [jsschools - Python CLI Development](https://jsschools.com/python/python-cli-development-top-libraries-for-building/) | **Comparatif superficiel** de bibliothèques sans profondeur technique. |
| [Khan Academy - Great Python Refactor](https://blog.khanacademy.org/the-great-python-refactor-of-2017-and-also-2018/) | **Contexte intéressant** mais spécifique à leur codebase, peu applicable directement. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Séparation des concerns** : Code CLI séparé de la logique métier
2. **Sous-commandes modulaires** : Un fichier par groupe de commandes liées
3. **Lazy loading** : Charger les dépendances lourdes uniquement si nécessaire
4. **Configuration centralisée** : Un module dédié pour init DB/config
5. **Tests isolés** : Chaque module de commandes testable indépendamment

### 📈 Remédiation Graduelle

#### Niveau 1 - Extraction des Helpers (1h) 👍 RECOMMANDÉ
```python
# rekall/config.py (nouveau fichier)
"""
Configuration et initialisation centralisées.

Extrait de cli.py pour réduire le bruit.
"""
from pathlib import Path
from typing import Optional
import os

# Constantes de configuration
DEFAULT_DB_NAME = "rekall.db"
DEFAULT_CONFIG_DIR = Path.home() / ".rekall"

_db_connection = None
_config = None


def get_config_dir() -> Path:
    """Retourne le répertoire de configuration."""
    config_dir = Path(os.environ.get("REKALL_CONFIG_DIR", DEFAULT_CONFIG_DIR))
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_db_path() -> Path:
    """Retourne le chemin de la base de données."""
    return get_config_dir() / DEFAULT_DB_NAME


def get_db_connection():
    """Retourne une connexion à la base de données (singleton)."""
    global _db_connection
    if _db_connection is None:
        import sqlite3
        _db_connection = sqlite3.connect(get_db_path())
        _db_connection.row_factory = sqlite3.Row
    return _db_connection


def init_db():
    """Initialise le schéma de la base de données."""
    conn = get_db_connection()
    # ... migrations et création de tables
    return conn
```

```python
# rekall/cli.py - Simplification
from rekall.config import get_db_connection, init_db, get_config_dir

# Au lieu de 200 lignes d'init, maintenant:
app = typer.Typer()

@app.callback()
def main():
    """Rekall - Base de connaissances personnelle."""
    init_db()

# ... commandes uniquement
```

#### Niveau 2 - Sous-commandes Modulaires (2-3h) 🟡 OPTIONNEL
```
rekall/
├── cli.py              # App principale + callback
├── config.py           # Configuration (niveau 1)
├── commands/
│   ├── __init__.py
│   ├── entries.py      # add, edit, delete, show
│   ├── search.py       # search, recall
│   ├── export.py       # export, archive, restore
│   └── integrations.py # install-*, configure-*
```

```python
# rekall/commands/export.py
import typer
from rekall.config import get_db_connection
from rekall.serializers import EntrySerializer

app = typer.Typer(help="Commandes d'export et d'archivage")

@app.command()
def json(output: Path, mask_pii: bool = False):
    """Exporte les entrées en JSON."""
    # ...

@app.command()
def archive(output: Path):
    """Crée une archive compressée."""
    # ...

@app.command()
def restore(archive_path: Path):
    """Restaure depuis une archive."""
    # ...
```

```python
# rekall/cli.py - App principale
import typer
from rekall.commands import entries, search, export, integrations

app = typer.Typer()

# Enregistrement des sous-commandes
app.add_typer(entries.app, name="entry")
app.add_typer(search.app, name="search")
app.add_typer(export.app, name="export")
app.add_typer(integrations.app, name="integration")

# Commandes de niveau racine (raccourcis)
@app.command()
def add(content: str):
    """Raccourci pour 'entry add'."""
    entries.add(content)
```

#### Niveau 3 - Architecture Plugins Typer (Demi-journée+) ⚠️ OVERKILL
```python
# rekall/plugin_loader.py
# ⚠️ Over-engineering pour une CLI de ~15 commandes
import importlib
import pkgutil
from pathlib import Path

def discover_commands(package_path: str = "rekall.commands"):
    """Découvre et charge automatiquement les modules de commandes."""
    package = importlib.import_module(package_path)

    for _, name, _ in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{package_path}.{name}")
        if hasattr(module, 'app'):
            yield name, module.app


# Dans cli.py:
for name, sub_app in discover_commands():
    app.add_typer(sub_app, name=name)
```

**Pourquoi c'est overkill :** Rekall a ~15 commandes. Un système de découverte automatique de plugins est utile quand tu as 50+ commandes ou des plugins tiers. Pour 15 commandes, `add_typer()` explicite est plus clair et debuggable.

---

## 11. Code Mort et Intégrations Non Raccordées

### 🔴 Problématique Identifiée

> **[MOYENNE] Code inactif / non raccordé**
> - Installateurs d'intégrations (Copilot, Windsurf, Cline, Aider, Continue) définis mais inaccessibles
> - Aucun appel référencé hors du module `integrations/__init__.py`
> - Capacités présentes mais non exposées depuis la CLI/TUI
> - Fichier concerné: `rekall/integrations/__init__.py` (L442-519)

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [Vulture (GitHub)](https://github.com/jendrikseipp/vulture) | **Outil de référence** pour la détection de code mort Python. Analyse AST, confidence levels, whitelists. Maintenu activement. |
| [deadcode (PyPI)](https://pypi.org/project/deadcode/) | **Alternative moderne** avec plus de règles que Vulture, option `--fix` pour suppression automatique, intégration avec ruff. |
| [Adam Johnson - Django Vulture](https://adamj.eu/tech/2023/07/12/django-clean-up-unused-code-vulture/) | **Guide pratique** avec workflow complet : exécution, whitelisting, intégration CI. Applicable au-delà de Django. |
| [OpenStack Stevedore](https://docs.openstack.org/stevedore/latest/user/essays/pycon2013.html) | **Référence** pour les architectures de plugins Python avec entry points. Patterns éprouvés en production. |
| [Pluggy (pytest)](https://medium.com/@garzia.luke/developing-plugin-architecture-with-pluggy-8eb7bdba3303) | **Framework de plugins** utilisé par pytest. Léger, bien documenté, adapté aux hooks d'extension. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [witve.com - Mastering Vulture](https://witve.com/codes/mastering-vulture-the-ultimate-guide-to-finding-dead-code-in-python/) | **Site de qualité douteuse**, contenu probablement généré, pas de valeur technique ajoutée. |
| [Medium - Dead code detection](https://medium.com/@kinjaldave299/dead-code-detection-in-python-6bbec093b86b) | **Article basique** répétant la doc Vulture sans insights. |
| [rj722 - Coverage for dead code](https://rj722.github.io/articles/18/why-use-coverage-to-find-which-python-code-is-run) | **Approche différente** (runtime vs static). Utile mais complémentaire, pas principal. |
| [vinnie.work - Python Plugin Pattern](https://www.vinnie.work/blog/2021-02-16-python-plugin-pattern) | **Article de 2021**, patterns moins modernes que Stevedore/Pluggy. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Détection automatique** : Vulture/deadcode en CI pour détecter le code mort
2. **Documenter l'intention** : Si le code est intentionnellement non utilisé (API future), le marquer
3. **Registre explicite** : Les extensions doivent être enregistrées et accessibles
4. **Supprimer ou exposer** : Pas de code "zombie" - soit il sert, soit il disparaît
5. **Whitelists versionnées** : Maintenir les exceptions Vulture dans le repo

### 📈 Remédiation Graduelle

#### Niveau 1 - Vulture en CI (15 min) ✅ ESSENTIEL
```yaml
# .github/workflows/lint.yml (ajout)
- name: Check dead code
  run: |
    pip install vulture
    vulture rekall/ --min-confidence 80
```

```toml
# pyproject.toml
[tool.vulture]
min_confidence = 80
paths = ["rekall"]
exclude = ["tests/", "*.pyi"]
```

```python
# vulture_whitelist.py
# Code intentionnellement non utilisé localement mais exposé via API
from rekall.integrations import (
    install_copilot,    # Installateur pour VS Code Copilot
    install_windsurf,   # Installateur pour Windsurf IDE
    install_cline,      # Installateur pour Cline
    install_aider,      # Installateur pour Aider
    install_continue,   # Installateur pour Continue
)

# Ces fonctions sont dans le registre INTEGRATIONS
# et seront exposées via CLI dans une future version
```

#### Niveau 2 - Exposer les Intégrations (1-2h) 👍 RECOMMANDÉ
```python
# rekall/cli.py - Ajout de commandes pour les intégrations

from rekall.integrations import INTEGRATIONS

@app.command("list-integrations")
def list_integrations():
    """Liste les intégrations disponibles."""
    from rich.table import Table
    from rich.console import Console

    console = Console()
    table = Table(title="Intégrations Disponibles")
    table.add_column("Nom", style="cyan")
    table.add_column("Description")
    table.add_column("Status")

    for name, integration in INTEGRATIONS.items():
        status = "✅ Installé" if integration.is_installed() else "❌ Non installé"
        table.add_row(name, integration.description, status)

    console.print(table)


@app.command("install-integration")
def install_integration(
    name: str = typer.Argument(..., help="Nom de l'intégration")
):
    """Installe une intégration IDE/agent."""
    if name not in INTEGRATIONS:
        typer.echo(f"❌ Intégration inconnue: {name}")
        typer.echo(f"Disponibles: {', '.join(INTEGRATIONS.keys())}")
        raise typer.Exit(1)

    integration = INTEGRATIONS[name]
    typer.echo(f"📦 Installation de {name}...")

    try:
        integration.install()
        typer.echo(f"✅ {name} installé avec succès!")
    except Exception as e:
        typer.echo(f"❌ Erreur: {e}")
        raise typer.Exit(1)
```

```python
# rekall/integrations/__init__.py - Amélioration du registre
from dataclasses import dataclass
from typing import Callable, Dict, Optional
from pathlib import Path

@dataclass
class Integration:
    """Définition d'une intégration."""
    name: str
    description: str
    install_fn: Callable[[], None]
    check_fn: Callable[[], bool]
    config_path: Optional[Path] = None

    def install(self):
        """Installe l'intégration."""
        self.install_fn()

    def is_installed(self) -> bool:
        """Vérifie si l'intégration est installée."""
        return self.check_fn()


# Registre unifié
INTEGRATIONS: Dict[str, Integration] = {
    "copilot": Integration(
        name="copilot",
        description="GitHub Copilot pour VS Code",
        install_fn=_install_copilot,
        check_fn=_check_copilot_installed,
        config_path=Path.home() / ".config" / "github-copilot",
    ),
    "windsurf": Integration(
        name="windsurf",
        description="Windsurf IDE",
        install_fn=_install_windsurf,
        check_fn=_check_windsurf_installed,
    ),
    # ... autres intégrations
}
```

#### Niveau 3 - Système de Plugins Dynamique (Demi-journée) 🟡 OPTIONNEL
```python
# rekall/plugins/__init__.py
# Utiliser stevedore pour les plugins tiers
from stevedore import ExtensionManager

def load_integration_plugins():
    """Charge les plugins d'intégration via entry points."""
    mgr = ExtensionManager(
        namespace='rekall.integrations',
        invoke_on_load=False,
    )

    for ext in mgr:
        INTEGRATIONS[ext.name] = ext.plugin


# setup.py / pyproject.toml du plugin tiers:
# [project.entry-points."rekall.integrations"]
# my_ide = "rekall_myide:MyIDEIntegration"
```

**Quand c'est utile :** Si tu veux permettre à d'autres développeurs de créer des plugins d'intégration installables via pip. Pour usage personnel, le registre statique (Niveau 2) suffit.

### Points Positifs Identifiés

L'audit a également relevé des éléments positifs à préserver :

1. **Registre unifié `INTEGRATIONS`** : Le pattern de registre est déjà en place, il suffit de l'exposer via la CLI.

2. **Regex pour champs sensibles** : Les fonctions d'export balisent déjà les champs sensibles, facilitant l'extension future des contrôles de fuite.

```python
# Déjà présent dans exporters.py L11-37 - À conserver et étendre
SENSITIVE_PATTERNS = {
    "api_key": r"[a-zA-Z0-9]{32,}",
    "password": r"password\s*[:=]\s*\S+",
    # ...
}
```

---

## 12. Observabilité et Gestion d'Erreurs

### 🔴 Problématique Identifiée

> **[MOYENNE] Exceptions silencieuses masquant les défaillances**
> - Plusieurs blocs `except Exception` sans journalisation ni remontée
> - Erreurs de migration/config invisibles pour l'utilisateur
> - Fichiers concernés: `cli.py:172-188`, `config.py:105-123`, `paths.py:247-280`

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [PEP 760 - No More Bare Excepts](https://peps.python.org/pep-0760/) | **Référence officielle Python** proposant l'interdiction des `except:` nus. Confirme que c'est un anti-pattern reconnu. |
| [Qodo - 6 Best Practices Python Exceptions](https://www.qodo.ai/blog/6-best-practices-for-python-exception-handling/) | **Guide complet 2025** avec exemples concrets : exceptions spécifiques, try blocks courts, custom exceptions. |
| [Real Python - Diabolical Antipattern](https://realpython.com/the-most-diabolical-python-antipattern/) | **Article de référence** expliquant pourquoi `except Exception` silencieux est le pire antipattern Python. |
| [Typer - Exceptions](https://typer.tiangolo.com/tutorial/exceptions/) | **Documentation officielle Typer** pour la gestion d'erreurs en CLI avec Rich et codes de sortie. |
| [BetterStack - Loguru Guide](https://betterstack.com/community/guides/logging/loguru/) | **Guide complet Loguru** avec backtrace enrichi, exception logging, configuration production. |
| [Structlog - Logging Best Practices](https://www.structlog.org/en/stable/logging-best-practices.html) | **Documentation officielle structlog** avec patterns pour structured logging et JSON output. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [Eduonix - Error Handling](https://blog.eduonix.com/2025/05/error-handling-in-python-master-try-except-and-best-practices/) | **Article généraliste** sans insights spécifiques pour CLI ou logging avancé. |
| [Medium - Divyansh Patel](https://medium.com/@divyansh9144/effective-error-handling-in-python-navigating-best-practices-and-common-pitfalls-c8f1680611c5) | **Contenu basique** répétant la doc Python sans valeur ajoutée. |
| [Trajectory Hub - Python Try](https://trajdash.usc.edu/python-try) | **Site académique** peu adapté au contexte professionnel, exemples trop simples. |
| [Jerry NSH - Stop Using Exceptions](https://jerrynsh.com/stop-using-exceptions-like-this-in-python/) | **Article blog personnel**, certains conseils discutables (pas de sources). |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Exceptions spécifiques** : Capturer `FileNotFoundError`, `TOMLDecodeError`, `sqlite3.Error` plutôt que `Exception`
2. **Logging systématique** : `logger.exception()` pour traceback complet, `logger.error()` pour messages simples
3. **Feedback utilisateur** : Messages Rich/Typer avec suggestions de remédiation
4. **Try blocks courts** : Minimiser le code dans le try pour identifier précisément l'origine
5. **Ne jamais silencer** : Si on catch, on log ou on remonte (re-raise)

### 📈 Remédiation Graduelle

#### Niveau 1 - Exceptions Ciblées + Logging (30 min) ✅ ESSENTIEL
```python
# AVANT (cli.py L172-188) - Mauvais
try:
    schema_info = get_schema()
except Exception:
    schema_info = {}  # Silencieux !

# APRÈS - Bon
import logging
logger = logging.getLogger(__name__)

try:
    schema_info = get_schema()
except sqlite3.Error as e:
    logger.exception("Erreur lecture schéma DB")
    schema_info = {}
except FileNotFoundError as e:
    logger.warning("Base de données non trouvée: %s", e)
    schema_info = {}
```

```python
# AVANT (config.py L105-123) - Mauvais
try:
    with open(config_path) as f:
        return tomllib.loads(f.read())
except Exception:
    return {}  # Config corrompue = silencieux !

# APRÈS - Bon
try:
    with open(config_path) as f:
        return tomllib.loads(f.read())
except FileNotFoundError:
    logger.info("Config non trouvée, utilisation des défauts")
    return {}
except tomllib.TOMLDecodeError as e:
    logger.error("Config TOML invalide: %s", e)
    typer.echo(f"⚠️  Config corrompue: {config_path}", err=True)
    typer.echo("   Suggestion: vérifiez la syntaxe ou supprimez le fichier", err=True)
    return {}
```

#### Niveau 2 - Rich/Typer Feedback (1h) 👍 RECOMMANDÉ
```python
from rich.console import Console
from rich.panel import Panel

console = Console(stderr=True)

def handle_config_error(path: Path, error: Exception) -> dict:
    """Gère les erreurs de config avec feedback utilisateur."""
    if isinstance(error, FileNotFoundError):
        return {}  # Normal au premier lancement

    if isinstance(error, tomllib.TOMLDecodeError):
        console.print(Panel(
            f"[red]Erreur de syntaxe TOML[/red]\n\n"
            f"Fichier: {path}\n"
            f"Erreur: {error}\n\n"
            f"[yellow]Suggestions:[/yellow]\n"
            f"• Vérifiez les guillemets et crochets\n"
            f"• Utilisez un validateur TOML en ligne\n"
            f"• Supprimez le fichier pour régénérer les défauts",
            title="⚠️  Configuration invalide",
            border_style="red"
        ))
        return {}

    # Erreur inattendue - on log et on propage
    logger.exception("Erreur config inattendue")
    raise
```

#### Niveau 3 - Structured Logging avec Loguru (2h) 🟡 OPTIONNEL
```python
from loguru import logger
import sys

# Configuration Loguru pour CLI
logger.remove()  # Supprimer handler par défaut
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="WARNING",  # Seulement warnings+ en CLI
    backtrace=True,
    diagnose=False,  # Désactiver en prod (sécurité)
)

# Log fichier pour debug
logger.add(
    "~/.rekall/debug.log",
    rotation="1 MB",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{line} | {message}",
)

# Usage
try:
    config = load_config()
except Exception:
    logger.exception("Échec chargement config")
    # Loguru capture automatiquement le traceback + variables locales
```

**Pourquoi c'est optionnel :** Pour une CLI locale, `logging` stdlib + Rich suffit. Loguru est utile si tu as besoin d'agréger des logs ou de debug des problèmes complexes.

---

## 13. Persistance de Configuration (Intégrité et Concurrence)

### 🔴 Problématique Identifiée

> **[MOYENNE] Écriture config non atomique et non sécurisée**
> - Écriture manuelle sans lib TOML (risque d'échappement)
> - Pas d'écriture atomique (crash = fichier partiel)
> - Retourne booléen silencieux sans feedback
> - Fichier concerné: `config.py:125-167`

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [Real Python - Python and TOML](https://realpython.com/python-toml/) | **Guide complet 2025** sur tomllib/tomli/tomli-w avec patterns de lecture/écriture. |
| [tomli-w (PyPI)](https://pypi.org/project/tomli-w/) | **Documentation officielle** du compagnon d'écriture pour tomllib, API simple et TOML 1.0 compliant. |
| [atomicwrites (GitHub)](https://github.com/untitaker/python-atomicwrites) | **Référence pour atomic writes** - bien que maintenance inactive, le pattern reste valide. |
| [gocept - Reliable File Updates](https://blog.gocept.com/2013/07/15/reliable-file-updates-with-python/) | **Article technique détaillé** sur le pattern write-tempfile-fsync-rename. Explique POURQUOI chaque étape est nécessaire. |
| [Python os.fsync (zetcode)](https://zetcode.com/python/os-fsync/) | **Guide pratique fsync** avec exemples et explications sur les buffers OS. |
| [Python.org - Atomic Write Discussion](https://discuss.python.org/t/adding-atomicwrite-in-stdlib/11899) | **Discussion officielle** sur l'ajout d'atomic write en stdlib, montre que c'est un besoin reconnu. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [atomicwrites docs](https://python-atomicwrites.readthedocs.io/en/latest/) | **Maintenance inactive** depuis 2+ ans. Le pattern est bon mais la lib elle-même est à éviter. |
| [Snyk - atomicwrites health](https://snyk.io/advisor/python/atomicwrites) | **Confirme le problème** : projet considéré discontinued. |
| [ActiveState Recipe 579097](https://code.activestate.com/recipes/579097-safely-and-atomically-write-to-a-file/) | **Code daté (2016)**, Python 2 compatible, pas les meilleures pratiques actuelles. |
| [bugs.python.org/issue8828](https://bugs.python.org/issue8828) | **Discussion historique** (2010), dépassée par `os.replace()` en Python 3.3+. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Utiliser une lib TOML** : `tomli-w` pour écriture, `tomllib` (3.11+) ou `tomli` pour lecture
2. **Atomic write pattern** : tempfile → write → fsync → rename
3. **os.replace()** : Atomique et cross-platform depuis Python 3.3
4. **Feedback utilisateur** : Ne pas retourner un booléen silencieux, lever une exception ou logger
5. **Validation avant écriture** : Vérifier que le TOML généré est valide

### 📈 Remédiation Graduelle

#### Niveau 1 - Lib TOML + Atomic Write Basique (30 min) ✅ ESSENTIEL
```python
# AVANT (config.py L125-167) - Mauvais
def save_config(config: dict, path: Path) -> bool:
    try:
        with open(path, "w") as f:
            f.write("[general]\n")
            f.write(f'db_path = "{config["db_path"]}"\n')  # Pas d'échappement !
        return True
    except Exception:
        return False  # Silencieux !

# APRÈS - Bon
import tomli_w
import tempfile
import os

def save_config(config: dict, path: Path) -> None:
    """Sauvegarde la config de manière atomique.

    Raises:
        OSError: Si l'écriture échoue
        TypeError: Si la config contient des types non sérialisables
    """
    # Sérialiser via tomli-w (gère l'échappement)
    toml_content = tomli_w.dumps(config)

    # Écriture atomique : tempfile + rename
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Créer fichier temp dans le même répertoire (même filesystem)
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=".config_",
        suffix=".tmp"
    )
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(toml_content)
        # Atomic rename (cross-platform depuis Python 3.3)
        os.replace(tmp_path, path)
    except:
        # Cleanup en cas d'erreur
        os.unlink(tmp_path)
        raise
```

#### Niveau 2 - fsync + Feedback Utilisateur (1h) 👍 RECOMMANDÉ
```python
import tomli_w
import tempfile
import os
from pathlib import Path

def save_config_atomic(config: dict, path: Path) -> None:
    """Sauvegarde la config avec garanties de durabilité.

    Pattern: write → flush → fsync → rename → fsync dir
    Garantit que les données sont sur disque même en cas de crash.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Sérialiser via tomli-w
    try:
        toml_content = tomli_w.dumps(config)
    except TypeError as e:
        raise ValueError(f"Config non sérialisable: {e}") from e

    # Créer fichier temp dans le même répertoire
    fd, tmp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=".config_",
        suffix=".tmp"
    )
    tmp_path = Path(tmp_path)

    try:
        # Écrire et sync le contenu
        with os.fdopen(fd, 'w') as f:
            f.write(toml_content)
            f.flush()
            os.fsync(f.fileno())

        # Atomic rename
        os.replace(tmp_path, path)

        # Sync le répertoire parent (pour que le rename soit durable)
        dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)

    except Exception as e:
        # Cleanup
        tmp_path.unlink(missing_ok=True)
        raise OSError(f"Échec sauvegarde config: {e}") from e


# Usage avec feedback Typer
def cmd_set_config(key: str, value: str):
    """Commande CLI pour modifier la config."""
    try:
        config = load_config()
        config[key] = value
        save_config_atomic(config, get_config_path())
        typer.echo(f"✅ Config mise à jour: {key}={value}")
    except OSError as e:
        typer.echo(f"❌ Erreur: {e}", err=True)
        typer.echo("   Vérifiez les permissions et l'espace disque", err=True)
        raise typer.Exit(1)
```

#### Niveau 3 - File Locking (Demi-journée) ⚠️ OVERKILL
```python
import fcntl  # Unix only
from contextlib import contextmanager

@contextmanager
def locked_config(path: Path, mode: str = 'r'):
    """Context manager avec verrou exclusif sur la config.

    ATTENTION: Complexité élevée, problèmes potentiels :
    - fcntl ne fonctionne pas sur NFS/SMB
    - Pas portable Windows
    - Deadlocks possibles si mal utilisé
    """
    path = Path(path)
    lock_path = path.with_suffix('.lock')

    with open(lock_path, 'w') as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            with open(path, mode) as f:
                yield f
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

# Ou avec portalocker (cross-platform mais dépendance supplémentaire)
# import portalocker
# with portalocker.Lock(path, 'w', timeout=5) as f:
#     f.write(content)
```

**Pourquoi c'est overkill :** Rekall est une CLI mono-utilisateur. Les accès concurrents au même fichier config sont quasi-impossibles. Le pattern atomic write (Niveau 2) protège déjà contre les corruptions par crash.

---

## 14. Durcissement des Archives et Imports

### 🔴 Problématique Identifiée

> **[MOYENNE] Chargement d'archives sans limites ni validation**
> - Lecture ZIP/JSON sans limite de taille → risque OOM
> - Pas de vérification du ratio de compression → vulnérable aux zip bombs
> - Aucune validation des champs JSON (taille contenu, nombre de tags)
> - Fichier concerné: `archive.py:250-319`

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [CVE-2024-0450 (Snyk)](https://security.snyk.io/vuln/SNYK-UNMANAGED-PYTHON-7924823) | **CVE récent (2024)** sur zipfile Python, montre que les zip bombs restent un vecteur d'attaque actif. |
| [Python zipfile docs](https://docs.python.org/3/library/zipfile.html) | **Documentation officielle** avec avertissement sur les decompression bombs. |
| [AWS CodeGuru - Zip Bomb](https://docs.aws.amazon.com/codeguru/detector-library/python/zip-bomb-attack/) | **Recommandations AWS** pour la détection et mitigation des zip bombs en Python. |
| [sunzip (GitHub)](https://github.com/twbgc/sunzip) | **Outil de référence** pour extraction sécurisée, documente les stratégies de défense (ratio, nested zips, limits). |
| [Pydantic - Field Constraints](https://docs.pydantic.dev/latest/concepts/fields/) | **Documentation officielle** pour les contraintes `max_length`, `min_items`, `max_items` sur les champs. |
| [bugs.python.org/issue36462](https://bugs.python.org/issue36462) | **CVE-2019-9674** - Discussion historique montrant que CPython ne corrigera pas le problème côté lib. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [bugs.python.org/issue39341](https://bugs.python.org/issue39341) | **Issue fermée** avec conclusion "won't fix", pas de solution proposée côté Python. |
| [Pillow #515](https://github.com/python-pillow/Pillow/issues/515) | **Spécifique aux images** (decompression bomb pour images), pas applicable aux ZIP génériques. |
| [pypi/warehouse #10504](https://github.com/pypi/warehouse/issues/10504) | **Contexte PyPI** spécifique, solution trop complexe pour notre cas. |
| [python-security.readthedocs.io](https://python-security.readthedocs.io/security.html) | **Page générale** sans détails spécifiques sur les zip bombs. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Limite de taille fichier** : Vérifier `stat.st_size` avant ouverture
2. **Limite de taille décompressée** : Calculer taille totale avant extraction
3. **Ratio de compression** : Rejeter si ratio > 10-100x (zip bombs typiques = 1000x+)
4. **Validation JSON** : Pydantic avec contraintes `max_length`, `max_items`
5. **Timeout/quotas** : Pour sources non fiables, limiter ressources du processus

### 📈 Remédiation Graduelle

#### Niveau 1 - Limites de Taille Basiques (30 min) ✅ ESSENTIEL
```python
import os
from pathlib import Path
from zipfile import ZipFile

# Constantes de sécurité
MAX_ARCHIVE_SIZE = 50 * 1024 * 1024  # 50 Mo max pour le fichier .rekall
MAX_DECOMPRESSED_SIZE = 200 * 1024 * 1024  # 200 Mo max décompressé
MAX_ENTRIES = 10000  # Nombre max d'entrées dans l'archive

class ArchiveSecurityError(Exception):
    """Erreur de sécurité lors du chargement d'archive."""
    pass

def load_archive_safe(path: Path) -> dict:
    """Charge une archive .rekall avec vérifications de sécurité."""
    path = Path(path)

    # 1. Vérifier la taille du fichier avant ouverture
    file_size = path.stat().st_size
    if file_size > MAX_ARCHIVE_SIZE:
        raise ArchiveSecurityError(
            f"Archive trop volumineuse: {file_size / 1024 / 1024:.1f} Mo "
            f"(max: {MAX_ARCHIVE_SIZE / 1024 / 1024:.0f} Mo)"
        )

    with ZipFile(path, 'r') as zf:
        # 2. Vérifier le nombre d'entrées
        if len(zf.namelist()) > MAX_ENTRIES:
            raise ArchiveSecurityError(
                f"Trop d'entrées: {len(zf.namelist())} (max: {MAX_ENTRIES})"
            )

        # 3. Vérifier la taille totale décompressée
        total_size = sum(info.file_size for info in zf.infolist())
        if total_size > MAX_DECOMPRESSED_SIZE:
            raise ArchiveSecurityError(
                f"Taille décompressée excessive: {total_size / 1024 / 1024:.1f} Mo "
                f"(max: {MAX_DECOMPRESSED_SIZE / 1024 / 1024:.0f} Mo)"
            )

        # 4. Lire les données
        data = zf.read('data.json')
        return json.loads(data)
```

#### Niveau 2 - Validation Champs + Ratio Compression (1-2h) 👍 RECOMMANDÉ
```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import json

# Constantes de validation
MAX_CONTENT_SIZE = 1 * 1024 * 1024  # 1 Mo max par entrée
MAX_TAGS = 50  # 50 tags max par entrée
MAX_TAG_LENGTH = 100  # 100 chars max par tag
MAX_COMPRESSION_RATIO = 100  # Ratio max (100:1)

class EntryModel(BaseModel):
    """Modèle Pydantic pour valider les entrées importées."""
    id: str = Field(max_length=36)  # UUID
    title: str = Field(max_length=500)
    content: str = Field(max_length=MAX_CONTENT_SIZE)
    tags: List[str] = Field(default_factory=list, max_length=MAX_TAGS)
    created_at: str
    updated_at: Optional[str] = None

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, tags: List[str]) -> List[str]:
        for tag in tags:
            if len(tag) > MAX_TAG_LENGTH:
                raise ValueError(f"Tag trop long: {len(tag)} chars (max: {MAX_TAG_LENGTH})")
        return tags

def check_compression_ratio(zf: ZipFile, compressed_size: int) -> None:
    """Vérifie le ratio de compression pour détecter les zip bombs."""
    total_uncompressed = sum(info.file_size for info in zf.infolist())

    if compressed_size > 0:
        ratio = total_uncompressed / compressed_size
        if ratio > MAX_COMPRESSION_RATIO:
            raise ArchiveSecurityError(
                f"Ratio de compression suspect: {ratio:.0f}:1 "
                f"(max: {MAX_COMPRESSION_RATIO}:1) - possible zip bomb"
            )

def load_archive_validated(path: Path) -> List[EntryModel]:
    """Charge et valide une archive .rekall."""
    path = Path(path)
    file_size = path.stat().st_size

    # Vérifications de base (Niveau 1)
    if file_size > MAX_ARCHIVE_SIZE:
        raise ArchiveSecurityError(f"Archive trop volumineuse")

    with ZipFile(path, 'r') as zf:
        # Vérifier ratio de compression
        check_compression_ratio(zf, file_size)

        # Lire et parser JSON
        raw_data = zf.read('data.json')
        data = json.loads(raw_data)

        # Valider chaque entrée avec Pydantic
        entries = []
        for i, item in enumerate(data.get('entries', [])):
            try:
                entry = EntryModel(**item)
                entries.append(entry)
            except Exception as e:
                raise ArchiveSecurityError(
                    f"Entrée {i} invalide: {e}"
                ) from e

        return entries
```

#### Niveau 3 - Sandbox avec Quotas Ressources (Demi-journée) 🟡 OPTIONNEL
```python
import resource
import signal
from multiprocessing import Process, Queue
from typing import Any

# Limites de ressources
MEMORY_LIMIT = 256 * 1024 * 1024  # 256 Mo RAM max
CPU_TIME_LIMIT = 30  # 30 secondes max
FILE_SIZE_LIMIT = 100 * 1024 * 1024  # 100 Mo fichiers temp max

class ResourceLimitExceeded(Exception):
    """Dépassement des limites de ressources."""
    pass

def _limited_loader(path: str, queue: Queue) -> None:
    """Worker avec limites de ressources (exécuté dans subprocess)."""
    # Appliquer les limites
    resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT, MEMORY_LIMIT))
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_TIME_LIMIT, CPU_TIME_LIMIT))
    resource.setrlimit(resource.RLIMIT_FSIZE, (FILE_SIZE_LIMIT, FILE_SIZE_LIMIT))

    try:
        result = load_archive_validated(Path(path))
        queue.put(('success', result))
    except Exception as e:
        queue.put(('error', str(e)))

def load_archive_sandboxed(path: Path, timeout: int = 60) -> List[EntryModel]:
    """Charge une archive dans un processus isolé avec limites.

    Utile si les archives proviennent de sources non fiables.
    """
    queue = Queue()
    process = Process(target=_limited_loader, args=(str(path), queue))
    process.start()
    process.join(timeout=timeout)

    if process.is_alive():
        process.terminate()
        process.join()
        raise ResourceLimitExceeded(f"Timeout après {timeout}s")

    if queue.empty():
        raise ResourceLimitExceeded("Process tué (probablement OOM)")

    status, result = queue.get()
    if status == 'error':
        raise ArchiveSecurityError(result)

    return result
```

**Quand c'est utile :** Si Rekall accepte des archives de sources externes (import depuis le web, partage entre utilisateurs). Pour usage personnel local, les Niveaux 1-2 suffisent amplement.

### Points Positifs Identifiés

L'audit a relevé que le système de checksum existe déjà, mais ne protège pas contre les zip bombs :

```python
# Déjà présent - À conserver mais insuffisant seul
def verify_checksum(path: Path, expected: str) -> bool:
    """Vérifie l'intégrité de l'archive."""
    # Le checksum valide l'intégrité, pas la sécurité !
    # Une zip bomb a un checksum valide.
    ...
```

**Recommandation :** Conserver la vérification de checksum (intégrité) ET ajouter les vérifications de taille/ratio (sécurité).

---

## 15. Détection et Correction des Contributions IA

### 🔴 Problématique Identifiée

> **[MOYENNE] Travers typiques du code généré par IA**
> - Fonctionnalités annoncées mais non implémentées (commande `similar` avec embeddings)
> - Chaînes/placeholders non résolus (TODO espagnol dans i18n)
> - Interpolations f-strings oubliées (`{config.embeddings_provider}` affiché littéralement)
> - Lint actuel (E/F/I/W) ne détecte pas ces dérives
> - Fichiers concernés: `cli.py:1188-1216`, `i18n.py:607-1104`, `cli.py:1197-1203`, `pyproject.toml:38-57`

### 📖 Sources Consultées

#### ✅ Sources Retenues

| Source | Raison de Rétention |
|--------|---------------------|
| [Ruff Rules Documentation](https://docs.astral.sh/ruff/rules/) | **Référence officielle** : liste exhaustive des 800+ règles Ruff, incluant ANN (annotations), B (bugbear), N (naming), PL (pylint). |
| [BetterStack - Ruff Explained](https://betterstack.com/community/guides/scaling-python/ruff-explained/) | **Guide complet 2025** avec exemples de configuration pyproject.toml et bonnes pratiques d'activation progressive des règles. |
| [Pylint W1309 - f-string-without-interpolation](https://pylint.readthedocs.io/en/stable/user_guide/messages/warning/f-string-without-interpolation.html) | **Documentation officielle** de la règle détectant les f-strings sans interpolation (pattern inverse du problème). |
| [Pylint Issue #2507 - Detect missing f-prefix](https://github.com/PyCQA/pylint/issues/2507) | **Discussion technique** sur la détection des strings avec syntax `{var}` mais sans préfixe f. Montre que le problème est reconnu. |
| [Sloppylint - AI Slop Detector](https://github.com/rsionnach/sloppylint) | **Outil spécialisé 2025** pour détecter les patterns IA : placeholders, imports hallucinés, cross-language leakage, hedging comments. |
| [Qodo - Code Quality 2025](https://www.qodo.ai/blog/code-quality/) | **Guide moderne** sur la qualité du code avec contributions IA, incluant stratégies de revue et outils. |
| [PEP 8 - Style Guide](https://peps.python.org/pep-0008/) | **Standard officiel** Python pour les conventions de nommage et de style. Référence incontournable. |
| [flake8-todos (orsinium)](https://github.com/orsinium-labs/flake8-todos) | **Plugin spécialisé** pour linter les commentaires TODO : format, auteur, lien issue. Règles T001-T005. |
| [JetBrains - Coding Guidelines for AI Agents](https://blog.jetbrains.com/idea/2025/05/coding-guidelines-for-your-ai-agents/) | **Guide pratique** pour créer des guidelines compatibles avec les agents IA. |

#### ❌ Sources Non Retenues

| Source | Raison de Rejet |
|--------|-----------------|
| [xugj520 - Detect AI Code](https://www.xugj520.cn/en/archives/detect-ai-generated-python-code.html) | **Site peu fiable**, contenu probablement traduit automatiquement, pas de sources techniques vérifiables. |
| [Musely AI Code Checker](https://musely.ai/tools/ai-code-checker) | **Outil commercial** sans documentation technique ouverte, approche boîte noire. |
| [Medium - Comment Checker](https://medium.com/@adrien.riaux/comment-checker-a-python-pre-commit-3b21dcaf7194) | **Article ancien** (2021), pré-Ruff, suggère des outils obsolètes. |
| [deepaksood619 - Static Analysis](https://deepaksood619.github.io/python/documentation/27-development-tools/static-code-analysis/) | **Notes personnelles** sans structure ni maintenance, liens cassés. |
| [Gatlen Culp - Pre-commit 2025](https://gatlenculp.medium.com/effortless-code-quality-the-ultimate-pre-commit-hooks-guide-for-2025-57ca501d9835) | **Medium paywall**, contenu inaccessible pour vérification. |

### 🎯 Bonnes Pratiques SOTA 2025

1. **Lint élargi** : Activer Ruff avec règles ANN, B, N, PL en plus de E/F/I/W
2. **Détection f-strings** : Pylint W1309 ou recherche manuelle `{.*}` sans préfixe f
3. **Audit TODO/placeholders** : flake8-todos ou grep pour TODO non formatés
4. **Conventions explicites** : Guide de style documenté avec PEP 8 + patterns projet
5. **Revue narrative** : Vérifier cohérence entre docs, messages CLI et fonctionnalités réelles
6. **Traitement des "promesses fantômes"** : Masquer ou implémenter les features annoncées

### 📈 Remédiation Graduelle

#### Niveau 1 - Ruff Élargi + Fix F-Strings (1h) ✅ ESSENTIEL
```toml
# pyproject.toml - Configuration Ruff étendue
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",    # Errors (pycodestyle)
    "F",    # Pyflakes
    "W",    # Warnings
    "I",    # isort
    "B",    # flake8-bugbear (bugs courants)
    "N",    # pep8-naming (conventions nommage)
    "UP",   # pyupgrade (Python moderne)
    "PL",   # Pylint (analyse approfondie)
    "ANN",  # flake8-annotations (types)
    "S",    # flake8-bandit (sécurité)
]

# Ignores raisonnables pour éviter le bruit
ignore = [
    "E501",   # Line too long (géré par formatter)
    "ANN101", # Missing type annotation for self
    "ANN102", # Missing type annotation for cls
    "ANN401", # Dynamically typed expressions (Any)
    "PLR0913", # Too many arguments (parfois nécessaire)
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["ANN", "S101"]  # Tests: pas de types, assert OK
"__init__.py" = ["F401"]      # Unused imports OK pour re-export
```

```python
# AVANT - cli.py:1197-1203 (f-string oubliée)
typer.echo("Using embeddings provider: {config.embeddings_provider}")

# APRÈS - Corrigé
typer.echo(f"Using embeddings provider: {config.embeddings_provider}")
```

```bash
# Script de détection des f-strings manquantes
grep -rn '"\{[a-zA-Z_][a-zA-Z0-9_.]*\}"' rekall/ --include="*.py" | \
  grep -v "^[^:]*:[^:]*:.*f\""
# Retourne les lignes avec {var} dans des strings non-f
```

#### Niveau 2 - Audit TODO + Guide de Style (2-3h) 👍 RECOMMANDÉ
```toml
# pyproject.toml - Ajout flake8-todos via Ruff
[tool.ruff.lint]
extend-select = ["TD"]  # flake8-todos rules

# TD001: Invalid TODO tag
# TD002: Missing author in TODO
# TD003: Missing link in TODO
# TD004: Missing colon in TODO
# TD005: Missing description in TODO
```

```python
# Script d'audit des TODO/placeholders non résolus
import re
from pathlib import Path

SUSPICIOUS_PATTERNS = [
    r'#\s*TODO(?!:)',           # TODO sans format standard
    r'#\s*FIXME',               # FIXME non résolu
    r'pass\s*#.*TODO',          # pass avec TODO = non implémenté
    r'raise NotImplementedError', # Placeholder explicite
    r'\.\.\..*#.*implement',    # Ellipsis avec commentaire
]

def audit_placeholders(directory: Path):
    """Scanne les placeholders suspects."""
    issues = []
    for py_file in directory.rglob("*.py"):
        content = py_file.read_text()
        for i, line in enumerate(content.splitlines(), 1):
            for pattern in SUSPICIOUS_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(f"{py_file}:{i}: {line.strip()}")
    return issues

# Usage
for issue in audit_placeholders(Path("rekall")):
    print(issue)
```

```markdown
# STYLE_GUIDE.md - Conventions du projet Rekall

## Conventions de Nommage (PEP 8)
- **Fonctions/Variables**: `snake_case` (ex: `get_entry_by_id`)
- **Classes**: `PascalCase` (ex: `ArchiveManager`)
- **Constantes**: `UPPER_SNAKE_CASE` (ex: `MAX_ARCHIVE_SIZE`)
- **Privé**: Préfixe `_` (ex: `_internal_helper`)

## Patterns Projet
- **Commandes CLI**: Un fichier par domaine dans `commands/`
- **Sérialisation**: Utiliser `rekall/serializers.py` exclusivement
- **Configuration**: Via `config.py`, jamais de hardcode

## TODO Format Standard
```python
# TODO(username): Description courte - Issue #123
```

## Fonctionnalités Non Implémentées
- Masquer dans l'UI jusqu'à implémentation complète
- Lever `NotImplementedError` avec message explicite
- Documenter dans ROADMAP.md, pas dans le code
```

#### Niveau 3 - Sloppylint + Revue Narrative (Demi-journée) 🟡 OPTIONNEL
```bash
# Installation de sloppylint (outil expérimental)
pip install sloppylint

# Analyse du projet
sloppylint rekall/

# Output typique:
# rekall/cli.py:1200 - PLACEHOLDER: pass statement with TODO comment
# rekall/cli.py:1210 - HEDGING: "should work" comment suggests uncertainty
# rekall/i18n.py:650 - PLACEHOLDER: "TODO" in user-visible string
```

```python
# Script de revue narrative : cohérence docs/fonctionnalités
import ast
from pathlib import Path

def extract_cli_commands(cli_file: Path) -> set:
    """Extrait les noms des commandes CLI définies."""
    tree = ast.parse(cli_file.read_text())
    commands = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call):
                    if hasattr(decorator.func, 'attr'):
                        if decorator.func.attr == 'command':
                            commands.add(node.name)
    return commands

def extract_documented_features(readme: Path) -> set:
    """Extrait les features mentionnées dans la doc."""
    content = readme.read_text().lower()
    # Patterns de features typiques
    features = set()
    import re
    for match in re.findall(r'`rekall (\w+)`', content):
        features.add(match)
    return features

# Audit de cohérence
cli_commands = extract_cli_commands(Path("rekall/cli.py"))
doc_features = extract_documented_features(Path("README.md"))

ghost_features = doc_features - cli_commands
print(f"⚠️ Features documentées mais non implémentées: {ghost_features}")

hidden_features = cli_commands - doc_features
print(f"ℹ️ Commandes non documentées: {hidden_features}")
```

**Quand c'est utile :** Si le projet a plusieurs contributeurs (humains ou IA) ou si tu reprends un projet généré par IA. Pour un projet solo avec historique connu, les Niveaux 1-2 suffisent.

### Cas Spécifiques Identifiés dans Rekall

#### 1. Commande `similar` - Fonctionnalité Fantôme
```python
# cli.py:1188-1216 - AVANT
@app.command("similar")
def similar(query: str):
    """Find similar entries using embeddings."""
    typer.echo("Using embeddings provider: {config.embeddings_provider}")
    # TODO: Implement actual embedding search
    pass

# APRÈS - Option A : Masquer jusqu'à implémentation
# Supprimer la commande et ajouter dans ROADMAP.md

# APRÈS - Option B : Message explicite
@app.command("similar")
def similar(query: str):
    """Find similar entries using embeddings (coming soon)."""
    typer.echo("⚠️ Cette fonctionnalité n'est pas encore implémentée.")
    typer.echo("Voir: https://github.com/user/rekall/issues/XX")
    raise typer.Exit(1)
```

#### 2. Traductions Espagnol - TODO Non Résolu
```python
# i18n.py:607-1104 - Fichier avec "TODO" dans les traductions
TRANSLATIONS = {
    "es": {
        "search_prompt": "TODO",  # ← Visible dans l'UI !
        "no_results": "TODO",
        # ...
    }
}

# Solution : Fallback sur anglais si TODO
def get_translation(key: str, lang: str = "en") -> str:
    text = TRANSLATIONS.get(lang, {}).get(key, "")
    if text == "TODO" or not text:
        return TRANSLATIONS["en"].get(key, key)
    return text
```

---

## 16. Roadmap de Mise en Œuvre (Révisée)

> ⚠️ **Cette roadmap a été ajustée** pour refléter l'analyse de pertinence ci-dessus.
> Les items marqués ~~barrés~~ sont de l'over-engineering pour le contexte Rekall.

### 📅 Planning Priorisé (Pragmatique)

| Phase | Durée | Items | Priorité |
|-------|-------|-------|----------|
| **Immédiat** | Semaine 1 | CI/CD Niveau 1, permissions 600, uv.lock, Ruff basique, DRY serializers, Vulture CI, Exceptions ciblées, tomli-w, Limites archives, **Ruff élargi IA (ANN,B,N,PL)**, **Fix f-strings** | 🔴 Critique |
| **Court terme** | Semaines 2-3 | Pydantic validators, CI lockfile, Ruff étendu, Safety, Module serializers, Commandes intégrations, Rich feedback, Atomic write+fsync, Validation ZIP ratio, **Audit TODO**, **Guide de style** | 🟠 Haute |
| **Optionnel** | Selon besoins | SQLCipher, keyring, détection PII regex, CLI modulaire, Plugins dynamiques, Loguru/structlog, Sandbox archives, **Sloppylint**, **Revue narrative** | 🟡 Si nécessaire |
| ~~Long terme~~ | ~~Mois 2-3~~ | ~~Clean Architecture, audit logs, Repository Pattern, File locking fcntl, AI detection ML~~ | ⚠️ OVERKILL |

### 📋 Checklist de Validation (Réaliste)

#### ✅ Phase Immédiate - Obligatoire (Score cible: B+)
- [ ] `.github/workflows/security.yml` avec pip-audit + Bandit
- [ ] `uv.lock` généré et committé
- [ ] Ruff configuré avec règles `E`, `F`, `W`
- [ ] Permissions 600 sur le fichier DB (`secure_db_permissions()`)
- [ ] Requêtes SQL toutes paramétrées (vérifier `?` placeholders)
- [ ] **DRY** : `entry_to_dict()` factorisé dans `rekall/serializers.py`
- [ ] **Vulture** : Configuration dans `pyproject.toml` + whitelist
- [ ] **Exceptions ciblées** : Remplacer `except Exception` par types spécifiques
- [ ] **tomli-w** : Utiliser lib TOML au lieu de manipulation manuelle
- [ ] **Limites archives** : `MAX_ARCHIVE_SIZE` + `MAX_DECOMPRESSED_SIZE`
- [ ] **Ruff élargi IA** : Activer règles ANN, B, N, PL *(Nouveau)*
- [ ] **Fix f-strings** : Corriger `{var}` sans préfixe f (grep + correction) *(Nouveau)*

#### 👍 Phase Court Terme - Recommandée (Score cible: A-)
- [ ] CI complète : tests + lint + security + **Vulture**
- [ ] Pydantic validators pour `NoteInput` et `SearchQuery`
- [ ] Ruff étendu avec `I`, `B`, `S`, `UP`
- [ ] Safety ajouté à la CI
- [ ] Documentation RGPD basique dans README
- [ ] **Module serializers** : `rekall/serializers.py` avec Pydantic (optionnel)
- [ ] **Intégrations exposées** : `rekall list-integrations` + `install-integration`
- [ ] **Rich error feedback** : Messages utilisateur avec Panel + suggestions
- [ ] **Atomic write + fsync** : Pattern tempfile → fsync → rename pour config.toml
- [ ] **Validation ZIP ratio** : Détection zip bombs (ratio > 100:1)
- [ ] **Audit TODO/placeholders** : Scanner et corriger les TODO non résolus *(Nouveau)*
- [ ] **Guide de style** : `STYLE_GUIDE.md` avec conventions PEP 8 + patterns projet *(Nouveau)*

#### 🟡 Phase Optionnelle - Selon Contexte
- [ ] SQLCipher : **Seulement si** données vraiment sensibles
- [ ] Keyring : **Seulement si** SQLCipher activé
- [ ] Détection PII regex : **Seulement si** exports fréquents
- [ ] Pre-commit hooks : **Seulement si** contributeurs externes
- [ ] Entités extraites : **Seulement si** tests unitaires poussés
- [ ] **CLI modulaire** : `rekall/commands/*.py` **Seulement si** cli.py dépasse ~3k LOC
- [ ] **Plugins dynamiques** : Stevedore/entry points **Seulement si** plugins tiers prévus
- [ ] **Structured logging** : Loguru/structlog **Seulement si** debug complexe requis
- [ ] **Sandbox extraction** : `resource.setrlimit()` **Seulement si** archives externes
- [ ] **Sloppylint** : Détection patterns IA **Seulement si** contributions multi-agents *(Nouveau)*
- [ ] **Revue narrative** : Audit cohérence docs/fonctionnalités **Seulement si** équipe *(Nouveau)*

#### ⚠️ Items Retirés (Over-engineering)
Les items suivants étaient dans la roadmap initiale mais sont **déconseillés** :

| Item retiré | Raison |
|-------------|--------|
| ~~Semgrep + SARIF~~ | Bandit couvre 88% des vulnérabilités Python, suffisant |
| ~~Sessions avec timeout~~ | Pattern web, non applicable à une CLI |
| ~~Audit logs~~ | `.bash_history` suffit pour usage personnel |
| ~~Triggers SQL audit~~ | Complexité injustifiée pour <500 LOC |
| ~~Repository Pattern~~ | Un seul backend SQLite, YAGNI |
| ~~Use Cases + DI~~ | Architecture enterprise, inadaptée |
| ~~Migration chiffrée auto~~ | Chiffrer dès le départ si nécessaire |
| ~~SBOM~~ | Pour projets critiques uniquement |
| ~~File locking fcntl~~ | CLI mono-utilisateur, atomic write suffit *(Nouveau)* |

### 🎯 Score Réaliste Atteignable

| Phase | Effort | Score | Valeur ajoutée |
|-------|--------|-------|----------------|
| Immédiat | ~2h | B+ | Protection CVE, reproductibilité, qualité code |
| Court terme | ~4h | A- | Validation robuste, sécurité FTS, CI complète |
| Total recommandé | ~6h | **A-** | Excellent rapport effort/sécurité |

**Note:** Viser A+ nécessiterait ~20h+ d'over-engineering pour un gain marginal.
Le score A- représente le **sweet spot** pour Rekall.

---

## 📚 Références Complètes

### Standards et Guides Officiels
- [OWASP Top 10:2025](https://owasp.org/Top10/2025/0x00_2025-Introduction/)
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
- [PEP 751 - Python Lock File Format](https://peps.python.org/pep-0751/)

### Outils de Sécurité
- [pip-audit (PyPA)](https://github.com/pypa/pip-audit)
- [Safety CLI](https://github.com/pyupio/safety)
- [Bandit](https://github.com/PyCQA/bandit)
- [SQLCipher](https://www.zetetic.net/sqlcipher/)

### Bibliothèques Python
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [keyring Documentation](https://keyring.readthedocs.io/)
- [sqlcipher3](https://github.com/coleifer/sqlcipher3)

### Qualité et Linting
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [Vulture - Dead Code Finder](https://github.com/jendrikseipp/vulture)
- [deadcode Package](https://pypi.org/project/deadcode/)
- [Adam Johnson - Vulture Best Practices](https://adamj.eu/tech/2023/07/12/django-clean-up-unused-code-vulture/)

### Architecture et Patterns
- [Cosmic Python - Architecture Patterns](https://www.cosmicpython.com/)
- [Clean Architecture Python (glukhov.org)](https://www.glukhov.org/post/2025/11/python-design-patterns-for-clean-architecture/)
- [Stevedore - Plugin Management (OpenStack)](https://docs.openstack.org/stevedore/latest/)
- [Pluggy - pytest Plugin Framework](https://github.com/pytest-dev/pluggy)

### CLI et Structure de Code
- [Typer Documentation](https://typer.tiangolo.com/)
- [Typer add_typer() for Subcommands](https://typer.tiangolo.com/tutorial/subcommands/)
- [Real Python - DRY Principle](https://realpython.com/python-refactoring/)
- [Martin Fowler - Refactoring: Extract Method](https://refactoring.com/catalog/extractMethod.html)

### RGPD et PII
- [Alation - GDPR Best Practices 2025](https://www.alation.com/blog/gdpr-data-compliance-best-practices-2025/)
- [PII Masker (HydroXai)](https://github.com/HydroXai/pii-masker)

### Exception Handling et Logging (Nouveau)
- [PEP 760 - No More Bare Excepts](https://peps.python.org/pep-0760/)
- [Qodo - 6 Best Practices Python Exceptions](https://www.qodo.ai/blog/6-best-practices-for-python-exception-handling/)
- [Real Python - Diabolical Antipattern](https://realpython.com/the-most-diabolical-python-antipattern/)
- [Typer - Exceptions](https://typer.tiangolo.com/tutorial/exceptions/)
- [BetterStack - Loguru Guide](https://betterstack.com/community/guides/logging/loguru/)
- [Structlog - Logging Best Practices](https://www.structlog.org/en/stable/logging-best-practices.html)

### Écriture Atomique et TOML (Nouveau)
- [Real Python - Python and TOML](https://realpython.com/python-toml/)
- [tomli-w (PyPI)](https://pypi.org/project/tomli-w/)
- [gocept - Reliable File Updates](https://blog.gocept.com/2013/07/15/reliable-file-updates-with-python/)
- [Python os.fsync (zetcode)](https://zetcode.com/python/os-fsync/)
- [Python.org - Atomic Write Discussion](https://discuss.python.org/t/adding-atomicwrite-in-stdlib/11899)

### Sécurité Archives et ZIP Bombs
- [CVE-2024-0450 (Snyk)](https://security.snyk.io/vuln/SNYK-UNMANAGED-PYTHON-7924823)
- [Python zipfile Documentation](https://docs.python.org/3/library/zipfile.html)
- [AWS CodeGuru - Zip Bomb Attack](https://docs.aws.amazon.com/codeguru/detector-library/python/zip-bomb-attack/)
- [sunzip - Secure Unzip (GitHub)](https://github.com/twbgc/sunzip)
- [CVE-2019-9674 Discussion](https://bugs.python.org/issue36462)

### Hygiène Code IA et Conventions (Nouveau)
- [Ruff Rules Documentation](https://docs.astral.sh/ruff/rules/)
- [BetterStack - Ruff Explained](https://betterstack.com/community/guides/scaling-python/ruff-explained/)
- [Pylint W1309 - f-string-without-interpolation](https://pylint.readthedocs.io/en/stable/user_guide/messages/warning/f-string-without-interpolation.html)
- [Pylint Issue #2507 - Missing f-prefix Detection](https://github.com/PyCQA/pylint/issues/2507)
- [Sloppylint - AI Slop Detector](https://github.com/rsionnach/sloppylint)
- [flake8-todos (orsinium)](https://github.com/orsinium-labs/flake8-todos)
- [PEP 8 - Style Guide](https://peps.python.org/pep-0008/)
- [Qodo - Code Quality 2025](https://www.qodo.ai/blog/code-quality/)
- [JetBrains - Coding Guidelines for AI Agents](https://blog.jetbrains.com/idea/2025/05/coding-guidelines-for-your-ai-agents/)

---

*Document généré le 2025-12-11*
*Basé sur l'audit de sécurité Rekall*
