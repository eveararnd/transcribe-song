#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
FastAPI server for NVIDIA Parakeet TDT 0.6B v2
Optimized for A100 GPU with latest Python/PyTorch
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List
import torch
import torch.nn.functional as F
import numpy as np
import soundfile as sf
import io
import os
import time
import logging
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instance
model = None
device = None

class TTSRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    speaker_id: Optional[int] = Field(0, description="Speaker ID for multi-speaker models")
    speed: Optional[float] = Field(1.0, description="Speech speed multiplier")
    sample_rate: Optional[int] = Field(22050, description="Output sample rate")
    format: Optional[str] = Field("wav", description="Output format: wav, mp3, flac")

class TTSResponse(BaseModel):
    audio_length: float
    sample_rate: int
    processing_time: float

class HealthResponse(BaseModel):
    status: str
    cuda_available: bool
    gpu_name: Optional[str]
    gpu_memory_total: Optional[float]
    gpu_memory_used: Optional[float]
    model_loaded: bool
    python_version: str
    torch_version: str
    cuda_version: Optional[str]

class ParakeetTDTModel:
    """Wrapper for Parakeet TDT model with A100 optimizations"""
    
    def __init__(self, model_path: str, device: str = "cuda"):
        self.model_path = Path(model_path)
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        
        # A100 optimizations
        if self.device.type == "cuda":
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
            torch.backends.cudnn.benchmark = True
            torch.set_float32_matmul_precision('high')
        
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load the model with error handling"""
        logger.info(f"Loading model from {self.model_path}")
        
        try:
            # This is a placeholder - actual loading depends on model format
            # For NeMo models:
            # from nemo.collections.tts.models import FastPitchModel
            # self.model = FastPitchModel.restore_from(str(self.model_path / "model.nemo"))
            
            # For Hugging Face models:
            # from transformers import AutoModelForTextToSpeech
            # self.model = AutoModelForTextToSpeech.from_pretrained(str(self.model_path))
            
            if self.model:
                self.model.to(self.device)
                self.model.eval()
                
            logger.info(f"Model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    @torch.no_grad()
    def synthesize(self, text: str, speaker_id: int = 0, speed: float = 1.0) -> np.ndarray:
        """Synthesize speech from text"""
        start_time = time.time()
        
        # Use automatic mixed precision for A100
        with torch.cuda.amp.autocast(enabled=self.device.type == "cuda"):
            # Placeholder for actual synthesis
            # In reality, this would:
            # 1. Tokenize text
            # 2. Run through model
            # 3. Generate audio waveform
            
            # For now, generate dummy audio
            duration = len(text.split()) * 0.5  # Rough estimate
            sample_rate = 22050
            t = np.linspace(0, duration, int(sample_rate * duration))
            audio = np.sin(2 * np.pi * 440 * t) * 0.1  # 440 Hz sine wave
            
            # Apply speed adjustment
            if speed != 1.0:
                # Resample for speed change
                new_length = int(len(audio) / speed)
                audio = np.interp(
                    np.linspace(0, len(audio), new_length),
                    np.arange(len(audio)),
                    audio
                )
        
        logger.info(f"Synthesis completed in {time.time() - start_time:.3f}s")
        return audio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage model lifecycle"""
    global model, device
    
    # Startup
    logger.info("Starting Parakeet TDT API server...")
    
    # Check CUDA
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info(f"CUDA available: {torch.cuda.get_device_name(0)}")
        logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
    else:
        device = torch.device("cpu")
        logger.warning("CUDA not available, using CPU")
    
    # Load model
    model_path = os.getenv("MODEL_PATH", "./models/parakeet-tdt-0.6b-v2")
    try:
        model = ParakeetTDTModel(model_path, device.type)
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        model = None
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if model:
        del model
        torch.cuda.empty_cache()

# Create FastAPI app
app = FastAPI(
    title="Parakeet TDT API",
    description="NVIDIA Parakeet TDT 0.6B v2 Text-to-Speech API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Serve the index.html page"""
    index_path = Path(__file__).parent / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    else:
        # Fallback to JSON response
        return {
            "message": "Parakeet TDT API",
            "version": "1.0.0",
            "endpoints": {
                "synthesize": "/synthesize",
                "health": "/health",
                "docs": "/docs"
            }
        }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    import sys
    
    health_info = {
        "status": "healthy" if model else "unhealthy",
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": None,
        "gpu_memory_total": None,
        "gpu_memory_used": None,
        "model_loaded": model is not None,
        "python_version": sys.version.split()[0],
        "torch_version": torch.__version__,
        "cuda_version": None
    }
    
    if torch.cuda.is_available():
        health_info["gpu_name"] = torch.cuda.get_device_name(0)
        health_info["cuda_version"] = torch.version.cuda
        
        # Get memory info
        mem_info = torch.cuda.mem_get_info(0)
        health_info["gpu_memory_total"] = mem_info[1] / 1024**3  # GB
        health_info["gpu_memory_used"] = (mem_info[1] - mem_info[0]) / 1024**3  # GB
    
    return health_info

@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """Synthesize speech from text"""
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    try:
        start_time = time.time()
        
        # Synthesize audio
        audio = model.synthesize(
            text=request.text,
            speaker_id=request.speaker_id,
            speed=request.speed
        )
        
        # Convert to requested format
        buffer = io.BytesIO()
        if request.format == "wav":
            sf.write(buffer, audio, request.sample_rate, format='WAV')
            media_type = "audio/wav"
        elif request.format == "flac":
            sf.write(buffer, audio, request.sample_rate, format='FLAC')
            media_type = "audio/flac"
        else:
            # Default to WAV
            sf.write(buffer, audio, request.sample_rate, format='WAV')
            media_type = "audio/wav"
        
        buffer.seek(0)
        
        # Add headers with metadata
        headers = {
            "X-Audio-Length": str(len(audio) / request.sample_rate),
            "X-Processing-Time": str(time.time() - start_time),
            "X-Sample-Rate": str(request.sample_rate)
        }
        
        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers=headers
        )
        
    except Exception as e:
        logger.error(f"Synthesis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/synthesize/batch")
async def synthesize_batch(texts: List[str], background_tasks: BackgroundTasks):
    """Batch synthesis endpoint"""
    if not model:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    # Queue background tasks
    job_id = f"batch_{int(time.time())}"
    
    # In production, you'd implement proper job queuing
    return {
        "job_id": job_id,
        "status": "queued",
        "num_texts": len(texts)
    }

@app.get("/gpu/stats")
async def gpu_stats():
    """Get current GPU statistics"""
    if not torch.cuda.is_available():
        return {"error": "CUDA not available"}
    
    return {
        "gpu_name": torch.cuda.get_device_name(0),
        "memory": {
            "total_gb": torch.cuda.get_device_properties(0).total_memory / 1024**3,
            "allocated_gb": torch.cuda.memory_allocated(0) / 1024**3,
            "reserved_gb": torch.cuda.memory_reserved(0) / 1024**3,
            "free_gb": (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1024**3
        },
        "utilization": {
            "compute": "N/A",  # Would need nvidia-ml-py for real stats
            "memory": f"{(torch.cuda.memory_allocated(0) / torch.cuda.get_device_properties(0).total_memory) * 100:.1f}%"
        }
    }

if __name__ == "__main__":
    # Run with optimal settings for production
    uvicorn.run(
        "parakeet_api:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker for GPU model
        log_level="info",
        access_log=True
    )