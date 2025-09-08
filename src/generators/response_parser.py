"""Generic response parser - completely agentic approach."""
import json
from typing import Any, Dict, List
from src.models.transcript import Message


class ResponseParser:
    """Generic response parser - handles any format."""
    
    def parse_response(self, response: Any) -> Dict[str, Any]:
        """Parse response with minimal assumptions.
        
        Args:
            response: Any response from API
            
        Returns:
            Parsed data as dictionary
        """
        # Try to extract text content first
        text_content = self._extract_text(response)
        
        # Try to parse as JSON first
        try:
            if text_content and text_content.strip().startswith('{'):
                return json.loads(text_content)
        except:
            pass
        
        # If not JSON, parse as simple conversation
        if text_content:
            messages = self._parse_simple_conversation(text_content)
            return {"messages": messages, "raw_text": text_content}
        
        # Default: return as-is
        return {"content": str(response)}
    
    def _extract_text(self, response: Any) -> str:
        """Extract text from various response formats."""
        if isinstance(response, str):
            return response
        
        if isinstance(response, dict):
            # Handle different response formats
            if "output_text" in response:
                return response["output_text"]
            elif "output_parsed" in response:
                return str(response["output_parsed"])
            elif "choices" in response and response["choices"]:
                choice = response["choices"][0]
                if "text" in choice:
                    return choice["text"]
                elif "message" in choice and "content" in choice["message"]:
                    return choice["message"]["content"]
        
        return str(response)
    
    def _parse_simple_conversation(self, text: str) -> List[Dict[str, Any]]:
        """Parse conversation text into messages.
        
        Args:
            text: Raw conversation text
            
        Returns:
            List of message dictionaries
        """
        messages = []
        
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Look for "Speaker: Text" pattern (flexible speaker names)
            if ':' in line:
                speaker, message_text = line.split(':', 1)
                speaker = speaker.strip()
                message_text = message_text.strip()
                
                if speaker and message_text:
                    messages.append({
                        'speaker': speaker,
                        'text': message_text
                    })
        
        return messages