"""
Marketing persona: Focus on customer segments, campaigns, churn prevention, revenue opportunities.

Transforms data to answer:
- Who should we target next?
- Which campaigns are working?
- Where are we losing customers?
- What's the ROI?
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from .base_persona import BasePersona


class MarketingPersona(BasePersona):
    """
    Marketing-focused data transformations.

    Key concerns: Segmentation, campaign ROI, churn prevention, customer lifetime value
    """

    # Financial assumptions
    AVG_LOAN_BALANCE = 250000
    AVG_SERVICING_FEE_ANNUAL = 250
    REFI_REVENUE_PER_LOAN = 2800
    CAMPAIGN_COST_PER_CONTACT = 15  # Email + SMS + potential call

    def transform_forecast(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform forecast to show marketing opportunities.

        Args:
            forecast: Raw Prophet forecast

        Returns:
            Marketing-focused forecast view
        """
        forecast_type = forecast.get('forecast_type', '')
        summary = forecast.get('summary', {})

        # Churn forecast → Retention opportunity
        if 'churn' in forecast_type:
            opportunity = self._calculate_retention_opportunity(forecast)

            return {
                'churn_prediction': {
                    'average_rate': summary.get('average_predicted'),
                    'trend': self._determine_trend(forecast.get('predictions', [])),
                    'high_risk_segment_size': opportunity['target_count']
                },
                'retention_opportunity': opportunity,
                'raw_forecast': forecast
            }

        # Sentiment → Satisfaction campaigns
        elif 'sentiment' in forecast_type:
            return {
                'sentiment_trend': {
                    'current': summary.get('average_predicted'),
                    'direction': self._determine_trend(forecast.get('predictions', []))
                },
                'engagement_opportunity': self._identify_engagement_campaigns(),
                'raw_forecast': forecast
            }

        return {
            'forecast_summary': forecast,
            'marketing_implication': 'Monitor for campaign opportunities'
        }

    def _determine_trend(self, predictions: List[Dict[str, Any]]) -> str:
        """Determine trend direction."""
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

    def _calculate_retention_opportunity(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate retention campaign opportunity from churn forecast.

        Args:
            forecast: Churn risk forecast

        Returns:
            Retention opportunity details
        """
        avg_churn_rate = forecast.get('summary', {}).get('average_predicted', 0)

        # Get high-risk customers
        result = self._query_db_one("""
            SELECT COUNT(DISTINCT t.customer_id)
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE a.churn_risk > 0.7
        """)
        high_risk_count = result[0] if result else 0

        # Calculate value
        lost_revenue = high_risk_count * self.AVG_SERVICING_FEE_ANNUAL
        campaign_cost = high_risk_count * self.CAMPAIGN_COST_PER_CONTACT
        expected_retention_rate = 0.65  # 65% retention with good campaign
        expected_save = lost_revenue * expected_retention_rate
        roi = (expected_save / campaign_cost) if campaign_cost > 0 else 0

        return {
            'target_count': high_risk_count,
            'lost_revenue_at_risk': lost_revenue,
            'campaign_cost': campaign_cost,
            'expected_retention_rate': expected_retention_rate,
            'expected_save': expected_save,
            'roi': round(roi, 1),
            'recommendation': 'Launch retention campaign' if roi > 5 else 'Monitor'
        }

    def _identify_engagement_campaigns(self) -> Dict[str, Any]:
        """Identify customer engagement opportunities."""
        # Look for positive sentiment customers (upsell opportunity)
        result = self._query_db_one("""
            SELECT COUNT(DISTINCT t.customer_id)
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE a.borrower_sentiment = 'Positive'
            AND t.timestamp >= datetime('now', '-30 days')
        """)
        positive_customers = result[0] if result else 0

        return {
            'satisfied_customers': positive_customers,
            'opportunity_type': 'referral_program',
            'estimated_response_rate': 0.25,
            'recommendation': f'Launch referral campaign to {positive_customers} satisfied customers'
        }

    def get_key_metrics(self) -> Dict[str, Any]:
        """
        Get marketing dashboard metrics.

        Returns:
            Key metrics for marketing view
        """
        # Segment sizes
        result = self._query_db_one("""
            SELECT COUNT(DISTINCT customer_id)
            FROM transcripts
        """)
        total_customers = result[0] if result else 0

        # High-value segments
        result = self._query_db_one("""
            SELECT
                COUNT(DISTINCT t.customer_id) as refi_ready,
                AVG(a.refinance_likelihood) as avg_refi_likelihood
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE a.refinance_likelihood > 0.7
        """)
        refi_ready = result[0] if result and result[0] else 0
        avg_refi_likelihood = result[1] if result and result[1] else 0

        # At-risk segment
        result = self._query_db_one("""
            SELECT COUNT(DISTINCT t.customer_id)
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE a.churn_risk > 0.6 OR a.delinquency_risk > 0.6
        """)
        at_risk = result[0] if result else 0

        # Loyal segment
        result = self._query_db_one("""
            SELECT COUNT(DISTINCT t.customer_id)
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE a.churn_risk < 0.3
            AND a.borrower_sentiment IN ('Positive', 'Satisfied')
        """)
        loyal = result[0] if result else 0

        return {
            'segment_overview': {
                'total_customers': total_customers,
                'refi_ready': refi_ready,
                'at_risk': at_risk,
                'loyal': loyal,
                'uncategorized': total_customers - refi_ready - at_risk - loyal
            },
            'opportunity_value': {
                'refi_revenue_potential': refi_ready * self.REFI_REVENUE_PER_LOAN,
                'retention_value_at_risk': at_risk * self.AVG_SERVICING_FEE_ANNUAL,
                'referral_potential': loyal * 0.25 * self.REFI_REVENUE_PER_LOAN  # 25% referral rate
            },
            'engagement_scores': {
                'avg_refi_likelihood': avg_refi_likelihood
            }
        }

    def get_recommended_actions(self) -> List[Dict[str, Any]]:
        """
        Get marketing campaign recommendations.

        Returns:
            List of recommended campaigns with ROI
        """
        actions = []
        metrics = self.get_key_metrics()

        # Refi campaign
        refi_ready = metrics['segment_overview']['refi_ready']
        if refi_ready > 20:
            refi_revenue = metrics['opportunity_value']['refi_revenue_potential']
            campaign_cost = refi_ready * self.CAMPAIGN_COST_PER_CONTACT
            expected_conversion = 0.25  # 25% conversion
            expected_revenue = refi_revenue * expected_conversion

            actions.append({
                'id': 'refi_campaign',
                'title': 'Refinance Promotion Campaign',
                'type': 'revenue_generation',
                'urgency': 'medium',
                'target_segment': 'refi_ready',
                'target_count': refi_ready,
                'campaign_cost': campaign_cost,
                'expected_revenue': expected_revenue,
                'expected_conversion_rate': expected_conversion,
                'roi': round(expected_revenue / campaign_cost, 1) if campaign_cost > 0 else 0,
                'recommendation': 'Launch personalized rate quote campaign'
            })

        # Retention campaign
        at_risk = metrics['segment_overview']['at_risk']
        if at_risk > 10:
            retention_value = metrics['opportunity_value']['retention_value_at_risk']
            campaign_cost = at_risk * self.CAMPAIGN_COST_PER_CONTACT
            expected_retention = 0.65
            expected_save = retention_value * expected_retention

            actions.append({
                'id': 'retention_campaign',
                'title': 'Churn Prevention Campaign',
                'type': 'retention',
                'urgency': 'high',
                'target_segment': 'at_risk',
                'target_count': at_risk,
                'campaign_cost': campaign_cost,
                'value_at_risk': retention_value,
                'expected_save': expected_save,
                'expected_retention_rate': expected_retention,
                'roi': round(expected_save / campaign_cost, 1) if campaign_cost > 0 else 0,
                'recommendation': 'Launch proactive outreach with retention offers'
            })

        # Referral campaign
        loyal = metrics['segment_overview']['loyal']
        if loyal > 50:
            referral_potential = metrics['opportunity_value']['referral_potential']
            campaign_cost = loyal * self.CAMPAIGN_COST_PER_CONTACT * 0.5  # Lighter touch

            actions.append({
                'id': 'referral_campaign',
                'title': 'Customer Referral Program',
                'type': 'acquisition',
                'urgency': 'low',
                'target_segment': 'loyal',
                'target_count': loyal,
                'campaign_cost': campaign_cost,
                'expected_revenue': referral_potential,
                'expected_referral_rate': 0.25,
                'roi': round(referral_potential / campaign_cost, 1) if campaign_cost > 0 else 0,
                'recommendation': 'Launch with incentive program'
            })

        # Sort by ROI
        actions.sort(key=lambda x: x.get('roi', 0), reverse=True)

        return actions

    def get_customer_segments(self) -> List[Dict[str, Any]]:
        """
        Get detailed customer segmentation.

        Returns:
            List of segments with characteristics and opportunities
        """
        segments = []

        # Refi-ready segment
        result = self._query_db_one("""
            SELECT
                COUNT(DISTINCT t.customer_id) as count,
                AVG(a.refinance_likelihood) as avg_likelihood,
                AVG(a.borrower_sentiment = 'Positive') as satisfaction_rate
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE a.refinance_likelihood > 0.7
        """)
        if result and result[0]:
            segments.append({
                'segment_name': 'Refi-Ready',
                'segment_id': 'refi_ready',
                'count': result[0],
                'profile': 'High refinance likelihood, rate-sensitive',
                'avg_score': result[1],
                'satisfaction_rate': result[2] if result[2] else 0.5,
                'opportunity': 'Revenue generation through refinancing',
                'opportunity_value': result[0] * self.REFI_REVENUE_PER_LOAN,
                'engagement_strategy': 'Personalized rate quotes, benefits calculator',
                'expected_response_rate': 0.45,
                'priority': 'high'
            })

        # At-risk segment
        result = self._query_db_one("""
            SELECT
                COUNT(DISTINCT t.customer_id) as count,
                AVG(a.churn_risk) as avg_churn,
                AVG(a.delinquency_risk) as avg_delinq
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE a.churn_risk > 0.6 OR a.delinquency_risk > 0.6
        """)
        if result and result[0]:
            segments.append({
                'segment_name': 'At-Risk',
                'segment_id': 'at_risk',
                'count': result[0],
                'profile': 'High churn/delinquency risk, needs attention',
                'avg_churn_risk': result[1] if result[1] else 0,
                'avg_delinq_risk': result[2] if result[2] else 0,
                'opportunity': 'Retention and loss prevention',
                'opportunity_value': result[0] * self.AVG_SERVICING_FEE_ANNUAL,
                'engagement_strategy': 'Proactive support, hardship assistance, retention offers',
                'expected_response_rate': 0.55,
                'priority': 'critical'
            })

        # Loyal segment
        result = self._query_db_one("""
            SELECT
                COUNT(DISTINCT t.customer_id) as count,
                AVG(a.churn_risk) as avg_churn
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE a.churn_risk < 0.3
            AND a.borrower_sentiment IN ('Positive', 'Satisfied')
        """)
        if result and result[0]:
            segments.append({
                'segment_name': 'Loyal Champions',
                'segment_id': 'loyal',
                'count': result[0],
                'profile': 'Low risk, high satisfaction, brand advocates',
                'avg_churn_risk': result[1] if result[1] else 0,
                'opportunity': 'Referrals and advocacy',
                'opportunity_value': result[0] * 0.25 * self.REFI_REVENUE_PER_LOAN,
                'engagement_strategy': 'Referral incentives, reviews, testimonials',
                'expected_response_rate': 0.35,
                'priority': 'medium'
            })

        # PMI removal segment
        result = self._query_db_one("""
            SELECT COUNT(DISTINCT t.customer_id)
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE a.primary_intent = 'PMI removal request'
        """)
        if result and result[0]:
            segments.append({
                'segment_name': 'PMI Removal Eligible',
                'segment_id': 'pmi_removal',
                'count': result[0],
                'profile': 'Potential equity position, rate optimization',
                'opportunity': 'Retention through cost savings',
                'opportunity_value': result[0] * 1200,  # $1200 annual PMI savings
                'engagement_strategy': 'Proactive PMI analysis, fast-track process',
                'expected_response_rate': 0.75,
                'priority': 'high'
            })

        return segments

    def get_campaign_performance(self) -> List[Dict[str, Any]]:
        """
        Get hypothetical campaign performance (since we don't have real campaign data).

        Returns:
            Estimated campaign metrics based on intent patterns
        """
        # Analyze intent patterns as proxy for campaign themes
        results = self._query_db("""
            SELECT
                a.primary_intent,
                COUNT(*) as contact_count,
                AVG(a.issue_resolved) as resolution_rate,
                AVG(a.borrower_sentiment = 'Positive') as satisfaction_rate
            FROM analysis a
            WHERE a.created_at >= datetime('now', '-30 days')
            GROUP BY a.primary_intent
            ORDER BY contact_count DESC
            LIMIT 5
        """)

        campaigns = []
        for row in results:
            intent = row[0]
            contact_count = row[1]
            resolution_rate = row[2] if row[2] else 0
            satisfaction_rate = row[3] if row[3] else 0

            # Synthesize campaign metrics
            campaigns.append({
                'campaign_theme': intent,
                'contacts': contact_count,
                'response_rate': min(0.85, resolution_rate + 0.2),  # Estimate
                'conversion_rate': resolution_rate,
                'satisfaction_rate': satisfaction_rate,
                'status': 'hypothetical',  # Mark as estimated
                'performance': 'strong' if resolution_rate > 0.7 else 'moderate'
            })

        return campaigns
