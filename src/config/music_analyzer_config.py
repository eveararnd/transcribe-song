# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Music Analyzer V2 Configuration
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
MUSIC_LIBRARY_BASE = BASE_DIR / "music_library_v2"
MUSIC_LIBRARY_BASE.mkdir(exist_ok=True)

# Storage paths
STORAGE_PATHS = {
    "original": MUSIC_LIBRARY_BASE / "original",
    "converted": MUSIC_LIBRARY_BASE / "converted",
    "cache": MUSIC_LIBRARY_BASE / "cache",
}

# Create storage directories
for path in STORAGE_PATHS.values():
    path.mkdir(exist_ok=True)

# Database configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "music_analyzer",
    "user": "music_user",
    "password": "music_analyzer_2025"
}

DATABASE_URL = f"postgresql+asyncpg://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"

# Redis configuration
REDIS_CONFIG = {
    "host": "localhost",
    "port": 6379,
    "db": 0,
    "decode_responses": True
}

# MinIO configuration
MINIO_CONFIG = {
    "endpoint": "localhost:9000",
    "access_key": "minio_admin",
    "secret_key": "minio_secret_2025",
    "bucket_name": "music-analyzer",
    "secure": False
}

# Model configuration
MODEL_CONFIG = {
    "parakeet_model_path": str(BASE_DIR / "models" / "parakeet-tdt-0.6b" / "parakeet-tdt-0.6b-tur_spm__pcm16.nemo"),
    "gemma_model_name": "google/gemma-3n-E4B-it-litert-preview",
    "embedding_dimension": 768
}

# API configuration
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "max_upload_size": 100 * 1024 * 1024,  # 100MB
    "supported_audio_formats": [
        ".mp3", ".wav", ".flac", ".m4a", ".ogg", ".opus",
        ".aac", ".wma", ".webm", ".mp4", ".avi", ".mkv"
    ]
}

# Search API configuration (to be filled by user)
SEARCH_API_CONFIG = {
    "brave": {
        "api_key": os.environ.get("BRAVE_API_KEY", ""),
        "base_url": "https://api.search.brave.com/res/v1/web/search"
    },
    "tavily": {
        "api_key": os.environ.get("TAVILY_API_KEY", ""),
        "base_url": "https://api.tavily.com/search"
    }
}

# Genre keywords for classification
GENRE_KEYWORDS = {
    'pop': ['pop', 'popular', 'top 40', 'mainstream'],
    'rock': ['rock', 'metal', 'punk', 'alternative', 'indie'],
    'hiphop': ['hip hop', 'rap', 'trap', 'drill', 'r&b', 'rnb'],
    'electronic': ['electronic', 'edm', 'house', 'techno', 'dance', 'dubstep', 'trance'],
    'classical': ['classical', 'orchestra', 'symphony', 'opera', 'baroque'],
    'jazz': ['jazz', 'blues', 'swing', 'bebop', 'fusion'],
    'country': ['country', 'folk', 'bluegrass', 'americana'],
    'latin': ['latin', 'salsa', 'reggaeton', 'bachata', 'merengue'],
    'world': ['world', 'ethnic', 'traditional', 'afrobeat'],
    'other': []
}

# FAISS configuration
FAISS_CONFIG = {
    "index_path": str(MUSIC_LIBRARY_BASE / "faiss_index.bin"),
    "id_map_path": str(MUSIC_LIBRARY_BASE / "faiss_id_map.json"),
    "dimension": 768,
    "search_k": 10
}

# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default"
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": str(BASE_DIR / "music_analyzer.log"),
            "formatter": "default"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
}