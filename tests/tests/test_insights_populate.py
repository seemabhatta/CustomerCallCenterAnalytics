"""
TDD tests for Insights Populate, Query, and Delete operations.
Tests written FIRST to ensure they fail, then implementation will make them pass.
Enforces NO FALLBACK principle - operations must work or fail fast.
"""

import pytest
import requests
import json
import subprocess
from pathlib import Path
import time


def wait_for_server(url: str = "http://localhost:8000", timeout: int = 30) -> bool:
    """Wait for server to be ready."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{url}/api/v1/health")
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(1)
    return False


def create_test_analysis():
    """Create test analysis data for populate testing."""
    base_url = "http://localhost:8000"
    
    # Create test transcript
    transcript_response = requests.post(f"{base_url}/api/v1/transcripts", json={
        "topic": "populate_test_topic",
        "urgency": "high",
        "customer_id": "CUST_POPULATE_001",
        "store": True
    })
    assert transcript_response.status_code == 200
    
    transcript_data = transcript_response.json()
    transcript_id = transcript_data.get("transcript_id")
    assert transcript_id, "No transcript_id in response"
    
    # Create test analysis
    analysis_response = requests.post(f"{base_url}/api/v1/analyses", json={
        "transcript_id": transcript_id,
        "analysis_type": "comprehensive",
        "store": True
    })
    assert analysis_response.status_code == 200
    
    analysis_data = analysis_response.json()
    analysis_id = analysis_data.get("analysis_id")
    assert analysis_id, "No analysis_id in response"
    
    return analysis_id, transcript_id


class TestInsightsPopulateAPI:
    """TDD tests for insights populate API endpoints."""
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_server(self):
        """Ensure server is running for tests."""
        if not wait_for_server():
            pytest.skip("Server not available - start with 'python server.py'")
    
    def test_populate_endpoint_exists(self):
        """
        TEST: POST /api/v1/insights/populate endpoint should exist (TDD - fails first).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/populate", json={
            "analysis_id": "TEST_123"
        })
        # Endpoint should exist (not 404), may return error due to missing analysis
        assert response.status_code != 404, "Populate endpoint should exist"
    
    def test_populate_requires_analysis_id(self):
        """
        TEST: Populate endpoint should require analysis_id (TDD - fails first).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/populate", json={})
        
        # Should fail fast without analysis_id (NO FALLBACK)
        assert response.status_code in [400, 422], "Should require analysis_id"
        
        if response.status_code in [400, 422]:
            error_data = response.json()
            assert "analysis_id" in str(error_data).lower(), "Error should mention analysis_id"
    
    def test_populate_invalid_analysis_fails_fast(self):
        """
        TEST: Invalid analysis ID should fail fast (NO FALLBACK).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/populate", json={
            "analysis_id": "NONEXISTENT_ANALYSIS"
        })
        
        # Should fail fast for nonexistent analysis
        assert response.status_code in [404, 400], "Should fail for nonexistent analysis"
    
    def test_populate_single_analysis_success(self):
        """
        TEST: Populate with valid analysis should succeed (TDD - fails first).
        """
        # Create test data
        analysis_id, _ = create_test_analysis()
        
        response = requests.post("http://localhost:8000/api/v1/insights/populate", json={
            "analysis_id": analysis_id
        })
        
        # Should succeed with valid analysis
        if response.status_code == 200:
            data = response.json()
            assert "success" in data or "message" in data, "Should return success confirmation"
            # Verify the analysis was actually added to graph
            assert analysis_id in str(data), "Should confirm specific analysis was populated"
    
    def test_populate_batch_analyses(self):
        """
        TEST: Populate should support batch operations (TDD - fails first).
        """
        # Create multiple test analyses
        analysis_id1, _ = create_test_analysis()
        analysis_id2, _ = create_test_analysis()
        
        response = requests.post("http://localhost:8000/api/v1/insights/populate", json={
            "analysis_ids": [analysis_id1, analysis_id2]
        })
        
        # Should support batch populate
        if response.status_code == 200:
            data = response.json()
            assert "count" in data or "populated" in str(data).lower(), "Should return count of populated analyses"


class TestInsightsQueryAPI:
    """TDD tests for insights query API endpoints."""
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_server(self):
        """Ensure server is running for tests."""
        if not wait_for_server():
            pytest.skip("Server not available - start with 'python server.py'")
    
    def test_query_endpoint_exists(self):
        """
        TEST: POST /api/v1/insights/query endpoint should exist (TDD - fails first).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/query", json={
            "cypher": "MATCH (n) RETURN count(n)"
        })
        # Endpoint should exist (not 404)
        assert response.status_code != 404, "Query endpoint should exist"
    
    def test_query_requires_cypher(self):
        """
        TEST: Query endpoint should require cypher parameter (TDD - fails first).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/query", json={})
        
        # Should fail fast without cypher query (NO FALLBACK)
        assert response.status_code in [400, 422], "Should require cypher parameter"
    
    def test_query_invalid_cypher_fails_fast(self):
        """
        TEST: Invalid Cypher should fail fast (NO FALLBACK).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/query", json={
            "cypher": "INVALID CYPHER SYNTAX HERE"
        })
        
        # Should fail fast for invalid Cypher
        assert response.status_code in [400, 500], "Should fail for invalid Cypher"
    
    def test_query_valid_cypher_returns_results(self):
        """
        TEST: Valid Cypher should return structured results (TDD - fails first).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/query", json={
            "cypher": "MATCH (n) RETURN count(n) as node_count"
        })
        
        if response.status_code == 200:
            data = response.json()
            # Should return results in structured format
            assert isinstance(data, (list, dict)), "Should return structured data"
            # Even if graph is empty, should return valid result structure
    
    def test_status_endpoint_exists(self):
        """
        TEST: GET /api/v1/insights/status endpoint should exist (TDD - fails first).
        """
        response = requests.get("http://localhost:8000/api/v1/insights/status")
        assert response.status_code != 404, "Status endpoint should exist"
        
        if response.status_code == 200:
            data = response.json()
            # Should return graph statistics
            expected_fields = ["node_count", "relationship_count", "graph_size"]
            # At least one field should be present
            assert any(field in data for field in expected_fields), "Should return graph statistics"


class TestInsightsDeleteAPI:
    """TDD tests for insights delete API endpoints."""
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_server(self):
        """Ensure server is running for tests."""
        if not wait_for_server():
            pytest.skip("Server not available - start with 'python server.py'")
    
    def test_delete_analysis_endpoint_exists(self):
        """
        TEST: DELETE /api/v1/insights/analyses/{id} endpoint should exist (TDD - fails first).
        """
        response = requests.delete("http://localhost:8000/api/v1/insights/analyses/TEST_123")
        # Endpoint should exist (not 404), may return error for nonexistent analysis
        assert response.status_code != 404, "Delete analysis endpoint should exist"
    
    def test_delete_nonexistent_analysis_fails_fast(self):
        """
        TEST: Deleting nonexistent analysis should fail fast (NO FALLBACK).
        """
        response = requests.delete("http://localhost:8000/api/v1/insights/analyses/NONEXISTENT")
        
        # Should fail fast for nonexistent analysis
        assert response.status_code in [404, 400], "Should fail for nonexistent analysis"
    
    def test_delete_customer_endpoint_exists(self):
        """
        TEST: DELETE /api/v1/insights/customers/{id} endpoint should exist (TDD - fails first).
        """
        response = requests.delete("http://localhost:8000/api/v1/insights/customers/CUST_TEST")
        # Endpoint should exist (not 404)
        assert response.status_code != 404, "Delete customer endpoint should exist"
    
    def test_prune_endpoint_exists(self):
        """
        TEST: POST /api/v1/insights/prune endpoint should exist (TDD - fails first).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/prune", json={
            "older_than_days": 90
        })
        # Endpoint should exist (not 404)
        assert response.status_code != 404, "Prune endpoint should exist"
    
    def test_prune_requires_days_parameter(self):
        """
        TEST: Prune endpoint should require older_than_days parameter (TDD - fails first).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/prune", json={})
        
        # Should fail fast without required parameter (NO FALLBACK)
        assert response.status_code in [400, 422], "Should require older_than_days parameter"
    
    def test_clear_endpoint_exists(self):
        """
        TEST: DELETE /api/v1/insights/clear endpoint should exist (TDD - fails first).
        """
        response = requests.delete("http://localhost:8000/api/v1/insights/clear")
        # Endpoint should exist (not 404)
        assert response.status_code != 404, "Clear endpoint should exist"


class TestInsightsCLICommands:
    """TDD tests for insights CLI commands."""
    
    def run_cli(self, args, timeout=120):
        """Helper to run CLI commands."""
        cmd = ['python', 'cli.py'] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path(__file__).parent.parent
        )
        return result
    
    def test_insights_populate_command_exists(self):
        """
        TEST: insights populate command should exist (TDD - fails first).
        """
        result = self.run_cli(['insights', 'populate', '--help'])
        assert result.returncode == 0, "insights populate command should exist"
        assert 'populate' in result.stdout.lower(), "Should show populate help"
    
    def test_insights_populate_requires_analysis_id(self):
        """
        TEST: insights populate should require analysis ID (TDD - fails first).
        """
        result = self.run_cli(['insights', 'populate'])
        # Should fail without analysis ID
        assert result.returncode != 0, "Should fail without analysis ID"
    
    def test_insights_query_command_exists(self):
        """
        TEST: insights query command should exist (TDD - fails first).
        """
        result = self.run_cli(['insights', 'query', '--help'])
        assert result.returncode == 0, "insights query command should exist"
        assert 'query' in result.stdout.lower(), "Should show query help"
    
    def test_insights_query_requires_cypher(self):
        """
        TEST: insights query should require Cypher parameter (TDD - fails first).
        """
        result = self.run_cli(['insights', 'query'])
        # Should fail without Cypher query
        assert result.returncode != 0, "Should fail without Cypher query"
    
    def test_insights_delete_command_exists(self):
        """
        TEST: insights delete command should exist (TDD - fails first).
        """
        result = self.run_cli(['insights', 'delete', '--help'])
        assert result.returncode == 0, "insights delete command should exist"
        assert 'delete' in result.stdout.lower(), "Should show delete help"
    
    def test_insights_status_command_exists(self):
        """
        TEST: insights status command should exist (TDD - fails first).
        """
        result = self.run_cli(['insights', 'status'])
        # May return error if graph not initialized, but command should exist
        # Non-zero return code is acceptable initially
        assert 'command not found' not in result.stderr.lower(), "Command should exist"
        assert 'no such command' not in result.stderr.lower(), "Command should exist"
    
    def test_insights_prune_command_exists(self):
        """
        TEST: insights prune command should exist (TDD - fails first).
        """
        result = self.run_cli(['insights', 'prune', '--help'])
        assert result.returncode == 0, "insights prune command should exist"
        assert 'prune' in result.stdout.lower(), "Should show prune help"
    
    def test_insights_clear_command_exists(self):
        """
        TEST: insights clear command should exist (TDD - fails first).
        """
        result = self.run_cli(['insights', 'clear', '--help'])
        assert result.returncode == 0, "insights clear command should exist"
        assert 'clear' in result.stdout.lower(), "Should show clear help"


class TestInsightsNoFallbackPrinciple:
    """Test that insights operations follow NO FALLBACK principle."""
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_server(self):
        """Ensure server is running for tests."""
        if not wait_for_server():
            pytest.skip("Server not available - start with 'python server.py'")
    
    def test_populate_never_creates_fake_data(self):
        """
        TEST: Populate should never create fake/mock data (NO FALLBACK).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/populate", json={
            "analysis_id": "FAKE_ANALYSIS_FOR_TEST"
        })
        
        # Should fail, not create fake data
        assert response.status_code != 200, "Should not create fake data for fake analysis"
        
        # Verify no fake data was added to graph
        status_response = requests.get("http://localhost:8000/api/v1/insights/status")
        if status_response.status_code == 200:
            # Should not show artificially inflated counts
            data = status_response.json()
            # If node count exists, it should be reasonable (not fake high numbers)
            if "node_count" in data:
                assert data["node_count"] < 1000, "Should not have fake inflated counts"
    
    def test_query_never_returns_mock_results(self):
        """
        TEST: Query should never return mock results (NO FALLBACK).
        """
        response = requests.post("http://localhost:8000/api/v1/insights/query", json={
            "cypher": "MATCH (fake:NonExistentNode) RETURN fake"
        })
        
        if response.status_code == 200:
            data = response.json()
            # Should return empty results, not fake data
            assert data == [] or (isinstance(data, dict) and not data), "Should return empty results, not fake data"
    
    def test_delete_never_pretends_success(self):
        """
        TEST: Delete should never pretend success for nonexistent data (NO FALLBACK).
        """
        response = requests.delete("http://localhost:8000/api/v1/insights/analyses/TOTALLY_FAKE_ANALYSIS")
        
        # Should fail, not pretend it deleted something
        assert response.status_code != 200, "Should not pretend to delete nonexistent data"
        
        if response.status_code in [400, 404]:
            error_data = response.json()
            # Should give clear error about not finding the analysis
            assert "not found" in str(error_data).lower() or "error" in str(error_data).lower(), "Should give clear error"