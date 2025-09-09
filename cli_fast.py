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


@app.command()
def analyze(
    transcript_id: Optional[str] = typer.Option(None, "--transcript-id", "-t", help="Specific transcript ID to analyze"),
    all_transcripts: bool = typer.Option(False, "--all", "-a", help="Analyze all transcripts")
):
    """Analyze transcript(s) for mortgage servicing insights."""
    client = CLIClient()
    
    if not transcript_id and not all_transcripts:
        client.print_error("Specify either --transcript-id or --all")
        raise typer.Exit(1)
    
    params = {
        'transcript_id': transcript_id,
        'all_transcripts': all_transcripts
    }
    
    console.print("🔍 [bold magenta]Analyzing transcript(s)...[/bold magenta]")
    result = client.send_command('analyze', params)
    
    if result['success']:
        analyses = result.get('analyses', [])
        client.print_success(f"Analyzed {len(analyses)} transcript(s)")
        
        # Show summary of analyses
        for analysis in analyses:
            console.print(f"\n📄 Transcript: {analysis['transcript_id']}")
            console.print(f"   Intent: {analysis.get('primary_intent', 'N/A')}")
            console.print(f"   Urgency: {analysis.get('urgency_level', 'N/A')}")
            console.print(f"   Sentiment: {analysis.get('borrower_sentiment', {}).get('overall', 'N/A')}")
            console.print(f"   Confidence: {analysis.get('confidence_score', 0):.2f}")
            if analysis.get('escalation_needed'):
                console.print("   🚨 [bold red]Escalation needed[/bold red]")
    else:
        client.print_error(f"Analysis failed: {result['error']}")


@app.command("analysis-report")
def analysis_report(
    transcript_id: Optional[str] = typer.Option(None, "--transcript-id", "-t", help="Specific transcript analysis to view"),
    analysis_id: Optional[str] = typer.Option(None, "--analysis-id", "-a", help="Specific analysis ID to view")
):
    """View detailed analysis report."""
    client = CLIClient()
    
    if not transcript_id and not analysis_id:
        client.print_error("Specify either --transcript-id or --analysis-id")
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
        client.print_error(f"Report failed: {result['error']}")


@app.command("analysis-metrics")
def analysis_metrics():
    """Show aggregate analysis metrics dashboard."""
    client = CLIClient()
    
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
        client.print_error(f"Metrics failed: {result['error']}")


@app.command("risk-report")
def risk_report(
    threshold: float = typer.Option(0.7, "--threshold", "-t", help="Minimum risk threshold (0.0-1.0)")
):
    """Show high-risk borrower report."""
    client = CLIClient()
    
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
        client.print_error(f"Risk report failed: {result['error']}")


@app.command("generate-action-plan")
def generate_action_plan(
    analysis_id: Optional[str] = typer.Option(None, "--analysis-id", "-a", help="Analysis ID to generate plan from"),
    transcript_id: Optional[str] = typer.Option(None, "--transcript-id", "-t", help="Transcript ID to generate plan from")
):
    """Generate four-layer action plan from analysis."""
    client = CLIClient()
    
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
        client.print_error(f"Action plan generation failed: {result['error']}")


@app.command("view-action-plan")
def view_action_plan(
    plan_id: str = typer.Argument(..., help="Action plan ID"),
    layer: Optional[str] = typer.Option(None, "--layer", "-l", help="Specific layer to view (borrower, advisor, supervisor, leadership)")
):
    """View action plan details."""
    client = CLIClient()
    
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
        client.print_error(f"Failed to get action plan: {result['error']}")


@app.command("action-plan-queue")
def action_plan_queue(
    status: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by queue status")
):
    """View action plan approval queue."""
    client = CLIClient()
    
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
        client.print_error(f"Failed to get queue: {result['error']}")


@app.command("approve-action-plan")
def approve_action_plan(
    plan_id: str = typer.Argument(..., help="Action plan ID to approve"),
    approver: str = typer.Option("CLI_USER", "--approver", "-by", help="Approver identifier")
):
    """Approve an action plan."""
    client = CLIClient()
    
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
        client.print_error(f"Approval failed: {result['error']}")


@app.command("action-plan-summary")
def action_plan_summary():
    """Show action plan summary metrics."""
    client = CLIClient()
    
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
        client.print_error(f"Failed to get metrics: {result['error']}")


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
    client = CLIClient()
    
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
                        status_icon = "✅" if action.get('status') == 'success' or 'sent' in str(action.get('status', '')) else "❌"
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
        client.print_error(f"Failed to execute plan: {result['error']}")


@app.command("execution-history")
def execution_history(
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent executions to show")
):
    """Show recent execution history."""
    client = CLIClient()
    
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
        client.print_error(f"Failed to get execution history: {result['error']}")


@app.command("view-artifacts")
def view_artifacts(
    artifact_type: str = typer.Option("all", "--type", "-t", help="Type of artifacts to view: emails, callbacks, documents, all"),
    limit: int = typer.Option(10, "--limit", "-l", help="Number of recent artifacts to show")
):
    """View execution artifacts (emails, documents, callbacks)."""
    client = CLIClient()
    
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
        client.print_error(f"Failed to get artifacts: {result['error']}")


@app.command("execution-metrics")  
def execution_metrics():
    """Show execution metrics and statistics."""
    client = CLIClient()
    
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
        client.print_error(f"Failed to get execution metrics: {result['error']}")


# ========== Decision Agent Commands ==========

@app.command("get-approval-queue")
def get_approval_queue(
    route: Optional[str] = typer.Option(None, help="Filter by approval route: advisor_approval, supervisor_approval")
):
    """Get actions pending approval in the Decision Agent queue."""
    client = CLIClient()
    result = client.send_command('get_approval_queue', {'route': route})
    
    if result['success']:
        queue = result['queue']
        
        if not queue:
            client.print_info("No actions pending approval")
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
        client.print_error(f"Failed to get approval queue: {result['error']}")


@app.command("approve-action")
def approve_action(
    action_id: str = typer.Argument(help="Action ID to approve"),
    approved_by: str = typer.Option("CLI_USER", help="Approver identifier"),
    notes: str = typer.Option("", help="Approval notes")
):
    """Approve a specific action in the queue."""
    client = CLIClient()
    result = client.send_command('approve_action', {
        'action_id': action_id,
        'approved_by': approved_by,
        'notes': notes
    })
    
    if result['success']:
        client.print_success(result['message'])
    else:
        client.print_error(f"Failed to approve action: {result['error']}")


@app.command("reject-action")  
def reject_action(
    action_id: str = typer.Argument(help="Action ID to reject"),
    rejected_by: str = typer.Option("CLI_USER", help="Rejector identifier"),
    reason: str = typer.Option("No reason provided", help="Rejection reason")
):
    """Reject a specific action in the queue."""
    client = CLIClient()
    result = client.send_command('reject_action', {
        'action_id': action_id,
        'rejected_by': rejected_by,
        'reason': reason
    })
    
    if result['success']:
        client.print_success(f"{result['message']} - Reason: {result['reason']}")
    else:
        client.print_error(f"Failed to reject action: {result['error']}")


@app.command("bulk-approve")
def bulk_approve_actions(
    action_ids: str = typer.Argument(help="Comma-separated list of action IDs to approve"),
    approved_by: str = typer.Option("CLI_USER", help="Approver identifier"),
    notes: str = typer.Option("Bulk approval", help="Approval notes")
):
    """Bulk approve multiple actions."""
    client = CLIClient()
    
    # Parse comma-separated action IDs
    ids_list = [aid.strip() for aid in action_ids.split(',')]
    
    result = client.send_command('bulk_approve_actions', {
        'action_ids': ids_list,
        'approved_by': approved_by,
        'notes': notes
    })
    
    if result['success']:
        client.print_success(result['message'])
        console.print(f"Approved: {result['approved_count']}/{result['total_requested']} actions")
    else:
        client.print_error(f"Failed to bulk approve: {result['error']}")


@app.command("approval-metrics")
def approval_metrics():
    """Get approval queue metrics and statistics."""
    client = CLIClient()
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
        client.print_error(f"Failed to get approval metrics: {result['error']}")


@app.command("decision-agent-summary")
def decision_agent_summary():
    """Get Decision Agent configuration and processing summary."""
    client = CLIClient()
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
        client.print_error(f"Failed to get decision agent summary: {result['error']}")


if __name__ == "__main__":
    app()