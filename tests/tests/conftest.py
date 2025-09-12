"""Test configuration and fixtures."""
import pytest
import sqlite3
from pathlib import Path
import tempfile
import os


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def sample_transcript_data():
    """Sample transcript data for testing."""
    return {
        'id': 'CALL_001',
        'customer_id': 'CUST_123',
        'advisor_id': 'ADV_456',
        'timestamp': '2024-01-01T10:00:00Z',
        'duration': 300,
        'topic': 'escrow_shortage',
        'messages': [
            {
                'speaker': 'Advisor',
                'text': 'Thank you for calling. How can I help you today?',
                'timestamp': '2024-01-01T10:00:00Z'
            },
            {
                'speaker': 'Customer',
                'text': 'I received a notice about an escrow shortage.',
                'timestamp': '2024-01-01T10:00:15Z'
            }
        ]
    }


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI Responses API response."""
    return {
        "choices": [{
            "text": """Advisor: Thank you for calling. How can I help you today?

Customer: I received a notice about an escrow shortage and I'm really confused about what this means.

Advisor: I understand your concern. Let me pull up your account and explain what's happening with your escrow account.

Customer: Okay, thank you. My loan number is 123456789.

Advisor: Perfect, I have your account here. The escrow shortage occurs when there isn't enough money in your escrow account to cover your property taxes and insurance.

Customer: So what does this mean for my monthly payment?

Advisor: Your payment will need to increase to cover the shortage and ensure we have enough for future payments. Would you like me to go over your options?""",
            "finish_reason": "stop"
        }]
    }