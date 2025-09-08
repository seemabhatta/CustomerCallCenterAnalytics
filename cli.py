#!/usr/bin/env python3
"""
Customer Call Center Analytics - CLI Tool
Comprehensive command-line interface for the agentic transcript generation system.
"""
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.generators.transcript_generator import TranscriptGenerator
from src.storage.transcript_store import TranscriptStore

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{text}{Colors.ENDC}")
    print("=" * len(text))

def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    """Print info message."""
    print(f"{Colors.CYAN}💡 {text}{Colors.ENDC}")

def init_system():
    """Initialize the transcript generation system."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print_error("OPENAI_API_KEY not found in environment")
            print_info("Please set your OpenAI API key in .env file or environment")
            sys.exit(1)
        
        generator = TranscriptGenerator(api_key=api_key)
        
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        store = TranscriptStore("data/call_center.db")
        return generator, store
        
    except Exception as e:
        print_error(f"Failed to initialize system: {e}")
        sys.exit(1)

def parse_key_value_args(args):
    """Parse key=value arguments into a dictionary."""
    kwargs = {}
    for arg in args:
        if '=' in arg:
            key, value = arg.split('=', 1)
            # Try to parse as JSON, fallback to string
            try:
                kwargs[key] = json.loads(value)
            except:
                kwargs[key] = value
        else:
            print_error(f"Invalid argument format: {arg}. Use key=value format.")
    return kwargs

def format_transcript_summary(transcript):
    """Format a transcript for list display."""
    messages_count = len(transcript.messages)
    speaker_preview = transcript.messages[0].speaker if transcript.messages else "No messages"
    
    # Get some attributes that might exist
    customer_id = getattr(transcript, 'customer_id', 'N/A')
    topic = getattr(transcript, 'topic', getattr(transcript, 'scenario', 'N/A'))
    sentiment = getattr(transcript, 'sentiment', 'N/A')
    
    return f"{Colors.BOLD}{transcript.id}{Colors.ENDC} | {customer_id} | {topic} | {sentiment} | {messages_count} msgs | {speaker_preview}..."

def format_transcript_detail(transcript):
    """Format a transcript for detailed display."""
    print(f"\n{Colors.BOLD}Transcript ID:{Colors.ENDC} {transcript.id}")
    
    # Show all attributes except id and messages
    print(f"{Colors.BOLD}Attributes:{Colors.ENDC}")
    for key, value in transcript.__dict__.items():
        if key not in ['id', 'messages']:
            print(f"  {key}: {value}")
    
    print(f"\n{Colors.BOLD}Messages ({len(transcript.messages)}):{Colors.ENDC}")
    for i, msg in enumerate(transcript.messages, 1):
        speaker_color = Colors.CYAN if 'customer' in msg.speaker.lower() else Colors.GREEN
        print(f"  {i}. {speaker_color}{msg.speaker}:{Colors.ENDC} {msg.text}")
        
        # Show message attributes if any
        msg_attrs = {k: v for k, v in msg.__dict__.items() if k not in ['speaker', 'text']}
        if msg_attrs:
            for key, value in msg_attrs.items():
                print(f"     └─ {key}: {value}")

def cmd_generate(args):
    """Generate new transcript(s)."""
    generator, store = init_system()
    
    print_header("🎤 Generating Transcripts")
    
    # Parse additional parameters
    kwargs = parse_key_value_args(args.params)
    
    # Add count if specified
    count = getattr(args, 'count', 1)
    
    try:
        if count == 1:
            print("Generating transcript...")
            transcript = generator.generate(**kwargs)
            print_success(f"Generated transcript: {transcript.id}")
            
            if args.store:
                store.store(transcript)
                print_success("Stored in database")
            
            if args.show:
                format_transcript_detail(transcript)
                
        else:
            print(f"Generating {count} transcripts...")
            transcripts = generator.generate_batch(count, **kwargs)
            print_success(f"Generated {len(transcripts)} transcripts")
            
            if args.store:
                for transcript in transcripts:
                    store.store(transcript)
                print_success(f"Stored {len(transcripts)} transcripts in database")
            
            if args.show:
                for transcript in transcripts:
                    format_transcript_detail(transcript)
                    
    except Exception as e:
        print_error(f"Generation failed: {e}")
        sys.exit(1)

def cmd_list(args):
    """List all transcripts."""
    _, store = init_system()
    
    print_header("📋 All Transcripts")
    
    try:
        transcripts = store.get_all()
        
        if not transcripts:
            print_info("No transcripts found in database")
            return
        
        print(f"Found {len(transcripts)} transcript(s):\n")
        
        for transcript in transcripts:
            print(format_transcript_summary(transcript))
            
        if args.detailed:
            print("\n" + "="*50)
            for transcript in transcripts:
                format_transcript_detail(transcript)
                print("-" * 40)
                
    except Exception as e:
        print_error(f"Failed to list transcripts: {e}")

def cmd_get(args):
    """Get a specific transcript by ID."""
    _, store = init_system()
    
    print_header(f"📄 Transcript: {args.transcript_id}")
    
    try:
        transcript = store.get_by_id(args.transcript_id)
        
        if not transcript:
            print_error(f"Transcript {args.transcript_id} not found")
            return
        
        format_transcript_detail(transcript)
        
        if args.export:
            filename = f"{args.transcript_id}.json"
            with open(filename, 'w') as f:
                json.dump(transcript.to_dict(), f, indent=2)
            print_success(f"Exported to {filename}")
            
    except Exception as e:
        print_error(f"Failed to get transcript: {e}")

def cmd_search(args):
    """Search transcripts."""
    _, store = init_system()
    
    print_header("🔍 Search Results")
    
    try:
        results = []
        
        if args.customer:
            results = store.search_by_customer(args.customer)
            print(f"Searching for customer: {args.customer}")
            
        elif args.topic:
            results = store.search_by_topic(args.topic)
            print(f"Searching for topic: {args.topic}")
            
        elif args.text:
            results = store.search_by_text(args.text)
            print(f"Searching for text: {args.text}")
            
        else:
            print_error("Please specify --customer, --topic, or --text")
            return
        
        if not results:
            print_info("No transcripts found matching criteria")
            return
        
        print(f"\nFound {len(results)} transcript(s):")
        
        for transcript in results:
            print(format_transcript_summary(transcript))
            
        if args.detailed:
            print("\n" + "="*50)
            for transcript in results:
                format_transcript_detail(transcript)
                print("-" * 40)
                
    except Exception as e:
        print_error(f"Search failed: {e}")

def cmd_delete(args):
    """Delete a transcript."""
    _, store = init_system()
    
    try:
        # Check if transcript exists first
        transcript = store.get_by_id(args.transcript_id)
        if not transcript:
            print_error(f"Transcript {args.transcript_id} not found")
            return
        
        if not args.force:
            print(f"Are you sure you want to delete transcript {args.transcript_id}?")
            confirm = input("Type 'yes' to confirm: ").strip().lower()
            if confirm != 'yes':
                print_info("Delete cancelled")
                return
        
        result = store.delete(args.transcript_id)
        if result:
            print_success(f"Deleted transcript {args.transcript_id}")
        else:
            print_error("Failed to delete transcript")
            
    except Exception as e:
        print_error(f"Delete failed: {e}")

def cmd_stats(args):
    """Show statistics about stored transcripts."""
    _, store = init_system()
    
    print_header("📊 Database Statistics")
    
    try:
        transcripts = store.get_all()
        
        if not transcripts:
            print_info("No transcripts in database")
            return
        
        total = len(transcripts)
        total_messages = sum(len(t.messages) for t in transcripts)
        
        # Collect statistics
        speakers = {}
        customers = set()
        topics = {}
        sentiments = {}
        
        for transcript in transcripts:
            # Customer IDs
            if hasattr(transcript, 'customer_id'):
                customers.add(transcript.customer_id)
            
            # Topics/scenarios
            topic = getattr(transcript, 'topic', getattr(transcript, 'scenario', 'Unknown'))
            topics[topic] = topics.get(topic, 0) + 1
            
            # Sentiments
            sentiment = getattr(transcript, 'sentiment', 'Unknown')
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            # Speakers
            for msg in transcript.messages:
                speakers[msg.speaker] = speakers.get(msg.speaker, 0) + 1
        
        print(f"Total Transcripts: {total}")
        print(f"Total Messages: {total_messages}")
        print(f"Unique Customers: {len(customers)}")
        print(f"Average Messages per Transcript: {total_messages/total:.1f}")
        
        if topics:
            print(f"\nTop Topics:")
            for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"  {topic}: {count}")
        
        if sentiments:
            print(f"\nSentiments:")
            for sentiment, count in sorted(sentiments.items(), key=lambda x: x[1], reverse=True):
                print(f"  {sentiment}: {count}")
        
        if speakers:
            print(f"\nSpeakers:")
            for speaker, count in sorted(speakers.items(), key=lambda x: x[1], reverse=True):
                print(f"  {speaker}: {count} messages")
                
    except Exception as e:
        print_error(f"Failed to generate statistics: {e}")

def cmd_export(args):
    """Export transcripts to JSON."""
    _, store = init_system()
    
    print_header("📤 Export Transcripts")
    
    try:
        transcripts = store.get_all()
        
        if not transcripts:
            print_info("No transcripts to export")
            return
        
        # Convert to dictionaries
        data = {
            "exported_at": datetime.now().isoformat(),
            "count": len(transcripts),
            "transcripts": [t.to_dict() for t in transcripts]
        }
        
        output_file = args.output or "transcripts_export.json"
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print_success(f"Exported {len(transcripts)} transcripts to {output_file}")
        
    except Exception as e:
        print_error(f"Export failed: {e}")

def cmd_demo(args):
    """Run a quick demo."""
    generator, store = init_system()
    
    print_header("🎭 Demo Mode")
    
    scenarios = [
        {"scenario": "escrow_shortage", "sentiment": "confused", "customer_id": "DEMO_001"},
        {"scenario": "payment_dispute", "sentiment": "frustrated", "customer_id": "DEMO_002"},
        {"scenario": "refinance_inquiry", "sentiment": "hopeful", "customer_id": "DEMO_003"},
    ]
    
    try:
        print(f"Generating {len(scenarios)} demo transcripts...\n")
        
        for i, params in enumerate(scenarios, 1):
            print(f"{i}. Generating {params['scenario']} transcript...")
            transcript = generator.generate(**params)
            
            # Store if requested
            if not args.no_store:
                store.store(transcript)
                print_success(f"Generated and stored: {transcript.id}")
            else:
                print_success(f"Generated: {transcript.id}")
            
            # Show summary
            print(f"   Messages: {len(transcript.messages)}")
            if transcript.messages:
                print(f"   First: {transcript.messages[0].speaker}: {transcript.messages[0].text[:50]}...")
        
        print_success("\nDemo completed!")
        
        if not args.no_store:
            print_info("Use 'python cli.py list' to see all transcripts")
            print_info("Use 'python cli.py stats' to see statistics")
        
    except Exception as e:
        print_error(f"Demo failed: {e}")

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Customer Call Center Analytics CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py generate scenario=escrow_shortage sentiment=confused customer_id=CUST_123
  python cli.py list --detailed
  python cli.py search --customer CUST_123
  python cli.py get CALL_ABC123 --export
  python cli.py stats
  python cli.py export --output my_transcripts.json
  python cli.py demo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate new transcript(s)')
    gen_parser.add_argument('params', nargs='*', help='Parameters in key=value format')
    gen_parser.add_argument('--count', type=int, default=1, help='Number of transcripts to generate')
    gen_parser.add_argument('--store', action='store_true', help='Store in database')
    gen_parser.add_argument('--show', action='store_true', help='Show generated transcript(s)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all transcripts')
    list_parser.add_argument('--detailed', action='store_true', help='Show detailed view')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get specific transcript')
    get_parser.add_argument('transcript_id', help='Transcript ID')
    get_parser.add_argument('--export', action='store_true', help='Export to JSON file')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search transcripts')
    search_group = search_parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument('--customer', help='Search by customer ID')
    search_group.add_argument('--topic', help='Search by topic')
    search_group.add_argument('--text', help='Search by text content')
    search_parser.add_argument('--detailed', action='store_true', help='Show detailed results')
    
    # Delete command
    del_parser = subparsers.add_parser('delete', help='Delete a transcript')
    del_parser.add_argument('transcript_id', help='Transcript ID to delete')
    del_parser.add_argument('--force', action='store_true', help='Skip confirmation')
    
    # Stats command
    subparsers.add_parser('stats', help='Show database statistics')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export transcripts to JSON')
    export_parser.add_argument('--output', help='Output filename')
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run quick demo')
    demo_parser.add_argument('--no-store', action='store_true', help='Don\'t store demo transcripts')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Route to appropriate command
    commands = {
        'generate': cmd_generate,
        'list': cmd_list,
        'get': cmd_get,
        'search': cmd_search,
        'delete': cmd_delete,
        'stats': cmd_stats,
        'export': cmd_export,
        'demo': cmd_demo,
    }
    
    commands[args.command](args)

if __name__ == "__main__":
    main()