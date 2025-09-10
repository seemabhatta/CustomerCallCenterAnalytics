# 🤖 Co-Pilot API Demo - Intelligent Teammate in Action

## 📋 LLM Execution Instructions

**FOR LLM AGENTS**: This demo is designed to be executed sequentially. Each step dynamically passes its outputs to subsequent steps. When executing:

1. **Execute steps in order** - Each step depends on variables from previous steps
2. **Track all variables** - The Python examples initialize and maintain variables throughout:
   - `transcript_id` (from Step 1)
   - `analysis_id` (from Step 2) 
   - `plan_id` (from Step 3)
   - `action_ids[]` (extracted in Step 4)
   - `governance_id` (from Step 5a)
   - `approval_id` (from Step 5c)
   - `execution_id` (from Step 7)
3. **No hardcoded values** - All IDs and data are extracted from actual API responses
4. **Error handling** - If any step fails, report the error and stop execution
5. **Output verification** - Each step prints the variables it will pass to next steps

> **Prerequisites:** 
> 1. **OpenAI API Key Required**: Set `OPENAI_API_KEY` environment variable with valid API key
> 2. Activate virtual environment: `source venv/bin/activate`  
> 3. Ensure the backend is running: `./start_services.sh`
> 4. **FastAPI Server Running**: Accessible at `http://localhost:8000`
>
> **⚠️ NO FALLBACK Policy**: System requires proper OpenAI API integration. No mock/fallback responses.

---

## 🎯 Co-Pilot Vision: Three Modes in Action

This demo showcases the **Intelligent Teammate** vision from [docs/01. vision_v2.md](docs/01.%20vision_v2.md), demonstrating how the Co-Pilot operates in three collaborative modes:

### 🧭 **Plan Mode**: Real-Time Strategy
- Co-Pilot instantly proposes action steps during customer interactions
- Risk assessment with predictive outcomes and approval routing
- Four-layer planning (Borrower → Advisor → Supervisor → Leadership)

### ⚙️ **Execute Mode**: Background Co-Execution  
- Automated execution of approved actions while advisor focuses on customer
- Actor simulation: emails, callbacks, CRM updates, document generation
- Compliance-aware execution with human oversight

### 📊 **Reflect Mode**: Continuous Learning
- Post-call analysis with Observer Agent evaluation
- Performance feedback and coaching opportunities
- Learning loop that improves future interactions

---

## 🏗️ Architecture Flow

Following the [High-Level Architecture](docs/02.%20HighLevelArchitecture.png):

```
Generator Agent → Analyzer Agent → Decision Agent → Execution Agent
      ↓              ↓              ↓              ↓
   Store Call    Store Analysis  Route Actions   Generate Artifacts
                                      ↓              ↓
                            Approval Workflow  Observer Agent (Feedback Loop)
```

---

## 🔧 API Foundation

### FastAPI Documentation
- **Interactive Swagger UI**: http://localhost:8000/docs
- **OpenAPI Schema**: http://localhost:8000/openapi.json
- **Total Endpoints**: 32 routes (20 new API v1 endpoints + 12 existing)

### Authentication
All API calls require the server to have valid OpenAI API key configuration. No additional API authentication required for demo purposes.

---

## 🎬 Step-by-Step Co-Pilot Demo

### Expected Outcomes Summary
Upon completion, you should have:
- [ ] 1 complex mortgage servicing call transcript generated
- [ ] 1 comprehensive AI analysis with risk scoring
- [ ] 1 four-layer action plan (~12 actions across all layers)
- [ ] Multi-level approval workflow demonstrated
- [ ] 1 execution with 5-8 artifacts generated
- [ ] Observer Agent evaluation and feedback
- [ ] Learning loop demonstration with measurable improvement

---

## Step 1. Generate Complex Customer Call (Generator Agent)

**Co-Pilot Mode**: 🧭 **Plan Mode** - Creating realistic scenario for analysis

**Purpose**: Generate a high-complexity mortgage servicing call that will trigger comprehensive action planning.

### API Call (curl):
```bash
curl -X POST "http://localhost:8000/api/v1/transcripts/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "scenario": "Mortgage Servicing - PMI Removal Dispute with Property Valuation Issues and CFPB Compliance Requirements",
       "urgency": "high",
       "financial_impact": true,
       "customer_sentiment": "frustrated",
       "store": true
     }'
```

### Python SDK Example (OpenAI Responses API Format):
```python
import requests
import json

# Initialize variables for tracking throughout the demo
transcript_id = None
analysis_id = None
plan_id = None
governance_id = None
approval_id = None
execution_id = None
action_ids = []  # Will store action IDs from plan generation

# Step 1: Generate transcript
response = requests.post(
    "http://localhost:8000/api/v1/transcripts/generate",
    json={
        "scenario": "Mortgage Servicing - PMI Removal Dispute with Property Valuation Issues and CFPB Compliance Requirements",
        "urgency": "high",
        "financial_impact": true,
        "customer_sentiment": "frustrated",
        "store": true
    }
)

transcript_data = response.json()
transcript_id = transcript_data["transcript_id"]
print(f"Generated Transcript: {transcript_id}")
print(f"Storing transcript_id for next steps: {transcript_id}")
```

### Expected Response:
```json
{
  "success": true,
  "transcript_id": "transcript_20241201_001",
  "customer_id": "CUST_2024_001",
  "scenario": "PMI Removal Dispute with Property Valuation Issues",
  "message_count": 18,
  "stored": true,
  "urgency": "high",
  "financial_impact": true
}
```

### Success Indicators:
- ✅ Response contains `"success": true`
- ✅ Transcript ID format: `transcript_YYYYMMDD_XXX`
- ✅ High message count (15-20 messages)
- ✅ Stored in database successfully

### Track Variable:
```bash
export TRANSCRIPT_ID="transcript_20241201_001"
```

---

## Step 2. Analyze Customer Intent & Risk (Analyzer Agent)

**Co-Pilot Mode**: 🧭 **Plan Mode** - Real-time sentiment and risk assessment

**Purpose**: Extract customer intent, emotional journey, and risk factors using AI analysis.

### API Call (curl):
```bash
curl -X POST "http://localhost:8000/api/v1/analysis/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "transcript_id": "'$TRANSCRIPT_ID'"
     }'
```

### Python SDK Example:
```python
# Step 2: Analyze transcript using ID from previous step
print(f"\nUsing transcript_id from Step 1: {transcript_id}")

response = requests.post(
    "http://localhost:8000/api/v1/analysis/analyze",
    json={"transcript_id": transcript_id}  # Using variable from Step 1
)

analysis_data = response.json()
analysis_id = analysis_data["analysis_id"]
print(f"Analysis ID: {analysis_id}")
print(f"Customer Intent: {analysis_data['intent']}")
print(f"Sentiment Journey: {analysis_data['sentiment']}")
print(f"Urgency Level: {analysis_data['urgency']}")
print(f"Confidence Score: {analysis_data['confidence']}")
print(f"Storing analysis_id for next steps: {analysis_id}")
```

### Expected Response:
```json
{
  "analysis_id": "analysis_20241201_001",
  "intent": "PMI Removal Assistance",
  "urgency": "high",
  "sentiment": "frustrated → concerned",
  "confidence": 0.89,
  "risk_scores": {
    "delinquency": 0.34,
    "churn": 0.72,
    "complaint": 0.81,
    "refinance": 0.45
  }
}
```

### Success Indicators:
- ✅ Analysis ID generated successfully
- ✅ Primary intent identified (PMI-related)
- ✅ High urgency classification
- ✅ Risk scores show elevated complaint risk (>0.7)
- ✅ Confidence score >0.8

### Track Variable:
```bash
export ANALYSIS_ID="analysis_20241201_001"
```

---

## Step 3. Generate Four-Layer Action Plan (Decision Agent)

**Co-Pilot Mode**: 🧭 **Plan Mode** - Intelligent action routing with risk assessment

**Purpose**: Create comprehensive action plan with Decision Agent risk evaluation and approval routing.

> **🛡️ Governance Integration**: All actions generated will go through the governance framework for compliance validation and risk-based approval routing.

### API Call (curl):
```bash
curl -X POST "http://localhost:8000/api/v1/plans/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "analysis_id": "'$ANALYSIS_ID'",
       "transcript_id": "'$TRANSCRIPT_ID'"
     }'
```

### Python SDK Example:
```python
# Step 3: Generate action plan using IDs from previous steps
print(f"\nUsing analysis_id: {analysis_id}, transcript_id: {transcript_id}")

response = requests.post(
    "http://localhost:8000/api/v1/plans/generate",
    json={
        "analysis_id": analysis_id,  # Using variable from Step 2
        "transcript_id": transcript_id  # Using variable from Step 1
    }
)

plan_data = response.json()
plan_id = plan_data["plan_id"]
print(f"Action Plan: {plan_id}")
print(f"Total Actions: {plan_data['total_actions']}")
print(f"Routing Distribution: {plan_data['routing_summary']}")
print(f"Storing plan_id for next steps: {plan_id}")
```

### Expected Response:
```json
{
  "plan_id": "plan_20241201_001",
  "total_actions": 12,
  "routing_summary": {
    "auto_approved": 3,
    "advisor_approval": 4,
    "supervisor_approval": 5
  },
  "layers": {
    "borrower_plan": 4,
    "advisor_plan": 3,
    "supervisor_plan": 3,
    "leadership_plan": 2
  },
  "risk_level": "high",
  "approval_route": "supervisor_approval"
}
```

### Success Indicators:
- ✅ Plan ID generated (format: `plan_YYYYMMDD_XXX`)
- ✅ ~12 total actions created
- ✅ Actions distributed across approval levels
- ✅ Four-layer structure (borrower/advisor/supervisor/leadership)
- ✅ High-risk actions routed to supervisor approval

### Track Variable:
```bash
export PLAN_ID="plan_20241201_001"
```

---

## Step 4. View Detailed Action Plan (Four Layers)

**Co-Pilot Mode**: 📊 **Reflect Mode** - Reviewing Co-Pilot's action proposals

**Purpose**: Inspect the four-layer action plan structure and individual action details.

### API Call (curl):
```bash
curl -X GET "http://localhost:8000/api/v1/plans/$PLAN_ID"
```

### View Specific Layer:
```bash
# View only supervisor actions
curl -X GET "http://localhost:8000/api/v1/plans/$PLAN_ID?layer=supervisor"
```

### Python SDK Example:
```python
# Step 4: Get full action plan details and extract action IDs
print(f"\nUsing plan_id from Step 3: {plan_id}")

response = requests.get(f"http://localhost:8000/api/v1/plans/{plan_id}")
plan_details = response.json()

# Extract action IDs for governance submission
action_ids = []
print("📄 Four-Layer Action Plan:")
for layer in ["borrower_plan", "advisor_plan", "supervisor_plan", "leadership_plan"]:
    actions = plan_details[layer]["actions"]
    print(f"\n🎯 {layer.replace('_', ' ').title()}: {len(actions)} actions")
    for action in actions[:2]:  # Show first 2 actions
        action_ids.append(action['action_id'])  # Collect action IDs
        print(f"  • {action['description']} (Risk: {action['risk_score']:.2f})")
        print(f"    Action ID: {action['action_id']}")

print(f"\nExtracted {len(action_ids)} action IDs for governance submission")
print(f"Action IDs: {action_ids}")
```

### Expected Response Structure:
```json
{
  "plan_id": "plan_20241201_001",
  "borrower_plan": {
    "actions": [
      {
        "action_id": "action_20241201_001",
        "description": "Send PMI removal eligibility documentation",
        "risk_score": 0.25,
        "approval_route": "auto",
        "timeline": "24 hours",
        "actor": "System"
      }
    ]
  },
  "advisor_plan": {
    "actions": [
      {
        "action_id": "action_20241201_005",
        "description": "Schedule coaching session on compliance phrasing",
        "risk_score": 0.45,
        "approval_route": "advisor_approval",
        "actor": "Supervisor"
      }
    ]
  },
  "supervisor_plan": {
    "actions": [
      {
        "action_id": "action_20241201_008",
        "description": "Review property valuation dispute escalation",
        "risk_score": 0.78,
        "approval_route": "supervisor_approval",
        "financial_impact": true,
        "actor": "Leadership"
      }
    ]
  },
  "leadership_plan": {
    "actions": [
      {
        "action_id": "action_20241201_011",
        "description": "Analyze PMI dispute patterns for policy review",
        "risk_score": 0.35,
        "approval_route": "auto",
        "strategic_value": "high",
        "actor": "Leadership"
      }
    ]
  }
}
```

### Success Indicators:
- ✅ All four layers populated with actions
- ✅ Risk scores vary appropriately (0.2-0.8 range)
- ✅ Approval routes aligned with risk levels
- ✅ Proper actor assignments (System/Advisor/Supervisor/Leadership)
- ✅ Financial impact flagged for high-risk actions

---

## Step 5. Submit Plan for Governance Review & Approval

**Co-Pilot Mode**: ⚙️ **Execute Mode** - Governance validation and approval workflow

**Purpose**: Submit the action plan through the governance framework for compliance validation and risk-based approval routing.

> **🛡️ New Governance Integration**: Actions now go through LLM-based compliance validation before traditional approval workflow.

### Step 5a: Submit for Governance Review
```bash
curl -X POST "http://localhost:8000/api/v1/governance/submit" \
     -H "Content-Type: application/json" \
     -d '{
       "plan_id": "'$PLAN_ID'",
       "actions": [
         {
           "action_id": "action_20241201_001",
           "description": "Send PMI removal eligibility documentation",
           "risk_score": 0.25,
           "financial_impact": false,
           "compliance_required": ["CFPB_PMI_DISCLOSURE"]
         },
         {
           "action_id": "action_20241201_008", 
           "description": "Review property valuation dispute escalation",
           "risk_score": 0.78,
           "financial_impact": true,
           "compliance_required": ["CFPB_ERROR_RESOLUTION", "STATE_FORECLOSURE"]
         }
       ],
       "submitted_by": "advisor_mike",
       "urgency": "high"
     }'
```

### Step 5b: Check Governance Status
```bash
curl -X GET "http://localhost:8000/api/v1/governance/status/$GOVERNANCE_ID"
```

### Step 5c: Traditional Approval Workflow (for approved actions)
```bash
curl -X POST "http://localhost:8000/api/v1/approvals/submit" \
     -H "Content-Type: application/json" \
     -d '{
       "plan_id": "'$PLAN_ID'",
       "submitted_by": "advisor_mike",
       "priority": "high",
       "notes": "Customer escalation requires immediate supervisor review",
       "governance_id": "'$GOVERNANCE_ID'"
     }'
```

### Python SDK Example:
```python
# Step 5a: Submit for Governance Review using actual action data
print(f"\nUsing plan_id: {plan_id} and action_ids from Step 4")

# Build actions list from actual plan details
actions_for_governance = []
for layer_name, layer_data in plan_details.items():
    if layer_name.endswith('_plan'):
        for action in layer_data['actions'][:2]:  # Take first 2 actions from each layer
            actions_for_governance.append({
                "action_id": action['action_id'],
                "description": action['description'],
                "risk_score": action.get('risk_score', 0.5),
                "financial_impact": action.get('financial_impact', False),
                "compliance_required": action.get('compliance_required', ["CFPB_GENERAL"])
            })

print(f"Submitting {len(actions_for_governance)} actions for governance review")

governance_response = requests.post(
    "http://localhost:8000/api/v1/governance/submit",
    json={
        "plan_id": plan_id,  # Using variable from Step 3
        "actions": actions_for_governance,  # Using actual actions from Step 4
        "submitted_by": "advisor_mike",
        "urgency": "high"
    }
)

governance_data = governance_response.json()
governance_id = governance_data["governance_id"]
print(f"🛡️ Governance ID: {governance_id}")
print(f"Compliance Status: {governance_data['compliance_status']}")
print(f"Risk Level: {governance_data['risk_level']}")
print(f"Storing governance_id for next steps: {governance_id}")

# Step 5b: Check Governance Status
print(f"\nChecking governance status for: {governance_id}")
status_response = requests.get(f"http://localhost:8000/api/v1/governance/status/{governance_id}")
status_data = status_response.json()
print(f"Governance Status: {status_data['status']}")

# Step 5c: Submit for Traditional Approval (if governance approved)
if status_data["status"] == "compliant":
    print(f"\nGovernance approved! Submitting for traditional approval...")
    approval_response = requests.post(
        "http://localhost:8000/api/v1/approvals/submit",
        json={
            "plan_id": plan_id,  # Using variable from Step 3
            "submitted_by": "advisor_mike",
            "priority": "high",
            "notes": "Customer escalation requires immediate supervisor review",
            "governance_id": governance_id  # Using variable from Step 5a
        }
    )
    
    approval_data = approval_response.json()
    approval_id = approval_data["approval_id"]
    print(f"📋 Approval ID: {approval_id}")
    print(f"Status: {approval_data['status']}")
    print(f"Storing approval_id for next steps: {approval_id}")
else:
    print(f"Governance not compliant. Status: {status_data['status']}")
    approval_id = None
```

### Expected Governance Response:
```json
{
  "governance_id": "governance_20241201_001",
  "plan_id": "plan_20241201_001", 
  "compliance_status": "compliant",
  "risk_level": "medium",
  "routing_decision": "supervisor_approval",
  "evaluated_actions": 12,
  "compliant_actions": 10,
  "flagged_actions": 2,
  "required_disclosures": [
    "CFPB PMI removal disclosure required",
    "State foreclosure prevention notice"
  ],
  "compliance_concerns": [
    "Property valuation dispute requires additional documentation"
  ],
  "confidence_score": 0.92,
  "next_step": "proceed_to_approval_workflow"
}
```

### Expected Approval Response (after governance):
```json
{
  "approval_id": "approval_20241201_001",
  "plan_id": "plan_20241201_001",
  "governance_id": "governance_20241201_001",
  "status": "pending_approval",
  "submitted_by": "advisor_mike",
  "submitted_at": "2024-12-01T15:30:22Z",
  "priority": "high",
  "approval_route": "supervisor_approval",
  "estimated_approval_time": "2-4 hours",
  "governance_validated": true
}
```

### Track Variables:
```bash
export GOVERNANCE_ID="governance_20241201_001"
export APPROVAL_ID="approval_20241201_001"
```

---

## Step 6. Governance Queue Management & Approval Actions

**Co-Pilot Mode**: ⚙️ **Execute Mode** - Human oversight with governance-aware approval workflow

**Purpose**: Review governance queue, handle compliance concerns, and approve/reject specific actions.

### Step 6a: Check Governance Queue
```bash
curl -X GET "http://localhost:8000/api/v1/governance/queue?status=pending"
```

### Step 6b: Review Audit Trail (Optional)
```bash
curl -X GET "http://localhost:8000/api/v1/governance/audit?governance_id=$GOVERNANCE_ID"
```

### Step 6c: Approve Actions with Compliance Conditions
```bash
curl -X POST "http://localhost:8000/api/v1/governance/approve" \
     -H "Content-Type: application/json" \
     -d '{
       "governance_id": "'$GOVERNANCE_ID'",
       "approved_by": "supervisor_jane",
       "conditions": [
         "Ensure CFPB PMI removal disclosure is sent within 24 hours",
         "Document property valuation review process",
         "Follow up within 48 hours for customer acknowledgment"
       ],
       "notes": "Approved with enhanced compliance monitoring"
     }'
```

### Step 6d: Traditional Approval Workflow (Existing System)
```bash
curl -X POST "http://localhost:8000/api/v1/approvals/$APPROVAL_ID/approve" \
     -H "Content-Type: application/json" \
     -d '{
       "approved_by": "supervisor_jane",
       "notes": "Governance validated - approved with documentation requirements",
       "conditions": ["Ensure CFPB compliance documentation", "Follow up within 48 hours"],
       "governance_validated": true
     }'
```

### Python SDK Example:
```python
# Step 6a: Check Governance Queue
print(f"\n=== Step 6: Governance Queue Management ===")
governance_queue = requests.get("http://localhost:8000/api/v1/governance/queue?status=pending").json()
print(f"🛡️ Governance Queue: {len(governance_queue['items'])} pending items")

# Step 6b: Review Audit Trail
print(f"\nReviewing audit trail for governance_id: {governance_id}")
audit_response = requests.get(f"http://localhost:8000/api/v1/governance/audit?governance_id={governance_id}")
audit_trail = audit_response.json()
print(f"📜 Audit Events: {len(audit_trail['events'])} recorded")

# Step 6c: Approve with Compliance Conditions
print(f"\nApproving governance_id: {governance_id}")
governance_approval = requests.post(
    "http://localhost:8000/api/v1/governance/approve",
    json={
        "governance_id": governance_id,  # Using variable from Step 5a
        "approved_by": "supervisor_jane",
        "conditions": [
            "Ensure CFPB PMI removal disclosure is sent within 24 hours",
            "Document property valuation review process", 
            "Follow up within 48 hours for customer acknowledgment"
        ],
        "notes": "Approved with enhanced compliance monitoring"
    }
)

governance_result = governance_approval.json()
print(f"🛡️ Governance Status: {governance_result['status']}")

# Step 6d: Traditional Approval (after governance approval)
if approval_id:  # Only if we have an approval_id from Step 5c
    print(f"\nApproving traditional approval_id: {approval_id}")
    traditional_approval = requests.post(
        f"http://localhost:8000/api/v1/approvals/{approval_id}/approve",  # Using variable from Step 5c
        json={
            "approved_by": "supervisor_jane",
            "notes": "Governance validated - approved with documentation requirements",
            "conditions": ["Ensure CFPB compliance documentation", "Follow up within 48 hours"],
            "governance_validated": True
        }
    )
    
    approval_result = traditional_approval.json()
    print(f"📋 Approval Status: {approval_result['status']}")
else:
    print("No approval_id available - skipping traditional approval")
```

### Expected Governance Response:
```json
{
  "governance_id": "governance_20241201_001",
  "status": "approved_with_conditions",
  "approved_by": "supervisor_jane",
  "approved_at": "2024-12-01T16:15:30Z",
  "conditions": [
    "Ensure CFPB PMI removal disclosure is sent within 24 hours",
    "Document property valuation review process",
    "Follow up within 48 hours for customer acknowledgment"
  ],
  "compliance_validated": true,
  "audit_event_id": "audit_20241201_003",
  "next_step": "proceed_to_traditional_approval"
}
```

### Expected Traditional Approval Response:
```json
{
  "approval_id": "approval_20241201_001",
  "plan_id": "plan_20241201_001",
  "governance_id": "governance_20241201_001",
  "status": "approved",
  "approved_by": "supervisor_jane",
  "approved_at": "2024-12-01T16:16:45Z",
  "conditions": ["Ensure CFPB compliance documentation", "Follow up within 48 hours"],
  "governance_validated": true,
  "next_step": "ready_for_execution"
}
```

### Success Indicators:
- ✅ **Governance validation**: Compliance check passed with confidence >0.9
- ✅ **Audit trail**: Governance approval event recorded with cryptographic integrity
- ✅ **Compliance conditions**: Required CFPB disclosures identified and enforced
- ✅ **Dual approval**: Both governance and traditional approval completed
- ✅ **Risk assessment**: Actions properly routed based on LLM governance evaluation
- ✅ Plan ready for execution with governance validation

---

## Step 7. Execute Governance-Validated Action Plan

**Co-Pilot Mode**: ⚙️ **Execute Mode** - Co-Pilot executing governance-validated actions in background

**Purpose**: Execute approved actions with compliance monitoring, actor simulation and artifact generation.

> **🛡️ Governance-Aware Execution**: All executed actions include compliance validation results and audit trail integration.

### API Call (curl):
```bash
curl -X POST "http://localhost:8000/api/v1/execution/execute" \
     -H "Content-Type: application/json" \
     -d '{
       "plan_id": "'$PLAN_ID'",
       "governance_id": "'$GOVERNANCE_ID'",
       "approval_id": "'$APPROVAL_ID'",
       "execution_mode": "full",
       "actor_simulation": true,
       "generate_artifacts": true,
       "compliance_monitoring": true
     }'
```

### Python SDK Example:
```python
# Step 7: Execute the governance-validated approved plan
print(f"\n=== Step 7: Execute Governance-Validated Action Plan ===")
print(f"Using plan_id: {plan_id}, governance_id: {governance_id}, approval_id: {approval_id}")

response = requests.post(
    "http://localhost:8000/api/v1/execution/execute",
    json={
        "plan_id": plan_id,  # Using variable from Step 3
        "governance_id": governance_id,  # Using variable from Step 5a
        "approval_id": approval_id,  # Using variable from Step 5c
        "execution_mode": "full",
        "actor_simulation": True,
        "generate_artifacts": True,
        "compliance_monitoring": True
    }
)

execution_data = response.json()
execution_id = execution_data["execution_id"]
print(f"🚀 Execution ID: {execution_id}")
print(f"Actions Executed: {execution_data['actions_executed']}")
print(f"Artifacts Created: {execution_data['artifacts_created']}")
print(f"🛡️ Compliance Events: {execution_data['compliance_events']}")
print(f"Audit Events Generated: {execution_data['audit_events_count']}")
print(f"Storing execution_id for next steps: {execution_id}")
```

### Expected Response:
```json
{
  "execution_id": "exec_20241201_001",
  "plan_id": "plan_20241201_001",
  "governance_id": "governance_20241201_001",
  "approval_id": "approval_20241201_001",
  "status": "completed",
  "actions_executed": 8,
  "actions_skipped": 4,
  "artifacts_created": 6,
  "compliance_events": 12,
  "audit_events_count": 8,
  "execution_summary": {
    "borrower_actions": 3,
    "advisor_actions": 2,
    "supervisor_actions": 2,
    "leadership_actions": 1
  },
  "artifact_types": {
    "emails": 3,
    "documents": 2,
    "callbacks": 1
  },
  "governance_summary": {
    "compliance_validated": true,
    "cfpb_disclosures_generated": 2,
    "audit_trail_events": 8,
    "risk_mitigations_applied": 3
  },
  "success_rate": 0.89
}
```

### Track Variable:
```bash
export EXECUTION_ID="exec_20241201_001"
```

### Success Indicators:
- ✅ **Governance-validated execution**: All actions executed with compliance monitoring
- ✅ **Audit trail integration**: 8+ audit events generated for complete traceability
- ✅ **CFPB compliance**: Required disclosures automatically generated during execution
- ✅ **Risk mitigation**: 3+ governance-mandated risk controls applied
- ✅ **Artifacts generated**: Emails, documents, callbacks with compliance validation
- ✅ **Success rate >85%** with governance oversight maintained

---

## Step 8. Monitor Execution Status & Results

**Co-Pilot Mode**: 📊 **Reflect Mode** - Real-time execution monitoring

**Purpose**: Track execution progress and review generated artifacts.

### Get Execution Status:
```bash
curl -X GET "http://localhost:8000/api/v1/execution/$EXECUTION_ID"
```

### List All Executions:
```bash
curl -X GET "http://localhost:8000/api/v1/execution?limit=5"
```

### Python SDK Example:
```python
# Step 8: Monitor execution status using execution_id from Step 7
print(f"\n=== Step 8: Monitor Execution Status ===")
print(f"Using execution_id from Step 7: {execution_id}")

response = requests.get(f"http://localhost:8000/api/v1/execution/{execution_id}")
execution_details = response.json()

print("📊 Execution Results:")
print(f"Status: {execution_details['status']}")
print(f"Duration: {execution_details['duration_seconds']}s")
print(f"Success Rate: {execution_details['success_rate']:.1%}")

# Show artifact details
artifacts = execution_details['artifacts']
for artifact_type, count in artifacts.items():
    print(f"  {artifact_type}: {count} generated")
```

### Expected Response:
```json
{
  "execution_id": "exec_20241201_001",
  "plan_id": "plan_20241201_001",
  "status": "completed",
  "started_at": "2024-12-01T16:20:00Z",
  "completed_at": "2024-12-01T16:23:45Z",
  "duration_seconds": 225,
  "success_rate": 0.89,
  "actions_detail": [
    {
      "action_id": "action_20241201_001",
      "description": "Send PMI removal eligibility documentation",
      "status": "completed",
      "actor": "System",
      "artifacts": ["emails/pmi_eligibility_CUST_001.html"]
    },
    {
      "action_id": "action_20241201_008",
      "description": "Review property valuation dispute escalation", 
      "status": "completed",
      "actor": "Leadership",
      "artifacts": ["documents/valuation_review_CUST_001.pdf"]
    }
  ],
  "artifacts": {
    "emails": 3,
    "documents": 2,
    "callbacks": 1
  }
}
```

---

## Step 9. View Generated Artifacts

**Co-Pilot Mode**: 📊 **Reflect Mode** - Reviewing Co-Pilot's work output

**Purpose**: Examine artifacts generated during execution (emails, documents, callbacks).

### API Calls (curl):
```bash
# Get all artifacts
curl -X GET "http://localhost:8000/api/v1/execution/$EXECUTION_ID/artifacts"

# Get specific artifact type
curl -X GET "http://localhost:8000/api/v1/execution/$EXECUTION_ID/artifacts?type=emails"
```

### Python SDK Example:
```python
# Step 9: View artifacts using execution_id from Step 7
print(f"\n=== Step 9: View Generated Artifacts ===")
print(f"Using execution_id: {execution_id}")

response = requests.get(f"http://localhost:8000/api/v1/execution/{execution_id}/artifacts")
artifacts = response.json()

print("📄 Generated Artifacts:")
for artifact in artifacts['artifacts']:
    print(f"  📁 {artifact['filename']}")
    print(f"     Type: {artifact['type']} | Size: {artifact['size']} bytes")
    print(f"     Actor: {artifact['actor']} | Created: {artifact['created_at']}")
    print(f"     Preview: {artifact['content_preview'][:100]}...")
    print()
```

### Expected Response:
```json
{
  "execution_id": "exec_20241201_001",
  "total_artifacts": 6,
  "artifacts": [
    {
      "artifact_id": "artifact_001",
      "filename": "pmi_eligibility_CUST_001.html",
      "type": "email",
      "size": 2847,
      "actor": "System",
      "created_at": "2024-12-01T16:21:15Z",
      "content_preview": "<html><body><h2>PMI Removal Eligibility Review</h2><p>Dear Valued Customer...</p></body></html>"
    },
    {
      "artifact_id": "artifact_002", 
      "filename": "valuation_review_CUST_001.pdf",
      "type": "document",
      "size": 15642,
      "actor": "Leadership",
      "created_at": "2024-12-01T16:22:30Z",
      "content_preview": "PROPERTY VALUATION DISPUTE REVIEW - Customer: CUST_001..."
    },
    {
      "artifact_id": "artifact_003",
      "filename": "callback_schedule_CUST_001.json",
      "type": "callback",
      "size": 456,
      "actor": "Advisor",
      "created_at": "2024-12-01T16:21:45Z",
      "content_preview": "{\"customer_id\": \"CUST_001\", \"callback_date\": \"2024-12-03T10:00:00Z\"...}"
    }
  ]
}
```

### Success Indicators:
- ✅ Multiple artifact types generated (emails, documents, callbacks)
- ✅ Proper actor assignments (System, Advisor, Leadership)
- ✅ Realistic content previews
- ✅ Appropriate file sizes and timestamps

---

## Step 10. Get Analysis, Execution & Governance Metrics

**Co-Pilot Mode**: 📊 **Reflect Mode** - Performance analytics with governance oversight and Observer Agent simulation

**Purpose**: Review system performance metrics including governance compliance and simulate Observer Agent evaluation.

### API Calls (curl):
```bash
# Get analysis metrics
curl -X GET "http://localhost:8000/api/v1/analysis/metrics"

# Get execution metrics  
curl -X GET "http://localhost:8000/api/v1/execution/metrics"

# Get governance metrics
curl -X GET "http://localhost:8000/api/v1/governance/metrics"

# Get analysis trends
curl -X GET "http://localhost:8000/api/v1/analysis/trends"
```

### Python SDK Example:
```python
# Step 10: Get comprehensive metrics
print(f"\n=== Step 10: Get Analysis, Execution & Governance Metrics ===")

analysis_metrics = requests.get("http://localhost:8000/api/v1/analysis/metrics").json()
execution_metrics = requests.get("http://localhost:8000/api/v1/execution/metrics").json()
governance_metrics = requests.get("http://localhost:8000/api/v1/governance/metrics").json()

print("📊 Co-Pilot Performance Dashboard with Governance:")
print(f"Total Analyses: {analysis_metrics['total_analyses']}")
print(f"Average Confidence: {analysis_metrics['average_confidence']:.1%}")
print(f"Execution Success Rate: {execution_metrics['success_rate']:.1%}")
print(f"Average Execution Time: {execution_metrics['avg_duration_minutes']:.1f} min")
print(f"🛡️ Governance Compliance Rate: {governance_metrics['compliance_rate']:.1%}")
print(f"Audit Events Generated: {governance_metrics['total_audit_events']}")
print(f"Average Governance Confidence: {governance_metrics['avg_confidence']:.1%}")

# Simulate Observer Agent Evaluation
observer_evaluation = {
    "overall_satisfaction": 4.5,
    "execution_quality": 4.3,
    "governance_effectiveness": 4.7,
    "issues_identified": [
        "Documentation completeness could be improved",
        "Some governance approvals took longer than expected"
    ],
    "improvement_opportunities": [
        "Implement pre-execution document validation",
        "Add automated governance status notifications", 
        "Optimize LLM governance confidence thresholds",
        "Streamline dual approval workflow"
    ],
    "actor_performance": {
        "advisor": 4.5,
        "supervisor": 4.1,
        "leadership": 4.2,
        "system": 4.6,
        "governance_engine": 4.8
    },
    "governance_insights": {
        "compliance_accuracy": 4.9,
        "risk_assessment_quality": 4.6,
        "audit_trail_completeness": 5.0,
        "regulatory_coverage": 4.7
    }
}

print("\n👁️ Observer Agent Evaluation (Simulated):")
print(f"Overall Satisfaction: {observer_evaluation['overall_satisfaction']}/5.0")
print(f"Execution Quality: {observer_evaluation['execution_quality']}/5.0")
print(f"🛡️ Governance Effectiveness: {observer_evaluation['governance_effectiveness']}/5.0")
print("\n🔍 Issues Identified:")
for issue in observer_evaluation['issues_identified']:
    print(f"  • {issue}")

print("\n🛡️ Governance Performance Insights:")
print(f"  Compliance Accuracy: {observer_evaluation['governance_insights']['compliance_accuracy']}/5.0")
print(f"  Risk Assessment Quality: {observer_evaluation['governance_insights']['risk_assessment_quality']}/5.0")
print(f"  Audit Trail Completeness: {observer_evaluation['governance_insights']['audit_trail_completeness']}/5.0")
print(f"  Regulatory Coverage: {observer_evaluation['governance_insights']['regulatory_coverage']}/5.0")
```

### Expected Metrics Response:
```json
{
  "analysis_metrics": {
    "total_analyses": 1,
    "average_confidence": 0.89,
    "resolution_rate": 1.0,
    "risk_distribution": {
      "high_delinquency": 0,
      "high_churn": 1,
      "high_complaint": 1
    },
    "intent_distribution": {
      "PMI Removal Assistance": 1
    },
    "urgency_distribution": {
      "high": 1,
      "medium": 0,
      "low": 0
    }
  },
  "execution_metrics": {
    "total_executions": 1,
    "success_rate": 0.89,
    "avg_duration_minutes": 3.75,
    "artifacts_generated": 6,
    "actions_by_actor": {
      "System": 3,
      "Advisor": 2,
      "Supervisor": 2,
      "Leadership": 1
    }
  },
  "governance_metrics": {
    "total_governance_reviews": 1,
    "compliance_rate": 0.92,
    "avg_confidence": 0.92,
    "total_audit_events": 8,
    "routing_distribution": {
      "auto_approved": 3,
      "advisor_approval": 4,
      "supervisor_approval": 5,
      "leadership_approval": 0
    },
    "compliance_categories": {
      "cfpb_compliance": 1,
      "state_regulations": 1,
      "company_policies": 1,
      "financial_validation": 1
    },
    "risk_mitigations_applied": 3,
    "avg_governance_time_minutes": 1.2
  }
}
```

---

## Step 11. Demonstrate Learning Loop with Governance (Second Iteration)

**Co-Pilot Mode**: 📊 **Reflect Mode** - Continuous learning and governance optimization

**Purpose**: Execute a second similar scenario to demonstrate Observer Agent feedback, governance learning, and improved compliance confidence.

### Generate Similar Scenario:
```bash
curl -X POST "http://localhost:8000/api/v1/transcripts/generate" \
     -H "Content-Type: application/json" \
     -d '{
       "scenario": "Mortgage Servicing - PMI Removal Follow-up with Updated Compliance Requirements",
       "urgency": "medium",
       "financial_impact": true,
       "customer_sentiment": "cautious",
       "store": true,
       "learning_context": "previous_pmi_dispute"
     }'
```

### Quick Workflow Execution:
```python
# Step 11: Second iteration - demonstrating learning
print(f"\n=== Step 11: Demonstrate Learning Loop ===")
print("🔄 Learning Loop Demonstration:")
print(f"Using data from first iteration for comparison...")

# Generate second transcript
response = requests.post("http://localhost:8000/api/v1/transcripts/generate", json={
    "scenario": "PMI Removal Follow-up with Updated Compliance Requirements",
    "urgency": "medium",
    "learning_context": "previous_pmi_dispute"
})
transcript_id_2 = response.json()["transcript_id"]
print(f"Second transcript generated: {transcript_id_2}")

# Analyze (should show improved confidence)
response = requests.post("http://localhost:8000/api/v1/analysis/analyze", 
                        json={"transcript_id": transcript_id_2})
analysis_2 = response.json()
analysis_id_2 = analysis_2["analysis_id"]
print(f"Second analysis: {analysis_id_2}")

# Generate action plan (should show improved routing)
response = requests.post("http://localhost:8000/api/v1/plans/generate",
                        json={
                            "analysis_id": analysis_id_2,
                            "transcript_id": transcript_id_2
                        })
plan_2 = response.json()
plan_id_2 = plan_2["plan_id"]
print(f"Second plan: {plan_id_2}")

print(f"\nLearning Improvements:")
print(f"  Confidence: {analysis_2['confidence']:.3f} (vs {analysis_data['confidence']:.3f} from first iteration)")
print(f"  Actions Generated: {plan_2['total_actions']} (vs {plan_data['total_actions']} from first iteration)")
print(f"  Auto-approved: {plan_2['routing_summary']['auto_approved']} (vs {plan_data['routing_summary']['auto_approved']} from first iteration)")

# Get plan details to extract actions for governance
response = requests.get(f"http://localhost:8000/api/v1/plans/{plan_id_2}")
plan_2_details = response.json()

# Build actions list from second plan
actions_for_governance_2 = []
for layer_name, layer_data in plan_2_details.items():
    if layer_name.endswith('_plan'):
        for action in layer_data['actions'][:1]:  # Take first action from each layer
            actions_for_governance_2.append({
                "action_id": action['action_id'],
                "description": action['description'],
                "risk_score": action.get('risk_score', 0.5),
                "financial_impact": action.get('financial_impact', False),
                "compliance_required": action.get('compliance_required', ["CFPB_GENERAL"])
            })

# Submit for governance (to see improved governance learning)
print(f"\nSubmitting second plan for governance: {plan_id_2}")
governance_response_2 = requests.post(
    "http://localhost:8000/api/v1/governance/submit",
    json={
        "plan_id": plan_id_2,
        "actions": actions_for_governance_2,
        "submitted_by": "advisor_mike",
        "urgency": "medium",
        "learning_context": "previous_pmi_governance"
    }
)
governance_2 = governance_response_2.json()
governance_id_2 = governance_2["governance_id"]
print(f"Second governance ID: {governance_id_2}")

# Calculate learning velocity
learning_velocity = (analysis_2['confidence'] - analysis_data['confidence']) / analysis_data['confidence']
first_governance_confidence = governance_data.get('confidence_score', 0.92)
governance_velocity = (governance_2.get('confidence_score', 0.95) - first_governance_confidence) / first_governance_confidence if 'confidence_score' in governance_2 else 0

print(f"  Learning Velocity: {learning_velocity:.3f} ({'+' if learning_velocity > 0 else ''}{learning_velocity:.1%})")
print(f"🛡️ Governance Learning Velocity: {governance_velocity:.3f} ({'+' if governance_velocity > 0 else ''}{governance_velocity:.1%})")
print(f"  Governance Time Improvement: {((1.2 - governance_2.get('processing_time_minutes', 1.0))/1.2):.1%} faster")
```

### Learning Velocity Metrics with Governance:
```json
{
  "learning_comparison": {
    "first_iteration": {
      "confidence": 0.89,
      "total_actions": 12,
      "auto_approved": 3,
      "execution_time": 225,
      "governance_confidence": 0.92,
      "governance_time_minutes": 1.2,
      "compliance_concerns": 2
    },
    "second_iteration": {
      "confidence": 0.93,
      "total_actions": 10,
      "auto_approved": 5,
      "execution_time": 180,
      "governance_confidence": 0.95,
      "governance_time_minutes": 0.8,
      "compliance_concerns": 1
    },
    "improvements": {
      "confidence_gain": 0.04,
      "efficiency_gain": 0.20,
      "auto_approval_rate": 0.67,
      "learning_velocity": 0.85,
      "governance_confidence_gain": 0.03,
      "governance_efficiency_gain": 0.33,
      "compliance_improvement": 0.50,
      "overall_governance_velocity": 0.95
    }
  }
}
```

---

## 🎯 Success Criteria & Validation (Enhanced with Governance)

### ✅ Core Workflow Completed
- [ ] Complex customer call generated with high urgency
- [ ] AI analysis with >80% confidence score
- [ ] Four-layer action plan with ~12 actions
- [ ] **🛡️ Governance validation**: LLM-based compliance review with >90% confidence
- [ ] **🛡️ Dual approval workflow**: Both governance and traditional approval completed
- [ ] Execution with >85% success rate and compliance monitoring
- [ ] 5+ artifacts generated (emails, documents, callbacks) with compliance validation

### ✅ Co-Pilot Vision Demonstrated
- [ ] **Plan Mode**: Real-time action planning with governance-integrated risk assessment
- [ ] **Execute Mode**: Background co-execution with compliance monitoring and actor simulation  
- [ ] **Reflect Mode**: Post-execution analysis with governance insights and Observer feedback

### ✅ API Integration Proven
- [ ] All 29 new API endpoints functional (20 existing + 9 governance)
- [ ] **🛡️ Governance APIs operational**: All 9 governance endpoints responding correctly
- [ ] Proper error handling and response formats
- [ ] Integration with existing CLI backend services
- [ ] Performance metrics available via API including governance metrics

### ✅ Learning Loop Functional
- [ ] Second iteration shows improved confidence
- [ ] Better action routing (more auto-approvals)
- [ ] Faster execution times
- [ ] Learning velocity >0.8 (positive improvement trend)
- [ ] **🛡️ Governance learning demonstrated**: Improved compliance confidence and processing time
- [ ] **🛡️ Overall governance velocity >0.9**: Strong improvement in governance effectiveness

---

## 🚀 Advanced API Scenarios with Governance

### Bulk Operations:
```bash
# Bulk governance approvals
curl -X POST "http://localhost:8000/api/v1/governance/bulk-approve" \
     -H "Content-Type: application/json" \
     -d '{
       "governance_ids": ["governance_001", "governance_002", "governance_003"],
       "approved_by": "supervisor_jane",
       "bulk_conditions": ["Standard CFPB compliance required for all actions"]
     }'

# Analyze multiple transcripts
curl -X POST "http://localhost:8000/api/v1/analysis/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "transcript_ids": ["transcript_001", "transcript_002", "transcript_003"]
     }'
```

### Error Handling:
```bash
# Test governance error response
curl -X GET "http://localhost:8000/api/v1/governance/status/nonexistent_governance_id"
# Expected: 404 with {"detail": "Governance ID nonexistent_governance_id not found"}

# Test plan error response
curl -X GET "http://localhost:8000/api/v1/plans/nonexistent_plan"
# Expected: 404 with {"detail": "Plan nonexistent_plan not found"}
```

### Performance Testing:
```python
import time
import concurrent.futures

def analyze_transcript(transcript_id):
    start = time.time()
    response = requests.post("http://localhost:8000/api/v1/analysis/analyze",
                           json={"transcript_id": transcript_id})
    duration = time.time() - start
    return {"transcript_id": transcript_id, "duration": duration, "success": response.status_code == 200}

# Test concurrent analysis
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(analyze_transcript, f"transcript_{i:03d}") for i in range(1, 6)]
    results = [future.result() for future in concurrent.futures.as_completed(futures)]

avg_duration = sum(r["duration"] for r in results) / len(results)
print(f"Average API Response Time: {avg_duration:.3f}s")
```

---

## 🎉 Demo Completion (Enhanced with Governance)

**Congratulations!** You have successfully demonstrated the complete **Co-Pilot Intelligent Teammate** system with **Epic 2: Approval & Governance Framework** integration via API:

### What You've Accomplished:
1. **🧭 Plan Mode**: Generated complex scenarios with governance-integrated real-time risk assessment
2. **⚙️ Execute Mode**: Automated multi-actor action execution with dual approval workflows (governance + traditional)
3. **📊 Reflect Mode**: Performance monitoring with governance insights and Observer Agent evaluation
4. **🔄 Learning Loop**: Demonstrated measurable improvement with governance learning optimization
5. **🛡️ Governance Integration**: Complete LLM-based compliance validation and audit trail management

### Co-Pilot Vision Realized with Governance:
- **Intelligent Teammate**: Co-executes alongside advisors with governance oversight, not just analyzes
- **Four-Layer Planning**: Borrower → Advisor → Supervisor → Leadership alignment with compliance validation
- **Dual Approval Workflows**: Risk-based routing with governance validation and human oversight
- **Continuous Learning**: Observer Agent feedback improves future performance including governance effectiveness
- **Regulatory Compliance**: Built-in CFPB compliance validation and audit trail integrity

### Technical Foundation Enhanced:
- **29 FastAPI Endpoints**: Complete REST API including 9 governance endpoints for enterprise integration
- **Real-time Processing**: Sub-4 minute end-to-end workflow execution with governance validation
- **Artifact Generation**: Tangible outputs (emails, documents, callbacks) with compliance validation
- **Governance Framework**: LLM-based compliance validation, cryptographic audit trails, and risk-based routing
- **Scalable Architecture**: Ready for UI development and enterprise deployment with regulatory compliance

The Co-Pilot is now operational as an **Intelligent Teammate with Governance** ready to transform mortgage servicing operations with full regulatory compliance! 🤖🛡️✨

---

## 📋 API Reference Summary

### Analysis APIs (5 endpoints):
- `POST /api/v1/analysis/analyze` - Analyze transcript(s)
- `GET /api/v1/analysis/{analysis_id}` - Get analysis results
- `GET /api/v1/analysis/metrics` - Get analysis metrics
- `GET /api/v1/analysis/trends` - Get analysis trends
- `GET /api/v1/analysis/summary` - Get analysis summary

### Action Plan APIs (5 endpoints):
- `POST /api/v1/plans/generate` - Generate action plan
- `GET /api/v1/plans/{plan_id}` - Get action plan
- `GET /api/v1/plans` - List action plans
- `PUT /api/v1/plans/{plan_id}` - Update action plan
- `DELETE /api/v1/plans/{plan_id}` - Delete action plan

### Execution APIs (5 endpoints):
- `POST /api/v1/execution/execute` - Execute action plan
- `GET /api/v1/execution/{exec_id}` - Get execution status
- `GET /api/v1/execution` - List executions
- `POST /api/v1/execution/{exec_id}/cancel` - Cancel execution
- `POST /api/v1/execution/{exec_id}/retry` - Retry execution

### Approval APIs (5 endpoints):
- `POST /api/v1/approvals/submit` - Submit for approval
- `GET /api/v1/approvals/{approval_id}` - Get approval status
- `GET /api/v1/approvals` - List approvals
- `POST /api/v1/approvals/{approval_id}/approve` - Approve
- `POST /api/v1/approvals/{approval_id}/reject` - Reject

### Governance APIs (9 endpoints):
- `POST /api/v1/governance/submit` - Submit action for governance review
- `GET /api/v1/governance/status/{governance_id}` - Get governance status
- `POST /api/v1/governance/approve` - Approve action with conditions
- `POST /api/v1/governance/reject` - Reject action with reason
- `POST /api/v1/governance/bulk-approve` - Bulk approve actions
- `GET /api/v1/governance/queue` - Get approval queue
- `GET /api/v1/governance/audit` - Query audit trail
- `GET /api/v1/governance/metrics` - Get governance metrics
- `POST /api/v1/governance/override` - Emergency override action

**Interactive Documentation**: http://localhost:8000/docs