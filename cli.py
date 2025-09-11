#!/usr/bin/env python3
"""
Customer Call Center Analytics CLI
Direct REST API client following industry best practices
No fallback logic - fail fast with clear error messages
"""
import json
import requests
import sys
import typer
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List, Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from urllib.parse import urljoin, urlencode

# Load environment variables from .env file
load_dotenv()

# Default API configuration
DEFAULT_API_URL = os.getenv("CCANALYTICS_API_URL", "http://localhost:8000")
DEFAULT_FORMAT = os.getenv("CCANALYTICS_FORMAT", "table")
DEFAULT_VERBOSE = os.getenv("CCANALYTICS_VERBOSE", "false").lower() == "true"

# Global configuration variables
GLOBAL_API_URL = DEFAULT_API_URL
GLOBAL_FORMAT = DEFAULT_FORMAT
GLOBAL_VERBOSE = DEFAULT_VERBOSE

# Create Typer app and Rich console  
app = typer.Typer(
    name="cli",
    help="Customer Call Center Analytics - REST API Client",
    add_completion=False
)
console = Console()


class CLIRestClient:
    """REST API client for Customer Call Center Analytics."""
    
    def __init__(self, api_url: str = DEFAULT_API_URL, verbose: bool = DEFAULT_VERBOSE):
        self.api_url = api_url.rstrip('/')  # Remove trailing slash
        self.verbose = verbose
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     json_data: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
        """Make REST API request with proper error handling."""
        url = urljoin(self.api_url, endpoint)
        
        if self.verbose:
            console.print(f"🔄 API Call: {method.upper()} {endpoint}", style="cyan")
            if json_data:
                console.print(f"📤 Payload: {json_data}", style="dim")
        
        try:
            start_time = datetime.now()
            
            if method.upper() == 'GET':
                if params:
                    url += '?' + urlencode(params)
                response = self.session.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=json_data, params=params, timeout=timeout)
            elif method.upper() == 'PUT':
                response = self.session.put(url, json=json_data, params=params, timeout=timeout)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, params=params, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if self.verbose:
                duration = (datetime.now() - start_time).total_seconds()
                console.print(f"⏱️  Response time: {duration:.2f}s", style="dim")
                console.print(f"📡 Status: {response.status_code}", style="dim")
            
            # Handle different response codes
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 201:
                return response.json()
            elif response.status_code == 404:
                raise CLIError(f"Not found: {endpoint}")
            elif response.status_code == 503:
                error_data = response.json() if response.content else {}
                raise CLIError(f"Service unavailable: {error_data.get('detail', 'Unknown error')}")
            else:
                error_text = response.text[:200] if response.text else 'Unknown error'
                raise CLIError(f"API error ({response.status_code}): {error_text}")
                
        except requests.exceptions.ConnectionError:
            raise CLIError(f"Cannot connect to API server at {self.api_url}. Is the server running?")
        except requests.exceptions.Timeout:
            raise CLIError(f"Request timed out after {timeout}s. Operation may still be running.")
        except requests.exceptions.RequestException as e:
            raise CLIError(f"Request failed: {str(e)}")
    
    # Transcript operations
    def generate_transcript(self, **kwargs) -> Dict[str, Any]:
        """Generate transcript via POST /api/v1/transcripts."""
        return self._make_request('POST', '/api/v1/transcripts', json_data=kwargs, timeout=300)
    
    def list_transcripts(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """List transcripts via GET /api/v1/transcripts."""
        params = {}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        return self._make_request('GET', '/api/v1/transcripts', params=params)
    
    def get_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """Get transcript by ID via GET /api/v1/transcripts/{id}."""
        return self._make_request('GET', f'/api/v1/transcripts/{transcript_id}')
    
    def delete_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """Delete transcript via DELETE /api/v1/transcripts/{id}."""
        return self._make_request('DELETE', f'/api/v1/transcripts/{transcript_id}')
    
    def search_transcripts(self, **kwargs) -> List[Dict[str, Any]]:
        """Search transcripts via GET /api/v1/transcripts/search."""
        return self._make_request('GET', '/api/v1/transcripts/search', params=kwargs)
    
    # Analysis operations  
    def analyze_transcript(self, **kwargs) -> Dict[str, Any]:
        """Analyze transcript via POST /api/v1/analyses."""
        return self._make_request('POST', '/api/v1/analyses', json_data=kwargs, timeout=300)
    
    def get_analysis(self, analysis_id: str) -> Dict[str, Any]:
        """Get analysis by ID via GET /api/v1/analyses/{id}."""
        return self._make_request('GET', f'/api/v1/analyses/{analysis_id}')
    
    def list_analyses(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List analyses via GET /api/v1/analyses."""
        params = {'limit': limit} if limit else {}
        return self._make_request('GET', '/api/v1/analyses', params=params)
    
    # Action plan operations
    def create_plan(self, **kwargs) -> Dict[str, Any]:
        """Create action plan via POST /api/v1/plans."""
        return self._make_request('POST', '/api/v1/plans', json_data=kwargs, timeout=300)
    
    def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get action plan by ID via GET /api/v1/plans/{id}."""
        return self._make_request('GET', f'/api/v1/plans/{plan_id}')
    
    def approve_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Approve action plan via POST /api/v1/plans/{id}/approve."""
        return self._make_request('POST', f'/api/v1/plans/{plan_id}/approve', json_data=kwargs)
    
    def execute_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Execute action plan via POST /api/v1/plans/{id}/execute."""
        return self._make_request('POST', f'/api/v1/plans/{plan_id}/execute', json_data=kwargs, timeout=300)
    
    def list_plans(self, limit: Optional[int] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List action plans via GET /api/v1/plans."""
        params = {}
        if limit is not None:
            params['limit'] = limit
        if status is not None:
            params['status'] = status
        return self._make_request('GET', '/api/v1/plans', params=params)
    
    # System operations
    def health_check(self) -> Dict[str, Any]:
        """Check system health via GET /api/v1/health."""
        return self._make_request('GET', '/api/v1/health')
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get dashboard metrics via GET /api/v1/metrics."""
        return self._make_request('GET', '/api/v1/metrics')
    
    def get_workflow_status(self) -> List[Dict[str, Any]]:
        """Get workflow status via GET /api/v1/workflow/status."""
        return self._make_request('GET', '/api/v1/workflow/status')
    
    # Case operations
    def list_cases(self, **kwargs) -> List[Dict[str, Any]]:
        """List cases via GET /api/v1/cases."""
        return self._make_request('GET', '/api/v1/cases', params=kwargs)
    
    def get_case(self, case_id: str) -> Dict[str, Any]:
        """Get case by ID via GET /api/v1/cases/{id}."""
        return self._make_request('GET', f'/api/v1/cases/{case_id}')


class CLIError(Exception):
    """Custom exception for CLI errors - no fallback logic."""
    pass
    
# Global CLI options
@app.callback()
def main(
    api_url: Optional[str] = typer.Option(DEFAULT_API_URL, "--api-url", help="API server URL"),
    format: Optional[str] = typer.Option(DEFAULT_FORMAT, "--format", help="Output format: table, json, yaml"),
    verbose: bool = typer.Option(DEFAULT_VERBOSE, "--verbose", help="Show detailed API calls"),
    version: bool = typer.Option(False, "--version", help="Show version")
):
    """Customer Call Center Analytics CLI - Direct REST API Client
    
    Server: REST API on http://localhost:8000
    
    Examples:
      cli.py generate --scenario "PMI Removal" --store
      cli.py list --limit 10
      cli.py analyze TRANSCRIPT_001
      cli.py health --verbose
    """
    if version:
        console.print("Customer Call Center Analytics CLI v1.0.0")
        console.print(f"API Server: {api_url}")
        raise typer.Exit()
    
    # Store global options as global variables for simplicity
    global GLOBAL_API_URL, GLOBAL_FORMAT, GLOBAL_VERBOSE
    GLOBAL_API_URL = api_url
    GLOBAL_FORMAT = format
    GLOBAL_VERBOSE = verbose


def get_client() -> CLIRestClient:
    """Get configured REST client."""
    return CLIRestClient(api_url=GLOBAL_API_URL, verbose=GLOBAL_VERBOSE)


def print_error(message: str):
    """Print error message in red."""
    console.print(f"❌ {message}", style="red")

def print_success(message: str):
    """Print success message in green."""
    console.print(f"✅ {message}", style="green")

def print_info(message: str):
    """Print info message."""
    console.print(f"💡 {message}", style="cyan")

def print_json(data: Any):
    """Print data as JSON."""
    console.print_json(json.dumps(data, indent=2, default=str))

def format_output(data: Any, output_format: str = "table"):
    """Format output based on requested format."""
    state = getattr(app, 'state', None)
    if state and hasattr(state, 'format'):
        output_format = state.format
    
    if output_format == "json":
        print_json(data)
    elif output_format == "yaml":
        import yaml
        console.print(yaml.dump(data, default_flow_style=False))
    else:
        # Default table format - will be implemented per command
        return data


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
            topic = transcript.get('topic', '')[:14]
            # Handle legacy data during transition: show "Legacy" for old empty topics
            if not topic:
                topic = "[Legacy]"
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
    topic: Optional[str] = typer.Option(None, "--topic", help="Call topic/scenario"),
    urgency: Optional[str] = typer.Option("medium", "--urgency", help="Urgency level: low, medium, high, critical"),
    financial: Optional[bool] = typer.Option(False, "--financial", help="Has financial impact"),
    sentiment: Optional[str] = typer.Option("neutral", "--sentiment", help="Customer sentiment"),
    customer: Optional[str] = typer.Option("CUST_001", "--customer", help="Customer ID"),
    store: bool = typer.Option(False, "--store", "-s", help="Store in database"),
    count: int = typer.Option(1, "--count", "-c", help="Number of transcripts to generate"),
    show: bool = typer.Option(False, "--show", help="Show generated transcript(s)")
):
    """Generate AI-powered call transcript using OpenAI.
    
    REST API: POST /api/v1/transcripts
    
    Examples:
      cli.py generate --topic "PMI Removal" --urgency high --store
      cli.py generate topic="Payment Dispute" financial=true --store
    """
    try:
        client = get_client()
        
        # Parse dynamic parameters from remaining args
        generation_params = parse_dynamic_params(params or [])
        
        # Build request payload
        request_data = {
            "topic": topic or generation_params.get("topic", "payment_inquiry"),
            "urgency": urgency,
            "financial_impact": financial or generation_params.get("financial_impact", False),
            "customer_sentiment": sentiment,
            "customer_id": customer,
            "store": store
        }
        
        # Override with any dynamic params
        request_data.update(generation_params)
        
        console.print("🎤 [bold magenta]Generating transcript...[/bold magenta]")
        
        if count == 1:
            result = client.generate_transcript(**request_data)
            
            # Extract transcript ID - NO FALLBACK: fail fast if missing
            transcript_id = result.get('id')
            if not transcript_id:
                raise CLIError(f"Failed to extract transcript ID from API response. Response: {result}")
            
            print_success(f"Generated transcript: {transcript_id}")
            
            # Show storage confirmation if stored
            if store and result.get('id'):
                print_success(f"✅ Stored in database with ID: {transcript_id}")
            
            # Show transcript details if requested
            if show:
                console.print(f"\n📄 [bold cyan]Transcript Details:[/bold cyan]")
                console.print(f"ID: {transcript_id}")
                console.print(f"Scenario: {result.get('scenario', 'N/A')}")
                console.print(f"Customer: {result.get('customer_id', 'N/A')}")
                console.print(f"Messages: {len(result.get('messages', []))}")
                console.print(f"Timestamp: {result.get('timestamp', 'N/A')}")
                
                # Show the conversation
                console.print(f"\n[bold cyan]Conversation:[/bold cyan]")
                if 'raw_text' in result:
                    # Show formatted conversation from raw_text
                    console.print(result['raw_text'])
                elif 'messages' in result:
                    # Fallback: show messages list
                    for i, msg in enumerate(result['messages'][:10], 1):  # Show first 10 messages
                        speaker = msg.get('speaker', 'Unknown')
                        text = msg.get('text', '')
                        console.print(f"{i}. [cyan]{speaker}:[/cyan] {text}")
                    if len(result['messages']) > 10:
                        console.print(f"... and {len(result['messages']) - 10} more messages")
                else:
                    console.print("No conversation content available")
        else:
            # For multiple transcripts, call API multiple times
            transcripts = []
            transcript_ids = []
            
            for i in range(count):
                result = client.generate_transcript(**request_data)
                
                # Extract transcript ID - NO FALLBACK: fail fast if missing
                transcript_id = result.get('id')
                if not transcript_id:
                    raise CLIError(f"Failed to extract transcript ID from API response for transcript {i+1}. Response: {result}")
                
                transcripts.append(result)
                transcript_ids.append(transcript_id)
                
                print_success(f"Generated transcript {i+1}/{count}: {transcript_id}")
                
                if store:
                    print_success(f"✅ Stored in database: {transcript_id}")
            
            print_success(f"Generated {count} transcripts: {', '.join(transcript_ids)}")
            
            # Show details for all transcripts if requested
            if show:
                for i, result in enumerate(transcripts, 1):
                    transcript_id = result.get('id')
                    console.print(f"\n📄 [bold cyan]Transcript {i} Details:[/bold cyan]")
                    console.print(f"ID: {transcript_id}")
                    console.print(f"Scenario: {result.get('scenario', 'N/A')}")
                    console.print(f"Messages: {len(result.get('messages', []))}")
                    if i < len(transcripts):  # Don't show full content for all, just summary
                        console.print("(Use single transcript generation with --show for full details)")
                    console.print("---")
                
    except CLIError as e:
        print_error(f"Generation failed: {str(e)}")
        raise typer.Exit(1)


@app.command("list")
def list_transcripts(
    limit: int = typer.Option(None, "--limit", "-l", help="Maximum number to show"),
    offset: int = typer.Option(None, "--offset", help="Skip first N transcripts"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed view")
):
    """List all transcripts from database.
    
    REST API: GET /api/v1/transcripts
    
    Examples:
      cli.py list --limit 10
      cli.py list --detailed
    """
    try:
        client = get_client()
        
        console.print("📋 [bold blue]Fetching transcripts...[/bold blue]")
        transcripts = client.list_transcripts(limit=limit, offset=offset)
        
        if not transcripts:
            print_info("No transcripts found in database")
            return
            
        print_success(f"Found {len(transcripts)} transcript(s)")
        format_transcript_table(transcripts, detailed=detailed)
        
    except CLIError as e:
        print_error(f"Failed to list transcripts: {str(e)}")
        raise typer.Exit(1)


@app.command()
def get(
    transcript_id: str = typer.Argument(..., help="Transcript ID"),
    export: bool = typer.Option(False, "--export", "-e", help="Export to JSON file")
):
    """Get a specific transcript by ID.
    
    REST API: GET /transcript/{transcript_id}
    """
    try:
        client = get_client()
        
        console.print(f"📄 [bold magenta]Getting transcript: {transcript_id}[/bold magenta]")
        transcript = client.get_transcript(transcript_id)
        
        format_transcript_table([transcript], detailed=True)
        
        if export:
            filename = f"{transcript_id}.json"
            with open(filename, 'w') as f:
                json.dump(transcript, f, indent=2)
            print_success(f"Exported to {filename}")
            
    except CLIError as e:
        print_error(f"Get failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def search(
    customer: Optional[str] = typer.Option(None, "--customer", "-c", help="Search by customer ID"),
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Search by topic"),
    text: Optional[str] = typer.Option(None, "--text", help="Search by text content"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed results")
):
    """Search transcripts by customer, topic, or text.
    
    REST API: GET /transcripts (with filtering)
    """
    try:
        client = get_client()
        
        if not any([customer, topic, text]):
            print_error("Please specify --customer, --topic, or --text")
            raise typer.Exit(1)
        
        console.print("🔍 [bold magenta]Searching...[/bold magenta]")
        
        # Get all transcripts and filter client-side for now
        # TODO: Add search endpoint to REST API
        all_transcripts = client.list_transcripts()
        
        filtered = []
        for transcript in all_transcripts:
            if customer and transcript.get('customer_id') == customer:
                filtered.append(transcript)
            elif topic and topic.lower() in transcript.get('topic', '').lower():
                filtered.append(transcript)
            elif text:
                # Search in messages
                messages = transcript.get('messages', [])
                for msg in messages:
                    if text.lower() in msg.get('text', '').lower():
                        filtered.append(transcript)
                        break
        
        console.print(f"Found [cyan]{len(filtered)}[/cyan] matching transcript(s)")
        format_transcript_table(filtered, detailed=detailed)
        
    except CLIError as e:
        print_error(f"Search failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def delete(
    transcript_id: str = typer.Argument(..., help="Transcript ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete a transcript.
    
    REST API: DELETE /transcript/{transcript_id}
    """
    try:
        client = get_client()
        
        if not force:
            if not typer.confirm(f"Delete transcript {transcript_id}?"):
                print_info("Delete cancelled")
                return
        
        # NO FALLBACK: Execute delete or fail fast
        result = client.delete_transcript(transcript_id)
        print_success(f"✅ Deleted transcript: {transcript_id}")
        
    except CLIError as e:
        print_error(f"Delete failed: {str(e)}")
        raise typer.Exit(1)


@app.command("delete-all")
def delete_all(
    force: bool = typer.Option(False, "--force", "-f", help="Skip first confirmation")
):
    """Delete ALL transcripts from the database.
    
    REST API: DELETE /transcripts (bulk delete)
    """
    try:
        client = get_client()
        
        # Get count to show in warning
        transcripts = client.list_transcripts()
        count = len(transcripts)
        
        if count == 0:
            print_info("No transcripts to delete")
            return
        
        # Safety warning
        console.print(f"⚠️  [bold red]WARNING:[/bold red] This will delete [bold yellow]{count}[/bold yellow] transcripts from the database!")
        console.print("This action cannot be undone.", style="red")
        
        # First confirmation (can be skipped with --force)
        if not force:
            if not typer.confirm("Are you sure you want to delete all transcripts?"):
                print_info("Delete cancelled")
                return
        
        # Second confirmation - safety check (cannot be skipped)
        console.print("\n[bold red]FINAL CONFIRMATION REQUIRED[/bold red]")
        console.print(f"Type 'DELETE ALL {count}' to confirm deletion of {count} transcripts:")
        
        confirmation = typer.prompt("", show_default=False)
        expected = f"DELETE ALL {count}"
        
        if confirmation.strip() != expected:
            print_error(f"Confirmation failed. Expected '{expected}' but got '{confirmation.strip()}'")
            print_info("Delete cancelled")
            return
        
        # NO FALLBACK: Execute bulk delete or fail fast
        console.print(f"\n🗑️  [bold red]Deleting {count} transcripts...[/bold red]")
        
        deleted_count = 0
        for transcript in transcripts:
            try:
                client.delete_transcript(transcript['id'])
                deleted_count += 1
                console.print(f"✅ Deleted {transcript['id']} ({deleted_count}/{count})")
            except Exception as e:
                print_error(f"Failed to delete {transcript['id']}: {str(e)}")
                # Continue with remaining deletions
        
        print_success(f"✅ Successfully deleted {deleted_count} of {count} transcripts")
        
    except CLIError as e:
        print_error(f"Delete all failed: {str(e)}")
        raise typer.Exit(1)



@app.command()
def export(
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output filename")
):
    """Export transcripts to JSON.
    
    REST API: GET /transcripts (then export to file)
    """
    try:
        client = get_client()
        
        console.print("📤 [bold magenta]Exporting transcripts...[/bold magenta]")
        transcripts = client.list_transcripts()
        
        filename = output or "transcripts_export.json"
        
        with open(filename, 'w') as f:
            json.dump(transcripts, f, indent=2)
        
        print_success(f"Exported {len(transcripts)} transcripts to {filename}")
        
    except CLIError as e:
        print_error(f"Export failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def demo(
    no_store: bool = typer.Option(False, "--no-store", help="Don't store demo transcripts")
):
    """Run a quick demo with sample transcripts.
    
    REST API: POST /api/v1/transcripts (multiple calls)
    """
    try:
        client = get_client()
        
        store = not no_store
        
        console.print("🎭 [bold magenta]Running demo...[/bold magenta]")
        
        # Generate sample demo transcripts
        demo_scenarios = [
            {"scenario": "Payment Dispute", "urgency": "high", "financial_impact": True, "customer_sentiment": "frustrated", "store": store},
            {"scenario": "PMI Removal", "urgency": "medium", "financial_impact": True, "customer_sentiment": "neutral", "store": store},
            {"scenario": "Account Balance Inquiry", "urgency": "low", "financial_impact": False, "customer_sentiment": "neutral", "store": store}
        ]
        
        generated_count = 0
        for scenario_data in demo_scenarios:
            try:
                result = client.generate_transcript(**scenario_data)
                generated_count += 1
                console.print(f"  ✓ Generated: {scenario_data['scenario']}")
            except Exception as e:
                console.print(f"  ✗ Failed: {scenario_data['scenario']} - {str(e)}")
        
        print_success(f"Demo completed! Generated {generated_count} transcripts")
        
        if store:
            print_info("Use 'python cli.py list' to see all transcripts")
            print_info("Use 'python cli.py stats' to see statistics")
        
    except CLIError as e:
        print_error(f"Demo failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def analyze(
    transcript_id: Optional[str] = typer.Argument(None, help="Transcript ID to analyze"),
    transcript_id_option: Optional[str] = typer.Option(None, "--transcript-id", "-t", help="Alternative way to specify transcript ID"),
    all_transcripts: bool = typer.Option(False, "--all", "-a", help="Analyze all unanalyzed transcripts"),
    analysis_type: str = typer.Option("comprehensive", "--type", help="Analysis type: comprehensive, quick, sentiment"),
    store: bool = typer.Option(True, "--store", help="Store analysis results"),
    show_risk: bool = typer.Option(False, "--show-risk", help="Display risk assessment")
):
    """Analyze transcript for customer intent, sentiment, and risks.
    
    REST API: POST /api/v1/analyses
    
    Examples:
      cli.py analyze TRANSCRIPT_001
      cli.py analyze --transcript-id TRANSCRIPT_001 --show-risk
      cli.py analyze --all --store
    """
    try:
        client = get_client()
        
        # Determine transcript ID from argument or option
        final_transcript_id = transcript_id or transcript_id_option
        
        if not final_transcript_id and not all_transcripts:
            print_error("Specify either transcript ID or --all")
            raise typer.Exit(1)
        
        if all_transcripts:
            # Get all transcripts and analyze unanalyzed ones
            console.print("🔍 [bold magenta]Analyzing all unanalyzed transcripts...[/bold magenta]")
            transcripts = client.list_transcripts()
            analyzed_count = 0
            
            for transcript in transcripts:
                try:
                    result = client.analyze_transcript(
                        transcript_id=transcript['transcript_id'],
                        analysis_type=analysis_type,
                        store=store
                    )
                    analyzed_count += 1
                    print_success(f"Analyzed transcript: {transcript['transcript_id']}")
                except CLIError as e:
                    print_error(f"Failed to analyze {transcript['transcript_id']}: {str(e)}")
            
            print_success(f"Analyzed {analyzed_count} transcript(s)")
        else:
            # Analyze single transcript
            console.print(f"🔍 [bold magenta]Analyzing transcript {final_transcript_id}...[/bold magenta]")
            result = client.analyze_transcript(
                transcript_id=final_transcript_id,
                analysis_type=analysis_type,
                store=store
            )
            
            print_success(f"✅ Analysis completed for transcript: {final_transcript_id}")
            
            # Display analysis results - NO FALLBACK: Use correct field names from API
            analysis_id = result.get('analysis_id')
            intent = result.get('primary_intent')
            
            # Handle nested sentiment structure
            borrower_sentiment = result.get('borrower_sentiment', {})
            if isinstance(borrower_sentiment, dict):
                sentiment = borrower_sentiment.get('overall')
            else:
                sentiment = None
            
            confidence_score = result.get('confidence_score')
            
            # NO FALLBACK: Fail fast if critical data is missing
            if not analysis_id:
                raise CLIError("Analysis ID missing from API response")
            if not intent:
                raise CLIError("Primary intent missing from API response")
            if not sentiment:
                raise CLIError("Sentiment data missing from API response")
            if confidence_score is None:
                raise CLIError("Confidence score missing from API response")
                
            console.print(f"\n📄 Analysis Results:")
            console.print(f"   Analysis ID: {analysis_id}")
            console.print(f"   Intent: {intent}")
            console.print(f"   Sentiment: {sentiment}")
            console.print(f"   Confidence: {confidence_score:.2%}")
            
            if show_risk and 'risk_scores' in result:
                console.print(f"\n⚠️  Risk Assessment:")
                risk_scores = result['risk_scores']
                for risk_type, score in risk_scores.items():
                    console.print(f"   {risk_type.title()}: {score:.2%}")
                    
    except CLIError as e:
        print_error(f"Analysis failed: {str(e)}")
        raise typer.Exit(1)
# Essential system commands for DEMO.md workflow

@app.command()
def health():
    """Check system health status.
    
    REST API: GET /api/v1/health
    
    Examples:
      cli.py health
      cli.py health --verbose
    """
    try:
        client = get_client()
        
        console.print("🏥 [bold blue]Checking system health...[/bold blue]")
        result = client.health_check()
        
        status = result.get('status', 'unknown')
        if status == 'healthy':
            print_success("System is healthy")
        else:
            print_error(f"System is {status}")
            if 'error' in result:
                console.print(f"Error: {result['error']}", style="red")
        
        # Show detailed health info
        console.print(f"\n🔍 Health Details:")
        console.print(f"   Database: {result.get('database', 'unknown')}")
        console.print(f"   API Key: {result.get('api_key', 'unknown')}")
        console.print(f"   Uptime: {result.get('uptime', 'unknown')}")
        
        if 'services' in result:
            console.print(f"   Services:")
            for service, status in result['services'].items():
                status_icon = "✅" if status == "healthy" else "❌"
                console.print(f"     {status_icon} {service}: {status}")
        
        # Exit with error code if unhealthy
        if status != 'healthy':
            raise typer.Exit(1)
            
    except CLIError as e:
        print_error(f"Health check failed: {str(e)}")
        raise typer.Exit(1)


@app.command()
def stats():
    """Display system statistics and metrics.
    
    REST API: GET /api/v1/metrics
    
    Examples:
      cli.py stats
    """
    try:
        client = get_client()
        
        console.print("📊 [bold blue]Fetching system statistics...[/bold blue]")
        result = client.get_metrics()
        
        print_success("System Statistics")
        
        # Display key metrics
        console.print(f"\n📈 Dashboard Metrics:")
        console.print(f"   Total Transcripts: {result.get('totalTranscripts', 0)}")
        console.print(f"   Completion Rate: {result.get('completeRate', 0.0):.2%}")
        console.print(f"   Avg Processing Time: {result.get('avgProcessingTime', 0.0):.1f}s")
        
        # Stage data
        if 'stageData' in result:
            console.print(f"\n🔄 Pipeline Status:")
            stage_data = result['stageData']
            for stage, counts in stage_data.items():
                if isinstance(counts, dict):
                    total = sum(counts.values())
                    console.print(f"   {stage.title()}: {total} items")
                    for substage, count in counts.items():
                        console.print(f"     {substage}: {count}")
        
        console.print(f"\n🕐 Last Updated: {result.get('lastUpdated', 'Unknown')}")
        
    except CLIError as e:
        print_error(f"Failed to get statistics: {str(e)}")
        raise typer.Exit(1)


@app.command("create-plan")
def create_plan(
    transcript_id: Optional[str] = typer.Option(None, "--transcript-id", help="Transcript to plan from"),
    analysis_id: Optional[str] = typer.Option(None, "--analysis-id", help="Use existing analysis"),
    plan_type: str = typer.Option("standard", "--plan-type", help="Type: standard, expedited, minimal"),
    store: bool = typer.Option(True, "--store", help="Store plan in database")
):
    """Generate comprehensive action plan from analysis.
    
    REST API: POST /api/v1/plans
    
    Examples:
      cli.py create-plan --transcript-id TRANSCRIPT_001
      cli.py create-plan --analysis-id ANALYSIS_001
    """
    try:
        client = get_client()
        
        if not transcript_id and not analysis_id:
            print_error("Specify either --transcript-id or --analysis-id")
            raise typer.Exit(1)
        
        request_data = {
            "plan_type": plan_type,
            "store": store
        }
        
        if transcript_id:
            request_data["transcript_id"] = transcript_id
        if analysis_id:
            request_data["analysis_id"] = analysis_id
        
        console.print("📋 [bold magenta]Generating action plan...[/bold magenta]")
        result = client.create_plan(**request_data)
        
        plan_id = result.get('plan_id', 'Unknown')
        total_actions = result.get('total_actions', 0)
        risk_level = result.get('risk_level', 'Unknown')
        
        print_success(f"✅ Action Plan {plan_id} created")
        console.print(f"   Total Actions: {total_actions}")
        console.print(f"   Risk Level: {risk_level}")
        console.print(f"   Approval Route: {result.get('approval_route', 'Unknown')}")
        console.print(f"   Queue Status: {result.get('queue_status', 'Unknown')}")
        
    except CLIError as e:
        print_error(f"Failed to create action plan: {str(e)}")
        raise typer.Exit(1)


@app.command("analysis-report")
def analysis_report(
    transcript_id: Optional[str] = typer.Option(None, "--transcript-id", "-t", help="Specific transcript analysis to view"),
    analysis_id: Optional[str] = typer.Option(None, "--analysis-id", "-a", help="Specific analysis ID to view")
):
    """View detailed analysis report."""
    client = get_client()
    
    if not transcript_id and not analysis_id:
        print_error("Specify either --transcript-id or --analysis-id")
        raise typer.Exit(1)
    
    params = {
        'transcript_id': transcript_id,
        'analysis_id': analysis_id
    }
    
    console.print("📊 [bold magenta]Getting analysis report...[/bold magenta]")
    result = client.send_command('analysis_report', params)
    
    if result['success']:
        analysis = result['analysis']
        
        # Display detailed analysis
        console.print(f"\n📄 [bold cyan]Analysis Report[/bold cyan]")
        console.print(f"Analysis ID: {analysis['analysis_id']}")
        console.print(f"Transcript ID: {analysis['transcript_id']}")
        console.print(f"Confidence Score: {analysis['confidence_score']:.2f}")
        
        console.print(f"\n[bold cyan]Call Summary:[/bold cyan]")
        console.print(analysis['call_summary'])
        
        console.print(f"\n[bold cyan]Key Insights:[/bold cyan]")
        console.print(f"  Primary Intent: {analysis['primary_intent']}")
        console.print(f"  Urgency Level: {analysis['urgency_level']}")
        
        # Borrower insights
        borrower_sentiment = analysis['borrower_sentiment']
        console.print(f"\n[bold cyan]Borrower Profile:[/bold cyan]")
        console.print(f"  Sentiment: {borrower_sentiment['overall']} ({borrower_sentiment['start']} → {borrower_sentiment['end']})")
        
        risks = analysis['borrower_risks']
        console.print(f"\n[bold cyan]Risk Assessment:[/bold cyan]")
        console.print(f"  Delinquency Risk: {risks['delinquency_risk']:.2f}")
        console.print(f"  Churn Risk: {risks['churn_risk']:.2f}")
        console.print(f"  Complaint Risk: {risks['complaint_risk']:.2f}")
        console.print(f"  Refinance Likelihood: {risks['refinance_likelihood']:.2f}")
        
        # Advisor performance
        advisor = analysis['advisor_metrics']
        console.print(f"\n[bold cyan]Advisor Performance:[/bold cyan]")
        console.print(f"  Empathy Score: {advisor['empathy_score']:.1f}/10")
        console.print(f"  Compliance Adherence: {advisor['compliance_adherence']:.1f}/10")
        console.print(f"  Solution Effectiveness: {advisor['solution_effectiveness']:.1f}/10")
        
        if advisor['coaching_opportunities']:
            console.print(f"\n[bold cyan]Coaching Opportunities:[/bold cyan]")
            for opportunity in advisor['coaching_opportunities']:
                console.print(f"  • {opportunity}")
        
        # Compliance and resolution
        console.print(f"\n[bold cyan]Resolution Status:[/bold cyan]")
        console.print(f"  Issue Resolved: {'✅' if analysis['issue_resolved'] else '❌'}")
        console.print(f"  First Call Resolution: {'✅' if analysis['first_call_resolution'] else '❌'}")
        console.print(f"  Escalation Needed: {'🚨 Yes' if analysis['escalation_needed'] else '✅ No'}")
        
        if analysis['compliance_flags']:
            console.print(f"\n[bold yellow]Compliance Flags:[/bold yellow]")
            for flag in analysis['compliance_flags']:
                console.print(f"  ⚠️  {flag}")
        
    else:
        print_error(f"Report failed: {result['error']}")


@app.command("analysis-metrics")
def analysis_metrics():
    """Show aggregate analysis metrics dashboard."""
    client = get_client()
    
    console.print("📊 [bold magenta]Getting analysis metrics...[/bold magenta]")
    result = client.send_command('analysis_metrics')
    
    if result['success']:
        metrics = result['metrics']
        
        console.print(f"\n📈 [bold cyan]Analysis Dashboard[/bold cyan]")
        console.print(f"Total Analyses: [green]{metrics['total_analyses']}[/green]")
        console.print(f"Average Confidence: [green]{metrics['avg_confidence_score']:.2f}[/green]")
        
        console.print(f"\n[bold cyan]Performance Metrics:[/bold cyan]")
        console.print(f"  First Call Resolution Rate: [green]{metrics['first_call_resolution_rate']:.1f}%[/green]")
        console.print(f"  Escalation Rate: [yellow]{metrics['escalation_rate']:.1f}%[/yellow]")
        console.print(f"  Average Empathy Score: [green]{metrics['avg_empathy_score']:.1f}/10[/green]")
        
        console.print(f"\n[bold cyan]Risk Indicators:[/bold cyan]")
        console.print(f"  Average Delinquency Risk: [yellow]{metrics['avg_delinquency_risk']:.2f}[/yellow]")
        console.print(f"  Average Churn Risk: [yellow]{metrics['avg_churn_risk']:.2f}[/yellow]")
        
        if metrics['top_intents']:
            console.print(f"\n[bold cyan]Top Call Intents:[/bold cyan]")
            for intent, count in list(metrics['top_intents'].items())[:5]:
                console.print(f"  {intent}: [green]{count}[/green]")
        
        if metrics['urgency_distribution']:
            console.print(f"\n[bold cyan]Urgency Distribution:[/bold cyan]")
            for urgency, count in metrics['urgency_distribution'].items():
                console.print(f"  {urgency}: [green]{count}[/green]")
                
    else:
        print_error(f"Metrics failed: {result['error']}")


@app.command("risk-report")
def risk_report(
    threshold: float = typer.Option(0.7, "--threshold", "-t", help="Minimum risk threshold (0.0-1.0)")
):
    """Show high-risk borrower report."""
    client = get_client()
    
    params = {'threshold': threshold}
    
    console.print(f"🚨 [bold magenta]Getting high-risk report (threshold: {threshold})...[/bold magenta]")
    result = client.send_command('risk_report', params)
    
    if result['success']:
        risk_data = result['high_risk_analyses']
        
        # High delinquency risk
        high_delinquency = risk_data['high_delinquency_risk']
        if high_delinquency:
            console.print(f"\n🚨 [bold red]High Delinquency Risk ({len(high_delinquency)} cases)[/bold red]")
            for case in high_delinquency[:10]:  # Show top 10
                console.print(f"  Transcript: {case['transcript_id']}")
                console.print(f"  Risk Score: {case['delinquency_risk']:.2f}")
                console.print(f"  Intent: {case['primary_intent']}")
                console.print(f"  Summary: {case['summary']}")
                console.print()
        
        # High churn risk
        high_churn = risk_data['high_churn_risk']
        if high_churn:
            console.print(f"\n⚠️  [bold yellow]High Churn Risk ({len(high_churn)} cases)[/bold yellow]")
            for case in high_churn[:10]:  # Show top 10
                console.print(f"  Transcript: {case['transcript_id']}")
                console.print(f"  Risk Score: {case['churn_risk']:.2f}")
                console.print(f"  Intent: {case['primary_intent']}")
                console.print(f"  Summary: {case['summary']}")
                console.print()
                
        if not high_delinquency and not high_churn:
            console.print(f"✅ No high-risk cases found above threshold {threshold}")
            
    else:
        print_error(f"Risk report failed: {result['error']}")


@app.command("generate-action-plan")
def generate_action_plan(
    analysis_id: Optional[str] = typer.Option(None, "--analysis-id", "-a", help="Analysis ID to generate plan from"),
    transcript_id: Optional[str] = typer.Option(None, "--transcript-id", "-t", help="Transcript ID to generate plan from")
):
    """Generate four-layer action plan from analysis."""
    client = get_client()
    
    if not analysis_id and not transcript_id:
        console.print("❌ Must specify either --analysis-id or --transcript-id")
        raise typer.Exit(1)
    
    params = {}
    if analysis_id:
        params['analysis_id'] = analysis_id
    if transcript_id:
        params['transcript_id'] = transcript_id
    
    console.print("🔄 [bold blue]Generating action plan...[/bold blue]")
    result = client.send_command('generate_action_plan', params)
    
    if result['success']:
        console.print(f"✅ Generated action plan: {result['plan_id']}")
        console.print(f"Risk Level: {result['risk_level']}")
        console.print(f"Approval Route: {result['approval_route']}")
        console.print(f"Queue Status: {result['queue_status']}")
        console.print(f"Message: {result['message']}")
            
    else:
        print_error(f"Action plan generation failed: {result['error']}")


@app.command("view-action-plan")
def view_action_plan(
    plan_id: str = typer.Argument(..., help="Action plan ID"),
    layer: Optional[str] = typer.Option(None, "--layer", "-l", help="Specific layer to view (borrower, advisor, supervisor, leadership)")
):
    """View action plan details."""
    client = get_client()
    
    params = {'plan_id': plan_id}
    if layer:
        params['layer'] = layer
    
    console.print(f"📋 [bold blue]Getting action plan {plan_id}...[/bold blue]")
    result = client.send_command('get_action_plan', params)
    
    if result['success']:
        plan = result['action_plan']
        
        console.print(f"\n📄 [bold green]Action Plan Report[/bold green]")
        console.print(f"Plan ID: {plan['plan_id']}")
        console.print(f"Transcript ID: {plan['transcript_id']}")
        console.print(f"Risk Level: {plan['risk_level']}")
        console.print(f"Status: {plan['queue_status']}")
        console.print(f"Created: {plan.get('created_at', 'N/A')}")
        
        if layer:
            # Show specific layer
            if layer in plan:
                console.print(f"\n🎯 [bold cyan]{layer.title()} Plan[/bold cyan]")
                _display_plan_layer(plan[layer], layer)
        else:
            # Show all layers
            for layer_name in ['borrower_plan', 'advisor_plan', 'supervisor_plan', 'leadership_plan']:
                if layer_name in plan:
                    layer_display = layer_name.replace('_plan', '').title()
                    console.print(f"\n🎯 [bold cyan]{layer_display} Plan[/bold cyan]")
                    _display_plan_layer(plan[layer_name], layer_name)
                    
    else:
        print_error(f"Failed to get action plan: {result['error']}")


@app.command("action-plan-queue")
def action_plan_queue(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by queue status")
):
    """View action plan approval queue."""
    client = get_client()
    
    params = {}
    if status:
        params['status'] = status
    
    console.print("📋 [bold blue]Getting approval queue...[/bold blue]")
    result = client.send_command('get_action_queue', params)
    
    if result['success']:
        queue = result['plans']
        
        if not queue:
            console.print("✅ No action plans in queue")
            return
        
        console.print(f"\n📊 [bold green]Action Plan Queue ({len(queue)} items)[/bold green]")
        
        for plan in queue:
            console.print(f"\nPlan ID: {plan['plan_id']}")
            console.print(f"  Transcript: {plan['transcript_id']}")
            console.print(f"  Risk Level: {plan['risk_level']}")
            console.print(f"  Status: {plan['queue_status']}")
            console.print(f"  Routing: {plan['approval_route']}")
            if plan.get('routing_reason'):
                console.print(f"  Reason: {plan['routing_reason']}")
            console.print(f"  Created: {plan.get('created_at', 'N/A')}")
            
    else:
        print_error(f"Failed to get queue: {result['error']}")


@app.command("approve-action-plan")
def approve_action_plan(
    plan_id: str = typer.Argument(..., help="Action plan ID to approve"),
    approver: str = typer.Option("CLI_USER", "--approver", "-by", help="Approver identifier")
):
    """Approve an action plan."""
    client = get_client()
    
    params = {
        'plan_id': plan_id,
        'approved_by': approver,
        'action': 'approve'
    }
    
    console.print(f"✅ [bold green]Approving action plan {plan_id}...[/bold green]")
    result = client.send_command('approve_action_plan', params)
    
    if result['success']:
        console.print("✅ Action plan approved successfully")
    else:
        print_error(f"Approval failed: {result['error']}")


@app.command("action-plan-summary")
def action_plan_summary():
    """Show action plan summary metrics."""
    client = get_client()
    
    console.print("📊 [bold blue]Getting action plan metrics...[/bold blue]")
    result = client.send_command('action_plan_summary', {})
    
    if result['success']:
        metrics = result['summary']
        
        console.print(f"\n📈 [bold green]Action Plan Dashboard[/bold green]")
        console.print(f"Total Plans: {metrics['total_plans']}")
        console.print(f"Pending Approvals: {metrics['pending_approvals']}")
        console.print(f"Auto-Executable: {metrics['auto_executable_percentage']}%")
        
        console.print(f"\n📋 Status Distribution:")
        for status, count in metrics['status_distribution'].items():
            console.print(f"  {status}: {count}")
        
        console.print(f"\n⚠️  Risk Distribution:")
        for risk, count in metrics['risk_distribution'].items():
            console.print(f"  {risk}: {count}")
        
        console.print(f"\n🔄 Route Distribution:")
        for route, count in metrics['route_distribution'].items():
            console.print(f"  {route}: {count}")
            
    else:
        print_error(f"Failed to get metrics: {result['error']}")


def _display_plan_layer(layer_data: Dict[str, Any], layer_type: str):
    """Display a specific action plan layer."""
    if layer_type == 'borrower_plan':
        if 'immediate_actions' in layer_data:
            console.print("\n🚀 Immediate Actions:")
            for action in layer_data['immediate_actions']:
                priority_color = "red" if action.get('priority') == 'high' else "yellow" if action.get('priority') == 'medium' else "green"
                console.print(f"  • [{priority_color}]{action.get('action', 'N/A')}[/{priority_color}]")
                console.print(f"    Timeline: {action.get('timeline', 'N/A')}")
                console.print(f"    Priority: {action.get('priority', 'N/A')}")
                if action.get('auto_executable'):
                    console.print("    ✅ Auto-executable")
                console.print()
        
        if 'follow_ups' in layer_data:
            console.print("📅 Follow-ups:")
            for followup in layer_data['follow_ups']:
                console.print(f"  • {followup.get('action', 'N/A')}")
                console.print(f"    Due: {followup.get('due_date', 'N/A')}")
                console.print(f"    Owner: {followup.get('owner', 'N/A')}")
                console.print()
    
    elif layer_type == 'advisor_plan':
        if 'coaching_items' in layer_data:
            console.print("\n💡 Coaching Items:")
            for item in layer_data['coaching_items']:
                console.print(f"  • {item}")
        
        if 'performance_feedback' in layer_data and layer_data['performance_feedback']:
            feedback = layer_data['performance_feedback']
            console.print("\n📊 Performance Feedback:")
            if 'strengths' in feedback:
                console.print("  ✅ Strengths:")
                for strength in feedback['strengths']:
                    console.print(f"    • {strength}")
            if 'improvements' in feedback:
                console.print("  🔧 Areas for Improvement:")
                for improvement in feedback['improvements']:
                    console.print(f"    • {improvement}")
    
    elif layer_type == 'supervisor_plan':
        if 'escalation_items' in layer_data:
            console.print("\n⚠️  Escalation Items:")
            for item in layer_data['escalation_items']:
                priority_color = "red" if item.get('priority') == 'high' else "yellow" if item.get('priority') == 'medium' else "green"
                console.print(f"  • [{priority_color}]{item.get('item', 'N/A')}[/{priority_color}]")
                console.print(f"    Reason: {item.get('reason', 'N/A')}")
                console.print(f"    Action: {item.get('action_required', 'N/A')}")
                console.print()
        
        if 'team_patterns' in layer_data:
            console.print("📊 Team Patterns:")
            for pattern in layer_data['team_patterns']:
                console.print(f"  • {pattern}")
    
    elif layer_type == 'leadership_plan':
        if 'portfolio_insights' in layer_data:
            console.print("\n📈 Portfolio Insights:")
            for insight in layer_data['portfolio_insights']:
                console.print(f"  • {insight}")
        
        if 'strategic_opportunities' in layer_data:
            console.print("💰 Strategic Opportunities:")
            for opp in layer_data['strategic_opportunities']:
                console.print(f"  • {opp}")


@app.command("execute-plan")
def execute_plan(
    plan_id: str = typer.Argument(..., help="Action plan ID to execute"),
    mode: str = typer.Option("auto", "--mode", "-m", help="Execution mode: auto (respects approval) or manual (override for testing)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be executed without actually executing")
):
    """Execute an action plan using intelligent LLM-powered execution."""
    client = get_client()
    
    if dry_run:
        console.print(f"🔍 [bold yellow]Dry run - showing what would be executed for plan {plan_id}[/bold yellow]")
        result = client.send_command('execute_plan_dry_run', {
            'plan_id': plan_id,
            'mode': mode
        })
    else:
        console.print(f"⚡ [bold green]Executing action plan {plan_id}...[/bold green]")
        result = client.send_command('execute_plan', {
            'plan_id': plan_id,
            'mode': mode
        })
    
    if result['success']:
        # Handle dry-run response
        if 'dry_run_result' in result:
            dry_run_result = result['dry_run_result']
            console.print(f"\n🔍 [bold cyan]Dry Run Preview for Plan {dry_run_result['plan_id']}[/bold cyan]")
            console.print(f"📊 Total actions would execute: {dry_run_result['total_actions_would_execute']}")
            
            # Show actions by layer
            console.print("\n📋 Actions by Layer:")
            for layer, count in dry_run_result['actions_by_layer'].items():
                if count > 0:
                    console.print(f"  • {layer.title()}: {count} actions")
            
            # Show estimated artifacts
            console.print("\n📄 Estimated Artifacts:")
            artifacts = dry_run_result['estimated_artifacts']
            console.print(f"  • Emails: ~{int(artifacts['emails'])} files")
            console.print(f"  • Documents: ~{int(artifacts['documents'])} files")  
            console.print(f"  • Callbacks: ~{int(artifacts['callbacks'])} files")
            
            console.print(f"\n💡 {dry_run_result['note']}")
            return
        
        execution_result = result['execution_result']
        
        if execution_result['status'] == 'pending_approval':
            console.print(f"⏳ [bold yellow]Plan requires approval[/bold yellow]")
            console.print(f"Status: {execution_result['message']}")
            console.print(f"Risk Level: {execution_result['risk_level']}")
            return
        
        if execution_result['status'] == 'success':
            console.print(f"✅ [bold green]Execution completed successfully![/bold green]")
            console.print(f"Execution ID: {execution_result['execution_id']}")
            
            # Show what was executed
            results = execution_result['results']
            total_actions = sum(len(actions) for actions in results.values())
            console.print(f"Total Actions Executed: {total_actions}")
            
            for action_type, actions in results.items():
                if actions:
                    console.print(f"\n📋 [bold cyan]{action_type.replace('_', ' ').title()}:[/bold cyan]")
                    for action in actions:
                        # Fixed: Show ✅ for successful completion, ❌ only for actual errors
                        status = action.get('status', 'unknown').lower()
                        if status in ['success', 'completed', 'generated', 'delivered', 'sent', 'approved']:
                            status_icon = "✅"
                        elif status in ['error', 'failed', 'rejected']:
                            status_icon = "❌"
                        else:
                            # For unknown statuses, show neutral indicator
                            status_icon = "⚠️"
                        console.print(f"  {status_icon} {action.get('action_source', 'Action')}: {action.get('status', 'Unknown')}")
            
            # Show artifacts created
            artifacts = execution_result.get('artifacts_created', [])
            if artifacts:
                console.print(f"\n📄 [bold magenta]Artifacts Created ({len(artifacts)}):[/bold magenta]")
                for artifact in artifacts:
                    if artifact:
                        console.print(f"  📁 {artifact}")
                        
        else:
            console.print(f"❌ [bold red]Execution failed[/bold red]")
            console.print(f"Error: {execution_result.get('message', 'Unknown error')}")
            
    else:
        print_error(f"Failed to execute plan: {result['error']}")


@app.command("execution-history")
def execution_history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent executions to show")
):
    """Show recent execution history."""
    client = get_client()
    
    console.print(f"📚 [bold blue]Getting execution history (last {limit})...[/bold blue]")
    result = client.send_command('execution_history', {'limit': limit})
    
    if result['success']:
        executions = result['executions']
        
        if not executions:
            console.print("No executions found.")
            return
        
        console.print(f"\n📋 [bold green]Recent Executions[/bold green]")
        console.print("-" * 80)
        
        for execution in executions:
            status_icon = "✅" if execution['status'] == 'success' else "❌"
            console.print(f"{status_icon} {execution['execution_id']} | Plan: {execution['plan_id']}")
            console.print(f"   📅 {execution['executed_at']} | Artifacts: {execution['artifacts_created']} | Errors: {execution['errors_count']}")
            console.print()
            
    else:
        print_error(f"Failed to get execution history: {result['error']}")


@app.command("view-artifacts")
def view_artifacts(
    artifact_type: str = typer.Option("all", "--type", "-t", help="Type of artifacts to view: emails, callbacks, documents, all"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent artifacts to show")
):
    """View execution artifacts (emails, documents, callbacks)."""
    client = get_client()
    
    console.print(f"📁 [bold blue]Getting {artifact_type} artifacts (last {limit})...[/bold blue]")
    result = client.send_command('view_artifacts', {
        'type': artifact_type,
        'limit': limit
    })
    
    if result['success']:
        artifacts = result['artifacts']
        
        if not artifacts:
            console.print(f"No {artifact_type} artifacts found.")
            return
        
        console.print(f"\n📄 [bold green]{artifact_type.title()} Artifacts[/bold green]")
        console.print("-" * 80)
        
        for artifact in artifacts:
            console.print(f"📁 {artifact['filename']}")
            console.print(f"   📅 {artifact['created']} | Size: {artifact['size']} bytes")
            if artifact.get('preview'):
                console.print(f"   👀 {artifact['preview'][:100]}...")
            console.print()
            
    else:
        print_error(f"Failed to get artifacts: {result['error']}")


@app.command("execution-metrics")  
def execution_metrics():
    """Show execution metrics and statistics."""
    client = get_client()
    
    console.print("📊 [bold blue]Getting execution metrics...[/bold blue]")
    result = client.send_command('execution_metrics', {})
    
    if result['success']:
        stats = result['stats']
        
        console.print(f"\n📈 [bold green]Execution Dashboard (Last 7 Days)[/bold green]")
        console.print(f"Total Executions: {stats['total_executions']}")
        console.print(f"Success Rate: {stats['success_rate']}%")
        console.print(f"Artifacts Created: {stats['total_artifacts_created']}")
        
        console.print(f"\n📊 Status Breakdown:")
        for status, count in stats['status_breakdown'].items():
            console.print(f"  {status}: {count}")
        
        console.print(f"\n🎯 Actions by Source:")
        for source, count in stats['actions_by_source'].items():
            console.print(f"  {source}: {count}")
        
        console.print(f"\n🛠️  Tools Usage:")
        for tool, count in stats['tools_usage'].items():
            console.print(f"  {tool}: {count}")
            
    else:
        print_error(f"Failed to get execution metrics: {result['error']}")


# ========== Decision Agent Commands ==========

@app.command("get-approval-queue")
def get_approval_queue(
    route: Optional[str] = typer.Option(None, help="Filter by approval route: advisor_approval, supervisor_approval")
):
    """Get actions pending approval in the Decision Agent queue."""
    client = get_client()
    result = client.send_command('get_approval_queue', {'route': route})
    
    if result['success']:
        queue = result['queue']
        
        if not queue:
            print_info("No actions pending approval")
            return
        
        console.print(f"\n📋 Approval Queue ({result['total_pending']} items)")
        console.print("=" * 60)
        
        # Group by approval route
        by_route = {}
        for item in queue:
            route = item['approval_route']
            if route not in by_route:
                by_route[route] = []
            by_route[route].append(item)
        
        for route, items in by_route.items():
            console.print(f"\n🎯 {route.replace('_', ' ').title()} ({len(items)} items):")
            
            for item in items:
                risk_color = {"high": "red", "medium": "yellow", "low": "green"}.get(item['risk_level'], "white")
                console.print(f"  [{risk_color}]●[/] {item['action_id']}: {item['action_text'][:50]}...")
                console.print(f"    Risk: {item['risk_level']} (score: {item['risk_score']:.3f})")
                console.print(f"    Financial: {item['financial_impact']}, Compliance: {item['compliance_impact']}")
                console.print(f"    Created: {item['created_at']}")
                console.print()
    
    else:
        print_error(f"Failed to get approval queue: {result['error']}")


@app.command("approve-action")
def approve_action(
    action_id: str = typer.Argument(help="Action ID to approve"),
    approved_by: str = typer.Option("CLI_USER", help="Approver identifier"),
    notes: str = typer.Option("", help="Approval notes")
):
    """Approve a specific action in the queue."""
    client = get_client()
    result = client.send_command('approve_action', {
        'action_id': action_id,
        'approved_by': approved_by,
        'notes': notes
    })
    
    if result['success']:
        print_success(result['message'])
    else:
        print_error(f"Failed to approve action: {result['error']}")


@app.command("reject-action")  
def reject_action(
    action_id: str = typer.Argument(help="Action ID to reject"),
    rejected_by: str = typer.Option("CLI_USER", help="Rejector identifier"),
    reason: str = typer.Option("No reason provided", help="Rejection reason")
):
    """Reject a specific action in the queue."""
    client = get_client()
    result = client.send_command('reject_action', {
        'action_id': action_id,
        'rejected_by': rejected_by,
        'reason': reason
    })
    
    if result['success']:
        print_success(f"{result['message']} - Reason: {result['reason']}")
    else:
        print_error(f"Failed to reject action: {result['error']}")


@app.command("bulk-approve")
def bulk_approve_actions(
    action_ids: str = typer.Argument(help="Comma-separated list of action IDs to approve"),
    approved_by: str = typer.Option("CLI_USER", help="Approver identifier"),
    notes: str = typer.Option("Bulk approval", help="Approval notes")
):
    """Bulk approve multiple actions."""
    client = get_client()
    
    # Parse comma-separated action IDs
    ids_list = [aid.strip() for aid in action_ids.split(',')]
    
    result = client.send_command('bulk_approve_actions', {
        'action_ids': ids_list,
        'approved_by': approved_by,
        'notes': notes
    })
    
    if result['success']:
        print_success(result['message'])
        console.print(f"Approved: {result['approved_count']}/{result['total_requested']} actions")
    else:
        print_error(f"Failed to bulk approve: {result['error']}")


@app.command("approval-metrics")
def approval_metrics():
    """Get approval queue metrics and statistics."""
    client = get_client()
    result = client.send_command('approval_metrics')
    
    if result['success']:
        metrics = result['metrics']
        
        console.print(f"\n📊 Approval Metrics")
        console.print("=" * 40)
        console.print(f"Total Actions: {metrics['total_actions']}")
        console.print(f"Pending Approvals: {metrics['pending_approvals']}")
        console.print(f"Approval Rate: {metrics['approval_rate']}%")
        console.print(f"Avg Approval Time: {metrics['avg_approval_time_hours']:.1f} hours")
        
        console.print(f"\n📈 Queue Status:")
        for route, statuses in metrics.get('queue_status', {}).items():
            console.print(f"  {route.replace('_', ' ').title()}:")
            for status, count in statuses.items():
                console.print(f"    {status}: {count}")
        
        console.print(f"\n⚠️  Risk Distribution:")
        for risk_level, count in metrics.get('risk_distribution', {}).items():
            risk_color = {"high": "red", "medium": "yellow", "low": "green"}.get(risk_level, "white")
            console.print(f"  [{risk_color}]{risk_level}[/]: {count}")
    
    else:
        print_error(f"Failed to get approval metrics: {result['error']}")


@app.command("decision-agent-summary")
def decision_agent_summary():
    """Get Decision Agent configuration and processing summary."""
    client = get_client()
    result = client.send_command('decision_agent_summary')
    
    if result['success']:
        summary = result['summary']
        
        console.print(f"\n🤖 Decision Agent Summary")
        console.print("=" * 40)
        console.print(f"Agent Version: {summary['agent_version']}")
        
        console.print(f"\n⚙️  Configuration:")
        config = summary['config']
        console.print(f"  Auto Approval Threshold: {config['auto_approval_threshold']}")
        console.print(f"  Supervisor Threshold: {config['supervisor_threshold']}")
        console.print(f"  Financial Always Supervisor: {config['financial_always_supervisor']}")
        console.print(f"  Compliance Always Supervisor: {config['compliance_always_supervisor']}")
        
        console.print(f"\n📊 Processing Summary:")
        processing = summary['summary']
        console.print(f"  Total Decisions: {processing['total_decisions']}")
        console.print(f"  Total Actions Processed: {processing.get('total_actions_processed', 0)}")
        console.print(f"  Auto Approval Rate: {processing.get('auto_approval_rate', 0)}%")
        console.print(f"  Avg Actions per Plan: {processing.get('avg_actions_per_plan', 0)}")
        
        if processing.get('routing_distribution'):
            console.print(f"\n🎯 Routing Distribution:")
            for route, count in processing['routing_distribution'].items():
                console.print(f"  {route.replace('_', ' ').title()}: {count}")
    
    else:
        print_error(f"Failed to get decision agent summary: {result['error']}")


if __name__ == "__main__":
    app()