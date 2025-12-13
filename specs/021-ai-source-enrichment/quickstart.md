# Quickstart: AI Source Enrichment

Guide rapide pour implémenter la Feature 021.

## Prérequis

- Python 3.10+
- Rekall installé (`uv pip install -e .`)
- Tests passent (`uv run pytest`)

## Étapes d'Implémentation

### 1. Migration Schema (v12)

Ajouter dans `rekall/db.py` > `MIGRATIONS`:

```python
12: [
    "ALTER TABLE sources ADD COLUMN ai_tags TEXT",
    "ALTER TABLE sources ADD COLUMN ai_summary TEXT",
    "ALTER TABLE sources ADD COLUMN ai_type TEXT",
    "ALTER TABLE sources ADD COLUMN ai_confidence REAL",
    "ALTER TABLE sources ADD COLUMN enrichment_status TEXT DEFAULT 'none'",
    "ALTER TABLE sources ADD COLUMN enriched_at TEXT",
    "ALTER TABLE sources ADD COLUMN validated_by TEXT",
    "CREATE INDEX IF NOT EXISTS idx_sources_enrichment_status ON sources(enrichment_status)",
],
```

Incrémenter `CURRENT_VERSION = 12`.

### 2. Méthodes DB

Ajouter dans `rekall/db.py`:

```python
def get_unenriched_sources(self, limit: int = 10, include_pending: bool = False) -> list[Source]:
    """Get sources without AI enrichment."""
    statuses = "('none')" if not include_pending else "('none', 'proposed')"
    rows = self.conn.execute(f"""
        SELECT * FROM sources
        WHERE enrichment_status IN {statuses}
          AND status = 'active'
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    return [self._row_to_source(row) for row in rows]

def update_source_enrichment(
    self,
    source_id: str,
    ai_tags: list[str],
    ai_summary: str,
    ai_type: str,
    ai_confidence: float,
    auto_validate: bool = False,
) -> bool:
    """Store AI enrichment for a source."""
    import json
    from datetime import datetime

    status = "validated" if auto_validate and ai_confidence >= 0.90 else "proposed"
    validated_by = "auto" if status == "validated" else None

    cursor = self.conn.execute("""
        UPDATE sources SET
            ai_tags = ?,
            ai_summary = ?,
            ai_type = ?,
            ai_confidence = ?,
            enrichment_status = ?,
            enriched_at = ?,
            validated_by = ?
        WHERE id = ?
    """, (
        json.dumps(ai_tags),
        ai_summary,
        ai_type,
        ai_confidence,
        status,
        datetime.now().isoformat(),
        validated_by,
        source_id,
    ))
    self.conn.commit()
    return cursor.rowcount > 0

def validate_enrichment(
    self,
    source_id: str,
    action: str,  # validate, reject, modify
    modifications: dict | None = None,
) -> str:
    """Human-in-the-loop validation."""
    import json

    if action == "validate":
        self.conn.execute("""
            UPDATE sources SET enrichment_status = 'validated', validated_by = 'human'
            WHERE id = ?
        """, (source_id,))
    elif action == "reject":
        self.conn.execute("""
            UPDATE sources SET enrichment_status = 'rejected', validated_by = 'human'
            WHERE id = ?
        """, (source_id,))
    elif action == "modify" and modifications:
        updates = []
        params = []
        for key, value in modifications.items():
            if key in ("ai_tags", "ai_summary", "ai_type"):
                updates.append(f"{key} = ?")
                params.append(json.dumps(value) if key == "ai_tags" else value)
        params.extend(["validated", "human", source_id])
        self.conn.execute(f"""
            UPDATE sources SET {', '.join(updates)}, enrichment_status = ?, validated_by = ?
            WHERE id = ?
        """, params)

    self.conn.commit()
    return action
```

### 3. MCP Tools

Ajouter dans `rekall/mcp_server.py`:

1. **Tool definitions** dans `list_tools()`:
   - Voir `contracts/*.json` pour les schemas

2. **Handlers** dans `call_tool()`:
```python
elif name == "rekall_get_entry_urls":
    return await _handle_get_entry_urls(arguments)
elif name == "rekall_enrich_source":
    return await _handle_enrich_source(arguments)
elif name == "rekall_list_unenriched":
    return await _handle_list_unenriched(arguments)
elif name == "rekall_validate_enrichment":
    return await _handle_validate_enrichment(arguments)
```

3. **Handler functions**:
```python
async def _handle_get_entry_urls(args: dict) -> list:
    from mcp.types import TextContent
    db = get_db()
    entry_id = args["entry_id"]

    # Resolve prefix
    entry = db.get_entry(entry_id)
    if not entry:
        return [TextContent(type="text", text=f"Entry not found: {entry_id}")]

    sources = db.get_entry_sources(entry.id)
    result = {
        "entry_id": entry.id,
        "entry_title": entry.title,
        "sources": [
            {
                "id": s.id,
                "source_type": s.source_type,
                "source_ref": s.source_ref,
                "domain": _extract_domain(s.source_ref) if s.source_type == "url" else None,
                "source_id": s.source_id,
                "note": s.note,
            }
            for s in sources
        ],
        "total_count": len(sources),
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
```

### 4. Tests

Créer `tests/unit/test_enrichment.py`:

```python
import pytest
from rekall.db import Database

def test_update_source_enrichment(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    # Create test source
    source_id = db.add_source(url="https://example.com", title="Test")

    # Enrich
    result = db.update_source_enrichment(
        source_id=source_id,
        ai_tags=["test", "example"],
        ai_summary="A test source.",
        ai_type="reference",
        ai_confidence=0.85,
    )

    assert result is True
    source = db.get_source(source_id)
    assert source.enrichment_status == "proposed"
    assert "test" in source.ai_tags

def test_auto_validate_high_confidence(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    source_id = db.add_source(url="https://example.com", title="Test")

    result = db.update_source_enrichment(
        source_id=source_id,
        ai_tags=["test"],
        ai_summary="Test.",
        ai_type="reference",
        ai_confidence=0.95,
        auto_validate=True,
    )

    source = db.get_source(source_id)
    assert source.enrichment_status == "validated"
    assert source.validated_by == "auto"
```

## Workflow Usage

```bash
# 1. List sources to enrich
# Agent calls: rekall_list_unenriched(limit=5)

# 2. For each source, agent analyzes and enriches
# Agent calls: rekall_enrich_source(source_id, tags, summary, type, confidence)

# 3. User reviews proposed enrichments
# Agent calls: rekall_validate_enrichment(source_id, action="validate")
```

## Vérification

```bash
# Run tests
uv run pytest tests/unit/test_enrichment.py -v

# Check migration
uv run rekall info  # Should show schema version 12
```
