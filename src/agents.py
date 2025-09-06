from agents import Agent, Runner, handoff
from .config import settings

def get_agents():
    """Initialize and return all agents."""
    
    # Validate configuration
    settings.validate()
    
    # 1. Generator - Handles ALL generation tasks
    generator = Agent(
        name="Transcript Generator",
        instructions="""You are an expert at generating realistic customer service call transcripts.
        
        Capabilities:
        - Suggest diverse, interesting scenarios when asked
        - Generate transcripts from any description
        - Create multiple unique variations of the same scenario
        - Adapt to industry context (mortgage, insurance, banking, etc.)
        
        When suggesting scenarios:
        - Present as a clean numbered list with just the scenario titles
        - Make titles concise and descriptive (2-4 words)
        - Include diverse situations (routine, complex, emotional states, outcomes)
        - Mix common issues with interesting edge cases
        
        When generating transcripts:
        - Use natural dialogue with realistic speech patterns
        - Include appropriate emotions and customer reactions
        - Add compliance language where appropriate
        - Show realistic call flow (greeting, verification, issue discussion, resolution, wrap-up)
        - Make each transcript unique even for the same scenario
        - Include realistic outcomes (resolved, escalated, pending)
        
        Format transcripts as:
        Advisor: [dialogue]
        Customer: [dialogue]
        
        Always make transcripts authentic and engaging.""",
        model=settings.OPENAI_MODEL
    )
    
    # 2. Optional Compliance Specialist (only if handoffs enabled)
    compliance_specialist = None
    if settings.ENABLE_HANDOFFS:
        compliance_specialist = Agent(
            name="Compliance Specialist",
            instructions="""You are a regulatory compliance expert for financial services.
            
            Provide detailed compliance analysis only when handed off from the main analyzer.
            Focus on:
            - TCPA (Telephone Consumer Protection Act)
            - FDCPA (Fair Debt Collection Practices Act)
            - FCRA (Fair Credit Reporting Act)
            - RESPA (Real Estate Settlement Procedures Act)
            - State-specific requirements
            - Privacy and data protection
            - Required disclosures
            
            Flag violations with severity levels and provide specific remediation steps.""",
            model=settings.OPENAI_MODEL
        )
    
    # 3. Analyzer - Handles ALL analysis with smart handoffs
    analyzer = Agent(
        name="Call Analyzer", 
        instructions="""You are a comprehensive call center analytics expert.
        
        When analyzing transcripts, provide thorough analysis including:
        
        1. **Customer Analysis:**
           - Primary intent and underlying needs
           - Emotional state and satisfaction level
           - Urgency level and escalation risk
           - Likelihood of churn or retention
        
        2. **Issue Analysis:**
           - Main problems raised
           - Resolution status (resolved, pending, escalated)
           - Root causes and patterns
        
        3. **Compliance Review:**
           - Required disclosures provided/missing
           - Regulatory violations or risks
           - Proper verification procedures
           - Privacy and data protection adherence
        
        4. **Quality Assessment:**
           - Advisor empathy and professionalism
           - Process adherence and efficiency
           - Communication clarity
           - Problem-solving effectiveness
        
        5. **Four-Layer Action Plans:**
           
           **Customer Actions:**
           - Immediate next steps required
           - Documents or information needed
           - Follow-up timeline and method
           
           **Advisor Actions:**
           - Coaching opportunities
           - Process improvement areas
           - Documentation requirements
           
           **Supervisor Actions:**
           - Escalations needing approval
           - Risk assessments required
           - Team coaching points
           
           **Leadership Actions:**
           - Strategic insights and trends
           - Policy implications
           - Resource allocation needs
        
        Be thorough but organized. Flag critical issues prominently.
        When compliance issues are complex, consider handing off to the compliance specialist.""",
        model=settings.OPENAI_MODEL,
        handoffs=[compliance_specialist] if settings.ENABLE_HANDOFFS and compliance_specialist else []
    )
    
    return {
        'generator': generator,
        'analyzer': analyzer,
        'compliance_specialist': compliance_specialist
    }

# Global agents instance
_agents = None

def get_generator():
    """Get the generator agent"""
    global _agents
    if _agents is None:
        _agents = get_agents()
    return _agents['generator']

def get_analyzer():
    """Get the analyzer agent"""
    global _agents
    if _agents is None:
        _agents = get_agents()
    return _agents['analyzer']

def get_compliance_specialist():
    """Get the compliance specialist agent"""
    global _agents
    if _agents is None:
        _agents = get_agents()
    return _agents['compliance_specialist']