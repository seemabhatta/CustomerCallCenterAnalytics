# Customer Call Center Analytics CLI

A comprehensive command-line interface for the agentic transcript generation system.

## Quick Start

```bash
# Run a quick demo
python cli.py demo

# Generate a custom transcript
python cli.py generate scenario=loan_modification sentiment=worried customer_id=CUST_123 --show --store

# List all transcripts
python cli.py list

# Search transcripts
python cli.py search --customer CUST_123

# Show statistics
python cli.py stats
```

## Available Commands

### `generate` - Generate new transcripts
Generate transcripts with any custom parameters (completely agentic - no validation).

```bash
# Basic generation
python cli.py generate scenario=escrow_shortage sentiment=confused

# With storage and display
python cli.py generate scenario=payment_dispute sentiment=angry customer_id=CUST_456 --store --show

# Generate multiple transcripts
python cli.py generate topic=refinance --count 3 --store

# Any custom parameters work!
python cli.py generate anything=works completely=flexible no_validation=true
```

**Options:**
- `--count N` - Generate N transcripts
- `--store` - Store in database
- `--show` - Display generated transcript(s)

### `list` - List all transcripts
```bash
# Simple list
python cli.py list

# Detailed view with full conversation
python cli.py list --detailed
```

### `get` - Get specific transcript
```bash
# View transcript
python cli.py get CALL_ABC123

# Export to JSON
python cli.py get CALL_ABC123 --export
```

### `search` - Search transcripts
```bash
# Search by customer ID
python cli.py search --customer CUST_123

# Search by topic
python cli.py search --topic escrow_shortage  

# Search by text content
python cli.py search --text "payment dispute"

# Add --detailed for full conversation view
python cli.py search --customer CUST_123 --detailed
```

### `delete` - Delete transcripts
```bash
# Delete with confirmation
python cli.py delete CALL_ABC123

# Force delete without confirmation
python cli.py delete CALL_ABC123 --force
```

### `stats` - Show statistics
```bash
python cli.py stats
```

Shows:
- Total transcripts and messages
- Unique customers
- Top topics/scenarios
- Sentiment distribution
- Speaker statistics

### `export` - Export to JSON
```bash
# Export all transcripts
python cli.py export

# Custom filename
python cli.py export --output my_transcripts.json
```

### `demo` - Run quick demo
```bash
# Demo with storage
python cli.py demo

# Demo without storing to database
python cli.py demo --no-store
```

## Key Features

### ✅ Completely Agentic
- **No validation** - Pass any parameters you want
- **No hardcoded scenarios** - AI interprets your intent
- **Natural conversations** - AI generates realistic dialogues

### ✅ Flexible Parameters
```bash
# Mortgage scenarios
python cli.py generate scenario=refinance rate=6.5% goal=lower_payment

# Customer service scenarios
python cli.py generate type=billing_inquiry mood=frustrated resolution_needed=true

# Custom scenarios
python cli.py generate context="angry customer calling about late fee" priority=high
```

### ✅ Smart Output
- **Colored output** for easy reading
- **Pretty formatting** for conversations
- **Flexible attributes** shown dynamically
- **JSON export** capability

### ✅ Full Pipeline
- **Generation** → **Storage** → **Search** → **Analysis**
- **Multiple API fallbacks** (Responses → Chat Completions → Completions)
- **SQLite database** with full CRUD operations

## Examples

### Generate and Store a Complex Scenario
```bash
python cli.py generate \
  scenario=hardship_assistance \
  customer_situation="job loss, behind on payments" \
  sentiment=desperate \
  urgency=critical \
  customer_id=CUST_789 \
  advisor_id=ADV_123 \
  --store --show
```

### Batch Generate Test Data
```bash
# Generate 5 escrow shortage conversations
python cli.py generate scenario=escrow_shortage sentiment=confused --count 5 --store

# Generate varied scenarios
for scenario in payment_dispute refinance_inquiry hardship_assistance; do
  python cli.py generate scenario=$scenario customer_id=CUST_${scenario:0:3} --store
done
```

### Full Workflow Example
```bash
# 1. Generate some data
python cli.py demo

# 2. List everything
python cli.py list

# 3. Search for specific customers
python cli.py search --customer DEMO_001 --detailed

# 4. View statistics
python cli.py stats

# 5. Export everything
python cli.py export --output backup.json
```

## Tips

1. **Any parameters work** - The system is completely agentic, so pass any context you want
2. **Use --show** to see generated conversations immediately
3. **Use --detailed** with list/search to see full conversations
4. **Export regularly** to backup your data
5. **Check stats** to understand your data patterns

The CLI makes it easy to work with the simplified, agentic transcript generation system!