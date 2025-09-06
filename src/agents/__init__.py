"""
Agents package for the Customer Call Center Analytics system.
"""

from .orchestrator import get_orchestrator, CoilotOrchestrator

# Import main agents module using importlib to avoid circular imports
import importlib.util
import sys
import os

def _get_main_agents():
    """Get the main agents module avoiding circular imports"""
    spec = importlib.util.spec_from_file_location(
        "main_agents", 
        os.path.join(os.path.dirname(__file__), "..", "agents.py")
    )
    main_agents = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(main_agents)
    return main_agents

# Re-export functions from the main agents module to maintain compatibility
def get_generator():
    """Get the generator agent"""
    main_agents = _get_main_agents()
    return main_agents.get_generator()

def get_analyzer():
    """Get the analyzer agent (triage orchestrator)"""
    main_agents = _get_main_agents()
    return main_agents.get_analyzer()

def get_triage_agent():
    """Get the triage orchestrator agent"""
    main_agents = _get_main_agents()
    return main_agents.get_triage_agent()

def get_sentiment_agent():
    """Get the sentiment intelligence agent"""
    main_agents = _get_main_agents()
    return main_agents.get_sentiment_agent()

def get_compliance_agent():
    """Get the compliance agent"""
    main_agents = _get_main_agents()
    return main_agents.get_compliance_agent()

def get_offer_agent():
    """Get the offer optimization agent"""
    main_agents = _get_main_agents()
    return main_agents.get_offer_agent()

def get_coach_agent():
    """Get the performance coach agent"""
    main_agents = _get_main_agents()
    return main_agents.get_coach_agent()

__all__ = [
    'get_orchestrator', 'CoilotOrchestrator',
    'get_generator', 'get_analyzer', 'get_triage_agent',
    'get_sentiment_agent', 'get_compliance_agent', 
    'get_offer_agent', 'get_coach_agent'
]