#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Debug test script for Gemma 3 12B-IT model
Includes comprehensive error checking and debugging information
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
import logging
import os
import sys
from pathlib import Path
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gemma_debug.log')
    ]
)

logger = logging.getLogger(__name__)

def check_environment():
    """Check the environment setup"""
    logger.info("=" * 60)
    logger.info("Environment Check")
    logger.info("=" * 60)
    
    # Check Python version
    logger.info(f"Python version: {sys.version}")
    
    # Check PyTorch version
    logger.info(f"PyTorch version: {torch.__version__}")
    
    # Check CUDA
    logger.info(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        logger.info(f"CUDA version: {torch.version.cuda}")
        logger.info(f"Number of GPUs: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            logger.info(f"GPU {i}: {torch.cuda.get_device_name(i)}")
            logger.info(f"GPU {i} Memory: {torch.cuda.get_device_properties(i).total_memory / 1e9:.2f} GB")
    
    # Check transformers version
    import transformers
    logger.info(f"Transformers version: {transformers.__version__}")
    
    # Check memory
    if torch.cuda.is_available():
        logger.info(f"Current GPU memory allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
        logger.info(f"Current GPU memory reserved: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

def find_model_path():
    """Find the Gemma model path"""
    possible_paths = [
        "./gemma-3-12b-it",
        "/home/davegornshtein/parakeet-tdt-deployment/gemma-3-12b-it",
        "/home/davegornshtein/parakeet-tdt-deployment/models/gemma-3-12b-it",
        "/home/davegornshtein/parakeet-tdt-deployment/models/gemma-3n-E4B",  # The old path
    ]
    
    for path in possible_paths:
        if Path(path).exists():
            logger.info(f"Found model at: {path}")
            # List files in the directory
            files = list(Path(path).iterdir())
            logger.info(f"Files in model directory: {[f.name for f in files[:10]]}")  # Show first 10 files
            return path
    
    logger.error(f"Model not found in any of these locations: {possible_paths}")
    return None

def test_tokenizer(model_path):
    """Test tokenizer loading separately"""
    logger.info("=" * 60)
    logger.info("Testing Tokenizer")
    logger.info("=" * 60)
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        logger.info("✓ Tokenizer loaded successfully")
        logger.info(f"Tokenizer class: {type(tokenizer).__name__}")
        logger.info(f"Vocab size: {tokenizer.vocab_size}")
        
        # Test encoding/decoding
        test_text = "Hello, this is a test."
        tokens = tokenizer.encode(test_text)
        decoded = tokenizer.decode(tokens)
        logger.info(f"Test encoding: '{test_text}' -> {tokens[:10]}... ({len(tokens)} tokens)")
        logger.info(f"Test decoding: {decoded}")
        
        return tokenizer
    except Exception as e:
        logger.error(f"✗ Failed to load tokenizer: {e}")
        traceback.print_exc()
        return None

def test_model_loading_methods(model_path, tokenizer):
    """Try different methods to load the model"""
    logger.info("=" * 60)
    logger.info("Testing Model Loading Methods")
    logger.info("=" * 60)
    
    # Method 1: Basic bfloat16 loading
    logger.info("\n--- Method 1: Basic bfloat16 ---")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,  # In case model needs custom code
        )
        logger.info("✓ Method 1 successful")
        test_generation(model, tokenizer, "Method 1")
        del model
        torch.cuda.empty_cache()
        return True
    except Exception as e:
        logger.error(f"✗ Method 1 failed: {e}")
        traceback.print_exc()
    
    # Method 2: With explicit config
    logger.info("\n--- Method 2: With low_cpu_mem_usage ---")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )
        logger.info("✓ Method 2 successful")
        test_generation(model, tokenizer, "Method 2")
        del model
        torch.cuda.empty_cache()
        return True
    except Exception as e:
        logger.error(f"✗ Method 2 failed: {e}")
        traceback.print_exc()
    
    # Method 3: With 8-bit quantization (if bfloat16 fails)
    logger.info("\n--- Method 3: With 8-bit quantization ---")
    try:
        quantization_config = BitsAndBytesConfig(
            load_in_8bit=True,
            bnb_8bit_compute_dtype=torch.bfloat16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True,
        )
        logger.info("✓ Method 3 successful")
        test_generation(model, tokenizer, "Method 3")
        del model
        torch.cuda.empty_cache()
        return True
    except Exception as e:
        logger.error(f"✗ Method 3 failed: {e}")
        traceback.print_exc()
    
    # Method 4: Load to CPU first, then move to GPU
    logger.info("\n--- Method 4: CPU first, then GPU ---")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            low_cpu_mem_usage=True,
            trust_remote_code=True,
        )
        model = model.to('cuda')
        logger.info("✓ Method 4 successful")
        test_generation(model, tokenizer, "Method 4")
        del model
        torch.cuda.empty_cache()
        return True
    except Exception as e:
        logger.error(f"✗ Method 4 failed: {e}")
        traceback.print_exc()
    
    return False

def test_generation(model, tokenizer, method_name):
    """Test text generation with the loaded model"""
    logger.info(f"\nTesting generation with {method_name}")
    
    try:
        # Simple prompt
        prompt = "The capital of France is"
        inputs = tokenizer.encode(prompt, return_tensors="pt")
        
        # Move to same device as model
        if hasattr(model, 'device'):
            inputs = inputs.to(model.device)
        else:
            inputs = inputs.to('cuda')
        
        logger.info(f"Input shape: {inputs.shape}")
        logger.info(f"Input device: {inputs.device}")
        
        # Generate with minimal settings
        with torch.no_grad():
            with torch.cuda.amp.autocast(dtype=torch.bfloat16):
                outputs = model.generate(
                    inputs,
                    max_new_tokens=20,
                    do_sample=False,  # Greedy for consistency
                    pad_token_id=tokenizer.eos_token_id,
                )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"Generated: {response}")
        
        # Check if generation is reasonable
        if len(response) > len(prompt):
            logger.info("✓ Generation successful")
        else:
            logger.warning("⚠ Generation might have issues")
            
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        traceback.print_exc()

def main():
    """Main test function"""
    logger.info("Starting Gemma 3 12B-IT Debug Test")
    logger.info("=" * 80)
    
    # Check environment
    check_environment()
    
    # Find model path
    model_path = find_model_path()
    if not model_path:
        return
    
    # Set memory optimization
    os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
    
    # Clear GPU cache
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()
    
    # Test tokenizer
    tokenizer = test_tokenizer(model_path)
    if not tokenizer:
        return
    
    # Test different loading methods
    success = test_model_loading_methods(model_path, tokenizer)
    
    if success:
        logger.info("\n" + "=" * 60)
        logger.info("✓ At least one method worked successfully!")
        logger.info("=" * 60)
    else:
        logger.info("\n" + "=" * 60)
        logger.error("✗ All methods failed. Check the log for details.")
        logger.info("=" * 60)
    
    # Final memory report
    if torch.cuda.is_available():
        logger.info(f"\nFinal GPU memory allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
        logger.info(f"Final GPU memory reserved: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
    finally:
        # Cleanup
        if torch.cuda.is_available():
            torch.cuda.empty_cache()