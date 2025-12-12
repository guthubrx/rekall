"""
Tests unitaires pour les parsers de transcript.

Feature 018: Auto-Capture Contexte Enrichi
Phase 3: US1 - T015
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from rekall.transcript import (
    TranscriptFormat,
    TranscriptMessage,
    CandidateExchanges,
    ClaudeTranscriptParser,
    ClineTranscriptParser,
    ContinueTranscriptParser,
    GenericJsonParser,
    detect_format,
    get_parser,
    get_parser_for_path,
)
from rekall.transcript.parser_base import ParserError


# =============================================================================
# Fixtures - Sample transcript data
# =============================================================================


@pytest.fixture
def claude_jsonl_content():
    """Sample Claude Code JSONL transcript."""
    messages = [
        {"type": "human", "message": {"content": "Hello, can you help me?"}, "timestamp": "2025-01-15T10:30:00Z"},
        {"type": "assistant", "message": {"content": "Of course! What do you need?"}, "timestamp": "2025-01-15T10:30:05Z"},
        {"type": "human", "message": {"content": "I have a bug with nginx"}, "timestamp": "2025-01-15T10:31:00Z"},
        {"type": "assistant", "message": {"content": "Let me help you debug that."}, "timestamp": "2025-01-15T10:31:10Z"},
    ]
    return "\n".join(json.dumps(m) for m in messages)


@pytest.fixture
def cline_json_content():
    """Sample Cline JSON transcript."""
    return json.dumps({
        "conversation": [
            {"role": "user", "content": "What's the weather like?", "ts": 1705312200000},
            {"role": "assistant", "content": "I can't check weather, but I can help with code!", "ts": 1705312205000},
            {"role": "user", "content": "Fix my Python script", "ts": 1705312300000},
            {"role": "assistant", "content": "Sure, show me the script.", "ts": 1705312310000},
        ]
    })


@pytest.fixture
def continue_json_content():
    """Sample Continue.dev JSON transcript."""
    return json.dumps({
        "sessions": [
            {
                "messages": [
                    {"role": "user", "content": "Explain this function"},
                    {"role": "assistant", "content": "This function does X, Y, Z..."},
                ]
            },
            {
                "messages": [
                    {"role": "user", "content": "Now optimize it"},
                    {"role": "assistant", "content": "Here's an optimized version..."},
                ]
            }
        ]
    })


@pytest.fixture
def generic_json_content():
    """Sample generic JSON transcript."""
    return json.dumps({
        "messages": [
            {"role": "human", "text": "Generic message 1"},
            {"role": "bot", "text": "Generic response 1"},
            {"role": "human", "text": "Generic message 2"},
        ]
    })


# =============================================================================
# ClaudeTranscriptParser Tests
# =============================================================================


class TestClaudeTranscriptParser:
    """Tests for Claude Code JSONL parser."""

    def test_format_property(self):
        parser = ClaudeTranscriptParser()
        assert parser.format == TranscriptFormat.CLAUDE_JSONL

    def test_parse_valid_jsonl(self, claude_jsonl_content, tmp_path):
        parser = ClaudeTranscriptParser()
        file = tmp_path / "transcript.jsonl"
        file.write_text(claude_jsonl_content)

        messages = parser.parse(file)

        assert len(messages) == 4
        assert messages[0].role == "human"
        assert messages[0].content == "Hello, can you help me?"
        assert messages[1].role == "assistant"
        assert messages[3].index == 3

    def test_parse_last_n(self, claude_jsonl_content, tmp_path):
        parser = ClaudeTranscriptParser()
        file = tmp_path / "transcript.jsonl"
        file.write_text(claude_jsonl_content)

        messages, total = parser.parse_last_n(file, n=2)

        assert len(messages) == 2
        assert total == 4
        # Should get the last 2 messages
        assert messages[0].content == "I have a bug with nginx"
        assert messages[1].content == "Let me help you debug that."

    def test_parse_file_not_found(self):
        parser = ClaudeTranscriptParser()
        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.jsonl"))

    def test_parse_invalid_jsonl_returns_empty(self, tmp_path):
        """Parser skips invalid lines and returns empty if all invalid."""
        parser = ClaudeTranscriptParser()
        file = tmp_path / "invalid.jsonl"
        file.write_text("not valid json\nalso invalid")

        # Parser skips invalid lines gracefully
        messages = parser.parse(file)
        assert len(messages) == 0  # No valid messages

    def test_normalize_role_human(self):
        parser = ClaudeTranscriptParser()
        assert parser.normalize_role("human") == "human"
        assert parser.normalize_role("user") == "human"
        assert parser.normalize_role("Human") == "human"
        assert parser.normalize_role("USER") == "human"

    def test_normalize_role_assistant(self):
        parser = ClaudeTranscriptParser()
        assert parser.normalize_role("assistant") == "assistant"
        assert parser.normalize_role("bot") == "assistant"
        assert parser.normalize_role("ai") == "assistant"
        assert parser.normalize_role("claude") == "assistant"


# =============================================================================
# ClineTranscriptParser Tests
# =============================================================================


class TestClineTranscriptParser:
    """Tests for Cline JSON parser."""

    def test_format_property(self):
        parser = ClineTranscriptParser()
        assert parser.format == TranscriptFormat.CLINE_JSON

    def test_parse_valid_json(self, cline_json_content, tmp_path):
        parser = ClineTranscriptParser()
        file = tmp_path / "conversation.json"
        file.write_text(cline_json_content)

        messages = parser.parse(file)

        assert len(messages) == 4
        assert messages[0].role == "human"
        assert messages[0].content == "What's the weather like?"
        assert messages[1].role == "assistant"
        # Check timestamp conversion (milliseconds)
        assert messages[0].timestamp is not None

    def test_parse_array_format(self, tmp_path):
        """Test direct array format (without wrapper object)."""
        parser = ClineTranscriptParser()
        content = json.dumps([
            {"role": "user", "content": "Direct array message"},
            {"role": "assistant", "content": "Response"},
        ])
        file = tmp_path / "array.json"
        file.write_text(content)

        messages = parser.parse(file)

        assert len(messages) == 2
        assert messages[0].content == "Direct array message"

    def test_parse_last_n(self, cline_json_content, tmp_path):
        parser = ClineTranscriptParser()
        file = tmp_path / "conversation.json"
        file.write_text(cline_json_content)

        messages, total = parser.parse_last_n(file, n=2)

        assert len(messages) == 2
        assert total == 4


# =============================================================================
# ContinueTranscriptParser Tests
# =============================================================================


class TestContinueTranscriptParser:
    """Tests for Continue.dev JSON parser."""

    def test_format_property(self):
        parser = ContinueTranscriptParser()
        assert parser.format == TranscriptFormat.CONTINUE_JSON

    def test_parse_sessions_format(self, continue_json_content, tmp_path):
        parser = ContinueTranscriptParser()
        file = tmp_path / "continue.json"
        file.write_text(continue_json_content)

        messages = parser.parse(file)

        # Should combine messages from both sessions
        assert len(messages) == 4
        assert messages[0].content == "Explain this function"
        assert messages[2].content == "Now optimize it"

    def test_parse_direct_messages_format(self, tmp_path):
        """Test direct messages format (without sessions wrapper)."""
        parser = ContinueTranscriptParser()
        content = json.dumps({
            "messages": [
                {"role": "user", "content": "Direct message"},
                {"role": "assistant", "content": "Direct response"},
            ]
        })
        file = tmp_path / "direct.json"
        file.write_text(content)

        messages = parser.parse(file)

        assert len(messages) == 2


# =============================================================================
# GenericJsonParser Tests
# =============================================================================


class TestGenericJsonParser:
    """Tests for generic JSON parser (fallback)."""

    def test_format_property(self):
        parser = GenericJsonParser()
        assert parser.format == TranscriptFormat.RAW_JSON

    def test_parse_messages_key(self, generic_json_content, tmp_path):
        parser = GenericJsonParser()
        file = tmp_path / "generic.json"
        file.write_text(generic_json_content)

        messages = parser.parse(file)

        assert len(messages) == 3
        assert messages[0].role == "human"
        assert messages[1].role == "assistant"  # bot normalized to assistant

    def test_parse_nested_structure(self, tmp_path):
        """Test finding messages in nested structure."""
        parser = GenericJsonParser()
        content = json.dumps({
            "data": {
                "chat": {
                    "history": [
                        {"from": "user", "body": "Nested message"},
                        {"from": "assistant", "body": "Nested response"},
                    ]
                }
            }
        })
        file = tmp_path / "nested.json"
        file.write_text(content)

        messages = parser.parse(file)

        assert len(messages) == 2
        assert messages[0].content == "Nested message"

    def test_parse_various_content_keys(self, tmp_path):
        """Test different content field names."""
        parser = GenericJsonParser()

        # Test 'text' key
        content = json.dumps([
            {"role": "user", "text": "Text content"},
            {"role": "assistant", "message": "Message content"},
        ])
        file = tmp_path / "various.json"
        file.write_text(content)

        messages = parser.parse(file)

        assert len(messages) == 2
        assert messages[0].content == "Text content"
        assert messages[1].content == "Message content"


# =============================================================================
# Format Detection Tests
# =============================================================================


class TestFormatDetection:
    """Tests for automatic format detection."""

    def test_detect_claude_by_path(self):
        path = Path("/Users/test/.claude/projects/abc/conversation.jsonl")
        assert detect_format(path) == TranscriptFormat.CLAUDE_JSONL

    def test_detect_claude_by_extension(self):
        path = Path("/some/path/transcript.jsonl")
        assert detect_format(path) == TranscriptFormat.CLAUDE_JSONL

    def test_detect_cline_by_path(self):
        path = Path("/Users/test/.vscode/extensions/saoudrizwan.claude-dev-1.0/history.json")
        assert detect_format(path) == TranscriptFormat.CLINE_JSON

    def test_detect_cline_conversation_name(self):
        path = Path("/some/path/api_conversation_history.json")
        assert detect_format(path) == TranscriptFormat.CLINE_JSON

    def test_detect_continue_by_path(self):
        path = Path("/Users/test/.continue/dev_data/sessions.json")
        assert detect_format(path) == TranscriptFormat.CONTINUE_JSON

    def test_detect_roo_code_by_path(self):
        path = Path("/Users/test/.vscode/extensions/rooveterinaryinc.roo-cline-1.0/history.json")
        assert detect_format(path) == TranscriptFormat.CLINE_JSON  # Same format as Cline

    def test_detect_fallback_raw_json(self):
        path = Path("/random/path/data.json")
        assert detect_format(path) == TranscriptFormat.RAW_JSON

    def test_detect_with_format_hint(self):
        path = Path("/random/path/file.txt")
        assert detect_format(path, format_hint="claude-jsonl") == TranscriptFormat.CLAUDE_JSONL

    def test_detect_invalid_hint_falls_back(self):
        path = Path("/random/path/file.jsonl")
        # Invalid hint should be ignored, falls back to extension detection
        assert detect_format(path, format_hint="invalid-format") == TranscriptFormat.CLAUDE_JSONL


# =============================================================================
# Parser Factory Tests
# =============================================================================


class TestParserFactory:
    """Tests for parser factory functions."""

    def test_get_parser_claude(self):
        parser = get_parser(TranscriptFormat.CLAUDE_JSONL)
        assert isinstance(parser, ClaudeTranscriptParser)

    def test_get_parser_cline(self):
        parser = get_parser(TranscriptFormat.CLINE_JSON)
        assert isinstance(parser, ClineTranscriptParser)

    def test_get_parser_continue(self):
        parser = get_parser(TranscriptFormat.CONTINUE_JSON)
        assert isinstance(parser, ContinueTranscriptParser)

    def test_get_parser_generic(self):
        parser = get_parser(TranscriptFormat.RAW_JSON)
        assert isinstance(parser, GenericJsonParser)

    def test_get_parser_for_path(self, claude_jsonl_content, tmp_path):
        file = tmp_path / ".claude" / "projects" / "test" / "transcript.jsonl"
        file.parent.mkdir(parents=True)
        file.write_text(claude_jsonl_content)

        parser, detected_format = get_parser_for_path(file)

        assert detected_format == TranscriptFormat.CLAUDE_JSONL
        assert isinstance(parser, ClaudeTranscriptParser)


# =============================================================================
# TranscriptMessage Tests
# =============================================================================


class TestTranscriptMessage:
    """Tests for TranscriptMessage dataclass."""

    def test_to_dict(self):
        msg = TranscriptMessage(
            role="human",
            content="Test content",
            timestamp=datetime(2025, 1, 15, 10, 30, 0),
            index=5,
        )
        d = msg.to_dict()

        assert d["role"] == "human"
        assert d["content"] == "Test content"
        assert d["index"] == 5
        assert "timestamp" in d

    def test_to_dict_no_timestamp(self):
        msg = TranscriptMessage(
            role="assistant",
            content="No timestamp",
            index=0,
        )
        d = msg.to_dict()

        assert d["timestamp"] is None

    def test_truncate_content(self):
        long_content = "x" * 1000
        msg = TranscriptMessage(
            role="human",
            content=long_content,
            index=0,
        )
        d = msg.to_dict()

        # to_dict tronque à 500 caractères par défaut
        assert len(d["content"]) == 503  # 500 + "..."
        assert d["content"].endswith("...")


# =============================================================================
# CandidateExchanges Tests
# =============================================================================


class TestCandidateExchanges:
    """Tests for CandidateExchanges dataclass."""

    @pytest.fixture
    def sample_candidates(self):
        return CandidateExchanges(
            session_id="test-session-123",
            total_exchanges=100,
            candidates=[
                TranscriptMessage(role="human", content="Message 0", index=0),
                TranscriptMessage(role="assistant", content="Response 0", index=1),
                TranscriptMessage(role="human", content="Message 1", index=2),
                TranscriptMessage(role="assistant", content="Response 1", index=3),
                TranscriptMessage(role="human", content="Message 2", index=4),
            ],
        )

    def test_to_mcp_response(self, sample_candidates):
        response = sample_candidates.to_mcp_response()

        assert response["status"] == "candidates_ready"
        assert response["session_id"] == "test-session-123"
        assert response["total_exchanges"] == 100
        assert len(response["candidates"]) == 5

    def test_get_by_indices(self, sample_candidates):
        selected = sample_candidates.get_by_indices([0, 2, 4])

        assert len(selected) == 3
        assert selected[0].content == "Message 0"
        assert selected[1].content == "Message 1"
        assert selected[2].content == "Message 2"

    def test_get_by_indices_out_of_range(self, sample_candidates):
        selected = sample_candidates.get_by_indices([0, 10, 20])

        # Should only return valid indices
        assert len(selected) == 1
        assert selected[0].content == "Message 0"

    def test_format_as_excerpt(self, sample_candidates):
        excerpt = sample_candidates.format_as_excerpt([0, 1])

        assert "Human:" in excerpt
        assert "Message 0" in excerpt
        assert "Assistant:" in excerpt
        assert "Response 0" in excerpt

    def test_format_as_excerpt_empty(self, sample_candidates):
        excerpt = sample_candidates.format_as_excerpt([])

        assert excerpt == ""
