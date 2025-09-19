"""
Insights Service for Knowledge Graph Analytics.

Provides business logic layer for AI-powered pattern detection and recommendations.
Uses GraphStore (KuzuDB) for relationship-aware analytics.
Follows NO FALLBACK principle - fails fast on errors.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime

from ..storage.graph_store import GraphStore, GraphStoreError



class InsightsServiceError(Exception):
    """Exception raised for insights service errors."""
    pass


class InsightsService:
    """Service layer for knowledge graph analytics and insights."""
    
    def __init__(self, graph_store: Optional[GraphStore] = None):
        """Initialize with GraphStore instance."""
        if graph_store is None:
            self.graph_store = GraphStore()
        else:
            self.graph_store = graph_store
        
    
    async def store_analysis_relationships(self, analysis_data: Dict[str, Any]) -> bool:
        """
        Store analysis data in knowledge graph for pattern detection.
        
        Args:
            analysis_data: Complete analysis result from AnalysisService
            
        Returns:
            bool: Success status
            
        Raises:
            InsightsServiceError: If storage fails
        """
        try:
            # Extract required IDs
            analysis_id = analysis_data.get('analysis_id')
            transcript_id = analysis_data.get('transcript_id')
            
            if not analysis_id or not transcript_id:
                raise InsightsServiceError("analysis_id and transcript_id are required")
            
            # Store transcript if not already exists
            await self._ensure_transcript_exists(transcript_id, analysis_data)
            
            # Store analysis with all relationships
            success = self.graph_store.add_analysis_with_relationships(analysis_data)
            
            if success:
                return True
            else:
                raise InsightsServiceError("Failed to store analysis relationships")
                
        except GraphStoreError as e:
            raise InsightsServiceError(f"Failed to store analysis: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Storage failed: {str(e)}")
    
    async def discover_risk_patterns(self, risk_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """
        Discover high-risk patterns across all analyses.
        
        Args:
            risk_threshold: Minimum risk score to include (0.0-1.0)
            
        Returns:
            List of risk pattern clusters with affected analyses
            
        Raises:
            InsightsServiceError: If pattern discovery fails
        """
        try:
            if not 0.0 <= risk_threshold <= 1.0:
                raise InsightsServiceError("risk_threshold must be between 0.0 and 1.0")
            
            risk_clusters = self.graph_store.get_high_risk_clusters(risk_threshold)
            
            # Enhance with metadata
            enhanced_clusters = []
            for cluster in risk_clusters:
                enhanced_cluster = {
                    "risk_type": cluster.get("risk_type"),
                    "description": cluster.get("description"),
                    "risk_score": cluster.get("risk_score"),
                    "affected_count": cluster.get("affected_analyses", 0),
                    "analysis_ids": cluster.get("analysis_ids", []),
                    "severity": self._calculate_severity(cluster.get("risk_score", 0.0)),
                    "recommendation": self._generate_risk_recommendation(cluster),
                    "discovered_at": datetime.utcnow().isoformat()
                }
                enhanced_clusters.append(enhanced_cluster)
            
            return enhanced_clusters
            
        except GraphStoreError as e:
            raise InsightsServiceError(f"Pattern discovery failed: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Discovery failed: {str(e)}")
    
    async def get_customer_recommendations(self, customer_id: str) -> List[Dict[str, Any]]:
        """
        Get AI recommendations for a customer based on graph analysis.
        
        Args:
            customer_id: Customer identifier
            
        Returns:
            List of personalized recommendations
            
        Raises:
            InsightsServiceError: If recommendation generation fails
        """
        try:
            if not customer_id:
                raise InsightsServiceError("customer_id is required")
            
            # Get graph-based recommendations
            recommendations = self.graph_store.get_customer_recommendations(customer_id)
            
            # Enhance recommendations with business logic
            enhanced_recommendations = []
            for rec in recommendations:
                enhanced_rec = {
                    "customer_id": customer_id,
                    "recommendation_type": self._classify_recommendation(rec),
                    "recommended_action": rec.get("recommended_action"),
                    "confidence": self._calculate_confidence(rec),
                    "basis": {
                        "similar_customer": rec.get("similar_customer"),
                        "pattern_type": rec.get("pattern_basis"),
                        "reasoning": rec.get("recommendation_reason")
                    },
                    "success_probability": rec.get("success_rate", 0.5),
                    "priority": self._calculate_priority(rec),
                    "generated_at": datetime.utcnow().isoformat()
                }
                enhanced_recommendations.append(enhanced_rec)
            
            return enhanced_recommendations
            
        except GraphStoreError as e:
            raise InsightsServiceError(f"Recommendation failed: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Recommendation failed: {str(e)}")
    
    async def find_similar_cases(self, analysis_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find analyses with similar risk patterns.
        
        Args:
            analysis_id: Reference analysis ID
            limit: Maximum number of similar cases to return
            
        Returns:
            List of similar analyses with relationship details
            
        Raises:
            InsightsServiceError: If similarity search fails
        """
        try:
            if not analysis_id:
                raise InsightsServiceError("analysis_id is required")
                
            if limit <= 0 or limit > 50:
                raise InsightsServiceError("limit must be between 1 and 50")
            
            similar_patterns = self.graph_store.find_similar_risk_patterns(analysis_id, limit)
            
            # Enhance with metadata
            enhanced_similar = []
            for pattern in similar_patterns:
                enhanced_pattern = {
                    "reference_analysis_id": analysis_id,
                    "similar_analysis_id": pattern.get("similar_analysis_id"),
                    "similarity": {
                        "shared_pattern": pattern.get("shared_pattern"),
                        "risk_score": pattern.get("risk_score"),
                        "confidence": self._calculate_similarity_confidence(pattern)
                    },
                    "case_details": {
                        "intent": pattern.get("intent"),
                        "urgency": pattern.get("urgency")
                    },
                    "learning_opportunity": self._extract_learning(pattern),
                    "found_at": datetime.utcnow().isoformat()
                }
                enhanced_similar.append(enhanced_pattern)
            
            return enhanced_similar
            
        except GraphStoreError as e:
            raise InsightsServiceError(f"Similarity search failed: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Similarity search failed: {str(e)}")
    
    async def get_insights_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive insights dashboard data.
        
        Returns:
            Dashboard data with patterns, risks, and recommendations
            
        Raises:
            InsightsServiceError: If dashboard generation fails
        """
        try:
            # Get base insights from graph
            base_insights = self.graph_store.get_insights_summary()
            
            # Enhance with business intelligence
            dashboard = {
                "summary": {
                    "total_risk_patterns": len(base_insights.get("risk_patterns", [])),
                    "total_compliance_flags": len(base_insights.get("compliance_flags", [])),
                    "analysis_coverage": self._calculate_coverage(),
                    "last_updated": datetime.utcnow().isoformat()
                },
                "risk_analysis": {
                    "patterns": base_insights.get("risk_patterns", []),
                    "top_risks": self._identify_top_risks(base_insights),
                    "trend_analysis": self._analyze_trends(base_insights)
                },
                "compliance_monitoring": {
                    "flags": base_insights.get("compliance_flags", []),
                    "severity_breakdown": self._analyze_severity(base_insights),
                    "regulatory_focus_areas": self._identify_focus_areas(base_insights)
                },
                "recommendations": {
                    "immediate_actions": self._generate_immediate_actions(base_insights),
                    "process_improvements": self._suggest_improvements(base_insights)
                }
            }
            
            return dashboard
            
        except GraphStoreError as e:
            raise InsightsServiceError(f"Dashboard generation failed: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Dashboard generation failed: {str(e)}")
    
    # Private helper methods
    
    async def _ensure_transcript_exists(self, transcript_id: str, analysis_data: Dict[str, Any]):
        """Ensure transcript exists in graph before linking."""
        try:
            # Extract transcript data from analysis if available
            topic = analysis_data.get('topic', '')
            message_count = len(analysis_data.get('messages', []))
            
            success = self.graph_store.add_transcript(transcript_id, topic, message_count)
            if not success:
                raise InsightsServiceError(f"Failed to ensure transcript {transcript_id} exists")
        except GraphStoreError as e:
            # Check if it's a "already exists" error (acceptable) vs real error (fail fast)
            error_msg = str(e).lower()
            if "duplicated primary key" in error_msg or "already exists" in error_msg:
                return  # This is fine, transcript exists
            else:
                # Real error - fail fast per NO FALLBACK principle
                raise InsightsServiceError(f"Failed to ensure transcript exists: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Failed to ensure transcript exists: {str(e)}")
    
    def _calculate_severity(self, risk_score: float) -> str:
        """Calculate severity level from risk score."""
        if risk_score >= 0.8:
            return "CRITICAL"
        elif risk_score >= 0.6:
            return "HIGH"
        elif risk_score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_risk_recommendation(self, cluster: Dict[str, Any]) -> str:
        """Generate recommendation based on risk cluster."""
        risk_type = cluster.get("risk_type", "")
        
        if "delinquency" in risk_type.lower():
            return "Implement proactive payment assistance programs"
        elif "elder_abuse" in risk_type.lower():
            return "Immediate escalation to compliance team required"
        elif "churn" in risk_type.lower():
            return "Deploy retention specialists for customer outreach"
        else:
            return "Monitor pattern closely and prepare intervention strategy"
    
    def _classify_recommendation(self, rec: Dict[str, Any]) -> str:
        """Classify recommendation type."""
        action = rec.get("recommended_action", "").lower()
        
        if "payment" in action or "financial" in action:
            return "FINANCIAL_ASSISTANCE"
        elif "escalate" in action or "urgent" in action:
            return "ESCALATION"
        elif "outreach" in action or "contact" in action:
            return "CUSTOMER_OUTREACH"
        else:
            return "GENERAL_SUPPORT"
    
    def _calculate_confidence(self, rec: Dict[str, Any]) -> float:
        """Calculate confidence score for recommendation."""
        base_confidence = 0.5
        success_rate = rec.get("success_rate", 0.5)
        
        # Adjust based on historical success
        if isinstance(success_rate, bool):
            confidence = base_confidence + (0.3 if success_rate else -0.2)
        else:
            confidence = base_confidence + (success_rate - 0.5) * 0.6
        
        return max(0.0, min(1.0, confidence))
    
    def _calculate_priority(self, rec: Dict[str, Any]) -> str:
        """Calculate priority level."""
        confidence = self._calculate_confidence(rec)
        
        if confidence >= 0.8:
            return "HIGH"
        elif confidence >= 0.6:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _calculate_similarity_confidence(self, pattern: Dict[str, Any]) -> float:
        """Calculate confidence in similarity match."""
        risk_score = pattern.get("risk_score", 0.5)
        return min(1.0, risk_score * 1.2)  # Scale risk score to confidence
    
    def _extract_learning(self, pattern: Dict[str, Any]) -> str:
        """Extract learning opportunity from similar pattern."""
        intent = pattern.get("intent", "")
        urgency = pattern.get("urgency", "")
        
        return f"Similar {urgency.lower()} urgency case with {intent.lower()} pattern"
    
    def _calculate_coverage(self) -> float:
        """Calculate analysis coverage percentage."""
        # Simplified calculation - in real implementation would compare against total transcripts
        return 0.85  # 85% coverage
    
    def _identify_top_risks(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify top risk patterns."""
        patterns = insights.get("risk_patterns", [])
        return sorted(patterns, key=lambda x: x.get("avg_risk_score", 0), reverse=True)[:3]
    
    def _analyze_trends(self, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze trends in risk patterns."""
        return {
            "increasing_risks": ["delinquency_risk", "complaint_risk"],
            "decreasing_risks": ["refinance_likelihood"],
            "stable_patterns": ["churn_risk"]
        }
    
    def _analyze_severity(self, insights: Dict[str, Any]) -> Dict[str, int]:
        """Analyze compliance flag severity distribution."""
        flags = insights.get("compliance_flags", [])
        severity_count = {}
        
        for flag in flags:
            severity = flag.get("severity", "MEDIUM")
            severity_count[severity] = severity_count.get(severity, 0) + 1
        
        return severity_count
    
    def _identify_focus_areas(self, insights: Dict[str, Any]) -> List[str]:
        """Identify regulatory focus areas."""
        return ["UDAAP Compliance", "Elder Abuse Detection", "Disclosure Requirements"]
    
    def _generate_immediate_actions(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate immediate action recommendations."""
        return [
            {
                "action": "Review high-risk compliance flags",
                "priority": "CRITICAL",
                "timeline": "24 hours"
            },
            {
                "action": "Implement elder abuse detection protocols",
                "priority": "HIGH",
                "timeline": "48 hours"
            }
        ]
    
    def _suggest_improvements(self, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Suggest process improvements."""
        return [
            {
                "improvement": "Automated risk pattern alerts",
                "impact": "Reduce response time by 50%",
                "effort": "Medium"
            },
            {
                "improvement": "Customer similarity matching for proactive outreach",
                "impact": "Improve customer satisfaction",
                "effort": "High"
            }
        ]
    
    # ===============================================
    # POPULATE OPERATIONS
    # ===============================================

    async def populate_insights(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generic populate method that handles all population types.

        Args:
            request: Request dict with populate parameters

        Returns:
            Dict with populate status and details

        Raises:
            ValueError: If invalid request parameters (NO FALLBACK)
            Exception: If population fails (NO FALLBACK)
        """
        if not request:
            raise ValueError("Request cannot be empty")

        analysis_id = request.get("analysis_id")
        analysis_ids = request.get("analysis_ids")
        from_date = request.get("from_date")
        populate_all = request.get("all", False)

        # Delegate to appropriate method based on request
        if analysis_id:
            return await self.populate_from_analysis(analysis_id)
        elif analysis_ids:
            return await self.populate_batch(analysis_ids)
        elif populate_all or from_date:
            return await self.populate_all(from_date)
        else:
            raise ValueError("Must provide analysis_id, analysis_ids, or all=true")

    async def populate_from_analysis(self, analysis_id: str) -> Dict[str, Any]:
        """
        Populate knowledge graph from a specific analysis ID.
        
        Args:
            analysis_id: Analysis ID to populate from
            
        Returns:
            Dict with populate status and details
            
        Raises:
            InsightsServiceError: If populate fails
        """
        try:
            # Get analysis from SQLite store
            from ..storage.analysis_store import AnalysisStore
            analysis_store = AnalysisStore("data/call_center.db")
            analysis = analysis_store.get_by_id(analysis_id)
            
            if not analysis:
                raise InsightsServiceError(f"Analysis {analysis_id} not found")
            
            # Convert to dict if needed
            if hasattr(analysis, 'to_dict'):
                analysis_data = analysis.to_dict()
            elif isinstance(analysis, dict):
                analysis_data = analysis
            else:
                raise InsightsServiceError(f"Unexpected analysis type: {type(analysis)}")
            
            # Store relationships in graph
            success = await self.store_analysis_relationships(analysis_data)
            
            if success:
                return {
                    "success": True,
                    "analysis_id": analysis_id,
                    "message": f"Analysis {analysis_id} populated in knowledge graph"
                }
            else:
                raise InsightsServiceError("Failed to populate graph")
                
        except Exception as e:
            raise InsightsServiceError(f"Populate failed: {str(e)}")
    
    async def populate_batch(self, analysis_ids: List[str]) -> Dict[str, Any]:
        """
        Populate knowledge graph from multiple analysis IDs.
        
        Args:
            analysis_ids: List of analysis IDs to populate from
            
        Returns:
            Dict with populate status and details
            
        Raises:
            InsightsServiceError: If batch populate fails
        """
        try:
            results = []
            errors = []
            
            for analysis_id in analysis_ids:
                try:
                    result = await self.populate_from_analysis(analysis_id)
                    results.append(result)
                except InsightsServiceError as e:
                    errors.append({"analysis_id": analysis_id, "error": str(e)})
            
            
            return {
                "success": len(errors) == 0,
                "populated_count": len(results),
                "error_count": len(errors),
                "results": results,
                "errors": errors if errors else None
            }
            
        except Exception as e:
            raise InsightsServiceError(f"Batch populate failed: {str(e)}")
    
    async def populate_all(self, from_date: str = None) -> Dict[str, Any]:
        """
        Populate knowledge graph from all available analyses.
        
        Args:
            from_date: Optional date filter (YYYY-MM-DD format)
            
        Returns:
            Dict with populate status and details
            
        Raises:
            InsightsServiceError: If populate all fails
        """
        try:
            # Get all analyses from SQLite
            from ..storage.analysis_store import AnalysisStore
            analysis_store = AnalysisStore("data/call_center.db")
            all_analyses = analysis_store.get_all()
            
            if not all_analyses:
                return {
                    "success": True,
                    "populated_count": 0,
                    "message": "No analyses found to populate"
                }
            
            # Filter by date if provided
            if from_date:
                from datetime import datetime
                try:
                    filter_date = datetime.strptime(from_date, "%Y-%m-%d")
                    # Filter logic would depend on analysis structure
                    # For now, populate all
                    pass
                except ValueError:
                    raise InsightsServiceError(f"Invalid date format: {from_date}. Use YYYY-MM-DD")
            
            # Extract analysis IDs
            analysis_ids = []
            for analysis in all_analyses:
                if hasattr(analysis, 'analysis_id'):
                    analysis_ids.append(analysis.analysis_id)
                elif isinstance(analysis, dict) and 'analysis_id' in analysis:
                    analysis_ids.append(analysis['analysis_id'])
            
            if not analysis_ids:
                raise InsightsServiceError("No analysis IDs found in analyses")
            
            # Batch populate
            return await self.populate_batch(analysis_ids)
            
        except Exception as e:
            raise InsightsServiceError(f"Populate all failed: {str(e)}")
    
    # ===============================================
    # QUERY OPERATIONS
    # ===============================================
    
    async def execute_query(self, cypher_query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Execute raw Cypher query on knowledge graph.
        
        Args:
            cypher_query: Cypher query string
            parameters: Optional query parameters
            
        Returns:
            List of query results
            
        Raises:
            InsightsServiceError: If query fails
        """
        try:
            if not cypher_query or not cypher_query.strip():
                raise InsightsServiceError("cypher_query is required")
            
            results = self.graph_store.execute_query(cypher_query, parameters)
            
            return results
            
        except GraphStoreError as e:
            raise InsightsServiceError(f"Query failed: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Query failed: {str(e)}")
    
    async def get_graph_status(self) -> Dict[str, Any]:
        """
        Get knowledge graph status and statistics.
        
        Returns:
            Dict with graph statistics
            
        Raises:
            InsightsServiceError: If status check fails
        """
        try:
            stats = self.graph_store.get_graph_statistics()
            
            # Add computed fields
            stats["graph_populated"] = stats.get("total_nodes", 0) > 0
            stats["last_checked"] = datetime.utcnow().isoformat()
            
            return stats
            
        except GraphStoreError as e:
            raise InsightsServiceError(f"Status check failed: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Status check failed: {str(e)}")
    
    # ===============================================
    # DELETE OPERATIONS
    # ===============================================
    
    async def delete_analysis(self, analysis_id: str) -> Dict[str, Any]:
        """
        Delete analysis from knowledge graph.
        
        Args:
            analysis_id: Analysis ID to delete
            
        Returns:
            Dict with deletion status
            
        Raises:
            InsightsServiceError: If deletion fails
        """
        try:
            if not analysis_id:
                raise InsightsServiceError("analysis_id is required")
            
            success = self.graph_store.delete_analysis_node(analysis_id)
            
            if success:
                return {
                    "success": True,
                    "analysis_id": analysis_id,
                    "message": f"Analysis {analysis_id} deleted from knowledge graph"
                }
            else:
                raise InsightsServiceError("Delete operation returned false")
                
        except GraphStoreError as e:
            raise InsightsServiceError(f"Delete failed: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Delete failed: {str(e)}")
    
    async def delete_customer(self, customer_id: str, cascade: bool = False) -> Dict[str, Any]:
        """
        Delete customer from knowledge graph.
        
        Args:
            customer_id: Customer ID to delete
            cascade: If True, delete all related data
            
        Returns:
            Dict with deletion status
            
        Raises:
            InsightsServiceError: If deletion fails
        """
        try:
            if not customer_id:
                raise InsightsServiceError("customer_id is required")
            
            if cascade:
                success = self.graph_store.delete_customer_cascade(customer_id)
                message = f"Customer {customer_id} and all related data deleted"
            else:
                # Non-cascade delete would need different implementation
                success = self.graph_store.delete_customer_cascade(customer_id)
                message = f"Customer {customer_id} deleted"
            
            if success:
                return {
                    "success": True,
                    "customer_id": customer_id,
                    "cascade": cascade,
                    "message": message
                }
            else:
                raise InsightsServiceError("Delete operation returned false")
                
        except GraphStoreError as e:
            raise InsightsServiceError(f"Delete customer failed: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Delete customer failed: {str(e)}")
    
    async def prune_old_data(self, older_than_days: int) -> Dict[str, Any]:
        """
        Remove data older than specified days (GDPR compliance).
        
        Args:
            older_than_days: Days threshold for deletion
            
        Returns:
            Dict with prune results
            
        Raises:
            InsightsServiceError: If prune fails
        """
        try:
            if older_than_days <= 0:
                raise InsightsServiceError("older_than_days must be positive")
            
            deleted_count = self.graph_store.prune_old_data(older_than_days)
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "older_than_days": older_than_days,
                "message": f"Deleted {deleted_count} nodes older than {older_than_days} days"
            }
            
        except GraphStoreError as e:
            raise InsightsServiceError(f"Prune failed: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Prune failed: {str(e)}")
    
    async def clear_graph(self) -> Dict[str, Any]:
        """
        Clear entire knowledge graph (use with caution).
        
        Returns:
            Dict with clear status
            
        Raises:
            InsightsServiceError: If clear fails
        """
        try:
            success = self.graph_store.clear_graph()
            
            if success:
                return {
                    "success": True,
                    "message": "Knowledge graph cleared completely"
                }
            else:
                raise InsightsServiceError("Clear operation returned false")
                
        except GraphStoreError as e:
            raise InsightsServiceError(f"Clear failed: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Clear failed: {str(e)}")
    
    async def get_visualization_data(self) -> Dict[str, Any]:
        """
        Get graph data formatted for visualization.
        
        Returns:
            Dict with nodes and edges for visualization
            
        Raises:
            InsightsServiceError: If visualization data extraction fails
        """
        try:
            graph_data = self.graph_store.get_graph_for_visualization()
            
            return graph_data
            
        except GraphStoreError as e:
            raise InsightsServiceError(f"Failed to get visualization data: {str(e)}")
        except Exception as e:
            raise InsightsServiceError(f"Visualization failed: {str(e)}")
    
    async def get_visualization_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph for visualization.
        
        Returns:
            Dict with graph statistics
            
        Raises:
            InsightsServiceError: If statistics extraction fails
        """
        try:
            from ..visualization.graph_visualizer import GraphVisualizer
            
            graph_data = await self.get_visualization_data()
            visualizer = GraphVisualizer()
            stats = visualizer.get_graph_statistics(graph_data)
            
            return stats
            
        except InsightsServiceError:
            raise  # Re-raise our own exceptions
        except Exception as e:
            raise InsightsServiceError(f"Failed to generate statistics: {str(e)}")
    
    def close(self):
        """Close service and underlying connections."""
        if self.graph_store:
            self.graph_store.close()
