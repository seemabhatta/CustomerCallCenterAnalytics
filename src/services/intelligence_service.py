"""
Intelligence service: API service layer for GenAI-powered insights.

Wraps personas and hybrid analyzer to expose intelligence via HTTP endpoints.
Handles caching, error handling, and response formatting.
"""

import uuid
import sqlite3
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import time

from src.analytics.intelligence.hybrid_analyzer import HybridAnalyzer
from src.analytics.personas.leadership import LeadershipPersona
from src.analytics.personas.servicing_ops import ServicingOpsPersona
from src.analytics.personas.marketing import MarketingPersona
from src.storage.insight_store import InsightStore
from src.services.forecasting_service import ForecastingServiceError


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
            compliance = metrics.get('compliance', {})
            trend = metrics.get('trend_metrics', {})

            delta_pct = trend.get('delta_pct')
            if delta_pct is None:
                trend_label = 'stable'
            elif delta_pct > 0.05:
                trend_label = 'increasing'
            elif delta_pct < -0.05:
                trend_label = 'decreasing'
            else:
                trend_label = 'stable'

            return {
                'total_at_risk': portfolio.get('at_risk_amount', 0),
                'by_category': {
                    'delinquency': portfolio.get('at_risk_amount', 0),
                    'churn': risk_scores.get('churn_revenue_at_risk', 0),
                    'compliance': compliance.get('estimated_penalty', 0)
                },
                'portfolio_value': portfolio.get('portfolio_value', 0),
                'high_risk_customers': portfolio.get('high_risk_customers', 0),
                'trend': trend_label,
                'trend_delta_pct': delta_pct,
                'recent_delinquency_avg': trend.get('recent_delinquency'),
                'previous_delinquency_avg': trend.get('previous_delinquency'),
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
            call_forecast = await self.hybrid_analyzer.forecasting_service.generate_forecast(
                forecast_type='call_volume_hourly',
                horizon_days=1,
                use_cache=True
            )

            predictions = call_forecast.get('predictions', [])[:4]

            metrics = self.servicing_ops.get_key_metrics()
            volume_metrics = metrics.get('volume_metrics', {})

            ops_forecast = self.servicing_ops.transform_forecast(call_forecast)
            staffing = ops_forecast.get('staffing_recommendation', {})
            gap = staffing.get('gap', 0)
            if gap > 0:
                staffing_status = 'understaffed'
            elif gap < 0:
                staffing_status = 'surplus'
            else:
                staffing_status = 'balanced'

            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM workflows
                    WHERE status = 'AWAITING_APPROVAL'
                      AND UPPER(COALESCE(risk_level, '')) IN ('HIGH', 'CRITICAL')
                    """
                )
                high_priority = cur.fetchone()[0] or 0

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM workflows
                    WHERE status = 'AWAITING_APPROVAL'
                      AND UPPER(COALESCE(risk_level, '')) NOT IN ('HIGH', 'CRITICAL')
                    """
                )
                standard = cur.fetchone()[0] or 0

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM analysis
                    WHERE escalation_needed = 1
                      AND COALESCE(issue_resolved, 0) = 0
                    """
                )
                escalations = cur.fetchone()[0] or 0

            return {
                'current_queue': {
                    'high_priority': high_priority,
                    'standard': standard,
                    'callback_scheduled': escalations
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
                'staffing_status': staffing_status,
                'staffing_gap': gap,
                'generated_at': datetime.utcnow().isoformat()
            }

        except ForecastingServiceError as error:
            return self._empty_queue_status(str(error))
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

        except ForecastingServiceError as error:
            return self._empty_sla_monitor(str(error))
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

        except ForecastingServiceError as error:
            return self._empty_workload_balance(str(error))
        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get workload balance: {str(e)}")

    async def get_case_resolution(self) -> Dict[str, Any]:
        """
        Get active case tracking.

        Returns:
            Case resolution status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM analysis
                    WHERE COALESCE(issue_resolved, 0) = 0
                """
                )
                total_active = cur.fetchone()[0] or 0

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM analysis
                    WHERE COALESCE(issue_resolved, 0) = 1
                      AND created_at >= datetime('now', '-7 days')
                """
                )
                resolved_last_7d = cur.fetchone()[0] or 0

                cur.execute(
                    """
                    SELECT AVG(julianday('now') - julianday(created_at))
                    FROM analysis
                    WHERE COALESCE(issue_resolved, 0) = 0
                """
                )
                avg_case_age = cur.fetchone()[0] or 0

                cur.execute(
                    """
                    SELECT a.id, a.transcript_id, a.delinquency_risk, a.churn_risk, a.created_at, t.topic
                    FROM analysis a
                    JOIN transcripts t ON t.id = a.transcript_id
                    WHERE COALESCE(a.issue_resolved, 0) = 0
                    ORDER BY a.delinquency_risk DESC, a.churn_risk DESC, a.created_at ASC
                    LIMIT 10
                """
                )

                urgent_cases = []
                for row in cur.fetchall():
                    created_at = row['created_at']
                    age_days = None
                    if created_at:
                        try:
                            opened = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                            age_days = max((datetime.utcnow() - opened.replace(tzinfo=None)).days, 0)
                        except ValueError:
                            age_days = None

                    urgent_cases.append({
                        'analysis_id': row['id'],
                        'transcript_id': row['transcript_id'],
                        'topic': row['topic'],
                        'delinquency_risk': row['delinquency_risk'],
                        'churn_risk': row['churn_risk'],
                        'opened_at': created_at,
                        'age_days': age_days
                    })

                cur.execute(
                    """
                    SELECT COUNT(*)
                    FROM analysis
                    WHERE COALESCE(issue_resolved, 0) = 1
                """
                )
                total_resolved = cur.fetchone()[0] or 0

            return {
                'message': 'Active case backlog overview',
                'summary': {
                    'total_active_cases': total_active,
                    'resolved_last_7_days': resolved_last_7d,
                    'avg_case_age_days': round(avg_case_age, 2) if avg_case_age else 0,
                    'total_resolved_cases': total_resolved
                },
                'urgent_cases': urgent_cases,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to compute case resolution insights: {str(e)}")

    async def get_case_resolution_insights(self) -> Dict[str, Any]:
        """Compatibility wrapper for API route expecting *_insights suffix."""
        return await self.get_case_resolution()

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

    async def get_campaign_performance(
        self,
        campaign_id: Optional[str] = None,
        date_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Summarise campaign (segment) performance from recent interactions.

        Args:
            campaign_id: Segment identifier (maps to persona segments)
            date_range: Optional time window shortcut (e.g., last_7_days, last_30_days)
        """
        try:
            where_clauses: List[str] = []
            condition = self.marketing.get_segment_condition(campaign_id)
            if condition:
                where_clauses.append(condition)

            if date_range == 'last_7_days':
                where_clauses.append("a.created_at >= datetime('now', '-7 days')")
            elif date_range == 'last_90_days':
                where_clauses.append("a.created_at >= datetime('now', '-90 days')")
            else:  # default to last 30 days window
                where_clauses.append("a.created_at >= datetime('now', '-30 days')")

            where_sql = ' AND '.join(where_clauses)
            if where_sql:
                where_sql = 'WHERE ' + where_sql

            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()

                cur.execute(
                    f"""
                    SELECT
                        COUNT(*) AS touchpoints,
                        SUM(CASE WHEN COALESCE(a.issue_resolved, 0) = 1 THEN 1 ELSE 0 END) AS resolved_cases,
                        AVG(a.churn_risk) AS avg_churn_risk,
                        AVG(a.delinquency_risk) AS avg_delinquency_risk,
                        AVG(a.compliance_adherence) AS avg_compliance,
                        AVG(CASE WHEN a.borrower_sentiment = 'Positive' THEN 1.0
                                 WHEN a.borrower_sentiment = 'Satisfied' THEN 0.8
                                 WHEN a.borrower_sentiment = 'Neutral' THEN 0.5
                                 ELSE 0.2 END) AS sentiment_index
                    FROM analysis a
                    JOIN transcripts t ON t.id = a.transcript_id
                    {where_sql}
                """
                )
                row = cur.fetchone()

                touchpoints = row['touchpoints'] or 0
                resolved = row['resolved_cases'] or 0
                unresolved = touchpoints - resolved
                avg_churn = row['avg_churn_risk'] or 0
                avg_delinq = row['avg_delinquency_risk'] or 0
                avg_compliance = row['avg_compliance'] or 0
                sentiment_index = row['sentiment_index'] or 0

                conversion_rate = resolved / touchpoints if touchpoints else 0

                # Estimate opportunity from persona segment data
                segments = self.marketing.get_customer_segments()
                segment = next((s for s in segments if s['segment_id'] == campaign_id), None)
                opportunity_value = segment.get('opportunity_value') if segment else None
                segment_name = segment.get('segment_name') if segment else campaign_id or 'all_customers'

                return {
                    'campaign_id': campaign_id,
                    'segment': segment_name,
                    'date_range': date_range or 'last_30_days',
                    'touchpoints': touchpoints,
                    'resolved_cases': resolved,
                    'open_cases': unresolved,
                    'conversion_rate': conversion_rate,
                    'avg_churn_risk': avg_churn,
                    'avg_delinquency_risk': avg_delinq,
                    'avg_compliance_score': avg_compliance,
                    'sentiment_index': sentiment_index,
                    'opportunity_value': opportunity_value,
                    'message': (
                        f"{resolved} of {touchpoints} contacts converted for segment {segment_name}."
                        if touchpoints else
                        f"No recent contacts found for segment {segment_name}."
                    ),
                    'generated_at': datetime.utcnow().isoformat()
                }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get campaign performance: {str(e)}")

    async def get_churn_analysis(
        self,
        use_cache: bool = True,
        ttl_hours: int = 2
    ) -> Dict[str, Any]:
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

        except ForecastingServiceError as error:
            return self._empty_churn_analysis(str(error))

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to get churn analysis: {str(e)}")

    async def get_message_optimizer(self) -> Dict[str, Any]:
        """Provide default optimization guidance (legacy compatibility)."""
        return await self.optimize_campaign_message("", "general")

    async def optimize_campaign_message(self, message: str, segment: str = 'general') -> Dict[str, Any]:
        """Return segment-aware copy suggestions based on persona metrics."""
        segments = self.marketing.get_customer_segments()
        segment_details = next((s for s in segments if s['segment_id'] == segment), None)

        opportunity_value = segment_details.get('opportunity_value') if segment_details else None
        size = segment_details.get('count') if segment_details else None
        priority = segment_details.get('priority') if segment_details else 'medium'

        cues: List[str] = []
        if opportunity_value:
            cues.append(f"Highlight the ${opportunity_value:,.0f} revenue opportunity for this segment.")
        if size:
            cues.append(f"Reference the {size} customers currently in this segment to build urgency.")
        if priority == 'high':
            cues.append("Use decisive language and a clear CTA within the first sentence.")
        elif priority == 'critical':
            cues.append("Lead with retention risk mitigation and offer concierge outreach.")
        else:
            cues.append("Reinforce brand trust and long-term relationship benefits.")

        optimized_message = message.strip()
        if optimized_message:
            tail = segment_details.get('engagement_strategy') if segment_details else None
            if tail:
                optimized_message = f"{optimized_message}\n\nNext step: {tail}."
        else:
            optimized_message = (
                f"Tailor outreach for {segment_details['segment_name']} with personalized value props."
                if segment_details else
                "Tailor outreach with personalized value props."
            )

        return {
            'segment': segment,
            'message': message,
            'optimized_message': optimized_message,
            'suggestions': cues,
            'generated_at': datetime.utcnow().isoformat()
        }

    async def get_customer_journey(self) -> Dict[str, Any]:
        """Summarise pipeline progression using existing artefacts."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cur = conn.cursor()

                cur.execute("SELECT COUNT(*) FROM transcripts WHERE timestamp >= datetime('now', '-30 days')")
                inquiries = cur.fetchone()[0] or 0

                cur.execute("SELECT COUNT(*) FROM analysis WHERE created_at >= datetime('now', '-30 days')")
                analyses = cur.fetchone()[0] or 0

                cur.execute("SELECT COUNT(*) FROM action_plans WHERE created_at >= datetime('now', '-30 days')")
                plans = cur.fetchone()[0] or 0

                cur.execute("SELECT COUNT(*) FROM workflows WHERE created_at >= datetime('now', '-30 days')")
                workflows_total = cur.fetchone()[0] or 0

                cur.execute("SELECT COUNT(*) FROM workflows WHERE status = 'EXECUTED' AND created_at >= datetime('now', '-30 days')")
                workflows_executed = cur.fetchone()[0] or 0

                cur.execute("""
                    SELECT primary_intent, COUNT(*)
                    FROM analysis
                    WHERE created_at >= datetime('now', '-30 days')
                    GROUP BY primary_intent
                    ORDER BY COUNT(*) DESC
                    LIMIT 3
                """
                )
                top_intents = cur.fetchall()

            stages = [
                {
                    'stage': 'Inquiry',
                    'count': inquiries,
                    'conversion_rate': analyses / inquiries if inquiries else 0,
                    'description': 'Inbound calls captured in the last 30 days'
                },
                {
                    'stage': 'Analysis',
                    'count': analyses,
                    'conversion_rate': plans / analyses if analyses else 0,
                    'description': 'AI analyses generated for conversations'
                },
                {
                    'stage': 'Action Planning',
                    'count': plans,
                    'conversion_rate': workflows_total / plans if plans else 0,
                    'description': 'Action plans produced for follow-up'
                },
                {
                    'stage': 'Workflow Execution',
                    'count': workflows_executed,
                    'conversion_rate': workflows_executed / inquiries if inquiries else 0,
                    'description': 'Workflows executed to completion'
                }
            ]

            top_intent_summary = ", ".join(f"{intent or 'Unknown'} ({count})" for intent, count in top_intents) or "No dominant intents recorded"

            message = (
                f"{inquiries} inbound calls fed {analyses} AI analyses, "
                f"resulting in {plans} action plans and {workflows_executed} executed workflows."
            )

            return {
                'message': message,
                'stages': stages,
                'top_intents': top_intent_summary,
                'generated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            raise IntelligenceServiceError(f"Failed to build customer journey: {str(e)}")

    async def get_customer_journey_insights(self) -> Dict[str, Any]:
        """Compatibility wrapper for API route expecting *_insights suffix."""
        return await self.get_customer_journey()

    def _empty_churn_analysis(self, message: str) -> Dict[str, Any]:
        """Fallback churn analysis when forecasts are unavailable."""
        now = datetime.utcnow().isoformat()
        return {
            'forecast': {
                'forecast_type': 'churn_risk',
                'summary': {
                    'message': message,
                    'average_predicted': 0,
                    'prediction_start': None,
                    'prediction_end': None,
                },
                'predictions': [],
                'metadata': {
                    'data_points_used': 0,
                    'data_available': False,
                },
            },
            'insights': {
                'churn_summary': {
                    'current_rate': 0,
                    'trend': 'insufficient_data',
                    'high_risk_count': 0,
                    'revenue_at_risk': 0,
                },
                'root_causes': [],
                'target_segments': [],
                'retention_strategies': [],
                'financial_impact': {
                    'total_revenue_at_risk': 0,
                    'with_no_action': 0,
                    'with_proactive_action': 0,
                    'net_save': 0,
                    'campaign_cost': 0,
                    'roi': 0,
                },
                'confidence': 'low',
                '_warning': message,
            },
            'at_risk_segment': None,
            'generated_at': now,
        }

    def _empty_queue_status(self, warning: str) -> Dict[str, Any]:
        return {
            'current_queue': {
                'high_priority': 0,
                'standard': 0,
                'callback_scheduled': 0,
            },
            'predicted_volume': [],
            'current_capacity': 0,
            'staffing_status': 'insufficient_data',
            'staffing_gap': None,
            'warning': warning,
            'generated_at': datetime.utcnow().isoformat(),
        }

    def _empty_sla_monitor(self, warning: str) -> Dict[str, Any]:
        return {
            'current_performance': {
                'fcr_rate': 0,
                'fcr_target': self.servicing_ops.SLA_FIRST_CALL_RESOLUTION,
                'fcr_status': 'insufficient_data',
                'escalation_rate': 0,
                'escalation_target': self.servicing_ops.SLA_ESCALATION_RATE,
                'escalation_status': 'insufficient_data',
                'compliance_score': 0,
            },
            'predictions': {
                'warning': warning,
            },
            'generated_at': datetime.utcnow().isoformat(),
        }

    def _empty_workload_balance(self, warning: str) -> Dict[str, Any]:
        return {
            'current_staff': 0,
            'needed_for_peak': 0,
            'gap': None,
            'recommendation': warning,
            'peak_hour': None,
            'generated_at': datetime.utcnow().isoformat(),
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

    async def ask(
        self,
        question: str,
        persona: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Natural language query interface for the intelligence layer.

        The method orchestrates a light-weight strategy/response loop using
        the prompt assets that power the new dashboards. It provides the LLM
        with:
        - persona-specific metrics and recommended actions
        - any cached insights that are still active
        - optional caller-supplied context (recent workflow IDs, etc.)
        """

        resolved_persona, persona_label = self._resolve_persona(persona)

        # Gather structured context that can be handed to the prompt set.
        persona_snapshot = self._build_persona_snapshot(resolved_persona)

        cached_insights = self.insight_store.list_cached(
            persona=resolved_persona if resolved_persona != 'cross_persona' else None,
            only_active=True,
        )

        # Reduce noise by keeping the freshest entries only.
        cached_insights = cached_insights[:5]

        session_context = {
            'persona': resolved_persona,
            'input_persona': persona,
            'caller_context': context or {},
            'persona_snapshot': persona_snapshot,
            'cached_insights': cached_insights,
        }

        try:
            # First determine the strategy for answering the question.
            strategy_result = await self.hybrid_analyzer.insight_generator.generate(
                prompt_name='insights/strategy/query_strategy',
                context={
                    'query': question,
                    'executive_role': persona_label,
                    'session_context': session_context,
                },
                temperature=0.2,
                max_tokens=800,
            )
            strategy = strategy_result.get('insight', {})

            # Provide the strategy, persona data, and interpretation scaffolding
            # back to the response prompt to synthesize an executive-ready answer.
            response_result = await self.hybrid_analyzer.insight_generator.generate(
                prompt_name='insights/response/strategic_executive_response',
                context={
                    'query': question,
                    'strategy': strategy,
                    'data_result': persona_snapshot,
                    'understanding': {
                        'cached_insights': cached_insights,
                        'persona': resolved_persona,
                    },
                },
                temperature=0.3,
                max_tokens=1200,
            )

            response_payload = response_result.get('insight', {})
            answer_text = (
                response_payload.get('content')
                if isinstance(response_payload, dict)
                else str(response_payload)
            )

            return {
                'question': question,
                'persona': persona or resolved_persona,
                'answer': answer_text,
                'generated_at': datetime.utcnow().isoformat(),
                'strategy': strategy,
                'response': response_payload,
            }

        except Exception as exc:
            raise IntelligenceServiceError(
                f"Failed to answer intelligence question: {str(exc)}"
            )

    async def get_cached_insights(
        self,
        persona: Optional[str] = None,
        insight_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return cached insight summaries with optional filtering."""

        resolved_persona, _ = self._resolve_persona(persona)

        try:
            insights = self.insight_store.list_cached(
                persona=None if resolved_persona == 'cross_persona' else resolved_persona,
                only_active=True,
            )

            if insight_type:
                insights = [i for i in insights if i.get('insight_type') == insight_type]

            return insights[: max(1, limit)]

        except Exception as exc:
            raise IntelligenceServiceError(
                f"Failed to list cached insights: {str(exc)}"
            )

    def _resolve_persona(self, persona: Optional[str]) -> Tuple[str, str]:
        """Normalise persona aliases for downstream prompts."""

        if not persona:
            return 'leadership', 'leadership'

        normalised = persona.lower().strip()
        mapping = {
            'leadership': 'leadership',
            'executive': 'leadership',
            'leader': 'leadership',
            'servicing': 'servicing',
            'operations': 'servicing',
            'servicing_ops': 'servicing',
            'marketing': 'marketing',
            'growth': 'marketing',
        }

        resolved = mapping.get(normalised)
        if not resolved:
            return 'cross_persona', 'cross_persona'

        return resolved, resolved

    def _build_persona_snapshot(self, persona: str) -> Dict[str, Any]:
        """Collect persona-specific context shared with the LLM prompts."""

        snapshot: Dict[str, Any] = {
            'metrics': {},
            'recommended_actions': [],
        }

        if persona == 'leadership':
            snapshot['metrics'] = self.leadership.get_key_metrics()
            snapshot['recommended_actions'] = self.leadership.get_recommended_actions()
        elif persona == 'servicing':
            metrics = self.servicing_ops.get_key_metrics()
            snapshot['metrics'] = metrics
            snapshot['recommended_actions'] = self.servicing_ops.get_recommended_actions()
        elif persona == 'marketing':
            snapshot['metrics'] = self.marketing.get_key_metrics()
            snapshot['recommended_actions'] = self.marketing.get_recommended_actions()
            snapshot['segments'] = self.marketing.get_customer_segments()
        else:
            # Cross-persona snapshot pulls the top-level data from all personas.
            snapshot['personas'] = {
                'leadership': {
                    'metrics': self.leadership.get_key_metrics(),
                    'actions': self.leadership.get_recommended_actions(),
                },
                'servicing': {
                    'metrics': self.servicing_ops.get_key_metrics(),
                    'actions': self.servicing_ops.get_recommended_actions(),
                },
                'marketing': {
                    'metrics': self.marketing.get_key_metrics(),
                    'actions': self.marketing.get_recommended_actions(),
                },
            }

        return snapshot

    async def clear_cache(
        self,
        persona: Optional[str] = None,
        insight_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clear insight cache.

        Args:
            persona: Optional persona filter

        Returns:
            Count of cleared insights
        """
        try:
            count = self.insight_store.clear_cache(
                persona=persona,
                insight_type=insight_type
            )
            return {
                'cleared_count': count,
                'persona': persona or 'all',
                'insight_type': insight_type or 'all',
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
