#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Debug phi-4-multimodal model generation
"""
import torch
from transformers import AutoProcessor, AutoModelForCausalLM, AutoConfig
import traceback

# Model paths
model_id = "microsoft/Phi-4-multimodal-instruct"
cache_dir = "/home/davegornshtein/parakeet-tdt-deployment/models/phi-4-multimodal"

print("Loading processor...")
processor = AutoProcessor.from_pretrained(
    model_id,
    trust_remote_code=True,
    cache_dir=cache_dir
)

print("Loading config...")
model_config = AutoConfig.from_pretrained(
    model_id,
    trust_remote_code=True,
    cache_dir=cache_dir
)

# Set attention implementation
model_config._attn_implementation = "eager"

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    config=model_config,
    torch_dtype=torch.float16,
    device_map="auto",
    trust_remote_code=True,
    cache_dir=cache_dir
)

print("\nModel loaded successfully!")
print(f"Model type: {type(model)}")

# Test generation
prompt = "What makes a good song? Answer in one sentence."
messages = [{"role": "user", "content": prompt}]

print("\nTesting generation...")

try:
    # Method 1: Using tokenizer directly
    print("\n1. Using tokenizer directly:")
    formatted_prompt = processor.tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    print(f"Formatted prompt: {formatted_prompt[:100]}...")
    
    inputs = processor.tokenizer(
        formatted_prompt,
        return_tensors="pt",
        truncation=True,
        max_length=2048
    )
    
    # Move to cuda
    inputs = {k: v.cuda() for k, v in inputs.items()}
    print(f"Input keys: {list(inputs.keys())}")
    print(f"Input shape: {inputs['input_ids'].shape}")
    
    # Try generate
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=50,
            temperature=0.7,
            do_sample=True,
            pad_token_id=processor.tokenizer.pad_token_id or processor.tokenizer.eos_token_id
        )
    
    response = processor.tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Response: {response}")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()

# Try Method 2: Using the processor with empty lists
try:
    print("\n\n2. Using processor with empty lists:")
    inputs = processor(
        text=formatted_prompt,
        images=[],  # Empty list instead of None
        audios=[],  # Empty list instead of None
        return_tensors="pt"
    )
    
    # Move tensors to device
    inputs = {k: v.cuda() if hasattr(v, 'cuda') else v for k, v in inputs.items()}
    print(f"Input keys: {list(inputs.keys())}")
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=50,
            temperature=0.7,
            do_sample=True,
            pad_token_id=processor.tokenizer.pad_token_id or processor.tokenizer.eos_token_id
        )
    
    response = processor.tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"Response: {response}")
    
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()

print("\nDone!")