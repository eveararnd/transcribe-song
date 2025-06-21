#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
FastAPI server for NVIDIA Parakeet TDT 0.6B v2 - Automatic Speech Recognition
With automatic audio format conversion using ffmpeg-python
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
import ffmpeg
from pydub import AudioSegment

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
    original_channels: Optional[int] = None
    original_sample_rate: Optional[int] = None
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
    ffmpeg_available: bool = True

def get_audio_info(file_path):
    """Get audio file information using ffmpeg-python"""
    try:
        probe = ffmpeg.probe(file_path)
        audio_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        if audio_info:
            return {
                'channels': audio_info.get('channels', 0),
                'sample_rate': int(audio_info.get('sample_rate', 0)),
                'duration': float(probe.get('format', {}).get('duration', 0)),
                'codec': audio_info.get('codec_name', 'unknown')
            }
    except Exception as e:
        logger.error(f"Error probing audio file: {e}")
    return None

def convert_audio_for_asr(input_path, output_path):
    """Convert any audio format to mono 16kHz WAV using ffmpeg-python"""
    try:
        # Use ffmpeg-python to convert
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(stream, output_path, 
                              acodec='pcm_s16le',  # 16-bit PCM
                              ar=16000,            # 16kHz sample rate
                              ac=1)                # Mono
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        return True
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error converting audio: {e}")
        return False

def convert_with_pydub(input_path, output_path):
    """Alternative conversion using pydub for common formats"""
    try:
        # Load audio file
        audio = AudioSegment.from_file(input_path)
        
        # Convert to mono if stereo
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # Set sample rate to 16kHz
        audio = audio.set_frame_rate(16000)
        
        # Export as WAV
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        logger.error(f"Pydub conversion error: {e}")
        return False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global asr_model, device
    
    logger.info("Starting Parakeet TDT ASR API server with automatic format conversion...")
    
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
    title="Parakeet TDT ASR API - Auto Format",
    description="NVIDIA Parakeet TDT 0.6B v2 - ASR with automatic audio format conversion",
    version="3.0.0",
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
        return {
            "message": "Parakeet TDT ASR API - Auto Format",
            "version": "3.0.0",
            "model": "nvidia/parakeet-tdt-0.6b-v2",
            "description": "ASR with automatic format conversion",
            "supported_formats": [
                "WAV", "MP3", "FLAC", "OGG", "M4A", "AAC", "WMA", "AIFF", 
                "MP4", "AVI", "MOV", "MKV", "WebM", "and more..."
            ],
            "features": [
                "Automatic stereo to mono conversion",
                "Automatic sample rate conversion to 16kHz",
                "Support for any audio/video format via FFmpeg",
                "Handles files with multiple audio channels"
            ],
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
        "ffmpeg_available": True
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
    file: UploadFile = File(..., description="Audio/video file to transcribe (any format)"),
    timestamps: Optional[bool] = Form(False, description="Include word-level timestamps"),
    return_segments: Optional[bool] = Form(False, description="Return detailed segments")
):
    """
    Transcribe audio to text using Parakeet TDT ASR model.
    
    Supports ANY audio or video format including:
    - Audio: WAV, MP3, FLAC, OGG, M4A, AAC, WMA, AIFF, etc.
    - Video: MP4, AVI, MOV, MKV, WebM, etc.
    
    Automatically converts:
    - Stereo/multi-channel to mono
    - Any sample rate to 16kHz
    - Any format to WAV for processing
    """
    if not asr_model:
        raise HTTPException(status_code=503, detail="ASR model not loaded")
    
    # Log received file
    logger.info(f"Received file: {file.filename}, content_type: {file.content_type or 'unknown'}")
    
    # Initialize variables
    tmp_file_path = None
    converted_file_path = None
    audio_converted = False
    original_info = {}
    
    try:
        start_time = time.time()
        
        # Save uploaded file temporarily
        suffix = Path(file.filename).suffix if file.filename else '.tmp'
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        logger.info(f"Saved temp file: {tmp_file_path} ({len(content)/1024/1024:.1f} MB)")
        
        # Get original audio info
        audio_info = get_audio_info(tmp_file_path)
        if audio_info:
            original_info = {
                'channels': audio_info['channels'],
                'sample_rate': audio_info['sample_rate'],
                'codec': audio_info['codec']
            }
            logger.info(f"Original: {audio_info['channels']}ch, {audio_info['sample_rate']}Hz, {audio_info['codec']}")
        
        # Always convert to ensure compatibility
        converted_file_path = tmp_file_path + "_converted.wav"
        processing_file = tmp_file_path
        
        # Try ffmpeg-python first
        logger.info("Converting audio to mono 16kHz WAV...")
        if convert_audio_for_asr(tmp_file_path, converted_file_path):
            processing_file = converted_file_path
            audio_converted = True
            logger.info("Audio conversion successful with ffmpeg-python")
        else:
            # Try pydub as fallback
            logger.info("Trying pydub conversion as fallback...")
            if convert_with_pydub(tmp_file_path, converted_file_path):
                processing_file = converted_file_path
                audio_converted = True
                logger.info("Audio conversion successful with pydub")
            else:
                # Last resort: try original file
                logger.warning("All conversions failed, attempting with original file")
                processing_file = tmp_file_path
        
        # Get audio duration from converted file
        audio_duration = 0
        try:
            audio_data, sample_rate = sf.read(processing_file)
            audio_duration = len(audio_data) / sample_rate
            logger.info(f"Processing audio: duration={audio_duration:.2f}s, rate={sample_rate}Hz")
        except Exception as e:
            logger.error(f"Error reading converted audio: {e}")
            # Try to get duration from original
            if audio_info:
                audio_duration = audio_info.get('duration', 0)
        
        # Transcribe with Parakeet
        logger.info("Starting transcription...")
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
                    hypotheses = asr_model.transcribe(
                        [processing_file],
                        return_hypotheses=True
                    )
                    
                    if hypotheses and len(hypotheses) > 0:
                        hypothesis = hypotheses[0]
                        if hasattr(hypothesis, 'word_timestamps'):
                            segments = hypothesis.word_timestamps
                            logger.info("Word timestamps extracted")
                except Exception as e:
                    logger.warning(f"Could not extract timestamps: {e}")
        
        processing_time = time.time() - start_time
        logger.info(f"Transcription completed in {processing_time:.3f}s")
        
        # Prepare response
        response = TranscriptionResponse(
            text=transcription_text.strip() if transcription_text else "",
            language="en",
            processing_time=processing_time,
            audio_duration=audio_duration,
            segments=segments,
            original_format=suffix,
            original_channels=original_info.get('channels'),
            original_sample_rate=original_info.get('sample_rate'),
            converted=audio_converted
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        # Clean up temp files
        for file_path in [tmp_file_path, converted_file_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                    logger.debug(f"Cleaned up: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {file_path}: {e}")

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
            "compute": "N/A",
            "memory": f"{(torch.cuda.memory_allocated(0) / torch.cuda.get_device_properties(0).total_memory) * 100:.1f}%"
        },
        "supported_formats": {
            "audio": ["WAV", "MP3", "FLAC", "OGG", "M4A", "AAC", "WMA", "AIFF", "APE", "WV"],
            "video": ["MP4", "AVI", "MOV", "MKV", "WebM", "FLV", "WMV", "MPG", "3GP"]
        }
    }

if __name__ == "__main__":
    # Run with optimal settings for production
    uvicorn.run(
        "parakeet_api_auto:app",
        host="0.0.0.0",
        port=8000,
        workers=1,  # Single worker for GPU model
        log_level="info",
        access_log=True
    )