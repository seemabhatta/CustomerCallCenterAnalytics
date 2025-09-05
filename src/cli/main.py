import click
import json
from datetime import datetime
from typing import Optional

from ..generators.transcript_generator import TranscriptGenerator
from ..storage.db_manager import DatabaseManager
from ..agents.orchestrator import OrchestratorAgent
from ..config.settings import settings

# Initialize global instances
generator = None
db_manager = None
orchestrator = None

def get_generator():
    """Get or create transcript generator instance."""
    global generator
    if generator is None:
        generator = TranscriptGenerator()
    return generator

def get_db():
    """Get or create database manager instance."""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def get_orchestrator():
    """Get or create orchestrator agent instance."""
    global orchestrator
    if orchestrator is None:
        orchestrator = OrchestratorAgent()
    return orchestrator

@click.group()
@click.version_option(version='0.1.0')
def cli():
    """Customer Call Center Analytics CLI - AI Co-Pilot for Loan Servicing"""
    pass

@cli.group()
def transcript():
    """Commands for managing call transcripts."""
    pass

@transcript.command()
@click.option('--scenario', '-s', 
              type=click.Choice(['hardship', 'escrow', 'refinance']),
              default='hardship',
              help='Scenario type for transcript generation')
@click.option('--count', '-c', default=1, help='Number of transcripts to generate')
@click.option('--save/--no-save', default=True, help='Save generated transcripts to database')
def generate(scenario: str, count: int, save: bool):
    """Generate realistic call transcripts using AI."""
    click.echo(f"Generating {count} transcript(s) for scenario: {scenario}")
    
    try:
        gen = get_generator()
        database = get_db() if save else None
        
        for i in range(count):
            click.echo(f"Generating transcript {i+1}/{count}...", nl=False)
            
            transcript = gen.generate_transcript(scenario=scenario)
            
            if save and database:
                database.store_transcript(transcript)
                click.echo(f" ✓ Saved with ID: {transcript.transcript_id}")
            else:
                click.echo(" ✓ Generated")
                
            # Show brief summary
            click.echo(f"   Call ID: {transcript.call_metadata.call_id}")
            click.echo(f"   Customer: {transcript.customer.name}")
            click.echo(f"   Advisor: {transcript.advisor.name}")
            click.echo(f"   Duration: {transcript.call_metadata.duration_seconds // 60} minutes")
            click.echo(f"   Segments: {len(transcript.segments)}")
            
            if not save:
                click.echo("\nSample dialogue:")
                for segment in transcript.segments[:3]:  # Show first 3 segments
                    click.echo(f"   {segment.speaker.value.title()}: {segment.text}")
                if len(transcript.segments) > 3:
                    click.echo("   ...")
            
            click.echo()
        
        click.secho(f"Successfully generated {count} transcript(s)!", fg='green')
        
    except Exception as e:
        click.secho(f"Error generating transcripts: {str(e)}", fg='red', err=True)
        return 1

@transcript.command()
@click.option('--limit', '-l', default=10, help='Limit number of results')
@click.option('--scenario', '-s', help='Filter by scenario type')
def list(limit: int, scenario: Optional[str]):
    """List stored transcripts."""
    try:
        database = get_db()
        transcripts = database.list_transcripts(limit=limit, scenario=scenario)
        
        if not transcripts:
            click.echo("No transcripts found.")
            return
        
        click.echo(f"Found {len(transcripts)} transcript(s):")
        click.echo()
        
        # Header
        click.echo(f"{'ID':<8} {'Call ID':<15} {'Scenario':<12} {'Customer':<20} {'Duration':<8} {'Created':<10}")
        click.echo("-" * 85)
        
        for t in transcripts:
            created_date = t['created_at'][:10] if isinstance(t['created_at'], str) else t['created_at'].date()
            click.echo(f"{t['transcript_id'][:8]:<8} "
                      f"{t['call_id']:<15} "
                      f"{t['scenario']:<12} "
                      f"{t['customer_name']:<20} "
                      f"{t['duration_minutes']}m{'':<5} "
                      f"{created_date}")
        
    except Exception as e:
        click.secho(f"Error listing transcripts: {str(e)}", fg='red', err=True)
        return 1

@transcript.command()
@click.argument('transcript_id')
@click.option('--format', '-f', type=click.Choice(['summary', 'full', 'segments']), 
              default='summary', help='Output format')
def show(transcript_id: str, format: str):
    """Show details of a specific transcript."""
    try:
        database = get_db()
        
        # Handle partial IDs - find matching transcript
        if len(transcript_id) == 8:
            transcripts = database.list_transcripts()
            matching = [t for t in transcripts if t['transcript_id'].startswith(transcript_id)]
            if not matching:
                click.secho(f"No transcript found with ID starting with: {transcript_id}", fg='red')
                return 1
            elif len(matching) > 1:
                click.echo(f"Multiple transcripts match ID '{transcript_id}':")
                for t in matching:
                    click.echo(f"  {t['transcript_id']} - {t['call_id']}")
                return 1
            transcript_id = matching[0]['transcript_id']
        
        transcript = database.get_transcript(transcript_id)
        if not transcript:
            click.secho(f"Transcript not found: {transcript_id}", fg='red')
            return 1
        
        if format == 'summary':
            click.echo(f"Transcript ID: {transcript.transcript_id}")
            click.echo(f"Call ID: {transcript.call_metadata.call_id}")
            click.echo(f"Scenario: {transcript.scenario}")
            click.echo(f"Date: {transcript.call_metadata.call_date.strftime('%Y-%m-%d %H:%M')}")
            click.echo(f"Duration: {transcript.call_metadata.duration_seconds // 60}m {transcript.call_metadata.duration_seconds % 60}s")
            click.echo(f"Customer: {transcript.customer.name} ({transcript.customer.customer_id})")
            click.echo(f"Advisor: {transcript.advisor.name} ({transcript.advisor.advisor_id})")
            click.echo(f"Resolution: {transcript.call_metadata.resolution_status}")
            if transcript.tags:
                click.echo(f"Tags: {', '.join(transcript.tags)}")
            click.echo(f"Segments: {len(transcript.segments)}")
            
        elif format == 'segments':
            click.echo(f"Transcript: {transcript.call_metadata.call_id}")
            click.echo("-" * 60)
            for i, segment in enumerate(transcript.segments, 1):
                timestamp_min = int(segment.timestamp // 60)
                timestamp_sec = int(segment.timestamp % 60)
                click.echo(f"[{timestamp_min:02d}:{timestamp_sec:02d}] {segment.speaker.value.title()}: {segment.text}")
                
        elif format == 'full':
            click.echo(json.dumps(transcript.model_dump(mode='json'), indent=2, default=str))
        
    except Exception as e:
        click.secho(f"Error showing transcript: {str(e)}", fg='red', err=True)
        return 1

@transcript.command()
@click.argument('query')
def search(query: str):
    """Search transcripts by content."""
    try:
        database = get_db()
        results = database.search_transcripts(query)
        
        if not results:
            click.echo(f"No transcripts found containing: '{query}'")
            return
        
        click.echo(f"Found {len(results)} transcript(s) containing '{query}':")
        click.echo()
        
        for result in results:
            click.echo(f"ID: {result['transcript_id'][:8]} | Call: {result['call_id']}")
            click.echo(f"Customer: {result['customer_name']} | Scenario: {result['scenario']}")
            click.echo(f"Match: {result['match_preview']}")
            click.echo("-" * 60)
        
    except Exception as e:
        click.secho(f"Error searching transcripts: {str(e)}", fg='red', err=True)
        return 1

@cli.group()
def db():
    """Database management commands."""
    pass

@db.command()
def stats():
    """Show database statistics."""
    try:
        database = get_db()
        stats = database.get_database_stats()
        
        click.echo("Database Statistics:")
        click.echo(f"  Transcripts: {stats['transcripts']}")
        click.echo(f"  Agent Sessions: {stats['agent_sessions']}")
        click.echo(f"  Analysis Results: {stats['analysis_results']}")
        click.echo(f"  Actions: {stats['actions']}")
        
    except Exception as e:
        click.secho(f"Error getting database stats: {str(e)}", fg='red', err=True)
        return 1

@cli.group()
def agent():
    """Agent management commands (coming soon)."""
    pass

@agent.command()
def list():
    """List available agents."""
    agents = [
        "orchestrator - Coordinates multi-agent analysis [ACTIVE]",
        "diarization - Identifies and labels speakers [PLANNED]", 
        "intent_entity - Extracts customer intents and entities [PLANNED]",
        "compliance - Checks for required disclosures [PLANNED]",
        "action_drafting - Suggests follow-up actions [PLANNED]",
        "quality_scoring - Evaluates call quality metrics [PLANNED]"
    ]
    
    click.echo("Available agents:")
    for agent in agents:
        click.echo(f"  • {agent}")

@agent.command()
@click.argument('transcript_id')
@click.option('--force', is_flag=True, help='Force re-analysis if results exist')
def analyze(transcript_id: str, force: bool):
    """Run orchestrator agent analysis on a transcript."""
    try:
        orchestrator_agent = get_orchestrator()
        database = get_db()
        
        # Handle partial IDs
        if len(transcript_id) == 8:
            transcripts = database.list_transcripts()
            matching = [t for t in transcripts if t['transcript_id'].startswith(transcript_id)]
            if not matching:
                click.secho(f"No transcript found with ID starting with: {transcript_id}", fg='red')
                return 1
            elif len(matching) > 1:
                click.echo(f"Multiple transcripts match ID '{transcript_id}':")
                for t in matching:
                    click.echo(f"  {t['transcript_id']} - {t['call_id']}")
                return 1
            transcript_id = matching[0]['transcript_id']
        
        # Check for existing analysis
        existing_results = orchestrator_agent.get_analysis_results(transcript_id)
        if existing_results and not force:
            click.echo(f"Analysis already exists for transcript {transcript_id[:8]}.")
            click.echo("Use --force to re-analyze or 'agent show' to view results.")
            return
        
        click.echo(f"Analyzing transcript {transcript_id[:8]}...")
        
        with click.progressbar(length=100, label='Running analysis') as bar:
            # Simulate progress for better UX
            import time
            bar.update(20)
            time.sleep(0.5)
            
            results = orchestrator_agent.analyze_transcript(transcript_id)
            
            bar.update(50)
            time.sleep(0.3)
            bar.update(30)
        
        click.secho("✓ Analysis completed!", fg='green')
        
        # Show summary
        insights = results['insights']
        click.echo(f"\nKey Findings:")
        click.echo(f"  Customer Intent: {insights.get('customer_intent', 'Unknown')}")
        click.echo(f"  Sentiment: {insights.get('customer_sentiment', 'Unknown')}")
        click.echo(f"  Resolution: {'✓' if insights.get('resolution_achieved') else '✗'}")
        click.echo(f"  Confidence: {insights.get('confidence', 0)*100:.0f}%")
        
        # Show action counts
        action_plans = results['action_plans']
        borrower_actions = len(action_plans['borrower_plan']['immediate_actions'])
        click.echo(f"  Actions Generated: {borrower_actions} for customer")
        
        click.echo(f"\nUse 'agent show {transcript_id[:8]}' to see detailed results.")
        
    except Exception as e:
        click.secho(f"Error analyzing transcript: {str(e)}", fg='red', err=True)
        return 1

@agent.command()
@click.argument('transcript_id')
@click.option('--section', '-s', type=click.Choice(['insights', 'actions', 'quality', 'compliance', 'summary']),
              help='Show specific section only')
def show(transcript_id: str, section: Optional[str]):
    """Show agent analysis results for a transcript."""
    try:
        orchestrator_agent = get_orchestrator()
        database = get_db()
        
        # Handle partial IDs
        if len(transcript_id) == 8:
            transcripts = database.list_transcripts()
            matching = [t for t in transcripts if t['transcript_id'].startswith(transcript_id)]
            if not matching:
                click.secho(f"No transcript found with ID starting with: {transcript_id}", fg='red')
                return 1
            elif len(matching) > 1:
                click.echo(f"Multiple transcripts match ID '{transcript_id}':")
                for t in matching:
                    click.echo(f"  {t['transcript_id']} - {t['call_id']}")
                return 1
            transcript_id = matching[0]['transcript_id']
        
        results = orchestrator_agent.get_analysis_results(transcript_id)
        if not results:
            click.secho(f"No analysis found for transcript {transcript_id[:8]}", fg='yellow')
            click.echo("Run 'agent analyze' first to generate analysis.")
            return
        
        if section == 'insights' or not section:
            insights = results['insights']
            click.echo("📊 INSIGHTS")
            click.echo("=" * 50)
            click.echo(f"Customer Intent: {insights.get('customer_intent')}")
            click.echo(f"Sentiment: {insights.get('customer_sentiment')}")
            click.echo(f"Resolution Achieved: {'Yes' if insights.get('resolution_achieved') else 'No'}")
            click.echo(f"Key Issues: {', '.join(insights.get('key_issues', []))}")
            click.echo(f"Risk Factors: {', '.join(insights.get('risk_factors', []))}")
            click.echo(f"Confidence: {insights.get('confidence', 0)*100:.1f}%")
            click.echo()
        
        if section == 'actions' or not section:
            action_plans = results['action_plans']
            click.echo("📋 ACTION PLANS")
            click.echo("=" * 50)
            
            click.echo("🏠 Borrower Actions:")
            for action in action_plans['borrower_plan']['immediate_actions']:
                click.echo(f"  • {action}")
            click.echo(f"  Follow-up: {action_plans['borrower_plan']['follow_up_timeline']}")
            click.echo()
            
            click.echo("👩‍💻 Advisor Coaching:")
            for point in action_plans['advisor_plan']['coaching_points']:
                click.echo(f"  • {point}")
            click.echo()
            
            if action_plans['supervisor_plan']['escalation_required']:
                click.echo("👩‍💼 Supervisor Escalation: REQUIRED")
                for item in action_plans['supervisor_plan']['approval_items']:
                    click.echo(f"  • {item['type']}: {item['description']}")
            else:
                click.echo("👩‍💼 Supervisor Escalation: Not required")
            click.echo()
        
        if section == 'quality' or not section:
            quality = results['quality_scores']
            click.echo("⭐ QUALITY SCORES")
            click.echo("=" * 50)
            click.echo(f"Compliance Adherence: {quality['compliance_adherence']*100:.1f}%")
            click.echo(f"Empathy Index: {quality['empathy_index']*100:.1f}%")
            click.echo(f"Efficiency Score: {quality['efficiency_score']*100:.1f}%")
            click.echo(f"Predicted CSAT: {quality['customer_satisfaction_predicted']:.1f}/5.0")
            click.echo(f"First Call Resolution: {'Yes' if quality['first_call_resolution'] == 1.0 else 'No'}")
            click.echo()
        
        if section == 'compliance' or not section:
            compliance = results['compliance']
            click.echo("⚖️  COMPLIANCE CHECK")
            click.echo("=" * 50)
            click.echo(f"Overall Score: {compliance['overall_score']*100:.1f}%")
            click.echo(f"Risk Level: {compliance['risk_level'].title()}")
            for check, passed in compliance['checks'].items():
                status = "✓" if passed else "✗"
                click.echo(f"  {status} {check.replace('_', ' ').title()}")
            if compliance['required_actions']:
                click.echo("Required Actions:")
                for action in compliance['required_actions']:
                    click.echo(f"  • {action}")
            click.echo()
        
        if section == 'summary' or not section:
            click.echo("📄 EXECUTIVE SUMMARY")
            click.echo("=" * 50)
            click.echo(results['summary'].strip())
        
    except Exception as e:
        click.secho(f"Error showing analysis results: {str(e)}", fg='red', err=True)
        return 1

@cli.command()
def scenarios():
    """List available transcript generation scenarios."""
    try:
        gen = get_generator()
        available = gen.get_available_scenarios()
        
        click.echo("Available scenarios:")
        for scenario in available:
            click.echo(f"  • {scenario}")
        
    except Exception as e:
        click.secho(f"Error listing scenarios: {str(e)}", fg='red', err=True)
        return 1

@cli.command()
def status():
    """Show system status and configuration."""
    click.echo("Customer Call Center Analytics - System Status")
    click.echo("=" * 50)
    
    # Check configuration
    try:
        settings.validate()
        click.secho("✓ Configuration: Valid", fg='green')
    except Exception as e:
        click.secho(f"✗ Configuration: {str(e)}", fg='red')
    
    # Check database
    try:
        database = get_db()
        stats = database.get_database_stats()
        click.secho("✓ Database: Connected", fg='green')
        click.echo(f"   {stats['transcripts']} transcripts stored")
    except Exception as e:
        click.secho(f"✗ Database: {str(e)}", fg='red')
    
    # Check AI
    try:
        gen = get_generator()
        scenarios = gen.get_available_scenarios()
        click.secho("✓ AI Generator: Ready", fg='green')
        click.echo(f"   {len(scenarios)} scenarios available")
    except Exception as e:
        click.secho(f"✗ AI Generator: {str(e)}", fg='red')

if __name__ == '__main__':
    cli()