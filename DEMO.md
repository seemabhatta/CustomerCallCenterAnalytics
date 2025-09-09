# 🎬 Decision Agent – Full Demo Script (Aligned to CLI Reference)

> **Prereq:** Ensure the backend is running:
> `python server.py`

---

## Step 1. Generate a Conversation
**Instruction:**
```bash
python cli_fast.py generate --store   scenario="Mortgage Servicing - PMI Removal - dispute with property valuation and compliance requirements"   urgency=high financial_impact=true
```

**Agent Expectations:**
- Store the generated transcript as an ID like `transcript_...` (capture the exact ID, e.g., `transcript_20241201_001`).
- Include borrower–advisor dialog with compliance requirements and financial implications.
- Print confirmation with transcript ID.

---

## Step 2. Analyze the Conversation
**Instruction:**
```bash
python cli_fast.py analyze --transcript-id transcript_20241201_001
```
*(Replace with the actual transcript ID from Step 1.)*

**Agent Expectations:**
- Enrich transcript with borrower sentiment, intent, compliance indicators.
- Produce structured metadata: delinquency, churn, complaint risk.
- Persist analysis and capture its ID (e.g., `analysis_20241201_001`).

---

## Step 3. Generate an Action Plan (Decision Agent)
**Instruction (either source is acceptable):**
```bash
# using analysis id
python cli_fast.py generate-action-plan --analysis-id analysis_20241201_001

# OR using transcript id
python cli_fast.py generate-action-plan --transcript-id transcript_20241201_001
```
**Agent Expectations:**
- Break down tasks into **borrower, advisor, supervisor, leadership** layers.
- Run **per-action risk evaluation** and set fields: `financial_impact`, `compliance_impact`, `customer_facing`, `risk_score (0–1)`, and `route` in `{auto, advisor_approval, supervisor_approval}`.
- Create a plan ID like `plan_20241201_001` (**capture the exact ID**).
- Place pending actions into approval queues per route.

**Sample Output:**
```
✅ Action Plan plan_20241201_001 created
- Total actions: 12
- Routing: 4 auto-approved, 3 advisor_approval, 5 supervisor_approval
- Queue status: pending_advisor (3), pending_supervisor (5)
```

---

## Step 4. Review the Action Plan
**Instruction:**
```bash
python cli_fast.py view-action-plan plan_20241201_001
# Optional (layer-specific):
python cli_fast.py view-action-plan --layer supervisor plan_20241201_001
```
**Agent Expectations:**
- Display action list with risk scores and approval routes.
- Example actions (note ID format):
  - `action_20241201_001` → risk 0.25 → auto
  - `action_20241201_002` → risk 0.80 → supervisor_approval

---

## Step 5. Check Approval Queues (Action-Level)
**Instruction (per CLI reference):**
```bash
python cli_fast.py get-approval-queue --route supervisor_approval
python cli_fast.py get-approval-queue --route advisor_approval
```
**Agent Expectations:**
- Show list of **actions** awaiting approvals by route.
- Include IDs like `action_20241201_002` and risk context.

> **Note:** If you want to review **plan-level** approvals, use:
> ```bash
> python cli_fast.py action-plan-queue --status pending_approval
> ```

---

## Step 6. Approve / Reject Actions (Action-Level)
**Instruction:**
```bash
# Approve supervisor-gated financial action
python cli_fast.py approve-action action_20241201_002 --approved-by "supervisor_jane" --notes "Approved with documentation"

# Reject expedited processing
python cli_fast.py reject-action action_20241201_003 --rejected-by "supervisor_jane" --reason "Requires supporting docs"

# Bulk approve advisor items
python cli_fast.py bulk-approve "action_20241201_010,action_20241201_011" --approved-by "advisor_mike" --notes "Routine coaching items"
```
**Agent Expectations:**
- Update **action-level** approval statuses.
- Print metrics (approved/rejected/pending).

---

## Step 6.5 Approve the Plan (Plan-Level, if required by your policy)
**Instruction (per CLI reference):**
```bash
python cli_fast.py approve-action-plan plan_20241201_001 --approver "supervisor_jane"
```
**Agent Expectations:**
- Set plan status to `approved` (needed for standard `execute-plan`).
- Log approver and timestamp in audit trail.

---

## Step 7. Execute the Plan (Approval-Aware)
**Instruction:**
```bash
# Optional preview
python cli_fast.py execute-plan --dry-run plan_20241201_001

# Execute (respects approvals; fails if plan not approved)
python cli_fast.py execute-plan plan_20241201_001
```
**Agent Expectations:**
- Execute only actions with `auto` or `approved` status.
- Skip actions with `pending` status.
- Generate artifacts (emails, callbacks, documents).

**Sample Execution Result:**
```
✅ Execution completed successfully!
Execution ID: exec_20241201_001
Total Actions Executed: 9, Skipped (pending): 3
Artifacts Created: 7
```

---

## Step 8. Monitor Execution & Metrics
**Instruction:**
```bash
python cli_fast.py execution-history --limit 5
python cli_fast.py execution-metrics
python cli_fast.py approval-metrics
```
**Agent Expectations:**
- Show recent executions with approval-aware skip tracking.
- Display counts like `actions_skipped_for_approval` and `approval_skip_rate`.
- Show approval rates, pending counts, and risk distributions.

---

## Step 9. View Artifacts
**Instruction (per CLI reference):**
```bash
python cli_fast.py view-artifacts --type emails --limit 20
python cli_fast.py view-artifacts --type documents
```
**Agent Expectations:**
- List generated files and previews (no `--execution-id` filter in CLI reference).

---

## Step 10. Observer Agent Evaluation & Feedback Loop
**Instruction:**
```bash
# View execution results with Observer Agent evaluation
python cli_fast.py execution-metrics --include-observer-feedback

# Check continuous learning insights
python cli_fast.py analysis-metrics --include-learning-patterns

# View Observer Agent lessons learned
python cli_fast.py decision-agent-summary --include-feedback-loop
```
**Agent Expectations:**
- Observer Agent automatically evaluates execution results for satisfaction and quality
- Identifies improvement opportunities and systemic issues
- Generates actionable feedback for Decision Agent refinement
- Builds lessons-learned dataset for continuous improvement
- Provides actor performance assessments and training recommendations

**Sample Observer Output:**
```
📊 Observer Agent Evaluation - exec_20241201_001
Overall Satisfaction: satisfactory (4.2/5.0)
Issues Identified: 2 (missing documentation, communication delay)
Improvement Opportunities: 3 
Actor Performance: Advisor (excellent), Supervisor (needs training)
Decision Agent Feedback: Consider pre-execution document validation
```

---

## Step 11. Complete Feedback Loop Demonstration
**Instruction:**
```bash
# Generate another similar scenario to test learning
python cli_fast.py generate --store scenario="Mortgage Servicing - PMI Removal - similar compliance dispute" urgency=high financial_impact=true

# Analyze and generate action plan (should show Observer improvements)
python cli_fast.py analyze --transcript-id [new_transcript_id]
python cli_fast.py generate-action-plan --transcript-id [new_transcript_id]

# Execute and compare Observer evaluation
python cli_fast.py execute-plan [new_plan_id]
python cli_fast.py execution-metrics --compare-previous --include-learning-velocity
```
**Agent Expectations:**
- Second iteration should show improved routing based on Observer feedback
- Decision Agent should incorporate lessons learned from first execution
- Observer Agent should detect patterns and systemic improvements
- Learning velocity metrics should demonstrate continuous improvement

---

# 🎯 Complete End State of Demo
- 1 transcript generated, analyzed, and converted into ~12 actions.
- Decision Agent routed actions by risk (auto/advisor/supervisor).
- Actions and plan approved as required.
- Execution completed with approved items only; pending items skipped.
- **Observer Agent evaluated execution results and provided continuous learning feedback.**
- **Lessons learned dataset built for future Decision Agent improvements.**
- **Complete feedback loop established for systematic quality enhancement.**
- Full audit trail, metrics, and artifacts available for review.
- **System demonstrates measurable learning and improvement over time.**
