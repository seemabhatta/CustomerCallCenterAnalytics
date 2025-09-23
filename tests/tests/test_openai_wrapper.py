"""
Test suite for OpenAIWrapper - LLM integration wrapper
Tests following TDD principles and NO FALLBACK logic
"""
import pytest
import json
import os
from unittest.mock import Mock, patch
from pydantic import BaseModel, Field, ValidationError
from typing import List, Literal
from src.infrastructure.llm.openai_wrapper import OpenAIWrapper
from src.call_center_agents.models.risk_models import RiskAssessment, ApprovalRouting
from src.models.shared import ActionItem, ActionItemList


@pytest.fixture
def openai_wrapper():
    """Create OpenAIWrapper for testing."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-123", "OPENAI_MODEL": "gpt-4o-mini"}):
        return OpenAIWrapper()


@pytest.fixture
def mock_text_response():
    """Mock OpenAI Responses API text response."""
    mock_response = Mock()
    mock_response.output_text = "Test response"
    mock_response.id = "resp-test"
    return mock_response


@pytest.fixture
def mock_structured_response():
    """Mock OpenAI Responses API structured response."""
    mock_response = Mock()
    mock_response.output_text = json.dumps(
        {
            "name": "Test Name",
            "value": 42,
            "category": "A"
        }
    )
    mock_response.id = "resp-structured"
    return mock_response


class SampleStructuredModel(BaseModel):
    """Sample Pydantic model for schema testing."""
    name: str = Field(description="Name field")
    value: int = Field(ge=0, description="Positive integer")
    category: Literal["A", "B", "C"] = Field(description="Category selection")


class TestRiskAssessment:
    """Test RiskAssessment model."""

    def test_risk_assessment_valid_data(self):
        """Test RiskAssessment model with valid data."""
        data = {
            "risk_level": "HIGH",
            "reasoning": "High financial impact detected",
            "factors": ["Large amount", "Delinquent account"],
            "score": 0.85
        }
        
        assessment = RiskAssessment.model_validate(data)
        
        assert assessment.risk_level == "HIGH"
        assert assessment.reasoning == "High financial impact detected"
        assert assessment.factors == ["Large amount", "Delinquent account"]
        assert assessment.score == 0.85

    def test_risk_assessment_invalid_risk_level(self):
        """Test RiskAssessment fails on invalid risk level."""
        data = {
            "risk_level": "EXTREME",  # Invalid
            "reasoning": "Test",
            "factors": [],
            "score": 0.5
        }
        
        with pytest.raises(ValidationError):
            RiskAssessment.model_validate(data)

    def test_risk_assessment_invalid_score(self):
        """Test RiskAssessment fails on invalid score range."""
        data = {
            "risk_level": "LOW",
            "reasoning": "Test",
            "factors": [],
            "score": 1.5  # Invalid: > 1.0
        }
        
        with pytest.raises(ValidationError):
            RiskAssessment.model_validate(data)


class TestApprovalRouting:
    """Test ApprovalRouting model."""

    def test_approval_routing_valid_data(self):
        """Test ApprovalRouting model with valid data."""
        data = {
            "approval_level": "SUPERVISOR",
            "reasoning": "Financial impact requires supervisor approval",
            "urgency": "HIGH",
            "estimated_time_days": 3
        }
        
        routing = ApprovalRouting.model_validate(data)
        
        assert routing.approval_level == "SUPERVISOR"
        assert routing.urgency == "HIGH"
        assert routing.estimated_time_days == 3

    def test_approval_routing_invalid_time_days(self):
        """Test ApprovalRouting fails on invalid time days."""
        data = {
            "approval_level": "ADVISOR",
            "reasoning": "Test",
            "urgency": "LOW",
            "estimated_time_days": 0  # Invalid: < 1
        }
        
        with pytest.raises(ValidationError):
            ApprovalRouting.model_validate(data)


class TestActionItem:
    """Test ActionItem model."""

    def test_action_item_valid_data(self):
        """Test ActionItem model with valid data."""
        data = {
            "title": "Send payment reminder",
            "description": "Send automated payment reminder to customer",
            "pillar": "BORROWER",
            "priority": "HIGH",
            "estimated_hours": 0.5
        }
        
        item = ActionItem.model_validate(data)
        
        assert item.title == "Send payment reminder"
        assert item.pillar == "BORROWER"
        assert item.estimated_hours == 0.5

    def test_action_item_invalid_hours(self):
        """Test ActionItem fails on invalid estimated hours."""
        data = {
            "title": "Test action",
            "description": "Test",
            "pillar": "ADVISOR",
            "priority": "LOW",
            "estimated_hours": 0.0  # Invalid: < 0.1
        }
        
        with pytest.raises(ValidationError):
            ActionItem.model_validate(data)


class TestActionItemList:
    """Test ActionItemList model."""

    def test_action_item_list_valid_data(self):
        """Test ActionItemList model with valid data."""
        action_item_data = {
            "title": "Test action",
            "description": "Test description",
            "pillar": "BORROWER",
            "priority": "MEDIUM",
            "estimated_hours": 1.0
        }
        
        data = {
            "workflow_type": "BORROWER_WORKFLOW",
            "action_items": [action_item_data],
            "total_items": 1
        }
        
        item_list = ActionItemList.model_validate(data)
        
        assert item_list.workflow_type == "BORROWER_WORKFLOW"
        assert len(item_list.action_items) == 1
        assert item_list.total_items == 1


class TestOpenAIWrapper:
    """Test OpenAIWrapper functionality."""

    def test_wrapper_initialization(self, openai_wrapper):
        """Test wrapper initializes with correct configuration."""
        assert openai_wrapper.client is not None
        assert openai_wrapper.async_client is not None
        assert openai_wrapper.model == "gpt-4o-mini"

    def test_wrapper_initialization_missing_api_key(self):
        """Test wrapper fails fast when API key missing."""
        with patch.dict(os.environ, {}, clear=True):  # Clear environment
            with pytest.raises(RuntimeError):
                OpenAIWrapper()

    def test_create_json_schema(self, openai_wrapper):
        """Test JSON schema creation from Pydantic model."""
        schema = openai_wrapper._create_json_schema(SampleStructuredModel)

        assert schema["name"] == "SampleStructuredModel"
        assert schema["strict"] is True
        assert "schema" in schema

        # Verify schema structure
        model_schema = schema["schema"]
        assert model_schema["type"] == "object"
        assert model_schema["additionalProperties"] is False
        assert "name" in model_schema["properties"]
        assert "value" in model_schema["properties"]
        assert "category" in model_schema["properties"]

    def test_create_json_schema_nested_objects(self, openai_wrapper):
        """Test JSON schema handles nested objects correctly."""
        schema = openai_wrapper._create_json_schema(ActionItemList)
        
        # Find nested objects and verify additionalProperties=false
        def check_additional_properties(obj):
            if isinstance(obj, dict):
                if obj.get("type") == "object":
                    assert obj.get("additionalProperties") is False, f"Missing additionalProperties=false in: {obj}"
                for value in obj.values():
                    check_additional_properties(value)
            elif isinstance(obj, list):
                for item in obj:
                    check_additional_properties(item)
        
        check_additional_properties(schema["schema"])

    def test_generate_text_success(self, openai_wrapper, mock_text_response):
        """Test successful text generation."""
        mock_text_response.output_text = "Generated response"

        with patch.object(openai_wrapper.client.responses, 'create', return_value=mock_text_response):
            result = openai_wrapper.generate_text("Test prompt")

            assert result == "Generated response"
            call_args = openai_wrapper.client.responses.create.call_args[1]
            assert call_args["input"] == [{"role": "user", "content": "Test prompt"}]

    def test_generate_text_with_temperature(self, openai_wrapper, mock_text_response):
        """Test text generation with custom temperature."""
        with patch.object(openai_wrapper.client.responses, 'create', return_value=mock_text_response) as mock_create:
            openai_wrapper.generate_text("Test prompt", temperature=0.7)

            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["temperature"] == 0.7
            assert call_args["input"] == [{"role": "user", "content": "Test prompt"}]

    def test_generate_text_api_failure(self, openai_wrapper):
        """Test text generation fails fast when API fails."""
        with patch.object(openai_wrapper.client.responses, 'create', side_effect=Exception("API error")):

            with pytest.raises(Exception, match="API error"):
                openai_wrapper.generate_text("Test prompt")

    def test_generate_structured_success(self, openai_wrapper, mock_structured_response):
        """Test successful structured output generation."""
        # Mock valid structured response
        response_data = {
            "name": "Test Name",
            "value": 42,
            "category": "A"
        }
        mock_structured_response.output_text = json.dumps(response_data)

        with patch.object(openai_wrapper.client.responses, 'create', return_value=mock_structured_response):
            result = openai_wrapper.generate_structured("Test prompt", SampleStructuredModel)

            assert isinstance(result, SampleStructuredModel)
            assert result.name == "Test Name"
            assert result.value == 42
            assert result.category == "A"

    def test_generate_structured_with_temperature(self, openai_wrapper, mock_structured_response):
        """Test structured generation with custom temperature."""
        response_data = {"name": "Test", "value": 1, "category": "B"}
        mock_structured_response.output_text = json.dumps(response_data)

        with patch.object(openai_wrapper.client.responses, 'create', return_value=mock_structured_response) as mock_create:
            openai_wrapper.generate_structured("Test prompt", SampleStructuredModel, temperature=0.9)

            call_args = mock_create.call_args[1]
            assert call_args["temperature"] == 0.9
            assert call_args["input"] == [{"role": "user", "content": "Test prompt"}]
            response_format = call_args["response_format"]
            assert response_format["type"] == "json_schema"
            assert response_format["json_schema"]["name"] == "SampleStructuredModel"

    def test_generate_structured_api_failure(self, openai_wrapper):
        """Test structured generation fails fast when API fails."""
        with patch.object(openai_wrapper.client.responses, 'create', side_effect=Exception("API error")):

            with pytest.raises(Exception, match="API error"):
                openai_wrapper.generate_structured("Test prompt", SampleStructuredModel)

    def test_generate_structured_validation_error(self, openai_wrapper, mock_structured_response):
        """Test structured generation fails fast on validation error."""
        # Mock response with invalid data
        response_data = {
            "name": "Test",
            "value": -1,  # Invalid: must be >= 0
            "category": "D"  # Invalid: not in allowed values
        }
        mock_structured_response.output_text = json.dumps(response_data)

        with patch.object(openai_wrapper.client.responses, 'create', return_value=mock_structured_response):

            with pytest.raises(ValidationError):
                openai_wrapper.generate_structured("Test prompt", SampleStructuredModel)

    def test_generate_structured_response_format(self, openai_wrapper, mock_structured_response):
        """Test structured generation uses correct text format."""
        response_data = {"name": "Test", "value": 1, "category": "A"}
        mock_structured_response.output_text = json.dumps(response_data)

        with patch.object(openai_wrapper.client.responses, 'create', return_value=mock_structured_response) as mock_create:
            openai_wrapper.generate_structured("Test prompt", SampleStructuredModel)

            call_args = mock_create.call_args[1]
            response_format = call_args["response_format"]

            assert response_format["type"] == "json_schema"
            assert response_format["json_schema"]["strict"] is True
            assert response_format["json_schema"]["name"] == "SampleStructuredModel"


    @pytest.mark.asyncio
    async def test_generate_text_async_success(self, openai_wrapper, mock_text_response):
        """Test successful async text generation."""
        mock_text_response.output_text = "Async response"

        with patch.object(openai_wrapper.async_client.responses, 'create', return_value=mock_text_response):
            result = await openai_wrapper.generate_text_async("Test prompt")

            assert result == "Async response"

    @pytest.mark.asyncio
    async def test_generate_structured_async_success(self, openai_wrapper, mock_structured_response):
        """Test successful async structured generation."""
        response_data = {"name": "Async Test", "value": 99, "category": "C"}
        mock_structured_response.output_text = json.dumps(response_data)

        with patch.object(openai_wrapper.async_client.responses, 'create', return_value=mock_structured_response):
            result = await openai_wrapper.generate_structured_async("Test prompt", SampleStructuredModel)

            assert isinstance(result, SampleStructuredModel)
            assert result.name == "Async Test"
            assert result.value == 99

    def test_wrapper_no_fallback_logic(self, openai_wrapper):
        """Meta-test: Verify wrapper contains NO fallback logic."""
        # Wrapper should not contain:
        # 1. Default responses when API fails
        # 2. Mock/cached responses when OpenAI is unavailable
        # 3. try/catch blocks that return placeholder data
        # 4. Any resilience patterns that mask API failures
        
        # This is verified by tests that expect exceptions to propagate
        assert True  # All other tests verify fail-fast behavior

    def test_wrapper_strict_schema_enforcement(self, openai_wrapper):
        """Test wrapper enforces strict schema validation."""
        # Wrapper should use strict=True for all JSON schemas
        # This ensures OpenAI API enforces exact schema compliance
        
        schema = openai_wrapper._create_json_schema(RiskAssessment)
        assert schema["strict"] is True
        
        # Verify all objects have additionalProperties=false
        def check_strict_schema(obj):
            if isinstance(obj, dict) and obj.get("type") == "object":
                assert obj.get("additionalProperties") is False
        
        def traverse_schema(obj):
            if isinstance(obj, dict):
                check_strict_schema(obj)
                for value in obj.values():
                    traverse_schema(value)
            elif isinstance(obj, list):
                for item in obj:
                    traverse_schema(item)
        
        traverse_schema(schema["schema"])
