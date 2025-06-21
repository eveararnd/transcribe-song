#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test all models in the multi-model manager
"""
import asyncio
import logging
from src.models.multi_model_manager import get_multi_model_manager
import torch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def test_all_models():
    """Test all three models"""
    manager = get_multi_model_manager()
    
    print("\n=== Testing All Models in Multi-Model Manager ===\n")
    
    # Get initial status
    status = manager.get_status()
    print("Available models:")
    for model_name in status['models']:
        print(f"  - {model_name}")
    
    # Test each model
    models_to_test = ["gemma-2b", "phi-4-multimodal", "phi-4-reasoning"]
    test_prompts = {
        "gemma-2b": "What makes music beautiful?",
        "phi-4-multimodal": "Describe the key elements of a good song.",
        "phi-4-reasoning": "Explain step by step how to compose a simple melody."
    }
    
    results = {}
    
    for model_name in models_to_test:
        print(f"\n{'='*60}")
        print(f"Testing {model_name}")
        print('='*60)
        
        # Clear CUDA cache before each model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        
        # Load the model
        print(f"\n1. Loading {model_name}...")
        try:
            success = await manager.switch_model(model_name)
            if success:
                print(f"✓ {model_name} loaded successfully")
                
                # Test generation
                print(f"\n2. Testing generation...")
                prompt = test_prompts[model_name]
                print(f"Prompt: {prompt}")
                
                try:
                    response = await manager.generate_text(prompt, max_length=100)
                    print(f"Response: {response}")
                    results[model_name] = {
                        "status": "success",
                        "response": response[:200] + "..." if len(response) > 200 else response
                    }
                except Exception as e:
                    print(f"✗ Generation failed: {e}")
                    results[model_name] = {
                        "status": "generation_failed",
                        "error": str(e)
                    }
                
                # Get memory usage
                status = manager.get_status()
                model_info = status['models'][model_name]
                if 'gpu_memory_mb' in model_info:
                    results[model_name]['gpu_memory_mb'] = model_info['gpu_memory_mb']
                
            else:
                print(f"✗ Failed to load {model_name}")
                results[model_name] = {"status": "load_failed"}
                
        except Exception as e:
            print(f"✗ Error with {model_name}: {e}")
            results[model_name] = {
                "status": "error",
                "error": str(e)
            }
        
        # Unload model after testing
        print(f"\n3. Unloading {model_name}...")
        await manager.unload_current_model()
        print(f"✓ {model_name} unloaded")
    
    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    for model_name, result in results.items():
        print(f"\n{model_name}:")
        print(f"  Status: {result['status']}")
        if 'gpu_memory_mb' in result:
            print(f"  GPU Memory: {result['gpu_memory_mb']:.2f} MB")
        if result['status'] == 'success':
            print(f"  Response preview: {result['response'][:100]}...")
        elif 'error' in result:
            print(f"  Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test_all_models())