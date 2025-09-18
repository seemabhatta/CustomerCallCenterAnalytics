"""Service to read from existing pipeline data stores.

Core Principles Applied:
- NO FALLBACK: Fail fast on missing data or invalid states
- READ-ONLY: Never modifies existing data, only reads
- INTELLIGENT FILTERING: Provides rich query capabilities for agents
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import json

from ..storage.transcript_store import TranscriptStore
from ..storage.analysis_store import AnalysisStore
from ..storage.action_plan_store import ActionPlanStore
from ..storage.workflow_store import WorkflowStore
from ..storage.workflow_execution_store import WorkflowExecutionStore


class DataReaderService:
    """Service to read from existing pipeline data stores.

    Provides intelligent querying capabilities for the Leadership Insights Agent
    to fetch relevant data based on LLM-determined plans.
    """

    def __init__(self, db_path: str):
        """Initialize with database path.

        Args:
            db_path: SQLite database file path

        Raises:
            Exception: If initialization fails (NO FALLBACK)
        """
        if not db_path:
            raise ValueError("Database path cannot be empty")

        self.db_path = db_path

        # Initialize all existing stores for read access
        self.transcript_store = TranscriptStore(db_path)
        self.analysis_store = AnalysisStore(db_path)
        self.plan_store = ActionPlanStore(db_path)
        self.workflow_store = WorkflowStore(db_path)
        self.execution_store = WorkflowExecutionStore(db_path)

    def fetch_by_plan(self, data_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch data according to LLM-generated plan.

        Args:
            data_plan: Plan dictionary from planning agent

        Returns:
            Dictionary with requested data

        Raises:
            Exception: If fetching fails (NO FALLBACK)
        """
        if not data_plan:
            raise ValueError("data_plan cannot be empty")

        fetched_data = {}

        try:
            # Fetch transcripts if needed
            if data_plan.get('needs_transcripts'):
                fetched_data['transcripts'] = self._fetch_transcripts(
                    data_plan.get('transcript_filters', {})
                )

            # Fetch analyses if needed
            if data_plan.get('needs_analyses'):
                fetched_data['analyses'] = self._fetch_analyses(
                    data_plan.get('analysis_filters', {})
                )

            # Fetch plans if needed
            if data_plan.get('needs_plans'):
                fetched_data['plans'] = self._fetch_plans(
                    data_plan.get('plan_filters', {})
                )

            # Fetch workflows if needed
            if data_plan.get('needs_workflows'):
                fetched_data['workflows'] = self._fetch_workflows(
                    data_plan.get('workflow_filters', {})
                )

            # Fetch executions if needed
            if data_plan.get('needs_executions'):
                fetched_data['executions'] = self._fetch_executions(
                    data_plan.get('execution_filters', {})
                )

            # Add metadata about the fetch
            fetched_data['_metadata'] = {
                'fetch_timestamp': datetime.now().isoformat(),
                'total_records': sum(len(v) if isinstance(v, list) else 1 for k, v in fetched_data.items() if k != '_metadata'),
                'data_sources': list(fetched_data.keys())
            }

            return fetched_data

        except Exception as e:
            raise Exception(f"Data fetching failed: {str(e)}")

    def _fetch_transcripts(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch transcripts with filters.

        Args:
            filters: Filter parameters

        Returns:
            List of transcript dictionaries
        """
        try:
            # Get basic transcripts
            transcripts = self.transcript_store.get_all()

            # Convert to dicts if needed
            if transcripts and hasattr(transcripts[0], 'to_dict'):
                transcripts = [t.to_dict() for t in transcripts]

            # Apply filters
            filtered = self._apply_transcript_filters(transcripts, filters)

            return filtered

        except Exception as e:
            raise Exception(f"Transcript fetching failed: {str(e)}")

    def _fetch_analyses(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch analyses with filters.

        Args:
            filters: Filter parameters

        Returns:
            List of analysis dictionaries
        """
        try:
            # Get all analyses
            analyses = self.analysis_store.get_all()

            # Convert to dicts if needed
            result = []
            for a in analyses:
                if hasattr(a, 'to_dict'):
                    result.append(a.to_dict())
                elif isinstance(a, dict):
                    result.append(a)
                else:
                    # Fail fast if unexpected type
                    raise ValueError(f"Unexpected analysis type: {type(a)}")

            # Apply filters
            filtered = self._apply_analysis_filters(result, filters)

            return filtered

        except Exception as e:
            raise Exception(f"Analysis fetching failed: {str(e)}")

    def _fetch_plans(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch action plans with filters.

        Args:
            filters: Filter parameters

        Returns:
            List of plan dictionaries
        """
        try:
            # Get all plans
            plans = self.plan_store.get_all()

            # Convert to dicts if needed
            if plans and hasattr(plans[0], 'to_dict'):
                plans = [p.to_dict() for p in plans]

            # Apply filters
            filtered = self._apply_plan_filters(plans, filters)

            return filtered

        except Exception as e:
            raise Exception(f"Plan fetching failed: {str(e)}")

    def _fetch_workflows(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch workflows with filters.

        Args:
            filters: Filter parameters

        Returns:
            List of workflow dictionaries
        """
        try:
            # Get all workflows
            workflows = self.workflow_store.get_all()

            # Apply filters
            filtered = self._apply_workflow_filters(workflows, filters)

            return filtered

        except Exception as e:
            raise Exception(f"Workflow fetching failed: {str(e)}")

    def _fetch_executions(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch executions with filters.

        Args:
            filters: Filter parameters

        Returns:
            List of execution dictionaries
        """
        try:
            # Get all executions
            executions = self.execution_store.get_all()

            # Apply filters
            filtered = self._apply_execution_filters(executions, filters)

            return filtered

        except Exception as e:
            raise Exception(f"Execution fetching failed: {str(e)}")

    def _apply_transcript_filters(self, transcripts: List[Dict[str, Any]],
                                 filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to transcript list.

        Args:
            transcripts: List of transcripts
            filters: Filter parameters

        Returns:
            Filtered transcripts
        """
        filtered = transcripts

        # Date range filter
        if filters.get('date_range'):
            start_date = filters['date_range'].get('start')
            end_date = filters['date_range'].get('end')
            if start_date or end_date:
                filtered = [t for t in filtered if self._in_date_range(
                    t.get('timestamp'), start_date, end_date)]

        # Topic filter
        if filters.get('topic'):
            topic = filters['topic'].lower()
            filtered = [t for t in filtered if topic in t.get('topic', '').lower()]

        # Customer ID filter
        if filters.get('customer_id'):
            customer_id = filters['customer_id']
            filtered = [t for t in filtered if t.get('customer_id') == customer_id]

        # Limit results
        limit = filters.get('limit', 1000)
        return filtered[:limit]

    def _apply_analysis_filters(self, analyses: List[Dict[str, Any]],
                               filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to analysis list.

        Args:
            analyses: List of analyses
            filters: Filter parameters

        Returns:
            Filtered analyses
        """
        filtered = analyses

        # Date range filter
        if filters.get('date_range'):
            start_date = filters['date_range'].get('start')
            end_date = filters['date_range'].get('end')
            if start_date or end_date:
                filtered = [a for a in filtered if self._in_date_range(
                    a.get('timestamp'), start_date, end_date)]

        # Compliance filter
        if filters.get('has_compliance_issues'):
            filtered = [a for a in filtered if self._has_compliance_issues(a)]

        # Risk level filter
        if filters.get('risk_level'):
            risk_level = filters['risk_level'].upper()
            filtered = [a for a in filtered if a.get('risk_level') == risk_level]

        # Sentiment filter
        if filters.get('sentiment'):
            sentiment = filters['sentiment'].lower()
            filtered = [a for a in filtered if sentiment in str(a.get('sentiment', '')).lower()]

        # Limit results
        limit = filters.get('limit', 1000)
        return filtered[:limit]

    def _apply_workflow_filters(self, workflows: List[Dict[str, Any]],
                               filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to workflow list.

        Args:
            workflows: List of workflows
            filters: Filter parameters

        Returns:
            Filtered workflows
        """
        filtered = workflows

        # Status filter
        if filters.get('status'):
            status = filters['status']
            filtered = [w for w in filtered if w.get('status') == status]

        # Risk level filter
        if filters.get('risk_level'):
            risk_level = filters['risk_level']
            filtered = [w for w in filtered if w.get('risk_level') == risk_level]

        # Workflow type filter
        if filters.get('workflow_type'):
            workflow_type = filters['workflow_type']
            filtered = [w for w in filtered if w.get('workflow_type') == workflow_type]

        # Approval required filter
        if filters.get('requires_approval') is not None:
            requires_approval = filters['requires_approval']
            filtered = [w for w in filtered if w.get('requires_human_approval') == requires_approval]

        # Limit results
        limit = filters.get('limit', 1000)
        return filtered[:limit]

    def _apply_execution_filters(self, executions: List[Dict[str, Any]],
                                filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to execution list.

        Args:
            executions: List of executions
            filters: Filter parameters

        Returns:
            Filtered executions
        """
        filtered = executions

        # Status filter
        if filters.get('status'):
            status = filters['status']
            filtered = [e for e in filtered if e.get('status') == status]

        # Success filter
        if filters.get('successful') is not None:
            successful = filters['successful']
            filtered = [e for e in filtered if e.get('successful') == successful]

        # Date range filter
        if filters.get('date_range'):
            start_date = filters['date_range'].get('start')
            end_date = filters['date_range'].get('end')
            if start_date or end_date:
                filtered = [e for e in filtered if self._in_date_range(
                    e.get('started_at'), start_date, end_date)]

        # Limit results
        limit = filters.get('limit', 1000)
        return filtered[:limit]

    def _apply_plan_filters(self, plans: List[Dict[str, Any]],
                           filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to plan list.

        Args:
            plans: List of plans
            filters: Filter parameters

        Returns:
            Filtered plans
        """
        filtered = plans

        # Status filter
        if filters.get('status'):
            status = filters['status']
            filtered = [p for p in filtered if p.get('status') == status]

        # Priority filter
        if filters.get('priority'):
            priority = filters['priority']
            filtered = [p for p in filtered if p.get('priority') == priority]

        # Limit results
        limit = filters.get('limit', 1000)
        return filtered[:limit]

    def _in_date_range(self, timestamp_str: str, start_date: str = None,
                      end_date: str = None) -> bool:
        """Check if timestamp is in date range.

        Args:
            timestamp_str: Timestamp string
            start_date: Start date string
            end_date: End date string

        Returns:
            True if in range
        """
        if not timestamp_str:
            return False

        try:
            # Parse timestamp
            if isinstance(timestamp_str, str):
                # Try different formats
                for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d']:
                    try:
                        timestamp = datetime.strptime(timestamp_str.split('.')[0], fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return False
            else:
                timestamp = timestamp_str

            # Check start date
            if start_date:
                start = datetime.fromisoformat(start_date.replace('Z', ''))
                if timestamp < start:
                    return False

            # Check end date
            if end_date:
                end = datetime.fromisoformat(end_date.replace('Z', ''))
                if timestamp > end:
                    return False

            return True

        except Exception:
            return False

    def _has_compliance_issues(self, analysis: Dict[str, Any]) -> bool:
        """Check if analysis has compliance issues.

        Args:
            analysis: Analysis dictionary

        Returns:
            True if has compliance issues
        """
        # Look for compliance indicators in various fields
        compliance_fields = ['compliance_issues', 'violations', 'compliance_flags']

        for field in compliance_fields:
            if field in analysis:
                value = analysis[field]
                if value:
                    # Could be boolean, list, or string
                    if isinstance(value, bool):
                        return value
                    elif isinstance(value, (list, dict)):
                        return len(value) > 0
                    elif isinstance(value, str):
                        return value.lower() not in ['none', 'false', '', 'null']

        # Check for compliance-related keywords in text fields
        text_fields = ['summary', 'issues', 'recommendations']
        compliance_keywords = ['compliance', 'violation', 'fdcpa', 'respa', 'tila', 'regulatory']

        for field in text_fields:
            if field in analysis and analysis[field]:
                text = str(analysis[field]).lower()
                if any(keyword in text for keyword in compliance_keywords):
                    return True

        return False

    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of available data across all stores.

        Returns:
            Data summary statistics
        """
        try:
            summary = {}

            # Transcript summary
            transcripts = self.transcript_store.get_all()
            summary['transcripts'] = {
                'total_count': len(transcripts),
                'sample_topics': list(set(t.get('topic', 'unknown') for t in (
                    [t.to_dict() if hasattr(t, 'to_dict') else t for t in transcripts[:10]]
                )))[:5]
            }

            # Analysis summary
            analyses = self.analysis_store.get_all()
            analysis_dicts = []
            for a in analyses:
                if hasattr(a, 'to_dict'):
                    analysis_dicts.append(a.to_dict())
                elif isinstance(a, dict):
                    analysis_dicts.append(a)

            compliance_count = sum(1 for a in analysis_dicts if self._has_compliance_issues(a))
            summary['analyses'] = {
                'total_count': len(analysis_dicts),
                'compliance_issues_count': compliance_count,
                'compliance_rate': round((1 - compliance_count / max(len(analysis_dicts), 1)) * 100, 2)
            }

            # Workflow summary
            workflows = self.workflow_store.get_all()
            summary['workflows'] = {
                'total_count': len(workflows),
                'pending_approval': len([w for w in workflows if w.get('status') == 'AWAITING_APPROVAL']),
                'high_risk': len([w for w in workflows if w.get('risk_level') == 'HIGH'])
            }

            # Execution summary
            executions = self.execution_store.get_all()
            successful_count = sum(1 for e in executions if e.get('successful'))
            summary['executions'] = {
                'total_count': len(executions),
                'successful_count': successful_count,
                'success_rate': round(successful_count / max(len(executions), 1) * 100, 2)
            }

            return summary

        except Exception as e:
            raise Exception(f"Data summary failed: {str(e)}")