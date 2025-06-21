#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Run scripts from the src directory with proper Python path setup
Usage: python run_script.py <script_path> [args...]
Example: python run_script.py src/scripts/initialize_database.py
"""
import sys
import os
import runpy

if len(sys.argv) < 2:
    print("Usage: python run_script.py <script_path> [args...]")
    print("Example: python run_script.py src/scripts/initialize_database.py")
    sys.exit(1)

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Get the script path
script_path = sys.argv[1]

# Remove the script runner from argv
sys.argv = [script_path] + sys.argv[2:]

# Run the script
try:
    runpy.run_path(script_path, run_name="__main__")
except Exception as e:
    print(f"Error running script: {e}")
    sys.exit(1)