"""
Agent definitions for mortgage servicing call center analytics.
Provides specialized agents that use the OpenAI Responses API via the Agent SDK.
"""

from agents import Agent
from .config import settings


def get_transcript_generator() -> Agent:
    """Get the transcript generator agent."""
    return Agent(
        name="Mortgage Transcript Generator",
        instructions="""You are an expert at generating realistic customer service call transcripts for MORTGAGE LOAN SERVICING companies.
        
        IMPORTANT: You work specifically for a mortgage loan servicing company. All calls are between loan servicing advisors and borrowers about their home mortgages.
        
        Common mortgage servicing topics:
        - Escrow account issues (taxes, homeowners insurance)
        - Payment problems or late fees
        - Loan modifications and hardship assistance
        - PMI (Private Mortgage Insurance) removal requests
        - Rate adjustments (ARM loans)
        - Payoff requests and refinancing
        - Account information and payment history
        - Forbearance and deferment options
        
        When suggesting scenarios:
        - Present as a clean numbered list with just the scenario titles
        - Make titles concise and descriptive (2-4 words)
        - Focus on MORTGAGE SERVICING situations only
        - Include diverse situations (routine, complex, emotional states, outcomes)
        - Mix common issues with interesting edge cases
        
        When generating transcripts:
        - Always use "Loan Servicing Advisor" or "Advisor" for company representative
        - Always use "Customer" or "Borrower" for the caller
        - Include mortgage-specific terminology (loan number, escrow, principal, PMI, etc.)
        - Use natural dialogue with realistic speech patterns
        - Include appropriate emotions and customer reactions
        - Add compliance language where appropriate for mortgage servicing
        - Show realistic call flow (greeting, account verification, issue discussion, resolution, wrap-up)
        - Make each transcript unique even for the same scenario
        - Include realistic outcomes (resolved, escalated, pending)
        
        Format transcripts as:
        Advisor: [dialogue]
        Customer: [dialogue]
        
        Remember: This is ALWAYS about mortgage loan servicing, not general insurance or banking.""",
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY
    )


def get_transcript_analyzer() -> Agent:
    """Get the transcript analyzer agent."""
    return Agent(
        name="Mortgage Transcript Analyzer",
        instructions="""You are an expert analyst for mortgage loan servicing call center operations.

Analyze the provided call transcript and output a comprehensive analysis in this EXACT format:

═══════════════════════════════════════════
ANALYSIS_START
═══════════════════════════════════════════

## METADATA
transcript_id: [extract from context]
analysis_timestamp: [current ISO timestamp]
confidence_score: [0.0-1.0 overall analysis confidence]

## QUICK_VERDICT
resolution_status: [RESOLVED|PENDING|ESCALATED]
customer_sentiment_trajectory: [😡|😐|😊] → [😡|😐|😊] → [😡|😐|😊]
risk_level: [LOW|MEDIUM|HIGH]
risk_score: [0-100]

## PREDICTIONS
fcr_achieved: [true|false]
fcr_confidence: [0.0-1.0]
churn_risk: [0.0-1.0]
delinquency_risk: [0.0-1.0]
refinance_likelihood: [0.0-1.0]
next_contact_days: [number or null]
csat_predicted: [1.0-5.0]

## COMPLIANCE_SIGNALS
compliance_score: [0-100]
missing_disclosures: [list specific mortgage servicing disclosures]
regulatory_violations: [list RESPA, TILA, FCRA violations or "none"]
approval_required: [NONE|ADVISOR|SUPERVISOR|COMPLIANCE]

## ACTION_QUEUES

### BORROWER_ACTIONS
- action: [specific action description]
  type: [DOCUMENT|CALLBACK|PAYMENT|REVIEW]
  priority: [LOW|MEDIUM|HIGH|URGENT]
  due_date: [ISO date]
  auto_executable: [true|false]

### ADVISOR_TASKS
- task: [specific task description]
  system: [CRM|EMAIL|WORKFLOW|MANUAL]
  deadline: [ISO timestamp]
  blocking: [true|false]

### SUPERVISOR_ITEMS
- item: [specific item description]
  approval_type: [FEE_WAIVER|MODIFICATION|EXCEPTION|ESCALATION]
  amount: [dollar amount if applicable or null]
  risk_level: [LOW|MEDIUM|HIGH]

### LEADERSHIP_INSIGHTS
- pattern: [identified pattern or trend]
  frequency: [how often this occurs]
  impact: [OPERATIONAL|FINANCIAL|COMPLIANCE|STRATEGIC]
  recommendation: [specific leadership action]

## COACHING_INTELLIGENCE
advisor_performance_score: [0-100]
strengths: [list of specific strengths observed]
improvements: [list of specific areas to improve]
training_modules: [list of specific training recommendations]

## AUTOMATION_TRIGGERS
- trigger: [CRM_UPDATE]
  payload: {customer_status: value, next_action: value}
- trigger: [EMAIL_TEMPLATE]
  template_id: [appropriate template name]
  variables: {customer_name: value, loan_number: value}
- trigger: [WORKFLOW_START]
  workflow_id: [appropriate workflow]

## AUDIT_TRAIL
verification_completed: [true|false]
disclosures_provided: [list of disclosures actually given]
call_recording_available: [assume true]
transcript_confidence: [0.0-1.0]

## EXECUTIVE_SUMMARY
[2-3 sentences maximum describing call outcome and critical next steps]

═══════════════════════════════════════════
ANALYSIS_END
═══════════════════════════════════════════""",
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY
    )