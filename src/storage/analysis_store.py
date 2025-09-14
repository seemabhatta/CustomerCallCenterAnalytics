"""SQLite storage layer for call analysis results."""
import sqlite3
import json
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models.transcript import Transcript


class AnalysisStore:
    """SQLite-based storage for call analysis results."""
    
    def __init__(self, db_path: str):
        """Initialize the analysis store.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema for analysis storage."""
        with sqlite3.connect(self.db_path) as conn:
            # Create analysis table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS analysis (
                    id TEXT PRIMARY KEY,
                    transcript_id TEXT NOT NULL,
                    analysis_data TEXT NOT NULL,
                    
                    -- Quick access fields for filtering/reporting
                    primary_intent TEXT,
                    urgency_level TEXT,
                    borrower_sentiment TEXT,
                    delinquency_risk REAL,
                    churn_risk REAL,
                    complaint_risk REAL,
                    refinance_likelihood REAL,
                    empathy_score REAL,
                    compliance_adherence REAL,
                    solution_effectiveness REAL,
                    compliance_issues INTEGER,
                    escalation_needed BOOLEAN,
                    issue_resolved BOOLEAN,
                    first_call_resolution BOOLEAN,
                    confidence_score REAL,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transcript_id) REFERENCES transcripts(id)
                )
            ''')
            
            # Create indexes for common queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_transcript_id ON analysis(transcript_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_primary_intent ON analysis(primary_intent)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_urgency ON analysis(urgency_level)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_risks ON analysis(delinquency_risk, churn_risk)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_escalation ON analysis(escalation_needed)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_resolution ON analysis(issue_resolved, first_call_resolution)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON analysis(created_at)')
            
            conn.commit()
    
    def store(self, analysis: Dict[str, Any]) -> str:
        """Store analysis results.
        
        Args:
            analysis: Analysis results dictionary
            
        Returns:
            Analysis ID
        """
        with sqlite3.connect(self.db_path) as conn:
            # Extract quick access fields from analysis
            borrower_risks = analysis.get('borrower_risks', {})
            advisor_metrics = analysis.get('advisor_metrics', {})
            
            # Count compliance issues
            compliance_issues = len(analysis.get('compliance_flags', []))
            
            # Store analysis with extracted fields
            conn.execute('''
                INSERT OR REPLACE INTO analysis (
                    id, transcript_id, analysis_data,
                    primary_intent, urgency_level, borrower_sentiment,
                    delinquency_risk, churn_risk, complaint_risk, refinance_likelihood,
                    empathy_score, compliance_adherence, solution_effectiveness,
                    compliance_issues, escalation_needed, issue_resolved, 
                    first_call_resolution, confidence_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis['analysis_id'],
                analysis['transcript_id'],
                json.dumps(analysis),
                analysis.get('primary_intent', ''),
                analysis.get('urgency_level', ''),
                analysis.get('borrower_sentiment', {}).get('overall', ''),
                borrower_risks.get('delinquency_risk', 0),
                borrower_risks.get('churn_risk', 0),
                borrower_risks.get('complaint_risk', 0),
                borrower_risks.get('refinance_likelihood', 0),
                advisor_metrics.get('empathy_score', 0),
                advisor_metrics.get('compliance_adherence', 0),
                advisor_metrics.get('solution_effectiveness', 0),
                compliance_issues,
                analysis.get('escalation_needed', False),
                analysis.get('issue_resolved', False),
                analysis.get('first_call_resolution', False),
                analysis.get('confidence_score', 0)
            ))
            
            conn.commit()
            
        return analysis['analysis_id']
    
    def get_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by ID.
        
        Args:
            analysis_id: Analysis ID
            
        Returns:
            Analysis data or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT analysis_data FROM analysis WHERE id = ?',
                (analysis_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return json.loads(row[0])
    
    def get_by_transcript_id(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get analysis by transcript ID.
        
        Args:
            transcript_id: Transcript ID
            
        Returns:
            Analysis data or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT analysis_data FROM analysis WHERE transcript_id = ? ORDER BY created_at DESC LIMIT 1',
                (transcript_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            return json.loads(row[0])
    
    def get_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all analyses.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of analysis data
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'SELECT analysis_data FROM analysis ORDER BY created_at DESC LIMIT ?',
                (limit,)
            )
            
            return [json.loads(row[0]) for row in cursor.fetchall()]
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get aggregate metrics summary.
        
        Returns:
            Summary statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            # Overall counts
            cursor = conn.execute('SELECT COUNT(*) FROM analysis')
            total_analyses = cursor.fetchone()[0]
            
            if total_analyses == 0:
                return {
                    'total_analyses': 0,
                    'avg_confidence_score': 0,
                    'escalation_rate': 0,
                    'first_call_resolution_rate': 0,
                    'avg_empathy_score': 0,
                    'avg_delinquency_risk': 0,
                    'avg_churn_risk': 0,
                    'top_intents': {},
                    'urgency_distribution': {},
                    'sentiment_distribution': {}
                }
            
            # Average metrics
            cursor = conn.execute('''
                SELECT 
                    AVG(confidence_score),
                    AVG(CASE WHEN escalation_needed = 1 THEN 1.0 ELSE 0.0 END),
                    AVG(CASE WHEN first_call_resolution = 1 THEN 1.0 ELSE 0.0 END),
                    AVG(empathy_score),
                    AVG(delinquency_risk),
                    AVG(churn_risk)
                FROM analysis
            ''')
            avg_metrics = cursor.fetchone()
            
            # Intent distribution
            cursor = conn.execute('''
                SELECT primary_intent, COUNT(*) 
                FROM analysis 
                WHERE primary_intent != '' 
                GROUP BY primary_intent 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            ''')
            top_intents = dict(cursor.fetchall())
            
            # Urgency distribution
            cursor = conn.execute('''
                SELECT urgency_level, COUNT(*) 
                FROM analysis 
                WHERE urgency_level != '' 
                GROUP BY urgency_level
            ''')
            urgency_distribution = dict(cursor.fetchall())
            
            # Sentiment distribution
            cursor = conn.execute('''
                SELECT borrower_sentiment, COUNT(*) 
                FROM analysis 
                WHERE borrower_sentiment != '' 
                GROUP BY borrower_sentiment
            ''')
            sentiment_distribution = dict(cursor.fetchall())
            
            return {
                'total_analyses': total_analyses,
                'avg_confidence_score': round(avg_metrics[0] or 0, 2),
                'escalation_rate': round((avg_metrics[1] or 0) * 100, 1),
                'first_call_resolution_rate': round((avg_metrics[2] or 0) * 100, 1),
                'avg_empathy_score': round(avg_metrics[3] or 0, 1),
                'avg_delinquency_risk': round(avg_metrics[4] or 0, 2),
                'avg_churn_risk': round(avg_metrics[5] or 0, 2),
                'top_intents': top_intents,
                'urgency_distribution': urgency_distribution,
                'sentiment_distribution': sentiment_distribution
            }
    
    def get_risk_reports(self, risk_threshold: float = 0.7) -> Dict[str, List[Dict[str, Any]]]:
        """Get high-risk borrowers report.
        
        Args:
            risk_threshold: Minimum risk score to include
            
        Returns:
            Dictionary with high-risk analyses by type
        """
        with sqlite3.connect(self.db_path) as conn:
            # High delinquency risk
            cursor = conn.execute('''
                SELECT transcript_id, analysis_data 
                FROM analysis 
                WHERE delinquency_risk >= ? 
                ORDER BY delinquency_risk DESC
            ''', (risk_threshold,))
            
            high_delinquency = []
            for row in cursor.fetchall():
                analysis = json.loads(row[1])
                high_delinquency.append({
                    'transcript_id': row[0],
                    'delinquency_risk': analysis['borrower_risks']['delinquency_risk'],
                    'primary_intent': analysis['primary_intent'],
                    'summary': analysis['call_summary'][:100] + '...' if len(analysis['call_summary']) > 100 else analysis['call_summary']
                })
            
            # High churn risk
            cursor = conn.execute('''
                SELECT transcript_id, analysis_data 
                FROM analysis 
                WHERE churn_risk >= ? 
                ORDER BY churn_risk DESC
            ''', (risk_threshold,))
            
            high_churn = []
            for row in cursor.fetchall():
                analysis = json.loads(row[1])
                high_churn.append({
                    'transcript_id': row[0],
                    'churn_risk': analysis['borrower_risks']['churn_risk'],
                    'primary_intent': analysis['primary_intent'],
                    'summary': analysis['call_summary'][:100] + '...' if len(analysis['call_summary']) > 100 else analysis['call_summary']
                })
            
            return {
                'high_delinquency_risk': high_delinquency,
                'high_churn_risk': high_churn
            }
    
    def delete(self, analysis_id: str) -> bool:
        """Delete an analysis.
        
        Args:
            analysis_id: Analysis ID to delete
            
        Returns:
            True if deleted, False if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                'DELETE FROM analysis WHERE id = ?',
                (analysis_id,)
            )
            conn.commit()
            
            return cursor.rowcount > 0
    
    def delete_all(self) -> int:
        """Delete all analyses.
        
        Returns:
            Number of analyses deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM analysis')
            count = cursor.fetchone()[0]
            
            conn.execute('DELETE FROM analysis')
            conn.commit()
            
            return count