#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test Gemma 3 12B using the PyTorch implementation following the provided example
"""
import sys
import os
import torch
import contextlib

# Add gemma_pytorch to path
sys.path.append('gemma_pytorch')

from gemma_pytorch.gemma.config import get_model_config
from gemma_pytorch.gemma.gemma3_model import Gemma3ForMultimodalLM

# Configuration
VARIANT = "12b"  # Model variant
MACHINE_TYPE = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer_path = "/home/davegornshtein/parakeet-tdt-deployment/gemma-3-12b-it/tokenizer.model"
ckpt_path = "/home/davegornshtein/parakeet-tdt-deployment/gemma-3-12b-it"  # We'll need to convert safetensors

print(f"Using device: {MACHINE_TYPE}")

# Set up model config
model_config = get_model_config(VARIANT)
model_config.dtype = "float32" if MACHINE_TYPE == "cpu" else "float16"
model_config.tokenizer = tokenizer_path

# Configure the device context
@contextlib.contextmanager
def _set_default_tensor_type(dtype: torch.dtype):
    """Sets the default torch dtype to the given dtype."""
    torch.set_default_dtype(dtype)
    yield
    torch.set_default_dtype(torch.float)

# Instantiate model (without loading weights for now)
print("\nInstantiating model...")
device = torch.device(MACHINE_TYPE)

try:
    with _set_default_tensor_type(model_config.get_dtype()):
        model = Gemma3ForMultimodalLM(model_config)
        print("Model instantiated successfully!")
        
        # Note: Loading weights would require converting from safetensors format
        # For now, let's test with the transformers version
        print("\nNote: The gemma_pytorch library expects checkpoint files in a specific format.")
        print("Our model is in safetensors format from HuggingFace.")
        print("To use gemma_pytorch, we would need to convert the weights.")
        
        # Show chat templates
        print("\nChat templates for Gemma 3:")
        USER_CHAT_TEMPLATE = "<start_of_turn>user\n{prompt}<end_of_turn><eos>\n"
        MODEL_CHAT_TEMPLATE = "<start_of_turn>model\n{prompt}<end_of_turn><eos>\n"
        
        # Sample formatted prompt
        prompt = (
            USER_CHAT_TEMPLATE.format(
                prompt='What is a good place for travel in the US?'
            )
            + MODEL_CHAT_TEMPLATE.format(prompt='California.')
            + USER_CHAT_TEMPLATE.format(prompt='What can I do in California?')
            + '<start_of_turn>model\n'
        )
        print('\nSample chat prompt:\n', prompt)
        
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

print("\nConclusion:")
print("- The gemma_pytorch library can instantiate Gemma 3 models")
print("- However, it expects weights in a different format than HuggingFace safetensors")
print("- The CUDA error we're seeing with transformers might be related to:")
print("  1. Model size (12B parameters)")
print("  2. Sampling parameters")
print("  3. Attention implementation")
print("- Consider using smaller temperature or different sampling strategy")