#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Complete Parakeet API with ASR and Music Analyzer functionality
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
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
import json
import shutil
import hashlib
from datetime import datetime
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import V2 integration
try:
    from music_analyzer_v2_integration import integrate_v2_endpoints
    V2_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Music Analyzer V2 not available: {e}")
    V2_AVAILABLE = False

# Global model instance
asr_model = None
device = None

# Authentication
security = HTTPBasic()
VALID_USERNAME = "parakeet"
VALID_PASSWORD = "Q7+sKsoPWJH5vuulfY+RuQSmUyZj3jBa09Ql5om32hI="

# Music library setup
MUSIC_BASE_DIR = Path("/home/davegornshtein/parakeet-tdt-deployment/music_library")
GENRES = ["pop", "rock", "hiphop", "electronic", "classical", "jazz", "country", "other"]
CATALOG_FILE = MUSIC_BASE_DIR / "catalog.json"

# Create directories
for genre in GENRES:
    (MUSIC_BASE_DIR / genre).mkdir(parents=True, exist_ok=True)

# Models
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

class TranscribeRequest(BaseModel):
    filepath: str

class LyricsSearchRequest(BaseModel):
    filename: str

# Helper functions
def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic credentials - accepts both nginx and API passwords"""
    NGINX_PASSWORD = "Q7+vD#8kN$2pL@9"
    
    if credentials.username != VALID_USERNAME:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Accept either the API password or nginx password
    if credentials.password != VALID_PASSWORD and credentials.password != NGINX_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return credentials

def load_catalog():
    """Load music catalog from JSON file"""
    if CATALOG_FILE.exists():
        try:
            with open(CATALOG_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"files": {}, "stats": {"total_files": 0, "total_size": 0}}

def save_catalog(catalog):
    """Save music catalog to JSON file"""
    with open(CATALOG_FILE, 'w') as f:
        json.dump(catalog, f, indent=2)

def get_audio_info(file_path):
    """Get audio file information using ffmpeg-python"""
    try:
        probe = ffmpeg.probe(str(file_path))
        audio_info = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        if audio_info:
            return {
                'channels': audio_info.get('channels', 0),
                'sample_rate': int(audio_info.get('sample_rate', 0)),
                'duration': float(probe.get('format', {}).get('duration', 0)),
                'codec': audio_info.get('codec_name', 'unknown'),
                'bitrate': int(probe.get('format', {}).get('bit_rate', 0))
            }
    except Exception as e:
        logger.error(f"Error probing audio file: {e}")
    return None

def convert_audio_for_asr(input_path, output_path):
    """Convert any audio format to mono 16kHz WAV using ffmpeg-python"""
    try:
        stream = ffmpeg.input(str(input_path))
        stream = ffmpeg.output(stream, str(output_path), 
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
        audio = AudioSegment.from_file(input_path)
        if audio.channels > 1:
            audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        logger.error(f"Pydub conversion error: {e}")
        return False

def detect_genre(filename, audio_info):
    """Detect genre based on filename and audio characteristics"""
    filename_lower = filename.lower()
    
    # Simple keyword-based detection
    if any(word in filename_lower for word in ['rock', 'metal', 'guitar']):
        return 'rock'
    elif any(word in filename_lower for word in ['pop', 'dance', 'hit']):
        return 'pop'
    elif any(word in filename_lower for word in ['hip', 'hop', 'rap', 'beat']):
        return 'hiphop'
    elif any(word in filename_lower for word in ['electronic', 'techno', 'house', 'edm']):
        return 'electronic'
    elif any(word in filename_lower for word in ['classical', 'symphony', 'orchestra']):
        return 'classical'
    elif any(word in filename_lower for word in ['jazz', 'blues', 'swing']):
        return 'jazz'
    elif any(word in filename_lower for word in ['country', 'folk', 'bluegrass']):
        return 'country'
    
    return 'other'

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global asr_model, device
    
    logger.info("Starting Complete Parakeet API with ASR and Music Analyzer...")
    
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
    
    logger.info("Shutting down API server...")

# Create FastAPI app
app = FastAPI(
    title="Parakeet Complete API",
    description="ASR + Music Analyzer - Complete Solution",
    version="4.0.0",
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

# Integrate V2 endpoints if available
if V2_AVAILABLE:
    integrate_v2_endpoints(app, asr_model)
    logger.info("Music Analyzer V2 endpoints integrated")

# Root endpoint
@app.get("/")
async def root():
    """Serve the index.html page"""
    index_path = Path(__file__).parent / "index.html"
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    else:
        return {
            "message": "Parakeet Complete API",
            "version": "4.0.0",
            "features": ["ASR", "Music Analyzer", "Auto Format Conversion"],
            "endpoints": {
                "asr": "/transcribe",
                "music": "/music/*",
                "health": "/health",
                "docs": "/docs"
            }
        }

# Health check
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
        
        mem_info = torch.cuda.mem_get_info(0)
        health_info["gpu_memory_total"] = mem_info[1] / 1024**3
        health_info["gpu_memory_used"] = (mem_info[1] - mem_info[0]) / 1024**3
    
    return health_info

# Main transcription endpoint
@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio/video file to transcribe (any format)"),
    timestamps: Optional[bool] = Form(False, description="Include word-level timestamps"),
    return_segments: Optional[bool] = Form(False, description="Return detailed segments"),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Transcribe audio to text using Parakeet TDT ASR model"""
    if not asr_model:
        raise HTTPException(status_code=503, detail="ASR model not loaded")
    
    logger.info(f"Received file: {file.filename}, content_type: {file.content_type or 'unknown'}")
    
    tmp_file_path = None
    converted_file_path = None
    audio_converted = False
    original_info = {}
    
    try:
        start_time = time.time()
        
        # Save uploaded file
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
        
        # Convert to suitable format
        converted_file_path = tmp_file_path + "_converted.wav"
        processing_file = tmp_file_path
        
        logger.info("Converting audio to mono 16kHz WAV...")
        if convert_audio_for_asr(tmp_file_path, converted_file_path):
            processing_file = converted_file_path
            audio_converted = True
            logger.info("Audio conversion successful")
        else:
            logger.info("Trying pydub conversion...")
            if convert_with_pydub(tmp_file_path, converted_file_path):
                processing_file = converted_file_path
                audio_converted = True
                logger.info("Audio conversion successful with pydub")
            else:
                logger.warning("All conversions failed, attempting with original file")
        
        # Get audio duration
        audio_duration = 0
        try:
            audio_data, sample_rate = sf.read(processing_file)
            audio_duration = len(audio_data) / sample_rate
            logger.info(f"Processing audio: duration={audio_duration:.2f}s, rate={sample_rate}Hz")
        except Exception as e:
            logger.error(f"Error reading converted audio: {e}")
            if audio_info:
                audio_duration = audio_info.get('duration', 0)
        
        # Transcribe
        logger.info("Starting transcription...")
        with torch.cuda.amp.autocast(enabled=device.type == "cuda"):
            transcriptions = asr_model.transcribe([processing_file])
            
            if isinstance(transcriptions, list) and len(transcriptions) > 0:
                if hasattr(transcriptions[0], 'text'):
                    transcription_text = transcriptions[0].text
                else:
                    transcription_text = str(transcriptions[0])
            else:
                transcription_text = str(transcriptions)
            
            segments = None
            if timestamps or return_segments:
                try:
                    hypotheses = asr_model.transcribe([processing_file], return_hypotheses=True)
                    if hypotheses and len(hypotheses) > 0:
                        hypothesis = hypotheses[0]
                        if hasattr(hypothesis, 'word_timestamps'):
                            segments = hypothesis.word_timestamps
                            logger.info("Word timestamps extracted")
                except Exception as e:
                    logger.warning(f"Could not extract timestamps: {e}")
        
        processing_time = time.time() - start_time
        logger.info(f"Transcription completed in {processing_time:.3f}s")
        
        return TranscriptionResponse(
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
        
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    finally:
        for file_path in [tmp_file_path, converted_file_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.unlink(file_path)
                except:
                    pass

# Music Analyzer page
@app.get("/music")
async def music_analyzer():
    """Serve the music analyzer interface"""
    html_path = Path(__file__).parent / "music_analyzer.html"
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    return {"message": "Music Analyzer", "version": "1.0.0"}

# Music upload
@app.post("/music/upload")
async def upload_music(
    file: UploadFile = File(...),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Upload and organize music file"""
    try:
        # Save uploaded file
        suffix = Path(file.filename).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = Path(tmp_file.name)
        
        # Get audio info
        audio_info = get_audio_info(tmp_path)
        if not audio_info:
            os.unlink(tmp_path)
            raise HTTPException(status_code=400, detail="Invalid audio file")
        
        # Detect genre
        genre = detect_genre(file.filename, audio_info)
        
        # Generate unique filename
        file_hash = hashlib.md5(content).hexdigest()[:8]
        safe_filename = f"{file_hash}_{file.filename}".replace(" ", "_")
        dest_path = MUSIC_BASE_DIR / genre / safe_filename
        
        # Move file
        shutil.move(str(tmp_path), str(dest_path))
        
        # Update catalog
        catalog = load_catalog()
        catalog["files"][str(dest_path)] = {
            "filename": file.filename,
            "genre": genre,
            "size": len(content),
            "duration": audio_info.get('duration'),
            "sample_rate": audio_info.get('sample_rate'),
            "channels": audio_info.get('channels'),
            "codec": audio_info.get('codec'),
            "bitrate": audio_info.get('bitrate'),
            "uploaded": datetime.now().isoformat(),
            "hash": file_hash
        }
        catalog["stats"]["total_files"] = len(catalog["files"])
        catalog["stats"]["total_size"] = sum(f.get("size", 0) for f in catalog["files"].values())
        save_catalog(catalog)
        
        return {
            "success": True,
            "file": safe_filename,
            "genre": genre,
            "path": str(dest_path),
            "info": audio_info
        }
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        if 'tmp_path' in locals() and tmp_path.exists():
            os.unlink(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))

# Get catalog
@app.get("/music/catalog")
async def get_catalog(credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    """Get music catalog"""
    catalog = load_catalog()
    return catalog

# Transcribe from catalog
@app.post("/music/transcribe")
async def transcribe_music(
    request: TranscribeRequest,
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Transcribe music file using Parakeet API"""
    try:
        filepath = Path(request.filepath)
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Convert for ASR
        converted_path = filepath.with_suffix('.converted.wav')
        if not convert_audio_for_asr(filepath, converted_path):
            raise HTTPException(status_code=500, detail="Conversion failed")
        
        try:
            # Use internal ASR model
            audio_duration = 0
            try:
                audio_data, sample_rate = sf.read(converted_path)
                audio_duration = len(audio_data) / sample_rate
            except:
                pass
            
            start_time = time.time()
            
            with torch.cuda.amp.autocast(enabled=device.type == "cuda"):
                transcriptions = asr_model.transcribe([str(converted_path)])
                
                if isinstance(transcriptions, list) and len(transcriptions) > 0:
                    if hasattr(transcriptions[0], 'text'):
                        transcription_text = transcriptions[0].text
                    else:
                        transcription_text = str(transcriptions[0])
                else:
                    transcription_text = str(transcriptions)
            
            processing_time = time.time() - start_time
            
            # Update catalog
            catalog = load_catalog()
            if str(filepath) in catalog["files"]:
                catalog["files"][str(filepath)]["transcription"] = transcription_text
                catalog["files"][str(filepath)]["transcribed_at"] = datetime.now().isoformat()
                save_catalog(catalog)
            
            return {
                "text": transcription_text.strip() if transcription_text else "",
                "language": "en",
                "processing_time": processing_time,
                "audio_duration": audio_duration
            }
                
        finally:
            if converted_path.exists():
                os.unlink(converted_path)
                
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Search lyrics
@app.post("/music/search-lyrics")
async def search_lyrics(
    request: LyricsSearchRequest,
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Search for song lyrics online"""
    try:
        filename = request.filename
        clean_name = Path(filename).stem.replace('_', ' ').replace('-', ' ')
        
        # Demo response
        lyrics_found = False
        lyrics_text = ""
        
        if "sample" in filename.lower():
            lyrics_found = True
            lyrics_text = "She had your dark suit in greasy wash water all year\n" \
                         "She had your dark suit in greasy wash water all year"
        
        return {
            "found": lyrics_found,
            "filename": filename,
            "lyrics": lyrics_text,
            "source": "demo" if lyrics_found else None
        }
        
    except Exception as e:
        logger.error(f"Lyrics search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# GPU stats
@app.get("/gpu/stats")
async def gpu_stats(credentials: HTTPBasicCredentials = Depends(verify_credentials)):
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
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "parakeet_api_complete:app",
        host="0.0.0.0",
        port=8000,
        workers=1,
        log_level="info",
        access_log=True
    )