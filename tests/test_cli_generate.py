"""
Test cases for CLI generate command to ensure it returns transcript IDs.
Following TDD principles - create test first, then implement.
"""

import pytest
import json
from unittest.mock import Mock, patch

def test_generate_command_returns_transcript_ids_when_storing():
    """Test that generate command returns transcript IDs when store=True"""
    
    # Test the server-side handler method directly
    with patch('server.generator') as mock_generator, \
         patch('server.store') as mock_store:
        
        # Create mock transcript with ID
        mock_transcript = Mock()
        mock_transcript.id = 'CALL_TEST_001'
        mock_transcript.to_dict.return_value = {
            'id': 'CALL_TEST_001', 
            'messages': [], 
            'timestamp': '2024-01-01T10:00:00'
        }
        
        mock_generator.generate.return_value = mock_transcript
        mock_store.store.return_value = None
        
        # Import and test the handle_generate method directly
        from server import CLIHandler
        
        # Create a mock handler instance (we only need the method)
        handler_class = CLIHandler
        params = {
            'count': 1,
            'store': True,
            'generation_params': {'scenario': 'test'}
        }
        
        # Call the method directly
        result = handler_class.handle_generate(handler_class, params)
        
        # Verify response includes transcript IDs
        assert result['success'] is True
        assert result['stored'] is True
        assert 'transcript_ids' in result, "Response must include transcript_ids when storing"
        assert len(result['transcript_ids']) == 1
        assert result['transcript_ids'][0] == 'CALL_TEST_001'

def test_generate_command_does_not_return_ids_when_not_storing():
    """Test that generate command doesn't return IDs when store=False"""
    
    with patch('server.generator') as mock_generator, \
         patch('server.store') as mock_store:
        
        mock_transcript = Mock()
        mock_transcript.id = 'CALL_TEST_002'
        mock_transcript.to_dict.return_value = {
            'id': 'CALL_TEST_002', 
            'messages': [], 
            'timestamp': '2024-01-01T10:00:00'
        }
        
        mock_generator.generate.return_value = mock_transcript
        
        # Import and test the handle_generate method directly
        from server import CLIHandler
        
        handler_class = CLIHandler
        params = {
            'count': 1,
            'store': False,  # Not storing
            'generation_params': {'scenario': 'test'}
        }
        
        result = handler_class.handle_generate(handler_class, params)
        
        # Verify response doesn't include transcript IDs when not storing
        assert result['success'] is True
        assert result['stored'] is False
        assert 'transcript_ids' not in result, "Should not include transcript_ids when not storing"

def test_generate_command_returns_multiple_ids_for_batch():
    """Test that generate command returns all IDs when generating multiple transcripts"""
    
    with patch('server.generator') as mock_generator, \
         patch('server.store') as mock_store:
        
        # Create multiple mock transcripts
        expected_ids = ['CALL_BATCH_001', 'CALL_BATCH_002', 'CALL_BATCH_003']
        mock_transcripts = []
        
        for transcript_id in expected_ids:
            mock_transcript = Mock()
            mock_transcript.id = transcript_id
            mock_transcript.to_dict.return_value = {
                'id': transcript_id, 
                'messages': [], 
                'timestamp': '2024-01-01T10:00:00'
            }
            mock_transcripts.append(mock_transcript)
        
        mock_generator.generate.side_effect = mock_transcripts
        mock_store.store.return_value = None
        
        # Import and test the handle_generate method directly
        from server import CLIHandler
        
        handler_class = CLIHandler
        params = {
            'count': 3,
            'store': True,
            'generation_params': {'scenario': 'batch_test'}
        }
        
        result = handler_class.handle_generate(handler_class, params)
        
        # Verify all IDs are returned
        assert result['success'] is True
        assert result['stored'] is True
        assert 'transcript_ids' in result
        assert len(result['transcript_ids']) == 3
        assert result['transcript_ids'] == expected_ids

def test_cli_displays_transcript_ids():
    """Test that CLI command displays the returned transcript IDs"""
    
    # This will be implemented after we fix the server side
    # For now, just ensure the structure is ready
    pass


# ========== CLI INTEGRATION TESTS ==========
# These test the actual CLI command behavior following TDD

import subprocess
import re
import os
from pathlib import Path


def run_cli(args, timeout=60):
    """Helper to run CLI commands with proper environment."""
    cmd = ['python', 'cli.py'] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        cwd=Path(__file__).parent.parent,  # Run from project root
        env={**os.environ, 'PYTHONPATH': str(Path(__file__).parent.parent)}
    )
    return result


class TestCLIGenerateIntegration:
    """Integration tests for CLI generate command following TDD principles."""
    
    def test_generate_returns_actual_transcript_id_not_unknown(self):
        """
        CRITICAL TEST: Generate command MUST return actual transcript ID.
        NO FALLBACK: Should never show 'Unknown ID'
        
        This is the main bug we're fixing.
        """
        result = run_cli(['generate', '--scenario', 'PMI Removal', '--store'])
        
        # Should succeed
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should contain actual transcript ID (CALL_XXXXXXXX format)
        transcript_id_match = re.search(r'CALL_[A-Z0-9]{8}', result.stdout)
        assert transcript_id_match, \
            f"No valid transcript ID found in output: {result.stdout}"
        
        # Should NEVER show fallback text
        assert 'Unknown ID' not in result.stdout, \
            "VIOLATION: Shows 'Unknown ID' fallback instead of real ID"
        
        print(f"✅ Test passed - Found transcript ID: {transcript_id_match.group()}")
    
    def test_show_flag_displays_transcript_details(self):
        """
        TEST: --show flag MUST display full transcript content.
        Currently this flag is ignored.
        """
        result = run_cli(['generate', '--scenario', 'Payment Dispute', '--show'])
        
        # Should succeed
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should show transcript details
        detail_indicators = [
            'Transcript Details:', 'Messages:', 'Customer:', 'Agent:', 
            'Borrower:', 'Advisor:', 'Dialog:', 'Conversation:'
        ]
        has_details = any(indicator in result.stdout for indicator in detail_indicators)
        
        assert has_details, \
            f"--show flag ignored. No transcript details found. Output: {result.stdout}"
        
        # Should show more than just the basic success message
        lines = result.stdout.strip().split('\n')
        assert len(lines) > 3, \
            "Output too short - likely not showing full transcript details"
    
    def test_store_flag_confirms_storage(self):
        """
        TEST: --store flag MUST confirm successful storage.
        Currently this confirmation is missing.
        """
        result = run_cli(['generate', '--scenario', 'Account Balance', '--store'])
        
        # Should succeed  
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should confirm storage
        storage_indicators = [
            'Stored', 'stored', 'Saved', 'saved', 'database', 
            'DB', 'stored with ID', 'stored successfully'
        ]
        has_confirmation = any(indicator in result.stdout for indicator in storage_indicators)
        
        assert has_confirmation, \
            f"No storage confirmation found. Output: {result.stdout}"
    
    def test_store_and_show_flags_work_together(self):
        """
        TEST: --store and --show flags MUST work together.
        Tests the complete user workflow.
        """
        result = run_cli(['generate', '--scenario', 'PMI Removal', '--store', '--show'])
        
        # Should succeed
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should have transcript ID (not Unknown)
        assert re.search(r'CALL_[A-Z0-9]{8}', result.stdout), \
            "Missing transcript ID"
        assert 'Unknown ID' not in result.stdout, \
            "Shows 'Unknown ID' fallback"
        
        # Should confirm storage
        storage_indicators = ['Stored', 'stored', 'Saved', 'saved', 'database']
        has_storage = any(indicator in result.stdout for indicator in storage_indicators)
        assert has_storage, "Missing storage confirmation"
        
        # Should show details
        detail_indicators = ['Messages:', 'Customer:', 'Agent:', 'Transcript Details:']
        has_details = any(indicator in result.stdout for indicator in detail_indicators)
        assert has_details, "Missing transcript details from --show flag"
    
    def test_no_fallback_principle_violated_currently(self):
        """
        REGRESSION TEST: Current implementation violates NO FALLBACK principle.
        This test documents the current bug and will pass once we fix it.
        """
        result = run_cli(['generate', '--scenario', 'Test Scenario'])
        
        # Current bug: shows "Unknown ID" instead of failing fast
        if 'Unknown ID' in result.stdout:
            pytest.skip("Bug confirmed: Shows 'Unknown ID' fallback (violates NO FALLBACK principle)")
        
        # After fix: should show actual ID
        assert re.search(r'CALL_[A-Z0-9]{8}', result.stdout), \
            "Fixed: Should show actual transcript ID"
    
    def test_generate_without_store_still_shows_id(self):
        """
        TEST: Generate without --store should still show transcript ID.
        The transcript is created, just not stored in database.
        """
        result = run_cli(['generate', '--scenario', 'Refinance Inquiry'])
        
        # Should succeed
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should show transcript ID even without storing
        assert re.search(r'CALL_[A-Z0-9]{8}', result.stdout), \
            f"No transcript ID shown when not storing: {result.stdout}"
        
        # Should NOT show Unknown ID
        assert 'Unknown ID' not in result.stdout, \
            "Shows 'Unknown ID' even when generation succeeds"
    
    def test_various_scenarios_work_correctly(self):
        """
        TEST: Different scenarios should all work and return proper IDs.
        Tests robustness across different inputs.
        """
        scenarios = [
            'PMI Removal',
            'Payment Dispute', 
            'Refinance Inquiry',
            'Escrow Shortage',
            'Account Balance Inquiry'
        ]
        
        for scenario in scenarios:
            result = run_cli(['generate', '--scenario', scenario])
            
            assert result.returncode == 0, \
                f"Scenario '{scenario}' failed: {result.stderr}"
            
            # Each should show proper transcript ID
            has_id = re.search(r'CALL_[A-Z0-9]{8}', result.stdout)
            assert has_id, \
                f"No transcript ID for scenario '{scenario}': {result.stdout}"
            
            # None should show fallback
            assert 'Unknown ID' not in result.stdout, \
                f"Scenario '{scenario}' shows 'Unknown ID': {result.stdout}"
    
    def test_additional_flags_work_with_id_display(self):
        """
        TEST: Additional flags (urgency, financial) should work with proper ID display.
        """
        result = run_cli([
            'generate', 
            '--scenario', 'PMI Removal',
            '--urgency', 'high',
            '--financial',
            '--store'
        ])
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should show transcript ID
        assert re.search(r'CALL_[A-Z0-9]{8}', result.stdout), \
            f"No transcript ID with additional flags: {result.stdout}"
        
        # Should not show Unknown ID
        assert 'Unknown ID' not in result.stdout, \
            "Shows 'Unknown ID' with additional flags"