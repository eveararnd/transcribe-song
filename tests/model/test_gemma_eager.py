#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Gemma 3 12B model with eager attention
"""
import asyncio
import logging
from multi_model_manager import get_multi_model_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_gemma_eager():
    """Test Gemma 3 12B model with eager attention"""
    manager = get_multi_model_manager()
    
    print("\n=== Testing Gemma 3 12B Model with Eager Attention ===\n")
    
    # First unload any current model
    print("1. Unloading current model...")
    await manager.unload_current_model()
    print("✓ Current model unloaded")
    
    # Load Gemma with eager attention
    print("\n2. Loading Gemma 3 12B with eager attention...")
    success = await manager.switch_model("gemma-3-12b")
    if success:
        print("✓ Model loaded successfully")
        
        # Test generation
        print("\n3. Testing text generation...")
        prompts = [
            "What makes a good song? Answer in one sentence.",
            "List three musical instruments.",
            "Complete this sentence: Music is"
        ]
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\nPrompt {i}: {prompt}")
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
    asyncio.run(test_gemma_eager())