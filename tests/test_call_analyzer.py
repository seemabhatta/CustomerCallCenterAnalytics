"""Tests for call analyzer - mortgage servicing intelligence."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.analyzers.call_analyzer import CallAnalyzer
from src.models.transcript import Transcript, Message


class TestCallAnalyzer:
    """Test the CallAnalyzer for mortgage servicing insights."""
    
    @pytest.fixture
    def sample_transcript(self):
        """Create a sample mortgage servicing transcript."""
        messages = [
            Message(
                "Advisor", 
                "Thank you for calling. I'm Sarah, how can I help you today?",
                timestamp="2024-01-01T10:00:00Z"
            ),
            Message(
                "Customer", 
                "Hi, I'm really confused about this PMI removal notice I received. I thought I could remove it already.",
                timestamp="2024-01-01T10:00:15Z"
            ),
            Message(
                "Advisor",
                "I understand your confusion. Let me pull up your account and explain the PMI removal process. Can you provide your loan number?",
                timestamp="2024-01-01T10:00:30Z"
            ),
            Message(
                "Customer",
                "It's 123456789. I've been paying on time for 3 years and I think my home value went up.",
                timestamp="2024-01-01T10:00:45Z"
            ),
            Message(
                "Advisor",
                "Perfect, I have your account here. You're correct that you've been making timely payments. For PMI removal, we need your loan-to-value ratio to be 80% or less. Would you like me to order an appraisal to determine current value?",
                timestamp="2024-01-01T10:01:00Z"
            )
        ]
        
        return Transcript(
            id="CALL_PMI_001",
            messages=messages,
            customer_id="CUST_456",
            advisor_id="ADV_SARAH_001",
            timestamp="2024-01-01T10:00:00Z",
            topic="PMI Removal",
            duration=300
        )
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI Responses API response for analysis."""
        return {
            "call_summary": "Customer inquired about PMI removal process, advisor explained requirements and offered appraisal option",
            "primary_intent": "PMI removal",
            "urgency_level": "medium",
            "borrower_sentiment": {
                "overall": "neutral",
                "start": "confused",
                "end": "hopeful",
                "trend": "improving"
            },
            "borrower_risks": {
                "delinquency_risk": 0.1,
                "churn_risk": 0.3,
                "complaint_risk": 0.2,
                "refinance_likelihood": 0.6
            },
            "advisor_metrics": {
                "empathy_score": 8.5,
                "compliance_adherence": 9.0,
                "solution_effectiveness": 8.0,
                "coaching_opportunities": ["Could offer more proactive next steps"]
            },
            "compliance_flags": [],
            "required_disclosures": ["PMI removal process disclosure"],
            "issue_resolved": False,
            "first_call_resolution": False,
            "escalation_needed": False,
            "topics_discussed": ["PMI removal", "appraisal process", "loan-to-value ratio"],
            "confidence_score": 0.95,
            "product_opportunities": ["appraisal services"],
            "payment_concerns": [],
            "property_related_issues": ["property valuation needed"]
        }
    
    def test_analyzer_initialization(self):
        """Test CallAnalyzer initialization."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            analyzer = CallAnalyzer()
            assert analyzer.api_key == 'test_key'
            assert analyzer.client is not None
    
    def test_analyzer_initialization_no_key(self):
        """Test CallAnalyzer fails without API key."""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key must be provided"):
                CallAnalyzer()
    
    def test_analyzer_initialization_with_key_param(self):
        """Test CallAnalyzer with API key parameter."""
        analyzer = CallAnalyzer(api_key="param_key")
        assert analyzer.api_key == "param_key"
    
    @patch('openai.OpenAI')
    def test_analyze_transcript_success(self, mock_openai, sample_transcript, mock_openai_response):
        """Test successful transcript analysis."""
        # Setup mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock successful responses API call
        mock_response = MagicMock()
        mock_response.output_parsed = mock_openai_response
        mock_client.responses.create.return_value = mock_response
        
        analyzer = CallAnalyzer(api_key="test_key")
        
        # Analyze transcript
        result = analyzer.analyze(sample_transcript)
        
        # Verify OpenAI was called correctly
        mock_client.responses.create.assert_called_once()
        call_args = mock_client.responses.create.call_args
        
        # Check that it used the Responses API correctly
        assert call_args.kwargs['model'] == "gpt-4.1"
        assert 'response_format' in call_args.kwargs
        assert call_args.kwargs['response_format']['type'] == "json_schema"
        assert 'MortgageCallAnalysis' in call_args.kwargs['response_format']['json_schema']['name']
        assert call_args.kwargs['temperature'] == 0.3
        
        # Check prompt contains transcript data
        prompt = call_args.kwargs['input']
        assert "PMI removal" in prompt
        assert "CUST_456" in prompt  # Customer ID should be in metadata
        assert "Sarah" in prompt  # Advisor name
        assert "Customer" in prompt
        
        # Verify analysis results
        assert result['transcript_id'] == sample_transcript.id
        assert result['primary_intent'] == "PMI removal"
        assert result['borrower_risks']['delinquency_risk'] == 0.1
        assert result['advisor_metrics']['empathy_score'] == 8.5
        assert result['confidence_score'] == 0.95
        assert 'analysis_id' in result
        assert result['analyzer_version'] == "1.0"
    
    @patch('openai.OpenAI')
    def test_analyze_transcript_openai_error(self, mock_openai, sample_transcript):
        """Test handling of OpenAI API errors."""
        # Setup mock OpenAI client to raise exception
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses.create.side_effect = Exception("OpenAI API Error")
        
        analyzer = CallAnalyzer(api_key="test_key")
        
        # Analyze should raise exception with context
        with pytest.raises(Exception, match="Analysis failed: OpenAI API Error"):
            analyzer.analyze(sample_transcript)
    
    def test_build_transcript_text(self, sample_transcript):
        """Test transcript text building for analysis."""
        analyzer = CallAnalyzer(api_key="test_key")
        
        transcript_text = analyzer._build_transcript_text(sample_transcript)
        
        # Check metadata is included
        assert "Call Date: 2024-01-01T10:00:00Z" in transcript_text
        assert "Topic: PMI Removal" in transcript_text
        
        # Check all messages are included
        assert "Advisor (2024-01-01T10:00:00Z): Thank you for calling" in transcript_text
        assert "Customer (2024-01-01T10:00:15Z): Hi, I'm really confused" in transcript_text
        assert "PMI removal notice" in transcript_text
        assert "123456789" in transcript_text  # Loan number
        
        # Check timestamps are preserved in the format
        assert "(2024-01-01T10:00:00Z):" in transcript_text
    
    def test_build_transcript_text_minimal(self):
        """Test transcript text building with minimal data."""
        minimal_transcript = Transcript(
            id="CALL_MIN",
            messages=[
                Message("Agent", "Hello"),
                Message("Caller", "Hi there")
            ]
        )
        
        analyzer = CallAnalyzer(api_key="test_key")
        transcript_text = analyzer._build_transcript_text(minimal_transcript)
        
        # Should work without metadata
        assert "Agent: Hello" in transcript_text
        assert "Caller: Hi there" in transcript_text
        
        # No metadata should not break
        assert "Call Date:" not in transcript_text
        assert "Topic:" not in transcript_text
    
    @patch('openai.OpenAI')
    def test_response_format_schema_validation(self, mock_openai, sample_transcript):
        """Test that the response format schema is properly structured."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock response to avoid actual API call
        mock_response = MagicMock()
        mock_response.output_parsed = {
            "call_summary": "test",
            "primary_intent": "test",
            "urgency_level": "low",
            "borrower_sentiment": {"overall": "neutral", "start": "neutral", "end": "neutral", "trend": "stable"},
            "borrower_risks": {"delinquency_risk": 0.1, "churn_risk": 0.1, "complaint_risk": 0.1, "refinance_likelihood": 0.1},
            "advisor_metrics": {"empathy_score": 5, "compliance_adherence": 5, "solution_effectiveness": 5, "coaching_opportunities": []},
            "compliance_flags": [],
            "required_disclosures": [],
            "issue_resolved": False,
            "first_call_resolution": False,
            "escalation_needed": False,
            "topics_discussed": [],
            "confidence_score": 0.8,
            "product_opportunities": [],
            "payment_concerns": [],
            "property_related_issues": []
        }
        mock_client.responses.create.return_value = mock_response
        
        analyzer = CallAnalyzer(api_key="test_key")
        analyzer.analyze(sample_transcript)
        
        # Get the schema that was sent to OpenAI
        call_args = mock_client.responses.create.call_args
        schema = call_args.kwargs['response_format']['json_schema']['schema']
        
        # Verify required schema structure
        assert 'properties' in schema
        properties = schema['properties']
        
        # Check mortgage-specific fields
        assert 'primary_intent' in properties
        assert 'borrower_risks' in properties
        assert 'advisor_metrics' in properties
        assert 'product_opportunities' in properties
        assert 'payment_concerns' in properties
        assert 'property_related_issues' in properties
        
        # Check nested object structures
        borrower_risks = properties['borrower_risks']['properties']
        assert 'delinquency_risk' in borrower_risks
        assert 'churn_risk' in borrower_risks
        assert 'refinance_likelihood' in borrower_risks
        
        advisor_metrics = properties['advisor_metrics']['properties']
        assert 'empathy_score' in advisor_metrics
        assert 'compliance_adherence' in advisor_metrics
        assert 'coaching_opportunities' in advisor_metrics
        
        # Check that strict mode is enabled
        assert schema.get('additionalProperties') == False
        assert call_args.kwargs['response_format']['json_schema']['strict'] == True