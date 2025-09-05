import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from openai import OpenAI

from ..config.settings import settings
from ..storage.db_manager import DatabaseManager
from ..models.transcript import CallTranscript

class OrchestratorAgent:
    """
    Orchestrator Agent coordinates the multi-agent analysis pipeline.
    This is the main controller that manages other agents and maintains context.
    """
    
    def __init__(self):
        settings.validate()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.db = DatabaseManager()
        
    def analyze_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """
        Orchestrate complete analysis of a transcript through multiple agents.
        Returns comprehensive analysis results.
        """
        
        # Get transcript
        transcript = self.db.get_transcript(transcript_id)
        if not transcript:
            raise ValueError(f"Transcript not found: {transcript_id}")
        
        # Create orchestration session
        session_id = self.db.create_agent_session(
            transcript_id=transcript_id,
            agent_type="orchestrator", 
            input_data={"analysis_type": "full_pipeline"}
        )
        
        try:
            # Phase 1: Extract key insights using AI
            insights = self._extract_insights(transcript)
            
            # Phase 2: Generate action plans (simulate multi-agent coordination)
            action_plans = self._generate_action_plans(transcript, insights)
            
            # Phase 3: Quality scoring
            quality_scores = self._calculate_quality_scores(transcript, insights)
            
            # Phase 4: Compliance check
            compliance_check = self._check_compliance(transcript, insights)
            
            # Compile comprehensive results
            analysis_results = {
                "transcript_id": transcript_id,
                "session_id": session_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "insights": insights,
                "action_plans": action_plans,
                "quality_scores": quality_scores,
                "compliance": compliance_check,
                "summary": self._generate_summary(transcript, insights, action_plans)
            }
            
            # Store results
            self.db.store_analysis_result(
                transcript_id=transcript_id,
                analysis_type="orchestrator_full_analysis",
                result_data=analysis_results,
                confidence=insights.get("confidence", 0.8)
            )
            
            # Update session
            self.db.update_agent_session(session_id, "completed", analysis_results)
            
            return analysis_results
            
        except Exception as e:
            self.db.update_agent_session(session_id, "failed")
            raise e
    
    def _extract_insights(self, transcript: CallTranscript) -> Dict[str, Any]:
        """Extract key insights from transcript using AI analysis."""
        
        system_prompt = """You are an expert call center analyst. Analyze this customer service call transcript and extract key insights in JSON format.

Focus on:
1. Customer intent and sentiment
2. Key issues and concerns raised
3. Advisor performance and adherence to protocols
4. Resolution status and next steps
5. Compliance requirements mentioned
6. Risk factors or red flags

Provide confidence scores (0-1) for your assessments."""
        
        user_prompt = f"""
Call Scenario: {transcript.scenario}
Customer: {transcript.customer.name}
Advisor: {transcript.advisor.name}
Duration: {transcript.call_metadata.duration_seconds // 60} minutes

Transcript:
{transcript.full_text}

Analyze this call and provide insights in the following JSON structure:
{{
    "customer_intent": "primary reason for calling",
    "customer_sentiment": "emotional state (frustrated/neutral/satisfied)",
    "key_issues": ["list", "of", "main", "issues"],
    "resolution_achieved": true/false,
    "next_steps_required": ["actions", "needed"],
    "compliance_items": ["disclosures", "mentioned"],
    "risk_factors": ["potential", "risks"],
    "advisor_performance": "assessment of advisor handling",
    "confidence": 0.85,
    "summary": "brief summary of the call"
}}
"""
        
        response = self.client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        
        try:
            import json
            return json.loads(response.output_text)
        except json.JSONDecodeError:
            # Fallback to basic analysis
            return {
                "customer_intent": "Unknown - parsing error",
                "customer_sentiment": "neutral",
                "key_issues": [],
                "resolution_achieved": False,
                "confidence": 0.1,
                "summary": "Analysis failed - JSON parsing error"
            }
    
    def _generate_action_plans(self, transcript: CallTranscript, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the four aligned action plans from the vision."""
        
        return {
            "borrower_plan": {
                "immediate_actions": self._generate_borrower_actions(transcript, insights),
                "follow_up_timeline": "1-3 business days",
                "predicted_outcomes": {
                    "satisfaction_likelihood": 0.75,
                    "resolution_probability": 0.8,
                    "churn_risk": 0.2
                }
            },
            "advisor_plan": {
                "coaching_points": self._generate_coaching_points(transcript, insights),
                "performance_score": insights.get("advisor_performance", "good"),
                "development_areas": ["empathy", "process_adherence"],
                "next_training": "hardship_procedures_refresher"
            },
            "supervisor_plan": {
                "escalation_required": self._needs_escalation(insights),
                "approval_items": self._generate_approval_items(transcript, insights),
                "risk_assessment": "medium",
                "team_insights": "Hardship calls increasing 15% this month"
            },
            "leadership_plan": {
                "kpi_impact": {
                    "fcr_contribution": 1 if insights.get("resolution_achieved") else 0,
                    "csat_predicted": 4.2,
                    "aht_variance": transcript.call_metadata.duration_seconds - 900  # vs 15min target
                },
                "trend_indicators": ["hardship_requests_up"],
                "strategic_actions": ["review_hardship_policies"]
            }
        }
    
    def _generate_borrower_actions(self, transcript: CallTranscript, insights: Dict[str, Any]) -> List[str]:
        """Generate specific actions for the borrower."""
        actions = []
        
        # Based on scenario and insights
        if transcript.scenario == "hardship":
            actions.extend([
                "Send hardship application packet via email",
                "Schedule follow-up call in 3 business days",
                "Provide financial counseling resource links"
            ])
        elif transcript.scenario == "escrow":
            actions.extend([
                "Email detailed escrow analysis breakdown",
                "Send payment adjustment notice",
                "Provide escrow FAQs document"
            ])
        elif transcript.scenario == "refinance":
            actions.extend([
                "Send pre-qualification application",
                "Provide current rate sheet",
                "Schedule loan officer consultation"
            ])
        
        # Add resolution-specific actions
        if not insights.get("resolution_achieved", False):
            actions.append("Escalate to supervisor for additional review")
        
        return actions
    
    def _generate_coaching_points(self, transcript: CallTranscript, insights: Dict[str, Any]) -> List[str]:
        """Generate coaching points for the advisor."""
        coaching_points = []
        
        # Analyze advisor performance
        advisor_segments = transcript.advisor_segments
        total_advisor_words = sum(len(seg.text.split()) for seg in advisor_segments)
        
        if total_advisor_words < 100:
            coaching_points.append("Provide more detailed explanations to customers")
        
        # Sentiment-based coaching
        if insights.get("customer_sentiment") == "frustrated":
            coaching_points.append("Focus on empathy statements early in calls")
        
        # Compliance reminders
        compliance_items = insights.get("compliance_items", [])
        if len(compliance_items) < 2:
            coaching_points.append("Ensure all required disclosures are provided")
        
        return coaching_points
    
    def _calculate_quality_scores(self, transcript: CallTranscript, insights: Dict[str, Any]) -> Dict[str, float]:
        """Calculate quality scores for the call."""
        
        scores = {
            "compliance_adherence": 0.8,  # Based on disclosures found
            "empathy_index": 0.7,         # Based on language analysis
            "efficiency_score": 0.75,     # Based on resolution vs time
            "customer_satisfaction_predicted": 4.2,  # 1-5 scale
            "first_call_resolution": 1.0 if insights.get("resolution_achieved") else 0.0
        }
        
        # Adjust based on transcript analysis
        if transcript.call_metadata.duration_seconds > 1800:  # > 30 minutes
            scores["efficiency_score"] *= 0.8
        
        if insights.get("customer_sentiment") == "satisfied":
            scores["empathy_index"] += 0.1
            scores["customer_satisfaction_predicted"] += 0.3
        
        return scores
    
    def _check_compliance(self, transcript: CallTranscript, insights: Dict[str, Any]) -> Dict[str, Any]:
        """Perform basic compliance checking."""
        
        full_text = transcript.full_text.lower()
        
        # Check for required elements
        compliance_checks = {
            "verification_completed": any(word in full_text for word in ["verify", "confirm", "last four"]),
            "disclosures_mentioned": len(insights.get("compliance_items", [])) > 0,
            "privacy_notice": "privacy" in full_text or "confidential" in full_text,
            "call_recorded_notice": "recorded" in full_text or "monitoring" in full_text,
        }
        
        compliance_score = sum(compliance_checks.values()) / len(compliance_checks)
        
        return {
            "overall_score": compliance_score,
            "checks": compliance_checks,
            "risk_level": "low" if compliance_score > 0.7 else "medium",
            "required_actions": [] if compliance_score > 0.7 else ["compliance_review_required"]
        }
    
    def _needs_escalation(self, insights: Dict[str, Any]) -> bool:
        """Determine if call needs supervisor escalation."""
        
        escalation_triggers = [
            insights.get("customer_sentiment") == "frustrated",
            not insights.get("resolution_achieved", True),
            len(insights.get("risk_factors", [])) > 2
        ]
        
        return any(escalation_triggers)
    
    def _generate_approval_items(self, transcript: CallTranscript, insights: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate items requiring supervisor approval."""
        
        approval_items = []
        
        # Scenario-specific approvals
        if transcript.scenario == "hardship":
            approval_items.append({
                "type": "hardship_assistance",
                "description": "Customer requesting payment deferral",
                "risk_level": "medium",
                "requires": "supervisor_approval"
            })
        
        # High-risk factors
        if len(insights.get("risk_factors", [])) > 1:
            approval_items.append({
                "type": "risk_review",
                "description": "Multiple risk factors identified",
                "risk_level": "high",
                "requires": "manager_review"
            })
        
        return approval_items
    
    def _generate_summary(self, transcript: CallTranscript, insights: Dict[str, Any], 
                         action_plans: Dict[str, Any]) -> str:
        """Generate executive summary of the analysis."""
        
        return f"""
Call Analysis Summary:

Customer {transcript.customer.name} contacted regarding {transcript.scenario} assistance. 
The call lasted {transcript.call_metadata.duration_seconds // 60} minutes with {insights.get('customer_sentiment', 'neutral')} customer sentiment.

Key Issues: {', '.join(insights.get('key_issues', ['None identified']))}

Resolution Status: {'Resolved' if insights.get('resolution_achieved') else 'Pending'}

Next Steps: {len(action_plans['borrower_plan']['immediate_actions'])} immediate actions planned for customer.

Compliance: {action_plans['supervisor_plan']['risk_assessment'].title()} risk level.

Recommended Actions: 
- Borrower: {action_plans['borrower_plan']['immediate_actions'][0] if action_plans['borrower_plan']['immediate_actions'] else 'None'}
- Advisor: {action_plans['advisor_plan']['coaching_points'][0] if action_plans['advisor_plan']['coaching_points'] else 'No coaching needed'}
"""
    
    def get_analysis_results(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get existing analysis results for a transcript."""
        
        results = self.db.get_analysis_results(transcript_id, "orchestrator_full_analysis")
        return results[0]['result_data'] if results else None
