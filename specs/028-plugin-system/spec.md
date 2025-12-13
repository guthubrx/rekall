# Feature Specification: Plugin System Architecture

**Feature Branch**: `028-plugin-system`
**Created**: 2025-12-13
**Project**: Rekall Home (16.devKMS)
**Priority**: P2
**Timeline**: 3-4 semaines

## Executive Summary

Architecture plugin permettant extensions Rekall sans modifier core. Exemples plugins : custom exporters, AI enrichment, graph visualizations.

## Architecture

```python
# rekall/plugins/base.py
class RekallPlugin(ABC):
    name: str
    version: str

    @abstractmethod
    def initialize(self, config: dict):
        pass

    @abstractmethod
    def execute(self, context: dict) -> dict:
        pass

# Plugin discovery
# ~/.rekall/plugins/
#   ├── my-plugin/
#   │   ├── __init__.py
#   │   └── plugin.py
```

## Plugin Types

1. **Exporter Plugins** : Custom export formats
2. **Enrichment Plugins** : AI processing entries
3. **Search Plugins** : Custom search algorithms
4. **UI Plugins** : TUI extensions

## Requirements

- **FR-01** : Plugin discovery automatique (`~/.rekall/plugins/`)
- **FR-02** : Plugin manifest (`plugin.yaml`)
- **FR-03** : Plugin API documentation
- **FR-04** : Sandbox execution (sécurité)

## Success Criteria

- **SC-001** : Community peut créer plugin < 2h (avec template)
- **SC-002** : 3+ plugins communauté dans 3 mois

## Timeline

- Week 1-2: Plugin architecture core
- Week 3: Template + docs
- Week 4: 2 plugins example (exporter, enrichment)
