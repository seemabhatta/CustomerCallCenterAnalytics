#!/usr/bin/env python3
"""
Customer Call Center Analytics CLI - Streamlined Core Commands
Direct REST API client following industry best practices
No fallback logic - fail fast with clear error messages
Resource-aligned commands: transcript, analysis, plan, workflow, execution, system
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize OpenTelemetry tracing IMMEDIATELY after env loading for complete observability coverage
try:
    from src.infrastructure.telemetry import initialize_tracing
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
    import asyncio
    sys.path.insert(0, '.')
    from src.agents.transcript_agent import TranscriptAgent
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
    help="Customer Call Center Analytics - Streamlined REST API Client",
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

    def list_transcripts(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """List transcripts via GET /api/v1/transcripts."""
        params = {}
        if limit is not None:
            params['limit'] = limit
        return self._make_request('GET', '/api/v1/transcripts', params=params)

    def get_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """Get transcript by ID via GET /api/v1/transcripts/{id}."""
        return self._make_request('GET', f'/api/v1/transcripts/{transcript_id}')

    def delete_transcript(self, transcript_id: str) -> Dict[str, Any]:
        """Delete transcript via DELETE /api/v1/transcripts/{id}."""
        return self._make_request('DELETE', f'/api/v1/transcripts/{transcript_id}')

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

    # Insights operations (core subset)
    def discover_risk_patterns(self, risk_threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Discover risk patterns via GET /api/v1/insights/patterns."""
        params = {'risk_threshold': risk_threshold}
        return self._make_request('GET', '/api/v1/insights/patterns', params=params)

    def get_insights_dashboard(self) -> Dict[str, Any]:
        """Get insights dashboard via GET /api/v1/insights/dashboard."""
        return self._make_request('GET', '/api/v1/insights/dashboard')

    def populate_insights(self, **kwargs) -> Dict[str, Any]:
        """Populate insights graph via POST /api/v1/insights/populate."""
        return self._make_request('POST', '/api/v1/insights/populate', json_data=kwargs)

    def get_insights_status(self) -> Dict[str, Any]:
        """Get insights status via GET /api/v1/insights/status."""
        return self._make_request('GET', '/api/v1/insights/status')

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

    def delete_plan(self, plan_id: str) -> Dict[str, Any]:
        """Delete plan via DELETE /api/v1/plans/{id}."""
        return self._make_request('DELETE', f'/api/v1/plans/{plan_id}')

    def delete_all_plans(self) -> Dict[str, Any]:
        """Delete all plans via DELETE /api/v1/plans."""
        return self._make_request('DELETE', '/api/v1/plans')

    # Workflow operations
    def extract_all_workflows(self, plan_id: str) -> Dict[str, Any]:
        """Extract all workflows from plan via POST /api/v1/workflows/extract-all."""
        return self._make_request('POST', '/api/v1/workflows/extract-all', json_data={'plan_id': plan_id}, timeout=300)

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

    def execute_workflow(self, workflow_id: str, executed_by: str) -> Dict[str, Any]:
        """Execute workflow via POST /api/v1/workflows/{workflow_id}/execute."""
        json_data = {'executed_by': executed_by}
        return self._make_request('POST', f'/api/v1/workflows/{workflow_id}/execute', json_data=json_data)

    def delete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Delete workflow by ID via DELETE /api/v1/workflows/{workflow_id}."""
        return self._make_request('DELETE', f'/api/v1/workflows/{workflow_id}')

    def delete_all_workflows(self) -> Dict[str, Any]:
        """Delete all workflows via DELETE /api/v1/workflows."""
        return self._make_request('DELETE', '/api/v1/workflows')

    def execute_all_workflows(self, executed_by: str = "cli_user") -> Dict[str, Any]:
        """Execute all approved workflows via POST /api/v1/workflows/execute-all."""
        json_data = {'executed_by': executed_by}
        return self._make_request('POST', '/api/v1/workflows/execute-all', json_data=json_data, timeout=600)

    # Execution operations
    def list_executions(self, workflow_id: Optional[str] = None, limit: Optional[int] = None,
                       status: Optional[str] = None, executor_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all executions via GET /api/v1/executions."""
        params = {}
        if workflow_id:
            params['workflow_id'] = workflow_id
        if limit is not None:
            params['limit'] = limit
        if status:
            params['status'] = status
        if executor_type:
            params['executor_type'] = executor_type
        return self._make_request('GET', '/api/v1/executions', params=params)

    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get execution details via GET /api/v1/executions/{execution_id}."""
        return self._make_request('GET', f'/api/v1/executions/{execution_id}')

    def delete_execution(self, execution_id: str) -> Dict[str, Any]:
        """Delete execution via DELETE /api/v1/executions/{execution_id}."""
        return self._make_request('DELETE', f'/api/v1/executions/{execution_id}')

    def delete_all_executions(self, status: Optional[str] = None,
                             executor_type: Optional[str] = None) -> Dict[str, Any]:
        """Delete all executions via DELETE /api/v1/executions."""
        params = {}
        if status:
            params['status'] = status
        if executor_type:
            params['executor_type'] = executor_type
        return self._make_request('DELETE', '/api/v1/executions', params=params)

    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get execution statistics via GET /api/v1/executions/statistics."""
        return self._make_request('GET', '/api/v1/executions/statistics')

    # System operations
    def get_health(self) -> Dict[str, Any]:
        """Get system health via GET /api/v1/health."""
        return self._make_request('GET', '/api/v1/health')

    def get_metrics(self) -> Dict[str, Any]:
        """Get system metrics via GET /api/v1/metrics."""
        return self._make_request('GET', '/api/v1/metrics')

    # Orchestration operations
    def orchestrate_run(self, transcript_ids: List[str], auto_approve: bool = False) -> Dict[str, Any]:
        """Start orchestration pipeline via POST /api/v1/orchestrate/run."""
        json_data = {
            'transcript_ids': transcript_ids,
            'auto_approve': auto_approve
        }
        return self._make_request('POST', '/api/v1/orchestrate/run', json_data=json_data, timeout=10)

    def get_orchestration_status(self, run_id: str) -> Dict[str, Any]:
        """Get orchestration run status via GET /api/v1/orchestrate/status/{run_id}."""
        return self._make_request('GET', f'/api/v1/orchestrate/status/{run_id}')

    def list_orchestration_runs(self, limit: Optional[int] = None, status: Optional[str] = None) -> Dict[str, Any]:
        """List orchestration runs via GET /api/v1/orchestrate/runs."""
        params = {}
        if limit:
            params['limit'] = limit
        if status:
            params['status'] = status
        return self._make_request('GET', '/api/v1/orchestrate/runs', params=params)

    # ===============================================
    # LEADERSHIP METHODS
    # ===============================================

    def leadership_chat(self, query: str, executive_id: str, executive_role: str = "Manager",
                       session_id: Optional[str] = None) -> Dict[str, Any]:
        """Chat with Leadership Insights Agent."""
        payload = {
            "query": query,
            "executive_id": executive_id,
            "executive_role": executive_role
        }
        if session_id:
            payload["session_id"] = session_id
        return self._make_request('POST', '/api/v1/leadership/chat', json_data=payload, timeout=120)

    def leadership_sessions(self, executive_id: str, limit: int = 10) -> Dict[str, Any]:
        """List sessions for an executive."""
        params = {"executive_id": executive_id, "limit": limit}
        return self._make_request('GET', '/api/v1/leadership/sessions', params=params)

    def leadership_session_history(self, session_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get conversation history for a session."""
        params = {"limit": limit}
        return self._make_request('GET', f'/api/v1/leadership/sessions/{session_id}/history', params=params)

    def leadership_dashboard(self, executive_role: Optional[str] = None) -> Dict[str, Any]:
        """Get pre-computed insights dashboard."""
        params = {}
        if executive_role:
            params["executive_role"] = executive_role
        return self._make_request('GET', '/api/v1/leadership/dashboard', params=params)

    def leadership_status(self) -> Dict[str, Any]:
        """Get leadership service health and component status."""
        return self._make_request('GET', '/api/v1/leadership/status')


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
    """Customer Call Center Analytics CLI - Streamlined Core Commands."""
    global GLOBAL_API_URL, GLOBAL_FORMAT, GLOBAL_VERBOSE

    if api_url:
        GLOBAL_API_URL = api_url
    if format:
        GLOBAL_FORMAT = format
    if verbose:
        GLOBAL_VERBOSE = verbose


# ====================================================================
# CORE RESOURCE COMMANDS
# ====================================================================

# Create subapps for each resource
transcript_app = typer.Typer(name="transcript", help="Transcript operations")
analysis_app = typer.Typer(name="analysis", help="Analysis operations")
insights_app = typer.Typer(name="insights", help="Core insights operations")
plan_app = typer.Typer(name="plan", help="Plan operations")
workflow_app = typer.Typer(name="workflow", help="Workflow operations")
execution_app = typer.Typer(name="execution", help="Execution operations")
system_app = typer.Typer(name="system", help="System operations")
orchestrate_app = typer.Typer(name="orchestrate", help="Core orchestration operations")
leadership_app = typer.Typer(name="leadership", help="Leadership insights operations")

# Add subapps to main app
app.add_typer(transcript_app)
app.add_typer(analysis_app)
app.add_typer(insights_app)
app.add_typer(plan_app)
app.add_typer(workflow_app)
app.add_typer(execution_app)
app.add_typer(orchestrate_app)
app.add_typer(leadership_app)
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
            generator = TranscriptAgent()
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


@transcript_app.command("show")
def transcript_show(transcript_id: str):
    """Show specific transcript details."""
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
        print_error(f"List failed: {str(e)}")
        raise typer.Exit(1)


@analysis_app.command("show")
def analysis_show(analysis_id: str):
    """Show specific analysis details."""
    try:
        client = get_client()

        console.print(f"📄 [bold magenta]Getting analysis {analysis_id}...[/bold magenta]")
        analysis = client.get_analysis(analysis_id)

        console.print(f"\n📋 [bold green]Analysis Details[/bold green]:")
        console.print(f"Analysis ID: [cyan]{analysis.get('analysis_id', analysis_id)}[/cyan]")
        console.print(f"Transcript ID: [cyan]{analysis.get('transcript_id', 'N/A')}[/cyan]")
        console.print(f"Intent: [yellow]{analysis.get('primary_intent', 'N/A')}[/yellow]")

        # Display sentiment details
        borrower_sentiment = analysis.get('borrower_sentiment', {})
        if borrower_sentiment:
            console.print(f"\n😊 [bold blue]Sentiment:[/bold blue]")
            console.print(f"   Overall: {borrower_sentiment.get('overall', 'N/A')}")
            console.print(f"   Start: {borrower_sentiment.get('start', 'N/A')}")
            console.print(f"   End: {borrower_sentiment.get('end', 'N/A')}")
            console.print(f"   Trend: {borrower_sentiment.get('trend', 'N/A')}")

        # Display risk assessment
        borrower_risks = analysis.get('borrower_risks', {})
        if borrower_risks:
            console.print(f"\n⚠️  [bold red]Risk Assessment:[/bold red]")
            for risk_type, risk_value in borrower_risks.items():
                if isinstance(risk_value, (int, float)):
                    console.print(f"   {risk_type.title()}: {risk_value:.2%}")
                else:
                    console.print(f"   {risk_type.title()}: {risk_value}")

    except CLIError as e:
        print_error(f"Get failed: {str(e)}")
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
            confirm = typer.confirm("Delete ALL analyses? This cannot be undone.", default=False)
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


# ====================================================================
# INSIGHTS COMMANDS (Core subset)
# ====================================================================

@insights_app.command("patterns")
def insights_patterns(
    risk_threshold: float = typer.Option(0.7, "--threshold", "-t", help="Risk threshold (0.0-1.0)")
):
    """Discover high-risk patterns across analyses."""
    try:
        client = get_client()

        console.print(f"🔍 [bold magenta]Discovering risk patterns (threshold: {risk_threshold:.2%})...[/bold magenta]")
        patterns = client.discover_risk_patterns(risk_threshold)

        if not patterns:
            console.print("📭 No risk patterns found above threshold")
            return

        console.print(f"\n📊 Found {len(patterns)} risk pattern(s):")

        for pattern in patterns:
            console.print(f"\n[bold yellow]Pattern:[/bold yellow] {pattern.get('pattern_type', 'Unknown')}")
            console.print(f"[cyan]Risk Score:[/cyan] {pattern.get('risk_score', 0):.2%}")
            console.print(f"[cyan]Frequency:[/cyan] {pattern.get('frequency', 0)}")
            console.print(f"[cyan]Description:[/cyan] {pattern.get('description', 'N/A')}")
            console.print("─" * 40)

    except CLIError as e:
        print_error(f"Patterns discovery failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("dashboard")
def insights_dashboard():
    """Get comprehensive insights dashboard."""
    try:
        client = get_client()

        console.print("📊 [bold magenta]Loading insights dashboard...[/bold magenta]")
        dashboard = client.get_insights_dashboard()

        console.print(f"\n📋 [bold green]Insights Dashboard[/bold green]:")

        # Display summary statistics
        stats = dashboard.get('summary_stats', {})
        if stats:
            console.print(f"\n📈 [bold blue]Summary Statistics:[/bold blue]")
            for key, value in stats.items():
                if isinstance(value, (int, float)):
                    if key.endswith('_rate') or key.endswith('_percentage'):
                        console.print(f"   {key.title()}: {value:.2%}")
                    else:
                        console.print(f"   {key.title()}: {value}")
                else:
                    console.print(f"   {key.title()}: {value}")

        # Display top patterns
        top_patterns = dashboard.get('top_patterns', [])
        if top_patterns:
            console.print(f"\n🔥 [bold red]Top Risk Patterns:[/bold red]")
            for i, pattern in enumerate(top_patterns[:5], 1):
                console.print(f"   {i}. {pattern.get('pattern_type', 'Unknown')} - {pattern.get('risk_score', 0):.2%}")

    except CLIError as e:
        print_error(f"Dashboard failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("populate")
def insights_populate(
    all: bool = typer.Option(False, "--all", help="Populate from all analyses"),
    analysis_id: Optional[str] = typer.Option(None, "--analysis", "-a", help="Populate from specific analysis")
):
    """Populate knowledge graph from analysis data."""
    try:
        client = get_client()

        if analysis_id:
            console.print(f"📥 [bold magenta]Populating insights from analysis {analysis_id}...[/bold magenta]")
            result = client.populate_insights(analysis_id=analysis_id)
        elif all:
            console.print("📥 [bold magenta]Populating insights from all analyses...[/bold magenta]")
            result = client.populate_insights(all=True)
        else:
            print_error("Must specify either --analysis <id> or --all")
            raise typer.Exit(1)

        nodes_created = result.get('nodes_created', 0)
        relationships_created = result.get('relationships_created', 0)

        print_success(f"Populated insights: {nodes_created} nodes, {relationships_created} relationships")

    except CLIError as e:
        print_error(f"Populate failed: {str(e)}")
        raise typer.Exit(1)


@insights_app.command("status")
def insights_status():
    """Get knowledge graph status and statistics."""
    try:
        client = get_client()

        console.print("📊 [bold magenta]Getting insights status...[/bold magenta]")
        status = client.get_insights_status()

        console.print(f"\n📋 [bold green]Knowledge Graph Status[/bold green]:")
        console.print(f"Status: [cyan]{status.get('status', 'Unknown')}[/cyan]")
        console.print(f"Total Nodes: [cyan]{status.get('total_nodes', 0)}[/cyan]")
        console.print(f"Total Relationships: [cyan]{status.get('total_relationships', 0)}[/cyan]")
        console.print(f"Last Updated: [cyan]{status.get('last_updated', 'Never')}[/cyan]")

        # Display node types breakdown
        node_types = status.get('node_types', {})
        if node_types:
            console.print(f"\n📈 [bold blue]Node Types:[/bold blue]")
            for node_type, count in node_types.items():
                console.print(f"   {node_type}: {count}")

    except CLIError as e:
        print_error(f"Status failed: {str(e)}")
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

        console.print(f"📋 [bold magenta]Creating action plan from analysis {analysis}...[/bold magenta]")
        result = client.create_plan(analysis_id=analysis, plan_type='standard', store=True)

        plan_id = result.get('plan_id')
        if not plan_id:
            raise CLIError("Plan ID missing from API response")

        print_success(f"Action plan created: {plan_id}")

        # Display plan details
        console.print(f"\n📄 [bold green]Action Plan Created[/bold green]:")
        console.print(f"Plan ID: [cyan]{plan_id}[/cyan]")
        console.print(f"Analysis ID: [cyan]{result.get('analysis_id', 'N/A')}[/cyan]")

        # Display action items
        action_items = result.get('action_items', [])
        if action_items:
            console.print(f"\n📋 [bold blue]Action Items ({len(action_items)}):[/bold blue]")
            for i, item in enumerate(action_items, 1):
                priority = item.get('priority', 'normal')
                action = item.get('action', 'N/A')
                console.print(f"   {i}. [{priority.upper()}] {action}")

        # Display summary
        summary = result.get('summary')
        if summary:
            console.print(f"\n📝 [bold yellow]Summary:[/bold yellow]")
            console.print(f"   {summary}")

    except CLIError as e:
        print_error(f"Plan creation failed: {str(e)}")
        raise typer.Exit(1)


@plan_app.command("list")
def plan_list(
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results")
):
    """List all action plans."""
    try:
        client = get_client()

        console.print("📋 [bold magenta]Listing action plans...[/bold magenta]")
        plans = client.list_plans(limit=limit)

        if not plans:
            console.print("📭 No action plans found")
            return

        console.print(f"\n📊 Found {len(plans)} plan(s):")

        for plan in plans:
            plan_id = plan.get('plan_id', 'N/A')
            analysis_id = plan.get('analysis_id', 'N/A')
            status = plan.get('status', 'N/A')
            action_count = len(plan.get('action_items', []))

            console.print(f"\n[cyan]Plan ID:[/cyan] {plan_id}")
            console.print(f"[cyan]Analysis ID:[/cyan] {analysis_id}")
            console.print(f"[cyan]Status:[/cyan] {status}")
            console.print(f"[cyan]Action Items:[/cyan] {action_count}")

            summary = plan.get('summary', '')
            if summary:
                console.print(f"[cyan]Summary:[/cyan] {summary[:100]}...")
            console.print("─" * 40)

    except CLIError as e:
        print_error(f"List failed: {str(e)}")
        raise typer.Exit(1)


@plan_app.command("show")
def plan_show(
    plan_id: str,
    stakeholder: Optional[str] = typer.Option(
        None,
        "--stakeholder", "-s",
        help="Filter by stakeholder: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP"
    )
):
    """View specific action plan details."""
    try:
        client = get_client()

        console.print(f"📄 [bold magenta]Getting plan {plan_id}...[/bold magenta]")
        plan = client.get_plan(plan_id)

        console.print(f"\n📋 [bold green]Action Plan Details[/bold green]:")
        console.print(f"Plan ID: [cyan]{plan.get('plan_id', plan_id)}[/cyan]")
        console.print(f"Analysis ID: [cyan]{plan.get('analysis_id', 'N/A')}[/cyan]")
        console.print(f"Status: [yellow]{plan.get('status', 'N/A')}[/yellow]")

        # Display summary
        summary = plan.get('summary')
        if summary:
            console.print(f"\n📝 [bold yellow]Summary:[/bold yellow]")
            console.print(f"   {summary}")

        # Filter stakeholders if specified
        stakeholders_to_show = []
        if stakeholder:
            stakeholder_upper = stakeholder.upper()
            if stakeholder_upper in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
                stakeholders_to_show = [stakeholder_upper]
            else:
                console.print(f"❌ [red]Invalid stakeholder: {stakeholder}. Valid options: BORROWER, ADVISOR, SUPERVISOR, LEADERSHIP[/red]")
                raise typer.Exit(1)
        else:
            stakeholders_to_show = ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']

        # Display stakeholder plans
        for stakeholder_name in stakeholders_to_show:
            stakeholder_key = f"{stakeholder_name.lower()}_plan"
            stakeholder_plan = plan.get(stakeholder_key)

            if stakeholder_plan:
                console.print(f"\n🎯 [bold cyan]{stakeholder_name} PLAN[/bold cyan]:")

                if stakeholder_name == 'BORROWER':
                    _display_borrower_plan(stakeholder_plan)
                elif stakeholder_name == 'ADVISOR':
                    _display_advisor_plan(stakeholder_plan)
                elif stakeholder_name == 'SUPERVISOR':
                    _display_supervisor_plan(stakeholder_plan)
                elif stakeholder_name == 'LEADERSHIP':
                    _display_leadership_plan(stakeholder_plan)

    except CLIError as e:
        print_error(f"View failed: {str(e)}")
        raise typer.Exit(1)


def _display_borrower_plan(borrower_plan: Dict[str, Any]):
    """Display BORROWER plan section."""
    # Immediate Actions
    immediate_actions = borrower_plan.get('immediate_actions', [])
    if immediate_actions:
        console.print(f"\n  🚨 [bold red]Immediate Actions ({len(immediate_actions)}):[/bold red]")
        for i, action in enumerate(immediate_actions, 1):
            console.print(f"    {i}. [{action.get('priority', 'N/A').upper()}] {action.get('action', 'N/A')}")
            console.print(f"       Timeline: {action.get('timeline', 'N/A')}")
            console.print(f"       Auto-executable: {action.get('auto_executable', False)}")
            if action.get('description'):
                console.print(f"       Description: {action['description']}")

    # Follow-ups
    follow_ups = borrower_plan.get('follow_ups', [])
    if follow_ups:
        console.print(f"\n  📋 [bold yellow]Follow-ups ({len(follow_ups)}):[/bold yellow]")
        for i, follow_up in enumerate(follow_ups, 1):
            console.print(f"    {i}. {follow_up.get('action', 'N/A')}")
            console.print(f"       Due: {follow_up.get('due_date', 'N/A')}")
            console.print(f"       Owner: {follow_up.get('owner', 'N/A')}")
            if follow_up.get('trigger_condition'):
                console.print(f"       Trigger: {follow_up['trigger_condition']}")

    # Risk Mitigation
    risk_mitigation = borrower_plan.get('risk_mitigation', [])
    if risk_mitigation:
        console.print(f"\n  🛡️ [bold blue]Risk Mitigation ({len(risk_mitigation)}):[/bold blue]")
        for i, risk in enumerate(risk_mitigation, 1):
            console.print(f"    {i}. {risk}")


def _display_advisor_plan(advisor_plan: Dict[str, Any]):
    """Display ADVISOR plan section."""
    # Coaching Items
    coaching_items = advisor_plan.get('coaching_items', [])
    if coaching_items:
        console.print(f"\n  👥 [bold green]Coaching Items ({len(coaching_items)}):[/bold green]")
        for i, item in enumerate(coaching_items, 1):
            console.print(f"    {i}. [{item.get('priority', 'N/A').upper()}] {item.get('action', 'N/A')}")
            console.print(f"       Coaching Point: {item.get('coaching_point', 'N/A')}")
            console.print(f"       Expected Improvement: {item.get('expected_improvement', 'N/A')}")

    # Training Recommendations
    training_recs = advisor_plan.get('training_recommendations', [])
    if training_recs:
        console.print(f"\n  🎓 [bold yellow]Training Recommendations ({len(training_recs)}):[/bold yellow]")
        for i, training in enumerate(training_recs, 1):
            console.print(f"    {i}. {training}")

    # Performance Feedback
    performance = advisor_plan.get('performance_feedback', {})
    if performance:
        console.print(f"\n  📊 [bold blue]Performance Feedback:[/bold blue]")
        strengths = performance.get('strengths', [])
        if strengths:
            console.print(f"    Strengths:")
            for strength in strengths:
                console.print(f"      • {strength}")

        improvements = performance.get('improvements', [])
        if improvements:
            console.print(f"    Areas for Improvement:")
            for improvement in improvements:
                console.print(f"      • {improvement}")

    # Next Actions
    next_actions = advisor_plan.get('next_actions', [])
    if next_actions:
        console.print(f"\n  ⏭️ [bold cyan]Next Actions ({len(next_actions)}):[/bold cyan]")
        for i, action in enumerate(next_actions, 1):
            console.print(f"    {i}. {action}")


def _display_supervisor_plan(supervisor_plan: Dict[str, Any]):
    """Display SUPERVISOR plan section."""
    # Escalation Items
    escalation_items = supervisor_plan.get('escalation_items', [])
    if escalation_items:
        console.print(f"\n  🚨 [bold red]Escalation Items ({len(escalation_items)}):[/bold red]")
        for i, item in enumerate(escalation_items, 1):
            if isinstance(item, dict):
                console.print(f"    {i}. {item.get('item', 'N/A')}")
                console.print(f"       Reason: {item.get('reason', 'N/A')}")
                console.print(f"       Action Required: {item.get('action_required', 'N/A')}")
            else:
                console.print(f"    {i}. {item}")

    # Team Patterns
    team_patterns = supervisor_plan.get('team_patterns', [])
    if team_patterns:
        console.print(f"\n  👥 [bold yellow]Team Patterns ({len(team_patterns)}):[/bold yellow]")
        for i, pattern in enumerate(team_patterns, 1):
            console.print(f"    {i}. {pattern}")

    # Compliance Review
    compliance_review = supervisor_plan.get('compliance_review', [])
    if compliance_review:
        console.print(f"\n  ⚖️ [bold blue]Compliance Review ({len(compliance_review)}):[/bold blue]")
        for i, review in enumerate(compliance_review, 1):
            console.print(f"    {i}. {review}")

    # Process Improvements
    process_improvements = supervisor_plan.get('process_improvements', [])
    if process_improvements:
        console.print(f"\n  📈 [bold green]Process Improvements ({len(process_improvements)}):[/bold green]")
        for i, improvement in enumerate(process_improvements, 1):
            if isinstance(improvement, dict):
                console.print(f"    {i}. {improvement.get('improvement', 'N/A')}")
                console.print(f"       Expected Benefit: {improvement.get('expected_benefit', 'N/A')}")
            else:
                console.print(f"    {i}. {improvement}")


def _display_leadership_plan(leadership_plan: Dict[str, Any]):
    """Display LEADERSHIP plan section."""
    # Strategic Initiatives
    strategic_initiatives = leadership_plan.get('strategic_initiatives', [])
    if strategic_initiatives:
        console.print(f"\n  🎯 [bold red]Strategic Initiatives ({len(strategic_initiatives)}):[/bold red]")
        for i, initiative in enumerate(strategic_initiatives, 1):
            if isinstance(initiative, dict):
                console.print(f"    {i}. {initiative.get('initiative', 'N/A')}")
                console.print(f"       Business Impact: {initiative.get('business_impact', 'N/A')}")
            else:
                console.print(f"    {i}. {initiative}")

    # Long-term Goals
    long_term_goals = leadership_plan.get('long_term_goals', [])
    if long_term_goals:
        console.print(f"\n  🎯 [bold yellow]Long-term Goals ({len(long_term_goals)}):[/bold yellow]")
        for i, goal in enumerate(long_term_goals, 1):
            console.print(f"    {i}. {goal}")

    # Resource Allocation
    resource_allocation = leadership_plan.get('resource_allocation', [])
    if resource_allocation:
        console.print(f"\n  💰 [bold green]Resource Allocation ({len(resource_allocation)}):[/bold green]")
        for i, resource in enumerate(resource_allocation, 1):
            if isinstance(resource, dict):
                console.print(f"    {i}. {resource.get('resource', 'N/A')}")
                console.print(f"       Amount: {resource.get('amount', 'N/A')}")
                console.print(f"       Justification: {resource.get('justification', 'N/A')}")
            else:
                console.print(f"    {i}. {resource}")

    # Budget Considerations
    budget_considerations = leadership_plan.get('budget_considerations', [])
    if budget_considerations:
        console.print(f"\n  💼 [bold blue]Budget Considerations ({len(budget_considerations)}):[/bold blue]")
        for i, consideration in enumerate(budget_considerations, 1):
            console.print(f"    {i}. {consideration}")


@plan_app.command("delete")
def plan_delete(
    plan_id: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete specific action plan."""
    try:
        client = get_client()

        if not force:
            confirm = typer.confirm(f"Delete action plan {plan_id}?", default=False)
            if not confirm:
                console.print("❌ Deletion cancelled")
                return

        console.print(f"🗑️ [bold magenta]Deleting plan {plan_id}...[/bold magenta]")
        client.delete_plan(plan_id)

        print_success(f"Deleted plan: {plan_id}")

    except CLIError as e:
        print_error(f"Delete failed: {str(e)}")
        raise typer.Exit(1)


@plan_app.command("delete-all")
def plan_delete_all(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete all action plans."""
    try:
        client = get_client()

        if not force:
            confirm = typer.confirm("Delete ALL action plans? This cannot be undone.", default=False)
            if not confirm:
                console.print("❌ Deletion cancelled")
                return

        console.print("🗑️ [bold magenta]Deleting all plans...[/bold magenta]")
        result = client.delete_all_plans()

        count = result.get('deleted_count', 0)
        print_success(f"Deleted {count} plans")

    except CLIError as e:
        print_error(f"Delete all failed: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# WORKFLOW COMMANDS
# ====================================================================

@workflow_app.command("generate")
def workflow_generate(
    plan: str = typer.Option(..., "--plan", "-p", help="Plan ID to generate workflows from")
):
    """Generate workflows from action plan."""
    try:
        client = get_client()

        console.print(f"⚙️ [bold magenta]Generating workflows from plan {plan}...[/bold magenta]")
        result = client.extract_all_workflows(plan)

        # Display generation results
        console.print(f"\n⚙️ [bold green]Workflow Generation Started[/bold green]:")
        console.print(f"Plan ID: [cyan]{result.get('plan_id', plan)}[/cyan]")
        console.print(f"Status: [yellow]{result.get('status', 'processing')}[/yellow]")

        workflows_created = result.get('workflows_created', 0)
        if workflows_created:
            print_success(f"Created {workflows_created} workflows")

        # Display workflow IDs if available
        workflow_ids = result.get('workflow_ids', [])
        if workflow_ids:
            console.print(f"\n📋 [bold blue]Created Workflow IDs:[/bold blue]")
            for workflow_id in workflow_ids:
                console.print(f"   • {workflow_id}")

        # Display message if available
        message = result.get('message')
        if message:
            console.print(f"\n💬 [bold cyan]Message:[/bold cyan] {message}")

    except CLIError as e:
        print_error(f"Workflow extraction failed: {str(e)}")
        raise typer.Exit(1)


@workflow_app.command("list")
def workflow_list(
    plan: Optional[str] = typer.Option(None, "--plan", "-p", help="Filter by plan ID"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results")
):
    """List workflows."""
    try:
        client = get_client()

        console.print("⚙️ [bold magenta]Listing workflows...[/bold magenta]")
        params = {}
        if plan:
            params['plan_id'] = plan
        if status:
            params['status'] = status
        if limit:
            params['limit'] = limit

        workflows = client.list_workflows(**params)

        if not workflows:
            console.print("📭 No workflows found")
            return

        console.print(f"\n📊 Found {len(workflows)} workflow(s):")

        for workflow in workflows:
            workflow_id = workflow.get('workflow_id', 'N/A')
            plan_id = workflow.get('plan_id', 'N/A')
            status = workflow.get('status', 'N/A')
            workflow_type = workflow.get('workflow_type', 'N/A')
            step_count = len(workflow.get('workflow_steps', []))

            console.print(f"\n[cyan]Workflow ID:[/cyan] {workflow_id}")
            console.print(f"[cyan]Plan ID:[/cyan] {plan_id}")
            console.print(f"[cyan]Status:[/cyan] {status}")
            console.print(f"[cyan]Type:[/cyan] {workflow_type}")
            console.print(f"[cyan]Steps:[/cyan] {step_count}")
            console.print("─" * 40)

    except CLIError as e:
        print_error(f"List failed: {str(e)}")
        raise typer.Exit(1)


@workflow_app.command("show")
def workflow_show(
    workflow_id: Optional[str] = typer.Argument(None, help="Workflow ID to show"),
    plan: Optional[str] = typer.Option(None, "--plan", "-p", help="Show all workflows for this plan ID")
):
    """Show detailed workflow information."""
    if not workflow_id and not plan:
        console.print("❌ [red]Either workflow_id or --plan must be specified[/red]")
        raise typer.Exit(1)

    if workflow_id and plan:
        console.print("❌ [red]Cannot specify both workflow_id and --plan[/red]")
        raise typer.Exit(1)

    try:
        client = get_client()

        if workflow_id:
            # Show single workflow
            console.print(f"⚙️ [bold magenta]Getting workflow {workflow_id}...[/bold magenta]")
            workflow = client.get_workflow(workflow_id)

            console.print(f"\n⚙️ [bold green]Workflow Details[/bold green]:")
            console.print(f"Workflow ID: [cyan]{workflow.get('workflow_id', workflow_id)}[/cyan]")
            console.print(f"Plan ID: [cyan]{workflow.get('plan_id', 'N/A')}[/cyan]")
            console.print(f"Status: [yellow]{workflow.get('status', 'N/A')}[/yellow]")
            console.print(f"Type: [yellow]{workflow.get('workflow_type', 'N/A')}[/yellow]")

            # Display workflow steps
            workflow_steps = workflow.get('workflow_steps', [])
            if workflow_steps:
                console.print(f"\n📋 [bold blue]Workflow Steps ({len(workflow_steps)}):[/bold blue]")
                for i, step in enumerate(workflow_steps, 1):
                    action = step.get('action', 'N/A')
                    tool = step.get('tool_needed', 'N/A')
                    details = step.get('details', '')
                    console.print(f"\n   {i}. {action}")
                    console.print(f"      Tool: {tool}")
                    if details:
                        console.print(f"      Details: {details}")

        elif plan:
            # Show all workflows for plan
            console.print(f"⚙️ [bold magenta]Getting all workflows for plan {plan}...[/bold magenta]")
            workflows = client.list_workflows(plan_id=plan)

            if not workflows:
                console.print("📭 No workflows found for this plan")
                return

            console.print(f"\n⚙️ [bold green]Workflows for Plan {plan} ({len(workflows)}):[/bold green]")

            # Group by stakeholder
            by_stakeholder = {}
            for workflow in workflows:
                stakeholder = workflow.get('workflow_type', 'UNKNOWN')
                if stakeholder not in by_stakeholder:
                    by_stakeholder[stakeholder] = []
                by_stakeholder[stakeholder].append(workflow)

            # Display by stakeholder
            for stakeholder in ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']:
                if stakeholder in by_stakeholder:
                    stakeholder_workflows = by_stakeholder[stakeholder]
                    console.print(f"\n🎯 [bold cyan]{stakeholder} WORKFLOWS ({len(stakeholder_workflows)}):[/bold cyan]")

                    for i, workflow in enumerate(stakeholder_workflows, 1):
                        workflow_id = workflow.get('workflow_id', 'N/A')
                        status = workflow.get('status', 'N/A')
                        workflow_data = workflow.get('workflow_data', {})
                        title = workflow_data.get('title', 'No title')
                        steps = workflow_data.get('steps', [])

                        console.print(f"\n  {i}. [cyan]{title}[/cyan]")
                        console.print(f"     ID: {workflow_id}")
                        console.print(f"     Status: [yellow]{status}[/yellow]")
                        console.print(f"     Steps: {len(steps)}")

                        if steps:
                            console.print(f"     📋 [bold blue]Steps:[/bold blue]")
                            for j, step in enumerate(steps[:3], 1):  # Show first 3 steps
                                step_action = step.get('action', 'N/A')
                                console.print(f"       {j}. {step_action}")
                            if len(steps) > 3:
                                console.print(f"       ... and {len(steps) - 3} more steps")

    except CLIError as e:
        print_error(f"Show failed: {str(e)}")
        raise typer.Exit(1)


@workflow_app.command("approve")
def workflow_approve(
    workflow_id: str,
    approved_by: str = typer.Option("cli_user", "--approved-by", help="Name of approver"),
    reasoning: Optional[str] = typer.Option(None, "--reasoning", help="Approval reasoning")
):
    """Approve a workflow."""
    try:
        client = get_client()

        console.print(f"✅ [bold magenta]Approving workflow {workflow_id}...[/bold magenta]")
        result = client.approve_workflow(workflow_id, approved_by, reasoning)

        print_success(f"Workflow approved: {workflow_id}")

        # Display approval details
        console.print(f"\n✅ [bold green]Approval Details[/bold green]:")
        console.print(f"Workflow ID: [cyan]{result.get('workflow_id', workflow_id)}[/cyan]")
        console.print(f"Approved By: [cyan]{result.get('approved_by', approved_by)}[/cyan]")
        console.print(f"Status: [yellow]{result.get('status', 'approved')}[/yellow]")
        if reasoning:
            console.print(f"Reasoning: [yellow]{reasoning}[/yellow]")

    except CLIError as e:
        print_error(f"Approval failed: {str(e)}")
        raise typer.Exit(1)


@workflow_app.command("execute")
def workflow_execute(
    workflow_id: str,
    executed_by: str = typer.Option("cli_user", "--executed-by", help="Name of executor")
):
    """Execute an approved workflow."""
    try:
        client = get_client()

        console.print(f"🚀 [bold magenta]Executing workflow {workflow_id}...[/bold magenta]")
        result = client.execute_workflow(workflow_id, executed_by)

        print_success(f"Workflow executed: {workflow_id}")

        # Display execution results
        console.print(f"\n🚀 [bold green]Execution Results[/bold green]:")
        console.print(f"Workflow ID: [cyan]{result.get('workflow_id', workflow_id)}[/cyan]")
        console.print(f"Executed By: [cyan]{result.get('executed_by', executed_by)}[/cyan]")
        console.print(f"Status: [yellow]{result.get('status', 'executed')}[/yellow]")

        # Display execution summary
        execution_summary = result.get('execution_summary', {})
        if execution_summary:
            console.print(f"\n📊 [bold blue]Execution Summary:[/bold blue]")
            total_steps = execution_summary.get('total_steps', 0)
            completed_steps = execution_summary.get('completed_steps', 0)
            failed_steps = execution_summary.get('failed_steps', 0)

            console.print(f"   Total Steps: {total_steps}")
            console.print(f"   Completed: {completed_steps}")
            console.print(f"   Failed: {failed_steps}")

            if total_steps > 0:
                success_rate = completed_steps / total_steps
                console.print(f"   Success Rate: {success_rate:.2%}")

    except CLIError as e:
        print_error(f"Execution failed: {str(e)}")
        raise typer.Exit(1)


@workflow_app.command("delete")
def workflow_delete(
    workflow_id: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete specific workflow."""
    try:
        client = get_client()

        if not force:
            confirm = typer.confirm(f"Delete workflow {workflow_id}?", default=False)
            if not confirm:
                console.print("❌ Deletion cancelled")
                return

        console.print(f"🗑️ [bold magenta]Deleting workflow {workflow_id}...[/bold magenta]")
        client.delete_workflow(workflow_id)

        print_success(f"Deleted workflow: {workflow_id}")

    except CLIError as e:
        print_error(f"Delete failed: {str(e)}")
        raise typer.Exit(1)


@workflow_app.command("delete-all")
def workflow_delete_all(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete all workflows."""
    try:
        client = get_client()

        if not force:
            confirm = typer.confirm("Delete ALL workflows? This cannot be undone.", default=False)
            if not confirm:
                console.print("❌ Deletion cancelled")
                return

        console.print("🗑️ [bold magenta]Deleting all workflows...[/bold magenta]")
        result = client.delete_all_workflows()

        count = result.get('deleted_count', 0)
        print_success(f"Deleted {count} workflows")

    except CLIError as e:
        print_error(f"Delete all failed: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# EXECUTION COMMANDS
# ====================================================================

@execution_app.command("list")
def execution_list(
    workflow: Optional[str] = typer.Option(None, "--workflow", "-w", help="Filter by workflow ID"),
    limit: Optional[int] = typer.Option(None, "--limit", "-l", help="Limit number of results"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
    executor_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by executor type")
):
    """List all executions."""
    try:
        client = get_client()

        console.print("🚀 [bold magenta]Listing executions...[/bold magenta]")
        executions = client.list_executions(workflow_id=workflow, limit=limit, status=status, executor_type=executor_type)

        if not executions:
            console.print("📭 No executions found")
            return

        console.print(f"\n📊 Found {len(executions)} execution(s):")

        for execution in executions:
            execution_id = execution.get('id', 'N/A')
            workflow_id = execution.get('workflow_id', 'N/A')
            executor_type = execution.get('executor_type', 'N/A')
            status = execution.get('execution_status', 'N/A')
            created_at = execution.get('created_at', 'N/A')

            console.print(f"\n[cyan]Execution ID:[/cyan] {execution_id}")
            console.print(f"[cyan]Workflow ID:[/cyan] {workflow_id}")
            console.print(f"[cyan]Executor Type:[/cyan] {executor_type}")
            console.print(f"[cyan]Status:[/cyan] {status}")
            console.print(f"[cyan]Created:[/cyan] {created_at}")

            # Show error message if failed
            if status == 'failed':
                error_msg = execution.get('error_message', 'Unknown error')
                console.print(f"[red]Error:[/red] {error_msg}")

            console.print("─" * 40)

    except CLIError as e:
        print_error(f"List failed: {str(e)}")
        raise typer.Exit(1)


@execution_app.command("show")
def execution_show(execution_id: str):
    """Show specific execution details."""
    try:
        client = get_client()

        console.print(f"🚀 [bold magenta]Getting execution {execution_id}...[/bold magenta]")
        execution = client.get_execution(execution_id)

        console.print(f"\n🚀 [bold green]Execution Details[/bold green]:")
        console.print(f"Execution ID: [cyan]{execution.get('id', execution_id)}[/cyan]")
        console.print(f"Workflow ID: [cyan]{execution.get('workflow_id', 'N/A')}[/cyan]")
        console.print(f"Executor Type: [cyan]{execution.get('executor_type', 'N/A')}[/cyan]")
        console.print(f"Status: [yellow]{execution.get('execution_status', 'N/A')}[/yellow]")
        console.print(f"Created: [cyan]{execution.get('created_at', 'N/A')}[/cyan]")

        # Show execution payload
        payload = execution.get('execution_payload', {})
        if payload:
            console.print(f"\n📋 [bold blue]Execution Payload:[/bold blue]")
            for key, value in payload.items():
                console.print(f"   {key}: {value}")

        # Show error details if failed
        if execution.get('execution_status') == 'failed':
            error_msg = execution.get('error_message', 'Unknown error')
            console.print(f"\n[red]Error Details:[/red] {error_msg}")

    except CLIError as e:
        print_error(f"Get failed: {str(e)}")
        raise typer.Exit(1)


@execution_app.command("delete")
def execution_delete(
    execution_id: str,
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation")
):
    """Delete specific execution."""
    try:
        client = get_client()

        if not force:
            confirm = typer.confirm(f"Delete execution {execution_id}?", default=False)
            if not confirm:
                console.print("❌ Deletion cancelled")
                return

        console.print(f"🗑️ [bold magenta]Deleting execution {execution_id}...[/bold magenta]")
        client.delete_execution(execution_id)

        print_success(f"Deleted execution: {execution_id}")

    except CLIError as e:
        print_error(f"Delete failed: {str(e)}")
        raise typer.Exit(1)


@execution_app.command("delete-all")
def execution_delete_all(
    force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation"),
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Only delete executions with this status"),
    executor_type: Optional[str] = typer.Option(None, "--type", "-t", help="Only delete executions of this type")
):
    """Delete all executions with optional filters."""
    try:
        client = get_client()

        filter_desc = ""
        if status or executor_type:
            filters = []
            if status:
                filters.append(f"status={status}")
            if executor_type:
                filters.append(f"type={executor_type}")
            filter_desc = f" with filters: {', '.join(filters)}"

        if not force:
            confirm = typer.confirm(f"Delete ALL executions{filter_desc}? This cannot be undone.", default=False)
            if not confirm:
                console.print("❌ Deletion cancelled")
                return

        console.print(f"🗑️ [bold magenta]Deleting all executions{filter_desc}...[/bold magenta]")
        result = client.delete_all_executions(status=status, executor_type=executor_type)

        count = result.get('deleted_count', 0)
        print_success(f"Deleted {count} executions")

    except CLIError as e:
        print_error(f"Delete all failed: {str(e)}")
        raise typer.Exit(1)


@execution_app.command("stats")
def execution_stats():
    """Get comprehensive execution statistics."""
    try:
        client = get_client()

        console.print("📊 [bold magenta]Getting execution statistics...[/bold magenta]")
        stats = client.get_execution_statistics()

        console.print(f"\n📊 [bold green]Execution Statistics[/bold green]:")

        # Overall statistics
        console.print(f"Total Executions: [cyan]{stats.get('total_executions', 0)}[/cyan]")
        console.print(f"Successful: [green]{stats.get('successful_executions', 0)}[/green]")
        console.print(f"Failed: [red]{stats.get('failed_executions', 0)}[/red]")
        console.print(f"In Progress: [yellow]{stats.get('in_progress_executions', 0)}[/yellow]")

        success_rate = stats.get('success_rate', 0)
        console.print(f"Success Rate: [cyan]{success_rate:.2%}[/cyan]")

        # Executor type breakdown
        executor_stats = stats.get('executor_type_stats', {})
        if executor_stats:
            console.print(f"\n📈 [bold blue]By Executor Type:[/bold blue]")
            for executor_type, type_stats in executor_stats.items():
                total = type_stats.get('total', 0)
                successful = type_stats.get('successful', 0)
                failed = type_stats.get('failed', 0)
                console.print(f"   {executor_type}: {total} total ({successful} success, {failed} failed)")

        # Recent activity
        recent_executions = stats.get('recent_executions', 0)
        console.print(f"\nRecent Executions (24h): [cyan]{recent_executions}[/cyan]")

    except CLIError as e:
        print_error(f"Statistics failed: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# ORCHESTRATE COMMANDS (Core subset)
# ====================================================================

@orchestrate_app.command("run")
def orchestrate_run(
    transcript_id: str = typer.Argument(..., help="Transcript ID to process through pipeline"),
    auto_approve: bool = typer.Option(False, "--auto-approve", "-a", help="Auto-approve all workflows"),
    verbose: bool = typer.Option(DEFAULT_VERBOSE, "--verbose", "-v", help="Enable verbose output")
):
    """Run complete orchestration pipeline: Transcript → Analysis → Plan → Workflows → Execution."""
    try:
        client = get_client()

        console.print(f"🚀 [bold cyan]Starting orchestration pipeline for transcript: {transcript_id}[/bold cyan]")

        if verbose:
            console.print("🔄 Pipeline stages: Transcript → Analysis → Plan → Workflows → Execution")

        # Start orchestration via API
        start_result = client.orchestrate_run([transcript_id], auto_approve)
        run_id = start_result["run_id"]

        console.print(f"📝 [bold blue]Run ID: {run_id}[/bold blue]")
        console.print(f"🚀 Status: {start_result['status']}")

        # Poll for completion with progress updates
        import time
        last_stage = ""
        while True:
            status = client.get_orchestration_status(run_id)

            current_stage = status.get("stage", "")
            if current_stage != last_stage:
                # Display user-friendly stage messages
                if current_stage == "ANALYSIS_COMPLETED":
                    analysis_id = status.get("analysis_id", "N/A")
                    console.print(f"✅ [bold green]Analysis Completed[/bold green] (ID: {analysis_id})")
                elif current_stage == "PLAN_COMPLETED":
                    plan_id = status.get("plan_id", "N/A")
                    console.print(f"✅ [bold green]Plan Completed[/bold green] (ID: {plan_id})")
                elif current_stage == "WORKFLOWS_COMPLETED":
                    workflow_count = status.get("workflow_count", 0)
                    console.print(f"✅ [bold green]Workflows Generated[/bold green] ({workflow_count} items)")
                elif current_stage == "EXECUTION_COMPLETED":
                    executed = status.get("executed_count", 0)
                    failed = status.get("failed_count", 0)
                    console.print(f"✅ [bold green]Execution Completed[/bold green] ({executed} successful, {failed} failed)")
                elif current_stage == "COMPLETE":
                    console.print(f"🎉 [bold green]Pipeline Complete![/bold green]")
                elif verbose:
                    console.print(f"🔄 [dim]Stage: {current_stage}[/dim]")
                last_stage = current_stage

            if status["status"] == "COMPLETED":
                break
            elif status["status"] == "FAILED":
                print_error("Pipeline failed!")
                raise typer.Exit(1)

            # Show progress if available
            progress = status.get("progress", {})
            if progress.get("percentage") is not None:
                console.print(f"⏳ Progress: {progress['percentage']:.1f}% ({progress['processed']}/{progress['total']})")

            time.sleep(2)  # Poll every 2 seconds

        # Get final results
        final_status = client.get_orchestration_status(run_id)

        # Display results in table format
        table = Table(title="Pipeline Execution Results")
        table.add_column("Stage", style="cyan")
        table.add_column("Result", style="green")

        table.add_row("Run ID", run_id)
        table.add_row("Transcript ID", transcript_id)
        table.add_row("Status", final_status["status"])
        table.add_row("Final Stage", final_status["stage"])

        # Results summary
        results = final_status.get("results", [])
        errors = final_status.get("errors", [])
        summary = final_status.get("summary", {})

        table.add_row("Successful Results", str(len(results)))
        table.add_row("Failed Results", str(len(errors)))

        if summary:
            table.add_row("Success Rate", f"{summary.get('success_rate', 0)*100:.0f}%")

        console.print(table)

        # Show individual results if verbose
        if verbose and results:
            console.print(f"\n📊 [bold blue]Pipeline Results:[/bold blue]")
            for i, result in enumerate(results, 1):
                console.print(f"   Result {i}:")
                console.print(f"     Transcript: {result.get('transcript_id')}")
                console.print(f"     Analysis: {result.get('analysis_id')}")
                console.print(f"     Plan: {result.get('plan_id')}")
                console.print(f"     Workflows: {result.get('workflow_count', 0)}")
                console.print(f"     Executed: {result.get('executed_count', 0)}")

        # Show errors if any
        if errors:
            console.print(f"\n❌ [bold red]Errors:[/bold red]")
            for error in errors:
                console.print(f"   Transcript {error.get('transcript_id')}: {error.get('error')}")

        # Final status message
        if summary:
            success_rate = summary.get('success_rate', 0)
            if success_rate == 1.0:
                print_success(f"Pipeline completed successfully! Success rate: 100%")
            elif success_rate > 0.5:
                print_warning(f"Pipeline completed with partial success! Success rate: {success_rate*100:.0f}%")
            else:
                print_error(f"Pipeline failed! Success rate: {success_rate*100:.0f}%")

    except CLIError as e:
        print_error(f"Pipeline orchestration failed: {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Pipeline orchestration failed: {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@orchestrate_app.command("execute-approved")
def orchestrate_execute_approved(
    executed_by: str = typer.Option("cli_user", "--executed-by", help="Name of executor")
):
    """Execute all approved workflows."""
    try:
        client = get_client()

        console.print("🚀 [bold magenta]Executing all approved workflows...[/bold magenta]")
        result = client.execute_all_workflows(executed_by)

        executed_count = result.get('executed_count', 0)
        failed_count = result.get('failed_count', 0)

        if failed_count > 0:
            print_warning(f"Executed {executed_count} workflows, {failed_count} failed")
        else:
            print_success(f"Executed {executed_count} workflows successfully")

        # Display execution summary
        if 'execution_summary' in result:
            summary = result['execution_summary']
            console.print(f"\n📊 [bold blue]Execution Summary:[/bold blue]")
            console.print(f"   Total Workflows: {summary.get('total_workflows', 0)}")
            console.print(f"   Executed: {summary.get('executed', 0)}")
            console.print(f"   Failed: {summary.get('failed', 0)}")
            console.print(f"   Success Rate: {summary.get('success_rate', 0):.2%}")

    except CLIError as e:
        print_error(f"Execute approved failed: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# SYSTEM COMMANDS
# ====================================================================

@system_app.command("tree")
def system_tree():
    """Show complete command tree using Rich Tree component."""
    from rich.tree import Tree

    # Create the root tree
    tree = Tree("🌳 [bold cyan]cli[/bold cyan] - Customer Call Center Analytics")

    # Helper function to add commands to a tree branch
    def add_commands_to_branch(branch, typer_instance):
        """Recursively add commands from a Typer instance to a tree branch."""
        if hasattr(typer_instance, 'registered_commands'):
            for cmd in typer_instance.registered_commands:
                name = cmd.name or cmd.callback.__name__
                help_text = cmd.help or cmd.callback.__doc__ or ""
                # Clean up help text - take first line only
                help_text = help_text.split('\n')[0] if help_text else ""
                branch.add(f"[green]{name}[/green] - {help_text}")

    # Add each sub-app as a branch
    sub_apps = [
        (transcript_app, "transcript", "📝"),
        (analysis_app, "analysis", "🔍"),
        (insights_app, "insights", "💡"),
        (plan_app, "plan", "📋"),
        (workflow_app, "workflow", "⚙️"),
        (execution_app, "execution", "🚀"),
        (orchestrate_app, "orchestrate", "🎯"),
        (system_app, "system", "🔧"),
    ]

    for app_instance, app_name, icon in sub_apps:
        branch = tree.add(f"{icon} [bold blue]{app_name}[/bold blue]")
        add_commands_to_branch(branch, app_instance)

    # Display the tree
    console.print(tree)

    # Show usage tip
    console.print("\n💡 [bold green]Tip:[/bold green] Use --help with any command for detailed options")
    console.print("  Example: [cyan]python cli.py workflow list --help[/cyan]")

@system_app.command("health")
def system_health():
    """Check system health."""
    try:
        client = get_client()

        console.print("🏥 [bold magenta]Checking system health...[/bold magenta]")
        health = client.get_health()

        status = health.get('status', 'unknown')
        if status == 'healthy':
            console.print(f"✅ [bold green]System Status: {status.upper()}[/bold green]")
        else:
            console.print(f"❌ [bold red]System Status: {status.upper()}[/bold red]")

        # Display health details
        services = health.get('services', {})
        if services:
            console.print(f"\n🔧 [bold blue]Service Status:[/bold blue]")
            for service, service_status in services.items():
                status_icon = "✅" if service_status == "healthy" else "❌"
                console.print(f"   {status_icon} {service}: {service_status}")

        # Display system info
        system_info = health.get('system_info', {})
        if system_info:
            console.print(f"\n💻 [bold cyan]System Info:[/bold cyan]")
            for key, value in system_info.items():
                console.print(f"   {key}: {value}")

    except CLIError as e:
        print_error(f"Health check failed: {str(e)}")
        raise typer.Exit(1)


@system_app.command("metrics")
def system_metrics():
    """Get system metrics."""
    try:
        client = get_client()

        console.print("📊 [bold magenta]Getting system metrics...[/bold magenta]")
        metrics = client.get_metrics()

        console.print(f"\n📊 [bold green]System Metrics[/bold green]:")

        # Display key metrics
        for key, value in metrics.items():
            if isinstance(value, dict):
                console.print(f"\n[bold yellow]{key.title()}:[/bold yellow]")
                for sub_key, sub_value in value.items():
                    console.print(f"   {sub_key}: {sub_value}")
            else:
                console.print(f"{key}: [cyan]{value}[/cyan]")

    except CLIError as e:
        print_error(f"Metrics failed: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# LEADERSHIP COMMANDS
# ====================================================================

@leadership_app.command("chat")
def leadership_chat(
    query: str = typer.Argument(..., help="Leadership query"),
    executive_id: str = typer.Option(..., "--exec-id", "-e", help="Executive identifier"),
    executive_role: str = typer.Option("Manager", "--role", "-r", help="Executive role (VP, CCO, Manager, etc.)"),
    session_id: Optional[str] = typer.Option(None, "--session", "-s", help="Continue existing session")
):
    """Chat with Leadership Insights Agent for strategic intelligence."""
    try:
        # Use API mode only - no direct bypass allowed
        console.print("🎯 [bold blue]Leadership Insights[/bold blue]")
        console.print(f"Query: [cyan]{query}[/cyan]")
        console.print(f"Role: [yellow]{executive_role}[/yellow]")
        console.print(f"Executive: [green]{executive_id}[/green]")
        if session_id:
            console.print(f"Session: [magenta]{session_id}[/magenta]")
        console.print()

        client = get_client()
        response = client.leadership_chat(query, executive_id, executive_role, session_id)

        # Display response
        console.print(Panel(
            response.get('content', 'No content generated'),
            title="[bold green]Strategic Insights[/bold green]",
            border_style="green"
        ))

        # Display session info
        if response.get('session_id'):
            console.print(f"\n📝 Session ID: [cyan]{response['session_id']}[/cyan]")

        # Display metadata
        metadata = response.get('metadata', {})
        if metadata:
            console.print(f"\n📊 Confidence: [yellow]{metadata.get('overall_confidence', 'N/A')}%[/yellow]")
            console.print(f"⏱️  Processing: [blue]{metadata.get('total_processing_time_ms', 'N/A')}ms[/blue]")
            if response.get('cache_hit'):
                console.print("💾 [green]Cache Hit[/green]")

    except CLIError as e:
        print_error(f"Leadership chat failed: {str(e)}")
        raise typer.Exit(1)


@leadership_app.command("sessions")
def list_sessions(
    executive_id: str = typer.Option(..., "--exec-id", "-e", help="Executive identifier"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum sessions to return")
):
    """List sessions for an executive."""
    try:
        console.print(f"📋 [bold blue]Sessions for Executive[/bold blue]: [cyan]{executive_id}[/cyan]")
        console.print()

        client = get_client()
        response = client.leadership_sessions(executive_id, limit)

        sessions = response.get('sessions', [])
        if not sessions:
            console.print("[yellow]No sessions found[/yellow]")
            return

        # Create table
        table = Table(title="Executive Sessions")
        table.add_column("Session ID", style="cyan", no_wrap=True)
        table.add_column("Focus Area", style="green")
        table.add_column("Started", style="yellow")
        table.add_column("Status", style="magenta")

        for session in sessions:
            table.add_row(
                session.get('session_id', 'N/A'),
                session.get('focus_area', 'N/A'),
                session.get('started_at', 'N/A'),
                session.get('status', 'active')
            )

        console.print(table)
        console.print(f"\n📊 Total: [cyan]{len(sessions)}[/cyan] sessions")

    except CLIError as e:
        print_error(f"Failed to list sessions: {str(e)}")
        raise typer.Exit(1)


@leadership_app.command("history")
def session_history(
    session_id: str = typer.Argument(..., help="Session identifier"),
    limit: int = typer.Option(50, "--limit", "-l", help="Maximum messages to return")
):
    """Get conversation history for a session."""
    try:
        console.print(f"📜 [bold blue]Session History[/bold blue]: [cyan]{session_id}[/cyan]")
        console.print()

        client = get_client()
        response = client.leadership_session_history(session_id, limit)

        session = response.get('session', {})
        messages = response.get('messages', [])

        if not messages:
            console.print("[yellow]No messages found[/yellow]")
            return

        # Display session info
        console.print(f"🎯 Focus Area: [green]{session.get('focus_area', 'N/A')}[/green]")
        console.print(f"👤 Executive: [yellow]{session.get('executive_role', 'N/A')}[/yellow]")
        console.print(f"📅 Started: [blue]{session.get('started_at', 'N/A')}[/blue]")
        console.print()

        # Display messages
        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            timestamp = msg.get('created_at', '')

            if role == 'user':
                console.print(f"[bold cyan]👤 {timestamp}[/bold cyan]")
                console.print(Panel(content, border_style="cyan"))
            else:
                console.print(f"[bold green]🤖 {timestamp}[/bold green]")
                console.print(Panel(content, border_style="green"))
            console.print()

        console.print(f"📊 Total messages: [cyan]{len(messages)}[/cyan]")

    except CLIError as e:
        print_error(f"Failed to get session history: {str(e)}")
        raise typer.Exit(1)


@leadership_app.command("dashboard")
def leadership_dashboard(
    executive_role: Optional[str] = typer.Option(None, "--role", "-r", help="Filter by executive role")
):
    """Get pre-computed insights dashboard."""
    try:
        console.print("📊 [bold blue]Leadership Dashboard[/bold blue]")
        console.print()

        client = get_client()
        response = client.leadership_dashboard(executive_role)

        # Display data overview
        data_overview = response.get('data_overview', {})
        if data_overview:
            console.print("📈 [bold yellow]Data Overview[/bold yellow]")
            for key, value in data_overview.items():
                console.print(f"   {key}: [cyan]{value}[/cyan]")
            console.print()

        # Display cache performance
        cache_perf = response.get('cache_performance', {})
        if cache_perf:
            console.print("💾 [bold yellow]Cache Performance[/bold yellow]")
            for key, value in cache_perf.items():
                console.print(f"   {key}: [cyan]{value}[/cyan]")
            console.print()

        # Display learning progress
        learning = response.get('learning_progress', {})
        if learning:
            console.print("🧠 [bold yellow]Learning Progress[/bold yellow]")
            for key, value in learning.items():
                console.print(f"   {key}: [cyan]{value}[/cyan]")
            console.print()

        # Display system status
        system_status = response.get('system_status', {})
        if system_status:
            console.print("⚙️  [bold yellow]System Status[/bold yellow]")
            for key, value in system_status.items():
                if isinstance(value, dict):
                    console.print(f"   {key}:")
                    for sub_key, sub_value in value.items():
                        console.print(f"      {sub_key}: [cyan]{sub_value}[/cyan]")
                else:
                    console.print(f"   {key}: [cyan]{value}[/cyan]")

    except CLIError as e:
        print_error(f"Failed to get dashboard: {str(e)}")
        raise typer.Exit(1)


@leadership_app.command("status")
def leadership_status():
    """Get leadership service health and component status."""
    try:
        console.print("⚙️  [bold blue]Leadership Service Status[/bold blue]")
        console.print()

        client = get_client()
        response = client.leadership_status()

        console.print(f"🏢 Service: [green]{response.get('service_name', 'N/A')}[/green]")
        console.print(f"📦 Version: [yellow]{response.get('version', 'N/A')}[/yellow]")
        console.print(f"🟢 Status: [green]{response.get('status', 'N/A')}[/green]")
        console.print(f"🕐 Last Checked: [blue]{response.get('last_checked', 'N/A')}[/blue]")
        console.print()

        # Display component status
        components = response.get('components', {})
        if components:
            console.print("🔧 [bold yellow]Components[/bold yellow]")
            for component, status in components.items():
                color = "green" if status == "ready" else "red"
                console.print(f"   {component}: [{color}]{status}[/{color}]")

    except CLIError as e:
        print_error(f"Failed to get status: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# MAIN ENTRY POINT
# ====================================================================

if __name__ == "__main__":
    app()