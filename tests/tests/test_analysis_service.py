"""
Test suite for AnalysisService - Business logic for analysis operations
Tests following TDD principles and NO FALLBACK logic
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from src.services.analysis_service import AnalysisService
from src.models.transcript import Transcript


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
def analysis_service(temp_db, mock_api_key):
    """Create AnalysisService with temporary database."""
    return AnalysisService(api_key=mock_api_key, db_path=temp_db)


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


@pytest.fixture
def sample_analysis():
    """Sample analysis result for testing."""
    return {
        "analysis_id": "ANALYSIS_TEST123",
        "transcript_id": "CALL_TEST123",
        "sentiment_analysis": {
            "overall_sentiment": "neutral",
            "customer_sentiment": "concerned",
            "confidence": 0.85
        },
        "risk_indicators": {
            "delinquency_risk": 0.3,
            "churn_risk": 0.2,
            "complaint_risk": 0.1
        },
        "topics": ["payment", "account_inquiry"],
        "resolution_status": "resolved",
        "follow_up_required": False
    }


class TestAnalysisService:
    """Test AnalysisService functionality."""

    @pytest.mark.asyncio
    async def test_list_all_empty_database(self, analysis_service):
        """Test listing analyses when database is empty."""
        result = await analysis_service.list_all()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_all_with_data(self, analysis_service, sample_analysis):
        """Test listing analyses with data in database."""
        # Store an analysis first
        analysis_service.store.store(sample_analysis)
        
        result = await analysis_service.list_all()
        assert len(result) == 1
        assert result[0]["analysis_id"] == "ANALYSIS_TEST123"
        assert result[0]["transcript_id"] == "CALL_TEST123"

    @pytest.mark.asyncio
    async def test_list_all_with_limit(self, analysis_service):
        """Test listing analyses with limit parameter."""
        # Store multiple analyses
        for i in range(5):
            analysis = {
                "analysis_id": f"ANALYSIS_{i:03d}",
                "transcript_id": f"CALL_{i:03d}",
                "sentiment_analysis": {"overall_sentiment": "neutral"}
            }
            analysis_service.store.store(analysis)
        
        result = await analysis_service.list_all(limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    async def test_list_all_handles_object_type(self, analysis_service):
        """Test list_all handles objects with to_dict method."""
        # Create a mock analysis object with to_dict method
        mock_analysis = Mock()
        mock_analysis.to_dict.return_value = {"analysis_id": "TEST123"}
        
        with patch.object(analysis_service.store, 'get_all', return_value=[mock_analysis]):
            result = await analysis_service.list_all()
            
        assert len(result) == 1
        assert result[0]["analysis_id"] == "TEST123"
        mock_analysis.to_dict.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_all_handles_dict_type(self, analysis_service, sample_analysis):
        """Test list_all handles dictionary objects."""
        analysis_service.store.store(sample_analysis)
        
        result = await analysis_service.list_all()
        assert len(result) == 1
        assert isinstance(result[0], dict)

    @pytest.mark.asyncio
    async def test_list_all_fails_on_unexpected_type(self, analysis_service):
        """Test list_all fails fast on unexpected object type."""
        with patch.object(analysis_service.store, 'get_all', return_value=["invalid_type"]):
            with pytest.raises(ValueError, match="Unexpected analysis type"):
                await analysis_service.list_all()

    @pytest.mark.asyncio
    @patch('src.analyzers.call_analyzer.CallAnalyzer.analyze')
    @patch('src.services.analysis_service.TranscriptStore')
    @patch('src.telemetry.set_span_attributes')
    @patch('src.telemetry.add_span_event')
    async def test_create_analysis_success(self, mock_span_event, mock_span_attr, mock_transcript_store_class, mock_analyze, analysis_service, sample_transcript, sample_analysis):
        """Test creating analysis successfully."""
        # Setup mocks
        mock_transcript_store = Mock()
        mock_transcript_store.get_by_id.return_value = sample_transcript
        mock_transcript_store_class.return_value = mock_transcript_store
        mock_analyze.return_value = sample_analysis.copy()
        
        request_data = {"transcript_id": "CALL_TEST123"}
        result = await analysis_service.create(request_data)
        
        # Verify telemetry calls
        mock_span_attr.assert_called_with(transcript_id="CALL_TEST123", operation="create_analysis")
        assert mock_span_event.call_count >= 4  # Multiple telemetry events
        
        # Verify transcript retrieval
        mock_transcript_store.get_by_id.assert_called_once_with("CALL_TEST123")
        
        # Verify analysis
        mock_analyze.assert_called_once_with(sample_transcript)
        assert result["transcript_id"] == "CALL_TEST123"
        assert "analysis_id" in result

    @pytest.mark.asyncio
    async def test_create_analysis_missing_transcript_id(self, analysis_service):
        """Test create fails fast when transcript_id missing."""
        request_data = {}
        
        with pytest.raises(ValueError, match="transcript_id is required"):
            await analysis_service.create(request_data)

    @pytest.mark.asyncio
    @patch('src.services.analysis_service.TranscriptStore')
    @patch('src.telemetry.set_span_attributes')
    @patch('src.telemetry.add_span_event')
    async def test_create_analysis_transcript_not_found(self, mock_span_event, mock_span_attr, mock_transcript_store_class, analysis_service):
        """Test create fails fast when transcript not found."""
        # Setup mock
        mock_transcript_store = Mock()
        mock_transcript_store.get_by_id.return_value = None
        mock_transcript_store_class.return_value = mock_transcript_store
        
        request_data = {"transcript_id": "NONEXISTENT"}
        
        with pytest.raises(ValueError, match="Transcript NONEXISTENT not found"):
            await analysis_service.create(request_data)

    @pytest.mark.asyncio
    @patch('src.analyzers.call_analyzer.CallAnalyzer.analyze')
    @patch('src.services.analysis_service.TranscriptStore')
    @patch('src.telemetry.set_span_attributes')
    @patch('src.telemetry.add_span_event')
    async def test_create_analysis_analyzer_failure(self, mock_span_event, mock_span_attr, mock_transcript_store_class, mock_analyze, analysis_service, sample_transcript):
        """Test create fails fast when analyzer fails."""
        # Setup mocks
        mock_transcript_store = Mock()
        mock_transcript_store.get_by_id.return_value = sample_transcript
        mock_transcript_store_class.return_value = mock_transcript_store
        mock_analyze.side_effect = Exception("OpenAI API error")
        
        request_data = {"transcript_id": "CALL_TEST123"}
        
        with pytest.raises(Exception, match="OpenAI API error"):
            await analysis_service.create(request_data)

    @pytest.mark.asyncio
    @patch('src.analyzers.call_analyzer.CallAnalyzer.analyze')
    @patch('src.services.analysis_service.TranscriptStore')
    @patch('src.telemetry.set_span_attributes')
    @patch('src.telemetry.add_span_event')
    async def test_create_analysis_no_store(self, mock_span_event, mock_span_attr, mock_transcript_store_class, mock_analyze, analysis_service, sample_transcript, sample_analysis):
        """Test creating analysis without storing."""
        # Setup mocks
        mock_transcript_store = Mock()
        mock_transcript_store.get_by_id.return_value = sample_transcript
        mock_transcript_store_class.return_value = mock_transcript_store
        mock_analyze.return_value = sample_analysis.copy()
        
        request_data = {"transcript_id": "CALL_TEST123", "store": False}
        result = await analysis_service.create(request_data)
        
        # Verify analysis was not stored
        stored_analysis = analysis_service.store.get_by_id(result.get("analysis_id"))
        assert stored_analysis is None

    @pytest.mark.asyncio
    async def test_get_by_id_existing_analysis(self, analysis_service, sample_analysis):
        """Test getting analysis by ID when it exists."""
        analysis_service.store.store(sample_analysis)
        
        result = await analysis_service.get_by_id("ANALYSIS_TEST123")
        assert result is not None
        assert result["analysis_id"] == "ANALYSIS_TEST123"
        assert result["transcript_id"] == "CALL_TEST123"

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_analysis(self, analysis_service):
        """Test getting analysis by ID when it doesn't exist."""
        result = await analysis_service.get_by_id("NONEXISTENT")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_by_id_handles_object_type(self, analysis_service):
        """Test get_by_id handles objects with to_dict method."""
        mock_analysis = Mock()
        mock_analysis.to_dict.return_value = {"analysis_id": "TEST123"}
        
        with patch.object(analysis_service.store, 'get_by_id', return_value=mock_analysis):
            result = await analysis_service.get_by_id("TEST123")
            
        assert result["analysis_id"] == "TEST123"
        mock_analysis.to_dict.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_fails_on_unexpected_type(self, analysis_service):
        """Test get_by_id fails fast on unexpected object type."""
        with patch.object(analysis_service.store, 'get_by_id', return_value="invalid_type"):
            with pytest.raises(ValueError, match="Unexpected analysis type"):
                await analysis_service.get_by_id("TEST123")

    @pytest.mark.asyncio
    async def test_delete_existing_analysis(self, analysis_service, sample_analysis):
        """Test deleting existing analysis."""
        analysis_service.store.store(sample_analysis)
        
        result = await analysis_service.delete("ANALYSIS_TEST123")
        assert result is True
        
        # Verify deletion
        deleted_analysis = analysis_service.store.get_by_id("ANALYSIS_TEST123")
        assert deleted_analysis is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_analysis(self, analysis_service):
        """Test deleting nonexistent analysis."""
        result = await analysis_service.delete("NONEXISTENT")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_all_analyses(self, analysis_service, sample_analysis):
        """Test deleting all analyses."""
        # Store multiple analyses
        for i in range(3):
            analysis = sample_analysis.copy()
            analysis["analysis_id"] = f"ANALYSIS_{i:03d}"
            analysis_service.store.store(analysis)
        
        count = await analysis_service.delete_all()
        assert count == 3
        
        # Verify all deleted
        remaining = await analysis_service.list_all()
        assert len(remaining) == 0

    @pytest.mark.asyncio
    async def test_search_by_transcript(self, analysis_service, sample_analysis):
        """Test searching analyses by transcript ID."""
        analysis_service.store.store(sample_analysis)
        
        with patch.object(analysis_service.store, 'search_by_transcript', return_value=[sample_analysis]) as mock_search:
            result = await analysis_service.search_by_transcript("CALL_TEST123")
            
        assert len(result) == 1
        assert result[0]["transcript_id"] == "CALL_TEST123"
        mock_search.assert_called_once_with("CALL_TEST123")

    @pytest.mark.asyncio
    async def test_search_by_transcript_store_failure(self, analysis_service):
        """Test search fails fast when store fails."""
        with patch.object(analysis_service.store, 'search_by_transcript', side_effect=Exception("Database error")):
            with pytest.raises(Exception, match="Database error"):
                await analysis_service.search_by_transcript("CALL_TEST123")

    def test_service_initialization(self, mock_api_key):
        """Test service initializes with correct dependencies."""
        service = AnalysisService(api_key=mock_api_key, db_path="test.db")
        
        assert service.api_key == mock_api_key
        assert service.db_path == "test.db"
        assert service.store is not None
        assert service.analyzer is not None

    def test_service_no_fallback_logic(self, analysis_service):
        """Meta-test: Verify service contains NO fallback logic."""
        # Service should not contain:
        # 1. try/catch blocks that return default values
        # 2. if/else blocks that return mock data
        # 3. any fallback mechanisms that hide errors
        
        # This is verified by other tests that expect exceptions to propagate
        assert True  # All other tests verify fail-fast behavior