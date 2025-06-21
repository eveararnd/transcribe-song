#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test phi-4-multimodal with a patched forward method
"""
import torch
from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig
import types

# Use the fresh clone
model_path = './phi-4-multimodal-fresh'

print("Loading processor...")
processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    trust_remote_code=True,
    torch_dtype='auto',
    _attn_implementation='eager',
).cuda()

print("Loading generation config...")
generation_config = GenerationConfig.from_pretrained(model_path, 'generation_config.json')

# Patch the forward method to handle None num_logits_to_keep
print("\nPatching model forward method...")
original_forward = model.forward

def patched_forward(self, *args, **kwargs):
    # If num_logits_to_keep is None, set it to 0 (which means keep all)
    if 'num_logits_to_keep' not in kwargs or kwargs['num_logits_to_keep'] is None:
        kwargs['num_logits_to_keep'] = 0
    return original_forward(*args, **kwargs)

# Bind the patched method
model.forward = types.MethodType(patched_forward, model)

user_prompt = '<|user|>'
assistant_prompt = '<|assistant|>'
prompt_suffix = '<|end|>'

# Test with patched model
prompt = f'{user_prompt}What makes a good song? Answer in one sentence.{prompt_suffix}{assistant_prompt}'
print(f'\n>>> Prompt\n{prompt}')

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
    
    print(f'>>> Response\n{response}')
    print("\n✅ SUCCESS! The model works with the patch!")
    
    # Test another prompt
    prompt = f'{user_prompt}what is the answer for 1+1? Explain it.{prompt_suffix}{assistant_prompt}'
    print(f'\n>>> Prompt 2\n{prompt}')
    inputs = processor(prompt, images=None, return_tensors='pt').to('cuda:0')
    
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
    import traceback
    traceback.print_exc()

print("\nDone!")