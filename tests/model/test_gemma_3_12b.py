#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Gemma 3 12B model with multi-model manager
"""
import asyncio
import logging
from multi_model_manager import get_multi_model_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_gemma_3_12b():
    """Test Gemma 3 12B model"""
    manager = get_multi_model_manager()
    
    print("\n=== Testing Gemma 3 12B Model ===\n")
    
    # Check if model is downloaded
    print("1. Checking if Gemma 3 12B is downloaded...")
    status = manager.get_status()
    gemma_status = status['models'].get('gemma-3-12b', {})
    
    if gemma_status.get('downloaded'):
        print("✓ Model already downloaded")
    else:
        print("✗ Model not downloaded yet")
        print("Downloading Gemma 3 12B (this may take a while)...")
        success = await manager.download_model("gemma-3-12b")
        if success:
            print("✓ Download complete")
        else:
            print("✗ Download failed")
            return
    
    # Load the model
    print("\n2. Loading Gemma 3 12B...")
    success = await manager.switch_model("gemma-3-12b")
    if success:
        print("✓ Model loaded successfully")
        
        # Test generation
        print("\n3. Testing text generation...")
        prompts = [
            "What makes a good song?",
            "Explain the difference between major and minor scales in music.",
            "Write a haiku about coding."
        ]
        
        for i, prompt in enumerate(prompts, 1):
            print(f"\nPrompt {i}: {prompt}")
            try:
                response = await manager.generate_text(prompt, max_length=100)
                print(f"Response: {response}")
            except Exception as e:
                print(f"✗ Generation failed: {e}")
    else:
        print("✗ Failed to load model")
    
    # Get final status
    print("\n4. Final Status:")
    status = manager.get_status()
    gemma_info = status['models']['gemma-3-12b']
    print(f"  - Loaded: {gemma_info['loaded']}")
    print(f"  - Downloaded: {gemma_info['downloaded']}")
    if gemma_info['loaded'] and 'gpu_memory_mb' in gemma_info:
        print(f"  - GPU Memory: {gemma_info['gpu_memory_mb']:.2f} MB")

if __name__ == "__main__":
    asyncio.run(test_gemma_3_12b())