"""
Test suite for AdvisorService - Business logic for advisor chat operations
Tests following TDD principles and NO FALLBACK logic
"""
import pytest
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from src.services.advisor_service import AdvisorService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    yield db_path

    # Cleanup
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def advisor_service(temp_db):
    """Create AdvisorService with temporary database."""
    return AdvisorService(db_path=temp_db)


@pytest.fixture
def mock_openai_key():
    """Mock OpenAI API key environment variable."""
    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key-123'}):
        yield


class TestAdvisorServiceInit:
    """Test AdvisorService initialization."""

    def test_init_with_valid_db_path(self, temp_db):
        """Should initialize successfully with valid database path."""
        service = AdvisorService(db_path=temp_db)
        assert service.db_path == temp_db
        assert service.session_manager is not None

    def test_init_fails_with_empty_db_path(self):
        """Should fail fast with empty database path."""
        with pytest.raises(ValueError, match="Database path is required"):
            AdvisorService(db_path="")

    def test_init_fails_with_none_db_path(self):
        """Should fail fast with None database path."""
        with pytest.raises(ValueError, match="Database path is required"):
            AdvisorService(db_path=None)


class TestAdvisorServiceChat:
    """Test chat functionality - the main entry point."""

    @pytest.mark.asyncio
    async def test_chat_requires_advisor_id(self, advisor_service):
        """Should fail fast without advisor_id."""
        with pytest.raises(ValueError, match="advisor_id and message are required"):
            await advisor_service.chat(advisor_id="", message="hello")

    @pytest.mark.asyncio
    async def test_chat_requires_message(self, advisor_service):
        """Should fail fast without message."""
        with pytest.raises(ValueError, match="advisor_id and message are required"):
            await advisor_service.chat(advisor_id="ADV001", message="")

    @pytest.mark.asyncio
    async def test_chat_handles_empty_message(self, advisor_service):
        """Should return helpful response for empty/whitespace message."""
        result = await advisor_service.chat(
            advisor_id="ADV001",
            message="   "
        )

        assert result["response"] == "I'm here to help with borrower workflows. What would you like to do?"
        assert "session_id" in result

    @pytest.mark.asyncio
    @patch('src.services.advisor_service.AdvisorAgent')
    async def test_chat_creates_new_session_when_none_provided(self, mock_agent_class, advisor_service, mock_openai_key):
        """Should create new session when no session_id provided."""
        # Mock agent instance
        mock_agent = AsyncMock()
        mock_agent.process_message.return_value = "Hello! Ready to help with workflows."
        mock_agent_class.return_value = mock_agent

        result = await advisor_service.chat(
            advisor_id="ADV001",
            message="Hello"
        )

        assert "session_id" in result
        assert result["advisor_id"] == "ADV001"
        assert result["response"] == "Hello! Ready to help with workflows."

    @pytest.mark.asyncio
    @patch('src.services.advisor_service.AdvisorAgent')
    async def test_chat_resumes_existing_session(self, mock_agent_class, advisor_service, mock_openai_key):
        """Should resume existing session when session_id provided."""
        # Mock agent instance
        mock_agent = AsyncMock()
        mock_agent.process_message.return_value = "Continuing our conversation..."
        mock_agent_class.return_value = mock_agent

        # First call to create session
        first_result = await advisor_service.chat(
            advisor_id="ADV001",
            message="Hello"
        )
        session_id = first_result["session_id"]

        # Second call to resume session
        second_result = await advisor_service.chat(
            advisor_id="ADV001",
            message="What can you do?",
            session_id=session_id
        )

        assert second_result["session_id"] == session_id
        assert second_result["response"] == "Continuing our conversation..."

    @pytest.mark.asyncio
    @patch('src.services.advisor_service.AdvisorAgent')
    async def test_chat_creates_new_session_for_invalid_session_id(self, mock_agent_class, advisor_service, mock_openai_key):
        """Should create new session if provided session_id doesn't exist."""
        # Mock agent instance
        mock_agent = AsyncMock()
        mock_agent.process_message.return_value = "New session started."
        mock_agent_class.return_value = mock_agent

        result = await advisor_service.chat(
            advisor_id="ADV001",
            message="Hello",
            session_id="INVALID_SESSION_123"
        )

        # Should get a new session_id, not the invalid one
        assert result["session_id"] != "INVALID_SESSION_123"
        assert result["response"] == "New session started."

    @pytest.mark.asyncio
    @patch('src.services.advisor_service.AdvisorAgent')
    async def test_chat_passes_transcript_context_to_agent(self, mock_agent_class, advisor_service, mock_openai_key):
        """Should pass transcript_id context to agent."""
        # Mock agent instance
        mock_agent = AsyncMock()
        mock_agent.process_message.return_value = "Context loaded successfully."
        mock_agent_class.return_value = mock_agent

        result = await advisor_service.chat(
            advisor_id="ADV001",
            message="Show me workflows",
            transcript_id="CALL_123"
        )

        # Agent should be initialized with correct context
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        assert call_args[1]["advisor_id"] == "ADV001"

        # Agent should receive message and session with context
        mock_agent.process_message.assert_called_once()
        process_args = mock_agent.process_message.call_args
        session_context = process_args[0][1]  # Second argument is session context
        assert session_context.get("transcript_id") == "CALL_123"

    @pytest.mark.asyncio
    @patch('src.services.advisor_service.AdvisorAgent')
    async def test_chat_passes_plan_context_to_agent(self, mock_agent_class, advisor_service, mock_openai_key):
        """Should pass plan_id context to agent."""
        # Mock agent instance
        mock_agent = AsyncMock()
        mock_agent.process_message.return_value = "Context loaded successfully."
        mock_agent_class.return_value = mock_agent

        result = await advisor_service.chat(
            advisor_id="ADV001",
            message="Show me workflows",
            plan_id="PLAN_456"
        )

        # Agent should be initialized with correct context
        mock_agent_class.assert_called_once()
        call_args = mock_agent_class.call_args
        assert call_args[1]["advisor_id"] == "ADV001"

        # Agent should receive message and session with context
        mock_agent.process_message.assert_called_once()
        process_args = mock_agent.process_message.call_args
        session_context = process_args[0][1]  # Second argument is session context
        assert session_context.get("plan_id") == "PLAN_456"

    @pytest.mark.asyncio
    async def test_chat_rejects_both_transcript_and_plan_context(self, advisor_service):
        """Should fail when both transcript_id and plan_id are provided."""
        with pytest.raises(Exception, match="Provide either transcript_id or plan_id, not both"):
            await advisor_service.chat(
                advisor_id="ADV001",
                message="Show me workflows",
                transcript_id="CALL_123",
                plan_id="PLAN_456"
            )


class TestAdvisorServiceErrorHandling:
    """Test error handling and fail-fast behavior."""

    @pytest.mark.asyncio
    @patch('src.services.advisor_service.AdvisorAgent')
    async def test_chat_fails_fast_on_agent_error(self, mock_agent_class, advisor_service, mock_openai_key):
        """Should fail fast when agent encounters error."""
        # Mock agent to raise an error
        mock_agent = AsyncMock()
        mock_agent.process_message.side_effect = Exception("LLM service unavailable")
        mock_agent_class.return_value = mock_agent

        with pytest.raises(Exception, match="Chat processing failed: LLM service unavailable"):
            await advisor_service.chat(
                advisor_id="ADV001",
                message="Hello"
            )

    @pytest.mark.asyncio
    @patch('src.services.advisor_service.AdvisorAgent')
    async def test_chat_provides_specific_error_guidance(self, mock_agent_class, advisor_service, mock_openai_key):
        """Should provide specific guidance based on error type."""
        # Mock agent to raise access denied error
        mock_agent = AsyncMock()
        mock_agent.process_message.side_effect = Exception("Access denied: borrower workflows only")
        mock_agent_class.return_value = mock_agent

        with pytest.raises(Exception) as exc_info:
            await advisor_service.chat(
                advisor_id="ADV001",
                message="Show supervisor workflows"
            )

        error_msg = str(exc_info.value)
        assert "Access restricted to borrower workflows only" in error_msg
        assert "Use available commands to see what you can access" in error_msg


class TestAdvisorServiceSessionManagement:
    """Test session management methods."""

    def test_get_recent_sessions_requires_advisor_id(self, advisor_service):
        """Should fail fast without advisor_id."""
        with pytest.raises(ValueError, match="advisor_id is required"):
            advisor_service.get_recent_sessions(advisor_id="")

    def test_get_session_summary_requires_session_id(self, advisor_service):
        """Should fail fast without session_id."""
        with pytest.raises(ValueError, match="session_id is required"):
            advisor_service.get_session_summary(session_id="")

    def test_delete_session_requires_session_id(self, advisor_service):
        """Should fail fast without session_id."""
        with pytest.raises(ValueError, match="session_id is required"):
            advisor_service.delete_session(session_id="")


# Integration test to verify the service works end-to-end
class TestAdvisorServiceIntegration:
    """Integration tests that verify service works with real components."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_chat_flow_without_mocks(self, temp_db):
        """Test complete chat flow with real database but mocked LLM."""
        # This test would require environment setup and real components
        # For now, skip it but keep the structure for future implementation
        pytest.skip("Integration test requires full environment setup")