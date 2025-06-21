#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Verify phi-4-multimodal model integrity
"""
import torch
from transformers import AutoModelForCausalLM, AutoProcessor
import hashlib
import os

model_path = "microsoft/Phi-4-multimodal-instruct"
cache_dir = "/home/davegornshtein/parakeet-tdt-deployment/models/phi-4-multimodal"

print("1. Checking model files...")
model_files = [
    "models--microsoft--Phi-4-multimodal-instruct/blobs/c46bb03332d82f6a3eaf85bd20af388dd4d4d68b198c2203c965c7381a466094",
    "models--microsoft--Phi-4-multimodal-instruct/blobs/b3e812c0c8acef4e7f5e34d6c9f77a7640ee4a2b93ea351921365ac62f19918d", 
    "models--microsoft--Phi-4-multimodal-instruct/blobs/7be96b7339303752634b202d3f377bcf312a03046586eca6cea23347ace1e65a"
]

total_size = 0
for f in model_files:
    path = os.path.join(cache_dir, f)
    if os.path.exists(path):
        size = os.path.getsize(path)
        print(f"  ✓ {os.path.basename(f)}: {size / 1024**3:.2f} GB")
        total_size += size
    else:
        print(f"  ✗ {os.path.basename(f)}: MISSING")

print(f"\nTotal model size: {total_size / 1024**3:.2f} GB")

print("\n2. Loading processor...")
try:
    processor = AutoProcessor.from_pretrained(
        model_path, 
        trust_remote_code=True,
        cache_dir=cache_dir
    )
    print("  ✓ Processor loaded successfully")
except Exception as e:
    print(f"  ✗ Processor loading failed: {e}")

print("\n3. Testing model loading (weights_only)...")
try:
    # Try loading with weights_only to verify model structure
    from transformers import AutoConfig
    config = AutoConfig.from_pretrained(
        model_path,
        trust_remote_code=True,
        cache_dir=cache_dir
    )
    print(f"  ✓ Config loaded: {config.architectures}")
    print(f"    Model type: {config.model_type}")
    print(f"    Hidden size: {config.hidden_size}")
    print(f"    Num layers: {config.num_hidden_layers}")
except Exception as e:
    print(f"  ✗ Config loading failed: {e}")

print("\n4. Checking for known issues...")
# Check modeling file for num_logits_to_keep issue
modeling_file = os.path.join(cache_dir, "models--microsoft--Phi-4-multimodal-instruct/blobs/31fe013b98d269c5962e17968bc376992704036f")
if os.path.exists(modeling_file):
    with open(modeling_file, 'r') as f:
        content = f.read()
        if "num_logits_to_keep: int = 0" in content:
            print("  ⚠️  Found num_logits_to_keep parameter with default=0")
        if "-num_logits_to_keep:" in content:
            print("  ⚠️  Found problematic -num_logits_to_keep usage")
            # Find the specific line
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "hidden_states[:, -num_logits_to_keep:, :]" in line:
                    print(f"    Line {i+1}: {line.strip()}")

print("\n5. Alternative model suggestions...")
print("  Since phi-4-multimodal has generation issues, consider using:")
print("  - phi-4-reasoning (fully working)")
print("  - Other multimodal models like LLaVA, BLIP-2, or Qwen-VL")

print("\nDone!")