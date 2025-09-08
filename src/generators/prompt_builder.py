"""Generic prompt builder - completely agentic approach."""
from typing import Any, Dict


class PromptBuilder:
    """Generic prompt builder - let AI decide everything."""
    
    def build_prompt(self, **kwargs) -> str:
        """Build a minimal prompt, letting AI determine all specifics.
        
        Args:
            **kwargs: Any context parameters to include
            
        Returns:
            Simple prompt string
        """
        if kwargs:
            # Just pass parameters and let AI interpret them
            params_str = ", ".join([f"{k}: {v}" for k, v in kwargs.items() if v is not None])
            return f"Generate a conversation with: {params_str}"
        else:
            return "Generate a conversation"
    
    # Keep backward compatibility
    def build_transcript_prompt(self, **kwargs) -> str:
        """Alias for backward compatibility."""
        return self.build_prompt(**kwargs)