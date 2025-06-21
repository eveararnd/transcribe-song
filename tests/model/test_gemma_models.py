#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test available Gemma models and check if we can use standard transformers instead of LiteRT
"""
import os
import sys

# Add the deployment directory to Python path
sys.path.insert(0, '/home/davegornshtein/parakeet-tdt-deployment')

print("Checking available Gemma models...\n")

# Standard Gemma models that work with transformers
gemma_models = [
    "google/gemma-2b",
    "google/gemma-2b-it",  # Instruction-tuned version
    "google/gemma-7b",
    "google/gemma-7b-it",
    "google/gemma-2-2b",
    "google/gemma-2-2b-it",
    "google/gemma-2-9b",
    "google/gemma-2-9b-it"
]

print("Available Gemma models that work with standard transformers:")
for model in gemma_models:
    print(f"  - {model}")

print("\nRecommendation:")
print("For our use case (music analysis on A100), I recommend:")
print("1. google/gemma-2-2b-it - Latest Gemma 2 model, 2B parameters, instruction-tuned")
print("2. google/gemma-2b-it - Original Gemma, 2B parameters, instruction-tuned")
print("\nBoth are small enough to run efficiently while providing good quality.")

# Check if we want to test loading
print("\nTo integrate with multi_model_manager.py, we need to:")
print("1. Change gemma-3n-E4B type from 'litert' to 'causal-lm'")
print("2. Update model_id to a standard Gemma model")
print("3. The model will then work with transformers and flash_attention_2")