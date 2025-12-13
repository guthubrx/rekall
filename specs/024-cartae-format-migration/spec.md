# Feature Specification: Migration Format CartaeItem (JSON-LD)

**Feature Branch**: `024-cartae-format-migration`
**Created**: 2025-12-13
**Status**: Draft
**Project**: Rekall Home (16.devKMS)
**Priority**: P0 (Foundation pour toutes features futures)

## Executive Summary

Migration du format interne Entry vers CartaeItem (JSON-LD + SKOS), format universel interopérable basé sur standards W3C. CartaeItem devient le format unique Rekall Home + Server, permettant interopérabilité, anti-vendor-lock-in, et compliance EU AI Act.

**Décision stratégique** : Format unique CartaeItem partout, différenciation par enrichissement (Home = basique local, Server = premium cloud).

---

## Contexte & Objectif

### Problème actuel

**Format propriétaire Entry** :
```python
class Entry:
    id: str
    type: str  # "bug", "pattern", etc.
    title: str
    content: str
    tags: List[str]  # Flat, pas de hiérarchie
    context: dict  # Structured context (bon)
    # ... mais pas d'interopérabilité
```

**Limitations** :
- ❌ Export vers Notion/Obsidian/Neo4j = conversion custom
- ❌ Tags plats (pas de taxonomie hiérarchique)
- ❌ Pas de standard W3C (vendor lock-in potentiel)
- ❌ Agents IA ne comprennent pas sémantique type

### Solution : CartaeItem (JSON-LD + SKOS)

**Format universel** basé sur standards W3C :
```json
{
  "@context": "https://schema.org",
  "@type": "TechArticle",
  "identifier": "01KCCJ...",
  "name": "Fix Safari CORS credentials",
  "about": {
    "prefLabel": "web-security",
    "broader": "security",
    "narrower": ["cors-specific", "safari-bugs"]
  },
  "situation": "Safari 16+ bloque fetch même avec CORS headers",
  "solution": "Ajouter credentials: 'include' + Access-Control-Allow-Credentials",
  "whatFailed": "Augmenter timeout n'a pas aidé",
  "aiInsights": [{
    "model": "all-MiniLM-L6-v2",
    "confidence": 0.67,
    "insight": "Pattern Safari CORS récurrent"
  }],
  "relationships": [{
    "type": "relatedTo",
    "target": "01HY2...",
    "weight": 0.8,
    "reason": "Both Safari security issues"
  }]
}
```

**Bénéfices** :
- ✅ Interopérabilité native (export/import vers n'importe quel outil)
- ✅ SKOS hiérarchique (expansion requêtes agents IA)
- ✅ Standards W3C (pérennité 20+ ans)
- ✅ Compliance EU AI Act (data portability GDPR)
- ✅ Anti-vendor-lock-in (argument de vente B2B)

---

## User Scenarios & Testing

### User Story 1 - Migration transparente utilisateur existant (Priority: P0)

Un utilisateur Rekall existant met à jour vers version avec CartaeItem. Toutes ses entries sont migrées automatiquement, zero action requise.

**Independent Test** : Installation nouvelle version, vérification que toutes entries existantes fonctionnent identiquement.

**Acceptance Scenarios** :

1. **Given** utilisateur avec 500 entries format Entry, **When** upgrade vers CartaeItem, **Then** toutes entries accessibles sans perte données
2. **Given** migration complétée, **When** search/review/show, **Then** fonctionnent comme avant (backward compatibility)
3. **Given** anciennes entries migrées, **When** création nouvelle entry, **Then** utilise format CartaeItem natif

---

### User Story 2 - Export interopérable vers Obsidian (Priority: P1)

Un utilisateur veut exporter sa knowledge base Rekall vers Obsidian pour backup ou migration. Export JSON-LD standard, import direct dans Obsidian.

**Independent Test** : Export Rekall → Import Obsidian, vérifier 100% données préservées.

**Acceptance Scenarios** :

1. **Given** 100 entries Rekall, **When** `rekall export --format=jsonld obsidian/`, **Then** 100 fichiers .json générés conformes JSON-LD
2. **Given** export JSON-LD, **When** import dans Obsidian, **Then** tags, relations, contenu préservés
3. **Given** entries avec SKOS categories, **When** export, **Then** hiérarchie broader/narrower préservée

---

### User Story 3 - Agent IA utilise SKOS pour expansion requête (Priority: P1)

Un agent IA (via MCP) cherche "sécurité web". Grâce à SKOS, trouve automatiquement entries sur CORS, XSS, CSRF (narrower concepts).

**Independent Test** : Query MCP "web security", vérifier que CORS/XSS/CSRF sont retournés même si pas mentionnés.

**Acceptance Scenarios** :

1. **Given** entry catégorisée "cors" (narrower de "web-security"), **When** agent cherche "web security", **Then** entry CORS retournée
2. **Given** entry avec broader "security", **When** agent traverse hiérarchie, **Then** peut remonter vers concepts parents
3. **Given** SKOS altLabel "Cross-Origin" pour "CORS", **When** agent cherche "Cross-Origin", **Then** trouve entries CORS

---

### Edge Cases

- **Migration échoue mid-process** : Rollback automatique vers backup pre-migration
- **Entry avec champs custom non-standard** : Préservés dans `additionalProperties`
- **Corruption données pendant migration** : Validation schéma JSON-LD avant écriture
- **Export vers outil ne supportant pas JSON-LD** : Fallback export Markdown avec frontmatter

---

## Requirements

### Functional Requirements - Migration

- **FR-M01** : Le système DOIT migrer automatiquement toutes entries Entry vers CartaeItem au premier lancement post-upgrade
- **FR-M02** : Le système DOIT créer backup SQLite pre-migration (`.rekall.db.backup`)
- **FR-M03** : Le système DOIT valider schéma JSON-LD de chaque entry migrée (pydantic model)
- **FR-M04** : Le système DOIT logger migration (succès/échecs) dans `~/.local/share/rekall/migration.log`
- **FR-M05** : Si migration échoue, le système DOIT rollback automatiquement vers backup

### Functional Requirements - Schéma CartaeItem

- **FR-S01** : Le système DOIT implémenter schéma CartaeItem complet (JSON-LD @context, @type, etc.)
- **FR-S02** : Le système DOIT supporter types Entry → @type mapping :
  - `bug` → `TechArticle` (schema.org)
  - `pattern` → `HowTo`
  - `decision` → `Article`
  - `pitfall` → `WarningMessage`
  - `config` → `SoftwareApplication`
  - `reference` → `WebPage`
- **FR-S03** : Le système DOIT préserver structured context (situation/solution/whatFailed)
- **FR-S04** : Le système DOIT implémenter `aiInsights` avec model/confidence/insight
- **FR-S05** : Le système DOIT implémenter `relationships` avec type/target/weight/reason

### Functional Requirements - SKOS

- **FR-SK01** : Le système DOIT implémenter SKOS basique (prefLabel, broader, narrower, altLabel)
- **FR-SK02** : Le système DOIT fournir 5-10 catégories SKOS generic pre-configured :
  - `web-security` (broader: security, narrower: cors, xss, csrf)
  - `database` (broader: backend, narrower: sql, nosql, migrations)
  - `api` (broader: backend, narrower: rest, graphql, grpc)
  - `frontend` (broader: ui, narrower: react, vue, css)
  - `devops` (broader: infrastructure, narrower: docker, kubernetes, ci-cd)
- **FR-SK03** : Le système DOIT permettre expansion requête via broader/narrower (search "security" → trouve "cors")
- **FR-SK04** : Le système DOIT supporter synonymes via altLabel ("CORS" = "Cross-Origin Resource Sharing")

### Functional Requirements - Export/Import

- **FR-EI01** : Le système DOIT supporter `rekall export --format=jsonld <output_path>`
- **FR-EI02** : Le système DOIT supporter `rekall import <jsonld_file>`
- **FR-EI03** : L'export DOIT générer JSON-LD valide (validation schema.org)
- **FR-EI04** : L'import DOIT valider schéma avant insertion DB
- **FR-EI05** : L'export DOIT préserver 100% données (metadata, context, relations)

### Non-Functional Requirements

- **NFR-01** : Migration de 10,000 entries DOIT prendre < 30 secondes
- **NFR-02** : Overhead stockage CartaeItem vs Entry < 15%
- **NFR-03** : Performance search après migration identique (± 5ms)
- **NFR-04** : Validation schéma JSON-LD DOIT prendre < 1ms par entry

---

## Schéma CartaeItem Détaillé

### Structure Complète

```typescript
interface CartaeItem {
  // JSON-LD Core
  "@context": "https://schema.org" | string;
  "@type": SchemaOrgType;  // TechArticle, HowTo, Article, etc.

  // Identifiers
  identifier: string;  // ULID (existing Entry.id)
  name: string;  // Entry.title
  dateCreated: string;  // ISO 8601
  dateModified: string;  // ISO 8601

  // SKOS Categories (hiérarchique)
  about: {
    prefLabel: string;  // "web-security"
    broader?: string;   // "security"
    narrower?: string[];  // ["cors", "xss"]
    altLabel?: string[];  // ["Web Security", "Application Security"]
  };

  // Tags (folksonomy, flat)
  keywords?: string[];  // Entry.tags

  // Structured Context (Rekall unique)
  situation?: string;
  solution?: string;
  whatFailed?: string;

  // Content
  articleBody?: string;  // Entry.content

  // AI Insights (Rekall unique)
  aiInsights?: {
    model: string;  // "all-MiniLM-L6-v2", "claude-opus-4"
    confidence: number;  // 0.0-1.0
    insight: string;
    timestamp?: string;
  }[];

  // Relationships (typed, weighted)
  relationships?: {
    type: "relatedTo" | "supersedes" | "derivedFrom" | "contradicts";
    target: string;  // Target entry identifier
    weight?: number;  // 0.0-1.0
    reason?: string;
  }[];

  // Metadata
  author?: {
    "@type": "Person";
    name?: string;
  };

  // Additional properties (extensibility)
  [key: string]: any;
}
```

### Mapping Entry → CartaeItem

| Entry Field | CartaeItem Field | Transformation |
|-------------|------------------|----------------|
| `id` | `identifier` | Direct copy (ULID) |
| `type` | `@type` | Mapping (bug → TechArticle) |
| `title` | `name` | Direct copy |
| `content` | `articleBody` | Direct copy |
| `tags` | `keywords` | Direct copy (folksonomy) |
| `context.situation` | `situation` | Direct copy |
| `context.solution` | `solution` | Direct copy |
| `context.what_failed` | `whatFailed` | Direct copy |
| `created_at` | `dateCreated` | ISO 8601 format |
| `updated_at` | `dateModified` | ISO 8601 format |
| N/A (nouveau) | `about` | Inféré depuis tags + type |
| N/A (nouveau) | `aiInsights` | Empty array initially |
| `links` | `relationships` | Mapping relation types |

---

## Migration Strategy

### Phase 1 : Schema Definition (Semaine 1)

**Tâches** :
1. Définir Pydantic models CartaeItem
2. Définir SKOS taxonomy basique (5-10 catégories)
3. Unit tests validation schéma

**Livrables** :
- `rekall/models/cartae_item.py`
- `rekall/taxonomy/skos_basic.json`
- Tests : `tests/models/test_cartae_item.py`

### Phase 2 : Migration Logic (Semaine 2)

**Tâches** :
1. Script migration Entry → CartaeItem
2. Backup/rollback mechanism
3. Logging + error handling

**Livrables** :
- `rekall/migrations/001_entry_to_cartae.py`
- `rekall/db/backup.py`
- Tests : `tests/migrations/test_entry_to_cartae.py`

### Phase 3 : Export/Import (Semaine 3)

**Tâches** :
1. Implémentation export JSON-LD
2. Implémentation import JSON-LD
3. Validation schema.org

**Livrables** :
- `rekall/export/jsonld.py`
- `rekall/import/jsonld.py`
- Tests : `tests/export/test_jsonld.py`

### Phase 4 : SKOS Integration (Semaine 4)

**Tâches** :
1. Query expansion broader/narrower
2. Synonym matching altLabel
3. MCP protocol update (expose SKOS)

**Livrables** :
- `rekall/search/skos_expansion.py`
- `rekall/mcp/skos_tools.py`
- Tests : `tests/search/test_skos.py`

---

## SKOS Taxonomy Basique (5-10 Catégories)

```json
{
  "concepts": [
    {
      "prefLabel": "security",
      "altLabel": ["Security", "Application Security", "InfoSec"],
      "narrower": ["web-security", "auth-security", "data-security"]
    },
    {
      "prefLabel": "web-security",
      "broader": "security",
      "altLabel": ["Web Security", "Browser Security"],
      "narrower": ["cors", "xss", "csrf", "csp"]
    },
    {
      "prefLabel": "cors",
      "broader": "web-security",
      "altLabel": ["CORS", "Cross-Origin Resource Sharing", "Cross-Origin"]
    },
    {
      "prefLabel": "backend",
      "narrower": ["database", "api", "server"]
    },
    {
      "prefLabel": "database",
      "broader": "backend",
      "altLabel": ["Database", "DB", "Data Storage"],
      "narrower": ["sql", "nosql", "migrations", "orm"]
    },
    {
      "prefLabel": "api",
      "broader": "backend",
      "altLabel": ["API", "Web Service"],
      "narrower": ["rest", "graphql", "grpc", "webhooks"]
    },
    {
      "prefLabel": "frontend",
      "altLabel": ["Frontend", "UI", "Client-Side"],
      "narrower": ["react", "vue", "css", "html", "javascript"]
    },
    {
      "prefLabel": "infrastructure",
      "altLabel": ["Infrastructure", "DevOps", "Operations"],
      "narrower": ["docker", "kubernetes", "ci-cd", "monitoring"]
    }
  ]
}
```

---

## Success Criteria

### Measurable Outcomes

- **SC-001** : Migration 10,000 entries existantes en < 30s sans perte données
- **SC-002** : Export JSON-LD valide (validation schema.org) 100% entries
- **SC-003** : Import Obsidian/Notion → Rekall préserve 100% structured context
- **SC-004** : Query expansion SKOS "security" trouve entries "cors/xss/csrf"
- **SC-005** : Performance search post-migration identique (± 5ms)
- **SC-006** : Overhead stockage < 15% (measured on 1,000 entries sample)

---

## Assumptions

- Python 3.10+ est requis (déjà le cas)
- SQLite schema change compatible backward (indexes préservés)
- Pydantic 2.x pour validation (déjà utilisé)
- JSON-LD @context peut être local file (pas fetch https://schema.org obligatoire)
- SKOS taxonomy basique suffisante Phase 1 (marketplace industry = Phase 2 Server)

---

## Out of Scope

- **SKOS Marketplace** (100+ schemas industry) → Phase 2 Server payant
- **OWL Reasoning** (inférence transitive) → Phase 3
- **SPARQL Endpoint** → Phase 3 Server
- **Graph embeddings** (Node2Vec) → Phase 3
- **Multi-modal** (images, PDFs) → Future

---

## Risks & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Migration corrompt données** | Faible | Critique | Backup automatique pre-migration + rollback |
| **Overhead stockage 20%+** | Moyenne | Moyen | Compression zlib context, @context local (pas inline) |
| **Performance search dégradée** | Faible | Haute | Benchmark pre/post, optimiser indexes SQLite |
| **SKOS expansion trop agressive** | Moyenne | Faible | Configurable depth (default=2), user peut disable |
| **JSON-LD validation lente** | Faible | Moyen | Cache schemas, validation batch |

---

## Dependencies

- **Internal** : `rekall/db.py` (schema change), `rekall/search.py` (SKOS expansion)
- **External** : `pydantic` (validation), `jsonschema` (JSON-LD validation)
- **Standards** : schema.org vocabulary, SKOS W3C spec

---

## Documentation Requirements

- **README update** : Section "CartaeItem Format" explaining JSON-LD benefits
- **Migration guide** : `docs/migration-cartae.md` (user-facing)
- **API reference** : `docs/api/cartae-schema.md` (developer-facing)
- **SKOS taxonomy** : `docs/skos-taxonomy.md` (categories reference)

---

## Next Steps

**Immédiat (Semaine 1)** :
1. Créer Pydantic model CartaeItem
2. Définir SKOS taxonomy JSON (5-10 catégories)
3. Unit tests validation schéma

**Validation Go/No-Go** :
- ✅ GO si : Schéma validé + migration test 1,000 entries < 3s
- ❌ NO-GO si : Overhead stockage > 20% ou performance search -15%+
