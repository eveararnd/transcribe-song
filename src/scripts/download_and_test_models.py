#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Download and test all three models:
- gemma-3n-E4B-it-litert-lm-preview
- Phi-4-multimodal-instruct
- Phi-4-reasoning-plus
"""
import asyncio
import logging
from src.models.multi_model_manager import get_multi_model_manager
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def download_all_models():
    """Download all models"""
    manager = get_multi_model_manager()
    
    print("="*70)
    print("📥 Downloading Models")
    print("="*70)
    
    # Check current status
    status = manager.get_status()
    print("\nCurrent status:")
    for model_type, info in status["models"].items():
        print(f"  {model_type}: Downloaded={info['downloaded']}, Loaded={info['loaded']}")
    
    # Download Phi-4 models
    models_to_download = ["phi-4-multimodal", "phi-4-reasoning"]
    
    for model_type in models_to_download:
        if not status["models"][model_type]["downloaded"]:
            print(f"\n📥 Downloading {model_type}...")
            success = await manager.download_model(model_type)
            if success:
                print(f"✓ {model_type} downloaded successfully")
            else:
                print(f"✗ Failed to download {model_type}")
    
    print("\n✅ Download phase complete")

async def test_all_models():
    """Test all three models"""
    manager = get_multi_model_manager()
    
    print("\n"+"="*70)
    print("🧪 Testing Models")
    print("="*70)
    
    test_prompts = {
        "lyrics_analysis": "Analyze these song lyrics: 'don't you worry child see heaven's got a plan for you'. What is the mood and theme?",
        "simple_test": "Complete this sentence: The music was",
        "multimodal_test": "Describe what makes a good song (text-only response)"
    }
    
    # Test each model
    for model_type in ["gemma-3n-E4B", "phi-4-multimodal", "phi-4-reasoning"]:
        print(f"\n{'='*50}")
        print(f"Testing: {model_type}")
        print('='*50)
        
        # Get model info
        model_config = manager.models_config[model_type]
        print(f"Model ID: {model_config['model_id']}")
        print(f"Type: {model_config['type']}")
        
        # Skip LiteRT model for now
        if model_config["type"] == "litert":
            print("⚠️  LiteRT model - requires special runtime, skipping inference test")
            continue
        
        # Try to load model
        print(f"\nLoading {model_type}...")
        try:
            success = await manager.load_model(model_type)
            if not success:
                print(f"✗ Failed to load {model_type}")
                continue
            print(f"✓ {model_type} loaded")
            
            # Test generation
            print("\nTesting generation:")
            for test_name, prompt in test_prompts.items():
                if test_name == "multimodal_test" and model_config["type"] != "multimodal":
                    continue
                
                print(f"\n  Test: {test_name}")
                print(f"  Prompt: {prompt[:50]}...")
                
                try:
                    response = await manager.generate_text(prompt, max_length=100)
                    print(f"  Response: {response[:150]}...")
                except Exception as e:
                    print(f"  Error: {e}")
            
            # Show memory usage
            status = manager.get_status()
            model_status = status["models"][model_type]
            if "gpu_memory_mb" in model_status:
                print(f"\n  GPU Memory: {model_status['gpu_memory_mb']:.1f} MB")
            
        except Exception as e:
            print(f"✗ Error with {model_type}: {e}")
        
        # Unload to free memory for next model
        print(f"\nUnloading {model_type}...")
        await manager.unload_current_model()
    
    print("\n✅ Testing complete")

async def main():
    """Main function"""
    print("🚀 Multi-Model System Test")
    print("Models: gemma-3n-E4B, phi-4-multimodal, phi-4-reasoning")
    
    # Download models
    await download_all_models()
    
    # Test models
    await test_all_models()
    
    # Final status
    manager = get_multi_model_manager()
    status = manager.get_status()
    
    print("\n" + "="*70)
    print("📊 Final Status")
    print("="*70)
    print(f"Device: {status['device']}")
    print(f"Current model: {status['current_model']}")
    print("\nModels:")
    for model_type, info in status["models"].items():
        print(f"  {model_type}:")
        print(f"    Downloaded: {info['downloaded']}")
        print(f"    Loaded: {info['loaded']}")

if __name__ == "__main__":
    asyncio.run(main())