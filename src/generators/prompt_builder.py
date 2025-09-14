"""Generic prompt builder - completely agentic approach."""
from typing import Any, Dict


class PromptBuilder:
    """Generic prompt builder - let AI decide everything."""
    
    def build_prompt(self, **kwargs) -> str:
        """Build a mortgage servicing prompt with context.

        Args:
            **kwargs: Any context parameters to include

        Returns:
            Mortgage servicing focused prompt string
        """
        if kwargs:
            # Add mortgage servicing context to all conversations
            params_str = ", ".join([f"{k}: {v}" for k, v in kwargs.items() if v is not None])
            return f"""Generate a mortgage servicing customer care call transcript about: {params_str}

Context: This is a call between a borrower and a mortgage servicing representative. Include realistic mortgage details like loan numbers, property addresses, payment amounts, and mortgage-specific terminology.

Generate a natural conversation that would occur in a mortgage servicing call center."""
        else:
            return "Generate a mortgage servicing customer care call transcript with realistic mortgage details and terminology."
    
    # Keep backward compatibility
    def build_transcript_prompt(self, **kwargs) -> str:
        """Alias for backward compatibility."""
        return self.build_prompt(**kwargs)