"""Tests for server handlers - Critical test coverage gap.

Following TDD principles:
1. Test each handler method individually
2. Mock dependencies (stores, generators, agents)  
3. Test error conditions and edge cases
4. Ensure proper integration points

Addresses GitHub Issue #2.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from server import CLIHandler


class TestServerHandlers:
    """Test all server handlers that currently lack test coverage."""
    
    def test_handle_analyze_success(self):
        """Test handle_analyze with successful analysis."""
        params = {'transcript_id': 'CALL_TEST_001'}
        
        # Mock dependencies
        with patch('server.TranscriptStore') as mock_transcript_store_class, \
             patch('src.analyzers.call_analyzer.CallAnalyzer') as mock_analyzer_class, \
             patch('src.storage.analysis_store.AnalysisStore') as mock_analysis_store_class:
            
            # Setup mock transcript store
            mock_transcript_store = MagicMock()
            mock_transcript_store_class.return_value = mock_transcript_store
            mock_transcript_store.get_by_id.return_value = Mock(id='CALL_TEST_001')
            
            # Setup mock analyzer
            mock_analyzer = MagicMock()
            mock_analyzer_class.return_value = mock_analyzer
            mock_analyzer.analyze.return_value = {'analysis_id': 'analysis_001', 'sentiment': 'positive'}
            
            # Setup mock analysis store
            mock_analysis_store = MagicMock()
            mock_analysis_store_class.return_value = mock_analysis_store
            
            # Execute - call method on class with mock self
            mock_self = MagicMock()
            result = CLIHandler.handle_analyze(mock_self, params)
            
            # Verify
            assert result['success'] is True
            assert result['count'] == 1
            assert 'Analyzed 1 transcript(s)' in result['message']
            mock_transcript_store.get_by_id.assert_called_once_with('CALL_TEST_001')
            mock_analyzer.analyze.assert_called_once()
            mock_analysis_store.store.assert_called_once()

    def test_handle_analyze_transcript_not_found(self):
        """Test handle_analyze when transcript not found."""
        params = {'transcript_id': 'NONEXISTENT'}
        
        with patch('server.TranscriptStore') as mock_store_class:
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            mock_store.get_by_id.return_value = None
            
            mock_self = MagicMock()
            result = CLIHandler.handle_analyze(mock_self, params)
            
            assert result['success'] is False
            assert 'not found' in result['error']

    def test_handle_analyze_missing_transcript_id(self):
        """Test handle_analyze with missing transcript_id parameter."""
        params = {}
        
        mock_self = MagicMock()
        result = CLIHandler.handle_analyze(mock_self, params)
        
        assert result['success'] is False
        assert 'Must specify either --transcript-id or --all' in result['error']

    def test_handle_list_success(self):
        """Test handle_list returns all transcripts."""
        with patch('server.TranscriptStore') as mock_store_class:
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            
            mock_transcripts = [
                Mock(to_dict=lambda: {'id': 'CALL_001', 'topic': 'PMI'}),
                Mock(to_dict=lambda: {'id': 'CALL_002', 'topic': 'Payment'})
            ]
            mock_store.get_all.return_value = mock_transcripts
            
            mock_self = MagicMock()
            result = CLIHandler.handle_list(mock_self, {})
            
            assert result['success'] is True
            assert len(result['transcripts']) == 2
            assert result['transcripts'][0]['id'] == 'CALL_001'
            mock_store.get_all.assert_called_once()

    def test_handle_get_success(self):
        """Test handle_get retrieves specific transcript."""
        params = {'transcript_id': 'CALL_TEST_001'}
        
        with patch('server.TranscriptStore') as mock_store_class:
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            
            mock_transcript = Mock()
            mock_transcript.to_dict.return_value = {'id': 'CALL_TEST_001', 'topic': 'Test'}
            mock_store.get_by_id.return_value = mock_transcript
            
            mock_self = MagicMock()
            result = CLIHandler.handle_get(mock_self, params)
            
            assert result['success'] is True
            assert result['transcript']['id'] == 'CALL_TEST_001'
            mock_store.get_by_id.assert_called_once_with('CALL_TEST_001')

    def test_handle_get_not_found(self):
        """Test handle_get when transcript not found."""
        params = {'transcript_id': 'NONEXISTENT'}
        
        with patch('server.TranscriptStore') as mock_store_class:
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            mock_store.get_by_id.return_value = None
            
            mock_self = MagicMock()
            result = CLIHandler.handle_get(mock_self, params)
            
            assert result['success'] is False
            assert 'not found' in result['error']

    def test_handle_delete_success(self):
        """Test handle_delete removes transcript successfully."""
        params = {'transcript_id': 'CALL_TEST_001'}
        
        with patch('server.TranscriptStore') as mock_store_class:
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            mock_store.delete.return_value = True
            
            mock_self = MagicMock()
            result = CLIHandler.handle_delete(mock_self, params)
            
            assert result['success'] is True
            assert 'Deleted transcript CALL_TEST_001' in result['message']
            mock_store.delete.assert_called_once_with('CALL_TEST_001')

    def test_handle_delete_not_found(self):
        """Test handle_delete when transcript not found."""
        params = {'transcript_id': 'NONEXISTENT'}
        
        with patch('server.TranscriptStore') as mock_store_class:
            mock_store = MagicMock()
            mock_store_class.return_value = mock_store
            mock_store.delete.return_value = False
            
            mock_self = MagicMock()
            result = CLIHandler.handle_delete(mock_self, params)
            
            assert result['success'] is False
            assert 'not found' in result['error']

    def test_handle_generate_action_plan_success(self):
        """Test handle_generate_action_plan with successful generation."""
        params = {'transcript_id': 'CALL_TEST_001'}
        
        with patch('server.TranscriptStore') as mock_transcript_store_class, \
             patch('src.storage.analysis_store.AnalysisStore') as mock_analysis_store_class, \
             patch('src.generators.action_plan_generator.ActionPlanGenerator') as mock_generator_class, \
             patch('src.storage.action_plan_store.ActionPlanStore') as mock_plan_store_class:
            
            # Setup mocks
            mock_transcript_store = MagicMock()
            mock_transcript_store_class.return_value = mock_transcript_store
            mock_transcript_store.get_by_id.return_value = Mock(id='CALL_TEST_001')
            
            mock_analysis_store = MagicMock()
            mock_analysis_store_class.return_value = mock_analysis_store
            mock_analysis_store.get_by_transcript_id.return_value = {'analysis_id': 'analysis_001'}
            
            mock_generator = MagicMock()
            mock_generator_class.return_value = mock_generator
            mock_generator.generate.return_value = {
                'plan_id': 'plan_001',
                'risk_level': 'medium',
                'approval_route': 'supervisor_approval'
            }
            
            mock_plan_store = MagicMock()
            mock_plan_store_class.return_value = mock_plan_store
            mock_plan_store.store.return_value = 'plan_001'
            
            # Execute
            mock_self = MagicMock()
            result = CLIHandler.handle_generate_action_plan(mock_self, params)
            
            # Verify
            assert result['success'] is True
            assert result['plan_id'] == 'plan_001'
            assert 'Generated action plan' in result['message']
            mock_generator.generate.assert_called_once()
            mock_plan_store.store.assert_called_once()

    def test_handle_generate_action_plan_no_analysis(self):
        """Test handle_generate_action_plan when analysis not found."""
        params = {'transcript_id': 'CALL_TEST_001'}
        
        with patch('server.TranscriptStore') as mock_transcript_store_class, \
             patch('src.storage.analysis_store.AnalysisStore') as mock_analysis_store_class:
            
            mock_transcript_store = MagicMock()
            mock_transcript_store_class.return_value = mock_transcript_store
            mock_transcript_store.get_by_id.return_value = Mock(id='CALL_TEST_001')
            
            mock_analysis_store = MagicMock()
            mock_analysis_store_class.return_value = mock_analysis_store
            mock_analysis_store.get_by_transcript_id.return_value = None
            
            mock_self = MagicMock()
            result = CLIHandler.handle_generate_action_plan(mock_self, params)
            
            assert result['success'] is False
            assert 'Analysis for transcript' in result['error']
            assert 'Run analyze first' in result['error']

    def test_error_handling_in_handlers(self):
        """Test that handlers properly catch and return exceptions."""
        params = {'transcript_id': 'CALL_TEST_001'}
        
        # Test that exceptions are caught and returned as error responses
        with patch('server.TranscriptStore') as mock_store_class:
            mock_store_class.side_effect = Exception("Database connection failed")
            
            mock_self = MagicMock()
            result = CLIHandler.handle_get(mock_self, params)
            
            assert result['success'] is False
            assert 'Database connection failed' in result['error']