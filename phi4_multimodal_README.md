# Phi-4-multimodal-instruct Usage Guide

This guide provides comprehensive examples for using Microsoft's Phi-4-multimodal-instruct model for text generation with various input modalities including text, images, and audio.

## Model Overview

Phi-4-multimodal-instruct is a lightweight open multimodal foundation model that:
- Processes text, image, and audio inputs
- Generates text outputs
- Supports 128K token context length
- Supports 23 languages for text, English for vision and audio (with additional languages for audio including Chinese, German, French, Italian, Japanese, Spanish, Portuguese)

## Installation

```bash
pip install transformers>=4.48.2 torch>=2.6.0 pillow soundfile scipy accelerate flash-attn
```

For Azure AI integration:
```bash
pip install azure-ai-inference azure-search-documents
```

## Key Features

### 1. Text-Only Generation
Basic conversational AI and text generation capabilities.

### 2. Visual Question Answering
Process images with text prompts to:
- Describe image contents
- Answer questions about images
- Perform OCR (Optical Character Recognition)
- Analyze charts and tables
- Compare multiple images

### 3. Audio Processing
Handle audio inputs for:
- Speech recognition (ASR)
- Speech translation
- Speech summarization
- Audio understanding
- Speech Q&A

### 4. Multimodal Processing
Combine multiple modalities:
- Image + Audio + Text analysis
- Vision-Speech tasks
- Multi-frame video understanding

## Usage Examples

### Basic Text Generation

```python
from transformers import AutoModelForCausalLM, AutoProcessor

model_id = "microsoft/Phi-4-multimodal-instruct"
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="cuda",
    torch_dtype="auto",
    trust_remote_code=True,
    attn_implementation='flash_attention_2',
)

messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is artificial intelligence?"}
]

prompt = processor.tokenizer.apply_chat_template(
    messages, 
    tokenize=False, 
    add_generation_prompt=True
)

inputs = processor(prompt, return_tensors="pt").to("cuda")
generate_ids = model.generate(**inputs, max_new_tokens=500, temperature=0.7)
response = processor.batch_decode(generate_ids, skip_special_tokens=True)[0]
```

### Image Analysis

```python
from PIL import Image

image = Image.open("path/to/image.jpg").convert('RGB')

messages = [
    {"role": "user", "content": "<|image_1|>\nDescribe this image in detail."}
]

prompt = processor.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = processor(text=prompt, images=[image], return_tensors="pt").to("cuda")
generate_ids = model.generate(**inputs, max_new_tokens=1000)
```

### Audio Transcription

```python
import soundfile as sf

audio_data, sample_rate = sf.read("path/to/audio.wav")

messages = [
    {"role": "user", "content": "<|audio_1|>\nTranscribe the audio to text."}
]

prompt = processor.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = processor(text=prompt, audios=[(audio_data, sample_rate)], return_tensors="pt").to("cuda")
generate_ids = model.generate(**inputs, max_new_tokens=500)
```

## Input Format Guidelines

### Special Tokens
- Images: `<|image_1|>`, `<|image_2|>`, etc.
- Audio: `<|audio_1|>`, `<|audio_2|>`, etc.
- System prompt: `<|system|>...<|end|>`
- User prompt: `<|user|>...<|end|>`
- Assistant response: `<|assistant|>...<|end|>`

### Best Practices
1. Always use the chat template format for optimal results
2. Place media placeholders before text in prompts
3. Use lower temperature (0.3-0.5) for transcription tasks
4. Use higher temperature (0.7-0.9) for creative tasks

## RAG (Retrieval Augmented Generation)

The model can be integrated with retrieval systems like Azure AI Search for enhanced knowledge-grounded generation. See `phi4_multimodal_rag_example.py` for detailed implementation.

## Performance Benchmarks

- **Speech Recognition**: WER 6.14% on OpenASR leaderboard
- **Vision**: Competitive with models like Gemini-2.0-Flash on tasks like MMMU (55.1%), DocVQA (93.2%)
- **Multimodal**: Strong performance on vision-speech tasks (72.2% average across multiple benchmarks)

## Limitations

- Vision and audio capabilities are primarily optimized for English
- Model may have performance differences across languages
- Requires GPU with sufficient memory (recommended: 24GB+ VRAM)
- Flash attention recommended for optimal performance

## Resources

- [Phi-4 Technical Report](https://arxiv.org/abs/2503.01743)
- [Microsoft PhiCookBook](https://github.com/microsoft/PhiCookBook)
- [Hugging Face Model Card](https://huggingface.co/microsoft/Phi-4-multimodal-instruct)
- [Azure AI Model Catalog](https://ai.azure.com)

## License

The model is released under the MIT license. See the model repository for full license details.