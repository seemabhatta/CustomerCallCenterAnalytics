"""Prompt loading utility for external prompt management."""
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class PromptLoader:
    """Utility for loading and managing external prompt files."""

    def __init__(self):
        """Initialize the prompt loader with the prompts directory."""
        self.prompt_dir = Path(__file__).parent.parent.parent / 'prompts'
        self._cache = {}

        # Ensure prompts directory exists
        if not self.prompt_dir.exists():
            logger.warning(f"Prompts directory not found: {self.prompt_dir}")

    def load(self, prompt_path: str) -> str:
        """Load prompt from file with caching.

        Args:
            prompt_path: Relative path to prompt file (e.g., 'generators/transcript_generation.txt')

        Returns:
            Content of the prompt file

        Raises:
            FileNotFoundError: If the prompt file doesn't exist
        """
        if prompt_path in self._cache:
            return self._cache[prompt_path]

        full_path = self.prompt_dir / prompt_path
        if not full_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {full_path}")

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise IOError(f"Failed to read prompt file {full_path}: {e}")

        self._cache[prompt_path] = content
        logger.debug(f"Loaded prompt: {prompt_path}")
        return content

    def format(self, prompt_path: str, **kwargs) -> str:
        """Load and format prompt with variables.

        Args:
            prompt_path: Relative path to prompt file
            **kwargs: Variables to substitute in the prompt template

        Returns:
            Formatted prompt string
        """
        template = self.load(prompt_path)

        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable {e} for prompt {prompt_path}")
        except Exception as e:
            raise ValueError(f"Failed to format prompt {prompt_path}: {e}")

    def parse_sections(self, prompt_path: str) -> Dict[str, str]:
        """Parse prompt file with sections (e.g., [SYSTEM], [USER]).

        Args:
            prompt_path: Relative path to prompt file

        Returns:
            Dictionary mapping section names to content
        """
        content = self.load(prompt_path)
        sections = {}
        current_section = None
        current_content = []

        for line in content.split('\n'):
            line = line.strip()

            # Check for section header
            if line.startswith('[') and line.endswith(']'):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = line[1:-1].lower()
                current_content = []
            else:
                current_content.append(line)

        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def clear_cache(self):
        """Clear the prompt cache."""
        self._cache.clear()
        logger.debug("Prompt cache cleared")


# Global instance for easy access
prompt_loader = PromptLoader()