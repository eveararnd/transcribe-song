#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Simple test for phi-4-multimodal
"""
import torch
from transformers import AutoModelForCausalLM, AutoProcessor

# Load model and processor
model_path = "microsoft/Phi-4-multimodal-instruct"
cache_dir = "/home/davegornshtein/parakeet-tdt-deployment/models/phi-4-multimodal"

print("Loading processor...")
processor = AutoProcessor.from_pretrained(
    model_path, 
    trust_remote_code=True,
    cache_dir=cache_dir
)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    model_path, 
    device_map="cuda", 
    torch_dtype="auto", 
    trust_remote_code=True,
    _attn_implementation='eager',
    cache_dir=cache_dir
).cuda()

# Format prompt
user_prompt = "<|user|>"
assistant_prompt = "<|assistant|>"
prompt_suffix = "<|end|>"
question = "What makes a good song? Answer in one sentence."

prompt = f'{user_prompt}{question}{prompt_suffix}{assistant_prompt}'
print(f"\nPrompt: {prompt}")

# Process input
inputs = processor(text=prompt, return_tensors='pt').to(model.device)

# Generate with explicit parameters
print("\nGenerating...")
with torch.no_grad():
    # Call generate with explicit num_logits_to_keep
    outputs = model.generate(
        **inputs,
        max_new_tokens=50,
        temperature=0.7,
        do_sample=True,
        pad_token_id=processor.tokenizer.pad_token_id,
        eos_token_id=processor.tokenizer.eos_token_id,
        # Try different approaches
        generation_config={"num_logits_to_keep": 1}  # Pass as dict
    )

response = processor.batch_decode(outputs, skip_special_tokens=True)[0]
print(f"\nResponse: {response}")

# Clean response
if assistant_prompt in response:
    response = response.split(assistant_prompt)[-1].strip()
    print(f"Cleaned: {response}")