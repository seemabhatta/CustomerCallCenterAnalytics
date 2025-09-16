"""
Observer Agent - Feedback Loop Implementation
Implements the "Co-Pilot Review & Evaluation (Self-Critique)" functionality.

The Observer Agent evaluates execution results, identifies improvement opportunities,
and provides actionable feedback to the Decision Agent for continuous learning.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter

from src.storage.approval_store import ApprovalStore
from src.infrastructure.llm.openai_wrapper import OpenAIWrapper
from src.agents.models.observer_models import ExecutionEvaluation, DecisionAgentFeedback
import os


class FeedbackType(Enum):
    """Types of feedback the Observer can provide"""
    POSITIVE_REINFORCEMENT = "positive_reinforcement"
    CORRECTIVE_ACTION = "corrective_action"
    PROCESS_IMPROVEMENT = "process_improvement"
    SYSTEMIC_ISSUE = "systemic_issue"


@dataclass
class ObservationResult:
    """Result of an observation cycle"""
    execution_id: str
    feedback_type: FeedbackType
    overall_satisfaction: str  # satisfactory, unsatisfactory, needs_improvement
    execution_quality: float  # 1.0-5.0 scale
    identified_issues: List[str]
    improvement_opportunities: List[str]
    actor_performance_notes: Dict[str, str]
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['feedback_type'] = self.feedback_type.value
        return data


class ObserverAgent:
    """
    Observer Agent implements the feedback loop for continuous learning.
    
    Key responsibilities:
    1. Observe execution results from actors
    2. Evaluate satisfaction and quality
    3. Identify systemic issues and patterns
    4. Generate actionable feedback for Decision Agent
    5. Build lessons-learned dataset
    """
    
    def __init__(self, db_path: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize the Observer Agent"""
        if db_path:
            self.approval_store = ApprovalStore(db_path)
        else:
            self.approval_store = None
            
        # Initialize OpenAI wrapper
        self.llm = OpenAIWrapper()
            
        self.observation_history: List[Dict[str, Any]] = []
        self.lessons_learned: List[Dict[str, Any]] = []
        self.feedback_patterns: Dict[str, List[str]] = defaultdict(list)
        
        # Configuration thresholds
        self.config = {
            'satisfaction_threshold': 3.0,      # Below this = needs improvement
            'quality_threshold': 3.5,           # Below this = corrective action needed
            'systemic_issue_frequency': 3,      # Issues appearing 3+ times = systemic
            'actor_performance_threshold': 0.7  # Success rate below this = needs training
        }

    def observe_execution_results(self, execution_id: str) -> ObservationResult:
        """
        Observe and evaluate execution results for a given execution ID.
        
        Args:
            execution_id: The execution ID to observe
            
        Returns:
            ObservationResult with evaluation and feedback
        """
        if not self.approval_store:
            raise Exception("ApprovalStore not initialized - cannot observe execution results")
            
        # Get execution results from approval store
        execution_results = self.approval_store.get_execution_results_by_execution_id(execution_id)
        
        if not execution_results:
            raise ValueError(f"No execution results found for execution_id: {execution_id}")
        
        # Use LLM to evaluate execution results
        evaluation = self._evaluate_execution_with_llm(execution_results)
        
        # Determine feedback type based on evaluation
        feedback_type = self._determine_feedback_type(evaluation)
        
        # Create observation result
        observation_result = ObservationResult(
            execution_id=execution_id,
            feedback_type=feedback_type,
            overall_satisfaction=evaluation.get('overall_satisfaction', 'unknown'),
            execution_quality=evaluation.get('execution_quality', 0.0),
            identified_issues=evaluation.get('identified_issues', []),
            improvement_opportunities=evaluation.get('improvement_opportunities', []),
            actor_performance_notes=self._extract_actor_notes(execution_results, evaluation)
        )
        
        # Store observation in history
        self.observation_history.append({
            'execution_id': execution_id,
            'timestamp': observation_result.timestamp,
            'identified_issues': observation_result.identified_issues,
            'actor_performance': observation_result.actor_performance_notes,
            'feedback_type': feedback_type.value
        })
        
        return observation_result

    def _evaluate_execution_with_llm(self, execution_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Use LLM to evaluate execution results and provide assessment"""
        
        evaluation_prompt = f"""
        As an AI Observer Agent, evaluate these execution results from our customer service action plan:

        EXECUTION RESULTS:
        {json.dumps(execution_results, indent=2)}

        Please provide a comprehensive evaluation in JSON format with these fields:
        - overall_satisfaction: "satisfactory", "unsatisfactory", or "needs_improvement"  
        - execution_quality: numeric score from 1.0-5.0
        - identified_issues: list of specific issues found
        - improvement_opportunities: list of actionable improvements
        - feedback_for_decision_agent: insights for improving future decision routing

        Focus on:
        1. Did actors complete actions successfully?
        2. Were there process gaps or failures?
        3. What patterns suggest systemic issues?
        4. How can routing/approval decisions be improved?
        5. Are there compliance or quality concerns?

        Provide objective, actionable feedback that helps improve the system.
        """
        
        try:
            # Use OpenAI wrapper with structured output
            evaluation_result = self.llm.generate_structured(
                prompt=evaluation_prompt,
                schema_model=ExecutionEvaluation,
                temperature=0.3
            )

            return evaluation_result.model_dump()
            
        except Exception as e:
            raise Exception(f"Observer Agent evaluation failed: {str(e)}")


    def _determine_feedback_type(self, evaluation: Dict[str, Any]) -> FeedbackType:
        """Determine appropriate feedback type based on evaluation"""
        satisfaction = evaluation.get('overall_satisfaction', 'unknown')
        quality = evaluation.get('execution_quality', 0.0)
        issues_count = len(evaluation.get('identified_issues', []))
        
        if satisfaction == 'satisfactory' and quality >= self.config['quality_threshold']:
            return FeedbackType.POSITIVE_REINFORCEMENT
        elif issues_count >= self.config['systemic_issue_frequency']:
            return FeedbackType.SYSTEMIC_ISSUE
        elif satisfaction == 'unsatisfactory' or quality < self.config['satisfaction_threshold']:
            return FeedbackType.CORRECTIVE_ACTION
        else:
            return FeedbackType.PROCESS_IMPROVEMENT

    def _extract_actor_notes(self, execution_results: List[Dict[str, Any]], 
                           evaluation: Dict[str, Any]) -> Dict[str, str]:
        """Extract performance notes for each actor involved"""
        actor_notes = {}
        
        for result in execution_results:
            actor = result.get('actor', 'Unknown')
            status = result.get('status', 'unknown')
            feedback = result.get('actor_feedback', 'No feedback provided')
            
            if status == 'completed':
                actor_notes[actor] = f"Successful execution - {feedback}"
            else:
                actor_notes[actor] = f"Execution issues - {feedback}"
                
        return actor_notes

    def analyze_actor_performance_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Analyze performance patterns across all actors"""
        if not self.approval_store:
            return {}
            
        performance_metrics = self.approval_store.get_actor_performance_metrics()
        patterns = {}
        
        for actor, metrics in performance_metrics.items():
            success_rate = metrics.get('success_rate', 0.0)
            avg_satisfaction = metrics.get('customer_satisfaction', 0.0)
            
            # Determine performance grade
            if success_rate >= 0.9 and avg_satisfaction >= 4.0:
                grade = "excellent"
                recommendation = "Continue current approach"
            elif success_rate >= 0.7 and avg_satisfaction >= 3.5:
                grade = "good"
                recommendation = "Minor improvements possible"
            else:
                grade = "needs_improvement" 
                recommendation = "Requires training and process review"
            
            patterns[actor] = {
                'performance_grade': grade,
                'success_rate': success_rate,
                'avg_satisfaction': avg_satisfaction,
                'training_recommendation': recommendation,
                'total_actions': metrics.get('total_actions', 0)
            }
            
        return patterns

    def generate_feedback_for_decision_agent(self, observation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate actionable feedback for the Decision Agent to improve routing"""
        
        feedback_prompt = f"""
        Based on this execution observation data, generate actionable feedback for our Decision Agent:

        OBSERVATION DATA:
        {json.dumps(observation_data, indent=2)}

        Generate feedback in JSON format with these fields:
        - routing_adjustments: changes to approval routing logic
        - risk_assessment_updates: updates to risk evaluation criteria  
        - process_improvements: workflow enhancements
        - training_recommendations: actor-specific training needs

        Focus on:
        1. How can routing decisions be improved?
        2. What risk factors should be weighted differently?
        3. What process gaps need addressing?
        4. Which actors need additional training?

        Provide specific, implementable recommendations.
        """
        
        try:
            # Use OpenAI wrapper with structured output
            feedback_result = self.llm.generate_structured(
                prompt=feedback_prompt,
                schema_model=DecisionAgentFeedback,
                temperature=0.3
            )

            return feedback_result.model_dump()
            
        except Exception as e:
            raise Exception(f"Observer Agent feedback generation failed: {str(e)}")

    def identify_systemic_issues(self) -> List[Dict[str, Any]]:
        """Identify systemic issues from observation history"""
        issue_counter = Counter()
        
        # Count frequency of each issue type
        for observation in self.observation_history:
            for issue in observation.get('identified_issues', []):
                issue_counter[issue] += 1
        
        systemic_issues = []
        threshold = self.config['systemic_issue_frequency']
        
        for issue, frequency in issue_counter.items():
            if frequency >= threshold:
                # Determine severity based on frequency and impact
                severity = 'high' if frequency >= threshold * 2 else 'medium'
                
                systemic_issues.append({
                    'pattern': issue,
                    'frequency': frequency,
                    'severity': severity,
                    'first_observed': self._find_first_occurrence(issue),
                    'recommended_action': self._recommend_systemic_fix(issue)
                })
        
        return sorted(systemic_issues, key=lambda x: x['frequency'], reverse=True)

    def _find_first_occurrence(self, issue: str) -> str:
        """Find when an issue was first observed"""
        for observation in self.observation_history:
            if issue in observation.get('identified_issues', []):
                return observation.get('timestamp', 'unknown')
        return 'unknown'

    def _recommend_systemic_fix(self, issue: str) -> str:
        """Recommend fix for systemic issue"""
        issue_lower = issue.lower()
        
        if 'documentation' in issue_lower:
            return 'Implement automated documentation validation'
        elif 'approval' in issue_lower:
            return 'Review approval workflow and thresholds'
        elif 'communication' in issue_lower:
            return 'Enhance communication protocols and training'
        elif 'process' in issue_lower:
            return 'Conduct process mapping and optimization'
        else:
            return 'Conduct root cause analysis'

    def extract_learning_insights(self) -> Dict[str, Any]:
        """Extract learning insights for continuous improvement"""
        positive_patterns = []
        failure_patterns = []
        
        for observation in self.observation_history:
            feedback_type = observation.get('feedback_type', '')
            
            if feedback_type == FeedbackType.POSITIVE_REINFORCEMENT.value:
                positive_patterns.extend(observation.get('identified_issues', []))
            elif feedback_type == FeedbackType.CORRECTIVE_ACTION.value:
                failure_patterns.extend(observation.get('identified_issues', []))
        
        return {
            'pattern_recognition': {
                'total_observations': len(self.observation_history),
                'positive_feedback_rate': sum(1 for obs in self.observation_history 
                                            if obs.get('feedback_type') == FeedbackType.POSITIVE_REINFORCEMENT.value) / len(self.observation_history) if self.observation_history else 0
            },
            'success_factors': list(set(positive_patterns)),
            'failure_patterns': list(set(failure_patterns)),
            'learning_velocity': self._calculate_learning_velocity()
        }

    def _calculate_learning_velocity(self) -> float:
        """Calculate how quickly the system is improving"""
        if len(self.observation_history) < 2:
            return 0.0
            
        recent_observations = self.observation_history[-10:]  # Last 10 observations
        positive_trend = sum(1 for obs in recent_observations 
                           if obs.get('feedback_type') in [FeedbackType.POSITIVE_REINFORCEMENT.value, FeedbackType.PROCESS_IMPROVEMENT.value])
        
        return positive_trend / len(recent_observations)

    def detect_compliance_gaps(self, execution_results: List[Dict[str, Any]]) -> List[str]:
        """Detect compliance gaps in execution results"""
        compliance_gaps = []
        
        for result in execution_results:
            artifacts = result.get('execution_artifacts', {})
            
            # Check common compliance requirements
            if not artifacts.get('documentation_provided', True):
                compliance_gaps.append('Missing required documentation')
                
            if result.get('action_type') in ['financial_adjustment', 'account_modification']:
                if not artifacts.get('supervisor_approval', True):
                    compliance_gaps.append('Missing supervisor approval for financial action')
                    
            if not artifacts.get('compliance_checklist_completed', True):
                compliance_gaps.append('Compliance checklist not completed')
        
        return compliance_gaps

    def add_to_lessons_learned(self, observation_result: ObservationResult):
        """Add observation to lessons learned dataset"""
        lesson = {
            'execution_id': observation_result.execution_id,
            'timestamp': observation_result.timestamp,
            'what_went_wrong': observation_result.identified_issues,
            'what_went_right': self._extract_successes_from_observation(observation_result),
            'actionable_insights': observation_result.improvement_opportunities,
            'feedback_type': observation_result.feedback_type.value,
            'quality_score': observation_result.execution_quality
        }
        
        self.lessons_learned.append(lesson)

    def _extract_successes_from_observation(self, observation_result: ObservationResult) -> List[str]:
        """Extract successful patterns from observation"""
        successes = []
        
        if observation_result.execution_quality >= 4.0:
            successes.append('High quality execution achieved')
            
        if observation_result.overall_satisfaction == 'satisfactory':
            successes.append('Customer satisfaction maintained')
            
        for actor, note in observation_result.actor_performance_notes.items():
            if 'successful' in note.lower() or 'excellent' in note.lower():
                successes.append(f'{actor} performed effectively')
        
        return successes

    def get_lessons_learned(self) -> List[Dict[str, Any]]:
        """Get all lessons learned for review"""
        return self.lessons_learned.copy()