#!/usr/bin/env python3
# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Test tar.gz export functionality
"""
import asyncio
import tarfile
import tempfile
from pathlib import Path
from src.utils.music_analyzer_export import get_exporter
from src.models.music_analyzer_models import DatabaseManager, MusicFile
from src.config.music_analyzer_config import DATABASE_URL
from sqlalchemy import select

async def test_tar_exports():
    """Test tar.gz export formats"""
    print("\n=== Testing TAR.GZ Export Functionality ===\n")
    
    # Initialize database
    db_manager = DatabaseManager(DATABASE_URL)
    await db_manager.initialize()
    
    exporter = get_exporter()
    
    # Get a sample music file
    async for db in db_manager.get_session():
        result = await db.execute(select(MusicFile).limit(1))
        music_file = result.scalar_one_or_none()
        
        if not music_file:
            print("No music files found in database")
            return
    
    print(f"Testing with file: {music_file.original_filename}")
    print(f"Storage path: {music_file.storage_path}")
    
    # Test 1: Single file tar.gz export (original files)
    print("\n1. Testing single file tar.gz export (original)...")
    try:
        tar_export = await exporter.export_music_file(str(music_file.id), 'tar.gz')
        print(f"✓ TAR.GZ export successful")
        print(f"  Filename: {tar_export['filename']}")
        print(f"  Size: {len(tar_export['content'])} bytes")
        
        # Verify tar content
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tmp:
            tmp.write(tar_export['content'])
            tmp.flush()
            
            with tarfile.open(tmp.name, 'r:gz') as tar:
                print(f"  Files in archive: {tar.getnames()}")
                
    except Exception as e:
        print(f"✗ TAR.GZ export failed: {e}")
    
    # Test 2: Single file mono tar.gz export
    print("\n2. Testing single file mono tar.gz export...")
    try:
        mono_export = await exporter.export_music_file(str(music_file.id), 'mono_tar.gz')
        print(f"✓ Mono TAR.GZ export successful")
        print(f"  Filename: {mono_export['filename']}")
        print(f"  Size: {len(mono_export['content'])} bytes")
        
        # Verify tar content
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tmp:
            tmp.write(mono_export['content'])
            tmp.flush()
            
            with tarfile.open(tmp.name, 'r:gz') as tar:
                print(f"  Files in archive: {tar.getnames()}")
                
    except Exception as e:
        print(f"✗ Mono TAR.GZ export failed: {e}")
    
    # Test 3: Batch tar.gz export
    print("\n3. Testing batch tar.gz export...")
    try:
        # Get multiple files
        async for db in db_manager.get_session():
            result = await db.execute(select(MusicFile).limit(3))
            files = result.scalars().all()
            file_ids = [str(f.id) for f in files]
        
        if len(file_ids) < 2:
            file_ids = [str(music_file.id)] * 3
        
        batch_tar_export = await exporter.export_batch(file_ids, 'tar.gz')
        print(f"✓ Batch TAR.GZ export successful")
        print(f"  Filename: {batch_tar_export['filename']}")
        print(f"  Size: {len(batch_tar_export['content'])} bytes")
        print(f"  Number of files: {len(file_ids)}")
        
        # Verify tar content
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tmp:
            tmp.write(batch_tar_export['content'])
            tmp.flush()
            
            with tarfile.open(tmp.name, 'r:gz') as tar:
                members = tar.getnames()
                print(f"  Files in archive: {len(members)} files")
                for member in members[:5]:  # Show first 5
                    print(f"    - {member}")
                if len(members) > 5:
                    print(f"    ... and {len(members) - 5} more")
                    
    except Exception as e:
        print(f"✗ Batch TAR.GZ export failed: {e}")
    
    # Test 4: Batch mono tar.gz export
    print("\n4. Testing batch mono tar.gz export...")
    try:
        batch_mono_export = await exporter.export_batch(file_ids, 'mono_tar.gz')
        print(f"✓ Batch Mono TAR.GZ export successful")
        print(f"  Filename: {batch_mono_export['filename']}")
        print(f"  Size: {len(batch_mono_export['content'])} bytes")
        
        # Verify tar content
        with tempfile.NamedTemporaryFile(suffix='.tar.gz') as tmp:
            tmp.write(batch_mono_export['content'])
            tmp.flush()
            
            with tarfile.open(tmp.name, 'r:gz') as tar:
                members = tar.getnames()
                print(f"  Files in archive: {len(members)} files")
                
                # Group by directory
                dirs = set()
                for member in members:
                    if '/' in member:
                        dirs.add(member.split('/')[0])
                
                print(f"  Directories: {len(dirs)}")
                for dir_name in list(dirs)[:3]:  # Show first 3 directories
                    dir_files = [m for m in members if m.startswith(f"{dir_name}/")]
                    print(f"    - {dir_name}/: {len(dir_files)} files")
                    for f in dir_files[:3]:  # Show first 3 files in each dir
                        print(f"      - {f}")
                        
    except Exception as e:
        print(f"✗ Batch Mono TAR.GZ export failed: {e}")
    
    print("\n✓ TAR.GZ export testing complete!")

if __name__ == "__main__":
    asyncio.run(test_tar_exports())