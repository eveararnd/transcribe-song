# Multi-Model System for Music Analyzer

## Overview
The Music Analyzer now supports three different AI models with the ability to switch between them:

1. **Google Gemma-3-12B-IT** - Large instruction-tuned model with bfloat16 optimization
2. **Microsoft Phi-4-multimodal-instruct** - Multimodal model supporting text, images, and audio
3. **Microsoft Phi-4-reasoning-plus** - Advanced reasoning model

## Model Details

### 1. Gemma-3-12B-IT
- **Path**: `/home/davegornshtein/parakeet-tdt-deployment/gemma-3-12b-it`
- **Type**: Causal Language Model
- **Size**: ~24GB
- **Status**: Fully functional with bfloat16 optimization for A100 GPU
- **Use Case**: General purpose instruction following, text generation, and analysis

### 2. Phi-4-multimodal-instruct
- **Path**: `/home/davegornshtein/parakeet-tdt-deployment/models/phi-4-multimodal`
- **Type**: Multimodal (text, image, audio)
- **Size**: Variable
- **Status**: Downloaded, ready to use
- **Use Case**: Analyzing lyrics with potential for album art and audio analysis

### 3. Phi-4-reasoning-plus
- **Path**: `/home/davegornshtein/parakeet-tdt-deployment/models/phi-4-reasoning`
- **Type**: Causal Language Model
- **Size**: Variable
- **Status**: Downloaded, ready to use
- **Use Case**: Advanced reasoning about music, lyrics interpretation

## API Endpoints

### Model Management

#### Get Model Status
```bash
GET /api/v2/models/status
```
Returns status of all models including download status, loaded state, and memory usage.

#### Load Model
```bash
POST /api/v2/models/load
{
  "model_type": "phi-4-multimodal"  # or "gemma-3n-E4B" or "phi-4-reasoning"
}
```
Loads the specified model into memory. Only one model can be loaded at a time.

#### Unload Model
```bash
POST /api/v2/models/unload
```
Unloads the current model to free GPU memory.

#### Generate Text
```bash
POST /api/v2/models/generate
{
  "prompt": "Analyze these lyrics...",
  "max_length": 200
}
```
Generates text using the currently loaded model.

## Configuration

The system uses environment variables from `.env`:
```bash
HF_TOKEN=your_huggingface_token_here
GEMMA_MODEL_PATH=/home/davegornshtein/parakeet-tdt-deployment/models/gemma-3n-E4B
```

## Usage Examples

### 1. Check Model Status
```python
import requests

response = requests.get(
    "http://localhost:8000/api/v2/models/status",
    auth=("parakeet", "password")
)
status = response.json()
print(f"Current model: {status['current_model']}")
```

### 2. Load Phi-4 Multimodal
```python
response = requests.post(
    "http://localhost:8000/api/v2/models/load",
    auth=("parakeet", "password"),
    json={"model_type": "phi-4-multimodal"}
)
```

### 3. Generate Analysis
```python
response = requests.post(
    "http://localhost:8000/api/v2/models/generate",
    auth=("parakeet", "password"),
    json={
        "prompt": "Analyze the mood of these lyrics: 'don't you worry child'",
        "max_length": 150
    }
)
result = response.json()
print(f"Analysis: {result['response']}")
```

## Model Selection Guide

### When to use Gemma-3-12B:
- General purpose text generation and analysis
- Instruction following tasks
- When you need high-quality, coherent responses
- Balanced performance and capability

### When to use Phi-4-multimodal:
- Analyzing lyrics with context from album art
- Future: Processing audio waveforms
- Multi-aspect music analysis
- When you need comprehensive understanding

### When to use Phi-4-reasoning:
- Complex lyrics interpretation
- Identifying hidden meanings
- Advanced music theory analysis
- Comparing multiple songs

## Memory Management

- Only one model can be loaded at a time
- Models are automatically unloaded when switching
- GPU memory is cleared between model switches
- Typical memory usage:
  - Phi-4-multimodal: ~8-12GB
  - Phi-4-reasoning: ~8-12GB
  - Gemma-3-12B: ~24GB (bfloat16)

## Future Enhancements

1. **Automatic Model Selection**: Based on task type
2. **Model Ensemble**: Use multiple models for better results
3. **LiteRT Integration**: Complete Gemma inference implementation
4. **Multimodal Features**: Enable image/audio input for Phi-4-multimodal
5. **Performance Optimization**: Model quantization and caching

## Troubleshooting

### Flash Attention Error
If you see Flash Attention errors, the system automatically falls back to eager attention.

### Out of Memory
Unload the current model before loading a new one:
```bash
POST /api/v2/models/unload
```

### Model Not Found
Ensure models are downloaded:
```bash
python download_and_test_models.py
```

## Integration with Music Analyzer

The multi-model system integrates seamlessly with existing features:
- Enhanced lyrics search uses the loaded model for decision making
- Lyrics analysis can leverage different models for different aspects
- Vector search can use embeddings from any loaded model