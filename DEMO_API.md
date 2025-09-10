# 🤖 Co-Pilot API Demo - Intelligent Teammate in Action

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

# Using requests for API demo (can be adapted to OpenAI SDK patterns)
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
# Analyze transcript for intent and risk
response = requests.post(
    "http://localhost:8000/api/v1/analysis/analyze",
    json={"transcript_id": transcript_id}
)

analysis_data = response.json()
analysis_id = analysis_data["analysis_id"]
print(f"Analysis ID: {analysis_id}")
print(f"Customer Intent: {analysis_data['intent']}")
print(f"Sentiment Journey: {analysis_data['sentiment']}")
print(f"Urgency Level: {analysis_data['urgency']}")
print(f"Confidence Score: {analysis_data['confidence']}")
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
# Generate action plan from analysis
response = requests.post(
    "http://localhost:8000/api/v1/plans/generate",
    json={
        "analysis_id": analysis_id,
        "transcript_id": transcript_id
    }
)

plan_data = response.json()
plan_id = plan_data["plan_id"]
print(f"Action Plan: {plan_id}")
print(f"Total Actions: {plan_data['total_actions']}")
print(f"Routing Distribution: {plan_data['routing_summary']}")
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
# Get full action plan details
response = requests.get(f"http://localhost:8000/api/v1/plans/{plan_id}")
plan_details = response.json()

print("📄 Four-Layer Action Plan:")
for layer in ["borrower_plan", "advisor_plan", "supervisor_plan", "leadership_plan"]:
    actions = plan_details[layer]["actions"]
    print(f"\n🎯 {layer.replace('_', ' ').title()}: {len(actions)} actions")
    for action in actions[:2]:  # Show first 2 actions
        print(f"  • {action['description']} (Risk: {action['risk_score']:.2f})")
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

## Step 5. Submit Plan for Approval Workflow

**Co-Pilot Mode**: ⚙️ **Execute Mode** - Initiating approval workflow

**Purpose**: Submit the action plan through the approval workflow system.

### API Call (curl):
```bash
curl -X POST "http://localhost:8000/api/v1/approvals/submit" \
     -H "Content-Type: application/json" \
     -d '{
       "plan_id": "'$PLAN_ID'",
       "submitted_by": "advisor_mike",
       "priority": "high",
       "notes": "Customer escalation requires immediate supervisor review"
     }'
```

### Python SDK Example:
```python
# Submit plan for approval
response = requests.post(
    "http://localhost:8000/api/v1/approvals/submit",
    json={
        "plan_id": plan_id,
        "submitted_by": "advisor_mike",
        "priority": "high",
        "notes": "Customer escalation requires immediate supervisor review"
    }
)

approval_data = response.json()
approval_id = approval_data["approval_id"]
print(f"Approval ID: {approval_id}")
print(f"Status: {approval_data['status']}")
```

### Expected Response:
```json
{
  "approval_id": "approval_20241201_001",
  "plan_id": "plan_20241201_001",
  "status": "pending_approval",
  "submitted_by": "advisor_mike",
  "submitted_at": "2024-12-01T15:30:22Z",
  "priority": "high",
  "approval_route": "supervisor_approval",
  "estimated_approval_time": "2-4 hours"
}
```

### Track Variable:
```bash
export APPROVAL_ID="approval_20241201_001"
```

---

## Step 6. List Pending Approvals & Approve Actions

**Co-Pilot Mode**: ⚙️ **Execute Mode** - Human oversight in approval workflow

**Purpose**: Review approval queue and approve/reject specific actions.

### List Pending Approvals:
```bash
curl -X GET "http://localhost:8000/api/v1/approvals?status=pending"
```

### Approve Specific Action:
```bash
curl -X POST "http://localhost:8000/api/v1/approvals/$APPROVAL_ID/approve" \
     -H "Content-Type: application/json" \
     -d '{
       "approved_by": "supervisor_jane",
       "notes": "Approved with documentation requirements",
       "conditions": ["Ensure CFPB compliance documentation", "Follow up within 48 hours"]
     }'
```

### Python SDK Example:
```python
# List pending approvals
response = requests.get("http://localhost:8000/api/v1/approvals?status=pending")
pending_approvals = response.json()

print(f"📋 Pending Approvals: {len(pending_approvals['approvals'])} items")

# Approve the plan
response = requests.post(
    f"http://localhost:8000/api/v1/approvals/{approval_id}/approve",
    json={
        "approved_by": "supervisor_jane",
        "notes": "Approved with documentation requirements",
        "conditions": ["Ensure CFPB compliance documentation", "Follow up within 48 hours"]
    }
)

approval_result = response.json()
print(f"Approval Status: {approval_result['status']}")
```

### Expected Response:
```json
{
  "approval_id": "approval_20241201_001",
  "plan_id": "plan_20241201_001",
  "status": "approved",
  "approved_by": "supervisor_jane",
  "approved_at": "2024-12-01T16:15:30Z",
  "conditions": ["Ensure CFPB compliance documentation", "Follow up within 48 hours"],
  "next_step": "ready_for_execution"
}
```

### Success Indicators:
- ✅ Approval status changed to "approved"
- ✅ Approver and timestamp recorded
- ✅ Conditional approvals properly logged
- ✅ Plan ready for execution

---

## Step 7. Execute Approved Action Plan

**Co-Pilot Mode**: ⚙️ **Execute Mode** - Co-Pilot executing actions in background

**Purpose**: Execute approved actions with actor simulation and artifact generation.

### API Call (curl):
```bash
curl -X POST "http://localhost:8000/api/v1/execution/execute" \
     -H "Content-Type: application/json" \
     -d '{
       "plan_id": "'$PLAN_ID'",
       "execution_mode": "full",
       "actor_simulation": true,
       "generate_artifacts": true
     }'
```

### Python SDK Example:
```python
# Execute the approved plan
response = requests.post(
    "http://localhost:8000/api/v1/execution/execute",
    json={
        "plan_id": plan_id,
        "execution_mode": "full",
        "actor_simulation": true,
        "generate_artifacts": true
    }
)

execution_data = response.json()
execution_id = execution_data["execution_id"]
print(f"Execution ID: {execution_id}")
print(f"Actions Executed: {execution_data['actions_executed']}")
print(f"Artifacts Created: {execution_data['artifacts_created']}")
```

### Expected Response:
```json
{
  "execution_id": "exec_20241201_001",
  "plan_id": "plan_20241201_001",
  "status": "completed",
  "actions_executed": 8,
  "actions_skipped": 4,
  "artifacts_created": 6,
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
  "success_rate": 0.89
}
```

### Track Variable:
```bash
export EXECUTION_ID="exec_20241201_001"
```

### Success Indicators:
- ✅ Execution completed successfully
- ✅ Actions executed vs skipped properly reported
- ✅ Artifacts generated (emails, documents, callbacks)
- ✅ Success rate >85%

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
# Get detailed execution status
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
# Get all artifacts from execution
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

## Step 10. Get Analysis & Execution Metrics

**Co-Pilot Mode**: 📊 **Reflect Mode** - Performance analytics and Observer Agent simulation

**Purpose**: Review system performance metrics and simulate Observer Agent evaluation.

### API Calls (curl):
```bash
# Get analysis metrics
curl -X GET "http://localhost:8000/api/v1/analysis/metrics"

# Get execution metrics  
curl -X GET "http://localhost:8000/api/v1/execution/metrics"

# Get analysis trends
curl -X GET "http://localhost:8000/api/v1/analysis/trends"
```

### Python SDK Example:
```python
# Get comprehensive metrics
analysis_metrics = requests.get("http://localhost:8000/api/v1/analysis/metrics").json()
execution_metrics = requests.get("http://localhost:8000/api/v1/execution/metrics").json()

print("📊 Co-Pilot Performance Dashboard:")
print(f"Total Analyses: {analysis_metrics['total_analyses']}")
print(f"Average Confidence: {analysis_metrics['average_confidence']:.1%}")
print(f"Execution Success Rate: {execution_metrics['success_rate']:.1%}")
print(f"Average Execution Time: {execution_metrics['avg_duration_minutes']:.1f} min")

# Simulate Observer Agent Evaluation
observer_evaluation = {
    "overall_satisfaction": 4.2,
    "execution_quality": 4.1,
    "issues_identified": [
        "Documentation completeness could be improved",
        "Approval workflow took longer than expected"
    ],
    "improvement_opportunities": [
        "Implement pre-execution document validation",
        "Add automated status notifications",
        "Optimize supervisor approval routing"
    ],
    "actor_performance": {
        "advisor": 4.5,
        "supervisor": 3.8,
        "leadership": 4.2,
        "system": 4.6
    }
}

print("\n👁️ Observer Agent Evaluation (Simulated):")
print(f"Overall Satisfaction: {observer_evaluation['overall_satisfaction']}/5.0")
print(f"Execution Quality: {observer_evaluation['execution_quality']}/5.0")
print("\n🔍 Issues Identified:")
for issue in observer_evaluation['issues_identified']:
    print(f"  • {issue}")
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
  }
}
```

---

## Step 11. Demonstrate Learning Loop (Second Iteration)

**Co-Pilot Mode**: 📊 **Reflect Mode** - Continuous learning and improvement

**Purpose**: Execute a second similar scenario to demonstrate Observer Agent feedback and learning velocity.

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
# Second iteration - demonstrating learning
print("🔄 Learning Loop Demonstration:")

# Generate second transcript
response = requests.post("http://localhost:8000/api/v1/transcripts/generate", json={
    "scenario": "PMI Removal Follow-up with Updated Compliance Requirements",
    "urgency": "medium",
    "learning_context": "previous_pmi_dispute"
})
transcript_id_2 = response.json()["transcript_id"]

# Analyze (should show improved confidence)
response = requests.post("http://localhost:8000/api/v1/analysis/analyze", 
                        json={"transcript_id": transcript_id_2})
analysis_2 = response.json()

# Generate action plan (should show improved routing)
response = requests.post("http://localhost:8000/api/v1/plans/generate",
                        json={"analysis_id": analysis_2["analysis_id"]})
plan_2 = response.json()

print(f"Learning Improvements:")
print(f"  Confidence: {analysis_2['confidence']:.3f} (vs {analysis_data['confidence']:.3f})")
print(f"  Actions Generated: {plan_2['total_actions']} (vs {plan_data['total_actions']})")
print(f"  Auto-approved: {plan_2['routing_summary']['auto_approved']} (vs {plan_data['routing_summary']['auto_approved']})")

# Calculate learning velocity
learning_velocity = (analysis_2['confidence'] - analysis_data['confidence']) / analysis_data['confidence']
print(f"  Learning Velocity: {learning_velocity:.3f} ({'+' if learning_velocity > 0 else ''}{learning_velocity:.1%})")
```

### Learning Velocity Metrics:
```json
{
  "learning_comparison": {
    "first_iteration": {
      "confidence": 0.89,
      "total_actions": 12,
      "auto_approved": 3,
      "execution_time": 225
    },
    "second_iteration": {
      "confidence": 0.93,
      "total_actions": 10,
      "auto_approved": 5,
      "execution_time": 180
    },
    "improvements": {
      "confidence_gain": 0.04,
      "efficiency_gain": 0.20,
      "auto_approval_rate": 0.67,
      "learning_velocity": 0.85
    }
  }
}
```

---

## 🎯 Success Criteria & Validation

### ✅ Core Workflow Completed
- [ ] Complex customer call generated with high urgency
- [ ] AI analysis with >80% confidence score
- [ ] Four-layer action plan with ~12 actions
- [ ] Multi-level approval workflow demonstrated
- [ ] Execution with >85% success rate
- [ ] 5+ artifacts generated (emails, documents, callbacks)

### ✅ Co-Pilot Vision Demonstrated
- [ ] **Plan Mode**: Real-time action planning with risk assessment
- [ ] **Execute Mode**: Background co-execution with actor simulation
- [ ] **Reflect Mode**: Post-execution analysis with Observer feedback

### ✅ API Integration Proven
- [ ] All 20 new API endpoints functional
- [ ] Proper error handling and response formats
- [ ] Integration with existing CLI backend services
- [ ] Performance metrics available via API

### ✅ Learning Loop Functional
- [ ] Second iteration shows improved confidence
- [ ] Better action routing (more auto-approvals)
- [ ] Faster execution times
- [ ] Learning velocity >0.8 (positive improvement trend)

---

## 🚀 Advanced API Scenarios

### Bulk Operations:
```bash
# Analyze multiple transcripts
curl -X POST "http://localhost:8000/api/v1/analysis/analyze" \
     -H "Content-Type: application/json" \
     -d '{
       "transcript_ids": ["transcript_001", "transcript_002", "transcript_003"]
     }'
```

### Error Handling:
```bash
# Test error response
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

## 🎉 Demo Completion

**Congratulations!** You have successfully demonstrated the complete **Co-Pilot Intelligent Teammate** system via API:

### What You've Accomplished:
1. **🧭 Plan Mode**: Generated complex scenarios with real-time risk assessment
2. **⚙️ Execute Mode**: Automated multi-actor action execution with approval workflows  
3. **📊 Reflect Mode**: Performance monitoring with Observer Agent evaluation
4. **🔄 Learning Loop**: Demonstrated measurable improvement between iterations

### Co-Pilot Vision Realized:
- **Intelligent Teammate**: Co-executes alongside advisors, not just analyzes
- **Four-Layer Planning**: Borrower → Advisor → Supervisor → Leadership alignment
- **Approval Workflows**: Risk-based routing with human oversight
- **Continuous Learning**: Observer Agent feedback improves future performance

### Technical Foundation:
- **20 FastAPI Endpoints**: Complete REST API for enterprise integration
- **Real-time Processing**: Sub-4 minute end-to-end workflow execution
- **Artifact Generation**: Tangible outputs (emails, documents, callbacks)
- **Scalable Architecture**: Ready for UI development and enterprise deployment

The Co-Pilot is now operational as an **Intelligent Teammate** ready to transform mortgage servicing operations! 🤖✨

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

**Interactive Documentation**: http://localhost:8000/docs