from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class Speaker(str, Enum):
    """Speaker types in a call."""
    ADVISOR = "advisor"
    CUSTOMER = "customer"
    SUPERVISOR = "supervisor"
    SYSTEM = "system"

class CallPhase(str, Enum):
    """Phases of a customer service call."""
    INTRO = "intro"
    VERIFICATION = "verification"
    ISSUE_DISCUSSION = "issue_discussion"
    RESOLUTION = "resolution"
    WRAP_UP = "wrap_up"

class TranscriptSegment(BaseModel):
    """A single segment of the transcript."""
    speaker: Speaker
    text: str
    timestamp: float = Field(description="Timestamp in seconds from call start")
    confidence: Optional[float] = Field(None, description="Confidence score for transcription")
    phase: Optional[CallPhase] = None

class CustomerProfile(BaseModel):
    """Customer profile information."""
    customer_id: str
    name: str
    loan_number: Optional[str] = None
    account_status: str = "active"
    phone: Optional[str] = None
    email: Optional[str] = None

class AdvisorProfile(BaseModel):
    """Advisor profile information."""
    advisor_id: str
    name: str
    department: str = "loan_servicing"
    experience_level: str = "experienced"  # "new", "experienced", "senior"

class CallMetadata(BaseModel):
    """Metadata about the call."""
    call_id: str
    duration_seconds: int
    call_date: datetime
    call_type: str  # "inbound", "outbound"
    queue_time_seconds: Optional[int] = None
    hold_time_seconds: Optional[int] = 0
    transfer_count: int = 0
    resolution_status: str = "resolved"  # "resolved", "pending", "escalated"

class CallTranscript(BaseModel):
    """Complete call transcript with metadata."""
    transcript_id: str
    call_metadata: CallMetadata
    customer: CustomerProfile
    advisor: AdvisorProfile
    segments: List[TranscriptSegment]
    tags: List[str] = Field(default_factory=list)
    scenario: str  # The scenario type used for generation
    created_at: datetime = Field(default_factory=datetime.now)
    
    @property
    def full_text(self) -> str:
        """Get the full transcript as a single string."""
        lines = []
        for segment in self.segments:
            lines.append(f"{segment.speaker.value.title()}: {segment.text}")
        return "\n".join(lines)
    
    @property
    def customer_segments(self) -> List[TranscriptSegment]:
        """Get only customer segments."""
        return [s for s in self.segments if s.speaker == Speaker.CUSTOMER]
    
    @property
    def advisor_segments(self) -> List[TranscriptSegment]:
        """Get only advisor segments."""
        return [s for s in self.segments if s.speaker == Speaker.ADVISOR]