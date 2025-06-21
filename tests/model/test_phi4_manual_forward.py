#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test phi-4-multimodal with manual forward pass
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
    _attn_implementation='eager',
    cache_dir=cache_dir
).cuda()

# Test direct forward pass
user_prompt = "<|user|>"
assistant_prompt = "<|assistant|>"
prompt_suffix = "<|end|>"
question = "What makes a good song?"

prompt = f'{user_prompt}{question}{prompt_suffix}{assistant_prompt}'
print(f"\nPrompt: {prompt}")

# Process input
inputs = processor(text=prompt, return_tensors='pt').to(model.device)
print(f"Input keys: {list(inputs.keys())}")

# Try manual forward pass with num_logits_to_keep
print("\nTrying manual forward pass...")
try:
    with torch.no_grad():
        # Add num_logits_to_keep to inputs
        outputs = model(
            **inputs,
            num_logits_to_keep=1,  # Explicitly pass this parameter
            return_dict=True
        )
    print(f"Success! Output keys: {list(outputs.keys())}")
    print(f"Logits shape: {outputs.logits.shape}")
except Exception as e:
    print(f"Error in forward pass: {e}")
    import traceback
    traceback.print_exc()

# Now try generation with custom parameters
print("\nTrying generation with custom parameters...")
try:
    # Create a custom generation function
    with torch.no_grad():
        # Override model.forward temporarily
        original_forward = model.forward
        
        def forward_with_num_logits(*args, **kwargs):
            if 'num_logits_to_keep' not in kwargs:
                kwargs['num_logits_to_keep'] = 1
            return original_forward(*args, **kwargs)
        
        # Monkey patch the forward method
        model.forward = forward_with_num_logits
        
        # Now try generation
        generate_ids = model.generate(
            **inputs,
            max_new_tokens=50,
            temperature=0.7,
            do_sample=True,
            pad_token_id=processor.tokenizer.pad_token_id
        )
        
        # Restore original forward
        model.forward = original_forward
        
    response = processor.batch_decode(generate_ids, skip_special_tokens=True)[0]
    print(f"Success! Response: {response}")
    
    # Clean response
    if assistant_prompt in response:
        response = response.split(assistant_prompt)[-1].strip()
        print(f"Cleaned response: {response}")
        
except Exception as e:
    print(f"Error in generation: {e}")
    import traceback
    traceback.print_exc()

print("\nDone!")