#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Multi-Model Manager
Tests loading, generation, search integration, and unloading for each model
"""
import asyncio
import logging
import sys
from typing import Dict
from src.models.multi_model_manager import get_multi_model_manager
from src.utils.lyrics_search_enhanced import get_enhanced_lyrics_manager
import time
import torch

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelManagerTester:
    def __init__(self):
        self.manager = get_multi_model_manager()
        self.lyrics_manager = get_enhanced_lyrics_manager()
        self.test_results = {}
    
    async def test_model(self, model_type: str) -> Dict:
        """Test a single model"""
        logger.info(f"\n{'='*60}")
        logger.info(f"Testing {model_type}")
        logger.info(f"{'='*60}")
        
        results = {
            "model": model_type,
            "load_test": False,
            "generate_test": False,
            "search_integration_test": False,
            "unload_test": False,
            "errors": []
        }
        
        # Test 1: Load Model
        logger.info(f"1. Loading {model_type}...")
        try:
            start_time = time.time()
            success = await self.manager.load_model(model_type)
            load_time = time.time() - start_time
            
            if success:
                results["load_test"] = True
                results["load_time"] = load_time
                logger.info(f"✓ Model loaded in {load_time:.2f}s")
                
                # Check memory usage
                if torch.cuda.is_available():
                    gpu_memory = torch.cuda.memory_allocated() / 1024**3
                    results["gpu_memory_gb"] = gpu_memory
                    logger.info(f"  GPU Memory: {gpu_memory:.2f} GB")
            else:
                logger.error(f"✗ Failed to load model")
                results["errors"].append("Model load failed")
        except Exception as e:
            logger.error(f"✗ Load error: {e}")
            results["errors"].append(f"Load error: {str(e)}")
        
        # Test 2: Generate Text (skip for LiteRT)
        if results["load_test"] and model_type != "gemma-3n-E4B":
            logger.info(f"\n2. Testing text generation...")
            test_prompts = [
                "What makes a good song? Answer in one sentence.",
                "Analyze the mood of: 'don't you worry child'",
                "List three elements of great lyrics."
            ]
            
            try:
                for i, prompt in enumerate(test_prompts, 1):
                    logger.info(f"  Test {i}: {prompt[:50]}...")
                    start_time = time.time()
                    response = await self.manager.generate_text(prompt, max_length=100)
                    gen_time = time.time() - start_time
                    
                    logger.info(f"  Response ({gen_time:.2f}s): {response[:100]}...")
                    results[f"prompt_{i}_time"] = gen_time
                
                results["generate_test"] = True
                logger.info("✓ Generation test passed")
            except Exception as e:
                logger.error(f"✗ Generation error: {e}")
                results["errors"].append(f"Generation error: {str(e)}")
        elif model_type == "gemma-3n-E4B":
            logger.info("\n2. Skipping generation test for LiteRT model")
            results["generate_test"] = "skipped"
        
        # Test 3: Search Integration (for supported models)
        if results["load_test"] and model_type != "gemma-3n-E4B":
            logger.info(f"\n3. Testing search integration...")
            try:
                # Test lyrics analysis with model
                test_lyrics = "don't you worry child see heaven's got a plan for you"
                
                # For multimodal/reasoning models, we can test analysis
                if hasattr(self.lyrics_manager, 'gemma_manager'):
                    # Replace gemma_manager with our multi-model manager's current model
                    original_gemma = self.lyrics_manager.gemma_manager
                    self.lyrics_manager.gemma_manager = self.manager
                    self.lyrics_manager.gemma_loaded = True
                    
                    # Test intelligent search
                    search_results = await self.lyrics_manager.search_lyrics_intelligent(
                        artist="Swedish House Mafia",
                        title="Don't You Worry Child",
                        transcribed_text=test_lyrics
                    )
                    
                    if search_results.get("results"):
                        logger.info(f"✓ Search integration successful")
                        logger.info(f"  Found results from: {list(search_results['results'].keys())}")
                        results["search_integration_test"] = True
                    else:
                        logger.warning("⚠ No search results found")
                        results["search_integration_test"] = False
                    
                    # Restore original
                    self.lyrics_manager.gemma_manager = original_gemma
                else:
                    logger.info("  Search integration not configured")
                    results["search_integration_test"] = "not_configured"
                    
            except Exception as e:
                logger.error(f"✗ Search integration error: {e}")
                results["errors"].append(f"Search integration error: {str(e)}")
        
        # Test 4: Unload Model
        logger.info(f"\n4. Unloading {model_type}...")
        try:
            await self.manager.unload_current_model()
            
            # Verify unloaded
            if self.manager.current_model is None:
                results["unload_test"] = True
                logger.info("✓ Model unloaded successfully")
                
                # Check memory freed
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    gpu_memory_after = torch.cuda.memory_allocated() / 1024**3
                    logger.info(f"  GPU Memory after: {gpu_memory_after:.2f} GB")
            else:
                logger.error("✗ Model still loaded after unload")
                results["errors"].append("Unload failed")
        except Exception as e:
            logger.error(f"✗ Unload error: {e}")
            results["errors"].append(f"Unload error: {str(e)}")
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"Summary for {model_type}:")
        logger.info(f"  Load: {'✓' if results['load_test'] else '✗'}")
        logger.info(f"  Generate: {'✓' if results['generate_test'] == True else ('⚠ skipped' if results['generate_test'] == 'skipped' else '✗')}")
        logger.info(f"  Search: {'✓' if results['search_integration_test'] == True else '✗'}")
        logger.info(f"  Unload: {'✓' if results['unload_test'] else '✗'}")
        if results["errors"]:
            logger.info(f"  Errors: {len(results['errors'])}")
        
        return results
    
    async def run_all_tests(self):
        """Run tests for all models"""
        logger.info("🧪 Multi-Model Manager Test Suite")
        logger.info("Testing: gemma-3n-E4B, phi-4-multimodal, phi-4-reasoning")
        
        # Check initial status
        status = self.manager.get_status()
        logger.info(f"\nInitial Status:")
        logger.info(f"  Device: {status['device']}")
        for model_type, info in status["models"].items():
            logger.info(f"  {model_type}: Downloaded={info['downloaded']}")
        
        # Test each model
        models_to_test = ["gemma-3n-E4B", "phi-4-multimodal", "phi-4-reasoning"]
        
        for model_type in models_to_test:
            if not status["models"][model_type]["downloaded"]:
                logger.warning(f"\n⚠️  {model_type} not downloaded, skipping tests")
                self.test_results[model_type] = {"skipped": True, "reason": "not_downloaded"}
                continue
            
            try:
                results = await self.test_model(model_type)
                self.test_results[model_type] = results
            except Exception as e:
                logger.error(f"\n❌ Critical error testing {model_type}: {e}")
                self.test_results[model_type] = {"error": str(e)}
            
            # Pause between models
            await asyncio.sleep(2)
        
        # Final report
        self.print_final_report()
    
    def print_final_report(self):
        """Print final test report"""
        logger.info("\n" + "="*60)
        logger.info("📊 FINAL TEST REPORT")
        logger.info("="*60)
        
        all_passed = True
        
        for model_type, results in self.test_results.items():
            logger.info(f"\n{model_type}:")
            
            if results.get("skipped"):
                logger.info(f"  ⚠️  SKIPPED: {results.get('reason', 'unknown')}")
                continue
            
            if results.get("error"):
                logger.info(f"  ❌ CRITICAL ERROR: {results['error']}")
                all_passed = False
                continue
            
            # Check test results
            load_pass = results.get("load_test", False)
            gen_pass = results.get("generate_test") in [True, "skipped"]
            search_pass = results.get("search_integration_test") in [True, "not_configured"]
            unload_pass = results.get("unload_test", False)
            
            model_passed = load_pass and gen_pass and search_pass and unload_pass
            
            status = "✅ PASSED" if model_passed else "❌ FAILED"
            logger.info(f"  {status}")
            
            logger.info(f"    Load: {'✓' if load_pass else '✗'}")
            if "load_time" in results:
                logger.info(f"      Time: {results['load_time']:.2f}s")
            if "gpu_memory_gb" in results:
                logger.info(f"      GPU: {results['gpu_memory_gb']:.2f} GB")
            
            logger.info(f"    Generate: {'✓' if results.get('generate_test') == True else ('⚠ skipped' if results.get('generate_test') == 'skipped' else '✗')}")
            logger.info(f"    Search: {'✓' if results.get('search_integration_test') == True else ('⚠ N/A' if results.get('search_integration_test') == 'not_configured' else '✗')}")
            logger.info(f"    Unload: {'✓' if unload_pass else '✗'}")
            
            if results.get("errors"):
                logger.info(f"    Errors:")
                for error in results["errors"]:
                    logger.info(f"      - {error}")
            
            if not model_passed:
                all_passed = False
        
        logger.info("\n" + "="*60)
        if all_passed:
            logger.info("✅ ALL TESTS PASSED!")
        else:
            logger.info("❌ SOME TESTS FAILED!")
        logger.info("="*60)
        
        return all_passed

async def main():
    """Main test runner"""
    tester = ModelManagerTester()
    
    try:
        await tester.run_all_tests()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ Test suite error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())