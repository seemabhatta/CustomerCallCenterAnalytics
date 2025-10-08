#!/bin/bash
# Start all 5 MCP app servers in separate terminals/processes
#
# Usage: ./start_all_apps.sh

echo "🚀 Starting all 5 MCP apps..."
echo ""

# Store PIDs for cleanup
declare -a PIDS

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all MCP servers..."
    for pid in "${PIDS[@]}"; do
        kill $pid 2>/dev/null
    done
    exit 0
}

trap cleanup EXIT INT TERM

# Start each server in background
echo "Starting Universal Analytics (port 8001)..."
python3 src/infrastructure/mcp/mcp_server.py > logs/mcp_universal.log 2>&1 &
PIDS+=($!)
sleep 2

echo "Starting Advisor Borrower Assistant (port 8002)..."
python3 src/infrastructure/mcp/apps/advisor_borrower_server.py > logs/mcp_advisor_borrower.log 2>&1 &
PIDS+=($!)
sleep 2

echo "Starting Advisor Performance Coach (port 8003)..."
python3 src/infrastructure/mcp/apps/advisor_performance_server.py > logs/mcp_advisor_performance.log 2>&1 &
PIDS+=($!)
sleep 2

echo "Starting Leadership Portfolio Manager (port 8004)..."
python3 src/infrastructure/mcp/apps/leadership_portfolio_server.py > logs/mcp_leadership_portfolio.log 2>&1 &
PIDS+=($!)
sleep 2

echo "Starting Leadership Strategy Advisor (port 8005)..."
python3 src/infrastructure/mcp/apps/leadership_strategy_server.py > logs/mcp_leadership_strategy.log 2>&1 &
PIDS+=($!)
sleep 2

echo ""
echo "✅ All 5 MCP apps started!"
echo ""
echo "📡 Endpoints:"
echo "  - Universal:              http://localhost:8001/mcp"
echo "  - Advisor Borrower:       http://localhost:8002/mcp"
echo "  - Advisor Performance:    http://localhost:8003/mcp"
echo "  - Leadership Portfolio:   http://localhost:8004/mcp"
echo "  - Leadership Strategy:    http://localhost:8005/mcp"
echo ""
echo "📝 Logs:"
echo "  - tail -f logs/mcp_universal.log"
echo "  - tail -f logs/mcp_advisor_borrower.log"
echo "  - tail -f logs/mcp_advisor_performance.log"
echo "  - tail -f logs/mcp_leadership_portfolio.log"
echo "  - tail -f logs/mcp_leadership_strategy.log"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for all background processes
wait
