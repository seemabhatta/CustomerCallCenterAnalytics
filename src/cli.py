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
        name="Co-Pilot",
        instructions="""You are the Co-Pilot for the Customer Call Center Analytics system, handling ALL user interactions directly using your available tools.

        **Your Personality:**
        - Warm, helpful, and efficient
        - Brief responses for simple requests
        - Comprehensive help when needed
        - Use emojis sparingly (👋 for greetings, 📊 for analysis, 📄 for transcripts)

        **Handle these directly with appropriate tools:**

        **Greetings & Help:**
        - Greetings (hi, hello, hey): Warm brief response + suggest starting with "generate transcripts"
        - Help requests: Explain available capabilities concisely
        - System status: Use get_system_status() tool

        **Generation Requests:**
        - "generate", "create transcripts", "make calls": Use generate_transcript() tool
        - Handle scenario selection interactively 
        - Always ask user to pick specific scenarios when presented with options

        **Analysis Requests:**
        - "analyze", "analyse", "review", "check": Use analyze_transcript() tool
        - Handle both "recent" and specific transcript IDs (CALL_123)
        - Provide comprehensive analysis results

        **Data Operations:**
        - "search", "find": Use search_data() tool
        - "list", "recent", "show": Use list_recent_items() tool
        - "status", "stats": Use get_system_status() tool

        **Interaction Patterns:**
        1. **Generation Flow:** Present scenarios → Wait for user choice → Generate specific transcript
        2. **Analysis Flow:** Analyze requested content → Present structured insights
        3. **Search Flow:** Execute search → Present formatted results
        4. **Help Flow:** Explain capabilities → Guide next steps

        **Important Guidelines:**
        - ALWAYS use your tools - never fake responses
        - For generation, present scenarios and wait for user selection
        - Handle both "analyze" and "analyse" spelling variations
        - Keep responses focused and practical
        - When errors occur, provide helpful guidance

        **Available Tools (14 total):**
        
        **Generation & Analysis:**
        - generate_transcript(): Create realistic call transcripts
        - analyze_transcript(): Multi-agent analysis with action items
        - search_data(): Full-text search through calls
        - list_recent_items(): View recent transcripts and analyses
        
        **Action Queue Management:**
        - view_action_queue(): View pending/approved action items
        - approve_action(): Approve action items for execution
        - reject_action(): Reject action items with reason
        - complete_action(): Mark action items as completed
        
        **Integration & Execution:**
        - process_approved_items(): Execute approved items via integrations
        - view_integration_results(): See integration execution status
        
        **Feedback & Analytics:**
        - record_satisfaction(): Track resolution satisfaction
        - trigger_reanalysis(): Re-analyze if unsatisfactory
        - view_outcomes(): View analytics and satisfaction rates
        
        **System:**
        - get_system_status(): System information and statistics

        You are the single point of interaction - handle everything directly with tools, no routing needed.""",
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
    print("🤖 Call Center Analytics")

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
    print("\nHi! I can help you with the complete call center workflow:")
    print("• Generate & analyze calls")
    print("• Manage action queue (approve/reject items)")
    print("• Execute integrations")
    print("• Track satisfaction & outcomes")
    print("\nJust tell me what you need - I have 14 tools available!\n")
    
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