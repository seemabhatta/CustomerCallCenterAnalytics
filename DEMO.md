# 🎬 Customer Call Center Analytics - LLM-Executable Demo Script

> **Prerequisites:** 
> 1. Activate virtual environment: `source venv/bin/activate`
> 2. Ensure the backend is running: `./start_services.py`

---

## 📊 Expected Outcomes

Upon successful completion of this demo, you should have achieved the following outcomes. Use this checklist to validate your execution:

### Generated Data
- [ ] 1 transcript with ID format: `transcript_YYYYMMDD_XXX`
- [ ] 1 analysis with ID format: `analysis_YYYYMMDD_XXX`  
- [ ] 1 action plan with ID format: `plan_YYYYMMDD_XXX`
- [ ] 1 execution with ID format: `exec_YYYYMMDD_XXX`

### Action Routing Results
- [ ] ~12 total actions generated across 4 layers (borrower/advisor/supervisor/leadership)
- [ ] Actions distributed approximately:
  - 30-40% auto-approved (low risk actions)
  - 25-35% advisor approval required (medium risk actions)
  - 30-40% supervisor approval required (high risk actions)

### Approval Workflow
- [ ] 3-5 actions in advisor approval queue initially
- [ ] 4-6 actions in supervisor approval queue initially
- [ ] All approved actions executed successfully
- [ ] Pending actions properly skipped during execution

### Execution Artifacts
- [ ] 5-8 artifacts created (emails, documents, callbacks)
- [ ] Execution success rate > 85%
- [ ] Proper actor assignments (Advisor, Supervisor, Leadership, Customer)
- [ ] All executed actions have audit trail with timestamps

### Observer Agent Evaluation
- [ ] Overall satisfaction score: 3.5-4.5/5.0
- [ ] 1-3 improvement opportunities identified
- [ ] Actor performance assessments generated
- [ ] Feedback for Decision Agent improvements created
- [ ] Lessons learned dataset populated

### Learning Loop Validation (Step 11)
- [ ] Second iteration shows improved routing efficiency
- [ ] Learning velocity > 0.8 (positive improvement trend)
- [ ] Reduced error rate compared to first iteration
- [ ] Pattern recognition and systemic improvements demonstrated

### Final Validation Commands
After completion, these commands should return meaningful data:
```bash
python cli_fast.py stats                                      # Shows 2+ transcripts
python cli_fast.py execution-history --limit 2               # Shows 2 executions  
python cli_fast.py approval-metrics                          # Shows approval statistics
python cli_fast.py execution-metrics --include-observer-feedback  # Observer evaluation
```

### Success Criteria Summary
- **Total Objects Created**: 4+ (transcript, analysis, plan, execution)
- **Actions Processed**: 12+ actions routed through Decision Agent
- **Approval Workflow**: Demonstrated multi-level approval routing
- **Execution Results**: >85% success rate with proper actor simulation
- **Observer Feedback**: Complete evaluation cycle with improvement recommendations
- **Learning Demonstrated**: Second iteration shows measurable improvement

---

## Step 1. Generate a Conversation
**Purpose:** Create a realistic mortgage servicing call transcript with high complexity and compliance requirements.

**Command:**
```bash
python cli_fast.py generate --store scenario="Mortgage Servicing - PMI Removal - dispute with property valuation and compliance requirements" urgency=high financial_impact=true
```

**Success Indicator:**
- Output contains: `✅ Transcript stored with ID: transcript_YYYYMMDD_XXX`
- JSON response shows `"success": true` and `"stored": true`

**Track Variable:**
- Save the transcript ID as `TRANSCRIPT_ID` for use in subsequent steps
- Example format: `transcript_20241201_001`

**Validation:**
```bash
python cli_fast.py list  # Should show the new transcript in the table
```

**Expected Content:**
- Borrower-advisor dialog with PMI removal dispute scenario
- High urgency and financial impact flags
- Compliance requirements and property valuation issues mentioned

---

## Step 2. Analyze the Conversation
**Purpose:** Extract customer intent, sentiment, and risk factors using AI analysis.

**Command:** *(Replace TRANSCRIPT_ID with actual ID from Step 1)*
```bash
python cli_fast.py analyze --transcript-id TRANSCRIPT_ID
```

**Success Indicator:**
- Output contains: `✅ Analysis completed for transcript: TRANSCRIPT_ID`
- Analysis results show sentiment, intent, and risk scores
- Analysis ID is generated and displayed

**Track Variable:**
- Save the analysis ID as `ANALYSIS_ID` for reference
- Example format: `analysis_20241201_001`

**Validation:**
```bash
python cli_fast.py analysis-metrics  # Should show 1+ completed analysis
```

**Expected Results:**
- Customer sentiment analysis (frustrated/concerned due to dispute)
- Primary intent: PMI removal assistance
- Risk factors: financial impact, compliance concerns
- Delinquency, churn, and complaint risk scores
- Structured metadata for downstream processing

---

## Step 3. Generate an Action Plan (Decision Agent)
**Purpose:** Create comprehensive four-layer action plan with Decision Agent risk evaluation and approval routing.

**Command:** *(Use TRANSCRIPT_ID from Step 1)*
```bash
python cli_fast.py generate-action-plan --transcript-id TRANSCRIPT_ID
```
*Alternative: Use analysis ID if you have it from Step 2*

**Success Indicator:**
- Output contains: `✅ Action Plan PLAN_ID created`
- Shows total actions count (~12 actions expected)
- Displays routing distribution across approval levels
- Queue status shows pending approvals by route

**Track Variable:**
- Save the plan ID as `PLAN_ID` for execution steps
- Example format: `plan_20241201_001`

**Validation:**
```bash
python cli_fast.py action-plan-summary  # Should show 1+ plan created
```

**Expected Output:**
```
✅ Action Plan plan_20241201_001 created
- Total actions: ~12
- Routing: 4 auto-approved, 3 advisor_approval, 5 supervisor_approval
- Queue status: pending_advisor (3), pending_supervisor (5)
```

**Expected Plan Structure:**
- **Borrower layer**: Customer-facing actions (immediate + follow-up)
- **Advisor layer**: Internal process actions
- **Supervisor layer**: Escalation and approval actions  
- **Leadership layer**: Strategic and policy actions
- Each action has risk scoring and appropriate approval routing

---

## Step 4. Review the Action Plan
**Purpose:** Inspect generated actions, risk assessments, and approval routing decisions.

**Command:** *(Use PLAN_ID from Step 3)*
```bash
python cli_fast.py view-action-plan PLAN_ID
# Optional layer-specific view:
python cli_fast.py view-action-plan --layer supervisor PLAN_ID
```

**Success Indicator:**
- Displays complete action breakdown by layer
- Shows individual action IDs, risk scores, and routing decisions
- Each action has clear approval requirements

**Track Variables:**
- Note specific action IDs for approval steps (e.g., `action_20241201_002`)
- Identify high-risk supervisor approval actions

**Expected Display:**
- Action list with risk scores and approval routes
- Example actions:
  - `action_20241201_001` → risk 0.25 → auto
  - `action_20241201_002` → risk 0.80 → supervisor_approval

---

## Step 5. Check Approval Queues (Action-Level)
**Purpose:** Review actions requiring manual approval before execution.

**Commands:**
```bash
python cli_fast.py get-approval-queue --route supervisor_approval
python cli_fast.py get-approval-queue --route advisor_approval
```

**Success Indicator:**
- Displays actions awaiting approval with risk context
- Shows action IDs, risk scores, and approval requirements
- Queue contains expected number of pending actions

**Track Variables:**
- Note action IDs requiring supervisor approval (for Step 6)
- Note action IDs requiring advisor approval (for Step 6)

**Expected Results:**
- 3-6 actions in supervisor approval queue
- 2-4 actions in advisor approval queue
- Each action shows ID, risk score, and reason for approval requirement

**Alternative:** For plan-level approvals:
```bash
python cli_fast.py action-plan-queue --status pending_approval
```

---

## Step 6. Approve / Reject Actions (Action-Level)
**Purpose:** Simulate human approval workflow by approving/rejecting specific actions.

**Commands:** *(Replace ACTION_IDs with actual IDs from Step 5)*
```bash
# Approve supervisor-gated financial action
python cli_fast.py approve-action ACTION_ID_HIGH_RISK --approved-by "supervisor_jane" --notes "Approved with documentation"

# Reject expedited processing (optional)
python cli_fast.py reject-action ACTION_ID_EXPEDITE --rejected-by "supervisor_jane" --reason "Requires supporting docs"

# Bulk approve advisor items
python cli_fast.py bulk-approve "ACTION_ID_1,ACTION_ID_2" --approved-by "advisor_mike" --notes "Routine coaching items"
```

**Success Indicator:**
- Each approval shows success confirmation
- Approval metrics update with new statuses
- Actions move from pending to approved status

**Validation:**
```bash
python cli_fast.py approval-metrics  # Should show updated approval counts
```

**Expected Results:**
- Most high-priority actions approved
- Some actions may be rejected for demonstration
- Approval workflow demonstrates multi-level human oversight
- Updated metrics show approval/rejection counts

---

## Step 6.5 Approve the Plan (Plan-Level)
**Purpose:** Approve the overall action plan for execution (may be required depending on configuration).

**Command:** *(Use PLAN_ID from Step 3)*
```bash
python cli_fast.py approve-action-plan PLAN_ID --approver "supervisor_jane"
```

**Success Indicator:**
- Output shows: `✅ Action plan PLAN_ID approved`
- Plan status changes to `approved`
- Approver and timestamp logged in audit trail

**Validation:**
```bash
python cli_fast.py action-plan-queue --status approved  # Should show approved plan
```

---

## Step 7. Execute the Plan (Approval-Aware)
**Purpose:** Execute approved actions with actor simulation and artifact generation.

**Commands:** *(Use PLAN_ID from Step 3)*
```bash
# Optional preview (recommended)
python cli_fast.py execute-plan --dry-run PLAN_ID

# Execute approved actions
python cli_fast.py execute-plan PLAN_ID
```

**Success Indicator:**
- Output shows: `✅ Execution completed successfully!`
- Execution ID is generated (format: `exec_YYYYMMDD_XXX`)
- Shows count of executed vs skipped actions
- Artifacts are created and counted

**Track Variable:**
- Save the execution ID as `EXECUTION_ID` for monitoring steps

**Expected Output:**
```
✅ Execution completed successfully!
Execution ID: exec_20241201_001
Total Actions Executed: 8-10, Skipped (pending): 2-4
Artifacts Created: 5-8
```

**Expected Results:**
- Only approved actions are executed
- Pending actions are properly skipped
- Artifacts generated: emails, callbacks, documents
- Actor assignments: Advisor, Supervisor, Leadership, Customer

---

## Step 8. Monitor Execution & Metrics
**Purpose:** Review execution results and system performance metrics.

**Commands:**
```bash
python cli_fast.py execution-history --limit 5
python cli_fast.py execution-metrics
python cli_fast.py approval-metrics
```

**Success Indicator:**
- Execution history shows completed execution with EXECUTION_ID
- Metrics display success rates >85%
- Approval metrics show workflow effectiveness

**Expected Results:**
- Recent executions list with status and artifact counts
- Actions executed vs skipped statistics
- Approval workflow performance metrics
- Success rates, approval rates, and risk distribution
- Counts like `actions_skipped_for_approval` and `approval_skip_rate`

---

## Step 9. View Artifacts
**Purpose:** Examine generated execution artifacts (emails, documents, callbacks).

**Commands:**
```bash
python cli_fast.py view-artifacts --type emails --limit 20
python cli_fast.py view-artifacts --type documents
python cli_fast.py view-artifacts --type callbacks
```

**Success Indicator:**
- Displays list of generated artifacts with timestamps
- Shows artifact content previews
- File sizes and creation dates are visible

**Expected Results:**
- 3-5 email artifacts (payment plans, follow-ups, notifications)
- 1-2 document artifacts (agreements, forms, receipts)
- 2-3 callback records (scheduled calls, reminders)
- Each artifact shows relevant customer and scenario information

---

## Step 10. Observer Agent Evaluation & Feedback Loop
**Purpose:** Observer Agent evaluates execution quality and generates continuous learning feedback.

**Commands:**
```bash
# View execution results with Observer Agent evaluation
python cli_fast.py execution-metrics --include-observer-feedback

# Check continuous learning insights
python cli_fast.py analysis-metrics --include-learning-patterns

# View Observer Agent lessons learned
python cli_fast.py decision-agent-summary --include-feedback-loop
```

**Success Indicator:**
- Observer evaluation displayed with satisfaction scores
- Improvement opportunities identified (1-3 items)
- Actor performance assessments generated
- Feedback for Decision Agent improvements provided

**Expected Results:**
```
📊 Observer Agent Evaluation - EXECUTION_ID
Overall Satisfaction: satisfactory (3.5-4.5/5.0)
Execution Quality: 3.8-4.2/5.0
Issues Identified: 1-3 (e.g., missing documentation, delays)
Improvement Opportunities: 2-4 actionable recommendations
Actor Performance: 
  - Advisor: excellent (4.5+/5.0)
  - Supervisor: good-needs improvement (3.0-4.0/5.0)
  - Leadership: good (4.0+/5.0)
Decision Agent Feedback: Specific routing/process improvements
```

**Learning Outcomes:**
- Lessons learned dataset populated
- Pattern recognition for similar scenarios
- Decision Agent receives actionable improvement feedback
- System demonstrates self-evaluation capability

---

## Step 11. Complete Feedback Loop Demonstration
**Purpose:** Execute a second similar scenario to demonstrate continuous learning and improvement.

**Commands:**
```bash
# Generate another similar scenario to test learning
python cli_fast.py generate --store scenario="Mortgage Servicing - PMI Removal - similar compliance dispute" urgency=high financial_impact=true

# Analyze and generate action plan (should show Observer improvements)
python cli_fast.py analyze --transcript-id NEW_TRANSCRIPT_ID
python cli_fast.py generate-action-plan --transcript-id NEW_TRANSCRIPT_ID

# Approve and execute the new plan
python cli_fast.py approve-action-plan NEW_PLAN_ID --approver "supervisor_jane"
python cli_fast.py execute-plan NEW_PLAN_ID

# Compare learning velocity and improvements
python cli_fast.py execution-metrics --compare-previous --include-learning-velocity
```

**Success Indicator:**
- Second transcript generated with similar scenario
- Action plan shows improved routing efficiency
- Execution demonstrates reduced errors/improved performance
- Learning velocity metrics show positive trend (>0.8)

**Track Variables:**
- Save NEW_TRANSCRIPT_ID, NEW_PLAN_ID for comparison

**Expected Learning Outcomes:**
- **Improved Routing**: Better risk assessment based on previous execution
- **Faster Execution**: Reduced processing time due to learned patterns
- **Higher Quality**: Fewer errors, better actor assignments
- **Pattern Recognition**: System identifies similar scenarios automatically
- **Learning Velocity >0.8**: Demonstrates positive improvement trend

**Comparison Metrics:**
- Success rate: Should be higher than first iteration
- Error rate: Should be lower than first iteration
- Processing efficiency: Faster approval/execution workflow
- Customer satisfaction: Higher predicted satisfaction scores

---

---

# 🎯 Final Validation & Demo Completion

## Completion Checklist

Upon successful execution of all 11 steps, verify these outcomes:

### ✅ **Core Workflow Completed**
- [ ] 2 transcripts generated (original + learning loop scenario)
- [ ] 2 analyses completed with risk assessment
- [ ] 2 action plans created with ~12 actions each
- [ ] 2 executions completed with artifacts generated
- [ ] Decision Agent routing demonstrated across approval levels
- [ ] Observer Agent feedback loop functional

### ✅ **Approval Workflow Demonstrated**
- [ ] Multi-level approval routing (auto/advisor/supervisor)
- [ ] Manual approval/rejection process executed
- [ ] Pending actions properly skipped during execution
- [ ] Audit trail maintained for all decisions

### ✅ **Execution & Artifacts**
- [ ] >85% execution success rate achieved
- [ ] 10-15 total artifacts created across both executions
- [ ] Actor assignments properly distributed
- [ ] Email, document, and callback artifacts generated

### ✅ **Observer Agent & Learning**
- [ ] Observer evaluations completed for both executions
- [ ] Satisfaction scores: 3.5-4.5/5.0 range
- [ ] Improvement opportunities identified and documented
- [ ] Learning velocity >0.8 demonstrated in second iteration
- [ ] Decision Agent received actionable feedback

### ✅ **System Metrics Available**
Run these final validation commands:
```bash
python cli_fast.py stats                                         # Shows 2+ transcripts
python cli_fast.py execution-history --limit 2                  # Shows both executions
python cli_fast.py approval-metrics                             # Shows approval workflow stats  
python cli_fast.py execution-metrics --include-observer-feedback # Observer evaluation summary
```

## 🏆 **Demo Success Criteria**

**Minimum Success Requirements:**
- **2 complete workflow cycles** (transcript → analysis → plan → execution)
- **Decision Agent routing** with risk-based approval requirements
- **Approval workflow** with manual approvals/rejections
- **Execution results** with >80% success rate and artifacts
- **Observer feedback** with quality evaluation and learning recommendations

**Excellence Indicators:**
- **Learning improvement** demonstrated between iterations
- **Pattern recognition** by Observer Agent
- **Workflow efficiency** gains in second execution
- **Complete audit trail** for compliance and quality review

## 🔄 **Continuous Learning Demonstrated**

The demo showcases a complete AI-powered customer service system with:

1. **Intelligent Analysis**: AI extracts customer intent and risk factors
2. **Smart Routing**: Decision Agent routes actions based on risk assessment  
3. **Human Oversight**: Multi-level approval workflow ensures compliance
4. **Automated Execution**: Actor-based simulation of real customer service actions
5. **Self-Improvement**: Observer Agent evaluates and provides feedback for continuous learning
6. **Measurable Progress**: Learning velocity metrics prove system improvement over time

**🎉 Congratulations! You have successfully demonstrated the complete Customer Call Center Analytics workflow with continuous learning capabilities.**
