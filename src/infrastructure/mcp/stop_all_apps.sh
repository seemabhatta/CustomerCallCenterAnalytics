#!/bin/bash
# Stop all running MCP app servers
#
# Usage: ./stop_all_apps.sh

echo "🛑 Stopping all MCP servers..."

# Kill by port
for port in 8001 8002 8003 8004 8005; do
    pid=$(lsof -ti:$port)
    if [ ! -z "$pid" ]; then
        echo "  Stopping server on port $port (PID: $pid)"
        kill $pid 2>/dev/null
    fi
done

sleep 2

# Verify all stopped
echo ""
echo "📊 Status check:"
for port in 8001 8002 8003 8004 8005; do
    pid=$(lsof -ti:$port)
    if [ -z "$pid" ]; then
        echo "  ✅ Port $port: stopped"
    else
        echo "  ❌ Port $port: still running (PID: $pid)"
    fi
done

echo ""
echo "Done!"
