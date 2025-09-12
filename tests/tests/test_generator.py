"""Tests for transcript generation - agentic approach."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.generators.transcript_generator import TranscriptGenerator
from src.generators.prompt_builder import PromptBuilder
from src.generators.response_parser import ResponseParser
from src.models.transcript import Transcript


class TestPromptBuilder:
    """Test the generic prompt builder."""
    
    def test_build_basic_prompt(self):
        """Test building a basic prompt."""
        builder = PromptBuilder()
        
        prompt = builder.build_prompt()
        
        assert isinstance(prompt, str)
        assert prompt == "Generate a conversation"
    
    def test_build_prompt_with_parameters(self):
        """Test building prompt with any parameters."""
        builder = PromptBuilder()
        
        prompt = builder.build_prompt(scenario="escrow_shortage", sentiment="frustrated")
        
        assert "Generate a conversation with:" in prompt
        assert "scenario: escrow_shortage" in prompt
        assert "sentiment: frustrated" in prompt
    
    def test_build_prompt_ignores_none_values(self):
        """Test that None values are ignored."""
        builder = PromptBuilder()
        
        prompt = builder.build_prompt(scenario="test", empty_param=None)
        
        assert "scenario: test" in prompt
        assert "empty_param" not in prompt
    
    def test_backward_compatibility(self):
        """Test backward compatibility method."""
        builder = PromptBuilder()
        
        prompt = builder.build_transcript_prompt(topic="greeting")
        
        assert "topic: greeting" in prompt


class TestResponseParser:
    """Test generic response parsing."""
    
    def test_parse_text_response(self):
        """Test parsing a simple text response."""
        parser = ResponseParser()
        
        response = "Advisor: Hello, how can I help?\nCustomer: I have a question about my loan."
        
        result = parser.parse_response(response)
        
        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) == 2
        assert result["messages"][0]["speaker"] == "Advisor"
        assert result["messages"][1]["speaker"] == "Customer"
    
    def test_parse_json_response(self):
        """Test parsing JSON response."""
        parser = ResponseParser()
        
        response = '{"messages": [{"speaker": "System", "text": "Call started"}], "topic": "greeting"}'
        
        result = parser.parse_response(response)
        
        assert isinstance(result, dict)
        assert "messages" in result
        assert "topic" in result
        assert result["topic"] == "greeting"
    
    def test_parse_complex_response(self):
        """Test parsing complex response format."""
        parser = ResponseParser()
        
        response = {
            "choices": [{
                "message": {
                    "content": "Advisor: Thank you for calling.\nCustomer: Hi there."
                }
            }]
        }
        
        result = parser.parse_response(response)
        
        assert isinstance(result, dict)
        assert "messages" in result
        assert len(result["messages"]) == 2
    
    def test_parse_malformed_response(self):
        """Test parsing malformed response gracefully."""
        parser = ResponseParser()
        
        response = "This is not a proper conversation format"
        
        result = parser.parse_response(response)
        
        assert isinstance(result, dict)
        assert "raw_text" in result


class TestTranscriptGenerator:
    """Test the transcript generator."""
    
    @patch('openai.OpenAI')
    def test_generator_initialization(self, mock_openai):
        """Test generator initialization with API key."""
        generator = TranscriptGenerator(api_key="test-key")
        
        assert generator.api_key == "test-key"
        assert generator.client is not None
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'env-key'})
    @patch('openai.OpenAI')
    def test_generator_uses_env_key(self, mock_openai):
        """Test generator uses environment variable for API key."""
        generator = TranscriptGenerator()
        
        assert generator.api_key == "env-key"
    
    @patch('openai.OpenAI')
    def test_generate_basic_transcript(self, mock_openai):
        """Test generating a basic transcript."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Advisor: Hello\nCustomer: Hi"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock responses attribute as None to skip Responses API
        mock_client.responses = None
        
        mock_openai.return_value = mock_client
        
        generator = TranscriptGenerator(api_key="test-key")
        
        transcript = generator.generate(scenario="greeting")
        
        assert isinstance(transcript, Transcript)
        assert transcript.id is not None
        assert transcript.scenario == "greeting"
        assert len(transcript.messages) == 2
    
    @patch('openai.OpenAI')
    def test_generate_with_any_parameters(self, mock_openai):
        """Test generating transcript with any parameters."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Agent: Welcome\nUser: Thanks"
        mock_client.chat.completions.create.return_value = mock_response
        mock_client.responses = None  # Skip Responses API
        mock_openai.return_value = mock_client
        
        generator = TranscriptGenerator(api_key="test-key")
        
        transcript = generator.generate(
            custom_field="value",
            another_param=123,
            topic="support"
        )
        
        assert transcript.custom_field == "value"
        assert transcript.another_param == 123
        assert transcript.topic == "support"
    
    @patch('openai.OpenAI')
    def test_generate_batch(self, mock_openai):
        """Test generating multiple transcripts."""
        # Mock OpenAI response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "A: Hello\nB: Hi"
        mock_client.chat.completions.create.return_value = mock_response
        mock_client.responses = None  # Skip Responses API
        mock_openai.return_value = mock_client
        
        generator = TranscriptGenerator(api_key="test-key")
        
        transcripts = generator.generate_batch(3, topic="test")
        
        assert len(transcripts) == 3
        for transcript in transcripts:
            assert isinstance(transcript, Transcript)
            assert transcript.topic == "test"
    
    @patch('openai.OpenAI')
    def test_api_fallback_methods(self, mock_openai):
        """Test that generator tries multiple API methods."""
        mock_client = Mock()
        
        # First method fails
        mock_client.responses = None
        
        # Chat completions works
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test conversation"
        mock_client.chat.completions.create.return_value = mock_response
        
        mock_openai.return_value = mock_client
        
        generator = TranscriptGenerator(api_key="test-key")
        result = generator._call_openai("test prompt")
        
        assert result == "Test conversation"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('openai.OpenAI')  
    def test_error_handling(self, mock_openai):
        """Test error handling in generation."""
        mock_client = Mock()
        
        # Mock responses attribute as None to skip Responses API
        mock_client.responses = None
        
        # All methods fail
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_client.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        generator = TranscriptGenerator(api_key="test-key")
        
        with pytest.raises(Exception, match="All API methods failed"):
            generator.generate()