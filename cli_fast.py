#!/usr/bin/env python3
"""
Fast CLI Client - Customer Call Center Analytics
Thin client that communicates with server.py for instant execution.
No heavy imports - just HTTP requests to pre-loaded server.
"""
import json
import requests
import sys
import argparse
from typing import List, Optional, Dict, Any
from datetime import datetime


CLI_SERVER_URL = "http://localhost:9999"


class CLIClient:
    """Thin CLI client that talks to server.py."""
    
    def __init__(self):
        self.server_url = CLI_SERVER_URL
    
    def send_command(self, command: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send command to server and return response."""
        try:
            payload = {
                'command': command,
                'params': params or {}
            }
            
            response = requests.post(
                self.server_url,
                json=payload,
                timeout=300  # 5 minute timeout for long operations
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {
                    'success': False,
                    'error': f'Server error: {response.status_code} - {response.text}'
                }
                
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': f'Cannot connect to server at {self.server_url}. Is server.py running?'
            }
        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Request timed out. Operation may still be running on server.'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Client error: {str(e)}'
            }
    
    def print_error(self, message: str):
        """Print error message in red."""
        print(f"❌ {message}")
    
    def print_success(self, message: str):
        """Print success message in green."""
        print(f"✅ {message}")
    
    def print_info(self, message: str):
        """Print info message."""
        print(f"💡 {message}")


def parse_dynamic_params(params: List[str]) -> Dict[str, Any]:
    """Parse key=value arguments with intelligent multi-word handling."""
    kwargs = {}
    i = 0
    while i < len(params):
        arg = params[i]
        
        if '=' in arg:
            key, value = arg.split('=', 1)
            
            # Handle potential continuation (multi-word values without quotes)
            while (i + 1 < len(params) and 
                   '=' not in params[i + 1] and 
                   not params[i + 1].startswith('--')):
                i += 1
                value += ' ' + params[i]
            
            # Try to parse as JSON, fallback to string
            try:
                kwargs[key] = json.loads(value)
            except:
                kwargs[key] = value
        
        i += 1
    
    return kwargs


def format_transcript_table(transcripts: List[Dict], detailed: bool = False):
    """Format transcripts for display."""
    if not transcripts:
        print("💡 No transcripts found")
        return
    
    if detailed:
        for transcript in transcripts:
            print(f"\n📄 Transcript ID: {transcript['id']}")
            
            # Show attributes
            for key, value in transcript.items():
                if key not in ['id', 'messages']:
                    print(f"  {key}: {value}")
            
            # Show messages
            messages = transcript.get('messages', [])
            print(f"\nMessages ({len(messages)}):")
            for i, msg in enumerate(messages, 1):
                speaker_emoji = "👤" if 'customer' in msg.get('speaker', '').lower() else "🎧"
                print(f"  {i}. {speaker_emoji} {msg.get('speaker', 'Unknown')}: {msg.get('text', '')}")
            
            print("-" * 50)
    else:
        # Table format
        print(f"\n{'ID':<12} {'Customer':<12} {'Topic':<15} {'Sentiment':<10} {'Msgs':<5} Preview")
        print("-" * 80)
        
        for transcript in transcripts:
            customer_id = transcript.get('customer_id', 'N/A')[:11]
            topic = transcript.get('topic', transcript.get('scenario', 'N/A'))[:14]
            sentiment = transcript.get('sentiment', 'N/A')[:9]
            msg_count = len(transcript.get('messages', []))
            
            messages = transcript.get('messages', [])
            preview = messages[0].get('speaker', 'No messages') if messages else "No messages"
            preview = preview[:20] + "..." if len(preview) > 20 else preview
            
            print(f"{transcript['id'][:11]:<12} {customer_id:<12} {topic:<15} {sentiment:<10} {msg_count:<5} {preview}")


def cmd_generate(client: CLIClient, args):
    """Handle generate command."""
    # Parse dynamic parameters from remaining args
    generation_params = parse_dynamic_params(args.params or [])
    
    params = {
        'count': args.count,
        'store': args.store,
        'generation_params': generation_params
    }
    
    print("🎤 Generating transcript(s)...")
    result = client.send_command('generate', params)
    
    if result['success']:
        transcripts = result['transcripts']
        client.print_success(f"Generated {len(transcripts)} transcript(s)")
        
        if result.get('stored'):
            client.print_success(f"Stored {len(transcripts)} transcript(s) in database")
        
        if args.show:
            format_transcript_table(transcripts, detailed=True)
    else:
        client.print_error(f"Generation failed: {result['error']}")


def cmd_list(client: CLIClient, args):
    """Handle list command."""
    print("📋 Listing transcripts...")
    result = client.send_command('list')
    
    if result['success']:
        transcripts = result['transcripts']
        print(f"Found {len(transcripts)} transcript(s)")
        format_transcript_table(transcripts, detailed=args.detailed)
    else:
        client.print_error(f"List failed: {result['error']}")


def cmd_get(client: CLIClient, args):
    """Handle get command."""
    params = {'transcript_id': args.transcript_id}
    
    print(f"📄 Getting transcript: {args.transcript_id}")
    result = client.send_command('get', params)
    
    if result['success']:
        transcript = result['transcript']
        format_transcript_table([transcript], detailed=True)
        
        if args.export:
            filename = f"{args.transcript_id}.json"
            with open(filename, 'w') as f:
                json.dump(transcript, f, indent=2)
            client.print_success(f"Exported to {filename}")
    else:
        client.print_error(f"Get failed: {result['error']}")


def cmd_search(client: CLIClient, args):
    """Handle search command."""
    params = {}
    if args.customer:
        params['customer'] = args.customer
    elif args.topic:
        params['topic'] = args.topic
    elif args.text:
        params['text'] = args.text
    else:
        client.print_error("Please specify --customer, --topic, or --text")
        return
    
    print("🔍 Searching...")
    result = client.send_command('search', params)
    
    if result['success']:
        transcripts = result['transcripts']
        print(f"Found {len(transcripts)} matching transcript(s)")
        format_transcript_table(transcripts, detailed=args.detailed)
    else:
        client.print_error(f"Search failed: {result['error']}")


def cmd_delete(client: CLIClient, args):
    """Handle delete command."""
    if not args.force:
        response = input(f"Delete transcript {args.transcript_id}? (y/N): ")
        if response.lower() not in ['y', 'yes']:
            client.print_info("Delete cancelled")
            return
    
    params = {'transcript_id': args.transcript_id}
    result = client.send_command('delete', params)
    
    if result['success']:
        client.print_success(result['message'])
    else:
        client.print_error(f"Delete failed: {result['error']}")


def cmd_stats(client: CLIClient, args):
    """Handle stats command."""
    print("📊 Getting statistics...")
    result = client.send_command('stats')
    
    if result['success']:
        stats = result['stats']
        
        print("\nDatabase Statistics:")
        print(f"  Total Transcripts: {stats['total_transcripts']}")
        print(f"  Total Messages: {stats['total_messages']}")
        print(f"  Unique Customers: {stats['unique_customers']}")
        print(f"  Avg Messages/Transcript: {stats['avg_messages_per_transcript']:.1f}")
        
        if stats['top_topics']:
            print("\nTop Topics:")
            for topic, count in list(stats['top_topics'].items())[:5]:
                print(f"  {topic}: {count}")
        
        if stats['sentiments']:
            print("\nSentiments:")
            for sentiment, count in stats['sentiments'].items():
                print(f"  {sentiment}: {count}")
        
        if stats.get('speakers'):
            print("\nTop Speakers:")
            for speaker, count in list(stats['speakers'].items())[:5]:
                print(f"  {speaker}: {count} messages")
    else:
        client.print_error(f"Stats failed: {result['error']}")


def cmd_export(client: CLIClient, args):
    """Handle export command."""
    params = {}
    if args.output:
        params['output'] = args.output
    
    print("📤 Exporting transcripts...")
    result = client.send_command('export', params)
    
    if result['success']:
        client.print_success(result['message'])
    else:
        client.print_error(f"Export failed: {result['error']}")


def cmd_demo(client: CLIClient, args):
    """Handle demo command."""
    params = {'no_store': args.no_store}
    
    print("🎭 Running demo...")
    result = client.send_command('demo', params)
    
    if result['success']:
        client.print_success(result['message'])
        
        if not args.no_store:
            client.print_info("Use 'python cli_fast.py list' to see all transcripts")
            client.print_info("Use 'python cli_fast.py stats' to see statistics")
    else:
        client.print_error(f"Demo failed: {result['error']}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Customer Call Center Analytics - Fast CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli_fast.py generate scenario="PMI Removal" --store --show
  python cli_fast.py generate --count 3 customer_id=DEMO_001 --store
  python cli_fast.py list
  python cli_fast.py get TRANSCRIPT_ID
  python cli_fast.py search --customer CUST_123
  python cli_fast.py stats
  python cli_fast.py demo
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate new transcript(s)')
    gen_parser.add_argument('params', nargs='*', help='Parameters in key=value format')
    gen_parser.add_argument('--count', '-c', type=int, default=1, help='Number of transcripts')
    gen_parser.add_argument('--store', '-s', action='store_true', help='Store in database')
    gen_parser.add_argument('--show', action='store_true', help='Show generated transcript(s)')
    gen_parser.set_defaults(func=cmd_generate)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all transcripts')
    list_parser.add_argument('--detailed', '-d', action='store_true', help='Show detailed view')
    list_parser.set_defaults(func=cmd_list)
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get specific transcript')
    get_parser.add_argument('transcript_id', help='Transcript ID')
    get_parser.add_argument('--export', '-e', action='store_true', help='Export to JSON file')
    get_parser.set_defaults(func=cmd_get)
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search transcripts')
    search_parser.add_argument('--customer', '-c', help='Search by customer ID')
    search_parser.add_argument('--topic', '-t', help='Search by topic')
    search_parser.add_argument('--text', help='Search by text content')
    search_parser.add_argument('--detailed', '-d', action='store_true', help='Show detailed results')
    search_parser.set_defaults(func=cmd_search)
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete transcript')
    delete_parser.add_argument('transcript_id', help='Transcript ID to delete')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    delete_parser.set_defaults(func=cmd_delete)
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    stats_parser.set_defaults(func=cmd_stats)
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export transcripts to JSON')
    export_parser.add_argument('--output', '-o', help='Output filename')
    export_parser.set_defaults(func=cmd_export)
    
    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run demo with sample transcripts')
    demo_parser.add_argument('--no-store', action='store_true', help="Don't store demo transcripts")
    demo_parser.set_defaults(func=cmd_demo)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create client and execute command
    client = CLIClient()
    
    try:
        args.func(client, args)
    except KeyboardInterrupt:
        client.print_info("Operation cancelled by user")
    except Exception as e:
        client.print_error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()