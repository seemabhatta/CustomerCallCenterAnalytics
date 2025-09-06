import click
import sys
from agents import Runner
from .agents import get_generator, get_analyzer
from .storage import get_storage
from .config import settings

# Initialize components
storage = get_storage()

def print_header():
    """Print welcome header"""
    print("🤖 Customer Call Center Analytics - AI-Powered Analysis")
    print("=" * 60)

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Customer Call Center Analytics - AI-Powered Analysis System"""
    if ctx.invoked_subcommand is None:
        # No command = interactive mode
        interactive_mode()

def interactive_mode():
    """Natural language interface"""
    print_header()
    print("\n💬 Interactive Mode - Just tell me what you want!")
    print("\nExamples:")
    print("  • Generate some transcripts")
    print("  • Analyze recent calls")
    print("  • Show me compliance issues")
    print("  • Create 5 calls about rate increases")
    print("  • Search for angry customers")
    print("\nType 'help' for more info or 'exit' to quit.\n")
    
    while True:
        try:
            user_input = input("> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("👋 Goodbye!")
                break
                
            if user_input.lower() in ['help', '?']:
                show_help()
                continue
                
            # Route based on keywords
            if any(word in user_input.lower() for word in ['generate', 'create', 'make']):
                handle_generation(user_input)
            elif any(word in user_input.lower() for word in ['analyze', 'review', 'check', 'examine']):
                handle_analysis(user_input)
            elif any(word in user_input.lower() for word in ['search', 'find', 'look']):
                handle_search(user_input)
            elif any(word in user_input.lower() for word in ['list', 'show', 'recent']):
                handle_list(user_input)
            elif user_input.lower() in ['status', 'stats']:
                handle_status()
            else:
                # Default to analysis for general questions
                print("🤔 I'll analyze that for you...\n")
                try:
                    analyzer = get_analyzer()
                    result = Runner.run_sync(analyzer, user_input)
                    print(result.final_output)
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
                
                suggestion_prompt = """Suggest 5-7 diverse customer service call scenarios for mortgage/loan servicing.
                
                Format as a clean numbered list with ONLY concise titles (2-4 words each):
                1. Escrow Shortage Confusion
                2. Hurricane Damage Claim  
                3. Rate Increase Complaint
                4. First-Time Buyer Questions
                5. Payment Processing Error
                6. Loan Modification Request
                7. Insurance Removal Inquiry
                
                Make each title descriptive but brief. Include mix of routine/complex, different emotions, various outcomes."""
                
                result = Runner.run_sync(generator, suggestion_prompt)
                print(result.final_output)
                
                choice = input("\nYour choice (number, description, or 'all'): ").strip()
                
                if choice.lower() == 'all':
                    user_input = "Generate one transcript for each suggested scenario"
                elif choice.isdigit():
                    user_input = f"Generate transcript for scenario {choice} from the suggestions above"
                else:
                    user_input = f"Generate transcript: {choice}"
        
        # Generate transcripts
        print(f"\n🔄 Generating transcripts...")
        result = Runner.run_sync(generator, user_input)
        
        # Save the output
        transcript_id = storage.save_transcript(result.final_output, 
                                              metadata={"generated_from": user_input})
        
        print(f"\n✅ Generated and saved: {transcript_id}")
        print("\n📄 Preview:")
        print("-" * 50)
        
        # Show preview (first 500 characters)
        preview = result.final_output[:500]
        if len(result.final_output) > 500:
            preview += "\n... [truncated]"
        print(preview)
        
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
            
            # Run new analysis
            print(f"\n🔄 Analyzing transcript {transcript_id}...")
            
            analysis_prompt = f"Analyze this customer service call transcript thoroughly:\n\n{transcript_data['content']}"
            result = Runner.run_sync(analyzer, analysis_prompt)
            
            print("\n📊 Analysis Results:")
            print("=" * 50)
            print(result.final_output)
            
            # Save analysis
            analysis_id = storage.save_analysis(transcript_id, result.final_output)
            print(f"\n💾 Analysis saved: {analysis_id}")
            
        else:
            # General analysis query
            print("\n🔄 Processing your request...")
            result = Runner.run_sync(analyzer, user_input)
            print("\n📊 Response:")
            print("=" * 30)
            print(result.final_output)
            
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

if __name__ == '__main__':
    cli()