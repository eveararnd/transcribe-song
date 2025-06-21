#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test script for multi_model_manager with Gemma-3-12B support
"""
import asyncio
import logging
from src.models.multi_model_manager import MultiModelManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_multi_model_manager():
    """Test the multi-model manager with all models including Gemma"""
    
    # Initialize manager
    manager = MultiModelManager()
    
    # Test 1: Get initial status
    logger.info("=== Test 1: Initial Status ===")
    status = manager.get_status()
    logger.info(f"Current model: {status['current_model']}")
    logger.info(f"Device: {status['device']}")
    for model_name, model_info in status['models'].items():
        logger.info(f"{model_name}: downloaded={model_info['downloaded']}, loaded={model_info['loaded']}")
    
    # Test 2: Load Gemma-3-12B
    logger.info("\n=== Test 2: Loading Gemma-3-12B ===")
    try:
        success = await manager.load_model("gemma-3-12b")
        if success:
            logger.info("✓ Gemma-3-12B loaded successfully")
        else:
            logger.error("✗ Failed to load Gemma-3-12B")
            return
    except Exception as e:
        logger.error(f"✗ Exception loading Gemma-3-12B: {e}")
        return
    
    # Test 3: Generate text with Gemma
    logger.info("\n=== Test 3: Generating Text with Gemma ===")
    test_prompts = [
        "What is artificial intelligence?",
        "Write a Python function to calculate factorial",
        "Explain quantum computing in simple terms"
    ]
    
    for prompt in test_prompts:
        try:
            logger.info(f"\nPrompt: {prompt}")
            response = await manager.generate_text(prompt, max_length=100)
            logger.info(f"Response: {response[:200]}...")
        except Exception as e:
            logger.error(f"✗ Generation failed: {e}")
    
    # Test 4: Switch to Phi-4 multimodal
    logger.info("\n=== Test 4: Switching to Phi-4 Multimodal ===")
    try:
        success = await manager.switch_model("phi-4-multimodal")
        if success:
            logger.info("✓ Switched to Phi-4 multimodal")
            # Test generation
            response = await manager.generate_text("Describe the importance of music in human culture", max_length=100)
            logger.info(f"Phi-4 response: {response[:200]}...")
        else:
            logger.error("✗ Failed to switch to Phi-4 multimodal")
    except Exception as e:
        logger.error(f"✗ Exception switching models: {e}")
    
    # Test 5: Switch to Phi-4 reasoning
    logger.info("\n=== Test 5: Switching to Phi-4 Reasoning ===")
    try:
        success = await manager.switch_model("phi-4-reasoning")
        if success:
            logger.info("✓ Switched to Phi-4 reasoning")
            # Test generation
            response = await manager.generate_text("Solve: If x + 5 = 12, what is x?", max_length=100)
            logger.info(f"Phi-4 reasoning response: {response[:200]}...")
        else:
            logger.error("✗ Failed to switch to Phi-4 reasoning")
    except Exception as e:
        logger.error(f"✗ Exception switching models: {e}")
    
    # Test 6: Switch back to Gemma
    logger.info("\n=== Test 6: Switching back to Gemma ===")
    try:
        success = await manager.switch_model("gemma-3-12b")
        if success:
            logger.info("✓ Switched back to Gemma-3-12B")
        else:
            logger.error("✗ Failed to switch back to Gemma")
    except Exception as e:
        logger.error(f"✗ Exception switching back to Gemma: {e}")
    
    # Test 7: Test compatibility methods
    logger.info("\n=== Test 7: Testing Compatibility Methods ===")
    try:
        # Test analyze_lyrics
        test_lyrics = "Don't stop believin', hold on to that feelin'"
        analysis = await manager.analyze_lyrics(test_lyrics, "mood")
        logger.info(f"Lyrics mood analysis: {analysis['analysis'][:200]}...")
        
        # Test comparison
        comparison = await manager.compare_transcriptions(
            "Don't stop believing",
            "Don't stop believin'"
        )
        logger.info(f"Transcription comparison: {comparison['comparison'][:200]}...")
    except Exception as e:
        logger.error(f"✗ Compatibility method test failed: {e}")
    
    # Final status
    logger.info("\n=== Final Status ===")
    final_status = manager.get_status()
    logger.info(f"Current model: {final_status['current_model']}")
    for model_name, model_info in final_status['models'].items():
        logger.info(f"{model_name}: loaded={model_info['loaded']}")
        if model_info['loaded'] and 'gpu_memory_mb' in model_info:
            logger.info(f"  GPU memory: {model_info['gpu_memory_mb']:.1f} MB")

if __name__ == "__main__":
    # Check if we're in the venv
    import sys
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        logger.warning("Not running in virtual environment. Activating parakeet-env...")
        import subprocess
        venv_python = "/home/davegornshtein/parakeet-env/bin/python"
        subprocess.run([venv_python, __file__])
    else:
        asyncio.run(test_multi_model_manager())