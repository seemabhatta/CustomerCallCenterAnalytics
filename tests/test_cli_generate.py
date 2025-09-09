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