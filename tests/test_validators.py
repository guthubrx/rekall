"""Tests for Pydantic validation models."""

import pytest
from pydantic import ValidationError

from rekall.constants import (
    MAX_CONTENT_LENGTH,
    MAX_TAG_LENGTH,
    MAX_TAGS_COUNT,
    MAX_TITLE_LENGTH,
)
from rekall.validators import (
    ArchiveEntryValidator,
    ArchiveMetadataValidator,
    ArchiveValidator,
    ConfigValidator,
    EntryValidator,
    validate_archive_entry,
    validate_entry,
)


class TestEntryValidator:
    """Tests for EntryValidator model."""

    def test_valid_entry(self):
        """Test validation of a valid entry."""
        entry = EntryValidator(
            title="Fix circular import bug",
            content="The issue was caused by importing module A in module B...",
            tags=["python", "import", "bug-fix"],
            entry_type="bug",
            confidence=4,
            project="my-project",
        )
        assert entry.title == "Fix circular import bug"
        assert entry.entry_type == "bug"
        assert entry.confidence == 4
        assert len(entry.tags) == 3

    def test_minimal_entry(self):
        """Test validation with minimal required fields."""
        entry = EntryValidator(title="Just a title")
        assert entry.title == "Just a title"
        assert entry.content == ""
        assert entry.tags == []
        assert entry.entry_type == "note"
        assert entry.confidence == 2
        assert entry.project is None

    def test_title_required(self):
        """Test that title is required and cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            EntryValidator(title="")
        errors = exc_info.value.errors()
        assert any("title" in str(e["loc"]) for e in errors)

    def test_title_too_long(self):
        """Test that overly long titles are rejected."""
        long_title = "x" * (MAX_TITLE_LENGTH + 1)
        with pytest.raises(ValidationError) as exc_info:
            EntryValidator(title=long_title)
        errors = exc_info.value.errors()
        assert any("title" in str(e["loc"]) for e in errors)

    def test_title_whitespace_stripped(self):
        """Test that title whitespace is stripped."""
        entry = EntryValidator(title="  spaced title  ")
        assert entry.title == "spaced title"

    def test_content_too_long(self):
        """Test that overly long content is rejected."""
        long_content = "x" * (MAX_CONTENT_LENGTH + 1)
        with pytest.raises(ValidationError) as exc_info:
            EntryValidator(title="Title", content=long_content)
        errors = exc_info.value.errors()
        assert any("content" in str(e["loc"]) for e in errors)

    def test_tags_normalized(self):
        """Test that tags are lowercased and stripped."""
        entry = EntryValidator(
            title="Test",
            tags=["  Python  ", "IMPORT", "  bug-fix  "],
        )
        assert entry.tags == ["python", "import", "bug-fix"]

    def test_tags_empty_removed(self):
        """Test that empty tags are removed."""
        entry = EntryValidator(
            title="Test",
            tags=["valid", "", "  ", "also-valid"],
        )
        assert entry.tags == ["valid", "also-valid"]

    def test_tag_too_long(self):
        """Test that overly long tags are rejected."""
        long_tag = "x" * (MAX_TAG_LENGTH + 1)
        with pytest.raises(ValidationError) as exc_info:
            EntryValidator(title="Test", tags=[long_tag])
        errors = exc_info.value.errors()
        assert any("Tag too long" in str(e["msg"]) for e in errors)

    def test_too_many_tags(self):
        """Test that too many tags are rejected."""
        many_tags = [f"tag{i}" for i in range(MAX_TAGS_COUNT + 1)]
        with pytest.raises(ValidationError) as exc_info:
            EntryValidator(title="Test", tags=many_tags)
        errors = exc_info.value.errors()
        assert any("tags" in str(e["loc"]) for e in errors)

    def test_invalid_entry_type(self):
        """Test that invalid entry types are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            EntryValidator(title="Test", entry_type="invalid")
        errors = exc_info.value.errors()
        assert any("entry_type" in str(e["loc"]) for e in errors)

    def test_valid_entry_types(self):
        """Test all valid entry types."""
        valid_types = ["bug", "pattern", "decision", "config", "pitfall", "reference", "note"]
        for entry_type in valid_types:
            entry = EntryValidator(title="Test", entry_type=entry_type)
            assert entry.entry_type == entry_type

    def test_confidence_out_of_range(self):
        """Test that confidence outside 0-5 is rejected."""
        with pytest.raises(ValidationError):
            EntryValidator(title="Test", confidence=-1)
        with pytest.raises(ValidationError):
            EntryValidator(title="Test", confidence=6)

    def test_confidence_valid_range(self):
        """Test valid confidence values."""
        for conf in range(6):
            entry = EntryValidator(title="Test", confidence=conf)
            assert entry.confidence == conf


class TestConfigValidator:
    """Tests for ConfigValidator model."""

    def test_valid_config(self):
        """Test validation of valid config."""
        config = ConfigValidator(
            db_path="/path/to/db",
            active_integrations=["vscode", "cursor"],
            embeddings_provider="ollama",
            language="en",
        )
        assert config.db_path == "/path/to/db"
        assert len(config.active_integrations) == 2

    def test_default_config(self):
        """Test default config values."""
        config = ConfigValidator()
        assert config.db_path is None
        assert config.active_integrations == []
        assert config.language == "en"

    def test_invalid_language_code(self):
        """Test that invalid language codes are rejected."""
        with pytest.raises(ValidationError):
            ConfigValidator(language="invalid")
        with pytest.raises(ValidationError):
            ConfigValidator(language="english")

    def test_valid_language_codes(self):
        """Test valid language code formats."""
        ConfigValidator(language="en")
        ConfigValidator(language="fr")
        ConfigValidator(language="de")
        ConfigValidator(language="en-US")
        ConfigValidator(language="fr-CA")


class TestArchiveValidator:
    """Tests for archive validation models."""

    def test_valid_archive_metadata(self):
        """Test validation of valid archive metadata."""
        from datetime import datetime

        metadata = ArchiveMetadataValidator(
            version="0.3.0",
            created_at=datetime.now(),
            entry_count=10,
            checksum="abc123",
        )
        assert metadata.version == "0.3.0"
        assert metadata.entry_count == 10

    def test_invalid_version_format(self):
        """Test that invalid version formats are rejected."""
        from datetime import datetime

        with pytest.raises(ValidationError):
            ArchiveMetadataValidator(
                version="invalid",
                created_at=datetime.now(),
                entry_count=0,
            )
        with pytest.raises(ValidationError):
            ArchiveMetadataValidator(
                version="1.0",  # Missing patch version
                created_at=datetime.now(),
                entry_count=0,
            )

    def test_valid_archive_entry(self):
        """Test validation of valid archive entry."""
        entry = ArchiveEntryValidator(
            id="01234567-89ab-cdef-0123-456789abcdef",
            title="Test entry",
            content="Content here",
            tags=["test"],
            entry_type="bug",
            confidence=3,
            created_at="2025-01-01T00:00:00",
        )
        assert entry.title == "Test entry"

    def test_complete_archive(self):
        """Test validation of complete archive."""
        from datetime import datetime

        archive = ArchiveValidator(
            metadata=ArchiveMetadataValidator(
                version="0.3.0",
                created_at=datetime.now(),
                entry_count=1,
            ),
            entries=[
                ArchiveEntryValidator(
                    id="test-id",
                    title="Test",
                    content="",
                    created_at="2025-01-01T00:00:00",
                )
            ],
        )
        assert len(archive.entries) == 1


class TestValidateFunctions:
    """Tests for validate_* helper functions."""

    def test_validate_entry_success(self):
        """Test validate_entry with valid data."""
        data = {
            "title": "Test entry",
            "content": "Some content",
            "tags": ["python"],
            "entry_type": "bug",
            "confidence": 3,
        }
        entry = validate_entry(data)
        assert entry.title == "Test entry"
        assert entry.entry_type == "bug"

    def test_validate_entry_failure(self):
        """Test validate_entry with invalid data."""
        data = {"title": ""}  # Empty title
        with pytest.raises(ValidationError):
            validate_entry(data)

    def test_validate_archive_entry_success(self):
        """Test validate_archive_entry with valid data."""
        data = {
            "id": "test-id",
            "title": "Test",
            "content": "Content",
            "created_at": "2025-01-01T00:00:00",
        }
        entry = validate_archive_entry(data)
        assert entry.id == "test-id"
