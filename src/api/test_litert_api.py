#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test ai_edge_litert API
"""
import ai_edge_litert as litert

print("ai_edge_litert attributes:")
for attr in dir(litert):
    if not attr.startswith('_'):
        print(f"  - {attr}")

# Check if it has submodules
if hasattr(litert, 'interpreter'):
    print("\nlitert.interpreter attributes:")
    for attr in dir(litert.interpreter):
        if not attr.startswith('_'):
            print(f"  - {attr}")