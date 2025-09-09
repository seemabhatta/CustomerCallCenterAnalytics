"""SQLite storage layer for transcripts."""
import sqlite3
import json
from typing import List, Optional

from src.models.transcript import Transcript, Message


class TranscriptStore:
    """SQLite-based storage for transcripts."""
    
    def __init__(self, db_path: str):
        """Initialize the store with database path.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create transcripts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcripts (
                id TEXT PRIMARY KEY,
                customer_id TEXT NOT NULL,
                advisor_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                topic TEXT NOT NULL,
                duration INTEGER NOT NULL,
                sentiment TEXT,  -- Optional, can be NULL
                urgency TEXT,   -- Optional, can be NULL
                compliance_flags TEXT,  -- JSON array
                outcome TEXT
            )
        ''')
        
        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transcript_id TEXT NOT NULL,
                speaker TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                sentiment TEXT,
                FOREIGN KEY (transcript_id) REFERENCES transcripts (id)
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_customer_id ON transcripts (customer_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_topic ON transcripts (topic)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transcript_id ON messages (transcript_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_text ON messages (text)')
        
        conn.commit()
        conn.close()
    
    def store(self, transcript: Transcript):
        """Store a transcript.
        
        Args:
            transcript: Transcript object to store
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Store transcript metadata - use getattr for dynamic attributes
            cursor.execute('''
                INSERT OR REPLACE INTO transcripts 
                (id, customer_id, advisor_id, timestamp, topic, duration, 
                 sentiment, urgency, compliance_flags, outcome)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                transcript.id,
                getattr(transcript, 'customer_id', ''),
                getattr(transcript, 'advisor_id', ''),
                getattr(transcript, 'timestamp', ''),
                getattr(transcript, 'topic', ''),
                getattr(transcript, 'duration', 0),
                getattr(transcript, 'sentiment', None),
                getattr(transcript, 'urgency', None),
                json.dumps(getattr(transcript, 'compliance_flags', [])),
                getattr(transcript, 'outcome', None)
            ))
            
            # Delete existing messages for this transcript (for updates)
            cursor.execute('DELETE FROM messages WHERE transcript_id = ?', (transcript.id,))
            
            # Store messages
            for message in transcript.messages:
                cursor.execute('''
                    INSERT INTO messages 
                    (transcript_id, speaker, text, timestamp, sentiment)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    transcript.id,
                    message.speaker,
                    message.text,
                    getattr(message, 'timestamp', ''),
                    getattr(message, 'sentiment', None)
                ))
            
            conn.commit()
            return transcript.id
        
        finally:
            conn.close()
    
    def get_by_id(self, transcript_id: str) -> Optional[Transcript]:
        """Get transcript by ID.
        
        Args:
            transcript_id: Transcript ID
            
        Returns:
            Transcript object or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get transcript metadata
            cursor.execute('''
                SELECT id, customer_id, advisor_id, timestamp, topic, duration,
                       sentiment, urgency, compliance_flags, outcome
                FROM transcripts WHERE id = ?
            ''', (transcript_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Get messages
            cursor.execute('''
                SELECT speaker, text, timestamp, sentiment
                FROM messages WHERE transcript_id = ?
                ORDER BY id
            ''', (transcript_id,))
            
            message_rows = cursor.fetchall()
            
            # Build objects using simplified models
            messages = [
                Message(
                    speaker=msg_row[0],
                    text=msg_row[1],
                    timestamp=msg_row[2] if msg_row[2] else '',
                    sentiment=msg_row[3] if msg_row[3] else None
                )
                for msg_row in message_rows
            ]
            
            # Build transcript with only provided attributes
            transcript_kwargs = {
                'id': row[0],
                'messages': messages,
                'customer_id': row[1] if row[1] else '',
                'advisor_id': row[2] if row[2] else '',
                'timestamp': row[3] if row[3] else '',
                'topic': row[4] if row[4] else '',
                'duration': row[5] if row[5] else 0,
                'compliance_flags': json.loads(row[8]) if row[8] else [],
                'outcome': row[9] if row[9] else None
            }
            
            # Only add sentiment and urgency if they have values
            if row[6]:  # sentiment
                transcript_kwargs['sentiment'] = row[6]
            if row[7]:  # urgency  
                transcript_kwargs['urgency'] = row[7]
                
            transcript = Transcript(**transcript_kwargs)
            
            return transcript
        
        finally:
            conn.close()
    
    def search_by_customer(self, customer_id: str) -> List[Transcript]:
        """Search transcripts by customer ID.
        
        Args:
            customer_id: Customer ID
            
        Returns:
            List of matching transcripts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM transcripts WHERE customer_id = ?', (customer_id,))
            transcript_ids = [row[0] for row in cursor.fetchall()]
            
            return [self.get_by_id(tid) for tid in transcript_ids if self.get_by_id(tid)]
        
        finally:
            conn.close()
    
    def search_by_topic(self, topic: str) -> List[Transcript]:
        """Search transcripts by topic.
        
        Args:
            topic: Topic to search for
            
        Returns:
            List of matching transcripts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM transcripts WHERE topic = ?', (topic,))
            transcript_ids = [row[0] for row in cursor.fetchall()]
            
            return [self.get_by_id(tid) for tid in transcript_ids if self.get_by_id(tid)]
        
        finally:
            conn.close()
    
    def search_by_text(self, search_term: str) -> List[Transcript]:
        """Search transcripts by message text content.
        
        Args:
            search_term: Term to search for in message text
            
        Returns:
            List of matching transcripts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT DISTINCT transcript_id 
                FROM messages 
                WHERE text LIKE ?
            ''', (f'%{search_term}%',))
            
            transcript_ids = [row[0] for row in cursor.fetchall()]
            
            return [self.get_by_id(tid) for tid in transcript_ids if self.get_by_id(tid)]
        
        finally:
            conn.close()
    
    def get_all(self) -> List[Transcript]:
        """Get all transcripts.
        
        Returns:
            List of all transcripts
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT id FROM transcripts ORDER BY timestamp')
            transcript_ids = [row[0] for row in cursor.fetchall()]
            
            return [self.get_by_id(tid) for tid in transcript_ids if self.get_by_id(tid)]
        
        finally:
            conn.close()
    
    def delete(self, transcript_id: str):
        """Delete a transcript.
        
        Args:
            transcript_id: ID of transcript to delete
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Check if transcript exists first
            cursor.execute('SELECT id FROM transcripts WHERE id = ?', (transcript_id,))
            if cursor.fetchone():
                cursor.execute('DELETE FROM messages WHERE transcript_id = ?', (transcript_id,))
                cursor.execute('DELETE FROM transcripts WHERE id = ?', (transcript_id,))
                conn.commit()
                return transcript_id
            else:
                return None
        
        finally:
            conn.close()
    
    def update(self, transcript: Transcript):
        """Update an existing transcript.
        
        Args:
            transcript: Updated transcript object
        """
        # For now, update is the same as store (INSERT OR REPLACE)
        return self.store(transcript)
    
    def delete_all(self):
        """Delete all transcripts from the database.
        
        Returns:
            Number of transcripts deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get count before deletion
            cursor.execute('SELECT COUNT(*) FROM transcripts')
            count = cursor.fetchone()[0]
            
            # Delete all messages first (foreign key constraint)
            cursor.execute('DELETE FROM messages')
            
            # Delete all transcripts
            cursor.execute('DELETE FROM transcripts')
            
            conn.commit()
            return count
        
        finally:
            conn.close()