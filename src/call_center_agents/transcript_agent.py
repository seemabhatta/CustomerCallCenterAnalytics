"""Simple transcript generator - just natural conversations."""
import os
import uuid
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

from src.models.transcript import Transcript, Message
from src.utils.prompt_loader import prompt_loader
from src.call_center_agents.helpers.response_parser import ResponseParser
from src.infrastructure.llm.openai_wrapper import OpenAIWrapper

# Load environment variables from .env file
load_dotenv()


def _get_generation_temperature() -> float:
    """Get temperature for text generation - NO FALLBACK."""
    temp = os.getenv("TEMPERATURE_GENERATION")
    if not temp:
        raise ValueError("TEMPERATURE_GENERATION environment variable not set - NO FALLBACK")
    return float(temp)


class TranscriptAgent:
    """Transcript generation agent - creates natural conversations."""
    
    def __init__(self):
        """Initialize the transcript agent."""
        self.llm = OpenAIWrapper()
        self.response_parser = ResponseParser()
    
    def generate(self, **context) -> Transcript:
        """Generate a natural conversation transcript.
        
        Args:
            **context: Any context parameters for the conversation
            
        Returns:
            Generated Transcript object
        """
        # Build simple prompt
        if context:
            params_str = ", ".join([f"{k}: {v}" for k, v in context.items() if v is not None])
            prompt = prompt_loader.format('agents/transcript_generation.txt', context=params_str)
        else:
            prompt = prompt_loader.format('agents/transcript_generation.txt', context="general mortgage servicing topics")
        
        # Get conversation from OpenAI
        try:
            conversation_text = self._call_openai(prompt)
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
        
        # Parse conversation
        parsed_data = self.response_parser.parse_response(conversation_text)
        
        # Create messages
        messages = []
        for msg_data in parsed_data.get("messages", []):
            if isinstance(msg_data, dict) and "speaker" in msg_data and "text" in msg_data:
                messages.append(Message(**msg_data))
        
        # Create transcript with any additional attributes from parsing
        transcript_attrs = {k: v for k, v in parsed_data.items() if k != "messages"}
        
        return Transcript(
            id=f"CALL_{uuid.uuid4().hex[:8].upper()}",
            messages=messages,
            timestamp=datetime.now().isoformat() + 'Z',
            **context,  # Include original context
            **transcript_attrs  # Include any parsed attributes
        )
    
    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API using wrapper.

        Args:
            prompt: The prompt to send

        Returns:
            Response text
        """
        return self.llm.generate_text(prompt, temperature=_get_generation_temperature())
    
    def generate_batch(self, count: int, **context) -> list[Transcript]:
        """Generate multiple transcripts.
        
        Args:
            count: Number of transcripts to generate
            **context: Context for all transcripts
            
        Returns:
            List of generated transcripts
        """
        transcripts = []
        
        for i in range(count):
            try:
                transcript = self.generate(**context)
                transcripts.append(transcript)
            except Exception as e:
                continue
        
        return transcripts