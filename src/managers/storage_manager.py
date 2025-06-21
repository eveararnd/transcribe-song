# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Storage Management and Cleanup Service for Music Analyzer
"""
import os
import asyncio
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from sqlalchemy import select, and_, or_, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
import json

from src.models.music_analyzer_models import DatabaseManager, MusicFile, Transcription
from src.config.music_analyzer_config import STORAGE_PATHS

logger = logging.getLogger(__name__)

class StorageManager:
    def __init__(self, db_manager: DatabaseManager):
        """Initialize storage manager"""
        self.db_manager = db_manager
        self.storage_paths = STORAGE_PATHS
        
    async def get_storage_statistics(self) -> Dict:
        """Get detailed storage statistics"""
        stats = {
            "original_files": await self._analyze_directory(self.storage_paths["original"]),
            "converted_files": await self._analyze_directory(self.storage_paths["converted"]),
            "cache_files": await self._analyze_directory(self.storage_paths["cache"]),
            "total_used": 0,
            "by_genre": {},
            "by_format": {},
            "database_size": await self._get_database_size(),
            "orphaned_files": []
        }
        
        # Calculate totals
        stats["total_used"] = (
            stats["original_files"]["total_size"] +
            stats["converted_files"]["total_size"] +
            stats["cache_files"]["total_size"]
        )
        
        # Analyze by genre and format
        async with self.db_manager.get_session() as db:
            # By genre
            genre_stats = await db.execute(
                select(
                    MusicFile.genre,
                    func.count(MusicFile.id).label("count"),
                    func.sum(MusicFile.file_size).label("total_size")
                ).group_by(MusicFile.genre)
            )
            for row in genre_stats:
                stats["by_genre"][row.genre] = {
                    "count": row.count,
                    "size": row.total_size or 0
                }
            
            # Find orphaned files
            stats["orphaned_files"] = await self._find_orphaned_files(db)
        
        return stats
    
    async def _analyze_directory(self, path: Path) -> Dict:
        """Analyze a directory and return statistics"""
        if not path.exists():
            return {"count": 0, "total_size": 0, "files": []}
        
        files = []
        total_size = 0
        
        for file_path in path.rglob("*"):
            if file_path.is_file():
                size = file_path.stat().st_size
                total_size += size
                files.append({
                    "path": str(file_path),
                    "name": file_path.name,
                    "size": size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return {
            "count": len(files),
            "total_size": total_size,
            "files": sorted(files, key=lambda x: x["size"], reverse=True)[:100]  # Top 100 by size
        }
    
    async def _get_database_size(self) -> int:
        """Get approximate database size"""
        async with self.db_manager.get_session() as db:
            # Count records
            music_count = await db.scalar(select(func.count(MusicFile.id)))
            trans_count = await db.scalar(select(func.count(Transcription.id)))
            
            # Estimate size (rough approximation)
            return (music_count * 1024) + (trans_count * 2048)
    
    async def _find_orphaned_files(self, db: AsyncSession) -> List[Dict]:
        """Find files on disk that don't have database entries"""
        orphaned = []
        
        # Get all file paths from database
        db_files = await db.execute(select(MusicFile.storage_path))
        db_paths = {Path(row[0]) for row in db_files}
        
        # Check original files
        original_dir = self.storage_paths["original"]
        if original_dir.exists():
            for file_path in original_dir.rglob("*"):
                if file_path.is_file() and file_path not in db_paths:
                    orphaned.append({
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "type": "original"
                    })
        
        return orphaned
    
    async def clean_orphaned_files(self, file_paths: List[str]) -> Dict:
        """Remove orphaned files"""
        removed = []
        failed = []
        freed_space = 0
        
        for file_path in file_paths:
            path = Path(file_path)
            if path.exists():
                try:
                    size = path.stat().st_size
                    path.unlink()
                    removed.append(file_path)
                    freed_space += size
                except Exception as e:
                    logger.error(f"Failed to remove {file_path}: {e}")
                    failed.append({"path": file_path, "error": str(e)})
        
        return {
            "removed_count": len(removed),
            "failed_count": len(failed),
            "freed_space": freed_space,
            "removed_files": removed,
            "failed_files": failed
        }
    
    async def clean_old_files(self, days: int = 30, dry_run: bool = True) -> Dict:
        """Clean files older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        async with self.db_manager.get_session() as db:
            # Find old files
            old_files = await db.execute(
                select(MusicFile).where(MusicFile.uploaded_at < cutoff_date)
            )
            old_files = old_files.scalars().all()
            
            if dry_run:
                return {
                    "dry_run": True,
                    "would_remove": len(old_files),
                    "would_free_space": sum(f.file_size or 0 for f in old_files),
                    "files": [
                        {
                            "id": str(f.id),
                            "filename": f.original_filename,
                            "size": f.file_size,
                            "uploaded": f.uploaded_at.isoformat()
                        }
                        for f in old_files[:10]  # Show first 10
                    ]
                }
            else:
                # Actually remove files
                removed_count = 0
                freed_space = 0
                
                for file in old_files:
                    try:
                        # Remove physical file
                        file_path = Path(file.storage_path)
                        if file_path.exists():
                            freed_space += file_path.stat().st_size
                            file_path.unlink()
                        
                        # Remove from database
                        await db.delete(file)
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to remove file {file.id}: {e}")
                
                await db.commit()
                
                return {
                    "dry_run": False,
                    "removed_count": removed_count,
                    "freed_space": freed_space
                }
    
    async def clean_duplicate_files(self, dry_run: bool = True) -> Dict:
        """Remove duplicate files based on hash"""
        async with self.db_manager.get_session() as db:
            # Find duplicates
            duplicates_query = select(
                MusicFile.file_hash,
                func.count(MusicFile.id).label("count"),
                func.array_agg(MusicFile.id).label("ids")
            ).group_by(MusicFile.file_hash).having(func.count(MusicFile.id) > 1)
            
            duplicates = await db.execute(duplicates_query)
            
            to_remove = []
            total_size = 0
            
            for row in duplicates:
                # Keep the first, remove the rest
                ids = row.ids[1:]  # Skip first
                for file_id in ids:
                    file = await db.get(MusicFile, file_id)
                    if file:
                        to_remove.append(file)
                        total_size += file.file_size or 0
            
            if dry_run:
                return {
                    "dry_run": True,
                    "would_remove": len(to_remove),
                    "would_free_space": total_size,
                    "duplicates": [
                        {
                            "id": str(f.id),
                            "filename": f.original_filename,
                            "hash": f.file_hash[:8] + "...",
                            "size": f.file_size
                        }
                        for f in to_remove[:10]
                    ]
                }
            else:
                removed_count = 0
                freed_space = 0
                
                for file in to_remove:
                    try:
                        # Remove physical file
                        file_path = Path(file.storage_path)
                        if file_path.exists():
                            freed_space += file_path.stat().st_size
                            file_path.unlink()
                        
                        # Remove from database
                        await db.delete(file)
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to remove duplicate {file.id}: {e}")
                
                await db.commit()
                
                return {
                    "dry_run": False,
                    "removed_count": removed_count,
                    "freed_space": freed_space
                }
    
    async def clean_cache(self, max_age_hours: int = 24) -> Dict:
        """Clean old cache files"""
        cache_dir = self.storage_paths["cache"]
        if not cache_dir.exists():
            return {"removed_count": 0, "freed_space": 0}
        
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        removed_count = 0
        freed_space = 0
        
        for file_path in cache_dir.rglob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    size = file_path.stat().st_size
                    file_path.unlink()
                    removed_count += 1
                    freed_space += size
                except Exception as e:
                    logger.error(f"Failed to remove cache file {file_path}: {e}")
        
        return {
            "removed_count": removed_count,
            "freed_space": freed_space
        }
    
    async def export_file_list(self, format: str = "json") -> bytes:
        """Export list of all files"""
        async with self.db_manager.get_session() as db:
            files = await db.execute(select(MusicFile))
            files = files.scalars().all()
            
            data = []
            for file in files:
                # Get transcription if exists
                trans = await db.execute(
                    select(Transcription).where(Transcription.file_id == file.id)
                )
                trans = trans.scalar_one_or_none()
                
                data.append({
                    "id": str(file.id),
                    "filename": file.original_filename,
                    "genre": file.genre,
                    "size": file.file_size,
                    "duration": file.duration,
                    "hash": file.file_hash,
                    "uploaded": file.uploaded_at.isoformat(),
                    "transcribed": trans is not None,
                    "transcription_preview": trans.transcription_text[:200] if trans else None
                })
            
            if format == "json":
                return json.dumps(data, indent=2).encode()
            elif format == "csv":
                import csv
                import io
                
                output = io.StringIO()
                if data:
                    writer = csv.DictWriter(output, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)
                
                return output.getvalue().encode()
            else:
                raise ValueError(f"Unsupported format: {format}")

# Singleton instance
_storage_manager = None

def get_storage_manager(db_manager: DatabaseManager) -> StorageManager:
    """Get or create storage manager instance"""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = StorageManager(db_manager)
    return _storage_manager