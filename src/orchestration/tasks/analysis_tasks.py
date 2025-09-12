"""
Analysis tasks for orchestration pipeline
NO FALLBACK LOGIC - fails fast on any errors
"""
from typing import Dict, Any
from prefect import task
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))


@task(name="generate-analysis", retries=0, task_run_name="Analysis for {transcript_id}")
async def generate_analysis_task(transcript_id: str) -> Dict[str, Any]:
    """
    Generate analysis from transcript using LLM agent.
    NO FALLBACK - fails fast if analysis cannot be generated.
    
    Args:
        transcript_id: Transcript ID to analyze
        
    Returns:
        Analysis data with ID
        
    Raises:
        Exception: If analysis generation fails (NO FALLBACK)
    """
    try:
        from src.services.analysis_service import AnalysisService
        
        # Initialize service with required parameters
        service = AnalysisService(
            api_key=os.getenv("OPENAI_API_KEY"),
            db_path="data/call_center.db"
        )
        
        # Generate analysis
        analysis = await service.create_analysis(transcript_id)
        
        if not analysis:
            raise ValueError(f"Analysis generation returned empty result for {transcript_id}")
        
        return analysis
        
    except Exception as e:
        # NO FALLBACK - fail immediately
        raise Exception(f"Analysis generation failed: {e}")


@task(name="validate-analysis", retries=0)
async def validate_analysis_task(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate analysis has required fields.
    NO FALLBACK - fails fast if validation fails.
    
    Args:
        analysis: Analysis data to validate
        
    Returns:
        Validated analysis data
        
    Raises:
        ValueError: If analysis is invalid (NO FALLBACK)
    """
    required_fields = ["id", "transcript_id", "status"]
    
    for field in required_fields:
        if field not in analysis:
            raise ValueError(f"Analysis missing required field: {field}")
    
    if analysis.get("status") != "completed":
        raise ValueError(f"Analysis not completed: {analysis.get('status')}")
    
    return analysis