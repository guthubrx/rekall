# Feature Specification: Export/Import Advanced

**Feature Branch**: `027-export-import-advanced`
**Created**: 2025-12-13
**Project**: Rekall Home (16.devKMS)
**Priority**: P2
**Timeline**: 2 semaines
**Dependencies**: 024-cartae-format-migration

## Executive Summary

Export/import avancé vers multiples formats : JSON-LD (déjà implémenté), Markdown, Obsidian, Notion. Permet migration facile et backup multi-format.

## Formats Supportés

### 1. JSON-LD (✅ Déjà dans 024)
- Standard W3C
- Interopérabilité complète

### 2. Markdown (Nouveau)
```bash
rekall export --format=markdown output/
# → Génère .md par entry avec frontmatter YAML
```

### 3. Obsidian (Nouveau)
```bash
rekall export --format=obsidian obsidian-vault/
# → .md + graph links [[Entry Name]]
```

### 4. Notion (Nouveau)
```bash
rekall export --format=notion notion-export/
# → CSV pour import Notion database
```

## Requirements

- **FR-01** : Export Markdown avec frontmatter (tags, dates, metadata)
- **FR-02** : Export Obsidian avec wikilinks [[]] pour relations
- **FR-03** : Export Notion CSV format compatible import
- **FR-04** : Import bidirectionnel (Markdown → Rekall, Obsidian → Rekall)

## Success Criteria

- **SC-001** : Export 1,000 entries < 10s
- **SC-002** : Import Obsidian vault preserves 100% links
- **SC-003** : Notion import successful (manual test)

## Timeline

- Week 1: Markdown export/import
- Week 2: Obsidian + Notion export
