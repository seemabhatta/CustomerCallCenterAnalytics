"""Tests for ApprovalStore - Database operations for action approvals."""

import pytest
import tempfile
import os
from datetime import datetime, timedelta

from src.storage.approval_store import ApprovalStore


class TestApprovalStore:
    """Test cases for ApprovalStore functionality."""
    
    def setup_method(self):
        """Set up test fixtures with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.store = ApprovalStore(self.temp_db.name)
        
        # Sample approval data
        self.sample_approval = {
            'id': 'APPR_TEST_001',
            'plan_id': 'PLAN_TEST_001', 
            'action_id': 'ACT_BORR_SEND_EMAIL_001',
            'transcript_id': 'CALL_TEST_001',
            'analysis_id': 'ANALYSIS_TEST_001',
            'action_text': 'Send confirmation email to customer',
            'action_description': 'Standard confirmation email with next steps',
            'action_layer': 'borrower',
            'action_type': 'customer_communication',
            'risk_score': 0.25,
            'risk_level': 'low',
            'financial_impact': False,
            'compliance_impact': False,
            'customer_facing': True,
            'needs_approval': False,
            'approval_status': 'auto_approved',
            'approval_route': 'auto_approved',
            'approval_reason': 'Low risk action auto-approved',
            'decision_agent_version': 'v1.0'
        }
    
    def teardown_method(self):
        """Clean up temporary database."""
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_initialization_creates_schema(self):
        """Test that initialization creates proper database schema."""
        # Tables should exist after initialization
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Check action_approvals table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='action_approvals'")
        assert cursor.fetchone() is not None
        
        # Check approval_queue_metrics table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='approval_queue_metrics'")
        assert cursor.fetchone() is not None
        
        # Check indexes exist using PRAGMA which is more reliable
        cursor.execute("PRAGMA index_list(action_approvals)")
        indexes = cursor.fetchall()
        # Should have multiple indexes (including auto-created primary key index)
        assert len(indexes) >= 6
        
        conn.close()
    
    def test_store_action_approval(self):
        """Test storing an action approval."""
        approval_id = self.store.store_action_approval(self.sample_approval)
        
        assert approval_id == self.sample_approval['id']
        
        # Verify it was stored correctly
        stored_approval = self.store.get_approval_by_action_id(self.sample_approval['action_id'])
        
        assert stored_approval is not None
        assert stored_approval['action_text'] == self.sample_approval['action_text']
        assert stored_approval['risk_level'] == self.sample_approval['risk_level']
        assert stored_approval['approval_status'] == self.sample_approval['approval_status']
    
    def test_store_approval_upsert(self):
        """Test that storing updates existing approvals."""
        # Store initial approval
        self.store.store_action_approval(self.sample_approval)
        
        # Update and store again
        updated_approval = self.sample_approval.copy()
        updated_approval['approval_status'] = 'pending'
        updated_approval['approval_reason'] = 'Updated for testing'
        
        self.store.store_action_approval(updated_approval)
        
        # Should have updated, not created duplicate
        stored = self.store.get_approval_by_action_id(self.sample_approval['action_id'])
        assert stored['approval_status'] == 'pending'
        assert stored['approval_reason'] == 'Updated for testing'
    
    def test_get_approval_queue_empty(self):
        """Test getting approval queue when empty."""
        queue = self.store.get_approval_queue()
        assert queue == []
        
        # Test with specific route
        supervisor_queue = self.store.get_approval_queue('supervisor_approval')
        assert supervisor_queue == []
    
    def test_get_approval_queue_with_items(self):
        """Test getting approval queue with pending items."""
        # Store multiple approvals with different statuses and routes
        approvals = [
            {
                **self.sample_approval,
                'id': 'APPR_001',
                'action_id': 'ACT_001',
                'approval_status': 'pending',
                'approval_route': 'advisor_approval'
            },
            {
                **self.sample_approval,
                'id': 'APPR_002',
                'action_id': 'ACT_002',
                'approval_status': 'pending',
                'approval_route': 'supervisor_approval'
            },
            {
                **self.sample_approval,
                'id': 'APPR_003',
                'action_id': 'ACT_003',
                'approval_status': 'approved',
                'approval_route': 'supervisor_approval'
            }
        ]
        
        for approval in approvals:
            self.store.store_action_approval(approval)
        
        # Get all pending
        all_pending = self.store.get_approval_queue()
        assert len(all_pending) == 2  # Only pending items
        
        # Get supervisor pending only
        supervisor_pending = self.store.get_approval_queue('supervisor_approval')
        assert len(supervisor_pending) == 1
        assert supervisor_pending[0]['approval_route'] == 'supervisor_approval'
        assert supervisor_pending[0]['approval_status'] == 'pending'
    
    def test_approve_action(self):
        """Test approving an action."""
        # Store pending approval
        pending_approval = {
            **self.sample_approval,
            'approval_status': 'pending',
            'needs_approval': True
        }
        self.store.store_action_approval(pending_approval)
        
        # Approve it
        success = self.store.approve_action(
            self.sample_approval['action_id'], 
            'supervisor_jane', 
            'Approved after review'
        )
        
        assert success == True
        
        # Verify approval was recorded
        approved = self.store.get_approval_by_action_id(self.sample_approval['action_id'])
        assert approved['approval_status'] == 'approved'
        assert approved['approved_by'] == 'supervisor_jane'
        assert approved['approval_reason'] == 'Approved after review'
        assert approved['approved_at'] is not None
    
    def test_approve_nonexistent_action(self):
        """Test approving non-existent action returns False."""
        success = self.store.approve_action('NONEXISTENT_ACTION', 'supervisor', 'notes')
        assert success == False
    
    def test_reject_action(self):
        """Test rejecting an action."""
        # Store pending approval
        pending_approval = {
            **self.sample_approval,
            'approval_status': 'pending'
        }
        self.store.store_action_approval(pending_approval)
        
        # Reject it
        success = self.store.reject_action(
            self.sample_approval['action_id'],
            'supervisor_jane',
            'Insufficient documentation provided'
        )
        
        assert success == True
        
        # Verify rejection was recorded
        rejected = self.store.get_approval_by_action_id(self.sample_approval['action_id'])
        assert rejected['approval_status'] == 'rejected'
        assert rejected['approved_by'] == 'supervisor_jane'
        assert rejected['rejection_reason'] == 'Insufficient documentation provided'
        assert rejected['approved_at'] is not None
    
    def test_bulk_approve(self):
        """Test bulk approval of multiple actions."""
        # Store multiple pending approvals
        action_ids = ['ACT_BULK_001', 'ACT_BULK_002', 'ACT_BULK_003']
        
        for i, action_id in enumerate(action_ids):
            approval = {
                **self.sample_approval,
                'id': f'APPR_BULK_{i:03d}',
                'action_id': action_id,
                'approval_status': 'pending'
            }
            self.store.store_action_approval(approval)
        
        # Bulk approve
        approved_count = self.store.bulk_approve(
            action_ids,
            'supervisor_bulk',
            'Bulk approval for routine actions'
        )
        
        assert approved_count == 3
        
        # Verify all were approved
        for action_id in action_ids:
            approval = self.store.get_approval_by_action_id(action_id)
            assert approval['approval_status'] == 'approved'
            assert approval['approved_by'] == 'supervisor_bulk'
    
    def test_bulk_approve_partial_success(self):
        """Test bulk approval with some non-existent actions."""
        # Store only some of the approvals
        valid_action_ids = ['ACT_VALID_001', 'ACT_VALID_002']
        invalid_action_ids = ['ACT_INVALID_001']
        
        for i, action_id in enumerate(valid_action_ids):
            approval = {
                **self.sample_approval,
                'id': f'APPR_VALID_{i:03d}',  # Unique ID for each record
                'action_id': action_id,
                'approval_status': 'pending'
            }
            self.store.store_action_approval(approval)
        
        # Try to bulk approve both valid and invalid
        all_action_ids = valid_action_ids + invalid_action_ids
        approved_count = self.store.bulk_approve(all_action_ids, 'supervisor', 'bulk test')
        
        assert approved_count == 2  # Only valid ones approved
    
    def test_get_approvals_by_plan_id(self):
        """Test getting all approvals for a specific plan."""
        plan_id = 'PLAN_MULTI_001'
        
        # Store multiple approvals for the same plan
        for i in range(3):
            approval = {
                **self.sample_approval,
                'id': f'APPR_PLAN_{i:03d}',
                'action_id': f'ACT_PLAN_{i:03d}',
                'plan_id': plan_id
            }
            self.store.store_action_approval(approval)
        
        # Store one approval for different plan
        other_approval = {
            **self.sample_approval,
            'id': 'APPR_OTHER_001',
            'action_id': 'ACT_OTHER_001',
            'plan_id': 'PLAN_OTHER_001'
        }
        self.store.store_action_approval(other_approval)
        
        # Get approvals for specific plan
        plan_approvals = self.store.get_approvals_by_plan_id(plan_id)
        
        assert len(plan_approvals) == 3
        for approval in plan_approvals:
            assert approval['plan_id'] == plan_id
    
    def test_get_approval_metrics_empty(self):
        """Test approval metrics with no data."""
        metrics = self.store.get_approval_metrics()
        
        assert metrics['total_actions'] == 0
        assert metrics['pending_approvals'] == 0
        assert metrics['approval_rate'] == 0
        assert metrics['avg_approval_time_hours'] == 0
        assert 'queue_status' in metrics
        assert 'risk_distribution' in metrics
    
    def test_get_approval_metrics_with_data(self):
        """Test approval metrics with sample data."""
        # Store approvals with different statuses and risk levels
        test_data = [
            ('pending', 'supervisor_approval', 'high'),
            ('pending', 'advisor_approval', 'medium'),
            ('approved', 'supervisor_approval', 'high'),
            ('rejected', 'advisor_approval', 'low'),
            ('auto_approved', 'auto_approved', 'low')
        ]
        
        for i, (status, route, risk) in enumerate(test_data):
            approval = {
                **self.sample_approval,
                'id': f'APPR_METRICS_{i:03d}',
                'action_id': f'ACT_METRICS_{i:03d}',
                'approval_status': status,
                'approval_route': route,
                'risk_level': risk
            }
            self.store.store_action_approval(approval)
        
        metrics = self.store.get_approval_metrics()
        
        assert metrics['total_actions'] == 5
        assert metrics['pending_approvals'] == 2
        assert 'queue_status' in metrics
        assert 'risk_distribution' in metrics
        
        # Check risk distribution
        risk_dist = metrics['risk_distribution']
        assert risk_dist['high'] == 2
        assert risk_dist['medium'] == 1
        assert risk_dist['low'] == 2
    
    def test_delete_approval(self):
        """Test deleting an approval record."""
        # Store approval
        self.store.store_action_approval(self.sample_approval)
        
        # Verify it exists
        assert self.store.get_approval_by_action_id(self.sample_approval['action_id']) is not None
        
        # Delete it
        success = self.store.delete_approval(self.sample_approval['action_id'])
        assert success == True
        
        # Verify it's gone
        assert self.store.get_approval_by_action_id(self.sample_approval['action_id']) is None
    
    def test_delete_nonexistent_approval(self):
        """Test deleting non-existent approval returns False."""
        success = self.store.delete_approval('NONEXISTENT_ACTION')
        assert success == False
    
    def test_delete_all_approvals(self):
        """Test deleting all approval records."""
        # Store multiple approvals
        for i in range(5):
            approval = {
                **self.sample_approval,
                'id': f'APPR_DELETE_ALL_{i:03d}',
                'action_id': f'ACT_DELETE_ALL_{i:03d}'
            }
            self.store.store_action_approval(approval)
        
        # Verify they exist
        queue = self.store.get_approval_queue()
        # Note: these are auto-approved, so won't be in pending queue
        # Check metrics instead
        metrics = self.store.get_approval_metrics()
        assert metrics['total_actions'] == 5
        
        # Delete all
        deleted_count = self.store.delete_all_approvals()
        assert deleted_count == 5
        
        # Verify all gone
        metrics_after = self.store.get_approval_metrics()
        assert metrics_after['total_actions'] == 0
    
    def test_database_indexes_performance(self):
        """Test that database indexes exist for performance."""
        import sqlite3
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        
        # Check that key indexes exist using PRAGMA (more reliable)
        cursor.execute("PRAGMA index_list(action_approvals)")
        indexes = cursor.fetchall()
        
        # Extract index names (format: [(seq, name, unique, origin, partial), ...])
        index_names = [idx[1] for idx in indexes]
        
        # Should have indexes on key columns (note: sqlite auto-creates primary key index)
        expected_indexes = [
            'idx_approval_status',
            'idx_approval_route', 
            'idx_needs_approval',
            'idx_plan_id',
            'idx_action_id',
            'idx_risk_level'
        ]
        
        for expected_idx in expected_indexes:
            assert expected_idx in index_names, f"Index {expected_idx} not found in {index_names}"
        
        conn.close()
    
    def test_approval_timing_calculation(self):
        """Test approval timing calculation for metrics."""
        # Create approval with known timing
        approval = {
            **self.sample_approval,
            'approval_status': 'pending'
        }
        self.store.store_action_approval(approval)
        
        # Approve it after a delay (simulate approval time)
        success = self.store.approve_action(
            self.sample_approval['action_id'],
            'supervisor_test',
            'Timing test approval'
        )
        assert success
        
        # Get metrics - should calculate average approval time
        metrics = self.store.get_approval_metrics()
        
        # Should have calculated some approval time (even if very small)
        assert 'avg_approval_time_hours' in metrics
        assert metrics['avg_approval_time_hours'] >= 0
    
    def test_concurrent_approval_operations(self):
        """Test concurrent approval operations don't conflict."""
        # This is a basic test - in production you'd want more sophisticated concurrency testing
        
        # Store approval with pending status
        pending_approval = {
            **self.sample_approval,
            'approval_status': 'pending',
            'needs_approval': True
        }
        self.store.store_action_approval(pending_approval)
        
        # Try to approve and reject simultaneously (simulate race condition)
        # In real scenario, only one should succeed due to SQL constraints
        approve_success = self.store.approve_action(self.sample_approval['action_id'], 'approver', 'notes')
        reject_success = self.store.reject_action(self.sample_approval['action_id'], 'rejector', 'reason')
        
        # One operation should succeed, one should fail (action no longer pending)
        assert (approve_success and not reject_success) or (reject_success and not approve_success)
    
    def test_approval_status_transitions(self):
        """Test valid approval status transitions."""
        approval = {
            **self.sample_approval,
            'approval_status': 'pending'
        }
        self.store.store_action_approval(approval)
        
        # pending -> approved
        success = self.store.approve_action(self.sample_approval['action_id'], 'supervisor', 'approved')
        assert success
        
        # Try to reject already approved action (should fail)
        reject_success = self.store.reject_action(self.sample_approval['action_id'], 'supervisor', 'reason')
        assert not reject_success
        
        # Verify final state
        final_state = self.store.get_approval_by_action_id(self.sample_approval['action_id'])
        assert final_state['approval_status'] == 'approved'