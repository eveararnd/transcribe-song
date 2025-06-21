# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Music Analyzer V2 Integration Module
Adds V2 endpoints to existing Parakeet API
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any
import asyncio
import logging
import uuid
from fastapi import UploadFile, File, HTTPException, Depends
from fastapi.security import HTTPBasicCredentials

# Import V2 modules
from src.config.music_analyzer_config import (
    DATABASE_URL, REDIS_CONFIG, MINIO_CONFIG, 
    STORAGE_PATHS, MODEL_CONFIG, API_CONFIG,
    GENRE_KEYWORDS, FAISS_CONFIG, SEARCH_API_CONFIG
)
from src.models.music_analyzer_models import (
    DatabaseManager, MusicFile, Transcription, 
    Lyrics, SearchHistory, APIConfig
)
from src.api.music_analyzer_api import (
    db_manager, redis_client, minio_client,
    TranscriptionRequest, TranscriptionResponse,
    LyricsSearchRequest, StorageStatsResponse,
    FileListRequest, verify_credentials,
    get_file_hash, detect_genre, convert_audio_for_asr,
    get_audio_metadata
)

logger = logging.getLogger(__name__)

def integrate_v2_endpoints(app, asr_model_ref):
    """
    Integrate V2 endpoints into existing FastAPI app
    
    Args:
        app: FastAPI application instance
        asr_model_ref: Reference to the loaded ASR model
    """
    
    # Store model reference
    global asr_model
    asr_model = asr_model_ref
    
    # Add V2 routes with /v2 prefix to avoid conflicts
    
    @app.get("/api/v2/info")
    async def v2_info():
        """Music Analyzer V2 information"""
        return {
            "name": "Music Analyzer V2",
            "version": "2.0.0",
            "features": [
                "PostgreSQL with pgvector",
                "Redis caching",
                "MinIO object storage",
                "FAISS vector search (planned)",
                "Gemma 3B integration (planned)",
                "Advanced storage management",
                "Export functionality"
            ],
            "endpoints": {
                "health": "/api/v2/health",
                "upload": "/api/v2/upload",
                "catalog": "/api/v2/catalog",
                "transcribe": "/api/v2/transcribe",
                "search_lyrics": "/api/v2/search-lyrics",
                "storage_stats": "/api/v2/storage/stats",
                "file_list": "/api/v2/files"
            }
        }
    
    @app.get("/api/v2/health")
    async def v2_health_check():
        """V2 health check endpoint"""
        from music_analyzer_api import health_check
        return await health_check()
    
    @app.post("/api/v2/upload")
    async def v2_upload_file(
        file: UploadFile = File(...),
        credentials: HTTPBasicCredentials = Depends(verify_credentials)
    ):
        """V2 upload endpoint with database storage"""
        from music_analyzer_api import upload_file
        # Get database session
        async for db in db_manager.get_session():
            return await upload_file(file, credentials, db)
    
    @app.post("/api/v2/transcribe")
    async def v2_transcribe_file(
        request: TranscriptionRequest,
        credentials: HTTPBasicCredentials = Depends(verify_credentials)
    ):
        """V2 transcribe endpoint with caching"""
        from music_analyzer_api import transcribe_file
        # Get database session
        async for db in db_manager.get_session():
            # Use the global asr_model
            import music_analyzer_api
            music_analyzer_api.asr_model = asr_model
            return await transcribe_file(request, credentials, db)
    
    @app.get("/api/v2/catalog")
    async def v2_get_catalog(
        credentials: HTTPBasicCredentials = Depends(verify_credentials)
    ):
        """V2 catalog endpoint from database"""
        from music_analyzer_api import get_catalog
        async for db in db_manager.get_session():
            return await get_catalog(credentials, db)
    
    @app.get("/api/v2/storage/stats")
    async def v2_storage_stats(
        credentials: HTTPBasicCredentials = Depends(verify_credentials)
    ):
        """Get storage statistics"""
        import shutil
        from sqlalchemy import select, func
        
        stats = {
            "original_files": {"count": 0, "total_size": 0},
            "converted_files": {"count": 0, "total_size": 0},
            "cache_files": {"count": 0, "total_size": 0},
            "database_size": 0,
            "faiss_index_size": 0,
            "total_used": 0,
            "available_space": shutil.disk_usage("/").free
        }
        
        # Count files in directories
        for storage_type, path in STORAGE_PATHS.items():
            if path.exists():
                files = list(path.rglob("*"))
                files = [f for f in files if f.is_file()]
                stats[f"{storage_type}_files"]["count"] = len(files)
                stats[f"{storage_type}_files"]["total_size"] = sum(f.stat().st_size for f in files)
        
        # Get database size
        async for db in db_manager.get_session():
            result = await db.execute(
                select(func.count(MusicFile.id), func.sum(MusicFile.file_size))
            )
            count, total_size = result.one()
            stats["database_entries"] = count or 0
            stats["database_tracked_size"] = total_size or 0
        
        # Calculate total
        stats["total_used"] = sum(
            v["total_size"] for k, v in stats.items() 
            if isinstance(v, dict) and "total_size" in v
        )
        
        return stats
    
    @app.post("/api/v2/files")
    async def v2_list_files(
        request: FileListRequest,
        credentials: HTTPBasicCredentials = Depends(verify_credentials)
    ):
        """List files with pagination and filtering"""
        from sqlalchemy import select, and_, or_, func
        from music_analyzer_models import MusicFile, Transcription, Lyrics
        
        async for db in db_manager.get_session():
            # Base query
            query = select(MusicFile)
            
            # Apply filters
            if request.filters:
                conditions = []
                if request.filters.get("genre"):
                    conditions.append(MusicFile.genre == request.filters["genre"])
                if request.filters.get("has_transcription") is not None:
                    if request.filters["has_transcription"]:
                        subq = select(Transcription.file_id).subquery()
                        conditions.append(MusicFile.id.in_(subq))
                if conditions:
                    query = query.where(and_(*conditions))
            
            # Apply search
            if request.search_query:
                query = query.where(
                    or_(
                        MusicFile.original_filename.ilike(f"%{request.search_query}%"),
                        MusicFile.genre.ilike(f"%{request.search_query}%")
                    )
                )
            
            # Count total
            count_result = await db.execute(select(func.count()).select_from(query.subquery()))
            total_count = count_result.scalar()
            
            # Apply sorting
            sort_map = {
                "filename": MusicFile.original_filename,
                "size": MusicFile.file_size,
                "uploaded_at": MusicFile.uploaded_at,
                "genre": MusicFile.genre,
                "duration": MusicFile.duration
            }
            sort_column = sort_map.get(request.sort_by, MusicFile.uploaded_at)
            if request.sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column)
            
            # Apply pagination
            offset = (request.page - 1) * request.per_page
            query = query.offset(offset).limit(request.per_page)
            
            # Execute query
            result = await db.execute(query)
            files = result.scalars().all()
            
            # Format response
            return {
                "files": [
                    {
                        "id": str(f.id),
                        "filename": f.original_filename,
                        "genre": f.genre,
                        "size": f.file_size,
                        "duration": f.duration,
                        "sample_rate": f.sample_rate,
                        "channels": f.channels,
                        "codec": f.codec,
                        "uploaded_at": f.uploaded_at.isoformat(),
                        "hash": f.file_hash
                    }
                    for f in files
                ],
                "pagination": {
                    "page": request.page,
                    "per_page": request.per_page,
                    "total_count": total_count,
                    "total_pages": (total_count + request.per_page - 1) // request.per_page,
                    "has_next": offset + request.per_page < total_count,
                    "has_prev": request.page > 1
                }
            }
    
    # Add startup event to initialize V2 services
    @app.on_event("startup")
    async def startup_v2():
        """Initialize V2 services"""
        try:
            # Initialize database
            await db_manager.initialize()
            logger.info("V2: Database initialized")
            
            # Initialize Redis
            global redis_client
            import redis.asyncio as redis
            redis_client = redis.Redis(**REDIS_CONFIG)
            await redis_client.ping()
            logger.info("V2: Redis connected")
            
            # Initialize MinIO
            global minio_client
            from minio import Minio
            minio_client = Minio(
                MINIO_CONFIG["endpoint"],
                access_key=MINIO_CONFIG["access_key"],
                secret_key=MINIO_CONFIG["secret_key"],
                secure=MINIO_CONFIG["secure"]
            )
            
            # Create bucket if not exists
            if not minio_client.bucket_exists(MINIO_CONFIG["bucket_name"]):
                minio_client.make_bucket(MINIO_CONFIG["bucket_name"])
                logger.info(f"V2: Created MinIO bucket: {MINIO_CONFIG['bucket_name']}")
            
            # Update music_analyzer_api module with initialized clients
            import music_analyzer_api
            music_analyzer_api.redis_client = redis_client
            music_analyzer_api.minio_client = minio_client
            
        except Exception as e:
            logger.error(f"V2 startup error: {e}")
    
    @app.on_event("shutdown")
    async def shutdown_v2():
        """Cleanup V2 services"""
        try:
            if redis_client:
                await redis_client.aclose()
            await db_manager.close()
            logger.info("V2: Services shut down")
        except Exception as e:
            logger.error(f"V2 shutdown error: {e}")
    
    logger.info("Music Analyzer V2 endpoints integrated successfully")