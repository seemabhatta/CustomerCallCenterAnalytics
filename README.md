# 📞 Customer Call Center Analytics

A comprehensive **AI-powered system** for generating and analyzing call center transcripts with **Post-Call Intelligence Analytics**.  
Built for **mortgage servicing insights, risk assessment, and advisor performance metrics** using OpenAI's Responses API.  

Designed with **Clean Architecture** principles and a **Universal Server** that powers both **Fast CLI** and **REST API** interfaces.

---

## ⚡ Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start the universal server (CLI + API)
./start_services.sh

# Use instant CLI
python cli_fast.py demo
python cli_fast.py generate topic="PMI Removal" --store
python cli_fast.py stats
```

---

## 📚 Documentation

- **[COMMANDS.md](COMMANDS.md)** - Complete CLI commands reference with examples
- **[DEMO.md](DEMO.md)** - Comprehensive workflow demonstration script
- **API Documentation** - Interactive docs at [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🚀 Usage

### Resource-Based CLI (Current)
Structured commands by resource type:

```bash
# Transcript operations
python cli.py transcript create --topic "PMI Removal" --urgency high
python cli.py transcript list
python cli.py transcript get CALL_123ABC

# Analysis operations (core CRUD only)
python cli.py analysis create --transcript-id CALL_123ABC
python cli.py analysis list

# Insights operations (knowledge graph analytics)
python cli.py insights populate --analysis-id ANALYSIS_456DEF
python cli.py insights patterns --risk-threshold 0.7
python cli.py insights dashboard

# Knowledge graph queries
python cli.py insights query "MATCH (a:Analysis) RETURN count(a)"
python cli.py insights status

# System operations
python cli.py system health
python cli.py system metrics
```

### Fast CLI (Legacy)
Instant execution via pre-loaded server:

```bash
# Generate transcripts
python cli_fast.py generate topic="PMI Removal" customer_id="CUST_001" --store --show
python cli_fast.py generate --count 5 topic="Refinance" --store

# Search & view
python cli_fast.py list --detailed
python cli_fast.py search --text "payment"

# Analyze & report
python cli_fast.py analyze --transcript-id CALL_001
python cli_fast.py analysis-report --transcript-id CALL_001
python cli_fast.py risk-report --threshold 0.8

# Action plans
python cli_fast.py generate-action-plan --analysis-id ANALYSIS_001
python cli_fast.py approval-queue --status pending_supervisor
python cli_fast.py approve-plan --plan-id PLAN_001 --approver SUPERVISOR_001
```

### Web API
Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

```bash
curl http://localhost:8000/stats
curl -X POST http://localhost:8000/generate   -H "Content-Type: application/json"   -d '{"scenario":"PMI Removal","customer_id":"API_001"}'
```

### Traditional CLI
(Slower due to imports)

```bash
python cli.py generate topic="PMI Removal" --store
python cli.py list
```

---

## 📊 Features

### AI-Powered Generation
- Realistic conversations via OpenAI
- Mortgage-specific scenarios: PMI removal, payment disputes, refinancing
- Dynamic parameters: **sentiment, urgency, outcomes**

### Post-Call Intelligence
- Mortgage **risk assessment** (delinquency, churn, complaints)  
- **Advisor performance metrics** & coaching  
- **Compliance monitoring** & disclosure tracking  
- Multi-layer insights: **Borrower, Advisor, Supervisor, Leadership**  
- Risk-based **approval routing** & workflow tracking  
- AI-generated **action plans** (Borrower → Advisor → Supervisor → Leadership)

### Knowledge Graph Analytics
- **KuzuDB-powered** knowledge graph for pattern detection
- **Risk pattern discovery** across customer interactions
- **Similar case matching** for advisor guidance
- **Customer relationship mapping** and compliance tracking
- **Raw Cypher queries** for custom analytics
- **GDPR compliance** with data deletion and pruning capabilities

### Data Management
- SQLite storage (CRUD, search, export)  
- Structured analysis with quick-access reporting fields  
- Metrics on transcripts, analyses, and action plans  

### Multiple Interfaces
- **Fast CLI** (~1s execution)  
- **REST API** (<100ms response)  
- **Traditional CLI** (direct logic access)

---

## 🏗️ Architecture

### Core Components
- **Business Logic Layer** (`src/`) – pure Python  
- **Interface Layers** – CLI & API built on same logic  
- **Universal Server** (`server.py`) – preloaded, multi-interface  
- **Fast CLI Client** (`cli_fast.py`) – instant execution via HTTP  

### Pipeline Flow
```
Generate Calls → Store → Analyze → Store Analysis 
→ Generate Action Plans → Approval Routing → Reports
```

### Performance Innovation
- Traditional CLI: ~12s (import delays)  
- Fast CLI: ~1s (via pre-loaded server)  

---

## 🛠️ Advanced Usage

### Server Management
```bash
./start_services.sh     # Start server
python server.py        # Manual start
./stop_services.sh      # Force stop
```

### Custom Parameters
```bash
python cli_fast.py generate topic="Escrow Shortage" sentiment="hopeful" urgency="medium"
python cli_fast.py generate --count 10 topic="Payment Dispute" --store
```

### Action Plan Workflow
```bash
python cli_fast.py analyze --transcript-id CALL_001
python cli_fast.py generate-action-plan --analysis-id ANALYSIS_001
python cli_fast.py approval-queue --status pending_supervisor
python cli_fast.py approve-plan --plan-id PLAN_001 --approver SUPERVISOR_001
```

---

## 🔧 Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_PATH=data/call_center.db
CLI_SERVER_PORT=9999
API_SERVER_PORT=8000
```

### Custom Scenarios
Edit `src/tools.py` to modify:
- Available scenarios  
- Sentiment options  
- Call outcomes  

---

## 🧪 Testing

```bash
pytest                              # Run all tests
pytest tests/test_call_analyzer.py  # Post-call analysis tests
pytest tests/test_integration.py    # System integration tests
```

Performance check:
```bash
time python cli.py stats       # ~12s
time python cli_fast.py stats  # ~1s
```

---

## 📈 Performance

- **Startup**: ~17–20s (one-time)  
- **Fast CLI**: ~1s per command  
- **Traditional CLI**: ~12s  
- **API**: <100ms typical  
- **Memory**: ~80MB  

Scales easily to PostgreSQL for production workloads.

---

## 🔍 Troubleshooting

**Server won’t start**  
```bash
./server_stop.sh
python server.py
```

**CLI can’t connect**  
```bash
curl http://localhost:9999
curl http://localhost:8000
```

**Database reset**  
```bash
rm data/call_center.db
python cli_fast.py demo
```

**Port conflicts**  
Run `./cleanup.sh` (ports: CLI → 9999–9996, API → 8000–8003)

---

## 🤝 Contributing

Guidelines:
1. Business logic must stay **UI-independent**  
2. Interface layers remain **thin wrappers**  
3. Tests are **layered by domain**  
4. Prefer **dynamic parameters** over hard validation  

Principles:
- **Agentic AI approach** (trust LLMs, minimal constraints)  
- **Clean separation** (logic vs. interface)  
- **Performance-first** design  
- **Flexible models** via `**kwargs`  

---

## 📄 License
MIT License – see LICENSE file for details.

---

## 🔗 API Reference
Start the server and visit:  
👉 [http://localhost:8000/docs](http://localhost:8000/docs)
