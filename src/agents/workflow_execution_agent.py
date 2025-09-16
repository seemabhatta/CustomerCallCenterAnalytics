"""
Workflow Execution Agent - LLM-powered execution decision maker.
Analyzes workflow action items and makes intelligent execution decisions.
NO FALLBACK LOGIC - fails fast if cannot make decisions.
"""
import json
from typing import Dict, Any
from datetime import datetime

from src.infrastructure.llm.openai_wrapper import OpenAIWrapper
from src.models.shared import ActionItem
from src.utils.prompt_loader import prompt_loader


class ExecutionDecision:
    """Structured output for execution decisions."""
    def __init__(self, executor_type: str, parameters: Dict[str, Any], 
                 confidence: float, reasoning: str):
        self.executor_type = executor_type
        self.parameters = parameters
        self.confidence = confidence
        self.reasoning = reasoning
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'executor_type': self.executor_type,
            'parameters': self.parameters,
            'confidence': self.confidence,
            'reasoning': self.reasoning
        }


class ExecutionPayload:
    """Structured output for execution payloads."""
    def __init__(self, payload: Dict[str, Any], metadata: Dict[str, Any]):
        self.payload = payload
        self.metadata = metadata
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'payload': self.payload,
            'metadata': self.metadata
        }


class WorkflowExecutionAgent:
    """LLM agent that makes execution decisions for workflow action items.
    
    This agent analyzes workflow action items and determines:
    1. What type of executor should handle the action
    2. What parameters the executor needs
    3. How confident it is in the decision
    
    NO FALLBACK LOGIC - if the agent cannot make a decision, it fails fast.
    """
    
    def __init__(self):
        """Initialize execution agent with LLM wrapper."""
        self.llm = OpenAIWrapper()
        self.agent_id = "workflow_execution_agent"
        self.agent_version = "v1.0"
    
    async def analyze_workflow_action(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze workflow action item and determine execution approach.
        
        Args:
            workflow: Complete workflow data including action_item
            
        Returns:
            ExecutionDecision with executor type and parameters
            
        Raises:
            ValueError: If cannot determine executor type (NO FALLBACK)
        """
        # Extract action item data
        workflow_data = workflow.get('workflow_data', {})
        action_item = workflow_data.get('action_item')
        description = workflow_data.get('description', '')
        workflow_type = workflow.get('workflow_type', 'UNKNOWN')
        
        if not action_item:
            raise ValueError("No action_item found in workflow data")
        
        # Create analysis prompt
        prompt = self._create_analysis_prompt(action_item, description, workflow_type, workflow)
        
        try:
            # Get LLM decision
            response = await self.llm.generate_text_async(prompt, temperature=0.2)
            
            # Debug: Check response
            if not response or not response.strip():
                raise ValueError(f"LLM returned empty response. Prompt length: {len(prompt)} chars")
            
            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]  # Remove ending ```
            cleaned_response = cleaned_response.strip()
            
            # Parse response as JSON
            decision_data = json.loads(cleaned_response)
            
            # Validate required fields
            required_fields = ['executor_type', 'parameters', 'confidence', 'reasoning']
            for field in required_fields:
                if field not in decision_data:
                    raise ValueError(f"LLM response missing required field: {field}")
            
            # Validate executor type
            valid_executors = [
                # Human-centric executors
                'email', 'crm', 'disclosure', 'task', 'training',
                # API-centric mortgage system executors
                'servicing_api', 'income_api', 'underwriting_api', 'hardship_api',
                'pricing_api', 'document_api', 'compliance_api', 'accounting_api'
            ]
            if decision_data['executor_type'] not in valid_executors:
                raise ValueError(f"Invalid executor type: {decision_data['executor_type']}")
            
            # Validate confidence
            confidence = decision_data['confidence']
            if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
                raise ValueError(f"Invalid confidence value: {confidence}")
            
            # If confidence too low, fail fast
            if confidence < 0.6:
                raise ValueError(
                    f"Low confidence ({confidence}) in executor decision. "
                    f"Action too ambiguous: {action_item}"
                )
            
            return decision_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON: {e}")
        except Exception as e:
            raise ValueError(f"Execution analysis failed: {e}")
    
    async def generate_execution_payload(self, workflow: Dict[str, Any], 
                                       executor_type: str) -> Dict[str, Any]:
        """Generate realistic execution payload for specific executor type.
        
        Args:
            workflow: Complete workflow data
            executor_type: Type of executor (email, crm, disclosure, task, training)
            
        Returns:
            ExecutionPayload with mock payload data
            
        Raises:
            ValueError: If cannot generate payload (NO FALLBACK)
        """
        # Validate executor type
        valid_executors = [
            # Human-centric executors
            'email', 'crm', 'disclosure', 'task', 'training',
            # API-centric mortgage system executors
            'servicing_api', 'income_api', 'underwriting_api', 'hardship_api',
            'pricing_api', 'document_api', 'compliance_api', 'accounting_api'
        ]
        if executor_type not in valid_executors:
            raise ValueError(f"Invalid executor type: {executor_type}")
        
        # Extract workflow data
        workflow_data = workflow.get('workflow_data', {})
        action_item = workflow_data.get('action_item', '')
        description = workflow_data.get('description', '')
        workflow_type = workflow.get('workflow_type', 'UNKNOWN')
        
        # Create payload generation prompt
        prompt = self._create_payload_prompt(executor_type, action_item, description, 
                                           workflow_type, workflow)
        
        try:
            # Get LLM payload
            response = await self.llm.generate_text_async(prompt, temperature=0.3)
            
            # Debug: Check response
            if not response or not response.strip():
                raise ValueError(f"LLM returned empty response for payload. Prompt length: {len(prompt)} chars")
            
            # Clean response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]  # Remove ```
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]  # Remove ending ```
            cleaned_response = cleaned_response.strip()
            
            # Parse response as JSON
            payload_data = json.loads(cleaned_response)
            
            # Validate payload structure based on executor type
            self._validate_payload_structure(executor_type, payload_data)
            
            return payload_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned invalid JSON for payload: {e}")
        except Exception as e:
            raise ValueError(f"Payload generation failed: {e}")
    
    def _create_analysis_prompt(self, action_item: str, description: str,
                              workflow_type: str, workflow: Dict[str, Any]) -> str:
        """Create prompt for execution analysis."""
        return prompt_loader.format(
            'agents/workflow_execution/analysis.txt',
            workflow_type=workflow_type,
            action_item=action_item,
            description=description,
            plan_id=workflow.get('plan_id', 'UNKNOWN'),
            risk_level=workflow.get('risk_level', 'UNKNOWN')
        )

    def _create_payload_prompt(self, executor_type: str, action_item: str,
                             description: str, workflow_type: str,
                             workflow: Dict[str, Any]) -> str:
        """Create prompt for payload generation."""

        # Load base prompt
        base_prompt = prompt_loader.format(
            'agents/workflow_execution/payload_base.txt',
            executor_type=executor_type,
            workflow_type=workflow_type,
            action_item=action_item,
            description=description,
            plan_id=workflow.get('plan_id', 'UNKNOWN'),
            risk_level=workflow.get('risk_level', 'UNKNOWN')
        )

        # Load specific payload format based on executor type
        if executor_type in ['email', 'crm', 'disclosure', 'task', 'training']:
            specific_prompt = prompt_loader.load(f'agents/workflow_execution/payload_{executor_type}.txt')
            return f"{base_prompt}\n\n{specific_prompt}"
        else:
            return base_prompt + "\nGenerate appropriate payload structure for this executor type."
    
    def _validate_payload_structure(self, executor_type: str, payload_data: Dict[str, Any]):
        """Validate payload has required structure for executor type."""
        
        if executor_type == 'email':
            required_fields = ['to', 'subject', 'body']
            for field in required_fields:
                if field not in payload_data:
                    raise ValueError(f"Email payload missing required field: {field}")
            
            # Validate email format
            if '@' not in payload_data['to']:
                raise ValueError("Invalid email address in 'to' field")
            
            # Validate content length
            if len(payload_data['body']) < 20:
                raise ValueError("Email body too short")
        
        elif executor_type == 'crm':
            required_fields = ['customer_id', 'updates']
            for field in required_fields:
                if field not in payload_data:
                    raise ValueError(f"CRM payload missing required field: {field}")
            
            # Validate updates structure
            if not isinstance(payload_data['updates'], dict):
                raise ValueError("CRM updates must be a dictionary")
        
        elif executor_type == 'disclosure':
            required_fields = ['document_type', 'customer_data']
            for field in required_fields:
                if field not in payload_data:
                    raise ValueError(f"Disclosure payload missing required field: {field}")
        
        elif executor_type == 'task':
            required_fields = ['assignee', 'title', 'description']
            for field in required_fields:
                if field not in payload_data:
                    raise ValueError(f"Task payload missing required field: {field}")
            
            # Validate description length
            if len(payload_data['description']) < 20:
                raise ValueError("Task description too short")
        
        elif executor_type == 'training':
            required_fields = ['employee_id', 'training_module']
            for field in required_fields:
                if field not in payload_data:
                    raise ValueError(f"Training payload missing required field: {field}")