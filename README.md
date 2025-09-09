# Customer Call Center Analytics

A comprehensive AI-powered system for generating and analyzing call center transcripts with **Post-Call Intelligence Analytics**. Features mortgage servicing insights, risk assessment, and advisor performance metrics using OpenAI's Responses API. Built with clean architecture principles featuring instant-execution CLI and full REST API.

## ⚡ Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start the universal server (handles both CLI and API)
./start_services.sh

# Use instant CLI (no import delays!)
python cli_fast.py demo
python cli_fast.py generate scenario="PMI Removal" --store
python cli_fast.py list
python cli_fast.py stats

# Analytics and Intelligence
python cli_fast.py analyze --transcript-id CALL_001
python cli_fast.py analysis-metrics
python cli_fast.py risk-report --threshold 0.7
```

## 🏗️ Architecture

This project implements a Universal Server Architecture with clean separation of concerns:

### Core Components
- **Business Logic Layer** (`src/`) - Pure Python, no UI dependencies
- **Interface Layers** - CLI and API consume the same business logic  
- **Universal Server** (`server.py`) - Pre-loads imports, serves multiple interfaces
- **Fast CLI Client** (`cli_fast.py`) - Instant execution via HTTP to server

### Performance Innovation
- **Traditional CLI**: 12+ seconds (OpenAI import delay)
- **Fast CLI**: ~1 second (10x faster via pre-loaded server)
- **Same business logic** powers both CLI and API interfaces

### Analytics Pipeline
Generate Calls → Store → Analyze → Store Analysis → Reports & Insights

## 📁 Project Structure

```
├── src/                           # Pure Business Logic
│   ├── generators/
│   │   └── transcript_generator.py   # Core transcript generation
│   ├── analyzers/
│   │   └── call_analyzer.py          # Post-call intelligence
│   ├── storage/
│   │   ├── transcript_store.py       # Transcript storage
│   │   └── analysis_store.py         # Analysis results storage
│   ├── models/
│   │   └── transcript.py             # Data models
│   └── tools.py                      # LLM tools & utilities
├── interfaces/                    # Interface Layer
│   ├── cli.py                        # Traditional CLI (slower)
│   ├── cli_fast.py                   # Fast CLI client
│   ├── api.py                        # Standalone FastAPI
│   └── server.py                     # Universal server
├── tests/                         # Test Layer
│   ├── test_transcript_generator.py  # Business logic tests
│   ├── test_call_analyzer.py         # Analytics tests
│   ├── test_analysis_store.py        # Analysis storage tests
│   └── test_cli.py                   # CLI interface tests
├── scripts/                       # Utilities
│   ├── cleanup.sh                    # Port cleanup
│   └── start_services.sh             # Server starter
└── data/                          # Storage
    └── call_center.db                # SQLite database
```

## 📊 Features

### AI-Powered Generation
- Realistic conversations using OpenAI's API
- Dynamic scenarios: PMI removal, payment disputes, refinancing, etc.
- Flexible parameters: customer sentiment, urgency, outcomes
- Consistent formatting with speaker identification

### 🧠 Post-Call Intelligence Analytics
- **Mortgage-specific risk assessment** (delinquency, churn, complaint risks)
- **Advisor performance metrics** and coaching opportunities
- **Compliance monitoring** and disclosure tracking
- **Multi-layer insights**: Borrower, Advisor, Supervisor, Leadership
- **Structured analysis** using OpenAI Responses API with confidence scoring
- **Comprehensive reporting** and metrics dashboard

### Data Management
- SQLite storage with full CRUD operations
- Search capabilities: by customer, topic, or text content
- Export functionality to JSON format
- Statistics and analytics on conversation patterns
- Enriched analysis storage with quick-access fields for reporting

### Multiple Interfaces
- **Fast CLI**: Instant execution for development workflow
- **REST API**: Full programmatic access with OpenAPI docs
- **Traditional CLI**: Direct access to business logic
- **Clean separation**: Same logic powers all interfaces

## 🚀 Usage

### Fast CLI (Recommended)
Instant execution via pre-loaded server:

```bash
# Generate transcripts
python cli_fast.py generate scenario="PMI Removal" customer_id="CUST_001" --store --show
python cli_fast.py generate --count 5 topic="Refinance" --store

# View and search
python cli_fast.py list --detailed
python cli_fast.py get TRANSCRIPT_ID --export
python cli_fast.py search --customer CUST_001
python cli_fast.py search --text "payment"

# Basic Analytics
python cli_fast.py stats
python cli_fast.py export --output backup.json

# Post-Call Intelligence
python cli_fast.py analyze --transcript-id CALL_001
python cli_fast.py analyze --all
python cli_fast.py analysis-report --transcript-id CALL_001
python cli_fast.py analysis-metrics
python cli_fast.py risk-report --threshold 0.8

# Demo data
python cli_fast.py demo
```

### Web API
Full REST API with interactive documentation:

```bash
# Access API documentation
open http://localhost:8000/docs

# API endpoints
curl http://localhost:8000/stats
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"scenario":"PMI Removal","customer_id":"API_001"}'
curl http://localhost:8000/transcripts
```

### Traditional CLI
Direct business logic access (slower due to imports):

```bash
python cli.py generate scenario="PMI Removal" --store
python cli.py list
```

## 🛠️ Advanced Usage

### Server Management
```bash
# Start with cleanup and status
./start_services.sh

# Manual startup
python server.py

# Clean shutdown (Press Ctrl+C once - server shuts down gracefully)

# Force cleanup if needed
./stop_services.sh
```

### Custom Parameters
The system supports dynamic parameters for realistic conversation generation:

```bash
# Mortgage scenarios
python cli_fast.py generate scenario="PMI Removal" sentiment="hopeful" urgency="medium"
python cli_fast.py generate scenario="Escrow Shortage" customer_id="CUST_123" outcome="resolved"

# Batch generation
python cli_fast.py generate --count 10 scenario="Payment Dispute" --store
```

### Export and Integration
```bash
# Export all data
python cli_fast.py export --output company_transcripts.json

# Get specific transcript
python cli_fast.py get CALL_ABC123 --export
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
DATABASE_PATH=data/call_center.db
CLI_SERVER_PORT=9999
API_SERVER_PORT=8000
```

### Customizing Scenarios
Edit `src/tools.py` to modify:
- Available scenarios
- Customer sentiment options
- Call outcomes
- Conversation patterns

## 🧪 Testing

```bash
# Run all tests
pytest

# Test specific components
pytest tests/test_transcript_generator.py
pytest tests/test_cli.py

# Analytics testing
pytest tests/test_call_analyzer.py     # OpenAI Responses API tests
pytest tests/test_analysis_store.py    # Analysis storage tests

# Performance comparison
time python cli.py stats     # ~12 seconds
time python cli_fast.py stats # ~1 second
```

## 📈 Performance

### Benchmarks
- **Server startup**: ~17-20 seconds (one-time cost)
- **Fast CLI execution**: ~1 second per command
- **Traditional CLI**: ~12 seconds per command
- **API response time**: <100ms for most operations

### Scalability
- **Concurrent requests**: Handles multiple CLI clients simultaneously
- **Database**: SQLite suitable for development; easily upgradeable to PostgreSQL
- **Memory usage**: ~80MB with all imports pre-loaded

## 🔍 Troubleshooting

### Common Issues

**Server won't start:**
```bash
./server_stop.sh  # Clean up port conflicts
python server.py  # Start in foreground to see errors
```

**CLI client can't connect:**
```bash
# Check if server is running
curl http://localhost:9999 || echo "Server not running"
curl http://localhost:8000 || echo "API not running"
```

**Import delays:**
- Use `cli_fast.py` instead of `cli.py`
- Ensure server is running first with `./start_services.sh`

**Database issues:**
```bash
# Reset database
rm data/call_center.db
python cli_fast.py demo  # Regenerate sample data
```

### Port Conflicts
The server automatically tries alternate ports:
- **CLI Backend**: 9999, 9998, 9997, 9996
- **FastAPI**: 8000, 8001, 8002, 8003

Run `./cleanup.sh` to force-clean any conflicts.

## 🤝 Contributing

This project follows clean architecture principles:

1. **Business logic must remain pure** (no UI dependencies)
2. **Interface layers should be thin wrappers**
3. **Tests should be separated by layer**
4. **Dynamic parameters preferred** over hardcoded validation

### Architecture Principles
- **Agentic Approach**: Trust AI/LLM decisions, minimal constraints
- **Clean Separation**: Business logic independent of interfaces
- **Performance First**: Optimize for development workflow speed
- **Flexible Models**: Use **kwargs and dynamic attributes

### Developer Experience
- No hardcoded validation - trust the AI/LLM
- Dynamic parameters using **kwargs pattern
- Comprehensive testing with separate test layers
- Port conflict handling with automatic fallbacks

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 API Reference

For detailed API documentation, start the server and visit: http://localhost:8000/docs