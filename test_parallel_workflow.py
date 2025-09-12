#!/usr/bin/env python3
"""Test script to verify parallel workflow implementation."""
import asyncio
import sys
from src.services.workflow_service import WorkflowService

async def test_parallel_processing():
    """Test the parallel processing implementation."""
    try:
        # Initialize workflow service
        workflow_service = WorkflowService("data/analytics_graph.db")
        
        # Test with a valid plan ID
        plan_id = "PLAN_ANALYSIS_CALL_B"
        
        print(f"Testing parallel extraction for plan: {plan_id}")
        
        # Time the operation
        import time
        start_time = time.time()
        
        # Run the extract operation
        workflows = await workflow_service.extract_all_workflows_from_plan(plan_id)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Successfully extracted {len(workflows)} workflows in {duration:.2f} seconds")
        
        # Print some details about the workflows
        workflow_types = {}
        for workflow in workflows:
            wtype = workflow.get('workflow_type', 'unknown')
            workflow_types[wtype] = workflow_types.get(wtype, 0) + 1
        
        print(f"Workflow breakdown: {workflow_types}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the async test
    success = asyncio.run(test_parallel_processing())
    sys.exit(0 if success else 1)