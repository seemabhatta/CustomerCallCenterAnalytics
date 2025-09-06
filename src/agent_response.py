"""
Agent Response wrapper for displaying agent information in CLI
"""

class AgentResponse:
    """Wrapper for agent responses with configurable display formatting"""
    
    def __init__(self, content, agent_name, agent_chain=None):
        """
        Initialize agent response
        
        Args:
            content: The response content from the agent
            agent_name: Name of the primary responding agent
            agent_chain: List of agent names in handoff chain (optional)
        """
        self.content = content
        self.agent_name = agent_name
        self.agent_chain = agent_chain or [agent_name]
    
    def format_display(self, mode="full", override=None):
        """
        Format the response for display based on configuration
        
        Args:
            mode: Display mode ("full", "simple", "none", "last_only")
            override: Override agent name to display (e.g., "Co-Pilot")
            
        Returns:
            Formatted string ready for display
        """
        if override:
            return f"[{override}]: {self.content}"
        
        if mode == "none":
            return self.content
        elif mode == "simple":
            return f"[{self.agent_name}]: {self.content}"
        elif mode == "last_only":
            final_agent = self.agent_chain[-1] if self.agent_chain else self.agent_name
            return f"[{final_agent}]: {self.content}"
        elif mode == "full":
            if len(self.agent_chain) > 1:
                chain = " → ".join(self.agent_chain)
                return f"[{chain}]: {self.content}"
            else:
                return f"[{self.agent_name}]: {self.content}"
        
        # Default fallback
        return self.content
    
    def add_to_chain(self, agent_name):
        """Add an agent to the handoff chain"""
        if agent_name not in self.agent_chain:
            self.agent_chain.append(agent_name)
    
    def __str__(self):
        """Default string representation"""
        return self.content