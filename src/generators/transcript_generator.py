"""Simple transcript generator - just natural conversations."""
import os
import uuid
from typing import Optional
from datetime import datetime
import openai
from dotenv import load_dotenv
from src.models.transcript import Transcript, Message
from src.generators.prompt_builder import PromptBuilder
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
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser()
    
    def generate(self, **context) -> Transcript:
        """Generate a natural conversation transcript.
        
        Args:
            **context: Any context parameters for the conversation
            
        Returns:
            Generated Transcript object
        """
        # Build simple prompt
        prompt = self.prompt_builder.build_prompt(**context)
        
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
        """Call OpenAI API - try different methods until one works.
        
        Args:
            prompt: The prompt to send
            
        Returns:
            Response text
        """
        # Try Responses API first (if available)
        if hasattr(self.client, 'responses'):
            try:
                response = self.client.responses.create(
                    model="gpt-4o-mini",
                    input=prompt,
                    temperature=0.7,
                    max_output_tokens=1500
                )
                return response
            except:
                pass  # Fall through to next method
        
        # Fallback to Chat Completions
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            return response.choices[0].message.content
        except:
            pass
        
        # Last resort: Completions API
        try:
            response = self.client.completions.create(
                model="gpt-3.5-turbo-instruct",
                prompt=prompt,
                temperature=0.7,
                max_tokens=1500
            )
            return response.choices[0].text
        except Exception as e:
            raise Exception(f"All API methods failed: {str(e)}")
    
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
                print(f"Error generating transcript {i+1}: {e}")
                continue
        
        return transcripts