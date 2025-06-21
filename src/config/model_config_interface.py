#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Model Configuration Interface
Allows selecting between:
- gemma-3n-E4B-it-litert-lm-preview
- Phi-4-multimodal-instruct
- Phi-4-reasoning-plus
"""
import asyncio
from src.models.multi_model_manager import get_multi_model_manager
import json
from pathlib import Path

async def show_status():
    """Show current model status"""
    manager = get_multi_model_manager()
    status = manager.get_status()
    
    print("\n" + "="*70)
    print("📊 Model Status")
    print("="*70)
    print(f"Device: {status['device']}")
    print(f"Current loaded model: {status['current_model'] or 'None'}")
    print("\nAvailable models:")
    
    for i, (model_type, info) in enumerate(status["models"].items(), 1):
        print(f"\n{i}. {model_type}")
        print(f"   Model ID: {info['model_id']}")
        print(f"   Type: {info['type']}")
        print(f"   Downloaded: {'✓' if info['downloaded'] else '✗'}")
        print(f"   Loaded: {'✓' if info['loaded'] else '✗'}")
        if info.get('gpu_memory_mb'):
            print(f"   GPU Memory: {info['gpu_memory_mb']:.1f} MB")

async def select_model():
    """Interactive model selection"""
    manager = get_multi_model_manager()
    
    while True:
        await show_status()
        
        print("\n" + "="*70)
        print("🎮 Model Control")
        print("="*70)
        print("1. Load gemma-3n-E4B")
        print("2. Load phi-4-multimodal")
        print("3. Load phi-4-reasoning")
        print("4. Unload current model")
        print("5. Test current model")
        print("6. Save configuration")
        print("0. Exit")
        
        choice = input("\nSelect option (0-6): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            print("\n⚠️  Note: gemma-3n-E4B is a LiteRT model and requires special runtime")
            print("Full inference is not implemented yet")
            await manager.load_model("gemma-3n-E4B")
        elif choice == "2":
            print("\nLoading Phi-4-multimodal...")
            success = await manager.load_model("phi-4-multimodal")
            if success:
                print("✓ Phi-4-multimodal loaded")
            else:
                print("✗ Failed to load Phi-4-multimodal")
        elif choice == "3":
            print("\nLoading Phi-4-reasoning...")
            success = await manager.load_model("phi-4-reasoning")
            if success:
                print("✓ Phi-4-reasoning loaded")
            else:
                print("✗ Failed to load Phi-4-reasoning")
        elif choice == "4":
            await manager.unload_current_model()
            print("✓ Model unloaded")
        elif choice == "5":
            if manager.current_model:
                print(f"\nTesting {manager.current_model}...")
                try:
                    response = await manager.generate_text(
                        "What makes a good song? Answer in one sentence.",
                        max_length=50
                    )
                    print(f"Response: {response}")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print("No model loaded")
        elif choice == "6":
            # Save current configuration
            config = {
                "default_model": manager.current_model,
                "models": {
                    model_type: {
                        "enabled": info["loaded"],
                        "path": info["local_path"]
                    }
                    for model_type, info in manager.get_status()["models"].items()
                }
            }
            config_path = Path("model_config.json")
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"✓ Configuration saved to {config_path}")

async def main():
    """Main function"""
    print("🤖 Music Analyzer Model Configuration")
    print("Models: gemma-3n-E4B, phi-4-multimodal, phi-4-reasoning")
    
    await select_model()
    
    print("\n👋 Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())