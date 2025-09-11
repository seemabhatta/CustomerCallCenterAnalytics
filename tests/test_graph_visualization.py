"""Tests for graph visualization data extraction from KuzuDB."""
import pytest
from unittest.mock import Mock, patch
from src.storage.graph_store import GraphStore


class TestGraphVisualizationDataExtraction:
    """Test data extraction for graph visualization - NO FALLBACK principle."""
    
    def test_get_graph_for_visualization_with_data(self):
        """Test getting graph data when graph contains nodes and edges."""
        graph_store = GraphStore(":memory:")
        
        # Setup test data 
        graph_store.add_transcript("TRANS_001", "Elder abuse concern", 5)
        analysis_data = {
            "analysis_id": "ANALYSIS_001",
            "transcript_id": "TRANS_001",
            "summary": "Test analysis",
            "risk_assessment": "High risk elder abuse",
            "risk_score": 0.8,
            "borrower_risks": {"elder_abuse": 0.8},
            "compliance_flags": ["ELDER_ABUSE|Potential elder abuse detected"]
        }
        graph_store.add_analysis_with_relationships(analysis_data)
        
        # Test the method
        result = graph_store.get_graph_for_visualization()
        
        # Assertions
        assert isinstance(result, dict)
        assert "nodes" in result
        assert "edges" in result
        assert len(result["nodes"]) > 0
        assert len(result["edges"]) > 0
        
        # Check node structure
        node = result["nodes"][0]
        assert "id" in node
        assert "label" in node
        assert "type" in node
        
        # Check edge structure
        edge = result["edges"][0]
        assert "source" in edge
        assert "target" in edge
        assert "relationship" in edge
    
    def test_get_graph_for_visualization_empty_graph_fails_fast(self):
        """Test that empty graph fails fast - NO FALLBACK."""
        graph_store = GraphStore(":memory:")
        
        # Should raise exception for empty graph - NO FALLBACK
        with pytest.raises(Exception) as excinfo:
            graph_store.get_graph_for_visualization()
        
        assert "No data" in str(excinfo.value) or "empty" in str(excinfo.value).lower()
    
    def test_node_types_correctly_identified(self):
        """Test that different node types are correctly identified."""
        graph_store = GraphStore(":memory:")
        
        # Add different types of nodes
        graph_store.add_transcript("TRANS_001", "Test topic", 3)
        analysis_data = {
            "analysis_id": "ANALYSIS_001", 
            "transcript_id": "TRANS_001",
            "summary": "Test summary",
            "risk_assessment": "Medium risk",
            "risk_score": 0.6,
            "borrower_risks": {"delinquency_risk": 0.6},
            "compliance_flags": ["GENERAL_COMPLIANCE|Test flag"]
        }
        graph_store.add_analysis_with_relationships(analysis_data)
        
        result = graph_store.get_graph_for_visualization()
        
        # Check that we have different node types
        node_types = {node["type"] for node in result["nodes"]}
        expected_types = {"Transcript", "Analysis", "RiskPattern", "ComplianceFlag"}
        assert node_types == expected_types
    
    def test_relationships_properly_extracted(self):
        """Test that relationships between nodes are properly extracted."""
        graph_store = GraphStore(":memory:")
        
        graph_store.add_transcript("TRANS_001", "Test topic", 3)
        analysis_data = {
            "analysis_id": "ANALYSIS_001",
            "transcript_id": "TRANS_001", 
            "summary": "Test summary",
            "risk_assessment": "High risk",
            "risk_score": 0.8,
            "borrower_risks": {"complaint_risk": 0.8},
            "compliance_flags": ["UDAAP_VIOLATION|Test violation"]
        }
        graph_store.add_analysis_with_relationships(analysis_data)
        
        result = graph_store.get_graph_for_visualization()
        
        # Check relationship types
        relationship_types = {edge["relationship"] for edge in result["edges"]}
        expected_relationships = {"GENERATED_FROM", "HAS_RISK_PATTERN", "HAS_COMPLIANCE_FLAG"}
        assert relationship_types.issubset(expected_relationships)
    
    def test_data_structure_for_visualization(self):
        """Test that data structure is suitable for visualization libraries."""
        graph_store = GraphStore(":memory:")
        
        graph_store.add_transcript("TRANS_001", "Test", 2)
        analysis_data = {
            "analysis_id": "ANALYSIS_001",
            "transcript_id": "TRANS_001",
            "summary": "Test",
            "risk_assessment": "Low risk", 
            "risk_score": 0.3,
            "borrower_risks": {"refinance_likelihood": 0.3},
            "compliance_flags": []
        }
        graph_store.add_analysis_with_relationships(analysis_data)
        
        result = graph_store.get_graph_for_visualization()
        
        # Validate structure for NetworkX/Plotly compatibility
        assert isinstance(result, dict)
        assert isinstance(result["nodes"], list)
        assert isinstance(result["edges"], list)
        
        # Each node should have required fields
        for node in result["nodes"]:
            assert isinstance(node["id"], str)
            assert isinstance(node["label"], str) 
            assert isinstance(node["type"], str)
            # Optional fields that visualization can use
            if "risk_score" in node:
                assert isinstance(node["risk_score"], (int, float))
            if "severity_score" in node:
                assert isinstance(node["severity_score"], (int, float))
        
        # Each edge should have required fields
        for edge in result["edges"]:
            assert isinstance(edge["source"], str)
            assert isinstance(edge["target"], str)
            assert isinstance(edge["relationship"], str)