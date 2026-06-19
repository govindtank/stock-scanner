#!/usr/bin/env python3
"""Simple launcher for the trading dashboard server."""
import os
import sys

# Ensure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8085))
    print(f"Starting DX Trading Dashboard on http://localhost:{port}")
    app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
