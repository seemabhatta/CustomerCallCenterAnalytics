"""
Servicing Operations persona: Focus on real-time operations, SLA, advisors, queue management.

Transforms data to answer:
- Are we meeting SLA targets?
- Which advisors need coaching?
- What's our queue status?
- How should we allocate staff?
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json

from .base_persona import BasePersona


class ServicingOpsPersona(BasePersona):
    """
    Operations-focused data transformations.

    Key concerns: SLA compliance, queue management, advisor performance, staffing
    """

    # SLA targets
    SLA_ANSWER_RATE = 0.90  # 90% of calls answered
    SLA_ANSWER_TIME_SECONDS = 30  # Within 30 seconds
    SLA_FIRST_CALL_RESOLUTION = 0.75  # 75% FCR
    SLA_ESCALATION_RATE = 0.15  # <15% escalation

    # Staffing assumptions
    AVG_CALLS_PER_HOUR_PER_ADVISOR = 6
    AVG_HANDLE_TIME_MINUTES = 8

    def transform_forecast(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform forecast to show operational implications.

        Args:
            forecast: Raw Prophet forecast

        Returns:
            Operations-focused forecast view
        """
        forecast_type = forecast.get('forecast_type', '')
        summary = forecast.get('summary', {})
        predictions = forecast.get('predictions', [])

        # Calculate staffing needs from call volume forecast
        if 'call_volume' in forecast_type:
            staffing = self._calculate_staffing_needs(forecast)
            sla_prediction = self._predict_sla_impact(forecast)

            return {
                'call_volume': {
                    'average': summary.get('average_predicted'),
                    'peak': summary.get('max_predicted'),
                    'trend': self._determine_trend(predictions)
                },
                'staffing_recommendation': staffing,
                'sla_prediction': sla_prediction,
                'raw_forecast': forecast
            }

        # Transform advisor performance forecasts
        elif 'advisor' in forecast_type or 'empathy' in forecast_type or 'compliance' in forecast_type:
            coaching_alerts = self._identify_coaching_needs()

            return {
                'performance_trend': {
                    'current': summary.get('average_predicted'),
                    'predicted': predictions[-1].get('predicted') if predictions else None,
                    'direction': self._determine_trend(predictions)
                },
                'coaching_alerts': coaching_alerts,
                'raw_forecast': forecast
            }

        return {
            'forecast_summary': forecast,
            'operational_impact': 'Monitor for changes'
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

    def _calculate_staffing_needs(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate staffing requirements from call volume forecast.

        Args:
            forecast: Call volume forecast

        Returns:
            Staffing recommendations
        """
        predictions = forecast.get('predictions', [])

        if not predictions:
            return {'recommendation': 'Insufficient data'}

        # Get current advisor count
        result = self._query_db_one("""
            SELECT COUNT(DISTINCT advisor_id)
            FROM transcripts
            WHERE advisor_id IS NOT NULL
        """)
        current_advisors = result[0] if result else 10  # Default assumption

        # Calculate needed advisors for peak volume
        peak_volume = max([p.get('predicted', 0) for p in predictions[:24]])  # Next 24 hours
        needed_advisors = int(peak_volume / self.AVG_CALLS_PER_HOUR_PER_ADVISOR) + 1

        gap = needed_advisors - current_advisors

        return {
            'current_staff': current_advisors,
            'needed_for_peak': needed_advisors,
            'gap': gap,
            'recommendation': self._staffing_recommendation(gap),
            'peak_hour_prediction': peak_volume
        }

    def _staffing_recommendation(self, gap: int) -> str:
        """Generate staffing recommendation text."""
        if gap > 5:
            return f"URGENT: Add {gap} advisors or enable overflow protocol"
        elif gap > 2:
            return f"Add {gap} advisors to handle predicted volume"
        elif gap < -3:
            return f"Surplus capacity: Can reallocate {abs(gap)} advisors"
        else:
            return "Staffing adequate for predicted volume"

    def _predict_sla_impact(self, forecast: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict SLA compliance based on volume forecast.

        Args:
            forecast: Call volume forecast

        Returns:
            SLA predictions
        """
        predictions = forecast.get('predictions', [])

        if not predictions:
            return {'status': 'unknown'}

        # Get current performance
        result = self._query_db_one("""
            SELECT
                AVG(CASE WHEN first_call_resolution = 1 THEN 1.0 ELSE 0.0 END) as fcr_rate,
                AVG(CASE WHEN escalation_needed = 1 THEN 1.0 ELSE 0.0 END) as escalation_rate
            FROM analysis
            WHERE created_at >= datetime('now', '-7 days')
        """)

        current_fcr = result[0] if result and result[0] else self.SLA_FIRST_CALL_RESOLUTION
        current_escalation = result[1] if result and result[1] else self.SLA_ESCALATION_RATE

        # Simple prediction: if volume increases >20%, performance degrades
        avg_volume = forecast.get('summary', {}).get('average_predicted', 0)
        result = self._query_db_one("""
            SELECT COUNT(*) / 7.0
            FROM transcripts
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        baseline_volume = result[0] if result else avg_volume

        volume_change = ((avg_volume - baseline_volume) / baseline_volume * 100) if baseline_volume > 0 else 0

        # Predict degradation
        predicted_fcr = current_fcr
        predicted_escalation = current_escalation

        if volume_change > 20:
            predicted_fcr *= 0.9  # 10% degradation
            predicted_escalation *= 1.15  # 15% increase

        breaches = []
        if predicted_fcr < self.SLA_FIRST_CALL_RESOLUTION:
            breaches.append({
                'metric': 'First Call Resolution',
                'target': self.SLA_FIRST_CALL_RESOLUTION,
                'predicted': predicted_fcr,
                'risk': 'high' if predicted_fcr < self.SLA_FIRST_CALL_RESOLUTION * 0.9 else 'medium'
            })

        if predicted_escalation > self.SLA_ESCALATION_RATE:
            breaches.append({
                'metric': 'Escalation Rate',
                'target': self.SLA_ESCALATION_RATE,
                'predicted': predicted_escalation,
                'risk': 'high' if predicted_escalation > self.SLA_ESCALATION_RATE * 1.2 else 'medium'
            })

        return {
            'status': 'at_risk' if breaches else 'on_track',
            'predicted_fcr': predicted_fcr,
            'predicted_escalation': predicted_escalation,
            'potential_breaches': breaches,
            'volume_change_pct': volume_change
        }

    def _identify_coaching_needs(self) -> List[Dict[str, Any]]:
        """
        Identify advisors needing coaching.

        Returns:
            List of coaching alerts
        """
        results = self._query_db("""
            SELECT
                t.advisor_id,
                AVG(a.empathy_score) as avg_empathy,
                AVG(a.compliance_adherence) as avg_compliance,
                AVG(a.solution_effectiveness) as avg_effectiveness,
                COUNT(*) as call_count,
                SUM(CASE WHEN a.escalation_needed = 1 THEN 1 ELSE 0 END) as escalation_count
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE t.advisor_id IS NOT NULL
            AND t.timestamp >= datetime('now', '-7 days')
            GROUP BY t.advisor_id
            HAVING avg_empathy < 7.0 OR avg_compliance < 0.8 OR avg_effectiveness < 7.0
            ORDER BY avg_compliance ASC, avg_empathy ASC
            LIMIT 10
        """)

        alerts = []
        for row in results:
            advisor_id = row[0]
            avg_empathy = row[1]
            avg_compliance = row[2]
            avg_effectiveness = row[3]
            call_count = row[4]
            escalation_count = row[5]

            issues = []
            if avg_compliance < 0.75:
                issues.append('compliance_critical')
            elif avg_compliance < 0.8:
                issues.append('compliance_needs_improvement')

            if avg_empathy < 6.0:
                issues.append('empathy_critical')
            elif avg_empathy < 7.0:
                issues.append('empathy_needs_improvement')

            if avg_effectiveness < 6.5:
                issues.append('effectiveness_low')

            if escalation_count / call_count > 0.25:
                issues.append('high_escalation_rate')

            alerts.append({
                'advisor_id': advisor_id,
                'alert_level': 'red' if any('critical' in i for i in issues) else 'yellow',
                'empathy_score': round(avg_empathy, 1),
                'compliance_score': round(avg_compliance, 2),
                'effectiveness_score': round(avg_effectiveness, 1),
                'calls_last_7d': call_count,
                'escalation_rate': round(escalation_count / call_count, 2),
                'issues': issues,
                'recommendation': self._coaching_recommendation(issues)
            })

        return alerts

    def _coaching_recommendation(self, issues: List[str]) -> str:
        """Generate coaching recommendation based on issues."""
        if 'compliance_critical' in issues:
            return "URGENT: Pull from queue for immediate compliance training"
        elif 'empathy_critical' in issues:
            return "Schedule empathy coaching session this week"
        elif 'high_escalation_rate' in issues:
            return "Review escalation protocols and decision-making"
        elif 'compliance_needs_improvement' in issues:
            return "Send compliance refresher module"
        elif 'empathy_needs_improvement' in issues:
            return "Provide empathy coaching resources"
        else:
            return "Monitor performance trends"

    def get_key_metrics(self) -> Dict[str, Any]:
        """
        Get operations dashboard metrics.

        Returns:
            Key metrics for operations view
        """
        # Current SLA performance
        result = self._query_db_one("""
            SELECT
                AVG(CASE WHEN first_call_resolution = 1 THEN 1.0 ELSE 0.0 END) as fcr_rate,
                AVG(CASE WHEN escalation_needed = 1 THEN 1.0 ELSE 0.0 END) as escalation_rate,
                AVG(compliance_adherence) as avg_compliance
            FROM analysis
            WHERE created_at >= datetime('now', '-7 days')
        """)

        fcr_rate = result[0] if result and result[0] else 0
        escalation_rate = result[1] if result and result[1] else 0
        avg_compliance = result[2] if result and result[2] else 0

        # Advisor performance summary
        result = self._query_db_one("""
            SELECT
                COUNT(DISTINCT t.advisor_id) as total_advisors,
                AVG(a.empathy_score) as avg_empathy,
                AVG(a.compliance_adherence) as avg_compliance
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE t.advisor_id IS NOT NULL
            AND t.timestamp >= datetime('now', '-7 days')
        """)

        total_advisors = result[0] if result else 0
        avg_empathy = result[1] if result and result[1] else 0
        avg_compliance_team = result[2] if result and result[2] else 0

        # Advisors needing attention
        coaching_needed = len(self._identify_coaching_needs())

        # Queue estimates (based on recent patterns)
        result = self._query_db_one("""
            SELECT COUNT(*) / 7.0
            FROM transcripts
            WHERE timestamp >= datetime('now', '-7 days')
        """)
        avg_daily_calls = result[0] if result else 0

        return {
            'sla_performance': {
                'fcr_rate': fcr_rate,
                'fcr_target': self.SLA_FIRST_CALL_RESOLUTION,
                'fcr_status': 'green' if fcr_rate >= self.SLA_FIRST_CALL_RESOLUTION else 'red',
                'escalation_rate': escalation_rate,
                'escalation_target': self.SLA_ESCALATION_RATE,
                'escalation_status': 'green' if escalation_rate <= self.SLA_ESCALATION_RATE else 'red',
                'compliance_score': avg_compliance
            },
            'team_performance': {
                'total_advisors': total_advisors,
                'avg_empathy_score': avg_empathy,
                'avg_compliance_score': avg_compliance_team,
                'advisors_needing_coaching': coaching_needed,
                'team_health': 'good' if coaching_needed < 3 else 'needs_attention'
            },
            'volume_metrics': {
                'avg_daily_calls': avg_daily_calls,
                'estimated_hourly_rate': avg_daily_calls / 10,  # Assume 10-hour day
                'current_capacity': total_advisors * self.AVG_CALLS_PER_HOUR_PER_ADVISOR
            }
        }

    def get_recommended_actions(self) -> List[Dict[str, Any]]:
        """
        Get operational actions needed.

        Returns:
            List of recommended operational interventions
        """
        actions = []

        # Check for SLA risks
        metrics = self.get_key_metrics()
        sla = metrics['sla_performance']

        if sla['fcr_status'] == 'red':
            actions.append({
                'id': 'improve_fcr',
                'title': 'First Call Resolution Below Target',
                'type': 'performance_improvement',
                'urgency': 'high',
                'current': sla['fcr_rate'],
                'target': sla['fcr_target'],
                'recommendation': 'Review escalation protocols and provide resolution training'
            })

        if sla['escalation_status'] == 'red':
            actions.append({
                'id': 'reduce_escalations',
                'title': 'Escalation Rate Above Target',
                'type': 'performance_improvement',
                'urgency': 'high',
                'current': sla['escalation_rate'],
                'target': sla['escalation_target'],
                'recommendation': 'Empower advisors with expanded decision authority'
            })

        # Check coaching needs
        coaching_alerts = self._identify_coaching_needs()
        if coaching_alerts:
            critical_alerts = [a for a in coaching_alerts if a['alert_level'] == 'red']
            if critical_alerts:
                actions.append({
                    'id': 'urgent_coaching',
                    'title': f'{len(critical_alerts)} Advisors Need Immediate Coaching',
                    'type': 'coaching_required',
                    'urgency': 'high',
                    'advisors': [a['advisor_id'] for a in critical_alerts],
                    'recommendation': 'Pull from queue for immediate intervention'
                })

        return actions

    def get_advisor_heatmap(self) -> List[Dict[str, Any]]:
        """
        Get advisor performance for heatmap visualization.

        Returns:
            List of advisor performance data
        """
        results = self._query_db("""
            SELECT
                t.advisor_id,
                AVG(a.empathy_score) as avg_empathy,
                AVG(a.compliance_adherence) as avg_compliance,
                AVG(a.solution_effectiveness) as avg_effectiveness,
                COUNT(*) as call_count,
                AVG(CASE WHEN a.first_call_resolution = 1 THEN 1.0 ELSE 0.0 END) as fcr_rate
            FROM transcripts t
            JOIN analysis a ON t.id = a.transcript_id
            WHERE t.advisor_id IS NOT NULL
            AND t.timestamp >= datetime('now', '-7 days')
            GROUP BY t.advisor_id
            ORDER BY avg_compliance DESC, avg_empathy DESC
            LIMIT 50
        """)

        heatmap = []
        for row in results:
            advisor_id = row[0]
            avg_empathy = row[1]
            avg_compliance = row[2]
            avg_effectiveness = row[3]
            call_count = row[4]
            fcr_rate = row[5]

            # Determine status color
            if avg_compliance >= 0.9 and avg_empathy >= 8.0:
                status = 'green'
            elif avg_compliance >= 0.8 and avg_empathy >= 7.0:
                status = 'yellow'
            else:
                status = 'red'

            heatmap.append({
                'advisor_id': advisor_id,
                'name': f"Advisor {advisor_id[-6:]}",  # Use last 6 chars of ID
                'empathy_score': round(avg_empathy, 1),
                'compliance_score': round(avg_compliance, 2),
                'effectiveness_score': round(avg_effectiveness, 1),
                'fcr_rate': round(fcr_rate, 2),
                'calls_last_7d': call_count,
                'status': status,
                'coaching_needed': status == 'red'
            })

        return heatmap
