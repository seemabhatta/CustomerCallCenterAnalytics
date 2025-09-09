# Customer Call Center Analytics - CLI Commands Reference

## Quick Start

### Prerequisites
```bash
# Start the backend server first
python3 server.py

# Then use CLI commands
python3 cli_fast.py [command] [options]
```

### Most Common Commands
```bash
# Basic workflow
python3 cli_fast.py demo                                    # Generate sample data
python3 cli_fast.py list                                    # View transcripts
python3 cli_fast.py analyze --all                          # Analyze all transcripts
python3 cli_fast.py generate-action-plan --transcript-id <id>  # Create action plan
python3 cli_fast.py execute-plan <plan_id>                 # Execute approved plan

# Quick stats
python3 cli_fast.py stats                                  # Database statistics
python3 cli_fast.py analysis-metrics                      # AI analysis metrics
python3 cli_fast.py approval-metrics                      # Approval system metrics
```

---

## Command Lifecycle

```
📝 GENERATE → 🔍 ANALYZE → 📋 PLAN → ✅ APPROVE → ⚡ EXECUTE → 📊 MONITOR
    ↓            ↓           ↓          ↓           ↓           ↓
 transcripts   insights   action     approval    automation  metrics
             patterns    plans      workflow    execution   tracking
```

---

## 📝 TRANSCRIPT MANAGEMENT

### `generate` - Create New Transcripts
Generate realistic call transcripts with AI.

```bash
python3 cli_fast.py generate [OPTIONS] [PARAMS...]
```

**Options:**
- `--count, -c INTEGER`: Number of transcripts (default: 1)
- `--store, -s`: Store in database
- `--show`: Display generated content

**Dynamic Parameters:** `key=value` format
- `scenario='PMI Removal'` - Call scenario/topic
- `customer_id='C123'` - Specific customer ID
- `sentiment='frustrated'` - Customer emotional state
- `urgency='high'` - Call urgency level
- `duration='15'` - Call length in minutes

**Examples:**
```bash
# Basic generation
python3 cli_fast.py generate --store

# Complex scenario with 3 transcripts
python3 cli_fast.py generate --count 3 --store --show \
    scenario='Late Payment Hardship' sentiment='worried' urgency='medium'

# Specific customer interaction
python3 cli_fast.py generate --store customer_id='CUST_2024_001' \
    scenario='Refinance Inquiry' duration='20'
```

**Output Format:**
```json
{
  "success": true,
  "transcripts": [...],
  "count": 1,
  "stored": true
}
```

### `list` - View All Transcripts
Display stored transcripts in table or detailed format.

```bash
python3 cli_fast.py list [OPTIONS]
```

**Options:**
- `--detailed, -d`: Show full conversation details

**Output Formats:**
- **Table Mode**: ID, Customer, Topic, Sentiment, Message Count, Preview
- **Detailed Mode**: Full messages with speakers and timestamps

**Examples:**
```bash
# Quick table view
python3 cli_fast.py list

# Full conversation details
python3 cli_fast.py list --detailed
```

### `get` - Retrieve Specific Transcript
Fetch a single transcript by ID.

```bash
python3 cli_fast.py get [OPTIONS] TRANSCRIPT_ID
```

**Options:**
- `--export, -e`: Save to JSON file

**Examples:**
```bash
# View transcript
python3 cli_fast.py get transcript_20241201_001

# Export to file
python3 cli_fast.py get --export transcript_20241201_001
# Creates: transcript_20241201_001.json
```

### `search` - Find Transcripts
Search by customer, topic, or content.

```bash
python3 cli_fast.py search [OPTIONS]
```

**Options:** (exactly one required)
- `--customer, -c TEXT`: Customer ID search
- `--topic, -t TEXT`: Topic/scenario search
- `--text TEXT`: Full-text content search
- `--detailed, -d`: Show detailed results

**Examples:**
```bash
# Customer-specific search
python3 cli_fast.py search --customer "CUST_2024"

# Topic search with details
python3 cli_fast.py search --topic "refinance" --detailed

# Content search across all conversations
python3 cli_fast.py search --text "payment plan"
```

### `delete` - Remove Transcript
Delete a specific transcript with confirmation.

```bash
python3 cli_fast.py delete [OPTIONS] TRANSCRIPT_ID
```

**Options:**
- `--force, -f`: Skip confirmation

**Safety Features:**
- Requires confirmation unless `--force` is used
- Shows transcript preview before deletion
- Cannot be undone

### `delete-all` - Clear All Data
**⚠️ DESTRUCTIVE OPERATION** - Remove all transcripts.

```bash
python3 cli_fast.py delete-all [OPTIONS]
```

**Options:**
- `--force, -f`: Skip first confirmation (final confirmation still required)

**Safety Protocol:**
1. Shows count of transcripts to be deleted
2. First confirmation (skippable with `--force`)
3. **Required typed confirmation**: Must type `DELETE ALL {count}`
4. No recovery possible after confirmation

### `stats` - Database Statistics
Comprehensive database overview and analytics.

```bash
python3 cli_fast.py stats
```

**Output Includes:**
- Total transcripts, messages, unique customers
- Average messages per transcript
- Top 5 topics and their frequency
- Sentiment distribution (positive/negative/neutral)
- Top 5 speakers by message count

### `export` - Bulk Export
Export all transcripts to JSON format.

```bash
python3 cli_fast.py export [OPTIONS]
```

**Options:**
- `--output, -o TEXT`: Custom filename (default: auto-generated timestamp)

**Examples:**
```bash
# Auto-generated filename
python3 cli_fast.py export
# Creates: transcripts_export_20241201_143022.json

# Custom filename
python3 cli_fast.py export --output my_data.json
```

### `demo` - Sample Data Generator
Create demonstration data for testing and training.

```bash
python3 cli_fast.py demo [OPTIONS]
```

**Options:**
- `--no-store`: Generate without saving to database

**Generated Content:**
- 5-10 diverse call scenarios
- Various customer personas and sentiment states
- Realistic conversation flows
- Mixed urgency levels and topics

---

## 🔍 ANALYSIS & INSIGHTS

### `analyze` - AI-Powered Analysis
Generate comprehensive mortgage servicing insights using AI.

```bash
python3 cli_fast.py analyze [OPTIONS]
```

**Options:** (exactly one required)
- `--transcript-id, -t TEXT`: Analyze specific transcript
- `--all, -a`: Analyze all stored transcripts

**Analysis Dimensions:**
- **Intent Detection**: Primary reason for call
- **Urgency Assessment**: Low/Medium/High priority classification
- **Sentiment Analysis**: Customer emotional journey (start → end)
- **Risk Scoring**: Delinquency, churn, complaint, refinance likelihood
- **Advisor Performance**: Empathy, compliance, solution effectiveness
- **Resolution Status**: First-call resolution, escalation needs

**Examples:**
```bash
# Analyze specific conversation
python3 cli_fast.py analyze --transcript-id transcript_20241201_001

# Batch analyze all data
python3 cli_fast.py analyze --all
```

**Output:**
```
✅ Analyzed 5 transcript(s)

📄 Transcript: transcript_20241201_001
   Intent: Payment Plan Setup
   Urgency: Medium
   Sentiment: frustrated → satisfied
   Confidence: 0.89
```

### `analysis-report` - Detailed Analysis View
Comprehensive analysis report for specific transcript.

```bash
python3 cli_fast.py analysis-report [OPTIONS]
```

**Options:** (exactly one required)
- `--transcript-id, -t TEXT`: View by transcript ID
- `--analysis-id, -a TEXT`: View by analysis ID

**Report Sections:**
1. **Call Summary**: AI-generated overview
2. **Key Insights**: Intent, urgency, resolution status
3. **Borrower Profile**: Sentiment progression, risk assessment
4. **Advisor Performance**: Coaching opportunities, strengths/improvements
5. **Compliance**: Flags, adherence scores
6. **Risk Scores**: Delinquency (0-1), Churn (0-1), Complaint (0-1), Refinance (0-1)

### `analysis-metrics` - Aggregate Analytics Dashboard
System-wide analysis performance metrics.

```bash
python3 cli_fast.py analysis-metrics
```

**Metrics Included:**
- Total analyses performed, average confidence score
- First-call resolution rate, escalation rate
- Average empathy and compliance scores
- Risk indicator averages (delinquency, churn)
- Top 5 call intents and urgency distribution

### `risk-report` - High-Risk Borrower Identification
Generate report of borrowers requiring immediate attention.

```bash
python3 cli_fast.py risk-report [OPTIONS]
```

**Options:**
- `--threshold, -t FLOAT`: Risk threshold 0.0-1.0 (default: 0.7)

**Risk Categories:**
- **High Delinquency Risk**: Payment issues, hardship indicators
- **High Churn Risk**: Refinance inquiries, competitor mentions
- **High Complaint Risk**: Service dissatisfaction patterns

**Output Format:**
```
🚨 High Delinquency Risk (3 cases)
  Transcript: transcript_20241201_003
  Risk Score: 0.85
  Intent: Payment Deferral Request
  Summary: Customer facing temporary hardship...

⚠️  High Churn Risk (2 cases)
  Transcript: transcript_20241201_007
  Risk Score: 0.73
  Intent: Rate Shopping
  Summary: Customer comparing rates with competitors...
```

---

## 📋 ACTION PLAN MANAGEMENT

### `generate-action-plan` - Create Four-Layer Plans
Generate comprehensive action plans from analysis results.

```bash
python3 cli_fast.py generate-action-plan [OPTIONS]
```

**Options:** (exactly one required)
- `--analysis-id, -a TEXT`: Generate from analysis ID
- `--transcript-id, -t TEXT`: Generate from transcript ID

**Four-Layer Plan Structure:**
1. **Borrower Plan**: Immediate actions, follow-ups, timelines
2. **Advisor Plan**: Coaching items, performance feedback
3. **Supervisor Plan**: Escalation items, team pattern analysis
4. **Leadership Plan**: Portfolio insights, strategic opportunities

**Output:**
```
✅ Generated action plan: plan_20241201_001
Risk Level: medium
Approval Route: advisor_approval
Queue Status: pending_approval
Message: Plan ready for advisor review
```

### `view-action-plan` - Detailed Plan Review
Display comprehensive action plan details.

```bash
python3 cli_fast.py view-action-plan [OPTIONS] PLAN_ID
```

**Options:**
- `--layer, -l TEXT`: View specific layer only
  - `borrower` - Customer-facing actions
  - `advisor` - Agent coaching and feedback
  - `supervisor` - Management escalations
  - `leadership` - Strategic insights

**Examples:**
```bash
# View complete plan
python3 cli_fast.py view-action-plan plan_20241201_001

# View only supervisor actions
python3 cli_fast.py view-action-plan --layer supervisor plan_20241201_001
```

**Sample Output Sections:**
```
📄 Action Plan Report
Plan ID: plan_20241201_001
Risk Level: medium
Status: pending_approval

🎯 Borrower Plan
🚀 Immediate Actions:
  • Send payment plan options email (Priority: high, Timeline: 24 hours)
    ✅ Auto-executable
  • Schedule follow-up call in 48 hours (Priority: medium)

📅 Follow-ups:
  • Payment confirmation check (Due: 2024-12-05, Owner: System)
```

### `action-plan-queue` - Approval Queue Management
View plans awaiting approval in the system.

```bash
python3 cli_fast.py action-plan-queue [OPTIONS]
```

**Options:**
- `--status, -s TEXT`: Filter by status
  - `pending_approval` - Waiting for approval
  - `approved` - Ready for execution
  - `rejected` - Declined plans
  - `executed` - Completed plans

**Queue Display:**
```
📊 Action Plan Queue (3 items)

Plan ID: plan_20241201_001
  Transcript: transcript_20241201_001
  Risk Level: medium
  Status: pending_approval
  Routing: advisor_approval
  Reason: Medium risk financial action
  Created: 2024-12-01 14:30:22
```

### `approve-action-plan` - Plan Approval
Approve action plans for execution.

```bash
python3 cli_fast.py approve-action-plan [OPTIONS] PLAN_ID
```

**Options:**
- `--approver, -by TEXT`: Approver identifier (default: CLI_USER)

**Approval Effects:**
- Changes plan status to `approved`
- Enables execution via `execute-plan`
- Logs approval audit trail
- Triggers auto-execution for qualifying plans

### `action-plan-summary` - Planning Metrics
Overview of action planning system performance.

```bash
python3 cli_fast.py action-plan-summary
```

**Metrics Displayed:**
- Total plans created, pending approvals
- Auto-executable percentage
- Status distribution (pending/approved/executed)
- Risk level distribution (low/medium/high)
- Routing distribution (advisor/supervisor approval)

---

## ⚡ EXECUTION SYSTEM

### `execute-plan` - Intelligent Plan Execution
Execute approved action plans using AI-powered automation.

```bash
python3 cli_fast.py execute-plan [OPTIONS] PLAN_ID
```

**Options:**
- `--mode, -m TEXT`: Execution mode
  - `auto` (default): Respects approval requirements
  - `manual`: Override for testing (bypasses approval)
- `--dry-run`: Preview execution without performing actions

**Execution Process:**
1. **Approval Check**: Verifies plan approval status
2. **Action Classification**: Identifies executable vs. manual actions
3. **Automated Execution**: Emails, callbacks, document generation
4. **Artifact Creation**: Generates evidence files
5. **Status Tracking**: Updates execution history

**Examples:**
```bash
# Standard execution (requires approval)
python3 cli_fast.py execute-plan plan_20241201_001

# Preview what would be executed
python3 cli_fast.py execute-plan --dry-run plan_20241201_001

# Manual override for testing
python3 cli_fast.py execute-plan --mode manual plan_20241201_001
```

**Execution Results:**
```
✅ Execution completed successfully!
Execution ID: exec_20241201_001
Total Actions Executed: 4

📋 Email Actions:
  ✅ payment_plan_options: Email sent successfully
  ✅ follow_up_reminder: Email scheduled

📋 Callback Actions:
  ✅ payment_confirmation_call: Callback scheduled

📄 Artifacts Created (3):
  📁 emails/payment_plan_options_CUST_001.html
  📁 callbacks/payment_confirmation_CUST_001.json
  📁 documents/payment_agreement_CUST_001.pdf
```

### `execution-history` - Execution Audit Trail
View recent execution history and results.

```bash
python3 cli_fast.py execution-history [OPTIONS]
```

**Options:**
- `--limit, -l INTEGER`: Number of executions to show (default: 10)

**History Format:**
```
📋 Recent Executions
--------------------------------------------------------------------------------
✅ exec_20241201_001 | Plan: plan_20241201_001
   📅 2024-12-01 15:45:22 | Artifacts: 3 | Errors: 0

❌ exec_20241201_002 | Plan: plan_20241201_002
   📅 2024-12-01 16:10:15 | Artifacts: 1 | Errors: 2
```

### `view-artifacts` - Execution Evidence
View generated artifacts from plan executions.

```bash
python3 cli_fast.py view-artifacts [OPTIONS]
```

**Options:**
- `--type, -t TEXT`: Artifact type filter
  - `emails` - Generated email communications
  - `callbacks` - Scheduled callback records
  - `documents` - PDF agreements, forms
  - `all` (default) - All artifact types
- `--limit, -l INTEGER`: Number to display (default: 10)

**Examples:**
```bash
# View all recent artifacts
python3 cli_fast.py view-artifacts

# View only email artifacts
python3 cli_fast.py view-artifacts --type emails --limit 20

# View generated documents
python3 cli_fast.py view-artifacts --type documents
```

**Artifact Display:**
```
📄 Email Artifacts
--------------------------------------------------------------------------------
📁 payment_plan_options_CUST_001.html
   📅 2024-12-01 15:45:22 | Size: 2,847 bytes
   👀 <html><body><h2>Payment Plan Options</h2><p>Dear Valued Customer...</p></body></html>...

📁 follow_up_reminder_CUST_001.html
   📅 2024-12-01 15:45:25 | Size: 1,923 bytes
   👀 <html><body><h2>Follow-up Reminder</h2><p>This is a friendly reminder...</p></body></html>...
```

### `execution-metrics` - Performance Dashboard
Execution system performance statistics.

```bash
python3 cli_fast.py execution-metrics
```

**7-Day Performance Metrics:**
- Total executions, success rate percentage
- Total artifacts created
- Status breakdown (success/failed/pending)
- Actions by source (borrower_plan/advisor_plan/etc.)
- Tools usage statistics (email/callback/document generation)

---

## ✅ DECISION AGENT & APPROVALS

### `get-approval-queue` - Pending Actions View
View actions requiring approval in the Decision Agent system.

```bash
python3 cli_fast.py get-approval-queue [OPTIONS]
```

**Options:**
- `--route TEXT`: Filter by approval route
  - `advisor_approval` - Actions requiring advisor approval
  - `supervisor_approval` - Actions requiring supervisor approval

**Queue Display Format:**
```
📋 Approval Queue (5 items)
============================================================

🎯 Advisor Approval (3 items):
  🟡 action_20241201_001: Send payment plan options to customer...
    Risk: medium (score: 0.654)
    Financial: moderate, Compliance: low
    Created: 2024-12-01 14:30:22

  🔴 action_20241201_002: Process payment deferral request...
    Risk: high (score: 0.821)
    Financial: significant, Compliance: moderate
    Created: 2024-12-01 14:35:18
```

### `approve-action` - Single Action Approval
Approve specific action in the queue.

```bash
python3 cli_fast.py approve-action [OPTIONS] ACTION_ID
```

**Options:**
- `--approved-by TEXT`: Approver identifier (default: CLI_USER)
- `--notes TEXT`: Optional approval notes

**Examples:**
```bash
# Basic approval
python3 cli_fast.py approve-action action_20241201_001

# Approval with notes
python3 cli_fast.py approve-action --notes "Approved for customer retention" \
    --approved-by "John.Smith" action_20241201_001
```

### `reject-action` - Action Rejection
Reject specific action with reason.

```bash
python3 cli_fast.py reject-action [OPTIONS] ACTION_ID
```

**Options:**
- `--rejected-by TEXT`: Rejector identifier (default: CLI_USER)
- `--reason TEXT`: Rejection reason (default: "No reason provided")

**Examples:**
```bash
# Basic rejection
python3 cli_fast.py reject-action action_20241201_002

# Rejection with detailed reason
python3 cli_fast.py reject-action --reason "Requires additional customer verification" \
    --rejected-by "Jane.Supervisor" action_20241201_002
```

### `bulk-approve` - Mass Action Approval
Approve multiple actions simultaneously.

```bash
python3 cli_fast.py bulk-approve [OPTIONS] ACTION_IDS
```

**Arguments:**
- `ACTION_IDS`: Comma-separated list of action IDs (no spaces)

**Options:**
- `--approved-by TEXT`: Approver identifier (default: CLI_USER)
- `--notes TEXT`: Bulk approval notes (default: "Bulk approval")

**Examples:**
```bash
# Bulk approve multiple actions
python3 cli_fast.py bulk-approve "action_001,action_002,action_003"

# Bulk approve with custom notes
python3 cli_fast.py bulk-approve --notes "Weekly batch approval session" \
    --approved-by "Manager.Smith" "action_004,action_005"
```

**Output:**
```
✅ Bulk approval completed
Approved: 3/3 actions
```

### `approval-metrics` - Approval System Analytics
Comprehensive approval queue performance metrics.

```bash
python3 cli_fast.py approval-metrics
```

**Metrics Dashboard:**
```
📊 Approval Metrics
========================================
Total Actions: 127
Pending Approvals: 8
Approval Rate: 89.2%
Avg Approval Time: 2.3 hours

📈 Queue Status:
  Advisor Approval:
    pending: 5
    approved: 45
    rejected: 3
  Supervisor Approval:
    pending: 3
    approved: 67
    rejected: 4

⚠️  Risk Distribution:
  low: 89
  medium: 31
  high: 7
```

### `decision-agent-summary` - Agent Configuration
View Decision Agent settings and processing summary.

```bash
python3 cli_fast.py decision-agent-summary
```

**Summary Sections:**
1. **Agent Version**: Current Decision Agent version
2. **Configuration**: Thresholds and routing rules
3. **Processing Summary**: Total decisions, routing distribution
4. **Performance Metrics**: Auto-approval rates, average actions per plan

---

## 👁️ OBSERVER AGENT & CONTINUOUS LEARNING (PLANNED FEATURES)

> **⚠️ NOTE**: The Observer Agent features documented below are **PLANNED FUNCTIONALITY** and are not yet fully implemented. The commands with `--include-observer-feedback` and similar flags may not exist in the current CLI.

### Observer Agent Overview
The Observer Agent implements the "Co-Pilot Review & Evaluation" functionality, providing continuous learning and improvement through execution result evaluation.

**Key Functions:**
- Evaluates execution results for satisfaction and quality
- Identifies improvement opportunities and systemic issues  
- Generates actionable feedback for Decision Agent refinement
- Builds lessons-learned dataset for future improvements
- Provides actor performance assessments

### `execution-metrics --include-observer-feedback` - Enhanced Execution Analytics
View execution metrics with Observer Agent evaluation insights.

```bash
python3 cli_fast.py execution-metrics --include-observer-feedback
```

**Enhanced Metrics Display:**
```
📊 Execution Metrics with Observer Analysis
===============================================
Total Executions: 47
Success Rate: 89.3%

👁️ Observer Agent Evaluation:
Overall Satisfaction: satisfactory (4.2/5.0)
Quality Score: 4.1/5.0

🔍 Issues Identified (Last 10 Executions):
  • Missing documentation (3 occurrences)
  • Communication delays (2 occurrences)
  • Approval process bottlenecks (1 occurrence)

💡 Improvement Opportunities:
  • Implement pre-execution document validation
  • Add automated status notifications
  • Review supervisor approval workflow

🎭 Actor Performance:
  Advisor: excellent (4.8/5.0)
  Supervisor: needs improvement (3.2/5.0)
  Leadership: good (4.0/5.0)

🔄 Feedback for Decision Agent:
  • Increase approval threshold for actions missing documentation
  • Add communication quality as risk factor
  • Consider automated document verification step
```

### `analysis-metrics --include-learning-patterns` - Learning Velocity Analytics
View analysis performance with continuous learning insights.

```bash
python3 cli_fast.py analysis-metrics --include-learning-patterns
```

**Learning Analytics Display:**
```
📈 Analysis Metrics with Learning Patterns
==========================================
Total Analyses: 234
Average Quality: 4.3/5.0

🧠 Learning Velocity:
Pattern Recognition Rate: 87.5%
Improvement Rate: +12.3% (last 30 days)
Learning Acceleration: 0.85

🔄 Success Patterns Identified:
  • Proactive customer communication (high satisfaction)
  • Early hardship intervention (reduced churn)
  • Documentation completeness (faster execution)

⚠️ Failure Patterns Identified:
  • Delayed supervisor approvals (customer frustration)
  • Missing context in action plans (execution errors)
  • Inadequate actor preparation (process failures)

🎯 System Learning Insights:
  • Decision Agent accuracy improved 15% over last month
  • Action plan quality scores trending upward
  • Execution error rates decreased by 23%
```

### `decision-agent-summary --include-feedback-loop` - Feedback Integration Status
View Decision Agent configuration with Observer feedback integration.

```bash
python3 cli_fast.py decision-agent-summary --include-feedback-loop
```

**Feedback Loop Status:**
```
🤖 Decision Agent Configuration with Feedback Loop
=================================================
Agent Version: v2.1 (Observer-Enhanced)
Last Observer Update: 2024-12-01 15:30:22

🔄 Feedback Integration:
Observer Evaluations Processed: 47
Routing Adjustments Made: 12
Risk Threshold Updates: 3

📋 Recent Observer Feedback Applied:
  ✅ Increased documentation requirement threshold (0.3 → 0.4)
  ✅ Added communication quality risk factor (weight: 0.15)
  ✅ Enhanced approval routing for financial actions
  
🎯 Continuous Improvement Metrics:
Feedback Implementation Rate: 92.3%
Decision Accuracy Improvement: +15.2%
Customer Satisfaction Impact: +8.7%

🧠 Lessons Learned Database:
Total Lessons: 156
Applied Improvements: 143
Success Rate: 91.7%
```

### `execution-metrics --compare-previous --include-learning-velocity` - Learning Comparison
Compare current execution performance with previous periods to measure learning velocity.

```bash
python3 cli_fast.py execution-metrics --compare-previous --include-learning-velocity
```

**Learning Velocity Display:**
```
📊 Execution Performance Comparison
===================================

Current Period (Last 30 days):
  Success Rate: 89.3% (+12.1% vs previous)
  Customer Satisfaction: 4.2/5.0 (+0.3 vs previous)
  Average Execution Time: 2.8 min (-0.7 min vs previous)

🚀 Learning Velocity Indicators:
  Improvement Rate: +12.1% (excellent)
  Learning Acceleration: 0.91 (strong positive trend)  
  Pattern Recognition: 94.2% (high)

🔄 Observer Impact Analysis:
  Feedback Implementation: 47/51 recommendations (92.1%)
  Decision Agent Improvements: 15 routing updates applied
  Actor Performance Gains: Supervisor +1.2, Advisor +0.3
  
⭐ Key Learning Achievements:
  • Reduced documentation-related failures by 65%
  • Improved approval workflow efficiency by 23%
  • Enhanced customer communication quality scores
  • Decreased average resolution time by 18%
```

### Integration with Existing Commands

**Enhanced Command Options:**
```bash
# Standard execution metrics with Observer insights
python3 cli_fast.py execution-metrics --include-observer-feedback

# Analysis performance with learning patterns
python3 cli_fast.py analysis-metrics --include-learning-patterns

# Decision Agent status with feedback loop info
python3 cli_fast.py decision-agent-summary --include-feedback-loop

# Performance comparison with learning velocity
python3 cli_fast.py execution-metrics --compare-previous --include-learning-velocity

# Approval metrics with Observer recommendations
python3 cli_fast.py approval-metrics --include-observer-insights
```

### Observer Agent Workflow Integration

**Complete Learning Cycle:**
```bash
# 1. Execute action plan
python3 cli_fast.py execute-plan plan_20241201_001

# 2. View Observer evaluation (automatic)
python3 cli_fast.py execution-metrics --include-observer-feedback

# 3. Check learning insights
python3 cli_fast.py analysis-metrics --include-learning-patterns

# 4. Verify Decision Agent improvements
python3 cli_fast.py decision-agent-summary --include-feedback-loop

# 5. Execute similar scenario to test learning
python3 cli_fast.py generate --scenario "similar_scenario"
python3 cli_fast.py generate-action-plan --transcript-id [new_id]
python3 cli_fast.py execute-plan [new_plan_id]

# 6. Compare learning velocity
python3 cli_fast.py execution-metrics --compare-previous --include-learning-velocity
```

---

## 📊 MONITORING & METRICS

### Common Metric Commands Quick Reference

```bash
# Database & Content Metrics
python3 cli_fast.py stats              # Transcript database statistics
python3 cli_fast.py analysis-metrics   # AI analysis performance
python3 cli_fast.py risk-report        # High-risk borrower identification

# Planning & Execution Metrics  
python3 cli_fast.py action-plan-summary    # Action planning statistics
python3 cli_fast.py execution-metrics      # Execution system performance
python3 cli_fast.py execution-history      # Recent execution audit trail

# Approval & Decision Metrics
python3 cli_fast.py approval-metrics       # Approval queue statistics
python3 cli_fast.py decision-agent-summary # Decision Agent configuration
python3 cli_fast.py get-approval-queue     # Current pending actions
```

---

## 🔧 TROUBLESHOOTING

### Common Issues

#### 1. Server Connection Problems
**Error:** `Cannot connect to server at http://localhost:9999`

**Solutions:**
```bash
# Check if server is running
ps aux | grep server.py

# Start the server
python3 server.py

# Verify server is listening
curl http://localhost:9999/health
```

#### 2. Timeout Issues
**Error:** `Request timed out. Operation may still be running on server.`

**Solutions:**
- Check server logs for processing status
- For bulk operations (analyze --all), consider smaller batches
- Increase timeout if necessary (server allows up to 5 minutes)

#### 3. Permission/Approval Errors
**Error:** `Plan requires approval before execution`

**Solutions:**
```bash
# Check plan approval status
python3 cli_fast.py view-action-plan plan_id

# Approve the plan
python3 cli_fast.py approve-action-plan plan_id

# Use dry-run to test without executing
python3 cli_fast.py execute-plan --dry-run plan_id
```

#### 4. Invalid ID Errors
**Error:** `Transcript/Analysis/Plan not found`

**Solutions:**
```bash
# List available transcripts
python3 cli_fast.py list

# Search for specific content
python3 cli_fast.py search --text "keyword"

# Check recent analyses
python3 cli_fast.py analysis-metrics
```

### Error Codes & Status Messages

| Status | Meaning | Action Required |
|--------|---------|----------------|
| ✅ Success | Operation completed | None |
| ❌ Error | Operation failed | Check error message, verify inputs |
| ⏳ Pending | Waiting for approval | Use approval commands |
| 💡 Info | Informational message | None |
| ⚠️ Warning | Caution required | Review before proceeding |

### Performance Tips

#### Bulk Operations
```bash
# Instead of individual analysis:
python3 cli_fast.py analyze --transcript-id id1
python3 cli_fast.py analyze --transcript-id id2

# Use batch analysis:
python3 cli_fast.py analyze --all
```

#### Efficient Searching
```bash
# Broad search first
python3 cli_fast.py search --topic "payment"

# Then narrow down with text search
python3 cli_fast.py search --text "payment plan setup"
```

#### Resource Management
- Use `--dry-run` for testing execution plans
- Export data before bulk deletions
- Monitor server resources during batch operations

---

## 📈 WORKFLOW EXAMPLES

### 1. Complete Customer Service Workflow

```bash
# 1. Generate customer interaction
python3 cli_fast.py generate --store scenario='Payment Difficulty' sentiment='concerned'

# 2. Analyze the interaction
python3 cli_fast.py analyze --transcript-id transcript_20241201_001

# 3. Generate action plan
python3 cli_fast.py generate-action-plan --transcript-id transcript_20241201_001

# 4. Review and approve plan
python3 cli_fast.py view-action-plan plan_20241201_001
python3 cli_fast.py approve-action-plan plan_20241201_001

# 5. Execute with preview first
python3 cli_fast.py execute-plan --dry-run plan_20241201_001
python3 cli_fast.py execute-plan plan_20241201_001

# 6. Monitor results
python3 cli_fast.py execution-history --limit 1
python3 cli_fast.py view-artifacts --type emails
```

### 2. Risk Management Workflow

```bash
# 1. Generate diverse scenarios
python3 cli_fast.py generate --count 10 --store

# 2. Analyze all for risk patterns
python3 cli_fast.py analyze --all

# 3. Identify high-risk cases
python3 cli_fast.py risk-report --threshold 0.75

# 4. Generate plans for high-risk borrowers
python3 cli_fast.py generate-action-plan --transcript-id high_risk_transcript_id

# 5. Review approval queue
python3 cli_fast.py get-approval-queue --route supervisor_approval

# 6. Approve high-priority actions
python3 cli_fast.py approve-action action_high_priority_id
```

### 3. Performance Monitoring Workflow

```bash
# Daily metrics review
python3 cli_fast.py stats
python3 cli_fast.py analysis-metrics
python3 cli_fast.py execution-metrics
python3 cli_fast.py approval-metrics

# Weekly performance analysis
python3 cli_fast.py risk-report
python3 cli_fast.py action-plan-summary
python3 cli_fast.py decision-agent-summary

# Monthly data management
python3 cli_fast.py export --output monthly_backup_$(date +%Y%m).json
python3 cli_fast.py execution-history --limit 100
```

### 4. Testing & Development Workflow

```bash
# Set up test environment
python3 cli_fast.py demo --no-store  # Generate test data without saving
python3 cli_fast.py generate --count 5 --store  # Create test dataset

# Test analysis pipeline
python3 cli_fast.py analyze --all
python3 cli_fast.py analysis-metrics

# Test action planning
python3 cli_fast.py generate-action-plan --transcript-id test_transcript

# Test execution with dry run
python3 cli_fast.py execute-plan --dry-run --mode manual test_plan_id

# Clean up test data
python3 cli_fast.py delete-all --force  # Use with extreme caution
```

---

## 🎯 BEST PRACTICES

### 1. Data Management
- **Regular Backups**: Use `export` command weekly
- **Cleanup Strategy**: Remove test data regularly
- **Naming Conventions**: Use descriptive scenario parameters

### 2. Analysis Workflow
- **Batch Processing**: Use `analyze --all` for efficiency
- **Risk Monitoring**: Run `risk-report` daily
- **Metrics Review**: Check `analysis-metrics` regularly

### 3. Action Planning
- **Review Before Approval**: Always use `view-action-plan`
- **Test Executions**: Use `--dry-run` for new plan types
- **Monitor Results**: Check `execution-history` after executions

### 4. Approval Management
- **Queue Monitoring**: Check `get-approval-queue` regularly
- **Bulk Processing**: Use `bulk-approve` for efficiency
- **Audit Trail**: Document approval decisions with `--notes`

### 5. Security & Compliance
- **Approval Workflows**: Never bypass approval requirements in production
- **Audit Logging**: All actions are logged with timestamps and users
- **Data Protection**: Export sensitive data securely
- **Access Control**: Use meaningful approver identifiers

---

*Last updated: 2024-12-01*
*CLI Version: Fast Client v1.0*
*Server Requirements: Python 3.8+, Backend Server on localhost:9999*