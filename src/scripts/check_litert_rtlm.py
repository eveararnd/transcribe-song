#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Check if ai_edge_litert supports RTLM format
"""
import ai_edge_litert

print("Checking ai_edge_litert for RTLM support...\n")

# Check available modules
print("Available modules in ai_edge_litert:")
for attr in dir(ai_edge_litert):
    if not attr.startswith('_'):
        print(f"  - {attr}")

# Check if there's a specific RTLM loader
if hasattr(ai_edge_litert, 'rtlm'):
    print("\nFound RTLM module!")
    for attr in dir(ai_edge_litert.rtlm):
        if not attr.startswith('_'):
            print(f"  - {attr}")

# Check interpreter module for RTLM support
print("\nChecking interpreter module:")
from ai_edge_litert import interpreter
for attr in dir(interpreter):
    if 'rtlm' in attr.lower() or 'runtime' in attr.lower():
        print(f"  - {attr}")

# Try to find version info
if hasattr(ai_edge_litert, '__version__'):
    print(f"\nai_edge_litert version: {ai_edge_litert.__version__}")