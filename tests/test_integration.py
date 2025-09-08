"""Integration tests for the simplified transcript generation system."""
import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from src.generators.transcript_generator import TranscriptGenerator
from src.storage.transcript_store import TranscriptStore
from src.models.transcript import Transcript, Message


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


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