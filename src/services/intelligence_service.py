"""
Intelligence service: API service layer for GenAI-powered insights.

Wraps personas and hybrid analyzer to expose intelligence via HTTP endpoints.
Handles caching, error handling, and response formatting.
"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from src.analytics.intelligence.hybrid_analyzer import HybridAnalyzer
from src.analytics.personas.leadership import LeadershipPersona
from src.analytics.personas.servicing_ops import ServicingOpsPersona
from src.analytics.personas.marketing import MarketingPersona
from src.storage.insight_store import InsightStore


class IntelligenceServiceError(Exception):
    """Exception raised by intelligence service."""
    pass


class IntelligenceService:
    """
    API service for GenAI-powered business intelligence.

    Coordinates:
    - Hybrid analyzer (Prophet + GenAI)
    - Persona transformations (Leadership, Ops, Marketing)
    - Insight caching
    """

    def __init__(
        self,
        hybrid_analyzer: HybridAnalyzer,
        insight_store: InsightStore,
        db_path: str = "data/call_center.db"
    ):
        """
        Initialize intelligence service.

        Args:
            hybrid_analyzer: Hybrid analyzer instance
            insight_store: Insight cache store
            db_path: Path to database
        """
        self.hybrid_analyzer = hybrid_analyzer
        self.insight_store = insight_store
        self.db_path = db_path

        # Initialize personas
        self.leadership = LeadershipPersona(db_path)
        self.servicing_ops = ServicingOpsPersona(db_path)
        self.marketing = MarketingPersona(db_path)

    # ============================================================
    # LEADERSHIP ENDPOINTS
    # ============================================================

    async def get_leadership_briefing(
        self,
        use_cache: bool = True,
        ttl_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Generate executive briefing for leadership.

        Args:
            use_cache: Whether to use cached version
            ttl_hours: Cache TTL in hours

        Returns:
            Executive briefing with urgent items and recommendations
        """
        insight_type = 'leadership_briefing'
        persona = 'leadership'

        # Check cache
        if use_cache:
            cached = self.insight_store.get(insight_type, persona)
            if cached:
                return cached

        # Generate new briefing
        start_time = time.time()

        try:
            briefing = await self.hybrid_analyzer.generate_executive_briefing()

            generation_time_ms = int((time.time() - start_time) * 1000)

            # Extract insight data
            insight_data = briefing.get('insight', {})

            # Add metadata
            result = {
                **insight_data,
                '_generated_at': datetime.utcnow().isoformat(),
                '_cached': False
            }

            # Cache it
            insight_id = f"{persona}_{insight_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            self.insight_store.store(
                insight_id=insight_id,
                insight_type=insight_type,
                persona=persona,
                insight_data=result,
                ttl_hours=ttl_hours,
                generation_time_ms=generation_time_ms,
                confidence_score=insight_data.get('confidence', 0.8)
            )

            return result

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to generate leadership briefing: {str(e)}")

    async def get_dollar_impact(self) -> Dict[str, Any]:
        """
        Get portfolio dollar impact analysis.

        Returns:
            Financial impact metrics
        """
        try:
            metrics = self.leadership.get_key_metrics()
            portfolio = metrics.get('portfolio', {})
            risk_scores = metrics.get('risk_scores', {})

            return {
                'total_at_risk': portfolio.get('at_risk_amount', 0),
                'by_category': {
                    'delinquency': portfolio.get('at_risk_amount', 0),
                    'churn': risk_scores.get('churn_revenue_at_risk', 0),
                    'compliance': 0  # TODO: Add compliance cost estimation
                },
                'portfolio_value': portfolio.get('portfolio_value', 0),
                'high_risk_customers': portfolio.get('high_risk_customers', 0),
                'trend': 'stable',  # TODO: Calculate trend from historical data
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to calculate dollar impact: {str(e)}")

    async def get_decision_queue(self) -> Dict[str, Any]:
        """
        Get items requiring executive decision.

        Returns:
            Prioritized decision queue
        """
        try:
            decisions = self.leadership.get_decision_queue()

            return {
                'count': len(decisions),
                'urgent_count': len([d for d in decisions if d.get('urgency') == 'high']),
                'decisions': decisions,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get decision queue: {str(e)}")

    async def get_risk_waterfall(self) -> Dict[str, Any]:
        """
        Get cascading risk breakdown (waterfall visualization data).

        Returns:
            Risk waterfall data
        """
        try:
            metrics = self.leadership.get_key_metrics()
            portfolio = metrics.get('portfolio', {})
            risk_scores = metrics.get('risk_scores', {})

            # Calculate waterfall stages
            total_value = portfolio.get('portfolio_value', 0)
            at_risk = portfolio.get('at_risk_amount', 0)
            actions = self.leadership.get_recommended_actions()

            # Calculate recoverable amount
            recoverable = sum([
                a.get('expected_impact', 0) - a.get('cost_estimate', 0)
                for a in actions
            ])

            return {
                'starting_portfolio': total_value,
                'at_risk': at_risk,
                'recoverable_with_action': recoverable,
                'net_risk': at_risk - recoverable,
                'stages': [
                    {'label': 'Total Portfolio', 'value': total_value},
                    {'label': 'At Risk', 'value': -at_risk, 'color': 'red'},
                    {'label': 'Recoverable', 'value': recoverable, 'color': 'green'},
                    {'label': 'Net Risk', 'value': at_risk - recoverable, 'color': 'orange'}
                ],
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to generate risk waterfall: {str(e)}")

    # ============================================================
    # SERVICING OPERATIONS ENDPOINTS
    # ============================================================

    async def get_queue_status(self) -> Dict[str, Any]:
        """
        Get real-time/predicted queue status.

        Returns:
            Queue status with predictions
        """
        try:
            # Get call volume forecast for next few hours
            call_forecast = await self.hybrid_analyzer.forecasting_service.generate_forecast(
                forecast_type='call_volume_hourly',
                horizon_days=1,
                use_cache=True
            )

            predictions = call_forecast.get('predictions', [])[:4]  # Next 4 hours

            metrics = self.servicing_ops.get_key_metrics()
            volume_metrics = metrics.get('volume_metrics', {})

            return {
                'current_queue': {
                    'high_priority': 0,  # TODO: Implement real-time queue
                    'standard': 0,
                    'callback_scheduled': 0
                },
                'predicted_volume': [
                    {
                        'hour': p.get('date'),
                        'predicted_calls': p.get('predicted'),
                        'confidence': p.get('confidence_interval')
                    }
                    for p in predictions
                ],
                'current_capacity': volume_metrics.get('current_capacity', 0),
                'staffing_status': 'adequate',  # TODO: Calculate from forecast
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get queue status: {str(e)}")

    async def get_sla_monitor(self) -> Dict[str, Any]:
        """
        Get SLA compliance tracking and predictions.

        Returns:
            SLA metrics and breach predictions
        """
        try:
            metrics = self.servicing_ops.get_key_metrics()
            sla = metrics.get('sla_performance', {})

            # Get forecast to predict SLA impact
            call_forecast = await self.hybrid_analyzer.forecasting_service.generate_forecast(
                forecast_type='call_volume_daily',
                horizon_days=7,
                use_cache=True
            )

            ops_forecast = self.servicing_ops.transform_forecast(call_forecast)
            sla_prediction = ops_forecast.get('sla_prediction', {})

            return {
                'current_performance': {
                    'fcr_rate': sla.get('fcr_rate', 0),
                    'fcr_target': sla.get('fcr_target', 0),
                    'fcr_status': sla.get('fcr_status', 'unknown'),
                    'escalation_rate': sla.get('escalation_rate', 0),
                    'escalation_target': sla.get('escalation_target', 0),
                    'escalation_status': sla.get('escalation_status', 'unknown'),
                    'compliance_score': sla.get('compliance_score', 0)
                },
                'predictions': sla_prediction,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get SLA monitor: {str(e)}")

    async def get_advisor_heatmap(self) -> Dict[str, Any]:
        """
        Get advisor performance heatmap data.

        Returns:
            Advisor performance matrix
        """
        try:
            heatmap = self.servicing_ops.get_advisor_heatmap()

            return {
                'advisors': heatmap,
                'summary': {
                    'total_advisors': len(heatmap),
                    'green_status': len([a for a in heatmap if a['status'] == 'green']),
                    'yellow_status': len([a for a in heatmap if a['status'] == 'yellow']),
                    'red_status': len([a for a in heatmap if a['status'] == 'red'])
                },
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get advisor heatmap: {str(e)}")

    async def get_coaching_alerts(self) -> Dict[str, Any]:
        """
        Get advisor coaching recommendations.

        Returns:
            Coaching alerts and recommendations
        """
        try:
            actions = self.servicing_ops.get_recommended_actions()
            coaching_actions = [a for a in actions if a.get('type') == 'coaching_required']

            metrics = self.servicing_ops.get_key_metrics()
            team = metrics.get('team_performance', {})

            return {
                'critical_alerts': coaching_actions,
                'team_summary': {
                    'total_advisors': team.get('total_advisors', 0),
                    'advisors_needing_coaching': team.get('advisors_needing_coaching', 0),
                    'avg_empathy_score': team.get('avg_empathy_score', 0),
                    'avg_compliance_score': team.get('avg_compliance_score', 0),
                    'team_health': team.get('team_health', 'unknown')
                },
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get coaching alerts: {str(e)}")

    async def get_workload_balance(self) -> Dict[str, Any]:
        """
        Get workload balancing recommendations.

        Returns:
            Staffing optimization recommendations
        """
        try:
            # Get call volume forecast
            call_forecast = await self.hybrid_analyzer.forecasting_service.generate_forecast(
                forecast_type='call_volume_hourly',
                horizon_days=1,
                use_cache=True
            )

            ops_forecast = self.servicing_ops.transform_forecast(call_forecast)
            staffing = ops_forecast.get('staffing_recommendation', {})

            return {
                'current_staff': staffing.get('current_staff', 0),
                'needed_for_peak': staffing.get('needed_for_peak', 0),
                'gap': staffing.get('gap', 0),
                'recommendation': staffing.get('recommendation', ''),
                'peak_hour': staffing.get('peak_hour_prediction', 0),
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get workload balance: {str(e)}")

    async def get_case_resolution(self) -> Dict[str, Any]:
        """
        Get active case tracking.

        Returns:
            Case resolution status
        """
        # TODO: Implement when we have case tracking data
        return {
            'message': 'Case tracking not yet implemented',
            'urgent_cases': [],
            'total_active_cases': 0,
            'generated_at': datetime.utcnow().isoformat()
        }

    # ============================================================
    # MARKETING ENDPOINTS
    # ============================================================

    async def get_marketing_segments(self) -> Dict[str, Any]:
        """
        Get customer segmentation with targeting opportunities.

        Returns:
            Customer segments with opportunity values
        """
        try:
            segments = self.marketing.get_customer_segments()

            return {
                'segments': segments,
                'summary': {
                    'total_segments': len(segments),
                    'high_priority_segments': len([s for s in segments if s.get('priority') == 'high']),
                    'total_opportunity_value': sum([s.get('opportunity_value', 0) for s in segments])
                },
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get marketing segments: {str(e)}")

    async def get_campaign_recommendations(self) -> Dict[str, Any]:
        """
        Get AI-generated campaign recommendations.

        Returns:
            Campaign ideas with ROI estimates
        """
        try:
            campaigns = self.marketing.get_recommended_actions()

            return {
                'campaigns': campaigns,
                'summary': {
                    'total_campaigns': len(campaigns),
                    'high_priority': len([c for c in campaigns if c.get('urgency') == 'high']),
                    'total_potential_revenue': sum([c.get('expected_revenue', 0) for c in campaigns]),
                    'total_cost': sum([c.get('campaign_cost', 0) for c in campaigns]),
                    'avg_roi': sum([c.get('roi', 0) for c in campaigns]) / len(campaigns) if campaigns else 0
                },
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get campaign recommendations: {str(e)}")

    async def get_campaign_performance(self, campaign_id: str) -> Dict[str, Any]:
        """
        Get specific campaign performance.

        Args:
            campaign_id: Campaign identifier

        Returns:
            Campaign performance metrics
        """
        # TODO: Implement when we have real campaign tracking
        return {
            'message': 'Campaign tracking not yet implemented',
            'campaign_id': campaign_id,
            'generated_at': datetime.utcnow().isoformat()
        }

    async def get_churn_analysis(self) -> Dict[str, Any]:
        """
        Get detailed churn intelligence.

        Returns:
            Churn predictions and retention strategies
        """
        try:
            analysis = await self.hybrid_analyzer.analyze_churn_risk()

            # Get marketing segment view
            segments = self.marketing.get_customer_segments()
            at_risk_segment = next((s for s in segments if s['segment_id'] == 'at_risk'), None)

            return {
                'forecast': analysis.get('forecast', {}),
                'insights': analysis.get('insights', {}),
                'at_risk_segment': at_risk_segment,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get churn analysis: {str(e)}")

    async def get_message_optimizer(self) -> Dict[str, Any]:
        """
        Get A/B test recommendations for messaging.

        Returns:
            Message optimization suggestions
        """
        # TODO: Implement message optimization
        return {
            'message': 'Message optimization not yet implemented',
            'suggestions': [],
            'generated_at': datetime.utcnow().isoformat()
        }

    async def get_customer_journey(self) -> Dict[str, Any]:
        """
        Get customer lifecycle analysis.

        Returns:
            Journey stage performance
        """
        # TODO: Implement journey analysis
        return {
            'message': 'Journey analysis not yet implemented',
            'stages': [],
            'generated_at': datetime.utcnow().isoformat()
        }

    async def get_roi_attribution(self) -> Dict[str, Any]:
        """
        Get marketing ROI attribution.

        Returns:
            Financial impact by campaign
        """
        try:
            metrics = self.marketing.get_key_metrics()
            opportunity = metrics.get('opportunity_value', {})

            return {
                'total_opportunity_value': sum(opportunity.values()),
                'by_category': opportunity,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get ROI attribution: {str(e)}")

    # ============================================================
    # CROSS-PERSONA ENDPOINTS
    # ============================================================

    async def answer_query(
        self,
        question: str,
        persona: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Natural language query interface.

        Args:
            question: Question to answer
            persona: Persona context (leadership, servicing, marketing)
            context: Optional additional context

        Returns:
            Answer with analysis
        """
        # TODO: Implement natural language query
        return {
            'question': question,
            'persona': persona,
            'answer': 'Natural language query not yet implemented',
            'generated_at': datetime.utcnow().isoformat()
        }

    async def list_cached_insights(self) -> List[Dict[str, Any]]:
        """
        List recently generated insights.

        Returns:
            List of cached insights
        """
        try:
            insights = self.insight_store.list_cached(only_active=True)
            return insights

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to list cached insights: {str(e)}")

    async def clear_cache(self, persona: Optional[str] = None) -> Dict[str, Any]:
        """
        Clear insight cache.

        Args:
            persona: Optional persona filter

        Returns:
            Count of cleared insights
        """
        try:
            count = self.insight_store.clear_cache(persona=persona)
            return {
                'cleared_count': count,
                'persona': persona or 'all',
                'cleared_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to clear cache: {str(e)}")

    async def get_health(self) -> Dict[str, Any]:
        """
        Get intelligence service health status.

        Returns:
            Service health metrics
        """
        try:
            stats = self.insight_store.get_statistics()

            return {
                'status': 'healthy',
                'cache_statistics': stats,
                'services': {
                    'hybrid_analyzer': 'operational',
                    'forecasting_service': 'operational',
                    'insight_store': 'operational'
                },
                'checked_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'checked_at': datetime.utcnow().isoformat()
            }
