"""
Test suite for FastAPI endpoints (Epic 13)
Tests all core business API endpoints with TDD approach.
"""
import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Import the FastAPI app
from server import create_fastapi_app

@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    app = create_fastapi_app()
    return TestClient(app)

@pytest.fixture
def sample_transcript_id():
    """Sample transcript ID for testing."""
    return "CALL_TEST123"

@pytest.fixture
def sample_analysis_id():
    """Sample analysis ID for testing."""
    return "analysis_test_456"

@pytest.fixture
def sample_plan_id():
    """Sample plan ID for testing."""
    return "plan_test_789"

@pytest.fixture
def sample_execution_id():
    """Sample execution ID for testing."""
    return "exec_test_abc"

# ===============================================
# ANALYSIS API TESTS (5 endpoints)
# ===============================================

class TestAnalysisAPI:
    """Test Analysis API endpoints."""
    
    def test_analyze_transcript_endpoint(self, client, sample_transcript_id):
        """Test POST /api/v1/analysis/analyze endpoint."""
        payload = {
            "transcript_id": sample_transcript_id,
            "options": {"include_risk_scores": True}
        }
        
        with patch('src.analyzers.call_analyzer.CallAnalyzer') as mock_analyzer:
            mock_analyzer.return_value.analyze.return_value = {
                "analysis_id": "analysis_123",
                "intent": "PMI Removal",
                "urgency": "high",
                "sentiment": "concerned",
                "confidence": 0.95
            }
            
            response = client.post("/api/v1/analysis/analyze", json=payload)
            
        assert response.status_code == 200
        result = response.json()
        assert "analysis_id" in result
        assert result["intent"] == "PMI Removal"
        assert result["urgency"] == "high"
    
    def test_analyze_multiple_transcripts_endpoint(self, client):
        """Test POST /api/v1/analysis/analyze with multiple transcripts."""
        payload = {
            "transcript_ids": ["CALL_1", "CALL_2", "CALL_3"],
            "batch": True
        }
        
        response = client.post("/api/v1/analysis/analyze", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert "analyses" in result
        assert len(result["analyses"]) == 3
    
    def test_get_analysis_by_id_endpoint(self, client, sample_analysis_id):
        """Test GET /api/v1/analysis/{id} endpoint."""
        response = client.get(f"/api/v1/analysis/{sample_analysis_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert "analysis_id" in result
        assert "intent" in result
        assert "sentiment" in result
        assert "risk_scores" in result
    
    def test_get_analysis_metrics_endpoint(self, client):
        """Test GET /api/v1/analysis/metrics endpoint."""
        response = client.get("/api/v1/analysis/metrics")
        
        assert response.status_code == 200
        result = response.json()
        assert "total_analyses" in result
        assert "average_confidence" in result
        assert "resolution_rate" in result
        assert "risk_distribution" in result
    
    def test_get_analysis_report_endpoint(self, client, sample_analysis_id):
        """Test GET /api/v1/analysis/report/{id} endpoint."""
        response = client.get(f"/api/v1/analysis/report/{sample_analysis_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert "call_summary" in result
        assert "borrower_profile" in result
        assert "advisor_performance" in result
        assert "compliance_flags" in result
    
    def test_get_risk_report_endpoint(self, client):
        """Test GET /api/v1/analysis/risk-report endpoint."""
        response = client.get("/api/v1/analysis/risk-report?threshold=0.7")
        
        assert response.status_code == 200
        result = response.json()
        assert "high_risk_borrowers" in result
        assert "risk_categories" in result
        assert "total_count" in result

# ===============================================
# ACTION PLAN API TESTS (5 endpoints)
# ===============================================

class TestActionPlanAPI:
    """Test Action Plan API endpoints."""
    
    def test_generate_plan_endpoint(self, client, sample_transcript_id):
        """Test POST /api/v1/plans/generate endpoint."""
        payload = {
            "transcript_id": sample_transcript_id,
            "analysis_id": None,
            "options": {"include_leadership_layer": True}
        }
        
        response = client.post("/api/v1/plans/generate", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert "plan_id" in result
        assert "risk_level" in result
        assert "approval_route" in result
        assert "total_actions" in result
        assert result["total_actions"] > 0
    
    def test_get_plan_details_endpoint(self, client, sample_plan_id):
        """Test GET /api/v1/plans/{id} endpoint."""
        response = client.get(f"/api/v1/plans/{sample_plan_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert "plan_id" in result
        assert "borrower_plan" in result
        assert "advisor_plan" in result
        assert "supervisor_plan" in result
        assert "leadership_plan" in result
    
    def test_get_plan_details_by_layer_endpoint(self, client, sample_plan_id):
        """Test GET /api/v1/plans/{id}?layer=borrower endpoint."""
        response = client.get(f"/api/v1/plans/{sample_plan_id}?layer=borrower")
        
        assert response.status_code == 200
        result = response.json()
        assert "immediate_actions" in result
        assert "follow_ups" in result
        assert "personalized_offers" in result
    
    def test_get_approval_queue_endpoint(self, client):
        """Test GET /api/v1/plans/queue endpoint."""
        response = client.get("/api/v1/plans/queue")
        
        assert response.status_code == 200
        result = response.json()
        assert "queue_items" in result
        assert "total_count" in result
        assert "status_distribution" in result
    
    def test_get_approval_queue_filtered_endpoint(self, client):
        """Test GET /api/v1/plans/queue?status=pending_supervisor endpoint."""
        response = client.get("/api/v1/plans/queue?status=pending_supervisor")
        
        assert response.status_code == 200
        result = response.json()
        assert "queue_items" in result
        # All items should have status pending_supervisor
        for item in result["queue_items"]:
            assert item["status"] == "pending_supervisor"
    
    def test_approve_plan_endpoint(self, client, sample_plan_id):
        """Test PUT /api/v1/plans/{id}/approve endpoint."""
        payload = {
            "approved_by": "supervisor_test",
            "notes": "Approved for testing",
            "decision": "approve"
        }
        
        response = client.put(f"/api/v1/plans/{sample_plan_id}/approve", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "approved"
        assert result["approved_by"] == "supervisor_test"
        assert "approval_timestamp" in result
    
    def test_get_planning_summary_endpoint(self, client):
        """Test GET /api/v1/plans/summary endpoint."""
        response = client.get("/api/v1/plans/summary")
        
        assert response.status_code == 200
        result = response.json()
        assert "total_plans" in result
        assert "pending_approvals" in result
        assert "auto_executable_percentage" in result
        assert "risk_distribution" in result

# ===============================================
# EXECUTION API TESTS (5 endpoints)
# ===============================================

class TestExecutionAPI:
    """Test Execution API endpoints."""
    
    def test_execute_plan_endpoint(self, client, sample_plan_id):
        """Test POST /api/v1/execution/{plan_id} endpoint."""
        payload = {
            "mode": "auto",
            "dry_run": False,
            "options": {"generate_artifacts": True}
        }
        
        response = client.post(f"/api/v1/execution/{sample_plan_id}", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert "execution_id" in result
        assert "status" == "success" in result.values()
        assert "total_actions_executed" in result
        assert "artifacts_created" in result
    
    def test_execute_plan_dry_run_endpoint(self, client, sample_plan_id):
        """Test POST /api/v1/execution/{plan_id} with dry_run=true."""
        payload = {
            "mode": "auto",
            "dry_run": True
        }
        
        response = client.post(f"/api/v1/execution/{sample_plan_id}", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert "preview" in result
        assert "would_execute" in result
        assert "estimated_artifacts" in result
    
    def test_get_execution_status_endpoint(self, client, sample_execution_id):
        """Test GET /api/v1/execution/{id} endpoint."""
        response = client.get(f"/api/v1/execution/{sample_execution_id}")
        
        assert response.status_code == 200
        result = response.json()
        assert "execution_id" in result
        assert "status" in result
        assert "plan_id" in result
        assert "executed_at" in result
        assert "action_results" in result
    
    def test_get_execution_history_endpoint(self, client):
        """Test GET /api/v1/execution/history endpoint."""
        response = client.get("/api/v1/execution/history?limit=10")
        
        assert response.status_code == 200
        result = response.json()
        assert "executions" in result
        assert "total_count" in result
        assert len(result["executions"]) <= 10
    
    def test_get_execution_artifacts_endpoint(self, client):
        """Test GET /api/v1/execution/artifacts endpoint."""
        response = client.get("/api/v1/execution/artifacts?type=emails&limit=20")
        
        assert response.status_code == 200
        result = response.json()
        assert "artifacts" in result
        assert "total_count" in result
        assert "artifact_type" in result
        assert result["artifact_type"] == "emails"
    
    def test_get_execution_metrics_endpoint(self, client):
        """Test GET /api/v1/execution/metrics endpoint."""
        response = client.get("/api/v1/execution/metrics")
        
        assert response.status_code == 200
        result = response.json()
        assert "total_executions" in result
        assert "success_rate" in result
        assert "artifacts_created" in result
        assert "actions_by_source" in result
        assert "status_breakdown" in result

# ===============================================
# APPROVAL API TESTS (5 endpoints)
# ===============================================

class TestApprovalAPI:
    """Test Approval API endpoints."""
    
    def test_get_approval_queue_endpoint(self, client):
        """Test GET /api/v1/approvals/queue endpoint."""
        response = client.get("/api/v1/approvals/queue")
        
        assert response.status_code == 200
        result = response.json()
        assert "pending_actions" in result
        assert "total_count" in result
        assert "route_distribution" in result
    
    def test_get_approval_queue_filtered_endpoint(self, client):
        """Test GET /api/v1/approvals/queue?route=supervisor_approval endpoint."""
        response = client.get("/api/v1/approvals/queue?route=supervisor_approval")
        
        assert response.status_code == 200
        result = response.json()
        assert "pending_actions" in result
        # All actions should require supervisor approval
        for action in result["pending_actions"]:
            assert action["approval_route"] == "supervisor_approval"
    
    def test_approve_action_endpoint(self, client):
        """Test POST /api/v1/approvals/{id}/approve endpoint."""
        action_id = "action_test_123"
        payload = {
            "approved_by": "supervisor_test",
            "notes": "Approved for customer retention"
        }
        
        response = client.post(f"/api/v1/approvals/{action_id}/approve", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "approved"
        assert result["approved_by"] == "supervisor_test"
        assert "approval_timestamp" in result
    
    def test_reject_action_endpoint(self, client):
        """Test POST /api/v1/approvals/{id}/reject endpoint."""
        action_id = "action_test_456"
        payload = {
            "rejected_by": "supervisor_test",
            "reason": "Requires additional customer verification"
        }
        
        response = client.post(f"/api/v1/approvals/{action_id}/reject", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "rejected"
        assert result["rejected_by"] == "supervisor_test"
        assert result["reason"] == "Requires additional customer verification"
    
    def test_bulk_approve_endpoint(self, client):
        """Test POST /api/v1/approvals/bulk endpoint."""
        payload = {
            "action_ids": ["action_1", "action_2", "action_3"],
            "approved_by": "manager_test",
            "notes": "Weekly batch approval session"
        }
        
        response = client.post("/api/v1/approvals/bulk", json=payload)
        
        assert response.status_code == 200
        result = response.json()
        assert "approved_count" in result
        assert "failed_count" in result
        assert result["approved_count"] == 3
        assert result["failed_count"] == 0
    
    def test_get_approval_metrics_endpoint(self, client):
        """Test GET /api/v1/approvals/metrics endpoint."""
        response = client.get("/api/v1/approvals/metrics")
        
        assert response.status_code == 200
        result = response.json()
        assert "total_actions" in result
        assert "pending_approvals" in result
        assert "approval_rate" in result
        assert "avg_approval_time" in result
        assert "queue_status" in result
        assert "risk_distribution" in result

# ===============================================
# ERROR HANDLING TESTS
# ===============================================

class TestErrorHandling:
    """Test API error handling."""
    
    def test_not_found_transcript(self, client):
        """Test 404 for non-existent transcript."""
        response = client.get("/api/v1/analysis/nonexistent_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_invalid_plan_id(self, client):
        """Test 404 for non-existent plan."""
        response = client.get("/api/v1/plans/invalid_plan_id")
        assert response.status_code == 404
    
    def test_unauthorized_approval(self, client):
        """Test unauthorized approval attempt."""
        payload = {"approved_by": "", "notes": ""}
        response = client.post("/api/v1/approvals/action_123/approve", json=payload)
        assert response.status_code == 400
    
    def test_invalid_json_payload(self, client):
        """Test invalid JSON in request body."""
        response = client.post("/api/v1/analysis/analyze", data="invalid json")
        assert response.status_code == 422

# ===============================================
# PERFORMANCE TESTS
# ===============================================

class TestPerformance:
    """Test API performance requirements."""
    
    def test_analysis_response_time(self, client, sample_transcript_id):
        """Test analysis endpoint response time < 500ms."""
        import time
        
        payload = {"transcript_id": sample_transcript_id}
        
        start_time = time.time()
        response = client.post("/api/v1/analysis/analyze", json=payload)
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        assert response_time_ms < 500, f"Response time {response_time_ms}ms exceeds 500ms limit"
    
    def test_metrics_response_time(self, client):
        """Test metrics endpoint response time < 500ms."""
        import time
        
        start_time = time.time()
        response = client.get("/api/v1/execution/metrics")
        end_time = time.time()
        
        response_time_ms = (end_time - start_time) * 1000
        assert response_time_ms < 500, f"Response time {response_time_ms}ms exceeds 500ms limit"

# ===============================================
# INTEGRATION TESTS
# ===============================================

class TestIntegration:
    """Test complete workflow integration."""
    
    def test_complete_api_workflow(self, client):
        """Test complete workflow: generate → analyze → plan → approve → execute."""
        # Step 1: Generate transcript (using existing endpoint)
        generate_payload = {
            "scenario": "PMI Removal Test",
            "urgency": "high",
            "financial_impact": True
        }
        generate_response = client.post("/generate", json=generate_payload)
        assert generate_response.status_code == 200
        transcript_id = generate_response.json()["transcripts"][0]["id"]
        
        # Step 2: Analyze transcript
        analyze_payload = {"transcript_id": transcript_id}
        analyze_response = client.post("/api/v1/analysis/analyze", json=analyze_payload)
        assert analyze_response.status_code == 200
        analysis_id = analyze_response.json()["analysis_id"]
        
        # Step 3: Generate action plan
        plan_payload = {"transcript_id": transcript_id, "analysis_id": analysis_id}
        plan_response = client.post("/api/v1/plans/generate", json=plan_payload)
        assert plan_response.status_code == 200
        plan_id = plan_response.json()["plan_id"]
        
        # Step 4: Approve plan
        approve_payload = {"approved_by": "test_supervisor", "decision": "approve"}
        approve_response = client.put(f"/api/v1/plans/{plan_id}/approve", json=approve_payload)
        assert approve_response.status_code == 200
        
        # Step 5: Execute plan
        execute_payload = {"mode": "auto", "dry_run": False}
        execute_response = client.post(f"/api/v1/execution/{plan_id}", json=execute_payload)
        assert execute_response.status_code == 200
        
        # Verify workflow completion
        execution_id = execute_response.json()["execution_id"]
        status_response = client.get(f"/api/v1/execution/{execution_id}")
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "success"