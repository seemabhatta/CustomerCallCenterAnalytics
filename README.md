# Customer Call Center Analytics

An AI Co-Pilot system for Customer Call Center Analytics with multi-agent architecture. This project implements an offline MVP that generates realistic call transcripts and provides intelligent analysis through AI agents.

## 🎯 Vision

Building an **intelligent teammate** that co-executes with loan servicing advisors, providing real-time insights and coordinated actions while maintaining human oversight for compliance-heavy decisions. The system operates in three modes:

- **Plan Mode** - AI drafts action plans with predicted risks and outcomes
- **Execute Mode** - Approved actions are executed across systems with one-click approval  
- **Reflect Mode** - Post-call analysis generates coaching insights and lessons learned

## 🏗️ Architecture

### Multi-Agent System
- **Orchestrator Agent** - Coordinates analysis pipeline and maintains context
- **Transcript Generator** - Creates realistic call scenarios using AI
- **Database Layer** - TinyDB for unstructured data, SQLite for structured data
- **CLI Interface** - Command-line tools for interaction and testing

### Four Aligned Action Plans
Every call analysis produces coordinated plans for:

1. **🏠 Borrower Plan** - Next steps, disclosures, personalized offers
2. **👩‍💻 Advisor Plan** - Coaching points, performance insights, development areas
3. **👩‍💼 Supervisor Plan** - Escalations, approvals, risk assessment
4. **🧑‍💼 Leadership Plan** - KPI impact, trends, strategic actions

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- OpenAI API key

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd CustomerCallCenterAnalytics
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Install CLI**:
   ```bash
   pip install -e .
   ```

### Basic Usage

1. **Check system status**:
   ```bash
   python -m src.cli.main status
   ```

2. **Generate sample transcripts**:
   ```bash
   # Generate a hardship assistance call
   python -m src.cli.main transcript generate --scenario hardship
   
   # Generate multiple escrow inquiry calls
   python -m src.cli.main transcript generate --scenario escrow --count 3
   ```

3. **List and view transcripts**:
   ```bash
   # List all transcripts
   python -m src.cli.main transcript list
   
   # View transcript details
   python -m src.cli.main transcript show <transcript_id>
   
   # Search transcripts
   python -m src.cli.main transcript search "payment"
   ```

4. **Run AI analysis**:
   ```bash
   # Analyze a transcript with orchestrator agent
   python -m src.cli.main agent analyze <transcript_id>
   
   # View analysis results
   python -m src.cli.main agent show <transcript_id>
   
   # View specific sections
   python -m src.cli.main agent show <transcript_id> --section insights
   python -m src.cli.main agent show <transcript_id> --section actions
   ```

## 📋 Available Commands

### Transcript Management
```bash
transcript generate     # Generate AI transcripts
transcript list         # List stored transcripts  
transcript show         # Show transcript details
transcript search       # Search transcript content
```

### Agent Operations
```bash
agent list             # List available agents
agent analyze          # Run orchestrator analysis
agent show            # Show analysis results
```

### Database Operations
```bash
db stats              # Show database statistics
```

### System Commands
```bash
status                # System health check
scenarios             # List generation scenarios
```

## 🎭 Available Scenarios

The system can generate realistic transcripts for:

- **hardship** - Financial hardship assistance requests
- **escrow** - Escrow account inquiries and analysis
- **refinance** - Refinancing eligibility and options

Each scenario includes:
- Realistic customer-advisor dialogue
- Compliance language and disclosures
- Appropriate call flow and timing
- Varied customer emotions and advisor responses

## 🔍 Analysis Capabilities

The Orchestrator Agent provides:

### 📊 Insights Extraction
- Customer intent and sentiment analysis
- Key issues identification
- Resolution status tracking
- Risk factor detection

### 📋 Action Plans Generation
- **Borrower Actions**: Follow-ups, disclosures, personalized offers
- **Advisor Coaching**: Performance feedback and development areas
- **Supervisor Escalations**: Risk reviews and approval requirements
- **Leadership Insights**: KPI impact and strategic recommendations

### ⭐ Quality Scoring
- Compliance adherence percentage
- Empathy index measurement
- Efficiency scoring
- Customer satisfaction prediction
- First-call resolution tracking

### ⚖️ Compliance Checking
- Verification process validation
- Required disclosures tracking
- Privacy notice compliance
- Risk level assessment

## 📁 Project Structure

```
CustomerCallCenterAnalytics/
├── src/
│   ├── agents/           # AI agents (orchestrator, etc.)
│   ├── generators/       # Transcript generation
│   ├── storage/         # Database management
│   ├── cli/             # Command-line interface
│   ├── config/          # Configuration management
│   └── models/          # Data models
├── data/
│   ├── prompts/         # AI generation prompts
│   └── db/              # Database files
├── tests/               # Test suite
└── docs/                # Project documentation
```

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: Required for AI generation and analysis
- `OPENAI_MODEL`: Model to use (default: `gpt-4o-mini`)

### Database
- **TinyDB**: JSON-based storage for transcripts and unstructured data
- **SQLite**: Relational storage for agent sessions and structured data

## 🧪 Development

### Running Tests
```bash
pytest
```

### Adding New Scenarios
1. Create prompt file in `data/prompts/[scenario]_scenario.txt`
2. Add scenario-specific logic to `TranscriptGenerator`
3. Test with: `python -m src.cli.main transcript generate --scenario [scenario]`

### Extending Agents
1. Create new agent class in `src/agents/`
2. Register with orchestrator in `OrchestratorAgent`
3. Add CLI commands for interaction

## 🗺️ Roadmap

### ✅ Phase 1: Offline MVP (Current)
- AI transcript generation
- Orchestrator agent analysis
- Four aligned action plans
- CLI interface

### 🔄 Phase 2: Real-time Expansion (Planned)
- Live call processing
- Plan/Execute/Reflect modes
- Multi-agent specialization
- Integration APIs

### 🚀 Phase 3: Production Features (Future)
- CRM integrations
- Approval workflows
- Supervisor dashboards
- Predictive analytics

## 📈 Key Metrics Tracked

- **First Call Resolution (FCR)** - Issues resolved in single call
- **Customer Satisfaction (CSAT)** - Predicted satisfaction scores
- **Average Handle Time (AHT)** - Call duration efficiency
- **Compliance Adherence** - Required disclosures completion rate
- **Empathy Index** - Advisor emotional intelligence scoring

## 🤝 Contributing

This is a demonstration project following the vision outlined in `docs/01. vision.md`. 

Key principles:
- Test-driven development
- Multi-agent architecture
- Compliance-first design
- Human-in-the-loop workflows

## 📄 License

This project is for demonstration purposes. See project documentation for full details.

---

Built with the vision of creating an **operating system for mortgage servicing** that helps organizations serve customers better, train advisors smarter, and run operations more efficiently. 🎯
