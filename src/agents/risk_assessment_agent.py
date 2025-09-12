"""Risk Assessment Agent - Pure LLM-based decision making.

Core Principles Applied:
- NO FALLBACK: Fail fast on invalid inputs or LLM failures
- COMPLETELY AGENTIC: All decisions made by LLM, no hardcoded logic
- Context Preservation: Full context chain maintained for decision traceability
"""
import os
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import openai
from dotenv import load_dotenv

load_dotenv()


class RiskAssessmentAgent:
    """Pure LLM-based agent for workflow risk assessment and routing decisions.
    
    All decisions (risk level, approval routing, execution validation) are made
    by LLM agents without any hardcoded business rules or fallback logic.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize the risk assessment agent.
        
        Args:
            api_key: OpenAI API key (uses env var if not provided)
            model: OpenAI model to use (uses env var if not provided)
            
        Raises:
            ValueError: If API key is missing (NO FALLBACK)
        """
        api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required - no fallback available")
        
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
        # Agent metadata for audit trail
        self.agent_id = str(uuid.uuid4())
        self.agent_version = "v1.0"
    
    async def extract_workflow_from_plan(self, plan_data: Dict[str, Any], 
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actionable workflow from action plan using LLM.
        
        Args:
            plan_data: Complete action plan data
            context: Full context chain for decision making
            
        Returns:
            Extracted workflow data
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM extraction failure (NO FALLBACK)
        """
        if not plan_data or not isinstance(plan_data, dict):
            raise ValueError("plan_data must be a non-empty dictionary")
        
        if not context or not isinstance(context, dict):
            raise ValueError("context must be a non-empty dictionary")
        
        # Build comprehensive prompt with full context
        system_prompt = """You are a Workflow Extraction Agent for mortgage servicing operations.

Your role is to analyze action plans and extract executable workflows with detailed step-by-step processes.

CRITICAL INSTRUCTIONS:
- Extract ONLY actionable workflow steps from the action plan
- Assess workflow complexity and dependencies
- Identify potential execution challenges
- NO GUESSING or assumptions - base decisions only on provided data
- FAIL if required information is missing

Return a structured workflow as valid JSON format with:
1. workflow_steps: Detailed step-by-step executable actions
2. complexity_assessment: Analysis of workflow complexity
3. dependencies: Required resources, systems, or approvals
4. execution_risks: Potential issues during execution
5. estimated_duration: Time estimate for completion"""

        user_prompt = f"""CONTEXT CHAIN:
Transcript ID: {context.get('transcript_id', 'Unknown')}
Analysis ID: {context.get('analysis_id', 'Unknown')}
Plan ID: {context.get('plan_id', 'Unknown')}
Pipeline Stage: {context.get('pipeline_stage', 'Unknown')}

ACTION PLAN TO ANALYZE:
{json.dumps(plan_data, indent=2)}

FULL CONTEXT:
{json.dumps(context, indent=2)}

Extract an executable workflow from this action plan. Focus on concrete, actionable steps that can be executed by operations teams. Return your response as valid JSON."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Low temperature for consistent extraction
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("LLM failed to generate workflow extraction response")
            
            workflow_data = json.loads(response.choices[0].message.content)
            
            # Add agent metadata
            workflow_data['extraction_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'extracted_at': datetime.utcnow().isoformat()
            }
            
            return workflow_data
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Workflow extraction failed: {e}")
    
    async def assess_workflow_risk(self, workflow_data: Dict[str, Any], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess workflow risk level using LLM agent.
        
        Args:
            workflow_data: Extracted workflow data
            context: Full context chain
            
        Returns:
            Risk assessment with level and reasoning
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM assessment failure (NO FALLBACK)
        """
        if not workflow_data or not isinstance(workflow_data, dict):
            raise ValueError("workflow_data must be a non-empty dictionary")
        
        if not context or not isinstance(context, dict):
            raise ValueError("context must be a non-empty dictionary")
        
        system_prompt = """You are a Risk Assessment Agent for mortgage servicing operations.

Your role is to evaluate workflow risk levels based on complexity, impact, and regulatory considerations.

CRITICAL INSTRUCTIONS:
- Assess risk level as LOW, MEDIUM, or HIGH only
- Provide detailed reasoning for risk assessment
- Consider operational complexity, customer impact, regulatory compliance
- NO FALLBACK assessments - base decisions only on provided data
- FAIL if insufficient information for accurate assessment

Risk Level Guidelines:
- LOW: Simple operations, minimal customer impact, standard procedures
- MEDIUM: Moderate complexity, potential customer impact, requires careful execution  
- HIGH: Complex operations, significant customer impact, regulatory implications"""

        user_prompt = f"""WORKFLOW TO ASSESS:
{json.dumps(workflow_data, indent=2)}

FULL CONTEXT:
{json.dumps(context, indent=2)}

Assess the risk level of this workflow. Consider:
1. Operational complexity and dependencies
2. Potential customer impact (financial, service)
3. Regulatory and compliance implications
4. Execution difficulty and error potential
5. Resource requirements and availability

Return your assessment with detailed reasoning as valid JSON format."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Consistent risk assessment
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("LLM failed to generate risk assessment response")
            
            risk_assessment = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            if 'risk_level' not in risk_assessment or 'reasoning' not in risk_assessment:
                raise Exception("LLM failed to provide required risk assessment fields")
            
            # Validate risk level
            if risk_assessment['risk_level'] not in ['LOW', 'MEDIUM', 'HIGH']:
                raise Exception(f"Invalid risk level from LLM: {risk_assessment['risk_level']}")
            
            # Add assessment metadata
            risk_assessment['assessment_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'assessed_at': datetime.utcnow().isoformat()
            }
            
            return risk_assessment
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Risk assessment failed: {e}")
    
    async def determine_approval_routing(self, workflow_data: Dict[str, Any],
                                       risk_assessment: Dict[str, Any], 
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine approval routing using LLM agent.
        
        Args:
            workflow_data: Extracted workflow
            risk_assessment: Risk assessment results
            context: Full context chain
            
        Returns:
            Approval routing decision
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM routing failure (NO FALLBACK)
        """
        if not workflow_data or not isinstance(workflow_data, dict):
            raise ValueError("workflow_data must be a non-empty dictionary")
        
        if not risk_assessment or not isinstance(risk_assessment, dict):
            raise ValueError("risk_assessment must be a non-empty dictionary")
        
        if not context or not isinstance(context, dict):
            raise ValueError("context must be a non-empty dictionary")
        
        system_prompt = """You are an Approval Routing Agent for mortgage servicing operations.

Your role is to determine approval requirements and routing based on workflow risk and operational context.

CRITICAL INSTRUCTIONS:
- Determine if workflow requires human approval (true/false)
- Set initial workflow status based on routing decision
- Assign appropriate approver if human approval required
- Provide detailed reasoning for routing decision
- NO HARDCODED RULES - make decisions based on provided data only

Routing Options:
- LOW risk: Usually auto-approved (status: AUTO_APPROVED, requires_human_approval: false)
- MEDIUM risk: Usually requires advisor approval (status: AWAITING_APPROVAL, requires_human_approval: true)
- HIGH risk: Usually requires supervisor approval (status: AWAITING_APPROVAL, requires_human_approval: true)

Consider context factors that may override standard routing.

Return your response as valid JSON format with these exact fields:
{
  "requires_human_approval": boolean,
  "initial_status": "PENDING_ASSESSMENT" | "AWAITING_APPROVAL" | "AUTO_APPROVED",
  "routing_reasoning": "detailed explanation"
}"""

        user_prompt = f"""WORKFLOW DATA:
{json.dumps(workflow_data, indent=2)}

RISK ASSESSMENT:
{json.dumps(risk_assessment, indent=2)}

FULL CONTEXT:
{json.dumps(context, indent=2)}

Determine the approval routing for this workflow. Consider:
1. Risk level and assessment reasoning
2. Workflow complexity and impact
3. Context factors (customer situation, compliance needs)
4. Operational capacity and urgency

Return routing decision with clear reasoning as valid JSON format using the exact field structure specified above."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1  # Consistent routing decisions
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("LLM failed to generate routing response")
            
            routing_decision = json.loads(response.choices[0].message.content)
            
            # Validate required fields
            required_fields = ['requires_human_approval', 'initial_status', 'routing_reasoning']
            for field in required_fields:
                if field not in routing_decision:
                    raise Exception(f"LLM failed to provide required routing field: {field}")
            
            # Validate status values
            valid_statuses = ['PENDING_ASSESSMENT', 'AWAITING_APPROVAL', 'AUTO_APPROVED']
            if routing_decision['initial_status'] not in valid_statuses:
                raise Exception(f"Invalid initial status from LLM: {routing_decision['initial_status']}")
            
            # Add routing metadata
            routing_decision['routing_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'routed_at': datetime.utcnow().isoformat()
            }
            
            return routing_decision
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Approval routing failed: {e}")
    
    async def validate_approval_decision(self, workflow_data: Dict[str, Any],
                                       approver: str, reasoning: Optional[str],
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate human approval decision using LLM agent.
        
        Args:
            workflow_data: Complete workflow data
            approver: Approver identifier
            reasoning: Approval reasoning
            context: Full context including approval metadata
            
        Returns:
            Validation results
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM validation failure (NO FALLBACK)
        """
        if not workflow_data or not isinstance(workflow_data, dict):
            raise ValueError("workflow_data must be a non-empty dictionary")
        
        if not approver or not isinstance(approver, str):
            raise ValueError("approver must be a non-empty string")
        
        system_prompt = """You are an Approval Validation Agent for mortgage servicing operations.

Your role is to validate human approval decisions for workflow execution.

CRITICAL INSTRUCTIONS:
- Validate if the approval decision is reasonable given the workflow and context
- Consider approver authority and reasoning quality
- Flag any potential issues or concerns
- Provide validation result (approval_valid: true/false)
- Include detailed reasoning for validation decision
- NO BLANKET APPROVALS - evaluate each decision carefully
- Return your response as valid JSON format with exact fields:
  {
    "approval_valid": boolean,
    "validation_reasoning": "detailed explanation",
    "rejection_reason": "reason if approval_valid is false"
  }"""

        user_prompt = f"""WORKFLOW TO VALIDATE:
{json.dumps(workflow_data, indent=2)}

APPROVAL DETAILS:
Approver: {approver}
Reasoning: {reasoning or 'No specific reasoning provided'}

FULL CONTEXT:
{json.dumps(context, indent=2)}

Validate this approval decision. Consider:
1. Workflow risk level and complexity
2. Approver authority level
3. Quality and completeness of reasoning
4. Alignment with operational best practices
5. Any red flags or concerns

Return validation decision with detailed analysis as valid JSON format."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("LLM failed to generate validation response")
            
            validation_result = json.loads(response.choices[0].message.content)
            
            # Add validation metadata
            validation_result['validation_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'validated_at': datetime.utcnow().isoformat()
            }
            
            return validation_result
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Approval validation failed: {e}")
    
    async def validate_rejection_decision(self, workflow_data: Dict[str, Any],
                                        rejector: str, reason: str,
                                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate human rejection decision using LLM agent.
        
        Args:
            workflow_data: Complete workflow data
            rejector: Rejector identifier
            reason: Rejection reason
            context: Full context including rejection metadata
            
        Returns:
            Validation results
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM validation failure (NO FALLBACK)
        """
        if not workflow_data or not isinstance(workflow_data, dict):
            raise ValueError("workflow_data must be a non-empty dictionary")
        
        if not rejector or not isinstance(rejector, str):
            raise ValueError("rejector must be a non-empty string")
        
        if not reason or not isinstance(reason, str):
            raise ValueError("reason must be a non-empty string")
        
        system_prompt = """You are a Rejection Validation Agent for mortgage servicing operations.

Your role is to validate human rejection decisions for workflows.

CRITICAL INSTRUCTIONS:
- Assess if the rejection decision is justified given the workflow and reasoning
- Consider rejection reason quality and validity
- Flag if rejection seems inappropriate or lacks justification
- Provide validation result (rejection_valid: true/false)
- Include concerns or recommendations if rejection seems questionable
- Support legitimate quality control through rejection validation
- Return your response as valid JSON format"""

        user_prompt = f"""WORKFLOW TO VALIDATE:
{json.dumps(workflow_data, indent=2)}

REJECTION DETAILS:
Rejector: {rejector}
Reason: {reason}

FULL CONTEXT:
{json.dumps(context, indent=2)}

Validate this rejection decision. Consider:
1. Appropriateness of rejection given workflow content
2. Quality and specificity of rejection reason
3. Rejector's authority to make this decision
4. Whether rejection serves legitimate quality/risk control
5. Alternative solutions or modifications that might address concerns

Return validation decision with analysis as valid JSON format."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("LLM failed to generate rejection validation response")
            
            validation_result = json.loads(response.choices[0].message.content)
            
            # Add validation metadata
            validation_result['validation_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'validated_at': datetime.utcnow().isoformat()
            }
            
            return validation_result
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Rejection validation failed: {e}")
    
    async def determine_post_approval_status(self, workflow_data: Dict[str, Any],
                                           approval_context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine workflow status after approval using LLM agent.
        
        Args:
            workflow_data: Complete workflow data
            approval_context: Context with approval details
            
        Returns:
            Next status decision
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM decision failure (NO FALLBACK)
        """
        system_prompt = """You are a Post-Approval Status Agent for mortgage servicing operations.

Your role is to determine the appropriate next status for workflows after human approval.

CRITICAL INSTRUCTIONS:
- Determine next status: AUTO_APPROVED or EXECUTED
- Consider if workflow can be immediately executed or needs additional preparation
- Provide reasoning for status decision
- NO HARDCODED LOGIC - base decisions on workflow specifics and context
- Return your decision as valid JSON format"""

        user_prompt = f"""APPROVED WORKFLOW:
{json.dumps(workflow_data, indent=2)}

APPROVAL CONTEXT:
{json.dumps(approval_context, indent=2)}

Determine the next status for this approved workflow. Consider:
1. Workflow readiness for immediate execution
2. Any dependencies or prerequisites remaining
3. Resource availability and timing considerations
4. Standard operational procedures

Return next status decision (AUTO_APPROVED or EXECUTED) with reasoning as valid JSON format."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("LLM failed to generate status decision response")
            
            status_decision = json.loads(response.choices[0].message.content)
            
            # Add decision metadata
            status_decision['decision_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'decided_at': datetime.utcnow().isoformat()
            }
            
            return status_decision
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Post-approval status decision failed: {e}")
    
    async def execute_workflow_steps(self, workflow_data: Dict[str, Any],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow steps using LLM agent.
        
        Args:
            workflow_data: Complete workflow data
            context: Execution context
            
        Returns:
            Execution results
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM execution failure (NO FALLBACK)
        """
        system_prompt = """You are a Workflow Execution Agent for mortgage servicing operations.

Your role is to simulate execution of approved workflow steps and report results.

CRITICAL INSTRUCTIONS:
- Process each workflow step systematically
- Report execution status for each step
- Identify any issues or blockers encountered
- Provide overall execution status (completed, partial, failed)
- Include execution summary and any recommendations
- SIMULATE EXECUTION - do not perform actual system operations
- Return your response as valid JSON format"""

        user_prompt = f"""WORKFLOW TO EXECUTE:
{json.dumps(workflow_data, indent=2)}

EXECUTION CONTEXT:
{json.dumps(context, indent=2)}

Simulate execution of this workflow. For each step:
1. Assess executability and prerequisites
2. Identify potential issues or dependencies
3. Report simulated execution outcome
4. Note any follow-up actions required

Return comprehensive execution results as valid JSON format."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.2  # Slightly higher for varied execution scenarios
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise Exception("LLM failed to generate execution response")
            
            execution_results = json.loads(response.choices[0].message.content)
            
            # Add execution metadata
            execution_results['execution_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'executed_at': datetime.utcnow().isoformat(),
                'execution_type': 'simulated'
            }
            
            return execution_results
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Workflow execution failed: {e}")