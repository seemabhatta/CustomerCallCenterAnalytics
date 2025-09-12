#!/usr/bin/env python3
"""
Customer Call Center Analytics CLI - Consolidated Resource-Based Commands
Direct REST API client following industry best practices
No fallback logic - fail fast with clear error messages
Resource-aligned commands: transcript, analysis, plan, system
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
system_app = typer.Typer(name="system", help="System operations")

# Add subapps to main app
app.add_typer(transcript_app)
app.add_typer(analysis_app)
app.add_typer(insights_app)
app.add_typer(plan_app)
app.add_typer(workflow_app)
app.add_typer(system_app)


# ====================================================================
# TRANSCRIPT COMMANDS
# ====================================================================

@transcript_app.command("create")
def transcript_create(
    topic: str = typer.Option(..., "--topic", help="Topic/scenario for transcript"),
    store: bool = typer.Option(True, "--store/--no-store", help="Store transcript in database")
):
    """Create new transcript."""
    try:
        client = get_client()
        
        console.print("📝 [bold magenta]Generating transcript...[/bold magenta]")
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

@workflow_app.command("extract")
def workflow_extract(
    plan_id: str = typer.Argument(..., help="Plan ID to extract workflow from")
):
    """Extract workflow from action plan."""
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


@workflow_app.command("list")
def workflow_list(
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


@workflow_app.command("view")
def workflow_view(
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
        console.print(f"Status: [green]{workflow.get('status')}[/green]")
        console.print(f"Risk Level: [red]{workflow.get('risk_level')}[/red]")
        
        # Risk reasoning
        if workflow.get('risk_reasoning'):
            console.print(f"\n💭 [bold blue]Risk Assessment:[/bold blue]")
            console.print(f"{workflow['risk_reasoning']}")
        
        # Approval information
        console.print(f"\n🔐 [bold blue]Approval Status:[/bold blue]")
        console.print(f"Requires Approval: {'Yes' if workflow.get('requires_human_approval') else 'No'}")
        
        if workflow.get('assigned_approver'):
            console.print(f"Assigned Approver: {workflow['assigned_approver']}")
        
        if workflow.get('approved_by'):
            console.print(f"Approved By: {workflow['approved_by']}")
            console.print(f"Approved At: {workflow.get('approved_at', 'N/A')}")
        
        if workflow.get('rejected_by'):
            console.print(f"Rejected By: {workflow['rejected_by']}")
            console.print(f"Rejected At: {workflow.get('rejected_at', 'N/A')}")
            console.print(f"Rejection Reason: {workflow.get('rejection_reason', 'N/A')}")
        
        # Workflow steps
        if workflow.get('workflow_data', {}).get('workflow_steps'):
            console.print(f"\n📝 [bold blue]Workflow Steps:[/bold blue]")
            for i, step in enumerate(workflow['workflow_data']['workflow_steps'], 1):
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


@workflow_app.command("approve")
def workflow_approve(
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


@workflow_app.command("reject")
def workflow_reject(
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


@workflow_app.command("execute")
def workflow_execute(
    workflow_id: str = typer.Argument(..., help="Workflow ID to execute"),
    executor: str = typer.Option(..., "--executor", "-e", help="Executor identifier")
):
    """Execute an approved workflow."""
    try:
        client = get_client()
        
        console.print(f"🚀 [bold magenta]Executing workflow...[/bold magenta]")
        result = client.execute_workflow(
            workflow_id=workflow_id,
            executed_by=executor
        )
        
        console.print(f"\n🚀 [bold green]Workflow Executed[/bold green]:")
        console.print(f"Workflow ID: [cyan]{result.get('id')}[/cyan]")
        console.print(f"Executed By: [yellow]{result.get('execution_results', {}).get('executor', executor)}[/yellow]")
        console.print(f"Status: [green]{result.get('status')}[/green]")
        console.print(f"Executed At: [blue]{result.get('executed_at', 'N/A')}[/blue]")
        
        # Show execution results if available
        exec_results = result.get('execution_results', {})
        if exec_results.get('execution_status'):
            console.print(f"Execution Status: [green]{exec_results['execution_status']}[/green]")
        
        print_success(f"Workflow executed: {workflow_id}")
        
    except CLIError as e:
        print_error(f"Execution failed: {str(e)}")
        raise typer.Exit(1)


@workflow_app.command("history")
def workflow_history(
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


@workflow_app.command("pending")
def workflow_pending():
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


if __name__ == "__main__":
    app()