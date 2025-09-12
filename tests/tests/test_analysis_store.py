"""Tests for analysis storage layer."""
import pytest
import tempfile
import os
import json
from src.storage.analysis_store import AnalysisStore


class TestAnalysisStore:
    """Test the AnalysisStore SQLite storage layer."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database file for testing."""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)
    
    @pytest.fixture
    def sample_analysis(self):
        """Create a sample analysis result."""
        return {
            "analysis_id": "ANALYSIS_001",
            "transcript_id": "CALL_PMI_001",
            "call_summary": "Customer inquired about PMI removal, advisor provided helpful guidance",
            "primary_intent": "PMI removal",
            "urgency_level": "medium",
            "borrower_sentiment": {
                "overall": "neutral",
                "start": "confused",
                "end": "hopeful",
                "trend": "improving"
            },
            "borrower_risks": {
                "delinquency_risk": 0.15,
                "churn_risk": 0.25,
                "complaint_risk": 0.10,
                "refinance_likelihood": 0.70
            },
            "advisor_metrics": {
                "empathy_score": 8.5,
                "compliance_adherence": 9.0,
                "solution_effectiveness": 7.5,
                "coaching_opportunities": ["Could provide more proactive follow-up options"]
            },
            "compliance_flags": ["Missing PMI disclosure timing"],
            "required_disclosures": ["PMI removal process", "Appraisal requirements"],
            "issue_resolved": False,
            "first_call_resolution": False,
            "escalation_needed": False,
            "topics_discussed": ["PMI removal", "property value", "appraisal process"],
            "confidence_score": 0.92,
            "product_opportunities": ["appraisal services", "refinance evaluation"],
            "payment_concerns": [],
            "property_related_issues": ["property valuation needed"]
        }
    
    @pytest.fixture
    def high_risk_analysis(self):
        """Create a high-risk analysis result."""
        return {
            "analysis_id": "ANALYSIS_HIGH_RISK",
            "transcript_id": "CALL_HARDSHIP_001",
            "call_summary": "Customer experiencing financial hardship, requesting payment modification",
            "primary_intent": "hardship assistance",
            "urgency_level": "high",
            "borrower_sentiment": {
                "overall": "distressed",
                "start": "anxious",
                "end": "slightly relieved",
                "trend": "improving"
            },
            "borrower_risks": {
                "delinquency_risk": 0.85,
                "churn_risk": 0.60,
                "complaint_risk": 0.40,
                "refinance_likelihood": 0.10
            },
            "advisor_metrics": {
                "empathy_score": 9.5,
                "compliance_adherence": 8.5,
                "solution_effectiveness": 8.0,
                "coaching_opportunities": []
            },
            "compliance_flags": ["Hardship documentation required"],
            "required_disclosures": ["Modification options", "Credit impact disclosure"],
            "issue_resolved": False,
            "first_call_resolution": False,
            "escalation_needed": True,
            "topics_discussed": ["financial hardship", "payment modification", "loss mitigation"],
            "confidence_score": 0.88,
            "product_opportunities": ["hardship programs"],
            "payment_concerns": ["missed payments", "financial instability"],
            "property_related_issues": []
        }
    
    def test_store_initialization(self, temp_db):
        """Test that store initializes and creates tables."""
        store = AnalysisStore(temp_db)
        
        # Verify database file was created
        assert os.path.exists(temp_db)
        
        # Check that tables and indexes were created
        import sqlite3
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check analysis table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='analysis';")
        assert cursor.fetchone() is not None
        
        # Check some key indexes exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_transcript_id';")
        assert cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name='idx_primary_intent';")
        assert cursor.fetchone() is not None
        
        conn.close()
    
    def test_store_analysis(self, temp_db, sample_analysis):
        """Test storing analysis results."""
        store = AnalysisStore(temp_db)
        
        # Store analysis
        result_id = store.store(sample_analysis)
        
        assert result_id == sample_analysis['analysis_id']
        
        # Verify it was stored by retrieving it
        retrieved = store.get_by_id(sample_analysis['analysis_id'])
        
        assert retrieved is not None
        assert retrieved['transcript_id'] == sample_analysis['transcript_id']
        assert retrieved['primary_intent'] == sample_analysis['primary_intent']
        assert retrieved['confidence_score'] == sample_analysis['confidence_score']
        
        # Check that nested objects are preserved
        assert retrieved['borrower_risks']['delinquency_risk'] == 0.15
        assert retrieved['advisor_metrics']['empathy_score'] == 8.5
    
    def test_store_analysis_upsert(self, temp_db, sample_analysis):
        """Test that storing overwrites existing analysis."""
        store = AnalysisStore(temp_db)
        
        # Store original analysis
        store.store(sample_analysis)
        
        # Modify and store again
        sample_analysis['confidence_score'] = 0.95
        sample_analysis['primary_intent'] = "PMI removal - updated"
        
        result_id = store.store(sample_analysis)
        assert result_id == sample_analysis['analysis_id']
        
        # Verify updated values
        retrieved = store.get_by_id(sample_analysis['analysis_id'])
        assert retrieved['confidence_score'] == 0.95
        assert retrieved['primary_intent'] == "PMI removal - updated"
    
    def test_get_by_id_not_found(self, temp_db):
        """Test getting analysis by non-existent ID."""
        store = AnalysisStore(temp_db)
        
        result = store.get_by_id("NON_EXISTENT")
        assert result is None
    
    def test_get_by_transcript_id(self, temp_db, sample_analysis):
        """Test getting analysis by transcript ID."""
        store = AnalysisStore(temp_db)
        
        # Store analysis
        store.store(sample_analysis)
        
        # Retrieve by transcript ID
        retrieved = store.get_by_transcript_id(sample_analysis['transcript_id'])
        
        assert retrieved is not None
        assert retrieved['analysis_id'] == sample_analysis['analysis_id']
        assert retrieved['transcript_id'] == sample_analysis['transcript_id']
    
    def test_get_by_transcript_id_multiple(self, temp_db, sample_analysis):
        """Test getting latest analysis when multiple exist for same transcript."""
        import time
        import json
        
        store = AnalysisStore(temp_db)
        
        # Store first analysis
        store.store(sample_analysis)
        
        # Wait longer to ensure different timestamps  
        time.sleep(1.1)
        
        # Create second analysis for same transcript with different ID (deep copy)
        second_analysis = json.loads(json.dumps(sample_analysis))
        second_analysis['analysis_id'] = "ANALYSIS_002"
        second_analysis['confidence_score'] = 0.88
        store.store(second_analysis)
        
        # Should get the latest one (ANALYSIS_002)
        retrieved = store.get_by_transcript_id(sample_analysis['transcript_id'])
        assert retrieved['analysis_id'] == "ANALYSIS_002"
        assert retrieved['confidence_score'] == 0.88
    
    def test_get_all(self, temp_db, sample_analysis, high_risk_analysis):
        """Test getting all analyses."""
        store = AnalysisStore(temp_db)
        
        # Store multiple analyses
        store.store(sample_analysis)
        store.store(high_risk_analysis)
        
        # Get all
        all_analyses = store.get_all()
        
        assert len(all_analyses) == 2
        
        # Should be ordered by created_at DESC (newest first)
        analysis_ids = [a['analysis_id'] for a in all_analyses]
        assert high_risk_analysis['analysis_id'] in analysis_ids
        assert sample_analysis['analysis_id'] in analysis_ids
    
    def test_get_all_with_limit(self, temp_db):
        """Test getting analyses with limit."""
        store = AnalysisStore(temp_db)
        
        # Store multiple analyses
        for i in range(5):
            analysis = {
                "analysis_id": f"ANALYSIS_{i:03d}",
                "transcript_id": f"CALL_{i:03d}",
                "call_summary": f"Call summary {i}",
                "primary_intent": "test",
                "urgency_level": "low",
                "borrower_sentiment": {"overall": "neutral", "start": "neutral", "end": "neutral", "trend": "stable"},
                "borrower_risks": {"delinquency_risk": 0.1, "churn_risk": 0.1, "complaint_risk": 0.1, "refinance_likelihood": 0.1},
                "advisor_metrics": {"empathy_score": 5, "compliance_adherence": 5, "solution_effectiveness": 5, "coaching_opportunities": []},
                "compliance_flags": [],
                "required_disclosures": [],
                "issue_resolved": False,
                "first_call_resolution": False,
                "escalation_needed": False,
                "topics_discussed": [],
                "confidence_score": 0.8,
                "product_opportunities": [],
                "payment_concerns": [],
                "property_related_issues": []
            }
            store.store(analysis)
        
        # Get with limit
        limited = store.get_all(limit=3)
        assert len(limited) == 3
    
    def test_get_metrics_summary_empty(self, temp_db):
        """Test metrics summary with no data."""
        store = AnalysisStore(temp_db)
        
        metrics = store.get_metrics_summary()
        
        assert metrics['total_analyses'] == 0
        assert metrics['avg_confidence_score'] == 0
        assert metrics['escalation_rate'] == 0
        assert metrics['first_call_resolution_rate'] == 0
        assert metrics['avg_empathy_score'] == 0
        assert metrics['top_intents'] == {}
    
    def test_get_metrics_summary_with_data(self, temp_db, sample_analysis, high_risk_analysis):
        """Test metrics summary with sample data."""
        store = AnalysisStore(temp_db)
        
        # Store analyses
        store.store(sample_analysis)
        store.store(high_risk_analysis)
        
        metrics = store.get_metrics_summary()
        
        assert metrics['total_analyses'] == 2
        assert metrics['avg_confidence_score'] == 0.9  # (0.92 + 0.88) / 2
        assert metrics['escalation_rate'] == 50.0  # 1 out of 2 needs escalation
        assert metrics['first_call_resolution_rate'] == 0.0  # Neither resolved
        assert metrics['avg_empathy_score'] == 9.0  # (8.5 + 9.5) / 2
        assert metrics['avg_delinquency_risk'] == 0.5  # (0.15 + 0.85) / 2
        assert metrics['avg_churn_risk'] == 0.42  # (0.25 + 0.60) / 2 = 0.425, rounded to 0.42
        
        # Check intent distribution
        assert 'PMI removal' in metrics['top_intents']
        assert 'hardship assistance' in metrics['top_intents']
        assert metrics['top_intents']['PMI removal'] == 1
        assert metrics['top_intents']['hardship assistance'] == 1
        
        # Check urgency distribution
        assert 'medium' in metrics['urgency_distribution']
        assert 'high' in metrics['urgency_distribution']
    
    def test_get_risk_reports(self, temp_db, sample_analysis, high_risk_analysis):
        """Test risk reporting functionality."""
        store = AnalysisStore(temp_db)
        
        # Store analyses
        store.store(sample_analysis)
        store.store(high_risk_analysis)
        
        # Get risk report with threshold 0.7
        risk_report = store.get_risk_reports(risk_threshold=0.7)
        
        # Should find high delinquency risk case
        high_delinquency = risk_report['high_delinquency_risk']
        assert len(high_delinquency) == 1
        assert high_delinquency[0]['transcript_id'] == 'CALL_HARDSHIP_001'
        assert high_delinquency[0]['delinquency_risk'] == 0.85
        assert high_delinquency[0]['primary_intent'] == 'hardship assistance'
        
        # Should not find high churn risk cases above 0.7
        high_churn = risk_report['high_churn_risk']
        assert len(high_churn) == 0  # 0.60 and 0.25 are both below 0.7
    
    def test_get_risk_reports_lower_threshold(self, temp_db, sample_analysis, high_risk_analysis):
        """Test risk reporting with lower threshold."""
        store = AnalysisStore(temp_db)
        
        # Store analyses
        store.store(sample_analysis)
        store.store(high_risk_analysis)
        
        # Get risk report with threshold 0.5
        risk_report = store.get_risk_reports(risk_threshold=0.5)
        
        # Should find high churn risk case now
        high_churn = risk_report['high_churn_risk']
        assert len(high_churn) == 1
        assert high_churn[0]['transcript_id'] == 'CALL_HARDSHIP_001'
        assert high_churn[0]['churn_risk'] == 0.60
    
    def test_delete_analysis(self, temp_db, sample_analysis):
        """Test deleting analysis."""
        store = AnalysisStore(temp_db)
        
        # Store analysis
        store.store(sample_analysis)
        
        # Verify it exists
        retrieved = store.get_by_id(sample_analysis['analysis_id'])
        assert retrieved is not None
        
        # Delete it
        deleted = store.delete(sample_analysis['analysis_id'])
        assert deleted is True
        
        # Verify it's gone
        retrieved = store.get_by_id(sample_analysis['analysis_id'])
        assert retrieved is None
        
        # Delete non-existent should return False
        deleted_again = store.delete(sample_analysis['analysis_id'])
        assert deleted_again is False
    
    def test_delete_all(self, temp_db, sample_analysis, high_risk_analysis):
        """Test deleting all analyses."""
        store = AnalysisStore(temp_db)
        
        # Store analyses
        store.store(sample_analysis)
        store.store(high_risk_analysis)
        
        # Verify they exist
        all_analyses = store.get_all()
        assert len(all_analyses) == 2
        
        # Delete all
        deleted_count = store.delete_all()
        assert deleted_count == 2
        
        # Verify they're gone
        all_analyses = store.get_all()
        assert len(all_analyses) == 0
        
        # Delete all on empty should return 0
        deleted_count = store.delete_all()
        assert deleted_count == 0