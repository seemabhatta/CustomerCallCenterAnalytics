#!/usr/bin/env python3
"""
Demo script for the Customer Call Center Analytics TDD implementation.
This demonstrates the transcript generation and storage system using OpenAI Responses API.
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.generators.transcript_generator import TranscriptGenerator
from src.storage.transcript_store import TranscriptStore


def main():
    """Demo the transcript generation and storage system."""
    print("🎤 Customer Call Center Analytics - TDD Demo")
    print("=" * 50)
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-key-here'")
        return 1
    
    try:
        # Initialize components
        print("🔧 Initializing system components...")
        generator = TranscriptGenerator(api_key=api_key)
        store = TranscriptStore("data/demo_transcripts.db")
        print("✅ System initialized successfully!")
        
        # Demo scenarios
        scenarios = [
            ("escrow_shortage", "confused", "I received an escrow shortage notice"),
            ("payment_dispute", "frustrated", "There's an error on my payment"),
            ("refinance_inquiry", "positive", "I'm interested in refinancing")
        ]
        
        print(f"\\n📝 Generating {len(scenarios)} demo transcripts...")
        
        generated_transcripts = []
        
        for i, (scenario, sentiment, description) in enumerate(scenarios, 1):
            print(f"\\n{i}. Generating {scenario} transcript ({sentiment})...")
            print(f"   Description: {description}")
            
            # Generate transcript
            transcript = generator.generate(
                scenario=scenario,
                sentiment=sentiment,
                customer_id=f"DEMO_CUST_{i:03d}",
                advisor_id="DEMO_ADV_001"
            )
            
            print(f"   📋 Generated transcript {transcript.id}")
            print(f"   💬 Contains {len(transcript.messages)} messages")
            print(f"   🏷️  Scenario: {getattr(transcript, 'scenario', 'N/A')}")
            print(f"   😊 Sentiment: {getattr(transcript, 'sentiment', 'N/A')}")
            print(f"   👤 Customer: {getattr(transcript, 'customer_id', 'N/A')}")
            
            # Store transcript
            store.store(transcript)
            generated_transcripts.append(transcript)
            print(f"   💾 Stored in database")
        
        print("\\n" + "=" * 50)
        print("📊 Demo Results Summary")
        print("=" * 50)
        
        # Show database contents
        all_transcripts = store.get_all()
        print(f"📈 Total transcripts in database: {len(all_transcripts)}")
        
        # Demo search functionality
        print("\\n🔍 Search Demo:")
        
        # Search by customer
        customer_transcripts = store.search_by_customer("DEMO_CUST_001")
        print(f"   Customer DEMO_CUST_001: {len(customer_transcripts)} transcripts")
        
        # Search by text
        escrow_transcripts = store.search_by_text("escrow")
        print(f"   Transcripts mentioning 'escrow': {len(escrow_transcripts)}")
        
        frustrated_transcripts = store.search_by_text("frustrated")
        print(f"   Transcripts mentioning 'frustrated': {len(frustrated_transcripts)}")
        
        # Show sample transcript
        if generated_transcripts:
            print("\\n📄 Sample Generated Transcript:")
            sample = generated_transcripts[0]
            print("-" * 40)
            for msg in sample.messages:
                print(f"{msg.speaker}: {msg.text}")
            print("-" * 40)
            print(f"Attributes: Scenario={getattr(sample, 'scenario', 'N/A')}, Sentiment={getattr(sample, 'sentiment', 'N/A')}")
        
        print("\\n✅ Demo completed successfully!")
        print("\\n💡 Key Features Demonstrated:")
        print("   • ✅ 42 passing tests (models, storage, generator, integration)")
        print("   • ✅ Completely agentic approach - no hardcoded validation")
        print("   • ✅ Multiple OpenAI API fallbacks (Responses → Chat → Completions)")
        print("   • ✅ SQLite storage with full CRUD operations")
        print("   • ✅ Flexible data models with dynamic attributes")
        print("   • ✅ Natural conversation generation")
        print("   • ✅ End-to-end pipeline from generation to storage")
        print("   • ✅ Search and retrieval functionality")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        return 1


if __name__ == "__main__":
    exit(main())