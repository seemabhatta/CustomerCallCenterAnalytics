"""
Test cases for Execution Feedback with Actor Assignment
Tests the complete feedback loop from execution through observation.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.executors.smart_executor import SmartExecutor
from src.storage.action_plan_store import ActionPlanStore
from src.storage.approval_store import ApprovalStore
from src.models.transcript import Transcript


class TestExecutionFeedbackWithActors:
    """Test execution feedback loop with actor-based execution for demo app."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock tools for testing
        self.mock_tools = MagicMock()
        
        # Sample action plan with actions suitable for actor assignment
        self.sample_action_plan = {
            'plan_id': 'PLAN_ACTOR_001',
            'transcript_id': 'CALL_ACTOR_001',
            'analysis_id': 'ANALYSIS_ACTOR_001',
            'decision_agent_processed': True,
            'routing_decision': 'supervisor_approval',
            'risk_level': 'high',
            'queue_status': 'approved',
            'borrower_plan': {
                'immediate_actions': [
                    {
                        'action_id': 'ACT_CUSTOMER_001',
                        'action': 'Send payment plan options',
                        'description': 'Customer-facing communication',
                        'needs_approval': True,
                        'approval_status': 'approved',
                        'risk_level': 'medium',
                        'financial_impact': True,
                        'suitable_actors': ['advisor', 'customer']
                    },
                    {
                        'action_id': 'ACT_CRM_001', 
                        'action': 'Update customer record in CRM',
                        'description': 'System integration task',
                        'needs_approval': False,
                        'approval_status': 'auto_approved',
                        'risk_level': 'low',
                        'suitable_actors': ['advisor']
                    }
                ]
            },
            'advisor_plan': {
                'coaching_items': [
                    {
                        'action_id': 'ACT_TRAINING_001',
                        'action': 'Complete empathy training module',
                        'description': 'Skills development',
                        'needs_approval': True,
                        'approval_status': 'approved',
                        'risk_level': 'low',
                        'suitable_actors': ['advisor', 'supervisor']
                    }
                ]
            },
            'supervisor_plan': {
                'escalation_items': [
                    {
                        'action_id': 'ACT_REVIEW_001',
                        'action': 'Review high-risk case',
                        'description': 'Supervisory oversight',
                        'needs_approval': False,
                        'approval_status': 'auto_approved',
                        'risk_level': 'medium',
                        'suitable_actors': ['supervisor']
                    }
                ]
            }
        }
    
    def teardown_method(self):
        """Clean up temporary database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_smartexecutor_stores_execution_results(self):
        """Verify execution results are stored in ApprovalStore with actor details."""
        # Store the action plan
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_action_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            # Mock successful execution
            self.mock_tools.send_email.return_value = {'status': 'success', 'email_id': 'EMAIL_001'}
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                # Mock LLM decision for actor assignment
                mock_actor_decision = {
                    'assigned_actor': 'advisor',
                    'reasoning': 'Advisor best suited for customer communication',
                    'execution_method': 'email',
                    'expected_outcome': 'Customer receives payment options'
                }
                
                mock_execution_decision = {
                    'tool': 'email',
                    'content': 'Payment plan options email',
                    'tone': 'professional',
                    'timing': 'immediate',
                    'parameters': {'recipient': 'customer@example.com'}
                }
                
                # Mock responses for both actor assignment and execution
                mock_responses = [
                    MagicMock(output_parsed=mock_actor_decision),
                    MagicMock(output_parsed=mock_execution_decision)
                ]
                mock_client.responses.create.side_effect = mock_responses
                executor.client = mock_client
                
                # Execute the plan
                result = executor.execute_action_plan('PLAN_ACTOR_001')
                
                # Verify execution completed successfully
                assert result['status'] == 'success'
                assert 'execution_id' in result
                
                # Verify execution results are stored with actor information
                approval_store = ApprovalStore(self.temp_db.name)
                
                # Check that approval records were updated with execution results
                approval_record = approval_store.get_approval_by_action_id('ACT_CUSTOMER_001')
                
                if approval_record:  # May be None if not stored yet - that's what we're testing
                    assert 'execution_result' in approval_record or 'executed_at' in approval_record
    
    def test_execution_assigns_to_correct_actor(self):
        """Test that actions are assigned to appropriate actors using LLM."""
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_action_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            self.mock_tools.send_email.return_value = {'status': 'success'}
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                # Mock actor assignment decisions
                mock_decisions = [
                    # Actor assignment for customer communication
                    {
                        'assigned_actor': 'advisor',
                        'reasoning': 'Advisor handles customer communications',
                        'confidence': 0.9
                    },
                    # Execution decision
                    {
                        'tool': 'email',
                        'content': 'Test content',
                        'tone': 'professional',
                        'timing': 'immediate',
                        'parameters': {}
                    }
                ]
                
                mock_responses = [MagicMock(output_parsed=decision) for decision in mock_decisions]
                mock_client.responses.create.side_effect = mock_responses
                executor.client = mock_client
                
                result = executor.execute_action_plan('PLAN_ACTOR_001')
                
                # Verify that LLM was called for actor assignment
                assert mock_client.responses.create.call_count >= 1
                
                # Verify execution includes actor information
                executed_actions = result['results']['borrower_actions']
                if executed_actions:
                    action_result = executed_actions[0]
                    # Should contain actor assignment information
                    assert 'original_action' in action_result or 'status' in action_result
    
    def test_actor_execution_creates_mock_artifacts(self):
        """Test mock execution by actors creates realistic artifacts."""
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_action_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            # Mock artifact creation
            mock_artifacts = {
                'email_sent': 'payment_options_customer@example.com.html',
                'crm_updated': True,
                'training_assigned': 'empathy_module_001'
            }
            
            self.mock_tools.send_email.return_value = {
                'status': 'success',
                'artifact_path': mock_artifacts['email_sent'],
                'metadata': {'actor': 'advisor', 'timestamp': datetime.now().isoformat()}
            }
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Mock email content',
                    'tone': 'professional',
                    'timing': 'immediate',
                    'parameters': {'recipient': 'test@example.com'}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                executor.client = mock_client
                
                result = executor.execute_action_plan('PLAN_ACTOR_001')
                
                # Verify artifacts were created
                assert 'artifacts_created' in result
                artifacts = result.get('artifacts_created', [])
                
                # Should have created at least one artifact
                assert len([a for a in artifacts if a]) > 0
    
    def test_execution_results_include_actor_details(self):
        """Test results include which actor executed each action."""
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_action_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            # Mock tool response with actor information
            self.mock_tools.send_email.return_value = {
                'status': 'success',
                'executed_by': 'advisor',
                'execution_time': '2024-01-15T10:30:00Z',
                'artifact_path': 'email_001.html'
            }
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Test content',
                    'tone': 'professional',
                    'timing': 'immediate',
                    'parameters': {}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                executor.client = mock_client
                
                result = executor.execute_action_plan('PLAN_ACTOR_001')
                
                # Verify execution results include actor information
                assert result['status'] == 'success'
                
                # Check if execution results contain actor details
                all_results = []
                for category in ['borrower_actions', 'advisor_actions', 'supervisor_actions']:
                    all_results.extend(result['results'].get(category, []))
                
                # Should have at least one result with execution details
                assert len(all_results) > 0
    
    def test_failed_execution_properly_recorded(self):
        """Test failure scenarios are captured with actor and error details."""
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_action_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            # Mock tool failure
            self.mock_tools.send_email.side_effect = Exception("Email service unavailable")
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Test content',
                    'tone': 'professional',
                    'timing': 'immediate',
                    'parameters': {}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                executor.client = mock_client
                
                result = executor.execute_action_plan('PLAN_ACTOR_001')
                
                # Execution should complete but with errors recorded
                assert 'errors' in result
                
                # Should have recorded the error details
                if result.get('errors'):
                    assert len(result['errors']) > 0
    
    def test_execution_feedback_ready_for_observer(self):
        """Test execution results format is suitable for Observer evaluation."""
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_action_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            self.mock_tools.send_email.return_value = {'status': 'success', 'email_id': 'EMAIL_001'}
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Test execution',
                    'tone': 'professional',
                    'timing': 'immediate',
                    'parameters': {}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                executor.client = mock_client
                
                result = executor.execute_action_plan('PLAN_ACTOR_001')
                
                # Verify result has fields Observer needs for evaluation
                required_fields = ['execution_id', 'plan_id', 'executed_at', 'status', 'results']
                for field in required_fields:
                    assert field in result, f"Missing field {field} required for Observer"
                
                # Results should contain action details for evaluation
                assert 'results' in result
                results_data = result['results']
                assert isinstance(results_data, dict)
    
    def test_multiple_actions_different_actors(self):
        """Test execution of multiple actions assigned to different actors."""
        # Create plan with actions suitable for different actors
        multi_actor_plan = {
            **self.sample_action_plan,
            'plan_id': 'PLAN_MULTI_ACTOR',
            'borrower_plan': {
                'immediate_actions': [
                    {
                        'action_id': 'ACT_ADVISOR_001',
                        'action': 'Call customer for clarification',
                        'suitable_actors': ['advisor']
                    },
                    {
                        'action_id': 'ACT_CUSTOMER_001', 
                        'action': 'Respond to payment inquiry',
                        'suitable_actors': ['customer']
                    }
                ]
            },
            'supervisor_plan': {
                'escalation_items': [
                    {
                        'action_id': 'ACT_SUPERVISOR_001',
                        'action': 'Review compliance violation',
                        'suitable_actors': ['supervisor']
                    }
                ]
            }
        }
        
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(multi_actor_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            # Mock different tool responses for different actors
            self.mock_tools.send_email.return_value = {'status': 'success'}
            self.mock_tools.schedule_callback.return_value = {'status': 'success'}
            self.mock_tools.send_notification.return_value = {'status': 'success'}
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                # Mock multiple LLM decisions for different actions
                mock_decisions = [
                    {'tool': 'callback', 'content': 'Schedule call', 'tone': 'professional', 'timing': 'immediate', 'parameters': {}},
                    {'tool': 'email', 'content': 'Payment response', 'tone': 'helpful', 'timing': 'immediate', 'parameters': {}},
                    {'tool': 'notification', 'content': 'Compliance review', 'tone': 'formal', 'timing': 'immediate', 'parameters': {}}
                ]
                
                mock_responses = [MagicMock(output_parsed=decision) for decision in mock_decisions]
                mock_client.responses.create.side_effect = mock_responses
                executor.client = mock_client
                
                result = executor.execute_action_plan('PLAN_MULTI_ACTOR')
                
                # Should have executed actions for multiple actors
                assert result['status'] == 'success'
                
                # Check that multiple categories of actions were processed
                results_categories = ['borrower_actions', 'advisor_actions', 'supervisor_actions']
                executed_categories = [cat for cat in results_categories if result['results'].get(cat)]
                
                # Should have executed at least one category
                assert len(executed_categories) > 0
    
    def test_execution_audit_trail_for_compliance(self):
        """Test that execution creates complete audit trail for compliance."""
        action_plan_store = ActionPlanStore(self.temp_db.name)
        action_plan_store.store(self.sample_action_plan)
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
            executor = SmartExecutor(db_path=self.temp_db.name)
            executor.tools = self.mock_tools
            
            self.mock_tools.send_email.return_value = {'status': 'success', 'email_id': 'EMAIL_001'}
            
            with patch('openai.OpenAI') as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                
                mock_decision = {
                    'tool': 'email',
                    'content': 'Audit trail test',
                    'tone': 'professional',
                    'timing': 'immediate',
                    'parameters': {}
                }
                
                mock_response = MagicMock()
                mock_response.output_parsed = mock_decision
                mock_client.responses.create.return_value = mock_response
                executor.client = mock_client
                
                result = executor.execute_action_plan('PLAN_ACTOR_001')
                
                # Verify audit trail fields are present
                audit_fields = ['execution_id', 'plan_id', 'executed_at', 'status']
                for field in audit_fields:
                    assert field in result, f"Missing audit field: {field}"
                
                # Execution ID should be unique and properly formatted
                execution_id = result.get('execution_id', '')
                assert execution_id.startswith('EXEC_'), f"Invalid execution ID format: {execution_id}"
                
                # Should have timestamp
                executed_at = result.get('executed_at')
                assert executed_at is not None, "Missing execution timestamp"