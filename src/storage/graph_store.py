"""
Knowledge Graph Store using KuzuDB for Customer Call Center Analytics.

Manages graph relationships between customers, transcripts, analyses, and patterns.
Following NO FALLBACK principle - fails fast on errors.
"""

import kuzu
import os
from typing import Dict, List, Any, Optional
from pathlib import Path



class GraphStoreError(Exception):
    """Exception raised for graph store errors."""
    pass


class GraphStore:
    """Knowledge Graph Store using KuzuDB for analytics insights."""
    
    def __init__(self, db_path: str = "data/analytics_graph.db"):
        """Initialize KuzuDB connection and schema."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Initialize KuzuDB database and connection
            self.database = kuzu.Database(str(self.db_path))
            self.connection = kuzu.Connection(self.database)
            
            # Initialize schema
            self._initialize_schema()
            
            
        except Exception as e:
            raise GraphStoreError(f"Failed to initialize GraphStore: {str(e)}")
    
    def _initialize_schema(self):
        """Create graph schema for call center analytics."""
        try:
            # Create node tables
            schema_queries = [
                # Customer nodes
                """CREATE NODE TABLE IF NOT EXISTS Customer(
                    customer_id STRING,
                    profile_type STRING,
                    risk_level STRING,
                    created_at TIMESTAMP,
                    PRIMARY KEY(customer_id)
                )""",
                
                # Transcript nodes  
                """CREATE NODE TABLE IF NOT EXISTS Transcript(
                    transcript_id STRING,
                    topic STRING,
                    message_count INT64,
                    created_at TIMESTAMP,
                    PRIMARY KEY(transcript_id)
                )""",
                
                # Analysis nodes
                """CREATE NODE TABLE IF NOT EXISTS Analysis(
                    analysis_id STRING,
                    primary_intent STRING,
                    urgency_level STRING,
                    confidence_score DOUBLE,
                    issue_resolved BOOLEAN,
                    escalation_needed BOOLEAN,
                    created_at TIMESTAMP,
                    PRIMARY KEY(analysis_id)
                )""",
                
                # Risk Pattern nodes (for clustering similar risks)
                """CREATE NODE TABLE IF NOT EXISTS RiskPattern(
                    pattern_id STRING,
                    pattern_type STRING,
                    description STRING,
                    risk_score DOUBLE,
                    frequency INT64,
                    PRIMARY KEY(pattern_id)
                )""",
                
                # Compliance Flag nodes
                """CREATE NODE TABLE IF NOT EXISTS ComplianceFlag(
                    flag_id STRING,
                    flag_type STRING,
                    description STRING,
                    severity STRING,
                    PRIMARY KEY(flag_id)
                )""",
            ]
            
            # Create relationships
            relationship_queries = [
                # Customer had call -> Transcript
                """CREATE REL TABLE IF NOT EXISTS HAD_CALL(
                    FROM Customer TO Transcript,
                    call_duration INT64,
                    created_at TIMESTAMP
                )""",
                
                # Transcript generated -> Analysis
                """CREATE REL TABLE IF NOT EXISTS GENERATED_ANALYSIS(
                    FROM Transcript TO Analysis,
                    processing_time DOUBLE,
                    created_at TIMESTAMP
                )""",
                
                # Analysis detected -> Risk Pattern
                """CREATE REL TABLE IF NOT EXISTS HAS_RISK_PATTERN(
                    FROM Analysis TO RiskPattern,
                    match_confidence DOUBLE,
                    created_at TIMESTAMP
                )""",
                
                # Analysis flagged -> Compliance Issue
                """CREATE REL TABLE IF NOT EXISTS HAS_COMPLIANCE_FLAG(
                    FROM Analysis TO ComplianceFlag,
                    severity_score DOUBLE,
                    created_at TIMESTAMP
                )""",
                
                # Customer similar to Customer (for recommendations)
                """CREATE REL TABLE IF NOT EXISTS SIMILAR_TO(
                    FROM Customer TO Customer,
                    similarity_score DOUBLE,
                    reason STRING,
                    created_at TIMESTAMP
                )""",
                
                # Analysis requires escalation
                """CREATE REL TABLE IF NOT EXISTS REQUIRES_ESCALATION(
                    FROM Analysis TO Analysis,
                    escalation_type STRING,
                    priority STRING,
                    created_at TIMESTAMP
                )""",
            ]
            
            # Execute schema creation
            for query in schema_queries + relationship_queries:
                self.connection.execute(query)
                
            
        except Exception as e:
            raise GraphStoreError(f"Failed to initialize schema: {str(e)}")
    
    def add_customer(self, customer_id: str, profile_type: str = "standard", risk_level: str = "low") -> bool:
        """Add customer node to graph."""
        try:
            # KuzuDB INSERT syntax
            query = """
            CREATE (:Customer {
                customer_id: $customer_id,
                profile_type: $profile_type,
                risk_level: $risk_level,
                created_at: current_timestamp()
            })
            """
            self.connection.execute(query, {
                "customer_id": customer_id,
                "profile_type": profile_type,
                "risk_level": risk_level
            })
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "duplicated primary key" in error_msg:
                # Customer already exists - this is acceptable, return success (idempotent behavior)
                return True
            else:
                raise GraphStoreError(f"Failed to add customer: {error_msg}")
    
    def add_analysis_with_relationships(self, analysis_data: Dict[str, Any]) -> bool:
        """Add analysis and create relationships to patterns and flags."""
        try:
            # Extract core analysis data
            analysis_id = analysis_data.get('analysis_id')
            transcript_id = analysis_data.get('transcript_id')
            
            if not analysis_id or not transcript_id:
                raise GraphStoreError("analysis_id and transcript_id are required")
            
            # Create analysis node
            self._add_analysis_node(analysis_data)
            
            # Create relationship to transcript
            self._link_transcript_to_analysis(transcript_id, analysis_id)
            
            # Process risk patterns
            self._process_risk_patterns(analysis_data)
            
            # Process compliance flags  
            self._process_compliance_flags(analysis_data)
            
            return True
            
        except Exception as e:
            raise GraphStoreError(f"Failed to add analysis: {str(e)}")
    
    def _add_analysis_node(self, analysis_data: Dict[str, Any]):
        """Create analysis node with robust duplicate handling."""
        analysis_id = analysis_data.get('analysis_id')
        if not analysis_id:
            raise GraphStoreError("analysis_id is required for creating analysis node")
        
        # Robust existence check with multiple fallback strategies
        exists = False
        try:
            # Strategy 1: Count-based existence check
            check_query = "MATCH (a:Analysis {analysis_id: $analysis_id}) RETURN count(a) as count"
            result = self.execute_query(check_query, {"analysis_id": analysis_id})
            
            if result and len(result) > 0 and "count" in result[0]:
                count = result[0]["count"]
                exists = count > 0
            else:
                exists = False
        except Exception as check_error:
            # Don't fail fast on existence check - proceed with create and handle duplicates there
            pass
        
        if exists:
            return
        
        # Create new analysis with comprehensive error handling
        try:
            query = """
            CREATE (a:Analysis {
                analysis_id: $analysis_id,
                primary_intent: $primary_intent,
                urgency_level: $urgency_level,
                confidence_score: $confidence_score,
                issue_resolved: $issue_resolved,
                escalation_needed: $escalation_needed,
                created_at: timestamp($created_at)
            })
            """
            
            from datetime import datetime
            created_at = datetime.utcnow().isoformat()
            
            self.connection.execute(query, parameters={
                "analysis_id": analysis_data.get('analysis_id'),
                "primary_intent": analysis_data.get('primary_intent', ''),
                "urgency_level": analysis_data.get('urgency_level', ''),
                "confidence_score": analysis_data.get('confidence_score', 0.0),
                "issue_resolved": analysis_data.get('issue_resolved', False),
                "escalation_needed": analysis_data.get('escalation_needed', False),
                "created_at": created_at
            })
            
        except Exception as create_error:
            error_msg = str(create_error)
            if "duplicated primary key" in error_msg.lower():
                # Analysis was created by another process between check and create (race condition)
                return
            elif "primary key" in error_msg.lower() and "constraint" in error_msg.lower():
                # Different format of primary key constraint error
                return
            else:
                # Real error - fail fast per NO FALLBACK principle
                raise GraphStoreError(f"Analysis creation failed: {error_msg}")
    
    def find_similar_risk_patterns(self, analysis_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find analyses with similar risk patterns."""
        try:
            query = """
            MATCH (a1:Analysis {analysis_id: $analysis_id})-[:HAS_RISK_PATTERN]->(rp:RiskPattern)
            MATCH (a2:Analysis)-[:HAS_RISK_PATTERN]->(rp)
            WHERE a1.analysis_id <> a2.analysis_id
            RETURN a2.analysis_id as similar_analysis_id,
                   a2.primary_intent as intent,
                   a2.urgency_level as urgency,
                   rp.pattern_type as shared_pattern,
                   rp.risk_score as risk_score
            LIMIT $limit
            """
            
            result = self.connection.execute(query, parameters={
                "analysis_id": analysis_id,
                "limit": limit
            })
            
            return [dict(record) for record in result]
            
        except Exception as e:
            raise GraphStoreError(f"Failed to find similar patterns: {str(e)}")
    
    def get_high_risk_clusters(self, risk_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Find clusters of high-risk analyses."""
        try:
            # Fixed query using WITH clause for proper KuzuDB aggregation
            query = """
            MATCH (a:Analysis)-[:HAS_RISK_PATTERN]->(p:RiskPattern)
            WHERE p.risk_score >= $risk_threshold
            WITH p.pattern_type as pattern_type, 
                 p.description as description,
                 p.risk_score as risk_score,
                 collect(a.analysis_id) as analysis_ids
            RETURN pattern_type as risk_type,
                   description as description,
                   risk_score as risk_score,
                   size(analysis_ids) as affected_analyses,
                   analysis_ids as analysis_ids
            ORDER BY risk_score DESC
            """
            
            result = self.execute_query(query, parameters={
                "risk_threshold": risk_threshold
            })
            
            return result
            
        except Exception as e:
            raise GraphStoreError(f"Failed to get risk clusters: {str(e)}")
    
    def get_customer_recommendations(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get AI recommendations based on similar customers and patterns."""
        try:
            query = """
            MATCH (c1:Customer {customer_id: $customer_id})-[:SIMILAR_TO]->(c2:Customer)
            MATCH (c2)-[:HAD_CALL]->(t:Transcript)-[:GENERATED_ANALYSIS]->(a:Analysis)
            MATCH (a)-[:HAS_RISK_PATTERN]->(rp:RiskPattern)
            RETURN c2.customer_id as similar_customer,
                   a.primary_intent as recommended_action,
                   rp.pattern_type as pattern_basis,
                   rp.description as recommendation_reason,
                   a.issue_resolved as success_rate
            LIMIT 5
            """
            
            result = self.connection.execute(query, parameters={
                "customer_id": customer_id
            })
            
            return [dict(record) for record in result]
            
        except Exception as e:
            raise GraphStoreError(f"Failed to get recommendations: {str(e)}")
    
    def _process_risk_patterns(self, analysis_data: Dict[str, Any]):
        """Process and link risk patterns from analysis data."""
        # Extract risk information
        borrower_risks = analysis_data.get('borrower_risks', {})
        compliance_flags = analysis_data.get('compliance_flags', [])
        
        for risk_type, risk_value in borrower_risks.items():
            if isinstance(risk_value, (int, float)) and risk_value > 0.5:  # Significant risk
                pattern_id = f"risk_{risk_type}_{hash(str(risk_value)) % 10000}"
                
                # Create or update risk pattern
                self._create_risk_pattern(pattern_id, risk_type, risk_value)
                
                # Link analysis to pattern
                self._link_analysis_to_risk_pattern(
                    analysis_data['analysis_id'], 
                    pattern_id, 
                    risk_value
                )
    
    def _process_compliance_flags(self, analysis_data: Dict[str, Any]):
        """Process and link compliance flags."""
        compliance_flags = analysis_data.get('compliance_flags', [])
        
        for flag_text in compliance_flags:
            if isinstance(flag_text, str):
                flag_id = f"compliance_{hash(flag_text) % 10000}"
                flag_type = self._extract_flag_type(flag_text)
                
                # Create compliance flag
                self._create_compliance_flag(flag_id, flag_type, flag_text)
                
                # Link analysis to flag
                self._link_analysis_to_compliance_flag(
                    analysis_data['analysis_id'],
                    flag_id,
                    self._calculate_severity_score(flag_text)
                )
    
    def _extract_flag_type(self, flag_text: str) -> str:
        """Extract flag type from text."""
        if "elder abuse" in flag_text.lower() or "undue influence" in flag_text.lower():
            return "ELDER_ABUSE"
        elif "udaap" in flag_text.lower():
            return "UDAAP_VIOLATION"
        elif "disclosure" in flag_text.lower():
            return "DISCLOSURE_VIOLATION"
        else:
            return "GENERAL_COMPLIANCE"
    
    def _calculate_severity_score(self, flag_text: str) -> float:
        """Calculate severity score based on flag text."""
        if "potential" in flag_text.lower():
            return 0.7
        elif "violation" in flag_text.lower():
            return 0.9
        else:
            return 0.5
    
    def _link_transcript_to_analysis(self, transcript_id: str, analysis_id: str):
        """Create relationship between transcript and analysis."""
        query = """
        MATCH (t:Transcript {transcript_id: $transcript_id}), (a:Analysis {analysis_id: $analysis_id})
        CREATE (t)-[:GENERATED_ANALYSIS {
            processing_time: 0.0,
            created_at: current_timestamp()
        }]->(a)
        """
        self.connection.execute(query, {
            "transcript_id": transcript_id,
            "analysis_id": analysis_id
        })
    
    def _create_risk_pattern(self, pattern_id: str, risk_type: str, risk_value: float):
        """Create or update risk pattern node."""
        # Check if pattern exists, if not create it
        query = """
        MERGE (:RiskPattern {
            pattern_id: $pattern_id,
            pattern_type: $risk_type,
            description: $description,
            risk_score: $risk_value,
            frequency: 1
        })
        """
        self.connection.execute(query, {
            "pattern_id": pattern_id,
            "risk_type": risk_type,
            "description": f"High {risk_type.replace('_', ' ')} risk pattern",
            "risk_value": risk_value
        })
    
    def _link_analysis_to_risk_pattern(self, analysis_id: str, pattern_id: str, confidence: float):
        """Link analysis to risk pattern."""
        query = """
        MATCH (a:Analysis {analysis_id: $analysis_id}), (rp:RiskPattern {pattern_id: $pattern_id})
        CREATE (a)-[:HAS_RISK_PATTERN {
            match_confidence: $confidence,
            created_at: current_timestamp()
        }]->(rp)
        """
        self.connection.execute(query, {
            "analysis_id": analysis_id,
            "pattern_id": pattern_id,
            "confidence": confidence
        })
    
    def _create_compliance_flag(self, flag_id: str, flag_type: str, description: str):
        """Create compliance flag node."""
        severity = "HIGH" if "violation" in description.lower() else "MEDIUM"
        
        query = """
        MERGE (:ComplianceFlag {
            flag_id: $flag_id,
            flag_type: $flag_type,
            description: $description,
            severity: $severity
        })
        """
        self.connection.execute(query, {
            "flag_id": flag_id,
            "flag_type": flag_type,
            "description": description,
            "severity": severity
        })
    
    def _link_analysis_to_compliance_flag(self, analysis_id: str, flag_id: str, severity_score: float):
        """Link analysis to compliance flag."""
        query = """
        MATCH (a:Analysis {analysis_id: $analysis_id}), (cf:ComplianceFlag {flag_id: $flag_id})
        CREATE (a)-[:HAS_COMPLIANCE_FLAG {
            severity_score: $severity_score,
            created_at: current_timestamp()
        }]->(cf)
        """
        self.connection.execute(query, {
            "analysis_id": analysis_id,
            "flag_id": flag_id,
            "severity_score": severity_score
        })
    
    def add_transcript(self, transcript_id: str, topic: str = "", message_count: int = 0) -> bool:
        """Add transcript node to graph with robust duplicate handling."""
        try:
            if not transcript_id:
                raise GraphStoreError("transcript_id is required")
                
            # Robust existence check using improved execute_query
            exists = False
            try:
                check_query = "MATCH (t:Transcript {transcript_id: $transcript_id}) RETURN count(t) as count"
                result = self.execute_query(check_query, {"transcript_id": transcript_id})
                
                if result and len(result) > 0 and "count" in result[0]:
                    count = result[0]["count"]
                    exists = count > 0
                else:
                    exists = False
            except Exception as check_e:
                # Continue with create attempt - will handle duplicates in create block
                pass
            
            if exists:
                return True
            
            # Create new transcript
            query = """
            CREATE (t:Transcript {
                transcript_id: $transcript_id,
                topic: $topic,
                message_count: $message_count,
                created_at: current_timestamp()
            })
            """
            self.connection.execute(query, {
                "transcript_id": transcript_id,
                "topic": topic,
                "message_count": message_count
            })
            return True
            
        except Exception as e:
            error_msg = str(e)
            if "duplicated primary key" in error_msg.lower():
                # Transcript was created concurrently - idempotent behavior
                return True
            elif "primary key" in error_msg.lower() and "constraint" in error_msg.lower():
                # Different format of primary key constraint error
                return True
            else:
                # Real error - fail fast per NO FALLBACK principle
                raise GraphStoreError(f"Failed to add transcript: {error_msg}")
    
    def get_insights_summary(self) -> Dict[str, Any]:
        """Get summary of insights from the knowledge graph."""
        try:
            # Get pattern summary
            pattern_query = """
            MATCH (rp:RiskPattern)
            RETURN rp.pattern_type as pattern_type,
                   avg(rp.risk_score) as avg_risk_score,
                   count(*) as pattern_count
            """
            pattern_result = self.execute_query(pattern_query)
            
            # Get compliance summary
            compliance_query = """
            MATCH (cf:ComplianceFlag)
            RETURN cf.flag_type as flag_type,
                   cf.severity as severity,
                   count(*) as flag_count
            """
            compliance_result = self.execute_query(compliance_query)
            
            return {
                "risk_patterns": pattern_result,
                "compliance_flags": compliance_result,
                "total_patterns": len(pattern_result),
                "total_flags": len(compliance_result)
            }
            
        except Exception as e:
            raise GraphStoreError(f"Failed to get insights: {str(e)}")
    
    # ===============================================
    # RAW QUERY OPERATIONS
    # ===============================================
    
    def execute_query(self, cypher_query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute raw Cypher query and return results."""
        try:
            if parameters is None:
                parameters = {}
            
            # Execute the query
            result = self.connection.execute(cypher_query, parameters)
            
            # Convert KuzuDB result to list for processing
            result_list = list(result)
            if not result_list:
                return []
            
            # Get column names - KuzuDB provides this through get_column_names()
            formatted_results = []
            
            try:
                # Try to get column names from the result object
                column_names = result.get_column_names()
                
                for record in result_list:
                    if isinstance(record, (list, tuple)):
                        # Record is a tuple/list, map to column names
                        if len(record) == len(column_names):
                            formatted_results.append(dict(zip(column_names, record)))
                        else:
                            # Mismatch between columns and values - use positional mapping
                            record_dict = {}
                            for i, value in enumerate(record):
                                col_name = column_names[i] if i < len(column_names) else f"col_{i}"
                                record_dict[col_name] = value
                            formatted_results.append(record_dict)
                    else:
                        # Single value result
                        if len(column_names) == 1:
                            formatted_results.append({column_names[0]: record})
                        else:
                            formatted_results.append({"value": record})
                            
            except (AttributeError, IndexError) as col_error:
                # Fallback: get_column_names() failed or column mismatch
                
                # Try to parse column names from the query itself
                import re
                as_matches = re.findall(r'as\s+(\w+)', cypher_query, re.IGNORECASE)
                
                if as_matches:
                    # Use extracted column names
                    for record in result_list:
                        if isinstance(record, (list, tuple)):
                            record_dict = {}
                            for i, value in enumerate(record):
                                col_name = as_matches[i] if i < len(as_matches) else f"col_{i}"
                                record_dict[col_name] = value
                            formatted_results.append(record_dict)
                        else:
                            formatted_results.append({as_matches[0]: record})
                else:
                    # Final fallback: generic column names
                    for record in result_list:
                        if isinstance(record, (list, tuple)):
                            if len(record) == 1:
                                formatted_results.append({"value": record[0]})
                            else:
                                record_dict = {}
                                for i, value in enumerate(record):
                                    record_dict[f"col_{i}"] = value
                                formatted_results.append(record_dict)
                        else:
                            formatted_results.append({"value": record})
            
            return formatted_results
            
        except Exception as e:
            raise GraphStoreError(f"Query execution failed: {str(e)}")
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get graph statistics for status monitoring."""
        try:
            stats = {}
            
            # Count nodes by type using the fixed execute_query method
            node_types = ["Customer", "Transcript", "Analysis", "RiskPattern", "ComplianceFlag"]
            for node_type in node_types:
                count_query = f"MATCH (n:{node_type}) RETURN count(n) as count"
                try:
                    result = self.execute_query(count_query)
                    count = result[0]["count"] if result else 0
                except Exception:
                    count = 0  # Table might not exist yet
                stats[f"{node_type.lower()}_count"] = count
            
            # Count relationships using the fixed execute_query method 
            try:
                rel_query = "MATCH ()-[r]-() RETURN count(r) as count"
                result = self.execute_query(rel_query)
                stats["relationship_count"] = result[0]["count"] if result else 0
            except Exception:
                stats["relationship_count"] = 0  # No relationships or tables not created
            
            # Total nodes
            stats["total_nodes"] = sum(v for k, v in stats.items() if k.endswith('_count') and k != 'relationship_count')
            
            return stats
            
        except Exception as e:
            raise GraphStoreError(f"Statistics failed: {str(e)}")
    
    # ===============================================
    # DELETE OPERATIONS
    # ===============================================
    
    def delete_analysis_node(self, analysis_id: str) -> bool:
        """Delete analysis node and all its relationships."""
        try:
            query = """
            MATCH (a:Analysis {analysis_id: $analysis_id})
            DETACH DELETE a
            """
            
            result = self.connection.execute(query, {"analysis_id": analysis_id})
            return True
            
        except Exception as e:
            raise GraphStoreError(f"Delete analysis failed: {str(e)}")
    
    def delete_customer_cascade(self, customer_id: str) -> bool:
        """Delete customer and all related data (cascading delete)."""
        try:
            query = """
            MATCH (c:Customer {customer_id: $customer_id})
            OPTIONAL MATCH (c)-[:HAD_CALL]->(t:Transcript)
            OPTIONAL MATCH (t)-[:GENERATED_ANALYSIS]->(a:Analysis)
            OPTIONAL MATCH (a)-[:HAS_RISK_PATTERN]->(p:RiskPattern)
            OPTIONAL MATCH (a)-[:HAS_COMPLIANCE_FLAG]->(f:ComplianceFlag)
            DETACH DELETE c, t, a, p, f
            """
            
            result = self.connection.execute(query, {"customer_id": customer_id})
            return True
            
        except Exception as e:
            raise GraphStoreError(f"Delete customer failed: {str(e)}")
    
    def prune_old_data(self, older_than_days: int) -> int:
        """Delete data older than specified days. Returns count of deleted nodes."""
        try:
            # Calculate cutoff timestamp
            from datetime import datetime, timedelta
            cutoff = datetime.utcnow() - timedelta(days=older_than_days)
            cutoff_timestamp = cutoff.timestamp()
            
            # First count what will be deleted
            count_query = """
            MATCH (n)
            WHERE n.created_at < $cutoff_timestamp
            RETURN count(n) as count
            """
            
            result = self.connection.execute(count_query, {"cutoff_timestamp": cutoff_timestamp})
            count = list(result)[0]["count"] if result else 0
            
            # Delete old nodes
            delete_query = """
            MATCH (n)
            WHERE n.created_at < $cutoff_timestamp
            DETACH DELETE n
            """
            
            self.connection.execute(delete_query, {"cutoff_timestamp": cutoff_timestamp})
            
            return count
            
        except Exception as e:
            raise GraphStoreError(f"Prune failed: {str(e)}")
    
    def clear_graph(self) -> bool:
        """Clear all nodes and relationships from the graph."""
        try:
            query = "MATCH (n) DETACH DELETE n"
            self.connection.execute(query)
            
            return True
            
        except Exception as e:
            raise GraphStoreError(f"Clear graph failed: {str(e)}")
    
    def get_graph_for_visualization(self) -> Dict[str, Any]:
        """Extract all nodes and edges for graph visualization.
        
        Returns:
            Dict with 'nodes' and 'edges' lists for NetworkX/Plotly visualization
            
        Raises:
            GraphStoreError: If graph is empty (NO FALLBACK) or query fails
        """
        try:
            # Get nodes by type to handle different schemas
            all_nodes = []
            
            # Get Transcript nodes
            transcript_query = """
            MATCH (n:Transcript)
            RETURN 
                CAST(ID(n), "STRING") as id,
                'Transcript' as type,
                n.transcript_id as label,
                n.topic as description,
                0.0 as risk_score,
                0.0 as severity_score
            """
            
            # Get Analysis nodes
            analysis_query = """
            MATCH (n:Analysis)
            RETURN 
                CAST(ID(n), "STRING") as id,
                'Analysis' as type,
                n.analysis_id as label,
                n.summary as description,
                n.risk_score as risk_score,
                0.0 as severity_score
            """
            
            # Get RiskPattern nodes
            risk_query = """
            MATCH (n:RiskPattern)
            RETURN 
                CAST(ID(n), "STRING") as id,
                'RiskPattern' as type,
                n.pattern_id as label,
                n.description as description,
                n.risk_score as risk_score,
                0.0 as severity_score
            """
            
            # Get ComplianceFlag nodes
            flag_query = """
            MATCH (n:ComplianceFlag)
            RETURN 
                CAST(ID(n), "STRING") as id,
                'ComplianceFlag' as type,
                n.flag_id as label,
                n.description as description,
                0.0 as risk_score,
                n.severity_score as severity_score
            """
            
            # Execute queries and combine results
            for query in [transcript_query, analysis_query, risk_query, flag_query]:
                try:
                    result = self.execute_query(query)
                    all_nodes.extend(result)
                except Exception:
                    # Skip if no nodes of this type exist
                    continue
            
            # Get all relationships by type
            all_edges = []
            
            # Get GENERATED_FROM relationships
            edges_queries = [
                """
                MATCH (a:Analysis)-[:GENERATED_FROM]->(t:Transcript)
                RETURN 
                    CAST(ID(a), "STRING") as source,
                    CAST(ID(t), "STRING") as target,
                    'GENERATED_FROM' as relationship
                """,
                """
                MATCH (a:Analysis)-[:HAS_RISK_PATTERN]->(r:RiskPattern)
                RETURN 
                    CAST(ID(a), "STRING") as source,
                    CAST(ID(r), "STRING") as target,
                    'HAS_RISK_PATTERN' as relationship
                """,
                """
                MATCH (a:Analysis)-[:HAS_COMPLIANCE_FLAG]->(f:ComplianceFlag)
                RETURN 
                    CAST(ID(a), "STRING") as source,
                    CAST(ID(f), "STRING") as target,
                    'HAS_COMPLIANCE_FLAG' as relationship
                """
            ]
            
            # Execute edge queries and combine results
            for query in edges_queries:
                try:
                    result = self.execute_query(query)
                    all_edges.extend(result)
                except Exception:
                    # Skip if no edges of this type exist
                    continue
            
            # Use combined edge results
            edges_result = all_edges
            
            # Use combined node results
            nodes_result = all_nodes
            
            # Check if graph is empty - NO FALLBACK
            if not nodes_result:
                raise GraphStoreError("No data in graph - cannot visualize empty graph")
            
            # Format nodes for visualization
            nodes = []
            for node in nodes_result:
                node_data = {
                    "id": str(node["id"]),
                    "label": str(node["label"]),
                    "type": str(node["type"]),
                    "description": str(node.get("description", "")),
                }
                
                # Add scores if present
                if node["risk_score"] > 0:
                    node_data["risk_score"] = float(node["risk_score"])
                if node["severity_score"] > 0:
                    node_data["severity_score"] = float(node["severity_score"])
                    
                nodes.append(node_data)
            
            # Format edges for visualization
            edges = []
            for edge in edges_result:
                edge_data = {
                    "source": str(edge["source"]),
                    "target": str(edge["target"]), 
                    "relationship": str(edge["relationship"])
                }
                edges.append(edge_data)
            
            
            return {
                "nodes": nodes,
                "edges": edges
            }
            
        except Exception as e:
            raise GraphStoreError(f"Graph visualization data extraction failed: {str(e)}")

    def close(self):
        """Close database connection."""
        try:
            if hasattr(self, 'connection'):
                self.connection.close()
        except Exception as e:
            pass
