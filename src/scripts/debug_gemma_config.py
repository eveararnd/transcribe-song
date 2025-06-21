#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Debug Gemma config and architecture
"""
import sys
sys.path.append('gemma_pytorch')

from gemma_pytorch.gemma.config import get_model_config, Architecture

# Test different variants
variants = ["12b"]

for variant in variants:
    print(f"\n--- Testing variant: {variant} ---")
    config = get_model_config(variant)
    print(f"Architecture: {config.architecture}")
    print(f"Architecture type: {type(config.architecture)}")
    print(f"Architecture.GEMMA_3: {Architecture.GEMMA_3}")
    print(f"Is GEMMA_3: {config.architecture == Architecture.GEMMA_3}")
    print(f"Architecture value: {config.architecture.value if hasattr(config.architecture, 'value') else 'N/A'}")
    
print("\n--- All Architecture values ---")
for arch in Architecture:
    print(f"{arch.name}: {arch.value}")