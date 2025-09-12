"""
Workflow Execution Agent - LLM-powered execution decision maker.
Analyzes workflow action items and makes intelligent execution decisions.
NO FALLBACK LOGIC - fails fast if cannot make decisions.
"""
import json
from typing import Dict, Any
from datetime import datetime

from src.llm.openai_wrapper import OpenAIWrapper
from src.llm.openai_wrapper import ActionItem


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
            
            # Parse response as JSON
            decision_data = json.loads(response)
            
            # Validate required fields
            required_fields = ['executor_type', 'parameters', 'confidence', 'reasoning']
            for field in required_fields:
                if field not in decision_data:
                    raise ValueError(f"LLM response missing required field: {field}")
            
            # Validate executor type
            valid_executors = ['email', 'crm', 'disclosure', 'task', 'training']
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
        valid_executors = ['email', 'crm', 'disclosure', 'task', 'training']
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
            
            # Parse response as JSON
            payload_data = json.loads(response)
            
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
        return f"""You are a Workflow Execution Analysis Agent. Your job is to analyze action items and determine the best execution approach.

WORKFLOW CONTEXT:
- Type: {workflow_type} 
- Action: {action_item}
- Description: {description}
- Plan ID: {workflow.get('plan_id', 'UNKNOWN')}
- Risk Level: {workflow.get('risk_level', 'UNKNOWN')}

AVAILABLE EXECUTORS:
1. email - Send emails to borrowers, advisors, or stakeholders
2. crm - Update customer records, add notes, change status
3. disclosure - Generate and deliver compliance documents
4. task - Create tasks for advisors, supervisors, or teams
5. training - Assign training modules to staff members

ANALYSIS RULES:
- If action involves "send email", "notify", "communicate" → email executor
- If action involves "update record", "CRM", "customer data" → crm executor  
- If action involves "disclosure", "documents", "compliance forms" → disclosure executor
- If action involves "assign task", "follow up", "schedule" → task executor
- If action involves "training", "coaching", "learning" → training executor

CONFIDENCE RULES:
- High confidence (0.9+): Clear action type with obvious executor
- Medium confidence (0.7-0.9): Clear action but some ambiguity
- Low confidence (<0.7): Ambiguous action - REJECT with error

OUTPUT REQUIREMENTS:
Return ONLY valid JSON with these exact fields:
{{
    "executor_type": "email|crm|disclosure|task|training",
    "parameters": {{
        "key1": "value1",
        "key2": "value2"
    }},
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of decision"
}}

PARAMETER GUIDELINES:
- email: recipient, subject, message_type, attachments
- crm: customer_id, updates, interaction_type  
- disclosure: document_type, customer_data, delivery_method
- task: assignee, title, priority, due_date
- training: employee_id, module_name, completion_required

CRITICAL: If action is unclear or ambiguous, set confidence < 0.7 and explain why in reasoning.
NO FALLBACK DECISIONS - be precise or fail."""

    def _create_payload_prompt(self, executor_type: str, action_item: str, 
                             description: str, workflow_type: str, 
                             workflow: Dict[str, Any]) -> str:
        """Create prompt for payload generation."""
        
        base_prompt = f"""You are a Workflow Payload Generation Agent. Generate realistic mock payload for {executor_type} executor.

WORKFLOW CONTEXT:
- Type: {workflow_type}
- Action: {action_item}
- Description: {description}
- Plan ID: {workflow.get('plan_id', 'UNKNOWN')}
- Risk Level: {workflow.get('risk_level', 'UNKNOWN')}

GENERATE REALISTIC PAYLOAD:
Create detailed, realistic data that would be used in production.
Use contextual information to make payload specific and relevant.
Include all required fields for {executor_type} operations.

"""
        
        if executor_type == 'email':
            return base_prompt + """
EMAIL PAYLOAD FORMAT:
{{
    "to": "recipient@example.com",
    "cc": ["cc@example.com"],
    "subject": "Specific subject based on action",
    "body": "Detailed email body content (minimum 100 chars)",
    "attachments": ["file1.pdf", "file2.pdf"],
    "template_id": "template_name",
    "delivery_method": "smtp",
    "priority": "normal|high|urgent"
}}

REQUIREMENTS:
- Subject must be specific to the action
- Body must be professional and relevant (100+ characters)
- Include appropriate attachments based on action type
- Use borrower-friendly language for BORROWER workflows
- Use internal language for ADVISOR/SUPERVISOR workflows
"""
        
        elif executor_type == 'crm':
            return base_prompt + """
CRM PAYLOAD FORMAT:
{{
    "customer_id": "CUST_123456",
    "api_endpoint": "/api/v1/customers/update",
    "method": "POST|PUT|PATCH",
    "updates": {{
        "status": "new_status",
        "notes": "Detailed notes about interaction",
        "last_contact": "2024-01-15",
        "tags": ["tag1", "tag2"],
        "custom_fields": {{
            "field1": "value1"
        }}
    }},
    "crm_system": "salesforce|hubspot|dynamics",
    "interaction_type": "call|email|meeting|system_update"
}}

REQUIREMENTS:
- Notes must be detailed and professional (50+ characters)
- Status updates must be meaningful business states
- Include relevant custom fields based on workflow type
- Use proper CRM terminology
"""
        
        elif executor_type == 'disclosure':
            return base_prompt + """
DISCLOSURE PAYLOAD FORMAT:
{{
    "document_type": "tila|respa|refinance_disclosure|general",
    "customer_id": "CUST_123456",
    "customer_data": {{
        "loan_amount": 250000,
        "interest_rate": 6.5,
        "term_years": 30,
        "property_address": "123 Main St, City, ST 12345"
    }},
    "required_fields": {{
        "apr": "6.75%",
        "finance_charge": "$150,000",
        "total_payments": "$400,000"
    }},
    "compliance_flags": ["TILA", "RESPA", "ECOA"],
    "delivery_method": "email|mail|portal",
    "generation_timestamp": "2024-01-15T10:30:00Z"
}}

REQUIREMENTS:
- Document type must match action requirements
- Include realistic financial data
- Add all relevant compliance flags
- Use proper regulatory terminology
"""
        
        elif executor_type == 'task':
            return base_prompt + """
TASK PAYLOAD FORMAT:
{{
    "task_id": "TASK_123456",
    "assignee": "advisor_id|supervisor_id|team_name",
    "title": "Specific task title based on action",
    "description": "Detailed task description with context",
    "priority": "low|medium|high|urgent",
    "due_date": "2024-01-20",
    "category": "follow_up|compliance|documentation|training",
    "workflow_id": "wf_123",
    "customer_id": "CUST_123456",
    "estimated_duration": "30 minutes",
    "task_type": "manual|automated|approval_required"
}}

REQUIREMENTS:
- Title must be actionable and specific
- Description must provide context and steps (50+ characters)
- Due date should be realistic based on priority
- Include customer context when relevant
"""
        
        elif executor_type == 'training':
            return base_prompt + """
TRAINING PAYLOAD FORMAT:
{{
    "employee_id": "EMP_123456",
    "training_module": "module_name",
    "module_details": {{
        "title": "Training Module Title",
        "description": "Module description and objectives",
        "duration_hours": 2,
        "difficulty": "beginner|intermediate|advanced",
        "category": "compliance|sales|customer_service|technical"
    }},
    "assignment_reason": "Based on workflow analysis",
    "due_date": "2024-01-30",
    "completion_required": true,
    "certification_level": "basic|advanced|expert",
    "learning_path": "regulatory_compliance|customer_relations|technical_skills"
}}

REQUIREMENTS:
- Module must be relevant to workflow type and action
- Assignment reason must explain why training is needed
- Include realistic duration and difficulty
- Use appropriate compliance categories for mortgage industry
"""
        
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