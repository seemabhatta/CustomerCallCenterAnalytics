"""Generic prompt builder - completely agentic approach."""
from typing import Any, Dict
from ..utils.prompt_loader import prompt_loader


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
            return prompt_loader.format('generators/transcript_generation.txt', context=params_str)
        else:
            # For empty kwargs, use a default context
            return prompt_loader.format('generators/transcript_generation.txt', context="general mortgage servicing topics")
    
    # Keep backward compatibility
    def build_transcript_prompt(self, **kwargs) -> str:
        """Alias for backward compatibility."""
        return self.build_prompt(**kwargs)