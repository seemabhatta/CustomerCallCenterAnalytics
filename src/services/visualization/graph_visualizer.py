"""Graph visualization using NetworkX and Plotly - NO FALLBACK principle."""
import networkx as nx
import plotly.graph_objects as go
import plotly.offline as pyo
from typing import Dict, Any, List, Tuple
import math
import os
from pathlib import Path


class GraphVisualizer:
    """Creates interactive graph visualizations using NetworkX and Plotly."""
    
    # Color scheme for different node types
    NODE_COLORS = {
        "Transcript": "#3498db",      # Blue
        "Analysis": "#2ecc71",        # Green  
        "RiskPattern": "#e74c3c",     # Red
        "ComplianceFlag": "#f39c12"   # Orange
    }
    
    def __init__(self):
        """Initialize the graph visualizer."""
        pass
    
    def create_network_graph(self, graph_data: Dict[str, Any]) -> go.Figure:
        """Create interactive network graph from KuzuDB data.
        
        Args:
            graph_data: Dict with 'nodes' and 'edges' lists
            
        Returns:
            Plotly Figure object
            
        Raises:
            ValueError: If data is empty or invalid (NO FALLBACK)
        """
        # Validate input data - NO FALLBACK
        if not graph_data:
            raise ValueError("Graph data is empty - cannot create visualization")
        
        if "nodes" not in graph_data or "edges" not in graph_data:
            raise ValueError("Graph data must contain 'nodes' and 'edges' keys")
        
        nodes = graph_data["nodes"] 
        edges = graph_data["edges"]
        
        if not nodes:
            raise ValueError("No nodes in graph data - cannot visualize empty graph")
        
        # Create NetworkX graph
        G = nx.DiGraph()
        
        # Add nodes with attributes
        for node in nodes:
            node_id = node["id"]
            G.add_node(node_id, **node)
        
        # Add edges
        for edge in edges:
            G.add_edge(edge["source"], edge["target"], 
                      relationship=edge["relationship"])
        
        # Generate layout using spring layout for better visualization
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Create edge traces
        edge_traces = self._create_edge_traces(G, pos)
        
        # Create node trace
        node_trace = self._create_node_trace(G, pos, nodes)
        
        # Combine traces
        traces = edge_traces + [node_trace]
        
        # Create figure
        fig = go.Figure(data=traces,
                       layout=go.Layout(
                           title=dict(text="Knowledge Graph Visualization", font=dict(size=16)),
                           showlegend=True,
                           hovermode='closest',
                           margin=dict(b=20,l=5,r=5,t=40),
                           annotations=[ dict(
                               text="Interactive graph visualization of call center analytics",
                               showarrow=False,
                               xref="paper", yref="paper",
                               x=0.005, y=-0.002,
                               xanchor='left', yanchor='bottom',
                               font=dict(color='#888', size=12)
                           )],
                           xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                           plot_bgcolor='white'
                       ))
        
        return fig
    
    def _create_edge_traces(self, G: nx.DiGraph, pos: Dict) -> List[go.Scatter]:
        """Create traces for graph edges with relationship labels."""
        edge_traces = []
        
        # Group edges by relationship type for different colors
        relationship_edges = {}
        for edge in G.edges(data=True):
            rel_type = edge[2].get("relationship", "UNKNOWN")
            if rel_type not in relationship_edges:
                relationship_edges[rel_type] = []
            relationship_edges[rel_type].append(edge)
        
        # Color scheme for relationships
        rel_colors = {
            "GENERATED_FROM": "#95a5a6",
            "HAS_RISK_PATTERN": "#e74c3c", 
            "HAS_COMPLIANCE_FLAG": "#f39c12",
            "UNKNOWN": "#7f8c8d"
        }
        
        for rel_type, edges in relationship_edges.items():
            edge_x = []
            edge_y = []
            
            for edge in edges:
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
            
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=2, color=rel_colors.get(rel_type, "#7f8c8d")),
                hoverinfo='none',
                mode='lines',
                name=rel_type,
                showlegend=True
            )
            edge_traces.append(edge_trace)
        
        return edge_traces
    
    def _create_node_trace(self, G: nx.DiGraph, pos: Dict, nodes: List[Dict]) -> go.Scatter:
        """Create trace for graph nodes with styling and hover info."""
        node_x = []
        node_y = []
        node_colors = []
        node_sizes = []
        node_text = []
        hover_text = []
        
        # Create lookup for node data
        node_lookup = {node["id"]: node for node in nodes}
        
        for node_id in G.nodes():
            x, y = pos[node_id]
            node_x.append(x)
            node_y.append(y)
            
            node_data = node_lookup.get(node_id, {})
            node_type = node_data.get("type", "Unknown")
            
            # Color by node type
            color = self.NODE_COLORS.get(node_type, "#95a5a6")
            node_colors.append(color)
            
            # Size by importance (risk/severity score)
            risk_score = node_data.get("risk_score", 0.0)
            severity_score = node_data.get("severity_score", 0.0)
            importance = max(risk_score, severity_score)
            
            # Base size 10, scale up to 30 based on importance
            size = 10 + (importance * 20)
            node_sizes.append(size)
            
            # Label text
            label = node_data.get("label", node_id)
            node_text.append(label)
            
            # Hover information
            hover_info = [f"<b>{label}</b>"]
            hover_info.append(f"Type: {node_type}")
            
            if node_data.get("description"):
                hover_info.append(f"Description: {node_data['description']}")
            
            if risk_score > 0:
                hover_info.append(f"Risk Score: {risk_score:.2f}")
                
            if severity_score > 0:
                hover_info.append(f"Severity Score: {severity_score:.2f}")
            
            # Connection info
            connections = len(list(G.neighbors(node_id))) + len(list(G.predecessors(node_id)))
            hover_info.append(f"Connections: {connections}")
            
            hover_text.append("<br>".join(hover_info))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_text,
            text=node_text,
            textposition="middle center",
            textfont=dict(size=8, color="white"),
            marker=dict(
                size=node_sizes,
                color=node_colors,
                line=dict(width=2, color="white")
            ),
            name="Nodes",
            showlegend=False
        )
        
        return node_trace
    
    def save_to_html(self, figure: go.Figure, output_path: str, 
                    auto_open: bool = False) -> None:
        """Save visualization to HTML file.
        
        Args:
            figure: Plotly figure to save
            output_path: Path for output HTML file
            auto_open: Whether to open file in browser
            
        Raises:
            ValueError: If invalid file path (NO FALLBACK)
        """
        try:
            # Validate output path
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # Save to HTML
            pyo.plot(figure, 
                    filename=output_path,
                    auto_open=auto_open,
                    config={'displayModeBar': True,
                           'toImageButtonOptions': {
                               'format': 'png',
                               'filename': 'knowledge_graph',
                               'height': 800,
                               'width': 1200,
                               'scale': 1
                           }})
            
        except Exception as e:
            raise ValueError(f"Failed to save visualization to {output_path}: {str(e)}")
    
    def get_graph_statistics(self, graph_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get basic statistics about the graph for display.
        
        Args:
            graph_data: Dict with 'nodes' and 'edges' lists
            
        Returns:
            Dict with graph statistics
        """
        if not graph_data or not graph_data.get("nodes"):
            return {"error": "No graph data available"}
        
        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        
        # Count by type
        type_counts = {}
        risk_scores = []
        severity_scores = []
        
        for node in nodes:
            node_type = node.get("type", "Unknown")
            type_counts[node_type] = type_counts.get(node_type, 0) + 1
            
            if node.get("risk_score", 0) > 0:
                risk_scores.append(node["risk_score"])
            if node.get("severity_score", 0) > 0:
                severity_scores.append(node["severity_score"])
        
        stats = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "node_types": type_counts,
            "avg_risk_score": sum(risk_scores) / len(risk_scores) if risk_scores else 0,
            "avg_severity_score": sum(severity_scores) / len(severity_scores) if severity_scores else 0,
            "high_risk_nodes": len([s for s in risk_scores if s > 0.7]),
            "high_severity_nodes": len([s for s in severity_scores if s > 0.7])
        }
        
        return stats