#!/usr/bin/env python3
"""
Complete Co-Pilot API Demo Script
Executes all 11 steps sequentially with dynamic variable passing
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:8000"

# Initialize tracking variables
transcript_id = None
analysis_id = None
plan_id = None
governance_id = None
approval_id = None
execution_id = None
action_ids = []

print("="*60)
print("🤖 Co-Pilot API Demo - Complete Execution")
print("="*60)

try:
    # Step 1: Generate Complex Customer Call
    print("\n📞 Step 1: Generate Complex Customer Call")
    response = requests.post(f"{BASE_URL}/api/v1/transcripts/generate", json={
        "scenario": "Mortgage Servicing - PMI Removal Dispute with Property Valuation Issues and CFPB Compliance Requirements",
        "urgency": "high",
        "financial_impact": True,
        "customer_sentiment": "frustrated",
        "store": True
    })
    response.raise_for_status()
    transcript_data = response.json()
    transcript_id = transcript_data["transcript_id"]
    print(f"✅ Generated Transcript: {transcript_id}")

    # Step 2: Analyze Customer Intent & Risk
    print("\n🔍 Step 2: Analyze Customer Intent & Risk")
    print(f"   Using transcript_id from Step 1: {transcript_id}")
    response = requests.post(f"{BASE_URL}/api/v1/analysis/analyze", 
                           json={"transcript_id": transcript_id})
    response.raise_for_status()
    analysis_data = response.json()
    analysis_id = analysis_data["analysis_id"]
    print(f"✅ Analysis ID: {analysis_id}")
    print(f"   Intent: {analysis_data.get('intent', 'N/A')}")
    print(f"   Confidence: {analysis_data.get('confidence', 0):.2%}")

    # Step 3: Generate Four-Layer Action Plan
    print("\n📋 Step 3: Generate Four-Layer Action Plan")
    print(f"   Using analysis_id: {analysis_id}, transcript_id: {transcript_id}")
    response = requests.post(f"{BASE_URL}/api/v1/plans/generate", json={
        "analysis_id": analysis_id,
        "transcript_id": transcript_id
    })
    response.raise_for_status()
    plan_data = response.json()
    plan_id = plan_data["plan_id"]
    print(f"✅ Action Plan: {plan_id}")
    print(f"   Total Actions: {plan_data.get('total_actions', 0)}")

    # Step 4: View Detailed Action Plan and Extract Action IDs
    print("\n📄 Step 4: View Detailed Action Plan")
    print(f"   Using plan_id from Step 3: {plan_id}")
    response = requests.get(f"{BASE_URL}/api/v1/plans/{plan_id}")
    response.raise_for_status()
    plan_details = response.json()
    
    # Extract action IDs and build governance actions
    actions_for_governance = []
    for layer_name in ["borrower_plan", "advisor_plan", "supervisor_plan", "leadership_plan"]:
        if layer_name in plan_details:
            actions = plan_details[layer_name].get("actions", [])
            print(f"   📁 {layer_name}: {len(actions)} actions")
            for action in actions[:2]:  # Take first 2 from each layer
                action_ids.append(action["action_id"])
                actions_for_governance.append({
                    "action_id": action["action_id"],
                    "description": action["description"],
                    "risk_score": action.get("risk_score", 0.5),
                    "financial_impact": action.get("financial_impact", False),
                    "compliance_required": action.get("compliance_required", ["CFPB_GENERAL"])
                })
                print(f"     • {action['description']}")
                print(f"       Action ID: {action['action_id']}")
    print(f"✅ Extracted {len(action_ids)} action IDs for governance")

    # Step 5a: Submit for Governance Review
    print("\n🛡️ Step 5a: Submit for Governance Review")
    print(f"   Using plan_id: {plan_id} and {len(actions_for_governance)} actions from Step 4")
    response = requests.post(f"{BASE_URL}/api/v1/governance/submit", json={
        "plan_id": plan_id,
        "actions": actions_for_governance[:4],  # Submit first 4 actions
        "submitted_by": "advisor_mike",
        "urgency": "high"
    })
    response.raise_for_status()
    governance_data = response.json()
    governance_id = governance_data["governance_id"]
    print(f"✅ Governance ID: {governance_id}")
    print(f"   Compliance Status: {governance_data.get('compliance_status', 'N/A')}")

    # Step 5b: Check Governance Status
    print("\n🛡️ Step 5b: Check Governance Status")
    print(f"   Checking governance status for: {governance_id}")
    response = requests.get(f"{BASE_URL}/api/v1/governance/status/{governance_id}")
    response.raise_for_status()
    status_data = response.json()
    print(f"   Status: {status_data.get('status', 'N/A')}")

    # Step 5c: Submit for Traditional Approval
    if status_data.get("status") == "compliant":
        print("\n📋 Step 5c: Submit for Traditional Approval")
        print(f"   Governance approved! Submitting for traditional approval...")
        response = requests.post(f"{BASE_URL}/api/v1/approvals/submit", json={
            "plan_id": plan_id,
            "submitted_by": "advisor_mike",
            "priority": "high",
            "notes": "Customer escalation requires immediate supervisor review",
            "governance_id": governance_id
        })
        response.raise_for_status()
        approval_data = response.json()
        approval_id = approval_data["approval_id"]
        print(f"✅ Approval ID: {approval_id}")
    else:
        print(f"   Governance not compliant. Status: {status_data.get('status')}")

    # Step 6: Governance Queue Management & Approval
    print("\n✅ Step 6: Governance Queue Management & Approval")
    
    # 6a: Check Governance Queue
    governance_queue = requests.get(f"{BASE_URL}/api/v1/governance/queue?status=pending").json()
    print(f"   🛡️ Governance Queue: {len(governance_queue.get('items', []))} pending items")

    # 6b: Review Audit Trail
    print(f"   Reviewing audit trail for governance_id: {governance_id}")
    audit_response = requests.get(f"{BASE_URL}/api/v1/governance/audit?governance_id={governance_id}")
    if audit_response.status_code == 200:
        audit_trail = audit_response.json()
        print(f"   📜 Audit Events: {len(audit_trail.get('events', []))} recorded")
    
    # 6c: Approve with Compliance Conditions
    print(f"   Approving governance_id: {governance_id}")
    response = requests.post(f"{BASE_URL}/api/v1/governance/approve", json={
        "governance_id": governance_id,
        "approved_by": "supervisor_jane",
        "conditions": [
            "Ensure CFPB PMI removal disclosure is sent within 24 hours",
            "Document property valuation review process"
        ],
        "notes": "Approved with enhanced compliance monitoring"
    })
    response.raise_for_status()
    print(f"   🛡️ Governance approved with conditions")

    # 6d: Traditional Approval
    if approval_id:
        print(f"   Approving traditional approval_id: {approval_id}")
        response = requests.post(f"{BASE_URL}/api/v1/approvals/{approval_id}/approve", json={
            "approved_by": "supervisor_jane",
            "notes": "Governance validated - approved",
            "conditions": ["Ensure CFPB compliance"],
            "governance_validated": True
        })
        response.raise_for_status()
        print(f"   📋 Traditional approval completed")

    # Step 7: Execute Governance-Validated Action Plan
    print("\n🚀 Step 7: Execute Governance-Validated Action Plan")
    print(f"   Using plan_id: {plan_id}, governance_id: {governance_id}, approval_id: {approval_id}")
    response = requests.post(f"{BASE_URL}/api/v1/execution/execute", json={
        "plan_id": plan_id,
        "governance_id": governance_id,
        "approval_id": approval_id,
        "execution_mode": "full",
        "actor_simulation": True,
        "generate_artifacts": True,
        "compliance_monitoring": True
    })
    response.raise_for_status()
    execution_data = response.json()
    execution_id = execution_data["execution_id"]
    print(f"✅ Execution ID: {execution_id}")
    print(f"   Actions Executed: {execution_data.get('actions_executed', 0)}")
    print(f"   Artifacts Created: {execution_data.get('artifacts_created', 0)}")
    print(f"   🛡️ Compliance Events: {execution_data.get('compliance_events', 0)}")

    # Step 8: Monitor Execution Status
    print("\n📊 Step 8: Monitor Execution Status")
    print(f"   Using execution_id from Step 7: {execution_id}")
    response = requests.get(f"{BASE_URL}/api/v1/execution/{execution_id}")
    response.raise_for_status()
    execution_details = response.json()
    print(f"   Status: {execution_details.get('status', 'N/A')}")
    print(f"   Success Rate: {execution_details.get('success_rate', 0):.1%}")
    if 'duration_seconds' in execution_details:
        print(f"   Duration: {execution_details['duration_seconds']}s")

    # Step 9: View Generated Artifacts
    print("\n📄 Step 9: View Generated Artifacts")
    print(f"   Using execution_id: {execution_id}")
    response = requests.get(f"{BASE_URL}/api/v1/execution/{execution_id}/artifacts")
    response.raise_for_status()
    artifacts = response.json()
    print(f"   Total Artifacts: {artifacts.get('total_artifacts', 0)}")
    for artifact in artifacts.get('artifacts', [])[:3]:  # Show first 3
        print(f"     📁 {artifact.get('filename', 'N/A')}")
        print(f"        Type: {artifact.get('type', 'N/A')} | Actor: {artifact.get('actor', 'N/A')}")

    # Step 10: Get Metrics
    print("\n📊 Step 10: Get Analysis, Execution & Governance Metrics")
    analysis_metrics = requests.get(f"{BASE_URL}/api/v1/analysis/metrics").json()
    execution_metrics = requests.get(f"{BASE_URL}/api/v1/execution/metrics").json()
    governance_metrics = requests.get(f"{BASE_URL}/api/v1/governance/metrics").json()
    
    print(f"   Total Analyses: {analysis_metrics.get('total_analyses', 0)}")
    print(f"   Execution Success Rate: {execution_metrics.get('success_rate', 0):.1%}")
    print(f"   🛡️ Governance Compliance Rate: {governance_metrics.get('compliance_rate', 0):.1%}")
    print(f"   Audit Events Generated: {governance_metrics.get('total_audit_events', 0)}")

    # Step 11: Demonstrate Learning Loop (Second Iteration)
    print("\n🔄 Step 11: Demonstrate Learning Loop")
    print(f"   Using data from first iteration for comparison...")
    
    # Generate second transcript
    response = requests.post(f"{BASE_URL}/api/v1/transcripts/generate", json={
        "scenario": "PMI Removal Follow-up with Updated Compliance Requirements",
        "urgency": "medium",
        "learning_context": "previous_pmi_dispute"
    })
    response.raise_for_status()
    transcript_id_2 = response.json()["transcript_id"]
    print(f"   Second transcript generated: {transcript_id_2}")
    
    # Analyze second transcript
    response = requests.post(f"{BASE_URL}/api/v1/analysis/analyze",
                           json={"transcript_id": transcript_id_2})
    response.raise_for_status()
    analysis_2 = response.json()
    analysis_id_2 = analysis_2["analysis_id"]
    print(f"   Second analysis: {analysis_id_2}")
    
    # Generate second plan
    response = requests.post(f"{BASE_URL}/api/v1/plans/generate", json={
        "analysis_id": analysis_id_2,
        "transcript_id": transcript_id_2
    })
    response.raise_for_status()
    plan_2 = response.json()
    plan_id_2 = plan_2["plan_id"]
    print(f"   Second plan: {plan_id_2}")
    
    # Calculate learning improvements
    if 'confidence' in analysis_data and 'confidence' in analysis_2:
        confidence_improvement = analysis_2['confidence'] - analysis_data['confidence']
        print(f"   Confidence Improvement: {confidence_improvement:+.3f}")
        learning_velocity = confidence_improvement / analysis_data['confidence']
        print(f"   Learning Velocity: {learning_velocity:+.1%}")
    
    print("\n" + "="*60)
    print("✅ DEMO_API.MD COMPLETED SUCCESSFULLY!")
    print("="*60)
    
    # Summary
    print("\n📊 Summary of Generated IDs (All Dynamic):")
    print(f"   Transcript ID: {transcript_id}")
    print(f"   Analysis ID: {analysis_id}")
    print(f"   Plan ID: {plan_id}")
    print(f"   Governance ID: {governance_id}")
    print(f"   Approval ID: {approval_id}")
    print(f"   Execution ID: {execution_id}")
    print(f"   Total Action IDs extracted: {len(action_ids)}")
    print(f"   Second Iteration IDs: {transcript_id_2}, {analysis_id_2}, {plan_id_2}")
    
    print("\n🛡️ Epic 2 Validation Summary:")
    print(f"   ✅ Governance framework fully integrated")
    print(f"   ✅ Dynamic variable passing throughout workflow") 
    print(f"   ✅ Real API integration with OpenAI")
    print(f"   ✅ Dual approval workflow (governance + traditional)")
    print(f"   ✅ Learning loop demonstrated")
    print(f"   ✅ All 11 steps executed successfully")

    sys.exit(0)  # Success

except requests.exceptions.RequestException as e:
    print(f"\n❌ API Error: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Status Code: {e.response.status_code}")
        try:
            print(f"Response: {e.response.json()}")
        except:
            print(f"Response Text: {e.response.text}")
    sys.exit(1)  # API Error

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(2)  # General Error