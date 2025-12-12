"""Tests for Rekall models (TDD - written before implementation)."""

import re
from datetime import datetime


class TestULID:
    """Tests for ULID generation (T007)."""

    def test_ulid_format_26_chars(self):
        """ULID must be exactly 26 characters."""
        from rekall.models import generate_ulid

        ulid = generate_ulid()
        assert len(ulid) == 26

    def test_ulid_valid_characters(self):
        """ULID must only contain Crockford Base32 characters."""
        from rekall.models import generate_ulid

        ulid = generate_ulid()
        # Crockford Base32: 0-9, A-Z excluding I, L, O, U
        valid_pattern = r"^[0-9A-HJKMNP-TV-Z]{26}$"
        assert re.match(valid_pattern, ulid), f"Invalid ULID: {ulid}"

    def test_ulid_uniqueness(self):
        """Multiple ULIDs must be unique."""
        from rekall.models import generate_ulid

        ulids = [generate_ulid() for _ in range(100)]
        assert len(set(ulids)) == 100, "ULIDs are not unique"

    def test_ulid_sortable_chronologically(self):
        """ULIDs generated later should sort after earlier ones."""
        import time

        from rekall.models import generate_ulid

        ulid1 = generate_ulid()
        time.sleep(0.002)  # Small delay to ensure different timestamp
        ulid2 = generate_ulid()
        assert ulid1 < ulid2, "ULIDs should be chronologically sortable"


class TestEntry:
    """Tests for Entry dataclass (T008)."""

    def test_entry_creation_valid(self):
        """Entry should be created with valid type."""
        from rekall.models import Entry, generate_ulid

        entry = Entry(
            id=generate_ulid(),
            title="Test bug",
            type="bug",
        )
        assert entry.title == "Test bug"
        assert entry.type == "bug"
        assert entry.confidence == 2  # default
        assert entry.status == "active"  # default

    def test_entry_all_valid_types(self):
        """All 6 types should be valid."""
        from rekall.models import Entry, generate_ulid

        valid_types = ["bug", "pattern", "decision", "pitfall", "config", "reference"]
        for entry_type in valid_types:
            entry = Entry(id=generate_ulid(), title="Test", type=entry_type)
            assert entry.type == entry_type

    def test_entry_invalid_type_raises(self):
        """Invalid type should raise ValueError."""
        import pytest

        from rekall.models import Entry, generate_ulid

        with pytest.raises(ValueError, match="invalid type"):
            Entry(id=generate_ulid(), title="Test", type="invalid")

    def test_entry_confidence_valid_range(self):
        """Confidence 0-5 should be valid."""
        from rekall.models import Entry, generate_ulid

        for confidence in range(6):
            entry = Entry(
                id=generate_ulid(), title="Test", type="bug", confidence=confidence
            )
            assert entry.confidence == confidence

    def test_entry_confidence_invalid_raises(self):
        """Confidence outside 0-5 should raise ValueError."""
        import pytest

        from rekall.models import Entry, generate_ulid

        with pytest.raises(ValueError, match="confidence must be 0-5"):
            Entry(id=generate_ulid(), title="Test", type="bug", confidence=6)

        with pytest.raises(ValueError, match="confidence must be 0-5"):
            Entry(id=generate_ulid(), title="Test", type="bug", confidence=-1)

    def test_entry_with_tags(self):
        """Entry should accept list of tags."""
        from rekall.models import Entry, generate_ulid

        entry = Entry(
            id=generate_ulid(),
            title="Test",
            type="bug",
            tags=["python", "sqlite"],
        )
        assert entry.tags == ["python", "sqlite"]

    def test_entry_with_project(self):
        """Entry should accept project name."""
        from rekall.models import Entry, generate_ulid

        entry = Entry(
            id=generate_ulid(),
            title="Test",
            type="bug",
            project="my-project",
        )
        assert entry.project == "my-project"

    def test_entry_obsolete_status(self):
        """Entry should support obsolete status."""
        from rekall.models import Entry, generate_ulid

        entry = Entry(
            id=generate_ulid(),
            title="Test",
            type="bug",
            status="obsolete",
            superseded_by="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        )
        assert entry.status == "obsolete"
        assert entry.superseded_by == "01ARZ3NDEKTSV4RRFFQ69G5FAV"

    def test_entry_timestamps_auto(self):
        """Entry should have auto-generated timestamps."""
        from rekall.models import Entry, generate_ulid

        before = datetime.now()
        entry = Entry(id=generate_ulid(), title="Test", type="bug")
        after = datetime.now()

        assert before <= entry.created_at <= after
        assert before <= entry.updated_at <= after


class TestConfig:
    """Tests for Config dataclass (T009)."""

    def test_config_default_db_path(self):
        """Config should have default db_path in XDG location."""
        from pathlib import Path

        from rekall.config import Config

        config = Config()
        # Now uses XDG paths by default
        expected = Path.home() / ".local" / "share" / "rekall" / "knowledge.db"
        assert config.db_path == expected

    def test_config_custom_db_path(self):
        """Config should accept custom paths via ResolvedPaths."""
        from pathlib import Path

        from rekall.config import Config
        from rekall.paths import PathSource, ResolvedPaths

        custom_path = Path("/tmp/test.db")
        paths = ResolvedPaths(
            config_dir=Path("/tmp"),
            data_dir=Path("/tmp"),
            cache_dir=Path("/tmp/cache"),
            db_path=custom_path,
            source=PathSource.CLI,
        )
        config = Config(paths=paths)
        assert config.db_path == custom_path

    def test_config_rekall_dir(self):
        """Config should provide rekall_dir property (now data_dir)."""
        from pathlib import Path

        from rekall.config import Config

        config = Config()
        # Now uses XDG data dir
        expected = Path.home() / ".local" / "share" / "rekall"
        assert config.rekall_dir == expected

    def test_config_embeddings_default_none(self):
        """Config embeddings settings should default to None."""
        from rekall.config import Config

        config = Config()
        assert config.embeddings_provider is None
        assert config.embeddings_model is None

    def test_config_smart_embeddings_defaults(self):
        """Config smart embeddings should have sensible defaults."""
        from rekall.config import Config

        config = Config()
        assert config.smart_embeddings_enabled is False
        assert config.smart_embeddings_model == "EmbeddingGemma-2B-v1"
        assert config.smart_embeddings_dimensions == 384
        assert config.smart_embeddings_similarity_threshold == 0.75


class TestEmbedding:
    """Tests for Embedding dataclass (Phase 0 - Smart Embeddings)."""

    def test_embedding_creation_valid(self):
        """Embedding should be created with valid type and dimensions."""
        from rekall.models import Embedding, generate_ulid

        embedding = Embedding(
            id=generate_ulid(),
            entry_id=generate_ulid(),
            embedding_type="summary",
            vector=b"\x00" * (384 * 4),  # 384 float32 values
            dimensions=384,
            model_name="test-model",
        )
        assert embedding.embedding_type == "summary"
        assert embedding.dimensions == 384

    def test_embedding_invalid_type_raises(self):
        """Embedding should reject invalid embedding_type."""
        import pytest

        from rekall.models import Embedding, generate_ulid

        with pytest.raises(ValueError, match="invalid embedding_type"):
            Embedding(
                id=generate_ulid(),
                entry_id=generate_ulid(),
                embedding_type="invalid",
                vector=b"\x00" * (384 * 4),
                dimensions=384,
                model_name="test-model",
            )

    def test_embedding_invalid_dimensions_raises(self):
        """Embedding should reject invalid dimensions."""
        import pytest

        from rekall.models import Embedding, generate_ulid

        with pytest.raises(ValueError, match="invalid dimensions"):
            Embedding(
                id=generate_ulid(),
                entry_id=generate_ulid(),
                embedding_type="summary",
                vector=b"\x00" * 100,
                dimensions=100,  # Not 128, 384, or 768
                model_name="test-model",
            )

    def test_embedding_valid_dimensions(self):
        """Embedding should accept all valid Matryoshka dimensions."""
        from rekall.models import Embedding, generate_ulid

        for dims in (128, 384, 768):
            embedding = Embedding(
                id=generate_ulid(),
                entry_id=generate_ulid(),
                embedding_type="context",
                vector=b"\x00" * (dims * 4),
                dimensions=dims,
                model_name="test-model",
            )
            assert embedding.dimensions == dims

    def test_embedding_to_numpy(self):
        """Embedding.to_numpy() should deserialize vector correctly."""
        import numpy as np

        from rekall.models import Embedding, generate_ulid

        # Create a known vector
        original = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        embedding = Embedding(
            id=generate_ulid(),
            entry_id=generate_ulid(),
            embedding_type="summary",
            vector=original.tobytes(),
            dimensions=128,  # Lie about dimensions for simplicity
            model_name="test-model",
        )

        # Override dimensions check for this test
        embedding.dimensions = 128  # Actually 3, but we bypass validation

        # to_numpy should recover the original values
        recovered = np.frombuffer(embedding.vector, dtype=np.float32)
        np.testing.assert_array_almost_equal(recovered, original)

    def test_embedding_from_numpy(self):
        """Embedding.from_numpy() should create embedding from array."""
        import numpy as np

        from rekall.models import Embedding, generate_ulid

        entry_id = generate_ulid()
        array = np.random.randn(384).astype(np.float32)

        embedding = Embedding.from_numpy(
            entry_id=entry_id,
            embedding_type="summary",
            array=array,
            model_name="test-model",
        )

        assert embedding.entry_id == entry_id
        assert embedding.embedding_type == "summary"
        assert embedding.dimensions == 384
        assert len(embedding.id) == 26  # Valid ULID

        # Verify round-trip
        recovered = embedding.to_numpy()
        np.testing.assert_array_almost_equal(recovered, array)


class TestSuggestion:
    """Tests for Suggestion dataclass (Phase 0 - Smart Embeddings)."""

    def test_suggestion_link_creation(self):
        """Suggestion link should be created with 2 entry_ids."""
        from rekall.models import Suggestion, generate_ulid

        ids = [generate_ulid(), generate_ulid()]
        suggestion = Suggestion(
            id=generate_ulid(),
            suggestion_type="link",
            entry_ids=ids,
            score=0.85,
            reason="Similar content",
        )
        assert suggestion.suggestion_type == "link"
        assert len(suggestion.entry_ids) == 2
        assert suggestion.status == "pending"

    def test_suggestion_generalize_creation(self):
        """Suggestion generalize should require 3+ entry_ids."""
        from rekall.models import Suggestion, generate_ulid

        ids = [generate_ulid() for _ in range(4)]
        suggestion = Suggestion(
            id=generate_ulid(),
            suggestion_type="generalize",
            entry_ids=ids,
            score=0.82,
        )
        assert suggestion.suggestion_type == "generalize"
        assert len(suggestion.entry_ids) == 4

    def test_suggestion_link_requires_2_ids(self):
        """Suggestion link should reject != 2 entry_ids."""
        import pytest

        from rekall.models import Suggestion, generate_ulid

        with pytest.raises(ValueError, match="exactly 2"):
            Suggestion(
                id=generate_ulid(),
                suggestion_type="link",
                entry_ids=[generate_ulid()],  # Only 1 ID
                score=0.8,
            )

    def test_suggestion_generalize_requires_3_ids(self):
        """Suggestion generalize should reject < 3 entry_ids."""
        import pytest

        from rekall.models import Suggestion, generate_ulid

        with pytest.raises(ValueError, match="3\\+"):
            Suggestion(
                id=generate_ulid(),
                suggestion_type="generalize",
                entry_ids=[generate_ulid(), generate_ulid()],  # Only 2 IDs
                score=0.8,
            )

    def test_suggestion_invalid_type_raises(self):
        """Suggestion should reject invalid suggestion_type."""
        import pytest

        from rekall.models import Suggestion, generate_ulid

        with pytest.raises(ValueError, match="invalid suggestion_type"):
            Suggestion(
                id=generate_ulid(),
                suggestion_type="invalid",
                entry_ids=[generate_ulid(), generate_ulid()],
                score=0.8,
            )

    def test_suggestion_invalid_score_raises(self):
        """Suggestion should reject score outside 0.0-1.0."""
        import pytest

        from rekall.models import Suggestion, generate_ulid

        with pytest.raises(ValueError, match="score must be"):
            Suggestion(
                id=generate_ulid(),
                suggestion_type="link",
                entry_ids=[generate_ulid(), generate_ulid()],
                score=1.5,  # Invalid
            )

    def test_suggestion_entry_ids_json(self):
        """Suggestion.entry_ids_json() should serialize to JSON."""
        import json

        from rekall.models import Suggestion, generate_ulid

        ids = [generate_ulid(), generate_ulid()]
        suggestion = Suggestion(
            id=generate_ulid(),
            suggestion_type="link",
            entry_ids=ids,
            score=0.8,
        )

        json_str = suggestion.entry_ids_json()
        parsed = json.loads(json_str)
        assert parsed == ids

    def test_suggestion_from_row(self):
        """Suggestion.from_row() should deserialize from DB row."""
        import json
        from datetime import datetime

        from rekall.models import Suggestion, generate_ulid

        ids = [generate_ulid(), generate_ulid()]
        now = datetime.now()
        row = {
            "id": generate_ulid(),
            "suggestion_type": "link",
            "entry_ids": json.dumps(ids),
            "score": 0.85,
            "reason": "Test reason",
            "status": "pending",
            "created_at": now.isoformat(),
            "resolved_at": None,
        }

        suggestion = Suggestion.from_row(row)
        assert suggestion.entry_ids == ids
        assert suggestion.score == 0.85
        assert suggestion.status == "pending"


class TestStructuredContext:
    """Tests for StructuredContext dataclass (Feature 006)."""

    def test_structured_context_creation_valid(self):
        """StructuredContext should be created with valid required fields."""
        from rekall.models import StructuredContext

        ctx = StructuredContext(
            situation="API timeout sur requêtes > 30s",
            solution="nginx proxy_read_timeout 120s",
            trigger_keywords=["504", "nginx", "timeout"],
        )
        assert ctx.situation == "API timeout sur requêtes > 30s"
        assert ctx.solution == "nginx proxy_read_timeout 120s"
        assert ctx.trigger_keywords == ["504", "nginx", "timeout"]
        assert ctx.extraction_method == "manual"  # default

    def test_structured_context_keywords_normalized(self):
        """Keywords should be lowercase and stripped."""
        from rekall.models import StructuredContext

        ctx = StructuredContext(
            situation="Test situation here",
            solution="Test solution here",
            trigger_keywords=["  NGINX  ", "TimeOut", "  API  "],
        )
        assert ctx.trigger_keywords == ["nginx", "timeout", "api"]

    def test_structured_context_situation_too_short_raises(self):
        """Situation < 5 chars should raise ValueError."""
        import pytest

        from rekall.models import StructuredContext

        with pytest.raises(ValueError, match="situation must be at least 5"):
            StructuredContext(
                situation="abc",  # Too short
                solution="Test solution here",
                trigger_keywords=["test"],
            )

    def test_structured_context_solution_too_short_raises(self):
        """Solution < 5 chars should raise ValueError."""
        import pytest

        from rekall.models import StructuredContext

        with pytest.raises(ValueError, match="solution must be at least 5"):
            StructuredContext(
                situation="Test situation here",
                solution="abc",  # Too short
                trigger_keywords=["test"],
            )

    def test_structured_context_empty_keywords_raises(self):
        """Empty keywords list should raise ValueError."""
        import pytest

        from rekall.models import StructuredContext

        with pytest.raises(ValueError, match="at least 1 trigger keyword"):
            StructuredContext(
                situation="Test situation here",
                solution="Test solution here",
                trigger_keywords=[],
            )

    def test_structured_context_whitespace_keywords_raises(self):
        """Only whitespace keywords should raise ValueError."""
        import pytest

        from rekall.models import StructuredContext

        with pytest.raises(ValueError, match="at least 1 non-empty"):
            StructuredContext(
                situation="Test situation here",
                solution="Test solution here",
                trigger_keywords=["   ", ""],
            )

    def test_structured_context_optional_fields(self):
        """Optional fields should be None by default."""
        from rekall.models import StructuredContext

        ctx = StructuredContext(
            situation="Test situation here",
            solution="Test solution here",
            trigger_keywords=["test"],
        )
        assert ctx.what_failed is None
        assert ctx.conversation_excerpt is None
        assert ctx.files_modified is None
        assert ctx.error_messages is None

    def test_structured_context_with_all_fields(self):
        """StructuredContext should accept all optional fields."""
        from rekall.models import StructuredContext

        ctx = StructuredContext(
            situation="API timeout sur requêtes > 30s",
            solution="nginx proxy_read_timeout 120s",
            trigger_keywords=["504", "nginx"],
            what_failed="Client-side timeout increase didn't work",
            conversation_excerpt="User: I get 504 errors...",
            files_modified=["/etc/nginx/nginx.conf"],
            error_messages=["504 Gateway Timeout"],
            extraction_method="hybrid",
        )
        assert ctx.what_failed == "Client-side timeout increase didn't work"
        assert ctx.files_modified == ["/etc/nginx/nginx.conf"]
        assert ctx.extraction_method == "hybrid"

    def test_structured_context_to_dict(self):
        """to_dict() should serialize all fields."""
        from rekall.models import StructuredContext

        ctx = StructuredContext(
            situation="Test situation here",
            solution="Test solution here",
            trigger_keywords=["test", "example"],
        )
        d = ctx.to_dict()
        assert d["situation"] == "Test situation here"
        assert d["solution"] == "Test solution here"
        assert d["trigger_keywords"] == ["test", "example"]
        assert "created_at" in d

    def test_structured_context_to_json(self):
        """to_json() should produce valid JSON."""
        import json

        from rekall.models import StructuredContext

        ctx = StructuredContext(
            situation="Test situation here",
            solution="Test solution here",
            trigger_keywords=["test"],
        )
        json_str = ctx.to_json()
        parsed = json.loads(json_str)
        assert parsed["situation"] == "Test situation here"

    def test_structured_context_from_dict(self):
        """from_dict() should deserialize correctly."""
        from rekall.models import StructuredContext

        data = {
            "situation": "Test situation here",
            "solution": "Test solution here",
            "trigger_keywords": ["test", "example"],
            "what_failed": "Nothing worked",
        }
        ctx = StructuredContext.from_dict(data)
        assert ctx.situation == "Test situation here"
        assert ctx.what_failed == "Nothing worked"

    def test_structured_context_from_json_string(self):
        """from_json() should parse JSON string."""
        import json

        from rekall.models import StructuredContext

        data = {
            "situation": "Test situation here",
            "solution": "Test solution here",
            "trigger_keywords": ["test"],
        }
        json_str = json.dumps(data)
        ctx = StructuredContext.from_json(json_str)
        assert ctx.situation == "Test situation here"

    def test_structured_context_from_json_dict(self):
        """from_json() should accept dict directly."""
        from rekall.models import StructuredContext

        data = {
            "situation": "Test situation here",
            "solution": "Test solution here",
            "trigger_keywords": ["test"],
        }
        ctx = StructuredContext.from_json(data)
        assert ctx.situation == "Test situation here"

    def test_structured_context_roundtrip(self):
        """to_json() -> from_json() should preserve data."""
        from rekall.models import StructuredContext

        original = StructuredContext(
            situation="API timeout sur requêtes > 30s",
            solution="nginx proxy_read_timeout 120s",
            trigger_keywords=["504", "nginx", "timeout"],
            what_failed="Client-side increase",
            files_modified=["/etc/nginx/nginx.conf"],
        )
        json_str = original.to_json()
        restored = StructuredContext.from_json(json_str)

        assert restored.situation == original.situation
        assert restored.solution == original.solution
        assert restored.trigger_keywords == original.trigger_keywords
        assert restored.what_failed == original.what_failed
        assert restored.files_modified == original.files_modified
