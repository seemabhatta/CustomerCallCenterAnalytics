#!/usr/bin/env python3
"""
Customer Call Center Analytics - CLI
Clean separation: CLI layer that uses pure business logic classes.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from dotenv import load_dotenv

import typer
from rich.console import Console
from rich.table import Table
from rich.progress import track

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import pure business logic classes
from src.generators.transcript_generator import TranscriptGenerator
from src.storage.transcript_store import TranscriptStore
from src.models.transcript import Transcript, Message

# Create Typer app and Rich console
app = typer.Typer(
    name="call-center-cli",
    help="Customer Call Center Analytics CLI - Generate and manage transcripts",
    add_completion=False
)
console = Console()


# CLI Helper Functions (Presentation Layer)
def init_system():
    """Initialize the transcript generation system."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            console.print("❌ OPENAI_API_KEY not found in environment", style="red")
            console.print("💡 Please set your OpenAI API key in .env file or environment", style="cyan")
            raise typer.Exit(1)
        
        # Use pure business logic classes
        generator = TranscriptGenerator(api_key=api_key)
        
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        store = TranscriptStore("data/call_center.db")
        return generator, store
        
    except Exception as e:
        console.print(f"❌ Failed to initialize system: {e}", style="red")
        raise typer.Exit(1)


def parse_dynamic_params(params: List[str]) -> dict:
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


def format_transcript_table(transcripts):
    """Format transcripts in a rich table."""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Customer", style="green")
    table.add_column("Topic", style="yellow")
    table.add_column("Sentiment", style="blue")
    table.add_column("Messages", justify="right", style="red")
    table.add_column("Preview", max_width=40)
    
    for transcript in transcripts:
        customer_id = getattr(transcript, 'customer_id', 'N/A')
        topic = getattr(transcript, 'topic', getattr(transcript, 'scenario', 'N/A'))
        sentiment = getattr(transcript, 'sentiment', 'N/A')
        message_count = str(len(transcript.messages))
        preview = transcript.messages[0].speaker if transcript.messages else "No messages"
        
        table.add_row(
            transcript.id,
            customer_id,
            topic, 
            sentiment,
            message_count,
            f"{preview}..."
        )
    
    return table


def format_transcript_detail(transcript):
    """Format a transcript for detailed display using Rich."""
    console.print(f"\n[bold cyan]Transcript ID:[/bold cyan] {transcript.id}")
    
    # Show all attributes except id and messages
    console.print("\n[bold cyan]Attributes:[/bold cyan]")
    for key, value in transcript.__dict__.items():
        if key not in ['id', 'messages']:
            console.print(f"  {key}: {value}")
    
    console.print(f"\n[bold cyan]Messages ({len(transcript.messages)}):[/bold cyan]")
    for i, msg in enumerate(transcript.messages, 1):
        speaker_color = "cyan" if 'customer' in msg.speaker.lower() else "green"
        console.print(f"  {i}. [{speaker_color}]{msg.speaker}:[/{speaker_color}] {msg.text}")
        
        # Show message attributes if any
        msg_attrs = {k: v for k, v in msg.__dict__.items() if k not in ['speaker', 'text']}
        if msg_attrs:
            for key, value in msg_attrs.items():
                console.print(f"     └─ {key}: {value}", style="dim")


# CLI Commands
@app.command()
def generate(
    params: List[str] = typer.Argument(None, help="Parameters in key=value format (e.g., scenario='PMI Removal')"),
    count: int = typer.Option(1, "--count", "-c", help="Number of transcripts to generate"),
    store: bool = typer.Option(False, "--store", "-s", help="Store in database"),
    show: bool = typer.Option(False, "--show", help="Show generated transcript(s)")
):
    """Generate new transcript(s) with dynamic parameters."""
    generator, transcript_store = init_system()
    
    console.print("🎤 [bold magenta]Generating Transcripts[/bold magenta]")
    
    # Parse dynamic parameters
    kwargs = parse_dynamic_params(params or [])
    
    try:
        if count == 1:
            console.print("Generating transcript...")
            # Use pure business logic
            transcript = generator.generate(**kwargs)
            console.print(f"✅ Generated transcript: [cyan]{transcript.id}[/cyan]", style="green")
            
            if store:
                transcript_store.store(transcript)
                console.print("✅ Stored in database", style="green")
            
            if show:
                format_transcript_detail(transcript)
                
        else:
            console.print(f"Generating {count} transcripts...")
            transcripts = []
            for i in track(range(count), description="Generating..."):
                transcript = generator.generate(**kwargs)
                transcripts.append(transcript)
            
            console.print(f"✅ Generated [cyan]{len(transcripts)}[/cyan] transcripts", style="green")
            
            if store:
                for transcript in track(transcripts, description="Storing..."):
                    transcript_store.store(transcript)
                console.print(f"✅ Stored [cyan]{len(transcripts)}[/cyan] transcripts in database", style="green")
            
            if show:
                for transcript in transcripts:
                    format_transcript_detail(transcript)
                    console.print("-" * 40, style="dim")
                    
    except Exception as e:
        console.print(f"❌ Generation failed: {e}", style="red")
        raise typer.Exit(1)


@app.command("list")
def list_transcripts(
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed view")
):
    """List all transcripts."""
    _, store = init_system()
    
    console.print("📋 [bold magenta]All Transcripts[/bold magenta]")
    
    try:
        transcripts = store.get_all()
        
        if not transcripts:
            console.print("💡 No transcripts found in database", style="cyan")
            return
        
        console.print(f"Found [cyan]{len(transcripts)}[/cyan] transcript(s):\n")
        
        if detailed:
            for transcript in transcripts:
                format_transcript_detail(transcript)
                console.print("-" * 50, style="dim")
        else:
            table = format_transcript_table(transcripts)
            console.print(table)
                
    except Exception as e:
        console.print(f"❌ Failed to list transcripts: {e}", style="red")


@app.command()
def get(
    transcript_id: str = typer.Argument(..., help="Transcript ID"),
    export: bool = typer.Option(False, "--export", "-e", help="Export to JSON file")
):
    """Get a specific transcript by ID."""
    _, store = init_system()
    
    console.print(f"📄 [bold magenta]Transcript: {transcript_id}[/bold magenta]")
    
    try:
        transcript = store.get_by_id(transcript_id)
        
        if not transcript:
            console.print(f"❌ Transcript [cyan]{transcript_id}[/cyan] not found", style="red")
            return
        
        format_transcript_detail(transcript)
        
        if export:
            filename = f"{transcript_id}.json"
            with open(filename, 'w') as f:
                json.dump(transcript.to_dict(), f, indent=2)
            console.print(f"✅ Exported to [cyan]{filename}[/cyan]", style="green")
            
    except Exception as e:
        console.print(f"❌ Failed to get transcript: {e}", style="red")


@app.command()
def search(
    customer: Optional[str] = typer.Option(None, "--customer", "-c", help="Search by customer ID"),
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Search by topic"),
    text: Optional[str] = typer.Option(None, "--text", help="Search by text content"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed results")
):
    """Search transcripts by customer, topic, or text."""
    if not any([customer, topic, text]):
        console.print("❌ Please specify --customer, --topic, or --text", style="red")
        raise typer.Exit(1)
    
    _, store = init_system()
    
    console.print("🔍 [bold magenta]Search Results[/bold magenta]")
    
    try:
        results = []
        
        if customer:
            results = store.search_by_customer(customer)
            console.print(f"Searching for customer: [cyan]{customer}[/cyan]")
            
        elif topic:
            results = store.search_by_topic(topic)
            console.print(f"Searching for topic: [cyan]{topic}[/cyan]")
            
        elif text:
            results = store.search_by_text(text)
            console.print(f"Searching for text: [cyan]{text}[/cyan]")
        
        if not results:
            console.print("💡 No transcripts found matching criteria", style="cyan")
            return
        
        console.print(f"\nFound [cyan]{len(results)}[/cyan] transcript(s):")
        
        if detailed:
            for transcript in results:
                format_transcript_detail(transcript)
                console.print("-" * 50, style="dim")
        else:
            table = format_transcript_table(results)
            console.print(table)
                
    except Exception as e:
        console.print(f"❌ Search failed: {e}", style="red")


@app.command()
def delete(
    transcript_id: str = typer.Argument(..., help="Transcript ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete a transcript."""
    _, store = init_system()
    
    try:
        # Check if transcript exists first
        transcript = store.get_by_id(transcript_id)
        if not transcript:
            console.print(f"❌ Transcript [cyan]{transcript_id}[/cyan] not found", style="red")
            return
        
        # Use Typer's built-in confirmation with force flag
        if force or typer.confirm(f"Delete transcript {transcript_id}?"):
            result = store.delete(transcript_id)
            if result:
                console.print(f"✅ Deleted transcript [cyan]{transcript_id}[/cyan]", style="green")
            else:
                console.print("❌ Failed to delete transcript", style="red")
        else:
            console.print("💡 Delete cancelled", style="cyan")
            
    except Exception as e:
        console.print(f"❌ Delete failed: {e}", style="red")


@app.command()
def stats():
    """Show statistics about stored transcripts."""
    _, store = init_system()
    
    console.print("📊 [bold magenta]Database Statistics[/bold magenta]")
    
    try:
        transcripts = store.get_all()
        
        if not transcripts:
            console.print("💡 No transcripts in database", style="cyan")
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
        
        # Create statistics table
        stats_table = Table(show_header=False, box=None)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Total Transcripts", str(total))
        stats_table.add_row("Total Messages", str(total_messages))
        stats_table.add_row("Unique Customers", str(len(customers)))
        stats_table.add_row("Avg Messages/Transcript", f"{total_messages/total:.1f}")
        
        console.print(stats_table)
        
        if topics:
            console.print("\n[bold cyan]Top Topics:[/bold cyan]")
            for topic, count in sorted(topics.items(), key=lambda x: x[1], reverse=True)[:5]:
                console.print(f"  {topic}: [green]{count}[/green]")
        
        if sentiments:
            console.print("\n[bold cyan]Sentiments:[/bold cyan]")
            for sentiment, count in sorted(sentiments.items(), key=lambda x: x[1], reverse=True):
                console.print(f"  {sentiment}: [green]{count}[/green]")
        
        if speakers:
            console.print("\n[bold cyan]Top Speakers:[/bold cyan]")
            for speaker, count in sorted(speakers.items(), key=lambda x: x[1], reverse=True)[:10]:
                console.print(f"  {speaker}: [green]{count}[/green] messages")
                
    except Exception as e:
        console.print(f"❌ Failed to generate statistics: {e}", style="red")


@app.command()
def export(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output filename")
):
    """Export transcripts to JSON."""
    _, store = init_system()
    
    console.print("📤 [bold magenta]Export Transcripts[/bold magenta]")
    
    try:
        transcripts = store.get_all()
        
        if not transcripts:
            console.print("💡 No transcripts to export", style="cyan")
            return
        
        # Convert to dictionaries
        data = {
            "exported_at": datetime.now().isoformat(),
            "count": len(transcripts),
            "transcripts": [t.to_dict() for t in transcripts]
        }
        
        output_file = output or "transcripts_export.json"
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        console.print(f"✅ Exported [cyan]{len(transcripts)}[/cyan] transcripts to [cyan]{output_file}[/cyan]", style="green")
        
    except Exception as e:
        console.print(f"❌ Export failed: {e}", style="red")


@app.command()
def demo(
    no_store: bool = typer.Option(False, "--no-store", help="Don't store demo transcripts")
):
    """Run a quick demo with sample transcripts."""
    generator, store = init_system()
    
    console.print("🎭 [bold magenta]Demo Mode[/bold magenta]")
    
    scenarios = [
        {"scenario": "escrow_shortage", "customer_id": "DEMO_001"},
        {"scenario": "payment_dispute", "customer_id": "DEMO_002"},
        {"scenario": "refinance_inquiry", "customer_id": "DEMO_003"},
    ]
    
    try:
        console.print(f"Generating [cyan]{len(scenarios)}[/cyan] demo transcripts...\n")
        
        for params in track(scenarios, description="Generating demo transcripts..."):
            # Use pure business logic
            transcript = generator.generate(**params)
            
            # Store if requested
            if not no_store:
                store.store(transcript)
                console.print(f"✅ Generated and stored: [cyan]{transcript.id}[/cyan]", style="green")
            else:
                console.print(f"✅ Generated: [cyan]{transcript.id}[/cyan]", style="green")
            
            # Show summary
            console.print(f"   Messages: {len(transcript.messages)}")
            if transcript.messages:
                console.print(f"   First: [cyan]{transcript.messages[0].speaker}[/cyan]: {transcript.messages[0].text[:50]}...")
        
        console.print("\n✅ Demo completed!", style="green")
        
        if not no_store:
            console.print("💡 Use '[cyan]python cli.py list[/cyan]' to see all transcripts", style="cyan")
            console.print("💡 Use '[cyan]python cli.py stats[/cyan]' to see statistics", style="cyan")
        
    except Exception as e:
        console.print(f"❌ Demo failed: {e}", style="red")


if __name__ == "__main__":
    app()