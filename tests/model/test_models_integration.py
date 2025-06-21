#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Integration test for all models in multi_model_manager
"""
import asyncio
import pytest
import logging
from src.models.multi_model_manager import MultiModelManager, get_multi_model_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_all_models():
    """Test loading and generating with all models"""
    manager = get_multi_model_manager()
    
    # Test each model
    models_to_test = ["gemma-3-12b", "phi-4-multimodal", "phi-4-reasoning"]
    test_prompts = {
        "gemma-3-12b": "What is the meaning of life?",
        "phi-4-multimodal": "Describe a beautiful sunset",
        "phi-4-reasoning": "If all roses are flowers and all flowers need water, do roses need water?"
    }
    
    for model_type in models_to_test:
        logger.info(f"\n=== Testing {model_type} ===")
        
        # Load model
        success = await manager.load_model(model_type)
        assert success, f"Failed to load {model_type}"
        
        # Check status
        status = manager.get_status()
        assert status["current_model"] == model_type
        assert status["models"][model_type]["loaded"] is True
        
        # Generate text
        prompt = test_prompts[model_type]
        response = await manager.generate_text(prompt, max_length=50)
        assert response, f"No response from {model_type}"
        assert len(response) > 0, f"Empty response from {model_type}"
        
        logger.info(f"✓ {model_type} test passed")
        logger.info(f"  Response preview: {response[:100]}...")

@pytest.mark.asyncio
async def test_model_switching():
    """Test switching between models"""
    manager = get_multi_model_manager()
    
    # Load Gemma first
    await manager.load_model("gemma-3-12b")
    assert manager.current_model == "gemma-3-12b"
    
    # Switch to Phi-4 multimodal
    await manager.switch_model("phi-4-multimodal")
    assert manager.current_model == "phi-4-multimodal"
    
    # Ensure Gemma is unloaded
    status = manager.get_status()
    assert status["models"]["gemma-3-12b"]["loaded"] is False
    assert status["models"]["phi-4-multimodal"]["loaded"] is True

@pytest.mark.asyncio
async def test_compatibility_methods():
    """Test compatibility methods for lyrics analysis"""
    manager = get_multi_model_manager()
    
    # Load Gemma for testing
    await manager.load_model("gemma-3-12b")
    
    # Test analyze_lyrics
    lyrics = "Imagine all the people living life in peace"
    result = await manager.analyze_lyrics(lyrics, "mood")
    assert "analysis" in result
    assert result["model"] == "gemma-3-12b"
    
    # Test compare_transcriptions
    comparison = await manager.compare_transcriptions(
        "Don't stop believing",
        "Don't stop believin'"
    )
    assert "comparison" in comparison

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_all_models())
    asyncio.run(test_model_switching())
    asyncio.run(test_compatibility_methods())
    print("\n✓ All integration tests passed!")