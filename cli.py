#!/usr/bin/env python3
"""
Customer Call Center Analytics CLI - Consolidated Resource-Based Commands
Direct REST API client following industry best practices
No fallback logic - fail fast with clear error messages
Resource-aligned commands: transcript, analysis, plan, case, governance, system
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
    
    def find_similar_cases(self, analysis_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar cases via GET /api/v1/insights/similar/{analysis_id}."""
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
    
    # Case operations
    def list_cases(self) -> List[Dict[str, Any]]:
        """List cases via GET /api/v1/cases."""
        return self._make_request('GET', '/api/v1/cases')
    
    def get_case(self, case_id: str) -> Dict[str, Any]:
        """Get case by ID via GET /api/v1/cases/{id}."""
        return self._make_request('GET', f'/api/v1/cases/{case_id}')
    
    # Governance operations  
    def get_approval_queue(self) -> List[Dict[str, Any]]:
        """Get approval queue via GET /api/v1/governance/queue."""
        return self._make_request('GET', '/api/v1/governance/queue')
    
    def approve_action(self, action_id: str, **kwargs) -> Dict[str, Any]:
        """Approve action via POST /api/v1/governance/approvals."""
        return self._make_request('POST', '/api/v1/governance/approvals', json_data={'action_id': action_id, **kwargs})
    
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
case_app = typer.Typer(name="case", help="Case operations")
governance_app = typer.Typer(name="governance", help="Governance operations")
system_app = typer.Typer(name="system", help="System operations")

# Add subapps to main app
app.add_typer(transcript_app)
app.add_typer(analysis_app)
app.add_typer(insights_app)
app.add_typer(plan_app)
app.add_typer(case_app)
app.add_typer(governance_app)
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
    analysis_id: str = typer.Argument(..., help="Analysis ID to find similar cases for"),
    limit: int = typer.Option(5, "--limit", "-l", help="Maximum similar cases to return")
):
    """Find similar cases using knowledge graph pattern matching."""
    try:
        if limit <= 0 or limit > 50:
            print_error("Limit must be between 1 and 50")
            raise typer.Exit(1)
        
        client = get_client()
        console.print(f"🔎 [bold cyan]Finding similar cases for {analysis_id} (limit: {limit})...[/bold cyan]")
        
        similar_cases = client.find_similar_cases(analysis_id, limit)
        
        if not similar_cases:
            console.print(f"🔍 No similar cases found for analysis {analysis_id}")
            return
        
        # Display similar cases
        table = Table(title=f"Similar Cases for {analysis_id}")
        table.add_column("Similar Analysis", style="blue")
        table.add_column("Shared Pattern", style="yellow")
        table.add_column("Risk Score", style="red")
        table.add_column("Confidence", style="green") 
        table.add_column("Learning Opportunity", style="white")
        
        for case in similar_cases:
            similarity = case.get('similarity', {})
            table.add_row(
                case.get('similar_analysis_id', 'Unknown'),
                similarity.get('shared_pattern', 'Unknown'),
                f"{similarity.get('risk_score', 0):.2f}",
                f"{similarity.get('confidence', 0):.2f}",
                case.get('learning_opportunity', 'None')[:40] + "..." if len(case.get('learning_opportunity', '')) > 40 else case.get('learning_opportunity', '')
            )
        
        console.print(table)
        print_success(f"Found {len(similar_cases)} similar cases")
        
    except CLIError as e:
        print_error(f"Similar case search failed: {str(e)}")
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


# ====================================================================
# CASE COMMANDS
# ====================================================================

@case_app.command("list")
def case_list():
    """List all cases."""
    try:
        client = get_client()
        
        console.print("📁 [bold magenta]Listing cases...[/bold magenta]")
        cases = client.list_cases()
        
        if not cases:
            console.print("📭 No cases found")
            return
        
        console.print(f"\n📊 Found {len(cases)} case(s):")
        
        for case in cases:
            case_id = case.get('case_id', 'N/A')
            status = case.get('status', 'N/A')
            
            console.print(f"\n[cyan]Case ID:[/cyan] {case_id}")
            console.print(f"[cyan]Status:[/cyan] {status}")
            console.print("─" * 40)
            
    except CLIError as e:
        print_error(f"List cases failed: {str(e)}")
        raise typer.Exit(1)


# ====================================================================
# GOVERNANCE COMMANDS
# ====================================================================

@governance_app.command("queue")
def governance_queue():
    """Show approval queue."""
    try:
        client = get_client()
        
        console.print("🎯 [bold magenta]Getting approval queue...[/bold magenta]")
        queue = client.get_approval_queue()
        
        if not queue:
            console.print("📭 No pending approvals")
            return
        
        console.print(f"\n📊 Found {len(queue)} pending approval(s):")
        
        for item in queue:
            action_id = item.get('action_id', 'N/A')
            status = item.get('status', 'N/A')
            
            console.print(f"\n[cyan]Action ID:[/cyan] {action_id}")
            console.print(f"[cyan]Status:[/cyan] {status}")
            console.print("─" * 40)
            
    except CLIError as e:
        print_error(f"Get approval queue failed: {str(e)}")
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