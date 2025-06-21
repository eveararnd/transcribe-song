#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test multi-model manager with flash_attention_2
"""
import asyncio
import logging
from multi_model_manager import get_multi_model_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_flash_attention():
    """Test models with flash_attention_2"""
    manager = get_multi_model_manager()
    
    print("\n=== Testing Multi-Model Manager with Flash Attention 2 ===\n")
    
    # Test phi-4-multimodal
    print("1. Testing phi-4-multimodal with flash_attention_2...")
    success = await manager.switch_model("phi-4-multimodal")
    if success:
        print("✓ Model loaded successfully")
        
        # Test generation
        try:
            response = await manager.generate_text("What makes a good song?", max_length=100)
            print(f"Response: {response}")
            print("✓ Generation successful with flash_attention_2")
        except Exception as e:
            print(f"✗ Generation failed: {e}")
    else:
        print("✗ Failed to load model")
    
    # Test phi-4-reasoning
    print("\n2. Testing phi-4-reasoning with flash_attention_2...")
    success = await manager.switch_model("phi-4-reasoning")
    if success:
        print("✓ Model loaded successfully")
        
        # Test generation
        try:
            response = await manager.generate_text("Explain why 2+2=4 step by step.", max_length=150)
            print(f"Response: {response}")
            print("✓ Generation successful with flash_attention_2")
        except Exception as e:
            print(f"✗ Generation failed: {e}")
    else:
        print("✗ Failed to load model")
    
    # Get status
    print("\n3. System Status:")
    status = manager.get_status()
    print(f"Current model: {status['current_model']}")
    print(f"Device: {status['device']}")
    for model_name, model_info in status['models'].items():
        print(f"\n{model_name}:")
        print(f"  - Loaded: {model_info['loaded']}")
        print(f"  - Downloaded: {model_info['downloaded']}")
        if model_info['loaded'] and 'gpu_memory_mb' in model_info:
            print(f"  - GPU Memory: {model_info['gpu_memory_mb']:.2f} MB")

if __name__ == "__main__":
    asyncio.run(test_flash_attention())