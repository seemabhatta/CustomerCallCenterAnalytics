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
from dotenv import load_dotenv
from ..llm import OpenAIWrapper
from .models.risk_models import RiskAssessment, ApprovalRouting
from ..models.shared import ActionItemList
from .models.workflow_models import (
    WorkflowExtraction, RoutingDecision, ValidationResult, StatusDecision, ExecutionResult
)
from ..telemetry import trace_async_function, set_span_attributes, add_span_event
from src.utils.prompt_loader import prompt_loader

load_dotenv()


class RiskAssessmentAgent:
    """Pure LLM-based agent for granular action item risk assessment and routing decisions.
    
    Supports both legacy workflow assessment and new granular action item assessment.
    All decisions (risk level, approval routing, execution validation) are made
    by LLM agents without any hardcoded business rules or fallback logic.
    
    New Features:
    - Individual action item risk assessment for 4-pillar workflows (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
    - Workflow type-specific risk evaluation criteria
    - Granular approval routing based on action item complexity
    - Item-level execution and validation
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
        
        self.llm = OpenAIWrapper()
        
        # Initialize attributes required by deprecated methods (for backward compatibility)
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-4o')
        
        # Agent metadata for audit trail
        self.agent_id = str(uuid.uuid4())
        self.agent_version = "v2.0"
    
    @trace_async_function("risk_agent.extract_action_items")
    async def extract_individual_action_items(self, plan_data: Dict[str, Any], 
                                               workflow_type: str, 
                                               context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract individual action items from 4-pillar action plan using LLM.
        
        Args:
            plan_data: Complete action plan data with all 4 pillars
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            context: Full context chain for decision making
            
        Returns:
            List of individual action items for the specified workflow type
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM extraction failure (NO FALLBACK)
        """
        if not plan_data or not isinstance(plan_data, dict):
            raise ValueError("plan_data must be a non-empty dictionary")
        
        if workflow_type not in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
            raise ValueError("workflow_type must be one of: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP")
        
        if not context or not isinstance(context, dict):
            raise ValueError("context must be a non-empty dictionary")
        
        # Start tracing the extraction process
        set_span_attributes(workflow_type=workflow_type, operation="extract_action_items")
        add_span_event("extraction.started", workflow_type=workflow_type)
        
        # Build comprehensive prompt for extracting individual items by workflow type
        add_span_event("extraction.prompt_building", workflow_type=workflow_type)
        full_prompt = prompt_loader.format(
            'agents/risk/extract_action_items.txt',
            workflow_type_lower=workflow_type.lower(),
            workflow_type=workflow_type,
            transcript_id=context.get('transcript_id', 'Unknown'),
            analysis_id=context.get('analysis_id', 'Unknown'),
            plan_id=context.get('plan_id', 'Unknown'),
            plan_data=json.dumps(plan_data, indent=2),
            context=json.dumps(context, indent=2)
        )

        try:
            add_span_event("extraction.api_call_started", workflow_type=workflow_type, model=self.model)
            # Use OpenAI wrapper with structured output for action item extraction
            result = await self.llm.generate_structured_async(full_prompt, ActionItemList, temperature=0.1)
            action_items = result.action_items
            add_span_event("extraction.api_call_completed", workflow_type=workflow_type, items_extracted=len(action_items))
            
            # Add extraction metadata to each item
            for item in action_items:
                item['extraction_metadata'] = {
                    'agent_id': self.agent_id,
                    'agent_version': self.agent_version,
                    'model_used': self.model,
                    'extracted_at': datetime.utcnow().isoformat(),
                    'workflow_type': workflow_type
                }
            
            return action_items
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Action items extraction failed: {e}")
    
    async def extract_workflow_from_plan(self, plan_data: Dict[str, Any], 
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract actionable workflow from action plan using LLM.
        
        DEPRECATED: Use extract_individual_action_items for granular assessment.
        Maintained for backward compatibility.
        
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
        full_prompt = prompt_loader.format(
            'agents/risk/extract_workflow.txt',
            transcript_id=context.get('transcript_id', 'Unknown'),
            analysis_id=context.get('analysis_id', 'Unknown'),
            plan_id=context.get('plan_id', 'Unknown'),
            pipeline_stage=context.get('pipeline_stage', 'Unknown'),
            plan_data=json.dumps(plan_data, indent=2),
            context=json.dumps(context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured WorkflowExtraction output
            result = await self.llm.generate_structured_async(full_prompt, WorkflowExtraction, temperature=0.1)

            # Convert to dict and add agent metadata
            workflow_data = result.model_dump()
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
    
    @trace_async_function("risk_agent.assess_action_item_risk")
    async def assess_action_item_risk(self, action_item: Dict[str, Any], 
                                     workflow_type: str,
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess individual action item risk level using LLM agent.
        
        Args:
            action_item: Individual action item data
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            context: Full context chain
            
        Returns:
            Risk assessment with level and reasoning for the action item
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM assessment failure (NO FALLBACK)
        """
        if not action_item or not isinstance(action_item, dict):
            raise ValueError("action_item must be a non-empty dictionary")
        
        if workflow_type not in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
            raise ValueError("workflow_type must be one of: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP")
        
        if not context or not isinstance(context, dict):
            raise ValueError("context must be a non-empty dictionary")
        
        # Workflow type-specific risk considerations
        type_considerations = {
            'BORROWER': {
                'focus': 'customer impact, financial implications, regulatory compliance',
                'high_risk_indicators': 'payment modifications, legal actions, hardship situations, compliance violations',
                'low_risk_indicators': 'standard communications, routine documentation, information requests'
            },
            'ADVISOR': {
                'focus': 'performance impact, coaching effectiveness, skill development',
                'high_risk_indicators': 'compliance violations, customer escalations, performance deficiencies',
                'low_risk_indicators': 'routine coaching, positive feedback, skill reinforcement'
            },
            'SUPERVISOR': {
                'focus': 'operational oversight, team management, compliance monitoring',
                'high_risk_indicators': 'escalated issues, compliance deviations, team performance problems',
                'low_risk_indicators': 'routine approvals, standard reviews, team updates'
            },
            'LEADERSHIP': {
                'focus': 'strategic impact, portfolio risks, organizational decisions',
                'high_risk_indicators': 'strategic changes, portfolio risks, regulatory implications',
                'low_risk_indicators': 'trend monitoring, strategic insights, routine reporting'
            }
        }
        
        considerations = type_considerations[workflow_type]
        
        full_prompt = prompt_loader.format(
            'agents/risk/assess_action_item_risk.txt',
            workflow_type_lower=workflow_type.lower(),
            workflow_type=workflow_type,
            focus=considerations['focus'],
            low_risk_indicators=considerations['low_risk_indicators'],
            high_risk_indicators=considerations['high_risk_indicators'],
            action_item=json.dumps(action_item, indent=2),
            context=json.dumps(context, indent=2)
        )

        try:
            # Add tracing attributes for observability
            set_span_attributes(
                workflow_type=workflow_type,
                action_item_id=action_item.get('id', 'unknown'),
                action_description=action_item.get('action_item', 'unknown')[:100],  # Truncate for logs
                model=self.model
            )
            add_span_event("risk_assessment.llm_call_started", 
                          workflow_type=workflow_type, 
                          action_item_id=action_item.get('id', 'unknown'))
            
            # Use OpenAI wrapper with structured RiskAssessment output
            result = await self.llm.generate_structured_async(full_prompt, RiskAssessment, temperature=0.1)
            add_span_event("risk_assessment.llm_call_completed")

            # Convert to dict and add assessment metadata
            risk_assessment = result.model_dump()
            risk_assessment['assessment_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'assessed_at': datetime.utcnow().isoformat(),
                'workflow_type': workflow_type,
                'assessment_type': 'granular_action_item'
            }
            
            # Add final span attributes with results
            set_span_attributes(
                risk_level=risk_assessment['risk_level'],
                assessment_completed=True
            )
            add_span_event("risk_assessment.completed", 
                          risk_level=risk_assessment['risk_level'],
                          action_item_id=action_item.get('id', 'unknown'))
            
            return risk_assessment
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Action item risk assessment failed: {e}")
    
    @trace_async_function("risk_agent.assess_workflow_risk")
    async def assess_workflow_risk(self, workflow_data: Dict[str, Any], 
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess workflow risk level using LLM agent.
        
        DEPRECATED: Use assess_action_item_risk for granular assessment.
        Maintained for backward compatibility.
        
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
        
        full_prompt = prompt_loader.format(
            'agents/risk/assess_workflow_risk.txt',
            workflow_data=json.dumps(workflow_data, indent=2),
            context=json.dumps(context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured RiskAssessment output
            result = await self.llm.generate_structured_async(full_prompt, RiskAssessment, temperature=0.1)

            # Convert to dict and add assessment metadata
            risk_assessment = result.model_dump()
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
    
    async def determine_action_item_approval_routing(self, action_item: Dict[str, Any],
                                                     risk_assessment: Dict[str, Any],
                                                     workflow_type: str, 
                                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine approval routing for individual action item using LLM agent.
        
        Args:
            action_item: Individual action item data
            risk_assessment: Risk assessment results for the action item
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            context: Full context chain
            
        Returns:
            Approval routing decision for the action item
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM routing failure (NO FALLBACK)
        """
        if not action_item or not isinstance(action_item, dict):
            raise ValueError("action_item must be a non-empty dictionary")
        
        if not risk_assessment or not isinstance(risk_assessment, dict):
            raise ValueError("risk_assessment must be a non-empty dictionary")
        
        if workflow_type not in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
            raise ValueError("workflow_type must be one of: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP")
        
        if not context or not isinstance(context, dict):
            raise ValueError("context must be a non-empty dictionary")
        
        # Workflow type-specific routing patterns
        routing_patterns = {
            'BORROWER': {
                'auto_approve': 'Low-risk customer communications, routine documentation',
                'advisor_approve': 'Standard customer interactions, payment arrangements',
                'supervisor_approve': 'Payment modifications, hardship programs, escalated issues'
            },
            'ADVISOR': {
                'auto_approve': 'Positive coaching feedback, routine skill reinforcement',
                'advisor_approve': 'Performance coaching, training recommendations',
                'supervisor_approve': 'Performance issues, compliance violations, corrective actions'
            },
            'SUPERVISOR': {
                'auto_approve': 'Routine team updates, standard performance reviews',
                'advisor_approve': 'Team coaching decisions, workflow approvals',
                'supervisor_approve': 'Escalated issues, compliance reviews, operational changes'
            },
            'LEADERSHIP': {
                'auto_approve': 'Routine reporting, trend insights, standard analytics',
                'advisor_approve': 'Strategic recommendations, resource allocation suggestions',
                'supervisor_approve': 'Strategic decisions, portfolio risks, policy changes'
            }
        }
        
        patterns = routing_patterns[workflow_type]
        
        full_prompt = prompt_loader.format(
            'agents/risk/action_item_approval_routing.txt',
            workflow_type_lower=workflow_type.lower(),
            workflow_type=workflow_type,
            auto_approve=patterns['auto_approve'],
            advisor_approve=patterns['advisor_approve'],
            supervisor_approve=patterns['supervisor_approve'],
            action_item=json.dumps(action_item, indent=2),
            risk_assessment=json.dumps(risk_assessment, indent=2),
            context=json.dumps(context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured RoutingDecision output
            result = await self.llm.generate_structured_async(full_prompt, RoutingDecision, temperature=0.1)

            # Convert to dict and add routing metadata
            routing_decision = result.model_dump()
            routing_decision['routing_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'routed_at': datetime.utcnow().isoformat(),
                'workflow_type': workflow_type,
                'routing_type': 'granular_action_item'
            }
            
            return routing_decision
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Action item approval routing failed: {e}")
    
    async def determine_approval_routing(self, workflow_data: Dict[str, Any],
                                       risk_assessment: Dict[str, Any], 
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine approval routing using LLM agent.
        
        DEPRECATED: Use determine_action_item_approval_routing for granular assessment.
        Maintained for backward compatibility.
        
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
        
        full_prompt = prompt_loader.format(
            'agents/risk/workflow_approval_routing.txt',
            workflow_data=json.dumps(workflow_data, indent=2),
            risk_assessment=json.dumps(risk_assessment, indent=2),
            context=json.dumps(context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured RoutingDecision output
            result = await self.llm.generate_structured_async(full_prompt, RoutingDecision, temperature=0.1)

            # Convert to dict and add routing metadata
            routing_decision = result.model_dump()
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
    
    async def validate_action_item_approval_decision(self, action_item: Dict[str, Any],
                                                     workflow_type: str,
                                                     approver: str, reasoning: Optional[str],
                                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate human approval decision for individual action item using LLM agent.
        
        Args:
            action_item: Individual action item data
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            approver: Approver identifier
            reasoning: Approval reasoning
            context: Full context including approval metadata
            
        Returns:
            Validation results for the action item approval
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM validation failure (NO FALLBACK)
        """
        if not action_item or not isinstance(action_item, dict):
            raise ValueError("action_item must be a non-empty dictionary")
        
        if workflow_type not in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
            raise ValueError("workflow_type must be one of: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP")
        
        if not approver or not isinstance(approver, str):
            raise ValueError("approver must be a non-empty string")
        
        full_prompt = prompt_loader.format(
            'agents/risk/validate_action_approval.txt',
            workflow_type_lower=workflow_type.lower(),
            workflow_type=workflow_type,
            action_item=json.dumps(action_item, indent=2),
            approver=approver,
            reasoning=reasoning or 'No specific reasoning provided',
            context=json.dumps(context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured ValidationResult output
            result = await self.llm.generate_structured_async(full_prompt, ValidationResult, temperature=0.1)
            validation_result = result.model_dump()

            # Add validation metadata
            validation_result['validation_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'validated_at': datetime.utcnow().isoformat(),
                'workflow_type': workflow_type,
                'validation_type': 'granular_action_item_approval'
            }
            
            return validation_result
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Action item approval validation failed: {e}")
    
    async def validate_approval_decision(self, workflow_data: Dict[str, Any],
                                       approver: str, reasoning: Optional[str],
                                       context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate human approval decision using LLM agent.
        
        DEPRECATED: Use validate_action_item_approval_decision for granular assessment.
        Maintained for backward compatibility.
        
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
        
        full_prompt = prompt_loader.format(
            'agents/risk/validate_workflow_approval.txt',
            workflow_data=json.dumps(workflow_data, indent=2),
            approver=approver,
            reasoning=reasoning or 'No specific reasoning provided',
            context=json.dumps(context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured ValidationResult output
            result = await self.llm.generate_structured_async(full_prompt, ValidationResult, temperature=0.1)
            validation_result = result.model_dump()
            
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
    
    async def validate_action_item_rejection_decision(self, action_item: Dict[str, Any],
                                                      workflow_type: str,
                                                      rejector: str, reason: str,
                                                      context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate human rejection decision for individual action item using LLM agent.
        
        Args:
            action_item: Individual action item data
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            rejector: Rejector identifier
            reason: Rejection reason
            context: Full context including rejection metadata
            
        Returns:
            Validation results for the action item rejection
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM validation failure (NO FALLBACK)
        """
        if not action_item or not isinstance(action_item, dict):
            raise ValueError("action_item must be a non-empty dictionary")
        
        if workflow_type not in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
            raise ValueError("workflow_type must be one of: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP")
        
        if not rejector or not isinstance(rejector, str):
            raise ValueError("rejector must be a non-empty string")
        
        if not reason or not isinstance(reason, str):
            raise ValueError("reason must be a non-empty string")
        
        full_prompt = prompt_loader.format(
            'agents/risk/validate_action_rejection.txt',
            workflow_type_lower=workflow_type.lower(),
            workflow_type=workflow_type,
            action_item=json.dumps(action_item, indent=2),
            rejector=rejector,
            reason=reason,
            context=json.dumps(context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured ValidationResult output
            result = await self.llm.generate_structured_async(full_prompt, ValidationResult, temperature=0.1)
            validation_result = result.model_dump()
            
            # Add validation metadata
            validation_result['validation_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'validated_at': datetime.utcnow().isoformat(),
                'workflow_type': workflow_type,
                'validation_type': 'granular_action_item_rejection'
            }
            
            return validation_result
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Action item rejection validation failed: {e}")
    
    async def validate_rejection_decision(self, workflow_data: Dict[str, Any],
                                        rejector: str, reason: str,
                                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate human rejection decision using LLM agent.
        
        DEPRECATED: Use validate_action_item_rejection_decision for granular assessment.
        Maintained for backward compatibility.
        
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
        
        full_prompt = prompt_loader.format(
            'agents/risk/validate_workflow_rejection.txt',
            workflow_data=json.dumps(workflow_data, indent=2),
            rejector=rejector,
            reason=reason,
            context=json.dumps(context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured ValidationResult output
            result = await self.llm.generate_structured_async(full_prompt, ValidationResult, temperature=0.1)
            validation_result = result.model_dump()

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
    
    async def determine_action_item_post_approval_status(self, action_item: Dict[str, Any],
                                                        workflow_type: str,
                                                        approval_context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine action item status after approval using LLM agent.
        
        Args:
            action_item: Individual action item data
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            approval_context: Context with approval details
            
        Returns:
            Next status decision for the action item
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM decision failure (NO FALLBACK)
        """
        if not action_item or not isinstance(action_item, dict):
            raise ValueError("action_item must be a non-empty dictionary")
        
        if workflow_type not in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
            raise ValueError("workflow_type must be one of: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP")
        
        full_prompt = prompt_loader.format(
            'agents/risk/action_post_approval_status.txt',
            workflow_type_lower=workflow_type.lower(),
            workflow_type=workflow_type,
            action_item=json.dumps(action_item, indent=2),
            approval_context=json.dumps(approval_context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured StatusDecision output
            result = await self.llm.generate_structured_async(full_prompt, StatusDecision, temperature=0.1)
            status_decision = result.model_dump()
            
            # Add decision metadata
            status_decision['decision_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'decided_at': datetime.utcnow().isoformat(),
                'workflow_type': workflow_type,
                'decision_type': 'granular_action_item_post_approval'
            }
            
            return status_decision
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Action item post-approval status decision failed: {e}")
    
    async def determine_post_approval_status(self, workflow_data: Dict[str, Any],
                                           approval_context: Dict[str, Any]) -> Dict[str, Any]:
        """Determine workflow status after approval using LLM agent.
        
        DEPRECATED: Use determine_action_item_post_approval_status for granular assessment.
        Maintained for backward compatibility.
        
        Args:
            workflow_data: Complete workflow data
            approval_context: Context with approval details
            
        Returns:
            Next status decision
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM decision failure (NO FALLBACK)
        """
        full_prompt = prompt_loader.format(
            'agents/risk/workflow_post_approval_status.txt',
            workflow_data=json.dumps(workflow_data, indent=2),
            approval_context=json.dumps(approval_context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured StatusDecision output
            result = await self.llm.generate_structured_async(full_prompt, StatusDecision, temperature=0.1)
            status_decision = result.model_dump()

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
    
    async def execute_action_item(self, action_item: Dict[str, Any],
                                 workflow_type: str,
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute individual action item using LLM agent.
        
        Args:
            action_item: Individual action item data
            workflow_type: Type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)
            context: Execution context
            
        Returns:
            Execution results for the action item
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM execution failure (NO FALLBACK)
        """
        if not action_item or not isinstance(action_item, dict):
            raise ValueError("action_item must be a non-empty dictionary")
        
        if workflow_type not in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
            raise ValueError("workflow_type must be one of: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP")
        
        if not context or not isinstance(context, dict):
            raise ValueError("context must be a non-empty dictionary")
        
        # Workflow type-specific execution patterns
        execution_patterns = {
            'BORROWER': {
                'systems': 'Customer management systems, payment processing, communication platforms',
                'considerations': 'Customer impact, compliance requirements, timing sensitivity'
            },
            'ADVISOR': {
                'systems': 'Performance management systems, coaching platforms, training modules',
                'considerations': 'Performance tracking, skill development, coaching effectiveness'
            },
            'SUPERVISOR': {
                'systems': 'Team management systems, approval workflows, operational dashboards',
                'considerations': 'Team impact, operational efficiency, compliance oversight'
            },
            'LEADERSHIP': {
                'systems': 'Strategic analytics, portfolio management, executive dashboards',
                'considerations': 'Strategic alignment, portfolio impact, organizational implications'
            }
        }
        
        patterns = execution_patterns[workflow_type]
        
        full_prompt = prompt_loader.format(
            'agents/risk/execute_action_item.txt',
            workflow_type_lower=workflow_type.lower(),
            workflow_type=workflow_type,
            action_item=json.dumps(action_item, indent=2),
            context=json.dumps(context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured ExecutionResult output
            result = await self.llm.generate_structured_async(full_prompt, ExecutionResult, temperature=0.2)
            execution_results = result.model_dump()
            
            # Add execution metadata
            execution_results['execution_metadata'] = {
                'agent_id': self.agent_id,
                'agent_version': self.agent_version,
                'model_used': self.model,
                'executed_at': datetime.utcnow().isoformat(),
                'workflow_type': workflow_type,
                'execution_type': 'simulated_granular_action_item'
            }
            
            return execution_results
            
        except json.JSONDecodeError as e:
            raise Exception(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise Exception(f"Action item execution failed: {e}")
    
    async def execute_workflow_steps(self, workflow_data: Dict[str, Any],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow steps using LLM agent.
        
        DEPRECATED: Use execute_action_item for granular execution.
        Maintained for backward compatibility.
        
        Args:
            workflow_data: Complete workflow data
            context: Execution context
            
        Returns:
            Execution results
            
        Raises:
            ValueError: Invalid inputs (NO FALLBACK)
            Exception: LLM execution failure (NO FALLBACK)
        """
        full_prompt = prompt_loader.format(
            'agents/risk/execute_workflow.txt',
            workflow_data=json.dumps(workflow_data, indent=2),
            context=json.dumps(context, indent=2)
        )

        try:
            # Use OpenAI wrapper with structured ExecutionResult output
            result = await self.llm.generate_structured_async(full_prompt, ExecutionResult, temperature=0.2)
            execution_results = result.model_dump()
            
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