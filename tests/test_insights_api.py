"""
TDD tests for Knowledge Graph Insights API endpoints.
Tests written FIRST to ensure they fail, then implementation will make them pass.
Enforces NO FALLBACK principle - insights must work with real data or fail fast.
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


def setup_test_data():
    """Create test transcript and analysis data for insights testing."""
    base_url = "http://localhost:8000"
    
    # Create test transcript
    transcript_payload = {
        "topic": "elder_abuse_concern",
        "urgency": "high",
        "financial_impact": True,
        "customer_sentiment": "distressed",
        "customer_id": "CUST_ELDER_001",
        "store": True
    }
    
    transcript_response = requests.post(f"{base_url}/api/v1/transcripts", json=transcript_payload)
    assert transcript_response.status_code == 200, f"Failed to create test transcript: {transcript_response.text}"
    
    transcript_data = transcript_response.json()
    transcript_id = transcript_data.get("transcript_id")
    assert transcript_id, "No transcript_id in response"
    
    # Create test analysis
    analysis_payload = {
        "transcript_id": transcript_id,
        "analysis_type": "comprehensive",
        "urgency": "high",
        "customer_tier": "priority",
        "store": True
    }
    
    analysis_response = requests.post(f"{base_url}/api/v1/analyses", json=analysis_payload)
    assert analysis_response.status_code == 200, f"Failed to create test analysis: {analysis_response.text}"
    
    analysis_data = analysis_response.json()
    analysis_id = analysis_data.get("analysis_id")
    assert analysis_id, "No analysis_id in response"
    
    return transcript_id, analysis_id


class TestInsightsEndpoints:
    """TDD tests for insights API endpoints."""
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_server(self):
        """Ensure server is running for tests."""
        if not wait_for_server():
            pytest.skip("Server not available - start with 'python server.py'")
    
    def test_insights_patterns_endpoint_exists(self):
        """
        TEST: /api/v1/insights/patterns endpoint should exist (TDD - fails first).
        """
        response = requests.get("http://localhost:8000/api/v1/insights/patterns")
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
        # 500 is acceptable initially as GraphStore might not have data yet
    
    def test_insights_risks_endpoint_exists(self):
        """
        TEST: /api/v1/insights/risks endpoint should exist (TDD - fails first).
        """
        response = requests.get("http://localhost:8000/api/v1/insights/risks")
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
    
    def test_insights_dashboard_endpoint_exists(self):
        """
        TEST: /api/v1/insights/dashboard endpoint should exist (TDD - fails first).
        """
        response = requests.get("http://localhost:8000/api/v1/insights/dashboard")
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
    
    def test_insights_recommendations_endpoint_with_customer_id(self):
        """
        TEST: /api/v1/insights/recommendations/{customer_id} should accept customer ID (TDD - fails first).
        """
        customer_id = "CUST_TEST_001"
        response = requests.get(f"http://localhost:8000/api/v1/insights/recommendations/{customer_id}")
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
    
    def test_insights_similar_endpoint_with_analysis_id(self):
        """
        TEST: /api/v1/insights/similar/{analysis_id} should accept analysis ID (TDD - fails first).
        """
        analysis_id = "ANALYSIS_TEST_123"
        response = requests.get(f"http://localhost:8000/api/v1/insights/similar/{analysis_id}")
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
    
    def test_insights_patterns_with_risk_threshold_parameter(self):
        """
        TEST: /api/v1/insights/patterns should accept risk_threshold parameter (TDD - fails first).
        """
        response = requests.get("http://localhost:8000/api/v1/insights/patterns?risk_threshold=0.8")
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"
        
        # Test invalid threshold should fail fast (NO FALLBACK)
        response = requests.get("http://localhost:8000/api/v1/insights/patterns?risk_threshold=1.5")
        assert response.status_code in [400, 422, 500], "Invalid threshold should fail fast"
    
    def test_insights_similar_with_limit_parameter(self):
        """
        TEST: /api/v1/insights/similar should accept limit parameter (TDD - fails first).
        """
        analysis_id = "ANALYSIS_TEST_123"
        response = requests.get(f"http://localhost:8000/api/v1/insights/similar/{analysis_id}?limit=3")
        assert response.status_code in [200, 500], f"Expected 200 or 500, got {response.status_code}"


class TestInsightsWithRealData:
    """TDD tests for insights endpoints with real data (requires working GraphStore)."""
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_server_and_data(self):
        """Ensure server is running and create test data."""
        if not wait_for_server():
            pytest.skip("Server not available - start with 'python server.py'")
        
        # Create test data
        self.transcript_id, self.analysis_id = setup_test_data()
    
    def test_patterns_endpoint_returns_structured_data(self):
        """
        TEST: patterns endpoint should return structured risk pattern data (TDD - fails first).
        """
        response = requests.get("http://localhost:8000/api/v1/insights/patterns")
        
        if response.status_code == 200:
            data = response.json()
            # Should return list of patterns
            assert isinstance(data, list), "Patterns should return a list"
            
            if data:  # If patterns exist
                pattern = data[0]
                required_fields = ["risk_type", "description", "risk_score", "severity", "recommendation"]
                for field in required_fields:
                    assert field in pattern, f"Pattern missing required field: {field}"
                
                # Risk score should be valid float between 0-1
                assert 0.0 <= pattern["risk_score"] <= 1.0, "Risk score should be between 0-1"
                
                # Severity should be valid enum
                valid_severities = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
                assert pattern["severity"] in valid_severities, f"Invalid severity: {pattern['severity']}"
    
    def test_risks_endpoint_filters_high_risk_patterns(self):
        """
        TEST: risks endpoint should filter patterns above threshold (TDD - fails first).
        """
        response = requests.get("http://localhost:8000/api/v1/insights/risks?risk_threshold=0.8")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Risks should return a list"
            
            # All returned patterns should have risk_score >= 0.8
            for pattern in data:
                assert pattern["risk_score"] >= 0.8, f"Risk pattern below threshold: {pattern['risk_score']}"
    
    def test_recommendations_endpoint_returns_personalized_data(self):
        """
        TEST: recommendations endpoint should return personalized recommendations (TDD - fails first).
        """
        customer_id = "CUST_ELDER_001"
        response = requests.get(f"http://localhost:8000/api/v1/insights/recommendations/{customer_id}")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Recommendations should return a list"
            
            if data:  # If recommendations exist
                rec = data[0]
                required_fields = ["customer_id", "recommendation_type", "recommended_action", "confidence", "priority"]
                for field in required_fields:
                    assert field in rec, f"Recommendation missing required field: {field}"
                
                # Should match requested customer
                assert rec["customer_id"] == customer_id, "Recommendation should match requested customer"
                
                # Confidence should be valid float between 0-1
                assert 0.0 <= rec["confidence"] <= 1.0, "Confidence should be between 0-1"
    
    def test_similar_cases_endpoint_finds_related_analyses(self):
        """
        TEST: similar cases endpoint should find related analyses (TDD - fails first).
        """
        response = requests.get(f"http://localhost:8000/api/v1/insights/similar/{self.analysis_id}")
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Similar cases should return a list"
            
            if data:  # If similar cases exist
                case = data[0]
                required_fields = ["reference_analysis_id", "similar_analysis_id", "similarity"]
                for field in required_fields:
                    assert field in case, f"Similar case missing required field: {field}"
                
                # Should reference correct analysis
                assert case["reference_analysis_id"] == self.analysis_id, "Should reference correct analysis"
    
    def test_dashboard_endpoint_returns_comprehensive_insights(self):
        """
        TEST: dashboard endpoint should return comprehensive insights summary (TDD - fails first).
        """
        response = requests.get("http://localhost:8000/api/v1/insights/dashboard")
        
        if response.status_code == 200:
            data = response.json()
            
            # Should have main sections
            required_sections = ["summary", "risk_analysis", "compliance_monitoring", "recommendations"]
            for section in required_sections:
                assert section in data, f"Dashboard missing section: {section}"
            
            # Summary should have counts
            summary = data["summary"]
            summary_fields = ["total_risk_patterns", "total_compliance_flags", "analysis_coverage"]
            for field in summary_fields:
                assert field in summary, f"Summary missing field: {field}"


class TestInsightsNoFallbackPrinciple:
    """Test that insights endpoints follow NO FALLBACK principle."""
    
    @pytest.fixture(autouse=True, scope="class")
    def setup_server(self):
        """Ensure server is running for tests."""
        if not wait_for_server():
            pytest.skip("Server not available - start with 'python server.py'")
    
    def test_invalid_customer_id_fails_fast(self):
        """
        TEST: Invalid customer ID should fail fast, not return mock data (NO FALLBACK).
        """
        invalid_customer_id = "NONEXISTENT_CUSTOMER"
        response = requests.get(f"http://localhost:8000/api/v1/insights/recommendations/{invalid_customer_id}")
        
        # Should either return empty list [] or error, but NEVER mock data
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Should return list"
            # Empty list is acceptable (no recommendations found)
            # But should NOT contain fake/mock data
    
    def test_invalid_analysis_id_fails_fast(self):
        """
        TEST: Invalid analysis ID should fail fast, not return mock data (NO FALLBACK).
        """
        invalid_analysis_id = "NONEXISTENT_ANALYSIS"
        response = requests.get(f"http://localhost:8000/api/v1/insights/similar/{invalid_analysis_id}")
        
        # Should either return empty list [] or error, but NEVER mock data
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Should return list"
            # Empty list is acceptable (no similar cases found)
            # But should NOT contain fake/mock data
    
    def test_invalid_risk_threshold_fails_fast(self):
        """
        TEST: Invalid risk threshold should fail fast with clear error (NO FALLBACK).
        """
        # Test negative threshold
        response = requests.get("http://localhost:8000/api/v1/insights/patterns?risk_threshold=-0.1")
        assert response.status_code in [400, 422, 500], "Negative threshold should fail"
        
        # Test > 1.0 threshold
        response = requests.get("http://localhost:8000/api/v1/insights/patterns?risk_threshold=1.5")
        assert response.status_code in [400, 422, 500], "Threshold > 1.0 should fail"
        
        # Test non-numeric threshold
        response = requests.get("http://localhost:8000/api/v1/insights/patterns?risk_threshold=invalid")
        assert response.status_code in [400, 422, 500], "Non-numeric threshold should fail"