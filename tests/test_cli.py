"""Tests for the CLI layer - focused on CLI behavior, not business logic."""
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest
from typer.testing import CliRunner

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import app, parse_dynamic_params
from src.models.transcript import Transcript, Message


class TestDynamicParameterParsing:
    """Test the CLI-specific parameter parsing functionality."""
    
    def test_parse_simple_key_value(self):
        """Test parsing simple key=value pairs."""
        params = ["scenario=test", "customer_id=123"]
        result = parse_dynamic_params(params)
        # Note: JSON parser converts "123" to integer 123
        assert result == {"scenario": "test", "customer_id": 123}
    
    def test_parse_multiple_key_value(self):
        """Test parsing multiple key=value pairs."""
        params = ["scenario=test", "customer_id=123", "sentiment=happy"]
        result = parse_dynamic_params(params)
        assert result == {"scenario": "test", "customer_id": 123, "sentiment": "happy"}
    
    def test_parse_json_value(self):
        """Test parsing JSON values."""
        params = ["data=[1,2,3]", "flag=true", "number=42"]
        result = parse_dynamic_params(params)
        assert result == {"data": [1, 2, 3], "flag": True, "number": 42}
    
    def test_parse_quoted_multi_word_value(self):
        """Test parsing quoted multi-word values."""
        params = ['scenario="PMI Removal"', "customer_id=456"]
        result = parse_dynamic_params(params)
        assert result == {"scenario": "PMI Removal", "customer_id": 456}
    
    def test_parse_multi_word_unquoted(self):
        """Test parsing multi-word values without quotes."""
        params = ["scenario=PMI", "Removal", "customer_id=456"]
        result = parse_dynamic_params(params)
        assert result == {"scenario": "PMI Removal", "customer_id": 456}
    
    def test_parse_mixed_with_continuation(self):
        """Test parsing with mixed quoted and continuation scenarios.""" 
        params = ["scenario=valid", "continuation", "another=valid"]
        result = parse_dynamic_params(params)
        # The improved parser treats "continuation" as part of scenario value
        assert result == {"scenario": "valid continuation", "another": "valid"}
    
    def test_parse_empty_params(self):
        """Test parsing empty parameter list."""
        params = []
        result = parse_dynamic_params(params)
        assert result == {}


class TestCLI:
    """Test the CLI interface layer."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()
        
        # Mock environment variable
        self.env_patcher = patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
        self.env_patcher.start()
        
        # Create sample transcript for testing
        self.sample_transcript = Transcript(
            id="TEST_123",
            messages=[
                Message(speaker="Customer", text="Hello, I need help"),
                Message(speaker="Agent", text="How can I assist you?")
            ],
            customer_id="CUST_001",
            scenario="test_scenario"
        )
    
    def teardown_method(self):
        """Clean up after tests."""
        self.env_patcher.stop()
    
    @patch('cli.init_system')
    def test_help_command(self, mock_init):
        """Test the help command output."""
        result = self.runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Customer Call Center Analytics CLI" in result.stdout
        assert "generate" in result.stdout
        assert "list" in result.stdout
        assert "delete" in result.stdout
    
    @patch('cli.init_system')
    def test_generate_command_basic(self, mock_init):
        """Test basic generate command."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_generator.generate.return_value = self.sample_transcript
        
        result = self.runner.invoke(app, [
            "generate", 
            "scenario=test_scenario",
            "customer_id=CUST_001"
        ])
        
        assert result.exit_code == 0
        assert "Generated transcript:" in result.stdout
        assert "TEST_123" in result.stdout
        # Verify business logic was called with parsed parameters
        mock_generator.generate.assert_called_once_with(
            scenario="test_scenario", 
            customer_id="CUST_001"
        )
    
    @patch('cli.init_system')
    def test_generate_command_with_store(self, mock_init):
        """Test generate command with store flag."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_generator.generate.return_value = self.sample_transcript
        
        result = self.runner.invoke(app, [
            "generate", 
            "scenario=test",
            "--store"
        ])
        
        assert result.exit_code == 0
        assert "Stored in database" in result.stdout
        # Verify business logic was called
        mock_store.store.assert_called_once_with(self.sample_transcript)
    
    @patch('cli.init_system')
    def test_generate_command_with_show(self, mock_init):
        """Test generate command with show flag."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_generator.generate.return_value = self.sample_transcript
        
        result = self.runner.invoke(app, [
            "generate", 
            "scenario=test",
            "--show"
        ])
        
        assert result.exit_code == 0
        assert "Transcript ID: TEST_123" in result.stdout
        assert "Customer: Hello, I need help" in result.stdout
    
    @patch('cli.init_system')
    def test_generate_multi_word_scenario(self, mock_init):
        """Test generate command with multi-word scenario."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_generator.generate.return_value = self.sample_transcript
        
        result = self.runner.invoke(app, [
            "generate", 
            "scenario=PMI", "Removal",
            "customer_id=CUST_123"
        ])
        
        assert result.exit_code == 0
        # Verify the multi-word parsing worked
        mock_generator.generate.assert_called_once_with(
            scenario="PMI Removal", 
            customer_id="CUST_123"
        )
    
    @patch('cli.init_system')
    def test_generate_batch(self, mock_init):
        """Test generate command with count parameter."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_generator.generate.return_value = self.sample_transcript
        
        result = self.runner.invoke(app, [
            "generate", 
            "scenario=test",
            "--count", "3"
        ])
        
        assert result.exit_code == 0
        assert "Generated 3 transcripts" in result.stdout
        assert mock_generator.generate.call_count == 3
    
    @patch('cli.init_system')
    def test_list_command_empty(self, mock_init):
        """Test list command with empty database."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_all.return_value = []
        
        result = self.runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        assert "No transcripts found" in result.stdout
    
    @patch('cli.init_system')
    def test_list_command_with_data(self, mock_init):
        """Test list command with transcripts."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_all.return_value = [self.sample_transcript]
        
        result = self.runner.invoke(app, ["list"])
        
        assert result.exit_code == 0
        assert "Found 1 transcript(s)" in result.stdout
        assert "TEST_123" in result.stdout
    
    @patch('cli.init_system')
    def test_list_command_detailed(self, mock_init):
        """Test list command with detailed flag."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_all.return_value = [self.sample_transcript]
        
        result = self.runner.invoke(app, ["list", "--detailed"])
        
        assert result.exit_code == 0
        assert "Transcript ID: TEST_123" in result.stdout
        assert "Customer: Hello, I need help" in result.stdout
    
    @patch('cli.init_system')
    def test_get_command_existing(self, mock_init):
        """Test get command with existing transcript."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_by_id.return_value = self.sample_transcript
        
        result = self.runner.invoke(app, ["get", "TEST_123"])
        
        assert result.exit_code == 0
        assert "Transcript ID: TEST_123" in result.stdout
        mock_store.get_by_id.assert_called_once_with("TEST_123")
    
    @patch('cli.init_system')
    def test_get_command_nonexistent(self, mock_init):
        """Test get command with nonexistent transcript."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_by_id.return_value = None
        
        result = self.runner.invoke(app, ["get", "MISSING_123"])
        
        assert result.exit_code == 0
        assert "not found" in result.stdout
    
    @patch('cli.init_system')
    def test_get_command_with_export(self, mock_init):
        """Test get command with export flag."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_by_id.return_value = self.sample_transcript
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            result = self.runner.invoke(app, ["get", "TEST_123", "--export"])
            
            assert result.exit_code == 0
            assert "Exported to TEST_123.json" in result.stdout
            assert os.path.exists("TEST_123.json")
    
    @patch('cli.init_system')
    def test_search_command_by_customer(self, mock_init):
        """Test search command by customer ID."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.search_by_customer.return_value = [self.sample_transcript]
        
        result = self.runner.invoke(app, ["search", "--customer", "CUST_001"])
        
        assert result.exit_code == 0
        assert "Searching for customer: CUST_001" in result.stdout
        assert "Found 1 transcript(s)" in result.stdout
        mock_store.search_by_customer.assert_called_once_with("CUST_001")
    
    @patch('cli.init_system')
    def test_search_command_by_topic(self, mock_init):
        """Test search command by topic."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.search_by_topic.return_value = [self.sample_transcript]
        
        result = self.runner.invoke(app, ["search", "--topic", "test_topic"])
        
        assert result.exit_code == 0
        assert "Searching for topic: test_topic" in result.stdout
        mock_store.search_by_topic.assert_called_once_with("test_topic")
    
    @patch('cli.init_system')
    def test_search_command_by_text(self, mock_init):
        """Test search command by text content."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.search_by_text.return_value = [self.sample_transcript]
        
        result = self.runner.invoke(app, ["search", "--text", "help"])
        
        assert result.exit_code == 0
        assert "Searching for text: help" in result.stdout
        mock_store.search_by_text.assert_called_once_with("help")
    
    @patch('cli.init_system')
    def test_search_command_no_criteria(self, mock_init):
        """Test search command without criteria."""
        result = self.runner.invoke(app, ["search"])
        
        assert result.exit_code == 1
        assert "Please specify --customer, --topic, or --text" in result.stdout
    
    @patch('cli.init_system')
    def test_delete_command_with_confirmation_yes(self, mock_init):
        """Test delete command with confirmation (yes)."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_by_id.return_value = self.sample_transcript
        mock_store.delete.return_value = "TEST_123"
        
        result = self.runner.invoke(app, ["delete", "TEST_123"], input="y\n")
        
        assert result.exit_code == 0
        assert "Deleted transcript TEST_123" in result.stdout
        mock_store.delete.assert_called_once_with("TEST_123")
    
    @patch('cli.init_system')
    def test_delete_command_with_confirmation_no(self, mock_init):
        """Test delete command with confirmation (no)."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_by_id.return_value = self.sample_transcript
        
        result = self.runner.invoke(app, ["delete", "TEST_123"], input="n\n")
        
        assert result.exit_code == 0
        assert "Delete cancelled" in result.stdout
        mock_store.delete.assert_not_called()
    
    @patch('cli.init_system')
    def test_delete_command_with_force(self, mock_init):
        """Test delete command with force flag."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_by_id.return_value = self.sample_transcript
        mock_store.delete.return_value = "TEST_123"
        
        result = self.runner.invoke(app, ["delete", "TEST_123", "--force"])
        
        assert result.exit_code == 0
        assert "Deleted transcript TEST_123" in result.stdout
        mock_store.delete.assert_called_once_with("TEST_123")
    
    @patch('cli.init_system')
    def test_delete_command_nonexistent(self, mock_init):
        """Test delete command with nonexistent transcript."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_by_id.return_value = None
        
        result = self.runner.invoke(app, ["delete", "MISSING_123"])
        
        assert result.exit_code == 0
        assert "not found" in result.stdout
    
    @patch('cli.init_system')
    def test_stats_command_empty(self, mock_init):
        """Test stats command with empty database."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_all.return_value = []
        
        result = self.runner.invoke(app, ["stats"])
        
        assert result.exit_code == 0
        assert "No transcripts in database" in result.stdout
    
    @patch('cli.init_system')
    def test_stats_command_with_data(self, mock_init):
        """Test stats command with data."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_all.return_value = [self.sample_transcript]
        
        result = self.runner.invoke(app, ["stats"])
        
        assert result.exit_code == 0
        assert "Total Transcripts" in result.stdout
        assert "Total Messages" in result.stdout
    
    @patch('cli.init_system')
    def test_export_command_empty(self, mock_init):
        """Test export command with empty database."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_all.return_value = []
        
        result = self.runner.invoke(app, ["export"])
        
        assert result.exit_code == 0
        assert "No transcripts to export" in result.stdout
    
    @patch('cli.init_system')
    def test_export_command_default_filename(self, mock_init):
        """Test export command with default filename."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_all.return_value = [self.sample_transcript]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            result = self.runner.invoke(app, ["export"])
            
            assert result.exit_code == 0
            assert "Exported 1 transcripts to transcripts_export.json" in result.stdout
            assert os.path.exists("transcripts_export.json")
    
    @patch('cli.init_system')
    def test_export_command_custom_filename(self, mock_init):
        """Test export command with custom filename."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_store.get_all.return_value = [self.sample_transcript]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            result = self.runner.invoke(app, ["export", "--output", "custom.json"])
            
            assert result.exit_code == 0
            assert "Exported 1 transcripts to custom.json" in result.stdout
            assert os.path.exists("custom.json")
    
    @patch('cli.init_system')
    def test_demo_command_with_store(self, mock_init):
        """Test demo command with store flag."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_generator.generate.return_value = self.sample_transcript
        
        result = self.runner.invoke(app, ["demo"])
        
        assert result.exit_code == 0
        assert "Demo completed!" in result.stdout
        assert mock_generator.generate.call_count == 3  # 3 demo scenarios
        assert mock_store.store.call_count == 3
    
    @patch('cli.init_system')
    def test_demo_command_no_store(self, mock_init):
        """Test demo command with no-store flag."""
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        mock_generator.generate.return_value = self.sample_transcript
        
        result = self.runner.invoke(app, ["demo", "--no-store"])
        
        assert result.exit_code == 0
        assert "Demo completed!" in result.stdout
        assert mock_generator.generate.call_count == 3
        mock_store.store.assert_not_called()
    
    def test_init_system_no_api_key(self):
        """Test init_system without API key."""
        with patch.dict(os.environ, {}, clear=True):
            from cli import init_system
            # typer.Exit raises click.exceptions.Exit, not SystemExit
            with pytest.raises(Exception):  # More general exception catching
                init_system()


class TestCLIIntegration:
    """Integration tests for the CLI interface."""
    
    @patch('cli.init_system')
    def test_full_workflow(self, mock_init):
        """Test a complete workflow: generate, list, get, delete."""
        runner = CliRunner()
        
        mock_generator = MagicMock()
        mock_store = MagicMock()
        mock_init.return_value = (mock_generator, mock_store)
        
        # Create a sample transcript
        sample_transcript = Transcript(
            id="WORKFLOW_123",
            messages=[
                Message(speaker="Customer", text="I need help"),
                Message(speaker="Agent", text="How can I help?")
            ],
            scenario="workflow_test"
        )
        
        mock_generator.generate.return_value = sample_transcript
        mock_store.get_by_id.return_value = sample_transcript
        mock_store.delete.return_value = "WORKFLOW_123"
        
        # Generate transcript
        result = runner.invoke(app, ["generate", "scenario=workflow_test", "--store"])
        assert result.exit_code == 0
        assert "Generated transcript: WORKFLOW_123" in result.stdout
        
        # Get transcript
        result = runner.invoke(app, ["get", "WORKFLOW_123"])
        assert result.exit_code == 0
        assert "Transcript ID: WORKFLOW_123" in result.stdout
        
        # Delete transcript with force
        result = runner.invoke(app, ["delete", "WORKFLOW_123", "--force"])
        assert result.exit_code == 0
        assert "Deleted transcript WORKFLOW_123" in result.stdout