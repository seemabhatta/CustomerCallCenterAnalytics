"""
Test suite for workflow execution system.
Following TDD principles - tests written first before implementation.
"""
import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

from src.agents.workflow_execution_agent import WorkflowExecutionAgent
from src.services.workflow_execution_engine import WorkflowExecutionEngine
from src.executors.workflow_mock_executors import (
    EmailMockExecutor,
    CRMockExecutor,
    DisclosureMockExecutor,
    TaskMockExecutor,
    TrainingMockExecutor
)
from src.storage.workflow_execution_store import WorkflowExecutionStore


class TestWorkflowExecutionAgent:
    """Test the LLM agent that makes execution decisions."""
    
    @pytest.fixture
    def execution_agent(self):
        """Create execution agent for testing."""
        return WorkflowExecutionAgent()
    
    @pytest.fixture
    def sample_borrower_workflow(self):
        """Sample BORROWER workflow for testing."""
        return {
            'id': 'wf_123',
            'status': 'APPROVED',
            'workflow_type': 'BORROWER',
            'workflow_data': {
                'action_item': 'Send refinance disclosure email to borrower',
                'description': 'Send required TILA disclosure documents to borrower via email',
                'priority': 'high'
            },
            'plan_id': 'PLAN_123',
            'risk_level': 'MEDIUM'
        }
    
    @pytest.fixture
    def sample_advisor_workflow(self):
        """Sample ADVISOR workflow for testing."""
        return {
            'id': 'wf_456',
            'status': 'APPROVED',
            'workflow_type': 'ADVISOR',
            'workflow_data': {
                'action_item': 'Update customer record with call summary',
                'description': 'Add notes from refinance discussion to CRM',
                'priority': 'medium'
            },
            'plan_id': 'PLAN_123',
            'risk_level': 'LOW'
        }
    
    @pytest.mark.asyncio
    async def test_analyze_borrower_email_action(self, execution_agent, sample_borrower_workflow):
        """Test agent correctly identifies email executor for borrower action."""
        # When: Agent analyzes borrower email action
        decision = await execution_agent.analyze_workflow_action(sample_borrower_workflow)
        
        # Then: Should identify email executor
        assert decision['executor_type'] == 'email'
        assert 'recipient' in decision['parameters']
        assert 'subject' in decision['parameters']
        assert decision['confidence'] > 0.8
    
    @pytest.mark.asyncio
    async def test_analyze_advisor_crm_action(self, execution_agent, sample_advisor_workflow):
        """Test agent correctly identifies CRM executor for advisor action."""
        # When: Agent analyzes advisor CRM action
        decision = await execution_agent.analyze_workflow_action(sample_advisor_workflow)
        
        # Then: Should identify CRM executor
        assert decision['executor_type'] == 'crm'
        assert 'customer_id' in decision['parameters']
        assert 'updates' in decision['parameters']
        assert decision['confidence'] > 0.7
    
    @pytest.mark.asyncio
    async def test_analyze_ambiguous_action_fails_fast(self, execution_agent):
        """Test agent fails fast on ambiguous actions - NO FALLBACK."""
        ambiguous_workflow = {
            'workflow_data': {
                'action_item': 'Do something unclear',
                'description': 'Unclear action description'
            }
        }
        
        # When/Then: Should raise exception, no fallback
        with pytest.raises(ValueError, match="Cannot determine executor type"):
            await execution_agent.analyze_workflow_action(ambiguous_workflow)
    
    @pytest.mark.asyncio
    async def test_generate_email_payload(self, execution_agent, sample_borrower_workflow):
        """Test agent generates realistic email payload."""
        # When: Agent generates email payload
        payload = await execution_agent.generate_execution_payload(
            sample_borrower_workflow,
            executor_type='email'
        )
        
        # Then: Should contain all required email fields
        assert payload['to']
        assert payload['subject']
        assert payload['body']
        assert len(payload['body']) > 50  # Should be substantial content
        assert 'disclosure' in payload['subject'].lower()
        assert isinstance(payload['attachments'], list)
    
    @pytest.mark.asyncio
    async def test_generate_crm_payload(self, execution_agent, sample_advisor_workflow):
        """Test agent generates realistic CRM payload."""
        # When: Agent generates CRM payload
        payload = await execution_agent.generate_execution_payload(
            sample_advisor_workflow,
            executor_type='crm'
        )
        
        # Then: Should contain CRM update structure
        assert payload['customer_id']
        assert payload['updates']
        assert isinstance(payload['updates'], dict)
        assert 'notes' in payload['updates']
        assert 'status' in payload['updates']


class TestMockExecutors:
    """Test individual mock executors."""
    
    @pytest.fixture
    def sample_workflow(self):
        """Generic workflow for executor testing."""
        return {
            'id': 'wf_test',
            'workflow_type': 'BORROWER',
            'workflow_data': {
                'action_item': 'Test action',
                'description': 'Test description'
            }
        }
    
    def test_email_executor_generates_payload(self, sample_workflow):
        """Test email executor generates proper payload."""
        # Given: Email executor and workflow
        executor = EmailMockExecutor()
        params = {
            'recipient': 'test@example.com',
            'subject': 'Test Email',
            'body': 'This is a comprehensive test email body with sufficient content to meet validation requirements for professional communication standards.'
        }
        
        # When: Execute
        result = executor.execute(sample_workflow, params)
        
        # Then: Should return email payload
        assert result['executor'] == 'email'
        assert result['mock'] is True
        assert result['payload']['to'] == 'test@example.com'
        assert result['payload']['subject'] == 'Test Email'
        assert 'comprehensive test email body' in result['payload']['body']
        assert isinstance(result['payload']['attachments'], list)
    
    def test_crm_executor_generates_payload(self, sample_workflow):
        """Test CRM executor generates proper payload."""
        # Given: CRM executor
        executor = CRMockExecutor()
        params = {
            'customer_id': 'CUST_123',
            'updates': {'status': 'contacted', 'notes': 'Comprehensive test notes with sufficient detail to meet CRM validation requirements for professional record keeping.'}
        }
        
        # When: Execute
        result = executor.execute(sample_workflow, params)
        
        # Then: Should return CRM payload
        assert result['executor'] == 'crm'
        assert result['mock'] is True
        assert result['payload']['customer_id'] == 'CUST_123'
        assert result['payload']['updates']['status'] == 'contacted'
        assert result['payload']['api_endpoint']
        assert result['payload']['method'] == 'POST'
    
    def test_disclosure_executor_generates_payload(self, sample_workflow):
        """Test disclosure executor generates proper payload."""
        # Given: Disclosure executor
        executor = DisclosureMockExecutor()
        params = {
            'document_type': 'refinance_disclosure',
            'customer_data': {'loan_amount': 250000, 'rate': 6.5}
        }
        
        # When: Execute
        result = executor.execute(sample_workflow, params)
        
        # Then: Should return disclosure payload
        assert result['executor'] == 'disclosure'
        assert result['payload']['document_type'] == 'refinance_disclosure'
        assert result['payload']['customer_data']
        assert 'compliance_flags' in result['payload']
        assert 'delivery_method' in result['payload']
    
    def test_task_executor_generates_payload(self, sample_workflow):
        """Test task executor generates proper payload."""
        # Given: Task executor
        executor = TaskMockExecutor()
        params = {
            'assignee': 'advisor_123',
            'title': 'Follow up with customer',
            'due_date': '2024-01-15'
        }
        
        # When: Execute
        result = executor.execute(sample_workflow, params)
        
        # Then: Should return task payload
        assert result['executor'] == 'task'
        assert result['payload']['assignee'] == 'advisor_123'
        assert result['payload']['title'] == 'Follow up with customer'
        assert result['payload']['due_date'] == '2024-01-15'
        assert result['payload']['priority']
        assert result['payload']['task_id']


class TestWorkflowExecutionEngine:
    """Test the main execution engine orchestrator."""
    
    @pytest.fixture
    def execution_engine(self):
        """Create execution engine for testing."""
        return WorkflowExecutionEngine()
    
    @pytest.fixture
    def approved_workflow(self):
        """Approved workflow ready for execution."""
        return {
            'id': 'wf_approved',
            'status': 'APPROVED',
            'workflow_type': 'BORROWER',
            'workflow_data': {
                'action_item': 'Send welcome email to new customer',
                'description': 'Send onboarding welcome email with next steps'
            },
            'plan_id': 'PLAN_WELCOME'
        }
    
    @pytest.fixture
    def pending_workflow(self):
        """Workflow still pending approval."""
        return {
            'id': 'wf_pending',
            'status': 'AWAITING_APPROVAL',
            'workflow_type': 'BORROWER',
            'workflow_data': {
                'action_item': 'Send disclosure documents'
            }
        }
    
    @pytest.mark.asyncio
    async def test_execute_approved_workflow(self, execution_engine, approved_workflow):
        """Test successful execution of approved workflow."""
        # Mock workflow store to return approved workflow
        with patch.object(execution_engine.workflow_store, 'get_by_id', return_value=approved_workflow):
            with patch.object(execution_engine.execution_store, 'create') as mock_store:
                mock_store.return_value = 'exec_123'
                
                # When: Execute workflow
                result = await execution_engine.execute_workflow('wf_approved')
                
                # Then: Should execute successfully
                assert result['execution_id']
                assert result['workflow_id'] == 'wf_approved'
                assert result['status'] == 'executed'
                assert result['executor_type']
                assert result['payload']
                assert result['mock'] is True
    
    @pytest.mark.asyncio
    async def test_execute_non_approved_workflow_fails(self, execution_engine, pending_workflow):
        """Test execution fails for non-approved workflows - NO FALLBACK."""
        # Mock workflow store to return pending workflow
        with patch.object(execution_engine.workflow_store, 'get_by_id', return_value=pending_workflow):
            
            # When/Then: Should fail fast, no fallback
            with pytest.raises(ValueError, match="Workflow must be approved"):
                await execution_engine.execute_workflow('wf_pending')
    
    @pytest.mark.asyncio
    async def test_execute_nonexistent_workflow_fails(self, execution_engine):
        """Test execution fails for nonexistent workflows - NO FALLBACK."""
        # Mock workflow store to return None
        with patch.object(execution_engine.workflow_store, 'get_by_id', return_value=None):
            
            # When/Then: Should fail fast
            with pytest.raises(ValueError, match="Workflow not found"):
                await execution_engine.execute_workflow('nonexistent')
    
    @pytest.mark.asyncio
    async def test_execution_result_stored(self, execution_engine, approved_workflow):
        """Test execution results are properly stored."""
        # Mock dependencies
        with patch.object(execution_engine.workflow_store, 'get_by_id', return_value=approved_workflow):
            with patch.object(execution_engine.execution_store, 'create') as mock_store:
                mock_store.return_value = 'exec_stored'
                
                # When: Execute workflow
                await execution_engine.execute_workflow('wf_approved')
                
                # Then: Should store execution record
                mock_store.assert_called_once()
                call_args = mock_store.call_args[0][0]  # First argument
                assert call_args['workflow_id'] == 'wf_approved'
                assert call_args['executor_type']
                assert call_args['execution_payload']
                assert call_args['execution_status'] == 'executed'
                assert call_args['mock_execution'] is True
    
    @pytest.mark.asyncio
    async def test_workflow_status_updated_after_execution(self, execution_engine, approved_workflow):
        """Test workflow status updated to EXECUTED after successful execution."""
        # Mock dependencies
        with patch.object(execution_engine.workflow_store, 'get_by_id', return_value=approved_workflow):
            with patch.object(execution_engine.execution_store, 'create', return_value='exec_123'):
                with patch.object(execution_engine.workflow_store, 'update_status') as mock_update:
                    
                    # When: Execute workflow
                    await execution_engine.execute_workflow('wf_approved')
                    
                    # Then: Should update workflow status
                    mock_update.assert_called_once_with(
                        'wf_approved',
                        'EXECUTED',
                        transitioned_by='system_executor',
                        reason='Workflow executed successfully',
                        additional_data={'execution_id': 'exec_123'}
                    )


class TestWorkflowExecutionStore:
    """Test execution storage functionality."""
    
    @pytest.fixture
    def execution_store(self):
        """Create execution store for testing."""
        return WorkflowExecutionStore(db_path=":memory:")  # In-memory for testing
    
    @pytest.fixture
    def sample_execution_data(self):
        """Sample execution data for storage."""
        return {
            'workflow_id': 'wf_test',
            'executor_type': 'email',
            'execution_payload': {
                'to': 'test@example.com',
                'subject': 'Test Email',
                'body': 'Test content'
            },
            'execution_status': 'executed',
            'executed_by': 'test_user',
            'mock_execution': True
        }
    
    @pytest.mark.asyncio
    async def test_create_execution_record(self, execution_store, sample_execution_data):
        """Test creating execution record."""
        # When: Create execution record
        execution_id = await execution_store.create(sample_execution_data)
        
        # Then: Should return execution ID
        assert execution_id
        assert execution_id.startswith('exec_')
    
    @pytest.mark.asyncio
    async def test_get_execution_by_workflow(self, execution_store, sample_execution_data):
        """Test retrieving executions by workflow ID."""
        # Given: Stored execution
        execution_id = await execution_store.create(sample_execution_data)
        
        # When: Get executions by workflow
        executions = await execution_store.get_by_workflow('wf_test')
        
        # Then: Should return execution records
        assert len(executions) == 1
        assert executions[0]['id'] == execution_id
        assert executions[0]['workflow_id'] == 'wf_test'
        assert executions[0]['executor_type'] == 'email'
        assert executions[0]['execution_payload']
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_workflow_executions(self, execution_store):
        """Test getting executions for nonexistent workflow."""
        # When: Get executions for nonexistent workflow
        executions = await execution_store.get_by_workflow('nonexistent')
        
        # Then: Should return empty list
        assert executions == []


class TestIntegration:
    """Integration tests for complete execution flow."""
    
    @pytest.mark.asyncio
    async def test_complete_execution_flow(self):
        """Test complete flow from workflow to stored execution."""
        # Given: Complete execution system setup
        agent = WorkflowExecutionAgent()
        engine = WorkflowExecutionEngine()
        
        workflow = {
            'id': 'wf_integration',
            'status': 'APPROVED',
            'workflow_type': 'BORROWER',
            'workflow_data': {
                'action_item': 'Send loan approval notification email',
                'description': 'Send email confirming loan approval with next steps'
            },
            'plan_id': 'PLAN_APPROVAL'
        }
        
        # Mock workflow store
        with patch.object(engine.workflow_store, 'get_by_id', return_value=workflow):
            with patch.object(engine.execution_store, 'create', return_value='exec_integration'):
                with patch.object(engine.workflow_store, 'update_status'):
                    
                    # When: Execute complete flow
                    result = await engine.execute_workflow('wf_integration')
                    
                    # Then: Should complete successfully
                    assert result['execution_id'] == 'exec_integration'
                    assert result['workflow_id'] == 'wf_integration'
                    assert result['status'] == 'executed'
                    assert result['executor_type']
                    assert result['payload']
                    assert 'to' in result['payload']  # Email payload
                    assert 'subject' in result['payload']
                    assert 'body' in result['payload']


# Test data samples for different workflow types
SAMPLE_WORKFLOWS = {
    'email_disclosure': {
        'workflow_data': {
            'action_item': 'Send TILA disclosure to borrower',
            'description': 'Send required Truth in Lending Act disclosure documents'
        },
        'expected_executor': 'email'
    },
    'crm_update': {
        'workflow_data': {
            'action_item': 'Update customer profile with new income information',
            'description': 'Add updated income data from recent call to CRM'
        },
        'expected_executor': 'crm'
    },
    'task_assignment': {
        'workflow_data': {
            'action_item': 'Assign follow-up call task to senior advisor',
            'description': 'Create task for advisor to follow up on complex refinance case'
        },
        'expected_executor': 'task'
    },
    'disclosure_generation': {
        'workflow_data': {
            'action_item': 'Generate refinance disclosure package',
            'description': 'Create complete disclosure package for refinance application'
        },
        'expected_executor': 'disclosure'
    },
    'training_assignment': {
        'workflow_data': {
            'action_item': 'Assign compliance training to advisor',
            'description': 'Assign mandatory RESPA training module to advisor'
        },
        'expected_executor': 'training'
    }
}


@pytest.mark.parametrize('workflow_key', SAMPLE_WORKFLOWS.keys())
@pytest.mark.asyncio
async def test_executor_type_detection(workflow_key):
    """Test that agent correctly detects executor type for different workflows."""
    # Given: Sample workflow
    workflow_data = SAMPLE_WORKFLOWS[workflow_key]
    workflow = {
        'id': f'wf_{workflow_key}',
        'workflow_data': workflow_data['workflow_data'],
        'workflow_type': 'BORROWER'
    }
    
    # Mock the agent
    agent = WorkflowExecutionAgent()
    
    # Mock LLM response
    mock_response = {
        'executor_type': workflow_data['expected_executor'],
        'confidence': 0.9,
        'parameters': {'test': 'value'},
        'reasoning': 'Test reasoning'
    }
    
    with patch.object(agent.llm, 'generate_structured', return_value=mock_response):
        # When: Analyze workflow
        decision = await agent.analyze_workflow_action(workflow)
        
        # Then: Should identify correct executor
        assert decision['executor_type'] == workflow_data['expected_executor']
        assert decision['confidence'] > 0.8