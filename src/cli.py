import click
import sys
import os

# Add src to path to handle imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.config import settings
from agents import Agent, Runner
from src.tools import generate_transcript, analyze_transcript, search_data, list_recent_items, get_system_status

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

        **Available Tools:**
        - generate_transcript(): Create call transcripts from scenarios
        - analyze_transcript(): Analyze calls with multi-agent intelligence
        - search_data(): Search transcript database
        - list_recent_items(): Show recent transcripts and analyses
        - get_system_status(): System information and statistics

        You are the single point of interaction - handle everything directly with tools, no routing needed.""",
        model=settings.OPENAI_MODEL,
        tools=[generate_transcript, analyze_transcript, search_data, list_recent_items, get_system_status]
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
    print("\nHi! I can help you:")
    print("• Generate transcripts")
    print("• Analyze calls")
    print("• Search data")
    print("\nType 'help' for options or just tell me what you need.\n")
    
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

@cli.command()
def chat():
    """Start interactive chat mode"""
    interactive_mode()

if __name__ == '__main__':
    cli()