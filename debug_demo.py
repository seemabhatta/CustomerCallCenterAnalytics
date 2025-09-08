#!/usr/bin/env python3
"""Debug demo to see what's being generated."""
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.generators.transcript_generator import TranscriptGenerator

def main():
    generator = TranscriptGenerator()
    
    try:
        print("Generating transcript...")
        transcript = generator.generate(scenario="escrow_shortage", sentiment="confused")
        
        print(f"Generated transcript: {transcript.id}")
        print(f"Messages: {len(transcript.messages)}")
        if hasattr(transcript, 'topic'):
            print(f"Topic: {transcript.topic}")
        
        if transcript.messages:
            print("Sample messages:")
            for i, msg in enumerate(transcript.messages[:3]):
                print(f"  {i+1}. {msg.speaker}: {msg.text}")
        else:
            print("No messages found - checking parsing...")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()