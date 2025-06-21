# Copyright © 2025 David Gornshtein @Eveara Ltd. All rights reserved.
"""
Music Analyzer Export Functionality
Provides export capabilities for music analysis results in various formats
"""
import json
import csv
import io
import zipfile
import tarfile
import tempfile
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd
from pathlib import Path
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.models.music_analyzer_models import MusicFile, Transcription, Lyrics, SearchHistory, DatabaseManager
from src.config.music_analyzer_config import MINIO_CONFIG, DATABASE_URL

class MusicAnalyzerExporter:
    """Handles export of music analysis data in various formats"""
    
    def __init__(self):
        self.supported_formats = ['json', 'csv', 'xlsx', 'zip', 'tar.gz', 'mono_tar.gz']
    
    async def export_music_file(self, file_id: str, format: str = 'json') -> Dict[str, Any]:
        """Export a single music file with all its data"""
        db_manager = DatabaseManager(DATABASE_URL)
        async for db in db_manager.get_session():
            # Get music file with all related data
            result = await db.execute(
                select(MusicFile)
                .options(
                    selectinload(MusicFile.transcriptions),
                    selectinload(MusicFile.lyrics)
                )
                .where(MusicFile.id == file_id)
            )
            music_file = result.scalar_one_or_none()
            
            if not music_file:
                raise ValueError(f"Music file not found: {file_id}")
            
            # Prepare data for export
            export_data = {
                'file_info': {
                    'id': str(music_file.id),
                    'original_filename': music_file.original_filename,
                    'file_format': music_file.file_format,
                    'duration': music_file.duration,
                    'sample_rate': music_file.sample_rate,
                    'channels': music_file.channels,
                    'bit_depth': music_file.bit_depth,
                    'file_size': music_file.file_size,
                    'uploaded_at': music_file.uploaded_at.isoformat() if music_file.uploaded_at else None,
                    'metadata': music_file.metadata
                },
                'transcriptions': [
                    {
                        'id': str(t.id),
                        'text': t.transcription_text,
                        'language': getattr(t, 'language', 'en'),
                        'confidence': t.confidence,
                        'word_timestamps': getattr(t, 'word_timestamps', None),
                        'created_at': t.created_at.isoformat() if t.created_at else None
                    }
                    for t in music_file.transcriptions
                ],
                'lyrics': [
                    {
                        'id': str(l.id),
                        'source': l.source,
                        'lyrics_text': l.lyrics_text,
                        'confidence': l.confidence,
                        'language': l.language,
                        'created_at': l.created_at.isoformat() if l.created_at else None
                    }
                    for l in (music_file.lyrics if hasattr(music_file, 'lyrics') else [])
                ]
            }
            
            # Format based on requested type
            if format == 'json':
                return {
                    'format': 'json',
                    'content': json.dumps(export_data, indent=2),
                    'filename': f"{music_file.original_filename}_export.json"
                }
            
            elif format == 'csv':
                return self._export_to_csv(export_data, music_file.original_filename)
            
            elif format == 'xlsx':
                return self._export_to_excel(export_data, music_file.original_filename)
            
            elif format == 'zip':
                return await self._export_to_zip(export_data, music_file)
            
            elif format == 'tar.gz':
                return await self._export_original_files_tar_gz([music_file])
            
            elif format == 'mono_tar.gz':
                return await self._export_mono_files_tar_gz([music_file], export_data)
            
            else:
                raise ValueError(f"Unsupported format: {format}")
    
    def _export_to_csv(self, data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Export data to CSV format"""
        csv_files = {}
        
        # File info CSV
        file_info_csv = io.StringIO()
        writer = csv.DictWriter(file_info_csv, fieldnames=data['file_info'].keys())
        writer.writeheader()
        writer.writerow(data['file_info'])
        csv_files['file_info.csv'] = file_info_csv.getvalue()
        
        # Transcriptions CSV
        if data['transcriptions']:
            trans_csv = io.StringIO()
            fieldnames = ['id', 'text', 'language', 'confidence', 'created_at']
            writer = csv.DictWriter(trans_csv, fieldnames=fieldnames)
            writer.writeheader()
            for t in data['transcriptions']:
                writer.writerow({k: t.get(k) for k in fieldnames})
            csv_files['transcriptions.csv'] = trans_csv.getvalue()
        
        # Lyrics CSV
        if data.get('lyrics'):
            lyrics_csv = io.StringIO()
            fieldnames = ['id', 'source', 'lyrics_text', 'confidence', 'language', 'created_at']
            writer = csv.DictWriter(lyrics_csv, fieldnames=fieldnames)
            writer.writeheader()
            for l in data['lyrics']:
                writer.writerow({k: l.get(k) for k in fieldnames})
            csv_files['lyrics.csv'] = lyrics_csv.getvalue()
        
        # Create a zip file with all CSVs
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for csv_filename, csv_content in csv_files.items():
                zip_file.writestr(csv_filename, csv_content)
        
        return {
            'format': 'csv',
            'content': zip_buffer.getvalue(),
            'filename': f"{filename}_export.zip",
            'content_type': 'application/zip'
        }
    
    def _export_to_excel(self, data: Dict[str, Any], filename: str) -> Dict[str, Any]:
        """Export data to Excel format"""
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # File info sheet
            df_info = pd.DataFrame([data['file_info']])
            df_info.to_excel(writer, sheet_name='File Info', index=False)
            
            # Transcriptions sheet
            if data['transcriptions']:
                df_trans = pd.DataFrame(data['transcriptions'])
                # Remove complex fields for Excel
                if 'word_timestamps' in df_trans.columns:
                    df_trans = df_trans.drop('word_timestamps', axis=1)
                df_trans.to_excel(writer, sheet_name='Transcriptions', index=False)
            
            # Lyrics sheet
            if data.get('lyrics'):
                df_lyrics = pd.DataFrame(data['lyrics'])
                df_lyrics.to_excel(writer, sheet_name='Lyrics', index=False)
        
        excel_buffer.seek(0)
        
        return {
            'format': 'xlsx',
            'content': excel_buffer.getvalue(),
            'filename': f"{filename}_export.xlsx",
            'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
    
    async def _export_to_zip(self, data: Dict[str, Any], music_file: MusicFile) -> Dict[str, Any]:
        """Export data with original audio file in a zip"""
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add JSON data
            zip_file.writestr('data.json', json.dumps(data, indent=2))
            
            # Add transcriptions as text files
            for i, trans in enumerate(data['transcriptions']):
                zip_file.writestr(
                    f'transcription_{i+1}.txt',
                    f"Language: {trans['language']}\n"
                    f"Confidence: {trans['confidence']}\n\n"
                    f"{trans['text']}"
                )
            
            # Add lyrics as text files
            for i, lyrics in enumerate(data.get('lyrics', [])):
                if lyrics.get('lyrics_text'):
                    zip_file.writestr(
                        f'lyrics_{lyrics.get("source", "unknown")}_{i+1}.txt',
                        lyrics['lyrics_text']
                    )
            
            # Add original audio file if available
            if music_file.storage_path:
                try:
                    # Try to read from local storage first
                    if Path(music_file.storage_path).exists():
                        with open(music_file.storage_path, 'rb') as f:
                            audio_data = f.read()
                        zip_file.writestr(
                            f"audio/{music_file.original_filename}",
                            audio_data
                        )
                    else:
                        # Fall back to MinIO if local file not found
                        from minio import Minio
                        minio_client = Minio(
                            f"{MINIO_CONFIG['host']}:{MINIO_CONFIG['port']}",
                            access_key=MINIO_CONFIG['access_key'],
                            secret_key=MINIO_CONFIG['secret_key'],
                            secure=MINIO_CONFIG['secure']
                        )
                        
                        # Construct MinIO path from storage path
                        # Extract genre from path (e.g., /path/to/original/genre/file.mp3)
                        path_parts = Path(music_file.storage_path).parts
                        if 'original' in path_parts:
                            idx = path_parts.index('original')
                            minio_path = '/'.join(path_parts[idx:])
                        else:
                            # Fallback: use genre and filename
                            genre = getattr(music_file, 'genre', 'unknown')
                            minio_path = f"original/{genre}/{Path(music_file.storage_path).name}"
                        
                        response = minio_client.get_object(
                            MINIO_CONFIG.get('bucket_name', 'music-analyzer'),
                            minio_path
                        )
                    audio_data = response.read()
                    response.close()
                    response.release_conn()
                    
                    zip_file.writestr(
                        f"audio/{music_file.original_filename}",
                        audio_data
                    )
                except Exception as e:
                    # Log error but continue export
                    print(f"Error adding audio file: {e}")
        
        zip_buffer.seek(0)
        
        return {
            'format': 'zip',
            'content': zip_buffer.getvalue(),
            'filename': f"{music_file.original_filename}_complete_export.zip",
            'content_type': 'application/zip'
        }
    
    async def export_batch(self, file_ids: List[str], format: str = 'json') -> Dict[str, Any]:
        """Export multiple music files"""
        # Handle tar.gz formats specially
        if format in ['tar.gz', 'mono_tar.gz']:
            db_manager = DatabaseManager(DATABASE_URL)
            music_files = []
            
            async for db in db_manager.get_session():
                for file_id in file_ids:
                    result = await db.execute(
                        select(MusicFile)
                        .options(
                            selectinload(MusicFile.transcriptions),
                            selectinload(MusicFile.lyrics)
                        )
                        .where(MusicFile.id == file_id)
                    )
                    music_file = result.scalar_one_or_none()
                    if music_file:
                        music_files.append(music_file)
            
            if format == 'tar.gz':
                return await self._export_original_files_tar_gz(music_files)
            else:  # mono_tar.gz
                # Collect all export data
                all_exports = []
                for music_file in music_files:
                    export_data = {
                        'file_info': {
                            'id': str(music_file.id),
                            'original_filename': music_file.original_filename,
                            'file_format': music_file.file_format,
                            'duration': music_file.duration,
                            'sample_rate': music_file.sample_rate,
                            'channels': music_file.channels,
                            'bit_depth': music_file.bit_depth,
                            'file_size': music_file.file_size,
                            'uploaded_at': music_file.uploaded_at.isoformat() if music_file.uploaded_at else None,
                            'metadata': music_file.metadata
                        },
                        'transcriptions': [
                            {
                                'id': str(t.id),
                                'text': t.transcription_text,
                                'language': getattr(t, 'language', 'en'),
                                'confidence': t.confidence,
                                'word_timestamps': getattr(t, 'word_timestamps', None),
                                'created_at': t.created_at.isoformat() if t.created_at else None
                            }
                            for t in music_file.transcriptions
                        ],
                        'lyrics': [
                            {
                                'id': str(l.id),
                                'source': l.source,
                                'lyrics_text': l.lyrics_text,
                                'confidence': l.confidence,
                                'language': l.language,
                                'created_at': l.created_at.isoformat() if l.created_at else None
                            }
                            for l in (music_file.lyrics if hasattr(music_file, 'lyrics') else [])
                        ]
                    }
                    all_exports.append(export_data)
                
                # Create mono tar.gz with all files
                return await self._export_mono_files_tar_gz_batch(music_files, all_exports)
        
        # Original implementation for other formats
        exports = []
        
        for file_id in file_ids:
            try:
                export = await self.export_music_file(file_id, 'json')
                exports.append(json.loads(export['content']))
            except Exception as e:
                exports.append({
                    'file_id': file_id,
                    'error': str(e)
                })
        
        # Combine exports
        combined_data = {
            'export_date': datetime.utcnow().isoformat(),
            'total_files': len(file_ids),
            'files': exports
        }
        
        if format == 'json':
            return {
                'format': 'json',
                'content': json.dumps(combined_data, indent=2),
                'filename': f"batch_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            }
        else:
            # For other formats, create a zip with individual exports
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add summary
                zip_file.writestr('summary.json', json.dumps(combined_data, indent=2))
                
                # Add individual exports
                for i, export in enumerate(exports):
                    if 'error' not in export:
                        filename = export.get('file_info', {}).get('original_filename', f'file_{i+1}')
                        if format == 'csv':
                            csv_export = self._export_to_csv(export, filename)
                            zip_file.writestr(f"{filename}.zip", csv_export['content'])
                        elif format == 'xlsx':
                            xlsx_export = self._export_to_excel(export, filename)
                            zip_file.writestr(f"{filename}.xlsx", xlsx_export['content'])
            
            zip_buffer.seek(0)
            
            return {
                'format': format,
                'content': zip_buffer.getvalue(),
                'filename': f"batch_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip",
                'content_type': 'application/zip'
            }
    
    async def export_search_history(self, search_id: str, format: str = 'json') -> Dict[str, Any]:
        """Export search history"""
        db_manager = DatabaseManager(DATABASE_URL)
        async for db in db_manager.get_session():
            result = await db.execute(
                select(SearchHistory)
                .where(SearchHistory.id == search_id)
            )
            search_history = result.scalar_one_or_none()
            
            if not search_history:
                raise ValueError(f"Search history not found: {search_id}")
            
            export_data = {
                'search_info': {
                    'id': str(search_history.id),
                    'query': search_history.query,
                    'search_type': search_history.search_type,
                    'results_count': search_history.results_count,
                    'created_at': search_history.created_at.isoformat() if search_history.created_at else None
                },
                'results': search_history.results or {}
            }
            
            if format == 'json':
                return {
                    'format': 'json',
                    'content': json.dumps(export_data, indent=2),
                    'filename': f"search_{search_history.search_type}_{search_history.id}.json"
                }
            else:
                # For CSV/Excel, flatten the results
                if isinstance(export_data['results'], list):
                    df = pd.DataFrame(export_data['results'])
                else:
                    df = pd.DataFrame([export_data['results']])
                
                if format == 'csv':
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    return {
                        'format': 'csv',
                        'content': csv_buffer.getvalue(),
                        'filename': f"search_{search_history.search_type}_{search_history.id}.csv"
                    }
                elif format == 'xlsx':
                    excel_buffer = io.BytesIO()
                    df.to_excel(excel_buffer, index=False)
                    excel_buffer.seek(0)
                    return {
                        'format': 'xlsx',
                        'content': excel_buffer.getvalue(),
                        'filename': f"search_{search_history.search_type}_{search_history.id}.xlsx",
                        'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    }
    
    async def _export_original_files_tar_gz(self, music_files: List[MusicFile]) -> Dict[str, Any]:
        """Export original uploaded files as tar.gz archive"""
        from minio import Minio
        
        # Create temporary file for tar.gz
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            tar_path = tmp_file.name
        
        try:
            # Initialize MinIO client
            minio_client = Minio(
                f"{MINIO_CONFIG['host']}:{MINIO_CONFIG['port']}",
                access_key=MINIO_CONFIG['access_key'],
                secret_key=MINIO_CONFIG['secret_key'],
                secure=MINIO_CONFIG['secure']
            )
            
            # Create tar.gz archive
            with tarfile.open(tar_path, 'w:gz') as tar:
                for music_file in music_files:
                    if music_file.storage_path:
                        try:
                            # Try local storage first
                            if Path(music_file.storage_path).exists():
                                tar.add(music_file.storage_path, arcname=music_file.original_filename)
                            else:
                                # Get file from MinIO
                                path_parts = Path(music_file.storage_path).parts
                                if 'original' in path_parts:
                                    idx = path_parts.index('original')
                                    minio_path = '/'.join(path_parts[idx:])
                                else:
                                    genre = getattr(music_file, 'genre', 'unknown')
                                    minio_path = f"original/{genre}/{Path(music_file.storage_path).name}"
                                
                                response = minio_client.get_object(
                                    MINIO_CONFIG.get('bucket_name', 'music-analyzer'),
                                    minio_path
                                )
                                
                                # Create temporary file for audio
                                with tempfile.NamedTemporaryFile(suffix=Path(music_file.original_filename).suffix, delete=False) as audio_tmp:
                                    audio_tmp.write(response.read())
                                    audio_tmp_path = audio_tmp.name
                                
                                response.close()
                                response.release_conn()
                                
                                # Add to tar archive
                                tar.add(audio_tmp_path, arcname=music_file.original_filename)
                                
                                # Clean up temp file
                                Path(audio_tmp_path).unlink()
                            
                        except Exception as e:
                            print(f"Error adding file {music_file.original_filename}: {e}")
            
            # Read tar.gz content
            with open(tar_path, 'rb') as f:
                tar_content = f.read()
            
            # Generate filename
            if len(music_files) == 1:
                base_filename = Path(music_files[0].original_filename).stem
            else:
                base_filename = f"music_files_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            return {
                'format': 'tar.gz',
                'content': tar_content,
                'filename': f"{base_filename}_original.tar.gz",
                'content_type': 'application/gzip'
            }
            
        finally:
            # Clean up temp file
            if Path(tar_path).exists():
                Path(tar_path).unlink()
    
    async def _export_mono_files_tar_gz(self, music_files: List[MusicFile], export_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Export mono converted files with all metadata as tar.gz archive"""
        from minio import Minio
        
        # Create temporary file for tar.gz
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            tar_path = tmp_file.name
        
        try:
            # Initialize MinIO client
            minio_client = Minio(
                f"{MINIO_CONFIG['host']}:{MINIO_CONFIG['port']}",
                access_key=MINIO_CONFIG['access_key'],
                secret_key=MINIO_CONFIG['secret_key'],
                secure=MINIO_CONFIG['secure']
            )
            
            # Create tar.gz archive
            with tarfile.open(tar_path, 'w:gz') as tar:
                for music_file in music_files:
                    # Create a directory for each file
                    file_dir = Path(music_file.original_filename).stem
                    
                    # Add mono audio file if exists
                    # Check for mono file in processed directory
                    mono_path = Path(str(music_file.storage_path).replace('/original/', '/processed/'))
                    mono_path = mono_path.with_suffix('.mono.wav')
                    
                    if mono_path.exists():
                        try:
                            tar.add(mono_path, arcname=f"{file_dir}/mono.wav")
                        except Exception as e:
                            print(f"Error adding mono file: {e}")
                    else:
                        # Try MinIO for mono file
                        try:
                            path_parts = Path(music_file.storage_path).parts
                            if 'original' in path_parts:
                                idx = path_parts.index('original')
                                base_path = '/'.join(path_parts[idx+1:])
                                minio_mono_path = f"processed/{Path(base_path).with_suffix('.mono.wav')}"
                            else:
                                genre = getattr(music_file, 'genre', 'unknown')
                                minio_mono_path = f"processed/{genre}/{Path(music_file.storage_path).stem}.mono.wav"
                            
                            response = minio_client.get_object(
                                MINIO_CONFIG.get('bucket_name', 'music-analyzer'),
                                minio_mono_path
                            )
                            
                            with tempfile.NamedTemporaryFile(suffix='_mono.wav', delete=False) as mono_tmp:
                                mono_tmp.write(response.read())
                                mono_tmp_path = mono_tmp.name
                            
                            response.close()
                            response.release_conn()
                            
                            tar.add(mono_tmp_path, arcname=f"{file_dir}/mono.wav")
                            Path(mono_tmp_path).unlink()
                            
                        except Exception as e:
                            print(f"Error adding mono file from MinIO: {e}")
                    
                    # Add metadata JSON
                    if export_data:
                        metadata_content = json.dumps(export_data, indent=2).encode('utf-8')
                        metadata_info = tarfile.TarInfo(name=f"{file_dir}/metadata.json")
                        metadata_info.size = len(metadata_content)
                        tar.addfile(metadata_info, io.BytesIO(metadata_content))
                    
                    # Add transcriptions
                    if export_data and export_data.get('transcriptions'):
                        for i, trans in enumerate(export_data['transcriptions']):
                            trans_text = f"Language: {trans.get('language', 'unknown')}\n"
                            trans_text += f"Confidence: {trans.get('confidence', 0)}\n\n"
                            trans_text += trans.get('text', '')
                            
                            trans_content = trans_text.encode('utf-8')
                            trans_info = tarfile.TarInfo(name=f"{file_dir}/transcription_{i+1}.txt")
                            trans_info.size = len(trans_content)
                            tar.addfile(trans_info, io.BytesIO(trans_content))
                    
                    # Add lyrics
                    if export_data and export_data.get('lyrics'):
                        for i, lyrics in enumerate(export_data['lyrics']):
                            if lyrics.get('lyrics_text'):
                                lyrics_content = lyrics['lyrics_text'].encode('utf-8')
                                lyrics_info = tarfile.TarInfo(
                                    name=f"{file_dir}/lyrics_{lyrics.get('source', 'unknown')}_{i+1}.txt"
                                )
                                lyrics_info.size = len(lyrics_content)
                                tar.addfile(lyrics_info, io.BytesIO(lyrics_content))
            
            # Read tar.gz content
            with open(tar_path, 'rb') as f:
                tar_content = f.read()
            
            # Generate filename
            if len(music_files) == 1:
                base_filename = Path(music_files[0].original_filename).stem
            else:
                base_filename = f"music_files_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            return {
                'format': 'mono_tar.gz',
                'content': tar_content,
                'filename': f"{base_filename}_mono_complete.tar.gz",
                'content_type': 'application/gzip'
            }
            
        finally:
            # Clean up temp file
            if Path(tar_path).exists():
                Path(tar_path).unlink()
    
    async def _export_mono_files_tar_gz_batch(self, music_files: List[MusicFile], all_exports: List[Dict]) -> Dict[str, Any]:
        """Export multiple mono files with metadata as tar.gz"""
        from minio import Minio
        
        # Create temporary file for tar.gz
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as tmp_file:
            tar_path = tmp_file.name
        
        try:
            # Initialize MinIO client
            minio_client = Minio(
                f"{MINIO_CONFIG['host']}:{MINIO_CONFIG['port']}",
                access_key=MINIO_CONFIG['access_key'],
                secret_key=MINIO_CONFIG['secret_key'],
                secure=MINIO_CONFIG['secure']
            )
            
            # Create tar.gz archive
            with tarfile.open(tar_path, 'w:gz') as tar:
                for i, (music_file, export_data) in enumerate(zip(music_files, all_exports)):
                    # Create a directory for each file
                    file_dir = Path(music_file.original_filename).stem
                    
                    # Add mono audio file if exists
                    # Check for mono file in processed directory
                    mono_path = Path(str(music_file.storage_path).replace('/original/', '/processed/'))
                    mono_path = mono_path.with_suffix('.mono.wav')
                    
                    if mono_path.exists():
                        try:
                            tar.add(mono_path, arcname=f"{file_dir}/mono.wav")
                        except Exception as e:
                            print(f"Error adding mono file for {music_file.original_filename}: {e}")
                    else:
                        # Try MinIO for mono file
                        try:
                            path_parts = Path(music_file.storage_path).parts
                            if 'original' in path_parts:
                                idx = path_parts.index('original')
                                base_path = '/'.join(path_parts[idx+1:])
                                minio_mono_path = f"processed/{Path(base_path).with_suffix('.mono.wav')}"
                            else:
                                genre = getattr(music_file, 'genre', 'unknown')
                                minio_mono_path = f"processed/{genre}/{Path(music_file.storage_path).stem}.mono.wav"
                            
                            response = minio_client.get_object(
                                MINIO_CONFIG.get('bucket_name', 'music-analyzer'),
                                minio_mono_path
                            )
                            
                            with tempfile.NamedTemporaryFile(suffix='_mono.wav', delete=False) as mono_tmp:
                                mono_tmp.write(response.read())
                                mono_tmp_path = mono_tmp.name
                            
                            response.close()
                            response.release_conn()
                            
                            tar.add(mono_tmp_path, arcname=f"{file_dir}/mono.wav")
                            Path(mono_tmp_path).unlink()
                            
                        except Exception as e:
                            print(f"Error adding mono file for {music_file.original_filename} from MinIO: {e}")
                    
                    # Add metadata JSON
                    metadata_content = json.dumps(export_data, indent=2).encode('utf-8')
                    metadata_info = tarfile.TarInfo(name=f"{file_dir}/metadata.json")
                    metadata_info.size = len(metadata_content)
                    tar.addfile(metadata_info, io.BytesIO(metadata_content))
                    
                    # Add transcriptions
                    if export_data.get('transcriptions'):
                        for j, trans in enumerate(export_data['transcriptions']):
                            trans_text = f"Language: {trans.get('language', 'unknown')}\n"
                            trans_text += f"Confidence: {trans.get('confidence', 0)}\n\n"
                            trans_text += trans.get('text', '')
                            
                            trans_content = trans_text.encode('utf-8')
                            trans_info = tarfile.TarInfo(name=f"{file_dir}/transcription_{j+1}.txt")
                            trans_info.size = len(trans_content)
                            tar.addfile(trans_info, io.BytesIO(trans_content))
                    
                    # Add lyrics
                    if export_data.get('lyrics'):
                        for j, lyrics in enumerate(export_data['lyrics']):
                            if lyrics.get('lyrics_text'):
                                lyrics_content = lyrics['lyrics_text'].encode('utf-8')
                                lyrics_info = tarfile.TarInfo(
                                    name=f"{file_dir}/lyrics_{lyrics.get('source', 'unknown')}_{j+1}.txt"
                                )
                                lyrics_info.size = len(lyrics_content)
                                tar.addfile(lyrics_info, io.BytesIO(lyrics_content))
            
            # Read tar.gz content
            with open(tar_path, 'rb') as f:
                tar_content = f.read()
            
            return {
                'format': 'mono_tar.gz',
                'content': tar_content,
                'filename': f"batch_mono_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.tar.gz",
                'content_type': 'application/gzip'
            }
            
        finally:
            # Clean up temp file
            if Path(tar_path).exists():
                Path(tar_path).unlink()

# Create singleton instance
_exporter = None

def get_exporter() -> MusicAnalyzerExporter:
    """Get or create exporter instance"""
    global _exporter
    if _exporter is None:
        _exporter = MusicAnalyzerExporter()
    return _exporter