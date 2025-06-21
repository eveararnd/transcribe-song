#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test the official example from phi-4-multimodal-fresh
"""
import os
import sys
import torch
from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig

# Change to the fresh clone directory
os.chdir('phi-4-multimodal-fresh')

model_path = './'

kwargs = {}
kwargs['torch_dtype'] = torch.bfloat16

print("Loading processor...")
processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
print(processor.tokenizer)

print("\nLoading model...")
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    trust_remote_code=True,
    torch_dtype='auto',
    _attn_implementation='eager',  # Using eager instead of flash_attention_2
).cuda()
print("model.config._attn_implementation:", model.config._attn_implementation)

print("\nLoading generation config...")
generation_config = GenerationConfig.from_pretrained(model_path, 'generation_config.json')

user_prompt = '<|user|>'
assistant_prompt = '<|assistant|>'
prompt_suffix = '<|end|>'

#################################################### text-only ####################################################
prompt = f'{user_prompt}what is the answer for 1+1? Explain it.{prompt_suffix}{assistant_prompt}'
print(f'\n>>> Prompt\n{prompt}')
inputs = processor(prompt, images=None, return_tensors='pt').to('cuda:0')

print("\nGenerating...")
try:
    generate_ids = model.generate(
        **inputs,
        max_new_tokens=100,
        generation_config=generation_config,
    )
    generate_ids = generate_ids[:, inputs['input_ids'].shape[1] :]
    response = processor.batch_decode(
        generate_ids, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    
    print(f'>>> Response\n{response}')
    print("\n✅ SUCCESS! The official example works!")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    
    # Check if it's the num_logits_to_keep error
    if "num_logits_to_keep" in str(e) or "bad operand type" in str(e):
        print("\n⚠️  This is the num_logits_to_keep bug we found!")
        print("The official example has the same issue when using eager attention.")
        print("Our patch fixes this problem.")