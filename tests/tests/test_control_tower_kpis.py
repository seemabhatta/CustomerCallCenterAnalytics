"""
Test cases for Control Tower KPI row functionality.

Following TDD principles:
1. Write tests first
2. Tests define expected behavior
3. Implementation follows tests

Core Principle: NO FALLBACK - fail fast on missing data
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta


class TestControlTowerKPIs:
    """Test suite for Control Tower KPI row calculations."""

    @pytest.fixture
    def mock_db_connection(self):
        """Mock database connection."""
        with patch('sqlite3.connect') as mock_conn:
            # Create mock cursor with default return values
            mock_cursor = Mock()
            mock_cursor.fetchone = Mock(return_value=(85,))  # Default sentiment score
            mock_cursor.fetchall = Mock(return_value=[])
            mock_conn.return_value.__enter__.return_value.cursor.return_value = mock_cursor
            yield mock_conn

    @pytest.fixture
    def intelligence_service(self, mock_db_connection):
        """Create intelligence service instance for testing."""
        from src.services.intelligence_service import IntelligenceService
        from src.analytics.intelligence.hybrid_analyzer import HybridAnalyzer
        from src.services.forecasting_service import ForecastingService
        from src.storage.insight_store import InsightStore

        # Mock dependencies
        forecasting_service = Mock(spec=ForecastingService)
        hybrid_analyzer = Mock(spec=HybridAnalyzer)
        hybrid_analyzer.forecasting_service = forecasting_service
        insight_store = Mock(spec=InsightStore)

        service = IntelligenceService(
            hybrid_analyzer=hybrid_analyzer,
            insight_store=insight_store,
            db_path=":memory:"
        )

        # Mock persona responses with realistic data
        service.leadership.get_key_metrics = Mock(return_value={
            'portfolio': {
                'total_customers': 1000,
                'portfolio_value': 250000000,
                'at_risk_amount': 5000000,
                'high_risk_customers': 50
            },
            'risk_scores': {
                'avg_delinquency_risk': 0.15,
                'avg_churn_risk': 0.08,
                'churn_revenue_at_risk': 20000
            },
            'compliance': {
                'compliance_score': 0.92,
                'status': 'good',
                'issue_count': 2,
                'estimated_penalty': 10000
            },
            'operational_efficiency': {
                'workflows_last_7d': 100,
                'execution_rate': 95.0,
                'pending_decisions': 5
            },
            'trend_metrics': {
                'recent_delinquency': 0.15,
                'previous_delinquency': 0.14,
                'delta': 0.01,
                'delta_pct': 0.071
            }
        })

        service.servicing_ops.get_key_metrics = Mock(return_value={
            'sla_performance': {
                'fcr_rate': 87.5,
                'fcr_target': 85.0,
                'fcr_status': 'on_track',
                'escalation_rate': 8.5,
                'escalation_target': 10.0,
                'escalation_status': 'good',
                'compliance_score': 0.92
            },
            'volume_metrics': {
                'current_capacity': 50,
                'avg_calls_per_hour': 25
            },
            'team_performance': {
                'total_advisors': 20,
                'advisors_needing_coaching': 3,
                'avg_empathy_score': 8.2,
                'avg_compliance_score': 0.91,
                'team_health': 'good'
            }
        })

        service.marketing.get_key_metrics = Mock(return_value={
            'opportunity_value': {
                'refi_ready': 50000,
                'at_risk': 30000,
                'loyal_champions': 40000
            },
            'segment_summary': {
                'total_segments': 3,
                'high_value_count': 100
            }
        })

        service.leadership.get_decision_queue = Mock(return_value=[
            {
                'id': 'decision_1',
                'title': 'Approve retention campaign',
                'urgency': 'high',
                'expected_impact': 50000,
                'type': 'campaign_approval'
            },
            {
                'id': 'decision_2',
                'title': 'Review compliance training',
                'urgency': 'medium',
                'expected_impact': 25000,
                'type': 'policy_enforcement'
            }
        ])

        return service

    # ============================================================
    # Customer Health Index Tests
    # ============================================================

    @pytest.mark.asyncio
    async def test_customer_health_index_calculation(self, intelligence_service):
        """Test Customer Health Index composite score calculation.

        Formula: Weighted average of:
        - FCR rate (30%)
        - CSAT score (25%)
        - Churn risk (25% - inverted)
        - Delinquency risk (20% - inverted)
        """
        # Expected behavior: Calculate composite from multiple metrics
        result = await intelligence_service.get_control_tower_kpis()

        assert 'customer_health_index' in result
        assert 'score' in result['customer_health_index']
        assert 'trend' in result['customer_health_index']
        assert 'components' in result['customer_health_index']

        # Score should be 0-100
        score = result['customer_health_index']['score']
        assert 0 <= score <= 100

        # Components breakdown
        components = result['customer_health_index']['components']
        assert 'fcr_contribution' in components
        assert 'csat_contribution' in components
        assert 'churn_contribution' in components
        assert 'delinquency_contribution' in components

    @pytest.mark.asyncio
    async def test_customer_health_trend_detection(self, intelligence_service):
        """Test trend detection for Customer Health Index."""
        result = await intelligence_service.get_control_tower_kpis()

        trend = result['customer_health_index']['trend']
        assert trend in ['improving', 'declining', 'stable']

        # Should include variance percentage
        assert 'variance_pct' in result['customer_health_index']

    @pytest.mark.asyncio
    async def test_customer_health_fails_on_missing_data(self, intelligence_service):
        """Test that Customer Health Index fails fast when data is missing.

        NO FALLBACK principle: Should raise exception, not return 0 or default.
        """
        # Mock empty database
        with patch.object(intelligence_service.leadership, '_query_db_one', return_value=None):
            with pytest.raises(Exception) as exc_info:
                await intelligence_service.get_control_tower_kpis()

            assert "insufficient data" in str(exc_info.value).lower() or "failed" in str(exc_info.value).lower()

    # ============================================================
    # Revenue Momentum Tests
    # ============================================================

    @pytest.mark.asyncio
    async def test_revenue_momentum_calculation(self, intelligence_service):
        """Test Revenue Momentum calculation.

        Should aggregate:
        - Refi opportunity revenue
        - Retention campaign impact
        - Referral revenue
        """
        result = await intelligence_service.get_control_tower_kpis()

        assert 'revenue_momentum' in result
        assert 'total_lift' in result['revenue_momentum']
        assert 'trend' in result['revenue_momentum']
        assert 'breakdown' in result['revenue_momentum']

        breakdown = result['revenue_momentum']['breakdown']
        assert 'refi_opportunity' in breakdown
        assert 'retention_impact' in breakdown
        assert 'referral_revenue' in breakdown

    @pytest.mark.asyncio
    async def test_revenue_momentum_trend_analysis(self, intelligence_service):
        """Test revenue momentum trend (WoW, MoM comparison)."""
        result = await intelligence_service.get_control_tower_kpis()

        revenue = result['revenue_momentum']
        assert 'wow_change_pct' in revenue  # Week over week
        assert 'mom_change_pct' in revenue  # Month over month

        # Trend should be descriptive
        assert revenue['trend'] in ['accelerating', 'stable', 'declining']

    # ============================================================
    # Operational Efficiency Tests
    # ============================================================

    @pytest.mark.asyncio
    async def test_operational_efficiency_metrics(self, intelligence_service):
        """Test Operational Efficiency calculation.

        Should include:
        - SLA % (FCR, response time)
        - Cases resolved per FTE
        - Cost per loan serviced
        """
        result = await intelligence_service.get_control_tower_kpis()

        assert 'operational_efficiency' in result
        efficiency = result['operational_efficiency']

        assert 'sla_percentage' in efficiency
        assert 'cases_per_fte' in efficiency
        assert 'cost_per_loan' in efficiency
        assert 'trend' in efficiency

        # SLA should be 0-100%
        assert 0 <= efficiency['sla_percentage'] <= 100

    @pytest.mark.asyncio
    async def test_operational_efficiency_vs_target(self, intelligence_service):
        """Test operational efficiency vs plan/target comparison."""
        result = await intelligence_service.get_control_tower_kpis()

        efficiency = result['operational_efficiency']
        assert 'variance_vs_plan' in efficiency
        assert 'status' in efficiency

        # Status should indicate performance
        assert efficiency['status'] in ['on_track', 'below_target', 'exceeding']

    # ============================================================
    # Compliance Posture Tests
    # ============================================================

    @pytest.mark.asyncio
    async def test_compliance_posture_calculation(self, intelligence_service):
        """Test Compliance Posture metrics.

        Should include:
        - Audit pass percentage
        - Open exceptions count
        - Compliance score
        """
        result = await intelligence_service.get_control_tower_kpis()

        assert 'compliance_posture' in result
        compliance = result['compliance_posture']

        assert 'audit_pass_rate' in compliance
        assert 'open_exceptions' in compliance
        assert 'compliance_score' in compliance
        assert 'status' in compliance

        # Audit pass rate should be percentage
        assert 0 <= compliance['audit_pass_rate'] <= 100

    @pytest.mark.asyncio
    async def test_compliance_posture_risk_level(self, intelligence_service):
        """Test compliance posture risk level determination."""
        result = await intelligence_service.get_control_tower_kpis()

        compliance = result['compliance_posture']
        assert 'risk_level' in compliance
        assert compliance['risk_level'] in ['low', 'medium', 'high', 'critical']

    # ============================================================
    # Integration Tests
    # ============================================================

    @pytest.mark.asyncio
    async def test_complete_kpi_row_structure(self, intelligence_service):
        """Test complete KPI row returns all required components."""
        result = await intelligence_service.get_control_tower_kpis()

        # All 4 KPIs must be present
        assert 'customer_health_index' in result
        assert 'revenue_momentum' in result
        assert 'operational_efficiency' in result
        assert 'compliance_posture' in result

        # Metadata
        assert 'generated_at' in result
        assert 'data_freshness' in result

    @pytest.mark.asyncio
    async def test_kpi_row_performance(self, intelligence_service):
        """Test KPI row generation performance (<500ms target)."""
        import time

        start = time.time()
        result = await intelligence_service.get_control_tower_kpis()
        duration_ms = (time.time() - start) * 1000

        # Should complete in under 500ms
        assert duration_ms < 500, f"KPI generation took {duration_ms}ms, should be <500ms"

    @pytest.mark.asyncio
    async def test_kpi_caching_behavior(self, intelligence_service):
        """Test that KPI results are properly cached."""
        # First call - should hit database
        result1 = await intelligence_service.get_control_tower_kpis()

        # Second call - should use cache
        result2 = await intelligence_service.get_control_tower_kpis()

        # Results should be identical when cached
        assert result1['customer_health_index']['score'] == result2['customer_health_index']['score']

    @pytest.mark.asyncio
    async def test_kpi_real_time_vs_cached(self, intelligence_service):
        """Test ability to force real-time calculation bypassing cache."""
        # Cached version
        cached = await intelligence_service.get_control_tower_kpis(use_cache=True)

        # Real-time version
        realtime = await intelligence_service.get_control_tower_kpis(use_cache=False)

        # Both should have valid structure
        assert 'customer_health_index' in cached
        assert 'customer_health_index' in realtime

    # ============================================================
    # Error Handling Tests (NO FALLBACK Principle)
    # ============================================================

    @pytest.mark.asyncio
    async def test_fails_on_database_error(self, intelligence_service):
        """Test that database errors cause failure, not degradation."""
        with patch('sqlite3.connect', side_effect=Exception("DB connection failed")):
            with pytest.raises(Exception) as exc_info:
                await intelligence_service.get_control_tower_kpis()

            assert "DB connection failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_fails_on_invalid_metrics(self, intelligence_service):
        """Test that invalid metric values cause failure."""
        # Mock invalid SLA data (>100%)
        with patch.object(intelligence_service.servicing_ops, 'get_key_metrics',
                         return_value={'sla_performance': {'fcr_rate': 150}}):
            with pytest.raises(ValueError) as exc_info:
                await intelligence_service.get_control_tower_kpis()

            assert "invalid" in str(exc_info.value).lower() or "range" in str(exc_info.value).lower()


class TestControlTowerExecutiveSummary:
    """Test suite for Executive Narrative Summary generation."""

    @pytest.fixture
    def intelligence_service(self):
        """Create intelligence service for testing."""
        from src.services.intelligence_service import IntelligenceService
        from unittest.mock import Mock

        service = Mock(spec=IntelligenceService)
        return service

    @pytest.mark.asyncio
    async def test_executive_summary_generation(self, intelligence_service):
        """Test auto-generated executive summary narrative."""
        # Mock KPI data
        kpi_data = {
            'customer_health_index': {'score': 82.3, 'trend': 'stable'},
            'revenue_momentum': {'total_lift': 18000, 'trend': 'accelerating'},
            'operational_efficiency': {'sla_percentage': 89, 'trend': 'declining'},
            'compliance_posture': {'status': 'green', 'open_exceptions': 0}
        }

        intelligence_service.get_control_tower_kpis = AsyncMock(return_value=kpi_data)

        from src.services.intelligence_service import IntelligenceService
        real_service = IntelligenceService(
            hybrid_analyzer=Mock(),
            insight_store=Mock()
        )

        summary = await real_service.get_executive_summary()

        assert 'narrative' in summary
        assert 'key_points' in summary
        assert 'urgent_actions' in summary

        # Narrative should be concise (1-3 sentences)
        narrative_sentences = summary['narrative'].count('.')
        assert 1 <= narrative_sentences <= 3

    @pytest.mark.asyncio
    async def test_executive_summary_highlights_risks(self, intelligence_service):
        """Test that summary highlights critical risks and opportunities."""
        summary = await intelligence_service.get_executive_summary()

        if 'risks' in summary:
            assert isinstance(summary['risks'], list)

        if 'opportunities' in summary:
            assert isinstance(summary['opportunities'], list)
