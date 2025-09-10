"""
ComplianceValidator: Automated compliance checking and validation

Core Principles:
- LLM-based compliance evaluation (no hardcoded rules)
- CFPB and regulatory requirement validation
- Financial action authorization checking
"""

import json
from typing import Dict, List, Any
from openai import OpenAI


class ComplianceValidator:
    """
    LLM-based compliance validator for mortgage servicing actions.
    
    Features:
    - CFPB disclosure requirement validation
    - Financial action authorization checking
    - Dynamic compliance rule evaluation
    - Risk assessment for compliance violations
    """
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def validate_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate action against comprehensive compliance requirements.
        
        Args:
            action: Action to validate
            
        Returns:
            Validation result with compliance status and recommendations
        """
        validation_prompt = self._build_validation_prompt(action)
        
        try:
            response = self.client.responses.create(
                model="gpt-4o",
                input=validation_prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "ComplianceValidation",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "compliance_status": {
                                    "type": "string",
                                    "enum": ["compliant", "non_compliant", "needs_review"]
                                },
                                "violations": {"type": "array", "items": {"type": "string"}},
                                "risk_level": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "critical"]
                                },
                                "recommendations": {"type": "array", "items": {"type": "string"}},
                                "required_disclosures": {"type": "array", "items": {"type": "string"}},
                                "regulatory_concerns": {"type": "array", "items": {"type": "string"}},
                                "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                            },
                            "required": ["compliance_status", "violations", "risk_level", "recommendations", "required_disclosures", "regulatory_concerns", "confidence_score"],
                            "additionalProperties": False
                        }
                    }
                }
            )
            
            # Extract validation result using the structured output
            for block in getattr(response, "output", []) or []:
                for content in getattr(block, "content", []) or []:
                    parsed = getattr(content, "parsed", None)
                    if parsed is not None:
                        return parsed
            
            # If structured parsing failed, return a safe default for testing
            return {
                "compliance_status": "needs_review",
                "violations": ["Validation parsing error"],
                "risk_level": "medium", 
                "recommendations": ["Review action manually"],
                "required_disclosures": [],
                "regulatory_concerns": [],
                "confidence_score": 0.5
            }
            
        except Exception as e:
            raise Exception(f"Compliance validation failed: {str(e)}")
    
    def _build_validation_prompt(self, action: Dict[str, Any]) -> str:
        """Build comprehensive compliance validation prompt."""
        return f"""
You are a compliance validation system for mortgage servicing operations. Validate this action against all applicable regulations.

ACTION TO VALIDATE:
{json.dumps(action, indent=2)}

COMPLIANCE FRAMEWORK:
1. CFPB Regulations:
   - Truth in Lending Act (TILA)
   - Real Estate Settlement Procedures Act (RESPA)
   - Fair Debt Collection Practices Act (FDCPA)
   - Fair Credit Reporting Act (FCRA)

2. State Regulations:
   - State-specific foreclosure laws
   - Consumer protection requirements
   - Licensing and disclosure requirements

3. Company Policies:
   - Customer communication standards
   - Documentation requirements
   - Approval thresholds and procedures

4. Industry Standards:
   - Mortgage Bankers Association guidelines
   - Best practices for customer service
   - Data privacy and security requirements

VALIDATION CRITERIA:
- Are all required disclosures present?
- Is proper authorization obtained for financial actions?
- Are customer rights properly protected?
- Is documentation complete and accurate?
- Are communication standards met?
- Are privacy and security requirements followed?

TASK: Provide comprehensive compliance validation with specific violations, risk assessment, and actionable recommendations.

Focus on mortgage servicing compliance requirements and customer protection standards.
"""
    
    def validate_cfpb_compliance(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Validate specific CFPB compliance requirements."""
        cfpb_prompt = f"""
Validate this mortgage servicing action against CFPB requirements:

ACTION:
{json.dumps(action, indent=2)}

CFPB REQUIREMENTS TO CHECK:
1. PMI Removal Disclosures (if applicable)
2. Payment Processing Notifications
3. Error Resolution Procedures
4. Loss Mitigation Communications
5. Foreclosure Prevention Requirements
6. Customer Rights Notifications

Provide detailed CFPB compliance assessment.
"""
        
        try:
            response = self.client.responses.create(
                model="gpt-4o",
                input=cfpb_prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "CFPBCompliance",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "compliant": {"type": "boolean"},
                                "violations": {"type": "array", "items": {"type": "string"}},
                                "required_disclosures": {"type": "array", "items": {"type": "string"}},
                                "cfpb_sections": {"type": "array", "items": {"type": "string"}},
                                "remediation_steps": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["compliant", "violations", "required_disclosures", "cfpb_sections", "remediation_steps"],
                            "additionalProperties": False
                        }
                    }
                }
            )
            
            for block in getattr(response, "output", []) or []:
                for content in getattr(block, "content", []) or []:
                    parsed = getattr(content, "parsed", None)
                    if parsed is not None:
                        return parsed
            
            return {"compliant": False, "violations": ["CFPB validation parsing error"], "required_disclosures": [], "cfpb_sections": [], "remediation_steps": []}
            
        except Exception as e:
            return {"compliant": False, "violations": [f"CFPB validation error: {str(e)}"], "required_disclosures": [], "cfpb_sections": [], "remediation_steps": []}
    
    def validate_financial_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Validate financial action authorization and documentation."""
        financial_prompt = f"""
Validate this financial action for proper authorization and documentation:

FINANCIAL ACTION:
{json.dumps(action, indent=2)}

VALIDATION CRITERIA:
1. Authorization Level Adequacy:
   - Is the authorizing party appropriate for the transaction amount?
   - Are proper approval hierarchies followed?
   - Is dual authorization required?

2. Documentation Completeness:
   - Are all required documents present?
   - Is customer consent documented?
   - Are regulatory forms completed?

3. Risk Assessment:
   - What is the financial risk exposure?
   - Are controls adequate for the risk level?
   - Is additional oversight needed?

4. Regulatory Compliance:
   - Are anti-money laundering requirements met?
   - Is proper record keeping in place?
   - Are reporting requirements satisfied?

Provide comprehensive financial action validation.
"""
        
        try:
            response = self.client.responses.create(
                model="gpt-4o",
                input=financial_prompt,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "FinancialValidation",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "authorization_adequate": {"type": "boolean"},
                                "documentation_complete": {"type": "boolean"},
                                "risk_assessment": {
                                    "type": "string",
                                    "enum": ["low", "medium", "high", "critical"]
                                },
                                "required_approvals": {"type": "array", "items": {"type": "string"}},
                                "missing_documents": {"type": "array", "items": {"type": "string"}},
                                "control_recommendations": {"type": "array", "items": {"type": "string"}}
                            },
                            "required": ["authorization_adequate", "documentation_complete", "risk_assessment", "required_approvals", "missing_documents", "control_recommendations"],
                            "additionalProperties": False
                        }
                    }
                }
            )
            
            for block in getattr(response, "output", []) or []:
                for content in getattr(block, "content", []) or []:
                    parsed = getattr(content, "parsed", None)
                    if parsed is not None:
                        return parsed
            
            return {
                "authorization_adequate": False,
                "documentation_complete": False,
                "risk_assessment": "high"
            }
            
        except Exception as e:
            return {
                "authorization_adequate": False,
                "documentation_complete": False,
                "risk_assessment": "critical",
                "validation_error": str(e)
            }