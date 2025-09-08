#!/usr/bin/env python3
"""
Fast CLI Client - Customer Call Center Analytics
Thin client that communicates with server.py for instant execution.
No heavy imports - just HTTP requests to pre-loaded server.
"""
import json
import requests
import sys
import typer
from rich.console import Console
from typing import List, Optional, Dict, Any
from datetime import datetime


CLI_SERVER_URL = "http://localhost:9999"

# Create Typer app and Rich console  
app = typer.Typer(
    name="cli-fast",
    help="Customer Call Center Analytics - Fast CLI (via server)",
    add_completion=False
)
console = Console()


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
        console.print(f"❌ {message}", style="red")
    
    def print_success(self, message: str):
        """Print success message in green."""
        console.print(f"✅ {message}", style="green")
    
    def print_info(self, message: str):
        """Print info message."""
        console.print(f"💡 {message}", style="cyan")


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
        console.print("💡 No transcripts found", style="cyan")
        return
    
    if detailed:
        for transcript in transcripts:
            console.print(f"\n📄 [bold cyan]Transcript ID:[/bold cyan] {transcript['id']}")
            
            # Show attributes
            console.print("\n[bold cyan]Attributes:[/bold cyan]")
            for key, value in transcript.items():
                if key not in ['id', 'messages']:
                    console.print(f"  {key}: {value}")
            
            # Show messages
            messages = transcript.get('messages', [])
            console.print(f"\n[bold cyan]Messages ({len(messages)}):[/bold cyan]")
            for i, msg in enumerate(messages, 1):
                speaker_color = "cyan" if 'customer' in msg.get('speaker', '').lower() else "green"
                console.print(f"  {i}. [{speaker_color}]{msg.get('speaker', 'Unknown')}:[/{speaker_color}] {msg.get('text', '')}")
            
            console.print("-" * 50, style="dim")
    else:
        # Table format
        console.print(f"\n{'ID':<16} {'Customer':<12} {'Topic':<15} {'Sentiment':<10} {'Msgs':<5} Preview")
        console.print("-" * 85)
        
        for transcript in transcripts:
            customer_id = transcript.get('customer_id', 'N/A')[:11]
            topic = transcript.get('topic', transcript.get('scenario', 'N/A'))[:14]
            sentiment = transcript.get('sentiment', 'N/A')[:9]
            msg_count = len(transcript.get('messages', []))
            
            messages = transcript.get('messages', [])
            preview = messages[0].get('speaker', 'No messages') if messages else "No messages"
            preview = preview[:20] + "..." if len(preview) > 20 else preview
            
            # Show full ID for copy-paste into delete commands
            full_id = transcript['id']
            display_id = full_id if len(full_id) <= 16 else full_id[:13] + "..."
            console.print(f"{display_id:<16} {customer_id:<12} {topic:<15} {sentiment:<10} {msg_count:<5} {preview}")


@app.command()
def generate(
    params: List[str] = typer.Argument(None, help="Parameters in key=value format (e.g., scenario='PMI Removal')"),
    count: int = typer.Option(1, "--count", "-c", help="Number of transcripts to generate"),
    store: bool = typer.Option(False, "--store", "-s", help="Store in database"),
    show: bool = typer.Option(False, "--show", help="Show generated transcript(s)")
):
    """Generate new transcript(s) with dynamic parameters."""
    client = CLIClient()
    
    # Parse dynamic parameters from remaining args
    generation_params = parse_dynamic_params(params or [])
    
    request_params = {
        'count': count,
        'store': store,
        'generation_params': generation_params
    }
    
    console.print("🎤 [bold magenta]Generating transcript(s)...[/bold magenta]")
    result = client.send_command('generate', request_params)
    
    if result['success']:
        transcripts = result['transcripts']
        client.print_success(f"Generated {len(transcripts)} transcript(s)")
        
        if result.get('stored'):
            client.print_success(f"Stored {len(transcripts)} transcript(s) in database")
        
        if show:
            format_transcript_table(transcripts, detailed=True)
    else:
        client.print_error(f"Generation failed: {result['error']}")


@app.command("list")
def list_transcripts(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed view")
):
    """List all transcripts."""
    client = CLIClient()
    
    console.print("📋 [bold magenta]Listing transcripts...[/bold magenta]")
    result = client.send_command('list')
    
    if result['success']:
        transcripts = result['transcripts']
        console.print(f"Found [cyan]{len(transcripts)}[/cyan] transcript(s)")
        format_transcript_table(transcripts, detailed=detailed)
    else:
        client.print_error(f"List failed: {result['error']}")


@app.command()
def get(
    transcript_id: str = typer.Argument(..., help="Transcript ID"),
    export: bool = typer.Option(False, "--export", "-e", help="Export to JSON file")
):
    """Get a specific transcript by ID."""
    client = CLIClient()
    
    params = {'transcript_id': transcript_id}
    
    console.print(f"📄 [bold magenta]Getting transcript: {transcript_id}[/bold magenta]")
    result = client.send_command('get', params)
    
    if result['success']:
        transcript = result['transcript']
        format_transcript_table([transcript], detailed=True)
        
        if export:
            filename = f"{transcript_id}.json"
            with open(filename, 'w') as f:
                json.dump(transcript, f, indent=2)
            client.print_success(f"Exported to {filename}")
    else:
        client.print_error(f"Get failed: {result['error']}")


@app.command()
def search(
    customer: Optional[str] = typer.Option(None, "--customer", "-c", help="Search by customer ID"),
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Search by topic"),
    text: Optional[str] = typer.Option(None, "--text", help="Search by text content"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed results")
):
    """Search transcripts by customer, topic, or text."""
    client = CLIClient()
    
    params = {}
    if customer:
        params['customer'] = customer
    elif topic:
        params['topic'] = topic
    elif text:
        params['text'] = text
    else:
        client.print_error("Please specify --customer, --topic, or --text")
        raise typer.Exit(1)
    
    console.print("🔍 [bold magenta]Searching...[/bold magenta]")
    result = client.send_command('search', params)
    
    if result['success']:
        transcripts = result['transcripts']
        console.print(f"Found [cyan]{len(transcripts)}[/cyan] matching transcript(s)")
        format_transcript_table(transcripts, detailed=detailed)
    else:
        client.print_error(f"Search failed: {result['error']}")


@app.command()
def delete(
    transcript_id: str = typer.Argument(..., help="Transcript ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete a transcript."""
    client = CLIClient()
    
    if not force:
        if not typer.confirm(f"Delete transcript {transcript_id}?"):
            client.print_info("Delete cancelled")
            return
    
    params = {'transcript_id': transcript_id}
    result = client.send_command('delete', params)
    
    if result['success']:
        client.print_success(result['message'])
    else:
        client.print_error(f"Delete failed: {result['error']}")


@app.command("delete-all")
def delete_all(
    force: bool = typer.Option(False, "--force", "-f", help="Skip first confirmation")
):
    """Delete ALL transcripts from the database."""
    client = CLIClient()
    
    # First get count to show in warning
    stats_result = client.send_command('stats')
    if not stats_result['success']:
        client.print_error("Could not get transcript count")
        return
    
    count = stats_result['stats']['total_transcripts']
    if count == 0:
        client.print_info("No transcripts to delete")
        return
    
    # Safety warning
    console.print(f"⚠️  [bold red]WARNING:[/bold red] This will delete [bold yellow]{count}[/bold yellow] transcripts from the database!")
    console.print("This action cannot be undone.", style="red")
    
    # First confirmation (can be skipped with --force)
    if not force:
        if not typer.confirm("Are you sure you want to delete all transcripts?"):
            client.print_info("Delete cancelled")
            return
    
    # Second confirmation - safety check (cannot be skipped)
    console.print("\n[bold red]FINAL CONFIRMATION REQUIRED[/bold red]")
    console.print(f"Type 'DELETE ALL {count}' to confirm deletion of {count} transcripts:")
    
    confirmation = typer.prompt("", show_default=False)
    expected = f"DELETE ALL {count}"
    
    if confirmation.strip() != expected:
        client.print_error(f"Confirmation failed. Expected '{expected}' but got '{confirmation.strip()}'")
        client.print_info("Delete cancelled")
        return
    
    # Perform deletion
    console.print("🗑️  Deleting all transcripts...")
    result = client.send_command('delete_all')
    
    if result['success']:
        client.print_success(result['message'])
    else:
        client.print_error(f"Delete all failed: {result['error']}")


@app.command()
def stats():
    """Show statistics about stored transcripts."""
    client = CLIClient()
    
    console.print("📊 [bold magenta]Getting statistics...[/bold magenta]")
    result = client.send_command('stats')
    
    if result['success']:
        stats = result['stats']
        
        console.print("\n[bold cyan]Database Statistics:[/bold cyan]")
        console.print(f"  Total Transcripts: [green]{stats['total_transcripts']}[/green]")
        console.print(f"  Total Messages: [green]{stats['total_messages']}[/green]")
        console.print(f"  Unique Customers: [green]{stats['unique_customers']}[/green]")
        console.print(f"  Avg Messages/Transcript: [green]{stats['avg_messages_per_transcript']:.1f}[/green]")
        
        if stats['top_topics']:
            console.print("\n[bold cyan]Top Topics:[/bold cyan]")
            for topic, count in list(stats['top_topics'].items())[:5]:
                console.print(f"  {topic}: [green]{count}[/green]")
        
        if stats['sentiments']:
            console.print("\n[bold cyan]Sentiments:[/bold cyan]")
            for sentiment, count in stats['sentiments'].items():
                console.print(f"  {sentiment}: [green]{count}[/green]")
        
        if stats.get('speakers'):
            console.print("\n[bold cyan]Top Speakers:[/bold cyan]")
            for speaker, count in list(stats['speakers'].items())[:5]:
                console.print(f"  {speaker}: [green]{count}[/green] messages")
    else:
        client.print_error(f"Stats failed: {result['error']}")


@app.command()
def export(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output filename")
):
    """Export transcripts to JSON."""
    client = CLIClient()
    
    params = {}
    if output:
        params['output'] = output
    
    console.print("📤 [bold magenta]Exporting transcripts...[/bold magenta]")
    result = client.send_command('export', params)
    
    if result['success']:
        client.print_success(result['message'])
    else:
        client.print_error(f"Export failed: {result['error']}")


@app.command()
def demo(
    no_store: bool = typer.Option(False, "--no-store", help="Don't store demo transcripts")
):
    """Run a quick demo with sample transcripts."""
    client = CLIClient()
    
    params = {'no_store': no_store}
    
    console.print("🎭 [bold magenta]Running demo...[/bold magenta]")
    result = client.send_command('demo', params)
    
    if result['success']:
        client.print_success(result['message'])
        
        if not no_store:
            client.print_info("Use 'python cli_fast.py list' to see all transcripts")
            client.print_info("Use 'python cli_fast.py stats' to see statistics")
    else:
        client.print_error(f"Demo failed: {result['error']}")


if __name__ == "__main__":
    app()