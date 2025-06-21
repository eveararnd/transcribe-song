#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test only phi-4-multimodal model
"""
import asyncio
import logging
from test_model_manager import ModelManagerTester

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Test only phi-4-multimodal"""
    tester = ModelManagerTester()
    
    # Get initial status
    status = tester.manager.get_status()
    logger.info("Testing phi-4-multimodal only")
    logger.info(f"Device: {status['device']}")
    
    # Test phi-4-multimodal
    if status["models"]["phi-4-multimodal"]["downloaded"]:
        results = await tester.test_model("phi-4-multimodal")
        
        # Print results
        logger.info("\n" + "="*60)
        logger.info("Test Results:")
        logger.info(f"  Load: {'✓' if results.get('load_test') else '✗'}")
        logger.info(f"  Generate: {'✓' if results.get('generate_test') else '✗'}")
        logger.info(f"  Search Integration: {'✓' if results.get('search_integration_test') else '✗'}")
        logger.info(f"  Unload: {'✓' if results.get('unload_test') else '✗'}")
        
        if results.get("errors"):
            logger.info("\nErrors:")
            for error in results["errors"]:
                logger.info(f"  - {error}")
    else:
        logger.error("phi-4-multimodal not downloaded")

if __name__ == "__main__":
    asyncio.run(main())