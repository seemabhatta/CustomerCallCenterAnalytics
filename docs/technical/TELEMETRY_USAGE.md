# OpenTelemetry Telemetry Usage Guide

## Overview

The system now includes comprehensive OpenTelemetry distributed tracing with a simple, readable console output format designed for easy debugging and monitoring.

## Installation

First, install the OpenTelemetry dependencies in a virtual environment:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Telemetry is configured via environment variables in `.env`:

```bash
# OpenTelemetry Configuration
OTEL_CONSOLE_ENABLED=true          # Enable console output
OTEL_JAEGER_ENABLED=false          # Enable Jaeger UI (requires Docker)
OTEL_OTLP_ENABLED=false            # Enable OTLP export (for cloud platforms)
OTEL_CONSOLE_FORMAT=simple         # Use simple one-line format (vs "json")
```

## Console Output Formats

### Simple Format (Default)
Clean, readable one-line output showing the most important information:

```
[10:23:45] → orchestration.run_complete_pipeline | ... | transcriptid=CALL_001
[10:23:45]   → pipeline.stage.analysis | 0.8s
[10:23:46]   ✓ pipeline.stage.analysis | 1.2s | analysisid=AN_123
[10:23:46]   → pipeline.stage.plan | 0.0s
[10:23:47]   ✓ pipeline.stage.plan | 0.9s | planid=PL_456
[10:23:47]   → pipeline.stage.workflows | 0.0s
[10:23:47]   📝 stage.started | stage=workflows message=This stage may take 2-5 minutes
[10:23:47]     → risk_agent.assess_action_item_risk | ... | workflowtype=BORROWER
[10:23:52]     ✓ risk_agent.assess_action_item_risk | 5.1s | risklevel=HIGH actionitemid=123
[10:23:52]     → risk_agent.assess_action_item_risk | ... | workflowtype=ADVISOR  
[10:23:57]     ✓ risk_agent.assess_action_item_risk | 4.8s | risklevel=LOW actionitemid=456
[10:28:47]   ✓ pipeline.stage.workflows | 300.2s | workflowcount=14
[10:28:48] ✓ orchestration.run_complete_pipeline | 302.5s | pipelinestatus=success
```

### JSON Format
Set `OTEL_CONSOLE_FORMAT=json` for detailed JSON output (useful for programmatic analysis).

## Understanding the Output

### Status Icons
- `→` - Operation in progress
- `✓` - Operation completed successfully  
- `✗` - Operation failed with error
- `📝` - Event occurred (sub-operation or milestone)

### Key Information
- `[HH:MM:SS]` - Timestamp when operation started/completed
- `operation_name` - What operation is being performed
- `duration` - How long the operation took (in seconds)
- `key=value` - Important attributes and context

### Identifying Bottlenecks

The format makes it easy to spot performance issues:

1. **Long durations**: Look for operations taking >30s
2. **Missing progress**: Operations stuck with `→` status
3. **Risk assessment delays**: Individual risk assessments taking >5s each
4. **Workflow stage timing**: The `pipeline.stage.workflows` will show total time

## Example Pipeline Execution

```bash
# Run a complete pipeline with telemetry
python cli.py orchestrate transcript CALL_001 --auto-approve --verbose

# You'll see output like:
[14:23:15] → orchestration.run_complete_pipeline | ... | transcriptid=CALL_001 autoapprove=true
[14:23:16] ✓ pipeline.stage.analysis | 1.1s | analysisid=AN_789
[14:23:17] ✓ pipeline.stage.plan | 0.8s | planid=PL_101
[14:23:18] → pipeline.stage.workflows | ...
[14:23:18]   📝 stage.started | stage=workflows message=This stage may take 2-5 minutes
[14:23:19]     ✓ risk_agent.assess_action_item_risk | 3.2s | workflowtype=BORROWER risklevel=MEDIUM
[14:23:22]     ✓ risk_agent.assess_action_item_risk | 2.8s | workflowtype=ADVISOR risklevel=LOW
[14:23:25]     ✓ risk_agent.assess_action_item_risk | 3.1s | workflowtype=SUPERVISOR risklevel=HIGH
[14:26:45] ✓ pipeline.stage.workflows | 207.3s | workflowcount=12
[14:26:46] ✓ orchestration.run_complete_pipeline | 210.8s | pipelinestatus=success workflowcount=12 executedcount=12
```

## Switching Between Formats

### To JSON format:
```bash
export OTEL_CONSOLE_FORMAT=json
python cli.py orchestrate transcript CALL_001
```

### Back to simple format:
```bash
export OTEL_CONSOLE_FORMAT=simple
python cli.py orchestrate transcript CALL_001
```

## Additional Viewing Options

### Jaeger UI (Visual Interface)

1. Start Jaeger with Docker:
```bash
docker run -d --name jaeger -p 16686:16686 -p 6831:6831/udp jaegertracing/all-in-one:latest
```

2. Enable Jaeger export:
```bash
export OTEL_JAEGER_ENABLED=true
export OTEL_CONSOLE_ENABLED=false  # Optional: reduce noise
```

3. Open http://localhost:16686 in your browser

4. Run your pipeline - traces will appear in Jaeger UI

### Cloud Platforms (Production)

For production monitoring, configure OTLP export to your observability platform:

```bash
export OTEL_OTLP_ENABLED=true
export OTEL_EXPORTER_OTLP_ENDPOINT=https://your-platform.com:4317
export OTEL_EXPORTER_OTLP_TOKEN=your-auth-token
```

## Testing the Implementation

Run the telemetry test suite:

```bash
python3 test_telemetry.py
```

This will test all telemetry components and show you sample output in both formats.

## Troubleshooting

### No telemetry output
- Check that `OTEL_CONSOLE_ENABLED=true` in your `.env`
- Ensure OpenTelemetry packages are installed
- Verify the virtual environment is activated

### JSON instead of simple format
- Check `OTEL_CONSOLE_FORMAT=simple` in your `.env`
- Environment variables override `.env` settings

### Missing spans
- Ensure telemetry is initialized before running operations
- Check that services are importing from `src.telemetry`

The simple format provides immediate visibility into your pipeline execution, making it easy to identify the exact bottlenecks (especially the 2-7 minute risk assessment delays) without parsing complex JSON output.