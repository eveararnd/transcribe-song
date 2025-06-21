#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Gemma 2 2B model
"""
import asyncio
import logging
from multi_model_manager import get_multi_model_manager
import torch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_gemma_2b():
    """Test Gemma 2 2B model"""
    manager = get_multi_model_manager()
    
    print("\n=== Testing Gemma 2 2B Model ===\n")
    
    # Clear CUDA cache
    print("0. Clearing CUDA cache...")
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    # First unload any current model
    print("\n1. Unloading current model...")
    await manager.unload_current_model()
    print("✓ Current model unloaded")
    
    # Download if needed
    print("\n2. Checking if Gemma 2 2B is downloaded...")
    status = manager.get_status()
    gemma_status = status['models'].get('gemma-2b', {})
    
    if not gemma_status.get('downloaded'):
        print("Downloading Gemma 2 2B...")
        success = await manager.download_model("gemma-2b")
        if success:
            print("✓ Download complete")
        else:
            print("✗ Download failed")
            return
    else:
        print("✓ Model already downloaded")
    
    # Load the model
    print("\n3. Loading Gemma 2 2B...")
    success = await manager.switch_model("gemma-2b")
    if success:
        print("✓ Model loaded successfully")
        
        # Test generation
        print("\n4. Testing text generation...")
        prompts = [
            "What is music?",
            "Name a musical instrument.",
            "Hello, how are you?"
        ]
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\nPrompt {i}: {prompt}")
            try:
                response = await manager.generate_text(prompt, max_length=30)
                print(f"Response: {response}")
                print("✓ Generation successful")
            except Exception as e:
                print(f"✗ Generation failed: {e}")
                # Don't print full traceback for each prompt
    else:
        print("✗ Failed to load model")
    
    # Get final status
    print("\n5. Final Status:")
    status = manager.get_status()
    gemma_info = status['models']['gemma-2b']
    print(f"  - Loaded: {gemma_info['loaded']}")
    print(f"  - Downloaded: {gemma_info['downloaded']}")
    if gemma_info['loaded'] and 'gpu_memory_mb' in gemma_info:
        print(f"  - GPU Memory: {gemma_info['gpu_memory_mb']:.2f} MB")

if __name__ == "__main__":
    asyncio.run(test_gemma_2b())