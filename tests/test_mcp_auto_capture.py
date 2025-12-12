"""
Tests d'intégration pour le Mode 2 Auto-Capture.

Feature 018: Auto-Capture Contexte Enrichi
Phase 3: US1 - T016
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rekall.transcript import (
    CandidateExchanges,
    TranscriptMessage,
    get_session_manager,
)
from rekall.transcript.session_manager import SessionManager, SessionData

# Check if MCP is available for integration tests
try:
    from mcp.types import TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Skip decorator for tests requiring MCP
requires_mcp = pytest.mark.skipif(not MCP_AVAILABLE, reason="MCP SDK not installed")


# =============================================================================
# SessionManager Tests
# =============================================================================


class TestSessionManager:
    """Tests for the Mode 2 session manager."""

    @pytest.fixture(autouse=True)
    def setup_session_manager(self):
        """Reset session manager state before each test."""
        manager = get_session_manager()
        manager.clear_all()
        manager.stop_cleanup()
        yield
        manager.clear_all()

    def test_singleton_pattern(self):
        """Session manager should be a singleton."""
        manager1 = get_session_manager()
        manager2 = get_session_manager()
        assert manager1 is manager2

    def test_create_session(self):
        """Test creating a new session."""
        manager = get_session_manager()

        candidates = CandidateExchanges(
            session_id="",
            total_exchanges=10,
            candidates=[
                TranscriptMessage(role="human", content="Test", index=0),
            ],
        )

        session_id = manager.create_session(
            candidates=candidates,
            entry_type="bug",
            title="Test Bug",
            context={"situation": "test", "solution": "fix"},
        )

        assert session_id is not None
        assert len(session_id) == 36  # UUID format
        assert manager.session_count == 1

    def test_get_session(self):
        """Test retrieving a session."""
        manager = get_session_manager()

        candidates = CandidateExchanges(
            session_id="",
            total_exchanges=5,
            candidates=[
                TranscriptMessage(role="human", content="Hello", index=0),
                TranscriptMessage(role="assistant", content="Hi", index=1),
            ],
        )

        session_id = manager.create_session(candidates=candidates, title="Test")
        session = manager.get_session(session_id)

        assert session is not None
        assert session.title == "Test"
        assert len(session.candidates.candidates) == 2

    def test_get_nonexistent_session(self):
        """Test getting a session that doesn't exist."""
        manager = get_session_manager()
        session = manager.get_session("nonexistent-id")
        assert session is None

    def test_delete_session(self):
        """Test deleting a session."""
        manager = get_session_manager()

        candidates = CandidateExchanges(
            session_id="",
            total_exchanges=1,
            candidates=[TranscriptMessage(role="human", content="Test", index=0)],
        )

        session_id = manager.create_session(candidates=candidates)
        assert manager.session_count == 1

        result = manager.delete_session(session_id)
        assert result is True
        assert manager.session_count == 0
        assert manager.get_session(session_id) is None

    def test_delete_nonexistent_session(self):
        """Test deleting a session that doesn't exist."""
        manager = get_session_manager()
        result = manager.delete_session("nonexistent-id")
        assert result is False

    def test_get_selected_messages(self):
        """Test retrieving selected messages by indices."""
        manager = get_session_manager()

        candidates = CandidateExchanges(
            session_id="",
            total_exchanges=5,
            candidates=[
                TranscriptMessage(role="human", content="Msg 0", index=0),
                TranscriptMessage(role="assistant", content="Msg 1", index=1),
                TranscriptMessage(role="human", content="Msg 2", index=2),
                TranscriptMessage(role="assistant", content="Msg 3", index=3),
            ],
        )

        session_id = manager.create_session(candidates=candidates)
        selected = manager.get_selected_messages(session_id, [0, 2])

        assert selected is not None
        assert len(selected) == 2
        assert selected[0].content == "Msg 0"
        assert selected[1].content == "Msg 2"

    def test_format_selected_as_excerpt(self):
        """Test formatting selected messages as excerpt."""
        manager = get_session_manager()

        candidates = CandidateExchanges(
            session_id="",
            total_exchanges=4,
            candidates=[
                TranscriptMessage(role="human", content="Question 1", index=0),
                TranscriptMessage(role="assistant", content="Answer 1", index=1),
                TranscriptMessage(role="human", content="Question 2", index=2),
                TranscriptMessage(role="assistant", content="Answer 2", index=3),
            ],
        )

        session_id = manager.create_session(candidates=candidates)
        excerpt = manager.format_selected_as_excerpt(session_id, [0, 1])

        assert excerpt is not None
        assert "Human: Question 1" in excerpt
        assert "Assistant: Answer 1" in excerpt

    def test_session_expiration(self):
        """Test that expired sessions are not returned."""
        # Use short TTL for test
        manager = SessionManager.__new__(SessionManager)
        manager._initialized = False
        manager.__init__(ttl_seconds=1)  # 1 second TTL
        manager.clear_all()

        candidates = CandidateExchanges(
            session_id="",
            total_exchanges=1,
            candidates=[TranscriptMessage(role="human", content="Test", index=0)],
        )

        session_id = manager.create_session(candidates=candidates)
        assert manager.get_session(session_id) is not None

        # Wait for expiration
        import time
        time.sleep(1.5)

        assert manager.get_session(session_id) is None


# =============================================================================
# MCP Handler Integration Tests
# =============================================================================


@requires_mcp
class TestMCPAutoCapture:
    """Integration tests for MCP auto-capture handlers."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        db = MagicMock()
        db.add = MagicMock()
        db.store_structured_context = MagicMock()
        db.store_context = MagicMock()
        db.close = MagicMock()
        return db

    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = MagicMock()
        config.smart_embeddings_enabled = False
        return config

    @pytest.fixture
    def sample_transcript_path(self, tmp_path):
        """Create a sample Claude transcript file."""
        content = "\n".join([
            json.dumps({"type": "human", "message": {"content": "I have a bug"}}),
            json.dumps({"type": "assistant", "message": {"content": "Let me help"}}),
            json.dumps({"type": "human", "message": {"content": "It's with nginx"}}),
            json.dumps({"type": "assistant", "message": {"content": "Here's the fix..."}}),
        ])
        file = tmp_path / ".claude" / "projects" / "test" / "transcript.jsonl"
        file.parent.mkdir(parents=True)
        file.write_text(content)
        return str(file)

    @pytest.fixture(autouse=True)
    def cleanup_sessions(self):
        """Clean up sessions after each test."""
        yield
        get_session_manager().clear_all()

    @pytest.mark.asyncio
    async def test_mode2_step1_returns_candidates(self, sample_transcript_path):
        """Test Mode 2 Step 1 returns candidate exchanges."""
        from rekall.mcp_server import _handle_auto_capture_step1

        args = {
            "type": "bug",
            "title": "Nginx bug fix",
            "context": {"situation": "Bug found", "solution": "Fixed it"},
            "auto_capture_conversation": True,
            "_transcript_path": sample_transcript_path,
        }

        result = await _handle_auto_capture_step1(args)

        assert len(result) == 1
        response = json.loads(result[0].text)

        assert response["status"] == "candidates_ready"
        assert "session_id" in response
        assert "candidates" in response
        assert len(response["candidates"]) == 4
        assert "instruction" in response

    @pytest.mark.asyncio
    async def test_mode2_step1_no_transcript_path(self):
        """Test Mode 2 Step 1 returns error when no transcript path."""
        from rekall.mcp_server import _handle_auto_capture_step1

        args = {
            "type": "bug",
            "title": "Test",
            "context": {"situation": "test", "solution": "test"},
            "auto_capture_conversation": True,
        }

        result = await _handle_auto_capture_step1(args)

        response = json.loads(result[0].text)
        assert response["status"] == "error"
        assert response["error_code"] == "TRANSCRIPT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_mode2_step1_transcript_not_found(self, tmp_path):
        """Test Mode 2 Step 1 returns error when transcript doesn't exist."""
        from rekall.mcp_server import _handle_auto_capture_step1

        args = {
            "type": "bug",
            "title": "Test",
            "context": {"situation": "test", "solution": "test"},
            "auto_capture_conversation": True,
            "_transcript_path": str(tmp_path / "nonexistent.jsonl"),
        }

        result = await _handle_auto_capture_step1(args)

        response = json.loads(result[0].text)
        assert response["status"] == "error"
        assert response["error_code"] == "TRANSCRIPT_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_mode2_step2_creates_entry(self, sample_transcript_path, mock_db, mock_config):
        """Test Mode 2 Step 2 creates entry with selected exchanges."""
        from rekall.mcp_server import _handle_auto_capture_step1, _handle_auto_capture_step2

        # Step 1: Get candidates
        args_step1 = {
            "type": "bug",
            "title": "Nginx bug fix",
            "context": {"situation": "Bug found", "solution": "Fixed it"},
            "auto_capture_conversation": True,
            "_transcript_path": sample_transcript_path,
        }

        result1 = await _handle_auto_capture_step1(args_step1)
        response1 = json.loads(result1[0].text)
        session_id = response1["session_id"]

        # Step 2: Finalize with selected indices
        # Patch at the source module level since imports are local
        with patch("rekall.mcp_server.get_db", return_value=mock_db):
            with patch("rekall.config.get_config", return_value=mock_config):
                args_step2 = {
                    "type": "bug",
                    "title": "Nginx bug fix",
                    "context": {"situation": "Bug found", "solution": "Fixed it"},
                    "conversation_excerpt_indices": [0, 1],
                    "_session_id": session_id,
                }

                result2 = await _handle_auto_capture_step2(args_step2)

        response2 = json.loads(result2[0].text.split("\n\n")[0])  # Get JSON part only

        assert response2["status"] == "success"
        assert "entry_id" in response2
        assert response2["context_summary"]["conversation_captured"] is True
        assert response2["context_summary"]["exchanges_selected"] == 2

        # Verify DB calls
        mock_db.add.assert_called_once()
        mock_db.store_structured_context.assert_called_once()
        mock_db.store_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_mode2_step2_session_not_found(self, mock_db, mock_config):
        """Test Mode 2 Step 2 returns error when session not found."""
        from rekall.mcp_server import _handle_auto_capture_step2

        args = {
            "type": "bug",
            "title": "Test",
            "context": {"situation": "test", "solution": "test"},
            "conversation_excerpt_indices": [0, 1],
            "_session_id": "nonexistent-session-id",
        }

        result = await _handle_auto_capture_step2(args)

        response = json.loads(result[0].text)
        assert response["status"] == "error"
        assert response["error_code"] == "SESSION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_mode2_step2_invalid_indices(self, sample_transcript_path, mock_db, mock_config):
        """Test Mode 2 Step 2 returns error for invalid indices."""
        from rekall.mcp_server import _handle_auto_capture_step1, _handle_auto_capture_step2

        # Step 1: Get candidates (4 messages, indices 0-3)
        args_step1 = {
            "type": "bug",
            "title": "Test",
            "context": {"situation": "test", "solution": "test"},
            "auto_capture_conversation": True,
            "_transcript_path": sample_transcript_path,
        }

        result1 = await _handle_auto_capture_step1(args_step1)
        response1 = json.loads(result1[0].text)
        session_id = response1["session_id"]

        # Step 2: Try with invalid indices
        args_step2 = {
            "type": "bug",
            "title": "Test",
            "context": {"situation": "test", "solution": "test"},
            "conversation_excerpt_indices": [0, 10, 20],  # 10 and 20 are invalid
            "_session_id": session_id,
        }

        result2 = await _handle_auto_capture_step2(args_step2)

        response2 = json.loads(result2[0].text)
        assert response2["status"] == "error"
        assert response2["error_code"] == "VALIDATION_ERROR"
        assert "Invalid indices" in response2["message"]


# =============================================================================
# End-to-End Flow Tests
# =============================================================================


@requires_mcp
class TestAutoCapturE2E:
    """End-to-end tests for the full auto-capture workflow."""

    @pytest.fixture
    def complex_transcript(self, tmp_path):
        """Create a more complex transcript for E2E testing."""
        messages = [
            {"type": "human", "message": {"content": "Can you help me with a React bug?"}},
            {"type": "assistant", "message": {"content": "Sure, what's the issue?"}},
            {"type": "human", "message": {"content": "useState isn't updating correctly"}},
            {"type": "assistant", "message": {"content": "Let me check your code..."}},
            {"type": "human", "message": {"content": "Here's the component"}},
            {"type": "assistant", "message": {"content": "I see the problem - you're mutating state directly"}},
            {"type": "human", "message": {"content": "How do I fix it?"}},
            {"type": "assistant", "message": {"content": "Use spread operator: setItems([...items, newItem])"}},
            {"type": "human", "message": {"content": "That fixed it, thanks!"}},
            {"type": "assistant", "message": {"content": "You're welcome! Remember to always create new references."}},
        ]

        file = tmp_path / "react_debug.jsonl"
        file.write_text("\n".join(json.dumps(m) for m in messages))
        return str(file)

    @pytest.fixture(autouse=True)
    def cleanup_sessions(self):
        yield
        get_session_manager().clear_all()

    @pytest.mark.asyncio
    async def test_full_workflow_mode1(self, mock_db, mock_config):
        """Test Mode 1 workflow (direct conversation_excerpt)."""
        from rekall.mcp_server import _handle_add

        with patch("rekall.mcp_server.get_db", return_value=mock_db):
            with patch("rekall.config.get_config", return_value=mock_config):
                args = {
                    "type": "bug",
                    "title": "React useState mutation bug",
                    "content": "Don't mutate state directly in React",
                    "context": {
                        "situation": "useState not updating UI",
                        "solution": "Use spread operator for immutable updates",
                        "trigger_keywords": ["react", "useState", "mutation"],
                        "conversation_excerpt": "Human: useState isn't updating\nAssistant: You're mutating state directly",
                    },
                }

                result = await _handle_add(args)

        # Should go through standard flow (Mode 1)
        assert "Entry created:" in result[0].text
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_workflow_mode2(self, complex_transcript, mock_db, mock_config):
        """Test complete Mode 2 workflow (step 1 + step 2)."""
        from rekall.mcp_server import _handle_add

        # Step 1: Request auto-capture
        args_step1 = {
            "type": "bug",
            "title": "React useState mutation bug",
            "context": {
                "situation": "useState not updating UI",
                "solution": "Use spread operator for immutable updates",
            },
            "auto_capture_conversation": True,
            "_transcript_path": complex_transcript,
        }

        result1 = await _handle_add(args_step1)
        response1 = json.loads(result1[0].text)

        assert response1["status"] == "candidates_ready"
        session_id = response1["session_id"]
        candidates = response1["candidates"]

        # Verify we got the expected candidates
        assert len(candidates) == 10
        assert candidates[0]["content"].startswith("Can you help me")

        # Step 2: Select relevant exchanges and finalize
        with patch("rekall.mcp_server.get_db", return_value=mock_db):
            with patch("rekall.config.get_config", return_value=mock_config):
                # Select exchanges 2,3,5,7 (the bug discussion)
                args_step2 = {
                    "type": "bug",
                    "title": "React useState mutation bug",
                    "context": {
                        "situation": "useState not updating UI",
                        "solution": "Use spread operator for immutable updates",
                    },
                    "conversation_excerpt_indices": [2, 3, 5, 7],
                    "_session_id": session_id,
                }

                result2 = await _handle_add(args_step2)

        response2 = json.loads(result2[0].text.split("\n\n")[0])

        assert response2["status"] == "success"
        assert response2["context_summary"]["exchanges_selected"] == 4

        # Verify the entry was created with correct context
        add_call = mock_db.add.call_args
        entry = add_call[0][0]
        assert entry.title == "React useState mutation bug"
        assert entry.type == "bug"

        # Verify structured context was stored
        context_call = mock_db.store_structured_context.call_args
        stored_context = context_call[0][1]
        assert "useState isn't updating" in stored_context.conversation_excerpt
        assert "spread operator" in stored_context.conversation_excerpt

    @pytest.fixture
    def mock_db(self):
        """Create a mock database for E2E tests."""
        db = MagicMock()
        db.add = MagicMock()
        db.store_structured_context = MagicMock()
        db.store_context = MagicMock()
        db.close = MagicMock()
        return db

    @pytest.fixture
    def mock_config(self):
        """Create a mock config for E2E tests."""
        config = MagicMock()
        config.smart_embeddings_enabled = False
        config.smart_embeddings_context_mode = "optional"
        return config
