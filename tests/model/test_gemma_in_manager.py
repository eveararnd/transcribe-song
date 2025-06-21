#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Quick test to verify Gemma works in multi_model_manager
"""
import asyncio
import logging
from src.models.multi_model_manager import MultiModelManager

logging.basicConfig(level=logging.INFO)

async def quick_test():
    manager = MultiModelManager()
    
    # Check status
    status = manager.get_status()
    print("\nAvailable models:")
    for model, info in status["models"].items():
        print(f"- {model}: downloaded={info['downloaded']}")
    
    # Load Gemma
    print("\nLoading Gemma-3-12B...")
    success = await manager.load_model("gemma-3-12b")
    if not success:
        print("Failed to load Gemma!")
        return
    
    print("Gemma loaded successfully!")
    
    # Test generation
    print("\nTesting generation...")
    response = await manager.generate_text("Hello, how are you today?", max_length=50)
    print(f"Response: {response}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(quick_test())