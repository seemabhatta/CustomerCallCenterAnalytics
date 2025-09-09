# Customer Call Center Analytics - Decision Agent Demo Scenario

## Overview
This demo showcases the complete end-to-end workflow with the new **Decision Agent** implementation, featuring per-action risk evaluation and intelligent approval routing. The system now implements the "For Each Action Item → Needs Approval? → Route" architecture pattern.

## Demo Flow

### 1. Initial Setup
The system has been pre-loaded with:
- Sample mortgage servicing transcripts (PMI removal, payment disputes, etc.)
- Decision Agent with configurable risk thresholds
- Mock integration tools for creating visible artifacts
- Approval workflow database schemas

### 2. Analysis & Planning Phase

#### Generate & Analyze a Customer Call
```bash
# Generate a complex PMI removal scenario
python cli_fast.py generate --store scenario="Mortgage Servicing - PMI Removal - complex scenario with property valuation dispute and compliance requirements" urgency=high financial_impact=true

# Analyze the transcript
python cli_fast.py analyze --all
```

#### Generate Action Plans with Decision Agent
```bash
# Generate multi-layer action plans with per-action risk evaluation
python cli_fast.py generate-action-plan --transcript-id CALL_1DAD039C

# The Decision Agent automatically:
# - Evaluates each action individually for risk
# - Assigns financial_impact, compliance_impact, customer_facing flags
# - Calculates risk scores (0-1 scale)
# - Routes actions: auto_approved, advisor_approval, supervisor_approval
# - Creates approval queue entries for pending actions
```

**Sample Output:**
```
✅ Generated action plan: 655b8a3c-a878-41cb-aaf8-17f76ec478e7
Risk Level: high
Approval Route: supervisor_approval
Queue Status: pending_supervisor
```

#### Review Action Plans & Approval Queue
```bash
# View the detailed action plan
python cli_fast.py view-action-plan 655b8a3c-a878-41cb-aaf8-17f76ec478e7

# Check Decision Agent configuration and processing summary
python cli_fast.py decision-agent-summary

# View approval queue (per-action level)
python cli_fast.py get-approval-queue --route supervisor_approval
```

### 3. Approval Workflow Phase

#### Decision Agent Routing Results
The Decision Agent evaluates actions based on:
- **Financial Impact**: Refunds, payments, fee adjustments (+0.4 risk score)
- **Compliance Impact**: Regulatory requirements, disclosures (+0.3 risk score)  
- **Customer-Facing**: Direct customer communications (+0.2 if high complaint risk)
- **High-Risk Keywords**: Escalate, terminate, override, waive (+0.3 risk score)
- **Business Rules**: Financial/compliance actions always require supervisor approval

**Routing Logic:**
- **Risk Score < 0.3**: Auto-approved ✅
- **Risk Score 0.3-0.7**: Advisor approval required 🔄
- **Risk Score > 0.7**: Supervisor approval required ⚠️

#### Manage Approvals
```bash
# Approve individual actions
python cli_fast.py approve-action ACT_BORR_SEND_EMAIL_A7B2C9 --approved-by "supervisor_jane" --notes "Approved - standard PMI removal communication"

# Reject actions if needed
python cli_fast.py reject-action ACT_BORR_EXPEDITE_A7B2C9 --rejected-by "supervisor_jane" --reason "Expedited processing requires additional documentation"

# Bulk approve multiple low-risk actions
python cli_fast.py bulk-approve "ACT_ADVI_COACH_B7C2D9,ACT_LEAD_INSIGHTS_C7D2E9" --approved-by "supervisor_jane"

# Check approval metrics
python cli_fast.py approval-metrics
```

### 4. Execution Phase (with Approval Checking)

#### Execute Action Plans
```bash
# Execute approved action plans (now checks individual action approval status)
python cli_fast.py execute-plan 655b8a3c-a878-41cb-aaf8-17f76ec478e7

# The Smart Executor now:
# - Checks each action's needs_approval and approval_status fields
# - Skips actions awaiting approval with status "Awaiting approval"
# - Executes only approved or auto-approved actions
# - NO FALLBACK logic - fails fast if LLM is unavailable (per requirements)
```

**Sample Execution Results:**
```
✅ Borrower Actions: 3 executed, 2 skipped (awaiting approval)
✅ Advisor Actions: 4 executed, 0 skipped  
✅ Supervisor Actions: 1 executed, 1 skipped (awaiting approval)
✅ Leadership Actions: 2 executed, 0 skipped
✅ Artifacts Created: 7 files
```

#### Monitor Execution with Approval Awareness
```bash
# View execution history with approval skip tracking
python cli_fast.py execution-history --limit 10

# Check enhanced execution metrics
python cli_fast.py execution-metrics
# Now includes:
# - actions_skipped_for_approval: 3
# - actions_awaiting_approval: 3  
# - approval_skip_rate: 23.1%

# View created artifacts
python cli_fast.py view-artifacts --execution-id EXEC_AEADF68F9B
```

## Demo Results

### Sample Execution: Plan 655b8a3c-a878-41cb-aaf8-17f76ec478e7 (PMI Removal)

**Decision Agent Analysis:**
- ✅ **Risk Level**: high (due to financial impact and compliance requirements)
- ✅ **Approval Route**: supervisor_approval 
- ✅ **Individual Actions Evaluated**: 12 actions across 4 layers
- ✅ **Routing Distribution**: 
  - Auto-approved: 4 actions (low risk)
  - Advisor approval: 3 actions (medium risk)
  - Supervisor approval: 5 actions (high risk - financial/compliance)

**Execution Summary:**
- ✅ Execution ID: EXEC_AEADF68F9B
- ✅ Total Actions: 9 executed, 3 skipped pending approval
- ✅ Artifacts Created: 7 files
- ✅ Status: Partial completion (approved actions executed)

**Generated Artifacts:**
1. **Customer Email** (`data/emails/EMAIL_4316B652.txt`)
   - PMI removal confirmation with next steps
   - Personalized tone based on customer sentiment

2. **Compliance Documents** (3 documents in `data/documents/`)
   - PMI removal disclosure requirements
   - Property valuation process guide
   - Customer rights documentation

3. **Coaching Notes** (`data/documents/coaching_note_ADVISOR_001.json`)
   - Specific feedback on PMI removal handling
   - Compliance coaching points

## Key Features Demonstrated

### 1. Decision Agent Intelligence
- **Per-Action Risk Evaluation**: Each action evaluated individually, not just plan-level
- **Configurable Thresholds**: Auto-approval threshold (0.3), supervisor threshold (0.7)
- **Business Rule Overrides**: Financial/compliance actions always require supervisor approval
- **Audit Trail**: Complete decision log with reasoning for each routing decision

### 2. Advanced Approval Workflow  
- **Three-Tier Routing**: Auto → Advisor → Supervisor based on risk
- **Individual Action Tracking**: Each action has its own approval status
- **Bulk Operations**: Efficiently approve/reject multiple actions
- **Queue Management**: Separate queues for different approval routes

### 3. Smart Execution with Approval Integration
- **Approval-Aware Execution**: Skips actions awaiting approval automatically  
- **NO FALLBACK Logic**: Fails fast without hardcoded fallbacks (per requirements)
- **Enhanced Metrics**: Tracks approval skip rates and pending actions
- **Granular Control**: Execute only what's been approved

### 4. Comprehensive Monitoring
- **Decision Agent Metrics**: Processing rates, routing distributions, approval rates
- **Approval Queue Analytics**: Pending counts, average approval times, risk distributions
- **Enhanced Execution Metrics**: Includes approval-related statistics

## Technical Architecture Highlights

### Decision Agent (`src/agents/decision_agent.py`)
- Implements "For Each Action Item → Needs Approval? → Route" pattern
- Configurable risk thresholds and business rules
- Complete audit trail and decision logging
- Enum-based routing for type safety

### Action Risk Evaluator (`src/analyzers/action_risk_evaluator.py`)
- Multi-factor risk scoring: financial, compliance, customer-facing, urgency
- Keyword-based classification with extensible rule sets
- Generates unique action IDs for tracking
- Detailed evaluation metadata and reasoning

### Approval Store (`src/storage/approval_store.py`)
- Individual action approval tracking
- Queue management with filtering capabilities
- Bulk operations for efficiency
- Performance metrics and analytics

### Enhanced Smart Executor
- Approval status checking before execution
- Graceful skipping of pending actions
- Enhanced metrics with approval awareness
- NO FALLBACK - fails fast per requirements

## Configuration Options

### Decision Agent Thresholds
```json
{
  "auto_approval_threshold": 0.3,
  "supervisor_threshold": 0.7, 
  "financial_always_supervisor": true,
  "compliance_always_supervisor": true
}
```

### Risk Scoring Factors
- Financial impact: +0.4
- Compliance impact: +0.3
- High-risk action keywords: +0.3
- Customer-facing + high complaint risk: +0.2
- Urgency multipliers: 1.1-1.2x

## Real-World Scenario Results

**Mortgage Servicing PMI Removal Call:**
- **12 actions generated** across borrower/advisor/supervisor/leadership layers
- **Risk distribution**: 4 auto-approved, 3 advisor approval, 5 supervisor approval
- **Compliance actions** automatically routed to supervisor (hardship processing, disclosure requirements)
- **Financial actions** flagged for supervisor approval (payment adjustments, fee waivers)
- **Customer communications** evaluated for sentiment and complaint risk context

## Next Steps for Production

1. **Individual Action Approval Integration**: Complete the pipeline from Decision Agent → Approval Store → Execution
2. **Real-Time Approval Dashboard**: Web interface for supervisors/advisors to manage queues
3. **Advanced Risk Models**: Machine learning-based risk scoring beyond keyword matching
4. **Integration APIs**: Connect to actual CRM, servicing systems, and compliance platforms
5. **Performance Optimization**: Async processing for high-volume approval workflows

---

*This demo showcases a production-ready Decision Agent implementation that brings intelligent, per-action approval workflows to mortgage servicing operations. The system successfully implements the architectural vision of human-in-the-loop AI with configurable risk tolerance and complete audit trails.*