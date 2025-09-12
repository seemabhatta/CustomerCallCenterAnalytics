# 📚 Customer Call Center Analytics - CLI Commands Reference

## Overview

The CLI provides 6 resource-based command groups with comprehensive CRUD operations and advanced analytics capabilities. All commands follow the pattern: `python3 cli.py <resource> <command> [options]`

## 🌐 Global Options

```bash
python3 cli.py [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**
- `--api-url TEXT` - API server URL (default: http://localhost:8000)
- `--format TEXT` - Output format (table, json)
- `--verbose -v` - Enable verbose output
- `--help` - Show help message

## 📋 Command Groups

### 1. Transcript Operations

**Resource Group:** `transcript`

#### Available Commands:
- `create` - Create new transcript
- `list` - List all transcripts  
- `get` - Get specific transcript details
- `delete` - Delete specific transcript
- `search` - Search transcripts

#### Examples:

```bash
# Create a new transcript
python3 cli.py transcript create --topic "Payment inquiry" --urgency high

# List all transcripts
python3 cli.py transcript list

# Get specific transcript details
python3 cli.py transcript get CALL_123ABC

# Delete transcript
python3 cli.py transcript delete CALL_123ABC

# Search transcripts
python3 cli.py transcript search --query "payment"
```

---

### 2. Analysis Operations

**Resource Group:** `analysis`

#### Core Analysis Commands:
- `create` - Create analysis for transcript
- `list` - List all analyses  
- `get` - Get specific analysis details
- `delete` - Delete specific analysis
- `delete-all` - Delete all analyses

#### Examples:

```bash
# Core Analysis Operations
python3 cli.py analysis create --transcript-id CALL_123ABC
python3 cli.py analysis list
python3 cli.py analysis get ANALYSIS_456DEF
python3 cli.py analysis delete ANALYSIS_456DEF
python3 cli.py analysis delete-all
```

---

### 3. Insights Operations (Knowledge Graph Analytics)

**Resource Group:** `insights`

#### Knowledge Graph Analytics Commands:
- `patterns` - Discover risk patterns across all analyses
- `risks` - Get high-risk patterns using knowledge graph analytics
- `recommend` - Get AI-powered recommendations for a customer
- `similar` - Find similar analyses using knowledge graph pattern matching
- `dashboard` - Get comprehensive insights dashboard

#### Knowledge Graph Management Commands:
- `populate` - Populate knowledge graph from analysis data
- `query` - Execute raw Cypher query on knowledge graph
- `status` - Get knowledge graph status and statistics
- `delete-analysis` - Delete analysis from knowledge graph
- `delete-customer` - Delete customer from knowledge graph  
- `prune` - Prune old data from knowledge graph (GDPR compliance)
- `clear` - Clear entire knowledge graph (use with extreme caution)

#### Examples:

```bash
# Knowledge Graph Analytics
python3 cli.py insights patterns --risk-threshold 0.7
python3 cli.py insights risks --limit 10
python3 cli.py insights recommend --customer-id CUST_001
python3 cli.py insights similar --analysis-id ANALYSIS_456DEF --limit 5
python3 cli.py insights dashboard

# Knowledge Graph Management
python3 cli.py insights populate --analysis-id ANALYSIS_456DEF
python3 cli.py insights populate --all
python3 cli.py insights populate --from-date 2024-01-01
python3 cli.py insights query "MATCH (a:Analysis) RETURN count(a)"
python3 cli.py insights status
python3 cli.py insights delete-analysis ANALYSIS_456DEF
python3 cli.py insights delete-customer CUST_001 --cascade
python3 cli.py insights prune --older-than-days 90
python3 cli.py insights clear  # Requires confirmation
```

---

### 4. Plan Operations

**Resource Group:** `plan`

#### Available Commands:
- `create` - Create action plan from analysis
- `list` - List all plans
- `view` - View detailed plan information
- `update` - Update plan status
- `delete` - Delete specific plan
- `delete-all` - Delete all plans

#### Examples:

```bash
# Create action plan from analysis
python3 cli.py plan create --analysis ANALYSIS_456DEF

# List all plans
python3 cli.py plan list

# View detailed plan
python3 cli.py plan view PLAN_GHI789

# Update plan status
python3 cli.py plan update PLAN_GHI789 --status approved --approved-by advisor_001

# Delete specific plan
python3 cli.py plan delete PLAN_GHI789

# Delete all plans
python3 cli.py plan delete-all
```

---

### 5. Workflow Approval Operations

**Resource Group:** `workflow`

#### Core Workflow Commands:
- `extract` - Extract workflow from action plan
- `list` - List workflows with optional filters
- `view` - View detailed workflow information
- `pending` - List workflows pending approval
- `history` - View workflow state transition history

#### Approval Commands:
- `approve` - Approve a workflow
- `reject` - Reject a workflow
- `execute` - Execute an approved workflow

#### Examples:

```bash
# Extract workflow from action plan
python3 cli.py workflow extract PLAN_GHI789

# List all workflows
python3 cli.py workflow list

# List workflows by status
python3 cli.py workflow list --status AWAITING_APPROVAL

# List workflows by risk level
python3 cli.py workflow list --risk HIGH

# View detailed workflow information
python3 cli.py workflow view WF_JKL012

# List pending approvals
python3 cli.py workflow pending

# Approve a workflow
python3 cli.py workflow approve WF_JKL012 --approver advisor_001 --reasoning "Customer qualifies for program"

# Reject a workflow
python3 cli.py workflow reject WF_JKL012 --rejector supervisor_001 --reason "Additional documentation required"

# Execute approved workflow
python3 cli.py workflow execute WF_JKL012 --executor advisor_001

# View workflow history
python3 cli.py workflow history WF_JKL012
```

---

### 6. System Operations

**Resource Group:** `system`

#### Available Commands:
- `health` - Check system health
- `metrics` - Show system metrics

#### Examples:

```bash
# Check system health
python3 cli.py system health

# Show system metrics
python3 cli.py system metrics
```

---

## 🔍 Advanced Knowledge Graph Queries

### Raw Cypher Query Examples:

```bash
# Count all nodes in the graph
python3 cli.py insights query "MATCH (n) RETURN count(n) as total_nodes"

# Find high-risk analyses
python3 cli.py insights query "MATCH (a:Analysis) WHERE a.confidence_score > 0.8 RETURN a.analysis_id, a.primary_intent"

# Find customer patterns
python3 cli.py insights query "MATCH (c:Customer)-[:HAD_CALL]->(t:Transcript)-[:GENERATED_ANALYSIS]->(a:Analysis) RETURN c.customer_id, count(a) as analysis_count ORDER BY analysis_count DESC LIMIT 10"

# Find risk patterns
python3 cli.py insights query "MATCH (a:Analysis)-[:HAS_RISK_PATTERN]->(r:RiskPattern) WHERE r.risk_score >= 0.7 RETURN r.pattern_type, r.risk_score, count(a) as affected_analyses"

# Find compliance flags
python3 cli.py insights query "MATCH (a:Analysis)-[:HAS_COMPLIANCE_FLAG]->(c:ComplianceFlag) RETURN c.flag_type, c.severity, count(a) as flag_count"
```

---

## 🛠️ Command Options Reference

### Populate Command Options:
```bash
python3 cli.py insights populate [OPTIONS]
```
- `--analysis-id -a TEXT` - Single analysis ID to populate
- `--all` - Populate all analyses
- `--from-date TEXT` - Populate from date (YYYY-MM-DD)

### Query Command Options:
```bash
python3 cli.py insights query [OPTIONS] CYPHER
```
- `CYPHER` (required) - Cypher query to execute

### Delete Commands Options:
```bash
python3 cli.py insights delete-customer [OPTIONS] CUSTOMER_ID
```
- `--cascade` - Delete all related data (transcripts, analyses)

```bash
python3 cli.py insights prune [OPTIONS]
```
- `--older-than-days INTEGER` (required) - Delete data older than specified days

---

## 🎯 Common Workflows

### Complete Knowledge Graph Workflow:

```bash
# 1. Create transcript and analysis
python cli.py transcript create --topic "Payment dispute" --urgency high
# Note the TRANSCRIPT_ID

python cli.py analysis create --transcript-id CALL_123ABC
# Note the ANALYSIS_ID

# 2. Populate knowledge graph
python cli.py insights populate --analysis-id ANALYSIS_456DEF

# 3. Check status
python cli.py insights status

# 4. Run analytics
python cli.py insights patterns
python cli.py insights risks
python cli.py analysis dashboard

# 5. Query for insights
python cli.py insights query "MATCH (a:Analysis) RETURN a.primary_intent, count(*) ORDER BY count(*) DESC"
```

### GDPR Compliance Workflow:

```bash
# Delete specific customer data
python cli.py insights delete-customer CUST_001 --cascade

# Prune old data (90 days)
python cli.py insights prune --older-than-days 90

# Complete cleanup (DANGER!)
python cli.py insights clear
```

---

## ⚠️ Important Notes

### NO FALLBACK Principle:
- All commands require proper API integration (OpenAI API key)
- Commands fail fast rather than returning mock data
- No placeholder or fallback responses

### Knowledge Graph Operations:
- `populate` commands are manual (not automatic)
- `clear-graph` requires user confirmation
- GDPR compliance through `delete-customer` and `prune` commands

### Data Flow:
1. **Transcript** → Created with customer conversation
2. **Analysis** → AI analysis of transcript (requires OpenAI API)
3. **Knowledge Graph** → Manual population from analysis data
4. **Analytics** → Pattern detection and insights from graph data

---

## 🔧 Prerequisites

1. **Virtual Environment**: `source venv/bin/activate`
2. **OpenAI API Key**: Set `OPENAI_API_KEY` environment variable
3. **Backend Running**: `python3 server.py` or `./start_services.sh`
4. **Database**: SQLite and KuzuDB initialized automatically

---

## 📊 Success Indicators

Commands should show:
- ✅ Success confirmations with generated IDs
- 📊 Tabulated output for list commands
- 🔍 Structured JSON for detailed views
- ⚠️ Clear error messages for failures (NO FALLBACK)

Example success output:
```
✅ Analysis ANALYSIS_456DEF populated in knowledge graph
📈 Knowledge Graph Status: Total Nodes: 5, Relationships: 8
🔍 Found 3 high-risk patterns above threshold 0.7
```

---

## 🆘 Troubleshooting

### Common Issues:
- **"Server not available"** → Start backend: `python3 server.py`  
- **"OpenAI API error"** → Check `OPENAI_API_KEY` environment variable
- **"Analysis not found"** → Verify analysis ID exists: `python3 cli.py analysis list`
- **"Graph shows 0 nodes"** → Check if populate succeeded: `python3 cli.py insights status`

### Debug Commands:
```bash
# System health check
python3 cli.py system health

# Verify API connectivity  
python3 cli.py --verbose system health

# Check server logs
tail -f server.log
```