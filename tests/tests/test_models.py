"""Tests for data models - flexible, agentic approach."""
import pytest
from datetime import datetime
from src.models.transcript import Transcript, Message


class TestMessage:
    """Test the Message data model."""
    
    def test_message_creation_with_required_fields(self):
        """Test creating a message with required fields."""
        message = Message(
            speaker="Advisor",
            text="Thank you for calling"
        )
        assert message.speaker == "Advisor"
        assert message.text == "Thank you for calling"
    
    def test_message_creation_with_any_attributes(self):
        """Test creating a message with any dynamic attributes."""
        message = Message(
            speaker="Customer",
            text="I'm frustrated about this notice",
            timestamp="2024-01-01T10:00:15Z",
            sentiment="frustrated",
            urgency="high",
            custom_field="value"
        )
        assert message.speaker == "Customer"
        assert message.text == "I'm frustrated about this notice"
        assert message.timestamp == "2024-01-01T10:00:15Z"
        assert message.sentiment == "frustrated"
        assert message.urgency == "high"
        assert message.custom_field == "value"
    
    def test_message_accepts_any_speaker(self):
        """Test that message accepts any speaker name."""
        message = Message(
            speaker="System",
            text="Call recording started"
        )
        assert message.speaker == "System"
    
    def test_message_to_dict(self):
        """Test message to_dict conversion."""
        message = Message(
            speaker="Advisor",
            text="Hello",
            timestamp="2024-01-01T10:00:00Z"
        )
        result = message.to_dict()
        assert result["speaker"] == "Advisor"
        assert result["text"] == "Hello"
        assert result["timestamp"] == "2024-01-01T10:00:00Z"
    
    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        data = {
            "speaker": "Customer",
            "text": "Hi there",
            "custom_attr": "test"
        }
        message = Message.from_dict(data)
        assert message.speaker == "Customer"
        assert message.text == "Hi there"
        assert message.custom_attr == "test"


class TestTranscript:
    """Test the Transcript model."""
    
    def test_transcript_creation_minimal(self):
        """Test creating a transcript with minimal fields."""
        transcript = Transcript()
        assert transcript.id is not None
        assert transcript.messages == []
    
    def test_transcript_creation_with_messages(self):
        """Test creating a transcript with messages."""
        messages = [
            Message("Advisor", "Hello"),
            Message("Customer", "Hi")
        ]
        
        transcript = Transcript(
            id="CALL_001",
            messages=messages
        )
        
        assert transcript.id == "CALL_001"
        assert len(transcript.messages) == 2
        assert transcript.messages[0].speaker == "Advisor"
        assert transcript.messages[1].speaker == "Customer"
    
    def test_transcript_with_dynamic_attributes(self):
        """Test transcript accepts any dynamic attributes."""
        transcript = Transcript(
            id="CALL_001",
            customer_id="CUST_123",
            advisor_id="ADV_456",
            timestamp="2024-01-01T10:00:00Z",
            topic="greeting",
            duration=300,
            sentiment="positive",
            custom_field="value"
        )
        
        assert transcript.id == "CALL_001"
        assert transcript.customer_id == "CUST_123"
        assert transcript.advisor_id == "ADV_456"
        assert transcript.timestamp == "2024-01-01T10:00:00Z"
        assert transcript.topic == "greeting"
        assert transcript.duration == 300
        assert transcript.sentiment == "positive"
        assert transcript.custom_field == "value"
    
    def test_transcript_to_dict(self):
        """Test converting transcript to dictionary."""
        messages = [
            Message("Advisor", "Hello"),
            Message("Customer", "Hi")
        ]
        
        transcript = Transcript(
            id="CALL_001",
            messages=messages,
            topic="greeting",
            duration=30
        )
        
        result = transcript.to_dict()
        
        assert result["id"] == "CALL_001"
        assert len(result["messages"]) == 2
        assert result["messages"][0]["speaker"] == "Advisor"
        assert result["topic"] == "greeting"
        assert result["duration"] == 30
    
    def test_transcript_from_dict(self):
        """Test creating transcript from dictionary."""
        data = {
            "id": "CALL_001",
            "messages": [
                {
                    "speaker": "Advisor",
                    "text": "Hello"
                }
            ],
            "topic": "greeting",
            "duration": 30
        }
        
        transcript = Transcript.from_dict(data)
        
        assert transcript.id == "CALL_001"
        assert len(transcript.messages) == 1
        assert transcript.messages[0].speaker == "Advisor"
        assert transcript.topic == "greeting"