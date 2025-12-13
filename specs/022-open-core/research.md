# Research: 022-open-core

**Date**: 2025-12-13
**Feature**: Architecture Open Core

## Recherche effectuée

### 1. Modèle Open Core

**Sources consultées:**
- [Open Core Model - TechTarget](https://www.techtarget.com/searchitoperations/definition/open-core-model-open-core-software)
- [Open Core Model - Wikipedia](https://en.wikipedia.org/wiki/Open-core_model)

**Décision:** Adopter le modèle Open Core avec repo public (rekall) + repo privé (rekall-server)

**Rationale:**
- Utilisé par Odoo avec succès (30 modules core + milliers payants)
- Permet de monétiser sans fragmenter le code
- Direction de dépendance claire : privé → public

**Alternatives rejetées:**
- Fork complet : Duplication de code, maintenance double
- Tout privé : Pas de communauté open source
- Feature flags dans même repo : Complexité excessive, risque de fuite

### 2. Architecture Plugin Python

**Sources consultées:**
- [Plugin Architecture in Python - Siv Scripts](https://alysivji.com/simple-plugin-system.html)

**Décision:** Utiliser ABC (Abstract Base Classes) + ServiceContainer

**Rationale:**
- ABC est dans la stdlib Python, pas de dépendance externe
- Pattern éprouvé et bien compris
- Compatible avec le pattern singleton existant dans rekall

**Alternatives rejetées:**
- Pluggy (pytest plugin system) : Overkill pour 2 interfaces
- Entry points (setuptools) : Trop magique, difficile à débugger
- Duck typing pur : Pas de validation de contrat

### 3. Gestion des pannes

**Décision:** Retry with exponential backoff (3 tentatives)

**Rationale:**
- Pattern standard pour la résilience
- Couvre les micro-coupures réseau sans surcharger le backend

### 4. Versioning des interfaces

**Décision:** Semver strict + deprecation warnings pendant 2 versions majeures

**Rationale:**
- Standard de l'industrie
- Donne le temps aux utilisateurs de migrer

## Aucun NEEDS CLARIFICATION restant

Tous les points techniques ont été résolus dans `/speckit.specify` et `/speckit.clarify`.
