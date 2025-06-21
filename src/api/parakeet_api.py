#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
FastAPI server for NVIDIA Parakeet TDT 0.6B v2 - Automatic Speech Recognition
Optimized for A100 GPU with latest Python/PyTorch
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import torch
import numpy as np
import soundfile as sf
import io
import os
import time
import logging
from pathlib import Path
from contextlib import asynccontextmanager
import uvicorn
import tempfile
import nemo.collections.asr as nemo_asr

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instance
asr_model = None
device = None

class TranscriptionResponse(BaseModel):
    text: str
    language: str = "en"
    segments: Optional[List[Dict]] = None
    processing_time: float
    audio_duration: float

class HealthResponse(BaseModel):
    status: str
    cuda_available: bool
    gpu_name: Optional[str]
    gpu_memory_total: Optional[float]
    gpu_memory_used: Optional[float]
    model_loaded: bool
    model_type: str = "ASR"
    python_version: str
    torch_version: str
    cuda_version: Optional[str]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global asr_model, device
    
    logger.info("Starting Parakeet TDT ASR API server...")
    
    # Set device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
        logger.info(f"CUDA available: {gpu_name}")
        logger.info(f"GPU Memory: {gpu_mem:.1f} GB")
    
    # Load ASR model
    model_path = Path("models/parakeet-tdt-0.6b-v2")
    nemo_file = model_path / "parakeet-tdt-0.6b-v2.nemo"
    
    if nemo_file.exists():
        try:
            logger.info(f"Loading ASR model from {nemo_file}")
            asr_model = nemo_asr.models.ASRModel.restore_from(str(nemo_file))
            asr_model = asr_model.to(device)
            asr_model.eval()
            logger.info(f"ASR model loaded successfully on {device}")
        except Exception as e:
            logger.error(f"Failed to load ASR model: {e}")
            # Try loading from Hugging Face
            try:
                logger.info("Attempting to load from Hugging Face...")
                asr_model = nemo_asr.models.ASRModel.from_pretrained("nvidia/parakeet-tdt-0.6b-v2")
                asr_model = asr_model.to(device)
                asr_model.eval()
                logger.info("ASR model loaded from Hugging Face successfully")
            except Exception as e2:
                logger.error(f"Failed to load from HuggingFace: {e2}")
                asr_model = None
    else:
        logger.warning(f"Model file {nemo_file} not found")
        asr_model = None
    
    yield
    
    # Cleanup
    logger.info("Shutting down API server...")

# Create FastAPI app
app = FastAPI(
    title="Parakeet TDT ASR API",
    description="NVIDIA Parakeet TDT 0.6B v2 - Automatic Speech Recognition API",
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
            "message": "Parakeet TDT ASR API",
            "version": "1.0.0",
            "model": "nvidia/parakeet-tdt-0.6b-v2",
            "description": "600M parameter automatic speech recognition model",
            "endpoints": {
                "transcribe": "/transcribe",
                "health": "/health",
                "docs": "/docs"
            }
        }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    import sys
    
    health_info = {
        "status": "healthy" if asr_model else "unhealthy",
        "cuda_available": torch.cuda.is_available(),
        "gpu_name": None,
        "gpu_memory_total": None,
        "gpu_memory_used": None,
        "model_loaded": asr_model is not None,
        "model_type": "ASR",
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

@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    timestamps: Optional[bool] = Form(False, description="Include word-level timestamps"),
    return_segments: Optional[bool] = Form(False, description="Return detailed segments")
):
    """Transcribe audio to text using Parakeet TDT ASR model"""
    if not asr_model:
        raise HTTPException(status_code=503, detail="ASR model not loaded")
    
    # Check file type
    allowed_types = ['audio/', 'video/']
    if not any(file.content_type.startswith(t) for t in allowed_types):
        raise HTTPException(
            status_code=400, 
            detail=f"File must be an audio or video file. Received: {file.content_type}"
        )
    
    try:
        start_time = time.time()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Processing audio file: {file.filename} ({len(content)/1024:.1f} KB)")
        
        # Load audio and get duration
        try:
            audio_data, sample_rate = sf.read(tmp_file_path)
            audio_duration = len(audio_data) / sample_rate
            logger.info(f"Audio duration: {audio_duration:.2f} seconds, Sample rate: {sample_rate} Hz")
        except Exception as e:
            logger.error(f"Error reading audio file: {e}")
            audio_duration = 0
        
        # Transcribe with Parakeet
        with torch.cuda.amp.autocast(enabled=device.type == "cuda"):
            # Basic transcription
            transcriptions = asr_model.transcribe([tmp_file_path])
            
            if isinstance(transcriptions, list) and len(transcriptions) > 0:
                # Check if it's a Hypothesis object
                if hasattr(transcriptions[0], 'text'):
                    transcription_text = transcriptions[0].text
                else:
                    transcription_text = str(transcriptions[0])
            else:
                transcription_text = str(transcriptions)
            
            # Get timestamps if requested
            segments = None
            if timestamps or return_segments:
                try:
                    # Try to get detailed output with timestamps
                    hypotheses = asr_model.transcribe(
                        [tmp_file_path],
                        return_hypotheses=True
                    )
                    
                    if hypotheses and len(hypotheses) > 0:
                        hypothesis = hypotheses[0]
                        if hasattr(hypothesis, 'timestep') or hasattr(hypothesis, 'word_timestamps'):
                            segments = []
                            # Extract word-level timestamps if available
                            # This varies by model configuration
                            logger.info("Timestamps available in hypothesis")
                except Exception as e:
                    logger.warning(f"Could not extract timestamps: {e}")
        
        processing_time = time.time() - start_time
        logger.info(f"ASR transcription completed in {processing_time:.3f}s")
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        # Prepare response
        response = TranscriptionResponse(
            text=transcription_text.strip(),
            language="en",  # Parakeet TDT is English-only
            processing_time=processing_time,
            audio_duration=audio_duration,
            segments=segments
        )
        
        return response
        
    except Exception as e:
        logger.error(f"ASR transcription error: {e}")
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals() and os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)
        raise HTTPException(status_code=500, detail=str(e))

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