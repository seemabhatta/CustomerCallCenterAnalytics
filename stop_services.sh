#!/bin/bash

# Customer Call Center Analytics - Port & Process Cleanup
# Cleans up ports and processes for clean server restart

echo "🧹 Customer Call Center Analytics - Cleanup Script"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check what's using a port
check_port() {
    local port=$1
    local processes
    
    # Try different methods to find processes using the port
    if command -v lsof >/dev/null 2>&1; then
        processes=$(lsof -ti :$port 2>/dev/null)
    elif command -v fuser >/dev/null 2>&1; then
        processes=$(fuser $port/tcp 2>/dev/null | tr -d ' ')
    elif command -v ss >/dev/null 2>&1; then
        processes=$(ss -tlnp | grep ":$port " | sed 's/.*pid=\([0-9]*\).*/\1/' 2>/dev/null)
    elif command -v netstat >/dev/null 2>&1; then
        processes=$(netstat -tlnp 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1)
    fi
    
    echo "$processes"
}

# Function to kill processes using a port
kill_port() {
    local port=$1
    local processes=$(check_port $port)
    
    if [ -n "$processes" ]; then
        echo -e "🔍 Found processes using port $port: ${YELLOW}$processes${NC}"
        for pid in $processes; do
            if [ -n "$pid" ] && [ "$pid" != "0" ]; then
                echo -e "   Killing PID ${YELLOW}$pid${NC}..."
                kill -9 "$pid" 2>/dev/null || sudo kill -9 "$pid" 2>/dev/null
            fi
        done
        
        # Verify port is free
        sleep 1
        local remaining=$(check_port $port)
        if [ -n "$remaining" ]; then
            echo -e "   ${RED}⚠️  Some processes still running on port $port${NC}"
            if command -v fuser >/dev/null 2>&1; then
                echo "   Trying fuser..."
                fuser -k $port/tcp 2>/dev/null || sudo fuser -k $port/tcp 2>/dev/null
            fi
        else
            echo -e "   ${GREEN}✅ Port $port is now free${NC}"
        fi
    else
        echo -e "✅ Port $port is already free"
    fi
}

# Function to kill processes by name pattern
kill_by_pattern() {
    local pattern=$1
    local description=$2
    local pids=$(pgrep -f "$pattern" 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo -e "🔍 Found $description processes: ${YELLOW}$pids${NC}"
        for pid in $pids; do
            echo -e "   Killing PID ${YELLOW}$pid${NC}..."
            kill -9 "$pid" 2>/dev/null
        done
        echo -e "   ${GREEN}✅ $description processes killed${NC}"
    else
        echo -e "✅ No $description processes running"
    fi
}

# Show current status
echo "🔍 Current Port Status:"
echo "======================"

if command -v netstat >/dev/null 2>&1; then
    echo "Ports 8000 and 9999:"
    netstat -tlnp 2>/dev/null | grep -E ":(8000|9999) " | head -10 || echo "   No processes found on these ports"
elif command -v ss >/dev/null 2>&1; then
    echo "Ports 8000 and 9999:"
    ss -tlnp 2>/dev/null | grep -E ":(8000|9999) " | head -10 || echo "   No processes found on these ports"
else
    echo "   Port checking tools not available"
fi

echo ""
echo "Python server processes:"
ps aux | grep -E "(python.*server\.py|python.*cli_fast\.py)" | grep -v grep || echo "   No python server processes found"

echo ""
echo "🧹 Starting Cleanup:"
echo "==================="

# Clean up specific ports
kill_port 9999
kill_port 8000

echo ""

# Clean up specific process patterns
kill_by_pattern "python.*server\.py" "Python server"
kill_by_pattern "python.*cli_fast\.py" "Python cli_fast"
kill_by_pattern "uvicorn.*server:app" "Uvicorn server"

echo ""

# Clean up any server log files that might be locked
echo "🧹 Cleaning up log files:"
if [ -f "server.log" ]; then
    echo "   Removing server.log..."
    rm -f server.log
    echo -e "   ${GREEN}✅ server.log removed${NC}"
else
    echo "✅ No server.log to clean"
fi

echo ""

# Final status check
echo "🔍 Final Port Status:"
echo "===================="

for port in 8000 9999; do
    local remaining=$(check_port $port)
    if [ -n "$remaining" ]; then
        echo -e "   Port $port: ${RED}STILL IN USE${NC} (PIDs: $remaining)"
    else
        echo -e "   Port $port: ${GREEN}FREE${NC}"
    fi
done

echo ""

# Check for any remaining python processes
remaining_python=$(ps aux | grep -E "(python.*server\.py|python.*cli_fast\.py)" | grep -v grep)
if [ -n "$remaining_python" ]; then
    echo -e "${YELLOW}⚠️  Remaining Python processes:${NC}"
    echo "$remaining_python"
    echo ""
    echo "If processes persist, you may need to:"
    echo "   sudo fuser -k 9999/tcp"
    echo "   sudo fuser -k 8000/tcp"
else
    echo -e "${GREEN}✅ All Python server processes cleaned up${NC}"
fi

echo ""
echo -e "${GREEN}🎯 Cleanup Complete!${NC}"
echo ""
echo "You can now safely start the server with:"
echo "   python server.py"
echo "   # or"
echo "   ./start_services.sh"
echo ""