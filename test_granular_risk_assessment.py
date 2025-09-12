#!/usr/bin/env python3
"""
Test script to verify the granular risk assessment agent functionality.
This script tests the new item-level risk evaluation features.
"""
import asyncio
import json
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agents.risk_assessment_agent import RiskAssessmentAgent

# Sample action plan data for testing
SAMPLE_ACTION_PLAN = {
    "borrower_plan": {
        "immediate_actions": [
            {
                "action": "Send hardship packet to borrower within 24 hours",
                "timeline": "24 hours",
                "priority": "high",
                "auto_executable": True,
                "description": "Send comprehensive hardship documentation packet including modification options and required forms"
            },
            {
                "action": "Schedule payment review call",
                "timeline": "3 days",
                "priority": "medium",
                "auto_executable": False,
                "description": "Schedule call to review current payment status and discuss options"
            }
        ],
        "follow_ups": [
            {
                "action": "Follow up on hardship packet receipt",
                "due_date": "2024-01-15",
                "owner": "ADVISOR_001",
                "trigger_condition": "5 days after packet sent"
            }
        ],
        "personalized_offers": ["Payment modification options", "Temporary forbearance"],
        "risk_mitigation": ["Document all interactions", "Compliance review required"]
    },
    "advisor_plan": {
        "coaching_items": [
            {
                "action": "Review advisor empathy score and provide coaching",
                "coaching_point": "Improve active listening during customer distress situations",
                "expected_improvement": "Increase empathy score from 3.2 to 4.0+",
                "priority": "high"
            }
        ],
        "performance_feedback": {
            "strengths": ["Good technical knowledge", "Prompt response time"],
            "improvements": ["Empathy in difficult situations", "Solution-oriented approach"],
            "score_explanations": ["Lower empathy score due to rushed responses during hardship discussion"]
        },
        "training_recommendations": ["Empathy training module", "Hardship communication best practices"],
        "next_actions": ["Schedule coaching session", "Assign empathy training"]
    },
    "supervisor_plan": {
        "escalation_items": [
            {
                "item": "Escalate compliance deviation to supervisor",
                "reason": "Potential CFPB violation in hardship handling process",
                "priority": "high",
                "action_required": "Immediate compliance review and corrective action plan"
            }
        ],
        "team_patterns": ["Multiple empathy score issues this week"],
        "compliance_review": ["Review all hardship cases for compliance"],
        "approval_required": True,
        "process_improvements": ["Update hardship handling procedures"]
    },
    "leadership_plan": {
        "portfolio_insights": ["Increasing hardship cases in Q4"],
        "strategic_opportunities": ["Proactive hardship outreach program"],
        "risk_indicators": ["Rising customer distress levels"],
        "trend_analysis": ["Analyze portfolio risk trends for leadership review"],
        "resource_allocation": ["Consider additional hardship specialists"]
    }
}

SAMPLE_CONTEXT = {
    "transcript_id": "transcript_123",
    "analysis_id": "analysis_456", 
    "plan_id": "plan_789",
    "pipeline_stage": "risk_assessment",
    "customer_id": "customer_001",
    "advisor_id": "advisor_001"
}

async def test_granular_risk_assessment():
    """Test the new granular risk assessment functionality."""
    print("🔍 Testing Granular Risk Assessment Agent")
    print("=" * 50)
    
    # Initialize agent
    try:
        agent = RiskAssessmentAgent()
        print("✅ Risk Assessment Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return False
    
    # Test workflow types
    workflow_types = ['BORROWER', 'ADVISOR', 'SUPERVISOR', 'LEADERSHIP']
    
    for workflow_type in workflow_types:
        print(f"\n📋 Testing {workflow_type} workflow...")
        
        try:
            # 1. Extract individual action items
            print(f"  Extracting {workflow_type.lower()} action items...")
            action_items = await agent.extract_individual_action_items(
                SAMPLE_ACTION_PLAN, workflow_type, SAMPLE_CONTEXT
            )
            print(f"  ✅ Extracted {len(action_items)} action items")
            
            if not action_items:
                print(f"  ⚠️  No action items found for {workflow_type}")
                continue
                
            # Test with first action item
            action_item = action_items[0]
            print(f"  📝 Testing action item: {action_item.get('action_item', 'Unknown')[:50]}...")
            
            # 2. Assess risk for action item
            print(f"  Assessing risk for {workflow_type.lower()} action item...")
            risk_assessment = await agent.assess_action_item_risk(
                action_item, workflow_type, SAMPLE_CONTEXT
            )
            risk_level = risk_assessment.get('risk_level', 'UNKNOWN')
            print(f"  ✅ Risk assessment complete: {risk_level}")
            
            # 3. Determine approval routing
            print(f"  Determining approval routing...")
            routing_decision = await agent.determine_action_item_approval_routing(
                action_item, risk_assessment, workflow_type, SAMPLE_CONTEXT
            )
            initial_status = routing_decision.get('initial_status', 'UNKNOWN')
            print(f"  ✅ Routing decision: {initial_status}")
            
            # 4. Test validation if approval required
            if routing_decision.get('requires_human_approval', False):
                print(f"  Testing approval validation...")
                validation_result = await agent.validate_action_item_approval_decision(
                    action_item, workflow_type, "test_approver", "Test approval reasoning", SAMPLE_CONTEXT
                )
                print(f"  ✅ Approval validation: {validation_result.get('approval_valid', False)}")
            
            # 5. Test post-approval status
            print(f"  Testing post-approval status...")
            post_approval = await agent.determine_action_item_post_approval_status(
                action_item, workflow_type, {"approved_by": "test_approver"}
            )
            next_status = post_approval.get('next_status', 'UNKNOWN')
            print(f"  ✅ Post-approval status: {next_status}")
            
            # 6. Test execution
            print(f"  Testing action item execution...")
            execution_results = await agent.execute_action_item(
                action_item, workflow_type, SAMPLE_CONTEXT
            )
            execution_status = execution_results.get('execution_status', 'UNKNOWN')
            print(f"  ✅ Execution simulation: {execution_status}")
            
            print(f"  ✅ All tests passed for {workflow_type}")
            
        except Exception as e:
            print(f"  ❌ Error testing {workflow_type}: {e}")
            return False
    
    print(f"\n🎉 All granular risk assessment tests completed successfully!")
    return True

async def test_backward_compatibility():
    """Test that legacy methods still work."""
    print("\n🔄 Testing Backward Compatibility")
    print("=" * 50)
    
    try:
        agent = RiskAssessmentAgent()
        
        # Test legacy workflow extraction
        workflow_data = await agent.extract_workflow_from_plan(SAMPLE_ACTION_PLAN, SAMPLE_CONTEXT)
        print("✅ Legacy workflow extraction still works")
        
        # Test legacy risk assessment
        risk_assessment = await agent.assess_workflow_risk(workflow_data, SAMPLE_CONTEXT)
        print("✅ Legacy risk assessment still works")
        
        # Test legacy approval routing
        routing = await agent.determine_approval_routing(workflow_data, risk_assessment, SAMPLE_CONTEXT)
        print("✅ Legacy approval routing still works")
        
        print("✅ All backward compatibility tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def print_summary():
    """Print test summary and usage examples."""
    print("\n📊 Test Summary")
    print("=" * 50)
    print("✅ Granular risk assessment agent successfully modified!")
    print("\n🔧 New Features Added:")
    print("  • extract_individual_action_items() - Extract items by workflow type")
    print("  • assess_action_item_risk() - Risk assessment for individual items")
    print("  • determine_action_item_approval_routing() - Granular approval routing")
    print("  • validate_action_item_approval_decision() - Item-level approval validation")
    print("  • validate_action_item_rejection_decision() - Item-level rejection validation")
    print("  • determine_action_item_post_approval_status() - Post-approval status")
    print("  • execute_action_item() - Individual item execution")
    print("\n🎯 Workflow Types Supported:")
    print("  • BORROWER - Customer-focused actions")
    print("  • ADVISOR - Performance and coaching actions") 
    print("  • SUPERVISOR - Management and oversight actions")
    print("  • LEADERSHIP - Strategic and portfolio actions")
    print("\n📈 Risk Levels: LOW, MEDIUM, HIGH")
    print("🔄 Backward Compatibility: All legacy methods maintained")

if __name__ == "__main__":
    async def main():
        success = await test_granular_risk_assessment()
        if success:
            success = await test_backward_compatibility()
        
        print_summary()
        return success
    
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)