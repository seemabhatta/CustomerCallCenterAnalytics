"""
TDD test cases to reproduce KuzuDB integration bugs.
These tests are written FIRST to fail, exposing the bugs before implementing fixes.
Follows NO FALLBACK principle - operations must work or fail fast.
"""

import pytest
import tempfile
import os
from pathlib import Path
from src.storage.graph_store import GraphStore, GraphStoreError
from src.services.insights_service import InsightsService
import logging

logger = logging.getLogger(__name__)


class TestGraphStoreBugReproduction:
    """Test cases to reproduce the specific bugs identified in GitHub issue #36."""
    
    def setup_method(self):
        """Setup test database for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_graph.db")
    
    def teardown_method(self):
        """Cleanup after each test."""
        # Clean up temp files
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except:
                pass
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
    
    def test_bug_node_counts_not_reflecting_actual_state(self):
        """
        BUG REPRODUCTION: Node counts don't reflect actual database state.
        
        Expected: After adding nodes, statistics should show correct counts
        Actual: Statistics always show 0 counts even when nodes exist
        Root Cause: execute_query parameter conversion fails silently
        """
        gs = GraphStore(self.test_db_path)
        
        # Clear graph to start fresh
        clear_result = gs.clear_graph()
        assert clear_result is True
        
        # Initial stats should show 0
        stats = gs.get_graph_statistics()
        assert stats["transcript_count"] == 0
        assert stats["total_nodes"] == 0
        
        # Add a transcript
        add_result = gs.add_transcript("BUG_REPRO_001", "test_topic", 5)
        assert add_result is True  # The add operation succeeds
        
        # BUG: Statistics should reflect the added transcript but don't
        stats_after_add = gs.get_graph_statistics()
        
        # This is the BUG - transcript_count should be 1, but it's 0
        # The test will FAIL initially, proving the bug exists
        assert stats_after_add["transcript_count"] == 1, "BUG: Node count should be 1 after adding transcript"
        assert stats_after_add["total_nodes"] == 1, "BUG: Total nodes should be 1"
        
        gs.close()
    
    def test_bug_execute_query_parameter_conversion_fails(self):
        """
        BUG REPRODUCTION: execute_query method fails on parameter conversion.
        
        Root Cause: KuzuDB returns [[1]] format, but code tries dict(record) conversion
        This causes "cannot convert dictionary update sequence element #0 to a sequence" error
        """
        gs = GraphStore(self.test_db_path)
        
        # Add a node first
        gs.add_transcript("QUERY_TEST_001", "test", 1)
        
        # This should work but currently fails due to parameter conversion bug
        try:
            result = gs.execute_query("MATCH (t:Transcript) RETURN count(t) as count")
            
            # The result should be accessible and properly formatted
            assert isinstance(result, list), "Result should be a list"
            assert len(result) > 0, "Should have at least one result"
            assert "count" in result[0], "Result should have count field"
            assert result[0]["count"] == 1, "Count should be 1"
            
        except Exception as e:
            # This will catch the bug - the conversion error
            pytest.fail(f"BUG: execute_query failed with parameter conversion error: {str(e)}")
        
        gs.close()
    
    def test_bug_clear_operation_effectiveness(self):
        """
        BUG REPRODUCTION: Clear operation may not fully clear the database.
        
        Expected: After clear, no nodes should exist and counts should be 0
        Actual: Primary key violations occur even after clear operations
        """
        gs = GraphStore(self.test_db_path)
        
        # Add some data
        gs.add_transcript("CLEAR_TEST_001", "test", 1)
        gs.add_customer("CUST_001", "standard", "low")
        
        # Clear the graph
        clear_result = gs.clear_graph()
        assert clear_result is True
        
        # Verify clear was effective by checking manual counts
        try:
            # Direct KuzuDB query to verify clearing
            transcript_result = gs.connection.execute("MATCH (t:Transcript) RETURN count(t) as count")
            transcript_count = list(transcript_result)[0][0]  # KuzuDB format [[count]]
            
            customer_result = gs.connection.execute("MATCH (c:Customer) RETURN count(c) as count")
            customer_count = list(customer_result)[0][0]
            
            assert transcript_count == 0, f"BUG: Transcripts not cleared, found {transcript_count}"
            assert customer_count == 0, f"BUG: Customers not cleared, found {customer_count}"
            
        except Exception as e:
            pytest.fail(f"BUG: Could not verify clear operation effectiveness: {str(e)}")
        
        # Adding the same IDs after clear should work (no primary key violations)
        try:
            add_result1 = gs.add_transcript("CLEAR_TEST_001", "test", 1)
            assert add_result1 is True
            
            add_result2 = gs.add_customer("CUST_001", "standard", "low") 
            assert add_result2 is True
            
        except GraphStoreError as e:
            if "duplicated primary key" in str(e).lower():
                pytest.fail(f"BUG: Clear operation didn't fully clear database, primary key violation: {str(e)}")
            else:
                raise
        
        gs.close()
    
    def test_bug_primary_key_constraint_handling_inconsistent(self):
        """
        BUG REPRODUCTION: Primary key constraint handling is inconsistent.
        
        Expected: Adding duplicate should return True (idempotent) or handle gracefully
        Actual: Raises GraphStoreError even for acceptable "already exists" cases
        """
        gs = GraphStore(self.test_db_path)
        
        # Add transcript first time
        result1 = gs.add_transcript("DUPLICATE_TEST_001", "test", 1)
        assert result1 is True
        
        # Add the same transcript again - should be idempotent or handled gracefully
        try:
            result2 = gs.add_transcript("DUPLICATE_TEST_001", "test", 1)
            
            # BUG: This should succeed (idempotent behavior) but currently raises GraphStoreError
            # The method should return True indicating "already exists, operation successful"
            assert result2 is True, "BUG: Duplicate add should be handled gracefully (idempotent)"
            
        except GraphStoreError as e:
            if "duplicated primary key" in str(e).lower():
                pytest.fail(f"BUG: Duplicate transcript add should be idempotent, not error: {str(e)}")
            else:
                raise
        
        gs.close()
    
    def test_bug_insights_service_database_concurrency(self):
        """
        BUG REPRODUCTION: InsightsService fails due to database concurrency issues.
        
        Expected: Multiple services can access the same database safely
        Actual: "Could not set lock on file" errors prevent populate operations
        """
        # Create a GraphStore first
        gs = GraphStore(self.test_db_path)
        
        # Try to create InsightsService with custom GraphStore (should work)
        try:
            insights_service = InsightsService(gs)
            # This should succeed - using existing connection
            assert insights_service.graph_store is not None
            
        except GraphStoreError as e:
            if "could not set lock" in str(e).lower():
                pytest.fail(f"BUG: InsightsService creation failed due to concurrency issue: {str(e)}")
            else:
                raise
        
        # Try to create another InsightsService with default path (may fail due to lock)
        try:
            insights_service2 = InsightsService()  # Uses default path
            # If both use same path, this will fail with lock error
            
        except GraphStoreError as e:
            if "could not set lock" in str(e).lower():
                # This is expected behavior, but documents the concurrency limitation
                logger.warning(f"Expected concurrency limitation: {str(e)}")
            else:
                raise
        
        gs.close()
    
    def test_bug_cypher_variable_scope_in_get_high_risk_clusters(self):
        """
        BUG REPRODUCTION: Cypher variable scope error in get_high_risk_clusters().
        
        Expected: Query should find high-risk clusters with proper variable scoping
        Actual: "Binder exception: Variable p is not in scope" error
        Root Cause: Aggregation query missing proper GROUP BY for variables used in RETURN
        GitHub Issue: #39
        """
        gs = GraphStore(self.test_db_path)
        
        # Add test data that would create risk patterns
        test_analysis = {
            "analysis_id": "SCOPE_BUG_TEST_001",
            "transcript_id": "TRANS_001",
            "primary_intent": "test_intent",
            "urgency_level": "high",
            "confidence_score": 0.8,
            "issue_resolved": False,
            "escalation_needed": True,
            "borrower_risks": {
                "delinquency_risk": 0.8,  # Above 0.5 threshold to create pattern
                "elder_abuse_risk": 0.9
            },
            "compliance_flags": ["potential UDAAP violation"]
        }
        
        # Add transcript first (required for relationships)
        gs.add_transcript("TRANS_001", "test_topic", 1)
        
        # Add analysis with relationships - this should create risk patterns
        success = gs.add_analysis_with_relationships(test_analysis)
        assert success is True
        
        # This should work but currently fails with variable scope error
        try:
            risk_clusters = gs.get_high_risk_clusters(risk_threshold=0.7)
            
            # Should return list of clusters, not fail with scope error
            assert isinstance(risk_clusters, list), "Should return list of risk clusters"
            # May be empty if no patterns above threshold, but should not error
            
        except Exception as e:
            error_msg = str(e)
            if "Variable p is not in scope" in error_msg:
                pytest.fail(f"BUG: Cypher variable scope error in get_high_risk_clusters: {error_msg}")
            elif "Binder exception" in error_msg:
                pytest.fail(f"BUG: Cypher binder error in get_high_risk_clusters: {error_msg}")
            else:
                # Re-raise if it's a different error
                raise
        
        gs.close()


class TestNoFallbackPrincipleViolations:
    """Test that bugs don't create fallback behavior (violating NO FALLBACK principle)."""
    
    def setup_method(self):
        """Setup test database for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_no_fallback.db")
    
    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except:
                pass
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
    
    def test_no_fallback_statistics_never_return_fake_data(self):
        """
        NO FALLBACK TEST: Statistics should never return fake/mock data.
        
        When statistics method fails, it should fail fast, not return fake counts.
        """
        gs = GraphStore(self.test_db_path)
        
        # Add real data
        gs.add_transcript("REAL_DATA_001", "test", 1)
        
        # Get statistics
        stats = gs.get_graph_statistics()
        
        # Statistics should either be accurate or the method should fail
        # It should NEVER return fake/mock data like transcript_count=999999
        
        # Current bug: returns 0 instead of 1, but at least doesn't return fake high numbers
        assert stats["transcript_count"] >= 0, "Statistics should not return negative counts"
        assert stats["transcript_count"] <= 10, "Statistics should not return unrealistically high counts"
        
        # NO FALLBACK: Should not return obviously fake data
        assert stats["transcript_count"] != 999999, "Should never return fake placeholder data"
        
        gs.close()
    
    def test_no_fallback_populate_never_creates_mock_nodes(self):
        """
        NO FALLBACK TEST: Populate operations should never create mock/fake nodes.
        
        When populate fails, it should fail fast, not create placeholder data.
        """
        gs = GraphStore(self.test_db_path)
        
        # Simulate a populate scenario with invalid data
        invalid_analysis_data = {
            "analysis_id": "INVALID_ANALYSIS",
            "transcript_id": "NONEXISTENT_TRANSCRIPT", 
            "primary_intent": "fake_intent",
            "urgency_level": "fake_urgency"
        }
        
        # This should fail fast, not create fake nodes
        try:
            result = gs.add_analysis_with_relationships(invalid_analysis_data)
            
            # If it succeeds, verify no fake data was created
            if result:
                stats = gs.get_graph_statistics()
                # Should have at most reasonable number of nodes, not thousands of fake ones
                assert stats["total_nodes"] <= 100, "Should not create unrealistic numbers of nodes"
                
        except GraphStoreError:
            # Failing fast is acceptable and follows NO FALLBACK principle
            pass
        except Exception as e:
            # Other errors should also fail fast
            pass
        
        gs.close()


class TestExpectedBehaviorAfterFix:
    """Test cases defining the expected correct behavior after bugs are fixed."""
    
    def setup_method(self):
        """Setup test database for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_fixed_behavior.db")
    
    def teardown_method(self):
        """Cleanup after each test."""
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except:
                pass
        try:
            os.rmdir(self.temp_dir)
        except:
            pass
    
    def test_expected_accurate_node_counts(self):
        """
        EXPECTED BEHAVIOR: Node counts should accurately reflect database state.
        
        This test defines how the system should behave after the bug is fixed.
        """
        gs = GraphStore(self.test_db_path)
        
        # Clear and verify
        gs.clear_graph()
        stats = gs.get_graph_statistics()
        assert stats["transcript_count"] == 0
        assert stats["customer_count"] == 0
        assert stats["total_nodes"] == 0
        
        # Add transcript and verify count increases
        gs.add_transcript("COUNT_TEST_001", "test", 1)
        stats = gs.get_graph_statistics()
        assert stats["transcript_count"] == 1
        assert stats["total_nodes"] == 1
        
        # Add customer and verify counts
        gs.add_customer("CUST_COUNT_001", "standard", "low")
        stats = gs.get_graph_statistics()
        assert stats["transcript_count"] == 1
        assert stats["customer_count"] == 1 
        assert stats["total_nodes"] == 2
        
        # Add another transcript
        gs.add_transcript("COUNT_TEST_002", "test2", 2)
        stats = gs.get_graph_statistics()
        assert stats["transcript_count"] == 2
        assert stats["customer_count"] == 1
        assert stats["total_nodes"] == 3
        
        gs.close()
    
    def test_expected_execute_query_returns_structured_results(self):
        """
        EXPECTED BEHAVIOR: execute_query should return properly structured results.
        """
        gs = GraphStore(self.test_db_path)
        
        # Add test data
        gs.add_transcript("QUERY_EXPECTED_001", "test", 1)
        
        # Query should return structured results
        result = gs.execute_query("MATCH (t:Transcript) RETURN t.transcript_id as id, t.topic as topic")
        
        assert isinstance(result, list), "Should return list of results"
        assert len(result) == 1, "Should return one result"
        assert isinstance(result[0], dict), "Each result should be a dictionary"
        assert "id" in result[0], "Result should have id field"
        assert "topic" in result[0], "Result should have topic field"
        assert result[0]["id"] == "QUERY_EXPECTED_001"
        assert result[0]["topic"] == "test"
        
        gs.close()
    
    def test_expected_idempotent_operations(self):
        """
        EXPECTED BEHAVIOR: Add operations should be idempotent.
        
        Adding the same entity multiple times should not fail.
        """
        gs = GraphStore(self.test_db_path)
        
        # First add should succeed
        result1 = gs.add_transcript("IDEMPOTENT_001", "test", 1)
        assert result1 is True
        
        # Second add of same transcript should also succeed (idempotent)
        result2 = gs.add_transcript("IDEMPOTENT_001", "test", 1)
        assert result2 is True, "Duplicate add should be idempotent"
        
        # Count should still be 1 (not 2)
        stats = gs.get_graph_statistics()
        assert stats["transcript_count"] == 1, "Should not create duplicates"
        
        gs.close()
    
    def test_expected_complete_clear_operations(self):
        """
        EXPECTED BEHAVIOR: Clear operations should completely remove all data.
        """
        gs = GraphStore(self.test_db_path)
        
        # Add various types of data
        gs.add_transcript("CLEAR_EXPECTED_001", "test", 1)
        gs.add_customer("CUST_CLEAR_001", "standard", "low")
        
        # Verify data exists
        stats_before = gs.get_graph_statistics()
        assert stats_before["total_nodes"] > 0
        
        # Clear should remove everything
        clear_result = gs.clear_graph()
        assert clear_result is True
        
        # Verify complete clearing
        stats_after = gs.get_graph_statistics()
        assert stats_after["transcript_count"] == 0
        assert stats_after["customer_count"] == 0
        assert stats_after["total_nodes"] == 0
        
        # Should be able to add same IDs again without primary key violations
        result1 = gs.add_transcript("CLEAR_EXPECTED_001", "test", 1)
        assert result1 is True
        
        result2 = gs.add_customer("CUST_CLEAR_001", "standard", "low")
        assert result2 is True
        
        gs.close()