#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test phi-4-multimodal with fresh clone using their sample code pattern
"""
import torch
from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig

# Use the fresh clone
model_path = './phi-4-multimodal-fresh'

print("Loading processor...")
processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    trust_remote_code=True,
    torch_dtype='auto',
    _attn_implementation='eager',  # Using eager instead of flash_attention_2
).cuda()

print("Loading generation config...")
generation_config = GenerationConfig.from_pretrained(model_path, 'generation_config.json')

user_prompt = '<|user|>'
assistant_prompt = '<|assistant|>'
prompt_suffix = '<|end|>'

# Test 1: Simple text-only prompt (following their example exactly)
prompt = f'{user_prompt}What makes a good song? Answer in one sentence.{prompt_suffix}{assistant_prompt}'
print(f'\n>>> Prompt\n{prompt}')

# IMPORTANT: Pass images=None explicitly as in their example
inputs = processor(prompt, images=None, return_tensors='pt').to('cuda:0')

print(f"\nInput keys: {list(inputs.keys())}")

try:
    generate_ids = model.generate(
        **inputs,
        max_new_tokens=100,
        generation_config=generation_config,
    )
    generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
    response = processor.batch_decode(
        generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    
    print(f'>>> Response\n{response}')
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Another example
prompt = f'{user_prompt}what is the answer for 1+1? Explain it.{prompt_suffix}{assistant_prompt}'
print(f'\n>>> Prompt 2\n{prompt}')
inputs = processor(prompt, images=None, return_tensors='pt').to('cuda:0')

try:
    generate_ids = model.generate(
        **inputs,
        max_new_tokens=100,
        generation_config=generation_config,
    )
    generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
    response = processor.batch_decode(
        generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    
    print(f'>>> Response 2\n{response}')
except Exception as e:
    print(f"Error: {e}")

print("\nDone!")