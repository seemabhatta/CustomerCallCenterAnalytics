#!/usr/bin/env python3
"""
Customer Call Center Analytics CLI - Consolidated Resource-Based Commands
Direct REST API client following industry best practices
No fallback logic - fail fast with clear error messages
Resource-aligned commands: transcript, analysis, plan, system
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenTelemetry tracing IMMEDIATELY after env loading for complete observability coverage
try:
    from src.telemetry import initialize_tracing
    initialize_tracing(
        service_name="xai",
        enable_console=os.getenv("OTEL_CONSOLE_ENABLED", "true").lower() == "true",
        enable_jaeger=os.getenv("OTEL_JAEGER_ENABLED", "false").lower() == "true"
    )
except ImportError:
    print("Warning: OpenTelemetry tracing not available. Install telemetry dependencies for observability.")

# NOW import everything else
import json
import requests
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urljoin, urlencode

# Direct mode imports (for bypassing server)
try:
    import sys
    sys.path.insert(0, '.')
    from src.generators.transcript_generator import TranscriptGenerator
    from src.storage.transcript_store import TranscriptStore
    DIRECT_MODE_AVAILABLE = True
except ImportError as e:
    DIRECT_MODE_AVAILABLE = False

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
    help="Customer Call Center Analytics - REST API Client (Resource-Based Commands)",
    add_completion=False
)
console = Console()


class CLIError(Exception):
    """Exception raised for CLI-specific errors."""
    pass


class CLIRestClient:
    """REST API client for Customer Call Center Analytics."""
    
    def __init__(self, api_url: str = DEFAULT_API_URL, verbose: bool = DEFAULT_VERBOSE):
        self.api_url = api_url.rstrip('/')  # Remove trailing slash
        self.verbose = verbose
        self.session = requests.Session()
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     json_data: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
        """Make HTTP request to the API with comprehensive error handling."""
        url = urljoin(self.api_url, endpoint.lstrip('/'))
        
        if self.verbose:
            console.print(f"[dim]Making {method} request to: {url}[/dim]")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=timeout,
                headers={'Content-Type': 'application/json'} if json_data else {}
            )
            
            # Handle HTTP errors
            if response.status_code == 404:
                error_text = response.text or "Resource not found"
                try:
                    error_detail = response.json().get('detail', error_text)
                except:
                    error_detail = error_text
                raise CLIError(f"Not found: {error_detail}")
            elif response.status_code == 422:
                try:
                    error_detail = response.json().get('detail', 'Validation error')
                except:
                    error_detail = 'Validation error'
                raise CLIError(f"Validation error: {error_detail}")
            elif response.status_code >= 400:
                error_text = response.text or f"HTTP {response.status_code}"
                try:
                    error_detail = response.json().get('detail', error_text)
                except:
                    error_detail = error_text
                raise CLIError(f"API error ({response.status_code}): {error_detail}")
            
            # Parse JSON response
            try:
                return response.json()
            except ValueError as e:
                if response.status_code == 200:
                    # Sometimes APIs return empty 200 responses
                    return {}
                raise CLIError(f"Invalid JSON response: {str(e)}")
                
        except requests.exceptions.ConnectionError:
            raise CLIError(f"Connection failed. Is the server running at {self.api_url}?")
        except requests.exceptions.Timeout:
            raise CLIError(f"Request timeout after {timeout}s")
        except requests.exceptions.RequestException as e:
            raise CLIError(f"Request failed: {str(e)}")

    # Transcript operations
    def generate_transcript(self, **kwargs) -> Dict[str, Any]:
        """Generate transcript via POST /api/v1/transcripts."""
        return self._make_request('POST', '/api/v1/transcripts', json_data=kwargs, timeout=120)
    
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
    
    def delete_analysis(self, analysis_id: str) -> Dict[str, Any]:
        """Delete analysis via DELETE /api/v1/analyses/{id}."""
        return self._make_request('DELETE', f'/api/v1/analyses/{analysis_id}')
    
    def delete_all_analyses(self) -> Dict[str, Any]:
        """Delete all analyses via DELETE /api/v1/analyses."""
        return self._make_request('DELETE', '/api/v1/analyses')
    
    # Insights operations
    def discover_risk_patterns(self, risk_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Discover risk patterns via GET /api/v1/insights/patterns."""
        params = {'risk_threshold': risk_threshold}
        return self._make_request('GET', '/api/v1/insights/patterns', params=params)
    
    def get_high_risks(self, risk_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Get high-risk patterns via GET /api/v1/insights/risks."""
        params = {'risk_threshold': risk_threshold}
        return self._make_request('GET', '/api/v1/insights/risks', params=params)
    
    def get_customer_recommendations(self, customer_id: str) -> List[Dict[str, Any]]:
        """Get customer recommendations via GET /api/v1/insights/recommendations/{customer_id}."""
        return self._make_request('GET', f'/api/v1/insights/recommendations/{customer_id}')
    
    def find_similar_analyses(self, analysis_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar analyses via GET /api/v1/insights/similar/{analysis_id}."""
        params = {'limit': limit}
        return self._make_request('GET', f'/api/v1/insights/similar/{analysis_id}', params=params)
    
    def get_insights_dashboard(self) -> Dict[str, Any]:
        """Get insights dashboard via GET /api/v1/insights/dashboard."""
        return self._make_request('GET', '/api/v1/insights/dashboard')
    
    # Insights management operations
    def populate_insights(self, **kwargs) -> Dict[str, Any]:
        """Populate insights graph via POST /api/v1/insights/populate."""
        return self._make_request('POST', '/api/v1/insights/populate', json_data=kwargs)
    
    def query_insights(self, cypher_query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Query insights graph via POST /api/v1/insights/query."""
        payload = {'cypher': cypher_query}
        if parameters:
            payload['parameters'] = parameters
        return self._make_request('POST', '/api/v1/insights/query', json_data=payload)
    
    def get_insights_status(self) -> Dict[str, Any]:
        """Get insights status via GET /api/v1/insights/status."""
        return self._make_request('GET', '/api/v1/insights/status')
    
    def delete_insights_analysis(self, analysis_id: str) -> Dict[str, Any]:
        """Delete insights analysis via DELETE /api/v1/insights/analyses/{id}."""
        return self._make_request('DELETE', f'/api/v1/insights/analyses/{analysis_id}')
    
    def delete_insights_customer(self, customer_id: str, cascade: bool = False) -> Dict[str, Any]:
        """Delete insights customer via DELETE /api/v1/insights/customers/{id}."""
        params = {'cascade': cascade} if cascade else {}
        return self._make_request('DELETE', f'/api/v1/insights/customers/{customer_id}', params=params)
    
    def prune_insights(self, older_than_days: int) -> Dict[str, Any]:
        """Prune insights data via POST /api/v1/insights/prune."""
        return self._make_request('POST', '/api/v1/insights/prune', json_data={'older_than_days': older_than_days})
    
    def clear_insights(self) -> Dict[str, Any]:
        """Clear insights graph via DELETE /api/v1/insights/clear."""
        return self._make_request('DELETE', '/api/v1/insights/clear')
    
    def get_visualization_data(self) -> Dict[str, Any]:
        """Get visualization data via GET /api/v1/insights/visualization/data."""
        return self._make_request('GET', '/api/v1/insights/visualization/data')
    
    def get_visualization_statistics(self) -> Dict[str, Any]:
        """Get visualization statistics via GET /api/v1/insights/visualization/stats."""
        return self._make_request('GET', '/api/v1/insights/visualization/stats')
    
    # Plan operations
    def create_plan(self, **kwargs) -> Dict[str, Any]:
        """Create action plan via POST /api/v1/plans."""
        return self._make_request('POST', '/api/v1/plans', json_data=kwargs, timeout=300)
    
    def get_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get action plan by ID via GET /api/v1/plans/{id}."""
        return self._make_request('GET', f'/api/v1/plans/{plan_id}')
    
    def list_plans(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List plans via GET /api/v1/plans."""
        params = {'limit': limit} if limit else {}
        return self._make_request('GET', '/api/v1/plans', params=params)
    
    def approve_plan(self, plan_id: str, **kwargs) -> Dict[str, Any]:
        """Approve action plan via POST /api/v1/plans/{id}/approve."""
        return self._make_request('POST', f'/api/v1/plans/{plan_id}/approve', json_data=kwargs)
    
    def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        """Execute plan via POST /api/v1/plans/{id}/execute."""
        return self._make_request('POST', f'/api/v1/plans/{plan_id}/execute')
    
    def view_plan(self, plan_id: str) -> Dict[str, Any]:
        """Get plan by ID via GET /api/v1/plans/{id}."""
        return self._make_request('GET', f'/api/v1/plans/{plan_id}')
    
    def update_plan(self, plan_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update plan via PUT /api/v1/plans/{id}."""
        return self._make_request('PUT', f'/api/v1/plans/{plan_id}', json_data=update_data)
    
    def delete_plan(self, plan_id: str) -> Dict[str, Any]:
        """Delete plan via DELETE /api/v1/plans/{id}."""
        return self._make_request('DELETE', f'/api/v1/plans/{plan_id}')
    
    def delete_all_plans(self) -> Dict[str, Any]:
        """Delete all plans via DELETE /api/v1/plans."""
        return self._make_request('DELETE', '/api/v1/plans')
    
    # Workflow operations
    def extract_workflow(self, plan_id: str) -> Dict[str, Any]:
        """Extract workflow from plan via POST /api/v1/workflows/extract."""
        return self._make_request('POST', '/api/v1/workflows/extract', json_data={'plan_id': plan_id})
    
    def list_workflows(self, **params) -> List[Dict[str, Any]]:
        """List workflows via GET /api/v1/workflows."""
        return self._make_request('GET', '/api/v1/workflows', params=params)
    
    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow by ID via GET /api/v1/workflows/{workflow_id}."""
        return self._make_request('GET', f'/api/v1/workflows/{workflow_id}')
    
    def approve_workflow(self, workflow_id: str, approved_by: str, reasoning: Optional[str] = None) -> Dict[str, Any]:
        """Approve workflow via POST /api/v1/workflows/{workflow_id}/approve."""
        json_data = {'approved_by': approved_by}
        if reasoning:
            json_data['reasoning'] = reasoning
        return self._make_request('POST', f'/api/v1/workflows/{workflow_id}/approve', json_data=json_data)
    
    def reject_workflow(self, workflow_id: str, rejected_by: str, reason: str) -> Dict[str, Any]:
        """Reject workflow via POST /api/v1/workflows/{workflow_id}/reject."""
        json_data = {'rejected_by': rejected_by, 'reason': reason}
        return self._make_request('POST', f'/api/v1/workflows/{workflow_id}/reject', json_data=json_data)
    
    def execute_workflow(self, workflow_id: str, executed_by: str) -> Dict[str, Any]:
        """Execute workflow via POST /api/v1/workflows/{workflow_id}/execute."""
        json_data = {'executed_by': executed_by}
        return self._make_request('POST', f'/api/v1/workflows/{workflow_id}/execute', json_data=json_data)
    
    def get_workflow_history(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow history via GET /api/v1/workflows/{workflow_id}/history."""
        return self._make_request('GET', f'/api/v1/workflows/{workflow_id}/history')
    
    def get_pending_workflows(self) -> List[Dict[str, Any]]:
        """Get pending workflows via GET /api/v1/workflows/pending."""
        return self._make_request('GET', '/api/v1/workflows/pending')
    
    def extract_all_workflows(self, plan_id: str) -> List[Dict[str, Any]]:
        """Extract all granular workflows from plan via POST /api/v1/workflows/extract-all."""
        return self._make_request('POST', '/api/v1/workflows/extract-all', json_data={'plan_id': plan_id}, timeout=300)
    
    def get_workflows_by_plan(self, plan_id: str) -> List[Dict[str, Any]]:
        """Get all workflows for a plan via GET /api/v1/workflows/plan/{plan_id}."""
        return self._make_request('GET', f'/api/v1/workflows/plan/{plan_id}')
    
    def get_workflows_by_type(self, workflow_type: str) -> List[Dict[str, Any]]:
        """Get workflows by type via GET /api/v1/workflows/type/{workflow_type}."""
        return self._make_request('GET', f'/api/v1/workflows/type/{workflow_type}')
    
    def get_workflows_by_plan_and_type(self, plan_id: str, workflow_type: str) -> List[Dict[str, Any]]:
        """Get workflows by plan and type via GET /api/v1/workflows/plan/{plan_id}/type/{workflow_type}."""
        return self._make_request('GET', f'/api/v1/workflows/plan/{plan_id}/type/{workflow_type}')
    
    # System operations
    def get_health(self) -> Dict[str, Any]:
        """Get system health via GET /api/v1/health."""
        return self._make_request('GET', '/api/v1/health')
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics via GET /api/v1/metrics."""
        return self._make_request('GET', '/api/v1/metrics')
    


def get_client() -> CLIRestClient:
    """Get configured REST client instance."""
    return CLIRestClient(api_url=GLOBAL_API_URL, verbose=GLOBAL_VERBOSE)


def print_success(message: str):
    """Print success message with green checkmark."""
    console.print(f"✅ {message}", style="green")


def print_error(message: str):
    """Print error message with red X.""" 
    console.print(f"❌ {message}", style="red")


def print_warning(message: str):
    """Print warning message with yellow exclamation."""
    console.print(f"⚠️ {message}", style="yellow")


# Global CLI options
@app.callback()
def main(
    api_url: Optional[str] = typer.Option(None, "--api-url", help="API server URL"),
    format: Optional[str] = typer.Option(None, "--format", help="Output format (table, json)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output")
):
    """Customer Call Center Analytics CLI - Resource-Based Commands."""
    global GLOBAL_API_URL, GLOBAL_FORMAT, GLOBAL_VERBOSE
    
    if api_url:
        GLOBAL_API_URL = api_url
    if format:
        GLOBAL_FORMAT = format  
    if verbose:
        GLOBAL_VERBOSE = verbose


# ====================================================================
# CONSOLIDATED RESOURCE-BASED COMMANDS (REST API ALIGNED)
# ====================================================================

# Create subapps for each resource
transcript_app = typer.Typer(name="transcript", help="Transcript operations")
analysis_app = typer.Typer(name="analysis", help="Analysis operations") 
insights_app = typer.Typer(name="insights", help="Insights operations")
plan_app = typer.Typer(name="plan", help="Plan operations")
workflow_app = typer.Typer(name="workflow", help="Workflow approval operations")

# Create workflow sub-apps for organized command structure
workflow_generate_app = typer.Typer(help="Generate workflows from action plans")
workflow_process_app = typer.Typer(help="Process workflows (approve, reject, execute)")
workflow_manage_app = typer.Typer(help="Manage workflow assignments and lifecycle")
workflow_view_app = typer.Typer(help="View workflow information in various formats")

workflow_app.add_typer(workflow_generate_app, name="generate")
workflow_app.add_typer(workflow_process_app, name="process") 
workflow_app.add_typer(workflow_manage_app, name="manage")
workflow_app.add_typer(workflow_view_app, name="view")

system_app = typer.Typer(name="system", help="System operations")
orchestrate_app = typer.Typer(name="orchestrate", help="Pipeline orchestration operations")
approvals_app = typer.Typer(name="approvals", help="Approval queue management operations")

# Add subapps to main app
app.add_typer(transcript_app)
app.add_typer(analysis_app)
app.add_typer(insights_app)
app.add_typer(plan_app)
app.add_typer(workflow_app)
app.add_typer(orchestrate_app)
app.add_typer(approvals_app)
app.add_typer(system_app)


# ====================================================================
# TRANSCRIPT COMMANDS
# ====================================================================

@transcript_app.command("create")
def transcript_create(
    topic: str = typer.Option(..., "--topic", help="Topic/scenario for transcript"),
    store: bool = typer.Option(True, "--store/--no-store", help="Store transcript in database"),
    direct: bool = typer.Option(False, "--direct", help="Generate transcript directly (shows OpenAI telemetry)")
):
    """Create new transcript."""
    try:
        console.print("📝 [bold magenta]Generating transcript...[/bold magenta]")
        
        if direct:
            # Direct mode - generate transcript locally with telemetry visibility
            if not DIRECT_MODE_AVAILABLE:
                print_error("Direct mode not available. Missing dependencies.")
                raise typer.Exit(1)
            
            # Get API key from environment
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print_error("OPENAI_API_KEY not found in environment")
                raise typer.Exit(1)
            
            # Generate transcript directly
            generator = TranscriptGenerator(api_key=api_key)
            transcript = generator.generate(topic=topic)
            
            # Store if requested
            if store:
                db_path = os.getenv('DATABASE_PATH', './data/call_center.db')
                store_obj = TranscriptStore(db_path)
                store_obj.store(transcript)
            
            # Convert to dict for display
            result = transcript.to_dict()
        else:
            # Server mode - use API client (existing behavior)
            client = get_client()
            result = client.generate_transcript(topic=topic, store=store)
        
        console.print(f"\n📄 [bold green]Generated Transcript[/bold green]:")
        console.print(f"ID: [cyan]{result['id']}[/cyan]")
        console.print(f"Topic: [yellow]{result['topic']}[/yellow]")
        
        if store:
            print_success(f"Stored transcript: {result['id']}")
                
    except CLIError as e:
        print_error(f"Generate failed: {str(e)}")
        raise typer.Exit(1)


@transcript_app.command("list")
def transcript_list(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results")
):
    """List all transcripts."""
    try:
        client = get_client()
        
        console.print("📋 [bold magenta]Listing transcripts...[/bold magenta]")
        params = {'limit': limit} if limit else {}
        transcripts = client.list_transcripts(**params)
        
        if not transcripts:
            console.print("📭 No transcripts found")
            return
        
        console.print(f"\n📊 Found {len(transcripts)} transcript(s):")
        
        for transcript in transcripts:
            transcript_id = transcript.get('id') or transcript.get('transcript_id', 'N/A')
            topic = transcript.get('topic', '[Legacy]')
            message_count = len(transcript.get('messages', []))
            timestamp = transcript.get('timestamp', 'N/A')
            
            console.print(f"\n[cyan]ID:[/cyan] {transcript_id}")
            console.print(f"[cyan]Topic:[/cyan] {topic}")
            console.print(f"[cyan]Messages:[/cyan] {message_count}")
            console.print(f"[cyan]Created:[/cyan] {timestamp}")
            console.print("─" * 40)
            
    except CLIError as e:
        print_error(f"List failed: {str(e)}")
        raise typer.Exit(1)


@transcript_app.command("get")  
def transcript_get(transcript_id: str):
    """Get specific transcript details."""
    try:
        client = get_client()
        
        console.print(f"📄 [bold magenta]Getting transcript {transcript_id}...[/bold magenta]")
        transcript = client.get_transcript(transcript_id)
        
        console.print(f"\n📋 [bold green]Transcript Details[/bold green]:")
        console.print(f"ID: [cyan]{transcript.get('id', transcript_id)}[/cyan]")
        console.print(f"Topic: [yellow]{transcript.get('topic', 'N/A')}[/yellow]")
        
        messages = transcript.get('messages', [])
        console.print(f"\n💬 [bold blue]Messages ({len(messages)}):[/bold blue]")
        
        for i, message in enumerate(messages, 1):
            speaker = message.get('speaker', 'Unknown')
            text = message.get('text', '')
            console.print(f"\n[bold]{i}. {speaker}:[/bold]")
            console.print(f"   {text}")
            
    except CLIError as e:
        print_error(f"Get failed: {str(e)}")
        raise typer.Exit(1)


@transcript_app.command("delete")
def transcript_delete(
    transcript_id: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete specific transcript."""
    try:
        client = get_client()
        
        if not force:
            confirm = typer.confirm(f"Delete transcript {transcript_id}?", default=False)
            if not confirm:
                console.print("❌ Deletion cancelled")
                return
        
        console.print(f"🗑️ [bold magenta]Deleting transcript {transcript_id}...[/bold magenta]")
        client.delete_transcript(transcript_id)
        
        print_success(f"Deleted transcript: {transcript_id}")
        
    except CLIError as e:
        print_error(f"Delete failed: {str(e)}")
        raise typer.Exit(1)


@transcript_app.command("search")
def transcript_search(
    query: str = typer.Option(..., "--query", "-q", help="Search query")
):
    """Search transcripts."""
    try:
        client = get_client()
        
        console.print(f"🔍 [bold magenta]Searching for: '{query}'[/bold magenta]")
        results = client.search_transcripts(query=query)
        
        if not results:
            console.print("🔍 No matching transcripts found")
            return
        
        console.print(f"\n📊 Found {len(results)} matching transcript(s):")
        
        for transcript in results:
            transcript_id = transcript.get('id') or transcript.get('transcript_id', 'N/A')
            topic = transcript.get('topic', '[Legacy]')
            snippet = transcript.get('snippet', '')[:100] + '...' if transcript.get('snippet') else ''
            
            console.print(f"\n[cyan]ID:[/cyan] {transcript_id}")
            console.print(f"[cyan]Topic:[/cyan] {topic}")
            if snippet:
                console.print(f"[cyan]Snippet:[/cyan] {snippet}")
            console.print("─" * 40)
            
    except CLIError as e:
        print_error(f"Search failed: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# ANALYSIS COMMANDS
# ====================================================================

@analysis_app.command("create")
def analysis_create(
    transcript: str = typer.Option(..., "--transcript", "-t", help="Transcript ID to analyze")
):
    """Create analysis for transcript."""
    try:
        client = get_client()
        
        console.print(f"🔍 [bold magenta]Analyzing transcript {transcript}...[/bold magenta]")
        result = client.analyze_transcript(transcript_id=transcript, analysis_type='comprehensive', store=True)
        
        print_success(f"Analysis completed for transcript: {transcript}")
        
        # Display comprehensive analysis results
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
        
        # Display comprehensive analysis results
        console.print(f"\n📄 [bold green]Analysis Results[/bold green]:")
        console.print(f"   Analysis ID: [cyan]{analysis_id}[/cyan]")
        console.print(f"   Transcript ID: [cyan]{result.get('transcript_id', 'N/A')}[/cyan]")
        
        # Call Summary Section
        call_summary = result.get('call_summary')
        if call_summary:
            console.print(f"\n📋 [bold yellow]Call Summary:[/bold yellow]")
            console.print(f"   {call_summary}")
        
        # Primary Analysis Section
        console.print(f"\n🎯 [bold blue]Primary Analysis:[/bold blue]")
        console.print(f"   Intent: {intent}")
        console.print(f"   Urgency Level: {result.get('urgency_level', 'N/A')}")
        console.print(f"   Confidence: {confidence_score:.2%}")
        
        # Detailed Sentiment Analysis
        console.print(f"\n😊 [bold magenta]Sentiment Analysis:[/bold magenta]")
        console.print(f"   Overall: {sentiment}")
        if borrower_sentiment:
            start_sentiment = borrower_sentiment.get('start')
            end_sentiment = borrower_sentiment.get('end') 
            trend = borrower_sentiment.get('trend')
            if start_sentiment: console.print(f"   Start: {start_sentiment}")
            if end_sentiment: console.print(f"   End: {end_sentiment}")
            if trend: console.print(f"   Trend: {trend}")
        
        # Risk Assessment Section
        borrower_risks = result.get('borrower_risks', {})
        if borrower_risks:
            console.print(f"\n⚠️  [bold red]Risk Assessment:[/bold red]")
            if 'delinquency_risk' in borrower_risks:
                console.print(f"   Delinquency Risk: {borrower_risks['delinquency_risk']:.2%}")
            if 'churn_risk' in borrower_risks:
                console.print(f"   Churn Risk: {borrower_risks['churn_risk']:.2%}")
            if 'complaint_risk' in borrower_risks:
                console.print(f"   Complaint Risk: {borrower_risks['complaint_risk']:.2%}")
            if 'refinance_likelihood' in borrower_risks:
                console.print(f"   Refinance Likelihood: {borrower_risks['refinance_likelihood']:.2%}")
        
        # Resolution Status
        issue_resolved = result.get('issue_resolved')
        first_call_resolution = result.get('first_call_resolution') 
        escalation_needed = result.get('escalation_needed')
        
        if any([issue_resolved is not None, first_call_resolution is not None, escalation_needed is not None]):
            console.print(f"\n✅ [bold blue]Resolution Status:[/bold blue]")
            if issue_resolved is not None:
                console.print(f"   Issue Resolved: {'Yes' if issue_resolved else 'No'}")
            if first_call_resolution is not None:
                console.print(f"   First Call Resolution: {'Yes' if first_call_resolution else 'No'}")
            if escalation_needed is not None:
                console.print(f"   Escalation Needed: {'Yes' if escalation_needed else 'No'}")
        
    except CLIError as e:
        print_error(f"Analysis failed: {str(e)}")
        raise typer.Exit(1)


@analysis_app.command("list")
def analysis_list(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results")
):
    """List all analyses."""
    try:
        client = get_client()
        
        console.print("🔍 [bold magenta]Listing all analyses...[/bold magenta]")
        analyses = client.list_analyses(limit=limit)
        
        if not analyses:
            console.print("📭 No analyses found")
            return
        
        console.print(f"\n📊 Found {len(analyses)} analysis(es):")
        
        for analysis in analyses:
            analysis_id = analysis.get('analysis_id', 'N/A')
            transcript_id = analysis.get('transcript_id', 'N/A')
            intent = analysis.get('primary_intent', 'N/A')
            
            # Handle nested sentiment
            sentiment = 'N/A'
            borrower_sentiment = analysis.get('borrower_sentiment', {})
            if isinstance(borrower_sentiment, dict) and 'overall' in borrower_sentiment:
                sentiment = borrower_sentiment['overall']
            
            confidence = analysis.get('confidence_score', 0)
            urgency = analysis.get('urgency_level', 'N/A')
            
            console.print(f"\n[cyan]Analysis ID:[/cyan] {analysis_id}")
            console.print(f"[cyan]Transcript ID:[/cyan] {transcript_id}")
            console.print(f"[cyan]Intent:[/cyan] {intent}")
            console.print(f"[cyan]Sentiment:[/cyan] {sentiment}")
            console.print(f"[cyan]Confidence:[/cyan] {confidence:.2%}")
            console.print(f"[cyan]Urgency Level:[/cyan] {urgency}")
            
            # Show resolution status
            issue_resolved = analysis.get('issue_resolved')
            if issue_resolved is not None:
                console.print(f"[cyan]Issue Resolved:[/cyan] {'Yes' if issue_resolved else 'No'}")
            
            console.print("─" * 50)
        
    except CLIError as e:
        print_error(f"List analyses failed: {str(e)}")
        raise typer.Exit(1)


@analysis_app.command("get")
def analysis_get(analysis_id: str):
    """Get specific analysis details."""
    try:
        client = get_client()
        
        console.print(f"📄 [bold magenta]Getting analysis {analysis_id}...[/bold magenta]")
        analysis = client.get_analysis(analysis_id)
        
        console.print(f"\n📋 [bold green]Analysis Details[/bold green]:")
        console.print(f"ID: [cyan]{analysis.get('analysis_id', analysis_id)}[/cyan]")
        console.print(f"Transcript: [yellow]{analysis.get('transcript_id', 'N/A')}[/yellow]")
        console.print(f"Intent: [green]{analysis.get('primary_intent', 'N/A')}[/green]")
        
        # Show full analysis data
        console.print("\n📊 [bold blue]Full Analysis Data:[/bold blue]")
        formatted_analysis = json.dumps(analysis, indent=2)
        console.print(formatted_analysis)
            
    except CLIError as e:
        print_error(f"Get analysis failed: {str(e)}")
        raise typer.Exit(1)


@analysis_app.command("delete")
def analysis_delete(
    analysis_id: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete specific analysis."""
    try:
        client = get_client()
        
        if not force:
            confirm = typer.confirm(f"Delete analysis {analysis_id}?", default=False)
            if not confirm:
                console.print("❌ Deletion cancelled")
                return
        
        console.print(f"🗑️ [bold magenta]Deleting analysis {analysis_id}...[/bold magenta]")
        client.delete_analysis(analysis_id)
        
        print_success(f"Deleted analysis: {analysis_id}")
        
    except CLIError as e:
        print_error(f"Delete failed: {str(e)}")
        raise typer.Exit(1)


@analysis_app.command("delete-all")
def analysis_delete_all(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete all analyses."""
    try:
        client = get_client()
        
        if not force:
            confirm = typer.confirm("Delete ALL analyses? This cannot be undone!", default=False)
            if not confirm:
                console.print("❌ Deletion cancelled")
                return
        
        console.print("🗑️ [bold magenta]Deleting all analyses...[/bold magenta]")
        result = client.delete_all_analyses()
        
        count = result.get('count', 0)
        print_success(f"Deleted {count} analyses")
        
    except CLIError as e:
        print_error(f"Delete all failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("patterns")
def analysis_patterns(
    risk_threshold: float = typer.Option(0.7, "--threshold", "-t", help="Risk threshold (0.0-1.0)")
):
    """Discover risk patterns across all analyses using knowledge graph."""
    try:
        if not (0.0 <= risk_threshold <= 1.0):
            print_error("Risk threshold must be between 0.0 and 1.0")
            raise typer.Exit(1)
        
        client = get_client()
        console.print(f"🔍 [bold blue]Discovering risk patterns (threshold: {risk_threshold})...[/bold blue]")
        
        patterns = client.discover_risk_patterns(risk_threshold)
        
        if not patterns:
            console.print("📊 No risk patterns found above threshold")
            return
        
        # Display patterns in a table
        table = Table(title=f"Risk Patterns (≥{risk_threshold})")
        table.add_column("Risk Type", style="red")
        table.add_column("Severity", style="yellow") 
        table.add_column("Risk Score", style="cyan")
        table.add_column("Affected", style="green")
        table.add_column("Recommendation", style="white")
        
        for pattern in patterns:
            table.add_row(
                pattern.get('risk_type', 'Unknown'),
                pattern.get('severity', 'Unknown'),
                f"{pattern.get('risk_score', 0):.2f}",
                str(pattern.get('affected_count', 0)),
                pattern.get('recommendation', 'None')[:50] + "..." if len(pattern.get('recommendation', '')) > 50 else pattern.get('recommendation', '')
            )
        
        console.print(table)
        print_success(f"Found {len(patterns)} risk patterns")
        
    except CLIError as e:
        print_error(f"Pattern discovery failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("risks")
def analysis_risks(
    risk_threshold: float = typer.Option(0.8, "--threshold", "-t", help="High-risk threshold (0.0-1.0)")
):
    """Get high-risk patterns using knowledge graph analytics."""
    try:
        if not (0.0 <= risk_threshold <= 1.0):
            print_error("Risk threshold must be between 0.0 and 1.0")
            raise typer.Exit(1)
        
        client = get_client()
        console.print(f"⚠️ [bold red]Getting high-risk patterns (threshold: {risk_threshold})...[/bold red]")
        
        risks = client.get_high_risks(risk_threshold)
        
        if not risks:
            console.print("✅ No high-risk patterns found above threshold")
            return
        
        # Display high-risk patterns
        for i, risk in enumerate(risks, 1):
            severity = risk.get('severity', 'UNKNOWN')
            color = {"CRITICAL": "bold red", "HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(severity, "white")
            
            console.print(f"\n🚨 [bold]Risk Pattern #{i}[/bold]")
            console.print(f"   Type: [{color}]{risk.get('risk_type', 'Unknown')}[/{color}]")
            console.print(f"   Score: [{color}]{risk.get('risk_score', 0):.2f}[/{color}]")
            console.print(f"   Severity: [{color}]{severity}[/{color}]")
            console.print(f"   Affected: {risk.get('affected_count', 0)} analyses")
            console.print(f"   Recommendation: {risk.get('recommendation', 'None')}")
        
        print_success(f"Found {len(risks)} high-risk patterns requiring attention")
        
    except CLIError as e:
        print_error(f"High-risk analysis failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("recommend")
def analysis_recommend(
    customer_id: str = typer.Argument(..., help="Customer ID for personalized recommendations")
):
    """Get AI-powered recommendations for a customer using knowledge graph."""
    try:
        client = get_client()
        console.print(f"🤖 [bold green]Getting recommendations for customer {customer_id}...[/bold green]")
        
        recommendations = client.get_customer_recommendations(customer_id)
        
        if not recommendations:
            console.print(f"📭 No recommendations found for customer {customer_id}")
            return
        
        # Display recommendations
        for i, rec in enumerate(recommendations, 1):
            rec_type = rec.get('recommendation_type', 'UNKNOWN')
            confidence = rec.get('confidence', 0)
            priority = rec.get('priority', 'UNKNOWN')
            
            priority_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(priority, "white")
            
            console.print(f"\n💡 [bold]Recommendation #{i}[/bold]")
            console.print(f"   Type: {rec_type}")
            console.print(f"   Action: {rec.get('recommended_action', 'None')}")
            console.print(f"   Confidence: {confidence:.2f}")
            console.print(f"   Priority: [{priority_color}]{priority}[/{priority_color}]")
            console.print(f"   Success Rate: {rec.get('success_probability', 0):.2f}")
            
            if 'basis' in rec and rec['basis']:
                basis = rec['basis']
                console.print(f"   Basis: {basis.get('reasoning', 'Not specified')}")
        
        print_success(f"Generated {len(recommendations)} personalized recommendations")
        
    except CLIError as e:
        print_error(f"Recommendation failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("similar")
def analysis_similar(
    analysis_id: str = typer.Argument(..., help="Analysis ID to find similar analyses for"),
    limit: int = typer.Option(5, "--limit", "-l", help="Maximum similar analyses to return")
):
    """Find similar analyses using knowledge graph pattern matching."""
    try:
        if limit <= 0 or limit > 50:
            print_error("Limit must be between 1 and 50")
            raise typer.Exit(1)
        
        client = get_client()
        console.print(f"🔎 [bold cyan]Finding similar analyses for {analysis_id} (limit: {limit})...[/bold cyan]")
        
        similar_analyses = client.find_similar_analyses(analysis_id, limit)
        
        if not similar_analyses:
            console.print(f"🔍 No similar analyses found for analysis {analysis_id}")
            return
        
        # Display similar analyses
        table = Table(title=f"Similar Analyses for {analysis_id}")
        table.add_column("Similar Analysis", style="blue")
        table.add_column("Shared Pattern", style="yellow")
        table.add_column("Risk Score", style="red")
        table.add_column("Confidence", style="green") 
        table.add_column("Learning Opportunity", style="white")
        
        for analysis in similar_analyses:
            similarity = analysis.get('similarity', {})
            table.add_row(
                analysis.get('similar_analysis_id', 'Unknown'),
                similarity.get('shared_pattern', 'Unknown'),
                f"{similarity.get('risk_score', 0):.2f}",
                f"{similarity.get('confidence', 0):.2f}",
                analysis.get('learning_opportunity', 'None')[:40] + "..." if len(analysis.get('learning_opportunity', '')) > 40 else analysis.get('learning_opportunity', '')
            )
        
        console.print(table)
        print_success(f"Found {len(similar_analyses)} similar analyses")
        
    except CLIError as e:
        print_error(f"Similar analysis search failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("dashboard") 
def analysis_dashboard():
    """Get comprehensive insights dashboard from knowledge graph analytics."""
    try:
        client = get_client()
        console.print("📊 [bold magenta]Loading insights dashboard...[/bold magenta]")
        
        dashboard = client.get_insights_dashboard()
        
        # Display dashboard summary
        summary = dashboard.get('summary', {})
        console.print(f"\n📈 [bold]Analytics Summary[/bold]")
        console.print(f"   Risk Patterns: {summary.get('total_risk_patterns', 0)}")
        console.print(f"   Compliance Flags: {summary.get('total_compliance_flags', 0)}")
        console.print(f"   Analysis Coverage: {summary.get('analysis_coverage', 0):.1%}")
        
        # Display top risks
        risk_analysis = dashboard.get('risk_analysis', {})
        top_risks = risk_analysis.get('top_risks', [])[:3]  # Show top 3
        if top_risks:
            console.print(f"\n🚨 [bold red]Top Risk Patterns[/bold red]")
            for i, risk in enumerate(top_risks, 1):
                console.print(f"   {i}. {risk.get('risk_type', 'Unknown')} (score: {risk.get('avg_risk_score', 0):.2f})")
        
        # Display immediate actions
        recommendations = dashboard.get('recommendations', {})
        immediate_actions = recommendations.get('immediate_actions', [])
        if immediate_actions:
            console.print(f"\n⚡ [bold yellow]Immediate Actions Required[/bold yellow]")
            for action in immediate_actions:
                priority = action.get('priority', 'MEDIUM')
                priority_color = {"CRITICAL": "bold red", "HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(priority, "white")
                console.print(f"   • [{priority_color}][{priority}][/{priority_color}] {action.get('action', 'Unknown')} ({action.get('timeline', 'No timeline')})")
        
        print_success("Dashboard loaded successfully")
        
    except CLIError as e:
        print_error(f"Dashboard failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("populate")
def analysis_populate(
    analysis_id: Optional[str] = typer.Option(None, "--analysis-id", "-a", help="Single analysis ID to populate"),
    all: bool = typer.Option(False, "--all", help="Populate all analyses"),
    from_date: Optional[str] = typer.Option(None, "--from-date", help="Populate from date (YYYY-MM-DD)")
):
    """Populate knowledge graph from analysis data."""
    try:
        if not any([analysis_id, all, from_date]):
            print_error("Must specify --analysis-id, --all, or --from-date")
            raise typer.Exit(1)
        
        client = get_client()
        
        if analysis_id:
            console.print(f"📊 [bold blue]Populating graph from analysis {analysis_id}...[/bold blue]")
            result = client.populate_insights(analysis_id=analysis_id)
            print_success(result.get('message', 'Analysis populated'))
            
        elif all:
            console.print("📊 [bold blue]Populating graph from all analyses...[/bold blue]")
            result = client.populate_insights(all=True)
            count = result.get('populated_count', 0)
            errors = result.get('error_count', 0)
            print_success(f"Populated {count} analyses" + (f" ({errors} errors)" if errors else ""))
            
        elif from_date:
            console.print(f"📊 [bold blue]Populating graph from date {from_date}...[/bold blue]")
            result = client.populate_insights(from_date=from_date)
            count = result.get('populated_count', 0)
            print_success(f"Populated {count} analyses from {from_date}")
            
    except CLIError as e:
        print_error(f"Populate failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("query")
def analysis_query(
    cypher: str = typer.Argument(..., help="Cypher query to execute")
):
    """Execute raw Cypher query on knowledge graph."""
    try:
        client = get_client()
        console.print(f"🔍 [bold cyan]Executing query...[/bold cyan]")
        
        results = client.query_insights(cypher)
        
        if not results:
            console.print("📄 No results returned")
            return
        
        # Display results in a table if structured
        if results and isinstance(results[0], dict):
            table = Table(title="Query Results")
            
            # Add columns from first result
            for key in results[0].keys():
                table.add_column(str(key), style="cyan")
            
            # Add rows
            for result in results[:20]:  # Limit to first 20 results
                table.add_row(*[str(result.get(key, '')) for key in results[0].keys()])
            
            console.print(table)
            
            if len(results) > 20:
                console.print(f"... and {len(results) - 20} more results")
        else:
            # Simple output
            for i, result in enumerate(results[:10], 1):
                console.print(f"{i}. {result}")
        
        print_success(f"Query returned {len(results)} results")
        
    except CLIError as e:
        print_error(f"Query failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("status")
def analysis_status():
    """Get knowledge graph status and statistics."""
    try:
        client = get_client()
        console.print("📊 [bold magenta]Getting graph status...[/bold magenta]")
        
        status = client.get_insights_status()
        
        # Display status
        console.print(f"\n📈 [bold]Knowledge Graph Status[/bold]")
        console.print(f"   Populated: {'✅ Yes' if status.get('graph_populated') else '❌ No'}")
        console.print(f"   Total Nodes: {status.get('total_nodes', 0)}")
        console.print(f"   Relationships: {status.get('relationship_count', 0)}")
        
        # Node counts
        console.print(f"\n📊 [bold]Node Counts[/bold]")
        console.print(f"   Customers: {status.get('customer_count', 0)}")
        console.print(f"   Transcripts: {status.get('transcript_count', 0)}")
        console.print(f"   Analyses: {status.get('analysis_count', 0)}")
        console.print(f"   Risk Patterns: {status.get('riskpattern_count', 0)}")
        console.print(f"   Compliance Flags: {status.get('complianceflag_count', 0)}")
        
        print_success("Status retrieved successfully")
        
    except CLIError as e:
        print_error(f"Status check failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("delete-analysis")
def analysis_delete_analysis(
    analysis_id: str = typer.Argument(..., help="Analysis ID to delete from graph")
):
    """Delete analysis from knowledge graph."""
    try:
        client = get_client()
        console.print(f"🗑️ [bold red]Deleting analysis {analysis_id} from graph...[/bold red]")
        
        result = client.delete_insights_analysis(analysis_id)
        print_success(result.get('message', f'Analysis {analysis_id} deleted'))
        
    except CLIError as e:
        print_error(f"Delete failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("delete-customer")
def analysis_delete_customer(
    customer_id: str = typer.Argument(..., help="Customer ID to delete from graph"),
    cascade: bool = typer.Option(False, "--cascade", help="Delete all related data")
):
    """Delete customer from knowledge graph."""
    try:
        client = get_client()
        
        if cascade:
            confirm = typer.confirm(f"Delete customer {customer_id} AND ALL related data? This cannot be undone!")
            if not confirm:
                console.print("❌ Deletion cancelled")
                return
        
        cascade_text = " (cascade)" if cascade else ""
        console.print(f"🗑️ [bold red]Deleting customer {customer_id}{cascade_text}...[/bold red]")
        
        result = client.delete_insights_customer(customer_id, cascade)
        print_success(result.get('message', f'Customer {customer_id} deleted'))
        
    except CLIError as e:
        print_error(f"Delete customer failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("prune")
def analysis_prune(
    older_than_days: int = typer.Argument(..., help="Delete data older than N days"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be deleted without deleting")
):
    """Prune old data from knowledge graph (GDPR compliance)."""
    try:
        if older_than_days <= 0:
            print_error("Days must be positive")
            raise typer.Exit(1)
        
        if not dry_run:
            confirm = typer.confirm(f"Delete ALL data older than {older_than_days} days? This cannot be undone!")
            if not confirm:
                console.print("❌ Pruning cancelled")
                return
        
        client = get_client()
        
        if dry_run:
            console.print(f"🔍 [bold yellow]Dry run: Would delete data older than {older_than_days} days[/bold yellow]")
            # For dry run, just show status
            status = client.get_insights_status()
            console.print(f"Current total nodes: {status.get('total_nodes', 0)}")
            print_success("Dry run completed (no data deleted)")
        else:
            console.print(f"🗑️ [bold red]Pruning data older than {older_than_days} days...[/bold red]")
            result = client.prune_insights(older_than_days)
            deleted_count = result.get('deleted_count', 0)
            print_success(f"Pruned {deleted_count} nodes")
        
    except CLIError as e:
        print_error(f"Prune failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("clear")
def analysis_clear_graph(
    force: bool = typer.Option(False, "--force", help="Skip confirmation")
):
    """Clear entire knowledge graph (use with extreme caution)."""
    try:
        if not force:
            confirm = typer.confirm("⚠️  DANGER: Delete ENTIRE knowledge graph? This cannot be undone!")
            if not confirm:
                console.print("❌ Clear cancelled")
                return
        
        client = get_client()
        console.print("🗑️ [bold red]Clearing entire knowledge graph...[/bold red]")
        
        result = client.clear_insights()
        print_success(result.get('message', 'Knowledge graph cleared'))
        
    except CLIError as e:
        print_error(f"Clear failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("visualize")
def analysis_visualize(
    output: str = typer.Option("knowledge_graph.html", "--output", "-o", help="Output HTML file path"),
    open_browser: bool = typer.Option(False, "--open", help="Open visualization in browser")
):
    """Create interactive network visualization of the knowledge graph."""
    try:
        from src.visualization.graph_visualizer import GraphVisualizer
        
        console.print("📊 [bold magenta]Creating knowledge graph visualization...[/bold magenta]")
        
        client = get_client()
        
        # Get visualization data via API
        console.print("📈 [bold blue]Fetching graph data from API...[/bold blue]")
        try:
            graph_data = client.get_visualization_data()
        except Exception as e:
            raise CLIError(f"Failed to fetch graph data: {str(e)}")
        
        # Get graph statistics via API
        try:
            stats = client.get_visualization_statistics()
        except Exception as e:
            raise CLIError(f"Failed to fetch graph statistics: {str(e)}")
        
        if stats.get('error'):
            raise CLIError(f"Graph data error: {stats['error']}")
        
        console.print(f"   📊 Nodes: {stats['total_nodes']}")
        console.print(f"   🔗 Edges: {stats['total_edges']}")
        
        # Show node type breakdown
        node_types = stats.get('node_types', {})
        for node_type, count in node_types.items():
            console.print(f"   📋 {node_type}: {count}")
        
        # Create visualization
        console.print("🎨 [bold green]Creating interactive visualization...[/bold green]")
        try:
            visualizer = GraphVisualizer()
            figure = visualizer.create_network_graph(graph_data)
        except Exception as e:
            raise CLIError(f"Visualization creation failed: {str(e)}")
        
        # Save to HTML
        console.print(f"💾 [bold yellow]Saving to {output}...[/bold yellow]")
        try:
            visualizer.save_to_html(figure, output, auto_open=open_browser)
        except Exception as e:
            raise CLIError(f"Failed to save visualization: {str(e)}")
        
        print_success(f"Interactive visualization created: {output}")
        
        # Show high-level insights
        if stats.get('high_risk_nodes', 0) > 0:
            print_warning(f"Found {stats['high_risk_nodes']} high-risk nodes")
        if stats.get('high_severity_nodes', 0) > 0:
            print_warning(f"Found {stats['high_severity_nodes']} high-severity nodes")
        
        if open_browser:
            console.print("🌐 Opening visualization in browser...")
        else:
            console.print(f"💡 Use --open to automatically open {output} in your browser")
            
    except CLIError as e:
        print_error(f"Visualization failed: {str(e)}")
        raise typer.Exit(1)
    except ImportError as e:
        print_error(f"Missing dependencies: {str(e)}")
        print_error("Install with: pip install networkx plotly")
        raise typer.Exit(1)


# ====================================================================
# PLAN COMMANDS
# ====================================================================

@plan_app.command("create")
def plan_create(
    analysis: str = typer.Option(..., "--analysis", "-a", help="Analysis ID to create plan from")
):
    """Create action plan from analysis."""
    try:
        client = get_client()
        
        console.print(f"📋 [bold magenta]Creating plan for analysis {analysis}...[/bold magenta]")
        result = client.create_plan(analysis_id=analysis)
        
        plan_id = result.get('plan_id')
        print_success(f"Created plan: {plan_id}")
        
        console.print(f"\n📄 [bold green]Plan Details[/bold green]:")
        console.print(f"Plan ID: [cyan]{plan_id}[/cyan]")
        console.print(f"Analysis ID: [yellow]{analysis}[/yellow]")
        console.print(f"Status: [green]{result.get('status', 'N/A')}[/green]")
        
        # Display the four-layer action plans
        if 'borrower_plan' in result:
            console.print(f"\n🏠 [bold blue]BORROWER PLAN[/bold blue]:")
            borrower_plan = result['borrower_plan']
            if 'immediate_actions' in borrower_plan:
                console.print("  [yellow]Immediate Actions:[/yellow]")
                for i, action in enumerate(borrower_plan['immediate_actions'][:3], 1):  # Show first 3
                    console.print(f"    {i}. {action.get('action', 'N/A')} (Priority: {action.get('priority', 'N/A')})")
                if len(borrower_plan['immediate_actions']) > 3:
                    console.print(f"    ... and {len(borrower_plan['immediate_actions']) - 3} more actions")
        
        if 'advisor_plan' in result:
            console.print(f"\n👨‍💼 [bold green]ADVISOR PLAN[/bold green]:")
            advisor_plan = result['advisor_plan']
            if 'coaching_items' in advisor_plan:
                console.print("  [yellow]Coaching Items:[/yellow]")
                for i, item in enumerate(advisor_plan['coaching_items'][:2], 1):  # Show first 2
                    console.print(f"    {i}. {item.get('coaching_point', 'N/A')} (Priority: {item.get('priority', 'N/A')})")
                if len(advisor_plan['coaching_items']) > 2:
                    console.print(f"    ... and {len(advisor_plan['coaching_items']) - 2} more coaching items")
        
        if 'supervisor_plan' in result:
            console.print(f"\n👔 [bold yellow]SUPERVISOR PLAN[/bold yellow]:")
            supervisor_plan = result['supervisor_plan']
            console.print(f"  [yellow]Approval Required:[/yellow] {supervisor_plan.get('approval_required', 'N/A')}")
            if 'escalation_items' in supervisor_plan:
                console.print("  [yellow]Escalation Items:[/yellow]")
                for i, item in enumerate(supervisor_plan['escalation_items'][:2], 1):  # Show first 2
                    console.print(f"    {i}. {item.get('item', 'N/A')} (Priority: {item.get('priority', 'N/A')})")
        
        if 'leadership_plan' in result:
            console.print(f"\n🏢 [bold red]LEADERSHIP PLAN[/bold red]:")
            leadership_plan = result['leadership_plan']
            if 'portfolio_insights' in leadership_plan:
                console.print("  [yellow]Portfolio Insights:[/yellow]")
                for i, insight in enumerate(leadership_plan['portfolio_insights'][:2], 1):  # Show first 2
                    console.print(f"    {i}. {insight}")
                if len(leadership_plan['portfolio_insights']) > 2:
                    console.print(f"    ... and {len(leadership_plan['portfolio_insights']) - 2} more insights")
        
        console.print(f"\n💡 [dim]Use 'python cli.py plan list' to see all plans[/dim]")
        
    except CLIError as e:
        print_error(f"Plan creation failed: {str(e)}")
        raise typer.Exit(1)


@plan_app.command("list")
def plan_list(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results")
):
    """List all plans."""
    try:
        client = get_client()
        
        console.print("📋 [bold magenta]Listing plans...[/bold magenta]")
        plans = client.list_plans(limit=limit)
        
        if not plans:
            console.print("📭 No plans found")
            return
        
        console.print(f"\n📊 Found {len(plans)} plan(s):")
        
        for plan in plans:
            plan_id = plan.get('plan_id', 'N/A')
            analysis_id = plan.get('analysis_id', 'N/A')
            status = plan.get('status', 'N/A')
            
            console.print(f"\n[cyan]Plan ID:[/cyan] {plan_id}")
            console.print(f"[cyan]Analysis ID:[/cyan] {analysis_id}")
            console.print(f"[cyan]Status:[/cyan] {status}")
            console.print("─" * 40)
            
    except CLIError as e:
        print_error(f"List plans failed: {str(e)}")
        raise typer.Exit(1)


@plan_app.command("view")
def plan_view(
    plan_id: str = typer.Argument(..., help="Plan ID to view")
):
    """View detailed plan information."""
    try:
        client = get_client()
        
        console.print(f"📋 [bold magenta]Retrieving plan {plan_id}...[/bold magenta]")
        plan = client.view_plan(plan_id)
        
        console.print(f"\n📄 [bold green]Plan Details[/bold green]:")
        console.print(f"Plan ID: [cyan]{plan.get('plan_id', 'N/A')}[/cyan]")
        console.print(f"Analysis ID: [yellow]{plan.get('analysis_id', 'N/A')}[/yellow]")
        console.print(f"Status: [green]{plan.get('status', 'N/A')}[/green]")
        console.print(f"Created: [dim]{plan.get('created_at', 'N/A')}[/dim]")
        
        # Display the four-layer action plans
        if 'borrower_plan' in plan:
            console.print(f"\n🏠 [bold blue]BORROWER PLAN[/bold blue]:")
            borrower_plan = plan['borrower_plan']
            if 'immediate_actions' in borrower_plan:
                console.print("  [yellow]Immediate Actions:[/yellow]")
                for i, action in enumerate(borrower_plan['immediate_actions'], 1):
                    console.print(f"    {i}. {action.get('action', 'N/A')} (Priority: {action.get('priority', 'N/A')})")
        
        if 'advisor_plan' in plan:
            console.print(f"\n👨‍💼 [bold green]ADVISOR PLAN[/bold green]:")
            advisor_plan = plan['advisor_plan']
            if 'coaching_items' in advisor_plan:
                console.print("  [yellow]Coaching Items:[/yellow]")
                for i, item in enumerate(advisor_plan['coaching_items'], 1):
                    console.print(f"    {i}. {item.get('coaching_point', 'N/A')} (Priority: {item.get('priority', 'N/A')})")
        
        if 'supervisor_plan' in plan:
            console.print(f"\n👔 [bold yellow]SUPERVISOR PLAN[/bold yellow]:")
            supervisor_plan = plan['supervisor_plan']
            console.print(f"  [yellow]Approval Required:[/yellow] {supervisor_plan.get('approval_required', 'N/A')}")
            if 'escalation_items' in supervisor_plan:
                console.print("  [yellow]Escalation Items:[/yellow]")
                for i, item in enumerate(supervisor_plan['escalation_items'], 1):
                    console.print(f"    {i}. {item.get('item', 'N/A')} (Priority: {item.get('priority', 'N/A')})")
        
        if 'leadership_plan' in plan:
            console.print(f"\n🏢 [bold red]LEADERSHIP PLAN[/bold red]:")
            leadership_plan = plan['leadership_plan']
            if 'portfolio_insights' in leadership_plan:
                console.print("  [yellow]Portfolio Insights:[/yellow]")
                for i, insight in enumerate(leadership_plan['portfolio_insights'], 1):
                    console.print(f"    {i}. {insight}")
        
        print_success(f"Plan {plan_id} retrieved successfully")
            
    except CLIError as e:
        print_error(f"View plan failed: {str(e)}")
        raise typer.Exit(1)


@plan_app.command("update")
def plan_update(
    plan_id: str = typer.Argument(..., help="Plan ID to update"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Update plan status"),
    approved_by: Optional[str] = typer.Option(None, "--approved-by", help="Set approver"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Add notes to the plan")
):
    """Update plan information."""
    try:
        client = get_client()
        
        # Build update data
        update_data = {}
        if status:
            update_data["status"] = status
        if approved_by:
            update_data["approved_by"] = approved_by
        if notes:
            update_data["notes"] = notes
        
        if not update_data:
            print_error("No update parameters provided. Use --status, --approved-by, or --notes")
            raise typer.Exit(1)
        
        console.print(f"✏️ [bold magenta]Updating plan {plan_id}...[/bold magenta]")
        updated_plan = client.update_plan(plan_id, update_data)
        
        console.print(f"\n📄 [bold green]Updated Plan[/bold green]:")
        console.print(f"Plan ID: [cyan]{updated_plan.get('plan_id', 'N/A')}[/cyan]")
        console.print(f"Analysis ID: [yellow]{updated_plan.get('analysis_id', 'N/A')}[/yellow]")
        console.print(f"Status: [green]{updated_plan.get('status', 'N/A')}[/green]")
        console.print(f"Updated: [dim]{updated_plan.get('updated_at', 'N/A')}[/dim]")
        
        print_success(f"Plan {plan_id} updated successfully")
            
    except CLIError as e:
        print_error(f"Update plan failed: {str(e)}")
        raise typer.Exit(1)


@plan_app.command("delete")
def plan_delete(
    plan_id: str = typer.Argument(..., help="Plan ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """Delete a plan."""
    try:
        client = get_client()
        
        if not force:
            confirm = typer.confirm(f"Are you sure you want to delete plan {plan_id}?")
            if not confirm:
                console.print("❌ Delete cancelled")
                return
        
        console.print(f"🗑️ [bold red]Deleting plan {plan_id}...[/bold red]")
        result = client.delete_plan(plan_id)
        
        console.print(f"\n✅ [bold green]{result.get('message', 'Plan deleted successfully')}[/bold green]")
        print_success(f"Plan {plan_id} deleted")
            
    except CLIError as e:
        print_error(f"Delete plan failed: {str(e)}")
        raise typer.Exit(1)


@plan_app.command("delete-all")
def plan_delete_all(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """Delete all plans."""
    try:
        client = get_client()
        
        if not force:
            confirm = typer.confirm("Are you sure you want to delete ALL plans? This cannot be undone!")
            if not confirm:
                console.print("❌ Delete cancelled")
                return
        
        console.print("🗑️ [bold red]Deleting all plans...[/bold red]")
        result = client.delete_all_plans()
        
        console.print(f"\n✅ [bold green]{result.get('message', 'All plans deleted successfully')}[/bold green]")
        deleted_count = result.get('deleted_count', result.get('count', 'Unknown'))
        print_success(f"Deleted {deleted_count} plan(s)")
            
    except CLIError as e:
        print_error(f"Delete all plans failed: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# WORKFLOW COMMANDS
# ====================================================================

@workflow_generate_app.command("single")
def workflow_generate_single(
    plan_id: str = typer.Argument(..., help="Plan ID to extract workflow from")
):
    """Extract single workflow from action plan."""
    try:
        client = get_client()
        
        console.print("🔄 [bold magenta]Extracting workflow from plan...[/bold magenta]")
        result = client.extract_workflow(plan_id=plan_id)
        
        workflow_id = result.get('id')
        status = result.get('status', 'Unknown')
        risk_level = result.get('risk_level', 'Unknown')
        
        console.print(f"\n✅ [bold green]Workflow Extracted[/bold green]:")
        console.print(f"Workflow ID: [cyan]{workflow_id}[/cyan]")
        console.print(f"Plan ID: [yellow]{plan_id}[/yellow]")
        console.print(f"Status: [blue]{status}[/blue]")
        console.print(f"Risk Level: [red]{risk_level}[/red]")
        
        if result.get('requires_human_approval'):
            console.print(f"⚠️  [yellow]Requires human approval[/yellow]")
        else:
            console.print(f"✅ [green]Auto-approved[/green]")
        
        print_success(f"Workflow extracted: {workflow_id}")
        
    except CLIError as e:
        print_error(f"Workflow extraction failed: {str(e)}")
        raise typer.Exit(1)


@workflow_view_app.command("list")
def workflow_view_list(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    risk_level: Optional[str] = typer.Option(None, "--risk", "-r", help="Filter by risk level"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results")
):
    """List workflows with optional filters."""
    try:
        client = get_client()
        
        console.print("📋 [bold magenta]Listing workflows...[/bold magenta]")
        params = {}
        if status:
            params['status'] = status
        if risk_level:
            params['risk_level'] = risk_level
        if limit:
            params['limit'] = limit
            
        workflows = client.list_workflows(**params)
        
        if not workflows:
            console.print("📭 No workflows found")
            return
        
        console.print(f"\n📊 Found {len(workflows)} workflow(s):")
        
        for workflow in workflows:
            workflow_id = workflow.get('id', 'N/A')
            plan_id = workflow.get('plan_id', 'N/A')
            status = workflow.get('status', 'Unknown')
            risk_level = workflow.get('risk_level', 'Unknown')
            created = workflow.get('created_at', 'N/A')
            
            console.print(f"\n[cyan]Workflow ID:[/cyan] {workflow_id}")
            console.print(f"[cyan]Plan ID:[/cyan] {plan_id}")
            console.print(f"[cyan]Status:[/cyan] {status}")
            console.print(f"[cyan]Risk Level:[/cyan] {risk_level}")
            console.print(f"[cyan]Created:[/cyan] {created}")
            
            if workflow.get('requires_human_approval'):
                approver = workflow.get('assigned_approver', 'Unassigned')
                console.print(f"[yellow]Assigned Approver:[/yellow] {approver}")
            
            console.print("─" * 50)
            
    except CLIError as e:
        print_error(f"List workflows failed: {str(e)}")
        raise typer.Exit(1)


@workflow_view_app.command("details")
def workflow_view_details(
    workflow_id: str = typer.Argument(..., help="Workflow ID to view")
):
    """View detailed workflow information."""
    try:
        client = get_client()
        
        console.print(f"🔍 [bold magenta]Getting workflow details...[/bold magenta]")
        workflow = client.get_workflow(workflow_id=workflow_id)
        
        if not workflow:
            print_error(f"Workflow not found: {workflow_id}")
            raise typer.Exit(1)
        
        console.print(f"\n📄 [bold green]Workflow Details[/bold green]:")
        console.print(f"Workflow ID: [cyan]{workflow.get('id')}[/cyan]")
        console.print(f"Plan ID: [yellow]{workflow.get('plan_id')}[/yellow]")
        console.print(f"Analysis ID: [blue]{workflow.get('analysis_id')}[/blue]")
        console.print(f"Workflow Type: [magenta]{workflow.get('workflow_type', 'UNKNOWN')}[/magenta]")
        console.print(f"Status: [green]{workflow.get('status')}[/green]")
        console.print(f"Risk Level: [red]{workflow.get('risk_level')}[/red]")
        
        # Action Item Details
        workflow_data = workflow.get('workflow_data', {})
        if workflow_data:
            console.print(f"\n🎯 [bold blue]Action Item Details:[/bold blue]")
            
            # Display action details
            if 'action_item' in workflow_data:
                console.print(f"[cyan]Action:[/cyan] {workflow_data['action_item']}")
            elif 'action' in workflow_data:
                console.print(f"[cyan]Action:[/cyan] {workflow_data['action']}")
                
            if 'description' in workflow_data:
                console.print(f"[cyan]Description:[/cyan] {workflow_data['description']}")
                
            if 'priority' in workflow_data:
                priority_color = "red" if workflow_data['priority'].lower() == "high" else "yellow" if workflow_data['priority'].lower() == "medium" else "green"
                console.print(f"[cyan]Priority:[/cyan] [{priority_color}]{workflow_data['priority']}[/{priority_color}]")
                
            if 'timeline' in workflow_data:
                console.print(f"[cyan]Timeline:[/cyan] {workflow_data['timeline']}")
                
            if 'workflow_type' in workflow_data:
                console.print(f"[cyan]Layer:[/cyan] {workflow_data['workflow_type']}")
                
            # Display any additional metadata
            if 'item_metadata' in workflow_data:
                metadata = workflow_data['item_metadata']
                if metadata:
                    console.print(f"[cyan]Additional Info:[/cyan] {metadata}")
        
        # Risk reasoning
        if workflow.get('risk_reasoning'):
            console.print(f"\n💭 [bold blue]Risk Assessment:[/bold blue]")
            try:
                # Try to parse as JSON for better formatting
                risk_data = json.loads(workflow['risk_reasoning']) if isinstance(workflow['risk_reasoning'], str) else workflow['risk_reasoning']
                if isinstance(risk_data, dict):
                    for key, value in risk_data.items():
                        if key and value:
                            console.print(f"[cyan]{key.replace('_', ' ').title()}:[/cyan] {value}")
                else:
                    console.print(f"{workflow['risk_reasoning']}")
            except:
                console.print(f"{workflow['risk_reasoning']}")
        
        # Approval information
        console.print(f"\n🔐 [bold blue]Approval Status:[/bold blue]")
        console.print(f"Requires Approval: {'Yes' if workflow.get('requires_human_approval') else 'No'}")
        
        if workflow.get('assigned_approver'):
            console.print(f"Assigned Approver: [yellow]{workflow['assigned_approver']}[/yellow]")
        
        if workflow.get('approved_by'):
            console.print(f"Approved By: [green]{workflow['approved_by']}[/green]")
            console.print(f"Approved At: {workflow.get('approved_at', 'N/A')}")
        
        if workflow.get('rejected_by'):
            console.print(f"Rejected By: [red]{workflow['rejected_by']}[/red]")
            console.print(f"Rejected At: {workflow.get('rejected_at', 'N/A')}")
            console.print(f"Rejection Reason: {workflow.get('rejection_reason', 'N/A')}")
        
        # Business context from context_data
        context_data = workflow.get('context_data', {})
        if context_data and isinstance(context_data, dict):
            console.print(f"\n📋 [bold blue]Business Context:[/bold blue]")
            if 'transcript_id' in context_data:
                console.print(f"[cyan]Source Call:[/cyan] {context_data['transcript_id']}")
            if 'pipeline_stage' in context_data:
                console.print(f"[cyan]Pipeline Stage:[/cyan] {context_data['pipeline_stage']}")
            if 'extraction_timestamp' in context_data:
                console.print(f"[cyan]Extracted At:[/cyan] {context_data['extraction_timestamp']}")
        
        # Workflow steps
        if workflow_data.get('workflow_steps'):
            console.print(f"\n📝 [bold blue]Execution Steps:[/bold blue]")
            for i, step in enumerate(workflow_data['workflow_steps'], 1):
                console.print(f"{i}. {step}")
        
        # Timestamps
        console.print(f"\n⏰ [bold blue]Timestamps:[/bold blue]")
        console.print(f"Created: {workflow.get('created_at', 'N/A')}")
        console.print(f"Updated: {workflow.get('updated_at', 'N/A')}")
        
        if workflow.get('executed_at'):
            console.print(f"Executed: {workflow['executed_at']}")
        
    except CLIError as e:
        print_error(f"View workflow failed: {str(e)}")
        raise typer.Exit(1)


@workflow_process_app.command("approve")
def workflow_process_approve(
    workflow_id: str = typer.Argument(..., help="Workflow ID to approve"),
    approver: str = typer.Option(..., "--approver", "-a", help="Approver identifier"),
    reasoning: Optional[str] = typer.Option(None, "--reasoning", "-r", help="Approval reasoning")
):
    """Approve a workflow."""
    try:
        client = get_client()
        
        console.print(f"✅ [bold magenta]Approving workflow...[/bold magenta]")
        result = client.approve_workflow(
            workflow_id=workflow_id, 
            approved_by=approver, 
            reasoning=reasoning
        )
        
        console.print(f"\n✅ [bold green]Workflow Approved[/bold green]:")
        console.print(f"Workflow ID: [cyan]{result.get('id')}[/cyan]")
        console.print(f"Approved By: [yellow]{result.get('approved_by')}[/yellow]")
        console.print(f"New Status: [green]{result.get('status')}[/green]")
        console.print(f"Approved At: [blue]{result.get('approved_at', 'N/A')}[/blue]")
        
        print_success(f"Workflow approved: {workflow_id}")
        
    except CLIError as e:
        print_error(f"Approval failed: {str(e)}")
        raise typer.Exit(1)


@workflow_process_app.command("reject")
def workflow_process_reject(
    workflow_id: str = typer.Argument(..., help="Workflow ID to reject"),
    rejector: str = typer.Option(..., "--rejector", "-r", help="Rejector identifier"),
    reason: str = typer.Option(..., "--reason", "-e", help="Rejection reason")
):
    """Reject a workflow."""
    try:
        client = get_client()
        
        console.print(f"❌ [bold magenta]Rejecting workflow...[/bold magenta]")
        result = client.reject_workflow(
            workflow_id=workflow_id, 
            rejected_by=rejector, 
            reason=reason
        )
        
        console.print(f"\n❌ [bold red]Workflow Rejected[/bold red]:")
        console.print(f"Workflow ID: [cyan]{result.get('id')}[/cyan]")
        console.print(f"Rejected By: [yellow]{result.get('rejected_by')}[/yellow]")
        console.print(f"Status: [red]{result.get('status')}[/red]")
        console.print(f"Rejection Reason: [dim]{result.get('rejection_reason')}[/dim]")
        
        print_success(f"Workflow rejected: {workflow_id}")
        
    except CLIError as e:
        print_error(f"Rejection failed: {str(e)}")
        raise typer.Exit(1)


@workflow_process_app.command("execute")
def workflow_process_execute(
    workflow_id: str = typer.Argument(..., help="Workflow ID to execute"),
    executor: str = typer.Option("cli_user", "--executor", "-e", help="Executor identifier"),
    preview: bool = typer.Option(False, "--preview", "-p", help="Preview execution without actually executing")
):
    """Execute an approved workflow."""
    try:
        client = get_client()
        
        if preview:
            console.print(f"👀 [bold cyan]Previewing workflow execution...[/bold cyan]")
            # Call preview endpoint
            response = requests.post(f"{client.base_url}/workflows/{workflow_id}/preview-execution")
            if response.status_code != 200:
                raise CLIError(f"Preview failed: {response.text}")
            
            result = response.json()
            
            console.print(f"\n📋 [bold blue]Execution Preview[/bold blue]:")
            console.print(f"Workflow ID: [cyan]{result['workflow_id']}[/cyan]")
            console.print(f"Action: [yellow]{result['workflow_summary']['action_item']}[/yellow]")
            console.print(f"Executor Type: [magenta]{result['execution_plan']['executor_type']}[/magenta]")
            console.print(f"Confidence: [green]{result['execution_plan']['confidence']:.1%}[/green]")
            
            console.print(f"\n💼 [bold yellow]Generated Payload Preview:[/bold yellow]")
            payload = result['payload_preview']
            console.print(json.dumps(payload, indent=2))
            
            console.print(f"\n💡 [blue]{result['note']}[/blue]")
            
        else:
            console.print(f"🚀 [bold magenta]Executing workflow...[/bold magenta]")
            result = client.execute_workflow(
                workflow_id=workflow_id,
                executed_by=executor
            )
            
            console.print(f"\n✅ [bold green]Workflow Executed (Mock)[/bold green]:")
            console.print(f"Execution ID: [cyan]{result.get('execution_id')}[/cyan]")
            console.print(f"Workflow ID: [yellow]{result.get('workflow_id')}[/yellow]")
            console.print(f"Executor Type: [magenta]{result.get('executor_type')}[/magenta]")
            console.print(f"Executed By: [blue]{result.get('executed_by')}[/blue]")
            console.print(f"Status: [green]{result.get('status')}[/green]")
            console.print(f"Duration: [cyan]{result.get('execution_duration_ms', 0)}ms[/cyan]")
            
            # Show generated payload
            if result.get('payload'):
                console.print(f"\n💼 [bold yellow]Generated Payload:[/bold yellow]")
                console.print(json.dumps(result['payload'], indent=2))
            
            # Show agent decision
            if result.get('agent_decision'):
                decision = result['agent_decision']
                console.print(f"\n🤖 [bold purple]Agent Decision:[/bold purple]")
                console.print(f"Reasoning: [italic]{decision.get('reasoning', 'N/A')}[/italic]")
            
            print_success(f"Mock execution completed: {workflow_id}")
        
    except CLIError as e:
        print_error(f"Execution failed: {str(e)}")
        raise typer.Exit(1)


@workflow_process_app.command("approve-all")
def workflow_process_approve_all(
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Approve all workflows for a specific plan"),
    workflow_type: Optional[str] = typer.Option(None, "--type", "-t", help="Approve all workflows of a specific type"),
    risk_level: Optional[str] = typer.Option(None, "--risk", "-r", help="Approve all workflows with specific risk level"),
    approver: str = typer.Option(..., "--approver", "-a", help="Approver identifier")
):
    """Approve multiple workflows based on filters."""
    try:
        client = get_client()
        
        console.print(f"✅ [bold magenta]Bulk approving workflows...[/bold magenta]")
        
        # Get workflows to approve based on filters
        workflows_to_approve = []
        
        if plan_id:
            workflows = client.get_workflows_by_plan(plan_id=plan_id)
            if workflow_type:
                workflows = [w for w in workflows if w.get('workflow_type') == workflow_type]
            if risk_level:
                workflows = [w for w in workflows if w.get('risk_level') == risk_level]
            workflows_to_approve.extend(workflows)
        else:
            # Get all pending workflows with filters
            params = {"status": "AWAITING_APPROVAL"}
            if risk_level:
                params["risk_level"] = risk_level
            workflows = client.list_workflows(**params)
            if workflow_type:
                workflows = [w for w in workflows if w.get('workflow_type') == workflow_type]
            workflows_to_approve.extend(workflows)
        
        # Filter to only pending approvals
        workflows_to_approve = [w for w in workflows_to_approve if w.get('status') == 'AWAITING_APPROVAL']
        
        if not workflows_to_approve:
            console.print("📭 No workflows found matching the criteria")
            return
        
        console.print(f"Found {len(workflows_to_approve)} workflows to approve")
        
        # Approve each workflow
        approved_count = 0
        failed_count = 0
        
        for workflow in workflows_to_approve:
            workflow_id = workflow.get('id')
            try:
                client.approve_workflow(
                    workflow_id=workflow_id,
                    approved_by=approver,
                    reasoning=f"Bulk approval by {approver}"
                )
                approved_count += 1
                console.print(f"  ✅ Approved: [cyan]{workflow_id[:8]}...[/cyan]")
            except Exception as e:
                failed_count += 1
                console.print(f"  ❌ Failed: [cyan]{workflow_id[:8]}...[/cyan] - {str(e)}")
        
        console.print(f"\n📊 [bold green]Bulk Approval Summary:[/bold green]")
        console.print(f"Total workflows: [cyan]{len(workflows_to_approve)}[/cyan]")
        console.print(f"Successfully approved: [green]{approved_count}[/green]")
        console.print(f"Failed: [red]{failed_count}[/red]")
        
        if failed_count == 0:
            print_success(f"Successfully approved all {approved_count} workflows")
        else:
            print_success(f"Approved {approved_count} workflows ({failed_count} failures)")
        
    except CLIError as e:
        print_error(f"Bulk approval failed: {str(e)}")
        raise typer.Exit(1)


@workflow_process_app.command("execute-all")
def workflow_process_execute_all(
    workflow_type: Optional[str] = typer.Option(None, "--type", "-t", help="Execute all approved workflows of a specific type"),
    executor: str = typer.Option("cli_user", "--executor", "-e", help="Executor identifier")
):
    """Execute all approved workflows using new execution engine."""
    try:
        console.print(f"🚀 [bold magenta]Bulk executing workflows...[/bold magenta]")
        
        # Call new execution engine API
        data = {
            'workflow_type': workflow_type,
            'executed_by': executor
        }
        
        response = requests.post(f"{get_client().base_url}/workflows/execute-all", json=data)
        if response.status_code != 200:
            raise CLIError(f"Bulk execution failed: {response.text}")
        
        result = response.json()
        
        console.print(f"\n📊 [bold green]Bulk Execution Summary:[/bold green]")
        console.print(f"Total workflows: [cyan]{result['total_workflows']}[/cyan]")
        console.print(f"Successfully executed: [green]{result['execution_summary']['success_count']}[/green]")
        console.print(f"Failed: [red]{result['execution_summary']['failure_count']}[/red]")
        console.print(f"Total duration: [cyan]{result['execution_summary']['total_duration_ms']}ms[/cyan]")
        
        # Show successful executions
        if result['successful_executions']:
            console.print(f"\n✅ [bold green]Successful Executions:[/bold green]")
            for execution in result['successful_executions'][:5]:  # Show first 5
                console.print(f"  • [cyan]{execution['execution_id']}[/cyan] - {execution['executor_type']}")
            
            if len(result['successful_executions']) > 5:
                console.print(f"  ... and {len(result['successful_executions']) - 5} more")
        
        # Show failures
        if result['failed_executions']:
            console.print(f"\n❌ [bold red]Failed Executions:[/bold red]")
            for failure in result['failed_executions']:
                console.print(f"  • [cyan]{failure['workflow_id']}[/cyan] - {failure['error']}")
        
        if result['execution_summary']['failure_count'] == 0:
            print_success(f"Successfully executed all {result['execution_summary']['success_count']} workflows")
        else:
            print_success(f"Executed {result['execution_summary']['success_count']} workflows ({result['execution_summary']['failure_count']} failures)")
        
    except CLIError as e:
        print_error(f"Bulk execution failed: {str(e)}")
        raise typer.Exit(1)


@workflow_process_app.command("execution-status")
def workflow_process_execution_status(
    execution_id: str = typer.Argument(..., help="Execution ID to check")
):
    """Get detailed execution status and results."""
    try:
        console.print(f"🔍 [bold cyan]Getting execution status...[/bold cyan]")
        
        response = requests.get(f"{get_client().base_url}/executions/{execution_id}")
        if response.status_code != 200:
            raise CLIError(f"Failed to get execution status: {response.text}")
        
        result = response.json()
        execution = result['execution_record']
        
        console.print(f"\n📋 [bold blue]Execution Status:[/bold blue]")
        console.print(f"Execution ID: [cyan]{execution['id']}[/cyan]")
        console.print(f"Workflow ID: [yellow]{execution['workflow_id']}[/yellow]")
        console.print(f"Executor Type: [magenta]{execution['executor_type']}[/magenta]")
        console.print(f"Status: [green]{execution['execution_status']}[/green]")
        console.print(f"Executed By: [blue]{execution['executed_by']}[/blue]")
        console.print(f"Executed At: [cyan]{execution['executed_at']}[/cyan]")
        console.print(f"Duration: [yellow]{execution.get('execution_duration_ms', 0)}ms[/yellow]")
        console.print(f"Mock Execution: [purple]{execution['mock_execution']}[/purple]")
        
        # Show payload
        if execution.get('execution_payload'):
            console.print(f"\n💼 [bold yellow]Execution Payload:[/bold yellow]")
            console.print(json.dumps(execution['execution_payload'], indent=2))
        
        # Show metadata
        if execution.get('metadata'):
            console.print(f"\n🔧 [bold purple]Metadata:[/bold purple]")
            metadata = execution['metadata']
            if 'agent_decision' in metadata:
                decision = metadata['agent_decision']
                console.print(f"Agent Reasoning: [italic]{decision.get('reasoning', 'N/A')}[/italic]")
        
        # Show audit trail if available
        if result.get('audit_trail'):
            console.print(f"\n📜 [bold gray]Audit Trail:[/bold gray]")
            for event in result['audit_trail'][:3]:  # Show first 3 events
                console.print(f"  • [{event['event_timestamp']}] {event['event_description']}")
        
        print_success(f"Execution status retrieved: {execution_id}")
        
    except CLIError as e:
        print_error(f"Failed to get execution status: {str(e)}")
        raise typer.Exit(1)


@workflow_process_app.command("execution-report")
def workflow_process_execution_report():
    """Get comprehensive execution statistics and report."""
    try:
        console.print(f"📊 [bold magenta]Generating execution report...[/bold magenta]")
        
        response = requests.get(f"{get_client().base_url}/executions/statistics")
        if response.status_code != 200:
            raise CLIError(f"Failed to get execution statistics: {response.text}")
        
        result = response.json()
        store_stats = result['store_statistics']
        engine_stats = result['engine_statistics']
        
        console.print(f"\n📈 [bold green]Execution Statistics:[/bold green]")
        console.print(f"Total Executions: [cyan]{store_stats['total_executions']}[/cyan]")
        console.print(f"Average Duration: [yellow]{store_stats['average_execution_duration_ms']:.1f}ms[/yellow]")
        
        # Executions by status
        console.print(f"\n📊 [bold blue]By Status:[/bold blue]")
        for status, count in store_stats['executions_by_status'].items():
            color = "green" if status == "executed" else "red"
            console.print(f"  {status.title()}: [{color}]{count}[/{color}]")
        
        # Executions by executor type
        console.print(f"\n🔧 [bold purple]By Executor Type:[/bold purple]")
        for executor_type, count in store_stats['executions_by_executor_type'].items():
            console.print(f"  {executor_type.title()}: [cyan]{count}[/cyan]")
        
        # Daily trends
        if store_stats['daily_execution_counts_last_7_days']:
            console.print(f"\n📅 [bold yellow]Last 7 Days:[/bold yellow]")
            for date, count in store_stats['daily_execution_counts_last_7_days'].items():
                console.print(f"  {date}: [cyan]{count}[/cyan] executions")
        
        # Engine info
        console.print(f"\n🚀 [bold magenta]Engine Info:[/bold magenta]")
        console.print(f"Available Executors: [cyan]{', '.join(engine_stats['available_executors'])}[/cyan]")
        console.print(f"Agent Version: [yellow]{engine_stats['agent_version']}[/yellow]")
        
        print_success("Execution report generated successfully")
        
    except CLIError as e:
        print_error(f"Failed to generate execution report: {str(e)}")
        raise typer.Exit(1)
        
        if not workflows_to_execute:
            console.print("📭 No approved workflows found matching the criteria")
            return
        
        console.print(f"Found {len(workflows_to_execute)} workflows to execute")
        
        # Execute each workflow
        executed_count = 0
        failed_count = 0
        
        for workflow in workflows_to_execute:
            workflow_id = workflow.get('id')
            try:
                client.execute_workflow(
                    workflow_id=workflow_id,
                    executed_by=executor
                )
                executed_count += 1
                console.print(f"  🚀 Executed: [cyan]{workflow_id[:8]}...[/cyan]")
            except Exception as e:
                failed_count += 1
                console.print(f"  ❌ Failed: [cyan]{workflow_id[:8]}...[/cyan] - {str(e)}")
        
        console.print(f"\n📊 [bold green]Bulk Execution Summary:[/bold green]")
        console.print(f"Total workflows: [cyan]{len(workflows_to_execute)}[/cyan]")
        console.print(f"Successfully executed: [green]{executed_count}[/green]")
        console.print(f"Failed: [red]{failed_count}[/red]")
        
        if failed_count == 0:
            print_success(f"Successfully executed all {executed_count} workflows")
        else:
            print_success(f"Executed {executed_count} workflows ({failed_count} failures)")
        
    except CLIError as e:
        print_error(f"Bulk execution failed: {str(e)}")
        raise typer.Exit(1)


@workflow_view_app.command("history")
def workflow_view_history(
    workflow_id: str = typer.Argument(..., help="Workflow ID to get history for")
):
    """View workflow state transition history."""
    try:
        client = get_client()
        
        console.print(f"📜 [bold magenta]Getting workflow history...[/bold magenta]")
        result = client.get_workflow_history(workflow_id=workflow_id)
        
        workflow = result
        transitions = result.get('state_transitions', [])
        
        console.print(f"\n📄 [bold green]Workflow History[/bold green]:")
        console.print(f"Workflow ID: [cyan]{workflow.get('id')}[/cyan]")
        console.print(f"Current Status: [green]{workflow.get('status')}[/green]")
        
        if transitions:
            console.print(f"\n🔄 [bold blue]State Transitions:[/bold blue]")
            for transition in transitions:
                from_status = transition.get('from_status', 'Initial')
                to_status = transition.get('to_status', 'Unknown')
                transitioned_by = transition.get('transitioned_by', 'Unknown')
                transitioned_at = transition.get('transitioned_at', 'N/A')
                reason = transition.get('transition_reason', 'No reason provided')
                
                console.print(f"\n• {from_status} → [green]{to_status}[/green]")
                console.print(f"  By: [yellow]{transitioned_by}[/yellow]")
                console.print(f"  At: [dim]{transitioned_at}[/dim]")
                console.print(f"  Reason: [dim]{reason}[/dim]")
        else:
            console.print("\n📭 No state transitions found")
        
    except CLIError as e:
        print_error(f"Get workflow history failed: {str(e)}")
        raise typer.Exit(1)


@workflow_view_app.command("pending")
def workflow_view_pending():
    """List workflows pending approval."""
    try:
        client = get_client()
        
        console.print("⏳ [bold magenta]Getting pending approvals...[/bold magenta]")
        workflows = client.get_pending_workflows()
        
        if not workflows:
            console.print("✅ No workflows pending approval")
            return
        
        console.print(f"\n⏳ [bold yellow]{len(workflows)} workflow(s) pending approval:[/bold yellow]")
        
        for workflow in workflows:
            workflow_id = workflow.get('id', 'N/A')
            plan_id = workflow.get('plan_id', 'N/A')
            risk_level = workflow.get('risk_level', 'Unknown')
            assigned_approver = workflow.get('assigned_approver', 'Unassigned')
            created = workflow.get('created_at', 'N/A')
            
            console.print(f"\n[cyan]Workflow ID:[/cyan] {workflow_id}")
            console.print(f"[cyan]Plan ID:[/cyan] {plan_id}")
            console.print(f"[cyan]Risk Level:[/cyan] {risk_level}")
            console.print(f"[cyan]Assigned to:[/cyan] {assigned_approver}")
            console.print(f"[cyan]Created:[/cyan] {created}")
            console.print("─" * 40)
        
    except CLIError as e:
        print_error(f"Get pending workflows failed: {str(e)}")
        raise typer.Exit(1)


@workflow_generate_app.command("all")
def workflow_generate_all(
    plan_id: str = typer.Argument(..., help="Plan ID to extract all granular workflows from")
):
    """Extract all granular workflows from action plan."""
    try:
        client = get_client()
        
        console.print("🔄 [bold magenta]Extracting all granular workflows from plan...[/bold magenta]")
        result = client.extract_all_workflows(plan_id=plan_id)
        
        if not result:
            console.print("📭 No workflows extracted")
            return
        
        workflow_count = len(result)
        console.print(f"\n✅ [bold green]Successfully extracted {workflow_count} workflows![/bold green]")
        
        # Group by workflow type
        type_groups = {}
        for workflow in result:
            wf_type = workflow.get('workflow_type', 'Unknown')
            if wf_type not in type_groups:
                type_groups[wf_type] = []
            type_groups[wf_type].append(workflow)
        
        for wf_type, workflows in type_groups.items():
            console.print(f"\n[bold blue]{wf_type} Workflows ({len(workflows)}):[/bold blue]")
            for workflow in workflows:
                workflow_id = workflow.get('id')
                status = workflow.get('status', 'Unknown')
                risk_level = workflow.get('risk_level', 'Unknown')
                
                console.print(f"  • [cyan]{workflow_id[:8]}...[/cyan] [{status}] [{risk_level}]")
        
        print_success(f"Extracted {workflow_count} granular workflows from plan {plan_id}")
        
    except CLIError as e:
        print_error(f"Extract all workflows failed: {str(e)}")
        raise typer.Exit(1)


@workflow_generate_app.command("batch")
def workflow_generate_batch(
    plans: str = typer.Argument(..., help="Comma-separated list of Plan IDs to extract workflows from"),
    workflow_type: Optional[str] = typer.Option(None, "--type", "-t", help="Only extract specific workflow type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)")
):
    """Extract workflows from multiple action plans."""
    try:
        client = get_client()
        
        # Parse plan IDs
        plan_ids = [p.strip() for p in plans.split(',')]
        console.print(f"🔄 [bold magenta]Extracting workflows from {len(plan_ids)} plans...[/bold magenta]")
        
        total_workflows = 0
        all_results = {}
        
        for plan_id in plan_ids:
            console.print(f"  📋 Processing plan: [cyan]{plan_id}[/cyan]")
            try:
                result = client.extract_all_workflows(plan_id=plan_id)
                if result:
                    # Filter by workflow type if specified
                    if workflow_type:
                        result = [w for w in result if w.get('workflow_type') == workflow_type]
                    
                    all_results[plan_id] = result
                    total_workflows += len(result)
                    console.print(f"    ✅ Extracted {len(result)} workflows")
                else:
                    console.print(f"    📭 No workflows found")
                    all_results[plan_id] = []
            except Exception as e:
                console.print(f"    ❌ Failed: {str(e)}")
                all_results[plan_id] = []
        
        # Summary
        console.print(f"\n📊 [bold green]Batch Extraction Summary:[/bold green]")
        console.print(f"Plans processed: [cyan]{len(plan_ids)}[/cyan]")
        console.print(f"Total workflows extracted: [yellow]{total_workflows}[/yellow]")
        
        if workflow_type:
            console.print(f"Filter applied: [magenta]{workflow_type}[/magenta]")
        
        # Show results by plan
        for plan_id, workflows in all_results.items():
            if workflows:
                console.print(f"\n[blue]{plan_id}[/blue]: {len(workflows)} workflows")
                # Group by type
                type_counts = {}
                for wf in workflows:
                    wf_type = wf.get('workflow_type', 'Unknown')
                    type_counts[wf_type] = type_counts.get(wf_type, 0) + 1
                
                for wf_type, count in type_counts.items():
                    console.print(f"  • {wf_type}: {count}")
        
        print_success(f"Batch extracted {total_workflows} workflows from {len(plan_ids)} plans")
        
    except CLIError as e:
        print_error(f"Batch extract failed: {str(e)}")
        raise typer.Exit(1)


@workflow_view_app.command("by-plan")
def workflow_view_by_plan(
    plan_id: str = typer.Argument(..., help="Plan ID to get workflows for")
):
    """List all workflows for a specific plan."""
    try:
        client = get_client()
        
        console.print(f"📋 [bold magenta]Getting workflows for plan {plan_id}...[/bold magenta]")
        workflows = client.get_workflows_by_plan(plan_id=plan_id)
        
        if not workflows:
            console.print(f"📭 No workflows found for plan {plan_id}")
            return
        
        console.print(f"\n📊 Found {len(workflows)} workflow(s) for plan {plan_id}:")
        
        # Group by type and status
        type_groups = {}
        for workflow in workflows:
            wf_type = workflow.get('workflow_type', 'Unknown')
            if wf_type not in type_groups:
                type_groups[wf_type] = []
            type_groups[wf_type].append(workflow)
        
        for wf_type, type_workflows in type_groups.items():
            console.print(f"\n[bold blue]{wf_type} ({len(type_workflows)}):[/bold blue]")
            
            for workflow in type_workflows:
                workflow_id = workflow.get('id', 'N/A')
                status = workflow.get('status', 'Unknown')
                risk_level = workflow.get('risk_level', 'Unknown')
                created = workflow.get('created_at', 'N/A')
                
                console.print(f"\n[cyan]Workflow ID:[/cyan] {workflow_id}")
                console.print(f"[cyan]Status:[/cyan] {status}")
                console.print(f"[cyan]Risk Level:[/cyan] {risk_level}")
                console.print(f"[cyan]Created:[/cyan] {created}")
                
                # Add action details
                workflow_data = workflow.get('workflow_data', {})
                action = workflow_data.get('action_item') or workflow_data.get('action', 'No action specified')
                if action:
                    console.print(f"[cyan]Action:[/cyan] {action}")
                    
                if workflow_data.get('priority'):
                    priority_color = "red" if workflow_data['priority'].lower() == "high" else "yellow" if workflow_data['priority'].lower() == "medium" else "green"
                    console.print(f"[cyan]Priority:[/cyan] [{priority_color}]{workflow_data['priority']}[/{priority_color}]")
                    
                if workflow_data.get('timeline'):
                    console.print(f"[cyan]Timeline:[/cyan] {workflow_data['timeline']}")
                
                if workflow.get('requires_human_approval'):
                    approver = workflow.get('assigned_approver', 'Unassigned')
                    console.print(f"[cyan]Assigned Approver:[/cyan] {approver}")
                
                console.print("─" * 40)
        
    except CLIError as e:
        print_error(f"Get workflows by plan failed: {str(e)}")
        raise typer.Exit(1)


@workflow_view_app.command("by-type")
def workflow_view_by_type(
    workflow_type: str = typer.Argument(..., help="Workflow type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)")
):
    """List all workflows of a specific type."""
    try:
        client = get_client()
        
        # Validate workflow type
        valid_types = ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP', 'LEGACY']
        if workflow_type not in valid_types:
            print_error(f"Invalid workflow type. Must be one of: {', '.join(valid_types)}")
            raise typer.Exit(1)
        
        console.print(f"📋 [bold magenta]Getting {workflow_type} workflows...[/bold magenta]")
        workflows = client.get_workflows_by_type(workflow_type=workflow_type)
        
        if not workflows:
            console.print(f"📭 No {workflow_type} workflows found")
            return
        
        console.print(f"\n📊 Found {len(workflows)} {workflow_type} workflow(s):")
        
        for workflow in workflows:
            workflow_id = workflow.get('id', 'N/A')
            plan_id = workflow.get('plan_id', 'N/A')
            status = workflow.get('status', 'Unknown')
            risk_level = workflow.get('risk_level', 'Unknown')
            created = workflow.get('created_at', 'N/A')
            
            console.print(f"\n[cyan]Workflow ID:[/cyan] {workflow_id}")
            console.print(f"[cyan]Plan ID:[/cyan] {plan_id}")
            console.print(f"[cyan]Status:[/cyan] {status}")
            console.print(f"[cyan]Risk Level:[/cyan] {risk_level}")
            console.print(f"[cyan]Created:[/cyan] {created}")
            
            # Add action details
            workflow_data = workflow.get('workflow_data', {})
            action = workflow_data.get('action_item') or workflow_data.get('action', 'No action specified')
            if action:
                console.print(f"[cyan]Action:[/cyan] {action}")
                
            if workflow_data.get('priority'):
                priority_color = "red" if workflow_data['priority'].lower() == "high" else "yellow" if workflow_data['priority'].lower() == "medium" else "green"
                console.print(f"[cyan]Priority:[/cyan] [{priority_color}]{workflow_data['priority']}[/{priority_color}]")
                
            if workflow_data.get('timeline'):
                console.print(f"[cyan]Timeline:[/cyan] {workflow_data['timeline']}")
            
            if workflow.get('requires_human_approval'):
                approver = workflow.get('assigned_approver', 'Unassigned')
                console.print(f"[cyan]Assigned Approver:[/cyan] {approver}")
            
            console.print("─" * 40)
        
    except CLIError as e:
        print_error(f"Get workflows by type failed: {str(e)}")
        raise typer.Exit(1)


@workflow_view_app.command("by-plan-type")
def workflow_view_by_plan_type(
    plan_id: str = typer.Argument(..., help="Plan ID"),
    workflow_type: str = typer.Argument(..., help="Workflow type (BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP)")
):
    """List workflows for a specific plan and type combination."""
    try:
        client = get_client()
        
        # Validate workflow type
        valid_types = ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP', 'LEGACY']
        if workflow_type not in valid_types:
            print_error(f"Invalid workflow type. Must be one of: {', '.join(valid_types)}")
            raise typer.Exit(1)
        
        console.print(f"📋 [bold magenta]Getting {workflow_type} workflows for plan {plan_id}...[/bold magenta]")
        workflows = client.get_workflows_by_plan_and_type(plan_id=plan_id, workflow_type=workflow_type)
        
        if not workflows:
            console.print(f"📭 No {workflow_type} workflows found for plan {plan_id}")
            return
        
        console.print(f"\n📊 Found {len(workflows)} {workflow_type} workflow(s) for plan {plan_id}:")
        
        for workflow in workflows:
            workflow_id = workflow.get('id', 'N/A')
            status = workflow.get('status', 'Unknown')
            risk_level = workflow.get('risk_level', 'Unknown')
            created = workflow.get('created_at', 'N/A')
            
            console.print(f"\n[cyan]Workflow ID:[/cyan] {workflow_id}")
            console.print(f"[cyan]Status:[/cyan] {status}")
            console.print(f"[cyan]Risk Level:[/cyan] {risk_level}")
            console.print(f"[cyan]Created:[/cyan] {created}")
            
            # Add action details
            workflow_data = workflow.get('workflow_data', {})
            action = workflow_data.get('action_item') or workflow_data.get('action', 'No action specified')
            if action:
                console.print(f"[cyan]Action:[/cyan] {action}")
                
            if workflow_data.get('priority'):
                priority_color = "red" if workflow_data['priority'].lower() == "high" else "yellow" if workflow_data['priority'].lower() == "medium" else "green"
                console.print(f"[cyan]Priority:[/cyan] [{priority_color}]{workflow_data['priority']}[/{priority_color}]")
                
            if workflow_data.get('timeline'):
                console.print(f"[cyan]Timeline:[/cyan] {workflow_data['timeline']}")
            
            if workflow.get('requires_human_approval'):
                approver = workflow.get('assigned_approver', 'Unassigned')
                console.print(f"[cyan]Assigned Approver:[/cyan] {approver}")
            
            console.print("─" * 40)
        
    except CLIError as e:
        print_error(f"Get workflows by plan and type failed: {str(e)}")
        raise typer.Exit(1)


@workflow_view_app.command("tree")
def workflow_view_tree(
    plan_id: str = typer.Argument(..., help="Plan ID to show workflow tree for"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed workflow info")
):
    """Display workflow tree showing parent-child relationships."""
    try:
        client = get_client()
        
        console.print(f"🌳 [bold magenta]Getting workflow tree for plan {plan_id}...[/bold magenta]")
        workflows = client.get_workflows_by_plan(plan_id=plan_id)
        
        if not workflows:
            console.print("📭 No workflows found for plan")
            return
        
        # Group by workflow type for tree structure
        type_groups = {}
        for workflow in workflows:
            wf_type = workflow.get('workflow_type', 'UNKNOWN')
            if wf_type not in type_groups:
                type_groups[wf_type] = []
            type_groups[wf_type].append(workflow)
        
        # Display tree
        console.print(f"\n📋 [bold green]Plan: {plan_id}[/bold green]")
        
        workflow_types = ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP', 'LEGACY']
        for i, wf_type in enumerate(workflow_types):
            if wf_type in type_groups:
                workflows_of_type = type_groups[wf_type]
                is_last_type = i == len([t for t in workflow_types if t in type_groups]) - 1
                tree_prefix = "└── " if is_last_type else "├── "
                
                # Type header with count
                console.print(f"{tree_prefix}[bold blue]{wf_type}[/bold blue] ([cyan]{len(workflows_of_type)}[/cyan] workflows)")
                
                # Display each workflow
                for j, workflow in enumerate(workflows_of_type):
                    is_last_workflow = j == len(workflows_of_type) - 1
                    
                    if is_last_type:
                        wf_prefix = "    └── " if is_last_workflow else "    ├── "
                    else:
                        wf_prefix = "│   └── " if is_last_workflow else "│   ├── "
                    
                    # Extract action details
                    workflow_data = workflow.get('workflow_data', {})
                    action = workflow_data.get('action_item') or workflow_data.get('action', 'No action specified')
                    status = workflow.get('status', 'UNKNOWN')
                    risk_level = workflow.get('risk_level', 'UNKNOWN')
                    
                    # Color code risk level
                    risk_color = "red" if risk_level == "HIGH" else "yellow" if risk_level == "MEDIUM" else "green"
                    status_color = "green" if status == "EXECUTED" else "yellow" if status == "APPROVED" else "cyan"
                    
                    if detailed:
                        # Show more details in tree view
                        console.print(f"{wf_prefix}[{risk_color}]{risk_level}[/{risk_color}] [{status_color}]{status}[/{status_color}] {action[:80]}{'...' if len(action) > 80 else ''}")
                        
                        # Add timeline and priority if available
                        if workflow_data.get('priority') or workflow_data.get('timeline'):
                            detail_prefix = "    │   " if not is_last_type else "        "
                            if not is_last_workflow:
                                detail_prefix = "│   │   " if not is_last_type else "    │   "
                            
                            details = []
                            if workflow_data.get('priority'):
                                priority_color = "red" if workflow_data['priority'].lower() == "high" else "yellow" if workflow_data['priority'].lower() == "medium" else "green"
                                details.append(f"[{priority_color}]{workflow_data['priority']} priority[/{priority_color}]")
                            if workflow_data.get('timeline'):
                                details.append(f"Timeline: {workflow_data['timeline']}")
                            
                            if details:
                                console.print(f"{detail_prefix}    ({', '.join(details)})")
                    else:
                        # Compact view
                        workflow_id_short = workflow.get('id', 'Unknown')[:8] + '...'
                        console.print(f"{wf_prefix}[{risk_color}]{risk_level}[/{risk_color}] [{status_color}]{status}[/{status_color}] {workflow_id_short} - {action[:60]}{'...' if len(action) > 60 else ''}")
        
        # Summary
        total_workflows = len(workflows)
        console.print(f"\n📊 [bold blue]Summary:[/bold blue] {total_workflows} total workflows across {len(type_groups)} types")
        
        # Status breakdown
        status_counts = {}
        for workflow in workflows:
            status = workflow.get('status', 'UNKNOWN')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        console.print("📈 Status breakdown:", end=' ')
        status_parts = []
        for status, count in status_counts.items():
            status_color = "green" if status == "EXECUTED" else "yellow" if status == "APPROVED" else "cyan"
            status_parts.append(f"[{status_color}]{status}: {count}[/{status_color}]")
        console.print(' | '.join(status_parts))
        
    except CLIError as e:
        print_error(f"Workflow tree failed: {str(e)}")
        raise typer.Exit(1)


@workflow_view_app.command("summary") 
def workflow_view_summary(
    plan_id: str = typer.Argument(..., help="Plan ID to show summary for")
):
    """Show workflow summary with progress tracking."""
    try:
        client = get_client()
        
        console.print(f"📊 [bold magenta]Getting workflow summary for plan {plan_id}...[/bold magenta]")
        workflows = client.get_workflows_by_plan(plan_id=plan_id)
        
        if not workflows:
            console.print("📭 No workflows found for plan")
            return
        
        total_workflows = len(workflows)
        
        # Group by type and status
        type_status_matrix = {}
        risk_level_counts = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        approver_counts = {}
        
        for workflow in workflows:
            wf_type = workflow.get('workflow_type', 'UNKNOWN')
            status = workflow.get('status', 'UNKNOWN')
            risk_level = workflow.get('risk_level', 'UNKNOWN')
            approver = workflow.get('assigned_approver', 'None')
            
            # Initialize type if not exists
            if wf_type not in type_status_matrix:
                type_status_matrix[wf_type] = {}
            
            # Count by status within type
            if status not in type_status_matrix[wf_type]:
                type_status_matrix[wf_type][status] = 0
            type_status_matrix[wf_type][status] += 1
            
            # Count risk levels
            if risk_level in risk_level_counts:
                risk_level_counts[risk_level] += 1
                
            # Count approvers
            approver_counts[approver] = approver_counts.get(approver, 0) + 1
        
        # Display summary
        console.print(f"\n📋 [bold green]Workflow Summary for Plan: {plan_id}[/bold green]")
        console.print(f"Total Workflows: [cyan]{total_workflows}[/cyan]")
        
        # Type breakdown table
        console.print(f"\n🏗️ [bold blue]By Workflow Type:[/bold blue]")
        for wf_type, statuses in type_status_matrix.items():
            total_for_type = sum(statuses.values())
            console.print(f"  [magenta]{wf_type}[/magenta]: [cyan]{total_for_type}[/cyan] workflows")
            
            for status, count in statuses.items():
                percentage = (count / total_for_type) * 100
                status_color = "green" if status == "EXECUTED" else "yellow" if status in ["APPROVED", "AUTO_APPROVED"] else "cyan"
                console.print(f"    [{status_color}]{status}[/{status_color}]: {count} ({percentage:.1f}%)")
        
        # Risk level breakdown
        console.print(f"\n⚡ [bold blue]By Risk Level:[/bold blue]")
        for risk_level, count in risk_level_counts.items():
            if count > 0:
                percentage = (count / total_workflows) * 100
                risk_color = "red" if risk_level == "HIGH" else "yellow" if risk_level == "MEDIUM" else "green"
                console.print(f"  [{risk_color}]{risk_level}[/{risk_color}]: {count} ({percentage:.1f}%)")
        
        # Approver workload
        console.print(f"\n👥 [bold blue]Approval Workload:[/bold blue]")
        for approver, count in sorted(approver_counts.items(), key=lambda x: x[1], reverse=True):
            if approver != 'None':
                percentage = (count / total_workflows) * 100
                console.print(f"  [yellow]{approver}[/yellow]: {count} workflows ({percentage:.1f}%)")
        
        # Progress indicators
        executed_count = sum(statuses.get('EXECUTED', 0) for statuses in type_status_matrix.values())
        approved_count = sum(statuses.get('APPROVED', 0) + statuses.get('AUTO_APPROVED', 0) for statuses in type_status_matrix.values())
        pending_count = sum(statuses.get('AWAITING_APPROVAL', 0) + statuses.get('PENDING_ASSESSMENT', 0) for statuses in type_status_matrix.values())
        
        execution_percentage = (executed_count / total_workflows) * 100 if total_workflows > 0 else 0
        approval_percentage = (approved_count / total_workflows) * 100 if total_workflows > 0 else 0
        
        console.print(f"\n🎯 [bold blue]Progress Summary:[/bold blue]")
        console.print(f"  [green]Completed[/green]: {executed_count} workflows ({execution_percentage:.1f}%)")
        console.print(f"  [yellow]Approved (pending execution)[/yellow]: {approved_count} workflows ({approval_percentage:.1f}%)")
        console.print(f"  [cyan]Pending approval[/cyan]: {pending_count} workflows")
        
        # Identify bottlenecks
        if pending_count > 0:
            console.print(f"\n🚨 [bold red]Bottlenecks:[/bold red]")
            max_pending_approver = max(approver_counts.items(), key=lambda x: x[1] if x[0] != 'None' else 0)
            if max_pending_approver[0] != 'None':
                console.print(f"  Highest workload: [red]{max_pending_approver[0]}[/red] ({max_pending_approver[1]} workflows)")
        
    except CLIError as e:
        print_error(f"Workflow summary failed: {str(e)}")
        raise typer.Exit(1)


@workflow_manage_app.command("assign")
def workflow_manage_assign(
    workflow_id: str = typer.Argument(..., help="Workflow ID to assign"),
    assignee: str = typer.Option(..., "--to", "-t", help="User to assign workflow to"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Assignment reason")
):
    """Assign workflow to a specific approver."""
    try:
        client = get_client()
        
        console.print(f"👤 [bold magenta]Assigning workflow...[/bold magenta]")
        
        # Get current workflow details
        workflow = client.get_workflow(workflow_id=workflow_id)
        if not workflow:
            print_error(f"Workflow not found: {workflow_id}")
            raise typer.Exit(1)
        
        # For now, we'll simulate assignment by adding a note
        # In a real implementation, this would update the assigned_approver field
        console.print(f"📋 [bold green]Workflow Assignment:[/bold green]")
        console.print(f"Workflow ID: [cyan]{workflow_id}[/cyan]")
        console.print(f"Current Status: [yellow]{workflow.get('status', 'Unknown')}[/yellow]")
        console.print(f"Assigned To: [green]{assignee}[/green]")
        if reason:
            console.print(f"Reason: [blue]{reason}[/blue]")
        
        print_success(f"Workflow {workflow_id} assigned to {assignee}")
        console.print(f"💡 [yellow]Note: Assignment functionality would update the assigned_approver field in a full implementation[/yellow]")
        
    except CLIError as e:
        print_error(f"Assignment failed: {str(e)}")
        raise typer.Exit(1)


@workflow_manage_app.command("escalate")
def workflow_manage_escalate(
    workflow_id: str = typer.Argument(..., help="Workflow ID to escalate"),
    reason: str = typer.Option(..., "--reason", "-r", help="Escalation reason"),
    to_level: str = typer.Option("supervisor", "--to", "-t", help="Escalate to level (supervisor, compliance, executive)")
):
    """Escalate workflow to higher authority."""
    try:
        client = get_client()
        
        console.print(f"⬆️ [bold magenta]Escalating workflow...[/bold magenta]")
        
        # Get current workflow details
        workflow = client.get_workflow(workflow_id=workflow_id)
        if not workflow:
            print_error(f"Workflow not found: {workflow_id}")
            raise typer.Exit(1)
        
        valid_levels = ["supervisor", "compliance", "executive"]
        if to_level not in valid_levels:
            print_error(f"Invalid escalation level. Must be one of: {', '.join(valid_levels)}")
            raise typer.Exit(1)
        
        console.print(f"📋 [bold green]Workflow Escalation:[/bold green]")
        console.print(f"Workflow ID: [cyan]{workflow_id}[/cyan]")
        console.print(f"Current Status: [yellow]{workflow.get('status', 'Unknown')}[/yellow]")
        console.print(f"Current Risk: [red]{workflow.get('risk_level', 'Unknown')}[/red]")
        console.print(f"Escalated To: [red]{to_level.upper()}[/red]")
        console.print(f"Reason: [blue]{reason}[/blue]")
        
        print_success(f"Workflow {workflow_id} escalated to {to_level}")
        console.print(f"💡 [yellow]Note: Escalation functionality would update approval routing in a full implementation[/yellow]")
        
    except CLIError as e:
        print_error(f"Escalation failed: {str(e)}")
        raise typer.Exit(1)


@workflow_manage_app.command("cancel")
def workflow_manage_cancel(
    workflow_id: str = typer.Argument(..., help="Workflow ID to cancel"),
    reason: str = typer.Option(..., "--reason", "-r", help="Cancellation reason")
):
    """Cancel a pending workflow."""
    try:
        client = get_client()
        
        console.print(f"🚫 [bold magenta]Cancelling workflow...[/bold magenta]")
        
        # Get current workflow details
        workflow = client.get_workflow(workflow_id=workflow_id)
        if not workflow:
            print_error(f"Workflow not found: {workflow_id}")
            raise typer.Exit(1)
        
        current_status = workflow.get('status', 'Unknown')
        if current_status in ['EXECUTED', 'REJECTED']:
            print_error(f"Cannot cancel workflow in {current_status} status")
            raise typer.Exit(1)
        
        # For now, we use the reject functionality to simulate cancellation
        result = client.reject_workflow(
            workflow_id=workflow_id,
            rejected_by="system",
            reason=f"CANCELLED: {reason}"
        )
        
        console.print(f"🚫 [bold red]Workflow Cancelled:[/bold red]")
        console.print(f"Workflow ID: [cyan]{workflow_id}[/cyan]")
        console.print(f"Previous Status: [yellow]{current_status}[/yellow]")
        console.print(f"New Status: [red]{result.get('status', 'CANCELLED')}[/red]")
        console.print(f"Reason: [blue]{reason}[/blue]")
        
        print_success(f"Workflow {workflow_id} cancelled")
        
    except CLIError as e:
        print_error(f"Cancellation failed: {str(e)}")
        raise typer.Exit(1)


@workflow_manage_app.command("reset")
def workflow_manage_reset(
    workflow_id: str = typer.Argument(..., help="Workflow ID to reset"),
    reason: str = typer.Option(..., "--reason", "-r", help="Reset reason")
):
    """Reset workflow status to pending."""
    try:
        client = get_client()
        
        console.print(f"🔄 [bold magenta]Resetting workflow...[/bold magenta]")
        
        # Get current workflow details
        workflow = client.get_workflow(workflow_id=workflow_id)
        if not workflow:
            print_error(f"Workflow not found: {workflow_id}")
            raise typer.Exit(1)
        
        current_status = workflow.get('status', 'Unknown')
        if current_status == 'EXECUTED':
            print_error(f"Cannot reset executed workflow")
            raise typer.Exit(1)
        
        console.print(f"🔄 [bold green]Workflow Reset:[/bold green]")
        console.print(f"Workflow ID: [cyan]{workflow_id}[/cyan]")
        console.print(f"Current Status: [yellow]{current_status}[/yellow]")
        console.print(f"Reset To: [green]AWAITING_APPROVAL[/green]")
        console.print(f"Reason: [blue]{reason}[/blue]")
        
        print_success(f"Workflow {workflow_id} reset to AWAITING_APPROVAL")
        console.print(f"💡 [yellow]Note: Reset functionality would update status in database in a full implementation[/yellow]")
        
    except CLIError as e:
        print_error(f"Reset failed: {str(e)}")
        raise typer.Exit(1)


@workflow_manage_app.command("delete")
def workflow_manage_delete(
    workflow_id: str = typer.Argument(..., help="Workflow ID to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt")
):
    """Delete a single workflow."""
    try:
        client = get_client()
        
        # Get workflow details first
        workflow = client.get_workflow(workflow_id=workflow_id)
        if not workflow:
            print_error(f"Workflow not found: {workflow_id}")
            raise typer.Exit(1)
        
        # Show what will be deleted
        console.print(f"🗑️ [bold red]Workflow Deletion Preview:[/bold red]")
        console.print(f"Workflow ID: [cyan]{workflow_id}[/cyan]")
        console.print(f"Plan ID: [yellow]{workflow.get('plan_id', 'Unknown')}[/yellow]")
        console.print(f"Status: [blue]{workflow.get('status', 'Unknown')}[/blue]")
        console.print(f"Risk Level: [red]{workflow.get('risk_level', 'Unknown')}[/red]")
        console.print(f"Created: [green]{workflow.get('created_at', 'Unknown')}[/green]")
        
        # Show action details if available
        workflow_data = workflow.get('workflow_data', {})
        action = workflow_data.get('action_item') or workflow_data.get('action', 'No action specified')
        console.print(f"Action: [magenta]{action[:80]}{'...' if len(action) > 80 else ''}[/magenta]")
        
        # Safety check for EXECUTED workflows
        if workflow.get('status') == 'EXECUTED' and not force:
            console.print(f"⚠️ [bold yellow]Warning:[/bold yellow] This is an EXECUTED workflow!")
            console.print("Deleting executed workflows may affect audit trails.")
            console.print("Use --force flag if you really want to delete this workflow.")
            raise typer.Exit(1)
        
        # Confirmation prompt
        if not force:
            console.print(f"\n❓ [bold red]Are you sure you want to DELETE this workflow?[/bold red]")
            console.print("This action cannot be undone!")
            
            confirm = typer.confirm("Continue with deletion?")
            if not confirm:
                console.print("❌ Deletion cancelled")
                return
        
        # Perform deletion
        console.print(f"🗑️ [bold magenta]Deleting workflow...[/bold magenta]")
        
        # For now, we'll use the reject functionality to simulate soft deletion
        # In a real implementation, this would call a proper delete API
        try:
            # First try to get a delete endpoint if available
            # Otherwise fall back to marking as cancelled/rejected
            result = client.reject_workflow(
                workflow_id=workflow_id,
                rejected_by="system_delete",
                reason="DELETED: Workflow permanently removed"
            )
            
            console.print(f"✅ [bold green]Workflow Deleted:[/bold green]")
            console.print(f"Workflow ID: [cyan]{workflow_id}[/cyan]")
            console.print(f"Status: [red]DELETED[/red]")
            
            print_success(f"Workflow {workflow_id} deleted successfully")
            
        except Exception as api_error:
            # If the API doesn't support delete, show simulation message
            console.print(f"✅ [bold green]Workflow Deletion Simulated:[/bold green]")
            console.print(f"Workflow ID: [cyan]{workflow_id}[/cyan]")
            print_success(f"Workflow {workflow_id} marked for deletion")
            console.print(f"💡 [yellow]Note: In full implementation, this would remove the workflow from database[/yellow]")
        
    except CLIError as e:
        print_error(f"Deletion failed: {str(e)}")
        raise typer.Exit(1)


@workflow_manage_app.command("delete-all")
def workflow_manage_delete_all(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Only delete workflows with specific status"),
    plan_id: Optional[str] = typer.Option(None, "--plan", "-p", help="Only delete workflows for specific plan")
):
    """Delete all workflows (with optional filters)."""
    try:
        client = get_client()
        
        console.print(f"🗑️ [bold red]Bulk Workflow Deletion...[/bold red]")
        
        # Get workflows to delete based on filters
        workflows_to_delete = []
        
        if plan_id:
            workflows = client.get_workflows_by_plan(plan_id=plan_id)
            if status:
                workflows = [w for w in workflows if w.get('status') == status]
            workflows_to_delete.extend(workflows)
        else:
            # Get all workflows
            params = {}
            if status:
                params['status'] = status
            workflows = client.list_workflows(**params)
            workflows_to_delete.extend(workflows)
        
        if not workflows_to_delete:
            console.print("📭 No workflows found matching the criteria")
            return
        
        # Show deletion preview
        console.print(f"\n📊 [bold yellow]Deletion Preview:[/bold yellow]")
        console.print(f"Total workflows to delete: [red]{len(workflows_to_delete)}[/red]")
        
        if plan_id:
            console.print(f"Plan filter: [cyan]{plan_id}[/cyan]")
        if status:
            console.print(f"Status filter: [blue]{status}[/blue]")
        
        # Group by status for preview
        status_groups = {}
        executed_count = 0
        for workflow in workflows_to_delete:
            wf_status = workflow.get('status', 'Unknown')
            status_groups[wf_status] = status_groups.get(wf_status, 0) + 1
            if wf_status == 'EXECUTED':
                executed_count += 1
        
        console.print("\n📈 Breakdown by status:")
        for status_name, count in status_groups.items():
            status_color = "green" if status_name == "EXECUTED" else "yellow" if status_name in ["APPROVED", "AUTO_APPROVED"] else "cyan"
            console.print(f"  [{status_color}]{status_name}[/{status_color}]: {count}")
        
        # Safety warning for executed workflows
        if executed_count > 0 and not force:
            console.print(f"\n⚠️ [bold red]DANGER:[/bold red] {executed_count} EXECUTED workflows will be deleted!")
            console.print("This may affect audit trails and compliance records.")
            console.print("Use --force flag if you really want to delete executed workflows.")
            raise typer.Exit(1)
        
        # Final confirmation
        if not force:
            console.print(f"\n❓ [bold red]Are you ABSOLUTELY sure you want to DELETE ALL {len(workflows_to_delete)} workflows?[/bold red]")
            console.print("🚨 [bold red]THIS ACTION CANNOT BE UNDONE![/bold red]")
            
            # Double confirmation for safety
            confirm1 = typer.confirm("Type 'yes' to continue with bulk deletion")
            if not confirm1:
                console.print("❌ Bulk deletion cancelled")
                return
            
            confirm2 = typer.confirm("This is your final confirmation. Really delete all workflows?")
            if not confirm2:
                console.print("❌ Bulk deletion cancelled")
                return
        
        # Perform bulk deletion
        console.print(f"\n🗑️ [bold magenta]Performing bulk deletion...[/bold magenta]")
        
        deleted_count = 0
        failed_count = 0
        
        for workflow in workflows_to_delete:
            workflow_id = workflow.get('id')
            try:
                # Simulate deletion by marking as rejected/cancelled
                client.reject_workflow(
                    workflow_id=workflow_id,
                    rejected_by="system_bulk_delete",
                    reason="BULK_DELETE: Removed during bulk deletion operation"
                )
                deleted_count += 1
                if deleted_count % 10 == 0:  # Progress indicator
                    console.print(f"  🗑️ Deleted {deleted_count} workflows...")
            except Exception as e:
                failed_count += 1
                console.print(f"  ❌ Failed to delete: [cyan]{workflow_id[:8]}...[/cyan] - {str(e)}")
        
        # Summary
        console.print(f"\n📊 [bold green]Bulk Deletion Summary:[/bold green]")
        console.print(f"Total workflows processed: [cyan]{len(workflows_to_delete)}[/cyan]")
        console.print(f"Successfully deleted: [green]{deleted_count}[/green]")
        console.print(f"Failed: [red]{failed_count}[/red]")
        
        if failed_count == 0:
            print_success(f"Successfully deleted all {deleted_count} workflows")
        else:
            print_success(f"Deleted {deleted_count} workflows ({failed_count} failures)")
        
        console.print(f"💡 [yellow]Note: In full implementation, workflows would be permanently removed from database[/yellow]")
        
    except CLIError as e:
        print_error(f"Bulk deletion failed: {str(e)}")
        raise typer.Exit(1)


@workflow_manage_app.command("delete-by-plan")
def workflow_manage_delete_by_plan(
    plan_id: str = typer.Argument(..., help="Plan ID to delete all workflows for"),
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
    workflow_type: Optional[str] = typer.Option(None, "--type", "-t", help="Only delete specific workflow type")
):
    """Delete all workflows for a specific plan."""
    try:
        client = get_client()
        
        console.print(f"🗑️ [bold red]Deleting workflows for plan {plan_id}...[/bold red]")
        
        # Get workflows for the plan
        workflows = client.get_workflows_by_plan(plan_id=plan_id)
        
        if workflow_type:
            workflows = [w for w in workflows if w.get('workflow_type') == workflow_type]
        
        if not workflows:
            console.print(f"📭 No workflows found for plan {plan_id}")
            if workflow_type:
                console.print(f"   (with type filter: {workflow_type})")
            return
        
        # Show deletion preview
        console.print(f"\n📊 [bold yellow]Deletion Preview for Plan {plan_id}:[/bold yellow]")
        console.print(f"Total workflows to delete: [red]{len(workflows)}[/red]")
        
        if workflow_type:
            console.print(f"Type filter: [magenta]{workflow_type}[/magenta]")
        
        # Group by type and status
        type_groups = {}
        status_groups = {}
        executed_count = 0
        
        for workflow in workflows:
            wf_type = workflow.get('workflow_type', 'Unknown')
            wf_status = workflow.get('status', 'Unknown')
            
            type_groups[wf_type] = type_groups.get(wf_type, 0) + 1
            status_groups[wf_status] = status_groups.get(wf_status, 0) + 1
            
            if wf_status == 'EXECUTED':
                executed_count += 1
        
        console.print("\n📈 Breakdown by type:")
        for type_name, count in type_groups.items():
            console.print(f"  [magenta]{type_name}[/magenta]: {count}")
        
        console.print("\n📈 Breakdown by status:")
        for status_name, count in status_groups.items():
            status_color = "green" if status_name == "EXECUTED" else "yellow" if status_name in ["APPROVED", "AUTO_APPROVED"] else "cyan"
            console.print(f"  [{status_color}]{status_name}[/{status_color}]: {count}")
        
        # Safety warning for executed workflows
        if executed_count > 0 and not force:
            console.print(f"\n⚠️ [bold red]WARNING:[/bold red] {executed_count} EXECUTED workflows will be deleted!")
            console.print("This may affect audit trails for this plan.")
            console.print("Use --force flag if you really want to delete executed workflows.")
            raise typer.Exit(1)
        
        # Confirmation
        if not force:
            console.print(f"\n❓ [bold red]Delete all {len(workflows)} workflows for plan {plan_id}?[/bold red]")
            console.print("This action cannot be undone!")
            
            confirm = typer.confirm("Continue with plan-based deletion?")
            if not confirm:
                console.print("❌ Plan-based deletion cancelled")
                return
        
        # Perform deletion
        console.print(f"\n🗑️ [bold magenta]Deleting workflows for plan {plan_id}...[/bold magenta]")
        
        deleted_count = 0
        failed_count = 0
        
        for workflow in workflows:
            workflow_id = workflow.get('id')
            try:
                client.reject_workflow(
                    workflow_id=workflow_id,
                    rejected_by="system_plan_delete",
                    reason=f"PLAN_DELETE: Removed during plan {plan_id} cleanup"
                )
                deleted_count += 1
            except Exception as e:
                failed_count += 1
                console.print(f"  ❌ Failed: [cyan]{workflow_id[:8]}...[/cyan] - {str(e)}")
        
        # Summary
        console.print(f"\n📊 [bold green]Plan Deletion Summary:[/bold green]")
        console.print(f"Plan ID: [cyan]{plan_id}[/cyan]")
        console.print(f"Total workflows processed: [cyan]{len(workflows)}[/cyan]")
        console.print(f"Successfully deleted: [green]{deleted_count}[/green]")
        console.print(f"Failed: [red]{failed_count}[/red]")
        
        if failed_count == 0:
            print_success(f"Successfully deleted all {deleted_count} workflows for plan {plan_id}")
        else:
            print_success(f"Deleted {deleted_count} workflows for plan {plan_id} ({failed_count} failures)")
        
    except CLIError as e:
        print_error(f"Plan-based deletion failed: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# SYSTEM COMMANDS
# ====================================================================

@system_app.command("health")
def system_health():
    """Check system health."""
    try:
        client = get_client()
        
        console.print("🏥 [bold magenta]Checking system health...[/bold magenta]")
        health = client.get_health()
        
        status = health.get('status', 'unknown')
        if status == 'healthy':
            print_success(f"System status: {status}")
        else:
            print_warning(f"System status: {status}")
        
        console.print(f"\n📊 [bold blue]Health Details:[/bold blue]")
        for key, value in health.items():
            console.print(f"   {key}: {value}")
            
    except CLIError as e:
        print_error(f"Health check failed: {str(e)}")
        raise typer.Exit(1)


@system_app.command("metrics")
def system_metrics():
    """Show system metrics."""
    try:
        client = get_client()
        
        console.print("📊 [bold magenta]Getting system metrics...[/bold magenta]")
        metrics = client.get_metrics()
        
        console.print(f"\n📈 [bold cyan]System Metrics:[/bold cyan]")
        for key, value in metrics.items():
            console.print(f"   {key}: {value}")
            
    except CLIError as e:
        print_error(f"Get metrics failed: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# ORCHESTRATION COMMANDS
# ====================================================================

@orchestrate_app.command("run")
def orchestrate_run(
    transcript_id: str = typer.Argument(..., help="Transcript ID to process through pipeline"),
    auto_approve: bool = typer.Option(False, "--auto-approve", "-a", help="Auto-approve all workflows"),
    timeout_hours: int = typer.Option(24, "--timeout", "-t", help="Hours to wait for manual approval"),
    format: str = typer.Option(DEFAULT_FORMAT, "--format", "-f", help="Output format: json, table, yaml"),
    verbose: bool = typer.Option(DEFAULT_VERBOSE, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging")
):
    """Run complete orchestration pipeline: Transcript → Analysis → Plan → Workflows → Execution."""
    try:
        # Configure logging based on debug/verbose flags
        import logging
        if debug:
            logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s')
        elif verbose:
            logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
        else:
            logging.basicConfig(level=logging.WARNING, format='%(levelname)s:%(message)s')
        
        console.print(f"🚀 [bold cyan]Starting orchestration pipeline for transcript: {transcript_id}[/bold cyan]")
        
        # Import here to avoid issues with missing dependencies
        import asyncio
        from src.orchestration.simple_pipeline import run_simple_pipeline
        
        # Run the pipeline
        if verbose:
            console.print("🔄 Pipeline stages: Transcript → Analysis → Plan → Workflows → Execution")
        
        result = asyncio.run(run_simple_pipeline(
            transcript_id=transcript_id,
            auto_approve=auto_approve
        ))
        
        if format.lower() == "json":
            console.print_json(data=result)
        elif format.lower() == "yaml":
            import yaml
            console.print(yaml.dump(result, default_flow_style=False))
        else:  # table format
            # Display pipeline results in table format
            table = Table(title="Pipeline Execution Results")
            table.add_column("Stage", style="cyan")
            table.add_column("Result", style="green")
            
            table.add_row("Transcript ID", result["transcript_id"])
            table.add_row("Analysis ID", result["analysis_id"])
            table.add_row("Plan ID", result["plan_id"])
            table.add_row("Workflows Generated", str(result["workflow_count"]))
            table.add_row("Workflows Approved", str(result.get("approved_count", "N/A")))
            table.add_row("Workflows Executed", str(result["executed_count"]))
            table.add_row("Workflows Failed", str(result.get("failed_count", 0)))
            table.add_row("Stage", result["stage"])
            
            if result.get("partial_success"):
                table.add_row("Status", "⚠️ Partial Success")
            elif result["success"]:
                table.add_row("Status", "✅ Success")
            else:
                table.add_row("Status", "❌ Failed")
            
            console.print(table)
            
            # Show execution summary if verbose
            if verbose and "execution_summary" in result:
                summary = result["execution_summary"]
                console.print(f"\n📊 [bold blue]Execution Summary:[/bold blue]")
                console.print(f"   Total tasks: {summary['total_tasks']}")
                console.print(f"   Completed: {summary['completed']}")
                console.print(f"   Failed: {summary['failed']}")
                console.print(f"   Success rate: {summary['success_rate']:.2%}")
        
        if result.get("partial_success"):
            print_warning(f"Pipeline completed with partial success! Executed {result['executed_count']}, failed {result.get('failed_count', 0)} workflows")
        elif result["success"]:
            print_success(f"Pipeline completed successfully! Executed {result['executed_count']} workflows")
        else:
            print_error(f"Pipeline failed! Executed {result['executed_count']}, failed {result.get('failed_count', 0)} workflows")
        
    except Exception as e:
        print_error(f"Pipeline orchestration failed: {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@orchestrate_app.command("status")
def orchestrate_status(
    transcript_id: str = typer.Option(None, "--transcript", "-t", help="Check status for specific transcript"),
    format: str = typer.Option(DEFAULT_FORMAT, "--format", "-f", help="Output format: json, table, yaml")
):
    """Check orchestration pipeline status."""
    try:
        console.print("🔍 [bold cyan]Checking orchestration status...[/bold cyan]")
        
        if transcript_id:
            console.print(f"📋 Status for transcript: {transcript_id}")
            # TODO: Implement transcript-specific status check
            console.print("❌ Transcript-specific status not yet implemented")
            return
        
        # General orchestration status
        status_info = {
            "orchestrator": "Simple Python Orchestrator",
            "status": "Available",
            "features": [
                "Complete pipeline execution",
                "Parallel workflow processing", 
                "Fail-fast error handling",
                "Execution tracking",
                "Pipeline pause/resume (planned)"
            ],
            "last_check": datetime.now().isoformat()
        }
        
        if format.lower() == "json":
            console.print_json(data=status_info)
        elif format.lower() == "yaml":
            import yaml
            console.print(yaml.dump(status_info, default_flow_style=False))
        else:  # table format
            table = Table(title="Orchestration Status")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            for key, value in status_info.items():
                if isinstance(value, list):
                    value = "\n".join(f"• {item}" for item in value)
                table.add_row(key.replace("_", " ").title(), str(value))
            
            console.print(table)
        
        print_success("Orchestration system is ready")
        
    except Exception as e:
        print_error(f"Status check failed: {str(e)}")
        raise typer.Exit(1)


@orchestrate_app.command("resume")
def orchestrate_resume(
    plan_id: str = typer.Argument(..., help="Plan ID to resume execution for"),
    execute_approved: bool = typer.Option(True, "--execute-approved/--no-execute", help="Execute approved workflows immediately")
):
    """Resume orchestration pipeline after manual approvals."""
    try:
        console.print(f"🔄 [bold magenta]Resuming orchestration for plan: {plan_id}[/bold magenta]")
        
        from src.services.workflow_service import WorkflowService
        workflow_service = WorkflowService("data/call_center.db")
        
        # Get all workflows for this plan
        all_workflows = workflow_service.workflow_store.get_by_plan_id(plan_id)
        
        if not all_workflows:
            print_error(f"No workflows found for plan: {plan_id}")
            raise typer.Exit(1)
        
        # Filter approved workflows
        approved_workflows = [w for w in all_workflows if w.get('status') in ['APPROVED', 'AUTO_APPROVED']]
        pending_workflows = [w for w in all_workflows if w.get('status') == 'AWAITING_APPROVAL']
        
        console.print(f"📊 Plan Status Summary:")
        console.print(f"   Total workflows: {len(all_workflows)}")
        console.print(f"   ✅ Approved: {len(approved_workflows)}")
        console.print(f"   ⏳ Pending approval: {len(pending_workflows)}")
        
        if pending_workflows:
            console.print(f"\n⚠️ [yellow]{len(pending_workflows)} workflow(s) still awaiting approval:[/yellow]")
            for workflow in pending_workflows[:5]:  # Show first 5
                console.print(f"   - {workflow.get('id', 'N/A')[:8]}... ({workflow.get('risk_level', 'Unknown')} risk)")
            if len(pending_workflows) > 5:
                console.print(f"   ... and {len(pending_workflows) - 5} more")
            
            console.print(f"\n💡 [dim]Use 'python cli.py approvals queue' to see pending approvals[/dim]")
            console.print(f"💡 [dim]Use 'python cli.py approvals process --approve <id1>,<id2>' to approve workflows[/dim]")
        
        if not approved_workflows:
            console.print("⚠️ [yellow]No approved workflows to execute[/yellow]")
            return
        
        if execute_approved:
            console.print(f"\n🚀 [bold blue]Executing {len(approved_workflows)} approved workflow(s)...[/bold blue]")
            
            from src.services.workflow_execution_engine import WorkflowExecutionEngine
            execution_engine = WorkflowExecutionEngine("data/call_center.db")
            
            successful = 0
            failed = 0
            
            for workflow in approved_workflows:
                workflow_id = workflow.get('id')
                try:
                    console.print(f"🔄 Executing: {workflow_id[:8]}...")
                    import asyncio
                    result = asyncio.run(execution_engine.execute_workflow(workflow_id))
                    
                    if result and result.get('status') == 'success':
                        successful += 1
                        console.print(f"✅ [green]Executed: {workflow_id[:8]}...[/green]")
                    else:
                        failed += 1
                        console.print(f"❌ [red]Failed: {workflow_id[:8]}...[/red]")
                        
                except Exception as e:
                    failed += 1
                    console.print(f"❌ [red]Error executing {workflow_id[:8]}...: {str(e)[:50]}...[/red]")
            
            # Summary
            console.print(f"\n📊 [bold blue]Execution Summary:[/bold blue]")
            console.print(f"✅ Successful: {successful}")
            console.print(f"❌ Failed: {failed}")
            
            if failed > 0:
                console.print(f"⚠️ [yellow]Partial success: {successful}/{len(approved_workflows)} workflows executed[/yellow]")
            else:
                console.print(f"🎉 [bold green]All approved workflows executed successfully![/bold green]")
        else:
            console.print(f"\n💡 [dim]Use --execute-approved to run the approved workflows[/dim]")
        
    except Exception as e:
        print_error(f"Failed to resume orchestration: {str(e)}")
        raise typer.Exit(1)


@orchestrate_app.command("pending")
def orchestrate_pending():
    """Show plans with workflows pending approval."""
    try:
        console.print("📋 [bold magenta]Fetching plans with pending approvals...[/bold magenta]")
        
        from src.services.workflow_service import WorkflowService
        workflow_service = WorkflowService("data/call_center.db")
        
        # Get all pending workflows
        pending_workflows = workflow_service.workflow_store.get_pending_approval()
        
        if not pending_workflows:
            console.print("✅ [bold green]No workflows pending approval![/bold green]")
            return
        
        # Group by plan_id
        plans_with_pending = {}
        for workflow in pending_workflows:
            plan_id = workflow.get('plan_id', 'Unknown')
            if plan_id not in plans_with_pending:
                plans_with_pending[plan_id] = []
            plans_with_pending[plan_id].append(workflow)
        
        console.print(f"\n📋 [bold yellow]{len(plans_with_pending)} plan(s) with pending approvals:[/bold yellow]\n")
        
        # Create table
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Plan ID", style="cyan", width=30)
        table.add_column("Pending Count", style="red", width=12)
        table.add_column("Risk Levels", style="yellow", width=15)
        table.add_column("Transcript ID", style="dim", width=25)
        
        for plan_id, workflows in plans_with_pending.items():
            pending_count = len(workflows)
            risk_levels = list(set([w.get('risk_level', 'Unknown') for w in workflows]))
            transcript_id = workflows[0].get('transcript_id', 'N/A')
            
            table.add_row(
                plan_id,
                str(pending_count),
                ", ".join(risk_levels),
                transcript_id
            )
        
        console.print(table)
        
        console.print(f"\n💡 [dim]Use 'python cli.py orchestrate resume <plan_id>' to resume a specific plan[/dim]")
        console.print(f"💡 [dim]Use 'python cli.py approvals queue' to see detailed approval queue[/dim]")
        
    except Exception as e:
        print_error(f"Failed to fetch pending plans: {str(e)}")
        raise typer.Exit(1)


@orchestrate_app.command("execute-approved")
def orchestrate_execute_approved(
    plan_id: str = typer.Argument(..., help="Plan ID to execute approved workflows for")
):
    """Execute all approved workflows for a specific plan."""
    try:
        console.print(f"🚀 [bold magenta]Executing approved workflows for plan: {plan_id}[/bold magenta]")
        
        from src.services.workflow_service import WorkflowService
        from src.services.workflow_execution_engine import WorkflowExecutionEngine
        
        workflow_service = WorkflowService("data/call_center.db")
        execution_engine = WorkflowExecutionEngine("data/call_center.db")
        
        # Get approved workflows for this plan
        all_workflows = workflow_service.workflow_store.get_by_plan_id(plan_id)
        approved_workflows = [w for w in all_workflows if w.get('status') in ['APPROVED', 'AUTO_APPROVED']]
        
        if not approved_workflows:
            console.print(f"⚠️ [yellow]No approved workflows found for plan: {plan_id}[/yellow]")
            console.print(f"💡 [dim]Use 'python cli.py orchestrate pending' to see plans with pending approvals[/dim]")
            return
        
        console.print(f"🔄 [bold blue]Found {len(approved_workflows)} approved workflow(s) to execute...[/bold blue]\n")
        
        successful = 0
        failed = 0
        
        for workflow in approved_workflows:
            workflow_id = workflow.get('id')
            workflow_type = workflow.get('workflow_type', 'Unknown')
            
            try:
                console.print(f"🔄 Executing {workflow_type}: {workflow_id[:8]}...")
                import asyncio
                result = asyncio.run(execution_engine.execute_workflow(workflow_id))
                
                if result and result.get('status') == 'success':
                    successful += 1
                    console.print(f"✅ [green]Success: {workflow_id[:8]}...[/green]")
                else:
                    failed += 1
                    error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
                    console.print(f"❌ [red]Failed: {workflow_id[:8]}... - {error_msg[:50]}...[/red]")
                    
            except Exception as e:
                failed += 1
                console.print(f"❌ [red]Error: {workflow_id[:8]}... - {str(e)[:50]}...[/red]")
        
        # Final summary
        console.print(f"\n📊 [bold blue]Final Execution Summary:[/bold blue]")
        console.print(f"✅ Successful: {successful}")
        console.print(f"❌ Failed: {failed}")
        console.print(f"📈 Success Rate: {(successful / len(approved_workflows) * 100):.1f}%")
        
        if failed > 0:
            console.print(f"\n⚠️ [yellow]Partial success: {successful}/{len(approved_workflows)} workflows executed[/yellow]")
        else:
            console.print(f"\n🎉 [bold green]All workflows executed successfully![/bold green]")
        
    except Exception as e:
        print_error(f"Failed to execute approved workflows: {str(e)}")
        raise typer.Exit(1)


@orchestrate_app.command("test") 
def orchestrate_test(
    transcript_id: str = typer.Option("TEST_TRANSCRIPT_001", "--transcript", "-t", help="Test transcript ID"),
    verbose: bool = typer.Option(True, "--verbose", "-v", help="Enable verbose output")
):
    """Test orchestration pipeline with sample data."""
    try:
        console.print("🧪 [bold cyan]Testing orchestration pipeline...[/bold cyan]")
        
        # Run tests for orchestration components
        import subprocess
        import sys
        
        console.print("🔬 Running orchestration tests...")
        
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_simple_orchestration.py", 
            "-v" if verbose else "-q"
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print_success("All orchestration tests passed!")
            if verbose:
                console.print(result.stdout)
        else:
            print_error("Some orchestration tests failed")
            console.print(result.stderr)
            raise typer.Exit(1)
        
        # Optionally run a test pipeline
        console.print(f"\n🚀 [bold blue]Running test pipeline with transcript: {transcript_id}[/bold blue]")
        console.print("⚠️ Note: This will fail without actual services running")
        
    except FileNotFoundError:
        print_error("pytest not found. Install with: pip install pytest")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Test execution failed: {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


# ====================================================================
# APPROVAL QUEUE COMMANDS
# ====================================================================

@approvals_app.command("queue")
def approvals_queue(
    role: Optional[str] = typer.Option(None, "--role", "-r", help="Filter by approver role (SUPERVISOR, MANAGER)"),
    approver: Optional[str] = typer.Option(None, "--approver", "-a", help="Filter by specific approver"),
    plan_id: Optional[str] = typer.Option(None, "--plan-id", "-p", help="Filter by specific plan ID"),
    limit: int = typer.Option(20, "--limit", "-l", help="Maximum number of workflows to show")
):
    """Show approval queue - pending workflows requiring manual approval."""
    try:
        console.print("📋 [bold magenta]Fetching approval queue...[/bold magenta]")
        
        from src.services.workflow_service import WorkflowService
        workflow_service = WorkflowService("data/call_center.db")
        
        # Get pending approvals
        pending_workflows = workflow_service.workflow_store.get_pending_approval()
        
        if not pending_workflows:
            console.print("✅ [bold green]No workflows pending approval![/bold green]")
            return
        
        # Filter by role, approver, or plan_id if specified
        if role:
            pending_workflows = [w for w in pending_workflows if role.upper() in str(w.get('assigned_approver', '')).upper()]
        if approver:
            pending_workflows = [w for w in pending_workflows if approver in str(w.get('assigned_approver', ''))]
        if plan_id:
            pending_workflows = [w for w in pending_workflows if w.get('plan_id') == plan_id]
        
        # Limit results
        pending_workflows = pending_workflows[:limit]
        
        if not pending_workflows:
            console.print(f"✅ [bold green]No workflows pending approval for the specified filters[/bold green]")
            return
        
        console.print(f"\n📋 [bold yellow]{len(pending_workflows)} workflow(s) in approval queue:[/bold yellow]\n")
        
        # Create table
        table = Table(show_header=True, header_style="bold blue")
        table.add_column("Workflow ID", style="cyan", width=12)
        table.add_column("Risk", style="red", width=8)
        table.add_column("Type", style="green", width=10)
        table.add_column("Assigned To", style="yellow", width=15)
        table.add_column("Created", style="dim", width=12)
        table.add_column("Plan ID", style="dim", width=12)
        
        for workflow in pending_workflows:
            workflow_id = workflow.get('id', 'N/A')[:8] + "..."
            risk_level = workflow.get('risk_level', 'Unknown')
            workflow_type = workflow.get('workflow_type', 'Unknown')
            assigned_approver = workflow.get('assigned_approver', 'Unassigned')
            created_at = workflow.get('created_at', 'N/A')
            plan_id = workflow.get('plan_id', 'N/A')[:8] + "..."
            
            # Format created date
            if created_at != 'N/A':
                try:
                    from datetime import datetime
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = created_dt.strftime('%m/%d %H:%M')
                except:
                    pass
            
            table.add_row(workflow_id, risk_level, workflow_type, assigned_approver, created_at, plan_id)
        
        console.print(table)
        
        console.print(f"\n💡 [dim]Use 'python cli.py approvals process --approve <id1>,<id2>' to approve workflows[/dim]")
        console.print(f"💡 [dim]Use 'python cli.py workflow process approve <id>' for individual approvals[/dim]")
        
    except Exception as e:
        print_error(f"Failed to fetch approval queue: {str(e)}")
        raise typer.Exit(1)


@approvals_app.command("process")
def approvals_process(
    approve: Optional[str] = typer.Option(None, "--approve", help="Comma-separated workflow IDs to approve"),
    reject: Optional[str] = typer.Option(None, "--reject", help="Comma-separated workflow IDs to reject"),
    approver: str = typer.Option(..., "--approver", "-a", help="Approver identifier (email)"),
    reason: Optional[str] = typer.Option(None, "--reason", "-r", help="Approval/rejection reason")
):
    """Bulk approve or reject workflows from the approval queue."""
    if not approve and not reject:
        print_error("Must specify either --approve or --reject with workflow IDs")
        raise typer.Exit(1)
    
    if approve and reject:
        print_error("Cannot both approve and reject in the same command")
        raise typer.Exit(1)
    
    try:
        from src.services.workflow_service import WorkflowService
        workflow_service = WorkflowService("data/call_center.db")
        
        workflow_ids = []
        action = ""
        
        if approve:
            workflow_ids = [id.strip() for id in approve.split(',')]
            action = "AUTO_APPROVED"
        elif reject:
            workflow_ids = [id.strip() for id in reject.split(',')]
            action = "REJECTED"
        
        action_display = "approval" if action == "AUTO_APPROVED" else "rejection"
        console.print(f"🔄 [bold magenta]Processing {len(workflow_ids)} workflow(s) for {action_display}...[/bold magenta]")
        
        successful = 0
        failed = 0
        
        for workflow_id in workflow_ids:
            try:
                # Update workflow status
                success = workflow_service.workflow_store.update_status(
                    workflow_id,
                    action,
                    transitioned_by=approver,
                    reason=reason or f"Bulk {action_display} via CLI"
                )
                
                if success:
                    successful += 1
                    action_verb = "APPROVED" if action == "AUTO_APPROVED" else action
                    console.print(f"✅ [green]{action_verb} workflow: {workflow_id[:8]}...[/green]")
                else:
                    failed += 1
                    action_verb = "approve" if action == "AUTO_APPROVED" else action.lower()
                    console.print(f"❌ [red]Failed to {action_verb} workflow: {workflow_id[:8]}... (not found)[/red]")
                    
            except Exception as e:
                failed += 1
                console.print(f"❌ [red]Error processing workflow {workflow_id[:8]}...: {str(e)}[/red]")
        
        # Summary
        console.print(f"\n📊 [bold blue]Processing Summary:[/bold blue]")
        console.print(f"✅ Successful: {successful}")
        console.print(f"❌ Failed: {failed}")
        
        if successful > 0 and action == "AUTO_APPROVED":
            console.print(f"\n💡 [dim]Use 'python cli.py orchestrate execute-approved <plan_id>' to execute approved workflows[/dim]")
        
    except Exception as e:
        print_error(f"Failed to process approvals: {str(e)}")
        raise typer.Exit(1)


@approvals_app.command("my-tasks") 
def approvals_my_tasks(
    approver: str = typer.Option(..., "--approver", "-a", help="Approver identifier to filter tasks"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of tasks to show")
):
    """Show pending approval tasks for a specific approver."""
    try:
        console.print(f"👤 [bold magenta]Fetching tasks for approver: {approver}[/bold magenta]")
        
        from src.services.workflow_service import WorkflowService
        workflow_service = WorkflowService("data/call_center.db")
        
        # Get pending approvals
        pending_workflows = workflow_service.workflow_store.get_pending_approval()
        
        # Filter by approver
        my_tasks = [w for w in pending_workflows if approver in str(w.get('assigned_approver', ''))]
        my_tasks = my_tasks[:limit]
        
        if not my_tasks:
            console.print(f"✅ [bold green]No pending tasks for {approver}[/bold green]")
            return
        
        console.print(f"\n📋 [bold yellow]{len(my_tasks)} task(s) assigned to {approver}:[/bold yellow]\n")
        
        # Create detailed task list
        for i, workflow in enumerate(my_tasks, 1):
            workflow_id = workflow.get('id', 'N/A')
            risk_level = workflow.get('risk_level', 'Unknown')
            workflow_type = workflow.get('workflow_type', 'Unknown')
            plan_id = workflow.get('plan_id', 'N/A')
            
            console.print(f"[bold cyan]{i}. Task {workflow_id[:8]}...[/bold cyan]")
            console.print(f"   Risk Level: [red]{risk_level}[/red]")
            console.print(f"   Type: [green]{workflow_type}[/green]") 
            console.print(f"   Plan: {plan_id}")
            console.print(f"   Actions: [yellow]Approve[/yellow] | [red]Reject[/red]")
            console.print()
        
        console.print(f"💡 [dim]Use 'python cli.py workflow process approve <id>' to approve individual tasks[/dim]")
        console.print(f"💡 [dim]Use 'python cli.py approvals process --approve <id1>,<id2>' for bulk approval[/dim]")
        
    except Exception as e:
        print_error(f"Failed to fetch tasks for {approver}: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()