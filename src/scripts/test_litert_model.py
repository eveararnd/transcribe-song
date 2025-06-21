#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test loading Gemma LiteRT model
"""
import sys
sys.path.insert(0, '/home/davegornshtein/parakeet-tdt-deployment')

from gemma_litert_manager import GemmaLiteRTManager

manager = GemmaLiteRTManager()

print("Testing Gemma LiteRT model loading...\n")

try:
    manager.load_model()
    print("✓ Model loaded successfully!")
    
    # Get model info
    info = manager.get_model_info()
    print(f"\nModel info:")
    print(f"  Status: {info['status']}")
    print(f"  Model size: {info['model_size_mb']:.2f} MB")
    if 'input_details' in info:
        print(f"  Input details: {info['input_details']}")
    if 'output_details' in info:
        print(f"  Output details: {info['output_details']}")
        
except Exception as e:
    print(f"✗ Failed to load model: {e}")
    import traceback
    traceback.print_exc()