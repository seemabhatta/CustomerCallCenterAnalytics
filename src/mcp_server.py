"""
MCP Server for Customer Call Center Analytics
Provides tools for analyzing call transcripts, generating insights, and managing call center data.
"""

import asyncio
from typing import Any, Optional, List, Dict
# from contextual import contextual_search  # Package not available
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from .storage import get_storage
from .agents import get_generator, get_analyzer, get_orchestrator
from agents import Runner


class GenerateTranscriptsArgs(BaseModel):
    """Arguments for generating call transcripts"""
    scenario: str
    count: Optional[int] = 1


class AnalyzeTranscriptArgs(BaseModel):
    """Arguments for analyzing a transcript"""
    transcript_id: Optional[str] = None
    transcript_content: Optional[str] = None


class SearchTranscriptsArgs(BaseModel):
    """Arguments for searching transcripts"""
    query: str
    limit: Optional[int] = 10


class ListTranscriptsArgs(BaseModel):
    """Arguments for listing transcripts"""
    limit: Optional[int] = 10


class PlanModeArgs(BaseModel):
    """Arguments for plan mode"""
    request: str


class ExecuteModeArgs(BaseModel):
    """Arguments for execute mode"""
    plan_id: Optional[str] = None
    auto_execute: bool = False


# Initialize MCP server
mcp = FastMCP("Customer Call Center Analytics")

# Initialize components
storage = get_storage()


@mcp.tool()
async def generate_transcripts(args: GenerateTranscriptsArgs) -> str:
    """Generate realistic call center transcripts based on scenarios"""
    try:
        generator = get_generator()
        
        # Create generation prompt
        prompt = f"Generate {args.count} realistic mortgage loan servicing call transcript(s) for: {args.scenario}"
        
        # Run agent synchronously in thread pool
        def run_sync():
            return Runner.run_sync(generator, prompt)
        
        result = await asyncio.get_event_loop().run_in_executor(None, run_sync)
        
        # Save transcript
        transcript_id = storage.save_transcript(
            result.final_output,
            metadata={"generated_from": args.scenario, "count": args.count}
        )
        
        return f"Generated transcript saved as {transcript_id}:\n\n{result.final_output[:500]}..."
        
    except Exception as e:
        return f"Error generating transcripts: {str(e)}"


@mcp.tool()
async def analyze_transcript(args: AnalyzeTranscriptArgs) -> str:
    """Analyze a call transcript for insights, compliance, and action items"""
    try:
        analyzer = get_analyzer()
        orchestrator = get_orchestrator()
        
        # Get transcript content
        if args.transcript_id:
            transcript_data = storage.get_transcript_with_analysis(args.transcript_id)
            if not transcript_data or 'error' in transcript_data:
                return f"Transcript {args.transcript_id} not found"
            content = transcript_data['content']
        elif args.transcript_content:
            content = args.transcript_content
            args.transcript_id = "TEMP_ANALYSIS"
        else:
            return "Either transcript_id or transcript_content must be provided"
        
        # Run comprehensive multi-agent analysis
        def run_analysis():
            return orchestrator.comprehensive_analysis(content, args.transcript_id)
        
        result = await asyncio.get_event_loop().run_in_executor(None, run_analysis)
        
        if result['status'] == 'completed':
            # Save analysis if we have a real transcript ID
            if args.transcript_id != "TEMP_ANALYSIS":
                analysis_id = storage.save_analysis(args.transcript_id, result['raw_analysis'])
                return f"Analysis saved as {analysis_id}:\n\n{result['raw_analysis']}"
            else:
                return result['raw_analysis']
        else:
            return f"Analysis failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"Error analyzing transcript: {str(e)}"


@mcp.tool()
async def search_transcripts(args: SearchTranscriptsArgs) -> str:
    """Search through call transcripts using natural language queries"""
    try:
        results = storage.search_transcripts(args.query, limit=args.limit)
        
        if not results:
            return f"No transcripts found matching: {args.query}"
        
        response = f"Found {len(results)} matches for '{args.query}':\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"{i}. {result['id']} ({result['created']})\n"
            response += f"   Context: {result['match_context']}\n\n"
        
        return response
        
    except Exception as e:
        return f"Error searching transcripts: {str(e)}"


@mcp.tool()
async def list_transcripts(args: ListTranscriptsArgs) -> str:
    """List recent call transcripts and analyses"""
    try:
        recent = storage.list_recent(args.limit)
        
        if not recent:
            return "No transcripts found"
        
        response = f"Recent {len(recent)} items:\n\n"
        
        for i, item in enumerate(recent, 1):
            icon = "📊" if item['type'] == 'analysis' else "📄"
            response += f"{i}. {icon} {item['id']}\n"
            response += f"   {item['summary']}\n"
            response += f"   Created: {item['created'][:10]}\n\n"
        
        return response
        
    except Exception as e:
        return f"Error listing transcripts: {str(e)}"


@mcp.tool()
async def plan_mode(args: PlanModeArgs) -> str:
    """Create actionable plans using Co-Pilot planning mode"""
    try:
        orchestrator = get_orchestrator()
        
        def run_plan():
            return orchestrator.plan_mode(args.request)
        
        result = await asyncio.get_event_loop().run_in_executor(None, run_plan)
        
        if result['status'] == 'ready_for_execution':
            response = f"Plan created (Confidence: {result['confidence']:.0%}):\n\n"
            response += result['plan']
            return response
        else:
            return f"Plan creation failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"Error in plan mode: {str(e)}"


@mcp.tool()
async def execute_mode(args: ExecuteModeArgs) -> str:
    """Execute plans with downstream system integrations"""
    try:
        orchestrator = get_orchestrator()
        
        # Get plan to execute
        if args.plan_id:
            # Get specific plan from history
            history = orchestrator.get_execution_history('PLAN')
            plan_data = None
            for plan in history:
                if plan.get('id') == args.plan_id:
                    plan_data = plan
                    break
            
            if not plan_data:
                return f"Plan {args.plan_id} not found"
        else:
            # Get most recent plan
            history = orchestrator.get_execution_history('PLAN')
            if not history:
                return "No plans available for execution. Create a plan first."
            plan_data = history[-1]
        
        def run_execute():
            return orchestrator.execute_mode(plan_data, args.auto_execute)
        
        result = await asyncio.get_event_loop().run_in_executor(None, run_execute)
        
        if result['status'] in ['completed', 'partial_completion']:
            response = "Execution Results:\n\n"
            
            integration_results = result.get('integration_results', {})
            executed_actions = integration_results.get('executed_actions', [])
            errors = integration_results.get('errors', [])
            
            if executed_actions:
                response += "✅ Successfully executed:\n"
                for action in executed_actions:
                    action_type = action.get('trigger', action.get('type', 'Unknown'))
                    status = action.get('status', 'Unknown')
                    response += f"   • {action_type}: {status}\n"
            
            if errors:
                response += "\n⚠️ Errors encountered:\n"
                for error in errors:
                    response += f"   • {error}\n"
            
            response += f"\nOverall Status: {result['status']}"
            return response
        else:
            return f"Execution failed: {result.get('error', 'Unknown error')}"
            
    except Exception as e:
        return f"Error in execute mode: {str(e)}"


@mcp.tool()
async def get_system_status() -> str:
    """Get system status and statistics"""
    try:
        from .config import settings
        
        response = "System Status:\n\n"
        response += f"Model: {settings.OPENAI_MODEL}\n"
        response += f"Handoffs: {'Enabled' if settings.ENABLE_HANDOFFS else 'Disabled'}\n"
        
        stats = storage.get_stats()
        if 'error' not in stats:
            response += f"\nStorage Statistics:\n"
            response += f"Path: {stats['storage_path']}\n"
            response += f"Total Files: {stats['total_files']}\n"
            response += f"Transcripts: {stats['transcripts']}\n"
            response += f"Analyses: {stats['analyses']}\n"
            response += f"Storage Used: {stats['total_size_mb']} MB\n"
        else:
            response += f"\nStorage Error: {stats['error']}\n"
        
        return response
        
    except Exception as e:
        return f"Error getting system status: {str(e)}"


# Contextual search support (simplified version)
async def search_call_center_data(query: str) -> List[Dict[str, Any]]:
    """Search call center data contextually"""
    try:
        results = storage.search_transcripts(query, limit=20)
        return [
            {
                "title": result['id'],
                "content": result['match_context'],
                "metadata": {
                    "created": result['created'],
                    "type": "call_transcript"
                }
            }
            for result in results
        ]
    except Exception:
        return []


def run_mcp_server(host: str = "localhost", port: int = 8000):
    """Run the MCP server"""
    import uvicorn
    uvicorn.run(mcp.app, host=host, port=port)


if __name__ == "__main__":
    run_mcp_server()