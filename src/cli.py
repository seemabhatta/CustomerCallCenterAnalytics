import click
import sys
import os

# Add src to path to handle imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.config import settings
from agents import Agent, Runner
from src.tools import (generate_transcript, analyze_transcript, search_data, list_recent_items, get_system_status,
                      view_action_queue, approve_action, reject_action, complete_action,
                      process_approved_items, view_integration_results, 
                      record_satisfaction, trigger_reanalysis, view_outcomes)

def get_router_agent():
    """Create the conversation router agent with tools"""
    return Agent(
        name="Mortgage Analytics Co-Pilot",
        instructions="""You are a tool router. When users make ANY request, immediately call the appropriate tool.

**ALWAYS use tools for these requests:**
- "generate" → generate_transcript("generate")
- "analyze" → analyze_transcript("analyze")  
- "queue" → view_action_queue()
- "list" → list_recent_items()
- "status" → get_system_status()

**Never ask questions. Always call tools immediately.**""",
        model=settings.OPENAI_MODEL,
        tools=[generate_transcript, analyze_transcript, search_data, list_recent_items, get_system_status,
               view_action_queue, approve_action, reject_action, complete_action,
               process_approved_items, view_integration_results,
               record_satisfaction, trigger_reanalysis, view_outcomes]
    )

def run_agent_sync(agent, prompt):
    """Run an agent with proper async handling using SDK best practices"""
    from agents import Runner
    
    try:
        # Use the sync version as recommended by SDK
        result = Runner.run_sync(agent, prompt)
        return result.final_output
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

def print_header():
    """Print welcome header"""
    print("🏠 Mortgage Servicing Call Center Analytics")

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Customer Call Center Analytics - AI-Powered Analysis System"""
    if ctx.invoked_subcommand is None:
        # No command = interactive mode
        interactive_mode()

def interactive_mode():
    """Pure agentic interface using conversation router with tools"""
    print_header()
    print("\nWelcome! I help mortgage servicing teams with AI-powered call analytics:")
    print("• Generate realistic mortgage servicing call transcripts")
    print("• Analyze calls for compliance, sentiment, and action items") 
    print("• Manage approval queue for fee waivers and modifications")
    print("• Track customer satisfaction and resolution outcomes")
    print("\nTry: 'generate a call about payment issues' or 'analyze recent'\n")
    
    router = get_router_agent()
    
    while True:
        try:
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break
            
            # Pure agentic approach - router handles everything with tools
            response = run_agent_sync(router, user_input)
            print(response)
                    
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


if __name__ == '__main__':
    cli()