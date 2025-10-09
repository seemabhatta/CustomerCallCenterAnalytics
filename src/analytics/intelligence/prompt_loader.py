"""
Utility for loading prompts from the /prompts directory.

Per CLAUDE.md: Keep all prompts in a "prompts" folder for easy updating
without modifying code.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import re


class PromptLoader:
    """Loads and manages LLM prompts from files."""

    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, str] = {}

    def load(self, prompt_name: str, variables: Optional[Dict[str, Any]] = None) -> str:
        """
        Load a prompt template and optionally substitute variables.

        Args:
            prompt_name: Name of prompt file (without .txt extension)
            variables: Dictionary of variables to substitute

        Returns:
            Formatted prompt string

        Example:
            prompt = loader.load('executive_briefing', {
                'forecast': forecast_data,
                'date': '2025-10-09'
            })
        """
        # Check cache
        if prompt_name in self._cache:
            template = self._cache[prompt_name]
        else:
            # Load from file
            prompt_file = self.prompts_dir / f"{prompt_name}.txt"

            if not prompt_file.exists():
                raise FileNotFoundError(
                    f"Prompt file not found: {prompt_file}. "
                    f"Create it in the {self.prompts_dir} directory."
                )

            template = prompt_file.read_text(encoding='utf-8')
            self._cache[prompt_name] = template

        # Substitute variables if provided
        if variables:
            return self._substitute_variables(template, variables)

        return template

    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Substitute {variable_name} placeholders in template.

        Args:
            template: Template string with {placeholders}
            variables: Dictionary of variable values

        Returns:
            Template with variables substituted
        """
        result = template

        for key, value in variables.items():
            placeholder = f"{{{key}}}"

            # Convert value to string appropriately
            if isinstance(value, dict) or isinstance(value, list):
                import json
                value_str = json.dumps(value, indent=2)
            else:
                value_str = str(value)

            result = result.replace(placeholder, value_str)

        return result

    def list_prompts(self) -> list[str]:
        """List all available prompt templates."""
        return [
            p.stem for p in self.prompts_dir.glob("*.txt")
        ]

    def reload(self, prompt_name: Optional[str] = None):
        """
        Reload prompts from disk, clearing cache.

        Args:
            prompt_name: Specific prompt to reload (None = all)
        """
        if prompt_name:
            self._cache.pop(prompt_name, None)
        else:
            self._cache.clear()
