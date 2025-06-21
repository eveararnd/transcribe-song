#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Gemma 3 12B model from cloned directory
"""
import asyncio
import logging
from multi_model_manager import get_multi_model_manager
import torch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_gemma_cloned():
    """Test Gemma 3 12B model from cloned directory"""
    manager = get_multi_model_manager()
    
    print("\n=== Testing Gemma 3 12B Model from Cloned Directory ===\n")
    
    # Clear CUDA cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    # Load the model
    print("1. Loading Gemma 3 12B from cloned directory...")
    success = await manager.switch_model("gemma-3-12b")
    if success:
        print("✓ Model loaded successfully")
        
        # Test generation
        print("\n2. Testing text generation...")
        prompt = "What is music?"
        print(f"Prompt: {prompt}")
        
        try:
            response = await manager.generate_text(prompt, max_length=50)
            print(f"Response: {response}")
            print("✓ Generation successful")
        except Exception as e:
            print(f"✗ Generation failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("✗ Failed to load model")

if __name__ == "__main__":
    asyncio.run(test_gemma_cloned())