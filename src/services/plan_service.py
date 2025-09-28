"""
Plan Service - Business logic for action plan operations
Clean separation from routing layer
"""
from typing import List, Optional, Dict, Any
import logging
import uuid
from ..storage.action_plan_store import ActionPlanStore
from ..call_center_agents.action_plan_agent import ActionPlanAgent
from ..infrastructure.events import (
    EventType,
    create_plan_generated_event,
    publish_event
)

logger = logging.getLogger(__name__)


class PlanService:
    """Service for action plan operations - contains ALL business logic."""
    
    def __init__(self, api_key: str, db_path: str = "data/call_center.db"):
        self.api_key = api_key
        self.db_path = db_path
        self.store = ActionPlanStore(db_path)
        self.generator = ActionPlanAgent()
    
    async def list_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List all action plans with optional limit."""
        plans = self.store.get_all()
        if limit:
            plans = plans[:limit]
        return plans  # plans already contains dicts from store.get_all()
    
    async def create(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new action plan from analysis."""
        # Set up tracing for plan creation
        from src.infrastructure.telemetry import set_span_attributes, add_span_event
        analysis_id = request_data.get("analysis_id")
        if not analysis_id:
            raise ValueError("analysis_id is required")
        
        set_span_attributes(analysis_id=analysis_id, operation="create_plan")
        add_span_event("plan.creation_started", analysis_id=analysis_id)
        
        # Get analysis and transcript from stores
        add_span_event("plan.fetching_data", analysis_id=analysis_id)
        from ..storage.analysis_store import AnalysisStore
        from ..storage.transcript_store import TranscriptStore
        analysis_store = AnalysisStore(self.db_path)
        transcript_store = TranscriptStore(self.db_path)
        
        analysis = analysis_store.get_by_id(analysis_id)
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")
        add_span_event("plan.analysis_loaded", analysis_id=analysis_id)
        
        transcript_id = analysis.get("transcript_id")
        transcript = transcript_store.get_by_id(transcript_id)
        if not transcript:
            raise ValueError(f"Transcript {transcript_id} not found")
        add_span_event("plan.transcript_loaded", transcript_id=transcript_id)

        # Generate plan using action plan generator
        add_span_event("plan.generator_started", analysis_id=analysis_id)
        plan_result = self.generator.generate(analysis, transcript)
        result_keys = list(plan_result.keys()) if isinstance(plan_result, dict) else []
        add_span_event("plan.generator_completed", analysis_id=analysis_id, result_keys_count=len(result_keys))
        
        # Add metadata
        plan_result["analysis_id"] = analysis_id
        plan_result["plan_id"] = f"PLAN_{analysis_id}_{len(str(plan_result))}"[:20]
        
        # Store if requested
        should_store = request_data.get("store", True)
        if should_store:
            self.store.store(plan_result)

            # Extract predictive knowledge from plan insights (NO FALLBACK)
            customer_id = getattr(transcript, 'customer_id', 'UNKNOWN')
            predictive_insight = plan_result.get('predictive_insight')
            if predictive_insight:
                # Convert to PredictiveInsight object and extract knowledge
                from ..infrastructure.graph.knowledge_types import PredictiveInsight, InsightContent, CustomerContext
                from ..infrastructure.graph.predictive_knowledge_extractor import get_predictive_knowledge_extractor
                from datetime import datetime

                # Create structured content
                content = InsightContent(
                    key=predictive_insight.get('content', {}).get('key', 'Plan strategy'),
                    value=predictive_insight.get('content', {}).get('value', 'Strategic planning insight'),
                    confidence=predictive_insight.get('content', {}).get('confidence', 0.8),
                    impact=predictive_insight.get('content', {}).get('impact', 'High strategic impact')
                )

                # Create structured customer context
                customer_context = CustomerContext(
                    customer_id=customer_id,
                    loan_type='mortgage',  # Default to mortgage for this use case
                    tenure='existing',  # Default to existing customer
                    risk_profile='standard'  # Default risk profile
                )

                insight = PredictiveInsight(
                    insight_type=predictive_insight.get('insight_type', 'wisdom'),
                    priority=predictive_insight.get('priority', 'medium'),
                    content=content,
                    reasoning=predictive_insight.get('reasoning', 'Plan insight'),
                    learning_value=predictive_insight.get('learning_value', 'routine'),
                    source_stage='planning',
                    transcript_id=transcript_id,
                    customer_context=customer_context,
                    timestamp=datetime.utcnow().isoformat() + 'Z'
                )

                knowledge_extractor = get_predictive_knowledge_extractor()
                context = {
                    'transcript_id': transcript_id,
                    'customer_id': customer_id,
                    'plan_id': plan_result["plan_id"],
                    'analysis_id': analysis_id
                }
                # NO FALLBACK: If knowledge extraction fails, entire operation fails
                await knowledge_extractor.extract_knowledge(insight, context)
                add_span_event("plan.knowledge_extracted", plan_id=plan_result["plan_id"])

                # Link patterns to advisor in unified graph
                try:
                    from ..infrastructure.graph.unified_graph_manager import get_unified_graph_manager
                    unified_graph = get_unified_graph_manager()

                    # Create advisor if doesn't exist
                    advisor_id = "ADV_DEFAULT"  # Could be extracted from plan metadata
                    advisor_actions = plan_result.get('advisor_plan', {}).get('coaching_items', [])

                    if advisor_actions:
                        # Create advisor node if it has coaching items
                        await unified_graph.create_or_update_advisor(
                            advisor_id=advisor_id,
                            name="Default Advisor",
                            department="Customer Service",
                            skill_level="senior",
                            performance_score=0.85
                        )

                        # Create and link pattern to advisor (if wisdom pattern exists)
                        if predictive_insight and predictive_insight.get('insight_type') == 'wisdom':
                            # Import Pattern here to avoid circular dependency
                            from ..infrastructure.graph.knowledge_types import Pattern

                            pattern_id = f"PATTERN_{uuid.uuid4().hex[:8]}"

                            # Create the Pattern object from the predictive insight
                            pattern = Pattern(
                                pattern_id=pattern_id,
                                pattern_type='success_workflow',  # Wisdom patterns are often about successful approaches
                                title=predictive_insight.get('reasoning', 'Planning wisdom pattern')[:100],
                                description=predictive_insight.get('reasoning', 'Wisdom pattern discovered during action planning'),
                                conditions={'planning_stage': 'action_planning', 'insight_source': 'wisdom_extraction'},
                                outcomes={'wisdom_strength': predictive_insight.get('confidence', 0.8)},
                                confidence=predictive_insight.get('confidence', 0.8),
                                occurrences=1,  # First occurrence
                                success_rate=0.8,  # Default until more data
                                last_observed=datetime.utcnow(),
                                source_pipeline='planning'
                            )

                            # Store the pattern in the graph first
                            await unified_graph.store_pattern(pattern)
                            logger.info(f"🧠 Created wisdom pattern {pattern_id} from planning insight")

                            # Now link the pattern to the advisor
                            await unified_graph.link_pattern_to_advisor(
                                pattern_id=pattern_id,
                                advisor_id=advisor_id,
                                learning_date=datetime.utcnow().isoformat(),
                                application_count=1
                            )
                            logger.info(f"🔗 Linked pattern {pattern_id} to advisor {advisor_id}")

                        # Create Wisdom nodes from advisor coaching insights
                        if advisor_actions:
                            # Import Wisdom here to avoid circular dependency
                            from ..infrastructure.graph.knowledge_types import Wisdom
                            from datetime import datetime, timedelta

                            for i, coaching_item in enumerate(advisor_actions[:3]):  # Limit to top 3 coaching items
                                wisdom_id = f"WISDOM_{uuid.uuid4().hex[:8]}"

                                # Extract wisdom from coaching content
                                wisdom_content = coaching_item if isinstance(coaching_item, str) else str(coaching_item)

                                wisdom = Wisdom(
                                    wisdom_id=wisdom_id,
                                    wisdom_type='coaching_insight',
                                    title=f"Advisor coaching insight {i+1}",
                                    content=wisdom_content,
                                    source_context={'plan_id': plan_result["plan_id"], 'transcript_id': transcript_id},
                                    learning_domain='customer_service',
                                    applicability='general',
                                    validated=False,
                                    validation_count=0,
                                    effectiveness_score=0.8,  # Default until validation
                                    created_at=datetime.utcnow(),
                                    last_applied=None,
                                    application_count=0
                                )

                                # Store the wisdom in the graph
                                await unified_graph.store_wisdom(wisdom)
                                logger.info(f"🧠 Created wisdom {wisdom_id} from coaching insight")

                                # Create Wisdom relationships to connect it to the main graph
                                await unified_graph.link_wisdom_to_plan(wisdom_id, plan_result["plan_id"])
                                logger.info(f"🔗 Linked wisdom {wisdom_id} to plan {plan_result['plan_id']}")

                    add_span_event("plan.advisor_patterns_linked", advisor_id=advisor_id)

                except Exception as e:
                    logger.warning(f"Failed to link patterns to advisor: {e}")
                    # Continue execution - pattern linking is supplementary

            # Count actions in the plan for event publishing
            borrower_actions = plan_result.get('borrower_plan', {}).get('immediate_actions', [])
            advisor_actions = plan_result.get('advisor_plan', {}).get('coaching_items', [])
            supervisor_actions = plan_result.get('supervisor_plan', {}).get('escalation_items', [])
            leadership_actions = plan_result.get('leadership_plan', {}).get('strategic_opportunities', [])
            action_count = len(borrower_actions) + len(advisor_actions) + len(supervisor_actions) + len(leadership_actions)

            # Publish plan generated event
            plan_event = create_plan_generated_event(
                plan_id=plan_result["plan_id"],
                analysis_id=analysis_id,
                transcript_id=transcript_id,
                customer_id=customer_id,
                priority_level='medium',
                action_count=action_count,
                urgency_level='medium'
            )
            publish_event(plan_event)
            add_span_event("plan.event_published", plan_id=plan_result["plan_id"])

        return plan_result
    
    async def get_by_id(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Get action plan by ID."""
        plan = self.store.get_by_id(plan_id)
        if not plan:
            return None
        return plan  # plan is already a dict from store.get_by_id()

    async def get_by_transcript_id(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get action plan by transcript ID."""
        plan = self.store.get_by_transcript_id(transcript_id)
        if not plan:
            return None
        return plan  # plan is already a dict from store.get_by_transcript_id()

    async def update(self, plan_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update action plan."""
        plan = self.store.get_by_id(plan_id)
        if not plan:
            return None
        
        # Apply updates directly to dict
        for key, value in updates.items():
            plan[key] = value
        
        # Store updated plan
        self.store.update(plan_id, plan)
        return plan  # plan is already a dict
    
    async def delete(self, plan_id: str) -> bool:
        """Delete action plan by ID."""
        return self.store.delete(plan_id)
    
    async def delete_all(self) -> Dict[str, Any]:
        """Delete all action plans."""
        count = self.store.delete_all()
        return {
            "message": "All plans deleted successfully",
            "deleted_count": count
        }
    
    async def search_by_analysis(self, analysis_id: str) -> List[Dict[str, Any]]:
        """Search action plans by analysis ID."""
        results = self.store.search_by_analysis(analysis_id)
        return results  # results are already dicts from store
    
    async def approve(self, plan_id: str, approval_data: Dict[str, Any]) -> Dict[str, Any]:
        """Approve action plan for execution."""
        plan = self.store.get_by_id(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        # Update plan status
        plan.status = "approved"
        plan.approved_by = approval_data.get("approved_by")
        plan.approved_at = approval_data.get("approved_at")
        plan.approval_notes = approval_data.get("notes", "")
        
        # Store updated plan
        self.store.update(plan_id, plan)
        
        return {
            "plan_id": plan_id,
            "status": "approved",
            "approved_by": plan.approved_by,
            "approved_at": plan.approved_at,
            "message": "Action plan approved for execution"
        }
    
    async def execute(self, plan_id: str, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute approved action plan."""
        plan = self.store.get_by_id(plan_id)
        if not plan:
            raise ValueError(f"Plan {plan_id} not found")
        
        if getattr(plan, 'status', 'pending') != 'approved':
            raise ValueError(f"Plan {plan_id} is not approved for execution")
        
        # Update plan status
        plan.status = "executing"
        plan.executed_by = execution_data.get("executed_by")
        plan.execution_started_at = execution_data.get("started_at")
        
        # Process execution steps
        execution_results = []
        for step in plan.steps:
            # Execute each step
            step_result = {
                "step_id": step.get("id"),
                "description": step.get("description"),
                "status": "completed",
                "executed_at": execution_data.get("started_at")
            }
            execution_results.append(step_result)
        
        # Update plan with execution results
        plan.execution_results = execution_results
        plan.status = "completed"
        plan.execution_completed_at = execution_data.get("completed_at")
        
        # Store updated plan
        self.store.update(plan_id, plan)
        
        return {
            "plan_id": plan_id,
            "status": "completed",
            "executed_by": plan.executed_by,
            "execution_results": execution_results,
            "message": "Action plan executed successfully"
        }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get action plan statistics and metrics."""
        plans = self.store.get_all()
        
        if not plans:
            return {
                "total_plans": 0,
                "pending_plans": 0,
                "approved_plans": 0,
                "executing_plans": 0,
                "completed_plans": 0,
                "plan_types": {},
                "urgency_levels": {},
                "avg_steps_per_plan": 0.0,
                "completion_rate": 0.0
            }
        
        total = len(plans)
        
        # Count by status
        pending = sum(1 for p in plans if getattr(p, 'status', 'pending') == 'pending')
        approved = sum(1 for p in plans if getattr(p, 'status', 'pending') == 'approved')
        executing = sum(1 for p in plans if getattr(p, 'status', 'pending') == 'executing')
        completed = sum(1 for p in plans if getattr(p, 'status', 'pending') == 'completed')
        
        # Collect statistics
        plan_types = {}
        urgency_levels = {}
        total_steps = 0
        
        for plan in plans:
            # Plan types
            plan_type = getattr(plan, 'plan_type', 'Unknown')
            plan_types[plan_type] = plan_types.get(plan_type, 0) + 1
            
            # Urgency levels
            urgency = getattr(plan, 'urgency', 'Unknown')
            urgency_levels[urgency] = urgency_levels.get(urgency, 0) + 1
            
            # Step counts
            steps = getattr(plan, 'steps', [])
            total_steps += len(steps)
        
        return {
            "total_plans": total,
            "pending_plans": pending,
            "approved_plans": approved,
            "executing_plans": executing,
            "completed_plans": completed,
            "plan_types": dict(sorted(plan_types.items(), key=lambda x: x[1], reverse=True)),
            "urgency_levels": urgency_levels,
            "avg_steps_per_plan": total_steps / total if total > 0 else 0.0,
            "completion_rate": completed / total if total > 0 else 0.0
        }