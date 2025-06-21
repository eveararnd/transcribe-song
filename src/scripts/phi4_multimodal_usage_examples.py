# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Phi-4-multimodal-instruct Usage Examples

This file contains code examples for using Microsoft's Phi-4-multimodal-instruct model
for text generation with various input modalities (text, image, audio).

Requirements:
- transformers>=4.48.2
- torch>=2.6.0
- pillow
- soundfile
- scipy
- accelerate
"""

import torch
from transformers import AutoModelForCausalLM, AutoProcessor, GenerationConfig
from PIL import Image
import soundfile as sf
import numpy as np

# Example 1: Basic Text-Only Generation
def text_only_example():
    """
    Basic example of using Phi-4-multimodal-instruct for text generation.
    """
    # Load model and processor
    model_id = "microsoft/Phi-4-multimodal-instruct"
    
    processor = AutoProcessor.from_pretrained(
        model_id,
        trust_remote_code=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cuda",
        torch_dtype="auto",
        trust_remote_code=True,
        attn_implementation='flash_attention_2',  # Requires flash-attn package
    )
    
    # Define chat format
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
    
    # Apply chat template
    prompt = processor.tokenizer.apply_chat_template(
        messages, 
        tokenize=False, 
        add_generation_prompt=True
    )
    
    # Prepare inputs
    inputs = processor(prompt, return_tensors="pt").to("cuda")
    
    # Generate response
    generation_args = {
        "max_new_tokens": 500,
        "temperature": 0.7,
        "do_sample": True,
        "top_p": 0.95,
    }
    
    generate_ids = model.generate(
        **inputs,
        eos_token_id=processor.tokenizer.eos_token_id,
        **generation_args
    )
    
    # Remove input tokens
    generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
    response = processor.batch_decode(
        generate_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]
    
    print("Response:", response)
    return response


# Example 2: Image + Text Generation (Visual Question Answering)
def image_text_example():
    """
    Example of using Phi-4-multimodal-instruct for visual question answering.
    """
    model_id = "microsoft/Phi-4-multimodal-instruct"
    
    processor = AutoProcessor.from_pretrained(
        model_id,
        trust_remote_code=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cuda",
        torch_dtype="auto",
        trust_remote_code=True,
        attn_implementation='flash_attention_2',
    )
    
    # Load an image
    image_path = "path/to/your/image.jpg"
    image = Image.open(image_path).convert('RGB')
    
    # Define the prompt with image placeholder
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "<|image_1|>\nWhat can you see in this image? Describe it in detail."}
    ]
    
    prompt = processor.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Process inputs with image
    inputs = processor(
        text=prompt,
        images=[image],
        return_tensors="pt"
    ).to("cuda")
    
    # Generate response
    generation_args = {
        "max_new_tokens": 1000,
        "temperature": 0.7,
        "do_sample": True,
    }
    
    generate_ids = model.generate(
        **inputs,
        eos_token_id=processor.tokenizer.eos_token_id,
        **generation_args
    )
    
    # Decode response
    generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
    response = processor.batch_decode(
        generate_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]
    
    print("Image Description:", response)
    return response


# Example 3: Audio + Text Generation (Speech Recognition/Translation)
def audio_text_example():
    """
    Example of using Phi-4-multimodal-instruct for audio processing tasks.
    """
    model_id = "microsoft/Phi-4-multimodal-instruct"
    
    processor = AutoProcessor.from_pretrained(
        model_id,
        trust_remote_code=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cuda",
        torch_dtype="auto",
        trust_remote_code=True,
        attn_implementation='flash_attention_2',
    )
    
    # Load audio file
    audio_path = "path/to/your/audio.wav"
    audio_data, sample_rate = sf.read(audio_path)
    
    # Define task - can be "transcribe", "translate", "summarize"
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "<|audio_1|>\nTranscribe the audio to text."}
    ]
    
    # For translation:
    # {"role": "user", "content": "<|audio_1|>\nTranscribe the audio to text, and then translate it to French. Use <sep> as a separator between the original transcript and the translation."}
    
    prompt = processor.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Process inputs with audio
    inputs = processor(
        text=prompt,
        audios=[(audio_data, sample_rate)],
        return_tensors="pt"
    ).to("cuda")
    
    # Generate response
    generation_args = {
        "max_new_tokens": 500,
        "temperature": 0.3,  # Lower temperature for transcription accuracy
        "do_sample": True,
    }
    
    generate_ids = model.generate(
        **inputs,
        eos_token_id=processor.tokenizer.eos_token_id,
        **generation_args
    )
    
    # Decode response
    generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
    response = processor.batch_decode(
        generate_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]
    
    print("Transcription:", response)
    return response


# Example 4: Multi-Modal (Image + Audio + Text) Generation
def multimodal_example():
    """
    Example of using all modalities together.
    """
    model_id = "microsoft/Phi-4-multimodal-instruct"
    
    processor = AutoProcessor.from_pretrained(
        model_id,
        trust_remote_code=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cuda",
        torch_dtype="auto",
        trust_remote_code=True,
        attn_implementation='flash_attention_2',
    )
    
    # Load image and audio
    image = Image.open("path/to/image.jpg").convert('RGB')
    audio_data, sample_rate = sf.read("path/to/audio.wav")
    
    # Complex multi-modal prompt
    messages = [
        {"role": "system", "content": "You are a helpful assistant that can analyze both visual and audio content."},
        {"role": "user", "content": "<|image_1|><|audio_1|>\nI've shown you an image and played an audio clip. Please describe what you see in the image and what you hear in the audio. Then explain any connections between them."}
    ]
    
    prompt = processor.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Process all inputs
    inputs = processor(
        text=prompt,
        images=[image],
        audios=[(audio_data, sample_rate)],
        return_tensors="pt"
    ).to("cuda")
    
    # Generate response
    generate_ids = model.generate(
        **inputs,
        max_new_tokens=1000,
        temperature=0.7,
        do_sample=True,
        eos_token_id=processor.tokenizer.eos_token_id,
    )
    
    # Decode response
    generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
    response = processor.batch_decode(
        generate_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]
    
    print("Multi-modal Analysis:", response)
    return response


# Example 5: Multiple Images Comparison
def multiple_images_example():
    """
    Example of comparing multiple images.
    """
    model_id = "microsoft/Phi-4-multimodal-instruct"
    
    processor = AutoProcessor.from_pretrained(
        model_id,
        trust_remote_code=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cuda",
        torch_dtype="auto",
        trust_remote_code=True,
        attn_implementation='flash_attention_2',
    )
    
    # Load multiple images
    image1 = Image.open("path/to/image1.jpg").convert('RGB')
    image2 = Image.open("path/to/image2.jpg").convert('RGB')
    
    # Prompt for comparison
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "<|image_1|><|image_2|>\nCompare these two images. What are the similarities and differences?"}
    ]
    
    prompt = processor.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Process inputs with multiple images
    inputs = processor(
        text=prompt,
        images=[image1, image2],
        return_tensors="pt"
    ).to("cuda")
    
    # Generate response
    generate_ids = model.generate(
        **inputs,
        max_new_tokens=1000,
        temperature=0.7,
        do_sample=True,
        eos_token_id=processor.tokenizer.eos_token_id,
    )
    
    # Decode response
    generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
    response = processor.batch_decode(
        generate_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]
    
    print("Image Comparison:", response)
    return response


# Example 6: Batch Processing
def batch_processing_example():
    """
    Example of processing multiple prompts in a batch.
    """
    model_id = "microsoft/Phi-4-multimodal-instruct"
    
    processor = AutoProcessor.from_pretrained(
        model_id,
        trust_remote_code=True
    )
    
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cuda",
        torch_dtype="auto",
        trust_remote_code=True,
        attn_implementation='flash_attention_2',
    )
    
    # Multiple prompts
    prompts = [
        "What is artificial intelligence?",
        "Explain quantum computing in simple terms.",
        "What are the benefits of renewable energy?"
    ]
    
    # Apply chat template to each prompt
    formatted_prompts = []
    for prompt in prompts:
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
        formatted_prompt = processor.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        formatted_prompts.append(formatted_prompt)
    
    # Process batch
    inputs = processor(
        formatted_prompts,
        padding=True,
        return_tensors="pt"
    ).to("cuda")
    
    # Generate responses
    generate_ids = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.7,
        do_sample=True,
        eos_token_id=processor.tokenizer.eos_token_id,
    )
    
    # Decode responses
    responses = processor.batch_decode(
        generate_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )
    
    for prompt, response in zip(prompts, responses):
        print(f"Q: {prompt}")
        print(f"A: {response}\n")
    
    return responses


# Helper function for common tasks
def phi4_multimodal_inference(
    prompt: str,
    system_prompt: str = "You are a helpful assistant.",
    images: list = None,
    audio_path: str = None,
    max_tokens: int = 500,
    temperature: float = 0.7,
    model_id: str = "microsoft/Phi-4-multimodal-instruct"
):
    """
    Simplified wrapper for Phi-4-multimodal-instruct inference.
    
    Args:
        prompt: User prompt text
        system_prompt: System prompt
        images: List of PIL Image objects (optional)
        audio_path: Path to audio file (optional)
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        model_id: Model identifier
    
    Returns:
        Generated text response
    """
    # Load model and processor
    processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cuda",
        torch_dtype="auto",
        trust_remote_code=True,
        attn_implementation='flash_attention_2',
    )
    
    # Prepare prompt with placeholders
    user_content = ""
    
    # Add image placeholders
    if images:
        for i in range(len(images)):
            user_content += f"<|image_{i+1}|>"
    
    # Add audio placeholder
    audios = None
    if audio_path:
        user_content += "<|audio_1|>"
        audio_data, sample_rate = sf.read(audio_path)
        audios = [(audio_data, sample_rate)]
    
    user_content += prompt
    
    # Format messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    formatted_prompt = processor.tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # Prepare inputs
    inputs_dict = {"text": formatted_prompt, "return_tensors": "pt"}
    if images:
        inputs_dict["images"] = images
    if audios:
        inputs_dict["audios"] = audios
    
    inputs = processor(**inputs_dict).to("cuda")
    
    # Generate
    generate_ids = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        temperature=temperature,
        do_sample=True,
        eos_token_id=processor.tokenizer.eos_token_id,
    )
    
    # Decode
    generate_ids = generate_ids[:, inputs['input_ids'].shape[1]:]
    response = processor.batch_decode(
        generate_ids,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False
    )[0]
    
    return response


if __name__ == "__main__":
    # Run examples
    print("=== Text-Only Example ===")
    text_only_example()
    
    # Uncomment to run other examples (requires appropriate files)
    # print("\n=== Image + Text Example ===")
    # image_text_example()
    
    # print("\n=== Audio + Text Example ===")
    # audio_text_example()
    
    # print("\n=== Multi-Modal Example ===")
    # multimodal_example()
    
    # print("\n=== Batch Processing Example ===")
    # batch_processing_example()