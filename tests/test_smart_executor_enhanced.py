"""Tests for enhanced SmartExecutor - Approval-aware execution with NO FALLBACK."""

import pytest
import tempfile
import os
import unittest.mock
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.executors.smart_executor import SmartExecutor
from src.storage.action_plan_store import ActionPlanStore


class TestSmartExecutorEnhanced:
    """Test cases for enhanced SmartExecutor with approval checking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock tools for testing
        self.mock_tools = MagicMock()
        
        # Sample action plan with per-action approval data
        self.sample_plan = {
            'plan_id': 'PLAN_ENHANCED_001',
            'transcript_id': 'CALL_ENHANCED_001',
            'analysis_id': 'ANALYSIS_ENHANCED_001',
            'risk_level': 'medium',
            'approval_route': 'advisor_approval',
            'queue_status': 'approved',
            'auto_executable': False,
            'borrower_plan': {
                'immediate_actions': [
                    {
                        'action': 'Send confirmation email',
                        'description': 'Standard confirmation',
                        'needs_approval': False,
                        'approval_status': 'auto_approved',
                        'risk_level': 'low',
                        'auto_executable': True
                    },
                    {
                        'action': 'Process payment refund',
                        'description': 'Refund $150 to customer',
                        'needs_approval': True,
                        'approval_status': 'approved',
                        'risk_level': 'high',
                        'auto_executable': True
                    },
                    {
                        'action': 'Escalate to supervisor',
                        'description': 'Complex case escalation',
                        'needs_approval': True,
                        'approval_status': 'pending',
                        'risk_level': 'high',
                        'auto_executable': False
                    }
                ],
                'follow_ups': [
                    {
                        'action': 'Schedule follow-up call',
                        'description': 'Customer satisfaction check',
                        'needs_approval': False,
                        'approval_status': 'auto_approved',
                        'risk_level': 'low',
                        'auto_executable': True
                    }
                ]
            },
            'advisor_plan': {
                'coaching_items': [
                    {
                        'action': 'Review compliance procedures',
                        'description': 'Training on new regulations',
                        'needs_approval': True,
                        'approval_status': 'pending',
                        'risk_level': 'medium',
                        'auto_executable': False
                    }
                ]
            },
            'supervisor_plan': {
                'escalation_items': [
                    {
                        'action': 'Review escalated case',
                        'description': 'Supervisor review required',
                        'needs_approval': False,
                        'approval_status': 'auto_approved',
                        'risk_level': 'low',
                        'auto_executable': True
                    }
                ]
            },
            'leadership_plan': {
                'portfolio_insights': 'Customer satisfaction metrics improving',
                'needs_approval': False,
                'approval_status': 'auto_approved',
                'risk_level': 'low'
            }
        }
    
    def teardown_method(self):
        """Clean up temporary database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_executor_initialization(self):
        """Test SmartExecutor initialization with database path."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            
            assert executor.tools is not None
            assert executor.action_plan_store is not None
            assert executor.analysis_store is not None
            assert executor.transcript_store is not None
            assert executor.client is not None
    
    def test_no_fallback_behavior(self):
        """Test that executor raises exceptions instead of using fallback."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            # Mock OpenAI client to raise exception
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                mock_client.responses.create.side_effect = Exception("OpenAI API Error")
                
                executor.client = mock_client
                
                # Test that LLM failure raises exception (NO FALLBACK)
                with pytest.raises(RuntimeError, match="LLM execution decision failed.*NO FALLBACK"):
                    executor._llm_decide_execution({'action': 'test'}, {}, 'test')
    
    def test_approval_aware_borrower_execution(self):
        """Test borrower actions execution with approval checking."""
        # Store the action plan
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            # Mock successful tool executions
            self.mock_tools.send_email.return_value = {'status': 'success', 'artifact_path': 'email.txt'}
            self.mock_tools.generate_document.return_value = {'status': 'success', 'file_path': 'doc.txt'}
            self.mock_tools.schedule_callback.return_value = {'status': 'success', 'callback_id': 'CB001'}
            
            with patch('openai.OpenAI') as mock_openai:
                # Mock LLM decisions
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Test email content',
                    'tone': 'friendly',
                    'timing': 'immediate',
                    'parameters': {'recipient': 'test@example.com', 'subject': 'Test'}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                
                executor.client = mock_client
                
                # Execute borrower actions
                context = {'customer_id': 'TEST_CUSTOMER', 'plan_id': 'PLAN_ENHANCED_001'}
                results = executor._execute_borrower_actions(self.sample_plan['borrower_plan'], context)
                
                # Test approval-aware execution behavior
                executed_count = sum(1 for r in results if r.get('status') != 'skipped')
                skipped_count = sum(1 for r in results if r.get('status') == 'skipped')
                
                # The key test: at least one action should be skipped due to pending approval
                assert skipped_count >= 1  # At least one should be skipped due to pending status
                
                # Check that skipped action has correct reason
                skipped_actions = [r for r in results if r.get('status') == 'skipped']
                assert len(skipped_actions) >= 1
                pending_skip = next((a for a in skipped_actions if a.get('approval_status') == 'pending'), None)
                assert pending_skip is not None
                assert 'Awaiting approval' in pending_skip['reason']
    
    def test_approval_aware_advisor_execution(self):
        """Test advisor actions execution with approval checking."""
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            self.mock_tools.generate_document.return_value = {'status': 'success', 'file_path': 'coaching.txt'}
            
            context = {'advisor_id': 'TEST_ADVISOR', 'plan_id': 'PLAN_ENHANCED_001'}
            results = executor._execute_advisor_actions(self.sample_plan['advisor_plan'], context)
            
            # Should skip the coaching item due to pending approval
            assert len(results) == 1
            assert results[0]['status'] == 'skipped'
            assert results[0]['reason'] == 'Awaiting approval'
    
    def test_approval_aware_supervisor_execution(self):
        """Test supervisor actions execution with approval checking.""" 
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            self.mock_tools.send_notification.return_value = {'status': 'success', 'notification_id': 'NOT001'}
            
            context = {'plan_id': 'PLAN_ENHANCED_001'}
            results = executor._execute_supervisor_actions(self.sample_plan['supervisor_plan'], context)
            
            # Should execute the auto-approved action
            assert len(results) == 1
            assert results[0]['status'] == 'success'
            assert 'escalation_details' in results[0]
    
    def test_approval_aware_leadership_execution(self):
        """Test leadership actions execution with approval checking."""
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            self.mock_tools.generate_document.return_value = {'status': 'success', 'file_path': 'insights.txt'}
            
            context = {'plan_id': 'PLAN_ENHANCED_001'}
            results = executor._execute_leadership_actions(self.sample_plan['leadership_plan'], context)
            
            # Should execute since auto-approved
            assert len(results) == 1
            assert results[0]['status'] == 'success'
            assert results[0]['action_source'] == 'leadership_insights'
    
    def test_full_plan_execution_with_approval_checking(self):
        """Test complete plan execution with approval-aware logic."""
        # Store the action plan
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            # Mock tool responses
            self.mock_tools.send_email.return_value = {'status': 'success', 'artifact_path': 'email.txt'}
            self.mock_tools.generate_document.return_value = {'status': 'success', 'file_path': 'doc.txt'}
            self.mock_tools.schedule_callback.return_value = {'status': 'success', 'callback_id': 'CB001'}
            self.mock_tools.send_notification.return_value = {'status': 'success', 'notification_id': 'NOT001'}
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Test content',
                    'tone': 'friendly',
                    'timing': 'immediate',
                    'parameters': {'recipient': 'test@example.com'}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                
                executor.client = mock_client
                
                # Execute the plan
                result = executor.execute_action_plan('PLAN_ENHANCED_001')
                
                assert result['status'] == 'success'
                assert 'execution_id' in result
                assert 'artifacts_created' in result
                
                # Check that some actions were executed and some were skipped
                all_results = (
                    result['results']['borrower_actions'] +
                    result['results']['advisor_actions'] +
                    result['results']['supervisor_actions'] +
                    result['results']['leadership_actions']
                )
                
                executed_actions = [r for r in all_results if r.get('status') != 'skipped']
                skipped_actions = [r for r in all_results if r.get('status') == 'skipped']
                
                assert len(executed_actions) > 0  # Some actions executed
                assert len(skipped_actions) > 0   # Some actions skipped
    
    def test_enhanced_execution_summary(self):
        """Test enhanced execution summary with approval metrics."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            # Mock tools to return sample action data
            sample_actions = [
                {'status': 'success'},
                {'status': 'skipped', 'reason': 'Awaiting approval'},
                {'status': 'success'},
                {'status': 'skipped', 'reason': 'Awaiting approval'}
            ]
            
            self.mock_tools.get_recent_actions.return_value = sample_actions
            self.mock_tools.get_execution_summary.return_value = {
                'total_executions': 1,
                'success_rate': 50.0,
                'total_artifacts_created': 2
            }
            
            summary = executor.get_execution_summary()
            
            # Should include enhanced approval metrics
            assert 'actions_skipped_for_approval' in summary
            assert 'actions_awaiting_approval' in summary
            assert 'approval_skip_rate' in summary
            
            assert summary['actions_skipped_for_approval'] == 2
            assert summary['actions_awaiting_approval'] == 2
            assert summary['approval_skip_rate'] == 50.0  # 2/4 * 100
    
    def test_plan_not_found_error(self):
        """Test execution with non-existent plan ID."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            
            result = executor.execute_action_plan('NONEXISTENT_PLAN')
            
            assert result['status'] == 'error'
            assert 'not found' in result['message']
    
    def test_plan_approval_status_checking(self):
        """Test plan-level approval status checking."""
        # Create plan that needs supervisor approval but isn't approved
        pending_plan = {
            **self.sample_plan,
            'plan_id': 'PLAN_PENDING_001',
            'queue_status': 'pending_supervisor',
            'risk_level': 'high'
        }
        
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(pending_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            
            # Should reject execution due to pending approval
            result = executor.execute_action_plan('PLAN_PENDING_001')
            
            assert result['status'] == 'pending_approval'
            assert 'requires approval' in result['message']
            assert result['risk_level'] == 'high'
    
    def test_manual_execution_mode(self):
        """Test manual execution mode can override approval requirements."""
        # Create plan that needs approval
        pending_plan = {
            **self.sample_plan,
            'plan_id': 'PLAN_MANUAL_001',
            'queue_status': 'pending_supervisor'
        }
        
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(pending_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            # Mock minimal successful execution
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Test',
                    'tone': 'friendly',
                    'timing': 'immediate',
                    'parameters': {}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                
                executor.client = mock_client
                
                # Manual mode should allow execution
                result = executor.execute_action_plan('PLAN_MANUAL_001', mode='manual')
                
                # Should execute despite pending approval
                assert result['status'] == 'success'
    
    def test_context_extraction_with_approval_data(self):
        """Test execution context extraction includes approval-related data."""
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            
            context = executor._get_execution_context(self.sample_plan)
            
            assert 'plan_id' in context
            assert 'risk_level' in context
            assert 'approval_route' in context
            assert context['risk_level'] == self.sample_plan['risk_level']
            assert context['approval_route'] == self.sample_plan['approval_route']
    
    def test_error_handling_in_approval_checking(self):
        """Test error handling during approval checking doesn't break execution."""
        # Create malformed action (missing approval fields)
        malformed_plan = {
            'plan_id': 'PLAN_MALFORMED_001',
            'analysis_id': 'ANALYSIS_MALFORMED_001',  # Required field
            'transcript_id': 'CALL_MALFORMED_001',   # Required field
            'risk_level': 'low',
            'queue_status': 'approved',
            'borrower_plan': {
                'immediate_actions': [
                    {
                        'action': 'Test action',
                        # Missing approval fields intentionally
                    }
                ]
            }
        }
        
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(malformed_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'document',
                    'content': 'Test content',
                    'tone': 'formal',
                    'timing': 'immediate',
                    'parameters': {}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                
                executor.client = mock_client
                
                # Should handle gracefully
                result = executor.execute_action_plan('PLAN_MALFORMED_001')
                
                # Should still execute (graceful degradation for missing fields)
                assert result['status'] == 'success'


class TestSmartExecutorApprovalStoreIntegration:
    """Test cases for SmartExecutor integration with ApprovalStore."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock tools for testing
        self.mock_tools = MagicMock()
        
        # Sample action plan generated by ActionPlanGenerator with DecisionAgent
        self.sample_plan_with_approvals = {
            'plan_id': 'PLAN_APPROVAL_001',
            'transcript_id': 'CALL_APPROVAL_001',
            'analysis_id': 'ANALYSIS_APPROVAL_001',
            'decision_agent_processed': True,
            'routing_decision': 'supervisor_approval',
            'risk_level': 'high',
            'queue_status': 'approved',
            'borrower_plan': {
                'immediate_actions': [
                    {
                        'action_id': 'ACT_001',
                        'action': 'Send payment confirmation',
                        'description': 'Confirm payment processing',
                        'needs_approval': False,
                        'approval_status': 'auto_approved',
                        'risk_level': 'low',
                        'risk_score': 0.25
                    },
                    {
                        'action_id': 'ACT_002',
                        'action': 'Process refund request',
                        'description': 'Refund $500 payment error',
                        'needs_approval': True,
                        'approval_status': 'supervisor_approval',
                        'risk_level': 'high',
                        'risk_score': 0.85
                    }
                ]
            },
            'advisor_plan': {
                'coaching_items': [
                    {
                        'action_id': 'ACT_003',
                        'action': 'Review empathy training',
                        'description': 'Customer expressed frustration',
                        'needs_approval': True,
                        'approval_status': 'advisor_approval',
                        'risk_level': 'medium',
                        'risk_score': 0.55
                    }
                ]
            }
        }
    
    def teardown_method(self):
        """Clean up temporary database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    @pytest.fixture
    def mock_approval_store(self):
        """Mock ApprovalStore for testing."""
        with patch('src.storage.approval_store.ApprovalStore') as mock:
            store = MagicMock()
            mock.return_value = store
            yield store
    
    def test_executor_checks_approval_store_before_execution(self, mock_approval_store):
        """Test that SmartExecutor queries ApprovalStore before executing actions."""
        # Setup approval records in store
        mock_approval_store.get_approval_by_action_id.side_effect = lambda action_id: {
            'ACT_001': {
                'action_id': 'ACT_001', 
                'approval_status': 'approved', 
                'approved_at': '2024-01-15T10:00:00Z',
                'approver_id': 'AUTO_SYSTEM'
            },
            'ACT_002': {
                'action_id': 'ACT_002', 
                'approval_status': 'pending_supervisor', 
                'submitted_at': '2024-01-15T09:30:00Z'
            },
            'ACT_003': {
                'action_id': 'ACT_003', 
                'approval_status': 'approved', 
                'approved_at': '2024-01-15T09:45:00Z',
                'approver_id': 'ADVISOR_001'
            }
        }.get(action_id)
        
        # Store the action plan
        from src.storage.action_plan_store import ActionPlanStore
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan_with_approvals)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            executor.approval_store = mock_approval_store  # Inject mock
            
            # Mock LLM and tool responses
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Test content',
                    'tone': 'friendly',
                    'timing': 'immediate',
                    'parameters': {'recipient': 'test@example.com'}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                executor.client = mock_client
                
                # Mock tool responses
                self.mock_tools.send_email.return_value = {'status': 'success'}
                self.mock_tools.generate_document.return_value = {'status': 'success'}
                
                # Execute borrower actions
                context = {'customer_id': 'CUST_001', 'plan_id': 'PLAN_APPROVAL_001'}
                results = executor._execute_borrower_actions(
                    self.sample_plan_with_approvals['borrower_plan'], context
                )
                
                # Verify ApprovalStore was queried for each action
                expected_calls = [
                    unittest.mock.call('ACT_001'),
                    unittest.mock.call('ACT_002')
                ]
                mock_approval_store.get_approval_by_action_id.assert_has_calls(expected_calls, any_order=True)
                
                # Should execute ACT_001 (approved) but skip ACT_002 (pending)
                executed_actions = [r for r in results if r.get('status') != 'skipped']
                skipped_actions = [r for r in results if r.get('status') == 'skipped']
                
                assert len(executed_actions) == 1  # ACT_001 should execute
                assert len(skipped_actions) == 1   # ACT_002 should be skipped
                
                # Verify the skipped action has correct details
                skipped = skipped_actions[0]
                assert skipped['reason'] == 'Awaiting approval'
                assert skipped['original_action']['action_id'] == 'ACT_002'
    
    def test_executor_execution_without_approval_store(self):
        """Test executor falls back to action plan approval status when ApprovalStore unavailable."""
        # Store the action plan
        from src.storage.action_plan_store import ActionPlanStore
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan_with_approvals)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            # Don't inject approval_store - it should be None
            
            # Mock LLM and tool responses
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Test content',
                    'tone': 'friendly',
                    'timing': 'immediate',
                    'parameters': {'recipient': 'test@example.com'}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                executor.client = mock_client
                
                self.mock_tools.send_email.return_value = {'status': 'success'}
                
                # Execute borrower actions - should use action plan approval status
                context = {'customer_id': 'CUST_001', 'plan_id': 'PLAN_APPROVAL_001'}
                results = executor._execute_borrower_actions(
                    self.sample_plan_with_approvals['borrower_plan'], context
                )
                
                # Should execute ACT_001 (auto_approved) but skip ACT_002 (supervisor_approval != approved)
                executed_actions = [r for r in results if r.get('status') != 'skipped']
                skipped_actions = [r for r in results if r.get('status') == 'skipped']
                
                assert len(executed_actions) == 1  # ACT_001 should execute
                assert len(skipped_actions) == 1   # ACT_002 should be skipped
    
    def test_approval_status_overrides_action_plan_status(self, mock_approval_store):
        """Test ApprovalStore status overrides action plan approval status."""
        # Setup: action plan says 'supervisor_approval' but ApprovalStore says 'approved'
        mock_approval_store.get_approval_by_action_id.return_value = {
            'action_id': 'ACT_002',
            'approval_status': 'approved',  # Override: now approved
            'approved_at': '2024-01-15T11:00:00Z',
            'approver_id': 'SUPERVISOR_001'
        }
        
        # Create plan with action that needs supervisor approval
        plan_with_pending = {
            **self.sample_plan_with_approvals,
            'borrower_plan': {
                'immediate_actions': [
                    {
                        'action_id': 'ACT_002',
                        'action': 'Process refund request',
                        'description': 'Refund $500 payment error',
                        'needs_approval': True,
                        'approval_status': 'supervisor_approval',  # Not approved in plan
                        'risk_level': 'high'
                    }
                ]
            }
        }
        
        from src.storage.action_plan_store import ActionPlanStore
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(plan_with_pending)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            executor.approval_store = mock_approval_store  # Inject mock
            
            # Mock LLM and tool responses
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Refund processed',
                    'tone': 'professional',
                    'timing': 'immediate',
                    'parameters': {'recipient': 'customer@example.com'}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                executor.client = mock_client
                
                self.mock_tools.send_email.return_value = {'status': 'success', 'email_id': 'EMAIL_001'}
                
                # Execute - should now execute because ApprovalStore says approved
                context = {'customer_id': 'CUST_001', 'plan_id': 'PLAN_APPROVAL_001'}
                results = executor._execute_borrower_actions(plan_with_pending['borrower_plan'], context)
                
                # Should execute the action (ApprovalStore override)
                executed_actions = [r for r in results if r.get('status') != 'skipped']
                assert len(executed_actions) == 1
                assert executed_actions[0]['status'] == 'success'
                
                # Verify ApprovalStore was consulted
                mock_approval_store.get_approval_by_action_id.assert_called_with('ACT_002')
    
    def test_approval_record_not_found_handling(self, mock_approval_store):
        """Test handling when approval record is not found in ApprovalStore."""
        # Setup: ApprovalStore returns None (no record found)
        mock_approval_store.get_approval_by_action_id.return_value = None
        
        from src.storage.action_plan_store import ActionPlanStore
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan_with_approvals)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            executor.approval_store = mock_approval_store
            
            # Execute - should fall back to action plan approval status
            context = {'customer_id': 'CUST_001', 'plan_id': 'PLAN_APPROVAL_001'}
            results = executor._execute_borrower_actions(
                self.sample_plan_with_approvals['borrower_plan'], context
            )
            
            # Should query ApprovalStore but fall back to action plan status
            mock_approval_store.get_approval_by_action_id.assert_called()
            
            # Verify fallback behavior: ACT_001 executes, ACT_002 skipped
            executed_actions = [r for r in results if r.get('status') != 'skipped']
            skipped_actions = [r for r in results if r.get('status') == 'skipped']
            
            assert len(executed_actions) >= 1  # At least ACT_001 should execute
            assert len(skipped_actions) >= 1   # At least ACT_002 should be skipped
    
    def test_approval_store_error_handling(self, mock_approval_store):
        """Test handling of ApprovalStore database errors."""
        # Setup: ApprovalStore raises exception
        mock_approval_store.get_approval_by_action_id.side_effect = Exception("Database connection error")
        
        from src.storage.action_plan_store import ActionPlanStore
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan_with_approvals)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            executor.approval_store = mock_approval_store
            
            # Should gracefully handle the error and fall back to action plan status
            context = {'customer_id': 'CUST_001', 'plan_id': 'PLAN_APPROVAL_001'}
            results = executor._execute_borrower_actions(
                self.sample_plan_with_approvals['borrower_plan'], context
            )
            
            # Should still return results (graceful degradation)
            assert len(results) >= 1
            
            # At least one action should still be processed (fallback to action plan status)
            processed_actions = [r for r in results if 'status' in r]
            assert len(processed_actions) >= 1
    
    def test_end_to_end_approval_aware_execution_flow(self, mock_approval_store):
        """Test complete end-to-end approval-aware execution flow."""
        # Setup complex approval scenario
        approval_records = {
            'ACT_001': {
                'action_id': 'ACT_001',
                'approval_status': 'approved',
                'approved_at': '2024-01-15T10:00:00Z',
                'approver_id': 'AUTO_SYSTEM'
            },
            'ACT_002': {
                'action_id': 'ACT_002', 
                'approval_status': 'approved',
                'approved_at': '2024-01-15T10:30:00Z',
                'approver_id': 'SUPERVISOR_001'
            },
            'ACT_003': {
                'action_id': 'ACT_003',
                'approval_status': 'pending_advisor',
                'submitted_at': '2024-01-15T10:15:00Z'
            }
        }
        
        mock_approval_store.get_approval_by_action_id.side_effect = lambda aid: approval_records.get(aid)
        
        from src.storage.action_plan_store import ActionPlanStore
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_plan_with_approvals)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            executor.approval_store = mock_approval_store
            
            # Mock all tool responses
            self.mock_tools.send_email.return_value = {'status': 'success', 'email_id': 'EMAIL_001'}
            self.mock_tools.generate_document.return_value = {'status': 'success', 'doc_id': 'DOC_001'}
            self.mock_tools.schedule_callback.return_value = {'status': 'success', 'callback_id': 'CB_001'}
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                # Mock different LLM decisions for different actions
                mock_decisions = [
                    {
                        'tool': 'email',
                        'content': 'Payment confirmation sent',
                        'tone': 'friendly',
                        'timing': 'immediate',
                        'parameters': {'recipient': 'customer@example.com'}
                    },
                    {
                        'tool': 'document',
                        'content': 'Refund documentation',
                        'tone': 'formal',
                        'timing': 'immediate', 
                        'parameters': {'doc_type': 'refund_receipt'}
                    }
                ]
                
                mock_responses = []
                for decision in mock_decisions:
                    mock_response = MagicMock()
                    mock_response.output_parsed = decision
                    mock_responses.append(mock_response)
                
                mock_client.responses.create.side_effect = mock_responses
                executor.client = mock_client
                
                # Execute full action plan
                result = executor.execute_action_plan('PLAN_APPROVAL_001')
                
                # Verify execution completed successfully
                assert result['status'] == 'success'
                assert 'execution_id' in result
                
                # Verify ApprovalStore was consulted for each action
                expected_queries = ['ACT_001', 'ACT_002', 'ACT_003']
                for action_id in expected_queries:
                    mock_approval_store.get_approval_by_action_id.assert_any_call(action_id)
                
                # Analyze results
                all_results = []
                for category in ['borrower_actions', 'advisor_actions', 'supervisor_actions']:
                    all_results.extend(result['results'].get(category, []))
                
                executed_actions = [r for r in all_results if r.get('status') == 'success']
                skipped_actions = [r for r in all_results if r.get('status') == 'skipped']
                
                # Should execute ACT_001 and ACT_002 (approved), skip ACT_003 (pending)
                assert len(executed_actions) == 2  # ACT_001 and ACT_002
                assert len(skipped_actions) == 1   # ACT_003
                
                # Verify skipped action details
                skipped = skipped_actions[0]
                assert 'Awaiting approval' in skipped.get('reason', '')
                assert skipped.get('original_action', {}).get('action_id') == 'ACT_003'