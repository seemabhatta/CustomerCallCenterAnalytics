# Customer Call Center Analytics - CLI Commands Reference

## Quick Start

### Prerequisites
```bash
# Start the backend server first
python3 simple_server.py   # REST API server on port 8000

# Then use CLI commands
python3 cli.py [command] [options]
```

## 🆕 NEW: Standardized API Endpoints

The system now provides 43 standardized RESTful endpoints at `/api/v1/*`:

### System Endpoints
```
GET  /api/v1/health                    # Health check
GET  /api/v1/metrics                   # Dashboard metrics  
GET  /api/v1/workflow/status           # Pipeline status
```

### Transcript Endpoints  
```
GET    /api/v1/transcripts             # List transcripts
POST   /api/v1/transcripts             # Create transcript
GET    /api/v1/transcripts/{id}        # Get transcript
DELETE /api/v1/transcripts/{id}        # Delete transcript
GET    /api/v1/transcripts/search      # Search transcripts
GET    /api/v1/transcripts/metrics     # Statistics
POST   /api/v1/transcripts/bulk        # Bulk creation
GET    /api/v1/transcripts/{id}/messages # Messages
```

### Analysis Endpoints
```
GET    /api/v1/analyses                # List analyses
POST   /api/v1/analyses                # Create analysis
GET    /api/v1/analyses/{id}           # Get analysis
DELETE /api/v1/analyses/{id}           # Delete analysis
GET    /api/v1/analyses/search/transcript/{id} # Search by transcript
```

### Action Plan Endpoints
```
GET    /api/v1/plans                   # List plans
POST   /api/v1/plans                   # Create plan
GET    /api/v1/plans/{id}              # Get plan
PUT    /api/v1/plans/{id}              # Update plan
DELETE /api/v1/plans/{id}              # Delete plan
GET    /api/v1/plans/search/analysis/{id} # Search by analysis
POST   /api/v1/plans/{id}/approve      # Approve plan
POST   /api/v1/plans/{id}/execute      # Execute plan
```

### Case Management Endpoints
```
GET    /api/v1/cases                   # List cases
GET    /api/v1/cases/{id}              # Case details
GET    /api/v1/cases/{id}/transcripts  # Case transcripts
GET    /api/v1/cases/{id}/analyses     # Case analyses
GET    /api/v1/cases/{id}/plans        # Case plans
```

### Governance Endpoints
```
POST   /api/v1/governance/submissions     # Submit for review
GET    /api/v1/governance/submissions/{id} # Submission status
GET    /api/v1/governance/queue           # Approval queue
POST   /api/v1/governance/approvals       # Process approvals
GET    /api/v1/governance/audit           # Audit trail
GET    /api/v1/governance/metrics         # Governance metrics
POST   /api/v1/governance/emergency-override # Emergency override
```

**📚 API Documentation:** Visit http://localhost:8000/docs for interactive API docs

### Most Common Commands
```bash
# Basic workflow
python3 cli.py demo                                    # Generate sample data
python3 cli.py list                                    # View transcripts
python3 cli.py analyze --all                          # Analyze all transcripts
python3 cli.py generate-action-plan --transcript-id <id>  # Create action plan
python3 cli.py execute-plan <plan_id>                 # Execute approved plan

# Quick stats
python3 cli.py stats                                  # Database statistics
python3 cli.py analysis-metrics                      # AI analysis metrics
python3 cli.py approval-metrics                      # Approval system metrics
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

## 🚀 CONSOLIDATED CLI COMMANDS

### Resource-Based Command Structure

The CLI now follows REST API resource patterns with consolidated commands:

```bash
python3 cli.py [RESOURCE] [ACTION] [OPTIONS]
```

**Available Resources:**
- `transcript` - Transcript management
- `analysis` - Analysis operations  
- `plan` - Action plan management
- `case` - Case operations
- `governance` - Approval workflows
- `system` - System health & metrics

---

## 📝 TRANSCRIPT RESOURCE

### `transcript create` - Generate New Transcripts
Generate realistic call transcripts with AI.

```bash
python3 cli.py transcript create [OPTIONS]
```

**Options:**
- `--topic TEXT`: Call topic/scenario
- `--count INTEGER`: Number of transcripts (default: 1)  
- `--store`: Store in database
- `--show`: Display generated content

**Examples:**
```bash
# Basic transcript creation
python3 cli.py transcript create --topic "PMI Removal" --store

# Generate multiple transcripts
python3 cli.py transcript create --topic "Late Payment" --count 3 --store --show
```

### `transcript list` - View All Transcripts
Display stored transcripts in table format.

```bash
python3 cli.py transcript list [OPTIONS]
```

**Options:**
- `--limit INTEGER`: Limit number of results

**Examples:**
```bash
# View all transcripts
python3 cli.py transcript list

# View latest 10 transcripts
python3 cli.py transcript list --limit 10
```

### `transcript get` - Retrieve Specific Transcript
Fetch a single transcript by ID.

```bash
python3 cli.py transcript get TRANSCRIPT_ID
```

**Examples:**
```bash
# View specific transcript
python3 cli.py transcript get CALL_ABC12345
```

### `transcript delete` - Remove Transcript
Delete a transcript from the system.

```bash
python3 cli.py transcript delete TRANSCRIPT_ID [OPTIONS]
```

**Options:**
- `--force`: Skip confirmation prompt

**Examples:**
```bash
# Delete with confirmation
python3 cli.py transcript delete CALL_ABC12345

# Force delete without confirmation
python3 cli.py transcript delete CALL_ABC12345 --force
```

### `transcript search` - Find Transcripts
Search transcripts by query.

```bash
python3 cli.py transcript search [OPTIONS]
```

**Options:**
- `--query TEXT`: Search query

**Examples:**
```bash
# Search for specific content
python3 cli.py transcript search --query "payment"
```

---

## 🔍 ANALYSIS RESOURCE

### `analysis create` - Analyze Transcript
Generate AI analysis for a transcript.

```bash
python3 cli.py analysis create [OPTIONS]
```

**Options:**
- `--transcript TEXT`: Transcript ID to analyze
- `--store`: Store analysis results

**Examples:**
```bash
# Analyze specific transcript
python3 cli.py analysis create --transcript CALL_ABC12345 --store
```

### `analysis list` - View All Analyses
Display all analysis results.

```bash
python3 cli.py analysis list [OPTIONS]
```

**Options:**
- `--limit INTEGER`: Limit number of results

**Examples:**
```bash
# View all analyses
python3 cli.py analysis list

# View latest 5 analyses
python3 cli.py analysis list --limit 5
```

### `analysis get` - Retrieve Specific Analysis
Fetch analysis results by ID.

```bash
python3 cli.py analysis get ANALYSIS_ID
```

**Examples:**
```bash
# View specific analysis
python3 cli.py analysis get ANALYSIS_ABC12345_123
```

---

## 📋 PLAN RESOURCE

### `plan create` - Generate Action Plan
Create action plan from analysis.

```bash
python3 cli.py plan create [OPTIONS]
```

**Options:**
- `--analysis TEXT`: Analysis ID to create plan from

**Examples:**
```bash
# Create plan from analysis
python3 cli.py plan create --analysis ANALYSIS_ABC12345_123
```

### `plan list` - View Action Plans
Display all action plans.

```bash
python3 cli.py plan list
```

### `plan metrics` - Plan Statistics
View action plan metrics and statistics.

```bash
python3 cli.py plan metrics
```

---

## 📊 CASE RESOURCE

### `case list` - View Cases
Display all cases in the system.

```bash
python3 cli.py case list
```

---

## ✅ GOVERNANCE RESOURCE

### `governance queue` - Approval Queue
View items waiting for approval.

```bash
python3 cli.py governance queue
```

### `governance metrics` - Approval Metrics
View governance and approval statistics.

```bash
python3 cli.py governance metrics
```

---

## 🔧 SYSTEM RESOURCE

### `system health` - Health Check
Check system health and component status.

```bash
python3 cli.py system health
```

### `system metrics` - System Statistics
View comprehensive system metrics.

```bash
python3 cli.py system metrics
```

---

## 📖 COMMON WORKFLOWS

### Basic Analysis Workflow
```bash
# 1. Create transcript
python3 cli.py transcript create --topic "Customer Issue" --store

# 2. List transcripts to get ID
python3 cli.py transcript list

# 3. Analyze transcript
python3 cli.py analysis create --transcript CALL_ABC12345 --store

# 4. Create action plan
python3 cli.py plan create --analysis ANALYSIS_ABC12345_123

# 5. Check system health
python3 cli.py system health
```

### Monitoring Workflow
```bash
# View system status
python3 cli.py system health
python3 cli.py system metrics

# Check analysis performance
python3 cli.py analysis list --limit 10

# Review governance queue
python3 cli.py governance queue
python3 cli.py governance metrics
```


---

## 🌐 API ENDPOINTS

### FastAPI Web Interface
The system provides RESTful API endpoints accessible at `http://localhost:8000` when the server is running.

**API Documentation:**
- Interactive Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON Schema: `http://localhost:8000/openapi.json`

### Analysis APIs (5 endpoints)
```
POST /api/v1/analysis/analyze          # Analyze transcript
GET  /api/v1/analysis/{analysis_id}    # Get analysis results
GET  /api/v1/analysis/summary          # Get analysis summary
GET  /api/v1/analysis/metrics          # Get analysis metrics
GET  /api/v1/analysis/trends           # Get analysis trends
```

### Action Plan APIs (5 endpoints)
```
POST /api/v1/plans/generate            # Generate action plan
GET  /api/v1/plans/{plan_id}           # Get action plan
GET  /api/v1/plans                     # List action plans
PUT  /api/v1/plans/{plan_id}           # Update action plan
DELETE /api/v1/plans/{plan_id}         # Delete action plan
```

### Execution APIs (5 endpoints)
```
POST /api/v1/execution/execute         # Execute action plan
GET  /api/v1/execution/{exec_id}       # Get execution status
GET  /api/v1/execution                 # List executions
POST /api/v1/execution/{exec_id}/cancel # Cancel execution
POST /api/v1/execution/{exec_id}/retry  # Retry execution
```

### Approval APIs (5 endpoints)
```
POST /api/v1/approvals/submit          # Submit for approval
GET  /api/v1/approvals/{approval_id}   # Get approval status
GET  /api/v1/approvals                 # List approvals
POST /api/v1/approvals/{approval_id}/approve # Approve
POST /api/v1/approvals/{approval_id}/reject  # Reject
```

**Example API Usage:**
```bash
# Analyze a transcript via API
curl -X POST "http://localhost:8000/api/v1/analysis/analyze" \
     -H "Content-Type: application/json" \
     -d '{"transcript_id": "transcript_20241201_001"}'

# Get analysis results
curl "http://localhost:8000/api/v1/analysis/analysis_20241201_001"

# Generate action plan
curl -X POST "http://localhost:8000/api/v1/plans/generate" \
     -H "Content-Type: application/json" \
     -d '{"analysis_id": "analysis_20241201_001"}'
```

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
python3 cli.py execution-metrics --include-observer-feedback
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
python3 cli.py analysis-metrics --include-learning-patterns
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
python3 cli.py decision-agent-summary --include-feedback-loop
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
python3 cli.py execution-metrics --compare-previous --include-learning-velocity
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
python3 cli.py execution-metrics --include-observer-feedback

# Analysis performance with learning patterns
python3 cli.py analysis-metrics --include-learning-patterns

# Decision Agent status with feedback loop info
python3 cli.py decision-agent-summary --include-feedback-loop

# Performance comparison with learning velocity
python3 cli.py execution-metrics --compare-previous --include-learning-velocity

# Approval metrics with Observer recommendations
python3 cli.py approval-metrics --include-observer-insights
```

### Observer Agent Workflow Integration

**Complete Learning Cycle:**
```bash
# 1. Execute action plan
python3 cli.py execute-plan plan_20241201_001

# 2. View Observer evaluation (automatic)
python3 cli.py execution-metrics --include-observer-feedback

# 3. Check learning insights
python3 cli.py analysis-metrics --include-learning-patterns

# 4. Verify Decision Agent improvements
python3 cli.py decision-agent-summary --include-feedback-loop

# 5. Execute similar scenario to test learning
python3 cli.py generate --scenario "similar_scenario"
python3 cli.py generate-action-plan --transcript-id [new_id]
python3 cli.py execute-plan [new_plan_id]

# 6. Compare learning velocity
python3 cli.py execution-metrics --compare-previous --include-learning-velocity
```

---

## 📊 MONITORING & METRICS

### Common Metric Commands Quick Reference

```bash
# Database & Content Metrics
python3 cli.py stats              # Transcript database statistics
python3 cli.py analysis-metrics   # AI analysis performance
python3 cli.py risk-report        # High-risk borrower identification

# Planning & Execution Metrics  
python3 cli.py action-plan-summary    # Action planning statistics
python3 cli.py execution-metrics      # Execution system performance
python3 cli.py execution-history      # Recent execution audit trail

# Approval & Decision Metrics
python3 cli.py approval-metrics       # Approval queue statistics
python3 cli.py decision-agent-summary # Decision Agent configuration
python3 cli.py get-approval-queue     # Current pending actions
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
python3 cli.py view-action-plan plan_id

# Approve the plan
python3 cli.py approve-action-plan plan_id

# Use dry-run to test without executing
python3 cli.py execute-plan --dry-run plan_id
```

#### 4. Invalid ID Errors
**Error:** `Transcript/Analysis/Plan not found`

**Solutions:**
```bash
# List available transcripts
python3 cli.py list

# Search for specific content
python3 cli.py search --text "keyword"

# Check recent analyses
python3 cli.py analysis-metrics
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
python3 cli.py analyze --transcript-id id1
python3 cli.py analyze --transcript-id id2

# Use batch analysis:
python3 cli.py analyze --all
```

#### Efficient Searching
```bash
# Broad search first
python3 cli.py search --topic "payment"

# Then narrow down with text search
python3 cli.py search --text "payment plan setup"
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
python3 cli.py generate --store topic='Payment Difficulty' sentiment='concerned'

# 2. Analyze the interaction
python3 cli.py analyze --transcript-id transcript_20241201_001

# 3. Generate action plan
python3 cli.py generate-action-plan --transcript-id transcript_20241201_001

# 4. Review and approve plan
python3 cli.py view-action-plan plan_20241201_001
python3 cli.py approve-action-plan plan_20241201_001

# 5. Execute with preview first
python3 cli.py execute-plan --dry-run plan_20241201_001
python3 cli.py execute-plan plan_20241201_001

# 6. Monitor results
python3 cli.py execution-history --limit 1
python3 cli.py view-artifacts --type emails
```

### 2. Risk Management Workflow

```bash
# 1. Generate diverse scenarios
python3 cli.py generate --count 10 --store

# 2. Analyze all for risk patterns
python3 cli.py analyze --all

# 3. Identify high-risk cases
python3 cli.py risk-report --threshold 0.75

# 4. Generate plans for high-risk borrowers
python3 cli.py generate-action-plan --transcript-id high_risk_transcript_id

# 5. Review approval queue
python3 cli.py get-approval-queue --route supervisor_approval

# 6. Approve high-priority actions
python3 cli.py approve-action action_high_priority_id
```

### 3. Performance Monitoring Workflow

```bash
# Daily metrics review
python3 cli.py stats
python3 cli.py analysis-metrics
python3 cli.py execution-metrics
python3 cli.py approval-metrics

# Weekly performance analysis
python3 cli.py risk-report
python3 cli.py action-plan-summary
python3 cli.py decision-agent-summary

# Monthly data management
python3 cli.py export --output monthly_backup_$(date +%Y%m).json
python3 cli.py execution-history --limit 100
```

### 4. Testing & Development Workflow

```bash
# Set up test environment
python3 cli.py demo --no-store  # Generate test data without saving
python3 cli.py generate --count 5 --store  # Create test dataset

# Test analysis pipeline
python3 cli.py analyze --all
python3 cli.py analysis-metrics

# Test action planning
python3 cli.py generate-action-plan --transcript-id test_transcript

# Test execution with dry run
python3 cli.py execute-plan --dry-run --mode manual test_plan_id

# Clean up test data
python3 cli.py delete-all --force  # Use with extreme caution
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