"""
Agents package for the Customer Call Center Analytics system.
"""

from .orchestrator import get_orchestrator, CoilotOrchestrator

# Re-export functions from the main agents module to maintain compatibility
def get_generator():
    """Get the generator agent"""
    from .. import agents as main_agents
    return main_agents.get_generator()

def get_analyzer():
    """Get the analyzer agent (triage orchestrator)"""
    from .. import agents as main_agents
    return main_agents.get_analyzer()

def get_triage_agent():
    """Get the triage orchestrator agent"""
    from .. import agents as main_agents
    return main_agents.get_triage_agent()

def get_sentiment_agent():
    """Get the sentiment intelligence agent"""
    from .. import agents as main_agents
    return main_agents.get_sentiment_agent()

def get_compliance_agent():
    """Get the compliance agent"""
    from .. import agents as main_agents
    return main_agents.get_compliance_agent()

def get_offer_agent():
    """Get the offer optimization agent"""
    from .. import agents as main_agents
    return main_agents.get_offer_agent()

def get_coach_agent():
    """Get the performance coach agent"""
    from .. import agents as main_agents
    return main_agents.get_coach_agent()

__all__ = [
    'get_orchestrator', 'CoilotOrchestrator',
    'get_generator', 'get_analyzer', 'get_triage_agent',
    'get_sentiment_agent', 'get_compliance_agent', 
    'get_offer_agent', 'get_coach_agent'
]