"""Tests for ActionPlanStore."""
import pytest
import tempfile
import os
import json
from datetime import datetime
from src.storage.action_plan_store import ActionPlanStore


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def action_plan_store(temp_db):
    """Create ActionPlanStore with temporary database."""
    return ActionPlanStore(temp_db)


@pytest.fixture
def sample_action_plan():
    """Sample action plan data for testing."""
    return {
        'plan_id': 'PLAN_001',
        'analysis_id': 'ANALYSIS_001',
        'transcript_id': 'TRANSCRIPT_001',
        'risk_level': 'medium',
        'approval_route': 'advisor_approval',
        'queue_status': 'pending_advisor',
        'auto_executable': False,
        'generator_version': '1.0',
        'routing_reason': 'Medium risk detected: 0.5',
        'borrower_plan': {
            'immediate_actions': [
                {
                    'action': 'Send confirmation email',
                    'timeline': 'Within 24 hours',
                    'priority': 'high',
                    'auto_executable': True
                }
            ],
            'follow_ups': [
                {
                    'action': 'Follow up call',
                    'due_date': '2024-01-15',
                    'owner': 'CSR'
                }
            ],
            'personalized_offers': ['Refinance evaluation'],
            'risk_mitigation': ['Monitor payment patterns']
        },
        'advisor_plan': {
            'coaching_items': ['Improve active listening'],
            'performance_feedback': {
                'strengths': ['Clear communication'],
                'improvements': ['Better questions'],
                'score_explanations': ['Good resolution']
            },
            'training_recommendations': ['De-escalation training'],
            'next_actions': ['Review recording']
        },
        'supervisor_plan': {
            'escalation_items': [
                {
                    'item': 'Payment dispute',
                    'reason': 'Complex case',
                    'priority': 'medium',
                    'action_required': 'Review'
                }
            ],
            'team_patterns': ['Increase in disputes'],
            'compliance_review': ['Check disclosures'],
            'approval_required': True,
            'process_improvements': ['Streamline process']
        },
        'leadership_plan': {
            'portfolio_insights': ['Rising concerns'],
            'strategic_opportunities': ['Improve online tools'],
            'risk_indicators': ['Customer satisfaction down'],
            'trend_analysis': ['Disputes trending up'],
            'resource_allocation': ['Add staff']
        }
    }


class TestActionPlanStore:
    """Test ActionPlanStore functionality."""
    
    def test_init_creates_database_schema(self, temp_db):
        """Test that initialization creates the correct database schema."""
        store = ActionPlanStore(temp_db)
        
        # Verify the store can be used (schema was created)
        metrics = store.get_summary_metrics()
        assert metrics['total_plans'] == 0
    
    def test_store_action_plan(self, action_plan_store, sample_action_plan):
        """Test storing an action plan."""
        plan_id = action_plan_store.store(sample_action_plan)
        
        assert plan_id == sample_action_plan['plan_id']
        
        # Verify plan was stored
        retrieved_plan = action_plan_store.get_by_id(plan_id)
        assert retrieved_plan is not None
        assert retrieved_plan['plan_id'] == plan_id
        assert retrieved_plan['analysis_id'] == sample_action_plan['analysis_id']
        assert retrieved_plan['transcript_id'] == sample_action_plan['transcript_id']
    
    def test_store_and_replace_action_plan(self, action_plan_store, sample_action_plan):
        """Test storing and replacing an action plan."""
        # Store initial plan
        plan_id = action_plan_store.store(sample_action_plan)
        
        # Modify and store again
        sample_action_plan['risk_level'] = 'high'
        plan_id_2 = action_plan_store.store(sample_action_plan)
        
        assert plan_id == plan_id_2  # Same ID
        
        # Verify updated data
        retrieved_plan = action_plan_store.get_by_id(plan_id)
        assert retrieved_plan['risk_level'] == 'high'
    
    def test_get_by_id(self, action_plan_store, sample_action_plan):
        """Test retrieving action plan by ID."""
        # Store plan
        plan_id = action_plan_store.store(sample_action_plan)
        
        # Retrieve by ID
        retrieved_plan = action_plan_store.get_by_id(plan_id)
        
        assert retrieved_plan is not None
        assert retrieved_plan['plan_id'] == plan_id
        assert retrieved_plan['borrower_plan'] == sample_action_plan['borrower_plan']
        assert retrieved_plan['advisor_plan'] == sample_action_plan['advisor_plan']
        assert retrieved_plan['supervisor_plan'] == sample_action_plan['supervisor_plan']
        assert retrieved_plan['leadership_plan'] == sample_action_plan['leadership_plan']
        
        # Verify metadata
        assert 'created_at' in retrieved_plan
        assert retrieved_plan['approved_at'] is None
        assert retrieved_plan['approved_by'] is None
    
    def test_get_by_id_not_found(self, action_plan_store):
        """Test retrieving non-existent action plan."""
        retrieved_plan = action_plan_store.get_by_id('NONEXISTENT')
        assert retrieved_plan is None
    
    def test_get_by_transcript_id(self, action_plan_store, sample_action_plan):
        """Test retrieving action plan by transcript ID."""
        # Store plan
        action_plan_store.store(sample_action_plan)
        
        # Retrieve by transcript ID
        retrieved_plan = action_plan_store.get_by_transcript_id(sample_action_plan['transcript_id'])
        
        assert retrieved_plan is not None
        assert retrieved_plan['transcript_id'] == sample_action_plan['transcript_id']
    
    def test_get_by_transcript_id_multiple_plans(self, action_plan_store, sample_action_plan):
        """Test that get_by_transcript_id returns one plan when multiple exist."""
        # Store first plan
        action_plan_store.store(sample_action_plan)
        
        # Create a completely separate second plan to avoid mutation issues
        second_plan = sample_action_plan.copy()
        second_plan['plan_id'] = 'PLAN_002'
        second_plan['risk_level'] = 'high'
        
        # Store second plan for same transcript
        action_plan_store.store(second_plan)
        
        # Should return one plan (the query works)
        retrieved_plan = action_plan_store.get_by_transcript_id(sample_action_plan['transcript_id'])
        assert retrieved_plan is not None
        assert retrieved_plan['transcript_id'] == sample_action_plan['transcript_id']
        # The plan_id could be either one since ORDER BY created_at might have same timestamps
        assert retrieved_plan['plan_id'] in ['PLAN_001', 'PLAN_002']
    
    def test_get_approval_queue_default(self, action_plan_store, sample_action_plan):
        """Test getting approval queue without status filter."""
        # Store plans with different statuses
        sample_action_plan['queue_status'] = 'pending_supervisor'
        action_plan_store.store(sample_action_plan)
        
        sample_action_plan['plan_id'] = 'PLAN_002'
        sample_action_plan['queue_status'] = 'pending_advisor'
        action_plan_store.store(sample_action_plan)
        
        sample_action_plan['plan_id'] = 'PLAN_003'
        sample_action_plan['queue_status'] = 'approved'
        action_plan_store.store(sample_action_plan)
        
        # Get approval queue (should exclude approved)
        queue = action_plan_store.get_approval_queue()
        
        assert len(queue) == 2  # Only pending ones
        statuses = {plan['queue_status'] for plan in queue}
        assert 'pending_supervisor' in statuses
        assert 'pending_advisor' in statuses
        assert 'approved' not in statuses
    
    def test_get_approval_queue_with_status(self, action_plan_store, sample_action_plan):
        """Test getting approval queue with specific status filter."""
        # Store plans
        sample_action_plan['queue_status'] = 'pending_supervisor'
        action_plan_store.store(sample_action_plan)
        
        sample_action_plan['plan_id'] = 'PLAN_002'
        sample_action_plan['queue_status'] = 'pending_advisor'
        action_plan_store.store(sample_action_plan)
        
        # Filter by specific status
        supervisor_queue = action_plan_store.get_approval_queue('pending_supervisor')
        assert len(supervisor_queue) == 1
        assert supervisor_queue[0]['queue_status'] == 'pending_supervisor'
        
        advisor_queue = action_plan_store.get_approval_queue('pending_advisor')
        assert len(advisor_queue) == 1
        assert advisor_queue[0]['queue_status'] == 'pending_advisor'
    
    def test_get_by_risk_level(self, action_plan_store, sample_action_plan):
        """Test retrieving action plans by risk level."""
        # Store plans with different risk levels
        sample_action_plan['risk_level'] = 'high'
        action_plan_store.store(sample_action_plan)
        
        sample_action_plan['plan_id'] = 'PLAN_002'
        sample_action_plan['risk_level'] = 'medium'
        action_plan_store.store(sample_action_plan)
        
        sample_action_plan['plan_id'] = 'PLAN_003'
        sample_action_plan['risk_level'] = 'low'
        action_plan_store.store(sample_action_plan)
        
        # Test filtering by risk level
        high_risk = action_plan_store.get_by_risk_level('high')
        assert len(high_risk) == 1
        assert high_risk[0]['risk_level'] == 'high'
        
        medium_risk = action_plan_store.get_by_risk_level('medium')
        assert len(medium_risk) == 1
        assert medium_risk[0]['risk_level'] == 'medium'
    
    def test_approve_plan(self, action_plan_store, sample_action_plan):
        """Test approving an action plan."""
        # Store plan
        plan_id = action_plan_store.store(sample_action_plan)
        
        # Approve plan
        result = action_plan_store.approve_plan(plan_id, 'SUPERVISOR_001')
        assert result is True
        
        # Verify approval
        approved_plan = action_plan_store.get_by_id(plan_id)
        assert approved_plan['queue_status'] == 'approved'
        assert approved_plan['approved_by'] == 'SUPERVISOR_001'
        assert approved_plan['approved_at'] is not None
    
    def test_approve_nonexistent_plan(self, action_plan_store):
        """Test approving a non-existent plan."""
        result = action_plan_store.approve_plan('NONEXISTENT', 'SUPERVISOR_001')
        assert result is False
    
    def test_reject_plan(self, action_plan_store, sample_action_plan):
        """Test rejecting an action plan."""
        # Store plan
        plan_id = action_plan_store.store(sample_action_plan)
        
        # Reject plan
        result = action_plan_store.reject_plan(plan_id, 'SUPERVISOR_001')
        assert result is True
        
        # Verify rejection
        rejected_plan = action_plan_store.get_by_id(plan_id)
        assert rejected_plan['queue_status'] == 'rejected'
        assert rejected_plan['approved_by'] == 'SUPERVISOR_001'
        assert rejected_plan['approved_at'] is not None
    
    def test_get_all(self, action_plan_store, sample_action_plan):
        """Test getting all action plans."""
        # Store multiple plans
        action_plan_store.store(sample_action_plan)
        
        sample_action_plan['plan_id'] = 'PLAN_002'
        action_plan_store.store(sample_action_plan)
        
        # Get all
        all_plans = action_plan_store.get_all()
        assert len(all_plans) == 2
    
    def test_get_all_with_limit(self, action_plan_store, sample_action_plan):
        """Test getting all action plans with limit."""
        # Store multiple plans
        for i in range(5):
            sample_action_plan['plan_id'] = f'PLAN_{i:03d}'
            action_plan_store.store(sample_action_plan)
        
        # Get with limit
        limited_plans = action_plan_store.get_all(limit=3)
        assert len(limited_plans) == 3
    
    def test_get_summary_metrics(self, action_plan_store, sample_action_plan):
        """Test getting summary metrics."""
        # Store plans with different characteristics
        sample_action_plan['risk_level'] = 'high'
        sample_action_plan['queue_status'] = 'pending_supervisor'
        sample_action_plan['approval_route'] = 'supervisor_approval'
        sample_action_plan['auto_executable'] = False
        action_plan_store.store(sample_action_plan)
        
        sample_action_plan['plan_id'] = 'PLAN_002'
        sample_action_plan['risk_level'] = 'low'
        sample_action_plan['queue_status'] = 'approved'
        sample_action_plan['approval_route'] = 'auto_approved'
        sample_action_plan['auto_executable'] = True
        action_plan_store.store(sample_action_plan)
        
        # Get metrics
        metrics = action_plan_store.get_summary_metrics()
        
        assert metrics['total_plans'] == 2
        assert metrics['status_distribution']['pending_supervisor'] == 1
        assert metrics['status_distribution']['approved'] == 1
        assert metrics['risk_distribution']['high'] == 1
        assert metrics['risk_distribution']['low'] == 1
        assert metrics['route_distribution']['supervisor_approval'] == 1
        assert metrics['route_distribution']['auto_approved'] == 1
        assert metrics['auto_executable_percentage'] == 50.0
        assert metrics['pending_approvals'] == 1
    
    def test_delete_action_plan(self, action_plan_store, sample_action_plan):
        """Test deleting an action plan."""
        # Store plan
        plan_id = action_plan_store.store(sample_action_plan)
        
        # Verify it exists
        assert action_plan_store.get_by_id(plan_id) is not None
        
        # Delete
        result = action_plan_store.delete(plan_id)
        assert result is True
        
        # Verify it's gone
        assert action_plan_store.get_by_id(plan_id) is None
    
    def test_delete_nonexistent_plan(self, action_plan_store):
        """Test deleting a non-existent plan."""
        result = action_plan_store.delete('NONEXISTENT')
        assert result is False
    
    def test_delete_all(self, action_plan_store, sample_action_plan):
        """Test deleting all action plans."""
        # Store multiple plans
        action_plan_store.store(sample_action_plan)
        sample_action_plan['plan_id'] = 'PLAN_002'
        action_plan_store.store(sample_action_plan)
        
        # Delete all
        count = action_plan_store.delete_all()
        assert count == 2
        
        # Verify they're gone
        all_plans = action_plan_store.get_all()
        assert len(all_plans) == 0
    
    def test_json_serialization(self, action_plan_store, sample_action_plan):
        """Test that complex plan data is properly serialized/deserialized."""
        # Store plan with complex nested data
        plan_id = action_plan_store.store(sample_action_plan)
        
        # Retrieve and verify structure
        retrieved_plan = action_plan_store.get_by_id(plan_id)
        
        # Verify nested structures are preserved
        assert isinstance(retrieved_plan['borrower_plan'], dict)
        assert isinstance(retrieved_plan['borrower_plan']['immediate_actions'], list)
        assert isinstance(retrieved_plan['borrower_plan']['immediate_actions'][0], dict)
        assert retrieved_plan['borrower_plan']['immediate_actions'][0]['action'] == 'Send confirmation email'
        
        # Verify supervisor plan escalation items structure
        escalation_item = retrieved_plan['supervisor_plan']['escalation_items'][0]
        assert escalation_item['item'] == 'Payment dispute'
        assert escalation_item['priority'] == 'medium'
    
    def test_database_indexes(self, action_plan_store):
        """Test that database indexes were created properly."""
        import sqlite3
        
        conn = sqlite3.connect(action_plan_store.db_path)
        cursor = conn.cursor()
        
        # Get index information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='action_plans'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # Verify expected indexes exist
        expected_indexes = [
            'idx_action_plans_queue_status',
            'idx_action_plans_risk_level',
            'idx_action_plans_approval_route',
            'idx_action_plans_transcript_id'
        ]
        
        for expected_index in expected_indexes:
            assert expected_index in indexes, f"Missing index: {expected_index}"