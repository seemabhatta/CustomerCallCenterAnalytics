#!/bin/bash

echo "🔄 Testing Granular Workflow Extraction via Direct API Call"
echo "=========================================================="
echo ""

echo "📡 Calling extract-all endpoint (this may take 60+ seconds)..."
echo "⏰ Started at: $(date)"
echo ""

curl -X POST http://localhost:8000/api/v1/workflows/extract-all \
  -H "Content-Type: application/json" \
  -d '{"plan_id": "PLAN_ANALYSIS_CALL_B"}' \
  -w "\n⏱️  Total time: %{time_total} seconds\n" \
  2>/dev/null | head -n 50

echo ""
echo "✅ Extraction completed at: $(date)"
echo ""
echo "To verify results, run:"
echo "  curl http://localhost:8000/api/v1/workflows/plan/PLAN_ANALYSIS_CALL_B | head -n 20"