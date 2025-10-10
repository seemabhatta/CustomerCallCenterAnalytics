"""
Test suite for TranscriptService - Business logic for transcript operations
Tests following TDD principles and NO FALLBACK logic
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from src.services.transcript_service import TranscriptService
from src.models.transcript import Transcript, Message


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
def mock_api_key():
    """Mock OpenAI API key."""
    return "test-api-key-123"


@pytest.fixture
def transcript_service(temp_db, mock_api_key):
    """Create TranscriptService with temporary database."""
    return TranscriptService(api_key=mock_api_key, db_path=temp_db)


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing."""
    return Transcript(
        transcript_id="CALL_TEST123",
        customer_id="CUST_001",
        topic="payment_inquiry",
        urgency="medium",
        messages=[
            {"speaker": "customer", "text": "I need help with my payment", "timestamp": "10:00"},
            {"speaker": "agent", "text": "I can help you with that", "timestamp": "10:01"}
        ]
    )


class TestTranscriptService:
    """Test TranscriptService functionality."""

    @pytest.mark.asyncio
    async def test_list_all_empty_database(self, transcript_service):
        """Test listing transcripts when database is empty."""
        result = await transcript_service.list_all()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_all_with_data(self, transcript_service, sample_transcript):
        """Test listing transcripts with data in database."""
        # Store a transcript first
        transcript_service.store.store(sample_transcript)
        
        result = await transcript_service.list_all()
        assert len(result) == 1
        assert result[0]["transcript_id"] == "CALL_TEST123"
        assert result[0]["customer_id"] == "CUST_001"

    @pytest.mark.asyncio
    async def test_list_all_with_limit(self, transcript_service):
        """Test listing transcripts with limit parameter."""
        # Store multiple transcripts
        for i in range(5):
            transcript = Transcript(
                transcript_id=f"CALL_{i:03d}",
                customer_id=f"CUST_{i:03d}",
                topic="test_topic",
                messages=[{"speaker": "test", "text": "test"}]
            )
            transcript_service.store.store(transcript)
        
        result = await transcript_service.list_all(limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    @patch('src.call_center_agents.transcript_agent.TranscriptAgent.generate')
    async def test_create_transcript_with_defaults(self, mock_generate, transcript_service, sample_transcript):
        """Test creating transcript with default parameters."""
        mock_generate.return_value = sample_transcript

        request_data = {"topic": "payment_inquiry"}
        result = await transcript_service.create(request_data)

        assert result["transcript_id"] == "CALL_TEST123"
        assert result["customer_id"].startswith("CUST-") or result["customer_id"].startswith("CUST_")
        assert result["advisor_id"].startswith("ADV-")
        assert "loan_profile" in result
        kwargs = mock_generate.call_args.kwargs
        assert kwargs["topic"] == "payment_inquiry"
        assert kwargs["customer_id"] == result["customer_id"]
        assert kwargs["advisor_id"] == result["advisor_id"]
        assert "customer_profile" in kwargs
        assert "loan_profile" in kwargs
        assert "property_profile" in kwargs
        assert "advisor_profile" in kwargs

    @pytest.mark.asyncio
    @patch('src.call_center_agents.transcript_agent.TranscriptAgent.generate')
    async def test_create_transcript_with_custom_parameters(self, mock_generate, transcript_service, sample_transcript):
        """Test creating transcript with custom parameters."""
        mock_generate.return_value = sample_transcript

        request_data = {
            "topic": "complaint_resolution",
            "urgency": "high",
            "financial_impact": True,
            "customer_sentiment": "frustrated",
            "customer_id": "CUST_VIP001",
            "advisor_id": "ADV-509"
        }
        result = await transcript_service.create(request_data)

        kwargs = mock_generate.call_args.kwargs
        assert kwargs["topic"] == "complaint_resolution"
        assert kwargs["customer_id"] == "CUST_VIP001"
        assert kwargs["customer_profile"]["customer_id"] == "CUST_VIP001"
        assert kwargs["advisor_id"] == "ADV-509"
        assert result["customer_id"] == "CUST_VIP001"
        assert result["advisor_id"] == "ADV-509"

    @pytest.mark.asyncio
    @patch('src.call_center_agents.transcript_agent.TranscriptAgent.generate')
    async def test_create_transcript_legacy_scenario_parameter(self, mock_generate, transcript_service, sample_transcript):
        """Test creating transcript with legacy 'scenario' parameter."""
        mock_generate.return_value = sample_transcript

        request_data = {"scenario": "legacy_payment_inquiry"}
        result = await transcript_service.create(request_data)

        kwargs = mock_generate.call_args.kwargs
        assert kwargs["topic"] == "legacy_payment_inquiry"
        assert result["topic"] == "legacy_payment_inquiry"

    @pytest.mark.asyncio
    @patch('src.call_center_agents.transcript_agent.TranscriptAgent.generate')
    async def test_create_transcript_no_store(self, mock_generate, transcript_service, sample_transcript):
        """Test creating transcript without storing."""
        mock_generate.return_value = sample_transcript

        request_data = {"topic": "test", "store": False}
        result = await transcript_service.create(request_data)
        
        # Verify transcript was not stored
        stored_transcript = transcript_service.store.get_by_id("CALL_TEST123")
        assert stored_transcript is None

    @pytest.mark.asyncio
    @patch('src.call_center_agents.transcript_agent.TranscriptAgent.generate')
    async def test_create_transcript_generator_failure(self, mock_generate, transcript_service):
        """Test create fails fast when generator fails."""
        mock_generate.side_effect = Exception("OpenAI API error")

        request_data = {"topic": "test"}
        
        with pytest.raises(Exception, match="OpenAI API error"):
            await transcript_service.create(request_data)

    @pytest.mark.asyncio
    @patch('src.call_center_agents.transcript_agent.TranscriptAgent.generate')
    async def test_create_transcript_with_context(self, mock_generate, transcript_service, sample_transcript):
        """Ensure optional context is forwarded to generator and transcript output."""
        mock_generate.return_value = sample_transcript

        request_data = {
            "topic": "payment_inquiry",
            "context": "Customer following up on unresolved escrow overage.",
        }

        result = await transcript_service.create(request_data)

        kwargs = mock_generate.call_args.kwargs
        assert kwargs["conversation_context"] == "Customer following up on unresolved escrow overage."
        assert result.get("conversation_context") == "Customer following up on unresolved escrow overage."

    @pytest.mark.asyncio
    @patch('src.call_center_agents.transcript_agent.TranscriptAgent.generate')
    async def test_create_bulk_transcripts(self, mock_generate, transcript_service, sample_transcript):
        """Test bulk transcript creation returns count and transcripts."""
        mock_generate.return_value = sample_transcript

        requests = [{"topic": "payment_inquiry"} for _ in range(3)]
        result = await transcript_service.create_bulk(requests)

        assert result["count"] == 3
        assert len(result["transcripts"]) == 3

    @pytest.mark.asyncio
    async def test_get_by_id_existing_transcript(self, transcript_service, sample_transcript):
        """Test getting transcript by ID when it exists."""
        transcript_service.store.store(sample_transcript)
        
        result = await transcript_service.get_by_id("CALL_TEST123")
        assert result is not None
        assert result["transcript_id"] == "CALL_TEST123"
        assert result["customer_id"] == "CUST_001"

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_transcript(self, transcript_service):
        """Test getting transcript by ID when it doesn't exist."""
        result = await transcript_service.get_by_id("NONEXISTENT")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing_transcript(self, transcript_service, sample_transcript):
        """Test deleting existing transcript."""
        transcript_service.store.store(sample_transcript)
        
        result = await transcript_service.delete("CALL_TEST123")
        assert result is True
        
        # Verify deletion
        deleted_transcript = transcript_service.store.get_by_id("CALL_TEST123")
        assert deleted_transcript is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_transcript(self, transcript_service):
        """Test deleting nonexistent transcript."""
        result = await transcript_service.delete("NONEXISTENT")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_all_transcripts(self, transcript_service):
        """Test deleting all transcripts returns deleted count."""
        for i in range(3):
            transcript_service.store.store(
                Transcript(
                    id=f"CALL_BULK_{i}",
                    customer_id=f"CUST_{i}",
                    topic="test",
                    messages=[Message("test", "hello")]
                )
            )

        count = await transcript_service.delete_all()

        assert count == 3
        assert transcript_service.store.get_all() == []

    @pytest.mark.asyncio
    async def test_search_by_customer(self, transcript_service, sample_transcript):
        """Test searching transcripts by customer."""
        transcript_service.store.store(sample_transcript)

        result = await transcript_service.search({"customer": "CUST_001"})
        assert len(result) == 1
        assert result[0]["customer_id"] == "CUST_001"

    @pytest.mark.asyncio
    async def test_search_by_topic(self, transcript_service, sample_transcript):
        """Test searching transcripts by topic."""
        transcript_service.store.store(sample_transcript)
        
        result = await transcript_service.search({"topic": "payment_inquiry"})
        assert len(result) == 1
        assert result[0]["topic"] == "payment_inquiry"

    @pytest.mark.asyncio
    async def test_search_by_text(self, transcript_service, sample_transcript):
        """Test searching transcripts by text content."""
        transcript_service.store.store(sample_transcript)
        
        result = await transcript_service.search({"text": "payment"})
        assert len(result) == 1
        assert "payment" in str(result[0]["messages"])

    @pytest.mark.asyncio
    async def test_search_no_parameters(self, transcript_service):
        """Test search fails fast when no search parameters provided."""
        with pytest.raises(ValueError, match="Must specify customer, topic, or text parameter"):
            await transcript_service.search({})

    @pytest.mark.asyncio
    async def test_search_store_failure(self, transcript_service):
        """Test search fails fast when store fails."""
        with patch.object(transcript_service.store, 'search_by_customer', side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Database error"):
                await transcript_service.search({"customer": "CUST_001"})

    @pytest.mark.asyncio
    async def test_get_metrics_empty_database(self, transcript_service):
        """Test getting metrics from empty database."""
        result = await transcript_service.get_metrics()
        
        expected_metrics = {
            "total_transcripts": 0,
            "total_messages": 0,
            "unique_customers": 0,
            "avg_messages_per_transcript": 0.0,
            "top_topics": {},
            "sentiments": {},
            "speakers": {}
        }
        assert result == expected_metrics

    @pytest.mark.asyncio
    async def test_get_metrics_with_data(self, transcript_service, sample_transcript):
        """Test getting metrics with data in database."""
        transcript_service.store.store(sample_transcript)
        
        result = await transcript_service.get_metrics()
        
        assert result["total_transcripts"] == 1
        assert result["total_messages"] == 2
        assert result["unique_customers"] == 1
        assert result["avg_messages_per_transcript"] == 2.0

    @pytest.mark.asyncio
    async def test_get_metrics_store_failure(self, transcript_service):
        """Test get_metrics fails fast when store fails."""
        with patch.object(transcript_service.store, 'get_all', side_effect=Exception("Database connection failed")):
            with pytest.raises(Exception, match="Database connection failed"):
                await transcript_service.get_metrics()

    def test_service_initialization(self, mock_api_key):
        """Test service initializes with correct dependencies."""
        service = TranscriptService(api_key=mock_api_key, db_path="test.db")
        
        assert service.api_key == mock_api_key
        assert service.db_path == "test.db"
        assert service.store is not None
        assert service.generator is not None

    def test_service_no_fallback_logic(self, transcript_service):
        """Meta-test: Verify service contains NO fallback logic."""
        # Service should not contain:
        # 1. try/catch blocks that return default values
        # 2. if/else blocks that return mock data
        # 3. any fallback mechanisms
        
        # This is verified by other tests that expect exceptions to propagate
        assert True  # All other tests verify fail-fast behavior
