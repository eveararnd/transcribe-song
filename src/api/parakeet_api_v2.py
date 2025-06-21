#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
FastAPI server for NVIDIA Parakeet TDT 0.6B v2 - Automatic Speech Recognition
Optimized for A100 GPU with automatic audio format conversion
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
import subprocess
import shutil

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
    original_format: Optional[str] = None
    converted: bool = False

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
    ffmpeg_available: bool

def check_ffmpeg():
    """Check if ffmpeg is available"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        return result.returncode == 0
    except:
        return False

def get_audio_info(file_path):
    """Get audio file information using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'stream=codec_type,channels,sample_rate',
            '-of', 'json', file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            import json
            data = json.loads(result.stdout)
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    return {
                        'channels': stream.get('channels', 0),
                        'sample_rate': stream.get('sample_rate', '0')
                    }
    except Exception as e:
        logger.error(f"Error getting audio info: {e}")
    return None

def convert_audio_for_asr(input_path, output_path):
    """Convert audio to mono 16kHz WAV format suitable for ASR"""
    try:
        # Use ffmpeg to convert to mono 16kHz WAV
        cmd = [
            'ffmpeg', '-i', input_path,
            '-acodec', 'pcm_s16le',  # 16-bit PCM
            '-ar', '16000',           # 16kHz sample rate
            '-ac', '1',               # Mono
            '-y',                     # Overwrite output
            output_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg conversion error: {result.stderr}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error converting audio: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global asr_model, device
    
    logger.info("Starting Parakeet TDT ASR API server...")
    
    # Check ffmpeg
    if check_ffmpeg():
        logger.info("FFmpeg is available for audio conversion")
    else:
        logger.warning("FFmpeg not found - audio conversion will be limited")
    
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
    description="NVIDIA Parakeet TDT 0.6B v2 - Automatic Speech Recognition API with automatic format conversion",
    version="2.0.0",
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
            "message": "Parakeet TDT ASR API v2",
            "version": "2.0.0",
            "model": "nvidia/parakeet-tdt-0.6b-v2",
            "description": "600M parameter automatic speech recognition model with automatic format conversion",
            "features": ["Automatic stereo to mono conversion", "Any audio format support via FFmpeg"],
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
        "cuda_version": None,
        "ffmpeg_available": check_ffmpeg()
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
    file: UploadFile = File(..., description="Audio file to transcribe (any format)"),
    timestamps: Optional[bool] = Form(False, description="Include word-level timestamps"),
    return_segments: Optional[bool] = Form(False, description="Return detailed segments")
):
    """Transcribe audio to text using Parakeet TDT ASR model with automatic format conversion"""
    if not asr_model:
        raise HTTPException(status_code=503, detail="ASR model not loaded")
    
    # Remove strict content type checking - accept any file
    logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")
    
    # Initialize variables
    tmp_file_path = None
    converted_file_path = None
    audio_converted = False
    original_format = Path(file.filename).suffix
    
    try:
        start_time = time.time()
        
        # Save uploaded file temporarily
        suffix = Path(file.filename).suffix or '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Processing audio file: {file.filename} ({len(content)/1024:.1f} KB)")
        
        # Get audio info
        audio_info = get_audio_info(tmp_file_path)
        if audio_info:
            logger.info(f"Original audio: {audio_info['channels']} channels, {audio_info['sample_rate']} Hz")
        
        # Check if conversion is needed
        needs_conversion = False
        processing_file = tmp_file_path
        
        # Try to read with soundfile first
        try:
            audio_data, sample_rate = sf.read(tmp_file_path)
            # Check if stereo or wrong sample rate
            if len(audio_data.shape) > 1 or sample_rate != 16000:
                needs_conversion = True
                logger.info(f"Conversion needed: shape={audio_data.shape}, rate={sample_rate}")
        except Exception as e:
            # If soundfile can't read it, we definitely need conversion
            needs_conversion = True
            logger.info(f"Soundfile cannot read file, conversion needed: {e}")
        
        # Convert if necessary
        if needs_conversion and check_ffmpeg():
            converted_file_path = tmp_file_path + "_converted.wav"
            logger.info("Converting audio to mono 16kHz WAV...")
            
            if convert_audio_for_asr(tmp_file_path, converted_file_path):
                processing_file = converted_file_path
                audio_converted = True
                logger.info("Audio conversion successful")
            else:
                logger.warning("Audio conversion failed, attempting with original file")
        
        # Get audio duration
        try:
            audio_data, sample_rate = sf.read(processing_file)
            audio_duration = len(audio_data) / sample_rate
            logger.info(f"Audio duration: {audio_duration:.2f} seconds, Sample rate: {sample_rate} Hz")
        except Exception as e:
            logger.error(f"Error reading audio file: {e}")
            audio_duration = 0
        
        # Transcribe with Parakeet
        with torch.cuda.amp.autocast(enabled=device.type == "cuda"):
            # Basic transcription
            transcriptions = asr_model.transcribe([processing_file])
            
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
                        [processing_file],
                        return_hypotheses=True
                    )
                    
                    if hypotheses and len(hypotheses) > 0:
                        hypothesis = hypotheses[0]
                        if hasattr(hypothesis, 'timestep') or hasattr(hypothesis, 'word_timestamps'):
                            segments = []
                            # Extract word-level timestamps if available
                            logger.info("Timestamps available in hypothesis")
                except Exception as e:
                    logger.warning(f"Could not extract timestamps: {e}")
        
        processing_time = time.time() - start_time
        logger.info(f"ASR transcription completed in {processing_time:.3f}s")
        
        # Prepare response
        response = TranscriptionResponse(
            text=transcription_text.strip() if transcription_text else "",
            language="en",  # Parakeet TDT is English-only
            processing_time=processing_time,
            audio_duration=audio_duration,
            segments=segments,
            original_format=original_format,
            converted=audio_converted
        )
        
        return response
        
    except Exception as e:
        logger.error(f"ASR transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Clean up temp files
        if tmp_file_path and os.path.exists(tmp_file_path):
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        if converted_file_path and os.path.exists(converted_file_path):
            try:
                os.unlink(converted_file_path)
            except:
                pass

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
        "parakeet_api_v2:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker for GPU model
        log_level="info",
        access_log=True
    )