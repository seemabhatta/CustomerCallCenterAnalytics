"""
Function tools for the Customer Call Center Analytics system.
Provides essential tools for the router agent to interact with the system.
"""

from agents import function_tool, Runner
from typing import Optional
import json

from .storage import get_storage
from .agents import get_generator, get_analyzer


storage = get_storage()


@function_tool
def generate_transcript(request: str) -> str:
    """Generate call transcript based on request"""
    try:
        generator = get_generator()
        result = Runner.run_sync(generator, request)
        
        # Save the transcript
        transcript_id = storage.save_transcript(
            result.final_output,
            metadata={"generated_from": request}
        )
        
        # Return preview with ID
        preview = result.final_output[:500]
        if len(result.final_output) > 500:
            preview += "\n... [truncated]"
            
        return f"Generated and saved as {transcript_id}.\n\nPreview:\n{preview}"
        
    except Exception as e:
        return f"Error generating transcript: {str(e)}"


@function_tool
def analyze_transcript(request: str) -> str:
    """Analyze transcript - handles 'recent', specific ID, or general request"""
    try:
        analyzer = get_analyzer()
        
        # Handle different types of analysis requests
        if "recent" in request.lower() or not request.strip():
            # Analyze most recent transcript
            recent = storage.list_recent(1)
            if not recent:
                return "No transcripts found. Generate some transcripts first!"
                
            transcript_data = storage.get_transcript_with_analysis(recent[0]['id'])
            if 'error' in transcript_data:
                return f"Error loading transcript: {transcript_data['error']}"
                
            result = Runner.run_sync(analyzer, f"Analyze this customer service call transcript:\n\n{transcript_data['content']}")
            
            # Save analysis
            analysis_id = storage.save_analysis(recent[0]['id'], result.final_output)
            
            return f"Analysis of {recent[0]['id']} (saved as {analysis_id}):\n\n{result.final_output}"
            
        elif "CALL_" in request.upper():
            # Extract transcript ID from request
            words = request.split()
            transcript_id = None
            for word in words:
                if "CALL_" in word.upper():
                    transcript_id = word.upper()
                    break
                    
            if transcript_id:
                transcript_data = storage.get_transcript_with_analysis(transcript_id)
                if 'error' in transcript_data:
                    return f"Transcript {transcript_id} not found."
                    
                result = Runner.run_sync(analyzer, f"Analyze this customer service call transcript:\n\n{transcript_data['content']}")
                analysis_id = storage.save_analysis(transcript_id, result.final_output)
                
                return f"Analysis of {transcript_id} (saved as {analysis_id}):\n\n{result.final_output}"
        
        # General analysis query - let analyzer handle it
        result = Runner.run_sync(analyzer, request)
        return result.final_output
        
    except Exception as e:
        return f"Error analyzing transcript: {str(e)}"


@function_tool
def search_data(query: str) -> str:
    """Search transcripts database"""
    try:
        results = storage.search_transcripts(query, limit=10)
        
        if not results:
            return f"No results found for '{query}'"
            
        output = f"Found {len(results)} matches for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            output += f"{i}. {result['id']} ({result['created']})\n"
            output += f"   Context: {result['match_context']}\n\n"
            
        return output
        
    except Exception as e:
        return f"Error searching data: {str(e)}"


@function_tool
def list_recent_items(limit: int = 10) -> str:
    """List recent transcripts and analyses"""
    try:
        recent = storage.list_recent(limit)
        
        if not recent:
            return "No items found. Generate some transcripts first!"
            
        output = f"Recent {len(recent)} items:\n\n"
        
        for i, item in enumerate(recent, 1):
            icon = "📊" if item['type'] == 'analysis' else "📄"
            output += f"{i}. {icon} {item['id']}\n"
            output += f"   {item['summary']}\n"
            output += f"   Created: {item['created'][:10]}\n\n"
            
        return output
        
    except Exception as e:
        return f"Error listing items: {str(e)}"


@function_tool
def get_system_status() -> str:
    """Get system status and statistics"""
    try:
        from .config import settings
        
        stats = storage.get_stats()
        
        output = "System Status:\n\n"
        output += f"Model: {settings.OPENAI_MODEL}\n"
        output += f"Handoffs: {'Enabled' if settings.ENABLE_HANDOFFS else 'Disabled'}\n"
        
        if 'error' not in stats:
            output += f"\nStorage Statistics:\n"
            output += f"Path: {stats['storage_path']}\n"
            output += f"Total Files: {stats['total_files']}\n"
            output += f"Transcripts: {stats['transcripts']}\n"
            output += f"Analyses: {stats['analyses']}\n"
            output += f"Storage Used: {stats['total_size_mb']} MB\n"
        else:
            output += f"\nStorage Error: {stats['error']}\n"
            
        return output
        
    except Exception as e:
        return f"Error getting system status: {str(e)}"