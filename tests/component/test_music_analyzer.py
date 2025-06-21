#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test script for Music Analyzer V2
"""
import asyncio
import sys
from pathlib import Path

from src.config.music_analyzer_config import DATABASE_URL
from src.models.music_analyzer_models import DatabaseManager

async def test_database():
    """Test database connection"""
    print("Testing database connection...")
    
    db_manager = DatabaseManager(DATABASE_URL)
    
    try:
        await db_manager.initialize()
        print("✓ Database connection successful")
        
        # Test query
        async for session in db_manager.get_session():
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            print("✓ Database query successful")
            
    except Exception as e:
        print(f"✗ Database error: {e}")
    finally:
        await db_manager.close()

async def test_redis():
    """Test Redis connection"""
    print("\nTesting Redis connection...")
    
    import redis.asyncio as redis
    from src.config.music_analyzer_config import REDIS_CONFIG
    
    try:
        client = redis.Redis(**REDIS_CONFIG)
        await client.ping()
        print("✓ Redis connection successful")
        
        # Test set/get
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        if value == "test_value":
            print("✓ Redis set/get successful")
        await client.delete("test_key")
        
        await client.aclose()
    except Exception as e:
        print(f"✗ Redis error: {e}")

async def test_minio():
    """Test MinIO connection"""
    print("\nTesting MinIO connection...")
    
    from minio import Minio
    from music_analyzer_config import MINIO_CONFIG
    
    try:
        client = Minio(
            MINIO_CONFIG["endpoint"],
            access_key=MINIO_CONFIG["access_key"],
            secret_key=MINIO_CONFIG["secret_key"],
            secure=MINIO_CONFIG["secure"]
        )
        
        buckets = client.list_buckets()
        print(f"✓ MinIO connection successful ({len(buckets)} buckets)")
        
        # Check if our bucket exists
        if client.bucket_exists(MINIO_CONFIG["bucket_name"]):
            print(f"✓ Bucket '{MINIO_CONFIG['bucket_name']}' exists")
        else:
            print(f"✗ Bucket '{MINIO_CONFIG['bucket_name']}' not found")
            
    except Exception as e:
        print(f"✗ MinIO error: {e}")

def test_storage_paths():
    """Test storage directory structure"""
    print("\nTesting storage paths...")
    
    from music_analyzer_config import STORAGE_PATHS
    
    for name, path in STORAGE_PATHS.items():
        if path.exists():
            print(f"✓ {name}: {path}")
        else:
            print(f"✗ {name}: {path} (not found)")

async def main():
    """Run all tests"""
    print("Music Analyzer V2 - System Test")
    print("=" * 40)
    
    await test_database()
    await test_redis()
    await test_minio()
    test_storage_paths()
    
    print("\n" + "=" * 40)
    print("Test complete!")

if __name__ == "__main__":
    asyncio.run(main())