"""
Multi-Agent Orchestrator
Coordinates the execution of specialized agents and integrates their outputs.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from agents import Runner
from ..llm.integrations import IntegrationOrchestrator, ContinuousLearningSystem
from ..config import settings


class CoilotOrchestrator:
    """
    The main orchestrator that implements the Co-Pilot vision.
    Coordinates Plan, Execute, and Reflect modes with multi-agent intelligence.
    """
    
    def __init__(self):
        self.integration_layer = IntegrationOrchestrator()
        self.learning_system = ContinuousLearningSystem()
        self.execution_history = []
        
    def plan_mode(self, user_request: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Plan Mode: AI Co-Pilot creates actionable plans in real-time.
        
        Args:
            user_request: Natural language request from advisor/user
            context: Additional context (call in progress, customer data, etc.)
            
        Returns:
            Structured plan with steps, risks, approvals needed
        """
        plan_prompt = f"""
        PLAN MODE REQUEST: {user_request}
        
        Context: {context or 'None provided'}
        
        As the Co-Pilot, create a comprehensive plan that includes:
        1. Immediate actionable steps
        2. Risk assessment and mitigation
        3. Required approvals and escalations
        4. Predicted outcomes and alternatives
        5. Timeline and dependencies
        
        Focus on mortgage servicing operations and ensure compliance considerations.
        Make this plan specific, actionable, and ready for execution.
        """
        
        try:
            import importlib.util
            import os
            
            # Load main agents module directly to avoid circular imports
            spec = importlib.util.spec_from_file_location(
                "main_agents", 
                os.path.join(os.path.dirname(__file__), "..", "agents.py")
            )
            main_agents = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_agents)
            
            triage_agent = main_agents.get_triage_agent()
            result = Runner.run_sync(triage_agent, plan_prompt)
            
            plan_output = {
                'mode': 'PLAN',
                'timestamp': datetime.now().isoformat(),
                'user_request': user_request,
                'plan': result.final_output,
                'status': 'ready_for_execution',
                'confidence': 0.85  # Could be extracted from analysis
            }
            
            self.execution_history.append(plan_output)
            return plan_output
            
        except Exception as e:
            return {
                'mode': 'PLAN',
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def execute_mode(self, plan: Dict[str, Any], auto_execute: bool = False) -> Dict[str, Any]:
        """
        Execute Mode: AI Co-Pilot executes approved plans with downstream integrations.
        
        Args:
            plan: Plan from plan_mode or manual plan structure
            auto_execute: Whether to auto-execute low-risk items
            
        Returns:
            Execution results with integration outcomes
        """
        
        execution_prompt = f"""
        EXECUTE MODE: Implementing the following plan
        
        Plan: {plan.get('plan', 'No plan provided')}
        Auto-execute enabled: {auto_execute}
        
        Analyze this plan and:
        1. Identify which steps can be automated
        2. Generate specific automation triggers for downstream systems
        3. Flag items requiring human approval
        4. Create integration payloads for CRM, workflows, etc.
        5. Provide execution monitoring checkpoints
        
        Output in the standard structured format for system integration.
        """
        
        try:
            import importlib.util
            import os
            
            # Load main agents module directly to avoid circular imports
            spec = importlib.util.spec_from_file_location(
                "main_agents", 
                os.path.join(os.path.dirname(__file__), "..", "agents.py")
            )
            main_agents = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_agents)
            
            triage_agent = main_agents.get_triage_agent()
            result = Runner.run_sync(triage_agent, execution_prompt)
            
            # Parse the analysis output and execute integrations
            parsed_analysis = self.integration_layer.parse_analysis_output(result.final_output)
            integration_results = self.integration_layer.execute_integrations(parsed_analysis)
            
            execution_output = {
                'mode': 'EXECUTE',
                'timestamp': datetime.now().isoformat(),
                'original_plan': plan,
                'analysis_output': result.final_output,
                'integration_results': integration_results,
                'auto_executed': auto_execute,
                'status': 'completed' if not integration_results.get('errors') else 'partial_completion'
            }
            
            self.execution_history.append(execution_output)
            return execution_output
            
        except Exception as e:
            return {
                'mode': 'EXECUTE', 
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def reflect_mode(self, execution_result: Dict[str, Any], 
                    human_feedback: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Reflect Mode: AI Co-Pilot analyzes outcomes and refines future performance.
        
        Args:
            execution_result: Result from execute_mode
            human_feedback: Optional human feedback on the execution
            
        Returns:
            Reflection analysis with lessons learned and improvements
        """
        
        reflect_prompt = f"""
        REFLECT MODE: Analyzing execution outcome and performance
        
        Execution Result: {execution_result}
        Human Feedback: {human_feedback or 'None provided'}
        
        As the Co-Pilot, provide a comprehensive reflection that includes:
        1. Execution outcome assessment (success/failure factors)
        2. Integration performance analysis
        3. Missed opportunities or oversights
        4. Compliance and risk review
        5. Lessons learned for future similar scenarios
        6. Specific improvements for next iteration
        7. Updated confidence scores based on outcomes
        
        Focus on continuous learning and system improvement.
        """
        
        try:
            import importlib.util
            import os
            
            # Load main agents module directly to avoid circular imports
            spec = importlib.util.spec_from_file_location(
                "main_agents", 
                os.path.join(os.path.dirname(__file__), "..", "agents.py")
            )
            main_agents = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_agents)
            
            triage_agent = main_agents.get_triage_agent()
            result = Runner.run_sync(triage_agent, reflect_prompt)
            
            # Record feedback in learning system
            if human_feedback:
                self.learning_system.record_analysis_feedback(
                    execution_result.get('timestamp', 'unknown'),
                    execution_result.get('analysis_output', ''),
                    human_feedback
                )
                
            # Record integration outcomes
            integration_success = not bool(execution_result.get('integration_results', {}).get('errors', []))
            self.learning_system.record_integration_outcome(
                execution_result.get('integration_results', {}),
                integration_success,
                result.final_output
            )
            
            reflection_output = {
                'mode': 'REFLECT',
                'timestamp': datetime.now().isoformat(),
                'execution_analyzed': execution_result.get('timestamp'),
                'reflection': result.final_output,
                'learning_updates': self.learning_system.analyze_agent_performance(),
                'status': 'completed'
            }
            
            self.execution_history.append(reflection_output)
            return reflection_output
            
        except Exception as e:
            return {
                'mode': 'REFLECT',
                'status': 'error', 
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def comprehensive_analysis(self, transcript: str, transcript_id: str = None) -> Dict[str, Any]:
        """
        Perform comprehensive multi-agent analysis of a transcript.
        This replaces the old single-agent analysis approach.
        """
        
        analysis_prompt = f"""
        Analyze this mortgage servicing call transcript comprehensively:
        
        Transcript ID: {transcript_id or 'N/A'}
        
        {transcript}
        
        Provide complete Co-Pilot analysis with all specialist insights integrated.
        """
        
        try:
            import importlib.util
            import os
            
            # Load main agents module directly to avoid circular imports
            spec = importlib.util.spec_from_file_location(
                "main_agents", 
                os.path.join(os.path.dirname(__file__), "..", "agents.py")
            )
            main_agents = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(main_agents)
            
            triage_agent = main_agents.get_triage_agent()
            result = Runner.run_sync(triage_agent, analysis_prompt)
            
            # Parse and prepare for integration
            parsed_analysis = self.integration_layer.parse_analysis_output(result.final_output)
            
            comprehensive_output = {
                'transcript_id': transcript_id,
                'timestamp': datetime.now().isoformat(),
                'raw_analysis': result.final_output,
                'parsed_analysis': parsed_analysis,
                'ready_for_integration': True,
                'status': 'completed'
            }
            
            return comprehensive_output
            
        except Exception as e:
            return {
                'transcript_id': transcript_id,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_execution_history(self, mode_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get execution history, optionally filtered by mode."""
        if mode_filter:
            return [h for h in self.execution_history if h.get('mode') == mode_filter.upper()]
        return self.execution_history.copy()
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics from the learning system."""
        return self.learning_system.analyze_agent_performance()


# Global orchestrator instance
_orchestrator = None

def get_orchestrator() -> CoilotOrchestrator:
    """Get the global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = CoilotOrchestrator()
    return _orchestrator