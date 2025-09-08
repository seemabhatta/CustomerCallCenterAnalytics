"""Tests for SQLite storage layer - simplified approach."""
import pytest
import sqlite3
import tempfile
import os
from src.storage.transcript_store import TranscriptStore
from src.models.transcript import Transcript, Message


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    yield path
    os.unlink(path)


@pytest.fixture
def sample_transcript():
    """Create a sample transcript for testing."""
    messages = [
        Message("Advisor", "Hello, how can I help you?", timestamp="2024-01-01T10:00:00Z"),
        Message("Customer", "I have a question about my loan", timestamp="2024-01-01T10:00:15Z")
    ]
    
    return Transcript(
        id="CALL_001",
        messages=messages,
        customer_id="CUST_123",
        advisor_id="ADV_456",
        timestamp="2024-01-01T10:00:00Z",
        topic="loan_inquiry",
        duration=300
    )


class TestTranscriptStore:
    """Test the SQLite transcript storage layer."""
    
    def test_store_initialization(self, temp_db):
        """Test that store initializes and creates tables."""
        store = TranscriptStore(temp_db)
        
        # Check that database file was created
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check that tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'transcripts' in tables
        assert 'messages' in tables
        
        conn.close()
    
    def test_store_transcript(self, temp_db, sample_transcript):
        """Test storing a transcript."""
        store = TranscriptStore(temp_db)
        
        # Store the transcript
        result = store.store(sample_transcript)
        
        assert result == sample_transcript.id
    
    def test_get_transcript_by_id(self, temp_db, sample_transcript):
        """Test retrieving a transcript by ID."""
        store = TranscriptStore(temp_db)
        
        # Store first
        store.store(sample_transcript)
        
        # Retrieve
        retrieved = store.get_by_id(sample_transcript.id)
        
        assert retrieved is not None
        assert retrieved.id == sample_transcript.id
        assert len(retrieved.messages) == len(sample_transcript.messages)
        assert retrieved.customer_id == sample_transcript.customer_id
    
    def test_get_nonexistent_transcript(self, temp_db):
        """Test retrieving a non-existent transcript returns None."""
        store = TranscriptStore(temp_db)
        
        result = store.get_by_id("NONEXISTENT")
        
        assert result is None
    
    def test_list_transcripts_empty(self, temp_db):
        """Test listing transcripts when database is empty."""
        store = TranscriptStore(temp_db)
        
        transcripts = store.get_all()
        
        assert transcripts == []
    
    def test_list_transcripts_with_data(self, temp_db, sample_transcript):
        """Test listing transcripts with data."""
        store = TranscriptStore(temp_db)
        
        # Store transcript
        store.store(sample_transcript)
        
        # List transcripts
        transcripts = store.get_all()
        
        assert len(transcripts) == 1
        assert transcripts[0].id == sample_transcript.id
    
    def test_update_transcript(self, temp_db, sample_transcript):
        """Test updating a transcript."""
        store = TranscriptStore(temp_db)
        
        # Store original
        store.store(sample_transcript)
        
        # Modify transcript
        sample_transcript.topic = "updated_topic"
        sample_transcript.sentiment = "positive"
        
        # Update
        result = store.update(sample_transcript)
        
        assert result == sample_transcript.id
        
        # Retrieve and verify
        retrieved = store.get_by_id(sample_transcript.id)
        assert retrieved.topic == "updated_topic"
        assert retrieved.sentiment == "positive"
    
    def test_delete_transcript(self, temp_db, sample_transcript):
        """Test deleting a transcript."""
        store = TranscriptStore(temp_db)
        
        # Store first
        store.store(sample_transcript)
        
        # Verify it exists
        assert store.get_by_id(sample_transcript.id) is not None
        
        # Delete
        result = store.delete(sample_transcript.id)
        
        assert result == sample_transcript.id
        
        # Verify it's gone
        assert store.get_by_id(sample_transcript.id) is None
    
    def test_delete_nonexistent_transcript(self, temp_db):
        """Test deleting a non-existent transcript."""
        store = TranscriptStore(temp_db)
        
        result = store.delete("NONEXISTENT")
        
        # The method should still work, just return None for non-existent
        assert result is None
    
    def test_search_transcripts_by_customer(self, temp_db):
        """Test searching transcripts by customer ID."""
        store = TranscriptStore(temp_db)
        
        # Create multiple transcripts
        transcript1 = Transcript(id="CALL_001", customer_id="CUST_123", messages=[])
        transcript2 = Transcript(id="CALL_002", customer_id="CUST_456", messages=[])
        transcript3 = Transcript(id="CALL_003", customer_id="CUST_123", messages=[])
        
        # Store all
        store.store(transcript1)
        store.store(transcript2)
        store.store(transcript3)
        
        # Search by customer
        results = store.search_by_customer("CUST_123")
        
        assert len(results) == 2
        customer_ids = [t.customer_id for t in results]
        assert all(cid == "CUST_123" for cid in customer_ids)
    
    def test_transcript_basic_attributes_preserved(self, temp_db):
        """Test that basic transcript attributes are stored and retrieved."""
        store = TranscriptStore(temp_db)
        
        # Create transcript with known attributes
        transcript = Transcript(
            id="CALL_BASIC",
            messages=[Message("Agent", "Test message")],
            customer_id="CUST_999",
            topic="test_topic",
            duration=150
        )
        
        # Store
        store.store(transcript)
        
        # Retrieve
        retrieved = store.get_by_id("CALL_BASIC")
        
        # Verify basic attributes
        assert retrieved.customer_id == "CUST_999"
        assert retrieved.topic == "test_topic"
        assert retrieved.duration == 150
        assert len(retrieved.messages) == 1
        assert retrieved.messages[0].speaker == "Agent"