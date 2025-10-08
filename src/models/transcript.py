"""Simple, flexible data models - no hardcoded logic."""
from typing import List, Any, Dict
import uuid


class Message:
    """Simple message in a conversation - completely flexible."""
    
    def __init__(self, speaker: str, text: str, **kwargs):
        """Store any message with any attributes.
        
        Args:
            speaker: Who said it (can be anyone)
            text: What they said
            **kwargs: Any additional attributes
        """
        self.speaker = speaker
        self.text = text
        
        # Store any additional attributes dynamically
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.__dict__
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create from dictionary."""
        return cls(**data)


class Transcript:
    """Simple transcript - just a conversation with any attributes."""
    
    def __init__(self, id: str = None, messages: List[Message] = None, **kwargs):
        """Store transcript with any attributes.
        
        Args:
            id: Unique identifier
            messages: List of Message objects
            **kwargs: Any additional attributes
        """
        self.id = id or str(uuid.uuid4())
        self.messages = messages or []
        
        # Store any additional attributes dynamically
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'id': self.id,
            'transcript_id': self.id,
            'messages': [msg.to_dict() for msg in self.messages]
        }
        
        # Add any other attributes
        for key, value in self.__dict__.items():
            if key not in ['id', 'messages']:
                result[key] = value
                
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transcript':
        """Create from dictionary."""
        messages = [Message.from_dict(msg_data) for msg_data in data.get('messages', [])]
        other_attrs = {k: v for k, v in data.items() if k not in ['id', 'messages']}
        return cls(id=data.get('id'), messages=messages, **other_attrs)
