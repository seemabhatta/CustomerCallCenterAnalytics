# Automated Test Harness for Advisor Agent

## Overview

This is an automated test harness that continuously tests the advisor agent API, finds bugs, creates GitHub issues, and suggests fixes. It uses LLM-driven scenario generation and response analysis.

## Features

- 🧪 **API Testing**: Tests advisor agent via REST API calls
- 🤖 **LLM Analysis**: Uses LLMClientV2 to intelligently analyze responses
- 📝 **GitHub Integration**: Automatically creates issues for bugs
- 🔄 **Self-Improving**: Generates new test scenarios based on findings
- 🛠️ **Fix Suggestions**: Provides specific code fixes for bugs

## Files

- `test_runner.py` - Main test orchestrator
- `test_scenarios.yaml` - Initial test scenarios (LLM generates more)
- `requirements.txt` - Dependencies (aiohttp, PyYAML)
- `README.md` - This file

## Setup

1. **Install dependencies**:
   ```bash
   cd test_advisor
   pip install -r requirements.txt
   ```

2. **Make sure server is running**:
   ```bash
   # In one terminal
   python server.py
   ```

3. **Run the test harness**:
   ```bash
   # In another terminal
   cd test_advisor
   python test_runner.py
   ```

## How It Works

### 1. Test Loop
- Loads test scenarios from YAML file
- For each iteration, either uses initial scenarios or generates new ones based on bugs found
- Tests scenarios via API calls to `/api/v1/advisor/chat`

### 2. LLM Analysis
- Sends each response to LLMClientV2 for intelligent analysis
- Checks for semantic correctness, tool usage, context awareness
- Identifies specific bug types: missing tools, wrong tools, context not used, etc.

### 3. Issue Creation
- Creates GitHub issues automatically using `gh` CLI
- Includes test scenario, bug details, and evidence
- Labels issues with "bug" and "automated-test"

### 4. Fix Generation
- LLM generates specific fix instructions
- Identifies which files need changes
- Provides code snippets and explanations

### 5. Self-Improvement
- Generates new test scenarios based on bugs found
- Focuses on areas where problems occur
- Continuously expands test coverage

## Example Bug Detection

The harness will detect bugs like:

```yaml
Bug Type: missing_tool
Description: "Asked for analysis but returned transcript list instead"
Evidence: "Here are the last 2 calls from your records..."
Fix: "Add get_transcript_analysis tool to workflow_tools.py"
```

## Test Scenarios

Initial scenarios test:
- Context-aware analysis requests
- Workflow resolution from transcripts
- Direct workflow execution
- Context switching
- Error handling
- Help and guidance

New scenarios are generated automatically based on findings.

## Usage Notes

- Requires GitHub CLI (`gh`) for issue creation
- Uses existing LLMClientV2 from main project
- Runs continuously until stopped with Ctrl+C
- Each iteration waits 2 minutes before repeating
- Results are saved and used for scenario generation

## Output

The harness provides real-time output showing:
- Which scenarios are being tested
- Test results (✅ pass, ❌ bugs found)
- GitHub issue numbers created
- Fix suggestions generated

This creates a self-testing, self-improving system that makes the advisor agent more robust over time!