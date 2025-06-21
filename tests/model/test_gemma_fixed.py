#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test script for Gemma 3 12B-IT model with proper bfloat16 configuration
Based on the recommended approach for A100 GPUs
"""
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import logging
import os
from pathlib import Path

# Configure logging for better insight into the process
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_gemma_12b_local():
    """
    Loads and runs the Gemma 3 12B-IT model from a local directory
    on an A100 GPU, using bfloat16 for numerical stability.
    """
    # --- 1. Define Model Path ---
    # Check multiple possible locations for the model
    possible_paths = [
        "./gemma-3-12b-it",
        "/home/davegornshtein/parakeet-tdt-deployment/gemma-3-12b-it",
        "/home/davegornshtein/parakeet-tdt-deployment/models/gemma-3-12b-it"
    ]
    
    model_path = None
    for path in possible_paths:
        if Path(path).exists():
            model_path = path
            break
    
    if not model_path:
        logging.error(f"Model not found in any of these locations: {possible_paths}")
        return
    
    logging.info(f"Using model path: {model_path}")

    # --- 2. Load the Tokenizer ---
    # The tokenizer is responsible for converting text to token IDs and back.
    # `from_pretrained` with a local path reads all necessary tokenizer files.
    try:
        logging.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        logging.info("Tokenizer loaded successfully.")
    except Exception as e:
        logging.error(f"Failed to load tokenizer: {e}")
        return

    # --- 3. Load the Model ---
    # This is the core of the solution. The parameters here are critical.
    try:
        logging.info("Loading model with bfloat16 and device_map='auto'...")
        # `torch.bfloat16` is essential for stability on A100 GPUs.
        # `device_map="auto"` automatically distributes the model across available GPUs.
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
        )
        logging.info("Model loaded successfully.")
        logging.info(f"Model memory footprint: {model.get_memory_footprint() / 1e9:.2f} GB")
    except Exception as e:
        logging.error(f"Failed to load model: {e}")
        return

    # --- 4. Prepare the Prompt using the Correct Chat Template ---
    # Instruction-tuned models require a specific format for conversational prompts.
    # `apply_chat_template` handles this formatting automatically.
    chat = [
        {"role": "user", "content": "Explain what artificial intelligence is in simple terms."}
    ]
    
    try:
        prompt = tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=True)
        logging.info(f"Formatted prompt: {prompt[:100]}...")  # Show first 100 chars
    except Exception as e:
        logging.warning(f"Chat template not available, using fallback: {e}")
        # Fallback for models without chat template
        prompt = "User: Explain what artificial intelligence is in simple terms.\n\nAssistant:"
    
    # Tokenize the formatted prompt
    inputs = tokenizer.encode(prompt, add_special_tokens=False, return_tensors="pt")
    inputs = inputs.to(model.device)  # Ensure inputs are on the same device as the model
    logging.info(f"Input shape: {inputs.shape}")

    # --- 5. Generate Text ---
    # `model.generate` performs the inference.
    try:
        logging.info("Generating response...")
        with torch.cuda.amp.autocast(dtype=torch.bfloat16):  # Ensure bfloat16 context
            outputs = model.generate(
                input_ids=inputs,
                max_new_tokens=256,  # Start with a smaller limit for testing
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,  # Prevent warnings
                eos_token_id=tokenizer.eos_token_id,
            )
        logging.info("Response generated.")
        logging.info(f"Output shape: {outputs.shape}")
    except Exception as e:
        logging.error(f"Error during text generation: {e}")
        return

    # --- 6. Decode and Print the Output ---
    # Decode the generated token IDs back to a human-readable string.
    response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    # The output includes the original prompt, so we can print just the generated part.
    if prompt in response_text:
        generated_part = response_text[len(prompt):]
    else:
        # Sometimes the decoded text might not exactly match due to tokenization
        generated_part = response_text
    
    print("\n--- Model Response ---")
    print(generated_part.strip())
    print("----------------------\n")
    
    # --- 7. Test with another prompt ---
    logging.info("Testing with a coding prompt...")
    chat2 = [
        {"role": "user", "content": "Write a Python function to calculate the factorial of a number."}
    ]
    
    try:
        prompt2 = tokenizer.apply_chat_template(chat2, tokenize=False, add_generation_prompt=True)
    except:
        prompt2 = "User: Write a Python function to calculate the factorial of a number.\n\nAssistant:"
    
    inputs2 = tokenizer.encode(prompt2, add_special_tokens=False, return_tensors="pt").to(model.device)
    
    try:
        with torch.cuda.amp.autocast(dtype=torch.bfloat16):
            outputs2 = model.generate(
                input_ids=inputs2,
                max_new_tokens=256,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        response_text2 = tokenizer.decode(outputs2[0], skip_special_tokens=True)
        if prompt2 in response_text2:
            generated_part2 = response_text2[len(prompt2):]
        else:
            generated_part2 = response_text2
        
        print("\n--- Second Test Response ---")
        print(generated_part2.strip())
        print("---------------------------\n")
    except Exception as e:
        logging.error(f"Error in second test: {e}")

if __name__ == "__main__":
    # Check CUDA availability
    if not torch.cuda.is_available():
        logging.error("CUDA is not available. This script requires a GPU.")
    else:
        logging.info(f"CUDA available. Using {torch.cuda.device_count()} GPU(s).")
        logging.info(f"GPU Name: {torch.cuda.get_device_name(0)}")
        logging.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        
        # Set environment variables for better memory management
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
        
        # Run the test
        run_gemma_12b_local()