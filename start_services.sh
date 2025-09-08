#!/bin/bash

# Customer Call Center Analytics - Service Starter
# Starts the universal server in background and provides helpful commands

echo "🚀 Customer Call Center Analytics - Universal Server"
echo "=================================================="
echo ""

# Run cleanup first
echo "🧹 Running cleanup to ensure clean start..."
./cleanup.sh
echo ""

# Check if server is already running (with timeout)
echo "🔍 Checking for existing server..."
if timeout 3 curl -s http://localhost:9999 >/dev/null 2>&1; then
    echo "✅ Server already running on ports 9999 (CLI) and 8000 (API)"
    echo ""
elif timeout 3 curl -s http://localhost:8000 >/dev/null 2>&1; then
    echo "✅ FastAPI server running on port 8000 (CLI backend may be on different port)"
    echo ""
else
    echo "🔧 Starting universal server..."
    
    # Start server in background
    nohup python server.py > server.log 2>&1 &
    SERVER_PID=$!
    
    echo "🎯 Server starting with PID: $SERVER_PID"
    echo "📝 Logs: tail -f server.log"
    echo ""
    
    # Wait for server to be ready (with shorter timeout)
    echo "⏳ Waiting for server to be ready..."
    
    # Check FastAPI first (more reliable)
    for i in {1..15}; do
        if timeout 2 curl -s http://localhost:8000 >/dev/null 2>&1; then
            echo "✅ FastAPI server ready on port 8000!"
            break
        fi
        sleep 1
        echo -n "."
    done
    
    echo ""
    
    # Check CLI backend (may be on different port)
    echo "🔍 Checking CLI backend..."
    for port in 9999 9998 9997 9996; do
        if timeout 2 curl -s http://localhost:$port >/dev/null 2>&1; then
            echo "✅ CLI backend ready on port $port!"
            if [ $port != 9999 ]; then
                echo "⚠️  Note: CLI backend is using port $port instead of 9999"
                echo "    You may need to update cli_fast.py if it doesn't work"
            fi
            break
        fi
    done
    
    echo ""
fi

# Display service information
echo "🌐 Available Services:"
echo "   • CLI Backend:     http://localhost:9999 (for cli_fast.py)"
echo "   • Web API:         http://localhost:8000"
echo "   • API Docs:        http://localhost:8000/docs"
echo "   • Alternative Docs: http://localhost:8000/redoc"
echo ""

echo "🚀 Quick Commands:"
echo "   # Fast CLI (instant execution)"
echo "   python cli_fast.py demo"
echo "   python cli_fast.py generate scenario=\"PMI Removal\" --store"
echo "   python cli_fast.py list"
echo "   python cli_fast.py stats"
echo ""
echo "   # Web API"
echo "   curl http://localhost:8000/"
echo "   curl http://localhost:8000/stats"
echo "   curl -X POST http://localhost:8000/generate -H 'Content-Type: application/json' -d '{\"scenario\":\"PMI Removal\"}'"
echo ""

echo "💡 Usage Tips:"
echo "   • cli_fast.py has NO import delay - instant execution!"
echo "   • cli.py still works but will be slower (11+ second delay)"
echo "   • Both CLI and API use the same pre-loaded business logic"
echo "   • Server handles all heavy imports once at startup"
echo ""

echo "🛑 To stop the server:"
echo "   pkill -f 'python server.py'"
echo ""