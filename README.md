# Customer Call Center Analytics

AI-powered call center transcript generation and analysis using OpenAI Agent SDK. Create realistic customer service conversations and get comprehensive insights with natural language interaction.

## ⚡ Quick Start

1. **Setup Environment**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure API key
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

2. **Run Interactive Mode**:
   ```bash
   python -m src
   ```

3. **Start Using**:
   ```
   > Generate some transcripts
   > Analyze recent calls
   > Create 3 calls about angry customers
   ```

## 🎯 Core Features

### Dynamic Transcript Generation
- **LLM suggests scenarios** - No hardcoded templates
- **Natural language requests** - "Generate calls about rate increases"
- **Unique variations** - Each transcript is different even for same scenario
- **Industry context** - Mortgage, insurance, banking conversations

### Intelligent Analysis
- **Customer psychology** - Intent, sentiment, urgency assessment
- **Compliance review** - Missing disclosures, regulatory risks
- **Quality metrics** - Empathy, professionalism, efficiency
- **Four-layer action plans** - Customer, Advisor, Supervisor, Leadership

### Natural Interface
- **Chat mode** - Just describe what you want
- **Smart routing** - LLM understands your intent
- **Contextual help** - Guides you through capabilities

## 🚀 Usage Examples

### Interactive Mode (Recommended)
```bash
$ python -m src

💬 Customer Call Center Analytics
> Generate some transcripts

🎯 Suggested Scenarios:
1. Elderly customer confused about escrow shortage
2. Hurricane victim needing immediate assistance
3. Young couple seeking loan modification
...

Your choice: 2
✅ Generated: CALL_20240105_143022
Analyze now? y

📊 Analysis Results:
- Customer Sentiment: Highly distressed, needs urgent help
- Compliance: Missing disaster relief disclosures  
- Action Plan: File insurance claim within 48 hours
...
```

### Direct Commands
```bash
# Generate transcripts
python -m src generate -n 5

# Analyze specific transcript
python -m src analyze CALL_123

# Search transcripts
python -m src search "payment issues"

# Show recent files
python -m src list

# System status
python -m src status
```

### Natural Language Examples
```
> Create 10 calls about customers upset about rate increases
> Search for compliance violations
> Analyze all transcripts for coaching opportunities
> Generate some calls about hurricane damage
> Show me recent analyses
```

## 🏗 Architecture

### Simple & Powerful
- **2 Core Agents**: Generator + Analyzer (with optional compliance specialist)
- **LLM-First Design**: AI handles understanding, not rule-based logic
- **JSON Storage**: Simple file-based persistence
- **Progressive Complexity**: Start simple, enhance as needed

### Agent Capabilities

**Generator Agent**:
- Suggests diverse scenarios on demand
- Creates realistic multi-turn conversations
- Adapts to any industry or situation
- Generates unique variations

**Analyzer Agent**:
- Comprehensive call analysis
- Customer psychology insights
- Compliance risk assessment
- Quality scoring and coaching
- Strategic action planning
- Smart handoffs to specialists when needed

## 📁 Project Structure

```
CustomerCallCenterAnalytics/
├── .env                # Your configuration
├── requirements.txt    # Dependencies
├── src/
│   ├── agents.py      # Core LLM agents
│   ├── cli.py         # Natural language interface
│   ├── storage.py     # JSON file storage
│   └── config.py      # Settings management
├── data/              # Generated transcripts & analysis
└── README.md
```

## ⚙️ Configuration

```bash
# .env file
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini              # Default model
# ENABLE_HANDOFFS=true                # Optional compliance specialist
# DATA_DIR=./data                     # Storage location
```

## 🔧 Advanced Usage

### Batch Operations
```
> Generate 20 transcripts: 10 about payments, 5 about escrow, 5 about complaints
> Analyze all recent transcripts for compliance risks
> Create action plans for high-priority issues
```

### Search & Filter
```
> Search for "frustrated" customers
> Find calls about "rate increases"
> Show transcripts from last week
```

### Analysis Deep-Dive
```
> Analyze CALL_123 for compliance issues
> Review coaching opportunities in recent calls
> Check quality metrics across all transcripts
```

## 🚀 Key Benefits

1. **Zero Learning Curve** - Just describe what you want
2. **Immediate Results** - Working system in 30 seconds
3. **Infinite Scenarios** - Not limited to predefined templates
4. **Rich Analysis** - Comprehensive insights with action plans
5. **Simple Architecture** - Easy to understand and extend

## 🔮 Extending the System

The design makes it easy to add new capabilities:

- **New Analysis Types**: Add specialized agents with handoffs
- **Different Industries**: Modify agent instructions
- **Enhanced Storage**: Swap JSON for database
- **Web Interface**: Add Flask/FastAPI layer
- **Real-time Processing**: Add streaming capabilities

## 📝 Example Output

### Generated Transcript
```
Advisor: Good morning, thank you for calling. How can I help you today?

Customer: Hi, I'm really stressed about this escrow shortage notice I got. I don't understand why my payment is going up by $300 a month!

Advisor: I completely understand your concern. Let me pull up your account and walk through this with you. Can you verify your loan number for me?

Customer: Sure, it's 1234567890. This is really putting a strain on our budget...
```

### Analysis Results
```
📊 Customer Analysis:
- Intent: Escrow shortage explanation and payment options
- Sentiment: Anxious but cooperative
- Urgency: High - financial strain indicated

⚖️ Compliance Review:  
- ✓ Account verification completed
- ⚠️ Missing: Escrow analysis explanation requirements
- ⚠️ Missing: Payment adjustment options disclosure

📋 Action Plans:
Customer: Review escrow analysis packet, choose payment plan
Advisor: Send detailed breakdown, follow up in 48 hours  
Supervisor: Review for hardship assistance eligibility
Leadership: Track escrow shortage trend - 15% increase this quarter
```

---

**Built with OpenAI Agent SDK - Leveraging LLM Intelligence Over Code Complexity** 🤖