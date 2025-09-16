"""Simple transcript generator - just natural conversations."""
import os
import uuid
from typing import Optional
from datetime import datetime
import openai
from dotenv import load_dotenv

from src.models.transcript import Transcript, Message
from src.utils.prompt_loader import prompt_loader
from src.generators.response_parser import ResponseParser

# Load environment variables from .env file
load_dotenv()


class TranscriptGenerator:
    """Simple transcript generator - creates natural conversations."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the generator.
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set in OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI(api_key=self.api_key)
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
            prompt = prompt_loader.format('generators/transcript_generation.txt', context=params_str)
        else:
            prompt = prompt_loader.format('generators/transcript_generation.txt', context="general mortgage servicing topics")
        
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
        """Call OpenAI API using Responses API.

        Args:
            prompt: The prompt to send

        Returns:
            Response text
        """
        response = self.client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            temperature=0.7,
            max_output_tokens=1500
        )
        return response.output_text
    
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