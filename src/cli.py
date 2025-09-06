import click
import sys
import json
import asyncio
from .agents import get_generator, get_analyzer, get_orchestrator, get_conversation_router
from .storage import get_storage
from .config import settings
from .commands import VisionCommandHandler
from .interactive_commands import create_command_selector
from .agent_response import AgentResponse

# Initialize components
storage = get_storage()
orchestrator = get_orchestrator()
command_handler = VisionCommandHandler()
interactive_selector = create_command_selector(command_handler)

def run_agent_sync(agent, prompt):
    """Run an agent with proper async handling using SDK best practices"""
    from agents import Runner
    import asyncio
    import nest_asyncio
    import concurrent.futures
    
    # Allow nested event loops (helps with CLI environments)
    nest_asyncio.apply()
    
    try:
        # First try the sync version as recommended by SDK
        result = Runner.run_sync(agent, prompt)
        
        # Wrap in AgentResponse for consistent display formatting
        return AgentResponse(
            content=result.final_output,
            agent_name=agent.name,
            agent_chain=[agent.name]
        )
        
    except RuntimeError as e:
        if "event loop" in str(e).lower():
            # Event loop conflict - use async version in isolated thread
            async def run_async():
                return await Runner.run(agent, prompt)
            
            def run_in_isolated_thread():
                # Create completely new event loop in this thread
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(run_async())
                finally:
                    new_loop.close()
                    # Clean up the thread's event loop reference
                    asyncio.set_event_loop(None)
            
            # Run in thread pool to completely isolate from any existing loops
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_isolated_thread)
                result = future.result(timeout=60)  # 60 second timeout
                
                # Wrap in AgentResponse for consistent display formatting
                return AgentResponse(
                    content=result.final_output,
                    agent_name=agent.name,
                    agent_chain=[agent.name]
                )
        else:
            # Re-raise non-event-loop errors
            raise

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
    """Natural language interface with Co-Pilot modes"""
    print_header()
    print("\nHi! I can help you:")
    print("• Generate transcripts")
    print("• Analyze calls") 
    print("• Search data")
    print("\nType 'help' for options or just tell me what you need.\n")
    
    # Register CLI handlers with command handler
    cli_handlers = {
        'handle_generation': handle_generation,
        'handle_analysis': handle_analysis,
        'handle_plan_mode': handle_plan_mode,
        'handle_execute_mode': handle_execute_mode,
        'handle_reflect_mode': handle_reflect_mode,
        'handle_search': handle_search,
        'handle_list': handle_list,
        'handle_status': handle_status
    }
    command_handler.register_cli_handlers(cli_handlers)
    
    while True:
        try:
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break
                
            # Handle vision-aligned commands first (/, @, ?)
            if command_handler.is_command(user_input):
                # Check if user typed just a prefix for interactive selection
                if user_input.strip() in ['/', '@', '?']:
                    selected_command = interactive_selector.show_prefix_commands(user_input.strip())
                    if selected_command:
                        # Process the selected command
                        handled, response = command_handler.process_command(selected_command)
                        if handled and response:
                            print(response)
                    continue
                
                # Handle regular command processing
                handled, response = command_handler.process_command(user_input)
                if handled and response:
                    print(response)
                continue
            
            # Pure agentic approach - router handles everything except system controls
            try:
                router = get_conversation_router()
                response = run_agent_sync(router, user_input)
                
                # Use configurable display formatting
                display = response.format_display(
                    mode=settings.AGENT_DISPLAY_MODE,
                    override=settings.AGENT_NAME_OVERRIDE
                )
                print(display)
            except Exception as e:
                print(f"❌ Error: {e}")
                    
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

def show_help():
    """Show help information"""
    print("\n📚 Help - What I can do:")
    
    print("\n🤖 Co-Pilot Modes:")
    print("  • 'plan [request]' - Create actionable plans")
    print("  • 'execute [plan]' - Execute approved plans with integrations")
    print("  • 'reflect' - Analyze outcomes and learn from results")
    print("  • 'copilot' - Show detailed Co-Pilot mode help")
    
    print("\n🎯 Generation:")
    print("  • 'Generate some calls' - I'll suggest scenarios")
    print("  • 'Create 3 calls about angry customers'")
    print("  • 'Make transcripts about refinancing'")
    
    print("\n📊 Analysis:")
    print("  • 'Analyze recent calls'")
    print("  • 'Check compliance issues'")
    print("  • 'Review transcript CALL_123'")
    
    print("\n🔍 Search & Lists:")
    print("  • 'Search for payment issues'")
    print("  • 'Show recent transcripts'")
    print("  • 'List my files'")
    
    print("\n⚙️  System:")
    print("  • 'status' - Show system information")
    print("  • 'help' - Show this help")
    print("  • 'exit' - Quit the program")

def show_copilot_help():
    """Show detailed Co-Pilot mode help"""
    print("\n🤖 Co-Pilot Modes - Your AI Teammate")
    print("=" * 50)
    
    print("\n🧭 PLAN MODE:")
    print("   Create actionable plans with risk assessment and approvals")
    print("   Examples:")
    print("   • plan hardship assistance for struggling borrower")
    print("   • plan escrow shortage resolution workflow")
    print("   • plan loan modification pre-qualification")
    
    print("\n⚙️  EXECUTE MODE:")
    print("   Execute plans with downstream system integrations")
    print("   Examples:")
    print("   • execute payment plan setup")
    print("   • execute compliance review workflow")
    print("   • execute customer callback sequence")
    
    print("\n📊 REFLECT MODE:")
    print("   Analyze execution outcomes and continuous learning")
    print("   Examples:")
    print("   • reflect on recent plan executions")
    print("   • reflect on integration success rates")
    print("   • reflect")
    
    print("\n💡 Vision Integration:")
    print("   • Four-layer action plans (Borrower, Advisor, Supervisor, Leadership)")
    print("   • Real-time compliance monitoring")
    print("   • Automated downstream system triggers")
    print("   • Continuous learning and improvement")

def handle_plan_mode(user_request):
    """Handle Plan Mode requests"""
    
    try:
        print(f"🧭 Plan Mode: Creating plan for '{user_request}'")
        print("🔄 Analyzing request and generating actionable plan...\n")
        
        result = orchestrator.plan_mode(user_request)
        
        if result['status'] == 'ready_for_execution':
            print("📋 PLAN CREATED:")
            print("=" * 40)
            print(result['plan'])
            print("\n" + "=" * 40)
            print(f"✅ Plan ready (Confidence: {result['confidence']:.0%})")
            
            # Offer to execute
            execute_now = input("\n⚙️  Execute this plan now? (y/n): ").lower().strip()
            if execute_now.startswith('y'):
                print("\n🚀 Moving to Execute Mode...\n")
                handle_execute_mode_with_plan(result)
        else:
            print(f"❌ Plan creation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Plan Mode error: {e}")

def handle_execute_mode(user_input):
    """Handle Execute Mode requests"""
    
    try:
        # Check for recent plans to execute
        history = orchestrator.get_execution_history('PLAN')
        
        if not history:
            print("📋 No recent plans found. Creating a plan first...")
            plan_request = input("What would you like me to plan? ").strip()
            if plan_request:
                handle_plan_mode(plan_request)
            return
        
        # Show recent plans
        print("📋 Recent Plans:")
        for i, plan in enumerate(history[-3:], 1):  # Show last 3 plans
            timestamp = plan['timestamp'][:19].replace('T', ' ')
            print(f"  {i}. {plan['user_request'][:50]}... ({timestamp})")
        
        # Get user choice
        choice = input("\nWhich plan to execute? (number or describe new plan): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(history[-3:]):
            selected_plan = history[-(4-int(choice))]  # Reverse index
            handle_execute_mode_with_plan(selected_plan)
        else:
            # Create new plan
            print(f"\n🧭 Creating new plan for: {choice}")
            handle_plan_mode(choice)
            
    except Exception as e:
        print(f"❌ Execute Mode error: {e}")

def handle_execute_mode_with_plan(plan_data):
    """Execute a specific plan"""
    
    try:
        print(f"⚙️  Execute Mode: Implementing plan")
        print("🔄 Executing with downstream system integrations...\n")
        
        # Ask about auto-execution
        auto_exec = input("Enable auto-execution for low-risk items? (y/n): ").lower().strip()
        auto_execute = auto_exec.startswith('y')
        
        result = orchestrator.execute_mode(plan_data, auto_execute)
        
        if result['status'] in ['completed', 'partial_completion']:
            print("🎯 EXECUTION RESULTS:")
            print("=" * 40)
            
            integration_results = result.get('integration_results', {})
            executed_actions = integration_results.get('executed_actions', [])
            errors = integration_results.get('errors', [])
            
            if executed_actions:
                print("✅ Successfully executed:")
                for action in executed_actions:
                    action_type = action.get('trigger', action.get('type', 'Unknown'))
                    status = action.get('status', 'Unknown')
                    print(f"   • {action_type}: {status}")
            
            if errors:
                print("\n⚠️  Errors encountered:")
                for error in errors:
                    print(f"   • {error}")
            
            print(f"\n📊 Overall Status: {result['status']}")
            
            # Offer reflection
            reflect_now = input("\n📊 Reflect on this execution? (y/n): ").lower().strip()
            if reflect_now.startswith('y'):
                print("\n🔍 Moving to Reflect Mode...\n")
                handle_reflect_mode_with_result(result)
        else:
            print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Execution error: {e}")

def handle_reflect_mode(user_input):
    """Handle Reflect Mode requests"""
    
    try:
        # Check for recent executions to reflect on
        history = orchestrator.get_execution_history('EXECUTE')
        
        if not history:
            print("📊 No recent executions found to reflect on.")
            print("💡 Execute some plans first, then come back to reflect!")
            return
        
        # Show recent executions
        print("📊 Recent Executions:")
        for i, execution in enumerate(history[-3:], 1):  # Show last 3
            timestamp = execution['timestamp'][:19].replace('T', ' ')
            status = execution.get('status', 'unknown')
            print(f"  {i}. {timestamp} - Status: {status}")
        
        # Get user choice or reflect on all
        choice = input("\nReflect on which execution? (number or 'all'): ").strip()
        
        if choice.lower() == 'all':
            # Reflect on most recent execution
            selected_execution = history[-1]
        elif choice.isdigit() and 1 <= int(choice) <= len(history[-3:]):
            selected_execution = history[-(4-int(choice))]  # Reverse index
        else:
            selected_execution = history[-1]  # Default to most recent
        
        handle_reflect_mode_with_result(selected_execution)
        
    except Exception as e:
        print(f"❌ Reflect Mode error: {e}")

def handle_reflect_mode_with_result(execution_result):
    """Reflect on a specific execution result"""
    
    try:
        print("📊 Reflect Mode: Analyzing execution outcome")
        print("🔄 Gathering insights and lessons learned...\n")
        
        # Optional human feedback
        print("💭 Provide feedback on this execution (optional):")
        satisfaction = input("   Satisfaction (1-5): ").strip()
        improvements = input("   What could be improved: ").strip()
        
        human_feedback = {}
        if satisfaction.isdigit():
            human_feedback['satisfaction_score'] = int(satisfaction)
        if improvements:
            human_feedback['improvement_suggestions'] = improvements
        
        result = orchestrator.reflect_mode(execution_result, human_feedback if human_feedback else None)
        
        if result['status'] == 'completed':
            print("🔍 REFLECTION ANALYSIS:")
            print("=" * 40)
            print(result['reflection'])
            
            learning_updates = result.get('learning_updates', {})
            if learning_updates and learning_updates.get('total_feedback_items', 0) > 0:
                print("\n📈 LEARNING METRICS:")
                print(f"   Analysis Accuracy: {learning_updates.get('analysis_accuracy', 0):.0%}")
                print(f"   Integration Success: {learning_updates.get('integration_success_rate', 0):.0%}")
                
                recommendations = learning_updates.get('improvement_recommendations', [])
                if recommendations:
                    print("\n💡 Recommendations:")
                    for rec in recommendations:
                        print(f"   • {rec}")
        else:
            print(f"❌ Reflection failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Reflection error: {e}")

def handle_generation(user_input):
    """Handle generation requests"""
    
    try:
        generator = get_generator()
        
        # Check if user wants suggestions first
        if not any(char.isdigit() for char in user_input) and 'suggest' not in user_input.lower():
            # Ask if they want suggestions
            want_suggestions = input("\n💡 Would you like me to suggest some scenarios? (y/n): ").lower().strip()
            
            if want_suggestions.startswith('y'):
                print("\n🎯 Let me suggest some interesting scenarios...")
                
                suggestion_prompt = """Suggest 5-7 diverse MORTGAGE LOAN SERVICING call scenarios.
                
                Format as a clean numbered list with ONLY concise titles (2-4 words each):
                1. Escrow Shortage Confusion
                2. PMI Removal Request  
                3. ARM Rate Adjustment
                4. Payment Plan Setup
                5. Hardship Forbearance
                6. Payoff Quote Request
                7. Late Fee Dispute
                
                Focus on mortgage servicing topics: escrow, PMI, payments, modifications, etc.
                Make each title descriptive but brief. Include mix of routine/complex, different emotions, various outcomes."""
                
                response = run_agent_sync(generator, suggestion_prompt)
                display = response.format_display(
                    mode=settings.AGENT_DISPLAY_MODE,
                    override=settings.AGENT_NAME_OVERRIDE
                )
                print(display)
                
                choice = input("\nYour choice (number, description, or 'all'): ").strip()
                
                if choice.lower() == 'all':
                    user_input = "Generate one transcript for each suggested scenario"
                elif choice.isdigit():
                    user_input = f"Generate transcript for scenario {choice} from the suggestions above"
                else:
                    user_input = f"Generate transcript: {choice}"
        
        # Generate transcripts
        print(f"\n🔄 Generating transcripts...")
        response = run_agent_sync(generator, user_input)
        
        # Save the output
        transcript_id = storage.save_transcript(response.content, 
                                              metadata={"generated_from": user_input})
        
        print(f"\n✅ Generated and saved: {transcript_id}")
        print("\n📄 Preview:")
        print("-" * 50)
        
        # Show preview (first 500 characters) with agent display
        preview_content = response.content[:500]
        if len(response.content) > 500:
            preview_content += "\n... [truncated]"
            
        # Create preview response for display formatting
        preview_response = AgentResponse(preview_content, response.agent_name, response.agent_chain)
        display = preview_response.format_display(
            mode=settings.AGENT_DISPLAY_MODE,
            override=settings.AGENT_NAME_OVERRIDE
        )
        print(display)
        
        # Offer immediate analysis
        analyze_now = input("\n🔍 Analyze this transcript now? (y/n): ").lower().strip()
        if analyze_now.startswith('y'):
            print("\n📊 Running analysis...")
            handle_analysis(f"analyze {transcript_id}")
            
    except Exception as e:
        print(f"❌ Generation failed: {e}")

def handle_analysis(user_input):
    """Handle analysis requests"""
    
    try:
        analyzer = get_analyzer()
        
        # Extract transcript ID if mentioned
        parts = user_input.split()
        transcript_id = None
        
        for part in parts:
            if 'CALL_' in part.upper() or (part.isdigit() and len(part) >= 3):
                transcript_id = part.upper() if 'CALL_' in part.upper() else part
                break
        
        if not transcript_id and 'recent' not in user_input.lower() and 'all' not in user_input.lower():
            # Show recent transcripts for selection
            recent = storage.list_recent(5)
            if recent:
                print("\n📂 Recent Transcripts:")
                for i, t in enumerate(recent, 1):
                    print(f"  {i}. {t['id']}: {t['summary']}")
                
                choice = input("\nWhich one? (number or ID): ").strip()
                
                if choice.isdigit() and 1 <= int(choice) <= len(recent):
                    transcript_id = recent[int(choice) - 1]['id']
                else:
                    transcript_id = choice.upper() if 'CALL_' in choice.upper() else choice
            else:
                print("📭 No transcripts found. Generate some first!")
                return
        
        # Load and analyze transcript
        if transcript_id:
            transcript_data = storage.get_transcript_with_analysis(transcript_id)
            
            if not transcript_data:
                print(f"❌ Transcript '{transcript_id}' not found.")
                return
            
            if 'error' in transcript_data:
                print(f"❌ {transcript_data['error']}")
                if 'matches' in transcript_data:
                    print(f"   Available matches: {', '.join(transcript_data['matches'])}")
                return
            
            # Check if analysis already exists
            existing_analyses = transcript_data.get('analyses', [])
            if existing_analyses:
                use_existing = input(f"\n♻️  Existing analysis found. Use it? (y/n): ").lower().strip()
                if use_existing.startswith('y'):
                    print("\n📊 Existing Analysis:")
                    print("=" * 50)
                    print(existing_analyses[0]['content'])
                    return
            
            # Run new comprehensive multi-agent analysis
            print(f"\n🔄 Running comprehensive multi-agent analysis on {transcript_id}...")
            
            comprehensive_result = orchestrator.comprehensive_analysis(
                transcript_data['content'], 
                transcript_id
            )
            
            if comprehensive_result['status'] == 'completed':
                print("\n📊 Multi-Agent Analysis Results:")
                print("=" * 50)
                print(comprehensive_result['raw_analysis'])
                
                # Save analysis
                analysis_id = storage.save_analysis(transcript_id, comprehensive_result['raw_analysis'])
                print(f"\n💾 Analysis saved: {analysis_id}")
                
                # Show integration readiness
                if comprehensive_result.get('ready_for_integration'):
                    print(f"\n🔗 Analysis ready for downstream integration")
                    
                    # Offer to execute integrations
                    execute_integrations = input("\n⚙️  Execute downstream integrations now? (y/n): ").lower().strip()
                    if execute_integrations.startswith('y'):
                        integration_results = orchestrator.integration_layer.execute_integrations(
                            comprehensive_result['parsed_analysis']
                        )
                        print("\n🎯 Integration Results:")
                        print("=" * 30)
                        executed = integration_results.get('executed_actions', [])
                        errors = integration_results.get('errors', [])
                        
                        if executed:
                            print("✅ Executed actions:")
                            for action in executed:
                                print(f"   • {action.get('trigger', 'Action')}: {action.get('status', 'Done')}")
                        
                        if errors:
                            print("\n⚠️  Errors:")
                            for error in errors:
                                print(f"   • {error}")
            else:
                print(f"\n❌ Analysis failed: {comprehensive_result.get('error', 'Unknown error')}")
                # Fallback to traditional analysis
                print("🔄 Falling back to traditional analysis...")
                response = run_agent_sync(analyzer, f"Analyze this customer service call transcript thoroughly:\n\n{transcript_data['content']}")
                print("\n📊 Analysis Results:")
                print("=" * 50)
                
                # Display with formatting
                display = response.format_display(
                    mode=settings.AGENT_DISPLAY_MODE,
                    override=settings.AGENT_NAME_OVERRIDE
                )
                print(display)
                
                # Save analysis
                analysis_id = storage.save_analysis(transcript_id, response.content)
                print(f"\n💾 Analysis saved: {analysis_id}")
            
        else:
            # General analysis query
            print("\n🔄 Processing your request...")
            response = run_agent_sync(analyzer, user_input)
            print("\n📊 Response:")
            print("=" * 30)
            
            # Display with formatting
            display = response.format_display(
                mode=settings.AGENT_DISPLAY_MODE,
                override=settings.AGENT_NAME_OVERRIDE
            )
            print(display)
            
    except Exception as e:
        print(f"❌ Analysis failed: {e}")

def handle_search(user_input):
    """Handle search requests"""
    
    try:
        # Extract search query
        query_words = user_input.lower().replace('search', '').replace('find', '').replace('look', '').strip()
        
        if not query_words:
            query_words = input("🔍 What would you like to search for? ").strip()
        
        if not query_words:
            print("❌ Please provide a search query.")
            return
            
        print(f"\n🔍 Searching for: '{query_words}'")
        
        results = storage.search_transcripts(query_words, limit=10)
        
        if results:
            print(f"\n📋 Found {len(results)} matches:")
            for i, result in enumerate(results, 1):
                print(f"\n  {i}. {result['id']} ({result['created']})")
                print(f"     Context: {result['match_context']}")
        else:
            print("📭 No matches found.")
            
    except Exception as e:
        print(f"❌ Search failed: {e}")

def handle_list(user_input):
    """Handle list/show requests"""
    
    try:
        recent = storage.list_recent(10)
        
        if recent:
            print(f"\n📂 Recent Files:")
            for i, item in enumerate(recent, 1):
                icon = "📊" if item['type'] == 'analysis' else "📄"
                print(f"  {i}. {icon} {item['id']}")
                print(f"      {item['summary']}")
                print(f"      Created: {item['created'][:10]}")  # Just the date part
                print()
        else:
            print("📭 No files found. Generate some transcripts first!")
            
    except Exception as e:
        print(f"❌ Failed to list files: {e}")

def handle_status():
    """Show system status"""
    
    try:
        print(f"\n🤖 System Status:")
        print(f"   Model: {settings.OPENAI_MODEL}")
        print(f"   Handoffs: {'Enabled' if settings.ENABLE_HANDOFFS else 'Disabled'}")
        
        stats = storage.get_stats()
        if 'error' not in stats:
            print(f"\n📊 Storage Statistics:")
            print(f"   Path: {stats['storage_path']}")
            print(f"   Total Files: {stats['total_files']}")
            print(f"   Transcripts: {stats['transcripts']}")
            print(f"   Analyses: {stats['analyses']}")
            print(f"   Storage Used: {stats['total_size_mb']} MB")
        else:
            print(f"\n❌ Storage Error: {stats['error']}")
            
    except Exception as e:
        print(f"❌ Status check failed: {e}")

# CLI Commands for direct usage
@cli.command()
@click.option('--count', '-n', default=1, help='Number of transcripts to generate')
def generate(count):
    """Quick generation with suggestions"""
    if count > 1:
        handle_generation(f"generate {count} transcripts")
    else:
        handle_generation("generate")

@cli.command()
@click.argument('transcript_id', required=False)
def analyze(transcript_id):
    """Quick analysis of transcripts"""
    if transcript_id:
        handle_analysis(f"analyze {transcript_id}")
    else:
        handle_analysis("analyze recent")

@cli.command()
@click.argument('query', required=False)
def search(query):
    """Search transcripts"""
    if query:
        handle_search(f"search {query}")
    else:
        handle_search("search")

@cli.command()
def list():
    """List recent transcripts"""
    handle_list("list")

@cli.command()
def status():
    """Show system status"""
    handle_status()

@cli.command()
def chat():
    """Start interactive chat mode"""
    interactive_mode()

@cli.command()
@click.argument('request', required=False)
def plan(request):
    """Co-Pilot Plan Mode - Create actionable plans"""
    if request:
        handle_plan_mode(request)
    else:
        request = input("What would you like me to plan? ").strip()
        if request:
            handle_plan_mode(request)

@cli.command() 
@click.argument('description', required=False)
def execute(description):
    """Co-Pilot Execute Mode - Execute plans with integrations"""
    if description:
        handle_execute_mode(description)
    else:
        handle_execute_mode("")

@cli.command()
def reflect():
    """Co-Pilot Reflect Mode - Analyze outcomes and learn"""
    handle_reflect_mode("")

@cli.command()
def copilot():
    """Show Co-Pilot mode capabilities"""
    show_copilot_help()

@cli.command()
def commands():
    """Show available vision-aligned commands"""
    handler = VisionCommandHandler()
    print(handler.show_command_help())

if __name__ == '__main__':
    cli()