# MCP Multi-App Architecture - ChatGPT Integration

## Overview

This MCP (Model Context Protocol) implementation provides **5 focused apps** that enable ChatGPT to interact with the Customer Call Center Analytics system. Each app is optimized for specific use cases with filtered tool sets and discovery keywords, allowing ChatGPT to automatically select the right app based on user intent.

## Multi-App Architecture

```
┌─────────────┐
│   ChatGPT   │ Natural language interface
└──────┬──────┘
       │ MCP Protocol (auto-selects app based on intent)
       │
       ├─────────────────────────────────────┬──────────────────────────────┐
       │                                     │                              │
       ↓                                     ↓                              ↓
┌──────────────────┐         ┌──────────────────────┐      ┌────────────────────────┐
│ Universal (8001) │         │ Advisor Apps         │      │ Leadership Apps        │
│ All 26 tools     │         │ - Borrower (8002)    │      │ - Portfolio (8004)     │
│ Admin/Power      │         │ - Performance (8003) │      │ - Strategy (8005)      │
└────────┬─────────┘         └──────────┬───────────┘      └───────────┬────────────┘
         │                              │                              │
         └──────────────────────────────┴──────────────────────────────┘
                                        │
                                        ↓
                              ┌─────────────────┐
                              │ Service Layer   │ Shared business logic
                              │ - Transcript    │
                              │ - Analysis      │
                              │ - Workflow      │
                              │ - Execution     │
                              └─────────────────┘
```

## The 5 MCP Apps

| App | Port | Tools | Use Case | Discovery Keywords |
|-----|------|-------|----------|-------------------|
| **Universal Analytics** | 8001 | 26 | Admin/power users, full access | admin, system wide, all tools |
| **Advisor Borrower Assistant** | 8002 | 19 | Customer service operations | customer, PMI, escrow, refinance, workflow |
| **Advisor Performance Coach** | 8003 | 5 | Personal performance review | my performance, self review, improvement |
| **Leadership Portfolio Manager** | 8004 | 12 | Organization-wide management | portfolio, high-risk, orchestration, batch |
| **Leadership Strategy Advisor** | 8005 | 7 | Strategic insights & optimization | performance, statistics, optimization |

### How ChatGPT Auto-Discovery Works

ChatGPT's model automatically selects the appropriate app based on:
1. **User's prompt** - Keywords and intent
2. **Tool metadata** - Descriptions optimized for each app
3. **Past usage patterns** - Learning from successful interactions

**Example:**
- User: "Help me with customer PMI removal" → **Advisor Borrower** (8002)
- User: "How's my performance this week?" → **Advisor Performance** (8003)
- User: "Show me high-risk customers" → **Leadership Portfolio** (8004)
- User: "System execution statistics" → **Leadership Strategy** (8005)

## Available Tools (26)

> The tool catalog is defined once in `src/infrastructure/mcp/tool_definitions.py` and consumed by the MCP server at runtime. Update that module to add, remove, or edit tools—documentation and runtime stay in sync.

### Pipeline Automation (6)
1. **create_transcript** – Generate customer call transcripts.
2. **analyze_transcript** – Analyze calls for risks, sentiment, compliance.
3. **create_action_plan** – Generate strategic action plans.
4. **extract_workflows** – Break plans into executable workflows.
5. **approve_workflow** – Approve workflows for execution.
6. **execute_workflow** – Execute approved workflows end-to-end.

### Transcript & Analysis Insights (8)
7. **list_transcripts** – List recorded calls with lightweight metadata.
8. **get_transcript** – Retrieve the full transcript by ID.
9. **get_analysis** – Fetch analysis details for a transcript.
10. **list_analyses** – List all analyses in the system.
11. **get_analysis_by_id** – Retrieve a specific analysis by its ID.
12. **get_action_plan** – Fetch existing action plans for an analysis.
13. **get_plan_by_id** – Retrieve a specific plan by its ID.
14. **get_plan_by_transcript** – Retrieve a plan by its transcript ID.

### Workflow Monitoring & Control (6)
15. **get_workflow** – Inspect workflow metadata and configured steps.
16. **list_workflows** – Filter workflows by plan, status, or risk.
17. **get_workflow_steps** – Retrieve step-by-step instructions for a workflow.
18. **execute_workflow_step** – Run an individual workflow step.
19. **get_step_status** – Check execution status for a workflow step.
20. **get_execution_status** – Review results of a workflow execution run.

### Execution Tracking (2)
21. **list_executions** – List all workflow executions with optional filters.
22. **get_execution_statistics** – Get comprehensive execution statistics and success rates.

### Orchestration Operations (3)
23. **run_orchestration** – Kick off the full Transcript→Execute pipeline for one or more calls.
24. **get_orchestration_status** – Track progress of an orchestration run.
25. **list_orchestration_runs** – Review prior orchestration runs.

### Analytics & Health (1)
26. **get_dashboard_metrics** – Surface platform KPIs and pipeline stage load.

## Quick Start

### Option A: Start All Apps at Once

```bash
# Start all 5 apps (ports 8001-8005)
cd src/infrastructure/mcp
./start_all_apps.sh

# Stop all apps
./stop_all_apps.sh
```

Logs are written to `logs/mcp_*.log`

### Option B: Start Individual Apps

```bash
# Universal Analytics (all 26 tools)
python src/infrastructure/mcp/mcp_server.py

# Advisor Borrower Assistant
python src/infrastructure/mcp/apps/advisor_borrower_server.py

# Advisor Performance Coach
python src/infrastructure/mcp/apps/advisor_performance_server.py

# Leadership Portfolio Manager
python src/infrastructure/mcp/apps/leadership_portfolio_server.py

# Leadership Strategy Advisor
python src/infrastructure/mcp/apps/leadership_strategy_server.py
```

### Verify Apps are Running

```bash
# Check all ports
for port in 8001 8002 8003 8004 8005; do
  echo "Port $port: $(curl -s http://localhost:$port/mcp | head -1)"
done
```

### Test Tool Calls

```bash
# Example: Create transcript via Advisor Borrower app (port 8002)
curl -X POST http://localhost:8002/execute \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "create_transcript",
    "params": {
      "topic": "PMI_removal",
      "urgency": "high",
      "customer_sentiment": "frustrated"
    }
  }'
```

## ChatGPT Integration Setup

### Multi-App Configuration

You can configure **multiple MCP apps** in ChatGPT. ChatGPT's model will automatically select the appropriate app based on your conversation intent.

### Option 1: Local Development with ngrok

1. **Install ngrok**
   ```bash
   # Download from https://ngrok.com/
   brew install ngrok  # macOS
   # or download binary for your OS
   ```

2. **Start All Apps**
   ```bash
   # Terminal 1: Start all 5 apps
   cd src/infrastructure/mcp
   ./start_all_apps.sh
   ```

3. **Expose Each App via ngrok** (separate terminals)
   ```bash
   # Terminal 2: Universal
   ngrok http 8001

   # Terminal 3: Advisor Borrower
   ngrok http 8002

   # Terminal 4: Advisor Performance
   ngrok http 8003

   # Terminal 5: Leadership Portfolio
   ngrok http 8004

   # Terminal 6: Leadership Strategy
   ngrok http 8005
   ```

   You'll get URLs like: `https://abc123.ngrok.io`, `https://def456.ngrok.io`, etc.

4. **Configure ChatGPT Apps** (Settings → Apps → Add App)

   Add each app separately:

   | App Name | ngrok URL | Description |
   |----------|-----------|-------------|
   | Universal Analytics | `https://abc123.ngrok.io` | Complete tool suite |
   | Advisor - Borrower Mode | `https://def456.ngrok.io` | Customer service |
   | Advisor - Performance | `https://ghi789.ngrok.io` | Self-review |
   | Leadership - Portfolio | `https://jkl012.ngrok.io` | Portfolio management |
   | Leadership - Strategy | `https://mno345.ngrok.io` | Strategic insights |

5. **Test Auto-Discovery**

   Open ChatGPT and try different prompts to see which app gets selected:

   ```
   "Help me resolve a customer PMI removal request"
   → ChatGPT selects: Advisor - Borrower Mode (8002)

   "How's my call handling performance this week?"
   → ChatGPT selects: Advisor - Performance (8003)

   "Show me all high-risk customers in the portfolio"
   → ChatGPT selects: Leadership - Portfolio (8004)

   "What's the system-wide execution success rate?"
   → ChatGPT selects: Leadership - Strategy (8005)
   ```

### Option 2: Production Deployment

For production, deploy the MCP server to a cloud provider:

**Railway.com** (Recommended):
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway up

# Get public URL
railway domain
```

**Or use any hosting platform that supports Python/FastAPI:**
- Heroku
- AWS Elastic Beanstalk
- Google Cloud Run
- Azure App Service

## Example ChatGPT Conversations

### End-to-End Pipeline

**User:** "Process a customer call about PMI removal"

**ChatGPT executes:**
1. `create_transcript(topic="PMI_removal")`
2. `analyze_transcript(transcript_id="TRANS_XXX")`
3. `create_action_plan(analysis_id="ANA_YYY")`
4. `extract_workflows(plan_id="PLAN_ZZZ")`
5. Shows results to user

### Workflow Management

**User:** "Show me all pending workflows"

**ChatGPT:** `list_workflows(status="pending")`

**User:** "Approve workflow WF_123 and execute it"

**ChatGPT:**
1. `approve_workflow(workflow_id="WF_123", approved_by="ChatGPT")`
2. `execute_workflow(workflow_id="WF_123", executed_by="ChatGPT")`

### Step-by-Step Execution

**User:** "Show me the steps for workflow WF_456"

**ChatGPT:** `get_workflow_steps(workflow_id="WF_456")`

**User:** "Execute just step 2"

**ChatGPT:** `execute_workflow_step(workflow_id="WF_456", step_number=2, executed_by="ChatGPT")`

### Analytics

**User:** "How's the system performing?"

**ChatGPT:** `get_dashboard_metrics()`

## Tool Details

### create_transcript

Creates a realistic customer call transcript.

**Parameters:**
- `topic` (optional): Call topic (default: "payment_inquiry")
  - Examples: "PMI_removal", "hardship_assistance", "escrow_inquiry"
- `urgency` (optional): low/medium/high/critical
- `financial_impact` (optional): boolean
- `customer_sentiment` (optional): positive/neutral/frustrated/angry
- `customer_id` (optional): Customer identifier

**Response:**
```json
{
  "success": true,
  "transcript_id": "TRANS_ABC123",
  "content": "...",
  "metadata": {...}
}
```

### analyze_transcript

Analyzes transcript for intent, risks, compliance, sentiment.

**Parameters:**
- `transcript_id` (required): Transcript to analyze
- `analysis_type` (optional): comprehensive/quick/compliance_focused

**Response:**
```json
{
  "success": true,
  "analysis_id": "ANA_XYZ789",
  "intent": "PMI_REMOVAL",
  "urgency": "high",
  "risks": [...],
  "compliance_issues": [...],
  "sentiment": "frustrated",
  "recommendations": [...]
}
```

### create_action_plan

Generates strategic action plan from analysis.

**Parameters:**
- `analysis_id` (required): Analysis to plan from
- `plan_type` (optional): standard/expedited/compliance_priority
- `urgency` (optional): low/medium/high/critical

**Response:**
```json
{
  "success": true,
  "plan_id": "PLAN_DEF456",
  "actions": [...],
  "priority": "high",
  "estimated_completion": "2024-10-10"
}
```

### extract_workflows

Breaks action plan into detailed, executable workflows.

**Parameters:**
- `plan_id` (required): Plan to extract workflows from

**Response:**
```json
{
  "success": true,
  "plan_id": "PLAN_DEF456",
  "workflow_count": 3,
  "extraction_status": "completed"
}
```

### approve_workflow

Approves workflow for execution.

**Parameters:**
- `workflow_id` (required): Workflow to approve
- `approved_by` (required): Approver identifier
- `reasoning` (optional): Approval notes

**Response:**
```json
{
  "success": true,
  "workflow_id": "WF_GHI789",
  "status": "approved",
  "approved_by": "ChatGPT"
}
```

### execute_workflow

Executes approved workflow.

**Parameters:**
- `workflow_id` (required): Workflow to execute
- `executed_by` (required): Executor identifier

**Response:**
```json
{
  "success": true,
  "workflow_id": "WF_GHI789",
  "execution_id": "EXEC_JKL012",
  "status": "completed",
  "results": [...]
}
```

## Development

### Running Alongside Main API

The MCP server runs on port 8001, while the main API runs on port 8000. Both can run simultaneously:

```bash
# Terminal 1: Main API
python server.py

# Terminal 2: MCP Server
python src/infrastructure/mcp/mcp_server.py
```

### Testing Tools Locally

```bash
# Create transcript
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "create_transcript", "params": {"topic": "PMI_removal"}}'

# Analyze it (use transcript_id from above)
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "analyze_transcript", "params": {"transcript_id": "TRANS_XXX"}}'
```

### Debugging

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python src/infrastructure/mcp/mcp_server.py
```

Check logs for tool execution details.

## Architecture Principles

### NO FALLBACK
- Server fails fast on errors
- No mock data or degraded modes
- Clear error messages returned to ChatGPT

### Service Layer Reuse
- MCP server reuses existing services
- No duplication of business logic
- Consistent behavior across APIs

### Stateless Tools
- Each tool call is independent
- No session management needed
- ChatGPT handles conversation context

## Security Considerations

### Production Deployment
- Use HTTPS (ngrok provides this automatically)
- Add authentication middleware
- Rate limit tool calls
- Validate all inputs (Pydantic schemas)

### Environment Variables
```bash
OPENAI_API_KEY=sk-...
DATABASE_PATH=./data/call_center.db
LOG_LEVEL=INFO
```

## Troubleshooting

### Server won't start
- Check `OPENAI_API_KEY` is set in `.env`
- Verify port 8001 is available
- Check database path exists

### ChatGPT can't connect
- Verify ngrok is running
- Check ngrok URL is correct in ChatGPT settings
- Test with `curl` first

### Tool calls fail
- Check logs: `tail -f mcp_server.log`
- Verify service layer is working
- Test tool directly via `/execute` endpoint

## Support

For issues or questions:
- Check logs in `mcp_server.log`
- Review tool definitions in `tool_definitions.py`
- Test individual services via main API on port 8000
- Create GitHub issue with error details
