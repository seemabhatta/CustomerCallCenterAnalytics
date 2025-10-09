# Intelligence Prompt Library

Complete catalog of GenAI prompts powering the control tower analytics system.

## Overview

The prompt library consists of **10 production prompts** totaling **23KB** of carefully crafted templates that transform raw data and forecasts into actionable business intelligence.

## Prompt Categories

### Core Intelligence Prompts

| Prompt | Size | Purpose | Used By |
|--------|------|---------|---------|
| `executive_briefing.txt` | 2.2KB | Daily leadership briefing combining multiple forecasts | `generate_executive_briefing()` |
| `churn_analysis.txt` | 2.4KB | Detailed churn risk intelligence with retention strategies | `analyze_churn_risk()` |
| `forecast_summary.txt` | 2.0KB | Natural language summaries of Prophet forecasts | Various forecast analyses |

### Operations Intelligence Prompts

| Prompt | Size | Purpose | Used By |
|--------|------|---------|---------|
| `operations_alerts.txt` | 2.0KB | Staffing alerts, SLA risks, coaching priorities | `analyze_operations()` |
| `coaching_recommendations.txt` | 2.9KB | Advisor performance analysis and coaching plans | Coaching endpoints |
| `staffing_optimization.txt` | 4.3KB | Workforce management and shift optimization | `get_workload_balance()` |

### Marketing Intelligence Prompts

| Prompt | Size | Purpose | Used By |
|--------|------|---------|---------|
| `campaign_recommendations.txt` | 3.7KB | Data-driven campaign generation with ROI projections | `get_campaign_recommendations()` |
| `message_optimizer.txt` | 3.6KB | Segment-specific message optimization | `optimize_campaign_message()` |

### Cross-Persona Prompts

| Prompt | Size | Purpose | Used By |
|--------|------|---------|---------|
| `insights/strategy/query_strategy.txt` | 1.8KB | Strategic routing for natural language queries | `ask()` endpoint |
| `insights/response/strategic_executive_response.txt` | 2.0KB | Executive response synthesis | `ask()` endpoint |

## Prompt Design Principles

All prompts follow these core principles:

### 1. **JSON Output Format**
Every prompt returns structured JSON for programmatic consumption:
```json
{
  "primary_output": "...",
  "supporting_data": {...},
  "confidence": "high|medium|low",
  "metadata": {...}
}
```

### 2. **Fail-Fast Error Handling**
No fallback logic or mock data. If data is insufficient:
```json
{
  "status": "insufficient_data",
  "message": "Clear explanation of what's missing",
  "minimum_requirements": "..."
}
```

### 3. **Quantified Recommendations**
Every recommendation includes:
- Dollar amounts ($)
- Percentages (%)
- Counts (#)
- Timelines (when)
- Expected impact (ROI)

### 4. **Action-Oriented**
Prompts generate specific actions, not generic advice:
- ❌ "Consider improving staffing"
- ✅ "Add 3 advisors from 2-5PM Tuesday to handle predicted 40% volume spike"

### 5. **Compliance-Aware**
Marketing and customer-facing prompts include:
- Regulatory checklist (TILA, RESPA, TCPA, Fair Housing)
- Brand voice consistency
- Approval workflows for sensitive content

## Prompt Variable Conventions

### Common Variables
- `{forecast}` - Prophet forecast output with predictions
- `{raw_data}` - Database query results for context
- `{date}` - Current date/timestamp
- `{forecast_type}` - Type of forecast (churn_risk, call_volume, etc.)

### Persona-Specific Variables
- **Leadership**: `{portfolio_metrics}`, `{risk_scores}`, `{dollar_impact}`
- **Operations**: `{advisor_metrics}`, `{queue_status}`, `{sla_performance}`
- **Marketing**: `{segments}`, `{campaign_data}`, `{customer_journey}`

## Integration with Intelligence Layer

### Request Flow

```
User Query
    ↓
Intelligence Service
    ↓
Hybrid Analyzer
    ↓
┌─────────────────┐     ┌─────────────────┐
│  Prophet        │  +  │  Prompt         │
│  Forecast       │     │  Template       │
└─────────────────┘     └─────────────────┘
    ↓                       ↓
    └────────────┬──────────┘
                 ↓
         Insight Generator
         (LLMClientV2)
                 ↓
         ┌──────────────┐
         │ JSON Response │
         └──────────────┘
                 ↓
         Cache + Return
```

### Caching Strategy

Prompts support intelligent caching:
- **TTL-based**: Insights cached with expiration (1-24 hours)
- **Persona-scoped**: Separate caches for Leadership, Operations, Marketing
- **Type-specific**: Cache key includes insight_type for granular invalidation

## Prompt Maintenance

### Adding New Prompts

1. Create prompt file in `/prompts/` directory
2. Follow JSON output format convention
3. Include confidence scoring
4. Add fail-fast error handling
5. Document in this file
6. Add integration tests

### Updating Existing Prompts

1. Test changes in dev environment
2. Validate JSON schema compatibility
3. Check impact on cached insights
4. Update version in prompt metadata
5. Clear relevant caches after deployment

## Testing Prompts

### Manual Testing
```bash
# Test via API endpoint
curl -X POST http://localhost:8000/api/v1/intelligence/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are our top operational risks?", "persona": "leadership"}'
```

### Automated Testing
See `tests/intelligence/test_prompt_integration.py` for examples

## Performance Metrics

Typical prompt response times (with GPT-4):
- **Simple prompts** (query_strategy): 1-2 seconds
- **Medium prompts** (executive_briefing): 3-5 seconds
- **Complex prompts** (campaign_recommendations): 5-8 seconds

Caching reduces response time to <100ms for cached insights.

## Roadmap

Future prompt additions:
- [ ] Compliance risk analysis
- [ ] Customer sentiment deep-dive
- [ ] Competitive intelligence
- [ ] Portfolio stress testing
- [ ] Agent performance benchmarking

## References

- Prompt engineering guide: `docs/prompt-engineering.md` (TBD)
- Intelligence architecture: `docs/intelligence-frontend.md`
- API documentation: `http://localhost:8000/docs`

---

Last updated: 2025-10-09
Prompt count: 10
Total size: 23KB
Coverage: 100% of GenAI endpoints
