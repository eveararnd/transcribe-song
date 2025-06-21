#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test phi-4-multimodal following exact DataCamp tutorial pattern
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

def clean_response(response, instruction_keywords):
    """Removes the prompt text dynamically based on instruction keywords."""
    for keyword in instruction_keywords:
        if response.lower().startswith(keyword.lower()):
            response = response[len(keyword):].strip()
    return response

def process_input(file, input_type, question):
    user_prompt = "<|user|>"
    assistant_prompt = "<|assistant|>"
    prompt_suffix = "<|end|>"
    
    if input_type == "Text":
        # Following exact pattern from DataCamp
        prompt = f'{user_prompt}{question} "{file}"{prompt_suffix}{assistant_prompt}'
        inputs = processor(text=prompt, return_tensors='pt').to(model.device)
    else:
        return "Invalid input type"
    
    # Generate exactly as in the example
    generate_ids = model.generate(**inputs, max_new_tokens=100, generation_config=generation_config)
    response = processor.batch_decode(generate_ids, skip_special_tokens=True)[0]
    return clean_response(response, [question])

# Test text generation
print("\n" + "="*60)
print("Testing phi-4-multimodal with exact DataCamp pattern")
print("="*60)

# Test case 1: Simple question (treating the question itself as "file" content)
question = "What makes a good song? Answer in one sentence"
file_content = ""  # Empty file content since we're asking a direct question
print(f"\nTest 1: {question}")
try:
    response = process_input(file_content, "Text", question)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test case 2: Grammar check example from DataCamp
def process_text_grammar(text):
    prompt = f'Check the grammar and provide corrections if needed for the following text: "{text}"'
    return process_input(text, "Text", prompt)

test_text = "This are a good songs"
print(f"\nTest 2: Grammar check for '{test_text}'")
try:
    response = process_text_grammar(test_text)
    print(f"Response: {response}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60)
print("Done!")