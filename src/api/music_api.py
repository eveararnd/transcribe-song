#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Music Analyzer API - Backend for music upload, organization, transcription and lyrics search
"""

from fastapi import FastAPI, HTTPException, File, UploadFile, Depends, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import os
import json
import shutil
import tempfile
import hashlib
import ffmpeg
import requests
from pathlib import Path
import asyncio
import aiofiles
from datetime import datetime
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Authentication
security = HTTPBasic()
VALID_USERNAME = "parakeet"
VALID_PASSWORD = "Q7+sKsoPWJH5vuulfY+RuQSmUyZj3jBa09Ql5om32hI="

# Directories
MUSIC_BASE_DIR = Path("/home/davegornshtein/parakeet-tdt-deployment/music_library")
GENRES = ["pop", "rock", "hiphop", "electronic", "classical", "jazz", "country", "other"]

# Create directories
for genre in GENRES:
    (MUSIC_BASE_DIR / genre).mkdir(parents=True, exist_ok=True)

# Catalog file
CATALOG_FILE = MUSIC_BASE_DIR / "catalog.json"

class TranscribeRequest(BaseModel):
    filepath: str

class LyricsSearchRequest(BaseModel):
    filename: str

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic credentials"""
    if credentials.username != VALID_USERNAME or credentials.password != VALID_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return credentials

def load_catalog():
    """Load music catalog from JSON file"""
    if CATALOG_FILE.exists():
        with open(CATALOG_FILE, 'r') as f:
            return json.load(f)
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

def convert_for_transcription(input_path, output_path):
    """Convert audio to format suitable for transcription"""
    try:
        stream = ffmpeg.input(str(input_path))
        stream = ffmpeg.output(stream, str(output_path), 
                              acodec='pcm_s16le',
                              ar=16000,
                              ac=1)
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        return True
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        return False

# Create FastAPI app
app = FastAPI(
    title="Music Analyzer API",
    description="Music upload, organization, transcription and lyrics search",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Serve the music analyzer interface"""
    html_path = Path(__file__).parent / "music_analyzer.html"
    if html_path.exists():
        return FileResponse(html_path, media_type="text/html")
    return {"message": "Music Analyzer API", "version": "1.0.0"}

@app.post("/music/upload")
async def upload_music(
    file: UploadFile = File(...),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Upload and organize music file"""
    try:
        # Create temp file
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
        
        # Move file to genre directory
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

@app.get("/music/catalog")
async def get_catalog(credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    """Get music catalog"""
    catalog = load_catalog()
    return catalog

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
        
        # Convert to suitable format
        converted_path = filepath.with_suffix('.converted.wav')
        if not convert_for_transcription(filepath, converted_path):
            raise HTTPException(status_code=500, detail="Conversion failed")
        
        # Call Parakeet API
        try:
            with open(converted_path, 'rb') as f:
                files = {'file': (filepath.name, f, 'audio/wav')}
                response = requests.post(
                    'http://localhost:8000/transcribe',
                    files=files,
                    auth=(VALID_USERNAME, VALID_PASSWORD),
                    timeout=60
                )
            
            if response.status_code == 200:
                result = response.json()
                # Update catalog with transcription
                catalog = load_catalog()
                if str(filepath) in catalog["files"]:
                    catalog["files"][str(filepath)]["transcription"] = result.get("text", "")
                    catalog["files"][str(filepath)]["transcribed_at"] = datetime.now().isoformat()
                    save_catalog(catalog)
                
                return result
            else:
                raise HTTPException(status_code=response.status_code, detail="Transcription failed")
                
        finally:
            # Clean up converted file
            if converted_path.exists():
                os.unlink(converted_path)
                
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/music/search-lyrics")
async def search_lyrics(
    request: LyricsSearchRequest,
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Search for song lyrics online"""
    try:
        # Extract artist and title from filename
        filename = request.filename
        # Remove file extension and common patterns
        clean_name = Path(filename).stem
        clean_name = clean_name.replace('_', ' ').replace('-', ' ')
        
        # Try to identify artist and title
        parts = clean_name.split(' ')
        
        # Simulate lyrics search (in production, use a lyrics API)
        # For demo, return a placeholder
        lyrics_found = False
        lyrics_text = ""
        
        # You could integrate with APIs like:
        # - Genius API
        # - Musixmatch API
        # - LyricsOVH API
        
        # Example placeholder response
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

@app.delete("/music/delete/{file_hash}")
async def delete_music(
    file_hash: str,
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Delete a music file"""
    try:
        catalog = load_catalog()
        
        # Find file by hash
        file_to_delete = None
        for filepath, info in catalog["files"].items():
            if info.get("hash") == file_hash:
                file_to_delete = filepath
                break
        
        if not file_to_delete:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete physical file
        file_path = Path(file_to_delete)
        if file_path.exists():
            os.unlink(file_path)
        
        # Update catalog
        del catalog["files"][file_to_delete]
        catalog["stats"]["total_files"] = len(catalog["files"])
        catalog["stats"]["total_size"] = sum(f.get("size", 0) for f in catalog["files"].values())
        save_catalog(catalog)
        
        return {"success": True, "deleted": file_to_delete}
        
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/music/stats")
async def get_stats(credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    """Get music library statistics"""
    catalog = load_catalog()
    
    # Calculate genre statistics
    genre_stats = {}
    for genre in GENRES:
        genre_files = [f for f in catalog["files"].values() if f.get("genre") == genre]
        genre_stats[genre] = {
            "count": len(genre_files),
            "size": sum(f.get("size", 0) for f in genre_files),
            "duration": sum(f.get("duration", 0) for f in genre_files)
        }
    
    # Calculate transcription stats
    transcribed = sum(1 for f in catalog["files"].values() if f.get("transcription"))
    
    return {
        "total_files": catalog["stats"]["total_files"],
        "total_size": catalog["stats"]["total_size"],
        "total_duration": sum(f.get("duration", 0) for f in catalog["files"].values()),
        "transcribed_count": transcribed,
        "genres": genre_stats,
        "formats": {}  # Could add format statistics
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)