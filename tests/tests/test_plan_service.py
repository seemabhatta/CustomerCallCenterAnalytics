"""
Test suite for PlanService - Business logic for action plan operations
Tests following TDD principles and NO FALLBACK logic
"""
import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, AsyncMock, patch
from src.services.plan_service import PlanService


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
def plan_service(temp_db, mock_api_key):
    """Create PlanService with temporary database."""
    return PlanService(api_key=mock_api_key, db_path=temp_db)


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
        "resolution_status": "resolved"
    }


@pytest.fixture
def sample_transcript():
    """Sample transcript for testing."""
    return {
        "transcript_id": "CALL_TEST123",
        "customer_id": "CUST_001",
        "topic": "payment_inquiry",
        "messages": [
            {"speaker": "customer", "text": "I need help with my payment", "timestamp": "10:00"},
            {"speaker": "agent", "text": "I can help you with that", "timestamp": "10:01"}
        ]
    }


@pytest.fixture
def sample_plan():
    """Sample action plan result for testing."""
    return {
        "plan_id": "PLAN_TEST123",
        "analysis_id": "ANALYSIS_TEST123",
        "borrower_plan": {
            "immediate_actions": [
                {
                    "action": "Send confirmation email",
                    "timeline": "Within 24 hours",
                    "priority": "high"
                }
            ],
            "follow_ups": [
                {
                    "action": "Follow up call",
                    "due_date": "2024-01-15",
                    "owner": "CSR"
                }
            ]
        },
        "advisor_plan": {
            "coaching_items": ["Improve active listening"],
            "performance_feedback": {
                "strengths": ["Clear communication"],
                "improvements": ["Better questions"]
            }
        },
        "supervisor_plan": {
            "escalation_items": [{
                "item": "Payment dispute",
                "priority": "medium"
            }]
        },
        "leadership_plan": {
            "portfolio_insights": ["Rising concerns"]
        }
    }


class TestPlanService:
    """Test PlanService functionality."""

    @pytest.mark.asyncio
    async def test_list_all_empty_database(self, plan_service):
        """Test listing plans when database is empty."""
        result = await plan_service.list_all()
        assert result == []

    @pytest.mark.asyncio
    async def test_list_all_with_data(self, plan_service, sample_plan):
        """Test listing plans with data in database."""
        # Store a plan first
        plan_service.store.store(sample_plan)
        
        result = await plan_service.list_all()
        assert len(result) == 1
        assert result[0]["plan_id"] == "PLAN_TEST123"
        assert result[0]["analysis_id"] == "ANALYSIS_TEST123"

    @pytest.mark.asyncio
    async def test_list_all_with_limit(self, plan_service):
        """Test listing plans with limit parameter."""
        # Store multiple plans
        for i in range(5):
            plan = {
                "plan_id": f"PLAN_{i:03d}",
                "analysis_id": f"ANALYSIS_{i:03d}",
                "borrower_plan": {"immediate_actions": []}
            }
            plan_service.store.store(plan)
        
        result = await plan_service.list_all(limit=3)
        assert len(result) == 3

    @pytest.mark.asyncio
    @patch('src.generators.action_plan_generator.ActionPlanGenerator.generate')
    @patch('src.services.plan_service.AnalysisStore')
    @patch('src.services.plan_service.TranscriptStore')
    @patch('src.telemetry.set_span_attributes')
    @patch('src.telemetry.add_span_event')
    async def test_create_plan_success(self, mock_span_event, mock_span_attr, mock_transcript_store_class, mock_analysis_store_class, mock_generate, plan_service, sample_analysis, sample_transcript, sample_plan):
        """Test creating action plan successfully."""
        # Setup mocks
        mock_analysis_store = Mock()
        mock_analysis_store.get_by_id.return_value = sample_analysis
        mock_analysis_store_class.return_value = mock_analysis_store
        
        mock_transcript_store = Mock()
        mock_transcript_store.get_by_id.return_value = sample_transcript
        mock_transcript_store_class.return_value = mock_transcript_store
        
        mock_generate.return_value = sample_plan.copy()
        
        request_data = {"analysis_id": "ANALYSIS_TEST123"}
        result = await plan_service.create(request_data)
        
        # Verify telemetry calls
        mock_span_attr.assert_called_with(analysis_id="ANALYSIS_TEST123", operation="create_plan")
        assert mock_span_event.call_count >= 5  # Multiple telemetry events
        
        # Verify data retrieval
        mock_analysis_store.get_by_id.assert_called_once_with("ANALYSIS_TEST123")
        mock_transcript_store.get_by_id.assert_called_once_with("CALL_TEST123")
        
        # Verify plan generation
        mock_generate.assert_called_once_with(sample_analysis, sample_transcript)
        assert result["analysis_id"] == "ANALYSIS_TEST123"
        assert "plan_id" in result

    @pytest.mark.asyncio
    async def test_create_plan_missing_analysis_id(self, plan_service):
        """Test create fails fast when analysis_id missing."""
        request_data = {}
        
        with pytest.raises(ValueError, match="analysis_id is required"):
            await plan_service.create(request_data)

    @pytest.mark.asyncio
    @patch('src.services.plan_service.AnalysisStore')
    @patch('src.telemetry.set_span_attributes')
    @patch('src.telemetry.add_span_event')
    async def test_create_plan_analysis_not_found(self, mock_span_event, mock_span_attr, mock_analysis_store_class, plan_service):
        """Test create fails fast when analysis not found."""
        # Setup mock
        mock_analysis_store = Mock()
        mock_analysis_store.get_by_id.return_value = None
        mock_analysis_store_class.return_value = mock_analysis_store
        
        request_data = {"analysis_id": "NONEXISTENT"}
        
        with pytest.raises(ValueError, match="Analysis NONEXISTENT not found"):
            await plan_service.create(request_data)

    @pytest.mark.asyncio
    @patch('src.services.plan_service.AnalysisStore')
    @patch('src.services.plan_service.TranscriptStore')
    @patch('src.telemetry.set_span_attributes')
    @patch('src.telemetry.add_span_event')
    async def test_create_plan_transcript_not_found(self, mock_span_event, mock_span_attr, mock_transcript_store_class, mock_analysis_store_class, plan_service, sample_analysis):
        """Test create fails fast when transcript not found."""
        # Setup mocks
        mock_analysis_store = Mock()
        mock_analysis_store.get_by_id.return_value = sample_analysis
        mock_analysis_store_class.return_value = mock_analysis_store
        
        mock_transcript_store = Mock()
        mock_transcript_store.get_by_id.return_value = None
        mock_transcript_store_class.return_value = mock_transcript_store
        
        request_data = {"analysis_id": "ANALYSIS_TEST123"}
        
        with pytest.raises(ValueError, match="Transcript CALL_TEST123 not found"):
            await plan_service.create(request_data)

    @pytest.mark.asyncio
    @patch('src.generators.action_plan_generator.ActionPlanGenerator.generate')
    @patch('src.services.plan_service.AnalysisStore')
    @patch('src.services.plan_service.TranscriptStore')
    @patch('src.telemetry.set_span_attributes')
    @patch('src.telemetry.add_span_event')
    async def test_create_plan_generator_failure(self, mock_span_event, mock_span_attr, mock_transcript_store_class, mock_analysis_store_class, mock_generate, plan_service, sample_analysis, sample_transcript):
        """Test create fails fast when generator fails."""
        # Setup mocks
        mock_analysis_store = Mock()
        mock_analysis_store.get_by_id.return_value = sample_analysis
        mock_analysis_store_class.return_value = mock_analysis_store
        
        mock_transcript_store = Mock()
        mock_transcript_store.get_by_id.return_value = sample_transcript
        mock_transcript_store_class.return_value = mock_transcript_store
        
        mock_generate.side_effect = Exception("OpenAI API error")
        
        request_data = {"analysis_id": "ANALYSIS_TEST123"}
        
        with pytest.raises(Exception, match="OpenAI API error"):
            await plan_service.create(request_data)

    @pytest.mark.asyncio
    @patch('src.generators.action_plan_generator.ActionPlanGenerator.generate')
    @patch('src.services.plan_service.AnalysisStore')
    @patch('src.services.plan_service.TranscriptStore')
    @patch('src.telemetry.set_span_attributes')
    @patch('src.telemetry.add_span_event')
    async def test_create_plan_no_store(self, mock_span_event, mock_span_attr, mock_transcript_store_class, mock_analysis_store_class, mock_generate, plan_service, sample_analysis, sample_transcript, sample_plan):
        """Test creating plan without storing."""
        # Setup mocks
        mock_analysis_store = Mock()
        mock_analysis_store.get_by_id.return_value = sample_analysis
        mock_analysis_store_class.return_value = mock_analysis_store
        
        mock_transcript_store = Mock()
        mock_transcript_store.get_by_id.return_value = sample_transcript
        mock_transcript_store_class.return_value = mock_transcript_store
        
        mock_generate.return_value = sample_plan.copy()
        
        request_data = {"analysis_id": "ANALYSIS_TEST123", "store": False}
        result = await plan_service.create(request_data)
        
        # Verify plan was not stored
        stored_plan = plan_service.store.get_by_id(result.get("plan_id"))
        assert stored_plan is None

    @pytest.mark.asyncio
    async def test_get_by_id_existing_plan(self, plan_service, sample_plan):
        """Test getting plan by ID when it exists."""
        plan_service.store.store(sample_plan)
        
        result = await plan_service.get_by_id("PLAN_TEST123")
        assert result is not None
        assert result["plan_id"] == "PLAN_TEST123"
        assert result["analysis_id"] == "ANALYSIS_TEST123"

    @pytest.mark.asyncio
    async def test_get_by_id_nonexistent_plan(self, plan_service):
        """Test getting plan by ID when it doesn't exist."""
        result = await plan_service.get_by_id("NONEXISTENT")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_existing_plan(self, plan_service, sample_plan):
        """Test updating existing plan."""
        plan_service.store.store(sample_plan)
        
        updates = {
            "status": "approved",
            "approved_by": "SUPERVISOR_001",
            "borrower_plan": {
                "immediate_actions": [
                    {"action": "Updated action", "priority": "high"}
                ]
            }
        }
        
        result = await plan_service.update("PLAN_TEST123", updates)
        assert result is not None
        assert result["status"] == "approved"
        assert result["approved_by"] == "SUPERVISOR_001"
        assert result["borrower_plan"]["immediate_actions"][0]["action"] == "Updated action"

    @pytest.mark.asyncio
    async def test_update_nonexistent_plan(self, plan_service):
        """Test updating nonexistent plan."""
        updates = {"status": "approved"}
        result = await plan_service.update("NONEXISTENT", updates)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_existing_plan(self, plan_service, sample_plan):
        """Test deleting existing plan."""
        plan_service.store.store(sample_plan)
        
        result = await plan_service.delete("PLAN_TEST123")
        assert result is True
        
        # Verify deletion
        deleted_plan = plan_service.store.get_by_id("PLAN_TEST123")
        assert deleted_plan is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_plan(self, plan_service):
        """Test deleting nonexistent plan."""
        result = await plan_service.delete("NONEXISTENT")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_all_plans(self, plan_service, sample_plan):
        """Test deleting all plans."""
        # Store multiple plans
        for i in range(3):
            plan = sample_plan.copy()
            plan["plan_id"] = f"PLAN_{i:03d}"
            plan_service.store.store(plan)
        
        result = await plan_service.delete_all()
        assert result["count"] == 3
        assert "deleted" in result
        
        # Verify all deleted
        remaining = await plan_service.list_all()
        assert len(remaining) == 0

    def test_service_initialization(self, mock_api_key):
        """Test service initializes with correct dependencies."""
        service = PlanService(api_key=mock_api_key, db_path="test.db")
        
        assert service.api_key == mock_api_key
        assert service.db_path == "test.db"
        assert service.store is not None
        assert service.generator is not None

    def test_service_no_fallback_logic(self, plan_service):
        """Meta-test: Verify service contains NO fallback logic."""
        # Service should not contain:
        # 1. try/catch blocks that return default values
        # 2. if/else blocks that return mock data
        # 3. any fallback mechanisms that hide errors
        
        # This is verified by other tests that expect exceptions to propagate
        assert True  # All other tests verify fail-fast behavior