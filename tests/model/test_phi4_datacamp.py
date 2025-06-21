#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test phi-4-multimodal following DataCamp tutorial example
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

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    model_path, 
    device_map="cuda", 
    torch_dtype="auto", 
    trust_remote_code=True,
    _attn_implementation='eager',  # Using eager instead of flash_attention_2
    cache_dir=cache_dir
).cuda()

print("Loading generation config...")
generation_config = GenerationConfig.from_pretrained(model_path, cache_dir=cache_dir)

def process_text_input(question):
    """Process text-only input following DataCamp example"""
    user_prompt = "<|user|>"
    assistant_prompt = "<|assistant|>"
    prompt_suffix = "<|end|>"
    
    # Format prompt exactly as in the example
    prompt = f'{user_prompt}{question}{prompt_suffix}{assistant_prompt}'
    
    # Use processor for text input
    inputs = processor(text=prompt, return_tensors='pt').to(model.device)
    
    # Generate response
    generate_ids = model.generate(**inputs, max_new_tokens=200, generation_config=generation_config)
    response = processor.batch_decode(generate_ids, skip_special_tokens=True)[0]
    
    # Clean response
    if assistant_prompt in response:
        response = response.split(assistant_prompt)[-1].strip()
    
    return response

# Test examples
print("\n" + "="*60)
print("Testing phi-4-multimodal with DataCamp format")
print("="*60)

test_questions = [
    "What makes a good song? Answer in one sentence.",
    "Analyze the mood of: 'don't you worry child'",
    "List three elements of great lyrics."
]

for i, question in enumerate(test_questions, 1):
    print(f"\nTest {i}: {question}")
    try:
        response = process_text_input(question)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*60)
print("Done!")