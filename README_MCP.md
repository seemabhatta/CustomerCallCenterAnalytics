# MCP Server for Customer Call Center Analytics

This MCP (Model Context Protocol) server provides AI-powered tools for analyzing customer call center transcripts and generating actionable insights.

## Features

### 🛠️ Tools Available

- **generate_transcripts** - Generate realistic call center transcripts based on scenarios
- **analyze_transcript** - Comprehensive multi-agent analysis for insights, compliance, and action items  
- **search_transcripts** - Search through call transcripts using natural language queries
- **list_transcripts** - List recent call transcripts and analyses
- **plan_mode** - Create actionable plans using Co-Pilot planning mode
- **execute_mode** - Execute plans with downstream system integrations
- **get_system_status** - Get system status and storage statistics

## Quick Start

### 1. Install Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 3. Run the MCP Server

```bash
# Start the server
python run_mcp_server.py

# Server will be available at:
# HTTP: http://localhost:8000
# MCP endpoint: http://localhost:8000/mcp
```

### 4. Configure Claude Code

Copy the MCP server configuration to Claude Code:

```bash
# Copy configuration 
cp claude_code_mcp_config.json ~/.claude/mcp_servers.json
```

Or manually add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "customer-call-center-analytics": {
      "command": "python",
      "args": ["/path/to/your/project/run_mcp_server.py"],
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

## Usage Examples

### Generate Transcripts
```
Tool: generate_transcripts
Args: {"scenario": "Angry customer about late fees", "count": 2}
```

### Analyze Transcript
```
Tool: analyze_transcript  
Args: {"transcript_content": "Customer: I'm very upset about..."}
```

### Search Transcripts
```
Tool: search_transcripts
Args: {"query": "payment issues", "limit": 5}
```

### Create Action Plan
```
Tool: plan_mode
Args: {"request": "Help customer with escrow shortage"}
```

### Execute Plan
```
Tool: execute_mode
Args: {"auto_execute": false}
```

## Architecture

The MCP server integrates with your existing call center analytics system:

- **Storage Layer** - TinyDB/SQLite for transcript and analysis storage
- **Agent Layer** - OpenAI Agents SDK for multi-agent analysis
- **Orchestration** - n8n workflow integration for downstream actions
- **MCP Layer** - FastMCP for protocol compliance and tool exposure

## Capabilities

- **Multi-Agent Analysis** - Comprehensive transcript analysis using specialized agents
- **Co-Pilot Modes** - Plan, Execute, Reflect workflow for complex scenarios  
- **Integration Ready** - Downstream system integrations via orchestration layer
- **Contextual Search** - Natural language search across transcript database
- **Real-time Insights** - Live analysis with compliance and risk assessment

## Development

### Project Structure
```
├── src/
│   ├── mcp_server.py      # MCP server implementation
│   ├── agents.py          # OpenAI agents 
│   ├── storage.py         # Data storage layer
│   └── config.py          # Configuration
├── run_mcp_server.py      # Server runner
├── mcp_config.json        # MCP server metadata
└── claude_code_mcp_config.json  # Claude Code configuration
```

### Custom Tools

To add new tools, modify `src/mcp_server.py`:

```python
@mcp.tool()
async def your_custom_tool(args: YourArgsModel) -> str:
    """Your tool description"""
    # Implementation
    return "Result"
```

## Troubleshooting

### Common Issues

1. **Import Errors** - Make sure all dependencies are installed in venv
2. **API Key Issues** - Verify OPENAI_API_KEY is set correctly  
3. **Port Conflicts** - Change port in `run_mcp_server.py` if needed
4. **Path Issues** - Update paths in `claude_code_mcp_config.json`

### Logs

Server logs are displayed in console. For debugging:

```bash
# Run with verbose logging
python run_mcp_server.py --log-level debug
```

## Support

- Check existing transcripts: `python -m src.cli list`
- Test basic functionality: `python -m src.cli status`  
- Generate test data: `python -m src.cli generate --count 3`