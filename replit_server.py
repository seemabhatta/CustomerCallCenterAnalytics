#!/usr/bin/env python3
"""
Replit-specific server wrapper for Customer Call Center Analytics
Handles port conflicts and ensures proper Replit environment setup.
"""
import os
import sys
import time
import signal
import subprocess
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def cleanup_port_5000():
    """Attempt to clean up any processes using port 5000."""
    try:
        # Kill any existing processes that might be using port 5000
        subprocess.run(['pkill', '-f', 'port.*5000'], capture_output=True)
        subprocess.run(['pkill', '-f', 'uvicorn'], capture_output=True)
        time.sleep(1)
    except Exception:
        pass

def main():
    """Main entry point for Replit server."""
    print("🚀 Starting Replit-optimized Customer Call Center Analytics Server")
    print("=" * 60)
    
    # Clean up any existing processes
    cleanup_port_5000()
    
    # Set environment variables for FastAPI
    os.environ['HOST'] = '0.0.0.0'
    os.environ['PORT'] = '5000'
    
    # Import and run the main server after cleanup
    try:
        from server import main as server_main
        server_main()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()