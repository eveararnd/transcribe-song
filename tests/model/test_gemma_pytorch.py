#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Gemma 3 12B using the PyTorch implementation
"""
import sys
import os
import torch
import contextlib

# Add gemma_pytorch to path
sys.path.append('gemma_pytorch')

from gemma_pytorch.gemma.config import get_model_config
from gemma_pytorch.gemma.gemma3_model import Gemma3ForMultimodalLM
from transformers import AutoTokenizer

# Configuration
VARIANT = "12b"  # Model variant for Gemma 3 12B
MACHINE_TYPE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_PATH = "/home/davegornshtein/parakeet-tdt-deployment/gemma-3-12b-it"

print(f"Using device: {MACHINE_TYPE}")
print(f"Model path: {MODEL_PATH}")

# Load tokenizer
print("\nLoading tokenizer...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)

# Set up model config
print("Setting up model config...")
model_config = get_model_config(VARIANT)
model_config.dtype = "float32" if MACHINE_TYPE == "cpu" else "float16"
model_config.tokenizer = os.path.join(MODEL_PATH, "tokenizer.model")

# Configure device context
@contextlib.contextmanager
def _set_default_tensor_type(dtype: torch.dtype):
    """Sets the default torch dtype to the given dtype."""
    torch.set_default_dtype(dtype)
    yield
    torch.set_default_dtype(torch.float)

# Load model
print("\nLoading model...")
device = torch.device(MACHINE_TYPE)

try:
    with _set_default_tensor_type(model_config.get_dtype()):
        model = Gemma3ForMultimodalLM(model_config)
        
        # Load weights from safetensors files
        print("Loading model weights...")
        # For now, we'll use transformers to load since we have safetensors files
        from transformers import AutoModelForCausalLM
        
        # Load using transformers first to get the weights
        hf_model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float16 if MACHINE_TYPE == "cuda" else torch.float32,
            device_map="auto" if MACHINE_TYPE == "cuda" else None,
            trust_remote_code=True,
            _attn_implementation='eager'  # Use eager for compatibility
        )
        
        # Transfer weights to gemma_pytorch model
        # Note: This may require mapping between different weight names
        print("Model loaded via transformers. Testing generation...")
        
        # Test with transformers model first
        prompt = "What is music?"
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = hf_model.generate(
                **inputs,
                max_new_tokens=50,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        print(f"\nPrompt: {prompt}")
        print(f"Response: {response}")
        
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

# Chat templates for future use
USER_CHAT_TEMPLATE = "<start_of_turn>user\n{prompt}<end_of_turn><eos>\n"
MODEL_CHAT_TEMPLATE = "<start_of_turn>model\n{prompt}<end_of_turn><eos>\n"

print("\nChat templates configured for future use:")
print(f"User template: {USER_CHAT_TEMPLATE}")
print(f"Model template: {MODEL_CHAT_TEMPLATE}")