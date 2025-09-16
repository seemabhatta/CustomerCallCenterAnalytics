"""Tests for graph visualizer using NetworkX and Plotly."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
from pathlib import Path


class TestGraphVisualizer:
    """Test NetworkX and Plotly graph visualization - NO FALLBACK principle."""
    
    def test_create_network_graph_with_valid_data(self):
        """Test creating NetworkX graph from valid KuzuDB data."""
        from src.services.visualization.graph_visualizer import GraphVisualizer
        
        # Mock graph data structure
        graph_data = {
            "nodes": [
                {"id": "TRANS_001", "label": "Elder abuse call", "type": "Transcript"},
                {"id": "ANALYSIS_001", "label": "High risk analysis", "type": "Analysis", "risk_score": 0.8},
                {"id": "RISK_001", "label": "Elder abuse pattern", "type": "RiskPattern", "risk_score": 0.8},
                {"id": "FLAG_001", "label": "ELDER_ABUSE flag", "type": "ComplianceFlag", "severity_score": 0.9}
            ],
            "edges": [
                {"source": "ANALYSIS_001", "target": "TRANS_001", "relationship": "GENERATED_FROM"},
                {"source": "ANALYSIS_001", "target": "RISK_001", "relationship": "HAS_RISK_PATTERN"},
                {"source": "ANALYSIS_001", "target": "FLAG_001", "relationship": "HAS_COMPLIANCE_FLAG"}
            ]
        }
        
        visualizer = GraphVisualizer()
        figure = visualizer.create_network_graph(graph_data)
        
        # Check that we get a Plotly figure
        assert figure is not None
        assert hasattr(figure, 'data')
        assert hasattr(figure, 'layout')
        
        # Should have scatter plots for nodes and lines for edges
        assert len(figure.data) >= 2  # At least nodes and edges
    
    def test_create_network_graph_fails_fast_with_empty_data(self):
        """Test that empty data fails fast - NO FALLBACK."""
        from src.services.visualization.graph_visualizer import GraphVisualizer
        
        empty_data = {"nodes": [], "edges": []}
        visualizer = GraphVisualizer()
        
        with pytest.raises(ValueError) as excinfo:
            visualizer.create_network_graph(empty_data)
        
        assert "empty" in str(excinfo.value).lower() or "no data" in str(excinfo.value).lower()
    
    def test_create_network_graph_fails_fast_with_invalid_data(self):
        """Test that invalid data structure fails fast - NO FALLBACK."""
        from src.services.visualization.graph_visualizer import GraphVisualizer
        
        invalid_data = {"invalid": "structure"}
        visualizer = GraphVisualizer()
        
        with pytest.raises(ValueError) as excinfo:
            visualizer.create_network_graph(invalid_data)
        
        assert "nodes" in str(excinfo.value) or "edges" in str(excinfo.value)
    
    def test_node_styling_by_type(self):
        """Test that nodes are styled differently by type."""
        from src.services.visualization.graph_visualizer import GraphVisualizer
        
        graph_data = {
            "nodes": [
                {"id": "TRANS_001", "label": "Call transcript", "type": "Transcript"},
                {"id": "ANALYSIS_001", "label": "Risk analysis", "type": "Analysis", "risk_score": 0.7},
                {"id": "RISK_001", "label": "Risk pattern", "type": "RiskPattern", "risk_score": 0.8},
                {"id": "FLAG_001", "label": "Compliance flag", "type": "ComplianceFlag", "severity_score": 0.6}
            ],
            "edges": [
                {"source": "ANALYSIS_001", "target": "TRANS_001", "relationship": "GENERATED_FROM"}
            ]
        }
        
        visualizer = GraphVisualizer()
        figure = visualizer.create_network_graph(graph_data)
        
        # Check that we have node styling (colors should be different for different types)
        node_trace = None
        for trace in figure.data:
            if hasattr(trace, 'mode') and 'markers' in str(trace.mode):
                node_trace = trace
                break
        
        assert node_trace is not None
        assert hasattr(node_trace, 'marker')
        # Colors should be assigned (not all the same)
        if hasattr(node_trace.marker, 'color') and len(node_trace.marker.color) > 1:
            colors = node_trace.marker.color
            # Should have different colors for different node types
            assert len(set(colors)) > 1
    
    def test_node_sizing_by_importance(self):
        """Test that nodes are sized based on risk/severity scores."""
        from src.services.visualization.graph_visualizer import GraphVisualizer
        
        graph_data = {
            "nodes": [
                {"id": "ANALYSIS_001", "label": "Low risk", "type": "Analysis", "risk_score": 0.2},
                {"id": "ANALYSIS_002", "label": "High risk", "type": "Analysis", "risk_score": 0.9},
                {"id": "RISK_001", "label": "Medium risk pattern", "type": "RiskPattern", "risk_score": 0.5}
            ],
            "edges": []
        }
        
        visualizer = GraphVisualizer()
        figure = visualizer.create_network_graph(graph_data)
        
        # Find node trace
        node_trace = None
        for trace in figure.data:
            if hasattr(trace, 'mode') and 'markers' in str(trace.mode):
                node_trace = trace
                break
        
        assert node_trace is not None
        # Sizes should be different based on scores
        if hasattr(node_trace.marker, 'size'):
            sizes = node_trace.marker.size
            # Should have different sizes for different risk scores
            assert len(set(sizes)) > 1
    
    def test_save_to_html(self):
        """Test saving visualization to HTML file."""
        from src.services.visualization.graph_visualizer import GraphVisualizer
        
        # Create a mock figure
        mock_figure = MagicMock()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_graph.html")
            
            # Mock plotly.offline.plot
            with patch('plotly.offline.plot') as mock_plot:
                visualizer = GraphVisualizer()
                visualizer.save_to_html(mock_figure, output_path)
                
                # Should call plotly.offline.plot
                mock_plot.assert_called_once()
                args, kwargs = mock_plot.call_args
                assert mock_figure == args[0]
                assert kwargs['filename'] == output_path
                assert kwargs['auto_open'] is False
    
    def test_save_to_html_fails_fast_invalid_path(self):
        """Test that invalid file path fails fast - NO FALLBACK."""
        from src.services.visualization.graph_visualizer import GraphVisualizer
        
        mock_figure = MagicMock()
        invalid_path = "/nonexistent/directory/graph.html"
        
        visualizer = GraphVisualizer()
        
        with pytest.raises(Exception) as excinfo:
            visualizer.save_to_html(mock_figure, invalid_path)
        
        # Should fail with a clear error about the path
        assert "path" in str(excinfo.value).lower() or "directory" in str(excinfo.value).lower()
    
    def test_hover_information_included(self):
        """Test that hover information is included in the visualization.""" 
        from src.services.visualization.graph_visualizer import GraphVisualizer
        
        graph_data = {
            "nodes": [
                {"id": "ANALYSIS_001", "label": "Test analysis", "type": "Analysis", 
                 "risk_score": 0.8, "summary": "High risk customer call"}
            ],
            "edges": []
        }
        
        visualizer = GraphVisualizer()
        figure = visualizer.create_network_graph(graph_data)
        
        # Find node trace
        node_trace = None
        for trace in figure.data:
            if hasattr(trace, 'mode') and 'markers' in str(trace.mode):
                node_trace = trace
                break
        
        assert node_trace is not None
        # Should have hover text with node information
        assert hasattr(node_trace, 'hovertext') or hasattr(node_trace, 'text')
    
    def test_edge_labels_included(self):
        """Test that edge relationships are labeled."""
        from src.services.visualization.graph_visualizer import GraphVisualizer
        
        graph_data = {
            "nodes": [
                {"id": "TRANS_001", "label": "Transcript", "type": "Transcript"},
                {"id": "ANALYSIS_001", "label": "Analysis", "type": "Analysis"}
            ],
            "edges": [
                {"source": "ANALYSIS_001", "target": "TRANS_001", "relationship": "GENERATED_FROM"}
            ]
        }
        
        visualizer = GraphVisualizer()
        figure = visualizer.create_network_graph(graph_data)
        
        # Should have traces for edges with relationship information
        edge_traces = [trace for trace in figure.data 
                      if hasattr(trace, 'mode') and 'lines' in str(trace.mode)]
        assert len(edge_traces) >= 1