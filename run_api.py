#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Run the Music Analyzer API with proper Python path setup
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the API
from src.api.music_analyzer_api import app, API_CONFIG
import uvicorn

if __name__ == "__main__":
    print("Starting Music Analyzer API...")
    print(f"Access the API at http://{API_CONFIG['host']}:{API_CONFIG['port']}")
    
    uvicorn.run(
        app,
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=False,
        log_level="info"
    )