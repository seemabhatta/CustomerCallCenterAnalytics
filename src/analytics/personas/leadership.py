"""
Leadership persona: Focus on portfolio risk, financial impact, strategic decisions.

Transforms data to answer:
- How much money is at risk?
- What decisions need my approval TODAY?
- What's the ROI of proposed actions?
- Are we compliant?
"""

from typing import Dict, Any, List
import json
from datetime import datetime, timedelta

from .base_persona import BasePersona


class LeadershipPersona(BasePersona):
    """
    Leadership-focused data transformations.

    Key concerns: $$$ impact, strategic decisions, compliance, portfolio health
    """

    # Industry averages for estimation
    AVG_LOAN_BALANCE = 250000  # $250K average mortgage
    AVG_SERVICING_FEE_ANNUAL = 250  # $250/year servicing fee per loan
    DELINQUENCY_LOSS_RATE = 0.15  # 15% loss on defaulted loans
    CHURN_REVENUE_LOSS = 250  # Lost servicing fees per churned loan
    COMPLIANCE_FINE_PER_ISSUE = 5000  # Estimated fine per compliance breach

    def transform_forecast(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform forecast to show dollar impact and strategic implications.

        Args:
            forecast: Raw Prophet forecast

        Returns:
            Leadership-focused forecast view
        """
        forecast_type = forecast.get('forecast_type', '')
        summary = forecast.get('summary', {})

        # Calculate financial impact based on forecast type
        financial_impact = self._calculate_financial_impact(forecast)

        return {
            'forecast_summary': {
                'metric': forecast_type.replace('_', ' ').title(),
                'current_level': summary.get('average_predicted'),
                'trend': self._determine_trend(forecast),
                'confidence': 'high' if forecast.get('cached') else 'medium'
            },
            'financial_impact': financial_impact,
            'strategic_implications': self._derive_implications(forecast),
            'raw_forecast': forecast  # Include for drill-down
        }

    def _calculate_financial_impact(self, forecast: Dict[str, Any]) -> Dict[str, float]:
        """
        Convert forecast metrics to dollar estimates.

        Args:
            forecast: Prophet forecast

        Returns:
            Financial impact estimates
        """
        forecast_type = forecast.get('forecast_type', '')
        summary = forecast.get('summary', {})
        avg_value = summary.get('average_predicted', 0)

        impact = {}

        if 'churn' in forecast_type:
            # Churn risk: Lost servicing revenue
            # Get customer count
            result = self._query_db_one("""
                SELECT COUNT(DISTINCT customer_id)
                FROM transcripts
            """)
            customer_count = result[0] if result else 0

            # Estimate churned customers
            churned_count = int(customer_count * avg_value)
            impact['lost_revenue'] = churned_count * self.CHURN_REVENUE_LOSS
            impact['at_risk_customers'] = churned_count

        elif 'delinquency' in forecast_type:
            # Delinquency risk: Potential loan losses
            result = self._query_db_one("""
                SELECT COUNT(DISTINCT customer_id)
                FROM transcripts
            """)
            customer_count = result[0] if result else 0

            high_risk_count = int(customer_count * avg_value)
            potential_loss = high_risk_count * self.AVG_LOAN_BALANCE * self.DELINQUENCY_LOSS_RATE
            impact['potential_loss'] = potential_loss
            impact['at_risk_portfolio'] = high_risk_count * self.AVG_LOAN_BALANCE

        elif 'call_volume' in forecast_type:
            # Call volume: Staffing cost impact
            avg_calls = avg_value
            # Assume $25/call handling cost
            impact['monthly_cost'] = avg_calls * 30 * 25

        else:
            # Generic: Use as percentage of portfolio
            result = self._query_db_one("""
                SELECT COUNT(DISTINCT customer_id)
                FROM transcripts
            """)
            customer_count = result[0] if result else 0
            impact['estimated_impact'] = customer_count * avg_value * 100

        return impact

    def _determine_trend(self, forecast: Dict[str, Any]) -> str:
        """
        Determine if forecast shows increasing, decreasing, or stable trend.

        Args:
            forecast: Prophet forecast

        Returns:
            Trend description
        """
        predictions = forecast.get('predictions', [])
        if len(predictions) < 2:
            return 'stable'

        first_val = predictions[0].get('predicted', 0)
        last_val = predictions[-1].get('predicted', 0)

        change_pct = ((last_val - first_val) / first_val * 100) if first_val > 0 else 0

        if change_pct > 10:
            return 'increasing'
        elif change_pct < -10:
            return 'decreasing'
        else:
            return 'stable'

    def _derive_implications(self, forecast: Dict[str, Any]) -> List[str]:
        """
        Derive strategic implications from forecast.

        Args:
            forecast: Prophet forecast

        Returns:
            List of strategic implications
        """
        forecast_type = forecast.get('forecast_type', '')
        trend = self._determine_trend(forecast)
        implications = []

        if 'churn' in forecast_type and trend == 'increasing':
            implications.append("Retention campaigns should be accelerated")
            implications.append("Rate competitiveness review recommended")

        if 'delinquency' in forecast_type and trend == 'increasing':
            implications.append("Hardship assistance outreach needed")
            implications.append("Loss mitigation resources should be scaled")

        if 'call_volume' in forecast_type and trend == 'increasing':
            implications.append("Staffing levels may need adjustment")
            implications.append("Consider temporary contractor support")

        if 'compliance' in forecast_type and trend == 'decreasing':
            implications.append("Compliance training effectiveness declining")
            implications.append("Review disclosure processes")

        return implications or ["Monitor trends for changes"]

    def get_key_metrics(self) -> Dict[str, Any]:
        """
        Get leadership dashboard metrics.

        Returns:
            Key metrics for leadership view
        """
        # Portfolio at risk
        result = self._query_db_one("""
            SELECT
                COUNT(DISTINCT t.customer_id) as total_customers,
                AVG(a.delinquency_risk) as avg_delinq_risk,
                AVG(a.churn_risk) as avg_churn_risk,
                SUM(CASE WHEN a.delinquency_risk > 0.7 THEN 1 ELSE 0 END) as high_risk_count
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
        """)

        total_customers = result[0] if result else 0
        avg_delinq = result[1] if result and result[1] else 0
        avg_churn = result[2] if result and result[2] else 0
        high_risk_count = result[3] if result and result[3] else 0

        # Dollar calculations
        portfolio_value = total_customers * self.AVG_LOAN_BALANCE
        at_risk_amount = portfolio_value * avg_delinq
        churn_revenue_at_risk = total_customers * avg_churn * self.CHURN_REVENUE_LOSS

        # Compliance
        result = self._query_db_one("""
            SELECT AVG(compliance_adherence)
            FROM analysis
            WHERE created_at >= datetime('now', '-7 days')
        """)
        compliance_score = result[0] if result and result[0] else 0

        # Workflow efficiency
        result = self._query_db_one("""
            SELECT
                COUNT(*) as total_workflows,
                SUM(CASE WHEN status = 'EXECUTED' THEN 1 ELSE 0 END) as executed,
                SUM(CASE WHEN status = 'AWAITING_APPROVAL' THEN 1 ELSE 0 END) as pending_approval
            FROM workflows
            WHERE created_at >= datetime('now', '-7 days')
        """)
        total_wf = result[0] if result else 0
        executed_wf = result[1] if result and result[1] else 0
        pending_wf = result[2] if result and result[2] else 0

        # Compliance incidents (last 30 days)
        result = self._query_db_one("""
            SELECT SUM(COALESCE(compliance_issues, 0))
            FROM analysis
            WHERE created_at >= datetime('now', '-30 days')
        """)
        compliance_issues = result[0] if result and result[0] else 0
        compliance_penalty = compliance_issues * self.COMPLIANCE_FINE_PER_ISSUE

        # Risk trend (compare last 7 days vs previous period)
        recent = self._query_db_one("""
            SELECT AVG(delinquency_risk)
            FROM analysis
            WHERE created_at >= datetime('now', '-7 days')
        """)
        prev = self._query_db_one("""
            SELECT AVG(delinquency_risk)
            FROM analysis
            WHERE created_at >= datetime('now', '-14 days')
              AND created_at < datetime('now', '-7 days')
        """)

        recent_delinq = recent[0] if recent and recent[0] is not None else 0
        previous_delinq = prev[0] if prev and prev[0] is not None else 0
        delta = recent_delinq - previous_delinq
        delta_pct = None
        if previous_delinq:
            delta_pct = delta / previous_delinq

        return {
            'portfolio': {
                'total_customers': total_customers,
                'portfolio_value': portfolio_value,
                'at_risk_amount': at_risk_amount,
                'high_risk_customers': high_risk_count
            },
            'risk_scores': {
                'avg_delinquency_risk': avg_delinq,
                'avg_churn_risk': avg_churn,
                'churn_revenue_at_risk': churn_revenue_at_risk
            },
            'compliance': {
                'compliance_score': compliance_score,
                'status': 'good' if compliance_score > 0.9 else 'needs_attention',
                'issue_count': compliance_issues,
                'estimated_penalty': compliance_penalty
            },
            'operational_efficiency': {
                'workflows_last_7d': total_wf,
                'execution_rate': (executed_wf / total_wf * 100) if total_wf > 0 else 0,
                'pending_decisions': pending_wf
            },
            'trend_metrics': {
                'recent_delinquency': recent_delinq,
                'previous_delinquency': previous_delinq,
                'delta': delta,
                'delta_pct': delta_pct
            }
        }

    def get_recommended_actions(self) -> List[Dict[str, Any]]:
        """
        Get actions requiring leadership decision/approval.

        Returns:
            List of recommended actions with ROI estimates
        """
        actions = []

        # High churn risk → Retention campaign
        result = self._query_db_one("""
            SELECT COUNT(*)
            FROM analysis
            WHERE churn_risk > 0.7
            AND created_at >= datetime('now', '-7 days')
        """)
        high_churn_count = result[0] if result else 0

        if high_churn_count > 10:
            actions.append({
                'id': 'retention_campaign',
                'title': 'Launch Retention Campaign',
                'type': 'campaign_approval',
                'urgency': 'high',
                'target_count': high_churn_count,
                'expected_impact': high_churn_count * self.CHURN_REVENUE_LOSS * 0.7,  # 70% retention
                'cost_estimate': high_churn_count * 15,  # $15/customer outreach
                'roi': 30,  # 30:1 ROI
                'recommendation': 'Approve immediately - high ROI retention opportunity'
            })

        # High delinquency → Hardship outreach
        result = self._query_db_one("""
            SELECT COUNT(*)
            FROM analysis
            WHERE delinquency_risk > 0.7
            AND created_at >= datetime('now', '-7 days')
        """)
        high_delinq_count = result[0] if result else 0

        if high_delinq_count > 10:
            potential_loss = high_delinq_count * self.AVG_LOAN_BALANCE * self.DELINQUENCY_LOSS_RATE
            actions.append({
                'id': 'hardship_campaign',
                'title': 'Hardship Assistance Outreach',
                'type': 'campaign_approval',
                'urgency': 'high',
                'target_count': high_delinq_count,
                'expected_impact': potential_loss * 0.6,  # 60% prevention
                'cost_estimate': high_delinq_count * 20,
                'roi': 150,  # Very high ROI
                'recommendation': 'Approve - prevents significant portfolio losses'
            })

        # Compliance issues → Training
        result = self._query_db_one("""
            SELECT COUNT(DISTINCT t.advisor_id)
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE a.compliance_adherence < 0.75
            AND t.advisor_id IS NOT NULL
        """)
        low_compliance_advisors = result[0] if result else 0

        if low_compliance_advisors > 5:
            actions.append({
                'id': 'compliance_training',
                'title': 'Mandatory Compliance Training',
                'type': 'policy_enforcement',
                'urgency': 'medium',
                'target_count': low_compliance_advisors,
                'expected_impact': 50000,  # Avoid regulatory fines
                'cost_estimate': low_compliance_advisors * 500,  # Training cost
                'roi': 20,
                'recommendation': 'Schedule within 2 weeks to mitigate regulatory risk'
            })

        return actions

    def get_decision_queue(self) -> List[Dict[str, Any]]:
        """
        Get items requiring executive decision TODAY.

        Returns:
            Prioritized decision queue
        """
        decisions = []

        # Workflows awaiting approval
        results = self._query_db("""
            SELECT id, workflow_type, created_at, risk_level
            FROM workflows
            WHERE status = 'AWAITING_APPROVAL'
            ORDER BY created_at ASC
            LIMIT 10
        """)

        for row in results:
            decisions.append({
                'id': row[0],
                'type': 'workflow_approval',
                'workflow_type': row[1],
                'waiting_since': row[2],
                'risk_level': row[3],
                'urgency': 'high' if row[3] in ['HIGH', 'CRITICAL'] else 'medium'
            })

        # Add recommended actions
        decisions.extend(self.get_recommended_actions())

        # Sort by urgency
        urgency_order = {'high': 0, 'medium': 1, 'low': 2}
        decisions.sort(key=lambda x: urgency_order.get(x.get('urgency', 'low'), 3))

        return decisions
