#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Direct test of phi-4-multimodal model to understand input requirements
"""
import torch
from transformers import AutoProcessor, AutoModelForCausalLM, AutoConfig
from pathlib import Path

# Model paths
model_id = "microsoft/Phi-4-multimodal-instruct"
cache_dir = "/home/davegornshtein/parakeet-tdt-deployment/models/phi-4-multimodal"

print("Loading processor...")
processor = AutoProcessor.from_pretrained(
    model_id,
    trust_remote_code=True,
    cache_dir=cache_dir
)

print("\nProcessor info:")
print(f"- Processor type: {type(processor)}")
print(f"- Has tokenizer: {hasattr(processor, 'tokenizer')}")
print(f"- Tokenizer type: {type(processor.tokenizer) if hasattr(processor, 'tokenizer') else 'N/A'}")

# Test different input methods
prompt = "What makes a good song? Answer in one sentence."

print("\n\nTesting input methods:")

# Method 1: Direct text
try:
    print("\n1. Direct text with processor:")
    inputs = processor(text=prompt, return_tensors="pt")
    print(f"   Success! Keys: {list(inputs.keys())}")
except Exception as e:
    print(f"   Failed: {e}")

# Method 2: Using messages format
try:
    print("\n2. Messages format:")
    messages = [{"role": "user", "content": prompt}]
    # Check if processor has chat template
    if hasattr(processor, 'tokenizer') and hasattr(processor.tokenizer, 'apply_chat_template'):
        formatted = processor.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        print(f"   Chat template applied: {formatted[:100]}...")
        inputs = processor.tokenizer(formatted, return_tensors="pt")
        print(f"   Success! Keys: {list(inputs.keys())}")
    else:
        print("   No chat template available")
except Exception as e:
    print(f"   Failed: {e}")

# Method 3: Check processor's expected inputs
print("\n3. Processor attributes:")
for attr in dir(processor):
    if not attr.startswith('_') and 'process' in attr.lower():
        print(f"   - {attr}")

# Method 4: Try with images=None explicitly
try:
    print("\n4. With explicit None for images/audio:")
    inputs = processor(text=prompt, images=None, audios=None, return_tensors="pt")
    print(f"   Success! Keys: {list(inputs.keys())}")
except Exception as e:
    print(f"   Failed: {e}")

print("\nDone!")