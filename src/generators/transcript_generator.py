import re
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
from openai import OpenAI

from ..config.settings import settings
from ..models.transcript import (
    CallTranscript, CallMetadata, CustomerProfile, AdvisorProfile,
    TranscriptSegment, Speaker, CallPhase
)

class TranscriptGenerator:
    """Generate realistic call center transcripts using OpenAI."""
    
    def __init__(self):
        settings.validate()
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.scenarios = self._load_scenarios()
        
    def _load_scenarios(self) -> Dict[str, str]:
        """Load scenario prompts from files."""
        scenarios = {}
        prompts_dir = Path(settings.PROMPTS_DIR)
        
        for scenario_file in prompts_dir.glob("*_scenario.txt"):
            scenario_name = scenario_file.stem.replace("_scenario", "")
            with open(scenario_file, 'r') as f:
                scenarios[scenario_name] = f.read().strip()
                
        return scenarios
    
    def generate_transcript(self, scenario: str = "hardship", **kwargs) -> CallTranscript:
        """Generate a complete call transcript for the given scenario."""
        
        if scenario not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario}. Available: {list(self.scenarios.keys())}")
        
        # Generate the raw transcript text
        raw_transcript = self._generate_raw_transcript(scenario)
        
        # Parse into structured segments
        segments = self._parse_transcript(raw_transcript)
        
        # Generate metadata
        call_metadata = self._generate_call_metadata(scenario, len(segments))
        customer = self._generate_customer_profile()
        advisor = self._generate_advisor_profile()
        
        return CallTranscript(
            transcript_id=str(uuid.uuid4()),
            call_metadata=call_metadata,
            customer=customer,
            advisor=advisor,
            segments=segments,
            scenario=scenario,
            tags=self._generate_tags(scenario, raw_transcript)
        )
    
    def _generate_raw_transcript(self, scenario: str) -> str:
        """Generate raw transcript text using OpenAI."""
        
        system_prompt = """You are an expert at creating realistic customer service call transcripts. 
        Generate a natural, realistic conversation that includes:
        - Natural speech patterns, hesitations, and interruptions
        - Realistic customer emotions and advisor professionalism
        - Specific numbers, dates, and account details
        - Compliance language where appropriate
        - Proper call flow and pacing
        
        Format as:
        Advisor: [dialogue]
        Customer: [dialogue]
        
        Make it feel like a real recorded call transcript."""
        
        user_prompt = self.scenarios[scenario]
        
        response = self.client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[
                {"role": "system", "content": [{"type": "input_text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "input_text", "text": user_prompt}]},
            ],
            temperature=0.8,
            max_output_tokens=3000,
        )

        return response.output_text
    
    def _parse_transcript(self, raw_transcript: str) -> List[TranscriptSegment]:
        """Parse raw transcript text into structured segments."""
        segments = []
        lines = raw_transcript.strip().split('\n')
        current_timestamp = 0.0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse speaker and text
            if ':' in line:
                speaker_text, dialogue = line.split(':', 1)
                speaker_text = speaker_text.strip().lower()
                dialogue = dialogue.strip()
                
                # Map speaker names to enum values
                if 'advisor' in speaker_text or 'agent' in speaker_text:
                    speaker = Speaker.ADVISOR
                elif 'customer' in speaker_text or 'caller' in speaker_text:
                    speaker = Speaker.CUSTOMER
                elif 'supervisor' in speaker_text:
                    speaker = Speaker.SUPERVISOR
                else:
                    speaker = Speaker.ADVISOR  # Default
                
                # Estimate timestamp based on dialogue length
                words = len(dialogue.split())
                duration = words / 150 * 60  # Assume 150 words per minute
                
                segments.append(TranscriptSegment(
                    speaker=speaker,
                    text=dialogue,
                    timestamp=current_timestamp,
                    confidence=random.uniform(0.85, 0.98),
                    phase=self._determine_phase(len(segments), dialogue)
                ))
                
                current_timestamp += duration + random.uniform(0.5, 2.0)  # Add pause
        
        return segments
    
    def _determine_phase(self, segment_index: int, text: str) -> CallPhase:
        """Determine call phase based on position and content."""
        text_lower = text.lower()
        
        if segment_index < 3:
            return CallPhase.INTRO
        elif any(word in text_lower for word in ['verify', 'confirm', 'last four', 'address']):
            return CallPhase.VERIFICATION
        elif any(word in text_lower for word in ['thank you', 'goodbye', 'follow up', 'next steps']):
            return CallPhase.WRAP_UP
        elif any(word in text_lower for word in ['solution', 'option', 'recommend', 'process']):
            return CallPhase.RESOLUTION
        else:
            return CallPhase.ISSUE_DISCUSSION
    
    def _generate_call_metadata(self, scenario: str, segment_count: int) -> CallMetadata:
        """Generate realistic call metadata."""
        base_duration = random.randint(8, 25) * 60  # 8-25 minutes in seconds
        call_date = datetime.now() - timedelta(days=random.randint(0, 30))
        
        return CallMetadata(
            call_id=f"CALL_{datetime.now().strftime('%Y%m%d')}_{random.randint(1000, 9999)}",
            duration_seconds=base_duration,
            call_date=call_date,
            call_type="inbound",
            queue_time_seconds=random.randint(30, 300),
            hold_time_seconds=random.randint(0, 180),
            transfer_count=0 if scenario != "escalation" else random.randint(1, 2),
            resolution_status=random.choices(
                ["resolved", "pending", "escalated"], 
                weights=[0.7, 0.2, 0.1]
            )[0]
        )
    
    def _generate_customer_profile(self) -> CustomerProfile:
        """Generate a realistic customer profile."""
        first_names = ["John", "Mary", "Robert", "Patricia", "Michael", "Jennifer", "William", "Linda"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        return CustomerProfile(
            customer_id=f"CUST_{random.randint(100000, 999999)}",
            name=f"{first_name} {last_name}",
            loan_number=f"{random.randint(100000000, 999999999)}",
            account_status=random.choices(
                ["current", "30_days_past_due", "60_days_past_due", "90_days_past_due"],
                weights=[0.6, 0.2, 0.1, 0.1]
            )[0],
            phone=f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            email=f"{first_name.lower()}.{last_name.lower()}@email.com"
        )
    
    def _generate_advisor_profile(self) -> AdvisorProfile:
        """Generate a realistic advisor profile."""
        advisor_names = ["Sarah Wilson", "Mike Johnson", "Lisa Chen", "David Martinez", "Emily Rodriguez"]
        
        return AdvisorProfile(
            advisor_id=f"ADV_{random.randint(1000, 9999)}",
            name=random.choice(advisor_names),
            department="loan_servicing",
            experience_level=random.choices(
                ["new", "experienced", "senior"],
                weights=[0.2, 0.6, 0.2]
            )[0]
        )
    
    def _generate_tags(self, scenario: str, transcript_text: str) -> List[str]:
        """Generate relevant tags based on scenario and content."""
        tags = [scenario]
        
        text_lower = transcript_text.lower()
        
        # Add content-based tags
        tag_keywords = {
            "payment_issue": ["payment", "past due", "missed", "behind"],
            "escrow": ["escrow", "taxes", "insurance", "analysis"],
            "hardship": ["hardship", "financial difficulty", "unemployment", "medical"],
            "refinance": ["refinance", "refi", "rate", "lower payment"],
            "complaint": ["complaint", "unhappy", "frustrated", "problem"],
            "escalation": ["supervisor", "manager", "escalate"],
            "resolved": ["resolved", "fixed", "solved", "taken care of"],
            "follow_up_required": ["follow up", "call back", "pending", "review"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return list(set(tags))  # Remove duplicates
    
    def get_available_scenarios(self) -> List[str]:
        """Get list of available scenario types."""
        return list(self.scenarios.keys())
