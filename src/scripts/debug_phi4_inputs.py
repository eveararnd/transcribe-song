#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Debug phi-4-multimodal inputs
"""
import torch
from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig

# Load model and processor
model_path = "microsoft/Phi-4-multimodal-instruct"
cache_dir = "/home/davegornshtein/parakeet-tdt-deployment/models/phi-4-multimodal"

print("Loading processor...")
processor = AutoProcessor.from_pretrained(
    model_path, 
    trust_remote_code=True,
    cache_dir=cache_dir
)

# Test input formatting
user_prompt = "<|user|>"
assistant_prompt = "<|assistant|>"
prompt_suffix = "<|end|>"
question = "What makes a good song? Answer in one sentence."

prompt = f'{user_prompt}{question}{prompt_suffix}{assistant_prompt}'
print(f"\nPrompt: {prompt}")

# Process with processor
print("\nProcessing with processor...")
inputs = processor(text=prompt, return_tensors='pt')

print(f"\nInput keys: {list(inputs.keys())}")
for key, value in inputs.items():
    if hasattr(value, 'shape'):
        print(f"{key}: shape={value.shape}, dtype={value.dtype}")
    else:
        print(f"{key}: {value}")

# Try to understand what's happening
print("\nChecking specific values...")
if 'input_ids' in inputs:
    print(f"input_ids first 20 tokens: {inputs['input_ids'][0][:20].tolist()}")
    
if 'input_mode' in inputs:
    print(f"input_mode value: {inputs['input_mode']}")

# Check if processor has any special methods
print("\nProcessor methods:")
relevant_methods = [m for m in dir(processor) if not m.startswith('_') and 'process' in m.lower()]
for method in relevant_methods:
    print(f"  - {method}")

# Try loading generation config
print("\nLoading generation config...")
generation_config = GenerationConfig.from_pretrained(model_path, cache_dir=cache_dir)
print(f"Generation config: {generation_config}")

# Check if there are any special generation parameters
if hasattr(generation_config, 'num_logits_to_keep'):
    print(f"num_logits_to_keep: {generation_config.num_logits_to_keep}")
else:
    print("num_logits_to_keep not found in generation config")

# Set it manually if missing
generation_config.num_logits_to_keep = 1
print(f"\nUpdated generation config with num_logits_to_keep=1")