#!/bin/bash
# Options Breakout Tracker V2 - Quick Start Script

cd "$(dirname "$0")/.."

echo "=============================================="
echo "  OPTIONS BREAKOUT TRACKER V2"
echo "  WebSocket Real-time Edition"
echo "=============================================="
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated"
else
    echo "Warning: No venv found. Using system Python."
fi

# Install dependencies if needed
echo ""
echo "Checking dependencies..."
pip install -q pyyaml aiohttp upstox-python-sdk 2>/dev/null

# Check for credentials
if [ ! -f "upstox_credentials.txt" ]; then
    echo ""
    echo "ERROR: upstox_credentials.txt not found!"
    echo "Please run: python upstox_token_generator.py"
    exit 1
fi

echo ""
echo "Starting tracker..."
echo "Dashboard will open at: http://localhost:8765"
echo ""

python v2/main.py "$@"
