"""Integration tests for the complete Customer Call Center Analytics system."""
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.generators.transcript_generator import TranscriptGenerator
from src.storage.transcript_store import TranscriptStore
from src.analyzers.call_analyzer import CallAnalyzer
from src.storage.analysis_store import AnalysisStore
from src.generators.action_plan_generator import ActionPlanGenerator
from src.storage.action_plan_store import ActionPlanStore
from src.models.transcript import Transcript, Message


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def mock_analysis_response():
    """Mock response for OpenAI Responses API analysis."""
    return {
        'call_summary': 'Customer inquired about PMI removal process',
        'primary_intent': 'PMI removal request',
        'urgency_level': 'medium',
        'borrower_sentiment': {
            'overall': 'hopeful',
            'start': 'curious',
            'end': 'satisfied',
            'trend': 'improving'
        },
        'borrower_risks': {
            'delinquency_risk': 0.1,
            'churn_risk': 0.2,
            'complaint_risk': 0.05,
            'refinance_likelihood': 0.3
        },
        'advisor_metrics': {
            'empathy_score': 8.5,
            'compliance_adherence': 9.0,
            'solution_effectiveness': 8.0
        },
        'compliance_flags': [],
        'required_disclosures': ['PMI removal disclosure'],
        'issue_resolved': False,
        'first_call_resolution': False,
        'escalation_needed': False,
        'topics_discussed': ['PMI', 'home_value', 'appraisal'],
        'confidence_score': 0.92,
        'product_opportunities': ['refinance_evaluation'],
        'payment_concerns': [],
        'property_related_issues': []
    }


@pytest.fixture
def mock_action_plan_response():
    """Mock response for OpenAI Responses API action plan generation."""
    return {
        'borrower_plan': {
            'immediate_actions': [{
                'action': 'Send PMI removal application form',
                'timeline': 'Within 24 hours',
                'priority': 'high',
                'auto_executable': True,
                'description': 'Email automated PMI removal application'
            }],
            'follow_ups': [{
                'action': 'Schedule appraisal if needed',
                'due_date': '2024-02-15',
                'owner': 'Customer Service',
                'trigger_condition': 'Upon application submission'
            }],
            'personalized_offers': ['Consider refinance evaluation'],
            'risk_mitigation': ['Monitor payment history consistency']
        },
        'advisor_plan': {
            'coaching_items': ['Review PMI removal process documentation'],
            'performance_feedback': {
                'strengths': ['Clear communication', 'Good product knowledge'],
                'improvements': ['Could probe more about customer timeline'],
                'score_explanations': ['Handled request efficiently']
            },
            'training_recommendations': ['Advanced PMI regulations training'],
            'next_actions': ['Update customer notes with application status']
        },
        'supervisor_plan': {
            'escalation_items': [{
                'item': 'Complex PMI calculation',
                'reason': 'Customer questions property value assessment',
                'priority': 'medium',
                'action_required': 'Review with underwriting team'
            }],
            'team_patterns': ['Increase in PMI removal requests'],
            'compliance_review': ['Ensure all PMI disclosures provided'],
            'approval_required': False,
            'process_improvements': ['Streamline PMI application process']
        },
        'leadership_plan': {
            'portfolio_insights': ['Growing demand for PMI removal services'],
            'strategic_opportunities': ['Develop automated PMI removal workflow'],
            'risk_indicators': ['Potential increase in appraisal costs'],
            'trend_analysis': ['Market conditions favorable for PMI removal'],
            'resource_allocation': ['Consider additional PMI specialist training']
        }
    }


class TestFullPipeline:
    """Test the complete transcript generation and storage pipeline."""
    
    @patch('openai.OpenAI')
    def test_generate_and_store_transcript(self, mock_openai, temp_db):
        """Test generating a transcript and storing it in the database."""
        # Setup mock OpenAI response
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses = None  # Skip Responses API
        
        # Mock successful Chat Completions response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """Advisor: Thank you for calling. How can I help you today?
Customer: I received a notice about an escrow shortage and I'm confused about what this means."""
        mock_client.chat.completions.create.return_value = mock_response
        
        generator = TranscriptGenerator(api_key="test_key")
        store = TranscriptStore(temp_db)
        
        # Generate transcript
        transcript = generator.generate(
            scenario="escrow_shortage",
            sentiment="confused",
            customer_id="CUST_123",
            advisor_id="ADV_456"
        )
        
        # Verify transcript
        assert isinstance(transcript, Transcript)
        assert len(transcript.messages) == 2
        assert transcript.scenario == "escrow_shortage"
        assert transcript.sentiment == "confused"
        assert transcript.customer_id == "CUST_123"
        
        # Store transcript
        result = store.store(transcript)
        assert result == transcript.id
        
        # Retrieve and verify
        retrieved = store.get_by_id(transcript.id)
        assert retrieved is not None
        assert retrieved.id == transcript.id
        assert len(retrieved.messages) == 2
    
    @patch('openai.OpenAI')
    def test_generate_batch_and_search(self, mock_openai, temp_db):
        """Test generating multiple transcripts and searching."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses = None
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Agent: Hello\nCustomer: Hi there"
        mock_client.chat.completions.create.return_value = mock_response
        
        generator = TranscriptGenerator(api_key="test_key")
        store = TranscriptStore(temp_db)
        
        # Generate batch
        transcripts = generator.generate_batch(3, customer_id="CUST_BATCH", topic="test")
        
        assert len(transcripts) == 3
        
        # Store all
        for transcript in transcripts:
            store.store(transcript)
        
        # Search by customer
        results = store.search_by_customer("CUST_BATCH")
        assert len(results) == 3
        
        # Verify all have the expected attributes
        for result in results:
            assert result.customer_id == "CUST_BATCH"
            assert result.topic == "test"
    
    @patch('openai.OpenAI')
    def test_error_handling_in_pipeline(self, mock_openai, temp_db):
        """Test error handling throughout the pipeline."""
        # Mock API error
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses = None
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_client.completions.create.side_effect = Exception("API Error")
        
        generator = TranscriptGenerator(api_key="test_key")
        
        with pytest.raises(Exception, match="All API methods failed"):
            generator.generate(scenario="test")
    
    @patch('openai.OpenAI')
    def test_different_scenarios_work(self, mock_openai, temp_db):
        """Test pipeline with various scenarios."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses = None
        
        # Mock response that varies based on input
        def mock_response_func(*args, **kwargs):
            response = MagicMock()
            response.choices = [MagicMock()]
            response.choices[0].message.content = "Agent: Test conversation\nUser: Response"
            return response
        
        mock_client.chat.completions.create.side_effect = mock_response_func
        
        generator = TranscriptGenerator(api_key="test_key")
        store = TranscriptStore(temp_db)
        
        # Test different scenarios
        scenarios = ["escrow_shortage", "payment_dispute", "refinance_inquiry"]
        
        for scenario in scenarios:
            transcript = generator.generate(
                scenario=scenario,
                sentiment="neutral",
                customer_id=f"CUST_{scenario[:4].upper()}"
            )
            
            # Verify basic properties
            assert transcript.scenario == scenario
            assert transcript.sentiment == "neutral"
            assert len(transcript.messages) >= 1
            
            # Store and verify retrieval
            store.store(transcript)
            retrieved = store.get_by_id(transcript.id)
            # Note: scenario is not stored in DB schema, but customer_id is
            assert retrieved.customer_id == f"CUST_{scenario[:4].upper()}"
            assert len(retrieved.messages) >= 1
    
    def test_data_integrity_through_pipeline(self, temp_db):
        """Test that data maintains integrity through the entire pipeline."""
        store = TranscriptStore(temp_db)
        
        # Create a transcript manually to test storage integrity
        original_transcript = Transcript(
            id="TEST_001",
            messages=[
                Message("Advisor", "Hello", timestamp="2024-01-01T10:00:00Z"),
                Message("Customer", "Hi there", timestamp="2024-01-01T10:00:15Z", sentiment="positive")
            ],
            customer_id="CUST_999",
            advisor_id="ADV_123",
            timestamp="2024-01-01T10:00:00Z",
            topic="greeting",
            duration=300,
            sentiment="positive"
        )
        
        # Store
        store.store(original_transcript)
        
        # Retrieve
        retrieved_transcript = store.get_by_id("TEST_001")
        
        # Verify all data integrity
        assert retrieved_transcript.id == original_transcript.id
        assert retrieved_transcript.customer_id == original_transcript.customer_id
        assert retrieved_transcript.advisor_id == original_transcript.advisor_id
        assert retrieved_transcript.topic == original_transcript.topic
        assert retrieved_transcript.duration == original_transcript.duration
        assert retrieved_transcript.sentiment == original_transcript.sentiment
        
        # Verify messages
        assert len(retrieved_transcript.messages) == len(original_transcript.messages)
        for i, (orig_msg, retr_msg) in enumerate(zip(original_transcript.messages, retrieved_transcript.messages)):
            assert retr_msg.speaker == orig_msg.speaker
            assert retr_msg.text == orig_msg.text
    
    def test_end_to_end_realistic_workflow(self, temp_db):
        """Test a realistic end-to-end workflow without external APIs."""
        store = TranscriptStore(temp_db)
        
        # Simulate what would happen with real data
        transcript = Transcript(
            id="WORKFLOW_001",
            messages=[
                Message("Advisor", "Good morning, thank you for calling. How can I help you?"),
                Message("Customer", "Hi, I got this escrow shortage notice and I don't understand it."),
                Message("Advisor", "I'd be happy to explain that. An escrow shortage occurs when..."),
                Message("Customer", "Oh, I see. So what do I need to do?"),
                Message("Advisor", "You have a few options...")
            ],
            customer_id="CUST_555",
            advisor_id="ADV_789",
            topic="escrow_shortage",
            duration=450,
            sentiment="initially_confused_then_satisfied",
            urgency="medium"
        )
        
        # Store the transcript
        stored_id = store.store(transcript)
        assert stored_id == transcript.id
        
        # Simulate searching/retrieval operations
        retrieved = store.get_by_id(stored_id)
        assert retrieved is not None
        
        # Simulate customer search
        customer_transcripts = store.search_by_customer("CUST_555")
        assert len(customer_transcripts) == 1
        assert customer_transcripts[0].id == stored_id
        
        # Simulate topic search
        escrow_transcripts = store.search_by_topic("escrow_shortage")
        assert len(escrow_transcripts) == 1
        assert escrow_transcripts[0].topic == "escrow_shortage"
        
        # Verify the data flow worked perfectly
        final_transcript = customer_transcripts[0]
        assert len(final_transcript.messages) == 5
        assert final_transcript.sentiment == "initially_confused_then_satisfied"
        assert final_transcript.duration == 450

    @patch('openai.OpenAI')
    def test_complete_analysis_workflow(self, mock_openai, temp_db, mock_analysis_response):
        """Test the complete workflow: Generate → Store → Analyze."""
        # Setup mocks for transcript generation
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_client.responses = None  # Skip Responses API for transcript generation
        
        # Mock transcript generation response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = """CSR: Thank you for calling. How can I help you?
Customer: I want to remove PMI from my mortgage. My home value has increased."""
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock analysis response (using Responses API)
        mock_analysis_client = MagicMock()
        mock_analysis_response_obj = MagicMock()
        # Try different response attribute patterns
        mock_analysis_response_obj.output_parsed = mock_analysis_response
        mock_analysis_response_obj.output = [MagicMock()]
        mock_analysis_response_obj.output[0].content = [MagicMock()]
        mock_analysis_response_obj.output[0].content[0].parsed = mock_analysis_response
        mock_analysis_client.responses.create.return_value = mock_analysis_response_obj
        
        # Initialize components
        with patch('src.analyzers.call_analyzer.openai.OpenAI', return_value=mock_analysis_client):
            transcript_generator = TranscriptGenerator(api_key="test_key")
            transcript_store = TranscriptStore(temp_db)
            call_analyzer = CallAnalyzer(api_key="test_key")
            analysis_store = AnalysisStore(temp_db)
            
            # Step 1: Generate transcript
            transcript = transcript_generator.generate(
                scenario="pmi_removal",
                customer_id="CUST_ANALYSIS",
                urgency="medium"
            )
            
            # Step 2: Store transcript
            transcript_store.store(transcript)
            
            # Step 3: Analyze transcript
            analysis = call_analyzer.analyze(transcript)
            
            # Verify analysis structure
            assert analysis['primary_intent'] == 'PMI removal request'
            assert analysis['confidence_score'] == 0.92
            assert 'borrower_risks' in analysis
            assert 'advisor_metrics' in analysis
            assert analysis['transcript_id'] == transcript.id
            
            # Step 4: Store analysis
            analysis_store.store(analysis)
            
            # Step 5: Verify retrieval
            stored_analysis = analysis_store.get_by_transcript_id(transcript.id)
            assert stored_analysis is not None
            assert stored_analysis['primary_intent'] == analysis['primary_intent']
            assert stored_analysis['confidence_score'] == analysis['confidence_score']
            
            # Step 6: Verify metrics
            metrics = analysis_store.get_metrics_summary()
            assert metrics['total_analyses'] == 1
            assert metrics['avg_confidence_score'] == 0.92

    @patch('openai.OpenAI')
    def test_complete_action_plan_workflow(self, mock_openai, temp_db, mock_analysis_response, mock_action_plan_response):
        """Test the complete workflow: Generate → Store → Analyze → Generate Action Plan → Store Plan."""
        # Setup mocks for transcript generation
        mock_transcript_client = MagicMock()
        mock_openai.return_value = mock_transcript_client
        mock_transcript_client.responses = None
        
        mock_transcript_response = MagicMock()
        mock_transcript_response.choices = [MagicMock()]
        mock_transcript_response.choices[0].message.content = """CSR: Thank you for calling. How can I help you?
Customer: I want to remove PMI from my mortgage. My home value has increased significantly."""
        mock_transcript_client.chat.completions.create.return_value = mock_transcript_response
        
        # Mock analysis and action plan clients
        mock_analysis_client = MagicMock()
        mock_analysis_response_obj = MagicMock()
        mock_analysis_response_obj.output_parsed = mock_analysis_response
        mock_analysis_response_obj.output = [MagicMock()]
        mock_analysis_response_obj.output[0].content = [MagicMock()]
        mock_analysis_response_obj.output[0].content[0].parsed = mock_analysis_response
        mock_analysis_client.responses.create.return_value = mock_analysis_response_obj
        
        mock_action_plan_client = MagicMock()
        mock_action_plan_response_obj = MagicMock()
        mock_action_plan_response_obj.output_parsed = mock_action_plan_response
        mock_action_plan_response_obj.output = [MagicMock()]
        mock_action_plan_response_obj.output[0].content = [MagicMock()]
        mock_action_plan_response_obj.output[0].content[0].parsed = mock_action_plan_response
        mock_action_plan_client.responses.create.return_value = mock_action_plan_response_obj
        
        # Initialize all components
        with patch('src.analyzers.call_analyzer.openai.OpenAI', return_value=mock_analysis_client), \
             patch('src.generators.action_plan_generator.openai.OpenAI', return_value=mock_action_plan_client):
            
            transcript_generator = TranscriptGenerator(api_key="test_key")
            transcript_store = TranscriptStore(temp_db)
            call_analyzer = CallAnalyzer(api_key="test_key")
            analysis_store = AnalysisStore(temp_db)
            action_plan_generator = ActionPlanGenerator(api_key="test_key")
            action_plan_store = ActionPlanStore(temp_db)
            
            # Step 1: Generate and store transcript
            transcript = transcript_generator.generate(
                scenario="pmi_removal",
                customer_id="CUST_ACTION_PLAN",
                urgency="medium"
            )
            transcript_store.store(transcript)
            
            # Step 2: Analyze and store analysis
            analysis = call_analyzer.analyze(transcript)
            analysis_store.store(analysis)
            
            # Step 3: Generate action plan
            action_plan = action_plan_generator.generate(analysis, transcript)
            
            # Verify action plan structure - all four layers
            assert 'borrower_plan' in action_plan
            assert 'advisor_plan' in action_plan
            assert 'supervisor_plan' in action_plan
            assert 'leadership_plan' in action_plan
            
            # Verify borrower plan structure
            borrower_plan = action_plan['borrower_plan']
            assert 'immediate_actions' in borrower_plan
            assert 'follow_ups' in borrower_plan
            assert 'personalized_offers' in borrower_plan
            assert 'risk_mitigation' in borrower_plan
            
            # Verify action plan metadata
            assert 'plan_id' in action_plan
            assert 'analysis_id' in action_plan
            assert 'transcript_id' in action_plan
            assert action_plan['transcript_id'] == transcript.id
            assert action_plan['analysis_id'] == analysis['analysis_id']
            
            # Verify risk-based routing
            assert 'risk_level' in action_plan
            assert 'approval_route' in action_plan
            assert 'queue_status' in action_plan
            assert action_plan['risk_level'] in ['low', 'medium', 'high']
            
            # Step 4: Store action plan
            plan_id = action_plan_store.store(action_plan)
            assert plan_id == action_plan['plan_id']
            
            # Step 5: Verify retrieval
            stored_plan = action_plan_store.get_by_id(plan_id)
            assert stored_plan is not None
            assert stored_plan['plan_id'] == action_plan['plan_id']
            assert stored_plan['transcript_id'] == transcript.id
            
            # Step 6: Verify metrics
            plan_metrics = action_plan_store.get_summary_metrics()
            assert plan_metrics['total_plans'] == 1
            
            # Step 7: Verify cross-referential integrity
            stored_analysis = analysis_store.get_by_transcript_id(transcript.id)
            stored_plan_by_transcript = action_plan_store.get_by_transcript_id(transcript.id)
            
            assert stored_analysis['transcript_id'] == transcript.id
            assert stored_plan_by_transcript['transcript_id'] == transcript.id
            assert stored_plan_by_transcript['analysis_id'] == stored_analysis['analysis_id']

    def test_approval_workflow_all_routes(self, temp_db):
        """Test approval workflow for all risk levels: high → supervisor, medium → advisor, low → auto."""
        action_plan_store = ActionPlanStore(temp_db)
        
        # Create action plans with different risk levels
        high_risk_plan = {
            'plan_id': 'PLAN_HIGH_001',
            'analysis_id': 'ANALYSIS_HIGH_001',
            'transcript_id': 'TRANSCRIPT_HIGH_001',
            'risk_level': 'high',
            'approval_route': 'supervisor_approval',
            'queue_status': 'pending_supervisor',
            'auto_executable': False,
            'generator_version': '1.0',
            'routing_reason': 'High risk: compliance flags detected',
            'borrower_plan': {'immediate_actions': [], 'follow_ups': [], 'personalized_offers': [], 'risk_mitigation': []},
            'advisor_plan': {'coaching_items': [], 'performance_feedback': {'strengths': [], 'improvements': [], 'score_explanations': []}, 'training_recommendations': [], 'next_actions': []},
            'supervisor_plan': {'escalation_items': [], 'team_patterns': [], 'compliance_review': [], 'approval_required': True, 'process_improvements': []},
            'leadership_plan': {'portfolio_insights': [], 'strategic_opportunities': [], 'risk_indicators': [], 'trend_analysis': [], 'resource_allocation': []}
        }
        
        medium_risk_plan = {
            'plan_id': 'PLAN_MEDIUM_001',
            'analysis_id': 'ANALYSIS_MEDIUM_001',
            'transcript_id': 'TRANSCRIPT_MEDIUM_001',
            'risk_level': 'medium',
            'approval_route': 'advisor_approval',
            'queue_status': 'pending_advisor',
            'auto_executable': False,
            'generator_version': '1.0',
            'routing_reason': 'Medium risk: moderate confidence score',
            'borrower_plan': {'immediate_actions': [], 'follow_ups': [], 'personalized_offers': [], 'risk_mitigation': []},
            'advisor_plan': {'coaching_items': [], 'performance_feedback': {'strengths': [], 'improvements': [], 'score_explanations': []}, 'training_recommendations': [], 'next_actions': []},
            'supervisor_plan': {'escalation_items': [], 'team_patterns': [], 'compliance_review': [], 'approval_required': False, 'process_improvements': []},
            'leadership_plan': {'portfolio_insights': [], 'strategic_opportunities': [], 'risk_indicators': [], 'trend_analysis': [], 'resource_allocation': []}
        }
        
        low_risk_plan = {
            'plan_id': 'PLAN_LOW_001',
            'analysis_id': 'ANALYSIS_LOW_001',
            'transcript_id': 'TRANSCRIPT_LOW_001',
            'risk_level': 'low',
            'approval_route': 'auto_approved',
            'queue_status': 'approved',
            'auto_executable': True,
            'generator_version': '1.0',
            'routing_reason': 'Low risk - auto-approved',
            'borrower_plan': {'immediate_actions': [], 'follow_ups': [], 'personalized_offers': [], 'risk_mitigation': []},
            'advisor_plan': {'coaching_items': [], 'performance_feedback': {'strengths': [], 'improvements': [], 'score_explanations': []}, 'training_recommendations': [], 'next_actions': []},
            'supervisor_plan': {'escalation_items': [], 'team_patterns': [], 'compliance_review': [], 'approval_required': False, 'process_improvements': []},
            'leadership_plan': {'portfolio_insights': [], 'strategic_opportunities': [], 'risk_indicators': [], 'trend_analysis': [], 'resource_allocation': []}
        }
        
        # Store all plans
        action_plan_store.store(high_risk_plan)
        action_plan_store.store(medium_risk_plan)
        action_plan_store.store(low_risk_plan)
        
        # Test approval queues
        supervisor_queue = action_plan_store.get_approval_queue('pending_supervisor')
        advisor_queue = action_plan_store.get_approval_queue('pending_advisor')
        approved_plans = action_plan_store.get_approval_queue('approved')
        
        assert len(supervisor_queue) == 1
        assert len(advisor_queue) == 1
        assert len(approved_plans) == 1
        
        assert supervisor_queue[0]['plan_id'] == 'PLAN_HIGH_001'
        assert advisor_queue[0]['plan_id'] == 'PLAN_MEDIUM_001'
        assert approved_plans[0]['plan_id'] == 'PLAN_LOW_001'
        
        # Test approval workflow
        high_plan_approved = action_plan_store.approve_plan('PLAN_HIGH_001', 'SUPERVISOR_001')
        assert high_plan_approved is True
        
        medium_plan_approved = action_plan_store.approve_plan('PLAN_MEDIUM_001', 'ADVISOR_001')
        assert medium_plan_approved is True
        
        # Verify approval updates
        approved_high_plan = action_plan_store.get_by_id('PLAN_HIGH_001')
        approved_medium_plan = action_plan_store.get_by_id('PLAN_MEDIUM_001')
        
        assert approved_high_plan['queue_status'] == 'approved'
        assert approved_high_plan['approved_by'] == 'SUPERVISOR_001'
        assert approved_high_plan['approved_at'] is not None
        
        assert approved_medium_plan['queue_status'] == 'approved'
        assert approved_medium_plan['approved_by'] == 'ADVISOR_001'
        assert approved_medium_plan['approved_at'] is not None
        
        # Test rejection workflow
        test_rejection_plan = {
            'plan_id': 'PLAN_REJECT_001',
            'analysis_id': 'ANALYSIS_REJECT_001',
            'transcript_id': 'TRANSCRIPT_REJECT_001',
            'risk_level': 'high',
            'approval_route': 'supervisor_approval',
            'queue_status': 'pending_supervisor',
            'auto_executable': False,
            'generator_version': '1.0',
            'routing_reason': 'High risk: requires review',
            'borrower_plan': {'immediate_actions': [], 'follow_ups': [], 'personalized_offers': [], 'risk_mitigation': []},
            'advisor_plan': {'coaching_items': [], 'performance_feedback': {'strengths': [], 'improvements': [], 'score_explanations': []}, 'training_recommendations': [], 'next_actions': []},
            'supervisor_plan': {'escalation_items': [], 'team_patterns': [], 'compliance_review': [], 'approval_required': True, 'process_improvements': []},
            'leadership_plan': {'portfolio_insights': [], 'strategic_opportunities': [], 'risk_indicators': [], 'trend_analysis': [], 'resource_allocation': []}
        }
        
        action_plan_store.store(test_rejection_plan)
        rejected = action_plan_store.reject_plan('PLAN_REJECT_001', 'SUPERVISOR_002')
        assert rejected is True
        
        rejected_plan = action_plan_store.get_by_id('PLAN_REJECT_001')
        assert rejected_plan['queue_status'] == 'rejected'
        assert rejected_plan['approved_by'] == 'SUPERVISOR_002'
        
        # Final metrics check
        final_metrics = action_plan_store.get_summary_metrics()
        assert final_metrics['total_plans'] == 4
        assert final_metrics['status_distribution']['approved'] == 3
        assert final_metrics['status_distribution']['rejected'] == 1

    @patch('openai.OpenAI')
    def test_batch_processing_with_analysis_and_plans(self, mock_openai, temp_db, mock_analysis_response, mock_action_plan_response):
        """Test batch processing: Generate multiple transcripts → Analyze all → Generate action plans for all."""
        # Setup mocks
        mock_transcript_client = MagicMock()
        mock_openai.return_value = mock_transcript_client
        mock_transcript_client.responses = None
        
        mock_transcript_response = MagicMock()
        mock_transcript_response.choices = [MagicMock()]
        mock_transcript_response.choices[0].message.content = "CSR: Hello\nCustomer: Hi, I need help"
        mock_transcript_client.chat.completions.create.return_value = mock_transcript_response
        
        # Mock analysis and action plan responses
        mock_analysis_client = MagicMock()
        mock_analysis_response_obj = MagicMock()
        # Return a fresh copy each time to avoid mutation issues
        mock_analysis_response_obj.output_parsed = mock_analysis_response.copy()
        mock_analysis_response_obj.output = [MagicMock()]
        mock_analysis_response_obj.output[0].content = [MagicMock()]
        mock_analysis_response_obj.output[0].content[0].parsed = mock_analysis_response.copy()
        # Use side_effect to return a fresh response object each time
        mock_analysis_client.responses.create.side_effect = lambda **kwargs: type('MockResponse', (), {
            'output_parsed': mock_analysis_response.copy(),
            'output': [type('MockOutput', (), {
                'content': [type('MockContent', (), {'parsed': mock_analysis_response.copy()})()]
            })()]
        })()
        
        mock_action_plan_client = MagicMock()
        # Use side_effect to return a fresh response object each time
        mock_action_plan_client.responses.create.side_effect = lambda **kwargs: type('MockResponse', (), {
            'output_parsed': mock_action_plan_response.copy(),
            'output': [type('MockOutput', (), {
                'content': [type('MockContent', (), {'parsed': mock_action_plan_response.copy()})()]
            })()]
        })()
        
        # Initialize components
        with patch('src.analyzers.call_analyzer.openai.OpenAI', return_value=mock_analysis_client), \
             patch('src.generators.action_plan_generator.openai.OpenAI', return_value=mock_action_plan_client):
            
            transcript_generator = TranscriptGenerator(api_key="test_key")
            transcript_store = TranscriptStore(temp_db)
            call_analyzer = CallAnalyzer(api_key="test_key")
            analysis_store = AnalysisStore(temp_db)
            action_plan_generator = ActionPlanGenerator(api_key="test_key")
            action_plan_store = ActionPlanStore(temp_db)
            
            # Generate multiple transcripts with different scenarios
            scenarios = [
                {'scenario': 'pmi_removal', 'customer_id': 'BATCH_001'},
                {'scenario': 'escrow_shortage', 'customer_id': 'BATCH_002'}, 
                {'scenario': 'payment_dispute', 'customer_id': 'BATCH_003'}
            ]
            
            transcripts = []
            for params in scenarios:
                transcript = transcript_generator.generate(**params)
                transcript_store.store(transcript)
                transcripts.append(transcript)
            
            assert len(transcripts) == 3
            
            # Analyze all transcripts
            analyses = []
            for transcript in transcripts:
                analysis = call_analyzer.analyze(transcript)
                analysis_store.store(analysis)
                analyses.append(analysis)
            
            assert len(analyses) == 3
            
            # Generate action plans for all
            action_plans = []
            for transcript, analysis in zip(transcripts, analyses):
                action_plan = action_plan_generator.generate(analysis, transcript)
                action_plan_store.store(action_plan)
                action_plans.append(action_plan)
            
            assert len(action_plans) == 3
            
            # Verify system metrics consistency
            transcript_count = len(transcript_store.get_all())
            analysis_metrics = analysis_store.get_metrics_summary()
            plan_metrics = action_plan_store.get_summary_metrics()
            
            assert transcript_count == 3
            assert analysis_metrics['total_analyses'] == 3
            assert plan_metrics['total_plans'] == 3
            
            # Verify cross-referential integrity for all items
            for transcript, analysis, action_plan in zip(transcripts, analyses, action_plans):
                assert analysis['transcript_id'] == transcript.id
                assert action_plan['transcript_id'] == transcript.id
                assert action_plan['analysis_id'] == analysis['analysis_id']

    def test_system_metrics_consistency(self, temp_db):
        """Test that metrics are consistent across all system components."""
        # Initialize stores
        transcript_store = TranscriptStore(temp_db)
        analysis_store = AnalysisStore(temp_db)
        action_plan_store = ActionPlanStore(temp_db)
        
        # Create test data manually to ensure consistency
        test_transcripts = []
        test_analyses = []
        test_action_plans = []
        
        for i in range(5):
            # Create transcript
            transcript = Transcript(
                id=f'METRICS_TRANSCRIPT_{i:03d}',
                messages=[
                    Message("CSR", f"Hello, call {i}"),
                    Message("CUSTOMER", f"Hi, I need help with issue {i}")
                ],
                customer_id=f'METRICS_CUST_{i:03d}',
                topic=f'test_topic_{i}'
            )
            transcript_store.store(transcript)
            test_transcripts.append(transcript)
            
            # Create analysis
            analysis = {
                'analysis_id': f'METRICS_ANALYSIS_{i:03d}',
                'transcript_id': transcript.id,
                'primary_intent': f'test_intent_{i}',
                'urgency_level': 'medium',
                'confidence_score': 0.8 + (i * 0.04),  # 0.8, 0.84, 0.88, 0.92, 0.96
                'borrower_risks': {'delinquency_risk': 0.1 + (i * 0.1)},
                'advisor_metrics': {'empathy_score': 7.0 + i},
                'compliance_flags': [],
                'topics_discussed': [f'topic_{i}'],
                'issue_resolved': i % 2 == 0,
                'first_call_resolution': i % 3 == 0,
                'escalation_needed': False,
                'analyzer_version': '1.0'
            }
            analysis_store.store(analysis)
            test_analyses.append(analysis)
            
            # Create action plan
            risk_level = 'low' if i < 2 else 'medium' if i < 4 else 'high'
            approval_route = 'auto_approved' if risk_level == 'low' else 'advisor_approval' if risk_level == 'medium' else 'supervisor_approval'
            if risk_level == 'low':
                queue_status = 'approved'
            elif risk_level == 'medium':
                queue_status = 'pending_advisor'
            else:
                queue_status = 'pending_supervisor'
            
            action_plan = {
                'plan_id': f'METRICS_PLAN_{i:03d}',
                'analysis_id': analysis['analysis_id'],
                'transcript_id': transcript.id,
                'risk_level': risk_level,
                'approval_route': approval_route,
                'queue_status': queue_status,
                'auto_executable': risk_level == 'low',
                'generator_version': '1.0',
                'routing_reason': f'{risk_level.title()} risk detected',
                'borrower_plan': {'immediate_actions': [], 'follow_ups': [], 'personalized_offers': [], 'risk_mitigation': []},
                'advisor_plan': {'coaching_items': [], 'performance_feedback': {'strengths': [], 'improvements': [], 'score_explanations': []}, 'training_recommendations': [], 'next_actions': []},
                'supervisor_plan': {'escalation_items': [], 'team_patterns': [], 'compliance_review': [], 'approval_required': risk_level == 'high', 'process_improvements': []},
                'leadership_plan': {'portfolio_insights': [], 'strategic_opportunities': [], 'risk_indicators': [], 'trend_analysis': [], 'resource_allocation': []}
            }
            action_plan_store.store(action_plan)
            test_action_plans.append(action_plan)
        
        # Verify counts are consistent
        transcript_count = len(transcript_store.get_all())
        analysis_metrics = analysis_store.get_metrics_summary()
        plan_metrics = action_plan_store.get_summary_metrics()
        
        assert transcript_count == 5
        assert analysis_metrics['total_analyses'] == 5
        assert plan_metrics['total_plans'] == 5
        
        # Verify specific metrics calculations
        expected_avg_confidence = (0.8 + 0.84 + 0.88 + 0.92 + 0.96) / 5  # 0.88
        assert abs(analysis_metrics['avg_confidence_score'] - expected_avg_confidence) < 0.01
        
        # Verify risk distribution
        assert plan_metrics['risk_distribution']['low'] == 2
        assert plan_metrics['risk_distribution']['medium'] == 2
        assert plan_metrics['risk_distribution']['high'] == 1
        
        # Verify approval queue counts
        assert plan_metrics['pending_approvals'] == 3  # 2 medium + 1 high
        
        # Verify auto-executable percentage
        expected_auto_pct = (2 / 5) * 100  # Only low-risk are auto-executable
        assert plan_metrics['auto_executable_percentage'] == expected_auto_pct

    def test_edge_cases_complete_system(self, temp_db):
        """Test edge cases across the complete system."""
        transcript_store = TranscriptStore(temp_db)
        analysis_store = AnalysisStore(temp_db) 
        action_plan_store = ActionPlanStore(temp_db)
        
        # Test 1: Empty transcript
        empty_transcript = Transcript(id='EMPTY_001', messages=[])
        transcript_store.store(empty_transcript)
        
        retrieved_empty = transcript_store.get_by_id('EMPTY_001')
        assert retrieved_empty is not None
        assert len(retrieved_empty.messages) == 0
        
        # Test 2: Analysis with edge case values
        edge_analysis = {
            'analysis_id': 'EDGE_ANALYSIS_001',
            'transcript_id': 'EMPTY_001',
            'primary_intent': '',  # Empty intent
            'confidence_score': 0.0,  # Minimum confidence
            'borrower_risks': {'delinquency_risk': 1.0},  # Maximum risk
            'advisor_metrics': {'empathy_score': 0.0},  # Minimum score
            'compliance_flags': ['multiple', 'compliance', 'issues'],  # Multiple flags
            'topics_discussed': [],  # No topics
            'issue_resolved': False,
            'first_call_resolution': False,
            'escalation_needed': True,
            'analyzer_version': '1.0'
        }
        analysis_store.store(edge_analysis)
        
        retrieved_edge_analysis = analysis_store.get_by_id('EDGE_ANALYSIS_001')
        assert retrieved_edge_analysis is not None
        assert retrieved_edge_analysis['confidence_score'] == 0.0
        
        # Test 3: Action plan with edge case routing
        edge_action_plan = {
            'plan_id': 'EDGE_PLAN_001',
            'analysis_id': 'EDGE_ANALYSIS_001',
            'transcript_id': 'EMPTY_001',
            'risk_level': 'high',
            'approval_route': 'supervisor_approval',
            'queue_status': 'pending_supervisor',
            'auto_executable': False,
            'generator_version': '1.0',
            'routing_reason': 'Multiple compliance flags and maximum risk',
            'borrower_plan': {'immediate_actions': [], 'follow_ups': [], 'personalized_offers': [], 'risk_mitigation': []},
            'advisor_plan': {'coaching_items': [], 'performance_feedback': {'strengths': [], 'improvements': [], 'score_explanations': []}, 'training_recommendations': [], 'next_actions': []},
            'supervisor_plan': {'escalation_items': [], 'team_patterns': [], 'compliance_review': [], 'approval_required': True, 'process_improvements': []},
            'leadership_plan': {'portfolio_insights': [], 'strategic_opportunities': [], 'risk_indicators': [], 'trend_analysis': [], 'resource_allocation': []}
        }
        action_plan_store.store(edge_action_plan)
        
        retrieved_edge_plan = action_plan_store.get_by_id('EDGE_PLAN_001')
        assert retrieved_edge_plan is not None
        assert retrieved_edge_plan['risk_level'] == 'high'
        
        # Test 4: Non-existent record handling
        assert transcript_store.get_by_id('NONEXISTENT') is None
        assert analysis_store.get_by_id('NONEXISTENT') is None
        assert action_plan_store.get_by_id('NONEXISTENT') is None
        
        # Test 5: Metrics with edge case data
        metrics = analysis_store.get_metrics_summary()
        plan_metrics = action_plan_store.get_summary_metrics()
        
        assert metrics['total_analyses'] == 1
        assert metrics['avg_confidence_score'] == 0.0
        
        assert plan_metrics['total_plans'] == 1
        assert plan_metrics['risk_distribution']['high'] == 1
        assert plan_metrics['pending_approvals'] == 1