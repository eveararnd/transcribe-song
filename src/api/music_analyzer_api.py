# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Music Analyzer V2 API
"""
import os
import sys
import asyncio
import hashlib
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import time

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query, Body, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from starlette.status import HTTP_401_UNAUTHORIZED
import uvicorn
from pydantic import BaseModel
import numpy as np
import redis.asyncio as redis
from minio import Minio
from minio.error import S3Error
import ffmpeg
import tempfile
import aiofiles
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession

# Import our modules
from src.config.music_analyzer_config import (
    DATABASE_URL, REDIS_CONFIG, MINIO_CONFIG, 
    STORAGE_PATHS, MODEL_CONFIG, API_CONFIG,
    GENRE_KEYWORDS, FAISS_CONFIG, SEARCH_API_CONFIG
)
from src.models.music_analyzer_models import (
    DatabaseManager, MusicFile, Transcription, 
    Lyrics, SearchHistory, APIConfig
)
from src.managers.faiss_manager import get_faiss_manager, FAISSManager
from src.managers.lyrics_search_manager import get_lyrics_manager, LyricsSearchManager
from src.utils.lyrics_search_enhanced import get_enhanced_lyrics_manager, EnhancedLyricsSearchManager
from src.models.gemma_manager import get_gemma_manager, GemmaManager
from src.models.multi_model_manager import get_multi_model_manager, MultiModelManager

# Import existing Parakeet modules
import nemo.collections.asr as nemo_asr
import torch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security
security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    """Verify HTTP Basic Auth credentials"""
    correct_username = "parakeet"
    correct_password = "Q7+vD#8kN$2pL@9"
    
    if credentials.username != correct_username or credentials.password != correct_password:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Pydantic models
class TranscriptionRequest(BaseModel):
    file_id: str
    timestamps: bool = False
    return_segments: bool = False

class TranscriptionResponse(BaseModel):
    file_id: str
    text: str
    confidence: Optional[float] = None
    processing_time: float
    audio_duration: float
    model_version: str = "parakeet-tdt-0.6b-v2"
    segments: Optional[List[Dict]] = None

class LyricsSearchRequest(BaseModel):
    file_id: str
    source: str = "brave"  # brave or tavily

class VectorSearchRequest(BaseModel):
    query: str
    k: int = 10
    filter_genre: Optional[str] = None
    filter_artist: Optional[str] = None

class SimilarSongsRequest(BaseModel):
    file_id: str
    k: int = 10

class StorageStatsResponse(BaseModel):
    original_files: Dict[str, Any]
    converted_files: Dict[str, Any]
    cache_files: Dict[str, Any]
    database_size: int
    faiss_index_size: int
    total_used: int
    available_space: int

class FileListRequest(BaseModel):
    page: int = 1
    per_page: int = 50
    sort_by: str = "uploaded_at"
    sort_order: str = "desc"
    filters: Optional[Dict] = None
    search_query: Optional[str] = None

# Global instances
db_manager = DatabaseManager(DATABASE_URL)
redis_client: Optional[redis.Redis] = None
minio_client: Optional[Minio] = None
asr_model = None
faiss_manager: Optional[FAISSManager] = None
lyrics_manager: Optional[LyricsSearchManager] = None
enhanced_lyrics_manager: Optional[EnhancedLyricsSearchManager] = None
gemma_manager: Optional[GemmaManager] = None
multi_model_manager: Optional[MultiModelManager] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Music Analyzer API...")
    
    # Initialize database
    await db_manager.initialize()
    logger.info("Database initialized")
    
    # Initialize Redis
    global redis_client
    redis_client = redis.Redis(**REDIS_CONFIG)
    await redis_client.ping()
    logger.info("Redis connected")
    
    # Initialize MinIO
    global minio_client
    minio_client = Minio(
        MINIO_CONFIG["endpoint"],
        access_key=MINIO_CONFIG["access_key"],
        secret_key=MINIO_CONFIG["secret_key"],
        secure=MINIO_CONFIG["secure"]
    )
    
    # Create bucket if not exists
    try:
        if not minio_client.bucket_exists(MINIO_CONFIG["bucket_name"]):
            minio_client.make_bucket(MINIO_CONFIG["bucket_name"])
            logger.info(f"Created MinIO bucket: {MINIO_CONFIG['bucket_name']}")
    except Exception as e:
        logger.error(f"MinIO error: {e}")
    
    # Load ASR model
    global asr_model
    try:
        if os.path.exists(MODEL_CONFIG["parakeet_model_path"]):
            asr_model = nemo_asr.models.ASRModel.restore_from(MODEL_CONFIG["parakeet_model_path"])
            if torch.cuda.is_available():
                asr_model = asr_model.cuda()
            asr_model.eval()
            logger.info("Parakeet ASR model loaded")
        else:
            logger.warning(f"ASR model not found at {MODEL_CONFIG['parakeet_model_path']}")
    except Exception as e:
        logger.error(f"Error loading ASR model: {e}")
    
    # Initialize FAISS manager
    global faiss_manager
    faiss_manager = get_faiss_manager()
    logger.info("FAISS manager initialized")
    
    # Initialize Lyrics manager
    global lyrics_manager
    lyrics_manager = get_lyrics_manager()
    logger.info("Lyrics manager initialized")
    
    # Initialize Enhanced Lyrics manager
    global enhanced_lyrics_manager
    enhanced_lyrics_manager = get_enhanced_lyrics_manager()
    logger.info("Enhanced lyrics manager initialized")
    
    # Initialize Gemma manager
    global gemma_manager
    try:
        gemma_manager = get_gemma_manager()
        logger.info("Gemma manager initialized")
        # Load model asynchronously
        asyncio.create_task(enhanced_lyrics_manager.initialize_gemma())
    except Exception as e:
        logger.warning(f"Gemma initialization failed: {e}")
    
    # Initialize Multi-Model manager
    global multi_model_manager
    try:
        multi_model_manager = get_multi_model_manager()
        logger.info("Multi-model manager initialized")
    except Exception as e:
        logger.warning(f"Multi-model initialization failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Music Analyzer API...")
    await redis_client.close()
    await db_manager.close()
    
    # Save FAISS index
    if faiss_manager:
        await asyncio.to_thread(faiss_manager.save_index)

# Create FastAPI app
app = FastAPI(
    title="Music Analyzer V2 API",
    description="Advanced music analysis with ASR, vector search, and lyrics integration",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware for external access
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://35.232.20.248", "http://localhost:3000"],  # Add your frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent.parent / "music-analyzer-frontend" / "build"
if static_path.exists():
    app.mount("/assets", StaticFiles(directory=str(static_path / "assets")), name="assets")
    
    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        """Serve the React frontend"""
        index_file = static_path / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        else:
            return HTMLResponse("<h1>Frontend not built. Run 'npm run build' in music-analyzer-frontend directory.</h1>")

# Utility functions
def get_file_hash(file_content: bytes) -> str:
    """Calculate SHA256 hash of file content"""
    return hashlib.sha256(file_content).hexdigest()

def detect_genre(filename: str) -> str:
    """Simple keyword-based genre detection"""
    filename_lower = filename.lower()
    for genre, keywords in GENRE_KEYWORDS.items():
        if any(keyword in filename_lower for keyword in keywords):
            return genre
    return "other"

async def convert_audio_for_asr(input_path: Path, output_path: Path):
    """Convert any audio format to mono 16kHz WAV using ffmpeg"""
    try:
        stream = ffmpeg.input(str(input_path))
        stream = ffmpeg.output(
            stream, 
            str(output_path), 
            acodec='pcm_s16le', 
            ar=16000, 
            ac=1,
            loglevel='error'
        )
        ffmpeg.run(stream, overwrite_output=True)
        return True
    except Exception as e:
        logger.error(f"FFmpeg conversion error: {e}")
        return False

def get_audio_metadata(file_path: Path) -> Dict[str, Any]:
    """Extract audio metadata using ffmpeg"""
    try:
        probe = ffmpeg.probe(str(file_path))
        audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
        
        if audio_stream:
            return {
                'duration': float(probe['format'].get('duration', 0)),
                'sample_rate': int(audio_stream.get('sample_rate', 0)),
                'channels': int(audio_stream.get('channels', 0)),
                'codec': audio_stream.get('codec_name', 'unknown'),
                'bitrate': int(probe['format'].get('bit_rate', 0))
            }
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
    
    return {'duration': 0, 'sample_rate': 0, 'channels': 0, 'codec': 'unknown'}

# API Endpoints
@app.get("/api")
async def api_root():
    """API root endpoint - returns API information"""
    return {
        "name": "Music Analyzer V2 API",
        "version": "2.0.0",
        "status": "operational",
        "endpoints": {
            "upload": "/api/v2/upload",
            "catalog": "/api/v2/catalog",
            "transcribe": "/api/v2/transcribe",
            "search_lyrics": "/api/v2/search-lyrics",
            "storage_stats": "/api/v2/storage/stats",
            "file_list": "/api/v2/files",
            "health": "/api/v2/health"
        }
    }

@app.get("/api/v2/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": False,
            "redis": False,
            "minio": False,
            "asr_model": asr_model is not None
        }
    }
    
    # Check database
    try:
        async for session in db_manager.get_session():
            await session.execute(select(1))
            health_status["services"]["database"] = True
    except:
        pass
    
    # Check Redis
    try:
        await redis_client.ping()
        health_status["services"]["redis"] = True
    except:
        pass
    
    # Check MinIO
    try:
        minio_client.list_buckets()
        health_status["services"]["minio"] = True
    except:
        pass
    
    # Overall health
    health_status["healthy"] = all(health_status["services"].values())
    
    return health_status

@app.post("/api/v2/upload")
async def upload_file(
    file: UploadFile = File(...),
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Upload a music file"""
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in API_CONFIG["supported_audio_formats"]:
        raise HTTPException(400, f"Unsupported format: {file_ext}")
    
    # Read file content
    content = await file.read()
    file_hash = get_file_hash(content)
    
    # Check if file already exists
    existing = await db.execute(
        select(MusicFile).where(MusicFile.file_hash == file_hash)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "File already exists")
    
    # Detect genre
    genre = detect_genre(file.filename)
    
    # Save to storage
    file_id = str(uuid.uuid4())
    storage_dir = STORAGE_PATHS["original"] / genre
    storage_dir.mkdir(exist_ok=True)
    
    storage_path = storage_dir / f"{file_id}_{file.filename}"
    
    async with aiofiles.open(storage_path, 'wb') as f:
        await f.write(content)
    
    # Extract metadata
    metadata = get_audio_metadata(storage_path)
    
    # Save to database
    music_file = MusicFile(
        id=file_id,
        original_filename=file.filename,
        storage_path=str(storage_path),
        file_hash=file_hash,
        file_size=len(content),
        duration=metadata['duration'],
        sample_rate=metadata['sample_rate'],
        channels=metadata['channels'],
        codec=metadata['codec'],
        genre=genre,
        file_metadata=metadata
    )
    
    db.add(music_file)
    await db.commit()
    
    # Upload to MinIO
    try:
        minio_client.put_object(
            MINIO_CONFIG["bucket_name"],
            f"original/{genre}/{file_id}_{file.filename}",
            data=content,
            length=len(content),
            content_type=f"audio/{file_ext[1:]}"
        )
    except Exception as e:
        logger.error(f"MinIO upload error: {e}")
    
    return {
        "file_id": file_id,
        "filename": file.filename,
        "genre": genre,
        "size": len(content),
        "duration": metadata['duration'],
        "hash": file_hash
    }

@app.post("/api/v2/transcribe", response_model=TranscriptionResponse)
async def transcribe_file(
    request: TranscriptionRequest,
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Transcribe a music file"""
    if not asr_model:
        raise HTTPException(503, "ASR model not available")
    
    # Get file from database
    result = await db.execute(
        select(MusicFile).where(MusicFile.id == request.file_id)
    )
    music_file = result.scalar_one_or_none()
    
    if not music_file:
        raise HTTPException(404, "File not found")
    
    # Check cache
    cache_key = f"transcription:{music_file.file_hash}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # Convert to suitable format
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        tmp_path = Path(tmp.name)
    
    try:
        if not await convert_audio_for_asr(Path(music_file.storage_path), tmp_path):
            raise HTTPException(500, "Audio conversion failed")
        
        # Transcribe
        start_time = time.time()
        
        with torch.no_grad():
            transcription = asr_model.transcribe([str(tmp_path)])
        
        processing_time = time.time() - start_time
        
        # Save to database
        trans_record = Transcription(
            file_id=music_file.id,
            transcription_text=transcription[0] if transcription else "",
            processing_time=processing_time,
            model_version="parakeet-tdt-0.6b-v2"
        )
        db.add(trans_record)
        await db.commit()
        await db.refresh(trans_record)
        
        # Index in FAISS
        if faiss_manager and transcription and transcription[0]:
            metadata = {
                "filename": music_file.original_filename,
                "genre": music_file.genre,
                "duration": music_file.duration,
                "uploaded_at": music_file.uploaded_at.isoformat()
            }
            await faiss_manager.add_transcription(
                file_id=str(music_file.id),
                transcription_id=str(trans_record.id),
                text=transcription[0],
                metadata=metadata
            )
        
        # Create response
        response = TranscriptionResponse(
            file_id=request.file_id,
            text=transcription[0] if transcription else "",
            processing_time=processing_time,
            audio_duration=music_file.duration,
            model_version="parakeet-tdt-0.6b-v2"
        )
        
        # Cache result
        await redis_client.setex(
            cache_key,
            86400,  # 24 hours
            response.model_dump_json()
        )
        
        return response
        
    finally:
        # Cleanup
        if tmp_path.exists():
            tmp_path.unlink()

@app.get("/api/v2/catalog")
async def get_catalog(
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Get music catalog with statistics"""
    # Get all files
    result = await db.execute(select(MusicFile))
    files = result.scalars().all()
    
    # Build catalog
    catalog = {
        "files": {},
        "stats": {
            "total_files": len(files),
            "total_size": 0,
            "by_genre": {},
            "by_format": {}
        }
    }
    
    for file in files:
        catalog["files"][str(file.id)] = {
            "filename": file.original_filename,
            "genre": file.genre,
            "size": file.file_size,
            "duration": file.duration,
            "sample_rate": file.sample_rate,
            "channels": file.channels,
            "codec": file.codec,
            "uploaded": file.uploaded_at.isoformat(),
            "hash": file.file_hash
        }
        
        # Update stats
        catalog["stats"]["total_size"] += file.file_size or 0
        
        # Genre stats
        if file.genre not in catalog["stats"]["by_genre"]:
            catalog["stats"]["by_genre"][file.genre] = {"count": 0, "size": 0}
        catalog["stats"]["by_genre"][file.genre]["count"] += 1
        catalog["stats"]["by_genre"][file.genre]["size"] += file.file_size or 0
        
        # Format stats
        ext = Path(file.original_filename).suffix.lower()
        if ext not in catalog["stats"]["by_format"]:
            catalog["stats"]["by_format"][ext] = {"count": 0, "size": 0}
        catalog["stats"]["by_format"][ext]["count"] += 1
        catalog["stats"]["by_format"][ext]["size"] += file.file_size or 0
    
    return catalog

@app.post("/api/v2/search/vector")
async def search_by_vector(
    request: VectorSearchRequest,
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Search for music using vector similarity"""
    if not faiss_manager:
        raise HTTPException(503, "Vector search not available")
    
    # Build filter metadata
    filter_metadata = {}
    if request.filter_genre:
        filter_metadata["genre"] = request.filter_genre
    if request.filter_artist:
        filter_metadata["artist"] = request.filter_artist
    
    # Search
    results = await faiss_manager.search(
        query=request.query,
        k=request.k,
        filter_metadata=filter_metadata if filter_metadata else None
    )
    
    # Enrich results with file info
    enriched_results = []
    for result in results:
        file_result = await db.execute(
            select(MusicFile).where(MusicFile.id == result["file_id"])
        )
        file = file_result.scalar_one_or_none()
        
        if file:
            enriched_results.append({
                **result,
                "filename": file.original_filename,
                "genre": file.genre,
                "duration": file.duration,
                "uploaded_at": file.uploaded_at.isoformat()
            })
    
    # Save search history
    search_record = SearchHistory(
        search_type="vector",
        query=request.query,
        results_count=len(enriched_results),
        parameters=request.model_dump()
    )
    db.add(search_record)
    await db.commit()
    
    return {
        "query": request.query,
        "results": enriched_results,
        "total": len(enriched_results)
    }

@app.post("/api/v2/search/similar")
async def find_similar_songs(
    request: SimilarSongsRequest,
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Find songs similar to a given file"""
    if not faiss_manager:
        raise HTTPException(503, "Vector search not available")
    
    # Check if file exists
    file_result = await db.execute(
        select(MusicFile).where(MusicFile.id == request.file_id)
    )
    file = file_result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(404, "File not found")
    
    # Find similar songs
    results = await faiss_manager.find_similar_songs(request.file_id, request.k)
    
    # Filter out the source file and enrich results
    enriched_results = []
    for result in results:
        if result["file_id"] == request.file_id:
            continue
            
        file_result = await db.execute(
            select(MusicFile).where(MusicFile.id == result["file_id"])
        )
        similar_file = file_result.scalar_one_or_none()
        
        if similar_file:
            enriched_results.append({
                **result,
                "filename": similar_file.original_filename,
                "genre": similar_file.genre,
                "duration": similar_file.duration,
                "uploaded_at": similar_file.uploaded_at.isoformat()
            })
    
    return {
        "source_file": {
            "file_id": request.file_id,
            "filename": file.original_filename,
            "genre": file.genre
        },
        "similar_songs": enriched_results,
        "total": len(enriched_results)
    }

@app.get("/api/v2/search/stats")
async def get_search_stats(
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Get FAISS index statistics"""
    if not faiss_manager:
        raise HTTPException(503, "Vector search not available")
    
    stats = await faiss_manager.get_statistics()
    return stats

@app.post("/api/v2/search/lyrics")
async def search_lyrics(
    request: LyricsSearchRequest,
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Search for lyrics using Brave or Tavily APIs"""
    if not lyrics_manager:
        raise HTTPException(503, "Lyrics search not available")
    
    # Get file from database
    file_result = await db.execute(
        select(MusicFile).where(MusicFile.id == request.file_id)
    )
    file = file_result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(404, "File not found")
    
    # Extract artist and title from filename
    # This is a simple extraction - in production you'd want better metadata
    filename = file.original_filename
    # Remove file extension
    name_parts = filename.rsplit('.', 1)[0]
    # Remove hash prefix if present
    if '_' in name_parts:
        name_parts = name_parts.split('_', 1)[1]
    
    # Simple heuristic: assume format is "Artist - Title" or just "Title"
    if ' - ' in name_parts:
        artist, title = name_parts.split(' - ', 1)
    else:
        artist = "Unknown Artist"
        title = name_parts
    
    # Search for lyrics
    results = await lyrics_manager.search_lyrics(
        artist=artist.strip(),
        title=title.strip(),
        source=request.source
    )
    
    # Save to database if we found lyrics
    if results.get("results"):
        lyrics_record = Lyrics(
            file_id=file.id,
            source=results.get("best_source", request.source),
            lyrics_text=results["results"].get(results.get("best_source", ""), {}).get("full_content", ""),
            lyrics_url=results["results"].get(results.get("best_source", ""), {}).get("url", ""),
            confidence_score=results["results"].get(results.get("best_source", ""), {}).get("confidence", 0)
        )
        db.add(lyrics_record)
        await db.commit()
    
    # Save search history
    search_record = SearchHistory(
        search_type="lyrics",
        query=f"{artist} - {title}",
        results_count=len(results.get("results", {})),
        parameters={"file_id": request.file_id, "source": request.source}
    )
    db.add(search_record)
    await db.commit()
    
    return {
        "file_id": request.file_id,
        "filename": file.original_filename,
        "artist": artist,
        "title": title,
        "search_results": results
    }

@app.post("/api/v2/search/lyrics-intelligent")
async def search_lyrics_intelligent(
    request: LyricsSearchRequest,
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Search for lyrics using Gemma-powered intelligent search"""
    if not enhanced_lyrics_manager:
        raise HTTPException(503, "Enhanced lyrics search not available")
    
    # Get file from database
    file_result = await db.execute(
        select(MusicFile).where(MusicFile.id == request.file_id)
    )
    file = file_result.scalar_one_or_none()
    
    if not file:
        raise HTTPException(404, "File not found")
    
    # Get transcription if available
    trans_result = await db.execute(
        select(Transcription).where(Transcription.file_id == request.file_id)
    )
    transcription = trans_result.scalar_one_or_none()
    
    # Extract artist and title
    filename = file.original_filename
    name_parts = filename.rsplit('.', 1)[0]
    if '_' in name_parts:
        name_parts = name_parts.split('_', 1)[1]
    
    if ' - ' in name_parts:
        artist, title = name_parts.split(' - ', 1)
    else:
        artist = "Unknown Artist"
        title = name_parts
    
    # Perform intelligent search
    results = await enhanced_lyrics_manager.search_lyrics_intelligent(
        artist=artist.strip(),
        title=title.strip(),
        transcribed_text=transcription.transcription_text if transcription else None
    )
    
    # Save best result to database
    if results.get("results") and results.get("best_source"):
        best_result = results["results"][results["best_source"]]
        lyrics_record = Lyrics(
            file_id=file.id,
            source=f"intelligent_{results['best_source']}",
            lyrics_text=best_result.get("full_content", best_result.get("lyrics", "")),
            lyrics_url=best_result.get("url", ""),
            confidence_score=best_result.get("confidence", 0)
        )
        db.add(lyrics_record)
        await db.commit()
    
    # Save search history
    search_record = SearchHistory(
        search_type="lyrics_intelligent",
        query=f"{artist} - {title}",
        results_count=len(results.get("results", {})),
        parameters={
            "file_id": request.file_id,
            "strategy": "gemma_intelligent",
            "best_source": results.get("best_source")
        }
    )
    db.add(search_record)
    await db.commit()
    
    return {
        "file_id": request.file_id,
        "filename": file.original_filename,
        "artist": artist,
        "title": title,
        "search_results": results,
        "gemma_available": enhanced_lyrics_manager.gemma_loaded
    }

@app.post("/api/v2/analyze/lyrics")
async def analyze_lyrics(
    request: TranscriptionRequest,
    credentials: HTTPBasicCredentials = Depends(verify_credentials),
    db: AsyncSession = Depends(db_manager.get_session)
):
    """Analyze lyrics using Gemma model"""
    if not gemma_manager:
        raise HTTPException(503, "Gemma model not available")
    
    # Get transcription
    trans_result = await db.execute(
        select(Transcription).where(Transcription.file_id == request.file_id)
    )
    transcription = trans_result.scalar_one_or_none()
    
    if not transcription or not transcription.transcription_text:
        raise HTTPException(404, "No transcription found for this file")
    
    # Get file metadata
    file_result = await db.execute(
        select(MusicFile).where(MusicFile.id == request.file_id)
    )
    file = file_result.scalar_one_or_none()
    
    # Perform comprehensive analysis
    analysis_results = {}
    
    # 1. Summary
    analysis_results["summary"] = await gemma_manager.analyze_lyrics(
        transcription.transcription_text, "summary"
    )
    
    # 2. Mood analysis
    analysis_results["mood"] = await gemma_manager.analyze_lyrics(
        transcription.transcription_text, "mood"
    )
    
    # 3. Theme extraction
    analysis_results["themes"] = await gemma_manager.analyze_lyrics(
        transcription.transcription_text, "theme"
    )
    
    # 4. Genre suggestion
    analysis_results["genre"] = await gemma_manager.analyze_lyrics(
        transcription.transcription_text, "genre"
    )
    
    # 5. Generate insights
    metadata = {
        "title": file.original_filename.rsplit('.', 1)[0],
        "genre": file.genre,
        "duration": file.duration
    }
    
    insights = await gemma_manager.generate_song_insights(
        transcription.transcription_text, metadata
    )
    analysis_results["insights"] = insights
    
    return {
        "file_id": request.file_id,
        "filename": file.original_filename,
        "transcription_length": len(transcription.transcription_text),
        "analysis": analysis_results,
        "model_info": gemma_manager.get_model_info()
    }

@app.get("/api/v2/gemma/status")
async def get_gemma_status(
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Get Gemma model status"""
    status = {
        "gemma_available": gemma_manager is not None,
        "enhanced_lyrics_available": enhanced_lyrics_manager is not None,
        "gemma_loaded_for_lyrics": enhanced_lyrics_manager.gemma_loaded if enhanced_lyrics_manager else False
    }
    
    if gemma_manager:
        status["model_info"] = gemma_manager.get_model_info()
    
    return status

@app.get("/api/v2/models/status")
async def get_models_status(
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Get status of all available models"""
    if not multi_model_manager:
        raise HTTPException(503, "Multi-model manager not available")
    
    return multi_model_manager.get_status()

@app.post("/api/v2/models/load")
async def load_model(
    model_type: str = Body(..., embed=True),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Load a specific model"""
    if not multi_model_manager:
        raise HTTPException(503, "Multi-model manager not available")
    
    valid_models = ["gemma-3-12b", "phi-4-multimodal", "phi-4-reasoning"]
    if model_type not in valid_models:
        raise HTTPException(400, f"Invalid model type. Must be one of: {valid_models}")
    
    try:
        success = await multi_model_manager.load_model(model_type)
        if success:
            return {"status": "success", "message": f"{model_type} loaded successfully"}
        else:
            raise HTTPException(500, f"Failed to load {model_type}")
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/api/v2/models/unload")
async def unload_model(
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Unload the current model"""
    if not multi_model_manager:
        raise HTTPException(503, "Multi-model manager not available")
    
    await multi_model_manager.unload_current_model()
    return {"status": "success", "message": "Model unloaded"}

@app.post("/api/v2/models/generate")
async def generate_with_model(
    prompt: str = Body(..., embed=True),
    max_length: int = Body(200, embed=True),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Generate text using the currently loaded model"""
    if not multi_model_manager:
        raise HTTPException(503, "Multi-model manager not available")
    
    if not multi_model_manager.current_model:
        raise HTTPException(400, "No model loaded")
    
    try:
        response = await multi_model_manager.generate_text(prompt, max_length)
        return {
            "model": multi_model_manager.current_model,
            "prompt": prompt,
            "response": response,
            "max_length": max_length
        }
    except Exception as e:
        raise HTTPException(500, str(e))

# Export endpoints
@app.get("/api/v2/export/{file_id}")
async def export_file(
    file_id: str,
    format: str = Query("json", description="Export format: json, csv, xlsx, zip, tar.gz, mono_tar.gz"),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Export music file data in various formats"""
    from src.utils.music_analyzer_export import get_exporter
    from fastapi.responses import Response
    
    exporter = get_exporter()
    
    if format not in exporter.supported_formats:
        raise HTTPException(400, f"Unsupported format. Choose from: {exporter.supported_formats}")
    
    try:
        export_data = await exporter.export_music_file(file_id, format)
        
        # Set appropriate content type
        content_type = export_data.get('content_type', 'application/octet-stream')
        if format == 'json':
            content_type = 'application/json'
        elif format == 'csv':
            content_type = 'text/csv'
        
        return Response(
            content=export_data['content'] if isinstance(export_data['content'], bytes) else export_data['content'].encode(),
            media_type=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{export_data["filename"]}"'
            }
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")

@app.post("/api/v2/export/batch")
async def export_batch(
    file_ids: List[str] = Body(..., description="List of file IDs to export"),
    format: str = Body("json", description="Export format: json, csv, xlsx, tar.gz, mono_tar.gz"),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Export multiple music files"""
    from src.utils.music_analyzer_export import get_exporter
    from fastapi.responses import Response
    
    exporter = get_exporter()
    
    if not file_ids:
        raise HTTPException(400, "No file IDs provided")
    
    if len(file_ids) > 100:
        raise HTTPException(400, "Maximum 100 files can be exported at once")
    
    try:
        export_data = await exporter.export_batch(file_ids, format)
        
        return Response(
            content=export_data['content'] if isinstance(export_data['content'], bytes) else export_data['content'].encode(),
            media_type=export_data.get('content_type', 'application/octet-stream'),
            headers={
                'Content-Disposition': f'attachment; filename="{export_data["filename"]}"'
            }
        )
    except Exception as e:
        raise HTTPException(500, f"Batch export failed: {str(e)}")

@app.get("/api/v2/export/search/{search_id}")
async def export_search_history(
    search_id: str,
    format: str = Query("json", description="Export format: json, csv, xlsx"),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Export search results"""
    from src.utils.music_analyzer_export import get_exporter
    from fastapi.responses import Response
    
    exporter = get_exporter()
    
    try:
        export_data = await exporter.export_search_history(search_id, format)
        
        content_type = 'application/json' if format == 'json' else export_data.get('content_type', 'application/octet-stream')
        
        return Response(
            content=export_data['content'] if isinstance(export_data['content'], bytes) else export_data['content'].encode(),
            media_type=content_type,
            headers={
                'Content-Disposition': f'attachment; filename="{export_data["filename"]}"'
            }
        )
    except ValueError as e:
        raise HTTPException(404, str(e))
    except Exception as e:
        raise HTTPException(500, f"Export failed: {str(e)}")

# File listing endpoint
@app.get("/api/v2/files")
async def list_files(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(db_manager.get_session),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """List uploaded files with pagination"""
    # Auth already verified by Depends
    
    try:
        # Count total files
        count_query = select(func.count(MusicFile.id))
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get files with pagination - eager load relationships
        from sqlalchemy.orm import selectinload
        query = (
            select(MusicFile)
            .options(selectinload(MusicFile.transcriptions))
            .offset(offset)
            .limit(limit)
            .order_by(MusicFile.uploaded_at.desc())
        )
        result = await db.execute(query)
        files = result.scalars().all()
        
        return {
            "files": [
                {
                    "id": str(file.id),
                    "filename": file.original_filename,
                    "artist": file.file_metadata.get("artist", "Unknown") if file.file_metadata else "Unknown",
                    "title": file.file_metadata.get("title", file.original_filename) if file.file_metadata else file.original_filename,
                    "genre": file.genre or "Unknown",
                    "duration": file.duration,
                    "file_size": file.file_size,
                    "transcribed": len(file.transcriptions) > 0 if file.transcriptions else False,
                    "created_at": file.uploaded_at.isoformat() if file.uploaded_at else None
                }
                for file in files
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(500, f"Failed to list files: {str(e)}")

# Storage statistics endpoint
@app.get("/api/v2/storage/stats")
async def get_storage_stats(
    db: AsyncSession = Depends(db_manager.get_session),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Get storage statistics"""
    # Auth already verified by Depends
    
    try:
        # Get file count and total size
        stats_query = select(
            func.count(MusicFile.id).label('total_files'),
            func.sum(MusicFile.file_size).label('total_size')
        )
        result = await db.execute(stats_query)
        stats = result.first()
        
        # Get genre distribution
        genre_query = select(
            MusicFile.genre,
            func.count(MusicFile.id).label('count')
        ).group_by(MusicFile.genre)
        genre_result = await db.execute(genre_query)
        genres = {row.genre or 'unknown': row.count for row in genre_result}
        
        # Get transcription stats
        transcribed_query = select(func.count(func.distinct(Transcription.file_id)))
        transcribed_result = await db.execute(transcribed_query)
        transcribed_count = transcribed_result.scalar()
        
        return {
            "total_files": stats.total_files or 0,
            "total_size": stats.total_size or 0,
            "total_size_mb": round((stats.total_size or 0) / (1024 * 1024), 2),
            "transcribed_files": transcribed_count or 0,
            "genre_distribution": genres,
            "storage_usage": {
                "used_mb": round((stats.total_size or 0) / (1024 * 1024), 2),
                "limit_mb": 10000  # 10GB limit
            }
        }
    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        raise HTTPException(500, f"Failed to get storage stats: {str(e)}")

# Get single file endpoint
@app.get("/api/v2/files/{file_id}")
async def get_file(
    file_id: str,
    db: AsyncSession = Depends(db_manager.get_session),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Get details for a single file"""
    try:
        # Get file with all relationships
        from sqlalchemy.orm import selectinload
        query = (
            select(MusicFile)
            .options(
                selectinload(MusicFile.transcriptions),
                selectinload(MusicFile.lyrics)
            )
            .where(MusicFile.id == file_id)
        )
        result = await db.execute(query)
        file = result.scalar_one_or_none()
        
        if not file:
            raise HTTPException(404, f"File not found: {file_id}")
        
        # Build response
        response = {
            "id": str(file.id),
            "filename": file.original_filename,
            "storage_path": file.storage_path,
            "file_hash": file.file_hash,
            "file_size": file.file_size,
            "duration": file.duration,
            "sample_rate": file.sample_rate,
            "channels": file.channels,
            "codec": file.codec,
            "genre": file.genre,
            "uploaded_at": file.uploaded_at.isoformat() if file.uploaded_at else None,
            "metadata": file.file_metadata or {},
            "transcriptions": [
                {
                    "id": str(t.id),
                    "text": t.transcription_text,
                    "confidence": t.confidence,
                    "processing_time": t.processing_time,
                    "model_version": t.model_version,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "segments": t.segments or []
                }
                for t in file.transcriptions
            ] if file.transcriptions else [],
            "lyrics": [
                {
                    "id": str(l.id),
                    "source": l.source,
                    "lyrics_text": l.lyrics_text,
                    "confidence": l.confidence,
                    "metadata": l.metadata or {},
                    "created_at": l.created_at.isoformat() if l.created_at else None
                }
                for l in file.lyrics
            ] if file.lyrics else []
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting file {file_id}: {e}")
        raise HTTPException(500, f"Failed to get file details: {str(e)}")

# Delete file endpoint
@app.delete("/api/v2/files/{file_id}")
async def delete_file(
    file_id: str,
    db: AsyncSession = Depends(db_manager.get_session),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Delete a music file and all associated data"""
    try:
        # Get the file first
        result = await db.execute(select(MusicFile).where(MusicFile.id == file_id))
        file = result.scalar_one_or_none()
        
        if not file:
            raise HTTPException(404, f"File not found: {file_id}")
        
        # Delete from MinIO/storage
        try:
            if file.storage_path:
                # Try to delete from MinIO
                if minio_client:
                    bucket_name = MINIO_CONFIG["bucket_name"]
                    object_name = file.storage_path.replace(f"{bucket_name}/", "")
                    await asyncio.to_thread(minio_client.remove_object, bucket_name, object_name)
                    logger.info(f"Deleted from MinIO: {object_name}")
                
                # Also try to delete from local storage if it exists
                local_paths = [
                    STORAGE_PATHS["original"] / file.storage_path,
                    STORAGE_PATHS["converted"] / file.storage_path.replace(".mp3", ".wav"),
                ]
                for path in local_paths:
                    if path.exists():
                        path.unlink()
                        logger.info(f"Deleted local file: {path}")
        except Exception as e:
            logger.warning(f"Failed to delete storage files: {e}")
            # Continue with database deletion even if storage deletion fails
        
        # Delete from FAISS index if exists
        if faiss_manager and file.transcriptions:
            for transcription in file.transcriptions:
                try:
                    await asyncio.to_thread(faiss_manager.remove_from_index, str(transcription.id))
                except Exception as e:
                    logger.warning(f"Failed to remove from FAISS: {e}")
        
        # Delete from database (cascades to transcriptions, lyrics, etc.)
        await db.delete(file)
        await db.commit()
        
        logger.info(f"Deleted file {file_id}: {file.original_filename}")
        
        return {
            "message": f"File '{file.original_filename}' deleted successfully",
            "file_id": file_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        await db.rollback()
        raise HTTPException(500, f"Failed to delete file: {str(e)}")

# Batch delete endpoint
@app.post("/api/v2/files/batch/delete")
async def batch_delete_files(
    file_ids: List[str] = Body(..., embed=True),
    db: AsyncSession = Depends(db_manager.get_session),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Delete multiple music files and all associated data"""
    deleted_files = []
    failed_files = []
    
    for file_id in file_ids:
        try:
            # Get the file first
            result = await db.execute(select(MusicFile).where(MusicFile.id == file_id))
            file = result.scalar_one_or_none()
            
            if not file:
                failed_files.append({"file_id": file_id, "error": "File not found"})
                continue
            
            # Delete from MinIO/storage
            try:
                if file.storage_path:
                    if minio_client:
                        bucket_name = MINIO_CONFIG["bucket_name"]
                        object_name = file.storage_path.replace(f"{bucket_name}/", "")
                        await asyncio.to_thread(minio_client.remove_object, bucket_name, object_name)
                    
                    # Also try to delete from local storage
                    local_paths = [
                        STORAGE_PATHS["original"] / file.storage_path,
                        STORAGE_PATHS["converted"] / file.storage_path.replace(".mp3", ".wav"),
                    ]
                    for path in local_paths:
                        if path.exists():
                            path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete storage files for {file_id}: {e}")
            
            # Delete from FAISS index if exists
            if faiss_manager and file.transcriptions:
                for transcription in file.transcriptions:
                    try:
                        await asyncio.to_thread(faiss_manager.remove_from_index, str(transcription.id))
                    except Exception as e:
                        logger.warning(f"Failed to remove from FAISS: {e}")
            
            # Delete from database
            await db.delete(file)
            deleted_files.append({"file_id": file_id, "filename": file.original_filename})
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            failed_files.append({"file_id": file_id, "error": str(e)})
    
    # Commit all deletions
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Failed to commit deletions: {str(e)}")
    
    return {
        "deleted": deleted_files,
        "failed": failed_files,
        "total_deleted": len(deleted_files),
        "total_failed": len(failed_files)
    }

# Batch export endpoint
@app.post("/api/v2/files/batch/export")
async def batch_export_files(
    request: dict = Body(...),
    db: AsyncSession = Depends(db_manager.get_session),
    credentials: HTTPBasicCredentials = Depends(verify_credentials)
):
    """Export multiple files in a single archive"""
    file_ids = request.get("file_ids", [])
    format = request.get("format", "tar.gz")
    
    if not file_ids:
        raise HTTPException(400, "No file IDs provided")
    
    # Get files from database
    result = await db.execute(
        select(MusicFile)
        .where(MusicFile.id.in_(file_ids))
        .options(selectinload(MusicFile.transcriptions), selectinload(MusicFile.lyrics))
    )
    files = result.scalars().all()
    
    if not files:
        raise HTTPException(404, "No files found")
    
    # Create temporary directory for export
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for file in files:
            # Create file directory
            file_dir = temp_path / f"{file.id}_{file.original_filename.replace('.', '_')}"
            file_dir.mkdir(parents=True, exist_ok=True)
            
            # Export metadata
            metadata = {
                "id": file.id,
                "filename": file.original_filename,
                "artist": file.artist,
                "title": file.title,
                "genre": file.genre,
                "duration": file.duration,
                "file_size": file.file_size,
                "created_at": file.uploaded_at.isoformat(),
                "transcriptions": [
                    {
                        "id": t.id,
                        "text": t.transcription_text,
                        "language": t.language,
                        "model_used": t.model_used,
                        "confidence": t.confidence,
                        "created_at": t.created_at.isoformat()
                    }
                    for t in file.transcriptions
                ],
                "lyrics": [
                    {
                        "id": l.id,
                        "source": l.source,
                        "text": l.lyrics_text,
                        "language": l.language,
                        "created_at": l.created_at.isoformat()
                    }
                    for l in file.lyrics
                ]
            }
            
            # Write metadata
            with open(file_dir / "metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)
            
            # Copy audio file if it exists
            if file.storage_path:
                source_path = STORAGE_PATHS["original"] / file.storage_path
                if source_path.exists():
                    import shutil
                    shutil.copy2(source_path, file_dir / file.original_filename)
        
        # Create archive
        archive_name = f"music_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if format == "zip":
            archive_path = temp_path / f"{archive_name}.zip"
            import zipfile
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_path):
                    for file in files:
                        if file != f"{archive_name}.zip":
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(temp_path)
                            zipf.write(file_path, arcname)
        else:  # tar.gz
            archive_path = temp_path / f"{archive_name}.tar.gz"
            import tarfile
            with tarfile.open(archive_path, "w:gz") as tar:
                for item in temp_path.iterdir():
                    if item.name != f"{archive_name}.tar.gz":
                        tar.add(item, arcname=item.name)
        
        # Return the archive
        return FileResponse(
            str(archive_path),
            media_type='application/octet-stream',
            filename=archive_path.name
        )

# Catch-all route for React Router - must be last!
@app.get("/{full_path:path}", response_class=HTMLResponse)
async def serve_spa(full_path: str):
    """Serve the React app for any non-API route"""
    # Don't catch API routes
    if full_path.startswith("api/"):
        raise HTTPException(404, "API endpoint not found")
    
    static_path = Path(__file__).parent.parent.parent / "music-analyzer-frontend" / "build"
    index_file = static_path / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    else:
        raise HTTPException(404, "Frontend not found")

# Run the application
if __name__ == "__main__":
    uvicorn.run(
        "music_analyzer_api:app",
        host=API_CONFIG["host"],
        port=API_CONFIG["port"],
        reload=False,
        log_level="info"
    )