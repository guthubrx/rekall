# Feature Specification: SKOS Basic Taxonomy (5-10 Catégories)

**Feature Branch**: `025-skos-basic-taxonomy`
**Created**: 2025-12-13
**Status**: Draft
**Project**: Rekall Home (16.devKMS)
**Priority**: P1 (Après migration CartaeItem)
**Timeline**: 1-2 semaines
**Dependencies**: 024-cartae-format-migration

## Executive Summary

Implémentation de taxonomie SKOS basique avec 5-10 catégories pré-configurées pour développeurs. Permet expansion automatique de requêtes (search "security" → trouve "cors/xss/csrf") et navigation conceptuelle hiérarchique.

**Objectif** : Améliorer recall search de 30-40% via expansion broader/narrower, support synonymes altLabel.

---

## Contexte & Objectif

### Problème

**Tags plats actuels** :
```python
entry.tags = ["cors", "safari", "fetch"]
# Recherche "web security" → 0 résultats (pas de match exact)
# Recherche "cross-origin" → 0 résultats (pas de synonyme)
```

### Solution SKOS

**Hiérarchie conceptuelle** :
```json
{
  "prefLabel": "cors",
  "broader": "web-security",
  "altLabel": ["CORS", "Cross-Origin Resource Sharing", "Cross-Origin"]
}
```

**Résultat** :
- Recherche "web security" → expand vers "cors/xss/csrf" → trouve entries
- Recherche "cross-origin" → match altLabel → trouve entries CORS

---

## Taxonomie 5-10 Catégories (Dev-Focused)

### 1. Security (Racine)

```json
{
  "prefLabel": "security",
  "altLabel": ["Security", "Application Security", "InfoSec"],
  "narrower": ["web-security", "auth-security", "data-security"]
}
```

### 2. Web Security

```json
{
  "prefLabel": "web-security",
  "broader": "security",
  "altLabel": ["Web Security", "Browser Security"],
  "narrower": ["cors", "xss", "csrf", "csp"]
}
```

#### 2.1 CORS

```json
{
  "prefLabel": "cors",
  "broader": "web-security",
  "altLabel": ["CORS", "Cross-Origin Resource Sharing", "Cross-Origin"]
}
```

#### 2.2 XSS

```json
{
  "prefLabel": "xss",
  "broader": "web-security",
  "altLabel": ["XSS", "Cross-Site Scripting"]
}
```

### 3. Backend (Racine)

```json
{
  "prefLabel": "backend",
  "narrower": ["database", "api", "server"]
}
```

### 4. Database

```json
{
  "prefLabel": "database",
  "broader": "backend",
  "altLabel": ["Database", "DB", "Data Storage"],
  "narrower": ["sql", "nosql", "migrations", "orm"]
}
```

### 5. API

```json
{
  "prefLabel": "api",
  "broader": "backend",
  "altLabel": ["API", "Web Service"],
  "narrower": ["rest", "graphql", "grpc", "webhooks"]
}
```

### 6. Frontend (Racine)

```json
{
  "prefLabel": "frontend",
  "altLabel": ["Frontend", "UI", "Client-Side"],
  "narrower": ["react", "vue", "css", "html", "javascript"]
}
```

### 7. Infrastructure (Racine)

```json
{
  "prefLabel": "infrastructure",
  "altLabel": ["Infrastructure", "DevOps", "Operations"],
  "narrower": ["docker", "kubernetes", "ci-cd", "monitoring"]
}
```

---

## Requirements

### Functional Requirements

- **FR-01** : Système DOIT charger taxonomie SKOS depuis `rekall/taxonomy/skos_basic.json`
- **FR-02** : Search DOIT expand broader/narrower (depth=2 par défaut)
- **FR-03** : Search DOIT match altLabel (synonymes)
- **FR-04** : User PEUT naviguer hiérarchie (CLI: `rekall browse taxonomy`)
- **FR-05** : Auto-suggestion catégories lors `rekall add` (basé sur content)

### Non-Functional Requirements

- **NFR-01** : Expansion requête DOIT prendre < 10ms
- **NFR-02** : Recall improvement ≥ 30% (measured sur 100 queries test)

---

## Success Criteria

- **SC-001** : Recherche "security" trouve entries "cors/xss/csrf"
- **SC-002** : Recherche "cross-origin" trouve entries CORS
- **SC-003** : Recall +30-40% vs tags plats

---

## Implementation

```python
# rekall/taxonomy/skos.py
class SKOSTaxonomy:
    def expand_query(self, query: str, depth: int = 2) -> List[str]:
        """Expand query via broader/narrower."""
        concepts = self.find_concepts(query)
        expanded = set([query])

        for concept in concepts:
            # Add narrower concepts
            expanded.update(concept.narrower)
            # Add altLabels (synonyms)
            expanded.update(concept.altLabel)

        return list(expanded)
```

---

## Timeline

- **Semaine 1** : Définir JSON taxonomy + unit tests
- **Semaine 2** : Intégrer search expansion + CLI browse
